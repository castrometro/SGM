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
import logging

from .utils.LibroRemuneraciones import clasificar_headers_libro_remuneraciones

User = get_user_model()

from .models import (
    CierreNomina,
    LibroRemuneracionesUpload,
    ArchivoAnalistaUpload,
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

from .serializers import (
    CierreNominaSerializer, 
    LibroRemuneracionesUploadSerializer, 
    ArchivoAnalistaUploadSerializer, 
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
    procesar_archivo_analista,
    procesar_archivo_novedades,
    generar_incidencias_cierre_task,
    generar_discrepancias_cierre_task,
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

    @action(detail=True, methods=['post'], url_path='actualizar-estado')
    def actualizar_estado(self, request, pk=None):
        """
        Actualiza automáticamente el estado del cierre basado en el estado de los archivos
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
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

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroRemuneracionesUpload.objects.all()
    serializer_class = LibroRemuneracionesUploadSerializer
    
    def perform_create(self, serializer):
        """
        Crear libro de remuneraciones con logging completo integrado
        """
        from .utils.mixins import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
        from .utils.clientes import get_client_ip
        from .utils.uploads import guardar_temporal
        from .models_logging import registrar_actividad_tarjeta_nomina
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
            from .utils.mixins import UploadLogNominaMixin
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
        
        from .models_logging import TarjetaActivityLogNomina
        
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
    
    def perform_destroy(self, instance):
        """
        Eliminar libro de remuneraciones y todos sus datos relacionados
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
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

    def perform_destroy(self, instance):
        """
        Eliminar archivo del analista y todos sus datos relacionados
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from django.db import transaction
        import logging
        
        logger = logging.getLogger(__name__)
        cierre = instance.cierre
        tipo = instance.tipo_archivo
        
        # Registrar actividad antes de eliminar
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta=f"archivo_analista_{tipo}",
            accion="delete_archivo",
            descripcion=f"Archivo del analista ({tipo}) eliminado para resubida",
            usuario=self.request.user,
            detalles={
                "archivo_id": instance.id,
                "tipo_archivo": tipo,
                "archivo_nombre": instance.archivo.name if instance.archivo else "N/A",
                "estado_anterior": instance.estado
            },
            ip_address=get_client_ip(self.request)
        )
        
        with transaction.atomic():
            # Contar registros antes de eliminar para logging
            if tipo == 'finiquitos':
                count = instance.analistafiniquito_set.count()
                logger.info(f"Eliminando {count} registros de finiquitos")
            elif tipo == 'incidencias':
                count = instance.analistaincidencia_set.count()
                logger.info(f"Eliminando {count} registros de incidencias")
            elif tipo == 'ingresos':
                count = instance.analistaingreso_set.count()
                logger.info(f"Eliminando {count} registros de ingresos")
            
            # El CASCADE automáticamente eliminará los registros relacionados
            # pero lo hacemos explícito para claridad
            instance.delete()
            logger.info(f"Archivo del analista {instance.id} ({tipo}) eliminado completamente")

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
        cierre.estado = 'completado'
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
        
        # Verificar que el cierre esté en estado completado y archivos consolidados
        if cierre.estado != 'completado':
            return Response({
                "error": "El cierre debe estar en estado 'completado' para iniciar análisis"
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
        if cierre.estado not in ['revision_inicial', 'validacion_conceptos', 'completado']:
            return Response({
                "error": "El cierre debe estar en estado 'revision_inicial', 'validacion_conceptos' o 'completado' para generar incidencias"
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

class DiscrepanciaCierreViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar discrepancias de verificación de datos"""
    queryset = DiscrepanciaCierre.objects.all()
    serializer_class = DiscrepanciaCierreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros disponibles
        cierre_id = self.request.query_params.get('cierre')
        tipo_discrepancia = self.request.query_params.get('tipo')
        rut_empleado = self.request.query_params.get('rut')
        grupo = self.request.query_params.get('grupo')
        
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_discrepancia:
            queryset = queryset.filter(tipo_discrepancia=tipo_discrepancia)
        if rut_empleado:
            queryset = queryset.filter(rut_empleado__icontains=rut_empleado)
        if grupo:
            # Filtrar por grupo de discrepancias
            libro_vs_novedades = [
                'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
                'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
            ]
            if grupo == 'libro_vs_novedades':
                queryset = queryset.filter(tipo_discrepancia__in=libro_vs_novedades)
            elif grupo == 'movimientos_vs_analista':
                queryset = queryset.exclude(tipo_discrepancia__in=libro_vs_novedades)
            
        return queryset.select_related('cierre', 'empleado_libro', 'empleado_novedades').order_by('-fecha_detectada')
    
    @action(detail=False, methods=['post'], url_path='generar/(?P<cierre_id>[^/.]+)')
    def generar_discrepancias(self, request, cierre_id=None):
        """Endpoint para generar discrepancias de un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar permisos básicos
        if not request.user.is_authenticated:
            return Response({"error": "Usuario no autenticado"}, status=401)
        
        # Verificar que el cierre esté en estado adecuado
        if cierre.estado not in ['revision_inicial']:
            return Response({
                "error": "El cierre debe estar en estado 'revision_inicial' para generar discrepancias"
            }, status=400)
        
        # Lanzar tarea de generación de discrepancias
        task = generar_discrepancias_cierre_task.delay(cierre_id)
        
        return Response({
            "message": "Generación de discrepancias iniciada",
            "task_id": task.id,
            "cierre_id": cierre_id
        }, status=202)
    
    @action(detail=False, methods=['get'], url_path='resumen/(?P<cierre_id>[^/.]+)')
    def resumen_discrepancias(self, request, cierre_id=None):
        """Obtiene un resumen estadístico de discrepancias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        from .utils.GenerarDiscrepancias import obtener_resumen_discrepancias
        resumen = obtener_resumen_discrepancias(cierre)
        
        serializer = ResumenDiscrepanciasSerializer(resumen)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado_discrepancias(self, request, cierre_id=None):
        """Obtiene el estado de discrepancias de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        total_discrepancias = cierre.discrepancias.count()
        
        # Clasificar por grupos
        libro_vs_novedades_tipos = [
            'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
            'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
        ]
        
        total_libro_vs_novedades = cierre.discrepancias.filter(tipo_discrepancia__in=libro_vs_novedades_tipos).count()
        total_movimientos_vs_analista = total_discrepancias - total_libro_vs_novedades
        
        return Response({
            "cierre_id": cierre.id,
            "estado_cierre": cierre.estado,
            "tiene_discrepancias": total_discrepancias > 0,
            "total_discrepancias": total_discrepancias,
            "discrepancias_por_grupo": {
                "libro_vs_novedades": total_libro_vs_novedades,
                "movimientos_vs_analista": total_movimientos_vs_analista
            },
            "empleados_afectados": cierre.discrepancias.values('rut_empleado').distinct().count(),
            "fecha_ultima_verificacion": cierre.discrepancias.first().fecha_detectada if total_discrepancias > 0 else None
        })
    
    @action(detail=False, methods=['post'], url_path='preview/(?P<cierre_id>[^/.]+)')
    def preview_discrepancias(self, request, cierre_id=None):
        """Endpoint para previsualizar qué discrepancias se generarían sin crearlas"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        from .utils.GenerarDiscrepancias import (
            generar_discrepancias_libro_vs_novedades,
            generar_discrepancias_movimientos_vs_analista
        )
        
        try:
            # Generar discrepancias preview sin guardarlas
            discrepancias_libro_novedades = generar_discrepancias_libro_vs_novedades(cierre)
            discrepancias_movimientos_analista = generar_discrepancias_movimientos_vs_analista(cierre)
            
            todas_discrepancias = discrepancias_libro_novedades + discrepancias_movimientos_analista
            
            # Convertir discrepancias a formato serializable
            discrepancias_preview = []
            for discrepancia in todas_discrepancias:
                discrepancias_preview.append({
                    'tipo_discrepancia': discrepancia.tipo_discrepancia,
                    'tipo_discrepancia_display': discrepancia.get_tipo_discrepancia_display(),
                    'rut_empleado': discrepancia.rut_empleado,
                    'descripcion': discrepancia.descripcion,
                    'concepto_afectado': discrepancia.concepto_afectado,
                    'valor_libro': discrepancia.valor_libro,
                    'valor_novedades': discrepancia.valor_novedades,
                    'valor_movimientos': discrepancia.valor_movimientos,
                    'valor_analista': discrepancia.valor_analista,
                })
            
            return Response({
                'total_discrepancias': len(todas_discrepancias),
                'libro_vs_novedades': len(discrepancias_libro_novedades),
                'movimientos_vs_analista': len(discrepancias_movimientos_analista),
                'discrepancias': discrepancias_preview,
                'mensaje': 'Vista previa generada - no se guardaron discrepancias'
            })
            
        except Exception as e:
            logger.error(f"Error generando preview de discrepancias: {e}")
            return Response({
                "error": f"Error generando preview: {str(e)}"
            }, status=500)
    
    @action(detail=False, methods=['delete'], url_path='limpiar/(?P<cierre_id>[^/.]+)')
    def limpiar_discrepancias(self, request, cierre_id=None):
        """
        Limpia todas las discrepancias de un cierre.
        Útil para re-ejecutar la verificación después de corregir archivos.
        """
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Eliminar todas las discrepancias del cierre
        deleted_count = cierre.discrepancias.all().delete()[0]
        
        # Resetear estado del cierre
        cierre.estado = 'datos_consolidados'
        cierre.save(update_fields=['estado'])
        
        logger.info(f"Eliminadas {deleted_count} discrepancias del cierre {cierre_id}")
        
        return Response({
            "message": f"Eliminadas {deleted_count} discrepancias. Cierre listo para nueva verificación.",
            "discrepancias_eliminadas": deleted_count,
            "nuevo_estado": cierre.estado
        })


class CierreNominaDiscrepanciasViewSet(viewsets.ViewSet):
    """ViewSet adicional para operaciones de verificación de datos en cierres"""
    
    @action(detail=True, methods=['get'])
    def estado_verificacion(self, request, pk=None):
        """Obtiene el estado de verificación de datos de un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        total_discrepancias = cierre.discrepancias.count()
        
        # Determinar estado automáticamente
        if total_discrepancias == 0:
            if cierre.estado in ['discrepancias_detectadas']:
                cierre.estado = 'datos_verificados'
                cierre.save(update_fields=['estado'])
        else:
            if cierre.estado in ['datos_consolidados', 'datos_verificados']:
                cierre.estado = 'discrepancias_detectadas'
                cierre.save(update_fields=['estado'])
        
        return Response({
            "cierre_id": cierre.id,
            "estado_verificacion": cierre.estado,
            "requiere_correccion": total_discrepancias > 0,
            "total_discrepancias": total_discrepancias,
            "mensaje": "Sin discrepancias - datos verificados" if total_discrepancias == 0 else f"Se encontraron {total_discrepancias} discrepancias que requieren corrección"
        })
    
    @action(detail=True, methods=['post'])
    def lanzar_verificacion(self, request, pk=None):
        """Lanza la verificación de datos para un cierre"""
        try:
            cierre = CierreNomina.objects.get(id=pk)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Verificar que el cierre esté en estado adecuado
        if cierre.estado not in ['datos_consolidados', 'discrepancias_detectadas']:
            return Response({
                "error": "El cierre debe estar en estado 'datos_consolidados' para verificar datos"
            }, status=400)
        
        # Lanzar tarea
        task = generar_discrepancias_cierre_task.delay(pk)
        
        return Response({
            "message": "Verificación de datos iniciada",
            "task_id": task.id,
            "cierre_id": pk
        }, status=202)


# ========== UPLOAD LOG ENDPOINTS ==========

@api_view(['GET'])
def obtener_estado_upload_log_nomina(request, upload_log_id):
    """
    Obtiene el estado actual de un UploadLogNomina específico
    """
    from .models_logging import UploadLogNomina
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


