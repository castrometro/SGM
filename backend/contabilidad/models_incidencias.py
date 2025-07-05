# contabilidad/models_incidencias.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class Incidencia(models.Model):
    CUENTA_NO_CLASIFICADA = "CUENTA_NO_CLAS"
    CUENTA_SIN_INGLES    = "CUENTA_INGLES"
    DOC_NO_RECONOCIDO    = "DOC_NO_REC"
    DOC_NULL             = "DOC_NULL"
    BALANCE_DESCUADRADO  = "BALANCE_DESC"

    TIPO_CHOICES = [
        (CUENTA_NO_CLASIFICADA, "Cuenta no clasificada"),
        (CUENTA_SIN_INGLES,      "Cuenta sin mapeo inglés"),
        (DOC_NO_RECONOCIDO,      "Tipo de documento no reconocido"),
        (DOC_NULL,               "Tipo de documento vacío"),
        (BALANCE_DESCUADRADO,    "Balance ESF/ERI descuadrado"),
    ]

    cierre                 = models.ForeignKey("CierreContabilidad", on_delete=models.CASCADE)
    tipo                   = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cuenta_codigo          = models.CharField("Código Cuenta", max_length=50, null=True, blank=True)
    tipo_doc_codigo        = models.CharField("Código Doc.",    max_length=20, null=True, blank=True)
    # Campos específicos para incidencias de clasificación
    set_clasificacion_id   = models.IntegerField("ID Set Clasificación", null=True, blank=True)
    set_clasificacion_nombre = models.CharField("Nombre Set Clasificación", max_length=100, null=True, blank=True)
    descripcion            = models.TextField(blank=True)
    fecha_creacion         = models.DateTimeField(auto_now_add=True)
    creada_por             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["tipo", "cuenta_codigo", "tipo_doc_codigo", "fecha_creacion"]

    def __str__(self):
        return f"[{self.get_tipo_display()}] Cuenta:{self.cuenta_codigo or '-'} Doc:{self.tipo_doc_codigo or '-'}"


class IncidenciaResumen(models.Model):
    ACTIVA   = "activa"
    RESUELTA = "resuelta"
    OBSOLETA = "obsoleta"
    ESTADO_CHOICES = [
        (ACTIVA,   "Activa"),
        (RESUELTA, "Resuelta"),
        (OBSOLETA, "Obsoleta"),
    ]

    BAJA    = "baja"
    MEDIA   = "media"
    ALTA    = "alta"
    CRITICA = "critica"
    SEVERIDAD_CHOICES = [
        (BAJA,    "Baja"),
        (MEDIA,   "Media"),
        (ALTA,    "Alta"),
        (CRITICA, "Crítica"),
    ]

    # Para enlazarlo al mismo upload_log / cierre
    upload_log        = models.ForeignKey("UploadLog", on_delete=models.CASCADE)
    cierre            = models.ForeignKey("CierreContabilidad", on_delete=models.CASCADE)

    tipo_incidencia   = models.CharField(max_length=32, choices=Incidencia.TIPO_CHOICES)
    codigo_problema = models.CharField(max_length=50, null=True, blank=True)
    cantidad_afectada = models.PositiveIntegerField()

    severidad         = models.CharField(max_length=8, choices=SEVERIDAD_CHOICES)
    estado            = models.CharField(max_length=8, choices=ESTADO_CHOICES, default=ACTIVA)

    # Mensajes para el usuario
    mensaje_usuario   = models.TextField(blank=True, help_text="Mensaje descriptivo para el usuario")
    accion_sugerida   = models.TextField(blank=True, help_text="Acción sugerida para resolver la incidencia")

    # aquí guardas la lista de claves (cuentas, docs, etc.) afectadas
    elementos_afectados = models.JSONField(default=list)

    # JSON extra o muestreo
    detalle_muestra   = models.JSONField(default=dict)
    # agrupaciones de conteos si las necesitas
    estadisticas      = models.JSONField(default=dict)

    fecha_deteccion   = models.DateTimeField(default=timezone.now)
    fecha_resolucion  = models.DateTimeField(null=True, blank=True)
    resuelto_por      = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         blank=True,
                                         related_name="+")
    creada_por        = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         blank=True,
                                         related_name="+")
    fecha_creacion    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_deteccion"]
        verbose_name = "Resumen de Incidencia"

    def __str__(self):
        return f"{self.get_tipo_incidencia_display()} ({self.cantidad_afectada})"