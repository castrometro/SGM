from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid
import hashlib
import json

# ============================================================================
#                           CONSTANTES GLOBALES
# ============================================================================

# Estados del Cierre (State Machine)
CLOSURE_STATUS_CHOICES = [
    ('CREATED', 'Creado'),
    ('UPLOADING_FILES', 'Subiendo Archivos'),
    ('VALIDATING', 'Validando Discrepancias'),
    ('CONSOLIDATING', 'Consolidando Datos'),
    ('COMPARING', 'Comparando con Período Anterior'),
    ('FINALIZING', 'Finalizando'),
    ('COMPLETED', 'Completado'),
    ('ERROR', 'Error'),
    ('CANCELLED', 'Cancelado'),
]

# Tipos de Archivos
FILE_TYPE_CHOICES = [
    # Archivos de Talana
    ('LIBRO_REMUNERACIONES', 'Libro de Remuneraciones'),
    ('MOVIMIENTOS_MES', 'Movimientos del Mes'),
    
    # Archivos del Analista
    ('FINIQUITOS', 'Finiquitos'),
    ('INGRESOS', 'Ingresos'),
    ('INCIDENCIAS', 'Incidencias (Ausentismos)'),
    ('NOVEDADES', 'Novedades'),
]

# Estados de Archivos
FILE_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('UPLOADING', 'Subiendo'),
    ('UPLOADED', 'Subido'),
    ('PARSING', 'Analizando'),
    ('PARSED', 'Analizado'),
    ('VALIDATED', 'Validado'),
    ('ERROR', 'Error'),
    ('CANCELLED', 'Cancelado'),
]

# Estados de Validación
VALIDATION_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('RUNNING', 'Ejecutando'),
    ('COMPLETED', 'Completada'),
    ('FAILED', 'Falló'),
    ('CANCELLED', 'Cancelada'),
]

# Tipos de Discrepancias
DISCREPANCY_TYPE_CHOICES = [
    ('EMPLOYEE_MISMATCH', 'Empleado no coincide'),
    ('AMOUNT_DIFFERENCE', 'Diferencia en montos'),
    ('MISSING_CONCEPT', 'Concepto faltante'),
    ('EXTRA_CONCEPT', 'Concepto extra'),
    ('DATE_MISMATCH', 'Fecha no coincide'),
    ('STATUS_DIFFERENCE', 'Estado diferente'),
]

# Niveles de Severidad
SEVERITY_CHOICES = [
    ('LOW', 'Baja'),
    ('MEDIUM', 'Media'),
    ('HIGH', 'Alta'),
    ('CRITICAL', 'Crítica'),
]

# ============================================================================
#                           MODELO BASE ABSTRACTO
# ============================================================================

class BasePayrollModel(models.Model):
    """
    Modelo base abstracto para todos los modelos de payroll.
    Incluye campos comunes de auditoría y funcionalidades compartidas.
    """
    
    # Identificación única
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Auditoría temporal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Auditoría de usuario
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted'
    )
    
    # Metadata adicional
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_deleted']),
        ]
    
    def soft_delete(self, user=None):
        """Eliminación suave del registro"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restaurar registro eliminado"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def add_metadata(self, key, value):
        """Agregar metadata al registro"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value
        self.save(update_fields=['metadata'])
    
    def get_metadata(self, key, default=None):
        """Obtener metadata del registro"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    @classmethod
    def active(cls):
        """Manager para registros activos (no eliminados)"""
        return cls.objects.filter(is_deleted=False)
    
    def __str__(self):
        return f"{self.__class__.__name__} #{self.id} ({self.uuid})"


# ============================================================================
#                           MIXINS ÚTILES
# ============================================================================

class ClientRelatedMixin(models.Model):
    """Mixin para modelos relacionados con cliente (multi-tenancy)"""
    
    cliente = models.ForeignKey(
        'api.Cliente',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['cliente']),
        ]


class StatusMixin(models.Model):
    """Mixin para modelos con estado y transiciones"""
    
    status = models.CharField(max_length=20)
    status_changed_at = models.DateTimeField(auto_now_add=True)
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_status_changes'
    )
    status_history = models.JSONField(default=list, blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['status_changed_at']),
        ]
    
    def change_status(self, new_status, user=None, reason=""):
        """Cambiar estado con historial"""
        old_status = self.status
        
        # Actualizar estado
        self.status = new_status
        self.status_changed_at = timezone.now()
        self.status_changed_by = user
        
        # Agregar a historial
        if not self.status_history:
            self.status_history = []
        
        self.status_history.append({
            'from_status': old_status,
            'to_status': new_status,
            'changed_at': timezone.now().isoformat(),
            'changed_by': user.id if user else None,
            'reason': reason
        })
        
        self.save(update_fields=[
            'status', 'status_changed_at', 'status_changed_by', 'status_history'
        ])


class FileRelatedMixin(models.Model):
    """Mixin para modelos relacionados con archivos"""
    
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    checksum_md5 = models.CharField(max_length=32)
    mime_type = models.CharField(max_length=100, blank=True)
    
    class Meta:
        abstract = True
    
    def calculate_checksum(self, file_content):
        """Calcular checksum MD5 del archivo"""
        return hashlib.md5(file_content).hexdigest()
    
    def validate_checksum(self, file_content):
        """Validar integridad del archivo"""
        return self.checksum_md5 == self.calculate_checksum(file_content)


# ============================================================================
#                           UTILIDADES COMPARTIDAS
# ============================================================================

def generate_upload_path(instance, filename):
    """Generar path para uploads organizados por fecha y cliente"""
    from datetime import datetime
    now = datetime.now()
    
    # Obtener cliente ID
    if hasattr(instance, 'cliente'):
        cliente_id = instance.cliente.id
    elif hasattr(instance, 'closure') and hasattr(instance.closure, 'cliente'):
        cliente_id = instance.closure.cliente.id
    else:
        cliente_id = 'unknown'
    
    return f"payroll/uploads/{cliente_id}/{now.year}/{now.month:02d}/{filename}"


def serialize_for_cache(obj):
    """Serializar objeto para almacenar en Redis"""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return str(obj)


def get_redis_key(model_name, instance_id, suffix=""):
    """Generar key consistente para Redis"""
    key = f"payroll:{model_name.lower()}:{instance_id}"
    if suffix:
        key += f":{suffix}"
    return key
