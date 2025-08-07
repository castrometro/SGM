from django.db import models
from django.utils import timezone
from ..base import BasePayrollModel, get_redis_key

# ============================================================================
#                           PAYROLL ACTIVITY LOG
# ============================================================================

class PayrollActivityLog(BasePayrollModel):
    """
    Log de actividades para trazabilidad completa del sistema de nóminas.
    Registra todas las acciones importantes realizadas por los usuarios.
    """
    
    # Relación con cierre (nullable para logs globales)
    closure = models.ForeignKey(
        'payroll.PayrollClosure',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    
    # Usuario que realizó la acción
    user = models.ForeignKey(
        'api.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payroll_activities'
    )
    
    # Tipo de actividad
    activity_type = models.CharField(
        max_length=30,
        choices=[
            # Actividades de archivos
            ('FILE_UPLOAD', 'Subida de Archivo'),
            ('FILE_PARSING', 'Análisis de Archivo'),
            ('FILE_DELETE', 'Eliminación de Archivo'),
            ('FILE_REUPLOAD', 'Re-subida de Archivo'),
            
            # Actividades de validación
            ('VALIDATION_START', 'Inicio de Validación'),
            ('VALIDATION_COMPLETE', 'Validación Completada'),
            ('VALIDATION_FAILED', 'Validación Falló'),
            ('DISCREPANCY_FOUND', 'Discrepancia Encontrada'),
            ('DISCREPANCY_RESOLVED', 'Discrepancia Resuelta'),
            
            # Actividades de cierre
            ('CLOSURE_CREATED', 'Cierre Creado'),
            ('STATUS_CHANGE', 'Cambio de Estado'),
            ('PHASE_ADVANCE', 'Avance de Fase'),
            ('CLOSURE_COMPLETED', 'Cierre Completado'),
            ('CLOSURE_CANCELLED', 'Cierre Cancelado'),
            
            # Actividades de consolidación
            ('CONSOLIDATION_START', 'Inicio de Consolidación'),
            ('CONSOLIDATION_COMPLETE', 'Consolidación Completada'),
            
            # Actividades de comparación
            ('COMPARISON_START', 'Inicio de Comparación'),
            ('COMPARISON_COMPLETE', 'Comparación Completada'),
            
            # Actividades de finalización
            ('REPORT_GENERATION', 'Generación de Reportes'),
            ('CLOSURE_FINALIZATION', 'Finalización de Cierre'),
            
            # Actividades del sistema
            ('SYSTEM_ERROR', 'Error del Sistema'),
            ('DATA_EXPORT', 'Exportación de Datos'),
            ('DATA_IMPORT', 'Importación de Datos'),
            ('USER_LOGIN', 'Inicio de Sesión'),
            ('USER_LOGOUT', 'Cierre de Sesión'),
        ]
    )
    
    # Descripción de la actividad
    description = models.TextField(
        help_text="Descripción legible de la actividad"
    )
    
    # Detalles adicionales en JSON
    details = models.JSONField(
        default=dict,
        help_text="Detalles adicionales de la actividad"
    )
    
    # Contexto de la actividad
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Dirección IP del usuario"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="User agent del navegador"
    )
    
    session_key = models.CharField(
        max_length=40,
        blank=True,
        help_text="Clave de sesión"
    )
    
    # Metadata de rendimiento
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo de ejecución en milisegundos"
    )
    
    # Estado de la actividad
    is_successful = models.BooleanField(
        default=True,
        help_text="Si la actividad fue exitosa"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si la actividad falló"
    )
    
    # Metadata adicional
    related_object_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tipo de objeto relacionado"
    )
    
    related_object_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID del objeto relacionado"
    )
    
    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        indexes = [
            models.Index(fields=['closure', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['is_successful']),
            models.Index(fields=['related_object_type', 'related_object_id']),
        ]
        ordering = ['-created_at']
    
    @classmethod
    def log_activity(cls, activity_type, description, user=None, closure=None, 
                    details=None, request=None, execution_time=None, 
                    related_object=None, is_successful=True, error_message=""):
        """
        Método helper para crear logs de actividad fácilmente.
        """
        log_data = {
            'activity_type': activity_type,
            'description': description,
            'user': user,
            'closure': closure,
            'details': details or {},
            'is_successful': is_successful,
            'error_message': error_message,
        }
        
        # Agregar tiempo de ejecución
        if execution_time:
            log_data['execution_time_ms'] = execution_time
        
        # Extraer información de la request
        if request:
            log_data.update({
                'ip_address': cls._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'session_key': request.session.session_key or '',
            })
        
        # Agregar información del objeto relacionado
        if related_object:
            log_data.update({
                'related_object_type': related_object.__class__.__name__,
                'related_object_id': str(related_object.id),
            })
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "Sistema"
        return f"{self.get_activity_type_display()} - {user_name} ({self.created_at})"


# ============================================================================
#                           AUDIT TRAIL
# ============================================================================

class AuditTrail(BasePayrollModel):
    """
    Rastro de auditoría para cambios en modelos importantes.
    Registra el estado antes y después de cambios críticos.
    """
    
    # Objeto auditado
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE
    )
    
    object_id = models.CharField(max_length=50)
    
    # Usuario que hizo el cambio
    user = models.ForeignKey(
        'api.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_trails'
    )
    
    # Tipo de acción
    action = models.CharField(
        max_length=20,
        choices=[
            ('CREATE', 'Creación'),
            ('UPDATE', 'Actualización'),
            ('DELETE', 'Eliminación'),
            ('RESTORE', 'Restauración'),
        ]
    )
    
    # Estado antes del cambio
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Valores antes del cambio"
    )
    
    # Estado después del cambio
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Valores después del cambio"
    )
    
    # Campos que cambiaron
    changed_fields = models.JSONField(
        default=list,
        help_text="Lista de campos que cambiaron"
    )
    
    # Razón del cambio
    change_reason = models.TextField(
        blank=True,
        help_text="Razón del cambio"
    )
    
    # Metadata del cambio
    change_context = models.JSONField(
        default=dict,
        help_text="Contexto adicional del cambio"
    )
    
    class Meta:
        verbose_name = "Rastro de Auditoría"
        verbose_name_plural = "Rastros de Auditoría"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.content_type} #{self.object_id}"


# ============================================================================
#                           PERFORMANCE LOG
# ============================================================================

class PerformanceLog(BasePayrollModel):
    """
    Log de rendimiento para operaciones críticas del sistema.
    Ayuda a identificar cuellos de botella y optimizar el sistema.
    """
    
    # Información de la operación
    operation_name = models.CharField(
        max_length=100,
        help_text="Nombre de la operación"
    )
    
    operation_type = models.CharField(
        max_length=30,
        choices=[
            ('FILE_PARSING', 'Análisis de Archivo'),
            ('VALIDATION', 'Validación'),
            ('CONSOLIDATION', 'Consolidación'),
            ('COMPARISON', 'Comparación'),
            ('REPORT_GENERATION', 'Generación de Reportes'),
            ('DATABASE_QUERY', 'Consulta de Base de Datos'),
            ('REDIS_OPERATION', 'Operación Redis'),
            ('API_REQUEST', 'Petición API'),
            ('TASK_EXECUTION', 'Ejecución de Tarea'),
        ]
    )
    
    # Métricas de rendimiento
    execution_time_ms = models.IntegerField(
        help_text="Tiempo de ejecución en milisegundos"
    )
    
    memory_usage_mb = models.FloatField(
        null=True,
        blank=True,
        help_text="Uso de memoria en MB"
    )
    
    cpu_usage_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Uso de CPU en porcentaje"
    )
    
    # Contexto de la operación
    records_processed = models.IntegerField(
        default=0,
        help_text="Cantidad de registros procesados"
    )
    
    operation_size = models.CharField(
        max_length=20,
        choices=[
            ('SMALL', 'Pequeña (< 1K registros)'),
            ('MEDIUM', 'Media (1K - 10K registros)'),
            ('LARGE', 'Grande (10K - 100K registros)'),
            ('XLARGE', 'Muy Grande (> 100K registros)'),
        ],
        blank=True
    )
    
    # Información del sistema
    server_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nombre del servidor"
    )
    
    worker_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nombre del worker (si es tarea Celery)"
    )
    
    # Estado de la operación
    is_successful = models.BooleanField(
        default=True,
        help_text="Si la operación fue exitosa"
    )
    
    error_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tipo de error si falló"
    )
    
    # Metadata adicional
    operation_metadata = models.JSONField(
        default=dict,
        help_text="Metadata adicional de la operación"
    )
    
    class Meta:
        verbose_name = "Log de Rendimiento"
        verbose_name_plural = "Logs de Rendimiento"
        indexes = [
            models.Index(fields=['operation_type', 'created_at']),
            models.Index(fields=['operation_name']),
            models.Index(fields=['execution_time_ms']),
            models.Index(fields=['is_successful']),
        ]
        ordering = ['-created_at']
    
    @classmethod
    def log_performance(cls, operation_name, operation_type, execution_time_ms,
                       records_processed=0, is_successful=True, **kwargs):
        """Método helper para crear logs de rendimiento"""
        
        # Determinar tamaño de operación
        if records_processed < 1000:
            operation_size = 'SMALL'
        elif records_processed < 10000:
            operation_size = 'MEDIUM'
        elif records_processed < 100000:
            operation_size = 'LARGE'
        else:
            operation_size = 'XLARGE'
        
        return cls.objects.create(
            operation_name=operation_name,
            operation_type=operation_type,
            execution_time_ms=execution_time_ms,
            records_processed=records_processed,
            operation_size=operation_size,
            is_successful=is_successful,
            **kwargs
        )
    
    def __str__(self):
        return f"{self.operation_name} - {self.execution_time_ms}ms"
