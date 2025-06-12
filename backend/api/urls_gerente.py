# backend/api/urls_gerente.py
from django.urls import path
from . import views_gerente

urlpatterns = [
    # ========== GESTIÓN DE CLIENTES ==========
    path('clientes/', views_gerente.obtener_clientes_gerente, name='gerente-clientes'),
    path('clientes/reasignar/', views_gerente.reasignar_cliente, name='gerente-reasignar-cliente'),
    path('clientes/<int:cliente_id>/perfil-completo/', views_gerente.perfil_completo_cliente, name='gerente-perfil-cliente'),
    
    # ========== MÉTRICAS Y KPIs ==========
    path('metricas/', views_gerente.metricas_avanzadas, name='gerente-metricas'),
    
    # ========== ANÁLISIS DE PORTAFOLIO ==========
    path('analisis-portafolio/', views_gerente.analisis_portafolio, name='gerente-analisis-portafolio'),
    
    # ========== SISTEMA DE ALERTAS ==========
    path('alertas/', views_gerente.obtener_alertas, name='gerente-alertas'),
    path('alertas/<int:alerta_id>/marcar-leida/', views_gerente.marcar_alerta_leida, name='gerente-marcar-alerta'),
    path('alertas/configuracion/', views_gerente.obtener_configuracion_alertas, name='gerente-config-alertas'),
    path('alertas/configurar/', views_gerente.configurar_alertas, name='gerente-configurar-alertas'),
    
    # ========== REPORTES ==========
    path('reportes/generar/', views_gerente.generar_reporte, name='gerente-generar-reporte'),
    path('reportes/historial/', views_gerente.historial_reportes, name='gerente-historial-reportes'),
    path('reportes/<str:reporte_id>/descargar/', views_gerente.descargar_reporte, name='gerente-descargar-reporte'),
]
