# Register your models here.

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import JsonResponse, HttpResponse
from django.urls import path
import json

from .models import (
    AccountClassification,
    AnalisisCuentaCierre,
    AperturaCuenta,
    Auxiliar,
    CentroCosto,
    CierreContabilidad,
    ClasificacionArchivo,
    # ClasificacionCuentaArchivo,  # OBSOLETO - COMENTADO
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    LibroMayorArchivo,  # Nuevo modelo para manejar archivos de libro mayor
    MovimientoContable,
    NombresEnInglesUpload,
    ReporteFinanciero,  # ✨ NUEVO: Modelo de reportes financieros
    TarjetaActivityLog,
    TipoDocumento,
    TipoDocumentoArchivo,
    UploadLog,
)

# ✨ NUEVO: Importar modelos de incidencias consolidadas
from .models_incidencias import (
    Incidencia,
    IncidenciaResumen,
)
# ✨ NUEVO: Importar modelo de excepciones
from .models import ExcepcionValidacion, ExcepcionClasificacionSet


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
    list_display = (
        "cierre", 
        "cuenta_info", 
        "saldo_inicial_debe", 
        "saldo_inicial_haber", 
        "saldo_neto",
        "periodo_info"
    )
    list_filter = (
        "cierre__cliente",  # Filtro por cliente
        "cierre",           # Filtro por cierre específico
        "cierre__periodo",  # Filtro por período
    )
    search_fields = (
        "cuenta__codigo",
        "cuenta__nombre",
        "cierre__periodo",
        "cierre__cliente__nombre"
    )
    raw_id_fields = ("cuenta",)
    
    def cuenta_info(self, obj):
        return f"{obj.cuenta.codigo} - {obj.cuenta.nombre}"
    cuenta_info.short_description = "Cuenta"
    cuenta_info.admin_order_field = "cuenta__codigo"
    
    def periodo_info(self, obj):
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    periodo_info.short_description = "Cliente - Período"
    
    def saldo_inicial_debe(self, obj):
        # Buscar campos de saldo inicial en el modelo
        # Nota: El modelo actual solo tiene 'saldo_anterior', 
        # pero necesitaríamos campos separados para debe/haber inicial
        return f"${obj.saldo_anterior:,.2f}" if obj.saldo_anterior > 0 else "$0.00"
    saldo_inicial_debe.short_description = "Saldo Inicial"
    
    def saldo_inicial_haber(self, obj):
        # Placeholder - necesitaríamos agregar este campo al modelo
        return "$0.00"  
    saldo_inicial_haber.short_description = "Saldo Inicial Haber"
    
    def saldo_neto(self, obj):
        return f"${obj.saldo_anterior:,.2f}"
    saldo_neto.short_description = "Saldo Neto"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre', 
            'cierre__cliente',
            'cuenta'
        )
    
    fieldsets = (
        ("Información Principal", {
            "fields": ("cierre", "cuenta")
        }),
        ("Saldos", {
            "fields": ("saldo_anterior",)
        })
    )


@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    list_display = (
        "cierre",
        "periodo",        # ← añade el periodo para ver en qué cierre quedó
        "cuenta",
        "debe",
        "haber",
        "saldo_movimiento",
        "tipo_documento",
        "numero_documento",
        "tipo",
        "numero_comprobante",
        "numero_interno",
    )
    list_filter = (
        "fecha", 
        "cierre__cliente",  # Filtro por cliente
        "cierre",           # Filtro por cierre específico
        "cuenta",           # Filtro por cuenta
        "tipo_documento",   # Filtro por tipo de documento
        "numero_interno",   # Filtro por número interno
        "flag_incompleto",  # Filtro por movimientos incompletos
    )
    search_fields = (
        "descripcion",
        "cuenta__codigo",
        "cuenta__nombre", 
        "numero_documento",
        "numero_comprobante",
        "cierre__periodo"
    )
    raw_id_fields = ("cuenta", "tipo_documento", "centro_costo", "auxiliar")
    readonly_fields = ("saldo_movimiento",)
    date_hierarchy = "fecha"

    def periodo(self, obj):
        """Muestra el periodo del cierre asociado"""
        return obj.cierre.periodo if obj.cierre else "-"

    periodo.short_description = "Periodo"
    
    def saldo_movimiento(self, obj):
        """Muestra el efecto neto del movimiento (debe - haber)"""
        saldo = obj.debe - obj.haber
        if saldo > 0:
            return f"${saldo:,.2f} (Débito)"
        elif saldo < 0:
            return f"${abs(saldo):,.2f} (Crédito)"
        else:
            return "$0.00"
    saldo_movimiento.short_description = "Efecto Neto"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre', 
            'cierre__cliente',
            'cuenta', 
            'tipo_documento',
            'centro_costo',
            'auxiliar'
        )
    
    fieldsets = (
        ("Información Principal", {
            "fields": ("cierre", "cuenta", "fecha")
        }),
        ("Montos", {
            "fields": ("debe", "haber", "saldo_movimiento")
        }),
        ("Documentos", {
            "fields": ("tipo_documento", "tipo_doc_codigo", "numero_documento", "numero_comprobante", "numero_interno")
        }),
        ("Detalles", {
            "fields": ("tipo", "centro_costo", "auxiliar", "detalle_gasto", "descripcion")
        }),
        ("Estado", {
            "fields": ("flag_incompleto",),
            "classes": ("collapse",)
        })
    )


@admin.register(ClasificacionSet)
class ClasificacionSetAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nombre", "total_opciones", "es_predefinido")
    list_filter = ("cliente", "nombre")
    search_fields = ("cliente__nombre", "nombre")
    actions = ["recuperar_sets_predefinidos", "reinstalar_sets_completos"]
    
    def total_opciones(self, obj):
        return obj.opciones.count()
    total_opciones.short_description = "Total Opciones"
    
    def es_predefinido(self, obj):
        sets_predefinidos = [
            "Tipo de Cuenta", "Clasificacion Balance", 
            "Categoria IFRS", "AGRUPACION CLIENTE"
        ]
        return "✓" if obj.nombre in sets_predefinidos else "-"
    es_predefinido.short_description = "Predefinido"
    
    def recuperar_sets_predefinidos(self, request, queryset):
        """Acción para recuperar sets predefinidos para los clientes seleccionados"""
        from .tasks_cuentas_bulk import crear_sets_predefinidos_clasificacion
        
        clientes_procesados = set()
        total_exitosos = 0
        total_errores = 0
        
        for obj in queryset:
            if obj.cliente.id not in clientes_procesados:
                try:
                    resultado = crear_sets_predefinidos_clasificacion(obj.cliente.id)
                    clientes_procesados.add(obj.cliente.id)
                    total_exitosos += 1
                except Exception as e:
                    self.message_user(
                        request, 
                        f"Error recuperando sets para cliente {obj.cliente.nombre}: {str(e)}",
                        level='ERROR'
                    )
                    total_errores += 1
        
        if total_exitosos > 0:
            self.message_user(
                request,
                f"Sets predefinidos recuperados exitosamente para {total_exitosos} cliente(s)",
                level='SUCCESS'
            )
    
    recuperar_sets_predefinidos.short_description = "Recuperar sets predefinidos"
    
    def reinstalar_sets_completos(self, request, queryset):
        """Acción para reinstalar completamente sets (RAW + predefinidos) para los clientes seleccionados"""
        from .tasks_cuentas_bulk import recuperar_sets_clasificacion_cliente
        
        clientes_procesados = set()
        total_exitosos = 0
        total_errores = 0
        
        for obj in queryset:
            if obj.cliente.id not in clientes_procesados:
                try:
                    resultado = recuperar_sets_clasificacion_cliente(
                        obj.cliente.id,
                        incluir_predefinidos=True,
                        limpiar_existentes=False
                    )
                    clientes_procesados.add(obj.cliente.id)
                    total_exitosos += 1
                except Exception as e:
                    self.message_user(
                        request, 
                        f"Error reinstalando sets para cliente {obj.cliente.nombre}: {str(e)}",
                        level='ERROR'
                    )
                    total_errores += 1
        
        if total_exitosos > 0:
            self.message_user(
                request,
                f"Sets completos reinstalados exitosamente para {total_exitosos} cliente(s)",
                level='SUCCESS'
            )
    
    reinstalar_sets_completos.short_description = "Reinstalar sets completos (RAW + predefinidos)"


@admin.register(ClasificacionOption)
class ClasificacionOptionAdmin(admin.ModelAdmin):
    list_display = ("set_clas", "valor")


# ✨ FILTROS PERSONALIZADOS PARA ACCOUNTCLASSIFICATION
class AccountClassificationStatusFilter(admin.SimpleListFilter):
    title = "Estado de la cuenta"
    parameter_name = "estado_cuenta"

    def lookups(self, request, model_admin):
        return [
            ("con_fk", "Con FK"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val == "con_fk":
            return queryset.filter(cuenta__isnull=False)
        return queryset


class AccountClassificationClienteFilter(admin.SimpleListFilter):
    title = "Cliente (optimizado)"
    parameter_name = "cliente_opt"

    def lookups(self, request, model_admin):
        # Obtener clientes que tienen clasificaciones
        from django.db.models import Count
        try:
            clientes = AccountClassification.objects.values(
                'cliente__id', 'cliente__nombre'
            ).annotate(
                clasificaciones_count=Count('id')
            ).order_by('-clasificaciones_count')[:10]  # Top 10 clientes con más clasificaciones
            
            return [(c['cliente__id'], f"{c['cliente__nombre']} ({c['clasificaciones_count']} clasif.)") for c in clientes if c['cliente__id']]
        except:
            return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(cliente_id=self.value())
        return queryset


@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = (
        "estado_cuenta_display", 
        "codigo_cuenta_display", 
        "nombre_cuenta_display",
        "set_clas", 
        "opcion", 
        "cliente_display",
        "asignado_por", 
        "fecha"
    )
    list_filter = (
    AccountClassificationStatusFilter,
    AccountClassificationClienteFilter,
        "set_clas",  # Filtro por set de clasificación
        "opcion",    # Filtro por opción de clasificación
        "asignado_por",     # Filtro por quien asignó
        "fecha",            # Filtro por fecha
    )
    search_fields = (
        "cuenta__codigo",    # Búsqueda por código FK
        "cuenta__nombre",    # Búsqueda por nombre FK
        "set_clas__nombre", 
        "opcion__valor",
        "cliente__nombre"
    )
    raw_id_fields = ("cuenta", "cliente")  # Para facilitar búsqueda
    readonly_fields = ("fecha",)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cuenta', 
            'cliente', 
            'set_clas', 
            'opcion', 
            'asignado_por'
        )
    
    def estado_cuenta_display(self, obj):
        """Muestra el estado de la relación con la cuenta"""
        if obj.cuenta:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ FK</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ TEMPORAL</span>'
            )
    estado_cuenta_display.short_description = "Estado"
    estado_cuenta_display.admin_order_field = "cuenta"
    
    def codigo_cuenta_display(self, obj):
        """Muestra el código de cuenta (FK o temporal)"""
        if obj.cuenta:
            return format_html('<strong style="color: green;">{}</strong>', obj.cuenta.codigo)
        return format_html('<span style="color: #888; font-style: italic;">Sin cuenta</span>')
    codigo_cuenta_display.short_description = "Código Cuenta"
    codigo_cuenta_display.admin_order_field = "cuenta__codigo"
    
    def nombre_cuenta_display(self, obj):
        """Muestra el nombre de la cuenta si existe FK"""
        if obj.cuenta:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.cuenta.nombre[:50] + "..." if len(obj.cuenta.nombre) > 50 else obj.cuenta.nombre
            )
        else:
            return format_html(
                '<span style="color: #888; font-style: italic;">Sin cuenta asignada</span>'
            )
    nombre_cuenta_display.short_description = "Nombre Cuenta"
    nombre_cuenta_display.admin_order_field = "cuenta__nombre"
    
    def cliente_display(self, obj):
        """Muestra el cliente"""
        if obj.cliente:
            return format_html(
                '{} ({})',
                obj.cliente.nombre[:30] + "..." if len(obj.cliente.nombre) > 30 else obj.cliente.nombre,
                obj.cliente.rut or "Sin RUT"
            )
        return "Sin cliente"
    cliente_display.short_description = "Cliente"
    cliente_display.admin_order_field = "cliente__nombre"
    
    fieldsets = (
        ("Estado de la Clasificación", {
            "fields": ("estado_cuenta_display", "codigo_cuenta_display", "nombre_cuenta_display"),
            "classes": ("wide",),
            "description": "Estado actual de la relación con la cuenta contable"
        }),
        ("Clasificación Principal", {
            "fields": ("cuenta", "cliente", "set_clas", "opcion"),
            "description": "Configuración de la clasificación."
        }),
        ("Metadatos", {
            "fields": ("asignado_por", "fecha"),
            "classes": ("collapse",)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Campos de solo lectura dinámicos"""
        readonly = list(self.readonly_fields)
        readonly.extend(["estado_cuenta_display", "codigo_cuenta_display", "nombre_cuenta_display"])
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Lógica personalizada al guardar"""
        # Si no hay asignado_por, usar el usuario actual
        if not obj.asignado_por:
            obj.asignado_por = request.user
        
        # Si no hay cliente pero hay cuenta FK, tomar cliente de la cuenta
        if obj.cuenta and not obj.cliente:
            obj.cliente = obj.cuenta.cliente
            
        super().save_model(request, obj, form, change)
    actions = []


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display  = ("tipo", "cuenta_codigo", "tipo_doc_codigo", "descripcion", "fecha_creacion", "creada_por")
    list_filter   = ("tipo",)
    search_fields = ("cuenta_codigo", "tipo_doc_codigo", "descripcion")
    readonly_fields = ("fecha_creacion",)

@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "nombre")
    list_filter = ("cliente",)


@admin.register(Auxiliar)
class AuxiliarAdmin(admin.ModelAdmin):
    list_display = ("rut_auxiliar", "nombre", "fecha_creacion")


# ADMIN OBSOLETO - COMENTADO JUNTO CON EL MODELO
# @admin.register(ClasificacionCuentaArchivo)
# class ClasificacionCuentaArchivoAdmin(admin.ModelAdmin):
#     list_display = (
#         "cliente",
#         "upload_log",
#         "numero_cuenta",
#         "fila_excel",
#         "fecha_creacion",
#     )
#     list_filter = ("cliente", "upload_log__estado", "fecha_creacion")
#     search_fields = ("numero_cuenta", "cliente__nombre")
#     readonly_fields = ("fecha_creacion",)
# 
#     def has_add_permission(self, request):
#         """No permitir agregar manualmente"""
#         return False
# 
#     def get_queryset(self, request):
#         return (
#             super()
#             .get_queryset(request)
#             .select_related("cliente", "upload_log")
#         )


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


    # Eliminado: admins de staging NombreIngles/NombreInglesArchivo

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






@admin.register(ExcepcionValidacion)
class ExcepcionValidacionAdmin(admin.ModelAdmin):
    """Admin para gestionar excepciones de validación"""
    list_display = [
        'cliente', 
        'codigo_cuenta', 
        'tipo_excepcion', 
        'activa', 
        'fecha_creacion',
        'usuario_creador'
    ]
    list_filter = [
        'tipo_excepcion',
        'activa',
        'fecha_creacion',
        'cliente'
    ]
    search_fields = [
        'codigo_cuenta',
        'nombre_cuenta',
        'cliente__nombre',
        'cliente__rut',
        'motivo'
    ]
    readonly_fields = [
        'fecha_creacion'
    ]
    fieldsets = (
        ('Información básica', {
            'fields': (
                'cliente',
                'codigo_cuenta',
                'nombre_cuenta',
                'tipo_excepcion',
                'activa'
            )
        }),
        ('Detalles', {
            'fields': (
                'motivo',
                'usuario_creador'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'usuario_creador')


@admin.register(ExcepcionClasificacionSet)
class ExcepcionClasificacionSetAdmin(admin.ModelAdmin):
    """Admin para gestionar excepciones específicas por set de clasificación"""
    list_display = [
        'cliente',
        'cuenta_codigo',
        'cuenta_nombre_display',
        'set_clasificacion',
        'activa',
        'fecha_creacion',
        'usuario_creador'
    ]
    list_filter = [
        'activa',
        'fecha_creacion',
        'cliente',
        'set_clasificacion',
        'set_clasificacion__nombre'
    ]
    search_fields = [
        'cuenta_codigo',
        'cliente__nombre',
        'cliente__rut',
        'set_clasificacion__nombre',
        'motivo',
        'usuario_creador__username'
    ]
    readonly_fields = [
        'fecha_creacion',
        'cuenta_nombre_display'
    ]
    raw_id_fields = [
        'set_clasificacion'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'cliente',
                'cuenta_codigo',
                'cuenta_nombre_display',
                'set_clasificacion',
                'activa'
            )
        }),
        ('Justificación', {
            'fields': (
                'motivo',
                'usuario_creador'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
            ),
            'classes': ('collapse',)
        })
    )
    
    def cuenta_nombre_display(self, obj):
        """Muestra el nombre de la cuenta si existe"""
        return obj.cuenta_nombre
    cuenta_nombre_display.short_description = 'Nombre de la Cuenta'
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related(
            'cliente', 
            'set_clasificacion', 
            'usuario_creador'
        )
    
    def save_model(self, request, obj, form, change):
        """Establece el usuario creador automáticamente al crear"""
        if not change and hasattr(request, 'user'):
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)
    
    # Acciones personalizadas
    actions = ['activar_excepciones', 'desactivar_excepciones']
    
    def activar_excepciones(self, request, queryset):
        """Activa las excepciones seleccionadas"""
        updated = queryset.update(activa=True)
        self.message_user(
            request,
            f'Se activaron {updated} excepción(es) de clasificación.'
        )
    activar_excepciones.short_description = 'Activar excepciones seleccionadas'
    
    def desactivar_excepciones(self, request, queryset):
        """Desactiva las excepciones seleccionadas"""
        updated = queryset.update(activa=False)
        self.message_user(
            request,
            f'Se desactivaron {updated} excepción(es) de clasificación.'
        )
    desactivar_excepciones.short_description = 'Desactivar excepciones seleccionadas'


# ===============================================================================
#                           REPORTES FINANCIEROS
# ===============================================================================

@admin.register(ReporteFinanciero)
class ReporteFinancieroAdmin(admin.ModelAdmin):
    """
    Admin para visualizar y gestionar reportes financieros generados
    """
    list_display = (
        'id',
        'cierre_info',
        'tipo_reporte_badge',
        'estado_badge',
        'usuario_generador',
        'fecha_generacion',
        'es_valido_badge',
        'acciones_reporte'
    )
    
    list_filter = (
        'tipo_reporte',
        'estado',
        'fecha_generacion',
        'cierre__cliente',
        'cierre__periodo'
    )
    
    search_fields = (
        'cierre__cliente__nombre',
        'cierre__periodo',
        'usuario_generador__username',
        'usuario_generador__first_name',
        'usuario_generador__last_name'
    )
    
    readonly_fields = (
        'id',
        'fecha_generacion',
        'fecha_actualizacion',
        'es_valido_badge',
        'datos_preview',
        'metadata_preview',
        'resumen_datos'
    )
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'id',
                'cierre',
                'tipo_reporte',
                'estado',
                'usuario_generador'
            )
        }),
        ('Estado y Validez', {
            'fields': (
                'es_valido_badge',
                'error_mensaje'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_generacion',
                'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        }),
        ('Datos del Reporte', {
            'fields': (
                'resumen_datos',
                'datos_preview'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'metadata_preview',
                'metadata'
            ),
            'classes': ('collapse',)
        })
    )
    
    def cierre_info(self, obj):
        """Información del cierre asociado"""
        return format_html(
            '<strong>{}</strong><br>'
            '<small>{} - {}</small>',
            obj.cierre.cliente.nombre,
            obj.cierre.periodo,
            obj.cierre.get_estado_display()
        )
    cierre_info.short_description = 'Cierre'
    
    def tipo_reporte_badge(self, obj):
        """Badge para el tipo de reporte"""
        color_map = {
            'esf': '#28a745',  # Verde
            'eri': '#17a2b8',  # Azul
            'ecp': '#ffc107'   # Amarillo
        }
        color = color_map.get(obj.tipo_reporte, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_reporte_display()
        )
    tipo_reporte_badge.short_description = 'Tipo'
    
    def estado_badge(self, obj):
        """Badge para el estado del reporte"""
        color_map = {
            'generando': '#ffc107',    # Amarillo
            'completado': '#28a745',   # Verde
            'error': '#dc3545'         # Rojo
        }
        color = color_map.get(obj.estado, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def es_valido_badge(self, obj):
        """Badge para mostrar si el reporte es válido"""
        if obj.es_valido:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✓ Válido</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✗ Inválido</span>'
            )
    es_valido_badge.short_description = 'Validez'
    
    def acciones_reporte(self, obj):
        """Enlaces de acciones para el reporte"""
        acciones = []
        
        # Reenviar al caché (solo para reportes completados)
        if obj.estado == 'completado' and obj.datos_reporte:
            acciones.append(
                f'<a href="/admin/contabilidad/reportefinanciero/{obj.id}/reenviar-cache/" '
                f'style="color: #dc3545; text-decoration: none; font-weight: bold;" '
                f'title="Reenviar reporte al caché" '
                f'onclick="return confirm(\'¿Estás seguro de que quieres reenviar este reporte al caché?\');">'
                f'🔄 Reenviar a Caché</a>'
            )
        
        # Descargar JSON del reporte
        if obj.datos_reporte and obj.estado == 'completado':
            acciones.append(
                f'<a href="/admin/contabilidad/reportefinanciero/{obj.id}/descargar-json/" '
                f'style="color: #28a745; text-decoration: none; font-weight: bold;" '
                f'title="Descargar JSON del reporte">💾 Descargar JSON</a>'
            )
        
        # Ver JSON en nueva ventana
        if obj.datos_reporte:
            acciones.append(
                f'<a href="/admin/contabilidad/reportefinanciero/{obj.id}/ver-json/" '
                f'target="_blank" '
                f'style="color: #007cba; text-decoration: none;" '
                f'title="Ver JSON del reporte">👁️ Ver JSON</a>'
            )
        
        # Editar reporte
        acciones.append(
            f'<a href="/admin/contabilidad/reportefinanciero/{obj.id}/change/" '
            f'style="color: #ffc107; text-decoration: none;">✏️ Editar</a>'
        )
        
        return format_html(' | '.join(acciones)) if acciones else '-'
    acciones_reporte.short_description = 'Acciones'
    
    def resumen_datos(self, obj):
        """Resumen de los datos del reporte"""
        if not obj.datos_reporte:
            return "Sin datos"
        
        if not isinstance(obj.datos_reporte, dict):
            return f"Datos: {type(obj.datos_reporte).__name__}"
        
        # Resumen específico por tipo de reporte
        if obj.tipo_reporte == 'esf':
            return self._resumen_esf(obj.datos_reporte)
        elif obj.tipo_reporte == 'eri':
            return self._resumen_eri(obj.datos_reporte)
        else:
            return f"Claves principales: {', '.join(list(obj.datos_reporte.keys())[:5])}"
    
    resumen_datos.short_description = 'Resumen de Datos'
    
    def _resumen_esf(self, datos):
        """Resumen específico para Estado de Situación Financiera"""
        try:
            assets = datos.get('assets', {})
            liabilities = datos.get('liabilities', {})
            patrimony = datos.get('patrimony', {})
            
            total_assets = assets.get('total_assets', 0)
            total_liabilities = liabilities.get('total_liabilities', 0)
            total_patrimony = patrimony.get('total_patrimony', 0)
            
            return format_html(
                '<strong>Total Assets:</strong> ${:,.0f}<br>'
                '<strong>Total Liabilities:</strong> ${:,.0f}<br>'
                '<strong>Total Patrimony:</strong> ${:,.0f}',
                float(total_assets),
                float(total_liabilities),
                float(total_patrimony)
            )
        except (KeyError, ValueError, TypeError):
            return "Error en formato de datos ESF"
    
    def _resumen_eri(self, datos):
        """Resumen específico para Estado de Resultado Integral"""
        try:
            revenue = datos.get('revenue', 0)
            earnings = datos.get('earnings_loss_before_taxes', 0)
            
            return format_html(
                '<strong>Revenue:</strong> ${:,.0f}<br>'
                '<strong>Earnings Before Taxes:</strong> ${:,.0f}',
                float(revenue),
                float(earnings)
            )
        except (KeyError, ValueError, TypeError):
            return "Error en formato de datos ERI"
    
    def datos_preview(self, obj):
        """Preview de los datos JSON del reporte"""
        if not obj.datos_reporte:
            return "Sin datos de reporte"
        
        try:
            # Mostrar JSON formateado (limitado para no sobrecargar la interfaz)
            json_str = json.dumps(obj.datos_reporte, indent=2, ensure_ascii=False)
            
            # Truncar si es muy largo
            if len(json_str) > 2000:
                json_str = json_str[:2000] + "\n\n... [Datos truncados para visualización] ..."
            
            return format_html(
                '<pre style="background-color: #f8f9fa; padding: 10px; '
                'border-radius: 5px; font-size: 12px; max-height: 400px; '
                'overflow-y: auto;">{}</pre>',
                json_str
            )
        except Exception as e:
            return f"Error mostrando datos: {str(e)}"
    
    datos_preview.short_description = 'Preview de Datos JSON'
    
    def metadata_preview(self, obj):
        """Preview de los metadatos"""
        if not obj.metadata:
            return "Sin metadatos"
        
        try:
            json_str = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background-color: #f8f9fa; padding: 10px; '
                'border-radius: 5px; font-size: 12px; max-height: 200px; '
                'overflow-y: auto;">{}</pre>',
                json_str
            )
        except Exception as e:
            return f"Error mostrando metadatos: {str(e)}"
    
    metadata_preview.short_description = 'Preview de Metadatos'
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente',
            'usuario_generador'
        )
    
    # Acciones personalizadas
    actions = ['reenviar_reportes_a_cache']
    
    def reenviar_reportes_a_cache(self, request, queryset):
        """Acción para reenviar reportes seleccionados al caché"""
        from .tasks import enviar_reporte_a_cache  # Importar la tarea de Celery
        
        reportes_enviados = 0
        reportes_error = 0
        mensajes_error = []
        
        for reporte in queryset:
            try:
                # Validar que el reporte esté completado y tenga datos
                if reporte.estado != 'completado':
                    mensajes_error.append(f"Reporte #{reporte.id}: No está completado")
                    reportes_error += 1
                    continue
                
                if not reporte.datos_reporte:
                    mensajes_error.append(f"Reporte #{reporte.id}: No tiene datos")
                    reportes_error += 1
                    continue
                
                # Enviar al caché usando la tarea de Celery
                enviar_reporte_a_cache.delay(reporte.id)
                reportes_enviados += 1
                
            except Exception as e:
                mensajes_error.append(f"Reporte #{reporte.id}: Error - {str(e)}")
                reportes_error += 1
        
        # Mostrar mensajes de resultado
        if reportes_enviados > 0:
            self.message_user(
                request,
                f"Se enviaron {reportes_enviados} reporte(s) al caché para procesamiento.",
                level='SUCCESS'
            )
        
        if reportes_error > 0:
            mensaje_errores = "\n".join(mensajes_error[:5])  # Mostrar máximo 5 errores
            if len(mensajes_error) > 5:
                mensaje_errores += f"\n... y {len(mensajes_error) - 5} errores más"
            
            self.message_user(
                request,
                f"Errores en {reportes_error} reporte(s):\n{mensaje_errores}",
                level='ERROR'
            )
    
    reenviar_reportes_a_cache.short_description = "Reenviar reportes seleccionados al caché"
    
    def get_urls(self):
        """URLs personalizadas para el admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/descargar-json/',
                self.admin_site.admin_view(self.descargar_json),
                name='contabilidad_reportefinanciero_descargar_json'
            ),
            path(
                '<path:object_id>/ver-json/',
                self.admin_site.admin_view(self.ver_json),
                name='contabilidad_reportefinanciero_ver_json'
            ),
            path(
                '<path:object_id>/reenviar-cache/',
                self.admin_site.admin_view(self.reenviar_cache_individual),
                name='contabilidad_reportefinanciero_reenviar_cache'
            ),
        ]
        return custom_urls + urls
    
    def descargar_json(self, request, object_id):
        """Vista para descargar el JSON del reporte financiero"""
        try:
            reporte = self.get_object(request, object_id)
            if not reporte:
                return HttpResponse("Reporte no encontrado", status=404)
            
            if not reporte.datos_reporte:
                return HttpResponse("El reporte no tiene datos JSON", status=400)
            
            # Preparar el nombre del archivo
            cliente_nombre = reporte.cierre.cliente.nombre.replace(' ', '_').replace('/', '_')
            periodo = reporte.cierre.periodo.replace('/', '_').replace(' ', '_')
            tipo_reporte = reporte.get_tipo_reporte_display().replace(' ', '_')
            
            filename = f"{cliente_nombre}_{periodo}_{tipo_reporte}_{reporte.id}.json"
            
            # Crear la respuesta HTTP con el archivo JSON
            response = HttpResponse(
                json.dumps(reporte.datos_reporte, indent=2, ensure_ascii=False),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return HttpResponse(f"Error al descargar el archivo: {str(e)}", status=500)
    
    def ver_json(self, request, object_id):
        """Vista para mostrar el JSON del reporte en el navegador"""
        try:
            reporte = self.get_object(request, object_id)
            if not reporte:
                return HttpResponse("Reporte no encontrado", status=404)
            
            if not reporte.datos_reporte:
                return HttpResponse("El reporte no tiene datos JSON", status=400)
            
            # Crear página HTML simple para mostrar el JSON
            json_formateado = json.dumps(reporte.datos_reporte, indent=2, ensure_ascii=False)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>JSON - {reporte.get_tipo_reporte_display()} - {reporte.cierre.cliente.nombre}</title>
                <style>
                    body {{ font-family: 'Courier New', monospace; margin: 20px; background-color: #f5f5f5; }}
                    .header {{ background-color: #007cba; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .json-container {{ background-color: white; padding: 20px; border-radius: 5px; border: 1px solid #ddd; overflow: auto; }}
                    pre {{ margin: 0; white-space: pre-wrap; word-wrap: break-word; }}
                    .download-btn {{ background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>Reporte Financiero - JSON</h2>
                    <p><strong>Cliente:</strong> {reporte.cierre.cliente.nombre}</p>
                    <p><strong>Período:</strong> {reporte.cierre.periodo}</p>
                    <p><strong>Tipo:</strong> {reporte.get_tipo_reporte_display()}</p>
                    <p><strong>Estado:</strong> {reporte.get_estado_display()}</p>
                    <a href="/admin/contabilidad/reportefinanciero/{reporte.id}/descargar-json/" class="download-btn">
                        Descargar como archivo JSON
                    </a>
                </div>
                <div class="json-container">
                    <pre>{json_formateado}</pre>
                </div>
            </body>
            </html>
            """
            
            return HttpResponse(html_content, content_type='text/html; charset=utf-8')
            
        except Exception as e:
            return HttpResponse(f"Error al mostrar el JSON: {str(e)}", status=500)
    
    def reenviar_cache_individual(self, request, object_id):
        """Vista para reenviar un reporte individual al caché"""
        from django.shortcuts import redirect
        from django.contrib import messages
        from .tasks import enviar_reporte_a_cache
        
        try:
            reporte = self.get_object(request, object_id)
            if not reporte:
                messages.error(request, "Reporte no encontrado")
                return redirect('admin:contabilidad_reportefinanciero_changelist')
            
            # Validar que el reporte esté completado
            if reporte.estado != 'completado':
                messages.error(request, f"El reporte #{reporte.id} no está completado y no se puede reenviar al caché")
                return redirect('admin:contabilidad_reportefinanciero_changelist')
            
            if not reporte.datos_reporte:
                messages.error(request, f"El reporte #{reporte.id} no tiene datos y no se puede reenviar al caché")
                return redirect('admin:contabilidad_reportefinanciero_changelist')
            
            # Enviar al caché
            enviar_reporte_a_cache.delay(reporte.id)
            
            messages.success(
                request, 
                f"Reporte #{reporte.id} ({reporte.get_tipo_reporte_display()}) enviado al caché para procesamiento. "
                f"Cliente: {reporte.cierre.cliente.nombre}, Período: {reporte.cierre.periodo}"
            )
            
            return redirect('admin:contabilidad_reportefinanciero_changelist')
            
        except Exception as e:
            messages.error(request, f"Error al reenviar el reporte al caché: {str(e)}")
            return redirect('admin:contabilidad_reportefinanciero_changelist')
