from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Q
from django.utils import timezone
import json

from .models import (
    CierrePayroll,
    Empleados_Cierre,
    Item_Cierre,
    Item_Empleado,
    Finiquitos_Cierre,
    Ingresos_Cierre,
    Ausentismos_Cierre,
    Incidencias_Cierre,
    Logs_Comparacion
)

# ============================================================================
#                         PERSONALIZACIÓN ADMIN SITE
# ============================================================================

admin.site.site_header = "SGM Payroll - Sistema de Gestión de Nóminas"
admin.site.site_title = "SGM Payroll Admin"
admin.site.index_title = "Administración de Cierres Payroll"

# ============================================================================
#                           CIERRE PAYROLL ADMIN
# ============================================================================

@admin.register(CierrePayroll)
class CierrePayrollAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cliente', 'periodo', 'estado_badge', 'usuario', 
        'empleados_count', 'progress_bar', 'fecha_creacion', 'acciones'
    ]
    list_filter = ['estado', 'cliente', 'fecha_creacion']
    search_fields = ['periodo', 'cliente__nombre', 'usuario__username']
    readonly_fields = [
        'fecha_creacion', 'progress_display', 'resumen_datos',
        'incidencias_pendientes', 'logs_recientes'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'periodo', 'usuario', 'fecha_creacion')
        }),
        ('Estado y Progreso', {
            'fields': ('estado', 'progress_display', 'fecha_completado')
        }),
        ('Configuración', {
            'fields': ('porcentaje_tolerancia',)
        }),
        ('Resumen de Datos', {
            'fields': ('total_empleados', 'monto_total', 'resumen_datos'),
            'classes': ('collapse',)
        }),
        ('Incidencias y Logs', {
            'fields': ('incidencias_pendientes', 'logs_recientes'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'usuario').annotate(
            empleados_count=Count('empleados'),
            incidencias_count=Count('incidencias')
        )
    
    def estado_badge(self, obj):
        color = obj.get_estado_display_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def empleados_count(self, obj):
        return obj.empleados_count
    empleados_count.short_description = 'Empleados'
    empleados_count.admin_order_field = 'empleados_count'
    
    def progress_bar(self, obj):
        progress = obj.get_progress_percentage()
        color = '#28a745' if progress >= 75 else '#ffc107' if progress >= 50 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; height: 20px; background-color: {}; '
            'border-radius: 3px; text-align: center; color: white; font-size: 12px; '
            'line-height: 20px;">{:.0f}%</div></div>',
            progress, color, progress
        )
    progress_bar.short_description = 'Progreso'
    
    def acciones(self, obj):
        empleados_url = reverse('admin:payroll_empleados_cierre_changelist') + f'?cierre_payroll__id__exact={obj.id}'
        incidencias_url = reverse('admin:payroll_incidencias_cierre_changelist') + f'?cierre_payroll__id__exact={obj.id}'
        logs_url = reverse('admin:payroll_logs_comparacion_changelist') + f'?cierre_payroll__id__exact={obj.id}'
        
        return format_html(
            '<a href="{}" style="margin-right: 5px;">👥 Empleados</a>'
            '<a href="{}" style="margin-right: 5px;">⚠️ Incidencias</a>'
            '<a href="{}">📋 Logs</a>',
            empleados_url, incidencias_url, logs_url
        )
    acciones.short_description = 'Acciones'
    
    def progress_display(self, obj):
        progress = obj.get_progress_percentage()
        return f"{progress}%"
    progress_display.short_description = 'Progreso Actual'
    
    def resumen_datos(self, obj):
        empleados = obj.empleados.count()
        items = Item_Empleado.objects.filter(empleado_cierre__cierre_payroll=obj).count()
        finiquitos = obj.finiquitos.count()
        ingresos = obj.ingresos.count()
        
        return format_html(
            '<strong>Empleados:</strong> {}<br>'
            '<strong>Items procesados:</strong> {}<br>'
            '<strong>Finiquitos:</strong> {}<br>'
            '<strong>Ingresos:</strong> {}',
            empleados, items, finiquitos, ingresos
        )
    resumen_datos.short_description = 'Resumen de Datos'
    
    def incidencias_pendientes(self, obj):
        incidencias = obj.incidencias.filter(estado_validacion='pendiente')
        if not incidencias.exists():
            return "✅ Sin incidencias pendientes"
        
        html = []
        for inc in incidencias[:5]:  # Mostrar máximo 5
            color = inc.get_color_prioridad()
            html.append(f'<span style="color: {color};">● {inc.get_tipo_incidencia_display()}</span>')
        
        if incidencias.count() > 5:
            html.append(f'<br><em>... y {incidencias.count() - 5} más</em>')
        
        return format_html('<br>'.join(html))
    incidencias_pendientes.short_description = 'Incidencias Pendientes'
    
    def logs_recientes(self, obj):
        logs = obj.logs.order_by('-timestamp')[:3]
        if not logs.exists():
            return "Sin logs recientes"
        
        html = []
        for log in logs:
            color = log.get_color_resultado()
            tiempo = timezone.localtime(log.timestamp).strftime('%d/%m %H:%M')
            html.append(f'<span style="color: {color};">● {log.get_accion_display()} ({tiempo})</span>')
        
        return format_html('<br>'.join(html))
    logs_recientes.short_description = 'Logs Recientes'


# ============================================================================
#                           EMPLEADOS CIERRE ADMIN
# ============================================================================

@admin.register(Empleados_Cierre)
class EmpleadosCierreAdmin(admin.ModelAdmin):
    list_display = [
        'rut_empleado', 'nombre_completo', 'estado_badge', 
        'cargo', 'cierre_info', 'items_count', 'liquido_calculado'
    ]
    list_filter = ['estado_empleado', 'cierre_payroll__cliente', 'cargo']
    search_fields = ['rut_empleado', 'nombre_completo', 'cargo']
    raw_id_fields = ['cierre_payroll']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('cierre_payroll', 'rut_empleado', 'nombre_completo')
        }),
        ('Estado y Cargo', {
            'fields': ('estado_empleado', 'cargo', 'departamento', 'centro_costo')
        }),
        ('Fechas', {
            'fields': ('fecha_ingreso', 'fecha_salida')
        }),
        ('Timestamps', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['creado_en', 'actualizado_en']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cierre_payroll', 'cierre_payroll__cliente'
        ).annotate(
            items_count=Count('items')
        )
    
    def estado_badge(self, obj):
        colors = {
            'activo': '#28a745',
            'nuevo_ingreso': '#17a2b8',
            'finiquito': '#dc3545',
            'licencia': '#ffc107',
            'suspension': '#fd7e14'
        }
        color = colors.get(obj.estado_empleado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_estado_empleado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def cierre_info(self, obj):
        return f"{obj.cierre_payroll.cliente.nombre} - {obj.cierre_payroll.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = 'Items'
    items_count.admin_order_field = 'items_count'
    
    def liquido_calculado(self, obj):
        try:
            liquido = obj.get_liquido_pagado()
            return f"${liquido:,.0f}"
        except:
            return "N/A"
    liquido_calculado.short_description = 'Líquido'


# ============================================================================
#                           ITEM CIERRE ADMIN
# ============================================================================

@admin.register(Item_Cierre)
class ItemCierreAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_item', 'nombre_item', 'tipo_badge', 'cierre_info',
        'es_imponible', 'es_variable', 'empleados_con_item', 'total_monto'
    ]
    list_filter = ['tipo_item', 'es_imponible', 'es_variable', 'cierre_payroll__cliente']
    search_fields = ['codigo_item', 'nombre_item']
    raw_id_fields = ['cierre_payroll']
    
    def tipo_badge(self, obj):
        colors = {
            'haberes': '#28a745',
            'descuentos': '#dc3545',
            'aportes': '#17a2b8',
            'informativos': '#6c757d'
        }
        color = colors.get(obj.tipo_item, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_tipo_item_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def cierre_info(self, obj):
        return f"{obj.cierre_payroll.cliente.nombre} - {obj.cierre_payroll.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def empleados_con_item(self, obj):
        return obj.get_empleados_count()
    empleados_con_item.short_description = 'Empleados'
    
    def total_monto(self, obj):
        total = obj.get_total_monto()
        return f"${total:,.0f}"
    total_monto.short_description = 'Total'


# ============================================================================
#                           ITEM EMPLEADO ADMIN
# ============================================================================

@admin.register(Item_Empleado)
class ItemEmpleadoAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_nombre', 'item_codigo', 'monto_formateado', 
        'cantidad', 'origen_badge', 'variacion_info'
    ]
    list_filter = [
        'origen_dato', 'item_cierre__tipo_item', 
        'empleado_cierre__cierre_payroll__cliente'
    ]
    search_fields = [
        'empleado_cierre__nombre_completo', 
        'item_cierre__codigo_item',
        'empleado_cierre__rut_empleado'
    ]
    raw_id_fields = ['empleado_cierre', 'item_cierre']
    
    def empleado_nombre(self, obj):
        return obj.empleado_cierre.nombre_completo
    empleado_nombre.short_description = 'Empleado'
    
    def item_codigo(self, obj):
        return obj.item_cierre.codigo_item
    item_codigo.short_description = 'Item'
    
    def monto_formateado(self, obj):
        return f"${obj.monto:,.0f}"
    monto_formateado.short_description = 'Monto'
    
    def origen_badge(self, obj):
        colors = {
            'talana': '#28a745',
            'analista': '#17a2b8',
            'manual': '#ffc107',
            'calculado': '#6f42c1'
        }
        color = colors.get(obj.origen_dato, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_origen_dato_display()
        )
    origen_badge.short_description = 'Origen'
    
    def variacion_info(self, obj):
        try:
            variacion = obj.calcular_variacion_porcentual()
            if variacion is None:
                return "Nuevo"
            
            color = '#dc3545' if abs(variacion) > 20 else '#ffc107' if abs(variacion) > 10 else '#28a745'
            signo = '+' if variacion > 0 else ''
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}{:.1f}%</span>',
                color, signo, variacion
            )
        except:
            return "N/A"
    variacion_info.short_description = 'Variación'


# ============================================================================
#                           INCIDENCIAS ADMIN
# ============================================================================

@admin.register(Incidencias_Cierre)
class IncidenciasCierreAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_item', 'tipo_badge', 'prioridad_badge', 
        'variacion_display', 'estado_badge', 'asignado_a', 'fecha_deteccion'
    ]
    list_filter = [
        'tipo_incidencia', 'prioridad', 'estado_validacion',
        'cierre_payroll__cliente', 'fecha_deteccion'
    ]
    search_fields = [
        'item_empleado_actual__empleado_cierre__nombre_completo',
        'explicacion', 'accion_tomada'
    ]
    raw_id_fields = [
        'item_empleado_actual', 'item_empleado_anterior',
        'asignado_a', 'validado_por'
    ]
    
    actions = ['asignar_a_mi', 'marcar_como_validada']
    
    def empleado_item(self, obj):
        empleado = obj.get_empleado_nombre()
        item = obj.get_item_codigo()
        return f"{empleado} - {item}"
    empleado_item.short_description = 'Empleado - Item'
    
    def tipo_badge(self, obj):
        colors = {
            'variacion_significativa': '#dc3545',
            'empleado_nuevo': '#17a2b8',
            'empleado_salida': '#fd7e14',
            'item_nuevo': '#28a745',
            'valor_cero': '#6c757d'
        }
        color = colors.get(obj.tipo_incidencia, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_tipo_incidencia_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def prioridad_badge(self, obj):
        color = obj.get_color_prioridad()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_prioridad_display().upper()
        )
    prioridad_badge.short_description = 'Prioridad'
    
    def estado_badge(self, obj):
        color = obj.get_color_estado()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_estado_validacion_display()
        )
    estado_badge.short_description = 'Estado'
    
    def variacion_display(self, obj):
        return obj.get_resumen_variacion()
    variacion_display.short_description = 'Variación'
    
    def asignar_a_mi(self, request, queryset):
        count = queryset.update(
            asignado_a=request.user,
            fecha_asignacion=timezone.now(),
            estado_validacion='en_revision'
        )
        self.message_user(request, f'{count} incidencias asignadas a ti.')
    asignar_a_mi.short_description = 'Asignar a mí'
    
    def marcar_como_validada(self, request, queryset):
        count = queryset.update(
            estado_validacion='validada',
            validado_por=request.user,
            fecha_validacion=timezone.now()
        )
        self.message_user(request, f'{count} incidencias marcadas como validadas.')
    marcar_como_validada.short_description = 'Marcar como validada'


# ============================================================================
#                           OTROS ADMINS
# ============================================================================

@admin.register(Finiquitos_Cierre)
class FiniquitosCierreAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_nombre', 'fecha_finiquito', 'motivo_salida',
        'monto_formateado', 'estado_badge'
    ]
    list_filter = ['motivo_salida', 'estado_finiquito', 'fecha_finiquito']
    search_fields = ['empleado_cierre__nombre_completo']
    raw_id_fields = ['empleado_cierre', 'aprobado_por']
    
    def empleado_nombre(self, obj):
        return obj.empleado_cierre.nombre_completo
    empleado_nombre.short_description = 'Empleado'
    
    def monto_formateado(self, obj):
        return f"${obj.monto_finiquito:,.0f}"
    monto_formateado.short_description = 'Monto'
    
    def estado_badge(self, obj):
        color = obj.get_color_estado()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_estado_finiquito_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Ingresos_Cierre)
class IngresosCierreAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_nombre', 'fecha_ingreso', 'tipo_contrato',
        'sueldo_formateado', 'estado_badge'
    ]
    list_filter = ['tipo_contrato', 'estado_ingreso', 'fecha_ingreso']
    search_fields = ['empleado_cierre__nombre_completo']
    raw_id_fields = ['empleado_cierre', 'aprobado_por']
    
    def empleado_nombre(self, obj):
        return obj.empleado_cierre.nombre_completo
    empleado_nombre.short_description = 'Empleado'
    
    def sueldo_formateado(self, obj):
        return f"${obj.sueldo_base:,.0f}"
    sueldo_formateado.short_description = 'Sueldo Base'
    
    def estado_badge(self, obj):
        color = obj.get_color_estado()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_estado_ingreso_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Ausentismos_Cierre)
class AusentismosCierreAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_nombre', 'tipo_ausentismo', 'fecha_inicio',
        'dias_ausentismo', 'monto_descontado', 'estado_badge'
    ]
    list_filter = ['tipo_ausentismo', 'estado_ausentismo', 'fecha_inicio']
    search_fields = ['empleado_cierre__nombre_completo']
    raw_id_fields = ['empleado_cierre', 'validado_por']
    
    def empleado_nombre(self, obj):
        return obj.empleado_cierre.nombre_completo
    empleado_nombre.short_description = 'Empleado'
    
    def estado_badge(self, obj):
        color = obj.get_color_estado()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_estado_ausentismo_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(Logs_Comparacion)
class LogsComparacionAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'cierre_info', 'usuario', 'accion_badge',
        'resultado_badge', 'duracion_formateada'
    ]
    list_filter = ['accion', 'resultado', 'timestamp']
    search_fields = ['cierre_payroll__periodo', 'usuario__username', 'detalles']
    readonly_fields = ['timestamp']
    raw_id_fields = ['cierre_payroll', 'usuario']
    
    def cierre_info(self, obj):
        return f"{obj.cierre_payroll.cliente.nombre} - {obj.cierre_payroll.periodo}"
    cierre_info.short_description = 'Cierre'
    
    def accion_badge(self, obj):
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.get_accion_display()
        )
    accion_badge.short_description = 'Acción'
    
    def resultado_badge(self, obj):
        color = obj.get_color_resultado()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_resultado_display()
        )
    resultado_badge.short_description = 'Resultado'
    
    def duracion_formateada(self, obj):
        return obj.get_duracion_display()
    duracion_formateada.short_description = 'Duración'
