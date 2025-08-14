# ============================================================================
#                           REPORTES VIEWS
# ============================================================================

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Sum, Count

from ..models import CierrePayroll, Empleados_Cierre, Incidencias_Cierre


class ReporteNominaView(LoginRequiredMixin, TemplateView):
    """Vista para reporte de nómina"""
    template_name = 'payroll/reportes/nomina.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cierre_id = kwargs.get('cierre_id')
        context['cierre'] = get_object_or_404(CierrePayroll, pk=cierre_id)
        return context


class ReporteIncidenciasView(LoginRequiredMixin, TemplateView):
    """Vista para reporte de incidencias"""
    template_name = 'payroll/reportes/incidencias.html'


class ReporteComparacionView(LoginRequiredMixin, TemplateView):
    """Vista para reporte de comparación"""
    template_name = 'payroll/reportes/comparacion.html'


@login_required
def reporte_estadisticas_ajax(request, cierre_id):
    """Vista AJAX para estadísticas del reporte"""
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    stats = {
        'total_empleados': cierre.empleados_cierre.count(),
        'total_liquido': cierre.empleados_cierre.aggregate(
            Sum('liquido_pagar'))['liquido_pagar__sum'] or 0,
        'incidencias_criticas': cierre.incidencias_cierre.filter(
            prioridad='critica').count()
    }
    
    return JsonResponse(stats)
