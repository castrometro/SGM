"""
Ejemplo de API endpoint para lista de empleados en nómina
Este archivo muestra cómo integrar las funcionalidades de lista de empleados
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

class EmpleadosNominaAPIView(View):
    """
    API para manejar listas de empleados en reportes de nómina
    """
    
    def get(self, request, cliente_id, periodo):
        """
        GET /api/nomina/empleados/{cliente_id}/{periodo}
        
        Parámetros query:
        - filtro: criterio de filtrado (opcional)
        - incluir_stats: incluir estadísticas (true/false)
        - limite: número máximo de empleados a retornar
        - offset: desplazamiento para paginación
        """
        
        try:
            from nomina.models_informe import InformeNomina
            from nomina.models import CierreNomina
            
            # Buscar el cierre de nómina
            cierre = CierreNomina.objects.get(
                cliente_id=cliente_id,
                periodo=periodo,
                estado='finalizado'
            )
            
            # Buscar o crear informe
            informe = InformeNomina.objects.filter(cierre=cierre).first()
            if not informe:
                return JsonResponse({
                    'error': 'Informe no encontrado para el período especificado'
                }, status=404)
            
            # Parámetros de la request
            filtro = request.GET.get('filtro', 'todos')
            incluir_stats = request.GET.get('incluir_stats', 'false').lower() == 'true'
            limite = int(request.GET.get('limite', 50))
            offset = int(request.GET.get('offset', 0))
            
            # Obtener empleados según filtro
            if filtro == 'todos':
                empleados = informe.datos_cierre.get('empleados', {}).get('detalle', [])
            else:
                empleados = informe.obtener_empleados_por_criterio(filtro)
            
            # Aplicar paginación
            total_empleados = len(empleados)
            empleados_paginados = empleados[offset:offset + limite]
            
            # Respuesta base
            response_data = {
                'meta': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'total_empleados': total_empleados,
                    'empleados_mostrados': len(empleados_paginados),
                    'offset': offset,
                    'limite': limite,
                    'filtro_aplicado': filtro,
                    'tiene_mas_paginas': offset + limite < total_empleados
                },
                'empleados': empleados_paginados
            }
            
            # Incluir estadísticas si se solicitan
            if incluir_stats:
                response_data['estadisticas'] = informe.obtener_estadisticas_empleados()
                response_data['dias_trabajados'] = informe.calcular_dias_trabajados_por_empleado()
            
            # Agregar filtros disponibles
            response_data['filtros_disponibles'] = [
                {'valor': 'todos', 'nombre': 'Todos los empleados'},
                {'valor': 'con_ausencias', 'nombre': 'Con ausencias'},
                {'valor': 'sin_ausencias', 'nombre': 'Sin ausencias'},
                {'valor': 'ingresos', 'nombre': 'Nuevos ingresos'},
                {'valor': 'finiquitos', 'nombre': 'Finiquitados'},
                {'valor': 'con_horas_extras', 'nombre': 'Con horas extras'},
                {'valor': 'alta_remuneracion', 'nombre': 'Alta remuneración (Top 20%)'},
                {'valor': 'isapre', 'nombre': 'Afiliados a Isapre'},
                {'valor': 'fonasa', 'nombre': 'Afiliados a Fonasa'}
            ]
            
            return JsonResponse(response_data)
            
        except CierreNomina.DoesNotExist:
            return JsonResponse({
                'error': 'Cierre de nómina no encontrado'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error interno: {str(e)}'
            }, status=500)

class EstadisticasEmpleadosAPIView(View):
    """
    API específica para estadísticas de empleados
    """
    
    def get(self, request, cliente_id, periodo):
        """
        GET /api/nomina/empleados/{cliente_id}/{periodo}/estadisticas
        
        Retorna estadísticas detalladas sin la lista de empleados
        """
        
        try:
            from nomina.models_informe import InformeNomina
            from nomina.models import CierreNomina
            
            cierre = CierreNomina.objects.get(
                cliente_id=cliente_id,
                periodo=periodo,
                estado='finalizado'
            )
            
            informe = InformeNomina.objects.filter(cierre=cierre).first()
            if not informe:
                return JsonResponse({
                    'error': 'Informe no encontrado'
                }, status=404)
            
            # Obtener estadísticas completas
            estadisticas = informe.obtener_estadisticas_empleados()
            dias_trabajados = informe.calcular_dias_trabajados_por_empleado()
            
            # Agregar métricas adicionales
            empleados_data = informe.datos_cierre.get('empleados', {})
            
            response_data = {
                'meta': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'fecha_generacion': informe.fecha_generacion.isoformat(),
                    'total_empleados': empleados_data.get('total_empleados', 0)
                },
                'estadisticas': estadisticas,
                'dias_trabajados': dias_trabajados,
                'resumen_ejecutivo': {
                    'remuneracion_promedio': estadisticas.get('remuneracion', {}).get('promedio', 0),
                    'empleados_sin_ausencias_porcentaje': round(
                        (estadisticas.get('ausentismo', {}).get('empleados_sin_ausencias', 0) / 
                         empleados_data.get('total_empleados', 1)) * 100, 2
                    ),
                    'distribucion_isapre_fonasa': {
                        'isapre': estadisticas.get('distribucion', {}).get('por_tipo_salud', {}).get('isapre', 0),
                        'fonasa': estadisticas.get('distribucion', {}).get('por_tipo_salud', {}).get('fonasa', 0)
                    }
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error obteniendo estadísticas: {str(e)}'
            }, status=500)

# Ejemplo de URLs para Django
"""
# En urls.py
from django.urls import path
from . import views_empleados_api

urlpatterns = [
    path('api/nomina/empleados/<int:cliente_id>/<str:periodo>/', 
         views_empleados_api.EmpleadosNominaAPIView.as_view(), 
         name='empleados_nomina_api'),
    
    path('api/nomina/empleados/<int:cliente_id>/<str:periodo>/estadisticas/', 
         views_empleados_api.EstadisticasEmpleadosAPIView.as_view(), 
         name='estadisticas_empleados_api'),
]
"""

# Ejemplos de uso desde frontend (JavaScript)
"""
// Obtener lista de empleados paginada
fetch('/api/nomina/empleados/123/2024-08/?limite=20&offset=0&incluir_stats=true')
  .then(response => response.json())
  .then(data => {
    console.log('Total empleados:', data.meta.total_empleados);
    console.log('Empleados:', data.empleados);
    console.log('Estadísticas:', data.estadisticas);
  });

// Filtrar empleados con ausencias
fetch('/api/nomina/empleados/123/2024-08/?filtro=con_ausencias')
  .then(response => response.json())
  .then(data => {
    console.log('Empleados con ausencias:', data.empleados);
  });

// Obtener solo estadísticas
fetch('/api/nomina/empleados/123/2024-08/estadisticas/')
  .then(response => response.json())
  .then(data => {
    console.log('Remuneración promedio:', data.estadisticas.remuneracion.promedio);
    console.log('Distribución salarial:', data.estadisticas.remuneracion.rangos_salariales);
  });
"""
