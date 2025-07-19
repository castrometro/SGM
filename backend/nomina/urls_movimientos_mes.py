"""
URLs específicas para MovimientosMes y sus modelos relacionados
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_movimientos_mes import (
    MovimientosMesUploadViewSet,
    MovimientoAltaBajaViewSet,
    MovimientoAusentismoViewSet,
    MovimientoVacacionesViewSet,
    MovimientoVariacionSueldoViewSet,
    MovimientoVariacionContratoViewSet,
)

# Crear router para los ViewSets
router = DefaultRouter()

# Registrar ViewSets de MovimientosMes
router.register(r'movimientos-mes', MovimientosMesUploadViewSet, basename='movimientos-mes')
router.register(r'movimientos-altas-bajas', MovimientoAltaBajaViewSet, basename='movimientos-altas-bajas')
router.register(r'movimientos-ausentismo', MovimientoAusentismoViewSet, basename='movimientos-ausentismo')
router.register(r'movimientos-vacaciones', MovimientoVacacionesViewSet, basename='movimientos-vacaciones')
router.register(r'movimientos-variacion-sueldo', MovimientoVariacionSueldoViewSet, basename='movimientos-variacion-sueldo')
router.register(r'movimientos-variacion-contrato', MovimientoVariacionContratoViewSet, basename='movimientos-variacion-contrato')

# URLs patterns para MovimientosMes
urlpatterns = [
    # Incluir las rutas del router
    path('', include(router.urls)),
]
