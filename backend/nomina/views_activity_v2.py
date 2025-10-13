# backend/nomina/views_activity_v2.py
"""
API endpoints para Activity Logging V2
Sistema unificado y simplificado
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
import json
import logging

from .models_activity_v2 import ActivityEvent, log_user_activity

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_single_activity(request):
    """
    Endpoint principal para logging individual
    
    POST /api/activity/
    {
        "cierre_id": 123,
        "modulo": "nomina",
        "seccion": "libro_remuneraciones", 
        "evento": "file_upload",
        "datos": {"filename": "libro.xlsx", "size": 1024}
    }
    """
    try:
        data = request.data
        
        # Validar campos requeridos
        required_fields = ['cierre_id', 'seccion', 'evento']
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response({
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar helper para registrar
        activity = log_user_activity(
            request=request,
            cierre_id=data['cierre_id'],
            modulo=data.get('modulo', 'nomina'),
            seccion=data['seccion'],
            evento=data['evento'],
            datos=data.get('datos', {})
        )
        
        return Response({
            'success': True,
            'activity_id': activity.id if activity else None,
            'message': 'Actividad registrada correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en log_single_activity: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_batch_activities(request):
    """
    Endpoint para logging en lotes (mejor performance)
    
    POST /api/activity/batch/
    {
        "events": [
            {
                "cierre_id": 123,
                "seccion": "libro_remuneraciones",
                "evento": "file_select",
                "datos": {"filename": "libro.xlsx"}
            },
            {
                "cierre_id": 123,
                "seccion": "libro_remuneraciones", 
                "evento": "file_upload",
                "datos": {"filename": "libro.xlsx", "success": true}
            }
        ]
    }
    """
    try:
        data = request.data
        events = data.get('events', [])
        
        if not events or not isinstance(events, list):
            return Response({
                'error': 'Se requiere una lista de eventos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(events) > 50:  # Limitar tamaño del batch
            return Response({
                'error': 'Máximo 50 eventos por batch'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        successful_count = 0
        failed_count = 0
        
        for event_data in events:
            # Validar cada evento
            if not all(k in event_data for k in ['cierre_id', 'seccion', 'evento']):
                failed_count += 1
                continue
                
            # Registrar evento
            activity = log_user_activity(
                request=request,
                cierre_id=event_data['cierre_id'],
                modulo=event_data.get('modulo', 'nomina'),
                seccion=event_data['seccion'],
                evento=event_data['evento'],
                datos=event_data.get('datos', {})
            )
            
            if activity:
                successful_count += 1
            else:
                failed_count += 1
        
        return Response({
            'success': True,
            'processed': len(events),
            'successful': successful_count,
            'failed': failed_count,
            'message': f'Batch procesado: {successful_count} exitosos, {failed_count} fallidos'
        })
        
    except Exception as e:
        logger.error(f"Error en log_batch_activities: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_stats(request, cierre_id):
    """
    Obtiene estadísticas de actividad para un cierre
    
    GET /api/activity/stats/{cierre_id}/
    ?seccion=libro_remuneraciones&days=7
    """
    try:
        # Filtros
        seccion = request.GET.get('seccion')
        days = int(request.GET.get('days', 7))
        
        # Query base
        queryset = ActivityEvent.objects.filter(cierre_id=cierre_id)
        
        if seccion:
            queryset = queryset.filter(seccion=seccion)
            
        # Filtrar por días recientes
        from django.utils import timezone
        from datetime import timedelta
        
        date_from = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(timestamp__gte=date_from)
        
        # Estadísticas básicas
        total_events = queryset.count()
        unique_sessions = queryset.values('session_id').distinct().count()
        unique_users = queryset.filter(usuario_id__isnull=False).values('usuario_id').distinct().count()
        
        # Top eventos
        top_eventos = list(
            queryset.values('seccion', 'evento')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:10]
        )
        
        # Eventos por día
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        eventos_por_dia = list(
            queryset.annotate(fecha=TruncDate('timestamp'))
            .values('fecha')
            .annotate(count=Count('id'))
            .order_by('fecha')
        )
        
        return Response({
            'cierre_id': cierre_id,
            'period_days': days,
            'stats': {
                'total_events': total_events,
                'unique_sessions': unique_sessions,
                'unique_users': unique_users,
                'top_eventos': top_eventos,
                'eventos_por_dia': eventos_por_dia,
            }
        })
        
    except Exception as e:
        logger.error(f"Error en get_activity_stats: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def get_activity_log(request, cierre_id):
    """
    Obtiene log detallado de actividades
    
    GET /api/activity/log/{cierre_id}/
    ?seccion=libro_remuneraciones&evento=file_upload&page=1&limit=50
    """
    try:
        # Filtros
        seccion = request.GET.get('seccion')
        evento = request.GET.get('evento') 
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 por página
        
        # Query
        queryset = ActivityEvent.objects.filter(cierre_id=cierre_id)
        
        if seccion:
            queryset = queryset.filter(seccion=seccion)
        if evento:
            queryset = queryset.filter(evento=evento)
            
        # Paginar
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serializar
        activities = []
        for activity in page_obj.object_list:
            activities.append({
                'id': activity.id,
                'timestamp': activity.timestamp.isoformat(),
                'seccion': activity.seccion,
                'evento': activity.evento,
                'datos': activity.datos,
                'resultado': activity.resultado,
                'usuario_id': activity.usuario_id,
                'session_id': activity.session_id,
            })
        
        return Response({
            'activities': activities,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        logger.error(f"Error en get_activity_log: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_old_activities(request):
    """
    Endpoint para limpieza manual de actividades antiguas
    Solo para administradores
    
    POST /api/activity/cleanup/
    {"days_to_keep": 30}
    """
    # Verificar permisos de admin
    if not request.user.is_superuser:
        return Response({
            'error': 'Permisos insuficientes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        days_to_keep = request.data.get('days_to_keep', 30)
        deleted_count = ActivityEvent.cleanup_old_events(days_to_keep)
        
        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'days_kept': days_to_keep,
            'message': f'Se eliminaron {deleted_count} eventos antiguos'
        })
        
    except Exception as e:
        logger.error(f"Error en cleanup_old_activities: {e}")
        return Response({
            'error': 'Error interno del servidor'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)