# backend/nomina/models_informe.py

from django.db import models
from django.conf import settings
from .models import CierreNomina


class ReporteNomina(models.Model):
    """
    📊 MODELO PARA REPORTES DE NÓMINA
    
    Similar al ReporteFinanciero de contabilidad, este modelo almacena 
    reportes de nómina generados en formato JSON.
    
    Ejemplos de tipos de reporte que se pueden implementar:
    - Reporte de Costos de Personal
    - Análisis de Rotación de Personal  
    - Indicadores de RRHH
    - Reporte de Ausentismo
    - Análisis de Remuneraciones
    """
    
    TIPOS_REPORTE = [
        ('costos_personal', 'Reporte de Costos de Personal'),
        ('rotacion_personal', 'Análisis de Rotación de Personal'),
        ('indicadores_rrhh', 'Indicadores de Recursos Humanos'),
        ('ausentismo', 'Reporte de Ausentismo'),
        ('remuneraciones', 'Análisis de Remuneraciones'),
        ('productividad', 'Reporte de Productividad'),
        ('dotacion', 'Análisis de Dotación'),
        ('comparativo_periodos', 'Comparativo entre Períodos'),
        # Se pueden agregar más tipos según las necesidades
    ]
    
    ESTADOS = [
        ('generando', 'Generando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    cierre = models.ForeignKey(
        CierreNomina, 
        on_delete=models.CASCADE, 
        related_name='reportes'
    )
    tipo_reporte = models.CharField(max_length=30, choices=TIPOS_REPORTE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='generando')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_generador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que solicitó la generación del reporte"
    )
    
    # Datos del reporte en formato JSON
    datos_reporte = models.JSONField(
        null=True, 
        blank=True,
        help_text="Datos estructurados del reporte de nómina"
    )
    
    # Metadatos adicionales
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Información adicional sobre el reporte (tiempo generación, versión, KPIs, etc.)"
    )
    
    # Error si falló la generación
    error_mensaje = models.TextField(
        blank=True,
        help_text="Mensaje de error si la generación falló"
    )
    
    class Meta:
        unique_together = ['cierre', 'tipo_reporte']
        indexes = [
            models.Index(fields=['cierre', 'tipo_reporte']),
            models.Index(fields=['estado', 'fecha_generacion']),
            models.Index(fields=['tipo_reporte', 'estado']),
        ]
        verbose_name = "Reporte de Nómina"
        verbose_name_plural = "Reportes de Nómina"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.cierre.cliente.nombre} {self.cierre.periodo}"
    
    @property
    def es_valido(self):
        """Verifica si el reporte es válido y está completado"""
        return self.estado == 'completado' and self.datos_reporte is not None
    
    def marcar_como_error(self, mensaje_error):
        """Marca el reporte como fallido"""
        self.estado = 'error'
        self.error_mensaje = mensaje_error
        self.save()
    
    def marcar_como_completado(self, datos):
        """Marca el reporte como completado con los datos"""
        self.estado = 'completado'
        self.datos_reporte = datos
        self.error_mensaje = ''
        self.save()
    
    @property
    def kpis_principales(self):
        """Extrae KPIs principales del reporte si están disponibles"""
        if not self.datos_reporte:
            return {}
        
        # Dependiendo del tipo de reporte, extraer KPIs relevantes
        metadata = self.metadata or {}
        return metadata.get('kpis_principales', {})
    
    def obtener_resumen_ejecutivo(self):
        """Obtiene un resumen ejecutivo del reporte"""
        if not self.es_valido:
            return None
            
        return {
            'tipo_reporte': self.get_tipo_reporte_display(),
            'periodo': self.cierre.periodo,
            'cliente': self.cierre.cliente.nombre,
            'fecha_generacion': self.fecha_generacion.isoformat(),
            'kpis_principales': self.kpis_principales,
            'estado': self.estado,
        }


