from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from .base import (
    BasePayrollModel, 
    ClientRelatedMixin, 
    StatusMixin,
    CLOSURE_STATUS_CHOICES
)

# ============================================================================
#                           PAYROLL CLOSURE
# ============================================================================

class PayrollClosure(BasePayrollModel, ClientRelatedMixin, StatusMixin):
    """
    Entidad principal del sistema de nóminas.
    Representa un cierre de nómina con sus 4 fases:
    1. Upload & Validation
    2. Consolidation  
    3. Comparison
    4. Finalization
    """
    
    # Información básica del cierre
    periodo = models.CharField(
        max_length=7,  # Formato: YYYY-MM (ej: 2025-03)
        help_text="Período del cierre en formato YYYY-MM"
    )
    
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo del cierre"
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción adicional del cierre"
    )
    
    # Estado del cierre (usando StatusMixin)
    status = models.CharField(
        max_length=20,
        choices=CLOSURE_STATUS_CHOICES,
        default='CREATED'
    )
    
    # Fechas importantes
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de inicio del cierre"
    )
    
    fecha_limite = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha límite para completar el cierre"
    )
    
    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de finalización del cierre"
    )
    
    # Usuario responsable del cierre
    analista_responsable = models.ForeignKey(
        'api.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cierres_responsable',
        help_text="Analista responsable del cierre"
    )
    
    supervisor_asignado = models.ForeignKey(
        'api.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_supervisor',
        help_text="Supervisor asignado para revisión"
    )
    
    # Control de fases
    fase_actual = models.IntegerField(
        default=1,
        choices=[(1, 'Fase 1: Upload & Validation'),
                 (2, 'Fase 2: Consolidation'),
                 (3, 'Fase 3: Comparison'), 
                 (4, 'Fase 4: Finalization')],
        help_text="Fase actual del cierre"
    )
    
    # Estadísticas del cierre
    total_empleados = models.IntegerField(
        default=0,
        help_text="Total de empleados en el cierre"
    )
    
    total_discrepancias = models.IntegerField(
        default=0,
        help_text="Total de discrepancias encontradas"
    )
    
    archivos_subidos = models.IntegerField(
        default=0,
        help_text="Cantidad de archivos subidos"
    )
    
    archivos_requeridos = models.IntegerField(
        default=6,  # 2 Talana + 4 Analista
        help_text="Cantidad de archivos requeridos"
    )
    
    # Configuración específica del cierre
    configuracion = models.JSONField(
        default=dict,
        help_text="Configuración específica del cierre"
    )
    
    # Redis integration
    redis_cache_key = models.CharField(
        max_length=100,
        blank=True,
        help_text="Key de Redis para cache del cierre"
    )
    
    class Meta:
        verbose_name = "Cierre de Nómina"
        verbose_name_plural = "Cierres de Nómina"
        unique_together = ['cliente', 'periodo']
        indexes = [
            models.Index(fields=['cliente', 'periodo']),
            models.Index(fields=['status']),
            models.Index(fields=['fase_actual']),
            models.Index(fields=['analista_responsable']),
            models.Index(fields=['fecha_inicio']),
        ]
        ordering = ['-fecha_inicio']
    
    def save(self, *args, **kwargs):
        # Generar nombre automático si no existe
        if not self.nombre:
            self.nombre = f"Cierre {self.cliente.nombre} - {self.periodo}"
        
        # Generar Redis cache key
        if not self.redis_cache_key:
            self.redis_cache_key = f"payroll:closure:{self.cliente.id}:{self.periodo}"
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validaciones custom del modelo"""
        super().clean()
        
        # Validar formato de período
        if self.periodo:
            import re
            if not re.match(r'^\d{4}-\d{2}$', self.periodo):
                raise ValidationError({
                    'periodo': 'El período debe tener formato YYYY-MM (ej: 2025-03)'
                })
        
        # Validar que el analista pertenezca al cliente
        if self.analista_responsable and hasattr(self.analista_responsable, 'cliente'):
            if self.analista_responsable.cliente != self.cliente:
                raise ValidationError({
                    'analista_responsable': 'El analista debe pertenecer al cliente seleccionado'
                })
    
    # ========================================================================
    #                           STATE MACHINE METHODS
    # ========================================================================
    
    def can_transition_to(self, new_status):
        """Validar si se puede hacer la transición de estado"""
        
        valid_transitions = {
            'CREATED': ['UPLOADING_FILES', 'CANCELLED'],
            'UPLOADING_FILES': ['VALIDATING', 'CREATED', 'CANCELLED'], 
            'VALIDATING': ['UPLOADING_FILES', 'CONSOLIDATING', 'CANCELLED'],
            'CONSOLIDATING': ['COMPARING', 'ERROR'],
            'COMPARING': ['FINALIZING', 'ERROR'],
            'FINALIZING': ['COMPLETED', 'ERROR'],
            'COMPLETED': [],  # Estado final
            'ERROR': ['CREATED', 'CANCELLED'],
            'CANCELLED': ['CREATED'],
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status, user=None, reason=""):
        """Cambiar estado del cierre con validaciones"""
        
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"No se puede cambiar de '{self.status}' a '{new_status}'", 
                code='invalid_transition'
            )
        
        old_status = self.status
        
        # Cambiar estado usando StatusMixin
        self.change_status(new_status, user, reason)
        
        # Actualizar fase según estado
        self._update_fase_from_status(new_status)
        
        # Actualizar fechas especiales
        if new_status == 'COMPLETED':
            self.fecha_completado = timezone.now()
            self.save(update_fields=['fecha_completado'])
        
        # Log de actividad
        self._log_status_change(old_status, new_status, user, reason)
        
        # Actualizar Redis cache
        self._update_redis_cache()
    
    def _update_fase_from_status(self, status):
        """Actualizar fase según el estado"""
        fase_mapping = {
            'CREATED': 1,
            'UPLOADING_FILES': 1,
            'VALIDATING': 1,
            'CONSOLIDATING': 2,
            'COMPARING': 3,
            'FINALIZING': 4,
            'COMPLETED': 4,
        }
        
        new_fase = fase_mapping.get(status, self.fase_actual)
        if new_fase != self.fase_actual:
            self.fase_actual = new_fase
            self.save(update_fields=['fase_actual'])
    
    def _log_status_change(self, old_status, new_status, user, reason):
        """Registrar cambio de estado en logs"""
        from .shared import PayrollActivityLog
        
        PayrollActivityLog.objects.create(
            closure=self,
            activity_type='STATUS_CHANGE',
            description=f"Estado cambiado de '{old_status}' a '{new_status}'",
            details={
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
                'fase': self.fase_actual
            },
            user=user
        )
    
    def _update_redis_cache(self):
        """Actualizar estado en Redis para polling"""
        from django.core.cache import cache
        
        cache_data = {
            'id': self.id,
            'status': self.status,
            'fase_actual': self.fase_actual,
            'total_empleados': self.total_empleados,
            'total_discrepancias': self.total_discrepancias,
            'archivos_subidos': self.archivos_subidos,
            'archivos_requeridos': self.archivos_requeridos,
            'can_advance': self.can_advance_phase(),
            'updated_at': timezone.now().isoformat(),
        }
        
        cache.set(self.redis_cache_key, cache_data, timeout=3600)  # 1 hora
    
    # ========================================================================
    #                           BUSINESS LOGIC METHODS
    # ========================================================================
    
    def can_advance_phase(self):
        """Verificar si se puede avanzar a la siguiente fase"""
        
        if self.fase_actual == 1:
            # Fase 1: Todos los archivos subidos y 0 discrepancias
            return (self.archivos_subidos >= self.archivos_requeridos and 
                    self.total_discrepancias == 0)
        
        elif self.fase_actual == 2:
            # Fase 2: Datos consolidados exitosamente
            return self.status == 'CONSOLIDATING'
        
        elif self.fase_actual == 3:
            # Fase 3: Comparación completada
            return self.status == 'COMPARING'
        
        elif self.fase_actual == 4:
            # Fase 4: Puede finalizar
            return self.status == 'FINALIZING'
        
        return False
    
    def get_archivos_pendientes(self):
        """Obtener lista de tipos de archivos pendientes"""
        from .phase1 import PayrollFileUpload
        
        archivos_subidos = PayrollFileUpload.objects.filter(
            closure=self,
            status='PARSED'
        ).values_list('file_type', flat=True)
        
        from .base import FILE_TYPE_CHOICES
        todos_los_tipos = [choice[0] for choice in FILE_TYPE_CHOICES]
        
        return [tipo for tipo in todos_los_tipos if tipo not in archivos_subidos]
    
    def update_estadisticas(self):
        """Actualizar estadísticas del cierre"""
        from .phase1 import PayrollFileUpload, DiscrepancyResult
        
        # Contar archivos
        self.archivos_subidos = PayrollFileUpload.objects.filter(
            closure=self,
            status='PARSED'
        ).count()
        
        # Contar discrepancias
        self.total_discrepancias = DiscrepancyResult.objects.filter(
            closure=self,
            is_resolved=False
        ).count()
        
        self.save(update_fields=['archivos_subidos', 'total_discrepancias'])
        
        # Actualizar Redis
        self._update_redis_cache()
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo} ({self.get_status_display()})"


# ============================================================================
#                           MANAGERS PERSONALIZADOS
# ============================================================================

class PayrollClosureManager(models.Manager):
    """Manager personalizado para PayrollClosure"""
    
    def active(self):
        """Cierres activos (no eliminados ni cancelados)"""
        return self.filter(
            is_deleted=False,
            status__in=['CREATED', 'UPLOADING_FILES', 'VALIDATING', 
                       'CONSOLIDATING', 'COMPARING', 'FINALIZING']
        )
    
    def by_analista(self, user):
        """Cierres asignados a un analista"""
        return self.filter(analista_responsable=user)
    
    def by_cliente(self, cliente):
        """Cierres de un cliente específico"""
        return self.filter(cliente=cliente)
    
    def en_fase(self, fase):
        """Cierres en una fase específica"""
        return self.filter(fase_actual=fase)
    
    def pendientes(self):
        """Cierres que requieren atención"""
        return self.filter(
            status__in=['UPLOADING_FILES', 'VALIDATING'],
            is_deleted=False
        )

# Asignar manager personalizado
PayrollClosure.objects = PayrollClosureManager()
