from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from celery import chain
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from api.models import Cliente, AsignacionClienteUsuario
from .permissions import SupervisorPuedeVerCierresNominaAnalistas
from django.contrib.auth import get_user_model
import logging

from .utils.LibroRemuneraciones import clasificar_headers_libro_remuneraciones

User = get_user_model()

from .models import (
    CierreNomina,
    LibroRemuneracionesUpload,
    MovimientosMesUpload,
    ArchivoAnalistaUpload,
    ArchivoNovedadesUpload,
    ChecklistItem,
    ConceptoRemuneracion,
    MovimientoAltaBaja,
    MovimientoAusentismo,
    MovimientoVacaciones,
    MovimientoVariacionSueldo,
    MovimientoVariacionContrato,
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
)

from .serializers import (
    CierreNominaSerializer, 
    LibroRemuneracionesUploadSerializer, 
    MovimientosMesUploadSerializer,
    ArchivoAnalistaUploadSerializer, 
    ArchivoNovedadesUploadSerializer, 
    CierreNominaCreateSerializer, 
    ChecklistItemUpdateSerializer, 
    ChecklistItemCreateSerializer,
    ConceptoRemuneracionSerializer,
    MovimientoAltaBajaSerializer,
    MovimientoAusentismoSerializer,
    MovimientoVacacionesSerializer,
    MovimientoVariacionSueldoSerializer,
    MovimientoVariacionContratoSerializer,
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
)

from .tasks import (
    analizar_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones_task,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    procesar_movimientos_mes,
    procesar_archivo_analista,
    procesar_archivo_novedades,
    generar_incidencias_cierre_task,
)

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
        
        # Filtrar por parámetros URL
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)

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
            return Response({
                "ultimo_cierre": cierre.periodo,
                "estado_cierre_actual": cierre.estado,
            })
        else:
            return Response({
                "ultimo_cierre": None,
                "estado_cierre_actual": None,
            })

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroRemuneracionesUpload.objects.all()
    serializer_class = LibroRemuneracionesUploadSerializer
    
    def perform_create(self, serializer):
        instance = serializer.save()
        chain(
            analizar_headers_libro_remuneraciones.s(instance.id),
            clasificar_headers_libro_remuneraciones_task.s(),
        )()

    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        libro = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if libro:
            return Response({
                "id": libro.id,
                "estado": libro.estado,
                "archivo_nombre": libro.archivo.name.split("/")[-1],
                "archivo_url": request.build_absolute_uri(libro.archivo.url),
                "header_json": libro.header_json,
                "fecha_subida": libro.fecha_subida,
                "cliente_id": libro.cierre.cliente.id,
                "cliente_nombre": libro.cierre.cliente.nombre,
            })
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
            })

    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """Procesar libro completo: actualizar empleados y guardar registros"""
        libro = self.get_object()
        libro.estado = 'procesando'
        libro.save(update_fields=['estado'])
        
        # Chain de procesamiento completo
        result = chain(
            actualizar_empleados_desde_libro.s(libro.id),
            guardar_registros_nomina.s(),
        )()
        
        return Response({
            'task_id': result.id if hasattr(result, 'id') else str(result), 
            'mensaje': 'Procesamiento iniciado'
        }, status=status.HTTP_202_ACCEPTED)

# Nuevos ViewSets para Movimientos_Mes

class MovimientoAltaBajaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoAltaBaja.objects.all()
    serializer_class = MovimientoAltaBajaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

class MovimientoAusentismoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoAusentismo.objects.all()
    serializer_class = MovimientoAusentismoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

class MovimientoVacacionesViewSet(viewsets.ModelViewSet):
    queryset = MovimientoVacaciones.objects.all()
    serializer_class = MovimientoVacacionesSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

class MovimientoVariacionSueldoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoVariacionSueldo.objects.all()
    serializer_class = MovimientoVariacionSueldoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

class MovimientoVariacionContratoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoVariacionContrato.objects.all()
    serializer_class = MovimientoVariacionContratoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

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

class MovimientosMesUploadViewSet(viewsets.ModelViewSet):
    queryset = MovimientosMesUpload.objects.all()
    serializer_class = MovimientosMesUploadSerializer
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        """Obtiene el estado del archivo de movimientos del mes para un cierre específico"""
        movimiento = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if movimiento:
            return Response({
                "id": movimiento.id,
                "estado": movimiento.estado,
                "archivo_nombre": movimiento.archivo.name.split("/")[-1] if movimiento.archivo else "",
                "archivo_url": request.build_absolute_uri(movimiento.archivo.url) if movimiento.archivo else "",
                "fecha_subida": movimiento.fecha_subida,
                "cierre_id": movimiento.cierre.id,
                "cliente_id": movimiento.cierre.cliente.id,
                "cliente_nombre": movimiento.cierre.cliente.nombre,
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
        """Sube un archivo de movimientos del mes para un cierre específico"""
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
        
        # Crear o actualizar el registro de movimientos
        movimiento, created = MovimientosMesUpload.objects.get_or_create(
            cierre=cierre,
            defaults={
                'archivo': archivo,
                'estado': 'pendiente'
            }
        )
        
        if not created:
            # Si ya existe, actualizar el archivo
            movimiento.archivo = archivo
            movimiento.estado = 'pendiente'
            movimiento.save()
        
        # Disparar tarea de procesamiento con Celery
        procesar_movimientos_mes.delay(movimiento.id)
        
        return Response({
            "id": movimiento.id,
            "estado": movimiento.estado,
            "archivo_nombre": archivo.name,
            "fecha_subida": movimiento.fecha_subida,
            "mensaje": "Archivo subido correctamente y enviado a procesamiento"
        }, status=201)

class ArchivoAnalistaUploadViewSet(viewsets.ModelViewSet):
    queryset = ArchivoAnalistaUpload.objects.all()
    serializer_class = ArchivoAnalistaUploadSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        tipo_archivo = self.request.query_params.get('tipo_archivo')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_archivo:
            queryset = queryset.filter(tipo_archivo=tipo_archivo)
        return queryset
    
    @action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)/(?P<tipo_archivo>[^/.]+)')
    def subir(self, request, cierre_id=None, tipo_archivo=None):
        """Sube un archivo del analista para un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Validar tipo de archivo
        tipos_validos = ['finiquitos', 'incidencias', 'ingresos']
        if tipo_archivo not in tipos_validos:
            return Response({"error": f"Tipo de archivo inválido. Debe ser uno de: {', '.join(tipos_validos)}"}, status=400)
        
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se proporcionó archivo"}, status=400)
        
        # Validar que sea un archivo Excel
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response({"error": "El archivo debe ser de tipo Excel (.xlsx o .xls)"}, status=400)
        
        # Crear el registro del archivo
        archivo_analista = ArchivoAnalistaUpload.objects.create(
            cierre=cierre,
            tipo_archivo=tipo_archivo,
            archivo=archivo,
            analista=request.user,
            estado='pendiente'
        )
        
        # Disparar tarea de procesamiento con Celery
        procesar_archivo_analista.delay(archivo_analista.id)
        
        return Response({
            "id": archivo_analista.id,
            "tipo_archivo": archivo_analista.tipo_archivo,
            "estado": archivo_analista.estado,
            "archivo_nombre": archivo.name,
            "fecha_subida": archivo_analista.fecha_subida,
            "mensaje": "Archivo subido correctamente y enviado a procesamiento"
        }, status=201)
    
    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        """Reprocesa un archivo del analista"""
        archivo = self.get_object()
        
        # Reiniciar estado
        archivo.estado = 'pendiente'
        archivo.save()
        
        # Disparar tarea de procesamiento
        procesar_archivo_analista.delay(archivo.id)
        
        return Response({
            "mensaje": "Archivo enviado a reprocesamiento",
            "estado": archivo.estado
        })

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

                if header_novedades in headers_sin_clasificar:
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
                        nombre_concepto_novedades=header_novedades,
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
                    headers_sin_clasificar.remove(header_novedades)
                    headers_clasificados.append(header_novedades)
            
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
        from celery import chain
        
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

class IncidenciaCierreViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar incidencias de cierre de nómina"""
    queryset = IncidenciaCierre.objects.all()
    serializer_class = IncidenciaCierreSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        estado = self.request.query_params.get('estado')
        prioridad = self.request.query_params.get('prioridad')
        asignado_a = self.request.query_params.get('asignado_a')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
        if asignado_a:
            queryset = queryset.filter(asignado_a_id=asignado_a)
            
        return queryset.select_related('cierre', 'empleado_libro', 'empleado_novedades', 'asignado_a')
    
    @action(detail=False, methods=['post'], url_path='generar/(?P<cierre_id>[^/.]+)')
    def generar_incidencias(self, request, cierre_id=None):
        """Endpoint para generar incidencias de un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar si el usuario tiene acceso al cierre (mismo cliente)
        # Esto se puede extender con lógica más específica según los requerimientos
        
        # Lanzar tarea de generación de incidencias
        task = generar_incidencias_cierre_task.delay(cierre_id)
        
        return Response({
            "message": "Generación de incidencias iniciada",
            "task_id": task.id,
            "cierre_id": cierre_id
        }, status=202)
    
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
            
        return queryset.select_related('incidencia', 'usuario').order_by('-fecha_resolucion')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearResolucionSerializer
        return ResolucionIncidenciaSerializer
    
    def perform_create(self, serializer):
        """Crear una nueva resolución para una incidencia"""
        incidencia_id = self.request.data.get('incidencia_id')
        
        if not incidencia_id:
            raise serializers.ValidationError("incidencia_id es requerido")
        
        try:
            incidencia = IncidenciaCierre.objects.get(id=incidencia_id)
        except IncidenciaCierre.DoesNotExist:
            raise serializers.ValidationError("Incidencia no encontrada")
        
        # Crear la resolución
        resolucion = serializer.save(
            incidencia=incidencia,
            usuario=self.request.user
        )
        
        # Actualizar estado de la incidencia según el tipo de resolución y rol del usuario
        tipo_resolucion = resolucion.tipo_resolucion
        if tipo_resolucion == 'solucion':
            # Si el usuario es staff o superuser, puede aprobar directamente
            if self.request.user.is_staff or self.request.user.is_superuser:
                incidencia.estado = 'aprobada_supervisor'
            else:
                incidencia.estado = 'resuelta_analista'
        elif tipo_resolucion == 'rechazo':
            incidencia.estado = 'rechazada_supervisor'
        
        incidencia.save(update_fields=['estado'])
        
        return resolucion
    
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
        return Response({
            "incidencia_id": incidencia_id,
            "resoluciones": serializer.data,
            "total_resoluciones": resoluciones.count()
        })


# ======== ENDPOINTS ADICIONALES PARA CIERRE NOMINA ========

# Agregar action al CierreNominaViewSet existente para manejo de incidencias
# (Se puede agregar como mixin o extender el ViewSet existente)

class CierreNominaIncidenciasViewSet(viewsets.ViewSet):
    """ViewSet adicional para operaciones de incidencias en cierres"""
    
    @action(detail=True, methods=['get'])
    def estado_incidencias(self, request, pk=None):
        """Obtiene el estado de incidencias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        return Response({
            "cierre_id": cierre.id,
            "estado_incidencias": cierre.estado_incidencias,
            "tiene_incidencias": cierre.incidencias.exists(),
            "total_incidencias": cierre.incidencias.count(),
            "incidencias_pendientes": cierre.incidencias.filter(estado='pendiente').count(),
            "incidencias_resueltas": cierre.incidencias.filter(
                estado__in=['aprobada_supervisor', 'resuelta_analista']
            ).count()
        })
    
    @action(detail=True, methods=['post'])
    def lanzar_generacion_incidencias(self, request, pk=None):
        """Lanza la tarea de generación de incidencias para un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que el cierre esté en estado adecuado
        if cierre.estado not in ['datos_consolidados', 'completado']:
            return Response({
                "error": "El cierre debe estar en estado 'datos_consolidados' o 'completado' para generar incidencias"
            }, status=400)
        
        # Lanzar tarea
        task = generar_incidencias_cierre_task.delay(pk)
        
        return Response({
            "message": "Generación de incidencias iniciada",
            "task_id": task.id,
            "cierre_id": pk
        }, status=202)


