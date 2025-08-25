from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CierrePayrollViewSet, ArchivoSubidoViewSet,
    clientes_asignados_payroll, clientes_por_area_payroll, todos_clientes_payroll,
    resumen_cliente_payroll
)

# Crear el router para los ViewSets
router = DefaultRouter()
router.register(r'cierres', CierrePayrollViewSet, basename='cierre')
router.register(r'archivos', ArchivoSubidoViewSet, basename='archivo')
# router.register(r'discrepancias', DiscrepanciaDetectadaViewSet, basename='discrepancia')  # Comentado hasta implementar

app_name = 'payroll'

urlpatterns = [
    # URLs del API REST
    path('api/', include(router.urls)),
    
    # URLs específicas para clientes con información de payroll
    path('api/clientes/asignados/', clientes_asignados_payroll, name='clientes-asignados-payroll'),
    path('api/clientes/por-area/', clientes_por_area_payroll, name='clientes-por-area-payroll'),
    path('api/clientes/todos/', todos_clientes_payroll, name='todos-clientes-payroll'),
    path('api/clientes/<int:cliente_id>/resumen/', resumen_cliente_payroll, name='resumen-cliente-payroll'),
    
    # URLs adicionales si se necesitan vistas específicas
    # path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('reportes/', ReportesView.as_view(), name='reportes'),
]
