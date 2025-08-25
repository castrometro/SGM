from django.db import models
from django.conf import settings
from api.models import Cliente
from datetime import datetime


class CierrePayroll(models.Model):
    """
    Modelo principal para el proceso de cierre de nómina.
    Maneja los estados del flujo completo de cierre.
    """
    
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('archivos_subidos', 'Archivos Subidos'),
        ('con_discrepancias', 'Con Discrepancias'),
        ('sin_discrepancias', 'Sin Discrepancias'),
        ('datos_consolidados', 'Datos Consolidados'),
        ('revision_analista', 'En Revisión por Analista'),
        ('aprobado', 'Aprobado'),
        ('cerrado', 'Cerrado'),
        ('error', 'Error'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cierres_payroll')
    periodo = models.CharField(max_length=7, help_text="Formato: YYYY-MM")
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='pendiente')
    
    # Metadatos del proceso
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_termino = models.DateTimeField(null=True, blank=True)
    usuario_responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Cierre de Payroll"
        verbose_name_plural = "Cierres de Payroll"
        unique_together = ['cliente', 'periodo']
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo} ({self.get_estado_display()})"
