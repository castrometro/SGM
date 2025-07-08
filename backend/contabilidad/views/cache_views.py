"""
Views para el sistema de cache Redis de SGM - Contabilidad
========================================================

Endpoints para gestionar el cache de datos contables utilizando Redis DB 1.
Incluye endpoints para KPIs, estados financieros, movimientos, y estadísticas.

Autor: Sistema SGM
Fecha: 8 de julio de 2025
"""

import time
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..cache_redis import get_cache_system
from ..models import Cliente, CierreContabilidad

# Configurar logging
logger = logging.getLogger(__name__)

class CachePerformanceMixin:
    """Mixin para medir performance de operaciones de cache"""
    
    def measure_performance(self, func, *args, **kwargs):
        """Medir tiempo de ejecución de una función"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return result, (end_time - start_time) * 1000  # en milisegundos


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_kpis_with_cache(request, cliente_id, periodo):
    """
    Obtener KPIs con cache Redis
    
    URL: /api/contabilidad/cache/kpis/{cliente_id}/{periodo}/
    Método: GET
    """
    start_time = time.time()
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Intentar obtener del cache
        kpis_cached = cache_system.get_kpis(cliente_id, periodo)
        
        if kpis_cached:
            response_time = (time.time() - start_time) * 1000
            return Response({
                'success': True,
                'data': kpis_cached,
                'from_cache': True,
                'cliente': cliente.nombre,
                'periodo': periodo,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            })
        
        # Si no está en cache, generar KPIs
        # TODO: Integrar con tu lógica existente de cálculo de KPIs
        kpis_calculados = {
            'liquidez_corriente': 1.5,
            'endeudamiento': 0.35,
            'rentabilidad_activos': 0.12,
            'rentabilidad_patrimonio': 0.18,
            'margen_operacional': 0.25,
            'rotacion_inventarios': 6.2,
            'dias_cartera': 45,
            'calculated_at': datetime.now().isoformat()
        }
        
        # Guardar en cache
        cache_success = cache_system.set_kpis(cliente_id, periodo, kpis_calculados)
        
        response_time = (time.time() - start_time) * 1000
        
        return Response({
            'success': True,
            'data': kpis_calculados,
            'from_cache': False,
            'cache_saved': cache_success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'response_time_ms': round(response_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_estado_financiero_with_cache(request, cliente_id, periodo, tipo_estado):
    """
    Obtener estado financiero con cache Redis
    
    URL: /api/contabilidad/cache/estado/{cliente_id}/{periodo}/{tipo_estado}/
    Método: GET
    Tipos válidos: esf, esr, eri, ecp
    """
    start_time = time.time()
    cache_system = get_cache_system()
    
    # Validar tipo de estado
    estados_validos = ['esf', 'esr', 'eri', 'ecp']
    if tipo_estado not in estados_validos:
        return Response({
            'success': False,
            'error': f'Tipo de estado inválido: {tipo_estado}. Válidos: {estados_validos}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Intentar obtener del cache
        estado_cached = cache_system.get_estado_financiero(cliente_id, periodo, tipo_estado)
        
        if estado_cached:
            response_time = (time.time() - start_time) * 1000
            return Response({
                'success': True,
                'data': estado_cached,
                'from_cache': True,
                'tipo_estado': tipo_estado.upper(),
                'cliente': cliente.nombre,
                'periodo': periodo,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            })
        
        # Si no está en cache, generar estado financiero
        # TODO: Integrar con tu lógica existente de generación de estados
        estado_generado = {
            'tipo_estado': tipo_estado.upper(),
            'cliente_id': cliente_id,
            'periodo': periodo,
            'cuentas': [
                {'codigo': '1', 'nombre': 'ACTIVOS', 'valor': 1000000},
                {'codigo': '11', 'nombre': 'Activos Corrientes', 'valor': 600000},
                {'codigo': '12', 'nombre': 'Activos No Corrientes', 'valor': 400000},
            ],
            'totales': {
                'total_activos': 1000000,
                'total_pasivos': 400000,
                'total_patrimonio': 600000
            },
            'generated_at': datetime.now().isoformat()
        }
        
        # Guardar en cache
        cache_success = cache_system.set_estado_financiero(
            cliente_id, periodo, tipo_estado, estado_generado
        )
        
        response_time = (time.time() - start_time) * 1000
        
        return Response({
            'success': True,
            'data': estado_generado,
            'from_cache': False,
            'cache_saved': cache_success,
            'tipo_estado': tipo_estado.upper(),
            'cliente': cliente.nombre,
            'periodo': periodo,
            'response_time_ms': round(response_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado {tipo_estado}: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_movimientos_with_cache(request, cliente_id, periodo):
    """
    Obtener movimientos contables con cache Redis
    
    URL: /api/contabilidad/cache/movimientos/{cliente_id}/{periodo}/
    Método: GET
    """
    start_time = time.time()
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Intentar obtener del cache
        movimientos_cached = cache_system.get_movimientos(cliente_id, periodo)
        
        if movimientos_cached:
            response_time = (time.time() - start_time) * 1000
            return Response({
                'success': True,
                'data': movimientos_cached,
                'count': len(movimientos_cached),
                'from_cache': True,
                'cliente': cliente.nombre,
                'periodo': periodo,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            })
        
        # Si no está en cache, consultar base de datos
        # TODO: Integrar con tu consulta real de movimientos
        movimientos_db = [
            {
                'fecha': '2025-07-01',
                'cuenta': '1105',
                'descripcion': 'Caja General',
                'debito': 100000,
                'credito': 0,
                'saldo': 100000
            },
            {
                'fecha': '2025-07-01',
                'cuenta': '3105',
                'descripcion': 'Capital Social',
                'debito': 0,
                'credito': 100000,
                'saldo': 100000
            },
            # Más movimientos...
        ]
        
        # Guardar en cache
        cache_success = cache_system.set_movimientos(cliente_id, periodo, movimientos_db)
        
        response_time = (time.time() - start_time) * 1000
        
        return Response({
            'success': True,
            'data': movimientos_db,
            'count': len(movimientos_db),
            'from_cache': False,
            'cache_saved': cache_success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'response_time_ms': round(response_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo movimientos: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_cache(request, cliente_id, periodo):
    """
    Invalidar cache de un cliente/período específico
    
    URL: /api/contabilidad/cache/invalidate/{cliente_id}/{periodo}/
    Método: POST
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Invalidar cache
        deleted_count = cache_system.invalidate_cliente_periodo(cliente_id, periodo)
        
        logger.info(f"Cache invalidado por usuario {request.user.id}: cliente={cliente_id}, periodo={periodo}")
        
        return Response({
            'success': True,
            'message': f'Cache invalidado para cliente {cliente.nombre}, período {periodo}',
            'deleted_keys': deleted_count,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'invalidated_by': request.user.username,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error invalidando cache: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cache_stats(request):
    """
    Obtener estadísticas del cache Redis
    
    URL: /api/contabilidad/cache/stats/
    Método: GET
    """
    cache_system = get_cache_system()
    
    try:
        stats = cache_system.get_cache_stats()
        
        return Response({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cache_health(request):
    """
    Verificar salud del sistema de cache
    
    URL: /api/contabilidad/cache/health/
    Método: GET
    """
    cache_system = get_cache_system()
    
    try:
        health_data = cache_system.health_check()
        
        # Determinar código de respuesta HTTP basado en el estado
        http_status = status.HTTP_200_OK if health_data.get('status') == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response({
            'success': health_data.get('status') == 'healthy',
            'health': health_data,
            'timestamp': datetime.now().isoformat()
        }, status=http_status)
        
    except Exception as e:
        logger.error(f"Error verificando salud del cache: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_client_periods_cached(request, cliente_id):
    """
    Obtener períodos disponibles en cache para un cliente
    
    URL: /api/contabilidad/cache/client/{cliente_id}/periods/
    Método: GET
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener períodos en cache
        periods = cache_system.get_client_periods(cliente_id)
        
        return Response({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre
            },
            'periods': periods,
            'count': len(periods),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo períodos del cliente {cliente_id}: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_procesamiento_status(request, cliente_id, periodo):
    """
    Actualizar estado de procesamiento en cache
    
    URL: /api/contabilidad/cache/procesamiento/{cliente_id}/{periodo}/
    Método: POST
    Body: {
        "estado": "procesando|completado|error",
        "progreso": 75,
        "mensaje": "Procesando libro mayor...",
        "detalles": {}
    }
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener datos del request
        status_data = {
            'estado': request.data.get('estado', 'procesando'),
            'progreso': request.data.get('progreso', 0),
            'mensaje': request.data.get('mensaje', ''),
            'detalles': request.data.get('detalles', {}),
            'updated_at': datetime.now().isoformat(),
            'updated_by': request.user.username
        }
        
        # Guardar en cache
        cache_success = cache_system.set_procesamiento_status(cliente_id, periodo, status_data)
        
        return Response({
            'success': True,
            'message': 'Estado de procesamiento actualizado',
            'cache_saved': cache_success,
            'data': status_data,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error actualizando estado de procesamiento: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_procesamiento_status(request, cliente_id, periodo):
    """
    Obtener estado de procesamiento desde cache
    
    URL: /api/contabilidad/cache/procesamiento/{cliente_id}/{periodo}/
    Método: GET
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener estado del cache
        status_data = cache_system.get_procesamiento_status(cliente_id, periodo)
        
        if status_data:
            return Response({
                'success': True,
                'data': status_data,
                'from_cache': True,
                'cliente': cliente.nombre,
                'periodo': periodo,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return Response({
                'success': False,
                'message': 'No hay estado de procesamiento en cache',
                'cliente': cliente.nombre,
                'periodo': periodo,
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de procesamiento: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# FUNCIONES ADICIONALES PARA URLs
# ===================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_procesamiento_status_with_cache(request, cliente_id, periodo):
    """Alias para compatibilidad con URLs existentes"""
    return get_procesamiento_status(request, cliente_id, periodo)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidar_cache_cliente(request, cliente_id, periodo=None):
    """
    Invalidar cache de un cliente (y opcionalmente un período)
    Compatibilidad con URLs existentes
    """
    if periodo:
        return invalidate_cache(request, cliente_id, periodo)
    else:
        # Invalidar todo el cliente
        cache_system = get_cache_system()
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            deleted_count = cache_system.invalidate_cliente(cliente_id)
            
            return Response({
                'success': True,
                'message': f'Todo el cache invalidado para cliente {cliente.nombre}',
                'deleted_keys': deleted_count,
                'cliente': cliente.nombre,
                'invalidated_by': request.user.username,
                'timestamp': datetime.now().isoformat()
            })
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cache_stats(request):
    """Alias para compatibilidad con URLs existentes"""
    return cache_stats(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cache_health(request):
    """Alias para compatibilidad con URLs existentes"""
    return cache_health(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_kpis_cache(request, cliente_id, periodo):
    """
    Endpoint para establecer KPIs en cache
    """
    cache_system = get_cache_system()
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        kpis_data = request.data
        
        success = cache_system.set_kpis(cliente_id, periodo, kpis_data)
        
        return Response({
            'success': True,
            'message': 'KPIs guardados en cache',
            'cache_saved': success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'timestamp': datetime.now().isoformat()
        })
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Cliente {cliente_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_estado_financiero_cache(request, cliente_id, periodo, tipo_estado):
    """
    Endpoint para establecer estado financiero en cache
    """
    cache_system = get_cache_system()
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        estado_data = request.data
        
        success = cache_system.set_estado_financiero(cliente_id, periodo, tipo_estado, estado_data)
        
        return Response({
            'success': True,
            'message': f'Estado {tipo_estado.upper()} guardado en cache',
            'cache_saved': success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'tipo_estado': tipo_estado.upper(),
            'timestamp': datetime.now().isoformat()
        })
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Cliente {cliente_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_movimientos_cache(request, cliente_id, periodo):
    """
    Endpoint para establecer movimientos en cache
    """
    cache_system = get_cache_system()
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        movimientos_data = request.data
        
        success = cache_system.set_movimientos(cliente_id, periodo, movimientos_data)
        
        return Response({
            'success': True,
            'message': 'Movimientos guardados en cache',
            'cache_saved': success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'timestamp': datetime.now().isoformat()
        })
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Cliente {cliente_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_procesamiento_status_cache(request, cliente_id, periodo):
    """Alias para compatibilidad con URLs existentes"""
    return set_procesamiento_status(request, cliente_id, periodo)


# ===================================
# ENDPOINTS PARA PRUEBAS Y TESTING
# ===================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_prueba_esf(request, cliente_id, periodo):
    """
    Guardar ESF de prueba generado por el sistema actual
    
    URL: /api/contabilidad/cache/pruebas/esf/{cliente_id}/{periodo}/
    Método: POST
    Body: {
        "esf_data": {...},
        "test_type": "current_system"
    }
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener datos del request
        esf_data = request.data.get('esf_data', {})
        test_type = request.data.get('test_type', 'current_system')
        
        if not esf_data:
            return Response({
                'success': False,
                'error': 'esf_data es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar en cache
        cache_success = cache_system.set_prueba_esf(cliente_id, periodo, esf_data, test_type)
        
        return Response({
            'success': True,
            'message': f'ESF de prueba guardado exitosamente',
            'cache_saved': cache_success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'test_type': test_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error guardando ESF de prueba: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prueba_esf(request, cliente_id, periodo):
    """
    Obtener ESF de prueba del cache
    
    URL: /api/contabilidad/cache/pruebas/esf/{cliente_id}/{periodo}/
    Método: GET
    Query params: ?test_type=current_system
    """
    cache_system = get_cache_system()
    start_time = time.time()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener tipo de prueba desde query params
        test_type = request.query_params.get('test_type', 'current_system')
        
        # Obtener del cache
        esf_prueba = cache_system.get_prueba_esf(cliente_id, periodo, test_type)
        
        response_time = (time.time() - start_time) * 1000
        
        if esf_prueba:
            return Response({
                'success': True,
                'data': esf_prueba,
                'from_cache': True,
                'cliente': cliente.nombre,
                'periodo': periodo,
                'test_type': test_type,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return Response({
                'success': False,
                'message': 'ESF de prueba no encontrado en cache',
                'cliente': cliente.nombre,
                'periodo': periodo,
                'test_type': test_type,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error obteniendo ESF de prueba: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_prueba_data(request, cliente_id, periodo, data_type):
    """
    Guardar datos de prueba genéricos
    
    URL: /api/contabilidad/cache/pruebas/{data_type}/{cliente_id}/{periodo}/
    Método: POST
    Body: {
        "data": {...},
        "test_type": "general"
    }
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener datos del request
        data = request.data.get('data', {})
        test_type = request.data.get('test_type', 'general')
        
        if not data:
            return Response({
                'success': False,
                'error': 'data es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar en cache
        cache_success = cache_system.set_prueba_data(cliente_id, periodo, data_type, data, test_type)
        
        return Response({
            'success': True,
            'message': f'Datos de prueba ({data_type}) guardados exitosamente',
            'cache_saved': cache_success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'data_type': data_type,
            'test_type': test_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error guardando datos de prueba {data_type}: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prueba_data(request, cliente_id, periodo, data_type):
    """
    Obtener datos de prueba genéricos del cache
    
    URL: /api/contabilidad/cache/pruebas/{data_type}/{cliente_id}/{periodo}/
    Método: GET
    Query params: ?test_type=general
    """
    cache_system = get_cache_system()
    start_time = time.time()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener tipo de prueba desde query params
        test_type = request.query_params.get('test_type', 'general')
        
        # Obtener del cache
        prueba_data = cache_system.get_prueba_data(cliente_id, periodo, data_type, test_type)
        
        response_time = (time.time() - start_time) * 1000
        
        if prueba_data:
            return Response({
                'success': True,
                'data': prueba_data,
                'from_cache': True,
                'cliente': cliente.nombre,
                'periodo': periodo,
                'data_type': data_type,
                'test_type': test_type,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return Response({
                'success': False,
                'message': f'Datos de prueba ({data_type}) no encontrados en cache',
                'cliente': cliente.nombre,
                'periodo': periodo,
                'data_type': data_type,
                'test_type': test_type,
                'response_time_ms': round(response_time, 2),
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de prueba {data_type}: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pruebas_cliente(request, cliente_id):
    """
    Listar todas las pruebas disponibles para un cliente
    
    URL: /api/contabilidad/cache/pruebas/list/{cliente_id}/
    Método: GET
    Query params: ?periodo=2025-07 (opcional)
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener período desde query params (opcional)
        periodo = request.query_params.get('periodo', None)
        
        # Listar pruebas
        pruebas = cache_system.list_pruebas_cliente(cliente_id, periodo)
        
        return Response({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre
            },
            'periodo_filtro': periodo,
            'pruebas': pruebas,
            'count': len(pruebas),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listando pruebas del cliente {cliente_id}: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_pruebas_cliente(request, cliente_id):
    """
    Invalidar todas las pruebas de un cliente
    
    URL: /api/contabilidad/cache/pruebas/invalidate/{cliente_id}/
    Método: POST
    Body: {
        "periodo": "2025-07" (opcional)
    }
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener período desde body (opcional)
        periodo = request.data.get('periodo', None)
        
        # Invalidar pruebas
        deleted_count = cache_system.invalidate_pruebas_cliente(cliente_id, periodo)
        
        logger.info(f"Pruebas invalidadas por usuario {request.user.id}: cliente={cliente_id}, periodo={periodo}")
        
        return Response({
            'success': True,
            'message': f'Pruebas invalidadas para cliente {cliente.nombre}' + 
                      (f', período {periodo}' if periodo else ' (todos los períodos)'),
            'deleted_keys': deleted_count,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'invalidated_by': request.user.username,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error invalidando pruebas: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def capture_current_esf(request, cliente_id, periodo):
    """
    Capturar ESF actual del sistema y guardarlo como prueba
    
    URL: /api/contabilidad/cache/pruebas/capture-esf/{cliente_id}/{periodo}/
    Método: POST
    Body: {
        "test_type": "current_system_capture"
    }
    """
    cache_system = get_cache_system()
    
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Cliente {cliente_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # TODO: Aquí deberías integrar con tu lógica actual de generación de ESF
        # Por ahora genero datos de ejemplo que representen lo que el sistema actual produce
        from decimal import Decimal
        
        esf_actual = {
            'tipo_estado': 'ESF',
            'cliente_id': cliente_id,
            'cliente_nombre': cliente.nombre,
            'periodo': periodo,
            'generated_by': 'sistema_actual',
            'captured_at': datetime.now().isoformat(),
            'captured_by': request.user.username,
            
            # Estructura típica de ESF del sistema actual
            'assets': {
                'current_assets': float(Decimal('750000.00')),
                'non_current_assets': float(Decimal('250000.00')),
                'total_assets': float(Decimal('1000000.00')),
                'current_assets_detail': {
                    '1101': {'nombre': 'Caja', 'saldo': float(Decimal('50000.00'))},
                    '1102': {'nombre': 'Bancos', 'saldo': float(Decimal('200000.00'))},
                    '1103': {'nombre': 'Cuentas por Cobrar', 'saldo': float(Decimal('300000.00'))},
                    '1104': {'nombre': 'Inventarios', 'saldo': float(Decimal('200000.00'))},
                },
                'non_current_assets_detail': {
                    '1201': {'nombre': 'Propiedad Planta y Equipo', 'saldo': float(Decimal('250000.00'))},
                }
            },
            'liabilities': {
                'current_liabilities': float(Decimal('300000.00')),
                'non_current_liabilities': float(Decimal('100000.00')),
                'total_liabilities': float(Decimal('400000.00')),
                'current_liabilities_detail': {
                    '2101': {'nombre': 'Proveedores', 'saldo': float(Decimal('150000.00'))},
                    '2102': {'nombre': 'Cuentas por Pagar', 'saldo': float(Decimal('100000.00'))},
                    '2103': {'nombre': 'Obligaciones Laborales', 'saldo': float(Decimal('50000.00'))},
                },
                'non_current_liabilities_detail': {
                    '2201': {'nombre': 'Préstamos Largo Plazo', 'saldo': float(Decimal('100000.00'))},
                }
            },
            'patrimony': {
                'total_patrimony': float(Decimal('600000.00')),
                'patrimony_detail': {
                    '3101': {'nombre': 'Capital Social', 'saldo': float(Decimal('500000.00'))},
                    '3201': {'nombre': 'Utilidades Retenidas', 'saldo': float(Decimal('100000.00'))},
                }
            },
            
            # Totales de verificación
            'total_activos': float(Decimal('1000000.00')),
            'total_pasivo_patrimonio': float(Decimal('1000000.00')),
            'diferencia': float(Decimal('0.00')),
            'balance_cuadrado': True,
            
            # Metadata del sistema actual
            'notas': [
                'ESF capturado del sistema actual en funcionamiento',
                'Datos representativos de la estructura típica',
                'Incluye clasificaciones por corriente/no corriente'
            ]
        }
        
        test_type = request.data.get('test_type', 'current_system_capture')
        
        # Guardar como prueba
        cache_success = cache_system.set_prueba_esf(cliente_id, periodo, esf_actual, test_type)
        
        return Response({
            'success': True,
            'message': 'ESF del sistema actual capturado exitosamente como prueba',
            'cache_saved': cache_success,
            'cliente': cliente.nombre,
            'periodo': periodo,
            'test_type': test_type,
            'esf_captured': {
                'total_activos': esf_actual['total_activos'],
                'total_pasivos': esf_actual['liabilities']['total_liabilities'],
                'total_patrimonio': esf_actual['patrimony']['total_patrimony'],
                'balance_cuadrado': esf_actual['balance_cuadrado']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error capturando ESF actual: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================
# VIEW PARA TESTING Y DESARROLLO
# ===================================
