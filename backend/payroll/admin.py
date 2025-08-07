from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
import json

from .models import (
    PayrollClosure, 
    PayrollFileUpload, 
    ParsedDataStorage,
    ValidationRun, 
    DiscrepancyResult, 
    ComparisonResult,
    ValidationRule
)
from .models.shared import (
    PayrollActivityLog, 
    AuditTrail, 
    PerformanceLog,
    RedisCache
)

# ============================================================================
#                         PERSONALIZACIÓN ADMIN SITE
# ============================================================================

# Personalizar títulos del admin principal
admin.site.site_header = "SGM - Sistema de Gestión de Nóminas"
admin.site.site_title = "SGM Admin"
admin.site.index_title = "Administración SGM"

# ============================================================================
#                           PAYROLL CLOSURE ADMIN
# ============================================================================

@admin.register(PayrollClosure)
class PayrollClosureAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cliente', 'periodo', 'status_badge', 'fase_actual_badge', 
        'analista_responsable', 'progress_bar', 'fecha_inicio', 'files_count'
    ]
    list_filter = [
        'status', 'fase_actual', 'cliente', 'analista_responsable',
        'fecha_inicio', 'created_at'
    ]
    search_fields = [
        'periodo', 'cliente__nombre', 'analista_responsable', 'observaciones'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'progress_display', 
        'redis_keys_display', 'files_summary'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'cliente', 'periodo', 'analista_responsable')
        }),
        ('Estado y Progreso', {
            'fields': ('status', 'fase_actual', 'progress_display')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_cierre_prevista', 'created_at', 'updated_at')
        }),
        ('Configuración', {
            'fields': ('configuracion_validaciones',)
        }),
        ('Detalles', {
            'fields': ('observaciones', 'metadata')
        }),
        ('Sistema', {
            'fields': ('redis_keys_display', 'files_summary'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente').annotate(
            files_count=Count('payrollfileupload')
        )
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': '#6c757d',
            'IN_PROGRESS': '#007bff', 
            'COMPLETED': '#28a745',
            'FINALIZED': '#17a2b8',
            'CANCELLED': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def fase_actual_badge(self, obj):
        colors = {
            'PHASE_1': '#ffc107',
            'PHASE_2': '#fd7e14', 
            'PHASE_3': '#6f42c1',
            'PHASE_4': '#20c997'
        }
        color = colors.get(obj.fase_actual, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_fase_actual_display()
        )
    fase_actual_badge.short_description = 'Fase'
    
    def progress_bar(self, obj):
        try:
            progress = obj.get_progress_percentage()
            color = '#28a745' if progress >= 75 else '#ffc107' if progress >= 50 else '#dc3545'
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
                '<div style="width: {}%; height: 20px; background-color: {}; '
                'border-radius: 3px; text-align: center; color: white; font-size: 12px; '
                'line-height: 20px;">{:.1f}%</div></div>',
                progress, color, progress
            )
        except:
            return format_html('<span style="color: #6c757d;">N/A</span>')
    progress_bar.short_description = 'Progreso'
    
    def files_count(self, obj):
        return obj.files_count
    files_count.short_description = 'Archivos'
    files_count.admin_order_field = 'files_count'
    
    def progress_display(self, obj):
        try:
            progress = obj.get_progress_percentage()
            return f"{progress:.1f}%"
        except:
            return "No calculado"
    progress_display.short_description = 'Progreso Actual'
    
    def redis_keys_display(self, obj):
        try:
            keys = obj.get_redis_keys()
            if keys:
                return format_html('<br>'.join([f"• {key}" for key in keys]))
            return "Sin keys de Redis"
        except:
            return "Error al obtener keys"
    redis_keys_display.short_description = 'Keys de Redis'
    
    def files_summary(self, obj):
        files = obj.payrollfileupload_set.all()
        if not files:
            return "Sin archivos cargados"
        
        summary = []
        for file_obj in files:
            summary.append(f"• {file_obj.get_file_type_display()}: {file_obj.get_status_display()}")
        
        return format_html('<br>'.join(summary))
    files_summary.short_description = 'Resumen de Archivos'


# ============================================================================
#                           FILE UPLOAD ADMIN
# ============================================================================

@admin.register(PayrollFileUpload)
class PayrollFileUploadAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'closure_link', 'file_type_badge', 'original_filename', 
        'status_badge', 'file_size_display', 'parsing_progress', 'created_at'
    ]
    list_filter = [
        'file_type', 'status', 'closure__cliente', 'created_at',
        'parsing_completed_at'
    ]
    search_fields = [
        'original_filename', 'closure__periodo', 'closure__cliente__nombre',
        'celery_task_id'
    ]
    readonly_fields = [
        'id', 'file_size_display', 'checksum_md5', 'parsing_duration', 
        'redis_cache_key', 'created_at', 'updated_at', 'parsing_errors_display'
    ]
    raw_id_fields = ['closure']
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('closure', 'file_type', 'file', 'original_filename', 'file_size_display')
        }),
        ('Estado de Procesamiento', {
            'fields': ('status', 'parsing_completed_at', 'parsing_duration')
        }),
        ('Datos Técnicos', {
            'fields': ('checksum_md5', 'redis_cache_key', 'celery_task_id'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('metadata', 'parsing_errors_display'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def closure_link(self, obj):
        url = reverse('admin:payroll_payrollclosure_change', args=[obj.closure.id])
        return format_html('<a href="{}">{}</a>', url, obj.closure)
    closure_link.short_description = 'Cierre'
    
    def file_type_badge(self, obj):
        colors = {
            'LIBRO_REMUNERACIONES': '#007bff',
            'MOVIMIENTOS_MES': '#28a745',
            'FINIQUITOS': '#ffc107',
            'INGRESOS': '#17a2b8',
            'INCIDENCIAS': '#fd7e14',
            'NOVEDADES': '#6f42c1'
        }
        color = colors.get(obj.file_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_file_type_display()
        )
    file_type_badge.short_description = 'Tipo'
    
    def status_badge(self, obj):
        colors = {
            'UPLOADED': '#6c757d',
            'PARSING': '#007bff',
            'PARSED': '#28a745',
            'ERROR': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size > 1024*1024:
                return f"{obj.file_size/(1024*1024):.1f} MB"
            elif obj.file_size > 1024:
                return f"{obj.file_size/1024:.1f} KB"
            else:
                return f"{obj.file_size} bytes"
        return "N/A"
    file_size_display.short_description = 'Tamaño'
    
    def parsing_progress(self, obj):
        if obj.status == 'PARSING':
            return format_html('<span style="color: #007bff;">⏳ Procesando...</span>')
        elif obj.status == 'PARSED':
            return format_html('<span style="color: #28a745;">✅ Completado</span>')
        elif obj.status == 'ERROR':
            return format_html('<span style="color: #dc3545;">❌ Error</span>')
        else:
            return format_html('<span style="color: #6c757d;">⏸️ Pendiente</span>')
    parsing_progress.short_description = 'Progreso'
    
    def parsing_errors_display(self, obj):
        if obj.parsing_errors:
            try:
                errors = obj.parsing_errors if isinstance(obj.parsing_errors, list) else [obj.parsing_errors]
                return format_html('<br>'.join([f"• {error}" for error in errors]))
            except:
                return str(obj.parsing_errors)
        return "Sin errores"
    parsing_errors_display.short_description = 'Errores de Parsing'


# ============================================================================
#                           VALIDATION ADMIN
# ============================================================================

@admin.register(ValidationRun)
class ValidationRunAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'closure_link', 'validation_type_badge', 'status_badge',
        'progress_percentage', 'discrepancies_count', 'started_at', 'duration'
    ]
    list_filter = [
        'validation_type', 'status', 'closure__cliente', 'started_at'
    ]
    search_fields = [
        'closure__periodo', 'closure__cliente__nombre', 'celery_task_id'
    ]
    readonly_fields = [
        'id', 'duration', 'discrepancies_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['closure']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('closure').annotate(
            discrepancies_count=Count('discrepancyresult')
        )
    
    def closure_link(self, obj):
        url = reverse('admin:payroll_payrollclosure_change', args=[obj.closure.id])
        return format_html('<a href="{}">{}</a>', url, obj.closure)
    closure_link.short_description = 'Cierre'
    
    def validation_type_badge(self, obj):
        colors = {
            'STRUCTURE': '#007bff',
            'BUSINESS_RULES': '#28a745',
            'CROSS_VALIDATION': '#ffc107',
            'COMPLETENESS': '#17a2b8'
        }
        color = colors.get(obj.validation_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_validation_type_display()
        )
    validation_type_badge.short_description = 'Tipo'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#6c757d',
            'RUNNING': '#007bff',
            'COMPLETED': '#28a745',
            'FAILED': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def progress_percentage(self, obj):
        if obj.total_records and obj.processed_records:
            progress = (obj.processed_records / obj.total_records) * 100
            return f"{progress:.1f}%"
        return "N/A"
    progress_percentage.short_description = 'Progreso'
    
    def discrepancies_count(self, obj):
        return obj.discrepancies_count
    discrepancies_count.short_description = 'Discrepancias'
    discrepancies_count.admin_order_field = 'discrepancies_count'
    
    def duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration).split('.')[0]  # Remove microseconds
        return "N/A"
    duration.short_description = 'Duración'


@admin.register(DiscrepancyResult)
class DiscrepancyResultAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'closure_link', 'discrepancy_type_badge', 'severity_badge',
        'employee_rut', 'concept_code', 'is_resolved', 'created_at'
    ]
    list_filter = [
        'discrepancy_type', 'severity', 'is_resolved', 'closure__cliente',
        'created_at', 'resolved_at'
    ]
    search_fields = [
        'employee_rut', 'concept_code', 'description', 
        'closure__periodo', 'closure__cliente__nombre'
    ]
    readonly_fields = [
        'id', 'calculated_difference', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['closure', 'validation_run']
    
    fieldsets = (
        ('Información de la Discrepancia', {
            'fields': ('closure', 'validation_run', 'discrepancy_type', 'severity')
        }),
        ('Detalles del Empleado', {
            'fields': ('employee_rut', 'employee_name', 'concept_code')
        }),
        ('Valores', {
            'fields': ('expected_value', 'actual_value', 'calculated_difference')
        }),
        ('Descripción y Resolución', {
            'fields': ('description', 'is_resolved', 'resolution_notes', 'resolved_by', 'resolved_at')
        }),
        ('Metadatos', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        })
    )
    
    def closure_link(self, obj):
        url = reverse('admin:payroll_payrollclosure_change', args=[obj.closure.id])
        return format_html('<a href="{}">{}</a>', url, obj.closure)
    closure_link.short_description = 'Cierre'
    
    def discrepancy_type_badge(self, obj):
        colors = {
            'MISSING_EMPLOYEE': '#dc3545',
            'DUPLICATE_EMPLOYEE': '#fd7e14',
            'AMOUNT_MISMATCH': '#ffc107',
            'INVALID_CONCEPT': '#6f42c1',
            'DATE_INCONSISTENCY': '#17a2b8'
        }
        color = colors.get(obj.discrepancy_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_discrepancy_type_display()
        )
    discrepancy_type_badge.short_description = 'Tipo'
    
    def severity_badge(self, obj):
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Severidad'
    
    def calculated_difference(self, obj):
        if obj.expected_value is not None and obj.actual_value is not None:
            try:
                diff = float(obj.actual_value) - float(obj.expected_value)
                return f"{diff:,.2f}"
            except (ValueError, TypeError):
                return "N/A"
        return "N/A"
    calculated_difference.short_description = 'Diferencia'


# ============================================================================
#                           AUDIT & LOGS ADMIN
# ============================================================================

@admin.register(PayrollActivityLog)
class PayrollActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'closure_link', 'activity_type_badge', 'user', 
        'is_successful', 'execution_time_ms', 'created_at'
    ]
    list_filter = [
        'activity_type', 'is_successful', 'closure__cliente', 'created_at', 'user'
    ]
    search_fields = [
        'description', 'user__username', 'closure__periodo',
        'related_object_type', 'related_object_id'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'details_display']
    raw_id_fields = ['closure', 'user']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('closure', 'user', 'activity_type', 'is_successful')
        }),
        ('Detalles', {
            'fields': ('description', 'details_display')
        }),
        ('Objeto Relacionado', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Rendimiento', {
            'fields': ('execution_time_ms',),
            'classes': ('collapse',)
        })
    )
    
    def closure_link(self, obj):
        if obj.closure:
            url = reverse('admin:payroll_payrollclosure_change', args=[obj.closure.id])
            return format_html('<a href="{}">{}</a>', url, obj.closure)
        return "N/A"
    closure_link.short_description = 'Cierre'
    
    def activity_type_badge(self, obj):
        colors = {
            'FILE_UPLOAD': '#007bff',
            'FILE_PARSING': '#17a2b8',
            'VALIDATION': '#28a745',
            'DISCREPANCY_RESOLUTION': '#ffc107',
            'STATUS_CHANGE': '#6f42c1',
            'ERROR': '#dc3545'
        }
        color = colors.get(obj.activity_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Tipo de Actividad'
    
    def details_display(self, obj):
        if obj.details:
            try:
                if isinstance(obj.details, dict):
                    return format_html('<pre>{}</pre>', json.dumps(obj.details, indent=2))
                else:
                    return str(obj.details)
            except:
                return str(obj.details)
        return "Sin detalles"
    details_display.short_description = 'Detalles JSON'


@admin.register(RedisCache)
class RedisCacheAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cache_key_short', 'cache_type_badge', 'data_size_mb',
        'access_count', 'is_active', 'expires_at', 'last_accessed'
    ]
    list_filter = [
        'cache_type', 'is_active', 'data_structure', 'created_at'
    ]
    search_fields = [
        'cache_key', 'description', 'related_object_type'
    ]
    readonly_fields = [
        'id', 'data_size_mb', 'created_at', 'updated_at', 'cache_metadata_display'
    ]
    
    def cache_key_short(self, obj):
        if len(obj.cache_key) > 50:
            return f"{obj.cache_key[:47]}..."
        return obj.cache_key
    cache_key_short.short_description = 'Cache Key'
    
    def cache_type_badge(self, obj):
        colors = {
            'FILE_PARSED_DATA': '#007bff',
            'VALIDATION_PROGRESS': '#28a745',
            'CLOSURE_STATUS': '#17a2b8',
            'DISCREPANCY_CACHE': '#ffc107',
            'TEMP_DATA': '#6c757d'
        }
        color = colors.get(obj.cache_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_cache_type_display()
        )
    cache_type_badge.short_description = 'Tipo'
    
    def data_size_mb(self, obj):
        if obj.data_size_bytes:
            mb = obj.data_size_bytes / (1024 * 1024)
            if mb >= 1:
                return f"{mb:.2f} MB"
            else:
                kb = obj.data_size_bytes / 1024
                return f"{kb:.1f} KB"
        return "0 B"
    data_size_mb.short_description = 'Tamaño'
    
    def cache_metadata_display(self, obj):
        if obj.cache_metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.cache_metadata, indent=2))
        return "Sin metadata"
    cache_metadata_display.short_description = 'Metadata'


# ============================================================================
#                           SMALLER MODELS
# ============================================================================

@admin.register(ValidationRule)
class ValidationRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'validation_type', 'is_active', 'execution_order']
    list_filter = ['validation_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['execution_order', 'name']


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'validation_run', 'comparison_type', 'source_file', 'target_file']
    list_filter = ['comparison_type']
    raw_id_fields = ['validation_run', 'source_file', 'target_file']


@admin.register(ParsedDataStorage)
class ParsedDataStorageAdmin(admin.ModelAdmin):
    list_display = ['id', 'file_upload', 'data_rows_count', 'is_cached_in_redis', 'last_accessed']
    list_filter = ['is_cached_in_redis', 'expires_at']
    raw_id_fields = ['file_upload']
    readonly_fields = ['data_size_mb']
    
    def data_rows_count(self, obj):
        if obj.parsed_data and isinstance(obj.parsed_data, list):
            return len(obj.parsed_data)
        elif obj.parsed_data and isinstance(obj.parsed_data, dict) and 'rows' in obj.parsed_data:
            return len(obj.parsed_data['rows'])
        return "N/A"
    data_rows_count.short_description = 'Filas de Datos'
    
    def data_size_mb(self, obj):
        import json
        if obj.parsed_data:
            data_str = json.dumps(obj.parsed_data)
            size_bytes = len(data_str.encode('utf-8'))
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        return "0 MB"
    data_size_mb.short_description = 'Tamaño'


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'object_id', 'action', 'user', 'created_at']
    list_filter = ['action', 'content_type', 'created_at']
    search_fields = ['object_id', 'user__username', 'content_type__model']
    readonly_fields = ['id', 'changes_display']
    
    def changes_display(self, obj):
        changes = {}
        if obj.old_values or obj.new_values:
            changes['old_values'] = obj.old_values
            changes['new_values'] = obj.new_values
            changes['changed_fields'] = obj.changed_fields
            return format_html('<pre>{}</pre>', json.dumps(changes, indent=2))
        return "Sin cambios"
    changes_display.short_description = 'Cambios'


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'operation_name', 'execution_time_ms', 'is_successful', 'created_at']
    list_filter = ['operation_type', 'is_successful', 'created_at']
    search_fields = ['operation_name']
    readonly_fields = ['id', 'performance_data_display']
    
    def performance_data_display(self, obj):
        if obj.performance_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.performance_data, indent=2))
        return "Sin datos de rendimiento"
    performance_data_display.short_description = 'Datos de Rendimiento'


# ============================================================================
#                           ADMIN SITE CUSTOMIZATION
# ============================================================================

# Configuración central del admin (se ejecuta al final por orden de apps)
admin.site.site_header = "SGM - Sistema de Gestión Empresarial"
admin.site.site_title = "SGM Admin"
admin.site.index_title = "Panel de Administración - Nóminas y Tareas"
