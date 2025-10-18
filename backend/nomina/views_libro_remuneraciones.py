# nomina/views_libro_remuneraciones.py

import logging
import os
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from celery import chain

from .models import CierreNomina, LibroRemuneracionesUpload, ActivityEvent  # ✅ ActivityEvent desde models principal
from .serializers import LibroRemuneracionesUploadSerializer
from .utils.mixins import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
from .utils.clientes import get_client_ip
from .utils.uploads import guardar_temporal
# ✅ DUAL LOGGING: TarjetaActivityLogNomina para historial UI, ActivityEvent para auditoría técnica
from .models_logging import registrar_actividad_tarjeta_nomina

# ✅ IMPORTS REFACTORIZADOS: Usar tareas del paquete organizado tasks_refactored/
from .tasks_refactored.libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    # 🚀 NUEVAS TASKS OPTIMIZADAS CON CHORD
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
)

logger = logging.getLogger(__name__)


class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la subida y procesamiento de libros de remuneraciones
    """
    queryset = LibroRemuneracionesUpload.objects.all()
    serializer_class = LibroRemuneracionesUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Crear libro de remuneraciones con logging completo integrado
        """
        logger.info("=== INICIANDO SUBIDA DE LIBRO DE REMUNERACIONES ===")
        
        # 1. OBTENER DATOS DEL REQUEST
        request = self.request
        archivo = request.FILES.get('archivo')
        cierre_id = request.data.get('cierre')
        
        if not archivo or not cierre_id:
            raise ValueError("Archivo y cierre_id son requeridos")
        
        logger.info(f"Procesando archivo: {archivo.name} para cierre: {cierre_id}")
        
        # 2. OBTENER CIERRE Y CLIENTE
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cliente = cierre.cliente
        except CierreNomina.DoesNotExist:
            raise ValueError("Cierre no encontrado")
        
        # ✅ LOGGING V2: Inicio de subida
        ActivityEvent.log(
            user=request.user,
            cliente=cliente,
            cierre=cierre,  # Normalizado
            event_type='upload',
            action='upload_iniciado',
            resource_type='libro_remuneraciones',
            resource_id=str(cierre.id),
            details={
                'archivo': archivo.name,
                'tamano_bytes': archivo.size,
            },
            request=request
        )
        logger.info(f"✅ ActivityEvent registrado: upload_iniciado para archivo {archivo.name}")
        
        # 3. VALIDAR ARCHIVO
        try:
            validator = ValidacionArchivoCRUDMixin()
            validator.validar_archivo(archivo)
            logger.info(f"Archivo {archivo.name} validado correctamente")
            
            # ✅ LOGGING V2: Archivo validado
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
                cierre=cierre,  # Normalizado
                event_type='validation',
                action='archivo_validado',
                resource_type='libro_remuneraciones',
                resource_id=str(cierre.id),
                details={
                    'archivo': archivo.name,
                    'validaciones': ['formato', 'tamaño', 'nombre'],
                },
                request=request
            )
            
            # 3.5. VALIDAR NOMBRE ESPECÍFICO DEL ARCHIVO
            periodo_formato = cierre.periodo.replace("-", "")  # "2025-08" → "202508"
            rut_sin_separadores = cliente.rut.replace("-", "").replace(".", "")  # "96.540.690-5" → "965406905"
            patron_regex = f"^{periodo_formato}_libro_remuneraciones_{rut_sin_separadores}(_.*)?\\.(xlsx|xls)$"
            
            logger.info(f"Validando nombre de archivo con patrón: {patron_regex}")
            validator.validar_nombre_archivo(archivo.name, patron_regex)
            logger.info(f"Nombre de archivo {archivo.name} válido")
            
        except ValueError as e:
            logger.error(f"Error validando archivo: {e}")
            
            # ✅ LOGGING V2: Error de validación
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
                cierre=cierre,  # Normalizado
                event_type='validation',
                action='validacion_fallida',
                resource_type='libro_remuneraciones',
                resource_id=str(cierre.id),
                details={
                    'archivo': archivo.name,
                    'error': str(e),
                },
                request=request
            )
            
            # Convertir ValueError a ValidationError para respuesta HTTP 400
            raise ValidationError({"detail": str(e)})
        
        # 4. CREAR UPLOAD LOG (STUB - NO-OP DURANTE TRANSICIÓN)
        # TODO: Migrar a Activity Logging V2
        log_mixin = UploadLogNominaMixin()
        log_mixin.tipo_upload = "libro_remuneraciones"
        log_mixin.usuario = request.user
        log_mixin.ip_usuario = get_client_ip(request)
        
        upload_log_stub = log_mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log stub creado (no persistido) - ID: {upload_log_stub.id}")
        
        # 5. GUARDAR ARCHIVO TEMPORAL - COMENTADO TEMPORALMENTE
        # TODO: Refactorizar para usar solo temporal hasta consolidación final
        
        # 6. CREAR/ACTUALIZAR REGISTRO DE LIBRO
        with transaction.atomic():
            libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
            
            if libro_existente:
                # Las señales se encargan automáticamente de eliminar archivos anteriores
                libro_existente.archivo = archivo
                libro_existente.estado = 'pendiente'
                libro_existente.header_json = []
                libro_existente.upload_log = None  # STUB: No asignar durante transición
                libro_existente.fecha_subida = timezone.now()
                libro_existente.save()
                instance = libro_existente
                logger.info(f"Libro actualizado con ID: {instance.id}")
            else:
                # Crear nuevo
                instance = serializer.save(
                    cierre=cierre,
                    upload_log=None,  # STUB: No asignar durante transición
                    estado='pendiente'
                )
                logger.info(f"Libro creado con ID: {instance.id}")
        
        # ✅ LOGGING V2: Upload completado exitosamente (técnico)
        ActivityEvent.log(
            user=request.user,
            cliente=cliente,
            cierre=cierre,  # Normalizado
            event_type='upload',
            action='upload_completado',
            resource_type='libro_remuneraciones',
            resource_id=str(instance.id),
            details={
                'libro_id': instance.id,
                'archivo': archivo.name,
                'tamano_bytes': archivo.size,
                'es_reemplazo': libro_existente is not None,
            },
            request=request
        )
        logger.info(f"✅ ActivityEvent registrado: upload_completado para libro {instance.id}")
        
        # ✅ LOGGING USUARIO: Registro para historial visible en UI
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="libro_remuneraciones",
            accion="upload_excel",
            descripcion=f"Subió {archivo.name}",
            usuario=request.user,
            detalles={
                'archivo': archivo.name,
                'hora': timezone.now().strftime('%H:%M:%S'),
                'tamano_mb': round(archivo.size / 1024 / 1024, 2)
            },
            resultado="exito",
            ip_address=get_client_ip(request)
        )
        logger.info(f"✅ TarjetaActivityLog registrado: upload_excel para libro {instance.id}")
        
        # 6.5. ACTUALIZAR UPLOAD_LOG CON RUTA DEFINITIVA - STUB DESHABILITADO
        # TODO: Migrar a Activity V2
        # upload_log_stub.ruta_archivo = instance.archivo.path
        # upload_log_stub.save()
        logger.debug(f"[STUB] Upload log NO persistido. Ruta del archivo: {instance.archivo.path}")
        
        # 7. REGISTRAR ACTIVIDAD - STUB DESHABILITADO
        # TODO: Migrar a Activity V2 con logActivity()
        # registrar_actividad_tarjeta_nomina(...)
        logger.debug(f"[STUB] Actividad NO registrada. Archivo: {archivo.name}")
        
        # 8. GUARDAR LIBRO_ID EN RESUMEN DEL UPLOAD_LOG - STUB DESHABILITADO
        # TODO: Migrar a Activity V2
        # upload_log_stub.resumen = {...}
        # upload_log_stub.save()
        logger.debug(f"[STUB] Resumen NO guardado. Libro ID: {instance.id}")
        
        # 9. INICIAR PROCESAMIENTO CON CELERY
        try:
            chain(
                analizar_headers_libro_remuneraciones_con_logging.s(instance.id, None, request.user.id),  # Pasar usuario_id
                clasificar_headers_libro_remuneraciones_con_logging.s(),
            ).apply_async()
            logger.info(f"Chain de Celery iniciado para libro {instance.id} con usuario_id={request.user.id}")
            
            # ✅ LOGGING V2: Procesamiento iniciado
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
                cierre=cierre,  # Normalizado
                event_type='process',
                action='procesamiento_iniciado',
                resource_type='libro_remuneraciones',
                resource_id=str(instance.id),
                details={
                    'libro_id': instance.id,
                    'archivo': archivo.name,
                },
                request=request
            )
            
        except Exception as e:
            logger.error(f"Error iniciando procesamiento: {e}")
            
            # ✅ LOGGING V2: Error al iniciar procesamiento
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
                cierre=cierre,  # Normalizado
                event_type='process',
                action='procesamiento_error_inicio',
                resource_type='libro_remuneraciones',
                resource_id=str(instance.id),
                details={
                    'libro_id': instance.id,
                    'error': str(e),
                },
                request=request
            )
            
            # upload_log_stub.marcar_como_error() - STUB deshabilitado
            raise
        
        logger.info("=== SUBIDA DE LIBRO DE REMUNERACIONES COMPLETADA ===")
    
    def perform_destroy(self, instance):
        """
        Eliminar libro de remuneraciones con logging
        """
        logger.info(f"=== ELIMINANDO LIBRO DE REMUNERACIONES ID: {instance.id} ===")
        
        # Obtener datos antes de eliminar
        cierre_id = instance.cierre.id
        archivo_nombre = instance.archivo.name.split("/")[-1] if instance.archivo else "sin_archivo"
        libro_id = instance.id
        
        # Obtener motivo si fue proporcionado
        motivo = self.request.data.get('motivo', 'No especificado') if hasattr(self.request, 'data') and self.request.data else 'No especificado'
        
        # ✅ LOGGING V2: Registro de eliminación (técnico)
        ActivityEvent.log(
            user=self.request.user,
            cliente=instance.cierre.cliente,
            cierre=instance.cierre,  # Normalizado
            event_type='delete',
            action='archivo_eliminado',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'libro_id': libro_id,
                'archivo': archivo_nombre,
                'motivo': motivo,
                'estado_previo': instance.estado,
            },
            request=self.request
        )
        logger.info(f"✅ ActivityEvent registrado: archivo_eliminado para libro {libro_id}")
        
        # ✅ LOGGING USUARIO: Registro para historial visible en UI
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="libro_remuneraciones",
            accion="delete_archivo",
            descripcion=f"Eliminó {archivo_nombre}",
            usuario=self.request.user,
            detalles={
                'archivo': archivo_nombre,
                'hora': timezone.now().strftime('%H:%M:%S'),
                'motivo': motivo
            },
            resultado="exito",
            ip_address=get_client_ip(self.request)
        )
        logger.info(f"✅ TarjetaActivityLog registrado: delete_archivo para libro {libro_id}")
        
        # Eliminar el libro (las señales se encargan del archivo físico)
        instance.delete()
        logger.info(f"=== LIBRO {libro_id} ELIMINADO CORRECTAMENTE ===")

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
                "archivo_nombre": libro.archivo.name.split("/")[-1] if libro.archivo else "",
                "archivo_url": request.build_absolute_uri(libro.archivo.url) if libro.archivo else "",
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
                        "headers_detectados": libro.upload_log.headers_detectados,
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
        """
        🚀 Procesar libro completo: actualizar empleados y guardar registros
        Versión optimizada con Celery Chord para mejor rendimiento.
        """
        libro = self.get_object()
        
        # Validar que el libro esté en estado clasificado
        if libro.estado != 'clasificado':
            return Response({
                'error': 'El libro debe estar en estado "clasificado" para procesar'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Limpiar cache de Redis antes de procesar
        try:
            from .cache_redis import get_cache_system_nomina
            cache_system = get_cache_system_nomina()
            cache_cleared = cache_system.clear_cierre_cache(
                cliente_id=libro.cierre.cliente.id,
                periodo=str(libro.cierre.periodo)  # Convertir a string directamente
            )
            if cache_cleared:
                logger.info(f"🗑️ Cache de Redis limpiado para cierre {libro.cierre.id}")
            else:
                logger.warning(f"⚠️ No se pudo limpiar completamente el cache para cierre {libro.cierre.id}")
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando cache de Redis: {e}")
        
        # Cambiar estado a procesando
        libro.estado = 'procesando'
        libro.save(update_fields=['estado'])
        
        # Leer parámetros opcionales - optimización activada por defecto
        usar_optimizacion = request.data.get('usar_optimizacion', True) if hasattr(request, 'data') and request.data else True
        
        logger.info(f"🔄 Iniciando procesamiento de libro {libro.id}, optimización: {usar_optimizacion}")
        
        # ✅ LOGGING USUARIO: Procesamiento iniciado (para historial UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=libro.cierre.id,
            tarjeta="libro_remuneraciones",
            accion="process_start",
            descripcion=f"Inició procesamiento {'optimizado' if usar_optimizacion else 'clásico'}",
            usuario=request.user,
            detalles={
                "libro_id": libro.id,
                "modo": 'optimizado' if usar_optimizacion else 'clasico',
                "hora": timezone.now().strftime('%H:%M:%S')
            },
            resultado="exito",
            ip_address=get_client_ip(request)
        )
        logger.info(f"✅ TarjetaActivityLog registrado: process_start para libro {libro.id}")
        
        if usar_optimizacion:
            # 🚀 USAR VERSIONES OPTIMIZADAS CON CHORD
            try:
                result = chain(
                    actualizar_empleados_desde_libro_optimizado.s(libro.id, request.user.id),
                    guardar_registros_nomina_optimizado.s(),
                ).apply_async()
                
                mensaje = 'Procesamiento optimizado iniciado (usando Celery Chord para mejor rendimiento)'
                logger.info(f"🚀 Chain optimizado iniciado para libro {libro.id} con usuario_id={request.user.id}")
                
            except Exception as e:
                # Fallback a versión no optimizada
                logger.warning(f"⚠️ Error iniciando procesamiento optimizado: {e}, usando fallback")
                result = chain(
                    actualizar_empleados_desde_libro.s(libro.id, request.user.id),
                    guardar_registros_nomina.s(),
                ).apply_async()
                mensaje = 'Procesamiento iniciado (fallback a modo clásico)'
        else:
            # 📝 USAR VERSIONES CLÁSICAS
            result = chain(
                actualizar_empleados_desde_libro.s(libro.id, request.user.id),
                guardar_registros_nomina.s(),
            ).apply_async()
            mensaje = 'Procesamiento clásico iniciado'
            logger.info(f"📝 Chain clásico iniciado para libro {libro.id} con usuario_id={request.user.id}")
        
        logger.info(f"Procesamiento completo iniciado para libro {libro.id}")
        
        return Response({
            'task_id': result.id if hasattr(result, 'id') else str(result), 
            'mensaje': mensaje,
            'libro_id': libro.id,
            'optimizado': usar_optimizacion
        }, status=status.HTTP_202_ACCEPTED)
    
    def perform_destroy(self, instance):
        """
        Eliminar libro de remuneraciones y todos sus datos relacionados
        """
        logger.info(f"=== ELIMINANDO LIBRO DE REMUNERACIONES {instance.id} ===")
        
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
            empleados_cierre = cierre.empleados.all()
            for empleado in empleados_cierre:
                count_registros = empleado.registroconceptoempleado_set.count()
                empleado.registroconceptoempleado_set.all().delete()
                logger.info(f"Eliminados {count_registros} registros de conceptos para empleado {empleado.rut}")
            
            # 2. Eliminar todos los empleados del cierre
            count_empleados = empleados_cierre.count()
            empleados_cierre.delete()
            logger.info(f"Eliminados {count_empleados} empleados del cierre {cierre.id}")
            
            # 3. Resetear estado del cierre a pendiente
            cierre.estado = 'pendiente'
            cierre.estado_incidencias = 'pendiente'
            cierre.save(update_fields=['estado', 'estado_incidencias'])
            
            # 4. Eliminar el libro de remuneraciones (las señales eliminan el archivo automáticamente)
            instance.delete()
            logger.info(f"Libro de remuneraciones {instance.id} eliminado completamente")
        
        logger.info("=== ELIMINACIÓN COMPLETADA ===")
