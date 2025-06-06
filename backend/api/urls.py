from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AreaViewSet, UsuarioViewSet, ClienteViewSet,
    ServicioViewSet, ServicioClienteViewSet, ContratoViewSet, AsignacionClienteUsuarioViewSet, ping
)

router = DefaultRouter()
router.register(r'areas', AreaViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'servicio-clientes', ServicioClienteViewSet, basename='servicio-cliente')
router.register(r'contratos', ContratoViewSet)
router.register(r'asignaciones', AsignacionClienteUsuarioViewSet, basename='asignaciones')

urlpatterns = [
    path('', include(router.urls)),
]
