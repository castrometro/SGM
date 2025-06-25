# Register your models here.

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json

from .models import (
    AccountClassification,
    AnalisisCuentaCierre,
    AperturaCuenta,
    Auxiliar,
    CentroCosto,
    CierreContabilidad,
    ClasificacionArchivo,
    ClasificacionCuentaArchivo,
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    Incidencia,
    LibroMayorUpload,
    LibroMayorArchivo,  # Nuevo modelo para manejar archivos de libro mayor
    MovimientoContable,
    NombreIngles,
    NombreInglesArchivo,
    NombresEnInglesUpload,
    TarjetaActivityLog,
    TipoDocumento,
    TipoDocumentoArchivo,
    UploadLog,
)

# ✨ NUEVO: Importar modelos de incidencias consolidadas
from .models_incidencias import (
    IncidenciaResumen,
    HistorialReprocesamiento,
    LogResolucionIncidencia,
)


class IncidenciaDetalleFilter(admin.SimpleListFilter):
    title = "Detalle"
    parameter_name = "detalle"

    def lookups(self, request, model_admin):
        return [
            ("sin_nombre_ingles", "Cuenta sin nombre en inglés"),
            ("sin_clasificacion", "Cuenta sin clasificación"),
            ("tipo_documento", "Tipo de documento no encontrado"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val == "sin_nombre_ingles":
            return queryset.filter(descripcion__icontains="nombre en inglés")
        if val == "sin_clasificacion":
            return queryset.filter(descripcion__icontains="sin clasificación")
        if val == "tipo_documento":
            return queryset.filter(descripcion__icontains="Tipo de documento")
        return queryset


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "codigo", "descripcion")
    search_fields = ("codigo", "descripcion")
    list_filter = ("cliente",)


@admin.register(TipoDocumentoArchivo)
class TipoDocumentoArchivoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "archivo_nombre",
        "fecha_subida",
        "tamaño_archivo",
        "upload_log_info",
    )
    list_filter = ("cliente", "fecha_subida")
    search_fields = ("archivo", "cliente__nombre")
    readonly_fields = ("fecha_subida",)

    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo, no la ruta completa"""
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo en formato legible"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"

    tamaño_archivo.short_description = "Tamaño"

    def upload_log_info(self, obj):
        """Muestra información del upload log asociado"""
        if obj.upload_log:
            return f"#{obj.upload_log.id} - {obj.upload_log.get_estado_display()}"
        return "Sin log"

    upload_log_info.short_description = "Upload Log"

    def get_queryset(self, request):
        """Optimiza queries con select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related("cliente", "upload_log")


@admin.register(ClasificacionArchivo)
class ClasificacionArchivoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "archivo_nombre", "fecha_subida", "upload_log_info")
    list_filter = ("cliente", "fecha_subida")
    search_fields = ("archivo", "cliente__nombre")
    readonly_fields = ("fecha_subida",)

    def archivo_nombre(self, obj):
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def upload_log_info(self, obj):
        if obj.upload_log:
            return f"#{obj.upload_log.id} - {obj.upload_log.get_estado_display()}"
        return "Sin log"

    upload_log_info.short_description = "Upload Log"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("cliente", "upload_log")


@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ("cliente", "codigo", "nombre", "nombre_en")
    search_fields = ("codigo", "nombre")
    list_filter = ("cliente",)


@admin.register(CierreContabilidad)
class CierreContabilidadAdmin(admin.ModelAdmin):
    list_display = ("cliente", "periodo", "estado", "usuario", "fecha_creacion")
    list_filter = ("estado", "cliente")
    search_fields = ("periodo",)


@admin.register(LibroMayorUpload)
class LibroMayorUploadAdmin(admin.ModelAdmin):
    list_display = (
        "cierre_info",
        "archivo_nombre",
        "fecha_subida",
        "estado",
        "procesado",
        "tamaño_archivo",
    )
    list_filter = ("procesado", "estado", "fecha_subida")
    search_fields = ("cierre__cliente__nombre", "cierre__periodo")
    readonly_fields = ("fecha_subida",)

    def cierre_info(self, obj):
        """Información del cierre asociado"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"

    cierre_info.short_description = "Cliente - Período"

    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"

    tamaño_archivo.short_description = "Tamaño"

@admin.register(LibroMayorArchivo)
class LibroMayorArchivoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "archivo_nombre",
        "fecha_subida",
        "periodo",
        "estado",           # ← mostrar si está subido, procesando o completado
        "upload_log_info",  # ← link al UploadLog para ver errores o tiempos
        "tamaño_archivo",
    )
    list_filter = ("cliente", "fecha_subida", "periodo")
    search_fields = ("archivo", "cliente__nombre")
    readonly_fields = ("fecha_subida",)

    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"

    tamaño_archivo.short_description = "Tamaño"

    def estado(self, obj):
        """Muestra el estado del procesamiento del archivo"""
        if not obj.upload_log:
            return "Sin procesar"
        
        # Usar el campo 'estado' del UploadLog
        if obj.upload_log.estado == 'error':
            return "Con errores"
        elif obj.upload_log.estado == 'completado':
            return "Completado"
        elif obj.upload_log.estado == 'procesando':
            return "Procesando"
        else:
            return "Subido"

    estado.short_description = "Estado"

    def upload_log_info(self, obj):
        """Muestra link al UploadLog para ver detalles"""
        if obj.upload_log:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse("admin:contabilidad_uploadlog_change", args=[obj.upload_log.pk])
            # Usar el campo 'estado' en lugar de 'completado'
            status = "✓" if obj.upload_log.estado == 'completado' else "⚠️" if obj.upload_log.estado == 'error' else "⏳"
            return format_html('<a href="{}">{} Ver log</a>', url, status)
        return "-"

    upload_log_info.short_description = "Log"
    upload_log_info.allow_tags = True


@admin.register(AperturaCuenta)
class AperturaCuentaAdmin(admin.ModelAdmin):
    list_display = ("cierre", "cuenta", "saldo_anterior")


@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    list_display = (
        "cierre",
        "periodo",        # ← añade el periodo para ver en qué cierre quedó
        "cuenta",
        "debe",
        "haber",
        "tipo_documento",
        "numero_documento",
        "tipo",
        "numero_comprobante",
        "numero_interno",
    )
    list_filter = ("fecha", "numero_interno", "tipo_documento", "cuenta")
    search_fields = ("descripcion",)

    def periodo(self, obj):
        """Muestra el periodo del cierre asociado"""
        return obj.cierre.periodo if obj.cierre else "-"

    periodo.short_description = "Periodo"


@admin.register(ClasificacionSet)
class ClasificacionSetAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nombre")


@admin.register(ClasificacionOption)
class ClasificacionOptionAdmin(admin.ModelAdmin):
    list_display = ("set_clas", "valor")


@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = ("cuenta", "set_clas", "opcion", "asignado_por", "fecha")


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("cierre", "tipo", "resuelta", "fecha_creacion")
    list_filter = ("resuelta", "tipo", IncidenciaDetalleFilter)
    search_fields = ("descripcion", "respuesta")


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nombre")
    list_filter = ("cliente",)


@admin.register(Auxiliar)
class AuxiliarAdmin(admin.ModelAdmin):
    list_display = ("rut_auxiliar", "nombre", "fecha_creacion")


@admin.register(ClasificacionCuentaArchivo)
class ClasificacionCuentaArchivoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "upload_log",
        "numero_cuenta",
        "procesado",
        "fila_excel",
        "fecha_creacion",
    )
    list_filter = ("procesado", "cliente", "upload_log__estado", "fecha_creacion")
    search_fields = ("numero_cuenta", "cliente__nombre")
    readonly_fields = ("fecha_creacion", "fecha_procesado")

    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("cliente", "upload_log", "cuenta_mapeada")
        )


@admin.register(NombresEnInglesUpload)
class NombresEnInglesUploadAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "cierre_info",
        "archivo_nombre",
        "fecha_subida",
        "estado",
        "resumen_info",
        "tamaño_archivo",
    )
    list_filter = ("estado", "cliente", "fecha_subida")
    search_fields = ("cliente__nombre", "cierre__periodo", "archivo")
    readonly_fields = ("fecha_subida", "resumen")

    def cierre_info(self, obj):
        """Información del cierre asociado"""
        if obj.cierre:
            return f"{obj.cierre.periodo}"
        return "Sin cierre específico"

    cierre_info.short_description = "Período"

    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def resumen_info(self, obj):
        """Muestra información del resumen de procesamiento"""
        if obj.resumen:
            actualizadas = obj.resumen.get("cuentas_actualizadas", 0)
            errores = obj.resumen.get("errores_count", 0)
            return f"{actualizadas} actualizadas, {errores} errores"
        return "-"

    resumen_info.short_description = "Resumen"

    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"

    tamaño_archivo.short_description = "Tamaño"

    actions = ["reprocesar_archivos"]

    def reprocesar_archivos(self, request, queryset):
        """Acción para reprocesar archivos seleccionados"""
        from .tasks import procesar_nombres_ingles_upload

        count = 0
        for upload in queryset:
            if upload.estado in ["error", "completado"]:
                upload.estado = "subido"
                upload.errores = ""
                upload.resumen = {}
                upload.save(update_fields=["estado", "errores", "resumen"])
                procesar_nombres_ingles_upload.delay(upload.id)
                count += 1

        self.message_user(
            request, f"Se enviaron {count} archivo(s) para reprocesamiento."
        )

    reprocesar_archivos.short_description = "Reprocesar archivos seleccionados"


@admin.register(TarjetaActivityLog)
class TarjetaActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "cliente_display",
        "tarjeta",
        "accion",
        "usuario",
        "resultado",
        "descripcion_corta",
    )
    list_filter = ("tarjeta", "accion", "resultado", "timestamp")
    search_fields = ("descripcion", "usuario__username", "cierre__cliente__nombre")
    readonly_fields = (
        "timestamp",
        "cierre",
        "tarjeta",
        "accion",
        "descripcion",
        "usuario",
        "detalles",
        "resultado",
        "ip_address",
    )
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"

    def cliente_display(self, obj):
        """Muestra el nombre del cliente del cierre"""
        return obj.cierre.cliente.nombre if obj.cierre and obj.cierre.cliente else "-"

    cliente_display.short_description = "Cliente"
    cliente_display.admin_order_field = "cierre__cliente__nombre"

    def descripcion_corta(self, obj):
        """Muestra una versión corta de la descripción"""
        return (
            obj.descripcion[:60] + "..."
            if len(obj.descripcion) > 60
            else obj.descripcion
        )

    descripcion_corta.short_description = "Descripción"

    def get_queryset(self, request):
        """Optimiza las consultas incluyendo relaciones"""
        queryset = super().get_queryset(request)
        return queryset.select_related("cierre", "cierre__cliente", "usuario")

    # Solo lectura para preservar la integridad de los logs
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Solo superusuarios pueden eliminar logs


@admin.register(NombreIngles)
class NombreInglesAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "cuenta_codigo",
        "nombre_ingles",
        "cierre_info",
        "fecha_creacion",
        "fecha_actualizacion",
    )
    list_filter = ("cliente", "cierre", "fecha_creacion")
    search_fields = ("cuenta_codigo", "nombre_ingles", "cliente__nombre")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    ordering = ("cliente", "cuenta_codigo")

    def cierre_info(self, obj):
        """Información del cierre asociado"""
        if obj.cierre:
            return f"{obj.cierre.periodo}"
        return "General (sin cierre específico)"

    cierre_info.short_description = "Período/Cierre"
    cierre_info.admin_order_field = "cierre__periodo"

    def get_queryset(self, request):
        """Optimiza las consultas incluyendo relaciones"""
        queryset = super().get_queryset(request)
        return queryset.select_related("cliente", "cierre")


@admin.register(NombreInglesArchivo)
class NombreInglesArchivoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "archivo_nombre", "fecha_subida", "tamaño_archivo")
    list_filter = ("cliente", "fecha_subida")
    search_fields = ("cliente__nombre", "archivo")
    readonly_fields = ("fecha_subida",)
    ordering = ("-fecha_subida",)

    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo, no la ruta completa"""
        import os

        return os.path.basename(obj.archivo.name) if obj.archivo else "-"

    archivo_nombre.short_description = "Archivo"

    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo en formato legible"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ["B", "KB", "MB", "GB"]:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"

    tamaño_archivo.short_description = "Tamaño"

    def get_queryset(self, request):
        """Optimiza las consultas incluyendo relaciones"""
        queryset = super().get_queryset(request)
        return queryset.select_related("cliente")


@admin.register(AnalisisCuentaCierre)
class AnalisisCuentaCierreAdmin(admin.ModelAdmin):
    list_display = (
        "cierre_info",
        "cuenta_info",
        "analista",
        "texto_analisis_corto",
        "creado",
        "actualizado",
    )
    list_filter = ("analista", "cierre__cliente", "cierre__periodo", "creado")
    search_fields = (
        "cuenta__codigo",
        "cuenta__nombre",
        "texto_analisis",
        "cierre__cliente__nombre",
        "cierre__periodo",
    )
    readonly_fields = ("creado", "actualizado")
    ordering = ("-actualizado",)
    date_hierarchy = "creado"

    def cierre_info(self, obj):
        """Información del cierre asociado"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"

    cierre_info.short_description = "Cliente - Período"
    cierre_info.admin_order_field = "cierre__periodo"

    def cuenta_info(self, obj):
        """Información de la cuenta"""
        return f"{obj.cuenta.codigo} - {obj.cuenta.nombre}"

    cuenta_info.short_description = "Cuenta"
    cuenta_info.admin_order_field = "cuenta__codigo"

    def texto_analisis_corto(self, obj):
        """Muestra una versión corta del análisis"""
        return (
            obj.texto_analisis[:80] + "..."
            if len(obj.texto_analisis) > 80
            else obj.texto_analisis
        )

    texto_analisis_corto.short_description = "Análisis"

    def get_queryset(self, request):
        """Optimiza las consultas incluyendo relaciones"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "cierre", "cierre__cliente", "cuenta", "analista"
        )

    fieldsets = (
        ("Información Principal", {"fields": ("cierre", "cuenta", "analista")}),
        ("Análisis", {"fields": ("texto_analisis",), "classes": ("wide",)}),
        ("Metadatos", {"fields": ("creado", "actualizado"), "classes": ("collapse",)}),
    )


@admin.register(UploadLog)
class UploadLogAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_subida",
        "tipo_upload",
        "cliente",
        "usuario",
        "estado",
        "nombre_archivo_corto",
        "tamaño_legible",
        "tiempo_procesamiento_corto",
    )
    list_filter = ("tipo_upload", "estado", "cliente", "usuario", "fecha_subida")
    search_fields = (
        "cliente__nombre",
        "usuario__username",
        "nombre_archivo_original",
        "errores",
        "hash_archivo",
    )
    readonly_fields = (
        "fecha_subida",
        "hash_archivo",
        "tamaño_archivo",
        "tiempo_procesamiento",
    )
    ordering = ("-fecha_subida",)
    date_hierarchy = "fecha_subida"

    def nombre_archivo_corto(self, obj):
        """Muestra nombre de archivo truncado"""
        if len(obj.nombre_archivo_original) > 30:
            return f"{obj.nombre_archivo_original[:27]}..."
        return obj.nombre_archivo_original

    nombre_archivo_corto.short_description = "Archivo"

    def tamaño_legible(self, obj):
        """Convierte bytes a formato legible"""
        size = obj.tamaño_archivo
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    tamaño_legible.short_description = "Tamaño"

    def tiempo_procesamiento_corto(self, obj):
        """Muestra tiempo de procesamiento en formato corto"""
        if obj.tiempo_procesamiento:
            seconds = obj.tiempo_procesamiento.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        return "-"

    tiempo_procesamiento_corto.short_description = "Tiempo Proc."

    def get_queryset(self, request):
        """Optimiza queries con select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related("cliente", "usuario", "cierre")

    fieldsets = (
        (
            "Información Principal",
            {"fields": ("tipo_upload", "cliente", "cierre", "usuario")},
        ),
        (
            "Archivo",
            {"fields": ("nombre_archivo_original", "tamaño_archivo", "hash_archivo")},
        ),
        (
            "Procesamiento",
            {"fields": ("estado", "errores", "resumen", "tiempo_procesamiento")},
        ),
        (
            "Metadatos",
            {"fields": ("fecha_subida", "ip_usuario"), "classes": ("collapse",)},
        ),
    )

    # Solo lectura para preservar integridad
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ===============================================================
#                    INCIDENCIAS CONSOLIDADAS
# ===============================================================

@admin.register(IncidenciaResumen)
class IncidenciaResumenAdmin(admin.ModelAdmin):
    """Administración de incidencias consolidadas"""
    
    list_display = [
        'id',
        'tipo_incidencia_display',
        'codigo_problema',
        'cantidad_afectada',
        'severidad_display',
        'estado_display',
        'elementos_afectados_display',
        'fecha_deteccion',
        'upload_log_info',
    ]
    
    list_filter = [
        'tipo_incidencia',
        'severidad',
        'estado',
        'fecha_deteccion',
        'upload_log__cliente',
    ]
    
    search_fields = [
        'codigo_problema',
        'mensaje_usuario',
        'upload_log__nombre_archivo_original',
        'upload_log__cierre__periodo',
    ]
    
    readonly_fields = [
        'fecha_deteccion',
        'elementos_afectados_display',
        'ver_todos_elementos',
        'estadisticas_adicionales',
        'detalle_muestra_json',
    ]
    
    date_hierarchy = 'fecha_deteccion'
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'upload_log',
                'tipo_incidencia',
                'codigo_problema',
                'cantidad_afectada',
                'estado'
            )
        }),
        ('Severidad y Mensajes', {
            'fields': (
                'severidad',
                'mensaje_usuario',
                'accion_sugerida'
            )
        }),
        ('Datos Consolidados', {
            'fields': (
                'elementos_afectados_display',
                'ver_todos_elementos',
                'detalle_muestra_json',
                'estadisticas_adicionales'
            ),
            'classes': ('collapse',)
        }),
        ('Resolución', {
            'fields': (
                'fecha_resolucion',
                'resuelto_por'
            ),
            'classes': ('collapse',)
        })
    )
    def detalle_muestra_json(self, obj):
        """Muestra el JSON completo de detalle_muestra."""
        if not obj.detalle_muestra:
            return "N/A"
        pretty = json.dumps(obj.detalle_muestra, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background-color: #000080; color: #FFD700; '
            'padding:10px; border:1px solid #444; max-height:300px; overflow:auto;">'
            '{}'
            '</pre>',
            pretty
        )
    detalle_muestra_json.short_description = "Detalle Completo (raw JSON)"
    
    def estadisticas_adicionales(self, obj):
        """Muestra el JSON de estadísticas de forma legible."""
        stats = getattr(obj, 'detalle_muestra', None) or obj.upload_log.resumen.get('conteos_por_tipo')
        if not stats:
            return "N/A"
        pretty = json.dumps(stats, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background-color: #000080; color: #FFD700; '
            'padding:10px; border:1px solid #444; max-height:300px; overflow:auto;">'
            '{}'
            '</pre>',
            pretty
        )
    estadisticas_adicionales.short_description = "Estadísticas Consolidadas"

    def tipo_incidencia_display(self, obj):
        """Tipo de incidencia con ícono"""
        icons = {
            'tipos_doc_no_reconocidos': '📄',
            'movimientos_tipodoc_nulo': '❌',
            'cuentas_sin_clasificacion': '🏷️',
            'cuentas_sin_nombre_ingles': '🌐',
            'cuentas_nuevas_detectadas': '✨',
        }
        icon = icons.get(obj.tipo_incidencia, '📝')
        return f"{icon} {obj.get_tipo_incidencia_display()}"
    tipo_incidencia_display.short_description = 'Tipo'
    
    def severidad_display(self, obj):
        """Severidad con colores"""
        colors = {
            'baja': '🟢',
            'media': '🟡',
            'alta': '🟠',
            'critica': '🔴'
        }
        color = colors.get(obj.severidad, '⚪')
        return f"{color} {obj.get_severidad_display()}"
    severidad_display.short_description = 'Severidad'
    
    def estado_display(self, obj):
        """Estado con íconos"""
        icons = {
            'activa': '🔴 Activa',
            'resuelta': '✅ Resuelta', 
            'obsoleta': '⏳ Obsoleta'
        }
        return icons.get(obj.estado, obj.estado)
    estado_display.short_description = 'Estado'
    
    def upload_log_info(self, obj):
        """Información del upload log"""
        return f"{obj.upload_log.cliente.nombre} - {obj.upload_log.nombre_archivo_original}"
    upload_log_info.short_description = 'Upload Log'
    
    def elementos_afectados_display(self, obj):
        """Muestra los elementos afectados de forma resumida"""
        if not obj.elementos_afectados:
            return "Sin elementos específicos"
        
        elementos = obj.elementos_afectados
        if len(elementos) <= 5:
            return ", ".join(elementos)
        else:
            primeros_cinco = ", ".join(elementos[:5])
            return f"{primeros_cinco}... (+{len(elementos)-5} más)"
    elementos_afectados_display.short_description = 'Elementos Afectados'
    
    def ver_todos_elementos(self, obj):
        """Link para ver todos los elementos afectados"""
        if not obj.elementos_afectados:
            return "N/A"
        
        # Construimos el HTML de los elementos con <br> y lo marcamos como seguro
        elementos_html = mark_safe("<br>".join(obj.elementos_afectados))
        
        return format_html(
            '<details>'
                '<summary style="background-color:#000080; color:#FFD700; padding:4px; '
                            'border-radius:4px; cursor:pointer;">'
                    'Ver {} elementos'
                '</summary>'
                '<div style="background-color:#000080; color:#FFD700; '
                            'max-height:200px; overflow-y:auto; padding:10px; '
                            'border:1px solid #444; border-top:none;">'
                    '{}'
                '</div>'
            '</details>',
            len(obj.elementos_afectados),
            elementos_html,  # ya es HTML “seguro”
        )
    ver_todos_elementos.short_description = 'Detalle Completo'
   

    
    def marcar_como_resueltas(self, request, queryset):
        """Acción para marcar incidencias como resueltas"""
        count = 0
        for incidencia in queryset.filter(estado='activa'):
            incidencia.marcar_como_resuelta(usuario=request.user)
            count += 1
        
        self.message_user(
            request,
            f'{count} incidencias marcadas como resueltas.'
        )
    marcar_como_resueltas.short_description = 'Marcar como resueltas'


@admin.register(HistorialReprocesamiento) 
class HistorialReprocesarAdmin(admin.ModelAdmin):
    """Administración del historial de reprocesamientos"""
    
    list_display = [
        'id',
        'upload_log_info',
        'iteracion',
        'mejora_display',
        'trigger_reprocesamiento',
        'usuario',
        'fecha_inicio',
    ]
    
    list_filter = [
        'trigger_reprocesamiento',
        'fecha_inicio',
        'upload_log__cliente',
    ]
    
    search_fields = [
        'upload_log__nombre_archivo_original',
        'notas',
    ]
    
    readonly_fields = [
        'fecha_inicio',
        'tiempo_procesamiento',
        'incidencias_previas',
        'incidencias_nuevas',
        'incidencias_resueltas',
        'calcular_efectividad',
        'obtener_mejoras',
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'upload_log',
                'usuario',
                'iteracion',
                'trigger_reprocesamiento'
            )
        }),
        ('Métricas', {
            'fields': (
                'incidencias_previas_count',
                'incidencias_nuevas_count', 
                'incidencias_resueltas_count',
                'movimientos_corregidos',
                'movimientos_total'
            )
        }),
        ('Detalles', {
            'fields': (
                'incidencias_previas',
                'incidencias_nuevas',
                'incidencias_resueltas',
                'tiempo_procesamiento',
                'notas'
            ),
            'classes': ('collapse',)
        })
    )
    
    def upload_log_info(self, obj):
        """Info del upload log"""
        return f"{obj.upload_log.cliente.nombre} - {obj.upload_log.nombre_archivo_original}"
    upload_log_info.short_description = 'Upload Log'
    
    def mejora_display(self, obj):
        """Muestra porcentaje de mejora"""
        efectividad = obj.calcular_efectividad()
        if efectividad == 100:
            return "✅ 100%"
        elif efectividad >= 80:
            return f"🟢 {efectividad:.1f}%"
        elif efectividad >= 50:
            return f"🟡 {efectividad:.1f}%" 
        else:
            return f"🔴 {efectividad:.1f}%"
    mejora_display.short_description = 'Efectividad'


@admin.register(LogResolucionIncidencia)
class LogResolucionIncidenciaAdmin(admin.ModelAdmin):
    """Administración de logs de resolución"""
    
    list_display = [
        'id',
        'incidencia_info',
        'accion_realizada',
        'cantidad_resuelta',
        'usuario',
        'fecha_accion',
    ]
    
    list_filter = [
        'accion_realizada',
        'fecha_accion',
    ]
    
    search_fields = [
        'observaciones',
        'incidencia_resumen__codigo_problema',
    ]
    
    readonly_fields = [
        'fecha_accion',
        'elementos_resueltos',
        'datos_adicionales',
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'incidencia_resumen',
                'usuario',
                'accion_realizada',
                'cantidad_resuelta'
            )
        }),
        ('Detalles', {
            'fields': (
                'elementos_resueltos',
                'upload_log_relacionado',
                'observaciones',
                'datos_adicionales'
            ),
            'classes': ('collapse',)
        })
    )
    
    def incidencia_info(self, obj):
        """Info de la incidencia"""
        return f"{obj.incidencia_resumen.get_tipo_incidencia_display()} - {obj.incidencia_resumen.codigo_problema or 'General'}"
    incidencia_info.short_description = 'Incidencia'
