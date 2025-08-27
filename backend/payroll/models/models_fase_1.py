from django.db import models
from django.conf import settings
import hashlib
import os
from datetime import datetime
from .models_cierre import CierrePayroll
from django.db.models.signals import pre_delete
from django.dispatch import receiver


def archivo_upload_path(instance, filename):
    """
    Genera la ruta de almacenamiento: media/payroll/id_cliente/año/mes/archivo
    """
    # Extraer año y mes del período del cierre (formato "YYYY-MM")
    año, mes = instance.cierre.periodo.split('-')
    
    # Construir la ruta
    return f"payroll/{instance.cierre.cliente.id}/{año}/{mes}/{filename}"


class ArchivoSubido(models.Model):
    """
    Modelo para gestionar los archivos subidos en el proceso de cierre.
    Cada archivo tiene un hash único para verificar integridad.
    """
    
    TIPOS_ARCHIVO = [
        ('libro_remuneraciones', 'Talana - Libro de Remuneraciones'),
        ('movimientos_mes', 'Talana - Movimientos del Mes'),
        ('ausentismos', 'Analista - Ausentismos'),
        ('ingresos', 'Analista - Ingresos'),
        ('finiquitos', 'Analista - Finiquitos'),
        ('novedades', 'Analista - Novedades'),
    ]
    
    ESTADOS_ARCHIVO = [
        ('subido', 'Subido'),
        ('procesando', 'Procesando'),
        ('procesado', 'Procesado'),
        ('error', 'Error'),
        ('validado', 'Validado'),
    ]
    
    ESTADOS_PROCESAMIENTO = [
        ('pendiente', 'Pendiente'),
        ('parseando', 'Parseando'),
        ('error', 'Error'),
        ('parsing_completo', 'Parsing Completo'),
    ]
    
    cierre = models.ForeignKey(CierrePayroll, on_delete=models.CASCADE, related_name='archivos')
    tipo_archivo = models.CharField(max_length=30, choices=TIPOS_ARCHIVO)
    estado = models.CharField(max_length=15, choices=ESTADOS_ARCHIVO, default='subido')
    estado_procesamiento = models.CharField(max_length=20, choices=ESTADOS_PROCESAMIENTO, default='pendiente')
    
    # Información del archivo
    nombre_original = models.CharField(max_length=255)
    archivo = models.FileField(upload_to=archivo_upload_path)
    tamaño = models.BigIntegerField(help_text="Tamaño en bytes")
    hash_md5 = models.CharField(max_length=32)
    
    # Metadatos de procesamiento
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    registros_procesados = models.IntegerField(default=0)
    errores_detectados = models.IntegerField(default=0)
    
    # Información adicional
    metadatos = models.JSONField(default=dict, blank=True)
    log_errores = models.JSONField(default=list, blank=True)
    
    class Meta:
        verbose_name = "Archivo Subido"
        verbose_name_plural = "Archivos Subidos"
        unique_together = ['cierre', 'tipo_archivo']
        ordering = ['fecha_subida']
    
    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.get_tipo_archivo_display()} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        if self.archivo and not self.hash_md5:
            self.hash_md5 = self.calcular_hash()
            self.tamaño = self.archivo.size
        super().save(*args, **kwargs)
    
    def calcular_hash(self):
        """Calcula el hash MD5 del archivo"""
        hash_md5 = hashlib.md5()
        for chunk in self.archivo.chunks():
            hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def delete(self, *args, **kwargs):
        """Override delete para eliminar archivo físico del storage"""
        if self.archivo:
            try:
                # Eliminar archivo físico del storage
                if self.archivo.storage.exists(self.archivo.name):
                    self.archivo.storage.delete(self.archivo.name)
                    print(f"🗑️ Archivo eliminado del storage: {self.archivo.name}")
            except Exception as e:
                print(f"❌ Error eliminando archivo del storage: {e}")
        
        # Llamar al delete original
        super().delete(*args, **kwargs)
    
    def agregar_error(self, mensaje, fila=None):
        """Agrega un error al log de errores del archivo"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje,
            'fila': fila
        }
        self.log_errores.append(error)
        self.errores_detectados += 1
        self.save(update_fields=['log_errores', 'errores_detectados'])
    
    @classmethod
    def limpiar_archivos_huerfanos(cls):
        """
        Método de utilidad para limpiar archivos físicos que no tienen registro en BD.
        Útil para mantenimiento.
        """
        import glob
        from django.conf import settings
        
        archivos_eliminados = 0
        payroll_path = os.path.join(settings.MEDIA_ROOT, 'payroll')
        
        if not os.path.exists(payroll_path):
            return archivos_eliminados
        
        # Buscar todos los archivos físicos en el directorio payroll
        archivos_fisicos = glob.glob(os.path.join(payroll_path, '**', '*.*'), recursive=True)
        
        for archivo_path in archivos_fisicos:
            # Obtener la ruta relativa desde MEDIA_ROOT
            ruta_relativa = os.path.relpath(archivo_path, settings.MEDIA_ROOT)
            
            # Verificar si existe un registro en BD con esta ruta
            if not cls.objects.filter(archivo=ruta_relativa).exists():
                try:
                    os.remove(archivo_path)
                    archivos_eliminados += 1
                    print(f"🧹 Archivo huérfano eliminado: {ruta_relativa}")
                except Exception as e:
                    print(f"❌ Error eliminando archivo huérfano {ruta_relativa}: {e}")
        
        return archivos_eliminados


# Signal para limpiar archivos cuando se elimina desde el admin u otros lugares
@receiver(pre_delete, sender=ArchivoSubido)
def limpiar_archivo_storage(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de eliminar un ArchivoSubido.
    Se asegura de que el archivo físico se elimine del storage.
    """
    if instance.archivo:
        try:
            if instance.archivo.storage.exists(instance.archivo.name):
                instance.archivo.storage.delete(instance.archivo.name)
                print(f"🗑️ [Signal] Archivo eliminado del storage: {instance.archivo.name}")
        except Exception as e:
            print(f"❌ [Signal] Error eliminando archivo del storage: {e}")
