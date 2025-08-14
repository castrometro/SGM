from django.db import models
from django.conf import settings
from .cierre import CierrePayroll
from .empleados import Empleados_Cierre


class Ingresos_Cierre(models.Model):
    """
    Registro de nuevos ingresos procesados en el cierre.
    Contiene información específica de empleados que ingresan a la empresa.
    """
    
    # Relaciones principales
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='ingresos'
    )
    empleado_cierre = models.OneToOneField(
        Empleados_Cierre,
        on_delete=models.CASCADE,
        related_name='ingreso',
        help_text="Empleado asociado al ingreso"
    )
    
    # Información del ingreso
    fecha_ingreso = models.DateField(
        help_text="Fecha efectiva de ingreso"
    )
    primer_dia_trabajado = models.DateField(
        help_text="Primer día trabajado por el empleado"
    )
    
    # Tipo de contrato
    tipo_contrato = models.CharField(
        max_length=30,
        choices=[
            ('indefinido', 'Contrato Indefinido'),
            ('plazo_fijo', 'Plazo Fijo'),
            ('obra_faena', 'Por Obra o Faena'),
            ('honorarios', 'Honorarios'),
            ('practica', 'Práctica Profesional'),
            ('temporal', 'Trabajo Temporal'),
            ('part_time', 'Part Time'),
            ('otros', 'Otros')
        ],
        help_text="Tipo de contrato del nuevo empleado"
    )
    
    # Información salarial
    sueldo_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Sueldo base mensual pactado"
    )
    gratificacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Gratificación pactada (si aplica)"
    )
    colacion = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Asignación de colación"
    )
    movilizacion = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Asignación de movilización"
    )
    otros_beneficios = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Otros beneficios pactados"
    )
    
    # Información del cargo
    cargo_inicial = models.CharField(
        max_length=100,
        help_text="Cargo inicial del empleado"
    )
    departamento_inicial = models.CharField(
        max_length=100,
        help_text="Departamento inicial"
    )
    centro_costo_inicial = models.CharField(
        max_length=50,
        blank=True,
        help_text="Centro de costo inicial"
    )
    
    # Jornada laboral
    tipo_jornada = models.CharField(
        max_length=20,
        choices=[
            ('completa', 'Jornada Completa'),
            ('parcial', 'Jornada Parcial'),
            ('turnos', 'Sistema de Turnos'),
            ('flexible', 'Horario Flexible')
        ],
        default='completa'
    )
    horas_semanales = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=45.0,
        help_text="Horas semanales pactadas"
    )
    
    # Estado del ingreso
    estado_ingreso = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('documentos_ok', 'Documentos OK'),
            ('aprobado', 'Aprobado'),
            ('activo', 'Activo'),
            ('observado', 'Con Observaciones')
        ],
        default='pendiente'
    )
    
    # Documentación
    documentos_pendientes = models.TextField(
        blank=True,
        help_text="Lista de documentos pendientes"
    )
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones especiales del ingreso"
    )
    
    # Control interno
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que aprobó el ingreso"
    )
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de aprobación del ingreso"
    )
    
    class Meta:
        db_table = 'payroll_ingresos_cierre'
        verbose_name = 'Ingreso del Cierre'
        verbose_name_plural = 'Ingresos del Cierre'
        ordering = ['-fecha_ingreso']
    
    def __str__(self):
        return f"Ingreso {self.empleado_cierre.nombre_completo} - {self.fecha_ingreso}"
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que el empleado esté marcado como nuevo ingreso
        if self.empleado_cierre.estado_empleado != 'nuevo_ingreso':
            raise ValidationError(
                "El empleado debe estar marcado como 'nuevo_ingreso' para tener un registro de ingreso"
            )
        
        # Validar fechas
        if self.primer_dia_trabajado < self.fecha_ingreso:
            raise ValidationError(
                "El primer día trabajado no puede ser anterior a la fecha de ingreso"
            )
        
        # Validar sueldo base positivo
        if self.sueldo_base <= 0:
            raise ValidationError(
                "El sueldo base debe ser mayor a cero"
            )
    
    def calcular_proporcional_mes(self):
        """Calcula el proporcional del mes de ingreso"""
        import calendar
        from datetime import date
        
        # Obtener último día del mes
        ultimo_dia_mes = calendar.monthrange(
            self.fecha_ingreso.year, 
            self.fecha_ingreso.month
        )[1]
        
        # Calcular días trabajados en el mes
        dias_trabajados = ultimo_dia_mes - self.fecha_ingreso.day + 1
        
        # Calcular proporcional
        proporcional = (self.sueldo_base / ultimo_dia_mes) * dias_trabajados
        return round(proporcional, 0)
    
    def get_dias_trabajados_mes(self):
        """Calcula días trabajados en el mes del ingreso"""
        import calendar
        
        ultimo_dia_mes = calendar.monthrange(
            self.fecha_ingreso.year, 
            self.fecha_ingreso.month
        )[1]
        
        return ultimo_dia_mes - self.fecha_ingreso.day + 1
    
    def get_total_remuneracion_pactada(self):
        """Calcula la remuneración total pactada mensual"""
        return (
            self.sueldo_base + 
            self.gratificacion + 
            self.colacion + 
            self.movilizacion + 
            self.otros_beneficios
        )
    
    def requires_approval(self):
        """Determina si el ingreso requiere aprobación especial"""
        # Sueldos altos requieren aprobación
        if self.sueldo_base > 2000000:  # > 2M
            return True
        
        # Contratos especiales requieren aprobación
        if self.tipo_contrato in ['honorarios', 'obra_faena']:
            return True
        
        return False
    
    def aprobar(self, usuario):
        """Aprueba el ingreso"""
        from django.utils import timezone
        
        self.estado_ingreso = 'aprobado'
        self.aprobado_por = usuario
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def get_color_estado(self):
        """Retorna color para el estado en el frontend"""
        colors = {
            'pendiente': '#ffc107',
            'documentos_ok': '#17a2b8',
            'aprobado': '#28a745',
            'activo': '#198754',
            'observado': '#dc3545'
        }
        return colors.get(self.estado_ingreso, '#6c757d')
    
    def get_documentos_pendientes_list(self):
        """Retorna lista de documentos pendientes"""
        if not self.documentos_pendientes:
            return []
        return [doc.strip() for doc in self.documentos_pendientes.split(',') if doc.strip()]
