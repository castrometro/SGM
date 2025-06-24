from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LibroMayorUploadViewSet,
    TipoDocumentoViewSet,
    NombreInglesViewSet,
    ClasificacionCuentaArchivoViewSet,
    CuentaContableViewSet,
    AperturaCuentaViewSet,
    MovimientoContableViewSet,
    CierreContabilidadViewSet,
    TarjetaActivityLogViewSet,
    cargar_libro_mayor,
    reprocesar_movimientos_incompletos,
    movimientos_incompletos,
    cargar_tipo_documento,
    cargar_nombres_ingles,
)

router = DefaultRouter()
router.register(r"cuentas", CuentaContableViewSet)
router.register(r"tipos-documento", TipoDocumentoViewSet)
router.register(r"nombres-ingles", NombreInglesViewSet)
router.register(r"cierres", CierreContabilidadViewSet, basename="cierres")
router.register(r"libromayor", LibroMayorUploadViewSet, basename="libromayor")
router.register(r"aperturas", AperturaCuentaViewSet)
router.register(r"movimientos", MovimientoContableViewSet)
router.register(r"clasificacion-archivo", ClasificacionCuentaArchivoViewSet, basename="clasificacion-archivo")
router.register(r"activity-logs", TarjetaActivityLogViewSet, basename="activity-logs")

urlpatterns = [
    path("", include(router.urls)),
    path("libro-mayor/subir-archivo/", cargar_libro_mayor),
    path("libro-mayor/reprocesar-incompletos/", reprocesar_movimientos_incompletos),
    path("libro-mayor/incompletos/<int:cierre_id>/", movimientos_incompletos),
    path("tipo-documento/subir-archivo/", cargar_tipo_documento),
    path("nombre-ingles/subir-archivo/", cargar_nombres_ingles),
]
