from rest_framework import viewsets, mixins, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from celery import chain
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from api.models import Cliente, AsignacionClienteUsuario
from .permissions import SupervisorPuedeVerCierresNominaAnalistas
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
import logging

from .utils.LibroRemuneraciones import clasificar_headers_libro_remuneraciones

User = get_user_model()

from .models import (
    CierreNomina,
    LibroRemuneracionesUpload,
    ArchivoNovedadesUpload,
    ChecklistItem,
    ConceptoRemuneracion,
    AnalistaFiniquito,
    AnalistaIncidencia,
    AnalistaIngreso,
    # Modelos de novedades
    EmpleadoCierreNovedades,
    ConceptoRemuneracionNovedades,
    RegistroConceptoEmpleadoNovedades,
    # Modelos para incidencias
    IncidenciaCierre,
    ResolucionIncidencia,
    # Modelos para discrepancias
    DiscrepanciaCierre,
)

# Importar modelo de informes
from .models_informe import InformeNomina

from .serializers import (
    CierreNominaSerializer, 
    LibroRemuneracionesUploadSerializer, 
    ArchivoNovedadesUploadSerializer, 
    CierreNominaCreateSerializer, 
    ChecklistItemUpdateSerializer, 
    ChecklistItemCreateSerializer,
    ConceptoRemuneracionSerializer,
    AnalistaFiniquitoSerializer,
    AnalistaIncidenciaSerializer,
    AnalistaIngresoSerializer,
    # Serializers de novedades
    EmpleadoCierreNovedadesSerializer,
    ConceptoRemuneracionNovedadesSerializer,
    RegistroConceptoEmpleadoNovedadesSerializer,
    # Serializers de incidencias
    IncidenciaCierreSerializer,
    ResolucionIncidenciaSerializer,
    CrearResolucionSerializer,
    ResumenIncidenciasSerializer,
    # Serializers de discrepancias
    DiscrepanciaCierreSerializer,
    ResumenDiscrepanciasSerializer,
    DiscrepanciaCreateSerializer,
)

from .tasks import (
    analizar_headers_libro_remuneraciones,
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_task,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    # 🚀 NUEVAS TASKS OPTIMIZADAS
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
    procesar_archivo_analista,
    procesar_archivo_novedades,
    generar_incidencias_cierre_task,
    generar_incidencias_cierre_paralelo,  # 🆕 Nueva tarea paralela incidencias
    generar_discrepancias_cierre_paralelo,  # 🆕 Nueva tarea paralela discrepancias (mantener para legacy)
)

# ✅ Import de tarea refactorizada de discrepancias
from .tasks_refactored.discrepancias import generar_discrepancias_cierre_con_logging

logger = logging.getLogger(__name__)

class CierreNominaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los cierres de nómina.
    Supervisores pueden ver cierres de clientes asignados a sus analistas supervisados.
    """
    queryset = CierreNomina.objects.all()
    serializer_class = CierreNominaSerializer
    permission_classes = [IsAuthenticated, SupervisorPuedeVerCierresNominaAnalistas]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        cliente_id = self.request.query_params.get('cliente')
        periodo = self.request.query_params.get('periodo')
        estado = self.request.query_params.get('estado')
        
        # Filtrar por parámetros URL
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        if estado:
            queryset = queryset.filter(estado=estado)

        # Aplicar filtros de acceso según tipo de usuario
        if user.tipo_usuario.lower() == 'gerente':
            # Gerentes ven todo (sin filtros adicionales)
            pass
        elif user.tipo_usuario.lower() == 'supervisor':
            # Supervisores solo ven cierres de clientes asignados a sus analistas supervisados
            analistas_supervisados = user.get_analistas_supervisados()
            clientes_accesibles = AsignacionClienteUsuario.objects.filter(
                usuario__in=analistas_supervisados
            ).values_list('cliente_id', flat=True)
            queryset = queryset.filter(cliente_id__in=clientes_accesibles)
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas solo ven cierres de sus clientes asignados
            clientes_asignados = AsignacionClienteUsuario.objects.filter(
                usuario=user
            ).values_list('cliente_id', flat=True)
            queryset = queryset.filter(cliente_id__in=clientes_asignados)

        return queryset.select_related("cliente", "usuario_analista").order_by(
            "-periodo"
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return CierreNominaCreateSerializer
        return CierreNominaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cierre = serializer.save(usuario_analista=request.user)
        read_serializer = CierreNominaSerializer(cierre, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='resumen/(?P<cliente_id>[^/.]+)')
    def resumen_cliente(self, request, cliente_id=None):
        user = request.user
        
        # Verificar si el usuario tiene acceso a este cliente
        tiene_acceso = False
        
        if user.tipo_usuario.lower() == 'gerente':
            # Gerentes tienen acceso a todos los clientes
            tiene_acceso = True
        elif user.tipo_usuario.lower() == 'supervisor':
            # Supervisores solo ven clientes de sus analistas supervisados
            analistas_supervisados = user.get_analistas_supervisados()
            tiene_acceso = AsignacionClienteUsuario.objects.filter(
                usuario__in=analistas_supervisados,
                cliente_id=cliente_id
            ).exists()
        elif user.tipo_usuario in ['analista', 'senior']:
            # Analistas solo ven sus clientes asignados
            tiene_acceso = AsignacionClienteUsuario.objects.filter(
                usuario=user,
                cliente_id=cliente_id
            ).exists()
        
        if not tiene_acceso:
            return Response({"detail": "No tienes permisos para ver este cliente."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Trae el último cierre de nómina por fecha para este cliente
        cierre = (
            CierreNomina.objects
            .filter(cliente_id=cliente_id)
            .order_by('-periodo')
            .first()
        )
        if cierre:
            # Determinar usuario del cierre: si está finalizado y tiene usuario_finalizacion, usarlo; si no, usuario_analista
            usuario_cierre = None
            try:
                if getattr(cierre, 'usuario_finalizacion_id', None) and cierre.usuario_finalizacion:
                    nombre = getattr(cierre.usuario_finalizacion, 'nombre', None)
                    apellido = getattr(cierre.usuario_finalizacion, 'apellido', None)
                    correo = getattr(cierre.usuario_finalizacion, 'correo_bdo', None)
                    if nombre or apellido:
                        usuario_cierre = f"{nombre or ''} {apellido or ''}".strip()
                    elif correo:
                        usuario_cierre = correo
                    else:
                        usuario_cierre = str(cierre.usuario_finalizacion)
                elif getattr(cierre, 'usuario_analista_id', None) and cierre.usuario_analista:
                    nombre = getattr(cierre.usuario_analista, 'nombre', None)
                    apellido = getattr(cierre.usuario_analista, 'apellido', None)
                    correo = getattr(cierre.usuario_analista, 'correo_bdo', None)
                    if nombre or apellido:
                        usuario_cierre = f"{nombre or ''} {apellido or ''}".strip()
                    elif correo:
                        usuario_cierre = correo
                    else:
                        usuario_cierre = str(cierre.usuario_analista)
            except Exception:
                usuario_cierre = None

            return Response({
                "ultimo_cierre": cierre.periodo,
                "estado_cierre_actual": cierre.estado,
                "usuario_cierre": usuario_cierre,
            })
        else:
            return Response({
                "ultimo_cierre": None,
                "estado_cierre_actual": None,
                "usuario_cierre": None,
            })

    @action(detail=True, methods=['post'], url_path='actualizar-estado')
    def actualizar_estado(self, request, pk=None):
        """
        Actualiza automáticamente el estado del cierre basado en el estado de los archivos
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        
        cierre = self.get_object()
        estado_anterior = cierre.estado
        
        # Verificar el estado de los archivos y actualizar
        estado_nuevo = cierre.actualizar_estado_automatico()
        detalles_archivos = cierre._verificar_archivos_listos()
        
        # Registrar la actividad
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="cierre_general",
            accion="actualizar_estado",
            descripcion=f"Estado actualizado de '{estado_anterior}' a '{estado_nuevo}'",
            usuario=request.user,
            detalles={
                "estado_anterior": estado_anterior,
                "estado_nuevo": estado_nuevo,
                "archivos_verificados": detalles_archivos['detalles'],
                "archivos_faltantes": detalles_archivos['archivos_faltantes'],
                "todos_listos": detalles_archivos['todos_listos']
            },
            ip_address=get_client_ip(request)
        )
        
        # Serializar el cierre actualizado
        serializer = self.get_serializer(cierre)
        
        return Response({
            "success": True,
            "mensaje": f"Estado actualizado de '{estado_anterior}' a '{estado_nuevo}'",
            "cierre": serializer.data,
            "detalles_archivos": detalles_archivos,
            "cambio_estado": estado_anterior != estado_nuevo
        })

    @action(detail=True, methods=['post'], url_path='consolidar-datos')
    def consolidar_datos(self, request, pk=None):
        """
        🔄 CONSOLIDAR DATOS DE NÓMINA
        
        Ejecuta la consolidación de datos del cierre de forma asíncrona:
        1. Valida estado 'verificado_sin_discrepancias'
        2. Lanza tarea Celery de consolidación
        3. Retorna inmediatamente con task_id para seguimiento
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from .tasks import consolidar_datos_nomina_task
        
        cierre = self.get_object()
        estado_anterior = cierre.estado
        
        # Verificar estado válido para consolidación
        # Estados permitidos: verificado_sin_discrepancias, datos_consolidados (reconsolidación) y con_incidencias
        estados_permitidos = ['verificado_sin_discrepancias', 'datos_consolidados', 'con_incidencias']
        if cierre.estado not in estados_permitidos:
            return Response({
                "success": False,
                "error": (
                    "El cierre debe estar en estado 'verificado_sin_discrepancias', "
                    "'datos_consolidados' o 'con_incidencias' para consolidar datos. "
                    f"Estado actual: {cierre.estado}"
                )
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verificar que hay archivos procesados
            libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
            movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
            
            if not libro:
                return Response({
                    "success": False,
                    "error": "No hay libro de remuneraciones procesado disponible"
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not movimientos:
                return Response({
                    "success": False,
                    "error": "No hay archivo de movimientos procesado disponible"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lanzar tarea asíncrona de consolidación OPTIMIZADA
            # Por defecto usa modo 'optimizado' con Celery Chord para mejor rendimiento
            modo_consolidacion = request.data.get('modo', 'optimizado')  # Permitir override
            task = consolidar_datos_nomina_task.delay(cierre.id, modo=modo_consolidacion)
            
            # Registrar inicio de la actividad
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="verificador_datos",
                accion="consolidar_datos",
                descripcion="Iniciando consolidación de datos de nómina",
                usuario=request.user,
                detalles={
                    "estado_anterior": estado_anterior,
                    "task_id": task.id,
                    "archivos_disponibles": {
                        "libro": libro.archivo.name,
                        "movimientos": movimientos.archivo.name
                    }
                },
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": True,
                "mensaje": "Consolidación de datos iniciada",
                "task_id": task.id,
                "cierre_id": cierre.id,
                "estado_inicial": estado_anterior,
                "archivos_procesados": {
                    "libro_remuneraciones": libro.archivo.name,
                    "movimientos_mes": movimientos.archivo.name
                }
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error al iniciar consolidación de datos: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='task-status/(?P<task_id>[^/.]+)')
    def consultar_estado_tarea(self, request, pk=None, task_id=None):
        """
        🔍 CONSULTAR ESTADO DE TAREA CELERY
        
        Permite verificar el estado de una tarea de Celery ejecutándose
        en background (como la consolidación de datos).
        """
        from celery import current_app
        
        if not task_id:
            return Response({
                "success": False,
                "error": "task_id es requerido"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener el resultado de la tarea
            result = current_app.AsyncResult(task_id)
            
            response_data = {
                "task_id": task_id,
                "status": result.status,
                "ready": result.ready()
            }
            
            if result.ready():
                if result.successful():
                    response_data.update({
                        "success": True,
                        "result": result.result
                    })
                else:
                    response_data.update({
                        "success": False,
                        "error": str(result.result) if result.result else "Tarea falló sin información específica"
                    })
            else:
                response_data.update({
                    "success": None,  # Aún en proceso
                    "mensaje": "Tarea en proceso..."
                })
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error consultando estado de tarea: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='estado-cache')
    def estado_cache_cierre(self, request, pk=None):
        """
        🔎 ESTADO DE CACHE PARA UN CIERRE
        Devuelve si existen datos en Redis para este cliente/periodo (informe/consolidados)
        y los contadores de hits/misses del sistema.
        """
        try:
            from .cache_redis import get_cache_system_nomina
            cierre = self.get_object()
            cache = get_cache_system_nomina()
            informe = cache.get_informe_nomina(cierre.cliente_id, cierre.periodo)
            consolidados = cache.get_datos_consolidados(cierre.cliente_id, cierre.periodo)

            # Obtener stats generales
            stats = cache.get_cache_stats()

            return Response({
                'cliente_id': cierre.cliente_id,
                'periodo': cierre.periodo,
                'informe_en_cache': bool(informe),
                'consolidados_en_cache': bool(consolidados),
                'informe_metadata': (informe.get('_metadata') if isinstance(informe, dict) and informe.get('_metadata') else None),
                'stats': stats.get('nomina_counters', stats)
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='generar-incidencias-consolidadas')
    def generar_incidencias_consolidadas(self, request, pk=None):
        """
        Genera incidencias comparando información consolidada con el período anterior
        """
        logger.warning(
            "[DEPRECATION] Endpoint legacy generar_incidencias_consolidadas llamado. "
            "Usar views_incidencias_v2.GeneracionIncidenciasViewSet (incidencias-v2) + tasks_refactored.incidencias"
        )
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
    # La detección usa el orquestador V2 a través de la task generar_incidencias_consolidadas_task
        
        cierre = self.get_object()
        
        # Verificar que el cierre esté consolidado
        if not cierre.puede_generar_incidencias():
            return Response({
                "success": False,
                "error": f"El cierre debe estar consolidado para generar incidencias. Estado actual: {cierre.estado_consolidacion}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya tiene incidencias generadas
        if cierre.estado_incidencias in ['incidencias_generadas', 'incidencias_resueltas']:
            return Response({
                "success": False,
                "error": f"Las incidencias ya fueron generadas para este cierre. Estado: {cierre.estado_incidencias}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Ejecutar generación simplificada sin background (respuesta inmediata con resumen)
            from .tasks import generar_incidencias_consolidadas_task

            resultado = generar_incidencias_consolidadas_task(cierre.id)

            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="generar_incidencias_consolidadas",
                descripcion="Generación de incidencias consolidadas (suma_total)",
                usuario=request.user,
                detalles={
                    "resultado": resultado,
                    "metodo": "suma_total",
                },
                ip_address=get_client_ip(request)
            )

            # Estado de incidencias se actualiza por la reconciliación según conteos
            return Response({
                "success": True,
                "resultado": resultado
            })
                
        except Exception as e:
            # Registrar el error
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="error_iniciar_generar_incidencias_consolidadas",
                descripcion=f"Error iniciando generación de incidencias consolidadas: {str(e)}",
                usuario=request.user,
                detalles={
                    "error": str(e),
                    "metodo": "consolidado_vs_periodo_anterior"
                },
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": False,
                "error": f"Error interno: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='generar-incidencias-dual')
    def generar_incidencias_dual(self, request, pk=None):
        """
        🚀 NUEVA API: Sistema Dual de Detección de Incidencias con Celery Chord
        
        Genera incidencias usando dos tipos de comparación paralela:
        1. Comparación Individual (elemento a elemento) para conceptos seleccionados
        2. Comparación Suma Total (agregada) para todos los conceptos
        
        Body esperado:
        {
            "clasificaciones_seleccionadas": [
                "haberes_imponibles",
                "descuentos_legales", 
                "aportes_patronales"
            ]
        }
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from .utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidados_v2
        
        cierre = self.get_object()
        
        # Validar datos del request
        clasificaciones_seleccionadas = request.data.get('clasificaciones_seleccionadas', [])
        
        if not clasificaciones_seleccionadas:
            return Response({
                "success": False,
                "error": "Debe seleccionar al menos una clasificación para análisis individual"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Clasificaciones válidas disponibles
        clasificaciones_validas = [
            'haberes_imponibles',
            'haberes_no_imponibles', 
            'horas_extras',
            'descuentos_legales',
            'otros_descuentos',
            'aportes_patronales',
            'informacion_adicional',
            'impuestos'
        ]
        
        # Validar clasificaciones enviadas
        clasificaciones_invalidas = set(clasificaciones_seleccionadas) - set(clasificaciones_validas)
        if clasificaciones_invalidas:
            return Response({
                "success": False,
                "error": f"Clasificaciones inválidas: {list(clasificaciones_invalidas)}",
                "clasificaciones_validas": clasificaciones_validas
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el cierre esté consolidado
        if not cierre.puede_generar_incidencias():
            return Response({
                "success": False,
                "error": f"El cierre debe estar consolidado para generar incidencias. Estado actual: {cierre.estado_consolidacion}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya tiene incidencias del sistema dual (permitir regenerar)
        # pero notificar si existen incidencias previas
        incidencias_existentes = cierre.incidencias.filter(tipo_comparacion__in=['individual', 'suma_total']).count()
        
        try:
            # Ejecutar la tarea del sistema dual usando Celery Chord
            resultado = generar_incidencias_consolidados_v2.delay(cierre.id, clasificaciones_seleccionadas)
            
            # Actualizar estado del cierre
            cierre.estado_incidencias = 'generando_incidencias_dual'
            cierre.save(update_fields=['estado_incidencias'])
            
            # Registrar la actividad
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="iniciar_sistema_dual_incidencias",
                descripcion="Iniciado sistema dual de detección de incidencias (Celery Chord)",
                usuario=request.user,
                detalles={
                    "task_id": resultado.id,
                    "clasificaciones_seleccionadas": clasificaciones_seleccionadas,
                    "sistema": "dual_comparacion",
                    "incidencias_existentes": incidencias_existentes,
                    "tipos_analisis": ["individual", "suma_total"]
                },
                ip_address=get_client_ip(request)
            )
            
            mensaje = "Sistema dual de incidencias iniciado exitosamente"
            if incidencias_existentes > 0:
                mensaje += f" (se regenerará sobre {incidencias_existentes} incidencias existentes)"
            
            return Response({
                "success": True,
                "mensaje": mensaje,
                "task_id": resultado.id,
                "estado_incidencias": cierre.estado_incidencias,
                "sistema": "dual_comparacion",
                "analisis_configurado": {
                    "comparacion_individual": {
                        "activa": True,
                        "clasificaciones": clasificaciones_seleccionadas,
                        "descripcion": "Análisis elemento a elemento por empleado"
                    },
                    "comparacion_suma_total": {
                        "activa": True,
                        "clasificaciones": "todas",
                        "descripcion": "Análisis agregado de sumas totales"
                    }
                },
                "clasificaciones_seleccionadas": clasificaciones_seleccionadas,
                "total_clasificaciones_disponibles": len(clasificaciones_validas)
            })
                
        except Exception as e:
            # Registrar el error
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="error_sistema_dual_incidencias",
                descripcion=f"Error iniciando sistema dual: {str(e)}",
                usuario=request.user,
                detalles={
                    "error": str(e),
                    "clasificaciones_seleccionadas": clasificaciones_seleccionadas,
                    "sistema": "dual_comparacion"
                },
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": False,
                "error": f"Error iniciando sistema dual: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='estado-incidencias')
    def estado_incidencias(self, request, pk=None):
        """
        Obtiene el resumen completo del estado de las incidencias para el dashboard
        ACTUALIZADO: Soporte para sistema dual de comparación
        """
        cierre = self.get_object()
        
        # Contar incidencias por estado de resolución usando el estado de la incidencia
        from .models import IncidenciaCierre
        # Base: excluir incidencias informativas del cómputo (p. ej. ingresos informativos auto-resueltos)
        incidencias = IncidenciaCierre.objects.filter(cierre=cierre).exclude(
            datos_adicionales__informativo=True
        )
        
        # NUEVO: Estadísticas por tipo de comparación del sistema dual
        incidencias_individuales = incidencias.filter(tipo_comparacion='individual')
        incidencias_suma_total = incidencias.filter(tipo_comparacion='suma_total')  
        incidencias_legacy = incidencias.filter(tipo_comparacion='legacy')
        
        # Progreso general (por estado directo de la incidencia)
        progreso = {
            'aprobadas': incidencias.filter(estado='aprobada_supervisor').count(),
            'pendientes': incidencias.filter(estado__in=['pendiente', 'resolucion_supervisor_pendiente']).count(),
            'rechazadas': incidencias.filter(estado='rechazada_supervisor').count(),
        }
        
        # Estados de resolución
        estados = {
            'pendiente': incidencias.filter(estado='pendiente').count(),
            'resolucion_supervisor_pendiente': incidencias.filter(estado='resolucion_supervisor_pendiente').count(),
            'resuelta_analista': incidencias.filter(estado='resuelta_analista').count(),
            'aprobada_supervisor': incidencias.filter(estado='aprobada_supervisor').count(),
            'rechazada_supervisor': incidencias.filter(estado='rechazada_supervisor').count(),
        }
        
        # Distribución por prioridad
        prioridades = {
            'critica': incidencias.filter(prioridad='critica').count(),
            'alta': incidencias.filter(prioridad='alta').count(),
            'media': incidencias.filter(prioridad='media').count(),
            'baja': incidencias.filter(prioridad='baja').count()
        }
        
        # NUEVO: Estadísticas del sistema dual
        sistema_dual = {
            'activo': incidencias_individuales.exists() or incidencias_suma_total.exists(),
            'comparacion_individual': {
                'total': incidencias_individuales.count(),
                'pendientes': incidencias_individuales.filter(estado__in=['pendiente', 'resolucion_supervisor_pendiente']).count(),
                'tipos_detectados': list(incidencias_individuales.values_list(
                    'tipo_incidencia', flat=True
                ).distinct()),
                'prioridades': {
                    'critica': incidencias_individuales.filter(prioridad='critica').count(),
                    'alta': incidencias_individuales.filter(prioridad='alta').count(),
                    'media': incidencias_individuales.filter(prioridad='media').count(),
                    'baja': incidencias_individuales.filter(prioridad='baja').count()
                }
            },
            'comparacion_suma_total': {
                'total': incidencias_suma_total.count(),
                'pendientes': incidencias_suma_total.filter(estado__in=['pendiente', 'resolucion_supervisor_pendiente']).count(),
                'tipos_detectados': list(incidencias_suma_total.values_list(
                    'tipo_incidencia', flat=True
                ).distinct()),
                'prioridades': {
                    'critica': incidencias_suma_total.filter(prioridad='critica').count(),
                    'alta': incidencias_suma_total.filter(prioridad='alta').count(),
                    'media': incidencias_suma_total.filter(prioridad='media').count(),
                    'baja': incidencias_suma_total.filter(prioridad='baja').count()
                }
            },
            'resumen_tipos': {
                'individual': incidencias_individuales.count(),
                'suma_total': incidencias_suma_total.count(),
                'legacy': incidencias_legacy.count()
            }
        }
        
        # Verificar si puede finalizar (todas aprobadas)
        total_incidencias = incidencias.count()
        puede_finalizar = total_incidencias > 0 and progreso['aprobadas'] == total_incidencias
        
        # NUEVO: Información de rendimiento si el sistema dual está activo
        rendimiento_info = {}
        if sistema_dual['activo']:
            # Buscar en logs la información del Chord si está disponible
            rendimiento_info = {
                'sistema_utilizado': 'dual_paralelo',
                'comparaciones_ejecutadas': ['individual', 'suma_total'],
                'paralelizacion': True,
                'optimizado': True
            }
        else:
            rendimiento_info = {
                'sistema_utilizado': 'legacy',
                'paralelizacion': False,
                'optimizado': False
            }
        
        return Response({
            'total_incidencias': total_incidencias,
            'progreso': progreso,
            'estados': estados,
            'prioridades': prioridades,
            'puede_finalizar': puede_finalizar,
            'estado_cierre': cierre.estado_incidencias,
            'estado_consolidacion': cierre.estado_consolidacion,
            # NUEVOS CAMPOS DEL SISTEMA DUAL
            'sistema_dual': sistema_dual,
            'rendimiento': rendimiento_info
        })

    @action(detail=True, methods=['get'], url_path='resumen-reconciliacion')
    def resumen_reconciliacion(self, request, pk=None):
        """Devuelve resumen de reconciliación por firma (vN) para mostrar KPIs de recarga."""
        from .utils.reconciliacion import reconciliar_cierre_por_firma
        cierre = self.get_object()
        resumen = reconciliar_cierre_por_firma(cierre.id)
        return Response({
            'success': True,
            'version': resumen.get('version'),
            'vigentes_actualizadas': resumen.get('vigentes_actualizadas', 0),
            'supervisor_pendiente': resumen.get('supervisor_pendiente', 0),
            'unificadas': resumen.get('unificadas', 0)
        })

    @action(detail=True, methods=['post'], url_path='marcar-todas-como-justificadas')
    def marcar_todas_como_justificadas(self, request, pk=None):
        """
        Marca todas las incidencias resueltas por analistas como aprobadas por supervisor (acción masiva)
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from .models import ResolucionIncidencia
        
        cierre = self.get_object()
        comentario = request.data.get('comentario', 'Aprobación masiva por supervisor')
        
        # Verificar permisos de supervisor
        if not request.user.puede_supervisar_analista():
            return Response({
                "error": "Solo supervisores pueden realizar aprobaciones masivas"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener resoluciones pendientes de aprobación (última resolución del analista)
        resoluciones_pendientes = ResolucionIncidencia.objects.filter(
            incidencia__cierre=cierre,
            tipo_resolucion__in=['justificacion_analista', 'correccion_analista', 'consulta_analista']
        ).filter(
            # Solo la última resolución por incidencia
            id__in=ResolucionIncidencia.objects.filter(
                incidencia__cierre=cierre
            ).order_by('incidencia', '-fecha_resolucion').distinct('incidencia').values('id')
        )
        
        if not resoluciones_pendientes.exists():
            return Response({
                "error": "No hay incidencias pendientes de aprobación"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            incidencias_aprobadas = 0
            
            with transaction.atomic():
                for resolucion in resoluciones_pendientes:
                    # Actualizar resolución
                    resolucion.estado = 'aprobada_supervisor'
                    resolucion.fecha_supervision = timezone.now()
                    resolucion.supervisor = request.user
                    resolucion.comentario_supervisor = comentario
                    resolucion.save()
                    
                    # Actualizar incidencia
                    resolucion.incidencia.estado = 'aprobada'
                    resolucion.incidencia.save()
                    
                    incidencias_aprobadas += 1
                
                # Actualizar estado del cierre si es necesario
                total_incidencias = cierre.incidencias_cierre.count()
                incidencias_aprobadas_total = cierre.incidencias_cierre.filter(estado='aprobada').count()
                
                if incidencias_aprobadas_total == total_incidencias:
                    cierre.estado_incidencias = 'incidencias_resueltas'
                    cierre.save(update_fields=['estado_incidencias'])
            
            # Registrar actividad
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="aprobacion_masiva_supervisor",
                descripcion=f"Aprobación masiva de {incidencias_aprobadas} incidencias",
                usuario=request.user,
                detalles={
                    "incidencias_aprobadas": incidencias_aprobadas,
                    "comentario": comentario,
                    "estado_cierre_actualizado": cierre.estado_incidencias
                },
                ip_address=get_client_ip(request)
            )
            
            return Response({
                "success": True,
                "incidencias_aprobadas": incidencias_aprobadas,
                "mensaje": f"{incidencias_aprobadas} incidencias aprobadas exitosamente",
                "nuevo_estado_cierre": cierre.estado_incidencias
            })
            
        except Exception as e:
            return Response({
                "error": f"Error en aprobación masiva: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='solicitar-recarga-archivos')
    def solicitar_recarga_archivos(self, request, pk=None):
        """
        Solicita que se habilite la recarga de archivos para corregir incidencias en Talana
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        
        cierre = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        
        if not motivo:
            return Response({
                "error": "Debe proporcionar un motivo para la recarga"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar permisos de supervisor
        if not request.user.puede_supervisar_analista():
            return Response({
                "error": "Solo supervisores pueden solicitar recarga de archivos"
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Actualizar campos de recarga
            cierre.observaciones_recarga = motivo
            cierre.fecha_solicitud_recarga = timezone.now()
            # Supervisor podría marcar de inmediato como pendiente de aprobación o directamente requerir recarga
            cierre.estado = 'recarga_solicitud_pendiente'
            cierre.save(update_fields=[
                'observaciones_recarga', 
                'fecha_solicitud_recarga', 
                'estado'
            ])
            
            # Registrar actividad
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="solicitar_recarga_archivos",
                descripcion=f"Solicitud de recarga de archivos: {motivo}",
                usuario=request.user,
                detalles={
                    "motivo": motivo,
                    "estado": cierre.estado
                },
                ip_address=get_client_ip(request)
            )
            
            # Instrucciones para el analista
            instrucciones = [
                "1. Corregir los datos problemáticos en Talana",
                "2. Exportar nuevamente los archivos desde Talana",
                "3. Resubir archivos en esta plataforma",
                "4. Ejecutar nueva consolidación",
                "5. Verificar que las incidencias se resuelvan"
            ]
            
            return Response({
                "success": True,
                "mensaje": "Solicitud de recarga registrada exitosamente",
                "estado_cierre": cierre.estado,
                "instrucciones": instrucciones
            })
            
        except Exception as e:
            return Response({
                "error": f"Error solicitando recarga: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='solicitar-recarga-archivos-analista')
    def solicitar_recarga_archivos_analista(self, request, pk=None):
        """
        El analista solicita la recarga; queda pendiente de aprobación del supervisor
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from django.utils import timezone

        cierre = self.get_object()
        motivo = request.data.get('motivo', '').strip()

        if not motivo:
            return Response({"error": "Debe proporcionar un motivo para la recarga"}, status=400)

        try:
            # Marcar como solicitud pendiente
            cierre.observaciones_recarga = motivo
            cierre.fecha_solicitud_recarga = timezone.now()
            cierre.fecha_aprobacion_recarga = None
            cierre.estado = 'recarga_solicitud_pendiente'
            cierre.save(update_fields=['observaciones_recarga', 'fecha_solicitud_recarga', 'fecha_aprobacion_recarga', 'estado'])

            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="solicitud_recarga_analista",
                descripcion=f"Analista solicita recarga: {motivo}",
                usuario=request.user,
                detalles={"motivo": motivo, "estado": cierre.estado},
                ip_address=get_client_ip(request)
            )

            return Response({
                "success": True,
                "mensaje": "Solicitud de recarga enviada y pendiente de aprobación",
                "estado_cierre": cierre.estado
            })
        except Exception as e:
            return Response({"error": f"Error solicitando recarga: {str(e)}"}, status=500)

    @action(detail=True, methods=['post'], url_path='aprobar-recarga-archivos')
    def aprobar_recarga_archivos(self, request, pk=None):
        """
        Supervisor aprueba la solicitud de recarga. Incrementa version_datos y habilita recarga.
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from django.utils import timezone

        cierre = self.get_object()

        # Verificar permisos de supervisor
        if not request.user.puede_supervisar_analista():
            return Response({"error": "Solo supervisores pueden aprobar recarga"}, status=403)

        try:
            cierre.fecha_aprobacion_recarga = timezone.now()
            cierre.version_datos = (cierre.version_datos or 0) + 1
            cierre.estado = 'requiere_recarga_archivos'
            cierre.save(update_fields=['fecha_aprobacion_recarga', 'version_datos', 'estado'])

            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="incidencias",
                accion="aprobar_recarga_archivos",
                descripcion=f"Aprobación de recarga. Versión datos: {cierre.version_datos}",
                usuario=request.user,
                detalles={
                    "estado_previo": 'recarga_solicitud_pendiente',
                    "estado_nuevo": cierre.estado,
                    "version_datos": cierre.version_datos
                },
                ip_address=get_client_ip(request)
            )

            instrucciones = [
                "1. Corregir los datos problemáticos en Talana",
                "2. Exportar nuevamente los archivos desde Talana",
                "3. Resubir archivos en esta plataforma",
                "4. Ejecutar nueva consolidación",
                "5. Verificar que las incidencias se resuelvan"
            ]

            return Response({
                "success": True,
                "mensaje": "Recarga aprobada. Proceda a resubir archivos",
                "version_datos": cierre.version_datos,
                "estado_cierre": cierre.estado,
                "instrucciones": instrucciones
            })
        except Exception as e:
            return Response({"error": f"Error aprobando recarga: {str(e)}"}, status=500)

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroRemuneracionesUpload.objects.all()
    serializer_class = LibroRemuneracionesUploadSerializer
    
    def perform_create(self, serializer):
        """
        Crear libro de remuneraciones con logging completo integrado
        """
        from .utils.mixins_stub import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
        from .utils.clientes import get_client_ip
        from .utils.uploads import guardar_temporal
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 1. OBTENER DATOS DEL REQUEST
        request = self.request
        archivo = request.FILES.get('archivo')
        cierre_id = request.data.get('cierre')
        
        if not archivo or not cierre_id:
            raise ValueError("Archivo y cierre_id son requeridos")
        
        # 2. OBTENER CIERRE Y CLIENTE
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cliente = cierre.cliente
        except CierreNomina.DoesNotExist:
            raise ValueError("Cierre no encontrado")
        
        # 3. VALIDAR ARCHIVO
        try:
            validator = ValidacionArchivoCRUDMixin()
            validator.validar_archivo(archivo)
        except ValueError as e:
            logger.error(f"Error validando archivo: {e}")
            raise
        
        # 4. CREAR UPLOAD LOG
        log_mixin = UploadLogNominaMixin()
        log_mixin.tipo_upload = "libro_remuneraciones"
        log_mixin.usuario = request.user
        log_mixin.ip_usuario = get_client_ip(request)
        
        upload_log = log_mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log creado con ID: {upload_log.id}")
        
        # 5. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta
        upload_log.save()
        
        # 6. CREAR/ACTUALIZAR REGISTRO DE LIBRO
        libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
        
        if libro_existente:
            # Actualizar existente
            libro_existente.archivo = archivo
            libro_existente.estado = 'pendiente'
            libro_existente.header_json = []
            libro_existente.upload_log = upload_log
            libro_existente.save()
            instance = libro_existente
            logger.info(f"Libro actualizado con ID: {instance.id}")
        else:
            # Crear nuevo
            instance = serializer.save(upload_log=upload_log)
            logger.info(f"Libro creado con ID: {instance.id}")
        
        # 7. REGISTRAR ACTIVIDAD
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="libro_remuneraciones",
            accion="upload_excel",
            descripcion=f"Archivo {archivo.name} subido para procesamiento",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "tamaño_archivo": archivo.size,
                "upload_log_id": upload_log.id
            },
            ip_address=get_client_ip(request),
            upload_log=upload_log
        )
        
        # 8. GUARDAR LIBRO_ID EN RESUMEN DEL UPLOAD_LOG
        upload_log.resumen = {"libro_id": instance.id}
        upload_log.save(update_fields=['resumen'])
        
        # 9. INICIAR PROCESAMIENTO CON CELERY
        with transaction.atomic():
            try:
                chain(
                    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, upload_log.id),
                    clasificar_headers_libro_remuneraciones_con_logging.s(),
                ).apply_async()
                logger.info(f"Chain de Celery iniciado para libro {instance.id} y upload_log {upload_log.id}")
            except Exception as e:
                logger.error(f"Error iniciando procesamiento: {e}")
                upload_log.marcar_como_error(f"Error iniciando procesamiento: {str(e)}")
                raise
        validator = ValidacionArchivoCRUDMixin()
        validator.validar_archivo(archivo)
        
        # 4. CREAR UPLOAD LOG
        mixin = UploadLogNominaMixin()
        mixin.tipo_upload = "libro_remuneraciones"
        mixin.usuario = request.user
        mixin.ip_usuario = get_client_ip(request)
        
        upload_log = mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log creado con ID: {upload_log.id}")
        
        # 5. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta
        upload_log.cierre = cierre
        upload_log.save()
        
        # 6. CREAR REGISTRO DEL LIBRO
        with transaction.atomic():
            # Marcar como no principal cualquier iteración anterior
            LibroRemuneracionesUpload.objects.filter(
                cierre=cierre
            ).update(estado='con_error')  # Marcar anteriores como error
            
            # Crear nueva instancia
            serializer.save(
                cierre=cierre,
                upload_log=upload_log,
                estado='pendiente'
            )
            instance = serializer.instance
            
            # Registrar actividad
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="libro_remuneraciones",
                accion="upload_excel",
                descripcion=f"Archivo {archivo.name} subido para procesamiento",
                usuario=request.user,
                detalles={
                    "nombre_archivo": archivo.name,
                    "tamaño_archivo": archivo.size,
                    "upload_log_id": upload_log.id,
                    "libro_id": instance.id
                },
                ip_address=get_client_ip(request),
                upload_log=upload_log
            )
        
        # 7. EJECUTAR CHAIN DE CELERY CON LOGGING
        try:
            chain(
                analizar_headers_libro_remuneraciones_con_logging.s(
                    instance.id, upload_log.id
                ),
            ).apply_async()
            
            logger.info(f"Chain iniciado para libro {instance.id} con upload_log {upload_log.id}")
            
        except Exception as e:
            logger.error(f"Error iniciando chain: {e}")
            upload_log.marcar_como_error(f"Error iniciando procesamiento: {str(e)}")
            raise
        try:
            validator.validar_archivo(archivo)
        except ValueError as e:
            raise ValueError(f"Error de validación: {e}")
        
        # 4. CREAR UPLOAD_LOG
        mixin = UploadLogNominaMixin()
        mixin.tipo_upload = "libro_remuneraciones"
        mixin.usuario = request.user
        mixin.ip_usuario = get_client_ip(request)
        
        upload_log = mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log creado con ID: {upload_log.id}")
        
        # 5. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta
        upload_log.save()
        
        # 6. CREAR/ACTUALIZAR LIBRO REMUNERACIONES
        instance = serializer.save()
        instance.upload_log = upload_log
        instance.save()
        
        # 7. REGISTRAR ACTIVIDAD
        mixin.registrar_actividad(
            tarjeta_tipo="libro_remuneraciones",
            tarjeta_id=instance.id,
            accion="upload_excel",
            descripcion=f"Archivo {archivo.name} subido para procesamiento",
            datos_adicionales={
                "nombre_archivo": archivo.name,
                "tamaño_archivo": archivo.size,
                "upload_log_id": upload_log.id
            }
        )
        
        # 8. INICIAR CHAIN DE CELERY CON LOGGING
        try:
            with transaction.atomic():
                chain(
                    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, upload_log.id),
                    clasificar_headers_libro_remuneraciones_con_logging.s(),
                ).apply_async()
                
                logger.info(f"Chain iniciado para libro {instance.id} con upload_log {upload_log.id}")
                
        except Exception as e:
            # Marcar upload como error si falla el chain
            upload_log.estado = 'error'
            upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
            upload_log.save()
            logger.error(f"Error iniciando chain: {e}")
            raise
        validador = ValidacionArchivoCRUDMixin()
        try:
            validador.validar_archivo(archivo)
        except ValueError as e:
            logger.error(f"Validación de archivo falló: {e}")
            raise ValueError(f"Archivo no válido: {e}")
        
        # 3. CREAR UPLOAD LOG ANTES DE GUARDAR
        mixin = UploadLogNominaMixin()
        mixin.tipo_upload = "libro_remuneraciones"
        mixin.usuario = self.request.user
        mixin.ip_usuario = get_client_ip(self.request)
        
        upload_log = mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log creado con ID: {upload_log.id}")
        
        # 4. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta
        upload_log.save()
        
        # 5. CREAR/ACTUALIZAR REGISTRO Y ENLAZAR CON UPLOAD_LOG
        with transaction.atomic():
            # Verificar si ya existe un libro para este cierre
            libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
            
            if libro_existente:
                # Actualizar archivo existente
                libro_existente.archivo = serializer.validated_data.get('archivo')
                libro_existente.fecha_subida = timezone.now()
                libro_existente.estado = 'pendiente'
                libro_existente.upload_log = upload_log
                libro_existente.save()
                instance = libro_existente
                logger.info(f"Archivo actualizado para cierre {cierre_id}")
            else:
                # Crear nuevo registro
                instance = serializer.save(upload_log=upload_log)
                logger.info(f"Nuevo archivo creado para cierre {cierre_id}")
        
        # 6. REGISTRAR ACTIVIDAD
        mixin.registrar_actividad(
            tarjeta_tipo="libro_remuneraciones",
            tarjeta_id=instance.id,
            accion="upload_excel",
            descripcion=f"Archivo {archivo.name} subido correctamente",
            datos_adicionales={
                "nombre_archivo": archivo.name,
                "tamaño_archivo": archivo.size,
                "upload_log_id": upload_log.id,
                "ruta_temporal": ruta
            }
        )
        
        # 7. GUARDAR INSTANCIA_ID EN EL RESUMEN DEL UPLOAD_LOG
        upload_log.resumen = {
            "libro_id": instance.id,
            "cierre_id": cierre_id,
            "cliente_id": cliente.id
        }
        upload_log.save(update_fields=['resumen'])
        
        # 8. INICIAR PROCESAMIENTO CELERY CON LOGGING
        try:
            # Usar la nueva tarea que incluye logging
            chain(
                analizar_headers_libro_remuneraciones_con_logging.s(instance.id, upload_log.id),
                clasificar_headers_libro_remuneraciones_con_logging.s()
            ).apply_async()
            
            logger.info(f"Chain de procesamiento iniciado para libro {instance.id} con upload_log {upload_log.id}")
            
        except Exception as e:
            logger.error(f"Error iniciando chain de procesamiento: {e}")
            # Marcar upload_log como error
            mixin.marcar_como_error(upload_log.id, f"Error iniciando procesamiento: {str(e)}")
            raise
        mixin = UploadLogNominaMixin()
        mixin.tipo_upload = "libro_remuneraciones"
        mixin.usuario = self.request.user
        mixin.ip_usuario = get_client_ip(self.request)
        
        upload_log = mixin.crear_upload_log(cliente, archivo)
        
        # 4. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta_temporal = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta_temporal
        upload_log.cierre = cierre
        upload_log.save()
        
        logger.info(f"Upload log creado: {upload_log.id} para cierre {cierre_id}")
        
        # 5. CREAR INSTANCIA DE LIBRO
        instance = serializer.save(upload_log=upload_log)
        
        # 6. REGISTRAR ACTIVIDAD
        try:
            mixin.registrar_actividad(
                tarjeta_tipo="libro_remuneraciones",
                tarjeta_id=instance.id,
                accion="upload_excel",
                descripcion=f"Archivo {archivo.name} subido para procesamiento",
                datos_adicionales={
                    "nombre_archivo": archivo.name,
                    "tamaño_archivo": archivo.size,
                    "upload_log_id": upload_log.id,
                    "cierre_id": cierre_id,
                }
            )
        except Exception as e:
            logger.warning(f"No se pudo registrar actividad: {e}")
        
        # 7. ACTUALIZAR RESUMEN DEL UPLOAD LOG
        upload_log.resumen = {
            "libro_id": instance.id,
            "cierre_id": cierre_id,
            "cliente_id": cliente.id,
            "archivo_original": archivo.name
        }
        upload_log.save(update_fields=['resumen'])
        
        # 8. EJECUTAR CHAIN DE CELERY CON LOGGING
        try:
            with transaction.atomic():
                # Forzar commit antes del chain
                transaction.on_commit(lambda: self._ejecutar_procesamiento_con_logging(instance.id, upload_log.id))
                
        except Exception as e:
            logger.error(f"Error iniciando procesamiento: {e}")
            # Marcar upload_log como error
            mixin.marcar_como_error(upload_log.id, f"Error iniciando procesamiento: {e}")
            raise
    
    def _ejecutar_procesamiento_con_logging(self, libro_id, upload_log_id):
        """
        Ejecuta el chain de procesamiento con logging integrado
        """
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Chain mejorado con logging
            chain(
                analizar_headers_libro_remuneraciones_con_logging.s(libro_id, upload_log_id),
                clasificar_headers_libro_remuneraciones_task.s(),
            ).apply_async()
            
            logger.info(f"Chain iniciado para libro {libro_id} con upload_log {upload_log_id}")
            
        except Exception as e:
            logger.error(f"Error ejecutando chain: {e}")
            # Marcar como error
            from .utils.mixins_stub import UploadLogNominaMixin
            mixin = UploadLogNominaMixin()
            mixin.marcar_como_error(upload_log_id, f"Error en chain: {e}")

    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        """
        Obtiene el estado del libro con información de logging
        """
        libro = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if libro:
            # Información básica del libro
            response_data = {
                "id": libro.id,
                "estado": libro.estado,
                "archivo_nombre": libro.archivo.name.split("/")[-1],
                "archivo_url": request.build_absolute_uri(libro.archivo.url),
                "header_json": libro.header_json,
                "fecha_subida": libro.fecha_subida,
                "cliente_id": libro.cierre.cliente.id,
                "cliente_nombre": libro.cierre.cliente.nombre,
            }
            
            # Agregar información de logging si existe
            if libro.upload_log:
                response_data.update({
                    "upload_log": {
                        "id": libro.upload_log.id,
                        "estado_upload": libro.upload_log.estado,
                        "registros_procesados": libro.upload_log.registros_procesados,
                        "registros_exitosos": libro.upload_log.registros_exitosos,
                        "registros_fallidos": libro.upload_log.registros_fallidos,
                        "errores": libro.upload_log.errores,
                        "usuario": libro.upload_log.usuario.correo_bdo if libro.upload_log.usuario else None,
                        "iteracion": libro.upload_log.iteracion,
                    }
                })
            
            return Response(response_data)
        else:
            return Response({
                "id": None,
                "estado": "no_subido",
                "archivo_nombre": "",
                "archivo_url": "",
                "header_json": [],
                "fecha_subida": None,
                "cliente_id": None,
                "cliente_nombre": "",
                "upload_log": None,
            })
    
    @action(detail=True, methods=['get'], url_path='log-actividades')
    def log_actividades(self, request, pk=None):
        """
        Obtiene el log de actividades para este libro específico
        """
        libro = self.get_object()
        
        from .models_logging_stub import TarjetaActivityLogNomina
        
        actividades = TarjetaActivityLogNomina.objects.filter(
            cierre=libro.cierre,
            tarjeta="libro_remuneraciones"
        ).order_by('-timestamp')[:20]  # Últimas 20 actividades
        
        data = []
        for actividad in actividades:
            data.append({
                "id": actividad.id,
                "accion": actividad.accion,
                "descripcion": actividad.descripcion,
                "usuario": actividad.usuario.correo_bdo if actividad.usuario else None,
                "timestamp": actividad.timestamp,
                "resultado": actividad.resultado,
                "detalles": actividad.detalles,
            })
        
        return Response({
            "libro_id": libro.id,
            "actividades": data,
            "total": len(data)
        })

    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """
        🚀 Procesar libro completo: actualizar empleados y guardar registros.
        Versión optimizada con Celery Chord para mejor rendimiento.
        """
        libro = self.get_object()
        libro.estado = 'procesando'
        libro.save(update_fields=['estado'])
        
        # Leer parámetros opcionales - optimización activada por defecto
        usar_optimizacion = request.data.get('usar_optimizacion', True) if hasattr(request, 'data') and request.data else True
        
        logger.info(f"🔄 Iniciando procesamiento de libro {libro.id}, optimización: {usar_optimizacion}")
        
        if usar_optimizacion:
            # 🚀 USAR VERSIONES OPTIMIZADAS CON CHORD
            try:
                result = chain(
                    actualizar_empleados_desde_libro_optimizado.s(libro.id),
                    guardar_registros_nomina_optimizado.s(),
                ).apply_async()
                
                mensaje = 'Procesamiento optimizado iniciado (usando Celery Chord para mejor rendimiento)'
                logger.info(f"🚀 Chain optimizado iniciado para libro {libro.id}")
                
            except Exception as e:
                # Fallback a versión no optimizada
                logger.warning(f"⚠️ Error iniciando procesamiento optimizado: {e}, usando fallback")
                result = chain(
                    actualizar_empleados_desde_libro.s(libro.id),
                    guardar_registros_nomina.s(),
                ).apply_async()
                mensaje = 'Procesamiento iniciado (fallback a modo clásico)'
        else:
            # 📝 USAR VERSIONES CLÁSICAS
            result = chain(
                actualizar_empleados_desde_libro.s(libro.id),
                guardar_registros_nomina.s(),
            ).apply_async()
            mensaje = 'Procesamiento clásico iniciado'
            logger.info(f"📝 Chain clásico iniciado para libro {libro.id}")
        
        return Response({
            'task_id': result.id if hasattr(result, 'id') else str(result), 
            'mensaje': mensaje,
            'optimizado': usar_optimizacion
        }, status=status.HTTP_202_ACCEPTED)
    
    def perform_destroy(self, instance):
        """
        Eliminar libro de remuneraciones y todos sus datos relacionados
        """
        from .models_logging_stub import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        cierre = instance.cierre
        
        # Registrar actividad antes de eliminar
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="libro_remuneraciones",
            accion="delete_archivo",
            descripcion=f"Libro de remuneraciones eliminado para resubida",
            usuario=self.request.user,
            detalles={
                "libro_id": instance.id,
                "archivo_nombre": instance.archivo.name if instance.archivo else "N/A",
                "estado_anterior": instance.estado
            },
            ip_address=get_client_ip(self.request)
        )
        
        with transaction.atomic():
            # 1. Eliminar todos los registros de conceptos de empleados del cierre
            # (estos están vinculados a EmpleadoCierre, que está vinculado al cierre)
            empleados_cierre = cierre.empleados.all()
            for empleado in empleados_cierre:
                empleado.registroconceptoempleado_set.all().delete()
                logger.info(f"Eliminados registros de conceptos para empleado {empleado.rut}")
            
            # 2. Eliminar todos los empleados del cierre
            count_empleados = empleados_cierre.count()
            empleados_cierre.delete()
            logger.info(f"Eliminados {count_empleados} empleados del cierre {cierre.id}")
            
            # 3. Resetear estado del cierre a pendiente
            cierre.estado = 'pendiente'
            cierre.estado_incidencias = 'pendiente'
            cierre.save(update_fields=['estado', 'estado_incidencias'])
            
            # 4. Eliminar el libro de remuneraciones
            instance.delete()
            logger.info(f"Libro de remuneraciones {instance.id} eliminado completamente")

# APIs de funciones

@api_view(['GET'])
def conceptos_remuneracion_por_cliente(request):
    cliente_id = request.query_params.get('cliente_id')
    if not cliente_id:
        return Response({"error": "Se requiere cliente_id"}, status=400)

    conceptos = ConceptoRemuneracion.objects.filter(cliente_id=cliente_id, vigente=True)
    serializer = ConceptoRemuneracionSerializer(conceptos, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def conceptos_remuneracion_por_cierre(request, cierre_id):
    """Obtiene los conceptos de remuneración del libro del cierre especificado"""
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        conceptos = ConceptoRemuneracion.objects.filter(
            cliente=cierre.cliente, 
            vigente=True
        ).order_by('nombre_concepto')
        
        serializer = ConceptoRemuneracionSerializer(conceptos, many=True)
        return Response(serializer.data)
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

class ConceptoRemuneracionBatchView(APIView):
    def post(self, request):
        data = request.data
        cliente_id = data.get("cliente_id")
        cierre_id = data.get("cierre_id")
        conceptos = data.get("conceptos", {})

        if not cliente_id or not isinstance(conceptos, dict):
            return Response({"error": "Datos incompletos"}, status=400)

        cliente = Cliente.objects.filter(id=cliente_id).first()
        if not cliente:
            return Response({"error": "Cliente no encontrado"}, status=404)

        usuario = request.user

        for nombre, info in conceptos.items():
            clasificacion = info.get("clasificacion")
            hashtags = info.get("hashtags", [])

            if not clasificacion:
                continue  # Ignora si falta clasificación

            obj, _ = ConceptoRemuneracion.objects.update_or_create(
                cliente=cliente,
                nombre_concepto=nombre,
                defaults={
                    "clasificacion": clasificacion,
                    "hashtags": hashtags,
                    "usuario_clasifica": usuario,
                    "vigente": True
                }
            )

        # Si se especificó un cierre, actualiza el JSON de headers
        if cierre_id:
            try:
                libro = (
                    LibroRemuneracionesUpload.objects
                    .filter(cierre_id=cierre_id)
                    .order_by('-fecha_subida')
                    .first()
                )
                if libro:
                    if isinstance(libro.header_json, dict):
                        headers = (
                            libro.header_json.get("headers_clasificados", [])
                            + libro.header_json.get("headers_sin_clasificar", [])
                        )
                    else:
                        headers = libro.header_json or []
                    headers_c, headers_s = clasificar_headers_libro_remuneraciones(headers, cliente)
                    libro.header_json = {
                        "headers_clasificados": headers_c,
                        "headers_sin_clasificar": headers_s,
                    }
                    libro.estado = 'clasif_pendiente' if headers_s else 'clasificado'
                    libro.save()
            except Exception as e:
                logger.error(f"Error actualizando libro tras clasificacion: {e}")

        return Response({"status": "ok", "actualizados": len(conceptos)}, status=status.HTTP_200_OK)

@api_view(['GET'])
def obtener_hashtags_disponibles(request, cliente_id):
    conceptos = ConceptoRemuneracion.objects.filter(cliente_id=cliente_id)
    hashtags = set()
    for c in conceptos:
        hashtags.update(c.hashtags or [])
    return Response(sorted(list(hashtags)))

@api_view(['DELETE'])
def eliminar_concepto_remuneracion(request, cliente_id, nombre_concepto):
    try:
        concepto = ConceptoRemuneracion.objects.get(
            cliente_id=cliente_id,
            nombre_concepto=nombre_concepto
        )
    except ConceptoRemuneracion.DoesNotExist:
        return Response(
            {"error": "No encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

    concepto.vigente = False
    concepto.save()
    return Response({"status": "ok"})

# ViewSets existentes

class ArchivoNovedadesUploadViewSet(viewsets.ModelViewSet):
    queryset = ArchivoNovedadesUpload.objects.all()
    serializer_class = ArchivoNovedadesUploadSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        """Obtiene el estado del archivo de novedades para un cierre específico"""
        archivo = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if archivo:
            return Response({
                "id": archivo.id,
                "estado": archivo.estado,
                "archivo_nombre": archivo.archivo.name.split("/")[-1] if archivo.archivo else "",
                "archivo_url": request.build_absolute_uri(archivo.archivo.url) if archivo.archivo else "",
                "fecha_subida": archivo.fecha_subida,
                "cierre_id": archivo.cierre.id,
                "cliente_id": archivo.cierre.cliente.id,
                "cliente_nombre": archivo.cierre.cliente.nombre,
            })
        else:
            return Response({
                "id": None,
                "estado": "no_subido",
                "archivo_nombre": "",
                "archivo_url": "",
                "fecha_subida": None,
                "cierre_id": None,
                "cliente_id": None,
                "cliente_nombre": "",
            })
    
    @action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)')
    def subir(self, request, cierre_id=None):
        """Sube un archivo de novedades para un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se proporcionó archivo"}, status=400)
        
        # Validar que sea un archivo Excel
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response({"error": "El archivo debe ser de tipo Excel (.xlsx o .xls)"}, status=400)
        
        # Crear o actualizar el registro de novedades
        archivo_novedades, created = ArchivoNovedadesUpload.objects.get_or_create(
            cierre=cierre,
            defaults={
                'archivo': archivo,
                'analista': request.user,
                'estado': 'pendiente'
            }
        )
        
        if not created:
            # Si ya existe, actualizar el archivo
            archivo_novedades.archivo = archivo
            archivo_novedades.analista = request.user
            archivo_novedades.estado = 'pendiente'
            archivo_novedades.save()
        
        # Disparar tarea de procesamiento con Celery
        procesar_archivo_novedades.delay(archivo_novedades.id)
        
        return Response({
            "id": archivo_novedades.id,
            "estado": archivo_novedades.estado,
            "archivo_nombre": archivo.name,
            "fecha_subida": archivo_novedades.fecha_subida,
            "mensaje": "Archivo subido correctamente y enviado a procesamiento"
        }, status=201)

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        """Reprocesa un archivo de novedades desde el inicio"""
        from nomina.tasks import procesar_archivo_novedades
        
        archivo = self.get_object()
        
        if archivo.estado == 'en_proceso':
            return Response({
                "error": "El archivo ya está siendo procesado"
            }, status=400)
        
        try:
            # Resetear estado y limpiar datos previos
            archivo.estado = 'en_proceso'
            archivo.header_json = None
            archivo.save()
            
            # Iniciar procesamiento asíncrono
            procesar_archivo_novedades.delay(archivo.id)
            
            return Response({
                "mensaje": "Reprocesamiento iniciado",
                "estado": archivo.estado
            })
            
        except Exception as e:
            archivo.estado = 'con_error'
            archivo.save()
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['get'])
    def headers(self, request, pk=None):
        """Obtiene los headers de un archivo de novedades para clasificación"""
        archivo = self.get_object()
        
        if archivo.estado not in ['clasif_pendiente', 'clasificado', 'procesado']:
            return Response({
                "error": "El archivo debe estar en estado 'clasif_pendiente', 'clasificado' o 'procesado' para obtener headers"
            }, status=400)
        
        headers_data = archivo.header_json
        if isinstance(headers_data, dict):
            headers_clasificados = headers_data.get("headers_clasificados", [])
            headers_sin_clasificar = headers_data.get("headers_sin_clasificar", [])
        else:
            headers_clasificados = []
            headers_sin_clasificar = headers_data if isinstance(headers_data, list) else []
        
        # Si el archivo está procesado, incluir los mapeos existentes
        mapeos_existentes = {}
        if archivo.estado == 'procesado':
            from nomina.models import ConceptoRemuneracionNovedades
            mapeos = ConceptoRemuneracionNovedades.objects.filter(
                cliente=archivo.cierre.cliente,
                activo=True,
                nombre_concepto_novedades__in=headers_clasificados
            ).select_related('concepto_libro')

            for mapeo in mapeos:
                if mapeo.concepto_libro:
                    mapeos_existentes[mapeo.nombre_concepto_novedades] = {
                        'concepto_libro_id': mapeo.concepto_libro.id,
                        'concepto_libro_nombre': mapeo.concepto_libro.nombre_concepto,
                        'concepto_libro_clasificacion': mapeo.concepto_libro.clasificacion,
                    }
                else:
                    mapeos_existentes[mapeo.nombre_concepto_novedades] = {
                        'concepto_libro_id': None,
                    }
        
        return Response({
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
            "mapeos_existentes": mapeos_existentes
        })

    @action(detail=True, methods=['post'])
    def clasificar_headers(self, request, pk=None):
        """Mapea headers pendientes de un archivo de novedades con conceptos del libro de remuneraciones"""
        from nomina.models import ConceptoRemuneracionNovedades, ConceptoRemuneracion
        
        archivo = self.get_object()
        
        if archivo.estado != 'clasif_pendiente':
            return Response({
                "error": "El archivo debe estar en estado 'clasif_pendiente' para mapear headers"
            }, status=400)
        
        mapeos = request.data.get('mapeos', [])
        if not mapeos:
            return Response({"error": "No se proporcionaron mapeos"}, status=400)
        
        try:
            # Obtener headers actuales
            headers_data = archivo.header_json
            headers_clasificados = headers_data.get("headers_clasificados", [])
            headers_sin_clasificar = headers_data.get("headers_sin_clasificar", [])
            
            # Procesar mapeos
            for mapeo in mapeos:
                header_novedades = mapeo.get('header_novedades')
                concepto_libro_id = mapeo.get('concepto_libro_id')

                if header_novedas in headers_sin_clasificar:
                    if concepto_libro_id:
                        try:
                            concepto_libro = ConceptoRemuneracion.objects.get(
                                id=concepto_libro_id,
                                cliente=archivo.cierre.cliente,
                                vigente=True
                            )
                        except ConceptoRemuneracion.DoesNotExist:
                            continue
                    else:
                        concepto_libro = None

                    # Crear o actualizar mapeo
                    mapeo_concepto, created = ConceptoRemuneracionNovedades.objects.get_or_create(
                        cliente=archivo.cierre.cliente,
                        nombre_concepto_novedas=header_novedas,
                        defaults={
                            'concepto_libro': concepto_libro,
                            'usuario_mapea': request.user,
                            'activo': True,
                        }
                    )

                    if not created:
                        mapeo_concepto.concepto_libro = concepto_libro
                        mapeo_concepto.usuario_mapea = request.user
                        mapeo_concepto.activo = True
                        mapeo_concepto.save()

                    # Mover de sin clasificar a clasificados
                    headers_sin_clasificar.remove(header_novedas)
                    headers_clasificados.append(header_novedas)
            
            # Actualizar archivo
            archivo.header_json = {
                "headers_clasificados": headers_clasificados,
                "headers_sin_clasificar": headers_sin_clasificar,
            }
            
            # Cambiar estado si ya no hay headers sin clasificar
            if not headers_sin_clasificar:
                archivo.estado = "clasificado"
            
            archivo.save()
            
            return Response({
                "mensaje": "Headers mapeados correctamente",
                "headers_clasificados": len(headers_clasificados),
                "headers_sin_clasificar": len(headers_sin_clasificar),
                "estado": archivo.estado
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def procesar_final(self, request, pk=None):
        """Procesa finalmente un archivo de novedades (actualiza empleados y guarda registros)"""
        from nomina.tasks import actualizar_empleados_desde_novedades_task, guardar_registros_novedades_task
        
        archivo = self.get_object()
        
        if archivo.estado != 'clasificado':
            return Response({
                "error": "El archivo debe estar clasificado completamente para procesamiento final"
            }, status=400)
        
        try:
            # Crear cadena de tareas finales
            workflow = chain(
                actualizar_empleados_desde_novedades_task.s({"archivo_id": archivo.id}),
                guardar_registros_novedades_task.s()
            )
            
            # Ejecutar la cadena
            workflow.apply_async()
            
            return Response({
                "mensaje": "Procesamiento final iniciado",
                "estado": archivo.estado
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ChecklistItemViewSet(mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemUpdateSerializer


# Nuevos ViewSets para los modelos del Analista

class AnalistaFiniquitoViewSet(viewsets.ModelViewSet):
    queryset = AnalistaFiniquito.objects.all()
    serializer_class = AnalistaFiniquitoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        archivo_origen_id = self.request.query_params.get('archivo_origen')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if archivo_origen_id:
            queryset = queryset.filter(archivo_origen_id=archivo_origen_id)
        return queryset


class AnalistaIncidenciaViewSet(viewsets.ModelViewSet):
    queryset = AnalistaIncidencia.objects.all()
    serializer_class = AnalistaIncidenciaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        archivo_origen_id = self.request.query_params.get('archivo_origen')
        tipo_ausentismo = self.request.query_params.get('tipo_ausentismo')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if archivo_origen_id:
            queryset = queryset.filter(archivo_origen_id=archivo_origen_id)
        if tipo_ausentismo:
            queryset = queryset.filter(tipo_ausentismo__icontains=tipo_ausentismo)
        return queryset


class AnalistaIngresoViewSet(viewsets.ModelViewSet):
    queryset = AnalistaIngreso.objects.all()
    serializer_class = AnalistaIngresoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset


# ViewSets para modelos de Novedades

class EmpleadoCierreNovedadesViewSet(viewsets.ModelViewSet):
    queryset = EmpleadoCierreNovedades.objects.all()
    serializer_class = EmpleadoCierreNovedadesSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset


class ConceptoRemuneracionNovedadesViewSet(viewsets.ModelViewSet):
    queryset = ConceptoRemuneracionNovedades.objects.all()
    serializer_class = ConceptoRemuneracionNovedadesSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class RegistroConceptoEmpleadoNovedadesViewSet(viewsets.ModelViewSet):
    queryset = RegistroConceptoEmpleadoNovedades.objects.all()
    serializer_class = RegistroConceptoEmpleadoNovedadesSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(empleado__cierre_id=cierre_id)
        return queryset

# ======== VIEWSETS PARA SISTEMA DE INCIDENCIAS ========
# ⚠️ MIGRADO A views_incidencias.py ⚠️
# Las siguientes clases han sido migradas a views_incidencias.py:
# - IncidenciaCierreViewSet
# - ResolucionIncidenciaViewSet  
# - CierreNominaIncidenciasViewSet (integrado en IncidenciaCierreViewSet)
# 
# TODO: Eliminar las clases duplicadas de este archivo después de verificar que todo funciona correctamente

class IncidenciaCierreViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar incidencias de cierre de nómina"""
    queryset = IncidenciaCierre.objects.all()
    serializer_class = IncidenciaCierreSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Manejar tanto WSGIRequest (Django) como Request (DRF)
        if hasattr(self.request, 'query_params'):
            # Request de DRF
            cierre_id = self.request.query_params.get('cierre')
            estado = self.request.query_params.get('estado')
            prioridad = self.request.query_params.get('prioridad')
            asignado_a = self.request.query_params.get('asignado_a')
            tipo_comparacion = self.request.query_params.get('tipo_comparacion')
        else:
            # WSGIRequest de Django
            cierre_id = self.request.GET.get('cierre')
            estado = self.request.GET.get('estado')
            prioridad = self.request.GET.get('prioridad')
            asignado_a = self.request.GET.get('asignado_a')
            tipo_comparacion = self.request.GET.get('tipo_comparacion')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        if asignado_a:
            queryset = queryset.filter(asignado_a_id=asignado_a)
        if tipo_comparacion:
            queryset = queryset.filter(tipo_comparacion=tipo_comparacion)
            
        return queryset.select_related('cierre', 'asignado_a', 'resuelto_por', 'supervisor_revisor')
    
    @action(detail=False, methods=['post'], url_path='generar/(?P<cierre_id>[^/.]+)')
    def generar_incidencias(self, request, cierre_id=None):
        """
        🔍 ENDPOINT: Generar incidencias comparando datos consolidados
        
        Ejecuta la detección de incidencias entre el mes actual y anterior:
        1. Variaciones de conceptos >±30%
        2. Ausentismos continuos
        3. Ingresos del mes anterior faltantes
        4. Finiquitos del mes anterior presentes
        
        🆕 SISTEMA DUAL:
        - Procesamiento filtrado: Solo clasificaciones seleccionadas
        - Procesamiento completo: Todas las clasificaciones
        - Comparación cruzada: Validación de coherencia
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar que el cierre esté en un estado válido para generar incidencias
        estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas']
        if cierre.estado not in estados_validos:
            return Response({
                "error": "Estado incorrecto",
                "message": f"El cierre debe estar en estado válido para generar incidencias. Estado actual: {cierre.estado}",
                "estado_actual": cierre.estado,
                "estados_validos": estados_validos
            }, status=400)
        
        # 🆕 NUEVO: Usar el orquestador V2 (configuración automática de Pablo) SIEMPRE
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎯 Generando incidencias (V2) para cierre {cierre_id} - configuración automática")

        from .utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidados_v2
        task = generar_incidencias_consolidados_v2.delay(cierre_id)

        return Response({
            "message": "Generación de incidencias V2 iniciada",
            "descripcion": "Sistema dual: comparaciones individual (conceptos críticos) + suma total (todos) con umbral fijo 30%",
            "task_id": task.id,
            "cierre_id": cierre_id,
            "estado_cierre": cierre.estado,
            "modo_procesamiento": "dual_v2",
            "logger": "nomina.incidencias"
        }, status=202)

    @action(detail=False, methods=['post'], url_path='generar-simple/(?P<cierre_id>[^/.]+)')
    def generar_incidencias_simple(self, request, cierre_id=None):
        """🆕 ENDPOINT SIMPLE: Generar SOLO incidencias agregadas por concepto (umbral 30%).

        Usa la tarea Celery generar_incidencias_totales_simple. No crea incidencias
        por empleado ni variaciones individuales. Ideal para flujos rápidos.
        """
        from .models import CierreNomina
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        # Validar estado mínimo (igual que endpoint principal, pero más laxo se podría permitir)
        estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas']
        if cierre.estado not in estados_validos:
            return Response({
                "error": "Estado incorrecto",
                "message": f"El cierre debe estar en estado válido para generar incidencias simples. Estado actual: {cierre.estado}",
                "estado_actual": cierre.estado,
                "estados_validos": estados_validos
            }, status=400)

        # Lanzar tarea
        from .tasks import generar_incidencias_totales_simple
        task = generar_incidencias_totales_simple.delay(cierre.id)
        return Response({
            "message": "Generación simple de incidencias iniciada",
            "task_id": task.id,
            "cierre_id": cierre_id,
            "modo_procesamiento": "suma_total_simple",
            "descripcion": "Comparación de totales por concepto vs período anterior (umbral 30%)"
        }, status=202)

    @action(detail=True, methods=['post'], url_path='confirmar-desaparicion')
    def confirmar_desaparicion(self, request, pk=None):
        """Confirma como cerrada una incidencia marcada como resolucion_supervisor_pendiente (caso desaparecida)."""
        try:
            inc = self.get_object()
            if inc.estado != 'resolucion_supervisor_pendiente':
                return Response({"error": "La incidencia no está pendiente de confirmación"}, status=400)
            if not request.user.puede_supervisar_analista():
                return Response({"error": "Solo supervisor puede confirmar desapariciones"}, status=403)
            inc.estado = 'aprobada_supervisor'
            inc.save(update_fields=['estado'])
            # Nota del sistema
            from .models import ResolucionIncidencia
            ResolucionIncidencia.objects.create(
                incidencia=inc,
                usuario=request.user,
                tipo_resolucion='aprobacion',
                comentario='Confirmada desaparición tras recarga (reconciliación)'
            )
            return Response({"success": True})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='confirmar-desapariciones/(?P<cierre_id>[^/.]+)')
    def confirmar_desapariciones_masivo(self, request, cierre_id=None):
        """Confirma en bloque todas las incidencias de un cierre en estado resolucion_supervisor_pendiente."""
        try:
            if not request.user.puede_supervisar_analista():
                return Response({"error": "Solo supervisor puede confirmar desapariciones"}, status=403)
            qs = IncidenciaCierre.objects.filter(cierre_id=cierre_id, estado='resolucion_supervisor_pendiente')
            count = 0
            from .models import ResolucionIncidencia
            for inc in qs.iterator():
                inc.estado = 'aprobada_supervisor'
                inc.save(update_fields=['estado'])
                ResolucionIncidencia.objects.create(
                    incidencia=inc,
                    usuario=request.user,
                    tipo_resolucion='aprobacion',
                    comentario='Confirmación masiva de desapariciones (reconciliación)'
                )
                count += 1
            return Response({"success": True, "confirmadas": count})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['delete'], url_path='limpiar/(?P<cierre_id>[^/.]+)')
    def limpiar_incidencias(self, request, cierre_id=None):
        """
        🗑️ ENDPOINT: Limpiar incidencias de un cierre (función de debug)
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            incidencias_borradas = IncidenciaCierre.objects.filter(cierre=cierre).count()
            IncidenciaCierre.objects.filter(cierre=cierre).delete()
            
            # Resetear estado de incidencias
            cierre.estado_incidencias = 'pendiente'
            cierre.total_incidencias = 0
            cierre.save(update_fields=['estado_incidencias', 'total_incidencias'])
            
            return Response({
                "message": f"✅ {incidencias_borradas} incidencias limpiadas del cierre {cierre_id}",
                "incidencias_borradas": incidencias_borradas,
                "nuevo_estado": cierre.estado_incidencias
            }, status=200)
            
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": f"Error limpiando incidencias: {str(e)}"}, status=500)
    
    @action(detail=False, methods=['get'], url_path='analisis-completo/(?P<cierre_id>[^/.]+)')
    def analisis_completo_temporal(self, request, cierre_id=None):
        """
        🔍 ENDPOINT: Análisis completo de comparación temporal
        
        Muestra TODAS las comparaciones vs período anterior, no solo incidencias:
        1. Todas las variaciones de conceptos (incluso <30%)
        2. Todos los ausentismos continuos
        3. Todos los ingresos del mes anterior
        4. Todos los finiquitos del mes anterior
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar que el cierre esté consolidado
        if cierre.estado != 'datos_consolidados':
            return Response({
                "error": "Estado incorrecto",
                "message": f"El cierre debe estar en 'datos_consolidados' para análisis completo. Estado actual: {cierre.estado}",
                "estado_actual": cierre.estado,
                "estado_requerido": "datos_consolidados"
            }, status=400)
        
        try:
            from .utils.AnalisisCompletoIncidencias import generar_analisis_completo_temporal
            analisis = generar_analisis_completo_temporal(cierre)
            
            return Response({
                "success": True,
                "cierre_id": cierre_id,
                "analisis": analisis,
                "mensaje": "✅ Análisis temporal completo generado exitosamente"
            }, status=200)
            
        except Exception as e:
            logger.error(f"Error generando análisis completo para cierre {cierre_id}: {e}")
            return Response({
                "error": "Error interno",
                "message": f"Error generando análisis completo: {str(e)}"
            }, status=500)
    
    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar_cierre(self, request, pk=None):
        """
        🎯 ENDPOINT: Finalizar cierre y generar informes (vía Celery chord)

        - Valida estado y ausencia de incidencias pendientes
        - Dispara chord: [build_informe_libro, build_informe_movimientos] -> unir_y_guardar_informe -> finalizar_cierre_post_informe
        - Devuelve 202 con task_id para seguimiento
        """
        cierre_id = pk
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        # Verificar permisos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)

        # Verificar que el cierre esté listo para finalizar
        if cierre.estado != 'incidencias_resueltas':
            return Response({
                "error": "Estado incorrecto",
                "message": f"El cierre debe estar en 'incidencias_resueltas' para ser finalizado. Estado actual: {cierre.estado}",
                "estado_actual": cierre.estado,
                "estados_permitidos": ["incidencias_resueltas"],
                "estado_incidencias": getattr(cierre, 'estado_incidencias', 'no_definido'),
                "total_incidencias": getattr(cierre, 'total_incidencias', 0)
            }, status=400)

        # Verificar que no hay incidencias pendientes
        incidencias_pendientes = cierre.incidencias.filter(
            estado__in=['pendiente', 'en_revision']
        ).count()

        if incidencias_pendientes > 0:
            return Response({
                "error": "Incidencias pendientes",
                "message": f"Hay {incidencias_pendientes} incidencias pendientes de resolución",
                "incidencias_pendientes": incidencias_pendientes,
                "accion_requerida": "Resolver todas las incidencias antes de finalizar"
            }, status=400)

        # Validar precondición: consolidación existente
        if not cierre.nomina_consolidada.exists():
            return Response(
                {
                    'error': 'No hay datos consolidados para este cierre. Ejecute consolidación antes de finalizar.'
                },
                status=409
            )

        # Disparar chord de generación de informe y finalización
        try:
            from celery import chord
            from .tasks import (
                build_informe_libro,
                build_informe_movimientos,
                unir_y_guardar_informe,
                calcular_kpis_cierre,
                enviar_informe_redis_task,
                finalizar_cierre_post_informe,
            )

            tasks = [
                build_informe_libro.s(cierre_id),
                build_informe_movimientos.s(cierre_id),
            ]
            callback_guardar = unir_y_guardar_informe.s(cierre_id)
            callback_en_redis = enviar_informe_redis_task.s(cierre_id, ttl_hours=72)
            callback_final = finalizar_cierre_post_informe.s(cierre_id, getattr(request.user, 'id', None))

            # Encadenar: chord(tasks)(guardar informe unificado -> enviar a redis -> finalizar)
            result = chord(tasks)(callback_guardar | callback_en_redis | callback_final)

            return Response(
                {
                    'success': True,
                    'message': 'Finalización iniciada. Generando informe y cerrando.',
                    'cierre_id': cierre_id,
                    'task_id': getattr(result, 'id', None)
                },
                status=202
            )
        except Exception as e:
            return Response({
                "error": "Error interno",
                "message": f"Error al iniciar finalización: {str(e)}"
            }, status=500)
    
    @action(detail=False, methods=['get'], url_path='informe/(?P<cierre_id>[^/.]+)')
    def obtener_informe_cierre(self, request, cierre_id=None):
        """
        📊 ENDPOINT: Obtener informe comprehensivo de un cierre finalizado
        
        Retorna el informe completo con todas las métricas de RRHH
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que el cierre esté finalizado
        if cierre.estado != 'finalizado':
            return Response({
                "error": "Cierre no finalizado",
                "message": "El informe solo está disponible para cierres finalizados",
                "estado_actual": cierre.estado
            }, status=400)
        
        # Verificar que existe el informe
        if not cierre.tiene_informe:
            return Response({
                "error": "Informe no encontrado",
                "message": "No se ha generado informe para este cierre"
            }, status=404)
        
        # Obtener el informe
        informe = cierre.informe
        
        return Response({
            "success": True,
            "informe": {
                "id": informe.id,
                "cierre_id": cierre.id,
                "periodo": str(cierre.periodo),
                "cliente": cierre.cliente.nombre,
                "fecha_generacion": informe.fecha_generacion,
                "version_calculo": informe.version_calculo,
                "tiempo_calculo": str(informe.tiempo_calculo) if informe.tiempo_calculo else None,
                
                # Datos del informe
                "datos_cierre": informe.datos_cierre
            }
        }, status=200)
    
    @action(detail=False, methods=['get'], url_path='informe-resumen/(?P<cierre_id>[^/.]+)')
    def obtener_resumen_informe(self, request, cierre_id=None):
        """
        📊 ENDPOINT: Obtener solo el resumen ejecutivo del informe (KPIs principales)
        
        Versión ligera para dashboards o vistas rápidas
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        if not cierre.tiene_informe:
            return Response({
                "error": "Informe no encontrado",
                "message": "No se ha generado informe para este cierre"
            }, status=404)
        
        informe = cierre.informe
        
        return Response({
            "success": True,
            "resumen": {
                "periodo": str(cierre.periodo),
                "cliente": cierre.cliente.nombre,
                "fecha_generacion": informe.fecha_generacion,
                "metricas_basicas": informe.datos_cierre.get('metricas_basicas', {}),
                "movimientos": informe.datos_cierre.get('movimientos', {}),
                "afp_isapre": informe.datos_cierre.get('afp_isapre', [])
            }
        }, status=200)
        
        # CÓDIGO ORIGINAL COMENTADO:
        # try:
        #     cierre = CierreNomina.objects.get(id=cierre_id)
        # except CierreNomina.DoesNotExist:
        #     return Response({"error": "Cierre no encontrado"}, status=404)
        # 
        # # Verificar permisos básicos
        # if not request.user.is_authenticated:
        #     return Response({"error": "Usuario no autenticado"}, status=401)
        # 
        # # FALTA: Verificar que discrepancias = 0 antes de generar incidencias
        # # FALTA: Implementar comparación contra mes anterior
        # 
        # # Lanzar tarea de generación de incidencias
        # task = generar_incidencias_cierre_task.delay(cierre_id)
        # 
        # return Response({
        #     "message": "Generación de incidencias iniciada",
        #     "task_id": task.id,
        #     "cierre_id": cierre_id
        # }, status=202)
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cierre_id>[^/.]+)')
    def resumen_incidencias(self, request, cierre_id=None):
        """Obtiene un resumen estadístico de incidencias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        from .utils.GenerarIncidencias import obtener_resumen_incidencias
        resumen = obtener_resumen_incidencias(cierre)
        
        serializer = ResumenIncidenciasSerializer(resumen)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar el estado de una incidencia específica"""
        incidencia = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in ['pendiente', 'resuelta_analista', 'aprobada_supervisor', 'rechazada_supervisor']:
            return Response({"error": "Estado inválido"}, status=400)
        
        incidencia.estado = nuevo_estado
        incidencia.save(update_fields=['estado'])
        
        return Response({"message": "Estado actualizado", "estado": nuevo_estado})
    
    @action(detail=True, methods=['patch'])
    def asignar_usuario(self, request, pk=None):
        """Asignar una incidencia a un usuario específico"""
        incidencia = self.get_object()
        usuario_id = request.data.get('usuario_id')
        
        if usuario_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                usuario = User.objects.get(id=usuario_id)
                incidencia.asignado_a = usuario
                incidencia.save(update_fields=['asignado_a'])
                return Response({"message": "Incidencia asignada correctamente"})
            except User.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=404)
        else:
            incidencia.asignado_a = None
            incidencia.save(update_fields=['asignado_a'])
            return Response({"message": "Asignación removida"})
    
    @action(detail=False, methods=['post'], url_path='dev-clear/(?P<cierre_id>[^/.]+)')
    def dev_clear_incidencias(self, request, cierre_id=None):
        """
        ⚠️ ENDPOINT DE DESARROLLO ÚNICAMENTE ⚠️
        Elimina todas las incidencias de un cierre para testing del flujo de consolidación.
        ¡¡¡REMOVER ANTES DE PRODUCCIÓN!!!
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Eliminar todas las incidencias del cierre
        deleted_count = IncidenciaCierre.objects.filter(cierre=cierre).delete()[0]
        
        # Actualizar el estado de incidencias del cierre
        cierre.estado_incidencias = 'resueltas'
        cierre.estado = 'finalizado'
        cierre.save(update_fields=['estado_incidencias', 'estado'])
        
        logger.info(f"DEV: Eliminadas {deleted_count} incidencias del cierre {cierre_id}")
        
        return Response({
            "message": f"⚠️ DEV: Eliminadas {deleted_count} incidencias. Estado: {cierre.estado}, Incidencias: {cierre.estado_incidencias}",
            "incidencias_eliminadas": deleted_count,
            "nuevo_estado": cierre.estado,
            "estado_incidencias": cierre.estado_incidencias
        })

    @action(detail=False, methods=['post'], url_path='analizar-datos/(?P<cierre_id>[^/.]+)')
    def analizar_datos(self, request, cierre_id=None):
        """Endpoint para iniciar análisis de datos del cierre"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que el cierre esté en estado finalizado y archivos consolidados
        if cierre.estado != 'finalizado':
            return Response({
                "error": "El cierre debe estar en estado 'finalizado' para iniciar análisis"
            }, status=400)
        
        if cierre.estado_incidencias != 'resueltas':
            return Response({
                "error": "El cierre debe tener incidencias resueltas (0 incidencias) para iniciar análisis"
            }, status=400)
        
        # Obtener tolerancia de variación (por defecto 30%)
        tolerancia_variacion = float(request.data.get('tolerancia_variacion', 30.0))
        
        # Validar tolerancia
        if tolerancia_variacion < 0 or tolerancia_variacion > 100:
            return Response({
                "error": "La tolerancia de variación debe estar entre 0 y 100"
            }, status=400)
        
        # Lanzar tarea de análisis
        from .tasks import analizar_datos_cierre_task
        task = analizar_datos_cierre_task.delay(cierre_id, tolerancia_variacion)
        
        return Response({
            "message": "Análisis de datos iniciado",
            "task_id": task.id,
            "cierre_id": cierre_id,
            "tolerancia_variacion": tolerancia_variacion
        }, status=202)

    @action(detail=False, methods=['get'], url_path='preview/(?P<cierre_id>[^/.]+)')
    def preview_incidencias(self, request, cierre_id=None):
        """Endpoint para previsualizar qué incidencias se generarían sin crearlas"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        from .utils.GenerarIncidencias import (
            generar_incidencias_libro_vs_novedades,
            generar_incidencias_movimientos_vs_analista
        )
        
        try:
            # Generar incidencias preview sin guardarlas
            incidencias_libro_novedades = generar_incidencias_libro_vs_novedades(cierre)
            incidencias_movimientos_analista = generar_incidencias_movimientos_vs_analista(cierre)
            
            todas_incidencias = incidencias_libro_novedades + incidencias_movimientos_analista
            
            # Convertir incidencias a formato serializable
            incidencias_preview = []
            for incidencia in todas_incidencias:
                incidencias_preview.append({
                    'tipo_incidencia': incidencia.tipo_incidencia,
                    'rut_empleado': incidencia.rut_empleado,
                    'descripcion': incidencia.descripcion,
                    'prioridad': incidencia.prioridad,
                    'concepto_afectado': incidencia.concepto_afectado,
                    'valor_libro': incidencia.valor_libro,
                    'valor_novedades': incidencia.valor_novedades,
                    'impacto_monetario': float(incidencia.impacto_monetario or 0),
                })
            
            return Response({
                'total_incidencias': len(todas_incidencias),
                'libro_vs_novedades': len(incidencias_libro_novedades),
                'movimientos_vs_analista': len(incidencias_movimientos_analista),
                'incidencias': incidencias_preview,
                'mensaje': 'Vista previa generada - no se guardaron incidencias'
            })
            
        except Exception as e:
            logger.error(f"Error generando preview de incidencias: {e}")
            return Response({
                "error": f"Error generando preview: {str(e)}"
            }, status=500)

    @action(detail=False, methods=['get'], url_path='mi-turno')
    def mi_turno(self, request):
        """
        Obtiene las incidencias que el usuario actual debe atender según el flujo de conversación
        """
        from django.db.models import Prefetch, OuterRef, Subquery
        
        # Obtener todas las incidencias con sus resoluciones
        incidencias = IncidenciaCierre.objects.prefetch_related(
            'resoluciones'
        ).filter(estado__in=['pendiente', 'resuelta_analista']).order_by('-fecha_ultima_accion')
        
        mi_turno = []
        
        for incidencia in incidencias:
            resoluciones = list(incidencia.resoluciones.all().order_by('fecha_resolucion'))
            
            # Determinar el estado de la conversación según la nueva arquitectura
            if not resoluciones:
                # INICIANDO: Sin mensajes → Turno del Analista
                if not (request.user.is_staff or request.user.is_superuser):
                    mi_turno.append({
                        'incidencia': incidencia,
                        'estado_conversacion': 'turno_analista',
                        'accion_requerida': 'Crear justificación inicial'
                    })
            else:
                ultima_resolucion = resoluciones[-1]
                
                # RESUELTA: Último mensaje es aprobación → Conversación terminada
                if ultima_resolucion.tipo_resolucion == 'aprobacion':
                    continue  # No requiere acción
                    
                # Determinar turno basado en el último mensaje
                es_del_supervisor = ultima_resolucion.tipo_resolucion in ['consulta', 'rechazo']
                
                if es_del_supervisor:
                    # TURNO_ANALISTA: Último mensaje fue de supervisor → Analista debe responder
                    if not (request.user.is_staff or request.user.is_superuser):
                        accion = 'Responder consulta' if ultima_resolucion.tipo_resolucion == 'consulta' else 'Nueva justificación'
                        mi_turno.append({
                            'incidencia': incidencia,
                            'estado_conversacion': 'turno_analista',
                            'accion_requerida': accion,
                            'ultimo_mensaje': {
                                'tipo': ultima_resolucion.tipo_resolucion,
                                'comentario': ultima_resolucion.comentario,
                                'usuario': ultima_resolucion.usuario.get_full_name(),
                                'fecha': ultima_resolucion.fecha_resolucion
                            }
                        })
                else:
                    # TURNO_SUPERVISOR: Último mensaje fue de analista → Supervisor debe decidir
                    if request.user.is_staff or request.user.is_superuser:
                        mi_turno.append({
                            'incidencia': incidencia,
                            'estado_conversacion': 'turno_supervisor',
                            'accion_requerida': 'Revisar y decidir (aprobar/rechazar/consultar)',
                            'ultimo_mensaje': {
                                'tipo': ultima_resolucion.tipo_resolucion,
                                'comentario': ultima_resolucion.comentario,
                                'usuario': ultima_resolucion.usuario.get_full_name(),
                                'fecha': ultima_resolucion.fecha_resolucion
                            }
                        })
        
        # Serializar las incidencias
        incidencias_data = []
        for item in mi_turno:
            incidencia_serializer = IncidenciaCierreSerializer(item['incidencia'])
            incidencias_data.append({
                **incidencia_serializer.data,
                'estado_conversacion': item['estado_conversacion'],
                'accion_requerida': item['accion_requerida'],
                'ultimo_mensaje': item.get('ultimo_mensaje')
            })
        
        return Response({
            'total': len(incidencias_data),
            'usuario': {
                'id': request.user.id,
                'nombre': request.user.get_full_name(),
                'es_supervisor': request.user.is_staff or request.user.is_superuser
            },
            'incidencias': incidencias_data
        })

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprobar una incidencia de cierre"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        # Verificar permisos básicos de autenticación
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar permisos de supervisor
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden aprobar incidencias"}, status=403)
        
        try:
            # Crear resolución de aprobación
            from .models import ResolucionIncidencia
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='aprobacion',
                comentario=comentario or 'Incidencia aprobada',
            )
            
            # Cambiar estado de la incidencia
            incidencia.estado = 'aprobada'
            incidencia.asignado_a = request.user
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'asignado_a', 'fecha_ultima_accion'])
            
            logger.info(f"✅ Incidencia {incidencia.id} aprobada por {request.user.correo_bdo}")
            
            return Response({
                "message": "Incidencia aprobada correctamente",
                "estado": incidencia.estado,
                "fecha_aprobacion": incidencia.fecha_ultima_accion,
                "resolucion_id": resolucion.id
            })
            
        except Exception as e:
            logger.error(f"Error aprobando incidencia {pk}: {e}")
            return Response({"error": f"Error aprobando incidencia: {str(e)}"}, status=500)
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechazar una incidencia de cierre"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        if not comentario:
            return Response({"error": "El comentario es requerido para rechazar"}, status=400)
        
        # Verificar permisos básicos de autenticación
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar permisos de supervisor
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden rechazar incidencias"}, status=403)
        
        try:
            # Crear resolución de rechazo
            from .models import ResolucionIncidencia
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='rechazo',
                comentario=comentario,
            )
            
            # Cambiar estado de la incidencia a pendiente (para re-justificación)
            incidencia.estado = 'pendiente'
            incidencia.asignado_a = None  # Liberar asignación para que analista pueda volver a justificar
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'asignado_a', 'fecha_ultima_accion'])
            
            logger.info(f"❌ Incidencia {incidencia.id} rechazada por {request.user.correo_bdo}")
            
            return Response({
                "message": "Incidencia rechazada correctamente",
                "estado": incidencia.estado,
                "fecha_rechazo": incidencia.fecha_ultima_accion,
                "resolucion_id": resolucion.id,
                "motivo": comentario
            })
            
        except Exception as e:
            logger.error(f"Error rechazando incidencia {pk}: {e}")
            return Response({"error": f"Error rechazando incidencia: {str(e)}"}, status=500)

class ResolucionIncidenciaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar resoluciones de incidencias"""
    queryset = ResolucionIncidencia.objects.all()
    serializer_class = ResolucionIncidenciaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        incidencia_id = self.request.query_params.get('incidencia')
        usuario_id = self.request.query_params.get('usuario')
        
        if incidencia_id:
            queryset = queryset.filter(incidencia_id=incidencia_id)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
            
        return queryset.select_related('incidencia', 'usuario').order_by('-fecha_creacion')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearResolucionSerializer
        return ResolucionIncidenciaSerializer
    
    def perform_create(self, serializer):
        """
        Crear una nueva resolución con arquitectura simplificada
        """
        # Con el nuevo serializer, la validación se hace automáticamente
        serializer.save(usuario=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='historial/(?P<incidencia_id>[^/.]+)')
    def historial_incidencia(self, request, incidencia_id=None):
        """Obtiene el historial completo de resoluciones de una incidencia"""
        try:
            incidencia = IncidenciaCierre.objects.get(id=incidencia_id)
        except IncidenciaCierre.DoesNotExist:
            return Response({"error": "Incidencia no encontrada"}, status=404)
        
        resoluciones = ResolucionIncidencia.objects.filter(
            incidencia=incidencia
        ).select_related('usuario').order_by('fecha_resolucion')
        
        serializer = ResolucionIncidenciaSerializer(resoluciones, many=True)
        
        # Información adicional sobre el estado de la conversación
        estado_conversacion = self._obtener_estado_conversacion(incidencia, resoluciones)
        
        return Response({
            "incidencia_id": incidencia_id,
            "resoluciones": serializer.data,
            "total_resoluciones": resoluciones.count(),
            "estado_actual": incidencia.estado,
            "estado_conversacion": estado_conversacion,
            "puede_aprobar": request.user.is_staff or request.user.is_superuser,
            "puede_resolver": True  # Todos pueden agregar comentarios/justificaciones
        })
    
    def _obtener_nombre_usuario(self, usuario):
        """Obtiene el correo del usuario para identificación"""
        return usuario.correo_bdo
    
    def _obtener_estado_conversacion(self, incidencia, resoluciones):
        """Determina el estado de la conversación para la UI"""
        if not resoluciones.exists():
            return {
                "estado": "pendiente_analista",
                "mensaje": "Esperando justificación del analista",
                "accion_siguiente": "El analista debe justificar esta incidencia"
            }
        
        ultima_resolucion = resoluciones.last()
        
        if incidencia.estado == 'resuelta_analista':
            return {
                "estado": "esperando_supervisor",
                "mensaje": "Esperando revisión del supervisor",
                "accion_siguiente": "El supervisor debe aprobar o rechazar la justificación",
                "ultima_accion": f"Justificada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        elif incidencia.estado == 'rechazada_supervisor':
            return {
                "estado": "rechazada",
                "mensaje": "Justificación rechazada por supervisor",
                "accion_siguiente": "El analista debe mejorar la justificación o corregir en Talana",
                "ultima_accion": f"Rechazada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        elif incidencia.estado == 'aprobada_supervisor':
            return {
                "estado": "aprobada",
                "mensaje": "Incidencia resuelta y aprobada",
                "accion_siguiente": "No se requieren más acciones",
                "ultima_accion": f"Aprobada por {self._obtener_nombre_usuario(ultima_resolucion.usuario)}"
            }
        else:
            return {
                "estado": "en_proceso",
                "mensaje": "Conversación en progreso",
                "accion_siguiente": "Continuar la conversación"
            }
    
    @action(detail=False, methods=['get'], url_path='pendientes-supervisor')
    def pendientes_supervisor(self, request):
        """
        Obtiene incidencias que requieren revisión del supervisor
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "Solo supervisores pueden acceder a esta vista"}, status=403)
        
        # Incidencias con justificaciones pendientes de revisión
        incidencias_pendientes = IncidenciaCierre.objects.filter(
            estado='resuelta_analista'
        ).select_related('cierre', 'cierre__cliente').prefetch_related(
            'resoluciones__usuario'
        ).order_by('-fecha_ultima_accion')
        
        data = []
        for incidencia in incidencias_pendientes:
            ultima_resolucion = incidencia.resoluciones.order_by('-fecha_resolucion').first()
            data.append({
                'id': incidencia.id,
                'rut_empleado': incidencia.rut_empleado,
                'tipo_incidencia': incidencia.get_tipo_incidencia_display(),
                'descripcion': incidencia.descripcion[:100] + '...' if len(incidencia.descripcion) > 100 else incidencia.descripcion,
                'prioridad': incidencia.prioridad,
                'cierre': {
                    'id': incidencia.cierre.id,
                    'cliente': incidencia.cierre.cliente.nombre,
                    'periodo': incidencia.cierre.periodo
                },
                'ultima_justificacion': {
                    'fecha': ultima_resolucion.fecha_resolucion if ultima_resolucion else None,
                    'usuario': self._obtener_nombre_usuario(ultima_resolucion.usuario) if ultima_resolucion else None,
                    'comentario': ultima_resolucion.comentario[:100] + '...' if ultima_resolucion and len(ultima_resolucion.comentario) > 100 else ultima_resolucion.comentario if ultima_resolucion else None
                },
                'fecha_ultima_accion': incidencia.fecha_ultima_accion,
                'impacto_monetario': incidencia.impacto_monetario
            })
        
        return Response({
            'incidencias_pendientes': data,
            'total': len(data),
            'resumen': {
                'alta_prioridad': len([i for i in data if i['prioridad'] == 'alta']),
                'media_prioridad': len([i for i in data if i['prioridad'] == 'media']),
                'baja_prioridad': len([i for i in data if i['prioridad'] == 'baja'])
            }
        })
    
    @action(detail=False, methods=['get'], url_path='mis-pendientes')
    def mis_pendientes(self, request):
        """
        Obtiene incidencias asignadas al usuario actual o que requieren su atención
        """
        usuario = request.user
        
        # Incidencias asignadas directamente
        asignadas = IncidenciaCierre.objects.filter(
            asignado_a=usuario,
            estado__in=['pendiente', 'rechazada_supervisor']
        )
        
        # Si es supervisor, agregar las que esperan su revisión
        esperando_revision = []
        if usuario.is_staff or usuario.is_superuser:
            esperando_revision = IncidenciaCierre.objects.filter(
                estado='resuelta_analista'
            )
        
        # Combinar querysets
        from django.db.models import Q
        todas = IncidenciaCierre.objects.filter(
            Q(asignado_a=usuario, estado__in=['pendiente', 'rechazada_supervisor']) |
            Q(estado='resuelta_analista') if (usuario.is_staff or usuario.is_superuser) else Q()
        ).select_related('cierre', 'cierre__cliente').distinct().order_by('-fecha_ultima_accion')
        
        data = []
        for incidencia in todas:
            estado_para_usuario = self._determinar_estado_para_usuario(incidencia, usuario)
            data.append({
                'id': incidencia.id,
                'rut_empleado': incidencia.rut_empleado,
                'tipo_incidencia': incidencia.get_tipo_incidencia_display(),
                'descripcion': incidencia.descripcion,
                'prioridad': incidencia.prioridad,
                'estado_para_usuario': estado_para_usuario,
                'cierre': {
                    'id': incidencia.cierre.id,
                    'cliente': incidencia.cierre.cliente.nombre,
                    'periodo': incidencia.cierre.periodo
                },
                'fecha_ultima_accion': incidencia.fecha_ultima_accion,
                'total_resoluciones': incidencia.resoluciones.count()
            })
        
        return Response({
            'mis_incidencias': data,
            'total': len(data),
            'rol': 'supervisor' if (usuario.is_staff or usuario.is_superuser) else 'analista'
        })
    
    def _determinar_estado_para_usuario(self, incidencia, usuario):
        """Determina qué acción debe tomar el usuario en esta incidencia"""
        if incidencia.estado == 'pendiente' and incidencia.asignado_a == usuario:
            return "requiere_justificacion"
        elif incidencia.estado == 'rechazada_supervisor' and incidencia.asignado_a == usuario:
            return "requiere_mejora_justificacion"
        elif incidencia.estado == 'resuelta_analista' and (usuario.is_staff or usuario.is_superuser):
            return "requiere_revision_supervisor"
        elif incidencia.estado == 'aprobada_supervisor':
            return "aprobada"
        else:
            return "en_proceso"


# ======== ENDPOINTS ADICIONALES PARA CIERRE NOMINA ========

# Agregar action al CierreNominaViewSet existente para manejo de incidencias
# (Se puede agregar como mixin o extender el ViewSet existente)

class CierreNominaIncidenciasViewSet(viewsets.ViewSet):
    """ViewSet adicional para operaciones de incidencias en cierres"""
    
    @action(detail=True, methods=['get'])
    def estado_incidencias(self, request, pk=None):
        """Obtiene el estado de incidencias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(pk=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        incidencias = cierre.incidencias.all()
        
        # Estadísticas por estado
        estados = {}
        for incidencia in incidencias:
            estado = incidencia.estado
            estados[estado] = estados.get(estado, 0) + 1
        
        # Estadísticas por prioridad
        prioridades = {}
        for incidencia in incidencias:
            prioridad = incidencia.prioridad
            prioridades[prioridad] = prioridades.get(prioridad, 0) + 1
        
        return Response({
            'cierre_id': pk,
            'total_incidencias': incidencias.count(),
            'estados': estados,
            'prioridades': prioridades,
            'puede_finalizar': all(inc.estado == 'aprobada_supervisor' for inc in incidencias),
            'progreso': {
                'aprobadas': estados.get('aprobada_supervisor', 0),
                'pendientes': estados.get('pendiente', 0) + estados.get('resuelta_analista', 0),
                'rechazadas': estados.get('rechazada_supervisor', 0)
            }
        })
    
    @action(detail=True, methods=['post'], url_path='solicitar-recarga-archivos')
    def solicitar_recarga_archivos(self, request, pk=None):
        """
        Permite solicitar la recarga de archivos cuando hay incidencias
        que requieren corrección en Talana
        """
        try:
            cierre = CierreNomina.objects.get(pk=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que existan incidencias rechazadas o que justifiquen la recarga
        incidencias_rechazadas = cierre.incidencias.filter(
            resoluciones__tipo_resolucion='rechazo_supervisor'
        ).distinct().count()
        
        if incidencias_rechazadas == 0:
            return Response({
                "error": "No hay incidencias rechazadas que justifiquen recargar archivos"
            }, status=400)
        
        motivo = request.data.get('motivo', '')
        if not motivo:
            return Response({"error": "Debe proporcionar un motivo para la recarga"}, status=400)
        
        # Cambiar estado del cierre para permitir recarga
        cierre.estado = 'requiere_recarga_archivos'
        cierre.observaciones_recarga = f"Solicitado por {request.user.correo_bdo}: {motivo}"
        cierre.fecha_solicitud_recarga = timezone.now()
        cierre.save(update_fields=['estado', 'observaciones_recarga', 'fecha_solicitud_recarga'])
        
        # Registrar la solicitud en el historial (si existe modelo de historial)
        logger.info(f"🔄 Recarga de archivos solicitada para cierre {pk} por {request.user.correo_bdo}: {motivo}")
        
        return Response({
            "mensaje": "Solicitud de recarga de archivos registrada",
            "cierre_id": pk,
            "nuevo_estado": cierre.estado,
            "motivo": motivo,
            "incidencias_rechazadas": incidencias_rechazadas,
            "instrucciones": [
                "1. Corregir los datos en Talana según las incidencias rechazadas",
                "2. Volver a subir los archivos corregidos (Libro, Movimientos, etc.)",
                "3. El sistema re-consolidará automáticamente los datos",
                "4. Se generarán nuevas incidencias basadas en los datos actualizados"
            ]
        })
    
    @action(detail=True, methods=['post'], url_path='marcar-todas-como-justificadas')
    def marcar_todas_como_justificadas(self, request, pk=None):
        """
        Acción masiva para que un supervisor marque todas las incidencias
        como justificadas (para casos donde el analista ha explicado todo correctamente)
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({
                "error": "Solo supervisores pueden realizar aprobaciones masivas"
            }, status=403)
        
        try:
            cierre = CierreNomina.objects.get(pk=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Obtener incidencias que están esperando revisión del supervisor
        incidencias_pendientes = cierre.incidencias.filter(
            estado='resuelta_analista'
        )
        
        if not incidencias_pendientes.exists():
            return Response({
                "error": "No hay incidencias pendientes de aprobación"
            }, status=400)
        
        comentario_aprobacion = request.data.get('comentario', 'Aprobación masiva por supervisor')
        
        # Crear resolución de aprobación para cada incidencia
        resoluciones_creadas = []
        for incidencia in incidencias_pendientes:
            resolucion = ResolucionIncidencia.objects.create(
                incidencia=incidencia,
                usuario=request.user,
                tipo_resolucion='aprobacion',
                comentario=comentario_aprobacion,
                estado_anterior=incidencia.estado,
                estado_nuevo='aprobada_supervisor'
            )
            
            # Actualizar estado de la incidencia
            incidencia.estado = 'aprobada_supervisor'
            incidencia.fecha_ultima_accion = timezone.now()
            incidencia.save(update_fields=['estado', 'fecha_ultima_accion'])
            
            resoluciones_creadas.append(resolucion)
        
        # Verificar si todas las incidencias están aprobadas
        incidencias_restantes = cierre.incidencias.exclude(estado='aprobada_supervisor').count()
        
        if incidencias_restantes == 0:
            # Todas las incidencias están resueltas
            cierre.estado = 'incidencias_resueltas'
            cierre.estado_incidencias = 'resueltas'
            cierre.save(update_fields=['estado', 'estado_incidencias'])
        
        logger.info(f"✅ Aprobación masiva realizada por {request.user.correo_bdo} en cierre {pk}: {len(resoluciones_creadas)} incidencias aprobadas")
        
        return Response({
            "mensaje": f"{len(resoluciones_creadas)} incidencias aprobadas exitosamente",
            "incidencias_aprobadas": len(resoluciones_creadas),
            "incidencias_restantes": incidencias_restantes,
            "cierre_completado": incidencias_restantes == 0,
            "nuevo_estado_cierre": cierre.estado
        })
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        total_incidencias = cierre.incidencias.count()
        
        # Actualizar estado automáticamente según las incidencias
        if total_incidencias == 0:
            if cierre.estado_incidencias != 'resueltas':
                cierre.estado_incidencias = 'resueltas'
                cierre.save(update_fields=['estado_incidencias'])
        else:
            if cierre.estado_incidencias != 'detectadas':
                cierre.estado_incidencias = 'detectadas'
                cierre.save(update_fields=['estado_incidencias'])
        
        return Response({
            "cierre_id": cierre.id,
            "estado_incidencias": cierre.estado_incidencias,
            "tiene_incidencias": total_incidencias > 0,
            "total_incidencias": total_incidencias,
            "incidencias_pendientes": cierre.incidencias.exclude(
                id__in=cierre.incidencias.filter(
                    resoluciones__tipo_resolucion__in=[
                        'aprobacion_supervisor', 'rechazo_supervisor'
                    ]
                ).values('id')
            ).count(),
            "incidencias_resueltas": cierre.incidencias.filter(
                resoluciones__tipo_resolucion__in=[
                    'aprobacion_supervisor', 'justificacion_analista', 
                    'correccion_analista', 'consulta_analista'
                ]
            ).distinct().count()
        })
    
    @action(detail=True, methods=['post'])
    def lanzar_generacion_incidencias(self, request, pk=None):
        """Lanza la tarea de generación de incidencias para un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que el cierre esté en estado adecuado
        if cierre.estado not in ['verificacion_datos', 'verificado_sin_discrepancias', 'con_discrepancias', 'finalizado']:
            return Response({
                "error": f"El cierre debe estar en estado válido para generar incidencias. Estado actual: '{cierre.estado}'"
            }, status=400)
        
        # Lanzar tarea
        task = generar_incidencias_cierre_task.delay(pk)
        
        return Response({
            "message": "Generación de incidencias iniciada",
            "task_id": task.id,
            "cierre_id": pk
        }, status=202)

# ======== VIEWSETS PARA ANÁLISIS DE DATOS ========

class AnalisisDatosCierreViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar análisis de datos de cierre"""
    from .models import AnalisisDatosCierre
    from .serializers import AnalisisDatosCierreSerializer
    
    queryset = AnalisisDatosCierre.objects.all()
    serializer_class = AnalisisDatosCierreSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'analista')


class IncidenciaVariacionSalarialViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar incidencias de variación salarial"""
    from .models import IncidenciaVariacionSalarial
    from .serializers import IncidenciaVariacionSalarialSerializer
    
    queryset = IncidenciaVariacionSalarial.objects.all()
    serializer_class = IncidenciaVariacionSalarialSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        estado = self.request.query_params.get('estado')
        analista_id = self.request.query_params.get('analista')
        supervisor_id = self.request.query_params.get('supervisor')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if analista_id:
            queryset = queryset.filter(analista_asignado_id=analista_id)
        if supervisor_id:
            queryset = queryset.filter(supervisor_revisor_id=supervisor_id)
            
        return queryset.select_related('cierre', 'analista_asignado', 'supervisor_revisor')
    
    @action(detail=True, methods=['post'])
    def justificar(self, request, pk=None):
        """Justificar una incidencia de variación salarial"""
        incidencia = self.get_object()
        justificacion = request.data.get('justificacion', '').strip()
        
        if not justificacion:
            return Response({"error": "La justificación es requerida"}, status=400)
        
        if not incidencia.puede_justificar(request.user):
            return Response({"error": "No tiene permisos para justificar esta incidencia"}, status=403)
        
        # Justificar la incidencia
        success = incidencia.marcar_como_justificada(request.user, justificacion)
        
        if success:
            return Response({
                "message": "Incidencia justificada correctamente",
                "estado": incidencia.estado,
                "fecha_justificacion": incidencia.fecha_justificacion
            })
        else:
            return Response({"error": "No se pudo justificar la incidencia"}, status=400)
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """Aprobar una incidencia de variación salarial"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        if not incidencia.puede_resolver(request.user):
            return Response({"error": "No tiene permisos para aprobar esta incidencia"}, status=403)
        
        # Aprobar la incidencia
        success = incidencia.aprobar(request.user, comentario)
        
        if success:
            return Response({
                "message": "Incidencia aprobada correctamente",
                "estado": incidencia.estado,
                "fecha_resolucion": incidencia.fecha_resolucion_supervisor
            })
        else:
            return Response({"error": "No se pudo aprobar la incidencia"}, status=400)
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """Rechazar una incidencia de variación salarial"""
        incidencia = self.get_object()
        comentario = request.data.get('comentario', '').strip()
        
        if not comentario:
            return Response({"error": "El comentario es requerido para rechazar"}, status=400)
        
        if not incidencia.puede_resolver(request.user):
            return Response({"error": "No tiene permisos para rechazar esta incidencia"}, status=403)
        
        # Rechazar la incidencia
        success = incidencia.rechazar(request.user, comentario)
        
        if success:
            return Response({
                "message": "Incidencia rechazada correctamente",
                "estado": incidencia.estado,
                "fecha_resolucion": incidencia.fecha_resolucion_supervisor
            })
        else:
            return Response({"error": "No se pudo rechazar la incidencia"}, status=400)
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cierre_id>[^/.]+)')
    def resumen_variaciones(self, request, cierre_id=None):
        """Obtiene un resumen de las incidencias de variación salarial"""
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Contar incidencias por estado
        incidencias = self.get_queryset().filter(cierre=cierre)
        
        resumen = {
            "total": incidencias.count(),
            "por_estado": {
                "pendiente": incidencias.filter(estado='pendiente').count(),
                "en_analisis": incidencias.filter(estado='en_analisis').count(),
                "justificado": incidencias.filter(estado='justificado').count(),
                "aprobado": incidencias.filter(estado='aprobado').count(),
                "rechazado": incidencias.filter(estado='rechazado').count(),
            },
            "por_tipo": {
                "aumento": incidencias.filter(tipo_variacion='aumento').count(),
                "disminucion": incidencias.filter(tipo_variacion='disminucion').count(),
            }
        }
        
        return Response(resumen)




# ===== VIEWSETS PARA SISTEMA DE DISCREPANCIAS (VERIFICACIÓN DE DATOS) =====
# ✅ REFACTORIZADO: ViewSets movidos a views_discrepancias.py
# Importar desde el nuevo archivo para mantener compatibilidad con URLs
from .views_discrepancias import (
    DiscrepanciaCierreViewSet,
    CierreNominaDiscrepanciasViewSet
)


# ========== UPLOAD LOG ENDPOINTS ==========

@api_view(['GET'])
def obtener_estado_upload_log_nomina(request, upload_log_id):
    """
    Obtiene el estado actual de un UploadLogNomina específico
    """
    from .models_logging_stub import UploadLogNomina
    from rest_framework.response import Response
    from rest_framework import status
    
    try:
        upload_log = UploadLogNomina.objects.get(id=upload_log_id)
        
        data = {
            'id': upload_log.id,
            'estado': upload_log.estado,
            'tipo_upload': upload_log.tipo_upload,
            'nombre_archivo_original': upload_log.nombre_archivo_original,
            'fecha_subida': upload_log.fecha_subida,
            'errores': upload_log.errores,
            'resumen': upload_log.resumen or {},
            'registros_procesados': upload_log.registros_procesados,
            'registros_exitosos': upload_log.registros_exitosos,
            'registros_fallidos': upload_log.registros_fallidos,
            'headers_detectados': upload_log.headers_detectados,
            'tiempo_procesamiento': upload_log.tiempo_procesamiento,
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except UploadLogNomina.DoesNotExist:
        return Response(
            {'error': 'Upload log no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def obtener_libro_remuneraciones(request, cierre_id):
    """
    📋 LIBRO DE REMUNERACIONES CONSOLIDADO
    
    Devuelve el libro de remuneraciones con toda la información consolidada:
    - Empleados con sus datos básicos
    - Headers con valores por empleado
    - Conceptos consolidados
    """
    try:
        # Obtener el cierre y verificar permisos
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar que hay datos consolidados
        if not cierre.nomina_consolidada.exists():
            return Response({
                'error': 'No hay datos consolidados para este cierre',
                'mensaje': 'Debe ejecutar la consolidación antes de ver el libro de remuneraciones'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Importar modelos aquí para evitar import circular
        from .models import NominaConsolidada, HeaderValorEmpleado, ConceptoConsolidado
        
        # Obtener empleados consolidados
        empleados = NominaConsolidada.objects.filter(cierre=cierre).order_by('nombre_empleado')
        
        # Datos principales del cierre
        data = {
            'cierre': {
                'id': cierre.id,
                'cliente': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': cierre.estado,
                'fecha_consolidacion': cierre.fecha_consolidacion,
            },
            'resumen': {
                'total_empleados': empleados.count(),
                # Calcular total haberes como suma de ambas categorías
                'total_haberes': sum((emp.haberes_imponibles or 0) + (emp.haberes_no_imponibles or 0) for emp in empleados),
                'total_descuentos': sum((emp.dctos_legales or 0) + (emp.otros_dctos or 0) + (emp.impuestos or 0) for emp in empleados),
                'liquido_total': sum(((emp.haberes_imponibles or 0) + (emp.haberes_no_imponibles or 0)) - ((emp.dctos_legales or 0) + (emp.otros_dctos or 0) + (emp.impuestos or 0)) for emp in empleados),
            },
            'empleados': []
        }
        
        # Obtener todos los headers únicos para crear columnas
        headers_unicos = HeaderValorEmpleado.objects.filter(
            nomina_consolidada__cierre=cierre
        ).values_list('nombre_header', flat=True).distinct().order_by('nombre_header')
        
        data['headers'] = list(headers_unicos)
        
        # Construir datos por empleado
        for empleado in empleados:
            # Obtener header-valores para este empleado
            header_valores = HeaderValorEmpleado.objects.filter(
                nomina_consolidada=empleado
            ).order_by('nombre_header')
            
            # Crear diccionario de valores por header
            valores_headers = {hv.nombre_header: hv.valor_original for hv in header_valores}
            
            # Obtener conceptos consolidados para este empleado
            conceptos = ConceptoConsolidado.objects.filter(
                nomina_consolidada=empleado
            ).order_by('nombre_concepto')
            
            empleado_data = {
                'id': empleado.id,
                'rut_empleado': empleado.rut_empleado,
                'nombre_empleado': empleado.nombre_empleado,
                'cargo': empleado.cargo,
                'centro_costo': empleado.centro_costo,
                'estado_empleado': empleado.estado_empleado,
                'total_haberes': str((empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0)),
                'total_descuentos': str((empleado.dctos_legales or 0) + (empleado.otros_dctos or 0) + (empleado.impuestos or 0)),
                'liquido_pagar': str(((empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0)) - ((empleado.dctos_legales or 0) + (empleado.otros_dctos or 0) + (empleado.impuestos or 0))),
                'dias_trabajados': empleado.dias_trabajados,
                'dias_ausencia': empleado.dias_ausencia,
                'valores_headers': valores_headers,
                'conceptos': [
                    {
                        'nombre': concepto.nombre_concepto,
                        'clasificacion': concepto.tipo_concepto,
                        'monto_total': str(concepto.monto_total),
                        'cantidad': concepto.cantidad,
                        'origen_datos': concepto.fuente_archivo,
                    }
                    for concepto in conceptos
                ]
            }
            
            data['empleados'].append(empleado_data)
        
        return Response(data, status=status.HTTP_200_OK)
        
    except CierreNomina.DoesNotExist:
        return Response(
            {'error': 'Cierre no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logging.error(f"Error obteniendo libro de remuneraciones: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def obtener_movimientos_mes(request, cierre_id):
    """Alias compacto (legacy path) → devuelve resumen normalizado basado en MovimientoPersonal.

    Se mantiene la URL /movimientos/ pero ahora SIN campos legacy y con estructura reducida.
    Para detalle completo usar /movimientos/v3/detalle/.
    """
    from .models import CierreNomina, MovimientoPersonal
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        if not cierre.nomina_consolidada.exists():
            return Response({'error': 'No hay datos consolidados para este cierre'}, status=status.HTTP_404_NOT_FOUND)
        qs = (MovimientoPersonal.objects
              .filter(nomina_consolidada__cierre=cierre)
              .select_related('nomina_consolidada'))
        por_categoria = {}
        for mv in qs:
            cat = mv.categoria or 'sin_categoria'
            entry = por_categoria.get(cat) or {'count': 0}
            entry['count'] += 1
            por_categoria[cat] = entry
        data = {
            'cierre': {
                'id': cierre.id,
                'cliente': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': cierre.estado,
            },
            'resumen': {
                'total_movimientos': qs.count(),
                'por_categoria': por_categoria,
            },
            'movimientos': [
                {
                    'id': mv.id,
                    'categoria': mv.categoria,
                    'subtipo': mv.subtipo,
                    'descripcion': mv.descripcion,
                    'fecha_inicio': mv.fecha_inicio,
                    'fecha_fin': mv.fecha_fin,
                    'dias_evento': mv.dias_evento,
                    'dias_en_periodo': mv.dias_en_periodo,
                    'empleado': {
                        'rut': mv.nomina_consolidada.rut_empleado if mv.nomina_consolidada else None,
                        'nombre': mv.nomina_consolidada.nombre_empleado if mv.nomina_consolidada else None,
                        'estado': mv.nomina_consolidada.estado_empleado if mv.nomina_consolidada else None,
                    },
                    'fecha_deteccion': mv.fecha_deteccion,
                } for mv in qs.order_by('-fecha_deteccion')
            ]
        }
        return Response(data, status=status.HTTP_200_OK)
    except CierreNomina.DoesNotExist:
        return Response({'error': 'Cierre no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logging.error(f"Error alias movimientos normalizados: {e}")
        return Response({'error': 'Error interno del servidor', 'detalle': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def obtener_estadisticas_cierre(request, cierre_id):
    """
    Obtiene las estadísticas completas de un cierre finalizado
    incluyendo total de empleados, archivos usados, etc.
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar si hay datos consolidados
        from .models import NominaConsolidada
        
        if not cierre.nomina_consolidada.exists():
            # Si no hay datos consolidados, devolver datos básicos
            return Response({
                'estadisticas': {
                    'total_empleados': 0,
                    'total_ingresos': 0,
                    'total_finiquitos': 0,
                    'total_ausentismos': 0
                },
                'talana': [],
                'analista': [],
                'resumen_ejecutivo': None
            }, status=status.HTTP_200_OK)
        
        # Obtener empleados consolidados
        empleados = NominaConsolidada.objects.filter(cierre=cierre)
        
        # Calcular estadísticas
        estadisticas = {
            'total_empleados': empleados.count(),
            'total_ingresos': empleados.filter(estado_empleado='nueva_incorporacion').count(),
            'total_finiquitos': empleados.filter(estado_empleado='finiquito').count(),
            'total_ausentismos': empleados.filter(estado_empleado__in=['ausente_total', 'ausente_parcial']).count()
        }
        
        # Datos de archivos usados
        archivos_talana = []
        archivos_analista = []
        
        # Archivos Talana
        if cierre.libro_remuneraciones.filter(estado='procesado').exists():
            libro = cierre.libro_remuneraciones.filter(estado='procesado').first()
            archivos_talana.append({
                'tipo': 'libro_remuneraciones',
                'nombre': libro.archivo.name.split('/')[-1] if libro.archivo else 'libro_remuneraciones.xlsx',
                'fecha_subida': libro.fecha_subida.isoformat() if libro.fecha_subida else None,
                'estado': 'procesado'
            })
        
        if cierre.movimientos_mes.filter(estado='procesado').exists():
            movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
            archivos_talana.append({
                'tipo': 'movimientos_mes',
                'nombre': movimientos.archivo.name.split('/')[-1] if movimientos.archivo else 'movimientos_mes.xlsx',
                'fecha_subida': movimientos.fecha_subida.isoformat() if movimientos.fecha_subida else None,
                'estado': 'procesado'
            })
        
        # Archivos del Analista
        if cierre.analista_finiquitos.exists():
            archivos_analista.append({
                'tipo': 'finiquitos',
                'nombre': 'finiquitos.xlsx',
                'fecha_subida': timezone.now().isoformat(),
                'estado': 'procesado'
            })
        
        if cierre.analista_incidencias.exists():
            archivos_analista.append({
                'tipo': 'incidencias',
                'nombre': 'incidencias.xlsx', 
                'fecha_subida': timezone.now().isoformat(),
                'estado': 'procesado'
            })
        
        if cierre.analista_ingresos.exists():
            archivos_analista.append({
                'tipo': 'ingresos',
                'nombre': 'ingresos.xlsx',
                'fecha_subida': timezone.now().isoformat(),
                'estado': 'procesado'
            })
        
        # Calcular totales de resumen
        total_haberes = sum(emp.total_haberes or 0 for emp in empleados)
        total_descuentos = sum(emp.total_descuentos or 0 for emp in empleados)
        total_liquido = sum(emp.liquido_pagar or 0 for emp in empleados)
        
        # Respuesta completa
        data = {
            'estadisticas': estadisticas,
            'talana': archivos_talana,
            'analista': archivos_analista,
            'resumen_ejecutivo': {
                'total_haberes': str(total_haberes),
                'total_descuentos': str(total_descuentos),
                'total_liquido': str(total_liquido),
                'fecha_consolidacion': cierre.fecha_consolidacion.isoformat() if cierre.fecha_consolidacion else None
            }
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except CierreNomina.DoesNotExist:
        return Response(
            {'error': 'Cierre no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logging.error(f"Error obteniendo estadísticas del cierre: {str(e)}")
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def estadisticas_historial_verificacion(request, cierre_id):
    """
    Endpoint para obtener estadísticas del historial de verificaciones de un cierre
    """
    try:
        from .models import HistorialVerificacionCierre, DiscrepanciaHistorial
        from django.db.models import Count, Q
        
        # Verificar que el cierre existe
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Obtener todo el historial de verificaciones
        historiales = HistorialVerificacionCierre.objects.filter(
            cierre_id=cierre_id
        ).order_by('-fecha_ejecucion')
        
        if not historiales.exists():
            return Response({
                'cierre_id': cierre_id,
                'mensaje': 'No hay historial de verificaciones para este cierre',
                'total_verificaciones': 0,
                'estado_actual': cierre.estado
            })
        
        # Estadísticas generales
        total_verificaciones = historiales.count()
        ultima_verificacion = historiales.first()
        primera_verificacion = historiales.last()
        
        # Estadísticas de intentos
        verificaciones_exitosas = historiales.filter(estado_verificacion='completado').count()
        verificaciones_con_error = historiales.filter(estado_verificacion='error').count()
        verificaciones_en_proceso = historiales.filter(estado_verificacion='procesando').count()
        
        # Progreso de discrepancias
        historial_discrepancias = []
        for historial in historiales:
            discrepancias_total = DiscrepanciaHistorial.objects.filter(
                historial_verificacion=historial
            ).count()
            
            historial_discrepancias.append({
                'intento': historial.numero_intento,
                'fecha': historial.fecha_ejecucion.isoformat(),
                'fecha_finalizacion': historial.fecha_finalizacion.isoformat() if historial.fecha_finalizacion else None,
                'usuario': historial.usuario_ejecutor.username if historial.usuario_ejecutor else 'Sistema',
                'correo': historial.usuario_ejecutor.correo_bdo if historial.usuario_ejecutor else 'Sin correo',
                'discrepancias_encontradas': historial.total_discrepancias_encontradas or 0,
                'discrepancias_libro_vs_novedades': historial.discrepancias_libro_vs_novedades or 0,
                'discrepancias_movimientos_vs_analista': historial.discrepancias_movimientos_vs_analista or 0,
                'estado': historial.estado_verificacion,
                'duracion_segundos': historial.tiempo_ejecucion or 0,
                'duracion_minutos': (
                    round(historial.tiempo_ejecucion / 60, 2) if historial.tiempo_ejecucion else None
                ),
                'observaciones': historial.observaciones or ''  # ✅ Campo correcto
            })
        
        # Estadísticas de mejora
        mejora_discrepancias = None
        if len(historial_discrepancias) >= 2:
            primera_discrepancias = historial_discrepancias[-1]['discrepancias_encontradas']
            ultima_discrepancias = historial_discrepancias[0]['discrepancias_encontradas']
            if primera_discrepancias > 0:
                mejora_discrepancias = (
                    (primera_discrepancias - ultima_discrepancias) / primera_discrepancias * 100
                )
        
        data = {
            'cierre_id': cierre_id,
            'cierre_estado': cierre.estado,
            'resumen': {
                'total_verificaciones': total_verificaciones,
                'verificaciones_exitosas': verificaciones_exitosas,
                'verificaciones_con_error': verificaciones_con_error,
                'verificaciones_en_proceso': verificaciones_en_proceso,
                'primera_verificacion': primera_verificacion.fecha_ejecucion.isoformat(),
                'ultima_verificacion': ultima_verificacion.fecha_ejecucion.isoformat(),
                'mejora_discrepancias_porcentaje': round(mejora_discrepancias, 2) if mejora_discrepancias else None
            },
            'historial_detallado': historial_discrepancias,
            'estadisticas_discrepancias': {
                'discrepancias_primera_verificacion': (
                    historial_discrepancias[-1]['discrepancias_encontradas'] 
                    if historial_discrepancias else 0
                ),
                'discrepancias_ultima_verificacion': (
                    historial_discrepancias[0]['discrepancias_encontradas'] 
                    if historial_discrepancias else 0
                ),
                'objetivo_cero_discrepancias': (
                    historial_discrepancias[0]['discrepancias_encontradas'] == 0 
                    if historial_discrepancias else False
                )
            }
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except CierreNomina.DoesNotExist:
        return Response(
            {'error': 'Cierre no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logging.error(f"Error obteniendo estadísticas del historial: {str(e)}")
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )