from django.db import models
from django.conf import settings
from .cierre import CierrePayroll
from .empleados import Empleados_Cierre


class Finiquitos_Cierre(models.Model):
    """
    Registro de finiquitos procesados en el cierre.
    Contiene información específica de empleados que salen de la empresa.
    """
    
    # Relaciones principales
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='finiquitos'
    )
    empleado_cierre = models.OneToOneField(
        Empleados_Cierre,
        on_delete=models.CASCADE,
        related_name='finiquito',
        help_text="Empleado asociado al finiquito"
    )
    
    # Información del finiquito
    fecha_finiquito = models.DateField(
        help_text="Fecha efectiva del finiquito"
    )
    ultimo_dia_trabajado = models.DateField(
        help_text="Último día trabajado por el empleado"
    )
    
    # Motivos de salida
    motivo_salida = models.CharField(
        max_length=50,
        choices=[
            ('renuncia', 'Renuncia Voluntaria'),
            ('despido', 'Despido'),
            ('mutuo_acuerdo', 'Mutuo Acuerdo'),
            ('termino_contrato', 'Término de Contrato'),
            ('jubilacion', 'Jubilación'),
            ('fallecimiento', 'Fallecimiento'),
            ('abandono', 'Abandono de Trabajo'),
            ('otros', 'Otros Motivos')
        ],
        help_text="Motivo de la salida del empleado"
    )
    
    # Montos del finiquito
    monto_finiquito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto total del finiquito"
    )
    indemnizacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Monto de indemnización si corresponde"
    )
    vacaciones_pendientes = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Monto por vacaciones no tomadas"
    )
    proporcional_aguinaldo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Proporcional de aguinaldo"
    )
    otros_beneficios = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Otros beneficios adicionales"
    )
    
    # Descuentos del finiquito
    descuentos_aplicados = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Descuentos aplicados al finiquito"
    )
    
    # Estado del finiquito
    estado_finiquito = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('calculado', 'Calculado'),
            ('aprobado', 'Aprobado'),
            ('pagado', 'Pagado'),
            ('observado', 'Con Observaciones')
        ],
        default='pendiente'
    )
    
    # Información adicional
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones especiales del finiquito"
    )
    documento_respaldo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Referencia al documento de respaldo"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que aprobó el finiquito"
    )
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de aprobación del finiquito"
    )
    
    class Meta:
        db_table = 'payroll_finiquitos_cierre'
        verbose_name = 'Finiquito del Cierre'
        verbose_name_plural = 'Finiquitos del Cierre'
        ordering = ['-fecha_finiquito']
    
    def __str__(self):
        return f"Finiquito {self.empleado_cierre.nombre_completo} - {self.fecha_finiquito}"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que el empleado esté marcado como finiquito
        if self.empleado_cierre.estado_empleado != 'finiquito':
            raise ValidationError(
                "El empleado debe estar marcado como 'finiquito' para tener un registro de finiquito"
            )
        
        # Validar fechas
        if self.ultimo_dia_trabajado > self.fecha_finiquito:
            raise ValidationError(
                "El último día trabajado no puede ser posterior a la fecha de finiquito"
            )
    
    def calcular_monto_total(self):
        """Calcula el monto total del finiquito"""
        total_haberes = (
            self.monto_finiquito + 
            self.indemnizacion + 
            self.vacaciones_pendientes + 
            self.proporcional_aguinaldo + 
            self.otros_beneficios
        )
        return total_haberes - self.descuentos_aplicados
    
    def get_dias_trabajados_mes(self):
        """Calcula días trabajados en el mes del finiquito"""
        import calendar
        from datetime import date
        
        # Obtener primer día del mes
        primer_dia = date(
            self.fecha_finiquito.year, 
            self.fecha_finiquito.month, 
            1
        )
        
        # Calcular días trabajados
        if self.ultimo_dia_trabajado >= primer_dia:
            return (self.ultimo_dia_trabajado - primer_dia).days + 1
        return 0
    
    def requires_approval(self):
        """Determina si el finiquito requiere aprobación especial"""
        # Finiquitos altos requieren aprobación
        if self.monto_finiquito > 1000000:  # > 1M
            return True
        
        # Despidos requieren aprobación
        if self.motivo_salida in ['despido', 'abandono']:
            return True
        
        return False
    
    def aprobar(self, usuario):
        """Aprueba el finiquito"""
        from django.utils import timezone
        
        self.estado_finiquito = 'aprobado'
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def get_color_estado(self):
        """Retorna color para el estado en el frontend"""
        colors = {
            'pendiente': '#ffc107',
            'calculado': '#17a2b8',
            'aprobado': '#28a745',
            'pagado': '#198754',
            'observado': '#dc3545'
        }
        return colors.get(self.estado_finiquito, '#6c757d')
