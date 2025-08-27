from django.contrib import admin
from django.utils import timezone
from .models import (
    CierrePayroll, 
    ArchivoSubido,
    ListaEmpleados_stg,
    ItemsRemuneraciones_stg,
    ValorItemEmpleado_stg,
)
from .models.models_staging import (
    AltasBajas_stg,
    Ausencias_stg,
    Finiquitos_analista_stg,
    Ausentismos_analista_stg,
    Ingresos_analista_stg,
)
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
        'cierre', 'tipo_archivo', 'estado', 'estado_procesamiento', 'nombre_original', 
        'tamaño_mb', 'registros_procesados', 'errores_detectados',
        'fecha_subida'
    ]
    list_filter = ['tipo_archivo', 'estado', 'estado_procesamiento', 'fecha_subida', 'cierre__cliente']
    search_fields = ['nombre_original', 'cierre__cliente__nombre', 'cierre__periodo']
    readonly_fields = ['id', 'hash_md5', 'tamaño', 'fecha_subida', 'fecha_procesamiento']
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('id', 'cierre', 'tipo_archivo', 'estado', 'estado_procesamiento', 'nombre_original', 'archivo')
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


# =============================================================================
# ADMIN PARA MODELOS STAGING
# =============================================================================

@admin.register(ListaEmpleados_stg)
class ListaEmpleadosStgAdmin(admin.ModelAdmin):
    list_display = [
        'rut_trabajador', 'nombre', 'apellido_paterno', 'apellido_materno',
        'archivo_subido', 'fila_excel', 'fecha_extraccion'
    ]
    list_filter = ['archivo_subido__tipo_archivo', 'archivo_subido__cierre__cliente', 'fecha_extraccion']
    search_fields = ['rut_trabajador', 'nombre', 'apellido_paterno', 'apellido_materno']
    readonly_fields = ['fecha_extraccion']
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('rut_trabajador', 'nombre', 'apellido_paterno', 'apellido_materno')
        }),
        ('Trazabilidad', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_extraccion')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')


@admin.register(ItemsRemuneraciones_stg)
class ItemsRemuneracionesStgAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_columna', 'nombre_concepto', 'tipo_concepto', 'orden',
        'archivo_subido', 'fecha_extraccion'
    ]
    list_filter = ['tipo_concepto', 'archivo_subido__tipo_archivo', 'archivo_subido__cierre__cliente']
    search_fields = ['nombre_concepto', 'nombre_normalizado', 'codigo_columna']
    readonly_fields = ['fecha_extraccion']
    ordering = ['archivo_subido', 'orden']
    
    fieldsets = (
        ('Información del Concepto', {
            'fields': ('codigo_columna', 'nombre_concepto', 'nombre_normalizado', 'tipo_concepto')
        }),
        ('Ubicación en Excel', {
            'fields': ('orden', 'fila_header')
        }),
        ('Trazabilidad', {
            'fields': ('archivo_subido', 'fecha_extraccion')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')


@admin.register(ValorItemEmpleado_stg)
class ValorItemEmpleadoStgAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_rut', 'item_concepto', 'valor_original', 'valor_numerico', 
        'valor_texto', 'es_numerico', 'fila_excel', 'columna_excel'
    ]
    list_filter = [
        'es_numerico', 'archivo_subido__tipo_archivo', 
        'archivo_subido__cierre__cliente', 'item_remuneracion__tipo_concepto'
    ]
    search_fields = [
        'empleado__rut_trabajador', 'empleado__nombre', 
        'item_remuneracion__nombre_concepto', 'valor_original'
    ]
    readonly_fields = ['fecha_extraccion']
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('archivo_subido', 'empleado', 'item_remuneracion')
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_numerico', 'valor_texto', 'es_numerico')
        }),
        ('Ubicación en Excel', {
            'fields': ('fila_excel', 'columna_excel')
        }),
        ('Trazabilidad', {
            'fields': ('fecha_extraccion',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        })
    )
    
    def empleado_rut(self, obj):
        return obj.empleado.rut_trabajador
    empleado_rut.short_description = "RUT Empleado"
    empleado_rut.admin_order_field = 'empleado__rut_trabajador'
    
    def item_concepto(self, obj):
        return f"[{obj.item_remuneracion.codigo_columna}] {obj.item_remuneracion.nombre_concepto[:30]}..."
    item_concepto.short_description = "Concepto"
    item_concepto.admin_order_field = 'item_remuneracion__nombre_concepto'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'empleado', 'item_remuneracion', 'archivo_subido__cierre__cliente'
        )


# =============================================================================
# ADMIN PARA MODELOS STAGING - MOVIMIENTOS DEL MES
# =============================================================================

@admin.register(AltasBajas_stg)
class AltasBajasStgAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'rut', 'empresa', 'cargo', 'alta_baja', 
        'fecha_ingreso', 'fecha_retiro', 'sueldo_base', 'archivo_subido'
    ]
    list_filter = [
        'alta_baja', 'empresa', 'cargo', 'centro_de_costo', 
        'archivo_subido__cierre__cliente', 'fecha_extraccion', 'tiene_errores'
    ]
    search_fields = [
        'nombre', 'rut', 'empresa', 'cargo', 'centro_de_costo', 'sucursal'
    ]
    readonly_fields = ['fecha_extraccion', 'fila_excel']
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('nombre', 'rut', 'empresa', 'cargo', 'centro_de_costo', 'sucursal')
        }),
        ('Información del Movimiento', {
            'fields': ('alta_baja', 'fecha_ingreso', 'fecha_retiro', 'tipo_contrato', 'motivo')
        }),
        ('Información Económica', {
            'fields': ('sueldo_base', 'sueldo_base_raw', 'dias_trabajados', 'dias_trabajados_raw')
        }),
        ('Trazabilidad', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_extraccion')
        }),
        ('Procesamiento', {
            'fields': ('tiene_errores', 'errores_detectados', 'observaciones_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')
    
    def sueldo_formateado(self, obj):
        if obj.sueldo_base:
            return f"${obj.sueldo_base:,.0f}"
        return obj.sueldo_base_raw or "N/A"
    sueldo_formateado.short_description = "Sueldo Base"
    
    def color_alta_baja(self, obj):
        if obj.alta_baja == 'Alta':
            return f'<span style="color: green; font-weight: bold;">{obj.alta_baja}</span>'
        elif obj.alta_baja == 'Baja':
            return f'<span style="color: red; font-weight: bold;">{obj.alta_baja}</span>'
        return obj.alta_baja
    color_alta_baja.allow_tags = True
    color_alta_baja.short_description = "Tipo"


@admin.register(Ausencias_stg)
class AusenciasStgAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'rut', 'empresa', 'cargo', 'tipo_de_ausentismo',
        'fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias', 'archivo_subido'
    ]
    list_filter = [
        'tipo_de_ausentismo', 'empresa', 'cargo', 'centro_de_costo',
        'archivo_subido__cierre__cliente', 'fecha_extraccion', 'tiene_errores'
    ]
    search_fields = [
        'nombre', 'rut', 'empresa', 'cargo', 'centro_de_costo', 
        'sucursal', 'tipo_de_ausentismo', 'motivo'
    ]
    readonly_fields = ['fecha_extraccion', 'fila_excel']
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('nombre', 'rut', 'empresa', 'cargo', 'centro_de_costo', 'sucursal')
        }),
        ('Información de la Ausencia', {
            'fields': ('tipo_de_ausentismo', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias')
        }),
        ('Detalles', {
            'fields': ('motivo', 'observaciones')
        }),
        ('Trazabilidad', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_extraccion')
        }),
        ('Procesamiento', {
            'fields': ('tiene_errores', 'errores_detectados', 'observaciones_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')
    
    def duracion_ausencia(self, obj):
        if obj.dias:
            if obj.dias == 1:
                return f"1 día"
            else:
                return f"{obj.dias} días"
        return "N/A"
    duracion_ausencia.short_description = "Duración"
    
    def tipo_color(self, obj):
        colores = {
            'Licencia Médica': 'red',
            'Vacaciones': 'blue',
            'Permiso Personal': 'orange',
            'Capacitación': 'green',
            'Licencia Maternal/Paternal': 'purple'
        }
        color = colores.get(obj.tipo_de_ausentismo, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.tipo_de_ausentismo}</span>'
    tipo_color.allow_tags = True
    tipo_color.short_description = "Tipo de Ausencia"


# ==============================================
# ADMIN PARA MODELOS STAGING DEL ANALISTA
# ==============================================

@admin.register(Finiquitos_analista_stg)
class FiniquitosAnalistaStgAdmin(admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'fecha_retiro', 'motivo_corto', 
        'archivo_subido', 'fila_excel', 'fecha_procesamiento'
    ]
    list_filter = [
        'fecha_retiro', 'fecha_procesamiento', 
        'archivo_subido__cierre__cliente', 'archivo_subido__cierre__periodo'
    ]
    search_fields = ['rut', 'nombre', 'motivo']
    readonly_fields = ['fecha_procesamiento']
    date_hierarchy = 'fecha_retiro'
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('rut', 'nombre')
        }),
        ('Detalles del Finiquito', {
            'fields': ('fecha_retiro', 'motivo')
        }),
        ('Metadatos', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    def motivo_corto(self, obj):
        if obj.motivo and len(obj.motivo) > 50:
            return obj.motivo[:50] + "..."
        return obj.motivo or "Sin motivo"
    motivo_corto.short_description = "Motivo"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')


@admin.register(Ausentismos_analista_stg)
class AusentismosAnalistaStgAdmin(admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 
        'duracion_dias', 'tipo_ausentismo_simple', 'archivo_subido', 'fila_excel'
    ]
    list_filter = [
        'tipo_ausentismo', 'fecha_inicio_ausencia', 'fecha_procesamiento',
        'archivo_subido__cierre__cliente', 'archivo_subido__cierre__periodo'
    ]
    search_fields = ['rut', 'nombre', 'tipo_ausentismo']
    readonly_fields = ['fecha_procesamiento', 'duracion_calculada']
    date_hierarchy = 'fecha_inicio_ausencia'
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('rut', 'nombre')
        }),
        ('Detalles de la Ausencia', {
            'fields': ('fecha_inicio_ausencia', 'fecha_fin_ausencia', 'dias', 'duracion_calculada', 'tipo_ausentismo')
        }),
        ('Metadatos', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    def duracion_dias(self, obj):
        duracion = obj.duracion_calculada
        if duracion:
            if duracion == 1:
                return "1 día"
            else:
                return f"{duracion} días"
        return "N/A"
    duracion_dias.short_description = "Duración"
    
    def tipo_ausentismo_simple(self, obj):
        return obj.tipo_ausentismo or "Sin especificar"
    tipo_ausentismo_simple.short_description = "Tipo de Ausentismo"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')


@admin.register(Ingresos_analista_stg)
class IngresosAnalistaStgAdmin(admin.ModelAdmin):
    list_display = [
        'rut', 'nombre', 'fecha_ingreso', 'dias_desde_ingreso',
        'archivo_subido', 'fila_excel', 'fecha_procesamiento'
    ]
    list_filter = [
        'fecha_ingreso', 'fecha_procesamiento',
        'archivo_subido__cierre__cliente', 'archivo_subido__cierre__periodo'
    ]
    search_fields = ['rut', 'nombre']
    readonly_fields = ['fecha_procesamiento', 'dias_desde_ingreso']
    date_hierarchy = 'fecha_ingreso'
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('rut', 'nombre')
        }),
        ('Detalles del Ingreso', {
            'fields': ('fecha_ingreso', 'dias_desde_ingreso')
        }),
        ('Metadatos', {
            'fields': ('archivo_subido', 'fila_excel', 'fecha_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    def dias_desde_ingreso(self, obj):
        if obj.fecha_ingreso:
            desde_ingreso = (timezone.now().date() - obj.fecha_ingreso).days
            if desde_ingreso == 0:
                return "Hoy"
            elif desde_ingreso == 1:
                return "1 día"
            elif desde_ingreso > 0:
                return f"{desde_ingreso} días"
            else:
                return f"Futuro ({abs(desde_ingreso)} días)"
        return "Sin fecha"
    dias_desde_ingreso.short_description = "Días desde ingreso"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivo_subido__cierre__cliente')
