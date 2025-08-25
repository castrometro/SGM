from django.contrib import admin
from .models import CierrePayroll, ArchivoSubido
# from .models import DiscrepanciaDetectada  # Comentado hasta implementar fase de discrepancias


@admin.register(CierrePayroll)
class CierrePayrollAdmin(admin.ModelAdmin):
    list_display = [
        'cliente', 'periodo', 'estado', 'fecha_inicio', 'fecha_termino'
    ]
    list_filter = ['estado', 'fecha_inicio', 'cliente']
    search_fields = ['cliente__nombre', 'periodo']
    readonly_fields = ['id', 'fecha_inicio']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'cliente', 'periodo', 'estado', 'usuario_responsable')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_termino')
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando objeto existente
            return self.readonly_fields + ['cliente', 'periodo']
        return self.readonly_fields


@admin.register(ArchivoSubido)
class ArchivoSubidoAdmin(admin.ModelAdmin):
    list_display = [
        'cierre', 'tipo_archivo', 'estado', 'nombre_original', 
        'tamaño_mb', 'registros_procesados', 'errores_detectados',
        'fecha_subida'
    ]
    list_filter = ['tipo_archivo', 'estado', 'fecha_subida', 'cierre__cliente']
    search_fields = ['nombre_original', 'cierre__cliente__nombre', 'cierre__periodo']
    readonly_fields = ['id', 'hash_md5', 'tamaño', 'fecha_subida', 'fecha_procesamiento']
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('id', 'cierre', 'tipo_archivo', 'estado', 'nombre_original', 'archivo')
        }),
        ('Metadatos', {
            'fields': ('hash_md5', 'tamaño', 'fecha_subida', 'fecha_procesamiento')
        }),
        ('Procesamiento', {
            'fields': ('registros_procesados', 'errores_detectados', 'metadatos', 'log_errores'),
            'classes': ('collapse',)
        })
    )
    
    def tamaño_mb(self, obj):
        if obj.tamaño:
            return f"{obj.tamaño / (1024*1024):.2f} MB"
        return "0 MB"
    tamaño_mb.short_description = "Tamaño"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando objeto existente
            return self.readonly_fields + ['cierre', 'tipo_archivo', 'archivo']
        return self.readonly_fields


# Comentado hasta implementar fase de discrepancias
# @admin.register(DiscrepanciaDetectada)
# class DiscrepanciaDetectadaAdmin(admin.ModelAdmin):
#     list_display = [
#         'cierre', 'tipo', 'gravedad', 'empleado_codigo', 
#         'concepto_codigo', 'resuelta', 'fecha_deteccion'
#     ]
#     list_filter = ['tipo', 'gravedad', 'resuelta', 'fecha_deteccion', 'cierre__cliente']
#     search_fields = [
#         'descripcion', 'empleado_codigo', 'concepto_codigo', 
#         'cierre__cliente__nombre', 'cierre__periodo'
#     ]
#     readonly_fields = ['id', 'fecha_deteccion', 'fecha_resolucion']
#     
#     fieldsets = (
#         ('Información de la Discrepancia', {
#             'fields': ('id', 'cierre', 'tipo', 'gravedad', 'descripcion')
#         }),
#         ('Archivos Relacionados', {
#             'fields': ('archivo_talana', 'archivo_analista')
#         }),
#         ('Detalles', {
#             'fields': ('empleado_codigo', 'concepto_codigo', 'valor_talana', 'valor_analista')
#         }),
#         ('Resolución', {
#             'fields': ('resuelta', 'fecha_deteccion', 'fecha_resolucion', 
#                       'resolucion_comentario', 'usuario_resolutor')
#         })
#     )
#     
#     actions = ['marcar_como_resueltas', 'marcar_como_no_resueltas']
#     
#     def marcar_como_resueltas(self, request, queryset):
#         queryset.update(resuelta=True)
#         self.message_user(request, f"{queryset.count()} discrepancias marcadas como resueltas.")
#     marcar_como_resueltas.short_description = "Marcar como resueltas"
#     
#     def marcar_como_no_resueltas(self, request, queryset):
#         queryset.update(resuelta=False, fecha_resolucion=None)
#         self.message_user(request, f"{queryset.count()} discrepancias marcadas como no resueltas.")
#     marcar_como_no_resueltas.short_description = "Marcar como no resueltas"
