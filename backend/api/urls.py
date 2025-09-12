from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AreaViewSet, UsuarioViewSet, ClienteViewSet, IndustriaViewSet,
    ServicioViewSet, ServicioClienteViewSet, ContratoViewSet,
    AsignacionClienteUsuarioViewSet, AnalistaPerformanceViewSet, ping,
    DashboardViewSet, AnalistasDetalladoViewSet,
    clientes_disponibles, clientes_asignados, remover_asignacion,
    captura_masiva_gastos, estado_captura_gastos, descargar_resultado_gastos,
    leer_headers_excel,
    parse_auxiliar_cxc
)
from .views_bypass import (
    clientes_disponibles_bypass, asignar_areas_cliente, 
    clientes_sin_areas, migrar_clientes_a_areas_directas,
    obtener_clientes_por_area, obtener_analistas_por_area
)

router = DefaultRouter()
router.register(r'areas', AreaViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'industrias', IndustriaViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'servicio-clientes', ServicioClienteViewSet, basename='servicio-cliente')
router.register(r'contratos', ContratoViewSet)
router.register(r'asignaciones', AsignacionClienteUsuarioViewSet, basename='asignaciones')
router.register(r'bi-analistas', AnalistaPerformanceViewSet, basename='bi-analistas')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'analistas-detallado', AnalistasDetalladoViewSet, basename='analistas-detallado')

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs originales (con lógica de servicios contratados)
    path('clientes-disponibles/<int:analista_id>/', clientes_disponibles, name='clientes-disponibles'),
    path('clientes-asignados/<int:analista_id>/', clientes_asignados, name='clientes-asignados'),
    path('asignaciones/<int:analista_id>/<int:cliente_id>/', remover_asignacion, name='remover-asignacion'),
    
    # URLs bypass (con lógica de áreas directas)
    path('clientes-disponibles-bypass/<int:analista_id>/', clientes_disponibles_bypass, name='clientes-disponibles-bypass'),
    path('clientes/<int:cliente_id>/asignar-areas/', asignar_areas_cliente, name='asignar-areas-cliente'),
    path('clientes-sin-areas/', clientes_sin_areas, name='clientes-sin-areas'),
    path('migrar-clientes-areas-directas/', migrar_clientes_a_areas_directas, name='migrar-clientes-areas-directas'),
    
    # URLs para gestión de clientes por área
    path('clientes-por-area/', obtener_clientes_por_area, name='clientes-por-area'),
    path('analistas-por-area/', obtener_analistas_por_area, name='analistas-por-area'),
    
    # URLs específicas del gerente
    path('gerente/', include('api.urls_gerente')),
    
    # URLs para captura masiva de gastos
    path('captura-masiva-gastos/', captura_masiva_gastos, name='captura-masiva-gastos'),
    path('estado-captura-gastos/<str:task_id>/', estado_captura_gastos, name='estado-captura-gastos'),
    path('descargar-resultado-gastos/<str:task_id>/', descargar_resultado_gastos, name='descargar-resultado-gastos'),
    path('captura-masiva-gastos/leer-headers/', leer_headers_excel, name='leer-headers-excel'),
    # CxC: parser de auxiliar sin persistencia
    path('cobranza/parse-auxiliar/', parse_auxiliar_cxc, name='parse-auxiliar-cxc'),
]
