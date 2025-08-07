from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..base import (
    BasePayrollModel,
    StatusMixin,
    VALIDATION_STATUS_CHOICES,
    DISCREPANCY_TYPE_CHOICES,
    SEVERITY_CHOICES,
    get_redis_key
)

# ============================================================================
#                           VALIDATION RUN
# ============================================================================

class ValidationRun(BasePayrollModel, StatusMixin):
    """
    Representa una ejecución de validación/comparación de archivos.
    Cada vez que el analista ejecuta 'Validar Discrepancias', se crea un ValidationRun.
    """
    
    # Relación con el cierre
    closure = models.ForeignKey(
        'payroll.PayrollClosure',
        on_delete=models.CASCADE,
        related_name='validation_runs'
    )
    
    # Información de la validación
    validation_type = models.CharField(
        max_length=30,
        choices=[
            ('LIBRO_VS_NOVEDADES', 'Libro vs Novedades'),
            ('MOVIMIENTOS_VS_ANALISTA', 'Movimientos vs Archivos Analista'),
            ('FULL_VALIDATION', 'Validación Completa'),
            ('CUSTOM', 'Validación Personalizada'),
        ],
        default='FULL_VALIDATION'
    )
    
    # Estado de la validación
    status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Archivos involucrados en la validación
    source_files = models.JSONField(
        default=list,
        help_text="IDs de archivos fuente para la validación"
    )
    
    # Estadísticas de la validación
    total_records_processed = models.IntegerField(
        default=0,
        help_text="Total de registros procesados"
    )
    
    total_discrepancies_found = models.IntegerField(
        default=0,
        help_text="Total de discrepancias encontradas"
    )
    
    critical_discrepancies = models.IntegerField(
        default=0,
        help_text="Discrepancias críticas encontradas"
    )
    
    # Tiempos de ejecución
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Configuración de la validación
    validation_config = models.JSONField(
        default=dict,
        help_text="Configuración específica de la validación"
    )
    
    # Resultados y errores
    validation_summary = models.JSONField(
        default=dict,
        help_text="Resumen de resultados de la validación"
    )
    
    error_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Detalles de errores si la validación falló"
    )
    
    # Task ID para tracking
    celery_task_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID de la tarea de Celery"
    )
    
    # Redis integration
    redis_progress_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Key de Redis para progreso en tiempo real"
    )
    
    class Meta:
        verbose_name = "Ejecución de Validación"
        verbose_name_plural = "Ejecuciones de Validación"
        indexes = [
            models.Index(fields=['closure', 'status']),
            models.Index(fields=['validation_type']),
            models.Index(fields=['started_at']),
            models.Index(fields=['celery_task_id']),
        ]
        ordering = ['-started_at']
    
    def save(self, *args, **kwargs):
        # Generar Redis progress key
        if not self.redis_progress_key:
            self.redis_progress_key = get_redis_key('validation_run', self.id, 'progress')
        super().save(*args, **kwargs)
    
    def start_validation(self, user=None):
        """Iniciar la validación"""
        self.status = 'RUNNING'
        self.started_at = timezone.now()
        self.change_status('RUNNING', user, "Validación iniciada")
        self.save(update_fields=['status', 'started_at'])
        
        # Actualizar Redis
        self.update_redis_progress(0, "Iniciando validación...")
    
    def complete_validation(self, user=None):
        """Completar la validación"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.change_status('COMPLETED', user, "Validación completada")
        self.save(update_fields=['status', 'completed_at'])
        
        # Actualizar estadísticas del cierre
        self.closure.update_estadisticas()
        
        # Actualizar Redis
        self.update_redis_progress(100, "Validación completada")
    
    def fail_validation(self, error_message, user=None):
        """Marcar validación como fallida"""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        self.error_details = {'error': error_message, 'timestamp': timezone.now().isoformat()}
        self.change_status('FAILED', user, f"Validación falló: {error_message}")
        self.save(update_fields=['status', 'completed_at', 'error_details'])
        
        # Actualizar Redis
        self.update_redis_progress(0, f"Error: {error_message}", error=True)
    
    def update_redis_progress(self, progress, message, error=False):
        """Actualizar progreso en Redis"""
        from django.core.cache import cache
        
        data = {
            'validation_run_id': self.id,
            'closure_id': self.closure.id,
            'status': self.status,
            'progress': progress,
            'message': message,
            'error': error,
            'total_records': self.total_records_processed,
            'discrepancies_found': self.total_discrepancies_found,
            'updated_at': timezone.now().isoformat()
        }
        
        cache.set(self.redis_progress_key, data, timeout=3600)
    
    def get_execution_time(self):
        """Obtener tiempo de ejecución"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
    
    def __str__(self):
        return f"Validación {self.validation_type} - {self.closure} ({self.get_status_display()})"


# ============================================================================
#                           DISCREPANCY RESULT
# ============================================================================

class DiscrepancyResult(BasePayrollModel):
    """
    Representa una discrepancia encontrada durante la validación.
    Cada diferencia entre archivos genera un DiscrepancyResult.
    """
    
    # Relación con validación y cierre
    validation_run = models.ForeignKey(
        ValidationRun,
        on_delete=models.CASCADE,
        related_name='discrepancies'
    )
    
    closure = models.ForeignKey(
        'payroll.PayrollClosure',
        on_delete=models.CASCADE,
        related_name='discrepancies'
    )
    
    # Tipo de discrepancia
    discrepancy_type = models.CharField(
        max_length=30,
        choices=DISCREPANCY_TYPE_CHOICES
    )
    
    # Severidad de la discrepancia
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MEDIUM'
    )
    
    # Información del empleado afectado
    employee_rut = models.CharField(
        max_length=12,
        help_text="RUT del empleado afectado"
    )
    
    employee_name = models.CharField(
        max_length=200,
        help_text="Nombre del empleado afectado"
    )
    
    # Concepto afectado (si aplica)
    concept_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Código del concepto afectado"
    )
    
    concept_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del concepto afectado"
    )
    
    # Archivos involucrados
    source_file_type = models.CharField(
        max_length=30,
        help_text="Tipo de archivo fuente"
    )
    
    target_file_type = models.CharField(
        max_length=30,
        help_text="Tipo de archivo destino"
    )
    
    # Valores encontrados
    source_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Valor encontrado en archivo fuente"
    )
    
    target_value = models.JSONField(
        null=True,
        blank=True,
        help_text="Valor encontrado en archivo destino"
    )
    
    # Descripción de la discrepancia
    description = models.TextField(
        help_text="Descripción detallada de la discrepancia"
    )
    
    # Información adicional
    row_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="Número de fila donde se encontró la discrepancia"
    )
    
    column_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre de la columna afectada"
    )
    
    # Estado de resolución
    is_resolved = models.BooleanField(
        default=False,
        help_text="Si la discrepancia ha sido resuelta"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de resolución"
    )
    
    resolved_by = models.ForeignKey(
        'api.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discrepancies_resolved',
        help_text="Usuario que resolvió la discrepancia"
    )
    
    resolution_method = models.CharField(
        max_length=30,
        blank=True,
        choices=[
            ('FILE_REUPLOAD', 'Re-subida de archivo'),
            ('MANUAL_CORRECTION', 'Corrección manual'),
            ('ACCEPTED_DIFFERENCE', 'Diferencia aceptada'),
            ('SYSTEM_CORRECTION', 'Corrección automática'),
        ]
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notas sobre la resolución"
    )
    
    # Metadata adicional
    context_data = models.JSONField(
        default=dict,
        help_text="Datos de contexto adicionales"
    )
    
    class Meta:
        verbose_name = "Discrepancia"
        verbose_name_plural = "Discrepancias"
        indexes = [
            models.Index(fields=['closure', 'is_resolved']),
            models.Index(fields=['validation_run']),
            models.Index(fields=['discrepancy_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['employee_rut']),
            models.Index(fields=['concept_code']),
        ]
        ordering = ['-created_at', 'severity']
    
    def resolve(self, user, method, notes=""):
        """Marcar discrepancia como resuelta"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_method = method
        self.resolution_notes = notes
        self.save(update_fields=[
            'is_resolved', 'resolved_at', 'resolved_by', 
            'resolution_method', 'resolution_notes'
        ])
        
        # Actualizar estadísticas del cierre
        self.closure.update_estadisticas()
        
        # Log de actividad
        from ..shared import PayrollActivityLog
        PayrollActivityLog.objects.create(
            closure=self.closure,
            activity_type='DISCREPANCY_RESOLVED',
            description=f"Discrepancia resuelta: {self.description[:100]}...",
            details={
                'discrepancy_id': self.id,
                'employee_rut': self.employee_rut,
                'resolution_method': method,
                'notes': notes
            },
            user=user
        )
    
    def get_severity_color(self):
        """Obtener color para UI según severidad"""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'yellow', 
            'HIGH': 'orange',
            'CRITICAL': 'red'
        }
        return colors.get(self.severity, 'gray')
    
    def __str__(self):
        return f"{self.get_discrepancy_type_display()} - {self.employee_name} ({self.employee_rut})"


# ============================================================================
#                           COMPARISON RESULT
# ============================================================================

class ComparisonResult(BasePayrollModel):
    """
    Resultado específico de comparación entre dos archivos.
    Almacena el resultado detallado de una comparación específica.
    """
    
    # Relación con validación
    validation_run = models.ForeignKey(
        ValidationRun,
        on_delete=models.CASCADE,
        related_name='comparison_results'
    )
    
    # Archivos comparados
    source_file = models.ForeignKey(
        'payroll.PayrollFileUpload',
        on_delete=models.CASCADE,
        related_name='comparisons_as_source'
    )
    
    target_file = models.ForeignKey(
        'payroll.PayrollFileUpload',
        on_delete=models.CASCADE,
        related_name='comparisons_as_target'
    )
    
    # Tipo de comparación
    comparison_type = models.CharField(
        max_length=50,
        choices=[
            ('EMPLOYEE_MATCH', 'Coincidencia de Empleados'),
            ('CONCEPT_VALUES', 'Valores de Conceptos'),
            ('DATE_COMPARISON', 'Comparación de Fechas'),
            ('STATUS_CHECK', 'Verificación de Estados'),
        ]
    )
    
    # Estadísticas de la comparación
    total_records_compared = models.IntegerField(default=0)
    matched_records = models.IntegerField(default=0)
    unmatched_records = models.IntegerField(default=0)
    
    # Resultado detallado
    comparison_summary = models.JSONField(
        default=dict,
        help_text="Resumen detallado de la comparación"
    )
    
    # Configuración usada
    comparison_config = models.JSONField(
        default=dict,
        help_text="Configuración aplicada para la comparación"
    )
    
    class Meta:
        verbose_name = "Resultado de Comparación"
        verbose_name_plural = "Resultados de Comparación"
        indexes = [
            models.Index(fields=['validation_run']),
            models.Index(fields=['source_file', 'target_file']),
            models.Index(fields=['comparison_type']),
        ]
    
    def get_match_percentage(self):
        """Calcular porcentaje de coincidencia"""
        if self.total_records_compared == 0:
            return 0
        return round((self.matched_records / self.total_records_compared) * 100, 2)
    
    def __str__(self):
        return f"{self.comparison_type} - {self.source_file.file_type} vs {self.target_file.file_type}"


# ============================================================================
#                           VALIDATION RULES
# ============================================================================

class ValidationRule(BasePayrollModel):
    """
    Reglas de validación configurables para diferentes tipos de comparaciones.
    Permite personalizar qué validaciones ejecutar y con qué parámetros.
    """
    
    # Información básica
    name = models.CharField(
        max_length=100,
        help_text="Nombre de la regla"
    )
    
    description = models.TextField(
        help_text="Descripción de la regla"
    )
    
    # Tipo de validación
    validation_type = models.CharField(
        max_length=30,
        choices=[
            ('EMPLOYEE_MATCHING', 'Coincidencia de Empleados'),
            ('CONCEPT_VALIDATION', 'Validación de Conceptos'),
            ('AMOUNT_COMPARISON', 'Comparación de Montos'),
            ('DATE_VALIDATION', 'Validación de Fechas'),
            ('CUSTOM_RULE', 'Regla Personalizada'),
        ]
    )
    
    # Configuración de la regla
    rule_config = models.JSONField(
        default=dict,
        help_text="Configuración específica de la regla"
    )
    
    # Severidad por defecto
    default_severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='MEDIUM'
    )
    
    # Estado de la regla
    is_active = models.BooleanField(
        default=True,
        help_text="Si la regla está activa"
    )
    
    # Orden de ejecución
    execution_order = models.IntegerField(
        default=100,
        help_text="Orden de ejecución (menor número = primero)"
    )
    
    class Meta:
        verbose_name = "Regla de Validación"
        verbose_name_plural = "Reglas de Validación"
        indexes = [
            models.Index(fields=['validation_type']),
            models.Index(fields=['is_active', 'execution_order']),
        ]
        ordering = ['execution_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_validation_type_display()})"
