# ============================================================================
#                           DASHBOARD VIEWS
# ============================================================================
# Views para el dashboard principal del sistema payroll

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import (
    CierrePayroll, Empleados_Cierre, Item_Cierre, 
    Incidencias_Cierre, Logs_Actividad
)
from api.models import Cliente


class PayrollDashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del dashboard de payroll
    """
    template_name = 'payroll/dashboard/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['stats_generales'] = self.get_estadisticas_generales()
        
        # Cierres recientes
        context['cierres_recientes'] = CierrePayroll.objects.select_related(
            'cliente', 'usuario_responsable'
        ).order_by('-fecha_creacion')[:10]
        
        # Incidencias pendientes
        context['incidencias_pendientes'] = Incidencias_Cierre.objects.filter(
            estado='abierta'
        ).select_related('cierre_payroll__cliente').order_by('-fecha_creacion')[:5]
        
        # Actividad reciente
        context['actividad_reciente'] = Logs_Actividad.objects.select_related(
            'cierre_payroll__cliente', 'usuario'
        ).order_by('-timestamp')[:10]
        
        return context
    
    def get_estadisticas_generales(self):
        """
        Obtiene estadísticas generales del sistema
        """
        now = timezone.now()
        mes_actual = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'total_cierres': CierrePayroll.objects.count(),
            'cierres_mes': CierrePayroll.objects.filter(fecha_creacion__gte=mes_actual).count(),
            'cierres_pendientes': CierrePayroll.objects.filter(estado='pendiente').count(),
            'cierres_procesando': CierrePayroll.objects.filter(estado='procesando').count(),
            'total_empleados': Empleados_Cierre.objects.count(),
            'incidencias_abiertas': Incidencias_Cierre.objects.filter(estado='abierta').count(),
            'clientes_activos': Cliente.objects.filter(cierrepayroll__isnull=False).distinct().count(),
        }


class ResumenCierreView(LoginRequiredMixin, TemplateView):
    """
    Vista de resumen detallado de un cierre específico
    """
    template_name = 'payroll/dashboard/resumen_cierre.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cierre_id = kwargs.get('cierre_id')
        
        context['cierre'] = get_object_or_404(CierrePayroll, pk=cierre_id)
        context['resumen'] = self.get_resumen_cierre(context['cierre'])
        
        return context
    
    def get_resumen_cierre(self, cierre):
        """
        Genera resumen completo del cierre
        """
        empleados = Empleados_Cierre.objects.filter(cierre_payroll=cierre)
        items = Item_Cierre.objects.filter(cierre_payroll=cierre)
        incidencias = Incidencias_Cierre.objects.filter(cierre_payroll=cierre)
        
        return {
            'empleados': {
                'total': empleados.count(),
                'procesados': empleados.filter(estado_procesamiento='procesado').count(),
                'pendientes': empleados.filter(estado_procesamiento='pendiente').count(),
                'con_errores': empleados.filter(estado_procesamiento='error').count(),
                'total_liquido': empleados.aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0,
            },
            'items': {
                'total': items.count(),
                'haberes': items.filter(tipo_item='haberes').count(),
                'descuentos': items.filter(tipo_item='descuentos').count(),
                'variables': items.filter(es_variable=True).count(),
            },
            'incidencias': {
                'total': incidencias.count(),
                'abiertas': incidencias.filter(estado='abierta').count(),
                'resueltas': incidencias.filter(estado='resuelta').count(),
                'criticas': incidencias.filter(prioridad='critica').count(),
            },
            'progreso': cierre.get_progreso_porcentaje(),
            'tiempo_procesamiento': cierre.get_tiempo_procesamiento(),
        }


class EstadisticasView(LoginRequiredMixin, TemplateView):
    """
    Vista de estadísticas avanzadas del sistema
    """
    template_name = 'payroll/dashboard/estadisticas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Periodo de análisis (últimos 6 meses por defecto)
        periodo = self.request.GET.get('periodo', '6')
        try:
            meses_atras = int(periodo)
        except ValueError:
            meses_atras = 6
        
        fecha_desde = timezone.now() - timedelta(days=30 * meses_atras)
        
        context['estadisticas'] = self.get_estadisticas_periodo(fecha_desde)
        context['periodo_seleccionado'] = meses_atras
        
        return context
    
    def get_estadisticas_periodo(self, fecha_desde):
        """
        Genera estadísticas para el periodo especificado
        """
        cierres = CierrePayroll.objects.filter(fecha_creacion__gte=fecha_desde)
        
        # Estadísticas por mes
        por_mes = cierres.extra(
            select={'mes': "DATE_FORMAT(fecha_creacion, '%%Y-%%m')"}
        ).values('mes').annotate(
            total_cierres=Count('id'),
            total_empleados=Sum('empleados_cierre__count')
        ).order_by('mes')
        
        # Estadísticas por cliente
        por_cliente = cierres.values(
            'cliente__nombre'
        ).annotate(
            total_cierres=Count('id'),
            promedio_empleados=Avg('empleados_cierre__count')
        ).order_by('-total_cierres')[:10]
        
        # Tiempo promedio de procesamiento
        cierres_completados = cierres.filter(
            estado='completado',
            fecha_fin_procesamiento__isnull=False
        )
        
        return {
            'total_cierres': cierres.count(),
            'por_mes': list(por_mes),
            'por_cliente': list(por_cliente),
            'tiempo_promedio_procesamiento': self.calcular_tiempo_promedio(cierres_completados),
            'tasa_exito': self.calcular_tasa_exito(cierres),
        }
    
    def calcular_tiempo_promedio(self, cierres):
        """
        Calcula tiempo promedio de procesamiento
        """
        tiempos = []
        for cierre in cierres:
            if cierre.fecha_inicio_procesamiento and cierre.fecha_fin_procesamiento:
                delta = cierre.fecha_fin_procesamiento - cierre.fecha_inicio_procesamiento
                tiempos.append(delta.total_seconds() / 3600)  # En horas
        
        if tiempos:
            return sum(tiempos) / len(tiempos)
        return 0
    
    def calcular_tasa_exito(self, cierres):
        """
        Calcula tasa de éxito (cierres completados sin incidencias críticas)
        """
        total = cierres.count()
        if total == 0:
            return 0
        
        exitosos = cierres.filter(
            estado='completado'
        ).exclude(
            incidencias_cierre__prioridad='critica',
            incidencias_cierre__estado='abierta'
        ).count()
        
        return (exitosos / total) * 100


# ============================================================================
#                           AJAX VIEWS
# ============================================================================

@login_required
def dashboard_stats_ajax(request):
    """
    Vista AJAX para obtener estadísticas actualizadas del dashboard
    """
    now = timezone.now()
    hoy = now.replace(hour=0, minute=0, second=0, microsecond=0)
    esta_semana = now - timedelta(days=7)
    este_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'hoy': {
            'cierres_creados': CierrePayroll.objects.filter(fecha_creacion__gte=hoy).count(),
            'empleados_procesados': Empleados_Cierre.objects.filter(
                fecha_procesamiento__gte=hoy
            ).count(),
            'incidencias_nuevas': Incidencias_Cierre.objects.filter(
                fecha_creacion__gte=hoy
            ).count(),
        },
        'semana': {
            'cierres_completados': CierrePayroll.objects.filter(
                estado='completado',
                fecha_fin_procesamiento__gte=esta_semana
            ).count(),
            'promedio_empleados': Empleados_Cierre.objects.filter(
                cierre_payroll__fecha_creacion__gte=esta_semana
            ).count(),
        },
        'mes': {
            'total_cierres': CierrePayroll.objects.filter(fecha_creacion__gte=este_mes).count(),
            'total_liquido': Empleados_Cierre.objects.filter(
                cierre_payroll__fecha_creacion__gte=este_mes
            ).aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0,
        }
    }
    
    return JsonResponse(stats)


@login_required
def cierres_por_estado_ajax(request):
    """
    Vista AJAX para obtener distribución de cierres por estado
    """
    distribucion = CierrePayroll.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    return JsonResponse({
        'distribucion': list(distribucion),
        'timestamp': timezone.now().isoformat()
    })


@login_required
def actividad_tiempo_real_ajax(request):
    """
    Vista AJAX para obtener actividad en tiempo real
    """
    # Últimos 30 minutos
    desde = timezone.now() - timedelta(minutes=30)
    
    actividad = Logs_Actividad.objects.filter(
        timestamp__gte=desde
    ).select_related('cierre_payroll__cliente', 'usuario').order_by('-timestamp')[:20]
    
    eventos = []
    for log in actividad:
        eventos.append({
            'timestamp': log.timestamp.isoformat(),
            'usuario': log.usuario.username,
            'accion': log.get_accion_display(),
            'cierre': f"{log.cierre_payroll.cliente.nombre} - {log.cierre_payroll.periodo}",
            'resultado': log.resultado,
            'descripcion_corta': log.descripcion[:50] + '...' if len(log.descripcion) > 50 else log.descripcion
        })
    
    return JsonResponse({
        'eventos': eventos,
        'total': len(eventos)
    })


@login_required
def metricas_rendimiento_ajax(request):
    """
    Vista AJAX para métricas de rendimiento del sistema
    """
    # Últimas 24 horas
    desde = timezone.now() - timedelta(hours=24)
    
    # Tiempo promedio de operaciones
    logs_con_duracion = Logs_Actividad.objects.filter(
        timestamp__gte=desde,
        resultado='exitoso'
    )
    
    # Operaciones por hora
    operaciones_hora = []
    for i in range(24):
        hora_inicio = timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
        hora_fin = hora_inicio + timedelta(hours=1)
        
        count = logs_con_duracion.filter(
            timestamp__gte=hora_inicio,
            timestamp__lt=hora_fin
        ).count()
        
        operaciones_hora.append({
            'hora': hora_inicio.strftime('%H:00'),
            'operaciones': count
        })
    
    # Errores por tipo
    errores_tipo = Logs_Actividad.objects.filter(
        timestamp__gte=desde,
        resultado='error'
    ).values('accion').annotate(
        total=Count('id')
    ).order_by('-total')
    
    return JsonResponse({
        'operaciones_hora': list(reversed(operaciones_hora)),
        'errores_tipo': list(errores_tipo),
        'total_operaciones': logs_con_duracion.count(),
        'periodo': '24 horas'
    })
