from rest_framework import routers
from .views import (
    CierreNominaViewSet,
    ChecklistItemViewSet,
    conceptos_remuneracion_por_cliente,
    conceptos_remuneracion_por_cierre,
    obtener_hashtags_disponibles,
    ConceptoRemuneracionBatchView,
    eliminar_concepto_remuneracion,
    obtener_estado_upload_log_nomina,
    # Nuevos endpoints para visualización
    obtener_libro_remuneraciones,
    obtener_movimientos_mes,
    # Endpoint para estadísticas del cierre
    obtener_estadisticas_cierre,
    # Endpoint para historial de verificación
    estadisticas_historial_verificacion,
)

# Importar ViewSets de archivos específicos desde sus módulos dedicados
from .views_archivos_analista import ArchivoAnalistaUploadViewSet, cargar_archivo_analista_con_logging
from .views_archivos_novedades import ArchivoNovedadesUploadViewSet

from .views import (
    # ViewSets para modelos del Analista
    AnalistaFiniquitoViewSet,
    AnalistaIncidenciaViewSet,
    AnalistaIngresoViewSet,
    # ViewSets para modelos de Novedades
    EmpleadoCierreNovedadesViewSet,
    ConceptoRemuneracionNovedadesViewSet,
    RegistroConceptoEmpleadoNovedadesViewSet,
    # ViewSets para Sistema de Incidencias
    IncidenciaCierreViewSet,
    ResolucionIncidenciaViewSet,
    CierreNominaIncidenciasViewSet,
    # ViewSets para Análisis de Datos
    AnalisisDatosCierreViewSet,
    IncidenciaVariacionSalarialViewSet,
    # ViewSets para Sistema de Discrepancias
    DiscrepanciaCierreViewSet,
    CierreNominaDiscrepanciasViewSet,
)
from .views_libro_remuneraciones import LibroRemuneracionesUploadViewSet
from .views_movimientos_mes import (
    MovimientosMesUploadViewSet,
    MovimientoAltaBajaViewSet,
    MovimientoAusentismoViewSet,
    MovimientoVacacionesViewSet,
    MovimientoVariacionSueldoViewSet,
    MovimientoVariacionContratoViewSet,
)
from .api_logging import (
    ModalActivityView,
    FileActivityView,
    ClassificationActivityView,
    SessionActivityView,
    get_activity_log,
    get_all_activity_logs
)

# Importar views de informes
from .views_informes import (
    obtener_informe_cierre,
    obtener_resumen_informe,
    listar_informes_cliente,
    generar_informe_cierre,
)

# Importar views de Redis
from .views_redis import (
    enviar_informe_redis,
    obtener_informe_redis,
    estadisticas_redis,
    limpiar_cache_cliente,
    listar_informes_redis,
    health_check_redis,
)

from django.urls import path
from django.conf import settings
from django.views.static import serve
from .views_nomina_consolidada import obtener_resumen_nomina_consolidada, obtener_detalle_nomina_consolidada
from .views_libro_v2 import libro_resumen_v2
from .views_movimientos_v3 import movimientos_personal_detalle_v3

router = routers.DefaultRouter()
router.register(r'cierres', CierreNominaViewSet)
router.register(r'libros-remuneraciones', LibroRemuneracionesUploadViewSet)
router.register(r'movimientos-mes', MovimientosMesUploadViewSet)
router.register(r'archivos-analista', ArchivoAnalistaUploadViewSet)
router.register(r'archivos-novedades', ArchivoNovedadesUploadViewSet)
router.register(r'checklist-items', ChecklistItemViewSet)

# ViewSets para modelos del Analista
router.register(r'analista-finiquitos', AnalistaFiniquitoViewSet)
router.register(r'analista-incidencias', AnalistaIncidenciaViewSet)
router.register(r'analista-ingresos', AnalistaIngresoViewSet)

# ViewSets para Movimientos del Mes
router.register(r'movimientos-altas-bajas', MovimientoAltaBajaViewSet)
router.register(r'movimientos-ausentismos', MovimientoAusentismoViewSet)
router.register(r'movimientos-vacaciones', MovimientoVacacionesViewSet)
router.register(r'movimientos-variacion-sueldo', MovimientoVariacionSueldoViewSet)
router.register(r'movimientos-variacion-contrato', MovimientoVariacionContratoViewSet)

# ViewSets para modelos de Novedades
router.register(r'empleados-cierre-novedades', EmpleadoCierreNovedadesViewSet)
router.register(r'conceptos-remuneracion-novedades', ConceptoRemuneracionNovedadesViewSet)
router.register(r'registros-concepto-empleado-novedades', RegistroConceptoEmpleadoNovedadesViewSet)

# ViewSets para Sistema de Incidencias
router.register(r'incidencias', IncidenciaCierreViewSet)
router.register(r'resoluciones-incidencias', ResolucionIncidenciaViewSet)
router.register(r'cierres-incidencias', CierreNominaIncidenciasViewSet, basename='cierre-incidencias')

# ViewSets para Análisis de Datos
router.register(r'analisis-datos', AnalisisDatosCierreViewSet)
router.register(r'incidencias-variacion', IncidenciaVariacionSalarialViewSet)

# ViewSets para Sistema de Discrepancias (Verificación de Datos)
router.register(r'discrepancias', DiscrepanciaCierreViewSet)
router.register(r'cierres-discrepancias', CierreNominaDiscrepanciasViewSet, basename='cierre-discrepancias')

urlpatterns = router.urls + [
    path(
        'libros-remuneraciones/<int:pk>/procesar/',
        LibroRemuneracionesUploadViewSet.as_view({'post': 'procesar'}),
        name='procesar-libro-remuneraciones',
    ),
    path(
        'movimientos/estado/<int:cierre_id>/',
        MovimientosMesUploadViewSet.as_view({'get': 'estado'}),
        name='estado-movimientos-mes',
    ),
    path(
        'movimientos/subir/<int:cierre_id>/',
        MovimientosMesUploadViewSet.as_view({'post': 'subir'}),
        name='subir-movimientos-mes',
    ),
    # URLs para archivos del analista
    path(
        'archivos-analista/subir/<int:cierre_id>/<str:tipo_archivo>/',
        ArchivoAnalistaUploadViewSet.as_view({'post': 'subir'}),
        name='subir-archivo-analista',
    ),
    path(
        'archivos-analista/<int:pk>/reprocesar/',
        ArchivoAnalistaUploadViewSet.as_view({'post': 'reprocesar'}),
        name='reprocesar-archivo-analista',
    ),
    path(
        'plantilla-libro-remuneraciones/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': '202503_libro_remuneraciones_completo.xlsx'
        },
        name='descargar_plantilla_libro_remuneraciones'
    ),
    path(
        'plantilla-movimientos-mes/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': 'plantilla_movimientos_mes.xlsx'
        },
        name='descargar_plantilla_movimientos_mes'
    ),
    # Plantillas para archivos del analista
    path(
        'plantilla-finiquitos/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': 'plantilla_finiquitos.xlsx'
        },
        name='descargar_plantilla_finiquitos'
    ),
    path(
        'plantilla-incidencias/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': 'plantilla_incidencias.xlsx'
        },
        name='descargar_plantilla_incidencias'
    ),
    path(
        'plantilla-ingresos/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': 'plantilla_ingresos.xlsx'
        },
        name='descargar_plantilla_ingresos'
    ),
    path(
        'plantilla-novedades/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas/nomina',
            'path': 'plantilla_novedades.xlsx'
        },
        name='descargar_plantilla_novedades'
    ),
    path('conceptos-remuneracion/', conceptos_remuneracion_por_cliente, name='conceptos_remuneracion_por_cliente'),
    path('conceptos/cierre/<int:cierre_id>/', conceptos_remuneracion_por_cierre, name='conceptos_remuneracion_por_cierre'),
    path('clientes/<int:cliente_id>/hashtags/', obtener_hashtags_disponibles),
    path("conceptos/", ConceptoRemuneracionBatchView.as_view(), name="guardar-conceptos"),
    
    # === URLs para Activity Logging ===
    path('activity-log/all/', get_all_activity_logs, name='get_all_activity_logs'),
    path('activity-log/modal/', ModalActivityView.as_view(), name='modal_activity_log'),
    path('activity-log/file/', FileActivityView.as_view(), name='file_activity_log'),
    path('activity-log/classification/', ClassificationActivityView.as_view(), name='classification_activity_log'),
    path('activity-log/session/', SessionActivityView.as_view(), name='session_activity_log'),
    path('activity-log/<int:cierre_id>/<str:tarjeta>/', get_activity_log, name='get_activity_log'),
    
    path(
        "conceptos/<int:cliente_id>/<path:nombre_concepto>/eliminar/",
        eliminar_concepto_remuneracion,
        name="eliminar-concepto-remuneracion",
    ),
    path('upload-log/<int:upload_log_id>/estado/', obtener_estado_upload_log_nomina, name='estado_upload_log_nomina'),
    
    # === URLs para Visualización de Datos Consolidados ===
    path('cierres/<int:cierre_id>/libro-remuneraciones/', obtener_libro_remuneraciones, name='libro_remuneraciones'),
    path('cierres/<int:cierre_id>/movimientos/', obtener_movimientos_mes, name='movimientos_mes'),
    path('cierres/<int:cierre_id>/movimientos/v3/detalle/', movimientos_personal_detalle_v3, name='movimientos_personal_detalle_v3'),
    
    # === URL para Estadísticas del Cierre ===
    path('cierres/<int:cierre_id>/estadisticas/', obtener_estadisticas_cierre, name='estadisticas_cierre'),
    
    # === URL para Historial de Verificación ===
    path('cierres/<int:cierre_id>/historial-verificacion/', estadisticas_historial_verificacion, name='historial_verificacion'),
    
    # === URLs para Informes de Cierre ===
    path('cierres/<int:cierre_id>/informe/', obtener_informe_cierre, name='obtener_informe_cierre'),
    path('cierres/<int:cierre_id>/informe/generar/', generar_informe_cierre, name='generar_informe_cierre'),
    path('cierres/<int:cierre_id>/informe/resumen/', obtener_resumen_informe, name='obtener_resumen_informe'),
    path('clientes/<int:cliente_id>/informes/', listar_informes_cliente, name='listar_informes_cliente'),
    
    # === URLs para Redis Cache ===
    path('informes/<int:informe_id>/enviar-redis/', enviar_informe_redis, name='enviar_informe_redis'),
    path('redis/<int:cliente_id>/<str:periodo>/', obtener_informe_redis, name='obtener_informe_redis'),
    path('redis/estadisticas/', estadisticas_redis, name='estadisticas_redis'),
    path('redis/limpiar-cliente/<int:cliente_id>/', limpiar_cache_cliente, name='limpiar_cache_cliente'),
    path('redis/informes/', listar_informes_redis, name='listar_informes_redis'),
    path('redis/health/', health_check_redis, name='health_check_redis'),
    
    # === Resumen Nómina Consolidada ===
    path('cierres/<int:cierre_id>/nomina-consolidada/resumen/', obtener_resumen_nomina_consolidada, name='resumen_nomina_consolidada'),
    path('cierres/<int:cierre_id>/nomina-consolidada/detalle/', obtener_detalle_nomina_consolidada, name='detalle_nomina_consolidada'),
    # === Libro Remuneraciones V2 (simplificado) ===
    path('cierres/<int:cierre_id>/libro/v2/resumen/', libro_resumen_v2, name='libro_resumen_v2'),
]
