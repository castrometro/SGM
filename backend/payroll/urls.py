# payroll/urls.py
from django.urls import path
from .views import clientes_views, dashboard_views, cierre_views

app_name = "payroll"

urlpatterns = [
    # Endpoints para obtener clientes con información de payroll
    path('clientes/asignados/', clientes_views.clientes_asignados_payroll, name='clientes_asignados_payroll'),
    path('clientes/por-area/', clientes_views.clientes_por_area_payroll, name='clientes_por_area_payroll'),
    path('clientes/<int:cliente_id>/resumen/', dashboard_views.resumen_cliente_payroll, name='resumen_cliente_payroll'),
    
    # Endpoints para gestión de cierres (movidos a cierre_views.py)
    path('clientes/<int:cliente_id>/cierres/', cierre_views.cierres_cliente_payroll, name='cierres_cliente_payroll'),
    path('clientes/<int:cliente_id>/cierres/crear/', cierre_views.crear_cierre_mensual_payroll, name='crear_cierre_mensual_payroll'),
    path('clientes/<int:cliente_id>/cierres/<str:periodo>/', cierre_views.obtener_cierre_mensual_payroll, name='obtener_cierre_mensual_payroll'),
]
