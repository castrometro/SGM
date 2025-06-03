from django.db import models
from django.contrib.auth.models import User
from api.models import Cliente, Usuario, Area
from django.utils.translation import gettext_lazy as _


# Create your models here.
# ======================================
#           CENTRO DE COSTO
# ======================================

class CentroCosto(models.Model):
    id = models.BigAutoField(
        primary_key=True,
        db_column='id_centro_costo'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column='cliente_id'
    )
    nombre = models.CharField(
        max_length=255,
        db_column='nombre'
    )

    class Meta:
        db_table = 'contabilidad_centrocosto'
        unique_together = ('cliente', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre}"


# ======================================
#              AUXILIAR
# ======================================

class Auxiliar(models.Model):
    rut_auxiliar = models.CharField(
        max_length=15,
        primary_key=True,
        db_column='rut_auxiliar'
    )
    nombre = models.CharField(
        max_length=255,
        blank=True,
        db_column='nombre_auxiliar'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column='fecha_creacion'
    )

    class Meta:
        db_table = 'contabilidad_auxiliar'
        ordering = ['rut_auxiliar']

    def __str__(self):
        return f"{self.rut_auxiliar} - {self.nombre}"
    
# ======================================
#          DOCUMENTOS
# ======================================
class TipoDocumento(models.Model):
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=255)

    class Meta:
        unique_together = ('cliente', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class CuentaContable(models.Model):
    id = models.BigAutoField(db_column='id_cuenta', primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255, blank=True)
    nombre_en = models.CharField(max_length=255, blank=True, null=True)  # <--- ESTE CAMPO
    # ...

    class Meta:
        unique_together = ('cliente', 'codigo')

    def __str__(self):
        return f"{self.codigo} - {self.nombre} - {self.nombre_en}"

class TipoDocumentoArchivo(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='tipo_documento/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archivo Tipo Documento - {self.cliente.nombre}"



class CierreContabilidad(models.Model):
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)
    periodo = models.CharField(max_length=7)  # Ej: "2025-04"
    fecha_inicio_libro = models.DateField(null=True, blank=True)  # <- calculada del parser (primer movimiento)
    fecha_fin_libro = models.DateField(null=True, blank=True) 
    estado = models.CharField(max_length=30, choices=[
        ("pendiente", "Pendiente"),
        ("procesando", "Procesando"),
        ("clasificacion", "Esperando Clasificación"),
        ("incidencias", "Incidencias Abiertas"),
        ("en_revision", "En Revisión"),
        ("rechazado", "Rechazado"),
        ("aprobado", "Aprobado"),
        ("completo", "Completo"),
    ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    cuentas_nuevas = models.IntegerField(default=0)
    resumen_parsing = models.JSONField(null=True, blank=True)
    parsing_completado = models.BooleanField(default=False)

    class Meta:
        unique_together = ('cliente', 'periodo')

    def __str__(self):
        return f"Cierre {self.periodo} - {self.cliente.nombre}"

def libro_upload_path(instance, filename):
    cliente_id = instance.cierre.cliente.id
    periodo = instance.cierre.periodo
    return f"libros/{cliente_id}/{periodo}/{filename}"

class LibroMayorUpload(models.Model):
    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
    ]
    id = models.BigAutoField(primary_key=True)
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE, related_name='libros')
    archivo = models.FileField(upload_to=libro_upload_path)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)
    errores = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")
    def __str__(self):
        return f"{self.cierre} | {self.archivo.name.split('/')[-1]}"

class AperturaCuenta(models.Model):
    id = models.BigAutoField(primary_key=True)
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    saldo_anterior = models.DecimalField(max_digits=20, decimal_places=2)


class MovimientoContable(models.Model):
    id = models.BigAutoField(primary_key=True)
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.SET_NULL, null=True)
    numero_documento = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(max_length=50, blank=True)
    numero_comprobante = models.CharField(max_length=50, blank=True)
    numero_interno = models.CharField(max_length=50, blank=True)
    centro_costo = models.ForeignKey(
        CentroCosto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='centro_costo_id'
    )
    auxiliar = models.ForeignKey(
        Auxiliar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='auxiliar_id'
    )
    detalle_gasto = models.TextField(blank=True)
    debe = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    haber = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)

# ======================================
#           CLASIFICACIONES
# ======================================
class ClasificacionSet(models.Model):
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        unique_together = ('cliente', 'nombre')

    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"

class ClasificacionOption(models.Model):
    id = models.BigAutoField(primary_key=True)
    set_clas = models.ForeignKey(ClasificacionSet, on_delete=models.CASCADE, related_name='opciones')
    valor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

   
    def __str__(self):
        return f"{self.valor} - {self.descripcion}"
    

class AccountClassification(models.Model):
    id = models.BigAutoField(primary_key=True)
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE, related_name='clasificaciones')
    set_clas = models.ForeignKey(ClasificacionSet, on_delete=models.CASCADE)
    opcion = models.ForeignKey(ClasificacionOption, on_delete=models.CASCADE)
    asignado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cuenta', 'set_clas')

    def __str__(self):
        return f"{self.cuenta.codigo} - {self.set_clas.nombre} - {self.opcion.valor}"

# ======================================
#           Incidencias
# ======================================
class Incidencia(models.Model):
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50, choices=[("formato", "Formato"), ("negocio", "Negocio")])
    descripcion = models.TextField()
    respuesta = models.TextField(blank=True)
    resuelta = models.BooleanField(default=False)
    creada_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='incidencias_creadas')
    respondida_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='incidencias_resueltas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

class AnalisisCuentaCierre(models.Model):
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE, related_name='analisis_cuentas')
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    analista = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    texto_analisis = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cierre', 'cuenta')
