from django.db import models
from django.conf import settings
import hashlib
from datetime import datetime
from .models_cierre import CierrePayroll


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
    
    cierre = models.ForeignKey(CierrePayroll, on_delete=models.CASCADE, related_name='archivos')
    tipo_archivo = models.CharField(max_length=30, choices=TIPOS_ARCHIVO)
    estado = models.CharField(max_length=15, choices=ESTADOS_ARCHIVO, default='subido')
    
    # Información del archivo
    nombre_original = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='payroll/archivos/%Y/%m/')
    tamaño = models.BigIntegerField(help_text="Tamaño en bytes")
    hash_md5 = models.CharField(max_length=32, unique=True)
    
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
