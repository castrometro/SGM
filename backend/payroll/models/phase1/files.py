from django.db import models
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import hashlib
from ..base import (
    BasePayrollModel,
    StatusMixin,
    FileRelatedMixin,
    FILE_TYPE_CHOICES,
    FILE_STATUS_CHOICES,
    generate_upload_path,
    get_redis_key,
)

# ============================================================================
#                           PAYROLL FILE UPLOAD
# ============================================================================

class PayrollFileUpload(BasePayrollModel, StatusMixin, FileRelatedMixin):
    """
    Modelo para archivos subidos en Fase 1.
    Maneja tanto archivos de Talana como del Analista.
    Integra con Redis para polling en tiempo real.
    """
    
    # Relación con el cierre
    closure = models.ForeignKey(
        'payroll.PayrollClosure',
        on_delete=models.CASCADE,
        related_name='file_uploads'
    )
    
    # Tipo de archivo
    file_type = models.CharField(
        max_length=25,
        choices=FILE_TYPE_CHOICES,
        help_text="Tipo de archivo subido"
    )
    
    # Archivo físico
    file = models.FileField(
        upload_to=generate_upload_path,
        help_text="Archivo Excel subido"
    )
    
    # Estado del archivo (usando StatusMixin)
    status = models.CharField(
        max_length=20,
        choices=FILE_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Versión del archivo (para re-uploads)
    version = models.IntegerField(
        default=1,
        help_text="Versión del archivo (incrementa en re-uploads)"
    )
    
    # Información de parsing
    parsing_started_at = models.DateTimeField(null=True, blank=True)
    parsing_completed_at = models.DateTimeField(null=True, blank=True)
    parsing_duration = models.DurationField(null=True, blank=True)
    
    # Resultados del parsing
    total_rows_parsed = models.IntegerField(
        default=0,
        help_text="Número total de filas procesadas"
    )
    
    total_employees_found = models.IntegerField(
        default=0,
        help_text="Número de empleados encontrados"
    )
    
    parsing_errors = models.JSONField(
        default=list,
        help_text="Errores encontrados durante el parsing"
    )
    
    parsing_warnings = models.JSONField(
        default=list,
        help_text="Advertencias durante el parsing"
    )
    
    # Preview de datos parseados (primeras 10 filas)
    data_preview = models.JSONField(
        default=list,
        help_text="Preview de los primeros datos parseados"
    )
    
    # Redis integration
    redis_cache_key = models.CharField(
        max_length=150,
        blank=True,
        help_text="Key de Redis para datos parseados"
    )
    
    # Task tracking
    celery_task_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID de la task de Celery para tracking"
    )
    
    # Retención de archivos
    retention_days = models.IntegerField(
        default=180,
        help_text="Días de retención del archivo"
    )
    
    is_compressed = models.BooleanField(
        default=False,
        help_text="Si el archivo está comprimido"
    )
    
    archived_location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ubicación si está archivado (S3, etc.)"
    )
    
    class Meta:
        verbose_name = "Archivo de Nómina"
        verbose_name_plural = "Archivos de Nómina"
        unique_together = ['closure', 'file_type', 'version']
        indexes = [
            models.Index(fields=['closure', 'file_type']),
            models.Index(fields=['status']),
            models.Index(fields=['parsing_completed_at']),
            models.Index(fields=['celery_task_id']),
        ]
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Generar Redis cache key
        if not self.redis_cache_key:
            self.redis_cache_key = get_redis_key(
                'file', 
                f"{self.closure_id}_{self.file_type}", 
                'parsed_data'
            )
        
        # Calcular checksum si hay archivo
        if self.file and not self.checksum_md5:
            self.file.seek(0)
            self.checksum_md5 = hashlib.md5(self.file.read()).hexdigest()
            self.file.seek(0)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validaciones custom"""
        super().clean()
        
        # Validar extensión de archivo
        if self.file:
            allowed_extensions = ['.xlsx', '.xls', '.csv']
            file_extension = self.file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError({
                    'file': f'Solo se permiten archivos: {', '.join(allowed_extensions)}'
                })
        
        # Validar que no exista otra versión activa del mismo tipo
        if self.closure and self.file_type:
            existing = PayrollFileUpload.objects.filter(
                closure=self.closure,
                file_type=self.file_type,
                status__in=['PARSED', 'VALIDATED'],
                is_deleted=False
            ).exclude(id=self.id)
            
            if existing.exists():
                # Al subir nueva versión, marcar anterior como obsoleta
                existing.update(status='OBSOLETE')
    
    # ========================================================================
    #                           REDIS INTEGRATION
    # ========================================================================
    
    def update_redis_status(self, status=None, progress=None, message="", errors=None):
        """Actualizar estado en Redis para polling"""
        
        if status:
            self.status = status
            self.save(update_fields=['status'])
        
        # Datos para Redis
        redis_data = {
            'id': self.id,
            'file_type': self.file_type,
            'status': self.status,
            'version': self.version,
            'updated_at': timezone.now().isoformat(),
            'total_rows_parsed': self.total_rows_parsed,
            'total_employees_found': self.total_employees_found,
            'celery_task_id': self.celery_task_id,
        }
        
        if progress is not None:
            redis_data['progress'] = progress
        if message:
            redis_data['message'] = message
        if errors:
            redis_data['errors'] = errors
        
        # Actualizar en Redis
        cache.set(
            f"payroll:file:{self.id}:status",
            redis_data,
            timeout=3600  # 1 hora
        )
        
        # Trigger actualización del cierre
        self.closure.update_estadisticas()
    
    def store_parsed_data_in_redis(self, parsed_data, ttl=86400):
        """Almacenar datos parseados en Redis"""
        
        cache.set(
            self.redis_cache_key,
            {
                'file_id': self.id,
                'file_type': self.file_type,
                'data': parsed_data,
                'parsed_at': timezone.now().isoformat(),
                'total_rows': len(parsed_data) if isinstance(parsed_data, list) else 0,
            },
            timeout=ttl  # 24 horas por defecto
        )
        
        # Actualizar preview
        if isinstance(parsed_data, list) and len(parsed_data) > 0:
            self.data_preview = parsed_data[:10]  # Primeras 10 filas
            self.total_rows_parsed = len(parsed_data)
            
            # Contar empleados únicos si es aplicable
            if self.file_type in ['LIBRO_REMUNERACIONES', 'NOVEDADES']:
                unique_ruts = set()
                for row in parsed_data:
                    if 'rut' in row:
                        unique_ruts.add(row['rut'])
                self.total_employees_found = len(unique_ruts)
            
            self.save(update_fields=[
                'data_preview', 'total_rows_parsed', 'total_employees_found'
            ])
    
    def get_parsed_data_from_redis(self):
        """Obtener datos parseados desde Redis"""
        return cache.get(self.redis_cache_key)
    
    def clear_redis_cache(self):
        """Limpiar cache de Redis"""
        cache.delete(self.redis_cache_key)
        cache.delete(f"payroll:file:{self.id}:status")
    
    # ========================================================================
    #                           BUSINESS LOGIC
    # ========================================================================
    
    def start_parsing(self, task_id=None):
        """Iniciar proceso de parsing"""
        self.parsing_started_at = timezone.now()
        self.celery_task_id = task_id or ''
        self.update_redis_status('PARSING', progress=0, message="Iniciando análisis...")
    
    def complete_parsing(self, success=True, errors=None, warnings=None):
        """Completar proceso de parsing"""
        self.parsing_completed_at = timezone.now()
        
        if self.parsing_started_at:
            self.parsing_duration = self.parsing_completed_at - self.parsing_started_at
        
        if success:
            self.update_redis_status('PARSED', progress=100, message="Análisis completado")
        else:
            self.parsing_errors = errors or []
            self.parsing_warnings = warnings or []
            self.update_redis_status('ERROR', progress=0, message="Error en análisis", errors=errors)
        
        self.save(update_fields=[
            'parsing_completed_at', 'parsing_duration', 'parsing_errors', 'parsing_warnings'
        ])
    
    def mark_as_validated(self):
        """Marcar archivo como validado"""
        self.update_redis_status('VALIDATED', progress=100, message="Validado exitosamente")
    
    def get_file_info(self):
        """Obtener información resumida del archivo"""
        return {
            'id': self.id,
            'file_type': self.file_type,
            'status': self.status,
            'version': self.version,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'total_rows_parsed': self.total_rows_parsed,
            'total_employees_found': self.total_employees_found,
            'parsing_duration': str(self.parsing_duration) if self.parsing_duration else None,
            'has_errors': len(self.parsing_errors) > 0,
            'created_at': self.created_at.isoformat(),
        }
    
    def should_cleanup(self):
        """Verificar si el archivo debe ser eliminado por retención"""
        if self.retention_days <= 0:
            return False
        
        cutoff_date = timezone.now() - timezone.timedelta(days=self.retention_days)
        return self.created_at < cutoff_date
    
    def __str__(self):
        return f"{self.get_file_type_display()} v{self.version} - {self.closure}"


# ============================================================================
#                           PARSED DATA STORAGE
# ============================================================================

class ParsedDataStorage(BasePayrollModel):
    """
    Almacenamiento persistente de datos parseados.
    Backup de Redis para datos que se mantienen más tiempo.
    """
    
    # Relación con archivo
    file_upload = models.OneToOneField(
        PayrollFileUpload,
        on_delete=models.CASCADE,
        related_name='parsed_storage'
    )
    
    # Datos parseados completos
    parsed_data = models.JSONField(
        help_text="Datos parseados completos del archivo"
    )
    
    # Metadata del parsing
    parsing_metadata = models.JSONField(
        default=dict,
        help_text="Metadata sobre el proceso de parsing"
    )
    
    # Control de expiración
    expires_at = models.DateTimeField(
        help_text="Fecha de expiración de los datos"
    )
    
    # Estado del cache
    is_cached_in_redis = models.BooleanField(
        default=False,
        help_text="Si los datos están actualmente en Redis"
    )
    
    last_accessed = models.DateTimeField(
        auto_now=True,
        help_text="Última vez que se accedieron los datos"
    )
    
    class Meta:
        verbose_name = "Datos Parseados"
        verbose_name_plural = "Datos Parseados"
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_cached_in_redis']),
            models.Index(fields=['last_accessed']),
        ]
    
    def save(self, *args, **kwargs):
        # Establecer fecha de expiración por defecto
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def restore_to_redis(self):
        """Restaurar datos a Redis desde BD"""
        if self.file_upload:
            self.file_upload.store_parsed_data_in_redis(
                self.parsed_data,
                ttl=86400  # 24 horas
            )
            self.is_cached_in_redis = True
            self.save(update_fields=['is_cached_in_redis'])
    
    def is_expired(self):
        """Verificar si los datos han expirado"""
        return timezone.now() > self.expires_at
    
    def extend_expiration(self, days=30):
        """Extender fecha de expiración"""
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.save(update_fields=['expires_at'])
    
    def __str__(self):
        return f"Datos parseados - {self.file_upload}"
