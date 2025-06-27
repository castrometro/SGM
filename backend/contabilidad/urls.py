from django.conf import settings
from django.urls import include, path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from .views import libro_mayor
from .views import (
    LibroMayorUploadViewSet,
    LibroMayorArchivoViewSet,  # ✅ Nuevo ViewSet
    TipoDocumentoViewSet,
    NombreInglesViewSet,
    ClasificacionCuentaArchivoViewSet,
    CuentaContableViewSet,
    AperturaCuentaViewSet,
    MovimientoContableViewSet,
    CierreContabilidadViewSet,
    TarjetaActivityLogViewSet,
    NombresEnInglesView,
    # ViewSets migrados
    ClasificacionViewSet,
    ClasificacionSetViewSet,
    ClasificacionOptionViewSet,
    AccountClassificationViewSet,
    IncidenciaViewSet,
    CentroCostoViewSet,
    AuxiliarViewSet,
    NombresEnInglesUploadViewSet,
    AnalisisCuentaCierreViewSet,
    # Function views
    cargar_libro_mayor,
    reprocesar_movimientos_incompletos,
    movimientos_incompletos,
    cargar_tipo_documento,
    cargar_nombres_ingles,
    cargar_clasificacion_bulk,
    # Incidencias consolidadas
    obtener_incidencias_consolidadas,
    dashboard_incidencias,
    marcar_incidencia_resuelta,
    historial_reprocesamiento,
    resumen_tipos_incidencia,
    estadisticas_globales_incidencias,
    # Cliente views
    resumen_cliente,
    historial_uploads_cliente,
    estado_tipo_documento,
    detalle_cliente,
    tipos_documento_cliente,
    registrar_vista_tipos_documento,
    eliminar_tipos_documento,
    eliminar_nombres_ingles,
    eliminar_todos_nombres_ingles_upload,
    estado_nombres_ingles,
    nombres_ingles_cliente,
    registrar_vista_nombres_ingles,
    registrar_vista_clasificaciones,
    cuentas_pendientes_set,
    # Utilidades
    test_celery,
    limpiar_archivos_temporales,
    estado_upload_log,
    estado_clasificaciones,
)

# Ya no necesitamos importar desde views_legacy

router = DefaultRouter()
router.register(r"cuentas", CuentaContableViewSet)
router.register(r"tipos-documento", TipoDocumentoViewSet)
router.register(r"nombres-ingles", NombreInglesViewSet)
router.register(r"cierres", CierreContabilidadViewSet, basename="cierres")
router.register(r"libromayor", LibroMayorUploadViewSet, basename="libromayor")
router.register(r"libromayor-archivo", LibroMayorArchivoViewSet, basename="libromayor-archivo")  # ✅ Nuevo endpoint
router.register(r"aperturas", AperturaCuentaViewSet)
router.register(r"movimientos", MovimientoContableViewSet)
router.register(r"clasificacion-archivo", ClasificacionCuentaArchivoViewSet, basename="clasificacion-archivo")
router.register(r"activity-logs", TarjetaActivityLogViewSet, basename="activity-logs")
# ViewSets del archivo original
router.register(r"clasificaciones-set", ClasificacionSetViewSet)
router.register(r"clasificaciones-opcion", ClasificacionOptionViewSet)
router.register(r"clasificaciones", AccountClassificationViewSet)
router.register(r"clasificacion", ClasificacionViewSet, basename="clasificacion")
router.register(r"incidencias", IncidenciaViewSet)
router.register(r"centros-costo", CentroCostoViewSet)
router.register(r"auxiliares", AuxiliarViewSet)
router.register(r"analisis-cuentas", AnalisisCuentaCierreViewSet)
router.register(r"nombres-ingles-upload", NombresEnInglesUploadViewSet, basename="nombres-ingles-upload")

urlpatterns = [
    path("", include(router.urls)),
    # Endpoints específicos de CierreContabilidadViewSet
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
    
    # Uploads y procesamiento
    path("libro-mayor/subir-archivo/", cargar_libro_mayor),
    path("libro-mayor/reprocesar-incompletos/", reprocesar_movimientos_incompletos),
    path("libro-mayor/incompletos/<int:cierre_id>/", movimientos_incompletos),
    path("tipo-documento/subir-archivo/", cargar_tipo_documento),
    path("clasificacion-bulk/subir-archivo/", cargar_clasificacion_bulk),
    path("nombre-ingles/subir-archivo/", cargar_nombres_ingles),
    
    # URLs para Incidencias Consolidadas
    path("incidencias/<int:cierre_id>/", obtener_incidencias_consolidadas, name="incidencias_consolidadas"),
    path("dashboard/<int:cliente_id>/incidencias/", dashboard_incidencias, name="dashboard_incidencias"),
    path("incidencias/<int:incidencia_id>/resolver/", marcar_incidencia_resuelta, name="resolver_incidencia"),
    path("upload-log/<int:upload_log_id>/historial/", historial_reprocesamiento, name="historial_reprocesamiento"),
    path("incidencias/tipos/", resumen_tipos_incidencia, name="tipos_incidencia"),
    path("incidencias/estadisticas/", estadisticas_globales_incidencias, name="estadisticas_globales"),
    
    # Cliente endpoints
    path("clientes/<int:cliente_id>/resumen/", resumen_cliente, name="resumen_cliente"),
    path("clientes/<int:cliente_id>/detalle/", detalle_cliente, name="detalle_cliente"),
    path("clientes/<int:cliente_id>/uploads/", historial_uploads_cliente, name="historial_uploads"),
    path("clientes/<int:cliente_id>/sets/<int:set_id>/cuentas_pendientes/", cuentas_pendientes_set),
    
    # Tipos de documento
    path("tipo-documento/<int:cliente_id>/estado/", estado_tipo_documento, name="estado_tipo_documento"),
    path("tipo-documento/<int:cliente_id>/list/", tipos_documento_cliente, name="tipos_documento_cliente"),
    path("tipo-documento/<int:cliente_id>/registrar-vista/", registrar_vista_tipos_documento, name="registrar_vista_tipos_documento"),
    path("tipo-documento/<int:cliente_id>/eliminar-todos/", eliminar_tipos_documento),
    
    # Clasificaciones
    path("clasificacion/<int:cliente_id>/estado/", estado_clasificaciones, name="estado_clasificaciones"),
    
    # Nombres en inglés
    path("nombre-ingles/<int:cliente_id>/estado/", estado_nombres_ingles),
    path("nombre-ingles/<int:cliente_id>/list/", nombres_ingles_cliente),
    path("nombre-ingles/<int:cliente_id>/registrar-vista/", registrar_vista_nombres_ingles),
    path("nombre-ingles/<int:cliente_id>/eliminar-todos/", eliminar_nombres_ingles),
    path("nombres-ingles-upload/eliminar-todos/", eliminar_todos_nombres_ingles_upload),
    path("nombres-ingles/", NombresEnInglesView.as_view(), name="nombres_ingles"),
    
    # Upload logs
    path("upload-log/<int:upload_log_id>/estado/", estado_upload_log),
    
    # Utilidades
    path("test-celery/", test_celery),
    path("limpiar-archivos-temporales/", limpiar_archivos_temporales),
    
    # Plantillas estáticas
    path("plantilla-tipo-doc/", serve, {
        "document_root": settings.BASE_DIR / "static/plantillas",
        "path": "plantilla_tipo_documento.xlsx",
    }, name="descargar_plantilla_tipo_doc"),
    path("plantilla-clasificacion-bulk/", serve, {
        "document_root": settings.BASE_DIR / "static/plantillas",
        "path": "plantilla_clasificacion.xlsx",
    }, name="descargar_plantilla_clasificacion_bulk"),
    path('libro-mayor/<int:cierre_id>/incidencias-consolidadas/', 
         libro_mayor.incidencias_consolidadas, 
         name='libro_mayor_incidencias_consolidadas'),
    path('libro-mayor/<int:cierre_id>/incidencias/<str:tipo_incidencia>/detalle/',
         libro_mayor.obtener_cuentas_detalle_incidencia, 
         name="detalle_incidencia"),
    path("libro-mayor/marcar-no-aplica/", 
         libro_mayor.marcar_cuenta_no_aplica, 
         name="marcar_no_aplica"),
    path("libro-mayor/reprocesar-con-excepciones/", 
         libro_mayor.reprocesar_con_excepciones, 
         name="reprocesar_con_excepciones"),
]
