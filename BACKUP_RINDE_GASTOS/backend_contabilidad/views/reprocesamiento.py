# views/reprocesamiento.py

import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    CierreContabilidad, 
    UploadLog, 
    LibroMayorArchivo,
    MovimientoContable,
    AperturaCuenta,
    Incidencia,
    ExcepcionClasificacionSet
)
from ..tasks_libro_mayor import crear_chain_libro_mayor

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reprocesar_libro_mayor_con_excepciones(request):
    """
    Reprocesa el Libro Mayor creando una nueva iteración.
    
    Flujo:
    1. Buscar el UploadLog del Libro Mayor completado más reciente
    2. Crear nueva iteración (nuevo UploadLog)
    3. Limpiar datos de movimientos e incidencias anteriores
    4. Reprocesar usando el archivo existente con las excepciones aplicadas
    5. Generar nuevo snapshot
    """
    cierre_id = request.data.get('cierre_id')
    
    if not cierre_id:
        return Response(
            {'error': 'cierre_id es requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Obtener el cierre
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        # Buscar el UploadLog más reciente del libro mayor para este cierre
        upload_log_anterior = UploadLog.objects.filter(
            cierre=cierre,
            tipo_upload='libro_mayor',
            estado='completado'
        ).order_by('-iteracion', '-fecha_subida').first()
        
        if not upload_log_anterior:
            return Response(
                {'error': 'No se encontró un procesamiento previo del Libro Mayor para este cierre'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que existe el archivo
        libro_mayor_archivo = LibroMayorArchivo.objects.filter(
            cierre=cierre,
            upload_log=upload_log_anterior
        ).first()
        
        if not libro_mayor_archivo or not libro_mayor_archivo.archivo:
            return Response(
                {'error': 'No se encontró el archivo del Libro Mayor para reprocesar'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear nueva iteración
        nueva_iteracion = crear_nueva_iteracion_reprocesamiento(
            upload_log_anterior, 
            libro_mayor_archivo,
            request.user,
            motivo="Reprocesamiento con excepciones aplicadas"
        )
        
        # Log para verificar que las excepciones están disponibles
        excepciones_activas = ExcepcionClasificacionSet.objects.filter(
            cliente=cierre.cliente, 
            activa=True
        ).count()
        logger.info(f"Reprocesamiento iniciado - Excepciones de clasificación activas: {excepciones_activas}")
        
        logger.info(f"Nueva iteración creada: {nueva_iteracion.id} "
                   f"(iteración {nueva_iteracion.iteracion}) para cierre {cierre_id}")
        
        return Response({
            'mensaje': 'Reprocesamiento iniciado correctamente',
            'nueva_iteracion': nueva_iteracion.iteracion,
            'upload_log_id': nueva_iteracion.id,
            'cierre_id': cierre_id,
            'estado': 'procesando'
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response(
            {'error': f'Cierre {cierre_id} no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error en reprocesamiento: {e}")
        return Response(
            {'error': f'Error interno: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def crear_nueva_iteracion_reprocesamiento(upload_log_anterior, libro_mayor_archivo, usuario, motivo="Reprocesamiento"):
    """
    Crea una nueva iteración de reprocesamiento basada en un UploadLog anterior
    """
    try:
        with transaction.atomic():
            # Marcar iteración anterior como no principal
            upload_log_anterior.es_iteracion_principal = False
            upload_log_anterior.save(update_fields=['es_iteracion_principal'])
            
            # Crear nueva iteración
            nueva_iteracion = UploadLog.objects.create(
                tipo_upload=upload_log_anterior.tipo_upload,
                cliente=upload_log_anterior.cliente,
                cierre=upload_log_anterior.cierre,
                usuario=usuario,
                nombre_archivo_original=upload_log_anterior.nombre_archivo_original,
                ruta_archivo=upload_log_anterior.ruta_archivo,  # Reutilizar archivo
                tamaño_archivo=upload_log_anterior.tamaño_archivo,
                hash_archivo=upload_log_anterior.hash_archivo,
                estado='procesando',
                iteracion=upload_log_anterior.iteracion + 1,
                es_iteracion_principal=True,
                resumen={
                    'reprocesamiento': {
                        'motivo': motivo,
                        'iteracion_anterior': upload_log_anterior.iteracion,
                        'upload_log_anterior_id': upload_log_anterior.id,
                        'timestamp_inicio': timezone.now().isoformat()
                    }
                }
            )
            
            # Limpiar datos anteriores del cierre para reprocesar limpio
            limpiar_datos_cierre_para_reprocesamiento(upload_log_anterior.cierre)
            
            # Preparar archivo para reprocesamiento desde LibroMayorArchivo
            if libro_mayor_archivo and libro_mayor_archivo.archivo:
                nueva_ruta_archivo = preparar_archivo_para_reprocesamiento(
                    libro_mayor_archivo, 
                    nueva_iteracion
                )
                # Actualizar la ruta en el nuevo UploadLog
                nueva_iteracion.ruta_archivo = nueva_ruta_archivo
                nueva_iteracion.save(update_fields=['ruta_archivo'])
                logger.info(f"Archivo preparado para reprocesamiento: {nueva_ruta_archivo}")
            else:
                raise ValueError("No se encontró archivo válido para reprocesamiento")
            
            # Iniciar cadena de reprocesamiento
            chain_result = crear_chain_libro_mayor(
                nueva_iteracion.id, 
                usuario.correo_bdo
            )
            
            # Iniciar la cadena
            chain_result.apply_async()
            
            logger.info(f"Chain de reprocesamiento iniciado para upload_log {nueva_iteracion.id}")
            
            return nueva_iteracion
            
    except Exception as e:
        logger.error(f"Error creando nueva iteración: {e}")
        raise


def preparar_archivo_para_reprocesamiento(libro_mayor_archivo, nueva_iteracion):
    """
    Copia el archivo desde LibroMayorArchivo a una nueva ubicación temporal para reprocesamiento
    """
    import os
    import shutil
    from django.core.files.storage import default_storage
    from django.utils import timezone
    
    try:
        # Leer el archivo original desde LibroMayorArchivo
        archivo_original = libro_mayor_archivo.archivo
        
        if not archivo_original:
            raise ValueError("No hay archivo en LibroMayorArchivo")
        
        # Crear nueva ruta temporal para reprocesamiento
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        nuevo_nombre = f"reproceso_{nueva_iteracion.id}_{timestamp}.xlsx"
        nueva_ruta_relativa = f"temp/{nuevo_nombre}"
        nueva_ruta_completa = default_storage.path(nueva_ruta_relativa)
        
        # Asegurarse de que existe el directorio
        os.makedirs(os.path.dirname(nueva_ruta_completa), exist_ok=True)
        
        # Copiar el archivo
        with archivo_original.open('rb') as src:
            with open(nueva_ruta_completa, 'wb') as dst:
                shutil.copyfileobj(src, dst)
        
        logger.info(f"Archivo copiado para reprocesamiento: {nueva_ruta_relativa}")
        logger.info(f"Tamaño del archivo: {os.path.getsize(nueva_ruta_completa)} bytes")
        
        return nueva_ruta_relativa
        
    except Exception as e:
        logger.error(f"Error preparando archivo para reprocesamiento: {e}")
        raise


def limpiar_datos_cierre_para_reprocesamiento(cierre):
    """
    Limpia los datos de movimientos e incidencias del cierre para reprocesamiento limpio
    y cambia el estado del cierre para permitir regeneración de reportes
    """
    try:
        with transaction.atomic():
            # Guardar estado anterior para logging
            estado_anterior = cierre.estado
            
            # Cambiar estado del cierre para permitir regeneración de reportes
            # Si está finalizado/aprobado, volver a sin_incidencias para permitir nuevos reportes
            if cierre.estado in ['finalizado', 'aprobado']:
                cierre.estado = 'sin_incidencias'
                cierre.fecha_finalizacion = None  # Limpiar fecha de finalización
                cierre.save(update_fields=['estado', 'fecha_finalizacion'])
                logger.info(f"Estado del cierre {cierre.id} cambiado de '{estado_anterior}' a '{cierre.estado}' para reprocesamiento")
            
            # Eliminar movimientos contables
            movimientos_eliminados = MovimientoContable.objects.filter(cierre=cierre).count()
            MovimientoContable.objects.filter(cierre=cierre).delete()
            
            # Eliminar aperturas de cuenta
            aperturas_eliminadas = AperturaCuenta.objects.filter(cierre=cierre).count()
            AperturaCuenta.objects.filter(cierre=cierre).delete()
            
            # Eliminar incidencias
            incidencias_eliminadas = Incidencia.objects.filter(cierre=cierre).count()
            Incidencia.objects.filter(cierre=cierre).delete()
            
            logger.info(f"Limpieza completada para cierre {cierre.id}: "
                       f"{movimientos_eliminados} movimientos, "
                       f"{aperturas_eliminadas} aperturas, "
                       f"{incidencias_eliminadas} incidencias eliminadas")
                       
    except Exception as e:
        logger.error(f"Error limpiando datos del cierre {cierre.id}: {e}")
        raise


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_historial_reprocesamiento(request, cierre_id):
    """
    Obtiene el historial de reprocesamiento para un cierre específico
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        historiales = UploadLog.objects.filter(
            cierre=cierre,
            tipo_upload='libro_mayor'
        ).order_by('-iteracion', '-fecha_subida')
        
        historial_data = []
        for upload in historiales:
            # Obtener estadísticas del snapshot si existe
            snapshot = upload.resumen.get('incidencias_snapshot', {}) if upload.resumen else {}
            estadisticas_snapshot = snapshot.get('estadisticas', {})
            
            historial_data.append({
                'iteracion': upload.iteracion,
                'fecha': upload.fecha_subida.isoformat(),
                'usuario': upload.usuario.correo_bdo if upload.usuario else 'Sistema',
                'estado': upload.estado,
                'es_principal': upload.es_iteracion_principal,
                'estadisticas': {
                    'incidencias': estadisticas_snapshot.get('total_incidencias', 0),
                    'elementos_afectados': snapshot.get('total_elementos_afectados', 0),
                    'procesamiento': upload.resumen.get('procesamiento', {}) if upload.resumen else {}
                },
                'motivo': (upload.resumen.get('reprocesamiento', {}) if upload.resumen else {}).get('motivo', 'Procesamiento inicial')
            })
        
        return Response({
            'cierre_id': cierre_id,
            'total_iteraciones': len(historial_data),
            'iteracion_actual': historial_data[0]['iteracion'] if historial_data else 0,
            'historial': historial_data
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response(
            {'error': f'Cierre {cierre_id} no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return Response(
            {'error': f'Error interno: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_iteracion_principal(request):
    """
    Cambia cuál iteración es la principal (la que se muestra por defecto)
    """
    cierre_id = request.data.get('cierre_id')
    nueva_iteracion = request.data.get('iteracion')
    
    if not cierre_id or nueva_iteracion is None:
        return Response(
            {'error': 'cierre_id e iteracion son requeridos'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        with transaction.atomic():
            # Desmarcar todas las iteraciones como principales
            UploadLog.objects.filter(
                cierre=cierre,
                tipo_upload='libro_mayor'
            ).update(es_iteracion_principal=False)
            
            # Marcar la nueva iteración como principal
            upload_actualizado = UploadLog.objects.filter(
                cierre=cierre,
                tipo_upload='libro_mayor',
                iteracion=nueva_iteracion
            ).update(es_iteracion_principal=True)
            
            if not upload_actualizado:
                return Response(
                    {'error': f'Iteración {nueva_iteracion} no encontrada'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        logger.info(f"Iteración principal cambiada a {nueva_iteracion} para cierre {cierre_id}")
        
        return Response({
            'mensaje': f'Iteración {nueva_iteracion} marcada como principal',
            'cierre_id': cierre_id,
            'nueva_iteracion_principal': nueva_iteracion
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response(
            {'error': f'Cierre {cierre_id} no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error cambiando iteración principal: {e}")
        return Response(
            {'error': f'Error interno: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
