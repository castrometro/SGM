# task_manager/services.py
import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from .models import TaskExecution, TaskNotification

logger = logging.getLogger(__name__)

class FlowerService:
    """
    🌸 Servicio global para interactuar con Flower API
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'FLOWER_API_URL', 'http://localhost:5555/api')
        self.timeout = getattr(settings, 'FLOWER_API_TIMEOUT', 5)
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Obtiene información de una tarea específica desde Flower"""
        try:
            response = requests.get(
                f"{self.base_url}/task/info/{task_id}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Tarea {task_id} no encontrada en Flower")
                return None
            else:
                logger.error(f"Error {response.status_code} consultando tarea {task_id}")
                return None
        except Exception as e:
            logger.error(f"Error conectando con Flower para tarea {task_id}: {e}")
            return None
    
    def get_workers_info(self) -> Dict:
        """Obtiene información de todos los workers"""
        try:
            response = requests.get(f"{self.base_url}/workers", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo workers de Flower: {e}")
            return {}
    
    def get_active_tasks(self) -> List[Dict]:
        """Obtiene todas las tareas activas"""
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                # Flower retorna un dict con task_id como key
                return [{'task_id': tid, **info} for tid, info in data.items()]
            return []
        except Exception as e:
            logger.error(f"Error obteniendo tareas activas de Flower: {e}")
            return []
    
    def revoke_task(self, task_id: str) -> bool:
        """Cancela una tarea"""
        try:
            response = requests.post(
                f"{self.base_url}/task/revoke/{task_id}",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error cancelando tarea {task_id}: {e}")
            return False


class TaskManager:
    """
    🎯 Servicio principal para gestión global de tareas
    """
    
    def __init__(self):
        self.flower = FlowerService()
    
    def register_task(self, task_id: str, task_name: str, module: str, 
                     user=None, description: str = "", context_data: Dict = None) -> TaskExecution:
        """Registra una nueva tarea en el sistema"""
        return TaskExecution.objects.create(
            task_id=task_id,
            task_name=task_name,
            task_module=module,
            description=description,
            user=user,
            context_data=context_data or {}
        )
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado completo de una tarea combinando datos locales y de Flower
        """
        # 1. Datos locales de la base de datos
        try:
            local_task = TaskExecution.objects.get(task_id=task_id)
        except TaskExecution.DoesNotExist:
            local_task = None
        
        # 2. Datos de Flower
        flower_data = self.flower.get_task_info(task_id)
        
        # 3. Combinar información
        return self._combine_task_data(local_task, flower_data)
    
    def _combine_task_data(self, local_task: Optional[TaskExecution], 
                          flower_data: Optional[Dict]) -> Dict[str, Any]:
        """Combina datos locales y de Flower en una respuesta unificada"""
        
        # Estado básico
        result = {
            'task_id': local_task.task_id if local_task else flower_data.get('uuid', 'unknown'),
            'exists_locally': local_task is not None,
            'exists_in_flower': flower_data is not None,
        }
        
        # Datos locales si existen
        if local_task:
            result.update({
                'id': str(local_task.id),
                'task_name': local_task.task_name,
                'module': local_task.task_module,
                'description': local_task.description,
                'status': local_task.status,
                'progress_percentage': local_task.progress_percentage,
                'current_step': local_task.current_step,
                'total_steps': local_task.total_steps,
                'user': local_task.user.username if local_task.user else None,
                'context_data': local_task.context_data,
                'created_at': local_task.created_at.isoformat(),
                'started_at': local_task.started_at.isoformat() if local_task.started_at else None,
                'completed_at': local_task.completed_at.isoformat() if local_task.completed_at else None,
                'duration_seconds': local_task.duration_seconds,
                'is_finished': local_task.is_finished,
                'is_running': local_task.is_running,
                'is_successful': local_task.is_successful,
                'result_data': local_task.result_data,
                'error_message': local_task.error_message,
                'worker_name': local_task.worker_name,
                'queue_name': local_task.queue_name,
            })
        
        # Datos de Flower si existen (pueden sobrescribir algunos locales)
        if flower_data:
            result.update({
                'flower_state': flower_data.get('state'),
                'flower_result': flower_data.get('result'),
                'flower_traceback': flower_data.get('traceback'),
                'flower_worker': flower_data.get('worker'),
                'flower_timestamp': flower_data.get('timestamp'),
                'flower_runtime': flower_data.get('runtime'),
            })
            
            # Sincronizar estado si hay diferencias
            if local_task and flower_data.get('state'):
                self._sync_flower_state(local_task, flower_data)
        
        # Estado unificado
        result['unified_status'] = self._get_unified_status(local_task, flower_data)
        result['user_friendly_message'] = self._get_user_friendly_message(result['unified_status'])
        
        return result
    
    def _sync_flower_state(self, local_task: TaskExecution, flower_data: Dict):
        """Sincroniza el estado local con el de Flower"""
        flower_state = flower_data.get('state')
        local_state = local_task.status
        
        # Mapeo de estados Flower -> Local
        flower_to_local = {
            'PENDING': 'PENDING',
            'STARTED': 'STARTED',
            'PROGRESS': 'PROGRESS',
            'SUCCESS': 'SUCCESS',
            'FAILURE': 'FAILURE',
            'RETRY': 'RETRY',
            'REVOKED': 'REVOKED',
        }
        
        mapped_state = flower_to_local.get(flower_state, flower_state)
        
        if mapped_state != local_state:
            logger.info(f"Sincronizando estado de tarea {local_task.task_id}: {local_state} -> {mapped_state}")
            
            local_task.status = mapped_state
            
            if mapped_state == 'STARTED' and not local_task.started_at:
                local_task.mark_started(
                    worker_name=flower_data.get('worker'),
                    queue_name=flower_data.get('queue')
                )
            elif mapped_state == 'SUCCESS':
                local_task.mark_completed(flower_data.get('result'))
            elif mapped_state == 'FAILURE':
                local_task.mark_failed(
                    error_message=flower_data.get('result'),
                    error_traceback=flower_data.get('traceback')
                )
            else:
                local_task.save(update_fields=['status'])
    
    def _get_unified_status(self, local_task: Optional[TaskExecution], 
                           flower_data: Optional[Dict]) -> str:
        """Determina el estado unificado de la tarea"""
        if flower_data:
            return flower_data.get('state', 'UNKNOWN')
        elif local_task:
            return local_task.status
        else:
            return 'NOT_FOUND'
    
    def _get_user_friendly_message(self, status: str) -> str:
        """Convierte el estado técnico en mensaje amigable"""
        messages = {
            'PENDING': 'Tarea en cola, esperando ser procesada',
            'STARTED': 'Tarea iniciada, procesando...',
            'PROGRESS': 'Tarea en progreso',
            'SUCCESS': 'Tarea completada exitosamente',
            'FAILURE': 'Tarea falló durante la ejecución',
            'RETRY': 'Reintentando tarea...',
            'REVOKED': 'Tarea cancelada',
            'NOT_FOUND': 'Tarea no encontrada',
            'UNKNOWN': 'Estado desconocido',
        }
        return messages.get(status, f'Estado: {status}')
    
    def get_tasks_by_module(self, module: str, limit: int = 50) -> List[TaskExecution]:
        """Obtiene tareas por módulo"""
        return TaskExecution.objects.filter(task_module=module)[:limit]
    
    def get_user_tasks(self, user, limit: int = 50) -> List[TaskExecution]:
        """Obtiene tareas de un usuario específico"""
        return TaskExecution.objects.filter(user=user)[:limit]
    
    def get_active_tasks(self) -> List[TaskExecution]:
        """Obtiene todas las tareas activas"""
        return TaskExecution.objects.filter(
            status__in=['PENDING', 'STARTED', 'PROGRESS', 'RETRY']
        )
    
    def get_workers(self) -> List[Dict]:
        """Obtiene información de workers desde Flower"""
        workers_data = self.flower.get_workers_info()
        workers = []
        
        for hostname, info in workers_data.items():
            workers.append({
                'hostname': hostname,
                'status': info.get('status', 'unknown'),
                'active': info.get('active', 0),
                'processed': info.get('processed', 0),
                'loadavg': info.get('loadavg', []),
                'stats': info.get('stats', {}),
                'heartbeat': info.get('heartbeat'),
                'online': info.get('status') == 'OK'
            })
        
        return workers
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea"""
        success = self.flower.revoke_task(task_id)
        
        if success:
            try:
                local_task = TaskExecution.objects.get(task_id=task_id)
                local_task.status = 'REVOKED'
                local_task.completed_at = timezone.now()
                local_task.save(update_fields=['status', 'completed_at'])
            except TaskExecution.DoesNotExist:
                pass
        
        return success
    
    def add_notification(self, task_id: str, type: str, title: str, 
                        message: str, details: Dict = None):
        """Agrega una notificación a una tarea"""
        try:
            task = TaskExecution.objects.get(task_id=task_id)
            TaskNotification.objects.create(
                task=task,
                type=type,
                title=title,
                message=message,
                details=details or {}
            )
        except TaskExecution.DoesNotExist:
            logger.warning(f"No se pudo agregar notificación a tarea inexistente: {task_id}")


# Instancia global del manager
task_manager = TaskManager()
