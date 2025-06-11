from django.db import models
from api.models import Cliente
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

CLASIFICACION_CHOICES = [
    ('haber', 'Haber'),
    ('descuento', 'Descuento'),
    ('informacion', 'Información'),
]

def libro_remuneraciones_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/libro/{now}_{filename}"

def movimientos_mes_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/mov_mes/{now}_{filename}"

def analista_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/{instance.tipo_archivo}/{now}_{filename}"

def novedades_upload_to(instance, filename):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cierre.cliente.id}/{instance.cierre.periodo}/novedades/{now}_{filename}"


class CierreNomina(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=7)  # Ej: "2025-06"
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('datos_consolidados', 'Datos Consolidados'),
            ('reportes_generados', 'Reportes Generados'),
            ('validacion_senior', 'Validación Senior'),
            ('completado', 'Completado'),
        ],
        default='pendiente'
    )
    usuario_analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_analista')

    class Meta:
        unique_together = ('cliente', 'periodo')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo}"


class EmpleadoCierre(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='empleados')
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)
    rut_empresa = models.CharField(max_length=20)
    dias_trabajados = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("cierre", "rut")

    def __str__(self):
        return f"{self.rut} - {self.nombre} {self.apellido_paterno}"


class ConceptoRemuneracion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre_concepto = models.CharField(max_length=120)
    clasificacion = models.CharField(max_length=20, choices=CLASIFICACION_CHOICES)
    hashtags = models.JSONField(default=list, blank=True)
    usuario_clasifica = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conceptos_clasificados",
    )
    vigente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.nombre_concepto}"


class RegistroConceptoEmpleado(models.Model):
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoRemuneracion, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_concepto_original = models.CharField(max_length=200)
    monto = models.CharField(max_length=255, blank=True, null=True)  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empleado', 'nombre_concepto_original')

    def __str__(self):
        return f"{self.empleado} - {self.nombre_concepto_original}: {self.monto}"
    
    @property
    def monto_numerico(self):
        """Convierte el monto a número para cálculos, retorna 0 si no es posible"""
        try:
            return float(self.monto) if self.monto else 0
        except (ValueError, TypeError):
            return 0
    
    @property
    def es_numerico(self):
        """Verifica si el monto puede convertirse a número"""
        try:
            float(self.monto) if self.monto else 0
            return True
        except (ValueError, TypeError):
            return False


# Modelos para Movimientos_Mes completos

class MovimientoAltaBaja(models.Model):
    """Modelo para Altas y Bajas (b.1)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    fecha_retiro = models.DateField(null=True, blank=True)
    tipo_contrato = models.CharField(max_length=80)
    dias_trabajados = models.IntegerField()
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2)
    alta_o_baja = models.CharField(max_length=20)  # "ALTA" o "BAJA"
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - {self.alta_o_baja}"


class MovimientoAusentismo(models.Model):
    """Modelo completo para Ausentismos (b.2)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    fecha_inicio_ausencia = models.DateField()
    fecha_fin_ausencia = models.DateField()
    dias = models.IntegerField()
    tipo = models.CharField(max_length=80)
    motivo = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - {self.tipo}"


class MovimientoVacaciones(models.Model):
    """Modelo para Vacaciones (b.3)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    fecha_inicio = models.DateField()
    fecha_fin_vacaciones = models.DateField()
    fecha_retorno = models.DateField()
    cantidad_dias = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Vacaciones"


class MovimientoVariacionSueldo(models.Model):
    """Modelo para Variaciones Sueldo Base (b.4)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    tipo_contrato = models.CharField(max_length=80)
    sueldo_base_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_base_actual = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje_reajuste = models.DecimalField(max_digits=5, decimal_places=2)
    variacion_pesos = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Variación Sueldo"


class MovimientoVariacionContrato(models.Model):
    """Modelo para Variaciones Tipo Contrato (b.5)"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    nombres_apellidos = models.CharField(max_length=200)
    rut = models.CharField(max_length=12)
    empresa_nombre = models.CharField(max_length=120)
    cargo = models.CharField(max_length=120)
    centro_de_costo = models.CharField(max_length=120)
    sucursal = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    tipo_contrato_anterior = models.CharField(max_length=80)
    tipo_contrato_actual = models.CharField(max_length=80)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombres_apellidos} - Cambio Contrato"


class LibroRemuneracionesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='libros_remuneraciones')
    archivo = models.FileField(upload_to=libro_remuneraciones_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=60, choices=[
        ('pendiente', 'Pendiente'),
        ('analizando_hdrs', 'Analizando Headers'),
        ('hdrs_analizados', 'Headers Analizados'),
        ('clasif_en_proceso', 'Clasificación en Proceso'),
        ('clasif_pendiente', 'Clasificación Pendiente'),
        ('clasificado', 'Clasificado'),
        ('con_error', 'Con Error')
    ], default='pendiente')
    header_json = models.JSONField(default=list)


class MovimientosMesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='movimientos_mes')
    archivo = models.FileField(upload_to=movimientos_mes_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error'),
        ('con_errores_parciales', 'Con Errores Parciales')
    ], default='pendiente')
    resultados_procesamiento = models.JSONField(default=dict, blank=True)


class ArchivoAnalistaUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_analista')
    tipo_archivo = models.CharField(max_length=20, choices=[
        ('ingresos', 'Ingresos'),
        ('finiquitos', 'Finiquitos'),
        ('incidencias', 'Incidencias')
    ])
    archivo = models.FileField(upload_to=analista_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')


class ArchivoNovedadesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_novedades')
    archivo = models.FileField(upload_to=novedades_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=60, choices=[
        ('pendiente', 'Pendiente'),
        ('analizando_hdrs', 'Analizando Headers'),
        ('hdrs_analizados', 'Headers Analizados'),
        ('clasif_en_proceso', 'Clasificación en Proceso'),
        ('clasif_pendiente', 'Clasificación Pendiente'),
        ('clasificado', 'Clasificado'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')
    header_json = models.JSONField(default=list)


class ChecklistItem(models.Model):
    CHECK_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('no_realizado', 'No Realizado'),
    ]

    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='checklist')
    descripcion = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=CHECK_CHOICES, default='pendiente')
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cierre} - {self.descripcion} - {self.estado}"


# Modelos específicos para Novedades

class EmpleadoCierreNovedades(models.Model):
    """Modelo específico para empleados en el procesamiento de novedades"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='empleados_novedades')
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("cierre", "rut")

    def __str__(self):
        return f"Novedades - {self.rut} - {self.nombre} {self.apellido_paterno}"


class ConceptoRemuneracionNovedades(models.Model):
    """Mapeo entre headers de novedades y conceptos del libro de remuneraciones"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    
    # Header tal como aparece en el archivo de novedades
    nombre_concepto_novedades = models.CharField(max_length=120)
    
    # Mapeo directo al concepto del libro de remuneraciones
    concepto_libro = models.ForeignKey(
        ConceptoRemuneracion, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Concepto del libro de remuneraciones al que mapea este header de novedades"
    )
    
    # Metadatos del mapeo
    usuario_mapea = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mapeos_novedades_creados",
    )
    activo = models.BooleanField(default=True)
    fecha_mapeo = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto_novedades')

    def __str__(self):
        return f"{self.cliente.nombre}: {self.nombre_concepto_novedades} → {self.concepto_libro.nombre_concepto}"
    
    # Propiedades que delegan al concepto del libro
    @property
    def clasificacion(self):
        return self.concepto_libro.clasificacion if self.concepto_libro else None
    
    @property
    def hashtags(self):
        return self.concepto_libro.hashtags if self.concepto_libro else []
    
    @property
    def nombre_concepto(self):
        """Compatibilidad con código existente"""
        return self.nombre_concepto_novedades
    
    @property
    def vigente(self):
        """Compatibilidad con código existente"""
        return self.activo and (self.concepto_libro.vigente if self.concepto_libro else False)


class RegistroConceptoEmpleadoNovedades(models.Model):
    """Modelo específico para registros de conceptos de empleados en novedades"""
    empleado = models.ForeignKey(EmpleadoCierreNovedades, on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoRemuneracionNovedades, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_concepto_original = models.CharField(max_length=200)
    monto = models.CharField(max_length=255, blank=True, null=True)  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empleado', 'nombre_concepto_original')

    def __str__(self):
        return f"Novedades - {self.empleado} - {self.nombre_concepto_original}: {self.monto}"
    
    @property
    def monto_numerico(self):
        """Convierte el monto a número para cálculos, retorna 0 si no es posible"""
        try:
            return float(self.monto) if self.monto else 0
        except (ValueError, TypeError):
            return 0
    
    @property
    def es_numerico(self):
        """Verifica si el monto puede convertirse a número"""
        try:
            float(self.monto) if self.monto else 0
            return True
        except (ValueError, TypeError):
            return False
    
    @property
    def concepto_libro_equivalente(self):
        """Retorna el concepto del libro de remuneraciones equivalente"""
        return self.concepto.concepto_libro if self.concepto else None


# Modelos para datos del Analista

class AnalistaFiniquito(models.Model):
    """Datos de Finiquitos subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_retiro = models.DateField()
    motivo = models.CharField(max_length=200)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - Finiquito"


class AnalistaIncidencia(models.Model):
    """Datos de Incidencias subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_inicio_ausencia = models.DateField()
    fecha_fin_ausencia = models.DateField()
    dias = models.IntegerField()
    tipo_ausentismo = models.CharField(max_length=80)

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - {self.tipo_ausentismo}"


class AnalistaIngreso(models.Model):
    """Datos de Ingresos subidos por el analista"""
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    archivo_origen = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=200)
    fecha_ingreso = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=['cierre', 'rut']),
        ]

    def __str__(self):
        return f"{self.rut} - {self.nombre} - Ingreso"
