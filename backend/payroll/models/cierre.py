from django.db import models
from django.conf import settings


class CierrePayroll(models.Model):
    """
    Modelo principal para el cierre de payroll mensual.
    Controla el flujo completo desde creación hasta finalización.
    """
    
    # Relaciones principales
    cliente = models.ForeignKey(
        'api.Cliente', 
        on_delete=models.CASCADE,
        help_text="Cliente al que pertenece este cierre"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que creó el cierre"
    )
    
    # Información básica
    periodo = models.CharField(
        max_length=7, 
        help_text="Período en formato YYYY-MM"
    )
    
    # Estados del flujo completo
    estado = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('cargando_archivos', 'Cargando Archivos'),
            ('mapeando_columnas', 'Mapeando Columnas'),
            ('comparando_archivos', 'Comparando Archivos'),
            ('archivos_validados', 'Archivos Validados'),
            ('consolidando', 'Consolidando Datos'),
            ('datos_consolidados', 'Datos Consolidados'),
            ('analizando_variaciones', 'Analizando Variaciones'),
            ('incidencias_detectadas', 'Incidencias Detectadas'),
            ('revision_analista', 'Revisión Analista'),
            ('revision_supervisor', 'Revisión Supervisor'),
            ('aprobado', 'Aprobado'),
            ('finalizado', 'Finalizado'),
            ('error', 'Error')
        ],
        default='pendiente'
    )
    
    # Fechas de control
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Datos de resumen (calculados)
    total_empleados = models.IntegerField(default=0)
    monto_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Monto total del período"
    )
    
    # Configuración
    porcentaje_tolerancia = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.0,
        help_text="Porcentaje de tolerancia para detectar variaciones"
    )
    
    class Meta:
        db_table = 'payroll_cierre'
        verbose_name = 'Cierre Payroll'
        verbose_name_plural = 'Cierres Payroll'
        unique_together = [['cliente', 'periodo']]
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo}"
    
    def get_estado_display_color(self):
        """Retorna color para mostrar en el frontend"""
        colors = {
            'pendiente': '#6c757d',
            'cargando_archivos': '#ffc107',
            'mapeando_columnas': '#fd7e14',
            'comparando_archivos': '#20c997',
            'archivos_validados': '#28a745',
            'consolidando': '#007bff',
            'datos_consolidados': '#17a2b8',
            'analizando_variaciones': '#6f42c1',
            'incidencias_detectadas': '#dc3545',
            'revision_analista': '#fd7e14',
            'revision_supervisor': '#ffc107',
            'aprobado': '#28a745',
            'finalizado': '#198754',
            'error': '#dc3545'
        }
        return colors.get(self.estado, '#6c757d')
    
    def get_progress_percentage(self):
        """Calcula porcentaje de progreso basado en el estado"""
        estados_progreso = {
            'pendiente': 0,
            'cargando_archivos': 10,
            'mapeando_columnas': 20,
            'comparando_archivos': 30,
            'archivos_validados': 40,
            'consolidando': 50,
            'datos_consolidados': 60,
            'analizando_variaciones': 70,
            'incidencias_detectadas': 80,
            'revision_analista': 85,
            'revision_supervisor': 90,
            'aprobado': 95,
            'finalizado': 100,
            'error': 0
        }
        return estados_progreso.get(self.estado, 0)
    
    def can_transition_to(self, new_estado):
        """Valida si se puede cambiar al nuevo estado"""
        valid_transitions = {
            'pendiente': ['cargando_archivos', 'error'],
            'cargando_archivos': ['mapeando_columnas', 'error'],
            'mapeando_columnas': ['comparando_archivos', 'error'],
            'comparando_archivos': ['archivos_validados', 'cargando_archivos', 'error'],
            'archivos_validados': ['consolidando', 'error'],
            'consolidando': ['datos_consolidados', 'error'],
            'datos_consolidados': ['analizando_variaciones', 'error'],
            'analizando_variaciones': ['incidencias_detectadas', 'revision_analista', 'error'],
            'incidencias_detectadas': ['revision_analista', 'error'],
            'revision_analista': ['revision_supervisor', 'incidencias_detectadas', 'error'],
            'revision_supervisor': ['aprobado', 'revision_analista', 'error'],
            'aprobado': ['finalizado', 'error'],
            'finalizado': [],
            'error': ['pendiente']  # Reiniciar proceso
        }
        return new_estado in valid_transitions.get(self.estado, [])
