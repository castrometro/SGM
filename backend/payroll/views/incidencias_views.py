# ============================================================================
#                           INCIDENCIAS VIEWS
# ============================================================================

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse

from ..models import Incidencias_Cierre, CierrePayroll


class IncidenciasCierreListView(LoginRequiredMixin, ListView):
    """Vista de lista de incidencias"""
    model = Incidencias_Cierre
    template_name = 'payroll/incidencias/list.html'
    context_object_name = 'incidencias'
    paginate_by = 30
    
    def get_queryset(self):
        cierre_id = self.kwargs.get('cierre_id')
        return Incidencias_Cierre.objects.filter(
            cierre_payroll_id=cierre_id
        ).order_by('-fecha_creacion')


class IncidenciasCierreDetailView(LoginRequiredMixin, DetailView):
    """Vista detalle de incidencia"""
    model = Incidencias_Cierre
    template_name = 'payroll/incidencias/detail.html'
    context_object_name = 'incidencia'
