from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    TipoDocumento, TipoDocumentoArchivo, 
    CuentaContable, CierreContabilidad, LibroMayorUpload,
    AperturaCuenta, MovimientoContable, ClasificacionSet,
    ClasificacionOption, AccountClassification, Incidencia, CentroCosto,
    Auxiliar, BulkClasificacionUpload, ClasificacionCuentaArchivo, NombresEnInglesUpload, TarjetaActivityLog
)

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'codigo', 'descripcion')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('cliente',)

@admin.register(TipoDocumentoArchivo)
class TipoDocumentoArchivoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'archivo_nombre', 'fecha_subida', 'tamaño_archivo')
    list_filter = ('cliente', 'fecha_subida')
    search_fields = ('archivo',)
    readonly_fields = ('fecha_subida',)
    
    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo, no la ruta completa"""
        import os
        return os.path.basename(obj.archivo.name) if obj.archivo else '-'
    archivo_nombre.short_description = "Archivo"
    
    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo en formato legible"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"
    tamaño_archivo.short_description = "Tamaño"

@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'codigo', 'nombre','nombre_en')
    search_fields = ('codigo', 'nombre')
    list_filter = ('cliente',)

@admin.register(CierreContabilidad)
class CierreContabilidadAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'periodo', 'estado', 'usuario', 'fecha_creacion')
    list_filter = ('estado', 'cliente')
    search_fields = ('periodo',)

@admin.register(LibroMayorUpload)
class LibroMayorUploadAdmin(admin.ModelAdmin):
    list_display = ('cierre_info', 'archivo_nombre', 'fecha_subida', 'estado', 'procesado', 'tamaño_archivo')
    list_filter = ('procesado', 'estado', 'fecha_subida')
    search_fields = ('cierre__cliente__nombre', 'cierre__periodo')
    readonly_fields = ('fecha_subida',)
    
    def cierre_info(self, obj):
        """Información del cierre asociado"""
        return f"{obj.cierre.cliente.nombre} - {obj.cierre.periodo}"
    cierre_info.short_description = "Cliente - Período"
    
    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os
        return os.path.basename(obj.archivo.name) if obj.archivo else '-'
    archivo_nombre.short_description = "Archivo"
    
    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"
    tamaño_archivo.short_description = "Tamaño"

@admin.register(AperturaCuenta)
class AperturaCuentaAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'cuenta', 'saldo_anterior')

@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'cuenta', 'debe', 'haber', 'tipo_documento', 'numero_documento', 'tipo', 'numero_comprobante','numero_interno')
    list_filter = ('fecha', 'numero_interno','tipo_documento','cuenta')
    search_fields = ('descripcion',)

@admin.register(ClasificacionSet)
class ClasificacionSetAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre')

@admin.register(ClasificacionOption)
class ClasificacionOptionAdmin(admin.ModelAdmin):
    list_display = ('set_clas', 'valor')

@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'set_clas', 'opcion', 'asignado_por', 'fecha')

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('cierre', 'tipo', 'resuelta', 'fecha_creacion')
    list_filter = ('resuelta', 'tipo')
    search_fields = ('descripcion', 'respuesta')

@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre')
    list_filter = ('cliente',)

@admin.register(Auxiliar)
class AuxiliarAdmin(admin.ModelAdmin):
    list_display = ('rut_auxiliar', 'nombre', 'fecha_creacion')

@admin.register(BulkClasificacionUpload)
class BulkClasificacionUploadAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'archivo_nombre', 'fecha_subida', 'estado', 'resumen_info', 'tamaño_archivo')
    list_filter = ('estado', 'cliente', 'fecha_subida')
    search_fields = ('cliente__nombre', 'archivo')
    readonly_fields = ('fecha_subida', 'resumen')
    
    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os
        return os.path.basename(obj.archivo.name) if obj.archivo else '-'
    archivo_nombre.short_description = "Archivo"
    
    def resumen_info(self, obj):
        """Muestra información del resumen de procesamiento"""
        if obj.resumen:
            clasificaciones = obj.resumen.get('clasificaciones_aplicadas', 0)
            errores = obj.resumen.get('errores_count', 0)
            return f"{clasificaciones} aplicadas, {errores} errores"
        return "-"
    resumen_info.short_description = "Resumen"
    
    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"
    tamaño_archivo.short_description = "Tamaño"
    
    actions = ['reprocesar_archivos']
    
    def reprocesar_archivos(self, request, queryset):
        """Acción para reprocesar archivos seleccionados"""
        from .tasks import procesar_bulk_clasificacion
        count = 0
        for upload in queryset:
            if upload.estado in ['error', 'completado']:
                upload.estado = 'subido'
                upload.errores = ''
                upload.resumen = {}
                upload.save(update_fields=['estado', 'errores', 'resumen'])
                procesar_bulk_clasificacion.delay(upload.id)
                count += 1
        
        self.message_user(
            request,
            f"Se enviaron {count} archivo(s) para reprocesamiento."
        )
    reprocesar_archivos.short_description = "Reprocesar archivos seleccionados"

@admin.register(ClasificacionCuentaArchivo)
class ClasificacionCuentaArchivoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'upload', 'numero_cuenta', 'procesado', 'fila_excel', 'fecha_creacion')
    list_filter = ('procesado', 'cliente', 'upload__estado', 'fecha_creacion')
    search_fields = ('numero_cuenta', 'cliente__nombre')
    readonly_fields = ('fecha_creacion', 'fecha_procesado')
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'upload', 'cuenta_mapeada')

@admin.register(NombresEnInglesUpload)
class NombresEnInglesUploadAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'cierre_info', 'archivo_nombre', 'fecha_subida', 'estado', 'resumen_info', 'tamaño_archivo')
    list_filter = ('estado', 'cliente', 'fecha_subida')
    search_fields = ('cliente__nombre', 'cierre__periodo', 'archivo')
    readonly_fields = ('fecha_subida', 'resumen')
    
    def cierre_info(self, obj):
        """Información del cierre asociado"""
        if obj.cierre:
            return f"{obj.cierre.periodo}"
        return "Sin cierre específico"
    cierre_info.short_description = "Período"
    
    def archivo_nombre(self, obj):
        """Muestra solo el nombre del archivo"""
        import os
        return os.path.basename(obj.archivo.name) if obj.archivo else '-'
    archivo_nombre.short_description = "Archivo"
    
    def resumen_info(self, obj):
        """Muestra información del resumen de procesamiento"""
        if obj.resumen:
            actualizadas = obj.resumen.get('cuentas_actualizadas', 0)
            errores = obj.resumen.get('errores_count', 0)
            return f"{actualizadas} actualizadas, {errores} errores"
        return "-"
    resumen_info.short_description = "Resumen"
    
    def tamaño_archivo(self, obj):
        """Muestra el tamaño del archivo"""
        if obj.archivo:
            try:
                size = obj.archivo.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"
            except:
                return "N/A"
        return "-"
    tamaño_archivo.short_description = "Tamaño"
    
    actions = ['reprocesar_archivos']
    
    def reprocesar_archivos(self, request, queryset):
        """Acción para reprocesar archivos seleccionados"""
        from .tasks import procesar_nombres_ingles_upload
        count = 0
        for upload in queryset:
            if upload.estado in ['error', 'completado']:
                upload.estado = 'subido'
                upload.errores = ''
                upload.resumen = {}
                upload.save(update_fields=['estado', 'errores', 'resumen'])
                procesar_nombres_ingles_upload.delay(upload.id)
                count += 1
        
        self.message_user(
            request,
            f"Se enviaron {count} archivo(s) para reprocesamiento."
        )
    reprocesar_archivos.short_description = "Reprocesar archivos seleccionados"

@admin.register(TarjetaActivityLog)
class TarjetaActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'cliente_display', 'tarjeta', 'accion', 'usuario', 'resultado', 'descripcion_corta')
    list_filter = ('tarjeta', 'accion', 'resultado', 'timestamp')
    search_fields = ('descripcion', 'usuario__username', 'cierre__cliente__nombre')
    readonly_fields = ('timestamp', 'cierre', 'tarjeta', 'accion', 'descripcion', 'usuario', 'detalles', 'resultado', 'ip_address')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def cliente_display(self, obj):
        """Muestra el nombre del cliente del cierre"""
        return obj.cierre.cliente.nombre if obj.cierre and obj.cierre.cliente else '-'
    cliente_display.short_description = "Cliente"
    cliente_display.admin_order_field = 'cierre__cliente__nombre'
    
    def descripcion_corta(self, obj):
        """Muestra una versión corta de la descripción"""
        return obj.descripcion[:60] + "..." if len(obj.descripcion) > 60 else obj.descripcion
    descripcion_corta.short_description = "Descripción"
    
    def get_queryset(self, request):
        """Optimiza las consultas incluyendo relaciones"""
        queryset = super().get_queryset(request)
        return queryset.select_related('cierre', 'cierre__cliente', 'usuario')
    
    # Solo lectura para preservar la integridad de los logs
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Solo superusuarios pueden eliminar logs
