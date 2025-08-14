# ============================================================================
#                           LOGS ACTIVIDAD VIEWS
# ============================================================================
# Views para la gestión y visualización de logs de actividad

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Logs_Actividad, CierrePayroll


class LogsActividadListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de logs de actividad
    """
    model = Logs_Actividad
    template_name = 'payroll/logs/list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Logs_Actividad.objects.select_related(
            'cierre_payroll', 'usuario', 'cierre_payroll__cliente'
        )
        
        # Filtro por cierre específico si se proporciona
        cierre_id = self.kwargs.get('cierre_id')
        if cierre_id:
            queryset = queryset.filter(cierre_payroll_id=cierre_id)
        
        # Filtros adicionales
        accion = self.request.GET.get('accion')
        if accion:
            queryset = queryset.filter(accion=accion)
            
        resultado = self.request.GET.get('resultado')
        if resultado:
            queryset = queryset.filter(resultado=resultado)
            
        usuario = self.request.GET.get('usuario')
        if usuario:
            queryset = queryset.filter(usuario__username__icontains=usuario)
            
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=fecha_desde)
            except ValueError:
                pass
                
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=fecha_hasta)
            except ValueError:
                pass
        
        # Búsqueda en descripción
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(descripcion__icontains=search) |
                Q(detalles__icontains=search) |
                Q(cierre_payroll__cliente__nombre__icontains=search)
            )
            
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Si es un cierre específico
        cierre_id = self.kwargs.get('cierre_id')
        if cierre_id:
            context['cierre'] = get_object_or_404(CierrePayroll, pk=cierre_id)
        
        # Estadísticas
        queryset = self.get_queryset()
        context['stats'] = {
            'total': queryset.count(),
            'exitosos': queryset.filter(resultado='exitoso').count(),
            'errores': queryset.filter(resultado='error').count(),
            'advertencias': queryset.filter(resultado='advertencia').count(),
            'hoy': queryset.filter(timestamp__date=timezone.now().date()).count(),
        }
        
        # Opciones para filtros
        context['acciones'] = Logs_Actividad.ACCIONES_CHOICES
        context['resultados'] = Logs_Actividad.RESULTADOS_CHOICES
        
        return context


class LogsActividadDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detalle de un log específico
    """
    model = Logs_Actividad
    template_name = 'payroll/logs/detail.html'
    context_object_name = 'log'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log = self.get_object()
        
        # Logs relacionados (del mismo cierre y usuario, en rango de tiempo)
        tiempo_limite = log.timestamp - timedelta(hours=1)
        context['logs_relacionados'] = Logs_Actividad.objects.filter(
            cierre_payroll=log.cierre_payroll,
            usuario=log.usuario,
            timestamp__gte=tiempo_limite,
            timestamp__lte=log.timestamp + timedelta(hours=1)
        ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        return context


@login_required
def logs_estadisticas_ajax(request):
    """
    Vista AJAX para obtener estadísticas de logs
    """
    periodo = request.GET.get('periodo', 'dia')  # dia, semana, mes
    
    now = timezone.now()
    
    if periodo == 'dia':
        fecha_desde = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semana':
        fecha_desde = now - timedelta(days=7)
    elif periodo == 'mes':
        fecha_desde = now - timedelta(days=30)
    else:
        fecha_desde = now - timedelta(days=1)
    
    logs = Logs_Actividad.objects.filter(timestamp__gte=fecha_desde)
    
    # Estadísticas por acción
    por_accion = logs.values('accion').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Estadísticas por resultado
    por_resultado = logs.values('resultado').annotate(
        total=Count('id')
    )
    
    # Estadísticas por usuario
    por_usuario = logs.values('usuario__username').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # Actividad por hora (últimas 24 horas)
    actividad_horaria = []
    for i in range(24):
        hora_inicio = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
        hora_fin = hora_inicio + timedelta(hours=1)
        
        count = logs.filter(
            timestamp__gte=hora_inicio,
            timestamp__lt=hora_fin
        ).count()
        
        actividad_horaria.append({
            'hora': hora_inicio.strftime('%H:00'),
            'count': count
        })
    
    return JsonResponse({
        'periodo': periodo,
        'total_logs': logs.count(),
        'por_accion': list(por_accion),
        'por_resultado': list(por_resultado),
        'por_usuario': list(por_usuario),
        'actividad_horaria': list(reversed(actividad_horaria))
    })


@login_required
def logs_timeline_ajax(request, cierre_id):
    """
    Vista AJAX para obtener timeline de logs de un cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    logs = Logs_Actividad.objects.filter(
        cierre_payroll=cierre
    ).select_related('usuario').order_by('-timestamp')
    
    timeline = []
    for log in logs:
        timeline.append({
            'id': log.id,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'accion': log.get_accion_display(),
            'accion_code': log.accion,
            'resultado': log.get_resultado_display(),
            'resultado_code': log.resultado,
            'usuario': log.usuario.username,
            'descripcion': log.descripcion,
            'duracion': log.get_duracion_display() if hasattr(log, 'get_duracion_display') else None,
            'color': log.get_color_resultado() if hasattr(log, 'get_color_resultado') else '#6c757d'
        })
    
    return JsonResponse({
        'timeline': timeline,
        'cierre': {
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
            'estado': cierre.get_estado_display()
        }
    })


@login_required
def exportar_logs_excel(request):
    """
    Vista para exportar logs a Excel
    """
    # Filtros similares a la lista
    queryset = Logs_Actividad.objects.all()
    
    cierre_id = request.GET.get('cierre_id')
    if cierre_id:
        queryset = queryset.filter(cierre_payroll_id=cierre_id)
    
    fecha_desde = request.GET.get('fecha_desde')
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__gte=fecha_desde)
        except ValueError:
            pass
            
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__lte=fecha_hasta)
        except ValueError:
            pass
    
    # Preparar datos para export
    logs_data = []
    for log in queryset.select_related('cierre_payroll__cliente', 'usuario'):
        logs_data.append({
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'cliente': log.cierre_payroll.cliente.nombre,
            'periodo': log.cierre_payroll.periodo,
            'usuario': log.usuario.username,
            'accion': log.get_accion_display(),
            'resultado': log.get_resultado_display(),
            'descripcion': log.descripcion,
            'detalles': log.detalles or '',
        })
    
    return JsonResponse({
        'logs': logs_data,
        'total': len(logs_data),
        'filtros_aplicados': {
            'cierre_id': cierre_id,
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d') if fecha_desde else None,
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d') if fecha_hasta else None,
        }
    })


@login_required
def limpiar_logs_antiguos(request):
    """
    Vista para limpiar logs antiguos (solo para admins)
    """
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Sin permisos para esta operación'
        })
    
    if request.method == 'POST':
        dias = int(request.POST.get('dias', 30))
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        logs_a_eliminar = Logs_Actividad.objects.filter(
            timestamp__lt=fecha_limite
        )
        
        total_eliminados = logs_a_eliminar.count()
        logs_a_eliminar.delete()
        
        # Crear log de la operación de limpieza
        Logs_Actividad.objects.create(
            cierre_payroll=None,  # Operación del sistema
            usuario=request.user,
            accion='mantenimiento',
            descripcion=f'Limpieza de logs antiguos: {total_eliminados} registros eliminados (>{dias} días)',
            resultado='exitoso'
        )
        
        return JsonResponse({
            'success': True,
            'eliminados': total_eliminados,
            'dias': dias
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })


@login_required
def resumen_errores_frecuentes(request):
    """
    Vista para obtener resumen de errores más frecuentes
    """
    # Últimos 30 días
    fecha_desde = timezone.now() - timedelta(days=30)
    
    errores = Logs_Actividad.objects.filter(
        resultado='error',
        timestamp__gte=fecha_desde
    )
    
    # Agrupar errores similares por descripción
    errores_agrupados = errores.values('descripcion').annotate(
        total=Count('id'),
        ultimo_error=timezone.now()  # Será reemplazado por el último timestamp
    ).order_by('-total')[:10]
    
    # Obtener el último timestamp para cada error
    for error in errores_agrupados:
        ultimo_log = errores.filter(
            descripcion=error['descripcion']
        ).order_by('-timestamp').first()
        
        if ultimo_log:
            error['ultimo_error'] = ultimo_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            error['usuario_ultimo'] = ultimo_log.usuario.username
            error['cierre_ultimo'] = f"{ultimo_log.cierre_payroll.cliente.nombre} - {ultimo_log.cierre_payroll.periodo}"
    
    return JsonResponse({
        'errores_frecuentes': list(errores_agrupados),
        'periodo_analisis': '30 días',
        'total_errores': errores.count()
    })
