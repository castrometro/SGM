# ============================================================================
#                           INGRESOS VIEWS
# ============================================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy

from ..models import Ingresos_Cierre


class IngresosCierreListView(LoginRequiredMixin, ListView):
    """Vista de lista de ingresos"""
    model = Ingresos_Cierre
    template_name = 'payroll/ingresos/list.html'
    context_object_name = 'ingresos'


class IngresosCierreCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear ingreso"""
    model = Ingresos_Cierre
    template_name = 'payroll/ingresos/create.html'
    fields = ['empleado', 'tipo_ingreso', 'monto', 'fecha_ingreso']
    success_url = reverse_lazy('payroll:ingresos_list')
