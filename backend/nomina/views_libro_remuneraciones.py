# nomina/views_libro_remuneraciones.py

import logging
import os
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from celery import chain

from .models import CierreNomina, LibroRemuneracionesUpload
from .serializers import LibroRemuneracionesUploadSerializer
from .utils.mixins import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
from .utils.clientes import get_client_ip
from .utils.uploads import guardar_temporal
from .models_logging import registrar_actividad_tarjeta_nomina
from .tasks import (
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
        
        # 3. VALIDAR ARCHIVO
        try:
            validator = ValidacionArchivoCRUDMixin()
            validator.validar_archivo(archivo)
            logger.info(f"Archivo {archivo.name} validado correctamente")
            
            # 3.5. VALIDAR NOMBRE ESPECÍFICO DEL ARCHIVO
            periodo_formato = cierre.periodo.replace("-", "")  # "2025-08" → "202508"
            rut_sin_guion = cliente.rut.replace("-", "")       # "12345678-9" → "123456789"
            patron_regex = f"^{periodo_formato}_libro_remuneraciones_{rut_sin_guion}(_.*)?\\.(xlsx|xls)$"
            
            logger.info(f"Validando nombre de archivo con patrón: {patron_regex}")
            validator.validar_nombre_archivo(archivo.name, patron_regex)
            logger.info(f"Nombre de archivo {archivo.name} válido")
            
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
        
        # 5. GUARDAR ARCHIVO TEMPORAL - COMENTADO TEMPORALMENTE
        # TODO: Refactorizar para usar solo temporal hasta consolidación final
        # nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
        # ruta = guardar_temporal(nombre_temporal, archivo)
        # upload_log.ruta_archivo = ruta
        upload_log.cierre = cierre
        upload_log.save()
        
        # 6. CREAR/ACTUALIZAR REGISTRO DE LIBRO
        with transaction.atomic():
            libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
            
            if libro_existente:
                # Las señales se encargan automáticamente de eliminar archivos anteriores
                libro_existente.archivo = archivo
                libro_existente.estado = 'pendiente'
                libro_existente.header_json = []
                libro_existente.upload_log = upload_log
                libro_existente.fecha_subida = timezone.now()
                libro_existente.save()
                instance = libro_existente
                logger.info(f"Libro actualizado con ID: {instance.id}")
                
                # Actualizar upload_log con la nueva ruta definitiva
                upload_log.ruta_archivo = instance.archivo.path
                upload_log.save(update_fields=['ruta_archivo'])
                logger.info(f"Upload log actualizado con nueva ruta: {instance.archivo.path}")
            else:
                # Crear nuevo
                instance = serializer.save(
                    cierre=cierre,
                    upload_log=upload_log,
                    estado='pendiente'
                )
                logger.info(f"Libro creado con ID: {instance.id}")
        
        # 6.5. ACTUALIZAR UPLOAD_LOG CON RUTA DEFINITIVA
        upload_log.ruta_archivo = instance.archivo.path
        upload_log.save(update_fields=['ruta_archivo'])
        logger.info(f"Upload log actualizado con ruta definitiva: {instance.archivo.path}")
        
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
                "upload_log_id": upload_log.id,
                "libro_id": instance.id
            },
            ip_address=get_client_ip(request),
            upload_log=upload_log
        )
        
        # 8. GUARDAR LIBRO_ID EN RESUMEN DEL UPLOAD_LOG
        upload_log.resumen = {
            "libro_id": instance.id,
            "cierre_id": cierre_id,
            "cliente_id": cliente.id,
            "archivo_original": archivo.name
        }
        upload_log.save(update_fields=['resumen'])
        
        # 9. INICIAR PROCESAMIENTO CON CELERY
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
        
        logger.info("=== SUBIDA DE LIBRO DE REMUNERACIONES COMPLETADA ===")

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
        
        # Cambiar estado a procesando
        libro.estado = 'procesando'
        libro.save(update_fields=['estado'])
        
        # Leer parámetros opcionales - optimización activada por defecto
        usar_optimizacion = request.data.get('usar_optimizacion', True) if hasattr(request, 'data') and request.data else True
        
        logger.info(f"🔄 Iniciando procesamiento de libro {libro.id}, optimización: {usar_optimizacion}")
        
        # Registrar actividad
        registrar_actividad_tarjeta_nomina(
            cierre_id=libro.cierre.id,
            tarjeta="libro_remuneraciones",
            accion="procesar_libro",
            descripcion=f"Iniciando procesamiento completo del libro de remuneraciones (optimizado: {usar_optimizacion})",
            usuario=request.user,
            detalles={
                "libro_id": libro.id,
                "optimizado": usar_optimizacion
            },
            ip_address=get_client_ip(request)
        )
        
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
