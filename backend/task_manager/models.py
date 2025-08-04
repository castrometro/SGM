# task_manager/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class TaskExecution(models.Model):
    """
    🔄 Modelo global para trackear ejecuciones de tareas Celery
    """
    
    TASK_STATES = [
        ('PENDING', 'Pendiente'),
        ('STARTED', 'Iniciada'),
        ('PROGRESS', 'En Progreso'),
        ('SUCCESS', 'Exitosa'),
        ('FAILURE', 'Fallida'),
        ('RETRY', 'Reintentando'),
        ('REVOKED', 'Cancelada'),
    ]
    
    TASK_MODULES = [
        ('nomina', 'Nómina'),
        ('contabilidad', 'Contabilidad'),
        ('api', 'API General'),
        ('task_manager', 'Gestión de Tareas'),
        ('system', 'Sistema'),
    ]
    
    # Identificadores únicos
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Información de la tarea
    task_name = models.CharField(max_length=255)
    task_module = models.CharField(max_length=50, choices=TASK_MODULES)
    description = models.TextField(blank=True, help_text="Descripción amigable de la tarea")
    
    # Estados y progreso
    status = models.CharField(max_length=20, choices=TASK_STATES, default='PENDING')
    progress_percentage = models.IntegerField(default=0, help_text="Porcentaje 0-100")
    current_step = models.CharField(max_length=500, blank=True)
    total_steps = models.IntegerField(default=1)
    
    # Metadatos temporales
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Usuario y contexto
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    context_data = models.JSONField(default=dict, help_text="Datos de contexto")
    
    # Resultados
    result_data = models.JSONField(default=dict, help_text="Resultado exitoso")
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Configuración
    timeout_seconds = models.IntegerField(default=3600)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Worker info (desde Flower)
    worker_name = models.CharField(max_length=255, blank=True)
    queue_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'task_manager_execution'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
            models.Index(fields=['task_module', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.task_name} ({self.task_id[:8]}...)"
    
    @property
    def duration_seconds(self):
        """Duración en segundos"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (timezone.now() - self.started_at).total_seconds()
        return 0
    
    @property
    def is_finished(self):
        return self.status in ['SUCCESS', 'FAILURE', 'REVOKED']
    
    @property
    def is_running(self):
        return self.status in ['STARTED', 'PROGRESS', 'RETRY']
    
    @property
    def is_successful(self):
        return self.status == 'SUCCESS'
    
    def update_progress(self, percentage=None, step_description=None, step_number=None):
        """Actualiza el progreso de la tarea"""
        if percentage is not None:
            self.progress_percentage = min(100, max(0, percentage))
        
        if step_description:
            self.current_step = step_description
        
        if step_number and self.total_steps:
            calculated_percentage = int((step_number / self.total_steps) * 100)
            self.progress_percentage = calculated_percentage
        
        # Actualizar estado si es necesario
        if self.progress_percentage > 0 and self.status == 'PENDING':
            self.status = 'PROGRESS'
        
        self.save(update_fields=['progress_percentage', 'current_step', 'status', 'updated_at'])
    
    def mark_started(self, worker_name=None, queue_name=None):
        """Marca la tarea como iniciada"""
        self.status = 'STARTED'
        self.started_at = timezone.now()
        if worker_name:
            self.worker_name = worker_name
        if queue_name:
            self.queue_name = queue_name
        self.save(update_fields=['status', 'started_at', 'worker_name', 'queue_name'])
    
    def mark_completed(self, result_data=None):
        """Marca la tarea como completada exitosamente"""
        self.status = 'SUCCESS'
        self.progress_percentage = 100
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save(update_fields=['status', 'progress_percentage', 'completed_at', 'result_data'])
    
    def mark_failed(self, error_message=None, error_traceback=None):
        """Marca la tarea como fallida"""
        self.status = 'FAILURE'
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = str(error_message)
        if error_traceback:
            self.error_traceback = str(error_traceback)
        self.save(update_fields=['status', 'completed_at', 'error_message', 'error_traceback'])


class TaskNotification(models.Model):
    """
    📢 Notificaciones asociadas a tareas
    """
    NOTIFICATION_TYPES = [
        ('info', 'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('progress', 'Progreso'),
    ]
    
    task = models.ForeignKey(TaskExecution, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'task_manager_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type.upper()}: {self.title}"


class TaskTemplate(models.Model):
    """
    📋 Templates de tareas para configuración consistente
    """
    name = models.CharField(max_length=255, unique=True)
    module = models.CharField(max_length=50, choices=TaskExecution.TASK_MODULES)
    description = models.TextField()
    
    # Configuración por defecto
    default_timeout = models.IntegerField(default=3600)
    default_max_retries = models.IntegerField(default=3)
    estimated_duration_seconds = models.IntegerField(default=300)
    
    # Pasos típicos (para progreso)
    typical_steps = models.JSONField(default=list, help_text="Lista de pasos típicos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_manager_template'
    
    def __str__(self):
        return f"{self.name} ({self.module})"
