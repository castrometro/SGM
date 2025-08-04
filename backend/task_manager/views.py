# task_manager/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import TaskExecution, TaskNotification, TaskTemplate
from .serializers import (
    TaskExecutionSerializer, TaskExecutionSummarySerializer,
    TaskNotificationSerializer, TaskTemplateSerializer,
    TaskStatusResponseSerializer, WorkerStatusSerializer,
    TaskProgressUpdateSerializer, TaskCreateSerializer
)
from .services import task_manager

logger = logging.getLogger(__name__)

class TaskExecutionViewSet(viewsets.ModelViewSet):
    """
    🔄 ViewSet global para gestión de tareas
    
    Proporciona endpoints unificados para todas las apps del sistema
    """
    queryset = TaskExecution.objects.all()
    serializer_class = TaskExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Usa serializer resumido para listas"""
        if self.action == 'list':
            return TaskExecutionSummarySerializer
        return TaskExecutionSerializer
    
    def get_queryset(self):
        """Filtra tareas según usuario y parámetros"""
        queryset = TaskExecution.objects.all()
        
        # Filtro por módulo
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(task_module=module)
        
        # Filtro por estado
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtro por usuario (solo las propias si no es staff)
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        # Filtro por fechas
        since = self.request.query_params.get('since')
        if since:
            try:
                since_date = timezone.now() - timedelta(hours=int(since))
                queryset = queryset.filter(created_at__gte=since_date)
            except ValueError:
                pass
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], url_path='status/(?P<task_id>[^/.]+)')
    def get_task_status(self, request, task_id=None):
        """
        🔍 ENDPOINT PRINCIPAL - Obtener estado completo de tarea
        
        Combina información local (BD) + Flower para estado completo
        """
        if not task_id:
            return Response({
                'error': 'task_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Usar el servicio para obtener estado completo
            task_data = task_manager.get_task_status(task_id)
            
            # Serializar respuesta
            serializer = TaskStatusResponseSerializer(data=task_data)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.validated_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de tarea {task_id}: {e}")
            return Response({
                'error': f'Error obteniendo estado: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def register_task(self, request):
        """
        📝 ENDPOINT - Registrar nueva tarea
        
        Permite a las apps registrar tareas para tracking
        """
        serializer = TaskCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        task = serializer.save()
        
        return Response({
            'success': True,
            'task': TaskExecutionSerializer(task).data,
            'message': 'Tarea registrada exitosamente'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """
        📊 ENDPOINT - Actualizar progreso de tarea
        """
        task = self.get_object()
        serializer = TaskProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        task.update_progress(
            percentage=data.get('percentage'),
            step_description=data.get('step_description'),
            step_number=data.get('step_number')
        )
        
        if data.get('total_steps'):
            task.total_steps = data['total_steps']
            task.save(update_fields=['total_steps'])
        
        return Response({
            'success': True,
            'task': TaskExecutionSerializer(task).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel_task(self, request, pk=None):
        """
        ❌ ENDPOINT - Cancelar tarea
        """
        task = self.get_object()
        
        success = task_manager.cancel_task(task.task_id)
        
        if success:
            return Response({
                'success': True,
                'message': f'Tarea {task.task_id} cancelada exitosamente'
            })
        else:
            return Response({
                'success': False,
                'error': 'No se pudo cancelar la tarea'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def workers_status(self, request):
        """
        👷 ENDPOINT - Estado de workers de Celery
        """
        try:
            workers_data = task_manager.flower.get_workers_info()
            
            workers_summary = []
            for worker_name, worker_info in workers_data.items():
                summary = {
                    'name': worker_name,
                    'status': 'active' if worker_info.get('active') is not None else 'inactive',
                    'active_tasks': len(worker_info.get('active', [])),
                    'total_tasks': worker_info.get('stats', {}).get('total', {}),
                    'queues': [q['name'] for q in worker_info.get('active_queues', [])],
                    'uptime': worker_info.get('stats', {}).get('uptime', 0),
                }
                workers_summary.append(summary)
            
            # Serializar
            serializer = WorkerStatusSerializer(workers_summary, many=True)
            
            return Response({
                'success': True,
                'workers': serializer.data,
                'total_workers': len(workers_summary),
                'active_workers': len([w for w in workers_summary if w['status'] == 'active'])
            })
            
        except Exception as e:
            logger.error(f"Error consultando workers: {e}")
            return Response({
                'success': False,
                'error': f'Error consultando workers: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def active_tasks(self, request):
        """
        🏃 ENDPOINT - Tareas activas del sistema
        """
        active_tasks = task_manager.get_active_tasks()
        serializer = TaskExecutionSummarySerializer(active_tasks, many=True)
        
        return Response({
            'success': True,
            'tasks': serializer.data,
            'count': len(active_tasks)
        })
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """
        👤 ENDPOINT - Tareas del usuario actual
        """
        limit = int(request.query_params.get('limit', 20))
        user_tasks = task_manager.get_user_tasks(request.user, limit)
        serializer = TaskExecutionSummarySerializer(user_tasks, many=True)
        
        return Response({
            'success': True,
            'tasks': serializer.data,
            'count': len(user_tasks)
        })
    
    @action(detail=False, methods=['get'])
    def module_tasks(self, request):
        """
        📦 ENDPOINT - Tareas por módulo
        """
        module = request.query_params.get('module')
        if not module:
            return Response({
                'error': 'Parámetro module es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        limit = int(request.query_params.get('limit', 50))
        module_tasks = task_manager.get_tasks_by_module(module, limit)
        serializer = TaskExecutionSummarySerializer(module_tasks, many=True)
        
        return Response({
            'success': True,
            'module': module,
            'tasks': serializer.data,
            'count': len(module_tasks)
        })


class TaskNotificationViewSet(viewsets.ModelViewSet):
    """
    📢 ViewSet para notificaciones de tareas
    """
    queryset = TaskNotification.objects.all()
    serializer_class = TaskNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra notificaciones según usuario"""
        queryset = TaskNotification.objects.select_related('task')
        
        # Solo notificaciones de tareas del usuario (si no es staff)
        if not self.request.user.is_staff:
            queryset = queryset.filter(task__user=self.request.user)
        
        # Filtro por leído/no leído
        read = self.request.query_params.get('read')
        if read is not None:
            queryset = queryset.filter(read=read.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marca notificación como leída"""
        notification = self.get_object()
        notification.read = True
        notification.save(update_fields=['read'])
        
        return Response({
            'success': True,
            'notification': TaskNotificationSerializer(notification).data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marca todas las notificaciones como leídas"""
        queryset = self.get_queryset().filter(read=False)
        count = queryset.update(read=True)
        
        return Response({
            'success': True,
            'marked_count': count
        })


class TaskTemplateViewSet(viewsets.ModelViewSet):
    """
    📋 ViewSet para templates de tareas
    """
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra templates según módulo"""
        queryset = TaskTemplate.objects.all()
        
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module=module)
        
        return queryset.order_by('name')
