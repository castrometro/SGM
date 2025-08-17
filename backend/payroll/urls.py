# payroll/urls.py
from django.urls import path
from .views import clientes_views

app_name = "payroll"

urlpatterns = [
    # Endpoints para obtener clientes con información de payroll
    path('clientes/asignados/', clientes_views.clientes_asignados_payroll, name='clientes_asignados_payroll'),
    path('clientes/por-area/', clientes_views.clientes_por_area_payroll, name='clientes_por_area_payroll'),
]
