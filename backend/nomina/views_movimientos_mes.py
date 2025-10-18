"""
Views específicos para MovimientosMes y sus modelos relacionados
Refactorizado desde views.py para mejor organización del código
"""

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import (
    CierreNomina,
    MovimientosMesUpload,
    MovimientoAltaBaja,
    MovimientoAusentismo,
    MovimientoVacaciones,
    MovimientoVariacionSueldo,
    MovimientoVariacionContrato,
)

from .serializers import (
    MovimientosMesUploadSerializer,
    MovimientoAltaBajaSerializer,
    MovimientoAusentismoSerializer,
    MovimientoVacacionesSerializer,
    MovimientoVariacionSueldoSerializer,
    MovimientoVariacionContratoSerializer,
)

# Importar tarea refactorizada desde tasks_refactored/
from .tasks_refactored.movimientos_mes import procesar_movimientos_mes_con_logging

logger = logging.getLogger(__name__)


class MovimientosMesUploadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar la subida y procesamiento de archivos de MovimientosMes"""
    queryset = MovimientosMesUpload.objects.all()
    serializer_class = MovimientosMesUploadSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        """Obtener el estado del archivo de movimientos para un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            movimiento = MovimientosMesUpload.objects.filter(cierre=cierre).first()
            
            if not movimiento:
                return Response({
                    "estado": "no_subido",
                    "mensaje": "No se ha subido ningún archivo de movimientos"
                })
            
            serializer = self.get_serializer(movimiento)
            return Response(serializer.data)
            
        except CierreNomina.DoesNotExist:
            return Response(
                {"error": "Cierre no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error obteniendo estado de movimientos para cierre {cierre_id}: {e}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)')
    def subir(self, request, cierre_id=None):
        """Subir archivo de MovimientosMes con logging integrado"""
        from .utils.mixins import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
        from .utils.clientes import get_client_ip
        from .utils.uploads import guardar_temporal
        from .models_logging import registrar_actividad_tarjeta_nomina
        from .models import ActivityEvent
        
        # 1. OBTENER DATOS DEL REQUEST
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response(
                {"error": "No se proporcionó ningún archivo"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. OBTENER CIERRE Y CLIENTE
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cliente = cierre.cliente
        except CierreNomina.DoesNotExist:
            return Response(
                {"error": "Cierre no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # LOG: Upload iniciado
        ActivityEvent.log(
            user=request.user,
            cliente=cliente,
            cierre=cierre,  # Normalizado
            event_type='upload',
            action='upload_iniciado',
            resource_type='movimientos_mes',
            resource_id=str(cierre.id),
            details={
                                'archivo_nombre': archivo.name,
                'archivo_size': archivo.size,
                'periodo': str(cierre.periodo)
            },
            request=request
        )
        
        # 3. VALIDAR ARCHIVO
        validador = ValidacionArchivoCRUDMixin()
        try:
            validador.validar_archivo(archivo)
        except ValueError as e:
            # LOG: Validación fallida
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
            cierre=cierre,  # Normalizado
                event_type='upload',
                action='validacion_fallida',
                resource_type='movimientos_mes',
                resource_id=str(cierre.id),
                details={
                                        'archivo_nombre': archivo.name,
                    'error': str(e),
                    'tipo_error': 'validacion_archivo'
                },
                request=request
            )
            
            return Response(
                {"error": f"Archivo inválido: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3.5. VALIDAR NOMBRE DE ARCHIVO
        from .utils.validaciones import validar_nombre_archivo_movimientos_mes
        try:
            resultado_validacion = validar_nombre_archivo_movimientos_mes(
                archivo.name, 
                rut_cliente=cliente.rut,
                periodo_cierre=cierre.periodo
            )
            
            if not resultado_validacion['es_valido']:
                errores = resultado_validacion.get('errores', [])
                mensaje_error = '\n'.join(errores) if errores else "Nombre de archivo inválido"
                
                # LOG: Validación de nombre fallida
                ActivityEvent.log(
                    user=request.user,
                    cliente=cliente,
            cierre=cierre,  # Normalizado
                    event_type='upload',
                    action='validacion_nombre_fallida',
                    resource_type='movimientos_mes',
                    resource_id=str(cierre.id),
                    details={
                                                'archivo_nombre': archivo.name,
                        'errores': errores,
                        'tipo_error': 'validacion_nombre'
                    },
                    request=request
                )
                
                return Response(
                    {"error": mensaje_error}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Log de advertencias si las hay
            advertencias = resultado_validacion.get('advertencias', [])
            if advertencias:
                logger.warning(f"Advertencias en validación de archivo {archivo.name}: {advertencias}")
                
        except Exception as e:
            logger.error(f"Error validando nombre de archivo {archivo.name}: {e}")
            
            # LOG: Error validando nombre
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
            cierre=cierre,  # Normalizado
                event_type='error',
                action='error_validacion_nombre',
                resource_type='movimientos_mes',
                resource_id=str(cierre.id),
                details={
                                        'archivo_nombre': archivo.name,
                    'error': str(e),
                    'tipo_error': 'exception_validacion'
                },
                request=request
            )
            
            return Response(
                {"error": "Error interno validando el nombre del archivo"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 4. CREAR UPLOAD LOG
        # 4.5. CREAR UPLOAD LOG - STUB DESHABILITADO
        # TODO: Migrar a ActivityEvent V2
        # mixin = UploadLogNominaMixin()
        # upload_log = mixin.crear_upload_log(cliente, archivo)
        logger.debug(f"[STUB] UploadLog NO creado para MovimientosMes")
        
        # 5. GUARDAR ARCHIVO TEMPORAL - ELIMINADO PARA EVITAR DUPLICACIÓN
        # TODO: Refactorizar para usar solo ubicación definitiva hasta consolidación final
        
        # 6. CREAR/ACTUALIZAR REGISTRO DE MOVIMIENTOS
        movimiento_existente = MovimientosMesUpload.objects.filter(cierre=cierre).first()
        
        if movimiento_existente:
            # Actualizar existente - Las señales se encargan automáticamente de eliminar archivos anteriores
            movimiento_existente.archivo = archivo
            movimiento_existente.estado = "pendiente"
            movimiento_existente.upload_log = None  # STUB: No asignar durante transición
            movimiento_existente.save()
            instance = movimiento_existente
            accion_db = 'actualizado'
        else:
            # Crear nuevo
            instance = MovimientosMesUpload.objects.create(
                cierre=cierre,
                archivo=archivo,
                estado="pendiente",
                upload_log=None  # STUB: No asignar durante transición
            )
            accion_db = 'creado'
        
        logger.info(f"Procesamiento iniciado para MovimientosMes {instance.id}")
        
        # LOG: Archivo validado y guardado
        ActivityEvent.log(
            user=request.user,
            cliente=cliente,
            cierre=cierre,  # Normalizado
            event_type='upload',
            action='archivo_validado',
            resource_type='movimientos_mes',
            resource_id=str(instance.id),
            details={
                                'movimiento_id': instance.id,
                'archivo_nombre': archivo.name,
                'archivo_size': archivo.size,
                'accion_db': accion_db,
                'periodo': str(cierre.periodo)
            },
            request=request
        )
        
        # 7. REGISTRAR ACTIVIDAD - STUB DESHABILITADO
        # TODO: Migrar a ActivityEvent V2
        # registrar_actividad_tarjeta_nomina(...)
        logger.debug(f"[STUB] Actividad NO registrada para MovimientosMes {instance.id}")
        
        # 8. ACTUALIZAR RESUMEN DEL UPLOAD LOG - STUB DESHABILITADO
        # TODO: Migrar a ActivityEvent V2
        # upload_log.resumen = {...}
        # upload_log.save()
        logger.debug(f"[STUB] Resumen NO guardado para MovimientosMes {instance.id}")
        
        # 9. INICIAR PROCESAMIENTO CON CELERY
        try:
            # ✅ Usar tarea refactorizada con logging dual (solo 2 parámetros)
            task = procesar_movimientos_mes_con_logging.delay(instance.id, request.user.id)
            logger.info(f"Tarea Celery iniciada: {task.id} para MovimientosMes {instance.id}")
            
            # LOG: Procesamiento iniciado en Celery
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
            cierre=cierre,  # Normalizado
                event_type='process',
                action='procesamiento_iniciado',
                resource_type='movimientos_mes',
                resource_id=str(instance.id),
                details={
                                        'movimiento_id': instance.id,
                    'celery_task_id': task.id,
                    'archivo_nombre': archivo.name
                },
                request=request
            )
            
        except Exception as e:
            logger.error(f"Error iniciando tarea Celery para MovimientosMes {instance.id}: {e}")
            
            # LOG: Error iniciando procesamiento
            ActivityEvent.log(
                user=request.user,
                cliente=cliente,
            cierre=cierre,  # Normalizado
                event_type='error',
                action='procesamiento_error_inicio',
                resource_type='movimientos_mes',
                resource_id=str(instance.id),
                details={
                                        'movimiento_id': instance.id,
                    'error': str(e),
                    'tipo_error': 'celery_task_error'
                },
                request=request
            )
            
            return Response(
                {"error": "Error iniciando el procesamiento"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 10. RESPUESTA EXITOSA
        serializer = MovimientosMesUploadSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Eliminar archivo de movimientos del mes y todos sus datos relacionados
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        from .models import ActivityEvent
        
        logger = logging.getLogger(__name__)
        cierre = instance.cierre
        cliente = cierre.cliente
        
        # LOG: Archivo eliminado
        ActivityEvent.log(
            user=self.request.user,
            cliente=cliente,
            cierre=instance.cierre,  # Normalizado
            event_type='delete',
            action='archivo_eliminado',
            resource_type='movimientos_mes',
            resource_id=str(instance.id),
            details={
                                'movimiento_id': instance.id,
                'archivo_nombre': instance.archivo.name if instance.archivo else "N/A",
                'estado_anterior': instance.estado,
                'periodo': str(cierre.periodo)
            },
            request=self.request
        )
        
        # Registrar actividad antes de eliminar
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="movimientos_mes",
            accion="delete_archivo",
            descripcion=f"Archivo de movimientos del mes eliminado para resubida",
            usuario=self.request.user,
            detalles={
                "movimiento_id": instance.id,
                "archivo_nombre": instance.archivo.name if instance.archivo else "N/A",
                "estado_anterior": instance.estado
            },
            ip_address=get_client_ip(self.request)
        )
        
        with transaction.atomic():
            # Eliminar registros relacionados
            MovimientoAltaBaja.objects.filter(cierre=cierre).delete()
            MovimientoAusentismo.objects.filter(cierre=cierre).delete()
            MovimientoVacaciones.objects.filter(cierre=cierre).delete()
            MovimientoVariacionSueldo.objects.filter(cierre=cierre).delete()
            MovimientoVariacionContrato.objects.filter(cierre=cierre).delete()
            
            # Eliminar el upload
            instance.delete()
            
        logger.info(f"MovimientosMes {instance.id} y datos relacionados eliminados exitosamente")


class MovimientoAltaBajaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar movimientos de altas y bajas"""
    queryset = MovimientoAltaBaja.objects.all()
    serializer_class = MovimientoAltaBajaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'cierre__cliente').order_by('-fecha_creacion')


class MovimientoAusentismoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar movimientos de ausentismo"""
    queryset = MovimientoAusentismo.objects.all()
    serializer_class = MovimientoAusentismoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'cierre__cliente').order_by('-fecha_creacion')


class MovimientoVacacionesViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar movimientos de vacaciones"""
    queryset = MovimientoVacaciones.objects.all()
    serializer_class = MovimientoVacacionesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'cierre__cliente').order_by('-fecha_creacion')


class MovimientoVariacionSueldoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar movimientos de variación de sueldo"""
    queryset = MovimientoVariacionSueldo.objects.all()
    serializer_class = MovimientoVariacionSueldoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'cierre__cliente').order_by('-fecha_creacion')


class MovimientoVariacionContratoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar movimientos de variación de contrato"""
    queryset = MovimientoVariacionContrato.objects.all()
    serializer_class = MovimientoVariacionContratoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.select_related('cierre', 'cierre__cliente').order_by('-fecha_creacion')
