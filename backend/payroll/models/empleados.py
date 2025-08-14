from django.db import models
from .cierre import CierrePayroll


class Empleados_Cierre(models.Model):
    """
    Empleados que forman parte de un cierre específico.
    Representa la plantilla del mes para el período.
    """
    
    # Relación principal
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='empleados'
    )
    
    # Datos del empleado
    rut_empleado = models.CharField(
        max_length=12,
        help_text="RUT del empleado (ej: 12345678-9)"
    )
    nombre_completo = models.CharField(
        max_length=200,
        help_text="Nombre completo del empleado"
    )
    
    # Estado en el período
    estado_empleado = models.CharField(
        max_length=20,
        choices=[
            ('activo', 'Activo'),
            ('nuevo_ingreso', 'Nuevo Ingreso'),
            ('finiquito', 'Finiquito'),
            ('licencia', 'Licencia'),
            ('suspension', 'Suspensión')
        ],
        default='activo'
    )
    
    # Fechas relevantes
    fecha_ingreso = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de ingreso a la empresa"
    )
    fecha_salida = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de salida si aplica"
    )
    
    # Información adicional
    cargo = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cargo del empleado"
    )
    departamento = models.CharField(
        max_length=100,
        blank=True,
        help_text="Departamento al que pertenece"
    )
    centro_costo = models.CharField(
        max_length=50,
        blank=True,
        help_text="Centro de costo"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payroll_empleados_cierre'
        verbose_name = 'Empleado del Cierre'
        verbose_name_plural = 'Empleados del Cierre'
        unique_together = [['cierre_payroll', 'rut_empleado']]
        ordering = ['nombre_completo']
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.rut_empleado}) - {self.cierre_payroll.periodo}"
    
    def is_nuevo_en_periodo(self):
        """Determina si es un empleado nuevo en este período"""
        return self.estado_empleado == 'nuevo_ingreso'
    
    def is_salida_en_periodo(self):
        """Determina si el empleado salió en este período"""
        return self.estado_empleado == 'finiquito'
    
    def get_total_haberes(self):
        """Calcula total de haberes del empleado en este cierre"""
        from .items import Item_Empleado
        return Item_Empleado.objects.filter(
            empleado_cierre=self,
            item_cierre__tipo_item='haberes'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
    
    def get_total_descuentos(self):
        """Calcula total de descuentos del empleado en este cierre"""
        from .items import Item_Empleado
        return Item_Empleado.objects.filter(
            empleado_cierre=self,
            item_cierre__tipo_item='descuentos'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
    
    def get_liquido_pagado(self):
        """Calcula líquido a pagar (haberes - descuentos)"""
        return self.get_total_haberes() - self.get_total_descuentos()
