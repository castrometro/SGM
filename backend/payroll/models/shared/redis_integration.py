from django.db import models
from django.core.cache import cache
from django.utils import timezone
from ..base import BasePayrollModel, get_redis_key
import json

# ============================================================================
#                           REDIS CACHE MANAGER
# ============================================================================

class RedisCache(BasePayrollModel):
    """
    Modelo para gestionar y trackear el uso de Redis en el sistema de nóminas.
    Mantiene un registro de las keys de Redis utilizadas para facilitar debugging.
    """
    
    # Información de la cache key
    cache_key = models.CharField(
        max_length=200,
        unique=True,
        help_text="Key de Redis"
    )
    
    cache_type = models.CharField(
        max_length=30,
        choices=[
            ('FILE_PARSED_DATA', 'Datos de Archivo Parseados'),
            ('VALIDATION_PROGRESS', 'Progreso de Validación'),
            ('CLOSURE_STATUS', 'Estado de Cierre'),
            ('TASK_PROGRESS', 'Progreso de Tarea'),
            ('DISCREPANCY_CACHE', 'Cache de Discrepancias'),
            ('CONSOLIDATED_DATA', 'Datos Consolidados'),
            ('REPORT_CACHE', 'Cache de Reportes'),
            ('SESSION_DATA', 'Datos de Sesión'),
            ('TEMP_DATA', 'Datos Temporales'),
        ]
    )
    
    # Relación con objetos del sistema
    related_closure_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID del cierre relacionado"
    )
    
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
    
    # Información del contenido
    data_size_bytes = models.BigIntegerField(
        default=0,
        help_text="Tamaño de los datos en bytes"
    )
    
    data_structure = models.CharField(
        max_length=20,
        choices=[
            ('STRING', 'String'),
            ('HASH', 'Hash'),
            ('LIST', 'List'),
            ('SET', 'Set'),
            ('JSON', 'JSON'),
        ],
        default='JSON'
    )
    
    # Control de expiración
    ttl_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time to Live en segundos"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración"
    )
    
    # Estado de la cache
    is_active = models.BooleanField(
        default=True,
        help_text="Si la cache está activa"
    )
    
    last_accessed = models.DateTimeField(
        auto_now=True,
        help_text="Último acceso a la cache"
    )
    
    access_count = models.IntegerField(
        default=0,
        help_text="Cantidad de veces accedida"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Descripción del contenido de la cache"
    )
    
    cache_metadata = models.JSONField(
        default=dict,
        help_text="Metadata adicional de la cache"
    )
    
    class Meta:
        verbose_name = "Cache Redis"
        verbose_name_plural = "Caches Redis"
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['cache_type']),
            models.Index(fields=['related_closure_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-last_accessed']
    
    def save(self, *args, **kwargs):
        # Calcular fecha de expiración si hay TTL
        if self.ttl_seconds and not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(seconds=self.ttl_seconds)
        super().save(*args, **kwargs)
    
    def set_cache_data(self, data, ttl=None):
        """Guardar datos en Redis y actualizar registro"""
        try:
            # Serializar datos si es necesario
            if isinstance(data, (dict, list)):
                cache_data = json.dumps(data)
                self.data_structure = 'JSON'
            else:
                cache_data = str(data)
                self.data_structure = 'STRING'
            
            # Guardar en Redis
            cache.set(self.cache_key, cache_data, timeout=ttl or self.ttl_seconds)
            
            # Actualizar registro
            self.data_size_bytes = len(cache_data.encode('utf-8'))
            if ttl:
                self.ttl_seconds = ttl
                self.expires_at = timezone.now() + timezone.timedelta(seconds=ttl)
            
            self.is_active = True
            self.save(update_fields=['data_size_bytes', 'data_structure', 
                                   'ttl_seconds', 'expires_at', 'is_active'])
            
            return True
            
        except Exception as e:
            self.cache_metadata['last_error'] = str(e)
            self.save(update_fields=['cache_metadata'])
            return False
    
    def get_cache_data(self):
        """Obtener datos de Redis"""
        try:
            data = cache.get(self.cache_key)
            
            if data is not None:
                # Incrementar contador de acceso
                self.access_count += 1
                self.save(update_fields=['access_count'])
                
                # Deserializar si es JSON
                if self.data_structure == 'JSON' and isinstance(data, str):
                    return json.loads(data)
                return data
            else:
                # Cache expiró o no existe
                self.is_active = False
                self.save(update_fields=['is_active'])
                return None
                
        except Exception as e:
            self.cache_metadata['last_error'] = str(e)
            self.save(update_fields=['cache_metadata'])
            return None
    
    def delete_cache(self):
        """Eliminar datos de Redis y marcar como inactivo"""
        try:
            cache.delete(self.cache_key)
            self.is_active = False
            self.save(update_fields=['is_active'])
            return True
        except Exception as e:
            self.cache_metadata['last_error'] = str(e)
            self.save(update_fields=['cache_metadata'])
            return False
    
    def refresh_ttl(self, new_ttl=None):
        """Renovar TTL de la cache"""
        ttl = new_ttl or self.ttl_seconds
        if ttl:
            cache.touch(self.cache_key, ttl)
            self.expires_at = timezone.now() + timezone.timedelta(seconds=ttl)
            self.save(update_fields=['expires_at'])
    
    def is_expired(self):
        """Verificar si la cache ha expirado"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @classmethod
    def create_cache_entry(cls, key, cache_type, data, ttl=3600, 
                          related_closure=None, description=""):
        """Método helper para crear entrada de cache"""
        
        # Crear o actualizar registro
        cache_entry, created = cls.objects.get_or_create(
            cache_key=key,
            defaults={
                'cache_type': cache_type,
                'ttl_seconds': ttl,
                'description': description,
                'related_closure_id': related_closure.id if related_closure else None,
            }
        )
        
        # Guardar datos en Redis
        if cache_entry.set_cache_data(data, ttl):
            return cache_entry
        return None
    
    @classmethod
    def cleanup_expired(cls):
        """Limpiar caches expiradas"""
        expired_keys = cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        
        count = 0
        for cache_entry in expired_keys:
            if cache_entry.delete_cache():
                count += 1
        
        return count
    
    def __str__(self):
        return f"{self.cache_key} ({self.get_cache_type_display()})"


# ============================================================================
#                           REDIS UTILITIES
# ============================================================================

class RedisPayrollManager:
    """
    Clase utilitaria para operaciones comunes de Redis en el sistema de nóminas.
    """
    
    @staticmethod
    def set_file_parsed_data(file_upload, parsed_data, ttl=7200):
        """Guardar datos parseados de archivo en Redis"""
        key = get_redis_key('file', file_upload.id, 'parsed')
        return RedisCache.create_cache_entry(
            key=key,
            cache_type='FILE_PARSED_DATA',
            data=parsed_data,
            ttl=ttl,
            related_closure=file_upload.closure,
            description=f"Datos parseados de {file_upload.file_type}"
        )
    
    @staticmethod
    def get_file_parsed_data(file_upload):
        """Obtener datos parseados de archivo desde Redis"""
        key = get_redis_key('file', file_upload.id, 'parsed')
        try:
            cache_entry = RedisCache.objects.get(cache_key=key, is_active=True)
            return cache_entry.get_cache_data()
        except RedisCache.DoesNotExist:
            return None
    
    @staticmethod
    def set_validation_progress(validation_run, progress_data, ttl=3600):
        """Guardar progreso de validación en Redis"""
        key = get_redis_key('validation', validation_run.id, 'progress')
        return RedisCache.create_cache_entry(
            key=key,
            cache_type='VALIDATION_PROGRESS',
            data=progress_data,
            ttl=ttl,
            related_closure=validation_run.closure,
            description=f"Progreso de validación {validation_run.validation_type}"
        )
    
    @staticmethod
    def get_validation_progress(validation_run):
        """Obtener progreso de validación desde Redis"""
        key = get_redis_key('validation', validation_run.id, 'progress')
        try:
            cache_entry = RedisCache.objects.get(cache_key=key, is_active=True)
            return cache_entry.get_cache_data()
        except RedisCache.DoesNotExist:
            return None
    
    @staticmethod
    def set_closure_status(closure, status_data, ttl=3600):
        """Guardar estado de cierre en Redis"""
        key = get_redis_key('closure', closure.id, 'status')
        return RedisCache.create_cache_entry(
            key=key,
            cache_type='CLOSURE_STATUS',
            data=status_data,
            ttl=ttl,
            related_closure=closure,
            description=f"Estado de cierre {closure.periodo}"
        )
    
    @staticmethod
    def get_closure_status(closure):
        """Obtener estado de cierre desde Redis"""
        key = get_redis_key('closure', closure.id, 'status')
        try:
            cache_entry = RedisCache.objects.get(cache_key=key, is_active=True)
            return cache_entry.get_cache_data()
        except RedisCache.DoesNotExist:
            return None
    
    @staticmethod
    def set_discrepancies_cache(closure, discrepancies_data, ttl=1800):
        """Guardar cache de discrepancias"""
        key = get_redis_key('closure', closure.id, 'discrepancies')
        return RedisCache.create_cache_entry(
            key=key,
            cache_type='DISCREPANCY_CACHE',
            data=discrepancies_data,
            ttl=ttl,
            related_closure=closure,
            description=f"Cache de discrepancias para {closure.periodo}"
        )
    
    @staticmethod
    def invalidate_closure_cache(closure):
        """Invalidar todas las caches relacionadas con un cierre"""
        cache_entries = RedisCache.objects.filter(
            related_closure_id=closure.id,
            is_active=True
        )
        
        count = 0
        for entry in cache_entries:
            if entry.delete_cache():
                count += 1
        
        return count
    
    @staticmethod
    def cleanup_old_caches(days_old=7):
        """Limpiar caches antiguas"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        old_caches = RedisCache.objects.filter(
            created_at__lt=cutoff_date,
            is_active=True
        )
        
        count = 0
        for cache_entry in old_caches:
            if cache_entry.delete_cache():
                count += 1
        
        return count
