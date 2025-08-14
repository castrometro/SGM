from django.db import models
from django.conf import settings
from .cierre import CierrePayroll
from .empleados import Empleados_Cierre


class Ausentismos_Cierre(models.Model):
    """
    Registro de ausentismos procesados en el cierre.
    Incluye licencias médicas, vacaciones, permisos, etc.
    """
    
    # Relaciones principales
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='ausentismos'
    )
    empleado_cierre = models.ForeignKey(
        Empleados_Cierre,
        on_delete=models.CASCADE,
        related_name='ausentismos'
    )
    
    # Tipo de ausentismo
    tipo_ausentismo = models.CharField(
        max_length=30,
        choices=[
            ('licencia_medica', 'Licencia Médica'),
            ('vacaciones', 'Vacaciones'),
            ('permiso_sin_goce', 'Permiso Sin Goce'),
            ('permiso_con_goce', 'Permiso Con Goce'),
            ('licencia_maternidad', 'Licencia Maternidad'),
            ('licencia_paternidad', 'Licencia Paternidad'),
            ('suspension', 'Suspensión'),
            ('falta_injustificada', 'Falta Injustificada'),
            ('accidente_laboral', 'Accidente Laboral'),
            ('capacitacion', 'Capacitación'),
            ('otros', 'Otros')
        ],
        help_text="Tipo de ausentismo del empleado"
    )
    
    # Fechas del ausentismo
    fecha_inicio = models.DateField(
        help_text="Fecha de inicio del ausentismo"
    )
    fecha_fin = models.DateField(
        help_text="Fecha de fin del ausentismo"
    )
    dias_ausentismo = models.IntegerField(
        help_text="Cantidad total de días de ausentismo"
    )
    
    # Información adicional
    motivo_detallado = models.TextField(
        blank=True,
        help_text="Descripción detallada del motivo"
    )
    documento_respaldo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Número de documento de respaldo (ej: N° licencia médica)"
    )
    
    # Impacto en remuneración
    afecta_remuneracion = models.BooleanField(
        default=True,
        help_text="Si el ausentismo afecta la remuneración"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de descuento aplicado (0-100)"
    )
    monto_descontado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto total descontado por el ausentismo"
    )
    
    # Estado del ausentismo
    estado_ausentismo = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('validado', 'Validado'),
            ('aprobado', 'Aprobado'),
            ('rechazado', 'Rechazado'),
            ('observado', 'Con Observaciones')
        ],
        default='pendiente'
    )
    
    # Información de subsidio (para licencias médicas)
    tiene_subsidio = models.BooleanField(
        default=False,
        help_text="Si aplica subsidio por licencia médica"
    )
    monto_subsidio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto del subsidio a recibir"
    )
    
    # Observaciones y seguimiento
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones adicionales del ausentismo"
    )
    requiere_seguimiento = models.BooleanField(
        default=False,
        help_text="Si requiere seguimiento especial"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que validó el ausentismo"
    )
    fecha_validacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de validación del ausentismo"
    )
    
    class Meta:
        db_table = 'payroll_ausentismos_cierre'
        verbose_name = 'Ausentismo del Cierre'
        verbose_name_plural = 'Ausentismos del Cierre'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.empleado_cierre.nombre_completo} - {self.get_tipo_ausentismo_display()} ({self.fecha_inicio} - {self.fecha_fin})"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar fechas
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError(
                "La fecha de fin no puede ser anterior a la fecha de inicio"
            )
        
        # Validar días de ausentismo
        dias_calculados = (self.fecha_fin - self.fecha_inicio).days + 1
        if self.dias_ausentismo != dias_calculados:
            raise ValidationError(
                f"Los días de ausentismo ({self.dias_ausentismo}) no coinciden con el período calculado ({dias_calculados} días)"
            )
        
        # Validar porcentaje de descuento
        if not (0 <= self.porcentaje_descuento <= 100):
            raise ValidationError(
                "El porcentaje de descuento debe estar entre 0 y 100"
            )
    
    def save(self, *args, **kwargs):
        """Override save para calcular días automáticamente"""
        if self.fecha_inicio and self.fecha_fin:
            self.dias_ausentismo = (self.fecha_fin - self.fecha_inicio).days + 1
        super().save(*args, **kwargs)
    
    def calcular_monto_descuento(self, sueldo_base_empleado):
        """Calcula el monto a descontar basado en el sueldo base"""
        if not self.afecta_remuneracion:
            return 0
        
        # Calcular descuento proporcional por días
        descuento_diario = sueldo_base_empleado / 30  # Asumir 30 días por mes
        descuento_total = descuento_diario * self.dias_ausentismo
        
        # Aplicar porcentaje de descuento
        descuento_final = descuento_total * (self.porcentaje_descuento / 100)
        
        return round(descuento_final, 0)
    
    def get_dias_habiles(self):
        """Calcula días hábiles en el período de ausentismo"""
        from datetime import timedelta
        
        dias_habiles = 0
        current_date = self.fecha_inicio
        
        while current_date <= self.fecha_fin:
            # Lunes a Viernes (0-4)
            if current_date.weekday() < 5:
                dias_habiles += 1
            current_date += timedelta(days=1)
        
        return dias_habiles
    
    def is_ausentismo_largo(self):
        """Determina si es un ausentismo largo (más de 15 días)"""
        return self.dias_ausentismo > 15
    
    def requires_medical_certificate(self):
        """Determina si requiere certificado médico"""
        return self.tipo_ausentismo in [
            'licencia_medica', 
            'licencia_maternidad', 
            'licencia_paternidad',
            'accidente_laboral'
        ]
    
    def validar(self, usuario):
        """Valida el ausentismo"""
        from django.utils import timezone
        
        self.estado_ausentismo = 'validado'
        self.validado_por = usuario
        self.fecha_validacion = timezone.now()
        self.save()
    
    def get_color_estado(self):
        """Retorna color para el estado en el frontend"""
        colors = {
            'pendiente': '#ffc107',
            'validado': '#17a2b8',
            'aprobado': '#28a745',
            'rechazado': '#dc3545',
            'observado': '#fd7e14'
        }
        return colors.get(self.estado_ausentismo, '#6c757d')
    
    def get_impacto_resumen(self):
        """Retorna resumen del impacto del ausentismo"""
        impacto = {
            'dias_totales': self.dias_ausentismo,
            'dias_habiles': self.get_dias_habiles(),
            'afecta_sueldo': self.afecta_remuneracion,
            'monto_descontado': self.monto_descontado,
            'tiene_subsidio': self.tiene_subsidio,
            'monto_subsidio': self.monto_subsidio
        }
        return impacto
