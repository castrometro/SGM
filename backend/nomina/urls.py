from rest_framework import routers
from .views import (
    CierreNominaViewSet,
    LibroRemuneracionesUploadViewSet,
    MovimientosMesUploadViewSet,
    ArchivoAnalistaUploadViewSet,
    ArchivoNovedadesUploadViewSet,
    ChecklistItemViewSet,
    conceptos_remuneracion_por_cliente,
    conceptos_remuneracion_por_cierre,
    obtener_hashtags_disponibles,
    ConceptoRemuneracionBatchView,
    eliminar_concepto_remuneracion,
    # ViewSets para modelos del Analista
    AnalistaFiniquitoViewSet,
    AnalistaIncidenciaViewSet,
    AnalistaIngresoViewSet,
    # ViewSets para Movimientos del Mes
    MovimientoAltaBajaViewSet,
    MovimientoAusentismoViewSet,
    MovimientoVacacionesViewSet,
    MovimientoVariacionSueldoViewSet,
    MovimientoVariacionContratoViewSet,
    # ViewSets para modelos de Novedades
    EmpleadoCierreNovedadesViewSet,
    ConceptoRemuneracionNovedadesViewSet,
    RegistroConceptoEmpleadoNovedadesViewSet,
    # ViewSets para Sistema de Incidencias
    IncidenciaCierreViewSet,
    ResolucionIncidenciaViewSet,
    CierreNominaIncidenciasViewSet,
)

from django.urls import path
from django.conf import settings
from django.views.static import serve

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
    path(
        "conceptos/<int:cliente_id>/<path:nombre_concepto>/eliminar/",
        eliminar_concepto_remuneracion,
        name="eliminar-concepto-remuneracion",
    ),
]
