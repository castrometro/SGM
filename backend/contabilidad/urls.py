from django.conf import settings
from django.urls import include, path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from .views import (
    AccountClassificationViewSet,
    AnalisisCuentaCierreViewSet,
    AperturaCuentaViewSet,
    AuxiliarViewSet,
    CentroCostoViewSet,
    CierreContabilidadViewSet,
    ClasificacionCuentaArchivoViewSet,
    ClasificacionOptionViewSet,
    ClasificacionSetViewSet,
    ClasificacionViewSet,
    CuentaContableViewSet,
    IncidenciaViewSet,
    LibroMayorUploadViewSet,
    MovimientoContableViewSet,
    NombreInglesViewSet,
    NombresEnInglesUploadViewSet,
    NombresEnInglesView,
    TarjetaActivityLogViewSet,
    TipoDocumentoViewSet,
    cargar_clasificacion_bulk,
    cargar_nombres_ingles,
    cargar_tipo_documento,
    cuentas_pendientes_set,
    eliminar_nombres_ingles,
    eliminar_tipos_documento,
    eliminar_todos_nombres_ingles_upload,
    estado_nombres_ingles,
    estado_tipo_documento,
    estado_upload_log,
    historial_uploads_cliente,
    limpiar_archivos_temporales,
    nombres_ingles_cliente,
    registrar_vista_clasificaciones,
    registrar_vista_nombres_ingles,
    registrar_vista_tipos_documento,
    resumen_cliente,
    test_celery,
    tipos_documento_cliente,
)

router = DefaultRouter()
router.register(r"cuentas", CuentaContableViewSet)
router.register(r"tipos-documento", TipoDocumentoViewSet)
router.register(r"nombres-ingles", NombreInglesViewSet)
router.register(r"cierres", CierreContabilidadViewSet, basename="cierres")
router.register(r"libromayor", LibroMayorUploadViewSet, basename="libromayor")
router.register(r"aperturas", AperturaCuentaViewSet)
router.register(r"movimientos", MovimientoContableViewSet)
router.register(r"clasificaciones-set", ClasificacionSetViewSet)
router.register(r"clasificaciones-opcion", ClasificacionOptionViewSet)
router.register(r"clasificaciones", AccountClassificationViewSet)
router.register(
    r"clasificacion", ClasificacionViewSet, basename="clasificacion"
)  # <--- ¡aquí!
router.register(r"incidencias", IncidenciaViewSet)
router.register(r"centros-costo", CentroCostoViewSet)
router.register(r"auxiliares", AuxiliarViewSet)
router.register(r"analisis-cuentas", AnalisisCuentaCierreViewSet)
router.register(
    r"clasificacion-archivo",
    ClasificacionCuentaArchivoViewSet,
    basename="clasificacion-archivo",
)
router.register(
    r"nombres-ingles-upload",
    NombresEnInglesUploadViewSet,
    basename="nombres-ingles-upload",
)
router.register(r"activity-logs", TarjetaActivityLogViewSet, basename="activity-logs")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "cierres/<int:pk>/movimientos-resumen/",
        CierreContabilidadViewSet.as_view({"get": "movimientos_resumen"}),
        name="cierre-movimientos-resumen",
    ),
    path(
        "cierres/<int:pk>/cuentas/<int:cuenta_id>/movimientos/",
        CierreContabilidadViewSet.as_view({"get": "movimientos_cuenta"}),
        name="cierre-cuenta-movimientos",
    ),
    path("clientes/<int:cliente_id>/resumen/", resumen_cliente),
    path("tipo-documento/subir-archivo/", cargar_tipo_documento),
    path("clasificacion-bulk/subir-archivo/", cargar_clasificacion_bulk),
    path("tipo-documento/<int:cliente_id>/estado/", estado_tipo_documento),
    path("tipo-documento/<int:cliente_id>/list/", tipos_documento_cliente),
    path(
        "tipo-documento/<int:cliente_id>/registrar-vista/",
        registrar_vista_tipos_documento,
    ),
    path("tipo-documento/<int:cliente_id>/eliminar-todos/", eliminar_tipos_documento),
    path("nombres-ingles-crud/subir-archivo/", cargar_nombres_ingles),
    path("nombres-ingles-crud/<int:cliente_id>/estado/", estado_nombres_ingles),
    path("nombres-ingles-crud/<int:cliente_id>/list/", nombres_ingles_cliente),
    path(
        "nombres-ingles-crud/<int:cliente_id>/registrar-vista/",
        registrar_vista_nombres_ingles,
    ),
    path(
        "nombres-ingles-crud/<int:cliente_id>/eliminar-todos/", eliminar_nombres_ingles
    ),
    path(
        "clasificacion/<int:cliente_id>/registrar-vista/",
        registrar_vista_clasificaciones,
    ),
    path("nombres-ingles-upload/eliminar-todos/", eliminar_todos_nombres_ingles_upload),
    path(
        "clientes/<int:cliente_id>/sets/<int:set_id>/cuentas_pendientes/",
        cuentas_pendientes_set,
    ),
    path("nombres-ingles/", NombresEnInglesView.as_view(), name="nombres_ingles"),
    path("test-celery/", test_celery),
    path("limpiar-archivos-temporales/", limpiar_archivos_temporales),
    # URLs para UploadLog
    path("upload-log/<int:upload_log_id>/estado/", estado_upload_log),
    path("clientes/<int:cliente_id>/uploads/", historial_uploads_cliente),
    path(
        "plantilla-tipo-doc/",
        serve,
        {
            "document_root": settings.BASE_DIR / "static/plantillas",
            "path": "plantilla_tipo_documento.xlsx",
        },
        name="descargar_plantilla_tipo_doc",
    ),
    path(
        "plantilla-clasificacion-bulk/",
        serve,
        {
            "document_root": settings.BASE_DIR / "static/plantillas",
            "path": "plantilla_clasificacion.xlsx",
        },
        name="descargar_plantilla_clasificacion_bulk",
    ),
]
