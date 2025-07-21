"""
Configuración del Admin para Nueva Arquitectura de Nómina SGM
===========================================================

Admin interface para modelos rediseñados centrados en CierreNomina:
- CierreNomina: Vista principal con estados y fechas del ciclo
- EmpleadoNomina/EmpleadoConcepto: Gestión de empleados y conceptos
- Incidencias: Sistema de foro para resolver diferencias
- KPIs: Visualización de métricas pre-calculadas
- Herramientas de optimización y análisis

Autor: Sistema SGM - Módulo Nómina  
Fecha: 20 de julio de 2025
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    # Modelos principales
    CierreNomina,
    EmpleadoNomina,
    EmpleadoConcepto,
    Ausentismo,
    Incidencia,
    InteraccionIncidencia,
    
    # KPIs y optimizaciones
    KPINomina,
    EmpleadoOfuscado,
    LogAccesoOfuscacion,
    IndiceEmpleadoBusqueda,
    ComparacionMensual,
    CacheConsultas,
    
    # Mapeos y utilidades
    MapeoConcepto,
    MapeoNovedades,
    LogArchivo,
)

# ========== ADMIN CIERRE NOMINA (PRINCIPAL) ==========

class EmpleadoNominaInline(admin.TabularInline):
    """Inline para mostrar empleados en el cierre"""
    model = EmpleadoNomina
    extra = 0
    readonly_fields = ('rut_empleado', 'nombre_empleado', 'tipo_empleado', 'fecha_consolidacion')
    fields = ('rut_empleado', 'nombre_empleado', 'tipo_empleado', 'fecha_consolidacion')
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(CierreNomina)
class CierreNominaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'periodo', 'cliente', 'estado_badge', 'analista_responsable',
        'total_empleados_display', 'fecha_creacion', 'fecha_consolidacion',
        'acciones_rapidas'
    ]
    list_filter = [
        'estado', 'fecha_creacion', 'fecha_consolidacion', 'cliente',
        'analista_responsable'
    ]
    search_fields = [
        'periodo', 'cliente__nombre', 'analista_responsable__correo_bdo'
    ]
    readonly_fields = [
        'cache_key_redis', 'total_empleados_activos', 'total_finiquitos',
        'total_ingresos', 'discrepancias_detectadas', 'version',
        'fecha_creacion', 'fecha_consolidacion', 'fecha_cierre',
        'fecha_reapertura'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'periodo', 'analista_responsable', 'estado')
        }),
        ('Contadores Automáticos', {
            'fields': ('total_empleados_activos', 'total_finiquitos', 'total_ingresos', 'discrepancias_detectadas'),
            'classes': ('collapse',)
        }),
        ('Control de Fechas', {
            'fields': ('fecha_creacion', 'fecha_consolidacion', 'fecha_cierre', 'fecha_reapertura'),
            'classes': ('collapse',)
        }),
        ('Técnico', {
            'fields': ('version', 'cache_key_redis', 'archivos_procesados'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones', 'motivo_reapertura'),
        }),
    )
    
    inlines = [EmpleadoNominaInline]
    
    def estado_badge(self, obj):
        """Badge colorido para el estado"""
        colors = {
            'iniciado': 'blue',
            'en_redis': 'orange',
            'validado': 'green',
            'con_discrepancias': 'red',
            'consolidado': 'purple',
            'cerrado': 'gray',
            'error': 'red',
            'reabierto': 'orange'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'
    
    def total_empleados_display(self, obj):
        """Display del total de empleados con link"""
        count = obj.empleados_nomina.count()
        if count > 0:
            url = reverse('admin:nomina_empleadonumina_changelist') + f'?cierre__id={obj.id}'
            return format_html('<a href="{}">{} empleados</a>', url, count)
        return '0 empleados'
    total_empleados_display.short_description = 'Empleados'
    
    def acciones_rapidas(self, obj):
        """Acciones rápidas para el cierre"""
        actions = []
        
        # Botón para ver KPIs
        kpis_count = obj.kpis_calculados.count()
        if kpis_count > 0:
            kpis_url = reverse('admin:nomina_kpinomina_changelist') + f'?cierre__id={obj.id}'
            actions.append(f'<a href="{kpis_url}" style="margin-right: 5px;">📊 {kpis_count} KPIs</a>')
        
        # Botón para ver incidencias
        incidencias_count = obj.incidencias.count()
        if incidencias_count > 0:
            inc_url = reverse('admin:nomina_incidencia_changelist') + f'?cierre__id={obj.id}'
            actions.append(f'<a href="{inc_url}" style="margin-right: 5px;">⚠️ {incidencias_count} incidencias</a>')
        
        return format_html(' | '.join(actions)) if actions else 'Sin acciones'
    acciones_rapidas.short_description = 'Acciones'

# ========== ADMIN EMPLEADOS Y CONCEPTOS ==========

class EmpleadoConceptoInline(admin.TabularInline):
    """Inline para conceptos del empleado"""
    model = EmpleadoConcepto
    extra = 0
    readonly_fields = ('concepto', 'valor', 'valor_numerico', 'fecha_consolidacion')
    fields = ('concepto', 'valor', 'valor_numerico', 'fecha_consolidacion')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(EmpleadoNomina)
class EmpleadoNominaAdmin(admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_empleado', 'cierre', 'tipo_empleado',
        'conceptos_count', 'fecha_consolidacion'
    ]
    list_filter = [
        'tipo_empleado', 'cierre__cliente', 'cierre__periodo',
        'fecha_consolidacion'
    ]
    search_fields = [
        'rut_empleado', 'nombre_empleado', 'cierre__periodo'
    ]
    readonly_fields = [
        'fecha_consolidacion', 'conceptos_resumen'
    ]
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('cierre', 'rut_empleado', 'nombre_empleado', 'tipo_empleado')
        }),
        ('Fechas Específicas', {
            'fields': ('fecha_ingreso', 'fecha_finiquito', 'motivo_finiquito'),
            'classes': ('collapse',)
        }),
        ('Resumen de Conceptos', {
            'fields': ('conceptos_resumen',),
            'classes': ('collapse',)
        }),
        ('Control', {
            'fields': ('fecha_consolidacion',)
        }),
    )
    
    inlines = [EmpleadoConceptoInline]
    
    def conceptos_count(self, obj):
        """Contador de conceptos"""
        return obj.conceptos.count()
    conceptos_count.short_description = 'Conceptos'
    
    def conceptos_resumen(self, obj):
        """Resumen de conceptos por clasificación"""
        if not obj.id:
            return "Guarde primero para ver el resumen"
        
        # Obtener mapeos de clasificación
        mapeos = {}
        try:
            mapeos_obj = MapeoConcepto.objects.filter(
                cliente=obj.cierre.cliente, activo=True
            ).select_related()
            mapeos = {m.concepto_original: m.clasificacion for m in mapeos_obj}
        except:
            pass
        
        # Agrupar conceptos por clasificación
        clasificaciones = {}
        for concepto in obj.conceptos.all():
            clasificacion = mapeos.get(concepto.concepto, 'sin_clasificar')
            if clasificacion not in clasificaciones:
                clasificaciones[clasificacion] = {'total': 0, 'count': 0}
            clasificaciones[clasificacion]['total'] += float(concepto.valor_numerico)
            clasificaciones[clasificacion]['count'] += 1
        
        # Generar HTML del resumen
        html_parts = []
        for clasificacion, data in clasificaciones.items():
            html_parts.append(
                f"<strong>{clasificacion.replace('_', ' ').title()}:</strong> "
                f"{data['count']} conceptos, ${data['total']:,.0f}"
            )
        
        return format_html('<br>'.join(html_parts)) if html_parts else 'Sin conceptos'
    conceptos_resumen.short_description = 'Resumen por Clasificación'

@admin.register(EmpleadoConcepto)
class EmpleadoConceptoAdmin(admin.ModelAdmin):
    list_display = ['empleado_nomina', 'concepto', 'valor', 'valor_numerico', 'fecha_consolidacion']
    list_filter = ['fecha_consolidacion', 'empleado_nomina__cierre__cliente']
    search_fields = ['empleado_nomina__rut_empleado', 'empleado_nomina__nombre_empleado', 'concepto']
    readonly_fields = ['fecha_consolidacion']

# ========== ADMIN INCIDENCIAS ==========

class InteraccionIncidenciaInline(admin.TabularInline):
    """Inline para interacciones de incidencias"""
    model = InteraccionIncidencia
    extra = 0
    readonly_fields = ('usuario', 'fecha_interaccion', 'tipo_interaccion')
    fields = ('usuario', 'fecha_interaccion', 'tipo_interaccion', 'mensaje')
    
    def has_add_permission(self, request, obj=None):
        return True  # Permitir agregar comentarios

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_nombre', 'concepto_afectado', 'cierre', 'tipo_incidencia',
        'estado_badge', 'diferencia_display', 'fecha_deteccion', 'asignaciones'
    ]
    list_filter = [
        'estado', 'tipo_incidencia', 'cierre__cliente', 'cierre__periodo',
        'analista_asignado', 'supervisor_asignado'
    ]
    search_fields = [
        'empleado_rut', 'empleado_nombre', 'concepto_afectado'
    ]
    readonly_fields = [
        'fecha_deteccion', 'diferencia_absoluta', 'diferencia_porcentual',
        'fecha_resolucion'
    ]
    
    fieldsets = (
        ('Información de la Incidencia', {
            'fields': ('cierre', 'empleado_rut', 'empleado_nombre', 'concepto_afectado')
        }),
        ('Análisis Comparativo', {
            'fields': ('valor_periodo_anterior', 'valor_periodo_actual', 
                      'diferencia_absoluta', 'diferencia_porcentual')
        }),
        ('Clasificación', {
            'fields': ('tipo_incidencia', 'estado')
        }),
        ('Asignaciones', {
            'fields': ('analista_asignado', 'supervisor_asignado')
        }),
        ('Resolución', {
            'fields': ('fecha_resolucion', 'usuario_resolucion', 'observaciones_resolucion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [InteraccionIncidenciaInline]
    
    def estado_badge(self, obj):
        """Badge para el estado de la incidencia"""
        colors = {
            'pendiente': 'red',
            'en_revision': 'orange',
            'escalada': 'blue',
            'resuelta': 'green',
            'descartada': 'gray'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'
    
    def diferencia_display(self, obj):
        """Display de la diferencia con formato"""
        if obj.diferencia_porcentual:
            return format_html(
                '${:,.0f} ({:+.1f}%)',
                abs(obj.diferencia_absoluta), obj.diferencia_porcentual
            )
        return format_html('${:,.0f}', abs(obj.diferencia_absoluta))
    diferencia_display.short_description = 'Diferencia'
    
    def asignaciones(self, obj):
        """Display de asignaciones"""
        asignaciones = []
        if obj.analista_asignado:
            asignaciones.append(f"A: {obj.analista_asignado.get_full_name()}")
        if obj.supervisor_asignado:
            asignaciones.append(f"S: {obj.supervisor_asignado.get_full_name()}")
        return ' | '.join(asignaciones) if asignaciones else 'Sin asignar'
    asignaciones.short_description = 'Asignado a'

# ========== ADMIN AUSENTISMO ==========

@admin.register(Ausentismo)
class AusentismoAdmin(admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_empleado', 'tipo_ausentismo', 'fecha_inicio', 
        'fecha_fin', 'dias_ausentismo', 'cierre', 'fecha_consolidacion'
    ]
    list_filter = [
        'tipo_ausentismo', 'cierre__cliente', 'cierre__periodo', 'fecha_consolidacion'
    ]
    search_fields = [
        'rut_empleado', 'nombre_empleado', 'tipo_ausentismo'
    ]
    readonly_fields = ['fecha_consolidacion', 'dias_ausentismo']
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('cierre', 'rut_empleado', 'nombre_empleado')
        }),
        ('Datos del Ausentismo', {
            'fields': ('tipo_ausentismo', 'fecha_inicio', 'fecha_fin', 'dias_ausentismo')
        }),
        ('Detalles Adicionales', {
            'fields': ('observaciones',)
        }),
        ('Control', {
            'fields': ('fecha_consolidacion',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related(
            'cierre',
            'cierre__cliente'
        )

# Registrar modelos simples sin personalización especial
admin.site.register(LogArchivo)
admin.site.register(LogAccesoOfuscacion)
admin.site.register(EmpleadoOfuscado)
admin.site.register(InteraccionIncidencia)
admin.site.register(KPINomina)
admin.site.register(MapeoConcepto)
admin.site.register(MapeoNovedades)
admin.site.register(ComparacionMensual)
admin.site.register(IndiceEmpleadoBusqueda)
admin.site.register(CacheConsultas)

# Configuración del sitio admin
admin.site.site_header = "SGM - Administración Nómina"
admin.site.site_title = "SGM Nómina"
admin.site.index_title = "Panel de Administración - Nueva Arquitectura"
