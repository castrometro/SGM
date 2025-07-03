from api.models import Area, Cliente, Usuario
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
# ======================================
#           CENTRO DE COSTO
# ======================================


class CentroCosto(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="id_centro_costo")
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, db_column="cliente_id"
    )
    nombre = models.CharField(max_length=255, db_column="nombre")

    class Meta:
        db_table = "contabilidad_centrocosto"
        unique_together = ("cliente", "nombre")
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre}"


# ======================================
#              AUXILIAR
# ======================================


class Auxiliar(models.Model):
    rut_auxiliar = models.CharField(
        max_length=15, primary_key=True, db_column="rut_auxiliar"
    )
    nombre = models.CharField(max_length=255, blank=True, db_column="nombre_auxiliar")
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column="fecha_creacion")

    class Meta:
        db_table = "contabilidad_auxiliar"
        ordering = ["rut_auxiliar"]

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
        unique_together = ("cliente", "codigo")

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class CuentaContable(models.Model):
    id = models.BigAutoField(db_column="id_cuenta", primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255, blank=True)
    nombre_en = models.CharField(
        max_length=255, blank=True, null=True
    )  # <--- ESTE CAMPO
    # ...

    class Meta:
        unique_together = ("cliente", "codigo")

    def __str__(self):
        return f"{self.codigo} - {self.nombre} - {self.nombre_en}"


class TipoDocumentoArchivo(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="tipo_documento/")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    upload_log = models.ForeignKey(
        "UploadLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Referencia al log del upload que generó este archivo",
    )

    def __str__(self):
        return f"Archivo Tipo Documento - {self.cliente.nombre}"


class ClasificacionArchivo(models.Model):
    """Almacena el Excel procesado de clasificaciones"""

    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="clasificacion/")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    upload_log = models.ForeignKey(
        "UploadLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Referencia al log del upload que generó este archivo",
    )

    def __str__(self):
        return f"Archivo Clasificación - {self.cliente.nombre}"


# ======================================
#           NOMBRES EN INGLÉS
# ======================================


class NombreIngles(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cierre = models.ForeignKey(
        "CierreContabilidad", on_delete=models.CASCADE, null=True, blank=True
    )
    cuenta_codigo = models.CharField(max_length=20)
    nombre_ingles = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("cliente", "cuenta_codigo")]
        db_table = "contabilidad_nombreingles"
        ordering = ["cuenta_codigo"]

    def __str__(self):
        return f"{self.cuenta_codigo} - {self.nombre_ingles}"


class NombreInglesArchivo(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to="nombres_ingles/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archivo Nombres en Inglés - {self.cliente.nombre}"


# ======================================
#           CIERRES CONTABILIDAD
# ======================================


class CierreContabilidad(models.Model):
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)
    periodo = models.CharField(max_length=7)  # Ej: "2025-04"
    fecha_inicio_libro = models.DateField(
        null=True, blank=True
    )  # <- calculada del parser (primer movimiento)
    fecha_fin_libro = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ("pendiente", "Pendiente"),
            ("procesando", "Procesando"),
            ("clasificacion", "Esperando Clasificación"),
            ("incidencias", "Incidencias Abiertas"),
            ("sin_incidencias", "Sin Incidencias"),
            ("generando_reportes", "Generando Reportes"),
            ("en_revision", "En Revisión"),
            ("rechazado", "Rechazado"),
            ("aprobado", "Aprobado"),
            ("finalizado", "Finalizado"),
            ("completo", "Completo"),
        ],
        default="pendiente"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    fecha_sin_incidencias = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha cuando el cierre quedó sin incidencias pendientes"
    )
    fecha_finalizacion = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha cuando se finalizó el cierre y se generaron reportes"
    )
    reportes_generados = models.BooleanField(
        default=False,
        help_text="Indica si se han generado los reportes finales"
    )
    cuentas_nuevas = models.IntegerField(default=0)
    resumen_parsing = models.JSONField(null=True, blank=True)
    parsing_completado = models.BooleanField(default=False)

    class Meta:
        unique_together = ("cliente", "periodo")

    def __str__(self):
        return f"Cierre {self.periodo} - {self.cliente.nombre}"
    
    def puede_finalizar(self):
        """
        Verifica si el cierre puede ser finalizado
        Debe estar en estado 'sin_incidencias' y sin incidencias pendientes
        """
        from .models_incidencias import Incidencia
        
        # Debe estar en sin_incidencias
        if self.estado != 'sin_incidencias':
            return False, f"El cierre debe estar en estado 'sin_incidencias', actualmente está en '{self.estado}'"
        
        # Verificar que no hay incidencias pendientes
        incidencias_pendientes = Incidencia.objects.filter(
            cierre=self,
            estado='pendiente'
        ).count()
        
        if incidencias_pendientes > 0:
            return False, f"Hay {incidencias_pendientes} incidencias pendientes por resolver"
        
        # Ya está finalizado
        if self.estado == 'finalizado':
            return False, "El cierre ya ha sido finalizado"
            
        return True, "El cierre puede ser finalizado"
    
    def iniciar_finalizacion(self, usuario=None):
        """
        Inicia el proceso de finalización del cierre
        Cambia el estado a 'generando_reportes' y dispara la tarea de Celery
        """
        from django.utils import timezone
        
        puede, mensaje = self.puede_finalizar()
        if not puede:
            raise ValueError(mensaje)
        
        # Cambiar estado
        self.estado = 'generando_reportes'
        self.save(update_fields=['estado'])
        
        # Disparar tarea de Celery
        from .tasks_finalizacion import finalizar_cierre_y_generar_reportes
        task = finalizar_cierre_y_generar_reportes.delay(
            cierre_id=self.id,
            usuario_id=usuario.id if usuario else None
        )
        
        return task.id
    
    def marcar_como_finalizado(self):
        """
        Marca el cierre como finalizado una vez que se generaron los reportes
        """
        from django.utils import timezone
        
        self.estado = 'finalizado'
        self.fecha_finalizacion = timezone.now()
        self.reportes_generados = True
        self.save(update_fields=['estado', 'fecha_finalizacion', 'reportes_generados'])

    def actualizar_estado_automatico(self):
        """
        Actualiza el estado del cierre basado en las incidencias pendientes
        y otros factores automáticamente.
        """
        from .models_incidencias import Incidencia
        from django.utils import timezone
        
        # Si ya está finalizado, no cambiar
        if self.estado == 'finalizado':
            return self.estado
            
        # Si está generando reportes, no cambiar
        if self.estado == 'generando_reportes':
            return self.estado
        
        # Contar incidencias pendientes
        incidencias_pendientes = Incidencia.objects.filter(
            cierre=self,
            estado='pendiente'
        ).count()
        
        # Determinar el estado correcto basado en incidencias
        if incidencias_pendientes == 0:
            # Sin incidencias pendientes
            if self.estado != 'sin_incidencias':
                self.estado = 'sin_incidencias'
                self.fecha_sin_incidencias = timezone.now()
                self.save(update_fields=['estado', 'fecha_sin_incidencias'])
        else:
            # Hay incidencias pendientes
            if self.estado != 'incidencias':
                self.estado = 'incidencias'
                self.save(update_fields=['estado'])
        
        return self.estado


def libro_upload_path(instance, filename):
    cliente_id = instance.cliente.id  # ✅ Ahora directo al cliente
    return f"libros/{cliente_id}/{filename}"


class LibroMayorArchivo(models.Model):
    """Almacena el archivo Excel de libro mayor (uno por cierre para mantener historicidad)"""
    
    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
    ]
    
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)  # ✅ Cambiado a ForeignKey
    cierre = models.OneToOneField(  # ✅ Un archivo por cierre
        CierreContabilidad, 
        on_delete=models.CASCADE,
        related_name="libro_mayor_archivo",
        help_text="Cierre contable al que pertenece este libro mayor"
    )
    archivo = models.FileField(upload_to=libro_upload_path)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    # ✅ Solo enlace a UploadLog (para tracking)
    upload_log = models.ForeignKey(
        "UploadLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Referencia al log del upload que generó este archivo",
    )
    
    # ✅ Período extraído del nombre del archivo
    periodo = models.CharField(
        max_length=6, 
        help_text="Período MMAAAA extraído del nombre del archivo (ej: 042025)"
    )
    
    # Estados
    procesado = models.BooleanField(default=False)
    errores = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")

    def __str__(self):
        cierre_info = self.cierre.periodo if self.cierre else "Sin cierre"
        return f"Libro Mayor {self.periodo} - {self.cliente.nombre} - {cierre_info}"

    class Meta:
        verbose_name = "Archivo de Libro Mayor"
        verbose_name_plural = "Archivos de Libro Mayor"
        # ✅ OneToOneField con cierre ya garantiza unicidad automáticamente


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
    tipo_documento = models.ForeignKey(
        TipoDocumento, on_delete=models.SET_NULL, null=True
    )
    tipo_doc_codigo = models.CharField(max_length=10, blank=True, default="")
    numero_documento = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(max_length=50, blank=True)
    numero_comprobante = models.CharField(max_length=50, blank=True)
    numero_interno = models.CharField(max_length=50, blank=True)
    centro_costo = models.ForeignKey(
        CentroCosto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="centro_costo_id",
    )
    auxiliar = models.ForeignKey(
        Auxiliar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="auxiliar_id",
    )
    detalle_gasto = models.TextField(blank=True)
    debe = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    haber = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    flag_incompleto = models.BooleanField(default=False)


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
        unique_together = ("cliente", "nombre")

    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"


class ClasificacionOption(models.Model):
    id = models.BigAutoField(primary_key=True)
    set_clas = models.ForeignKey(
        ClasificacionSet, on_delete=models.CASCADE, related_name="opciones"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sub_opciones",
    )
    valor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    # Campos para soporte bilingüe (solo para sets por defecto del sistema)
    valor_en = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Valor en inglés para sets por defecto del sistema"
    )
    descripcion_en = models.TextField(
        blank=True,
        help_text="Descripción en inglés para sets por defecto del sistema"
    )

    @property
    def nivel(self):
        n = 1
        p = self.parent
        while p:
            n += 1
            p = p.parent
        return n

    def get_valor(self, idioma='es'):
        """
        Obtiene el valor en el idioma especificado.
        
        Args:
            idioma (str): 'es' para español, 'en' para inglés
            
        Returns:
            str: Valor en el idioma solicitado
        """
        if idioma == 'en' and self.valor_en:
            return self.valor_en
        return self.valor

    def get_descripcion(self, idioma='es'):
        """
        Obtiene la descripción en el idioma especificado.
        
        Args:
            idioma (str): 'es' para español, 'en' para inglés
            
        Returns:
            str: Descripción en el idioma solicitado
        """
        if idioma == 'en' and self.descripcion_en:
            return self.descripcion_en
        return self.descripcion

    def tiene_traduccion_completa(self):
        """
        Verifica si la opción tiene traducción completa al inglés.
        
        Returns:
            bool: True si tiene tanto valor_en como descripcion_en
        """
        return bool(self.valor_en and self.descripcion_en)

    def __str__(self):
        return f"{self.valor} - {self.descripcion}"


class AccountClassification(models.Model):
    id = models.BigAutoField(primary_key=True)
    cuenta = models.ForeignKey(
        CuentaContable, on_delete=models.CASCADE, related_name="clasificaciones"
    )
    set_clas = models.ForeignKey(ClasificacionSet, on_delete=models.CASCADE)
    opcion = models.ForeignKey(ClasificacionOption, on_delete=models.CASCADE)
    asignado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cuenta", "set_clas")

    def __str__(self):
        return f"{self.cuenta.codigo} - {self.set_clas.nombre} - {self.opcion.valor}"

class AnalisisCuentaCierre(models.Model):
    cierre = models.ForeignKey(
        CierreContabilidad, on_delete=models.CASCADE, related_name="analisis_cuentas"
    )
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    analista = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    texto_analisis = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cierre", "cuenta")


class NombresEnInglesUpload(models.Model):
    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
    ]
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cierre = models.ForeignKey(
        CierreContabilidad, on_delete=models.CASCADE, null=True, blank=True
    )
    archivo = models.FileField(upload_to="nombres_ingles/%Y/%m/%d/")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")
    errores = models.TextField(blank=True)
    resumen = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Nombres en Inglés {self.cliente.nombre} - {self.id}"

    class Meta:
        verbose_name = "Upload de Nombres en Inglés"
        verbose_name_plural = "Uploads de Nombres en Inglés"
        ordering = ["-fecha_subida"]


# ======================================
#           TRAZABILIDAD POR TARJETA
# ======================================


class TarjetaActivityLog(models.Model):
    # Asociación al cierre
    cierre = models.ForeignKey(
        CierreContabilidad, on_delete=models.CASCADE, related_name="activity_logs"
    )

    # Identificación de la tarjeta
    TARJETA_CHOICES = [
        ("tipo_documento", "Tarjeta: Tipo de Documento"),
        ("libro_mayor", "Tarjeta: Libro Mayor"),
        ("clasificacion", "Tarjeta: Clasificaciones"),
        ("nombres_ingles", "Tarjeta: Nombres en Inglés"),
        ("incidencias", "Tarjeta: Incidencias"),
        ("revision", "Tarjeta: Revisión"),
    ]
    tarjeta = models.CharField(max_length=20, choices=TARJETA_CHOICES)

    # Acción realizada
    ACCION_CHOICES = [
        ("upload_excel", "Subida de Excel"),
        ("manual_create", "Creación Manual"),
        ("manual_edit", "Edición Manual"),
        ("manual_delete", "Eliminación Manual"),
        ("bulk_delete", "Eliminación Masiva"),
        ("view_data", "Visualización de Datos"),
        ("view_list", "Visualización de Lista"),
        ("validation_error", "Error de Validación"),
        ("process_start", "Inicio de Procesamiento"),
        ("process_complete", "Procesamiento Completado"),
        ("set_create", "Creación de Set"),
        ("set_edit", "Edición de Set"),
        ("set_delete", "Eliminación de Set"),
        ("option_create", "Creación de Opción"),
        ("option_edit", "Edición de Opción"),
        ("option_delete", "Eliminación de Opción"),
        ("individual_create", "Creación Individual"),
        ("individual_edit", "Edición Individual"),
        ("individual_delete", "Eliminación Individual"),
        ("delete_all", "Eliminación Total"),
    ]
    accion = models.CharField(max_length=25, choices=ACCION_CHOICES)

    # Metadatos
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    descripcion = models.TextField()  # Descripción legible
    detalles = models.JSONField(null=True, blank=True)  # Datos específicos
    resultado = models.CharField(
        max_length=10,
        choices=[("exito", "Exitoso"), ("error", "Error"), ("warning", "Advertencia")],
        default="exito",
    )

    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Log de Actividad de Tarjeta"
        verbose_name_plural = "Logs de Actividad de Tarjetas"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["cierre", "tarjeta"]),
            models.Index(fields=["usuario", "timestamp"]),
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
    upload_log = models.ForeignKey(
        "UploadLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Referencia al log del upload que generó este archivo",
        related_name="clasificaciones_archivo",
    )

    # Datos tal como vienen del archivo
    numero_cuenta = models.CharField(
        max_length=50
    )  # Código de cuenta tal como está en el archivo

    # Clasificaciones por sets (dinámico según los sets del cliente)
    clasificaciones = (
        models.JSONField()
    )  # {"set_nombre_1": "opcion_valor_1", "set_nombre_2": "opcion_valor_2"}

    # Metadatos
    fila_excel = models.IntegerField(null=True, blank=True)  # Para tracking de errores
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("upload_log", "numero_cuenta")
        indexes = [
            models.Index(fields=["cliente"]),
            models.Index(fields=["upload_log"]),
        ]

    def __str__(self):
        return f"{self.numero_cuenta} - {self.cliente.nombre}"


# ======================================
#           UPLOAD LOG UNIFICADO
# ======================================


class UploadLog(models.Model):
    """
    Modelo unificado para tracking de uploads de todas las tarjetas
    """

    TIPO_CHOICES = [
        ("tipo_documento", "Tipo de Documento"),
        ("clasificacion", "Clasificación Bulk"),
        ("nombres_ingles", "Nombres en Inglés"),
        ("libro_mayor", "Libro Mayor"),
        # Fácil agregar nuevas tarjetas
    ]

    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("completado", "Procesado correctamente"),
        ("error", "Con errores"),
        ("datos_eliminados", "Datos procesados eliminados"),
    ]

    # Identificación
    tipo_upload = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cierre = models.ForeignKey(
        "CierreContabilidad", on_delete=models.CASCADE, null=True, blank=True
    )

    # Usuario y tracking
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    # Archivo y procesamiento
    nombre_archivo_original = models.CharField(max_length=255)
    ruta_archivo = models.CharField(
        max_length=500, blank=True, help_text="Ruta relativa del archivo en storage"
    )
    tamaño_archivo = models.BigIntegerField(help_text="Tamaño en bytes")
    hash_archivo = models.CharField(
        max_length=64, blank=True, help_text="SHA-256 del archivo"
    )

    # Estados y resultados
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="subido")
    errores = models.TextField(blank=True)
    resumen = models.JSONField(null=True, blank=True)

    # Metadatos adicionales
    tiempo_procesamiento = models.DurationField(null=True, blank=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)
    
    # Sistema de iteraciones para reprocesamiento
    iteracion = models.PositiveIntegerField(
        default=1,
        help_text="Número de iteración de procesamiento para este cierre (1=inicial, 2+=reproceso)"
    )
    es_iteracion_principal = models.BooleanField(
        default=True,
        help_text="Marca si es la iteración principal visible al usuario"
    )

    class Meta:
        verbose_name = "Log de Upload"
        verbose_name_plural = "Logs de Uploads"
        ordering = ["-fecha_subida"]
        indexes = [
            models.Index(fields=["cliente", "tipo_upload"]),
            models.Index(fields=["estado", "fecha_subida"]),
            models.Index(fields=["tipo_upload", "estado"]),
            models.Index(fields=["cierre", "tipo_upload", "iteracion"]),
            models.Index(fields=["cierre", "tipo_upload", "es_iteracion_principal"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_upload_display()} - {self.cliente.nombre} - {self.fecha_subida.strftime('%Y-%m-%d %H:%M')}"

    @staticmethod
    def validar_nombre_archivo(nombre_archivo_original, tipo_upload, cliente_rut):
        """
        Valida que el nombre del archivo corresponda al cliente y tipo de upload

        Formatos:
        - Tipo Documento: {rut_limpio}_TipoDocumento.xlsx
        - Clasificación: {rut_limpio}_Clasificacion.xlsx
        - Nombres Inglés: {rut_limpio}_NombresIngles.xlsx
        - Libro Mayor: {rut_limpio}_LibroMayor_MMAAAA.xlsx (ej: 12345678_LibroMayor_042025.xlsx)
        """
        import re

        # Obtener RUT sin puntos ni guión
        rut_limpio = (
            cliente_rut.replace(".", "").replace("-", "") if cliente_rut else ""
        )

        # Eliminar extensión
        nombre_sin_ext = re.sub(
            r"\.(xlsx|xls)$", "", nombre_archivo_original, flags=re.IGNORECASE
        )

        # Validación específica para libro mayor (requiere mes y año)
        if tipo_upload == "LibroMayor":
            patron_libro = rf"^{rut_limpio}_(LibroMayor|Mayor)_(\d{{6}})$"
            match = re.match(patron_libro, nombre_sin_ext)

            if match:
                periodo = match.group(2)
                mes = int(periodo[:2])
                año = int(periodo[2:])

                # Validar mes válido (01-12)
                if 1 <= mes <= 12 and año >= 2020:
                    return True, f"Nombre de archivo válido (período: {mes:02d}/{año})"
                else:
                    return False, {
                        "error": "Período inválido en nombre de archivo",
                        "periodo_recibido": periodo,
                        "formato_periodo": "MMAAAA (ej: 042025 para abril 2025)",
                        "ejemplo": f"{rut_limpio}_LibroMayor_042025.xlsx",
                    }

            return False, {
                "error": "Libro Mayor requiere período en el nombre",
                "formato_requerido": f"{rut_limpio}_LibroMayor_MMAAAA.xlsx",
                "ejemplo": f"{rut_limpio}_LibroMayor_042025.xlsx",
                "nota": "MMAAAA = mes y año (ej: 042025 para abril 2025)",
            }

        # Validación para otros tipos (sin período requerido)
        tipos_validos = {
            "TipoDocumento": ["TipoDocumento", "TiposDocumento"],
            "Clasificacion": ["Clasificacion", "Clasificaciones"],
            "NombresIngles": ["NombresIngles", "NombreIngles"],
        }

        tipos_permitidos = tipos_validos.get(tipo_upload, [tipo_upload])

        for tipo in tipos_permitidos:
            patron_esperado = f"{rut_limpio}_{tipo}"
            if nombre_sin_ext == patron_esperado:
                return True, "Nombre de archivo válido"

        # Generar sugerencia
        tipo_sugerido = tipos_permitidos[0]
        sugerencia = f"{rut_limpio}_{tipo_sugerido}.xlsx"

        return False, {
            "error": "Nombre de archivo no corresponde al formato requerido",
            "archivo_recibido": nombre_archivo_original,
            "formato_esperado": f"{rut_limpio}_{tipo_sugerido}.xlsx",
            "sugerencia": sugerencia,
            "tipos_validos": [f"{rut_limpio}_{t}.xlsx" for t in tipos_permitidos],
        }

    @classmethod
    def validar_archivo_cliente_estatico(cls, nombre_archivo, tipo_upload, cliente):
        """
        Validación estática que se puede usar antes de crear el UploadLog
        """
        import re

        # Obtener RUT sin puntos ni guión
        rut_limpio = (
            cliente.rut.replace(".", "").replace("-", "")
            if cliente.rut
            else str(cliente.id)
        )

        # Eliminar extensión
        nombre_sin_ext = re.sub(
            r"\.(xlsx|xls)$", "", nombre_archivo, flags=re.IGNORECASE
        )

        # Validación específica para libro mayor (requiere período)
        if tipo_upload == "libro_mayor":
            patron_libro = rf"^{rut_limpio}_(LibroMayor|Mayor)_(\d{{6}})$"
            match = re.match(patron_libro, nombre_sin_ext)

            if match:
                periodo = match.group(2)
                mes = int(periodo[:2])
                año = int(periodo[2:])

                # Validar mes válido (01-12) y año razonable
                if 1 <= mes <= 12 and año >= 2020:
                    return True, f"Nombre válido (período: {mes:02d}/{año})"
                else:
                    return False, {
                        "error": "Período inválido en libro mayor",
                        "periodo_recibido": periodo,
                        "mes_detectado": mes,
                        "año_detectado": año,
                        "formato_correcto": "MMAAAA (01-12 para mes, año >= 2020)",
                        "ejemplo": f"{rut_limpio}_LibroMayor_042025.xlsx",
                    }

            return False, {
                "error": "Libro Mayor requiere período MMAAAA en el nombre",
                "archivo_recibido": nombre_archivo,
                "formato_requerido": f"{rut_limpio}_LibroMayor_MMAAAA.xlsx",
                "ejemplo": f"{rut_limpio}_LibroMayor_042025.xlsx",
                "explicacion": "MMAAAA = mes (01-12) + año (ej: 042025 = abril 2025)",
            }

        # Validación para otros tipos (sin período requerido)
        tipos_validos = {
            "tipo_documento": ["TipoDocumento", "TiposDocumento"],
            "clasificacion": ["Clasificacion", "Clasificaciones"],
            "nombres_ingles": ["NombresIngles", "NombreIngles"],
        }

        # Verificar formato
        tipos_permitidos = tipos_validos.get(tipo_upload, [tipo_upload.title()])

        for tipo in tipos_permitidos:
            patron_esperado = f"{rut_limpio}_{tipo}"
            if nombre_sin_ext == patron_esperado:
                return True, "Nombre de archivo válido"

        # Si no es válido, devolver error detallado
        tipo_sugerido = tipos_permitidos[0]

        return False, {
            "error": "Nombre de archivo no corresponde al cliente o tipo",
            "archivo_recibido": nombre_archivo,
            "cliente_rut": cliente.rut,
            "rut_esperado": rut_limpio,
            "tipo_upload": tipo_upload,
            "formato_correcto": f"{rut_limpio}_{tipo_sugerido}.xlsx",
            "formatos_validos": [f"{rut_limpio}_{t}.xlsx" for t in tipos_permitidos],
            "ejemplos_generales": [
                f"{rut_limpio}_TipoDocumento.xlsx",
                f"{rut_limpio}_Clasificacion.xlsx",
                f"{rut_limpio}_NombresIngles.xlsx",
                f"{rut_limpio}_LibroMayor_042025.xlsx",
            ],
        }


# ======================================
#       EXCEPCIONES DE VALIDACIÓN
# ======================================

class ExcepcionValidacion(models.Model):
    """
    Modelo para manejar excepciones de validación por cliente.
    Permite marcar cuentas como "No aplica" para ciertos tipos de validación.
    """
    TIPOS_EXCEPCION = [
        ('tipos_doc_no_reconocidos', 'Tipo de Documento No Aplica'),
        ('movimientos_tipodoc_nulo', 'Tipo de Documento No Requerido'),
        ('cuentas_sin_nombre_ingles', 'Nombre en Inglés No Aplica'),
        ('cuentas_sin_clasificacion', 'Clasificación No Aplica'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipo_excepcion = models.CharField(max_length=50, choices=TIPOS_EXCEPCION)
    codigo_cuenta = models.CharField(max_length=20)
    nombre_cuenta = models.CharField(max_length=200, blank=True)
    motivo = models.TextField(blank=True, help_text="Motivo por el cual no aplica")
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que creó la excepción"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['cliente', 'tipo_excepcion', 'codigo_cuenta']
        indexes = [
            models.Index(fields=['cliente', 'tipo_excepcion', 'activa']),
            models.Index(fields=['codigo_cuenta']),
        ]
        verbose_name = "Excepción de Validación"
        verbose_name_plural = "Excepciones de Validación"
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.codigo_cuenta} - {self.get_tipo_excepcion_display()}"


class ExcepcionClasificacionSet(models.Model):
    """
    Modelo para manejar excepciones específicas por set de clasificación.
    Permite marcar que una cuenta NO aplica para un set específico de clasificación.
    
    Ejemplo: Una cuenta de "Caja" no aplica para el set "Tipo de Activo Fijo"
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cuenta_codigo = models.CharField(max_length=20, help_text="Código de la cuenta")
    set_clasificacion = models.ForeignKey(
        'ClasificacionSet', 
        on_delete=models.CASCADE,
        help_text="Set de clasificación al que NO aplica esta cuenta"
    )
    motivo = models.TextField(
        blank=True,
        help_text="Motivo por el cual esta cuenta no aplica a este set específico"
    )
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que creó la excepción"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(
        default=True,
        help_text="Si está activa, la cuenta no será requerida en este set"
    )
    
    class Meta:
        unique_together = ['cliente', 'cuenta_codigo', 'set_clasificacion']
        indexes = [
            models.Index(fields=['cliente', 'set_clasificacion', 'activa']),
            models.Index(fields=['cuenta_codigo', 'activa']),
        ]
        verbose_name = "Excepción de Clasificación por Set"
        verbose_name_plural = "Excepciones de Clasificación por Set"
    
    def __str__(self):
        return f"{self.cuenta_codigo} NO aplica en {self.set_clasificacion.nombre} ({self.cliente.nombre})"
    
    @property
    def cuenta_nombre(self):
        """Obtener el nombre de la cuenta si existe"""
        try:
            cuenta = CuentaContable.objects.get(
                cliente=self.cliente, 
                codigo=self.cuenta_codigo
            )
            return cuenta.nombre
        except CuentaContable.DoesNotExist:
            return f"Cuenta {self.cuenta_codigo}"
from .models_incidencias import Incidencia, IncidenciaResumen