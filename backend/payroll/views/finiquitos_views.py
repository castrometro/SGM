# ============================================================================
#                           FINIQUITOS VIEWS
# ============================================================================
# Views para gestión de finiquitos

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse

from ..models import Finiquitos_Cierre, CierrePayroll


class FiniquitosCierreListView(LoginRequiredMixin, ListView):
    """Vista de lista de finiquitos"""
    model = Finiquitos_Cierre
    template_name = 'payroll/finiquitos/list.html'
    context_object_name = 'finiquitos'
    paginate_by = 20
    
    def get_queryset(self):
        cierre_id = self.kwargs.get('cierre_id')
        return Finiquitos_Cierre.objects.filter(
            cierre_payroll_id=cierre_id
        ).select_related('empleado')


class FiniquitosCierreDetailView(LoginRequiredMixin, DetailView):
    """Vista detalle de finiquito"""
    model = Finiquitos_Cierre
    template_name = 'payroll/finiquitos/detail.html'
    context_object_name = 'finiquito'
