from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
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
    idioma = models.CharField(
        max_length=2,
        choices=[("es", "Español"), ("en", "English")],
        default="es",
    )

    class Meta:
        unique_together = ('cliente', 'nombre')

    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"

class ClasificacionOption(models.Model):
    id = models.BigAutoField(primary_key=True)
    set_clas = models.ForeignKey(
        ClasificacionSet,
        on_delete=models.CASCADE,
        related_name='opciones'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='sub_opciones'
    )
    valor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    @property
    def nivel(self):
        n = 1
        p = self.parent
        while p:
            n += 1
            p = p.parent
        return n

   
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

class BulkClasificacionUpload(models.Model):
    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
    ]
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='clasificaciones/%Y/%m/%d/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")
    errores = models.TextField(blank=True)
    resumen = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Bulk Clasificación {self.cliente.nombre} - {self.id}"

class NombresEnInglesUpload(models.Model):
    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
    ]
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE, null=True, blank=True)
    archivo = models.FileField(upload_to='nombres_ingles/%Y/%m/%d/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")
    errores = models.TextField(blank=True)
    resumen = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Nombres en Inglés {self.cliente.nombre} - {self.id}"

    class Meta:
        verbose_name = "Upload de Nombres en Inglés"
        verbose_name_plural = "Uploads de Nombres en Inglés"
        ordering = ['-fecha_subida']

# ======================================
#           TRAZABILIDAD POR TARJETA
# ======================================

class TarjetaActivityLog(models.Model):
    # Asociación al cierre
    cierre = models.ForeignKey(CierreContabilidad, on_delete=models.CASCADE, related_name='activity_logs')
    
    # Identificación de la tarjeta
    TARJETA_CHOICES = [
        ('tipo_documento', 'Tarjeta 1: Tipo de Documento'),
        ('libro_mayor', 'Tarjeta 2: Libro Mayor'),
        ('clasificacion', 'Tarjeta 3: Clasificaciones'),
        ('incidencias', 'Tarjeta 4: Incidencias'),
        ('revision', 'Tarjeta 5: Revisión'),
    ]
    tarjeta = models.CharField(max_length=20, choices=TARJETA_CHOICES)
    
    # Acción realizada
    ACCION_CHOICES = [
        ('upload_excel', 'Subida de Excel'),
        ('manual_create', 'Creación Manual'),
        ('manual_edit', 'Edición Manual'), 
        ('manual_delete', 'Eliminación Manual'),
        ('bulk_delete', 'Eliminación Masiva'),
        ('view_data', 'Visualización de Datos'),
        ('validation_error', 'Error de Validación'),
        ('process_start', 'Inicio de Procesamiento'),
        ('process_complete', 'Procesamiento Completado'),
    ]
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    
    # Metadatos
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    descripcion = models.TextField()  # Descripción legible 
    detalles = models.JSONField(null=True, blank=True)  # Datos específicos
    resultado = models.CharField(max_length=10, choices=[
        ('exito', 'Exitoso'),
        ('error', 'Error'),
        ('warning', 'Advertencia')
    ], default='exito')
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Log de Actividad de Tarjeta"
        verbose_name_plural = "Logs de Actividad de Tarjetas"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['cierre', 'tarjeta']),
            models.Index(fields=['usuario', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_tarjeta_display()} - {self.get_accion_display()} - {self.usuario}"

# ======================================
#           LOGGING
# ======================================

class ClasificacionCuentaArchivo(models.Model):
    """
    Modelo para guardar las clasificaciones tal como vienen del archivo Excel,
    sin hacer mapeo inmediato a cuentas existentes (similar a TipoDocumento)
    """
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    upload = models.ForeignKey(BulkClasificacionUpload, on_delete=models.CASCADE, related_name='clasificaciones_archivo')
    
    # Datos tal como vienen del archivo
    numero_cuenta = models.CharField(max_length=50)  # Código de cuenta tal como está en el archivo
    
    # Clasificaciones por sets (dinámico según los sets del cliente)
    clasificaciones = models.JSONField()  # {"set_nombre_1": "opcion_valor_1", "set_nombre_2": "opcion_valor_2"}
    
    # Metadatos
    fila_excel = models.IntegerField(null=True, blank=True)  # Para tracking de errores
    procesado = models.BooleanField(default=False)  # Si ya se mapeó a cuentas reales
    errores_mapeo = models.TextField(blank=True)  # Errores al hacer el mapeo real
    
    # Referencia a la cuenta real (cuando se procese)
    cuenta_mapeada = models.ForeignKey(
        'CuentaContable', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='clasificaciones_archivo'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_procesado = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('upload', 'numero_cuenta')
        indexes = [
            models.Index(fields=['cliente', 'procesado']),
            models.Index(fields=['upload', 'procesado']),
        ]
    
    def __str__(self):
        return f"{self.numero_cuenta} - {self.cliente.nombre}"


