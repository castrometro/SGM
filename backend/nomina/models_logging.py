# nomina/models_logging.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from api.models import Cliente
from datetime import datetime
import hashlib
import re


class UploadLogNomina(models.Model):
    """
    Modelo unificado para tracking de uploads de todas las tarjetas de nómina
    """

    TIPO_CHOICES = [
        ("libro_remuneraciones", "Libro de Remuneraciones"),
        ("movimientos_mes", "Movimientos del Mes"),
        ("novedades", "Novedades"),
        ("movimientos_ingresos", "Movimientos - Ingresos"),
        ("movimientos_finiquitos", "Movimientos - Finiquitos"),
        ("movimientos_incidencias", "Movimientos - Incidencias"),
        ("archivos_analista", "Archivos del Analista"),
    ]

    ESTADO_CHOICES = [
        ("subido", "Archivo subido"),
        ("procesando", "Procesando"),
        ("analizando_hdrs", "Analizando Headers"),
        ("hdrs_analizados", "Headers Analizados"),
        ("clasif_en_proceso", "Clasificación en Proceso"),
        ("clasif_pendiente", "Clasificación Pendiente"),
        ("clasificado", "Clasificado"),
        ("completado", "Procesado correctamente"),
        ("procesado", "Procesado"),
        ("error", "Con errores"),
        ("con_errores_parciales", "Con Errores Parciales"),
        ("datos_eliminados", "Datos procesados eliminados"),
    ]

    # Identificación
    tipo_upload = models.CharField(max_length=30, choices=TIPO_CHOICES)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cierre = models.ForeignKey(
        "CierreNomina", on_delete=models.CASCADE, null=True, blank=True
    )

    # Usuario y tracking
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
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
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default="subido")
    errores = models.TextField(blank=True)
    resumen = models.JSONField(null=True, blank=True)

    # Metadatos adicionales
    tiempo_procesamiento = models.DurationField(null=True, blank=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)
    
    # Campos específicos para nómina
    registros_procesados = models.PositiveIntegerField(default=0)
    registros_exitosos = models.PositiveIntegerField(default=0)
    registros_fallidos = models.PositiveIntegerField(default=0)
    headers_detectados = models.JSONField(default=list, blank=True)
    
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
        verbose_name = "Log de Upload Nómina"
        verbose_name_plural = "Logs de Uploads Nómina"
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
    def validar_nombre_archivo_nomina(nombre_archivo_original, tipo_upload, cliente_rut):
        """
        Valida que el nombre del archivo corresponda al cliente y tipo de upload para nómina

        Formatos:
        - Libro Remuneraciones: {rut_limpio}_LibroRemuneraciones_MMAAAA.xlsx
        - Movimientos Mes: {rut_limpio}_MovimientosMes_MMAAAA.xlsx
        - Novedades: {rut_limpio}_Novedades_MMAAAA.xlsx
        - Archivos Analista: {rut_limpio}_[Ingresos|Finiquitos|Incidencias]_MMAAAA.xlsx
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

        # Tipos que requieren período MMAAAA
        tipos_con_periodo = {
            "libro_remuneraciones": ["LibroRemuneraciones", "Remuneraciones"],
            "movimientos_mes": ["MovimientosMes", "Movimientos"],
            "novedades": ["Novedades"],
            "movimientos_ingresos": ["Ingresos"],
            "movimientos_finiquitos": ["Finiquitos"],
            "movimientos_incidencias": ["Incidencias"],
        }

        if tipo_upload in tipos_con_periodo:
            tipos_permitidos = tipos_con_periodo[tipo_upload]
            
            for tipo in tipos_permitidos:
                patron_periodo = rf"^{rut_limpio}_{tipo}_(\d{{6}})$"
                match = re.match(patron_periodo, nombre_sin_ext)

                if match:
                    periodo = match.group(1)
                    mes = int(periodo[:2])
                    año = int(periodo[2:])

                    # Validar mes válido (01-12)
                    if 1 <= mes <= 12 and año >= 2020:
                        return True, f"Nombre de archivo válido (período: {mes:02d}/{año})"
                    else:
                        return False, {
                            "error": "Período inválido en nombre de archivo",
                            "periodo_recibido": periodo,
                            "formato_periodo": "MMAAAA (ej: 062025 para junio 2025)",
                            "ejemplo": f"{rut_limpio}_{tipo}_062025.xlsx",
                        }

            # Si no coincide con ningún patrón
            tipo_sugerido = tipos_permitidos[0]
            return False, {
                "error": f"{tipo_sugerido} requiere período en el nombre",
                "formato_requerido": f"{rut_limpio}_{tipo_sugerido}_MMAAAA.xlsx",
                "ejemplo": f"{rut_limpio}_{tipo_sugerido}_062025.xlsx",
                "nota": "MMAAAA = mes y año (ej: 062025 para junio 2025)",
            }

        # Tipos sin período (genérico para futuras extensiones)
        return True, "Nombre de archivo válido"

    @classmethod
    def validar_archivo_cliente_estatico_nomina(cls, nombre_archivo, tipo_upload, cliente):
        """
        Validación estática que se puede usar antes de crear el UploadLogNomina
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

        # Mapeo de tipos de upload a nombres de archivo posibles
        tipos_validos = {
            "libro_remuneraciones": ["LibroRemuneraciones", "Remuneraciones"],
            "movimientos_mes": ["MovimientosMes", "Movimientos"],
            "novedades": ["Novedades"],
            "movimientos_ingresos": ["Ingresos"],
            "movimientos_finiquitos": ["Finiquitos"],
            "movimientos_incidencias": ["Incidencias"],
            "archivos_analista": ["Analista", "ArchivoAnalista"],
        }

        # Verificar formato
        tipos_permitidos = tipos_validos.get(tipo_upload, [tipo_upload.title()])

        for tipo in tipos_permitidos:
            # Verificar con período
            patron_con_periodo = rf"^{rut_limpio}_{tipo}_(\d{{6}})$"
            match = re.match(patron_con_periodo, nombre_sin_ext)
            
            if match:
                periodo = match.group(1)
                mes = int(periodo[:2])
                año = int(periodo[2:])

                if 1 <= mes <= 12 and año >= 2020:
                    return True, f"Nombre válido (período: {mes:02d}/{año})"
                else:
                    return False, {
                        "error": "Período inválido en archivo de nómina",
                        "periodo_recibido": periodo,
                        "mes_detectado": mes,
                        "año_detectado": año,
                        "formato_correcto": "MMAAAA (01-12 para mes, año >= 2020)",
                        "ejemplo": f"{rut_limpio}_{tipo}_062025.xlsx",
                    }

        # Si no es válido, devolver error detallado
        tipo_sugerido = tipos_permitidos[0]

        return False, {
            "error": "Nombre de archivo no corresponde al formato requerido para nómina",
            "archivo_recibido": nombre_archivo,
            "formato_esperado": f"{rut_limpio}_{tipo_sugerido}_MMAAAA.xlsx",
            "ejemplo": f"{rut_limpio}_{tipo_sugerido}_062025.xlsx",
            "tipos_validos": [f"{rut_limpio}_{t}_MMAAAA.xlsx" for t in tipos_permitidos],
            "nota": "MMAAAA = mes y año (ej: 062025 para junio 2025)",
        }

    def calcular_hash_archivo(self, archivo_contenido):
        """Calcula el hash SHA-256 del archivo"""
        return hashlib.sha256(archivo_contenido).hexdigest()

    def actualizar_resumen(self, datos_nuevos):
        """Actualiza el resumen con nuevos datos"""
        if not self.resumen:
            self.resumen = {}
        
        self.resumen.update(datos_nuevos)
        self.save(update_fields=['resumen'])

    def marcar_como_error(self, mensaje_error):
        """Marca el upload como error"""
        self.estado = "error"
        self.errores = mensaje_error
        self.save(update_fields=['estado', 'errores'])

    def marcar_como_completado(self, resumen_final=None):
        """Marca el upload como completado"""
        self.estado = "completado"
        if resumen_final:
            self.resumen = resumen_final
        self.save(update_fields=['estado', 'resumen'])


class TarjetaActivityLogNomina(models.Model):
    """
    Registro de actividades realizadas en las tarjetas del cierre de nómina
    """
    
    # Asociación al cierre
    cierre = models.ForeignKey(
        "CierreNomina", on_delete=models.CASCADE, related_name="activity_logs_nomina"
    )

    # Identificación de la tarjeta
    TARJETA_CHOICES = [
        ("libro_remuneraciones", "Tarjeta: Libro de Remuneraciones"),
        ("movimientos_mes", "Tarjeta: Movimientos del Mes"),
        ("novedades", "Tarjeta: Novedades"),
        ("archivos_analista", "Tarjeta: Archivos del Analista"),
        ("incidencias", "Tarjeta: Incidencias"),
        ("revision", "Tarjeta: Revisión"),
    ]
    tarjeta = models.CharField(max_length=25, choices=TARJETA_CHOICES)

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
        ("header_analysis", "Análisis de Headers"),
        ("classification_start", "Inicio de Clasificación"),
        ("classification_complete", "Clasificación Completada"),
        ("reprocesar", "Reprocesamiento"),
        ("delete_all", "Eliminación Total"),
        ("delete_archivo", "Eliminación de Archivo"),
        # Nuevas acciones para logging completo
        ("modal_open", "Apertura de Modal"),
        ("modal_close", "Cierre de Modal"),
        ("view_classification", "Ver Clasificación"),
        ("save_classification", "Guardar Clasificación"),
        ("download_template", "Descarga de Plantilla"),
        ("file_select", "Selección de Archivo"),
        ("file_validate", "Validación de Archivo"),
        ("state_change", "Cambio de Estado"),
        ("polling_start", "Inicio de Polling"),
        ("polling_stop", "Detención de Polling"),
        ("concept_map", "Mapeo de Concepto"),
        ("concept_unmap", "Desmapeo de Concepto"),
        ("auto_classify", "Clasificación Automática"),
        ("manual_classify", "Clasificación Manual"),
        ("headers_detected", "Headers Detectados"),
        ("progress_update", "Actualización de Progreso"),
        ("error_recovery", "Recuperación de Error"),
        ("session_start", "Inicio de Sesión de Trabajo"),
        ("session_end", "Fin de Sesión de Trabajo"),
    ]
    accion = models.CharField(max_length=25, choices=ACCION_CHOICES)

    # Metadatos
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
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

    # Referencias a uploads
    upload_log = models.ForeignKey(
        UploadLogNomina, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Referencia al log del upload relacionado"
    )

    class Meta:
        verbose_name = "Log de Actividad de Tarjeta Nómina"
        verbose_name_plural = "Logs de Actividad de Tarjetas Nómina"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["cierre", "tarjeta"]),
            models.Index(fields=["usuario", "timestamp"]),
            models.Index(fields=["tarjeta", "accion"]),
        ]

    def __str__(self):
        return f"{self.get_tarjeta_display()} - {self.get_accion_display()} - {self.usuario}"


# Función de utilidad para registrar actividades
def registrar_actividad_tarjeta_nomina(
    cierre_id,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado="exito",
    ip_address=None,
    upload_log=None
):
    """
    Función helper para registrar actividades en tarjetas de nómina
    """
    return TarjetaActivityLogNomina.objects.create(
        cierre_id=cierre_id,
        tarjeta=tarjeta,
        accion=accion,
        descripcion=descripcion,
        usuario=usuario,
        detalles=detalles or {},
        resultado=resultado,
        ip_address=ip_address,
        upload_log=upload_log,
    )
