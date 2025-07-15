from django.conf import settings
from django.urls import include, path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from .views import libro_mayor
from .views.actividad import (
    TarjetaActivityLogViewSet,
    registrar_actividad_crud,
)
# Imports para cache Redis
from .views.cache_views import (
    get_kpis_with_cache,
    get_estado_financiero_with_cache,
    get_movimientos_with_cache,
    get_procesamiento_status_with_cache,
    invalidar_cache_cliente,
    get_cache_stats,
    get_cache_health,
    set_kpis_cache,
    set_estado_financiero_cache,
    set_movimientos_cache,
    set_procesamiento_status_cache,
    # Endpoints de pruebas
    set_prueba_esf,
    get_prueba_esf,
    set_prueba_data,
    get_prueba_data,
    list_pruebas_cliente,
    invalidate_pruebas_cliente,
    capture_current_esf,
)
# Views para gerentes
from .views.gerente import (
    obtener_logs_actividad,
    obtener_estadisticas_actividad,
    obtener_usuarios_actividad,
    obtener_estados_cierres,
    obtener_metricas_cierres,
    obtener_estado_cache,
    obtener_cierres_en_cache,
    cargar_cierre_a_cache,
    limpiar_cache,
    # Nuevas funciones añadidas
    gestionar_usuarios,
    actualizar_usuario,
    eliminar_usuario,
    gestionar_clientes,
    obtener_areas,
    obtener_metricas_sistema,
    obtener_metricas_cache,
    forzar_recalculo_cierre,
    obtener_usuarios_conectados,
    # Funciones para estados de cierres
    obtener_historial_cierre,
    obtener_dashboard_cierres,
    debug_cierres,
)
from .views.incidencias import (
    obtener_incidencias_consolidadas,
    obtener_incidencias_consolidadas_optimizado,
    obtener_historial_incidencias,
    dashboard_incidencias,
    marcar_incidencia_resuelta,
    historial_reprocesamiento,
    resumen_tipos_incidencia,
    estadisticas_globales_incidencias,
    estado_cache_incidencias,
    limpiar_cache_incidencias,
)
from .views.excepciones import (
    marcar_cuenta_no_aplica,
    listar_excepciones_cuenta,
    eliminar_excepcion,
    eliminar_excepcion_clasificacion,
)
from .views.cuenta_clasificaciones import (
    crear_cuenta_con_clasificaciones,
    actualizar_cuenta_con_clasificaciones,
    eliminar_cuenta_con_clasificaciones,
    clasificacion_masiva_cuentas,
)
from .views.reprocesamiento import (
    reprocesar_libro_mayor_con_excepciones,
    obtener_historial_reprocesamiento,
    cambiar_iteracion_principal,
)
from .views import (
    LibroMayorArchivoViewSet,  # ✅ Nuevo ViewSet
    TipoDocumentoViewSet,
    NombreInglesViewSet,
    # ClasificacionCuentaArchivoViewSet,  # OBSOLETO - ELIMINADO EN REDISEÑO
    CuentaContableViewSet,
    AperturaCuentaViewSet,
    MovimientoContableViewSet,
    CierreContabilidadViewSet,
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
    cargar_tipo_documento,
    cargar_nombres_ingles,
    cargar_clasificacion_bulk,
    # Incidencias consolidadas
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
    estado_clasificaciones,
    # Funciones de clasificación persistente (ya incluidas desde __init__.py)
    obtener_clasificaciones_persistentes_detalladas,
    registrar_vista_clasificaciones_persistentes,
    clasificacion_masiva_persistente,
    obtener_estadisticas_clasificaciones_persistentes,
    crear_registro_clasificacion_completo,
    actualizar_registro_clasificacion_completo,
    eliminar_registro_clasificacion_completo,
    # Utilidades
    test_celery,
    limpiar_archivos_temporales,
    estado_upload_log,
)

# Ya no necesitamos importar desde views_legacy

router = DefaultRouter()
router.register(r"cuentas", CuentaContableViewSet)
router.register(r"tipos-documento", TipoDocumentoViewSet)
router.register(r"nombres-ingles", NombreInglesViewSet)
router.register(r"cierres", CierreContabilidadViewSet, basename="cierres")
router.register(r"libromayor-archivo", LibroMayorArchivoViewSet, basename="libromayor-archivo")  # ✅ Nuevo endpoint
router.register(r"aperturas", AperturaCuentaViewSet)
router.register(r"movimientos", MovimientoContableViewSet)
# router.register(r"clasificacion-archivo", ClasificacionCuentaArchivoViewSet, basename="clasificacion-archivo")  # OBSOLETO - ELIMINADO
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
    # Rutas específicas de clasificaciones (DEBEN IR ANTES del router)
    path("clasificaciones/registro-completo/", 
         crear_registro_clasificacion_completo, 
         name="crear_registro_clasificacion_completo"),
    path("clasificaciones/registro-completo/<str:cuenta_codigo>/", 
         actualizar_registro_clasificacion_completo, 
         name="actualizar_registro_clasificacion_completo"),
    path("clasificaciones/registro-completo/<str:cuenta_codigo>/delete/", 
         eliminar_registro_clasificacion_completo, 
         name="eliminar_registro_clasificacion_completo"),
    
    # Router con ViewSets (incluye el resto de endpoints)
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
    #path("libro-mayor/reprocesar-incompletos/", reprocesar_movimientos_incompletos),
    #path("libro-mayor/incompletos/<int:cierre_id>/", movimientos_incompletos),
    path("tipo-documento/subir-archivo/", cargar_tipo_documento),
    path("clasificacion-bulk/subir-archivo/", cargar_clasificacion_bulk),
    path("nombre-ingles/subir-archivo/", cargar_nombres_ingles),
    
    # URLs para Incidencias Consolidadas
    path("dashboard/<int:cliente_id>/incidencias/", dashboard_incidencias, name="dashboard_incidencias"),
    path("incidencias/<int:incidencia_id>/resolver/", marcar_incidencia_resuelta, name="resolver_incidencia"),
    path("upload-log/<int:upload_log_id>/historial/", historial_reprocesamiento, name="historial_reprocesamiento"),
    path("incidencias/tipos/", resumen_tipos_incidencia, name="tipos_incidencia"),
    path("incidencias/estadisticas/", estadisticas_globales_incidencias, name="estadisticas_globales"),
    
    # Gestión de caché de incidencias
    path("cache/incidencias/estado/", estado_cache_incidencias, name="estado_cache_incidencias"),
    path("cache/incidencias/limpiar/", limpiar_cache_incidencias, name="limpiar_cache_incidencias"),
    
    # URLs para Incidencias del Libro Mayor (para el modal del frontend)
    path("libro-mayor/<int:cierre_id>/incidencias-consolidadas/", 
         obtener_incidencias_consolidadas, 
         name="incidencias_consolidadas_libro_mayor"),
    path("libro-mayor/<int:cierre_id>/incidencias-optimizado/", 
         obtener_incidencias_consolidadas_optimizado, 
         name="incidencias_consolidadas_optimizado"),
    path("libro-mayor/<int:cierre_id>/historial-incidencias/", 
         obtener_historial_incidencias, 
         name="historial_incidencias"),
    
    # Excepciones de validación
    path("libro-mayor/marcar-no-aplica/", marcar_cuenta_no_aplica, name="marcar_cuenta_no_aplica"),
    path("libro-mayor/excepciones/<str:codigo_cuenta>/", listar_excepciones_cuenta, name="listar_excepciones_cuenta"),
    path("libro-mayor/excepciones/<int:excepcion_id>/eliminar/", eliminar_excepcion, name="eliminar_excepcion"),
    path("libro-mayor/excepciones/clasificacion/eliminar/", eliminar_excepcion_clasificacion, name="eliminar_excepcion_clasificacion"),
    
    # Reprocesamiento
    path("libro-mayor/reprocesar-con-excepciones/", reprocesar_libro_mayor_con_excepciones, name="reprocesar_libro_mayor"),
    path("libro-mayor/<int:cierre_id>/historial-reprocesamiento/", obtener_historial_reprocesamiento, name="historial_reprocesamiento"),
    path("libro-mayor/cambiar-iteracion-principal/", cambiar_iteracion_principal, name="cambiar_iteracion_principal"),
    
    # Clientes y estados
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
    path("clasificacion/<int:cliente_id>/registrar-vista/", registrar_vista_clasificaciones),
    
    # Clasificaciones persistentes (base de datos)
    path("clientes/<int:cliente_id>/clasificaciones/detalladas/", 
         obtener_clasificaciones_persistentes_detalladas, 
         name="clasificaciones_persistentes_detalladas"),
    path("clientes/<int:cliente_id>/clasificaciones/registrar-vista/", 
         registrar_vista_clasificaciones_persistentes, 
         name="registrar_vista_clasificaciones_persistentes"),
    
    # Nombres en inglés
    path("nombre-ingles/<int:cliente_id>/estado/", estado_nombres_ingles),
    path("nombre-ingles/<int:cliente_id>/list/", nombres_ingles_cliente),
    path("nombre-ingles/<int:cliente_id>/registrar-vista/", registrar_vista_nombres_ingles),
    path("nombre-ingles/<int:cliente_id>/eliminar-todos/", eliminar_nombres_ingles),
    path("nombres-ingles-upload/eliminar-todos/", eliminar_todos_nombres_ingles_upload),
    path("nombres-ingles/", NombresEnInglesView.as_view(), name="nombres_ingles"),
    
    # Upload logs
    path("upload-log/<int:upload_log_id>/estado/", estado_upload_log),
    
    # Logging de actividades
    path("registrar-actividad/", registrar_actividad_crud, name="registrar_actividad_crud"),
    
    # Finalización de cierres
    path("", include("contabilidad.urls_finalizacion")),
    
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
    
    # ===================================
    # SISTEMA DE CACHE REDIS - SGM
    # ===================================
    
    # Endpoints de lectura (GET) con cache
    path("cache/kpis/<int:cliente_id>/<str:periodo>/", 
         get_kpis_with_cache, 
         name="cache_get_kpis"),
    
    path("cache/estado-financiero/<int:cliente_id>/<str:periodo>/<str:tipo_estado>/", 
         get_estado_financiero_with_cache, 
         name="cache_get_estado_financiero"),
    
    path("cache/movimientos/<int:cliente_id>/<str:periodo>/", 
         get_movimientos_with_cache, 
         name="cache_get_movimientos"),
    
    path("cache/procesamiento/<int:cliente_id>/<str:periodo>/", 
         get_procesamiento_status_with_cache, 
         name="cache_get_procesamiento"),
    
    # Endpoints de escritura (POST) para cache
    path("cache/kpis/<int:cliente_id>/<str:periodo>/set/", 
         set_kpis_cache, 
         name="cache_set_kpis"),
    
    path("cache/estado-financiero/<int:cliente_id>/<str:periodo>/<str:tipo_estado>/set/", 
         set_estado_financiero_cache, 
         name="cache_set_estado_financiero"),
    
    path("cache/movimientos/<int:cliente_id>/<str:periodo>/set/", 
         set_movimientos_cache, 
         name="cache_set_movimientos"),
    
    path("cache/procesamiento/<int:cliente_id>/<str:periodo>/set/", 
         set_procesamiento_status_cache, 
         name="cache_set_procesamiento"),
    
    # Gestión del cache
    path("cache/invalidar/<int:cliente_id>/", 
         invalidar_cache_cliente, 
         name="cache_invalidar_cliente"),
    
    path("cache/invalidar/<int:cliente_id>/<str:periodo>/", 
         invalidar_cache_cliente, 
         name="cache_invalidar_cliente_periodo"),
    
    # Monitoreo del cache
    path("cache/stats/", 
         get_cache_stats, 
         name="cache_stats"),
    
    path("cache/health/", 
         get_cache_health, 
         name="cache_health"),
    
    # ===============================================
    # ENDPOINTS DE PRUEBAS - SISTEMA DE CACHE
    # ===============================================
    
    # ESF de pruebas
    path("cache/pruebas/esf/<int:cliente_id>/<str:periodo>/", 
         set_prueba_esf, 
         name="cache_set_prueba_esf"),
    
    path("cache/pruebas/esf/<int:cliente_id>/<str:periodo>/get/", 
         get_prueba_esf, 
         name="cache_get_prueba_esf"),
    
    # Datos de prueba genéricos
    path("cache/pruebas/<str:data_type>/<int:cliente_id>/<str:periodo>/", 
         set_prueba_data, 
         name="cache_set_prueba_data"),
    
    path("cache/pruebas/<str:data_type>/<int:cliente_id>/<str:periodo>/get/", 
         get_prueba_data, 
         name="cache_get_prueba_data"),
    
    # Gestión de pruebas
    path("cache/pruebas/list/<int:cliente_id>/", 
         list_pruebas_cliente, 
         name="cache_list_pruebas_cliente"),
    
    path("cache/pruebas/invalidate/<int:cliente_id>/", 
         invalidate_pruebas_cliente, 
         name="cache_invalidate_pruebas_cliente"),
    
    # Captura ESF del sistema actual
    path("cache/pruebas/capture-esf/<int:cliente_id>/<str:periodo>/", 
         capture_current_esf, 
         name="cache_capture_current_esf"),
    
    # CRUD de cuentas con clasificaciones
    path("cuentas/crear/", crear_cuenta_con_clasificaciones, name="crear_cuenta_clasificaciones"),
    path("cuentas/<int:cuenta_id>/actualizar/", actualizar_cuenta_con_clasificaciones, name="actualizar_cuenta_clasificaciones"),
    path("cuentas/<int:cuenta_id>/eliminar/", eliminar_cuenta_con_clasificaciones, name="eliminar_cuenta_clasificaciones"),
    path("cuentas/clasificacion-masiva/", clasificacion_masiva_cuentas, name="clasificacion_masiva_cuentas"),
    
    # ===================================
    # ENDPOINTS PARA GERENTES
    # ===================================
    
    # Logs y actividad
    path("gerente/logs-actividad/", 
         obtener_logs_actividad, 
         name="gerente_logs_actividad"),
    
    path("gerente/estadisticas-actividad/", 
         obtener_estadisticas_actividad, 
         name="gerente_estadisticas_actividad"),
    
    path("gerente/usuarios-actividad/", 
         obtener_usuarios_actividad, 
         name="gerente_usuarios_actividad"),
    
    # Estados de cierres
    path("gerente/estados-cierres/", 
         obtener_estados_cierres, 
         name="gerente_estados_cierres"),
    
    path("gerente/metricas-cierres/", 
         obtener_metricas_cierres, 
         name="gerente_metricas_cierres"),
    
    # Cache Redis
    path("gerente/estado-cache/", 
         obtener_estado_cache, 
         name="gerente_estado_cache"),
    
    path("gerente/cierres-cache/", 
         obtener_cierres_en_cache, 
         name="gerente_cierres_cache"),
    
    path("gerente/cargar-cierre-cache/", 
         cargar_cierre_a_cache, 
         name="gerente_cargar_cierre_cache"),
    
    path("gerente/limpiar-cache/", 
         limpiar_cache, 
         name="gerente_limpiar_cache"),
    
    # Admin Sistema
    path("gerente/usuarios/", 
         gestionar_usuarios, 
         name="gerente_usuarios"),
    
    path("gerente/usuarios/<int:user_id>/", 
         actualizar_usuario, 
         name="gerente_actualizar_usuario"),
    
    path("gerente/usuarios/<int:user_id>/eliminar/", 
         eliminar_usuario, 
         name="gerente_eliminar_usuario"),
    
    path("gerente/clientes/", 
         gestionar_clientes, 
         name="gerente_clientes"),
    
    path("gerente/areas/", 
         obtener_areas, 
         name="gerente_areas"),
    
    path("gerente/metricas-sistema/", 
         obtener_metricas_sistema, 
         name="gerente_metricas_sistema"),
    
    path("gerente/metricas-cache/", 
         obtener_metricas_cache, 
         name="gerente_metricas_cache"),
    
    path("gerente/cierres/<int:cierre_id>/recalcular/", 
         forzar_recalculo_cierre, 
         name="gerente_forzar_recalculo"),
    
    path("gerente/usuarios-conectados/", 
         obtener_usuarios_conectados, 
         name="gerente_usuarios_conectados"),
    
    # Estados de cierres - Nuevas funcionalidades
    path("gerente/historial-cierre/<int:cierre_id>/", 
         obtener_historial_cierre, 
         name="gerente_historial_cierre"),
    
    path("gerente/dashboard-cierres/", 
         obtener_dashboard_cierres, 
         name="gerente_dashboard_cierres"),
    
    # Debug endpoint
    path("gerente/debug-cierres/", 
         debug_cierres, 
         name="gerente_debug_cierres"),
]