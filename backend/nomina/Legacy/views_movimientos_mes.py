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

from .tasks import procesar_movimientos_mes

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
        
        # 3. VALIDAR ARCHIVO
        validador = ValidacionArchivoCRUDMixin()
        try:
            validador.validar_archivo(archivo)
        except ValueError as e:
            return Response(
                {"error": f"Archivo inválido: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 4. CREAR UPLOAD LOG
        mixin = UploadLogNominaMixin()
        mixin.tipo_upload = "movimientos_mes"
        mixin.usuario = request.user
        mixin.ip_usuario = get_client_ip(request)
        
        upload_log = mixin.crear_upload_log(cliente, archivo)
        logger.info(f"Upload log creado para MovimientosMes con ID: {upload_log.id}")
        
        # 5. GUARDAR ARCHIVO TEMPORAL
        nombre_temporal = f"movimientos_mes_cierre_{cierre_id}_{upload_log.id}.xlsx"
        ruta_temporal = guardar_temporal(nombre_temporal, archivo)
        upload_log.ruta_archivo = ruta_temporal
        upload_log.cierre = cierre
        upload_log.save()
        
        # 6. CREAR/ACTUALIZAR REGISTRO DE MOVIMIENTOS
        movimiento_existente = MovimientosMesUpload.objects.filter(cierre=cierre).first()
        
        if movimiento_existente:
            # Actualizar existente
            movimiento_existente.archivo = archivo
            movimiento_existente.estado = "subido"
            movimiento_existente.upload_log = upload_log
            movimiento_existente.save()
            instance = movimiento_existente
        else:
            # Crear nuevo
            instance = MovimientosMesUpload.objects.create(
                cierre=cierre,
                archivo=archivo,
                estado="subido",
                upload_log=upload_log
            )
        
        logger.info(f"Procesamiento iniciado para MovimientosMes {instance.id} con UploadLog {upload_log.id}")
        
        # 7. REGISTRAR ACTIVIDAD
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="movimientos_mes",
            accion="upload_excel",
            descripcion=f"Archivo {archivo.name} subido para procesamiento",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "tamaño_archivo": archivo.size,
                "upload_log_id": upload_log.id,
                "movimiento_id": instance.id
            },
            ip_address=get_client_ip(request),
            upload_log=upload_log
        )
        
        # 8. ACTUALIZAR RESUMEN DEL UPLOAD LOG
        upload_log.resumen = {
            "movimiento_id": instance.id,
            "cierre_id": cierre_id,
            "cliente_id": cliente.id,
            "archivo_original": archivo.name
        }
        upload_log.save(update_fields=['resumen'])
        
        # 9. INICIAR PROCESAMIENTO CON CELERY
        try:
            task = procesar_movimientos_mes.delay(instance.id, upload_log.id)
            
            # Verificar si el modelo tiene el campo celery_task_id antes de asignarlo
            if hasattr(upload_log, 'celery_task_id'):
                upload_log.celery_task_id = task.id
                upload_log.save(update_fields=['celery_task_id'])
            else:
                # Si no tiene el campo, guardar en resumen
                if upload_log.resumen is None:
                    upload_log.resumen = {}
                upload_log.resumen["celery_task_id"] = task.id
                upload_log.save(update_fields=['resumen'])
            
            logger.info(f"Tarea Celery iniciada: {task.id} para MovimientosMes {instance.id}")
            
        except Exception as e:
            logger.error(f"Error iniciando tarea Celery para MovimientosMes {instance.id}: {e}")
            upload_log.estado = "error"
            upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
            upload_log.save()
            
            return Response(
                {"error": "Error iniciando el procesamiento"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 10. RESPUESTA EXITOSA
        serializer = MovimientosMesUploadSerializer(instance)
        response_data = serializer.data
        response_data['upload_log_id'] = upload_log.id
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Eliminar archivo de movimientos del mes y todos sus datos relacionados
        """
        from .models_logging import registrar_actividad_tarjeta_nomina
        from .utils.clientes import get_client_ip
        
        logger = logging.getLogger(__name__)
        cierre = instance.cierre
        
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
