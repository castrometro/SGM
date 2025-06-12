from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AreaViewSet, UsuarioViewSet, ClienteViewSet,
    ServicioViewSet, ServicioClienteViewSet, ContratoViewSet,
    AsignacionClienteUsuarioViewSet, AnalistaPerformanceViewSet, ping,
    DashboardViewSet, AnalistasDetalladoViewSet,
    clientes_disponibles, clientes_asignados, remover_asignacion
)

router = DefaultRouter()
router.register(r'areas', AreaViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'servicio-clientes', ServicioClienteViewSet, basename='servicio-cliente')
router.register(r'contratos', ContratoViewSet)
router.register(r'asignaciones', AsignacionClienteUsuarioViewSet, basename='asignaciones')
router.register(r'bi-analistas', AnalistaPerformanceViewSet, basename='bi-analistas')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'analistas-detallado', AnalistasDetalladoViewSet, basename='analistas-detallado')

urlpatterns = [
    path('', include(router.urls)),
    path('clientes-disponibles/<int:analista_id>/', clientes_disponibles, name='clientes-disponibles'),
    path('clientes-asignados/<int:analista_id>/', clientes_asignados, name='clientes-asignados'),
    path('asignaciones/<int:analista_id>/<int:cliente_id>/', remover_asignacion, name='remover-asignacion'),
    # URLs específicas del gerente
    path('gerente/', include('api.urls_gerente')),
]
