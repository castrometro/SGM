from django.db import models
from api.models import Cliente  # Asumiendo que ya tienes este modelo
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


def libro_remuneraciones_upload_to(instance, filename):
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    cliente_id = instance.cierre.cliente.id
    periodo = instance.cierre.periodo
    return f"remuneraciones/{cliente_id}/{periodo}/libro/{now}_{filename}"

def movimientos_mes_upload_to(instance, filename):
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    cliente_id = instance.cierre.cliente.id
    periodo = instance.cierre.periodo
    return f"remuneraciones/{cliente_id}/{periodo}/mov_mes/{now}_{filename}"

def analista_upload_to(instance, filename):
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    cliente_id = instance.cierre.cliente.id
    periodo = instance.cierre.periodo
    tipo_archivo = instance.tipo_archivo
    return f"remuneraciones/{cliente_id}/{periodo}/{tipo_archivo}/{now}_{filename}"


class Empleado(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombres = models.CharField(max_length=120)
    apellido_paterno = models.CharField(max_length=120)
    apellido_materno = models.CharField(max_length=120, blank=True)
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.rut} - {self.nombres} {self.apellido_paterno}"




class CierreNomina(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    # Podrías usar un campo DateField si prefieres manejarlo como fecha, ejemplo periodo = models.DateField()
    periodo = models.CharField(max_length=7)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('listo_para_revision', 'Listo para Revisión'),
            ('aprobado', 'Aprobado'),
            ('cerrado', 'Cerrado'),
            ('rechazado', 'Rechazado'),
        ],
        default='pendiente'
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    usuario_analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_analista')
    usuario_supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cierres_supervisor')

    class Meta:
        unique_together = ('cliente', 'periodo')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.periodo} ({self.estado})"


# === Modelo para manejar la subida de archivos de libro de remuneraciones ===
class LibroRemuneracionesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='libros_remuneraciones')
    archivo = models.FileField(upload_to=libro_remuneraciones_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=60,
        choices=[
            ('pendiente', 'Pendiente'),
            ('analizando_hdrs', 'Analizando Headers'),
            ('hdrs_analizados', 'Headers Analizados'),
            ('clasif_en_proceso', 'Clasificación en Proceso'),
            ('clasif_pendiente', 'Clasificación Pendiente'),
            ('clasificado', 'Clasificado'),
            ('con_error', 'Con Error'),
        ],
        default='pendiente'
    )
    header_json = models.JSONField(default=list)

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.cierre.periodo} - Libro Remuneraciones"



CLASIFICACION_CHOICES = [
    ('haber', 'Haber'),
    ('descuento', 'Descuento'),
    ('informacion', 'Información'),
]

class ConceptoRemuneracion(models.Model):
    """
    Representa un concepto individual detectado en algún libro de remuneraciones
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre_concepto = models.CharField(max_length=120)
    clasificacion = models.CharField(max_length=20, choices=CLASIFICACION_CHOICES)
    hashtags = models.JSONField(default=list)  # Ejemplo: ["Bono", "Legal"]
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_clasifica = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('cliente', 'nombre_concepto')

    def __str__(self):
        return f"{self.cliente.nombre} - {self.nombre_concepto} [{self.clasificacion}]"

    def hashtag_string(self):
        return ", ".join(self.hashtags)


class MovimientosMesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='movimientos_mes')
    archivo = models.FileField(upload_to=movimientos_mes_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('procesado', 'Procesado'),
            ('con_error', 'Con Error'),
        ],
        default='pendiente'
    )

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.cierre.periodo}"

class MovimientoAltaBaja(models.Model):
    movimientos_mes = models.ForeignKey(MovimientosMesUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    tipo_movimiento = models.CharField(max_length=20, choices=[('alta', 'Alta'), ('baja', 'Baja')])
    fecha = models.DateField()
    motivo = models.CharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return f"{self.rut} - {self.tipo_movimiento} - {self.fecha}"

class MovimientoAusentismo(models.Model):
    movimientos_mes = models.ForeignKey(MovimientosMesUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    tipo_ausentismo = models.CharField(max_length=80)  # Licencia, Permiso, etc.
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.IntegerField()

    def __str__(self):
        return f"{self.rut} - {self.tipo_ausentismo} ({self.fecha_inicio} a {self.fecha_fin})"


class MovimientoVacaciones(models.Model):
    movimientos_mes = models.ForeignKey(MovimientosMesUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.IntegerField()

    def __str__(self):
        return f"{self.rut} - Vacaciones ({self.fecha_inicio} a {self.fecha_fin})"
    

class VariacionSueldoBase(models.Model):
    movimientos_mes = models.ForeignKey(MovimientosMesUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    sueldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    sueldo_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()

    def __str__(self):
        return f"{self.rut} - {self.sueldo_anterior} ➔ {self.sueldo_nuevo} ({self.fecha})"


class VariacionTipoContrato(models.Model):
    movimientos_mes = models.ForeignKey(MovimientosMesUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    tipo_anterior = models.CharField(max_length=80)
    tipo_nuevo = models.CharField(max_length=80)
    fecha = models.DateField()

    def __str__(self):
        return f"{self.rut} - {self.tipo_anterior} ➔ {self.tipo_nuevo} ({self.fecha})"
    

class ArchivoAnalistaUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_analista')
    tipo_archivo = models.CharField(max_length=20, choices=[
        ('ingresos', 'Ingresos'),
        ('finiquitos', 'Finiquitos'),
        ('ausentismos', 'Ausentismos'),
    ])
    archivo = models.FileField(upload_to=analista_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('procesado', 'Procesado'),
            ('con_error', 'Con Error'),
        ],
        default='pendiente'
    )

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.cierre.periodo} - {self.tipo_archivo}"


    

class RegistroIngresoAnalista(models.Model):
    archivo_upload = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    fecha_ingreso = models.DateField()
    cargo = models.CharField(max_length=80, blank=True, null=True)
    # Otros campos del archivo real

    def __str__(self):
        return f"{self.rut} - Ingreso {self.fecha_ingreso}"

class RegistroFiniquitoAnalista(models.Model):
    archivo_upload = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    fecha_finiquito = models.DateField()
    motivo = models.CharField(max_length=120, blank=True, null=True)
    # Otros campos...

    def __str__(self):
        return f"{self.rut} - Finiquito {self.fecha_finiquito}"

class RegistroAusentismoAnalista(models.Model):
    archivo_upload = models.ForeignKey(ArchivoAnalistaUpload, on_delete=models.CASCADE)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120)
    tipo_ausentismo = models.CharField(max_length=80)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.IntegerField()

    def __str__(self):
        return f"{self.rut} - {self.tipo_ausentismo} ({self.fecha_inicio} a {self.fecha_fin})"


class IncidenciaComparacion(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='incidencias_comparacion')
    tipo_incidencia = models.CharField(max_length=30)
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    detalle = models.TextField()
    resuelto = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.tipo_incidencia} - {self.rut}"




def novedades_upload_to(instance, filename):
    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"remuneraciones/{instance.cliente.id}/{instance.periodo}/novedades/{now}_{filename}"

class ArchivoNovedadesUpload(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='archivos_novedades')
    archivo = models.FileField(upload_to=novedades_upload_to)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_proceso', 'En Proceso'),
            ('procesado', 'Procesado'),
            ('con_error', 'Con Error'),
        ],
        default='pendiente'
    )

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.cierre.periodo} - Novedades"



class Novedad(models.Model):
    archivo_upload = models.ForeignKey(ArchivoNovedadesUpload, on_delete=models.CASCADE, null=True, blank=True, related_name='novedades')
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120, blank=True, null=True)
    concepto = models.CharField(max_length=120)  # Header del archivo novedad
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    # Mapping a ConceptoRemuneracion (si existe)
    mapping = models.ForeignKey('ConceptoRemuneracion', on_delete=models.SET_NULL, null=True, blank=True)
    # Heredamos categoría y hashtags por conveniencia (para acelerar reporting)
    clasificacion = models.CharField(max_length=20, choices=CLASIFICACION_CHOICES, blank=True, null=True)
    hashtags = models.JSONField(default=list, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.rut} - {self.concepto} - {self.monto}"


class IncidenciaNovedad(models.Model):
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE, related_name='incidencias_novedad')
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=120, blank=True, null=True)
    concepto = models.CharField(max_length=120)
    monto_novedad = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    monto_libro = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    tipo_incidencia = models.CharField(max_length=60)
    detalle = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_resuelto = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.cierre.cliente.nombre} - {self.cierre.periodo} - {self.rut} - {self.concepto} [{self.tipo_incidencia}]"


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


class RegistroNomina(models.Model):
    """Almacena los montos del libro de remuneraciones por empleado."""

    cierre = models.ForeignKey(
        CierreNomina,
        on_delete=models.CASCADE,
        related_name="registros_nomina",
    )
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="registros_nomina",
    )
    data = models.JSONField()

    class Meta:
        unique_together = ("cierre", "empleado")

    def __str__(self):
        return f"{self.empleado.rut} - {self.cierre.periodo}"
