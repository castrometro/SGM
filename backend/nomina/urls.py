"""
URLs para la API de Nómina - Nueva Arquitectura
=============================================

Configuración de URLs para la API REST de nómina usando Django REST Framework.
Implementa endpoints para:

- CierreNomina: CRUD + acciones especiales (consolidar, cerrar, dashboard)
- EmpleadoNomina: Gestión de empleados por cierre
- Incidencias: Sistema colaborativo de incidencias
- KPIs: Métricas pre-calculadas y comparaciones
- Utilidades: Mapeos, búsquedas, cache

Autor: Sistema SGM - Módulo Nómina
Fecha: 20 de julio de 2025
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configurar router principal
router = DefaultRouter()

# ========== REGISTRO DE VIEWSETS ==========

# ViewSets principales disponibles
router.register(r'cierres', views.CierreNominaViewSet, basename='cierre')
router.register(r'empleados', views.EmpleadoNominaViewSet, basename='empleado')
router.register(r'libros-remuneraciones', views.LibroRemuneracionesViewSet, basename='libro-remuneraciones')

# ViewSets de incidencias y colaboración
router.register(r'incidencias', views.IncidenciaViewSet, basename='incidencia')

# ViewSets de KPIs y análisis
router.register(r'kpis', views.KPINominaViewSet, basename='kpi')

# NOTA: Los siguientes ViewSets están pendientes de implementación:
# - EmpleadoConceptoViewSet
# - InteraccionIncidenciaViewSet
# - ComparacionMensualViewSet
# - MapeoConceptoViewSet
# - AusentismoViewSet

# ========== PATRONES DE URL ==========

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
    
    # Endpoints adicionales específicos (si los necesitas)
    # path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    # path('reportes/', views.ReportesView.as_view(), name='reportes'),
]

# ========== DOCUMENTACIÓN DE ENDPOINTS ==========

"""
ENDPOINTS DISPONIBLES:

📋 CIERRES DE NÓMINA:
- GET /api/cierres/                    → Listar todos los cierres
- POST /api/cierres/                   → Crear nuevo cierre
- GET /api/cierres/{id}/               → Detalle de un cierre
- PUT /api/cierres/{id}/               → Actualizar cierre completo
- PATCH /api/cierres/{id}/             → Actualizar cierre parcial
- DELETE /api/cierres/{id}/            → Eliminar cierre

ACCIONES ESPECIALES:
- POST /api/cierres/{id}/consolidar/   → Consolidar datos del cierre
- POST /api/cierres/{id}/cerrar/       → Cerrar período de nómina
- POST /api/cierres/{id}/reabrir/      → Reabrir período cerrado
- GET /api/cierres/{id}/dashboard/     → Dashboard con KPIs del cierre
- GET /api/cierres/{id}/validar/       → Validar integridad de datos
- POST /api/cierres/{id}/procesar/     → Procesar archivos pendientes

👥 EMPLEADOS:
- GET /api/empleados/                  → Listar empleados
- POST /api/empleados/                 → Crear empleado
- GET /api/empleados/{id}/             → Detalle de empleado
- PUT/PATCH /api/empleados/{id}/       → Actualizar empleado
- DELETE /api/empleados/{id}/          → Eliminar empleado

ACCIONES ESPECIALES:
- GET /api/empleados/{id}/conceptos/   → Conceptos del empleado
- GET /api/empleados/{id}/historico/   → Histórico salarial
- POST /api/empleados/buscar/          → Búsqueda avanzada
- POST /api/empleados/comparar/        → Comparar períodos

💰 CONCEPTOS:
- GET /api/conceptos/                  → Listar conceptos
- POST /api/conceptos/                 → Crear concepto
- GET /api/conceptos/{id}/             → Detalle de concepto
- PUT/PATCH /api/conceptos/{id}/       → Actualizar concepto
- DELETE /api/conceptos/{id}/          → Eliminar concepto

⚠️ INCIDENCIAS:
- GET /api/incidencias/                → Listar incidencias
- POST /api/incidencias/               → Crear incidencia
- GET /api/incidencias/{id}/           → Detalle de incidencia
- PUT/PATCH /api/incidencias/{id}/     → Actualizar incidencia
- DELETE /api/incidencias/{id}/        → Eliminar incidencia

ACCIONES ESPECIALES:
- POST /api/incidencias/{id}/asignar/  → Asignar incidencia
- POST /api/incidencias/{id}/resolver/ → Resolver incidencia
- POST /api/incidencias/{id}/escalar/  → Escalar a supervisor
- GET /api/incidencias/{id}/historial/ → Ver historial de resolución

💬 INTERACCIONES:
- GET /api/interacciones/              → Listar interacciones
- POST /api/interacciones/             → Crear interacción
- GET /api/interacciones/{id}/         → Detalle de interacción

📊 KPIs:
- GET /api/kpis/                       → Listar KPIs
- POST /api/kpis/                      → Crear KPI
- GET /api/kpis/{id}/                  → Detalle de KPI

ACCIONES ESPECIALES:
- POST /api/kpis/calcular/             → Calcular KPIs para período
- GET /api/kpis/tendencias/            → Tendencias históricas
- GET /api/kpis/comparativas/          → Comparativas entre clientes

🔄 COMPARACIONES:
- GET /api/comparaciones/              → Listar comparaciones mensuales
- POST /api/comparaciones/             → Crear comparación
- GET /api/comparaciones/{id}/         → Detalle de comparación

🔧 UTILIDADES:
- GET /api/mapeos/                     → Listar mapeos de conceptos
- POST /api/mapeos/                    → Crear mapeo
- GET /api/mapeos/{id}/                → Detalle de mapeo
- PUT/PATCH /api/mapeos/{id}/          → Actualizar mapeo

- GET /api/ausentismos/                → Listar ausentismos
- POST /api/ausentismos/               → Crear ausentismo
- GET /api/ausentismos/{id}/           → Detalle de ausentismo

FILTROS DISPONIBLES:
- ?cliente=ID                          → Filtrar por cliente
- ?periodo=YYYY-MM                     → Filtrar por período
- ?estado=estado                       → Filtrar por estado
- ?search=término                      → Búsqueda texto libre
- ?page=N                             → Paginación
- ?page_size=N                        → Tamaño de página
- ?ordering=campo                     → Ordenamiento

FORMATOS SOPORTADOS:
- JSON (por defecto)
- XML (agregar ?format=xml)
- API navegable (desde navegador)

AUTENTICACIÓN:
- Token authentication
- Session authentication (para desarrollo)

PERMISOS:
- IsAuthenticated para todas las operaciones
- Permisos específicos por modelo en admin
- Validaciones de integridad en ViewSets
"""
