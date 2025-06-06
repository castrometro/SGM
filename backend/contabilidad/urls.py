from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path, include
from django.views.static import serve
from django.conf import settings

router = DefaultRouter()
router.register(r'cuentas', CuentaContableViewSet)
router.register(r'cierres', CierreContabilidadViewSet, basename='cierres')
router.register(r'libromayor', LibroMayorUploadViewSet, basename='libromayor')
router.register(r'aperturas', AperturaCuentaViewSet)
router.register(r'movimientos', MovimientoContableViewSet)
router.register(r'clasificaciones-set', ClasificacionSetViewSet)
router.register(r'clasificaciones-opcion', ClasificacionOptionViewSet)
router.register(r'clasificaciones', AccountClassificationViewSet)
router.register(r'clasificacion', ClasificacionViewSet, basename='clasificacion')  # <--- ¡aquí!
router.register(r'incidencias', IncidenciaViewSet)
router.register(r'centros-costo', CentroCostoViewSet)
router.register(r'auxiliares', AuxiliarViewSet)
router.register(r'analisis-cuentas', AnalisisCuentaCierreViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cierres/<int:pk>/movimientos-resumen/',
         CierreContabilidadViewSet.as_view({'get': 'movimientos_resumen'}),
         name='cierre-movimientos-resumen'),
    path('clientes/<int:cliente_id>/resumen/', resumen_cliente),
    path('tipo-documento/subir-archivo/', cargar_tipo_documento),
    path('tipo-documento/<int:cliente_id>/estado/', estado_tipo_documento),
    path('tipo-documento/<int:cliente_id>/list/', tipos_documento_cliente),
    path('tipo-documento/<int:cliente_id>/eliminar-todos/', eliminar_tipos_documento),
    path('clientes/<int:cliente_id>/sets/<int:set_id>/cuentas_pendientes/', cuentas_pendientes_set),
    path("nombres-ingles/", NombresEnInglesView.as_view(), name="nombres_ingles"),

    path('test-celery/', test_celery),
    path(
        'plantilla-tipo-doc/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas',
            'path': 'plantilla_tipo_documento.xlsx'
        },
        name='descargar_plantilla_tipo_doc'
    ),
    path(
        'plantilla-nombres-en-ingles/',
        serve,
        {
            'document_root': settings.BASE_DIR / 'static/plantillas',
            'path': 'plantilla_nombres_en_ingles.xlsx'
        },
    )
]
