"""
Utilidades para el sistema de gestión de tareas
"""
from functools import wraps
from typing import Optional, Dict, Any, Callable
from django.contrib.auth.models import User
from .models import TaskExecution, TaskTemplate
from .services import task_manager


def track_task(task_name: str, module: str, description: str = "", 
               template_name: Optional[str] = None, 
               timeout_seconds: int = 300):
    """
    Decorador para trackear automáticamente tareas de Celery
    
    Args:
        task_name: Nombre de la tarea Celery
        module: Módulo al que pertenece (nomina, contabilidad, etc.)
        description: Descripción de la tarea
        template_name: Nombre de plantilla opcional
        timeout_seconds: Timeout en segundos
    
    Usage:
        @shared_task
        @track_task('nomina.consolidar', 'nomina', 'Consolidar nómina')
        def consolidar_nomina(periodo_id, user_id):
            # ... lógica de la tarea
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extraer user_id si está disponible
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else None)
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            # Obtener el task_id actual de Celery
            from celery import current_task
            celery_task_id = current_task.request.id if current_task else None
            
            # Registrar inicio de tarea
            task_execution = task_manager.register_task_start(
                task_id=celery_task_id,
                task_name=task_name,
                task_module=module,
                description=description,
                user=user,
                parameters={'args': args, 'kwargs': kwargs},
                timeout_seconds=timeout_seconds,
                template_name=template_name
            )
            
            try:
                # Ejecutar la función original
                result = func(*args, **kwargs)
                
                # Registrar éxito
                task_manager.update_task_status(
                    task_execution.id,
                    'SUCCESS',
                    result={'success': True, 'data': result}
                )
                
                return result
                
            except Exception as e:
                # Registrar error
                task_manager.update_task_status(
                    task_execution.id,
                    'FAILURE',
                    error_message=str(e),
                    result={'success': False, 'error': str(e)}
                )
                raise
        
        return wrapper
    return decorator


def get_user_tasks(user: User, module: Optional[str] = None, 
                  status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Obtiene las tareas de un usuario con filtros opcionales
    
    Args:
        user: Usuario
        module: Filtrar por módulo (opcional)
        status: Filtrar por estado (opcional)
        limit: Límite de resultados
    
    Returns:
        Dict con las tareas y estadísticas
    """
    queryset = TaskExecution.objects.filter(user=user)
    
    if module:
        queryset = queryset.filter(task_module=module)
    
    if status:
        queryset = queryset.filter(status=status)
    
    tasks = queryset.order_by('-created_at')[:limit]
    
    # Estadísticas
    stats = {
        'total': queryset.count(),
        'pending': queryset.filter(status='PENDING').count(),
        'started': queryset.filter(status='STARTED').count(),
        'success': queryset.filter(status='SUCCESS').count(),
        'failure': queryset.filter(status='FAILURE').count(),
        'revoked': queryset.filter(status='REVOKED').count(),
    }
    
    return {
        'tasks': [
            {
                'id': task.id,
                'task_id': task.task_id,
                'task_name': task.task_name,
                'task_module': task.task_module,
                'status': task.status,
                'description': task.description,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'progress': task.progress,
                'result': task.result,
                'error_message': task.error_message,
            }
            for task in tasks
        ],
        'stats': stats
    }


def create_task_template(name: str, task_name: str, module: str, 
                        description: str, default_parameters: Dict[str, Any] = None,
                        estimated_duration: int = 60, 
                        notification_settings: Dict[str, Any] = None) -> TaskTemplate:
    """
    Crea una plantilla de tarea reutilizable
    
    Args:
        name: Nombre único de la plantilla
        task_name: Nombre de la tarea Celery
        module: Módulo al que pertenece
        description: Descripción
        default_parameters: Parámetros por defecto
        estimated_duration: Duración estimada en segundos
        notification_settings: Configuración de notificaciones
    
    Returns:
        TaskTemplate creado
    """
    template, created = TaskTemplate.objects.get_or_create(
        name=name,
        defaults={
            'task_name': task_name,
            'task_module': module,
            'description': description,
            'default_parameters': default_parameters or {},
            'estimated_duration': estimated_duration,
            'notification_settings': notification_settings or {},
            'is_active': True
        }
    )
    
    if not created:
        # Actualizar si ya existe
        template.task_name = task_name
        template.task_module = module
        template.description = description
        template.default_parameters = default_parameters or {}
        template.estimated_duration = estimated_duration
        template.notification_settings = notification_settings or {}
        template.save()
    
    return template


def cancel_user_tasks(user: User, module: Optional[str] = None, 
                     task_name: Optional[str] = None) -> Dict[str, int]:
    """
    Cancela tareas pendientes o en ejecución de un usuario
    
    Args:
        user: Usuario
        module: Filtrar por módulo (opcional)
        task_name: Filtrar por nombre de tarea (opcional)
    
    Returns:
        Dict con estadísticas de cancelación
    """
    queryset = TaskExecution.objects.filter(
        user=user,
        status__in=['PENDING', 'STARTED']
    )
    
    if module:
        queryset = queryset.filter(task_module=module)
    
    if task_name:
        queryset = queryset.filter(task_name=task_name)
    
    cancelled_count = 0
    failed_count = 0
    
    for task in queryset:
        try:
            success = task_manager.cancel_task(task.task_id)
            if success:
                cancelled_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1
    
    return {
        'cancelled': cancelled_count,
        'failed': failed_count,
        'total_attempted': cancelled_count + failed_count
    }


def get_module_stats(module: str, days: int = 7) -> Dict[str, Any]:
    """
    Obtiene estadísticas de un módulo en los últimos días
    
    Args:
        module: Nombre del módulo
        days: Número de días atrás para las estadísticas
    
    Returns:
        Dict con estadísticas del módulo
    """
    from django.utils import timezone
    from datetime import timedelta
    
    since = timezone.now() - timedelta(days=days)
    
    queryset = TaskExecution.objects.filter(
        task_module=module,
        created_at__gte=since
    )
    
    stats = {
        'total_tasks': queryset.count(),
        'success_rate': 0,
        'avg_duration': 0,
        'by_status': {},
        'by_task_name': {},
        'recent_failures': []
    }
    
    if stats['total_tasks'] > 0:
        # Por estado
        for status in ['PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'REVOKED']:
            count = queryset.filter(status=status).count()
            stats['by_status'][status] = count
        
        # Tasa de éxito
        success_count = stats['by_status'].get('SUCCESS', 0)
        stats['success_rate'] = (success_count / stats['total_tasks']) * 100
        
        # Por nombre de tarea
        task_names = queryset.values_list('task_name', flat=True).distinct()
        for task_name in task_names:
            count = queryset.filter(task_name=task_name).count()
            stats['by_task_name'][task_name] = count
        
        # Fallas recientes
        recent_failures = queryset.filter(
            status='FAILURE'
        ).order_by('-created_at')[:5]
        
        stats['recent_failures'] = [
            {
                'task_name': task.task_name,
                'error_message': task.error_message,
                'created_at': task.created_at,
                'user': task.user.username if task.user else None
            }
            for task in recent_failures
        ]
    
    return stats


# Shortcuts para las operaciones más comunes
def start_task_tracking(task_id: str, task_name: str, module: str, 
                       user: Optional[User] = None, **kwargs) -> TaskExecution:
    """Shortcut para iniciar tracking de una tarea"""
    return task_manager.register_task_start(
        task_id=task_id,
        task_name=task_name,
        task_module=module,
        user=user,
        **kwargs
    )


def update_task_progress(task_execution_id: int, progress: int, 
                        status_message: str = ""):
    """Shortcut para actualizar progreso de una tarea"""
    return task_manager.update_task_progress(
        task_execution_id, progress, status_message
    )


def finish_task(task_execution_id: int, success: bool = True, 
               result: Dict[str, Any] = None, error_message: str = ""):
    """Shortcut para finalizar una tarea"""
    status = 'SUCCESS' if success else 'FAILURE'
    return task_manager.update_task_status(
        task_execution_id, status, result=result, error_message=error_message
    )
