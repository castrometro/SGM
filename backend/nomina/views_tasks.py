"""
🚀 VIEWS PARA MANEJO ASÍNCRONO DE INFORMES DE NÓMINA

Este módulo proporciona endpoints para:
- Finalización asíncrona de cierres
- Monitoreo de progreso de tasks
- Consulta de resultados
- Gestión de informes

Autor: Sistema SGM
Fecha: Agosto 2024
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import logging
import json

from .models import CierreNomina
from .models_informe import InformeNomina
from .tasks_informes import (
    generar_informe_nomina_completo,
    regenerar_informe_existente,
    verificar_estado_informe,
    obtener_progreso_task
)

logger = logging.getLogger(__name__)

# ============================================================================
#                           ENDPOINTS PRINCIPALES
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_cierre_async(request, cierre_id):
    """
    🚀 POST /api/nomina/finalizar-async/{cierre_id}/
    
    Inicia la finalización asíncrona de un cierre de nómina
    
    Body (opcional):
    {
        "forzar_async": true,  // Forzar modo asíncrono
        "modo": "completo"     // completo, rapido, solo_kpis
    }
    
    Response:
    {
        "success": true,
        "task_id": "uuid-del-task",
        "mensaje": "Proceso iniciado",
        "cierre_id": 123,
        "modo": "asincrono"
    }
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)
        
        # Validar permisos (aquí podrías agregar validaciones específicas)
        
        # Obtener parámetros del request
        data = request.data if hasattr(request, 'data') else {}
        forzar_async = data.get('forzar_async', True)
        modo = data.get('modo', 'completo')
        
        # Verificar que se puede finalizar
        puede, razon = cierre.puede_finalizar()
        if not puede:
            return Response({
                'error': f'No se puede finalizar el cierre: {razon}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya hay un task activo
        task_activo = cierre.get_task_activo()
        if task_activo:
            return Response({
                'error': 'Ya hay un proceso de finalización en curso',
                'task_activo': task_activo
            }, status=status.HTTP_409_CONFLICT)
        
        # Iniciar finalización asíncrona
        if forzar_async:
            resultado = cierre.iniciar_finalizacion_asincrona(request.user)
        else:
            # Usar el método híbrido que decide automáticamente
            resultado = cierre.finalizar_cierre(request.user, usar_tasks=True)
        
        logger.info(f"Finalización asíncrona iniciada para cierre {cierre_id} por {request.user}")
        
        return Response(resultado, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error iniciando finalización asíncrona para cierre {cierre_id}: {str(e)}")
        return Response({
            'error': f'Error iniciando proceso: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progreso_task(request, task_id):
    """
    📊 GET /api/nomina/task-progreso/{task_id}/
    
    Consulta el progreso de un task de finalización
    
    Response:
    {
        "state": "PROGRESS",
        "descripcion": "Calculando KPIs...",
        "porcentaje": 45,
        "paso_actual": 3,
        "total_pasos": 8,
        "tiempo_transcurrido": 12.5,
        "cierre_id": 123
    }
    """
    try:
        progreso = obtener_progreso_task(task_id)
        return Response(progreso, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error consultando progreso del task {task_id}: {str(e)}")
        return Response({
            'error': f'Error consultando progreso: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resultado_task(request, task_id):
    """
    📋 GET /api/nomina/task-resultado/{task_id}/
    
    Obtiene el resultado final de un task completado
    
    Response (si exitoso):
    {
        "success": true,
        "informe_id": 456,
        "cierre_id": 123,
        "duracion_segundos": 15.2,
        "estadisticas": {...},
        "kpis_principales": {...},
        "datos_resumen": {...}
    }
    """
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        if result.state == 'PENDING':
            return Response({
                'state': 'PENDING',
                'mensaje': 'Task aún no iniciado'
            }, status=status.HTTP_202_ACCEPTED)
            
        elif result.state == 'PROGRESS':
            return Response({
                'state': 'PROGRESS',
                'mensaje': 'Task aún en progreso',
                'progreso': result.result
            }, status=status.HTTP_202_ACCEPTED)
            
        elif result.state == 'SUCCESS':
            return Response({
                'state': 'SUCCESS',
                'resultado': result.result
            }, status=status.HTTP_200_OK)
            
        elif result.state == 'FAILURE':
            return Response({
                'state': 'FAILURE',
                'error': str(result.result)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        else:
            return Response({
                'state': result.state,
                'mensaje': f'Estado desconocido: {result.state}'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error obteniendo resultado del task {task_id}: {str(e)}")
        return Response({
            'error': f'Error obteniendo resultado: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_task(request, task_id):
    """
    ❌ POST /api/nomina/task-cancelar/{task_id}/
    
    Cancela un task en progreso
    """
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        if result.state in ['PENDING', 'PROGRESS']:
            result.revoke(terminate=True)
            
            return Response({
                'success': True,
                'mensaje': 'Task cancelado exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': f'No se puede cancelar task en estado: {result.state}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error cancelando task {task_id}: {str(e)}")
        return Response({
            'error': f'Error cancelando task: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
#                           ENDPOINTS DE GESTIÓN
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerar_informe(request, cierre_id):
    """
    🔄 POST /api/nomina/regenerar-informe/{cierre_id}/
    
    Regenera un informe existente de forma asíncrona
    
    Body (opcional):
    {
        "forzar": true  // Regenerar aunque el cierre no esté finalizado
    }
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)
        
        # Obtener parámetros
        data = request.data if hasattr(request, 'data') else {}
        forzar = data.get('forzar', False)
        
        # Validar estado
        if cierre.estado != 'finalizado' and not forzar:
            return Response({
                'error': 'Solo se pueden regenerar informes de cierres finalizados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Iniciar regeneración
        task = regenerar_informe_existente.delay(
            cierre_id=cierre_id,
            usuario_id=request.user.id,
            forzar=forzar
        )
        
        logger.info(f"Regeneración de informe iniciada para cierre {cierre_id} por {request.user}")
        
        return Response({
            'success': True,
            'task_id': task.id,
            'mensaje': 'Regeneración de informe iniciada',
            'cierre_id': cierre_id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Error iniciando regeneración para cierre {cierre_id}: {str(e)}")
        return Response({
            'error': f'Error iniciando regeneración: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_informe(request, cierre_id):
    """
    🔍 GET /api/nomina/estado-informe/{cierre_id}/
    
    Consulta el estado actual de un informe
    
    Response:
    {
        "cierre_id": 123,
        "estado_cierre": "finalizado",
        "estado_informe": "generado",
        "fecha_generacion": "2024-08-04T15:30:00Z",
        "tiempo_calculo_segundos": 12.5,
        "tiene_informe": true
    }
    """
    try:
        resultado = verificar_estado_informe.delay(cierre_id).get()
        return Response(resultado, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error consultando estado de informe {cierre_id}: {str(e)}")
        return Response({
            'error': f'Error consultando estado: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
#                           ENDPOINTS HÍBRIDOS
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_cierre_hibrido(request, cierre_id):
    """
    ⚡ POST /api/nomina/finalizar/{cierre_id}/
    
    Finalización híbrida que decide automáticamente entre sync/async
    
    Body (opcional):
    {
        "forzar_async": false,    // true para forzar async
        "forzar_sync": false,     // true para forzar sync
        "threshold_empleados": 200 // umbral para decidir modo
    }
    
    Response (sync):
    {
        "success": true,
        "modo": "sincrono",
        "informe_id": 456,
        "datos_cierre": {...}
    }
    
    Response (async):
    {
        "success": true,
        "modo": "asincrono", 
        "task_id": "uuid",
        "mensaje": "Proceso iniciado"
    }
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)
        
        # Obtener parámetros
        data = request.data if hasattr(request, 'data') else {}
        forzar_async = data.get('forzar_async', False)
        forzar_sync = data.get('forzar_sync', False)
        threshold = data.get('threshold_empleados', 200)
        
        # Validar que se puede finalizar
        puede, razon = cierre.puede_finalizar()
        if not puede:
            return Response({
                'error': f'No se puede finalizar el cierre: {razon}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decidir modo
        usar_tasks = None
        if forzar_async:
            usar_tasks = True
        elif forzar_sync:
            usar_tasks = False
        else:
            # Auto-decidir basado en número de empleados
            total_empleados = cierre.empleados.count()
            usar_tasks = total_empleados > threshold
        
        # Ejecutar finalización
        resultado = cierre.finalizar_cierre(request.user, usar_tasks=usar_tasks)
        
        logger.info(f"Finalización híbrida completada para cierre {cierre_id} en modo {resultado.get('modo')}")
        
        if resultado.get('modo') == 'asincrono':
            return Response(resultado, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(resultado, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en finalización híbrida para cierre {cierre_id}: {str(e)}")
        return Response({
            'error': f'Error en finalización: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
#                           UTILIDADES Y MONITORING
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tasks_activos(request):
    """
    📊 GET /api/nomina/tasks-activos/
    
    Lista todos los tasks activos de nómina
    """
    try:
        # Aquí podrías implementar lógica para obtener tasks activos
        # Por simplicidad, retornamos cierres en estado 'generando_informe'
        
        cierres_procesando = CierreNomina.objects.filter(
            estado='generando_informe'
        ).values(
            'id', 'cliente__nombre', 'periodo', 'estado'
        )
        
        return Response({
            'tasks_activos': list(cierres_procesando),
            'total': len(cierres_procesando)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo tasks activos: {str(e)}")
        return Response({
            'error': f'Error obteniendo tasks: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def estadisticas_tasks(request):
    """
    📈 GET /api/nomina/estadisticas-tasks/
    
    Estadísticas de uso de tasks de nómina
    """
    try:
        from .tasks_informes import generar_estadisticas_informes
        
        estadisticas = generar_estadisticas_informes.delay().get()
        
        return Response(estadisticas, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return Response({
            'error': f'Error obteniendo estadísticas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
