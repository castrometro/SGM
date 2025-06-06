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
    vigente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.nombre_concepto}"


class RegistroConceptoEmpleado(models.Model):
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, related_name="conceptos")
    concepto = models.ForeignKey(ConceptoRemuneracion, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_concepto_original = models.CharField(max_length=120)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.empleado.rut} - {self.nombre_concepto_original} - ${self.monto}"


class MovimientoIngreso(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()


class MovimientoFiniquito(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    fecha_finiquito = models.DateField()
    motivo = models.CharField(max_length=120, blank=True, null=True)


class MovimientoAusentismo(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    empleado = models.ForeignKey(EmpleadoCierre, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    tipo_ausentismo = models.CharField(max_length=80)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.IntegerField()


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
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')


class ArchivoAnalistaUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_analista')
    tipo_archivo = models.CharField(max_length=20, choices=[
        ('ingresos', 'Ingresos'),
        ('finiquitos', 'Finiquitos'),
        ('ausentismos', 'Ausentismos')
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
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('procesado', 'Procesado'),
        ('con_error', 'Con Error')
    ], default='pendiente')


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
