"""
Views para finalización de cierres contables.

Este módulo maneja los endpoints relacionados con:
- Finalización de cierres
- Consulta de estado de finalización
- Monitoreo de tareas de finalización
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from celery.result import AsyncResult
import logging

from ..models import CierreContabilidad
from api.models import Usuario

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_cierre(request, cierre_id):
    """
    Endpoint para iniciar la finalización de un cierre contable.
    
    POST /api/contabilidad/cierres/{cierre_id}/finalizar/
    
    Response:
    {
        "success": true,
        "mensaje": "Finalización iniciada exitosamente",
        "task_id": "uuid-de-la-tarea",
        "cierre": {
            "id": 123,
            "estado": "generando_reportes",
            "periodo": "2025-06"
        }
    }
    """
    try:
        # Obtener el cierre
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Obtener usuario desde el request
        try:
            usuario = Usuario.objects.get(user=request.user)
        except Usuario.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado en el sistema'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar permisos básicos (puedes agregar más lógica aquí)
        if cierre.cliente != usuario.cliente and not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'No tienes permisos para finalizar este cierre'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que el cierre puede ser finalizado
        puede, mensaje = cierre.puede_finalizar()
        if not puede:
            return Response({
                'success': False,
                'error': mensaje,
                'estado_actual': cierre.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Iniciar la tarea de finalización
        try:
            task_id = cierre.iniciar_finalizacion(usuario=usuario)
            
            logger.info(f"Finalización iniciada para cierre {cierre_id} por usuario {usuario.username}, task_id: {task_id}")
            
            return Response({
                'success': True,
                'mensaje': 'Finalización iniciada exitosamente',
                'task_id': task_id,
                'cierre': {
                    'id': cierre.id,
                    'estado': cierre.estado,
                    'periodo': cierre.periodo,
                    'cliente': cierre.cliente.nombre
                },
                'estimacion_tiempo': 'Aproximadamente 2-5 minutos'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error al iniciar finalización del cierre {cierre_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_finalizacion(request, cierre_id):
    """
    Endpoint para consultar el estado de finalización de un cierre.
    
    GET /api/contabilidad/cierres/{cierre_id}/estado-finalizacion/
    
    Response:
    {
        "cierre": {
            "id": 123,
            "estado": "generando_reportes",
            "puede_finalizar": false,
            "fecha_finalizacion": null,
            "reportes_generados": false
        },
        "tarea_activa": {
            "task_id": "uuid",
            "estado": "PENDING|SUCCESS|FAILURE",
            "progreso": "Paso 2 de 5: Ejecutando cálculos contables..."
        }
    }
    """
    try:
        # Obtener el cierre
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Verificar permisos
        try:
            usuario = Usuario.objects.get(user=request.user)
            if cierre.cliente != usuario.cliente and not request.user.is_superuser:
                return Response({
                    'error': 'No tienes permisos para ver este cierre'
                }, status=status.HTTP_403_FORBIDDEN)
        except Usuario.DoesNotExist:
            if not request.user.is_superuser:
                return Response({
                    'error': 'Usuario no encontrado'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Información del cierre
        puede, motivo = cierre.puede_finalizar()
        
        response_data = {
            'cierre': {
                'id': cierre.id,
                'estado': cierre.estado,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
                'puede_finalizar': puede,
                'motivo_no_finalizar': motivo if not puede else None,
                'fecha_finalizacion': cierre.fecha_finalizacion.isoformat() if cierre.fecha_finalizacion else None,
                'reportes_generados': cierre.reportes_generados,
                'fecha_sin_incidencias': cierre.fecha_sin_incidencias.isoformat() if cierre.fecha_sin_incidencias else None
            }
        }
        
        # Si está en proceso de finalización, buscar la tarea activa
        if cierre.estado == 'generando_reportes':
            # Buscar tareas de finalización activas para este cierre
            # Esto es una aproximación - en producción podrías almacenar el task_id
            tarea_info = buscar_tarea_finalizacion_activa(cierre_id)
            if tarea_info:
                response_data['tarea_activa'] = tarea_info
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al consultar estado de finalización del cierre {cierre_id}: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progreso_tarea(request, task_id):
    """
    Endpoint para consultar el progreso de una tarea específica de finalización.
    
    GET /api/contabilidad/tareas/{task_id}/progreso/
    
    Response:
    {
        "task_id": "uuid",
        "estado": "PENDING|PROGRESS|SUCCESS|FAILURE",
        "resultado": {...},
        "progreso": {
            "paso_actual": 2,
            "total_pasos": 5,
            "descripcion": "Ejecutando cálculos contables...",
            "porcentaje": 40
        }
    }
    """
    try:
        # Obtener la tarea de Celery
        task_result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'estado': task_result.state,
        }
        
        if task_result.state == 'PENDING':
            response_data['mensaje'] = 'Tarea en cola, esperando procesamiento...'
            
        elif task_result.state == 'PROGRESS':
            # Si la tarea está en progreso, obtener información adicional
            info = task_result.info
            response_data['progreso'] = info
            
        elif task_result.state == 'SUCCESS':
            response_data['resultado'] = task_result.result
            response_data['mensaje'] = 'Finalización completada exitosamente'
            
        elif task_result.state == 'FAILURE':
            response_data['error'] = str(task_result.info)
            response_data['mensaje'] = 'Error en la finalización'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al consultar progreso de tarea {task_id}: {str(e)}")
        return Response({
            'error': 'Error al consultar el progreso de la tarea'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cierres_finalizables(request):
    """
    Endpoint para obtener lista de cierres que pueden ser finalizados.
    
    GET /api/contabilidad/cierres-finalizables/
    
    Response:
    {
        "cierres": [
            {
                "id": 123,
                "periodo": "2025-06",
                "cliente": "Empresa ABC",
                "estado": "sin_incidencias",
                "fecha_sin_incidencias": "2025-07-01T10:30:00Z",
                "puede_finalizar": true
            }
        ],
        "total": 1
    }
    """
    try:
        # Obtener usuario
        try:
            usuario = Usuario.objects.get(user=request.user)
            # Filtrar por cliente del usuario (a menos que sea superuser)
            if request.user.is_superuser:
                cierres_qs = CierreContabilidad.objects.all()
            else:
                cierres_qs = CierreContabilidad.objects.filter(cliente=usuario.cliente)
        except Usuario.DoesNotExist:
            if request.user.is_superuser:
                cierres_qs = CierreContabilidad.objects.all()
            else:
                return Response({
                    'error': 'Usuario no encontrado'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrar cierres en estado 'sin_incidencias' (candidatos a finalización)
        cierres_candidatos = cierres_qs.filter(estado='sin_incidencias').order_by('-fecha_sin_incidencias')
        
        cierres_data = []
        for cierre in cierres_candidatos:
            puede, motivo = cierre.puede_finalizar()
            cierres_data.append({
                'id': cierre.id,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
                'estado': cierre.estado,
                'fecha_sin_incidencias': cierre.fecha_sin_incidencias.isoformat() if cierre.fecha_sin_incidencias else None,
                'puede_finalizar': puede,
                'motivo_no_finalizar': motivo if not puede else None,
                'dias_sin_incidencias': (timezone.now() - cierre.fecha_sin_incidencias).days if cierre.fecha_sin_incidencias else 0
            })
        
        return Response({
            'cierres': cierres_data,
            'total': len(cierres_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al obtener cierres finalizables: {str(e)}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actualizar_estado_cierre(request, cierre_id):
    """
    Endpoint para forzar la actualización del estado de un cierre.
    
    POST /api/contabilidad/cierres/{cierre_id}/actualizar-estado/
    
    Response:
    {
        "success": true,
        "cierre": {
            "id": 123,
            "estado_anterior": "incidencias_abiertas",
            "estado_nuevo": "sin_incidencias",
            "puede_finalizar": true
        }
    }
    """
    try:
        # Obtener el cierre
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Verificar permisos
        try:
            usuario = Usuario.objects.get(user=request.user)
            if cierre.cliente != usuario.cliente and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'No tienes permisos para actualizar este cierre'
                }, status=status.HTTP_403_FORBIDDEN)
        except Usuario.DoesNotExist:
            if not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'Usuario no encontrado'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar estado anterior
        estado_anterior = cierre.estado
        
        # Forzar actualización del estado
        estado_nuevo = cierre.actualizar_estado_automatico()
        
        # Verificar si puede finalizar
        puede_finalizar, motivo = cierre.puede_finalizar()
        
        logger.info(f"Estado de cierre {cierre_id} actualizado: {estado_anterior} -> {estado_nuevo}")
        
        return Response({
            'success': True,
            'cierre': {
                'id': cierre.id,
                'estado_anterior': estado_anterior,
                'estado_nuevo': estado_nuevo,
                'cambio_estado': estado_anterior != estado_nuevo,
                'puede_finalizar': puede_finalizar,
                'motivo_no_finalizar': motivo if not puede_finalizar else None,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al actualizar estado del cierre {cierre_id}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def buscar_tarea_finalizacion_activa(cierre_id):
    """
    Helper para buscar tareas activas de finalización para un cierre.
    
    Nota: Esta es una implementación básica. En producción podrías:
    1. Almacenar el task_id en la base de datos
    2. Usar Redis para trackear tareas activas
    3. Implementar un sistema más robusto de seguimiento
    """
    try:
        from celery import current_app
        
        # Obtener tareas activas (esto es una aproximación)
        inspect = current_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return None
        
        # Buscar tareas de finalización para este cierre
        for worker, tasks in active_tasks.items():
            for task in tasks:
                if (task.get('name') == 'contabilidad.finalizar_cierre_y_generar_reportes' and 
                    task.get('args') and len(task['args']) > 0 and 
                    task['args'][0] == cierre_id):
                    
                    return {
                        'task_id': task['id'],
                        'estado': 'RUNNING',
                        'worker': worker,
                        'descripcion': 'Procesando finalización...'
                    }
        
        return None
        
    except Exception as e:
        logger.warning(f"No se pudo obtener información de tareas activas: {str(e)}")
        return None
