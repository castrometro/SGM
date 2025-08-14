# ============================================================================
#                           AUSENTISMOS VIEWS
# ============================================================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy

from ..models import Ausentismos_Cierre


class AusentismosCierreListView(LoginRequiredMixin, ListView):
    """Vista de lista de ausentismos"""
    model = Ausentismos_Cierre
    template_name = 'payroll/ausentismos/list.html'
    context_object_name = 'ausentismos'


class AusentismosCierreCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear ausentismo"""
    model = Ausentismos_Cierre
    template_name = 'payroll/ausentismos/create.html'
    fields = ['empleado', 'tipo_ausentismo', 'fecha_inicio', 'fecha_fin', 'dias_ausentismo']
    success_url = reverse_lazy('payroll:ausentismos_list')
