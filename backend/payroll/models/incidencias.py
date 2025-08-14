from django.db import models
from django.conf import settings
from .cierre import CierrePayroll
from .items import Item_Empleado


class Incidencias_Cierre(models.Model):
    """
    Incidencias detectadas automáticamente durante el análisis de variaciones.
    Registra diferencias significativas entre períodos que requieren revisión.
    """
    
    # Relación principal
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='incidencias'
    )
    
    # Items comparados
    item_empleado_actual = models.ForeignKey(
        Item_Empleado,
        on_delete=models.CASCADE,
        related_name='incidencias_actual',
        help_text="Item del período actual"
    )
    item_empleado_anterior = models.ForeignKey(
        Item_Empleado,
        on_delete=models.CASCADE,
        related_name='incidencias_anterior',
        null=True,
        blank=True,
        help_text="Item del período anterior (null si es empleado nuevo)"
    )
    
    # Tipo de incidencia
    tipo_incidencia = models.CharField(
        max_length=30,
        choices=[
            ('variacion_significativa', 'Variación Significativa'),
            ('empleado_nuevo', 'Empleado Nuevo'),
            ('empleado_salida', 'Empleado con Salida'),
            ('item_nuevo', 'Item Nuevo'),
            ('item_eliminado', 'Item Eliminado'),
            ('valor_cero', 'Valor en Cero'),
            ('valor_negativo', 'Valor Negativo'),
            ('fuera_rango', 'Fuera de Rango Normal')
        ],
        help_text="Clasificación de la incidencia detectada"
    )
    
    # Valores de comparación
    valor_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor del período anterior"
    )
    valor_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Valor del período actual"
    )
    porcentaje_variacion = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Porcentaje de variación calculado"
    )
    
    # Prioridad de la incidencia
    prioridad = models.CharField(
        max_length=10,
        choices=[
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('critica', 'Crítica')
        ],
        default='media',
        help_text="Prioridad de revisión de la incidencia"
    )
    
    # Estado de validación
    estado_validacion = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_revision', 'En Revisión'),
            ('validada', 'Validada'),
            ('descartada', 'Descartada'),
            ('requiere_accion', 'Requiere Acción')
        ],
        default='pendiente'
    )
    
    # Información de revisión
    explicacion = models.TextField(
        blank=True,
        help_text="Explicación de la incidencia (completada por analista)"
    )
    accion_tomada = models.TextField(
        blank=True,
        help_text="Descripción de la acción tomada para resolver"
    )
    
    # Asignación y seguimiento
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_asignadas',
        help_text="Usuario responsable de revisar la incidencia"
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidencias_validadas',
        help_text="Usuario que validó la incidencia"
    )
    
    # Fechas de control
    fecha_deteccion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha cuando se detectó la incidencia"
    )
    fecha_asignacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de asignación a usuario"
    )
    fecha_validacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de validación/resolución"
    )
    
    # Metadatos adicionales
    tolerancia_aplicada = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de tolerancia que se aplicó en la detección"
    )
    algoritmo_deteccion = models.CharField(
        max_length=50,
        default='comparacion_porcentual',
        help_text="Algoritmo usado para detectar la incidencia"
    )
    
    class Meta:
        db_table = 'payroll_incidencias_cierre'
        verbose_name = 'Incidencia del Cierre'
        verbose_name_plural = 'Incidencias del Cierre'
        ordering = ['-prioridad', '-fecha_deteccion']
        indexes = [
            models.Index(fields=['estado_validacion', 'prioridad']),
            models.Index(fields=['asignado_a', 'estado_validacion']),
            models.Index(fields=['cierre_payroll', 'tipo_incidencia']),
        ]
    
    def __str__(self):
        empleado = self.item_empleado_actual.empleado_cierre.nombre_completo
        item = self.item_empleado_actual.item_cierre.codigo_item
        return f"{empleado} - {item}: {self.get_tipo_incidencia_display()}"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que los items pertenezcan al mismo empleado
        if (self.item_empleado_anterior and 
            self.item_empleado_anterior.empleado_cierre.rut_empleado != 
            self.item_empleado_actual.empleado_cierre.rut_empleado):
            raise ValidationError(
                "Los items deben pertenecer al mismo empleado"
            )
        
        # Validar que sean del mismo tipo de item
        if (self.item_empleado_anterior and
            self.item_empleado_anterior.item_cierre.codigo_item !=
            self.item_empleado_actual.item_cierre.codigo_item):
            raise ValidationError(
                "Los items deben ser del mismo tipo"
            )
    
    def save(self, *args, **kwargs):
        """Override save para calcular valores automáticamente"""
        # Establecer valor actual
        self.valor_actual = self.item_empleado_actual.monto
        
        # Establecer valor anterior y calcular variación
        if self.item_empleado_anterior:
            self.valor_anterior = self.item_empleado_anterior.monto
            if self.valor_anterior and self.valor_anterior != 0:
                self.porcentaje_variacion = (
                    (self.valor_actual - self.valor_anterior) / self.valor_anterior
                ) * 100
        
        # Determinar prioridad automáticamente
        if not self.pk:  # Solo al crear
            self.prioridad = self.calcular_prioridad()
        
        super().save(*args, **kwargs)
    
    def calcular_prioridad(self):
        """Calcula la prioridad basada en el tipo y magnitud de la variación"""
        # Empleados nuevos o salidas son alta prioridad
        if self.tipo_incidencia in ['empleado_nuevo', 'empleado_salida']:
            return 'alta'
        
        # Valores negativos o en cero son críticos
        if self.tipo_incidencia in ['valor_negativo', 'valor_cero']:
            return 'critica'
        
        # Variaciones muy altas son críticas
        if (self.porcentaje_variacion and 
            abs(self.porcentaje_variacion) > 50):
            return 'critica'
        
        # Variaciones altas son alta prioridad
        if (self.porcentaje_variacion and 
            abs(self.porcentaje_variacion) > 25):
            return 'alta'
        
        # El resto son media prioridad
        return 'media'
    
    def asignar_a(self, usuario):
        """Asigna la incidencia a un usuario"""
        from django.utils import timezone
        
        self.asignado_a = usuario
        self.fecha_asignacion = timezone.now()
        if self.estado_validacion == 'pendiente':
            self.estado_validacion = 'en_revision'
        self.save()
    
    def validar(self, usuario, explicacion, accion_tomada=None):
        """Valida la incidencia"""
        from django.utils import timezone
        
        self.validado_por = usuario
        self.fecha_validacion = timezone.now()
        self.explicacion = explicacion
        if accion_tomada:
            self.accion_tomada = accion_tomada
        self.estado_validacion = 'validada'
        self.save()
    
    def descartar(self, usuario, razon):
        """Descarta la incidencia"""
        from django.utils import timezone
        
        self.validado_por = usuario
        self.fecha_validacion = timezone.now()
        self.explicacion = f"DESCARTADA: {razon}"
        self.estado_validacion = 'descartada'
        self.save()
    
    def get_color_prioridad(self):
        """Retorna color para la prioridad en el frontend"""
        colors = {
            'baja': '#28a745',
            'media': '#ffc107',
            'alta': '#fd7e14',
            'critica': '#dc3545'
        }
        return colors.get(self.prioridad, '#6c757d')
    
    def get_color_estado(self):
        """Retorna color para el estado en el frontend"""
        colors = {
            'pendiente': '#6c757d',
            'en_revision': '#ffc107',
            'validada': '#28a745',
            'descartada': '#17a2b8',
            'requiere_accion': '#dc3545'
        }
        return colors.get(self.estado_validacion, '#6c757d')
    
    def get_resumen_variacion(self):
        """Retorna resumen de la variación para mostrar"""
        if not self.valor_anterior:
            return "Empleado nuevo"
        
        if self.porcentaje_variacion is None:
            return "Sin variación calculable"
        
        signo = "+" if self.porcentaje_variacion > 0 else ""
        return f"{signo}{self.porcentaje_variacion:.1f}%"
    
    def get_empleado_nombre(self):
        """Obtiene el nombre del empleado de la incidencia"""
        return self.item_empleado_actual.empleado_cierre.nombre_completo
    
    def get_item_codigo(self):
        """Obtiene el código del item de la incidencia"""
        return self.item_empleado_actual.item_cierre.codigo_item
    
    def is_overdue(self):
        """Determina si la incidencia está vencida"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.estado_validacion in ['validada', 'descartada']:
            return False
        
        # Críticas: 1 día, Altas: 2 días, Medias: 3 días, Bajas: 5 días
        dias_limite = {
            'critica': 1,
            'alta': 2,
            'media': 3,
            'baja': 5
        }
        
        limite = self.fecha_deteccion + timedelta(days=dias_limite.get(self.prioridad, 3))
        return timezone.now() > limite
