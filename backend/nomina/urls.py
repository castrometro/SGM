from rest_framework import routers
from .views import (
    CierreNominaViewSet,
    LibroRemuneracionesUploadViewSet,
    MovimientosMesUploadViewSet,
    ArchivoAnalistaUploadViewSet,
    ArchivoNovedadesUploadViewSet,
    ChecklistItemViewSet,
    conceptos_remuneracion_por_cliente,
    obtener_hashtags_disponibles,
    ConceptoRemuneracionBatchView,
    eliminar_concepto_remuneracion,
    # nuevos si ya los creaste
    # EmpleadoCierreViewSet,
    # RegistroConceptoEmpleadoViewSet,
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

# si ya creaste los viewsets de estos modelos, puedes habilitar
# router.register(r'empleados-cierre', EmpleadoCierreViewSet)
# router.register(r'registros-concepto', RegistroConceptoEmpleadoViewSet)

urlpatterns = router.urls + [
    path(
        'libros-remuneraciones/<int:pk>/procesar/',
        LibroRemuneracionesUploadViewSet.as_view({'post': 'procesar'}),
        name='procesar-libro-remuneraciones',
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
    path('conceptos-remuneracion/', conceptos_remuneracion_por_cliente, name='conceptos_remuneracion_por_cliente'),
    path('clientes/<int:cliente_id>/hashtags/', obtener_hashtags_disponibles),
    path("conceptos/", ConceptoRemuneracionBatchView.as_view(), name="guardar-conceptos"),
    path(
        "conceptos/<int:cliente_id>/<path:nombre_concepto>/eliminar/",
        eliminar_concepto_remuneracion,
        name="eliminar-concepto-remuneracion",
    ),
]
