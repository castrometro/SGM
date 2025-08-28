    AreaViewSet, UsuarioViewSet, ClienteViewSet, IndustriaViewSet,
    ServicioViewSet, ServicioClienteViewSet, ContratoViewSet,
    AsignacionClienteUsuarioViewSet, AnalistaPerformanceViewSet, ping,
    DashboardViewSet, AnalistasDetalladoViewSet,
    clientes_disponibles, clientes_asignados, remover_asignacion,
    captura_masiva_gastos, estado_captura_gastos, descargar_resultado_gastos,
    leer_headers_excel_gastos
)
from .views_bypass import (
    clientes_disponibles_bypass, asignar_areas_cliente, 
    clientes_sin_areas, migrar_clientes_a_areas_directas,
--
    
    # URLs para gestión de clientes por área
    path('clientes-por-area/', obtener_clientes_por_area, name='clientes-por-area'),
    path('analistas-por-area/', obtener_analistas_por_area, name='analistas-por-area'),
    
    # URLs para captura masiva de gastos
    path('captura-masiva-gastos/', captura_masiva_gastos, name='captura-masiva-gastos'),
    path('estado-captura-gastos/<str:task_id>/', estado_captura_gastos, name='estado-captura-gastos'),
    path('descargar-resultado-gastos/<str:task_id>/', descargar_resultado_gastos, name='descargar-resultado-gastos'),
    path('gastos/leer-headers/', leer_headers_excel_gastos, name='leer-headers-excel-gastos'),
    
    # URLs específicas del gerente
    path('gerente/', include('api.urls_gerente')),
