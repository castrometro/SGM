from django.db import models
from .cierre import CierrePayroll
from .empleados import Empleados_Cierre


class Item_Cierre(models.Model):
    """
    Catálogo de items de nómina para un cierre específico.
    Define los conceptos que pueden aplicar a los empleados.
    """
    
    # Relación principal
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='items_catalogo'
    )
    
    # Identificación del item
    codigo_item = models.CharField(
        max_length=50,
        help_text="Código único del item (ej: SUELDO_BASE, HRS_EXTRA)"
    )
    nombre_item = models.CharField(
        max_length=200,
        help_text="Nombre descriptivo del item"
    )
    
    # Clasificación
    tipo_item = models.CharField(
        max_length=20,
        choices=[
            ('haberes', 'Haberes'),
            ('descuentos', 'Descuentos'),
            ('aportes', 'Aportes Empresa'),
            ('informativos', 'Informativos')
        ],
        help_text="Tipo de item para clasificación"
    )
    
    # Configuración
    es_imponible = models.BooleanField(
        default=True,
        help_text="Si el item es imponible para cálculos de impuestos"
    )
    es_variable = models.BooleanField(
        default=False,
        help_text="Si el item puede variar mes a mes"
    )
    orden_display = models.IntegerField(
        default=0,
        help_text="Orden para mostrar en reportes"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll_item_cierre'
        verbose_name = 'Item del Cierre'
        verbose_name_plural = 'Items del Cierre'
        unique_together = [['cierre_payroll', 'codigo_item']]
        ordering = ['tipo_item', 'orden_display', 'nombre_item']
    
    def __str__(self):
        return f"{self.codigo_item} - {self.nombre_item}"
    
    def get_total_monto(self):
        """Calcula total del item sumando todos los empleados"""
        return self.item_empleados.aggregate(
            total=models.Sum('monto')
        )['total'] or 0
    
    def get_empleados_count(self):
        """Cuenta empleados que tienen este item"""
        return self.item_empleados.count()


class Item_Empleado(models.Model):
    """
    Valores específicos de cada item para cada empleado en el cierre.
    Esta es la tabla de detalle donde se almacenan los montos reales.
    """
    
    # Relaciones principales
    empleado_cierre = models.ForeignKey(
        Empleados_Cierre,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_cierre = models.ForeignKey(
        Item_Cierre,
        on_delete=models.CASCADE,
        related_name='item_empleados'
    )
    
    # Valores
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto del item para este empleado"
    )
    cantidad = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1,
        help_text="Cantidad (ej: horas, días, etc.)"
    )
    
    # Información adicional
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones específicas para este item"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    # Metadatos para comparación
    origen_dato = models.CharField(
        max_length=20,
        choices=[
            ('talana', 'Archivo Talana'),
            ('analista', 'Archivo Analista'),
            ('manual', 'Ingreso Manual'),
            ('calculado', 'Calculado por Sistema')
        ],
        default='talana'
    )
    
    class Meta:
        db_table = 'payroll_item_empleado'
        verbose_name = 'Item del Empleado'
        verbose_name_plural = 'Items del Empleado'
        unique_together = [['empleado_cierre', 'item_cierre']]
        ordering = ['item_cierre__tipo_item', 'item_cierre__orden_display']
    
    def __str__(self):
        return f"{self.empleado_cierre.nombre_completo} - {self.item_cierre.codigo_item}: ${self.monto:,.0f}"
    
    def get_valor_anterior(self):
        """Busca el valor de este item en el período anterior para el mismo empleado"""
        try:
            # Buscar cierre anterior del mismo cliente
            cierre_anterior = CierrePayroll.objects.filter(
                cliente=self.empleado_cierre.cierre_payroll.cliente,
                periodo__lt=self.empleado_cierre.cierre_payroll.periodo
            ).order_by('-periodo').first()
            
            if not cierre_anterior:
                return None
            
            # Buscar empleado en cierre anterior
            empleado_anterior = Empleados_Cierre.objects.filter(
                cierre_payroll=cierre_anterior,
                rut_empleado=self.empleado_cierre.rut_empleado
            ).first()
            
            if not empleado_anterior:
                return None
            
            # Buscar item anterior
            item_anterior = Item_Cierre.objects.filter(
                cierre_payroll=cierre_anterior,
                codigo_item=self.item_cierre.codigo_item
            ).first()
            
            if not item_anterior:
                return None
            
            # Buscar valor anterior
            item_empleado_anterior = Item_Empleado.objects.filter(
                empleado_cierre=empleado_anterior,
                item_cierre=item_anterior
            ).first()
            
            return item_empleado_anterior.monto if item_empleado_anterior else None
            
        except Exception:
            return None
    
    def calcular_variacion_porcentual(self):
        """Calcula la variación porcentual respecto al período anterior"""
        valor_anterior = self.get_valor_anterior()
        
        if valor_anterior is None or valor_anterior == 0:
            return None
        
        variacion = ((self.monto - valor_anterior) / valor_anterior) * 100
        return round(variacion, 2)
    
    def tiene_variacion_significativa(self, tolerancia_porcentaje=10.0):
        """Determina si la variación supera la tolerancia"""
        variacion = self.calcular_variacion_porcentual()
        
        if variacion is None:
            return False
        
        return abs(variacion) > tolerancia_porcentaje
