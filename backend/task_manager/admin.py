# task_manager/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import TaskExecution, TaskTemplate, TaskNotification


@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    """
    🚀 Administración de ejecuciones de tareas
    """
    list_display = [
        'id', 'task_name_short', 'status_badge', 'task_module', 
        'progress_bar', 'user_link', 'created_at_short', 'duration_display'
    ]
    list_filter = [
        'status', 'task_module', 'created_at'
    ]
    search_fields = [
        'task_id', 'task_name', 'description', 'user__nombre', 'user__apellido', 'user__correo_bdo'
    ]
    readonly_fields = [
        'task_id', 'created_at', 'updated_at', 'started_at', 'completed_at',
        'duration_display', 'is_finished', 'is_running', 'is_successful',
        'context_data_display', 'result_data_display', 'error_traceback_display'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'task_id', 'task_name', 'task_module', 'status',
                'description', 'user'
            )
        }),
        ('Progreso', {
            'fields': (
                'progress_percentage', 'current_step', 'total_steps'
            )
        }),
        ('Tiempos', {
            'fields': (
                'created_at', 'started_at', 'completed_at', 
                'updated_at'
            )
        }),
        ('Información Calculada', {
            'fields': (
                'duration_display', 'is_finished', 'is_running', 'is_successful'
            )
        }),
        ('Configuración', {
            'fields': (
                'timeout_seconds', 'retry_count', 'max_retries'
            )
        }),
        ('Worker Info', {
            'fields': (
                'worker_name', 'queue_name'
            )
        }),
        ('Datos y Resultados', {
            'fields': (
                'context_data_display', 'result_data_display',
                'error_message', 'error_traceback_display'
            )
        }),
    )
    
    def task_name_short(self, obj):
        """Nombre de tarea abreviado"""
        if len(obj.task_name) > 30:
            return f"{obj.task_name[:30]}..."
        return obj.task_name
    task_name_short.short_description = 'Tarea'
    
    def status_badge(self, obj):
        """Badge colorido para el estado"""
        colors = {
            'PENDING': '#ffc107',    # Amarillo
            'STARTED': '#17a2b8',    # Azul
            'PROGRESS': '#007bff',   # Azul primario
            'SUCCESS': '#28a745',    # Verde
            'FAILURE': '#dc3545',    # Rojo
            'RETRY': '#fd7e14',      # Naranja
            'REVOKED': '#6c757d',    # Gris
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Estado'
    
    def progress_bar(self, obj):
        """Barra de progreso visual"""
        if obj.progress_percentage > 0:
            percentage = int(obj.progress_percentage)
            return format_html(
                '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
                '<div style="width: {}%; background-color: #007bff; height: 20px; '
                'border-radius: 3px; text-align: center; color: white; font-size: 11px; '
                'line-height: 20px;">{}%</div></div>',
                percentage, percentage
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    progress_bar.short_description = 'Progreso'
    
    def user_link(self, obj):
        """Link al usuario si existe"""
        if obj.user:
            try:
                # Construir nombre de usuario para mostrar
                user_display = f"{obj.user.nombre} {obj.user.apellido}".strip()
                if not user_display:
                    user_display = str(obj.user)  # Fallback al __str__ del modelo
                
                return format_html(
                    '<a href="{}">{}</a>',
                    reverse('admin:api_usuario_change', args=[obj.user.pk]),
                    user_display
                )
            except Exception:
                # Si falla el link, mostrar solo el nombre
                user_display = f"{obj.user.nombre} {obj.user.apellido}".strip()
                return user_display if user_display else str(obj.user)
        return '-'
    user_link.short_description = 'Usuario'
    
    def created_at_short(self, obj):
        """Fecha de creación abreviada"""
        return obj.created_at.strftime('%d/%m %H:%M')
    created_at_short.short_description = 'Creado'
    
    def duration_display(self, obj):
        """Duración formateada"""
        duration = obj.duration_seconds  # Esta es la propiedad calculada
        if duration and duration > 0:
            if duration < 60:
                return f"{duration:.0f}s"
            elif duration < 3600:
                return f"{duration/60:.1f}m"
            else:
                return f"{duration/3600:.1f}h"
        return '-'
    duration_display.short_description = 'Duración'
    
    def context_data_display(self, obj):
        """Mostrar context_data formateado"""
        if obj.context_data:
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; '
                'border-radius: 5px; max-height: 200px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.context_data, indent=2, ensure_ascii=False)
            )
        return '-'
    context_data_display.short_description = 'Datos de Contexto'
    
    def result_data_display(self, obj):
        """Mostrar result_data formateado"""
        if obj.result_data:
            return format_html(
                '<pre style="background: #d4edda; padding: 10px; '
                'border-radius: 5px; max-height: 200px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.result_data, indent=2, ensure_ascii=False)
            )
        return '-'
    result_data_display.short_description = 'Datos de Resultado'
    
    def error_traceback_display(self, obj):
        """Mostrar error_traceback formateado"""
        if obj.error_traceback:
            return format_html(
                '<pre style="background: #f8d7da; padding: 10px; '
                'border-radius: 5px; max-height: 300px; overflow-y: auto; '
                'font-family: monospace; font-size: 12px;">{}</pre>',
                obj.error_traceback
            )
        return '-'
    error_traceback_display.short_description = 'Stack Trace del Error'
    
    actions = ['mark_as_revoked', 'retry_failed_tasks']
    
    def mark_as_revoked(self, request, queryset):
        """Acción para marcar tareas como revocadas"""
        count = queryset.update(status='REVOKED')
        self.message_user(request, f'{count} tareas marcadas como revocadas.')
    mark_as_revoked.short_description = 'Marcar como revocadas'
    
    def retry_failed_tasks(self, request, queryset):
        """Acción para reintentar tareas fallidas"""
        failed_tasks = queryset.filter(status='FAILURE')
        count = 0
        for task in failed_tasks:
            task.retry_count += 1
            task.status = 'PENDING'
            task.save()
            count += 1
        self.message_user(request, f'{count} tareas fallidas marcadas para reintento.')
    retry_failed_tasks.short_description = 'Reintentar tareas fallidas'


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    """
    📋 Administración de plantillas de tareas
    """
    list_display = [
        'name', 'module', 'description_short', 'estimated_duration_display',
        'usage_count', 'created_at_short'
    ]
    list_filter = ['module', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'module', 'description')
        }),
        ('Configuración por Defecto', {
            'fields': (
                'default_timeout', 'default_max_retries', 
                'estimated_duration_seconds'
            )
        }),
        ('Pasos Típicos', {
            'fields': ('typical_steps',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'usage_count')
        }),
    )
    
    def description_short(self, obj):
        """Descripción abreviada"""
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    description_short.short_description = 'Descripción'
    
    def estimated_duration_display(self, obj):
        """Duración estimada formateada"""
        if obj.estimated_duration_seconds < 60:
            return f"{obj.estimated_duration_seconds}s"
        elif obj.estimated_duration_seconds < 3600:
            return f"{obj.estimated_duration_seconds/60:.0f}m"
        else:
            return f"{obj.estimated_duration_seconds/3600:.1f}h"
    estimated_duration_display.short_description = 'Duración Est.'
    
    def created_at_short(self, obj):
        """Fecha de creación abreviada"""
        return obj.created_at.strftime('%d/%m/%Y')
    created_at_short.short_description = 'Creado'
    
    def usage_count(self, obj):
        """Número de veces que se ha usado esta plantilla"""
        return TaskExecution.objects.filter(
            task_name__icontains=obj.name
        ).count()
    usage_count.short_description = 'Usos'


@admin.register(TaskNotification)
class TaskNotificationAdmin(admin.ModelAdmin):
    """
    🔔 Administración de notificaciones de tareas
    """
    list_display = [
        'id', 'task_link', 'type_badge', 'title', 'read',
        'created_at_short'
    ]
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['title', 'message', 'task__task_name']
    readonly_fields = ['created_at', 'details_display']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('task', 'type', 'title', 'message')
        }),
        ('Estado', {
            'fields': ('read', 'created_at')
        }),
        ('Detalles', {
            'fields': ('details_display',)
        }),
    )
    
    def task_link(self, obj):
        """Link a la tarea relacionada"""
        if obj.task:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:task_manager_taskexecution_change', args=[obj.task.pk]),
                obj.task.task_name[:30] + ('...' if len(obj.task.task_name) > 30 else '')
            )
        return '-'
    task_link.short_description = 'Tarea'
    
    def type_badge(self, obj):
        """Badge para el tipo de notificación"""
        colors = {
            'INFO': '#17a2b8',
            'SUCCESS': '#28a745',
            'WARNING': '#ffc107',
            'ERROR': '#dc3545',
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.type
        )
    type_badge.short_description = 'Tipo'
    
    def created_at_short(self, obj):
        """Fecha de creación abreviada"""
        return obj.created_at.strftime('%d/%m %H:%M')
    created_at_short.short_description = 'Creado'
    
    def details_display(self, obj):
        """Mostrar detalles formateado"""
        if obj.details:
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; '
                'border-radius: 5px; max-height: 150px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.details, indent=2, ensure_ascii=False)
            )
        return '-'
    details_display.short_description = 'Detalles'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Marcar notificaciones como leídas"""
        count = queryset.update(read=True)
        self.message_user(request, f'{count} notificaciones marcadas como leídas.')
    mark_as_read.short_description = 'Marcar como leídas'
    
    def mark_as_unread(self, request, queryset):
        """Marcar notificaciones como no leídas"""
        count = queryset.update(read=False)
        self.message_user(request, f'{count} notificaciones marcadas como no leídas.')
    mark_as_unread.short_description = 'Marcar como no leídas'


# Personalizar el admin site
admin.site.site_header = "SGM - Gestión de Tareas"
admin.site.site_title = "SGM Task Manager"
admin.site.index_title = "Panel de Administración de Tareas"
