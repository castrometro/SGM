# backend/nomina/views_redis.py

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
import logging

from .models_informe import InformeNomina
from .cache_redis import get_cache_system_nomina
from .models import CierreNomina

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def enviar_informe_redis(request, informe_id):
    """
    🚀 Endpoint para enviar un informe específico a Redis
    
    POST /api/nomina/informes/{informe_id}/enviar-redis/
    """
    try:
        # Obtener el informe
        informe = get_object_or_404(InformeNomina, id=informe_id)
        
        # Parsear parámetros opcionales
        data = json.loads(request.body) if request.body else {}
        ttl_hours = data.get('ttl_hours', 24)
        
        # Enviar a Redis
        resultado = informe.enviar_a_redis(ttl_hours=ttl_hours)
        
        if resultado['success']:
            logger.info(f"✅ Informe {informe_id} enviado a Redis por usuario {request.user.correo_bdo}")
            return JsonResponse({
                'success': True,
                'mensaje': 'Informe enviado exitosamente a Redis',
                'datos': resultado
            })
        else:
            logger.error(f"❌ Error enviando informe {informe_id} a Redis: {resultado['error']}")
            return JsonResponse({
                'success': False,
                'error': resultado['error']
            }, status=400)
            
    except Exception as e:
        logger.error(f"❌ Excepción enviando informe {informe_id} a Redis: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def obtener_informe_redis(request, cliente_id, periodo):
    """
    📥 Endpoint para obtener un informe desde Redis
    
    GET /api/nomina/redis/{cliente_id}/{periodo}/
    """
    try:
        # Obtener desde Redis
        datos_redis = InformeNomina.obtener_desde_redis(cliente_id, periodo)
        
        if datos_redis:
            logger.info(f"✅ Informe obtenido desde Redis: cliente={cliente_id}, periodo={periodo}")
            return JsonResponse({
                'success': True,
                'en_redis': True,
                'datos': datos_redis
            })
        else:
            logger.info(f"⚠️ Informe no encontrado en Redis: cliente={cliente_id}, periodo={periodo}")
            return JsonResponse({
                'success': True,
                'en_redis': False,
                'mensaje': 'Informe no encontrado en Redis'
            })
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo informe desde Redis: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def estadisticas_redis(request):
    """
    📊 Endpoint para obtener estadísticas del cache Redis de nómina
    
    GET /api/nomina/redis/estadisticas/
    """
    try:
        cache_system = get_cache_system_nomina()
        stats = cache_system.get_cache_stats()
        
        return JsonResponse({
            'success': True,
            'estadisticas': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas Redis: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def limpiar_cache_cliente(request, cliente_id):
    """
    🗑️ Endpoint para limpiar cache de un cliente específico
    
    POST /api/nomina/redis/limpiar-cliente/{cliente_id}/
    """
    try:
        # Parsear parámetros
        data = json.loads(request.body) if request.body else {}
        periodo = data.get('periodo')  # Opcional: limpiar solo un período
        
        cache_system = get_cache_system_nomina()
        
        if periodo:
            # Limpiar solo un período específico
            deleted = cache_system.invalidate_cliente_periodo(cliente_id, periodo)
            mensaje = f"Cache limpiado para cliente {cliente_id}, período {periodo}: {deleted} claves eliminadas"
        else:
            # Limpiar todos los períodos del cliente
            deleted = cache_system.invalidate_cliente_all(cliente_id)
            mensaje = f"Cache completo limpiado para cliente {cliente_id}: {deleted} claves eliminadas"
        
        logger.info(f"✅ {mensaje} por usuario {request.user.correo_bdo}")
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'claves_eliminadas': deleted
        })
        
    except Exception as e:
        logger.error(f"❌ Error limpiando cache: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def listar_informes_redis(request):
    """
    📋 Endpoint para listar todos los informes disponibles en Redis
    
    GET /api/nomina/redis/informes/
    """
    try:
        cache_system = get_cache_system_nomina()
        
        # Obtener estadísticas para ver qué clientes tienen datos
        stats = cache_system.get_cache_stats()
        clientes_con_datos = stats.get('keys_by_client', {})
        
        informes_disponibles = []
        
        for cliente_id, num_claves in clientes_con_datos.items():
            if cliente_id.isdigit():  # Solo IDs numéricos de clientes
                try:
                    periodos = cache_system.get_client_periods(int(cliente_id))
                    for periodo in periodos:
                        # Obtener datos básicos del informe
                        datos_informe = cache_system.get_informe_nomina(int(cliente_id), periodo)
                        if datos_informe:
                            informes_disponibles.append({
                                'cliente_id': int(cliente_id),
                                'cliente_nombre': datos_informe.get('cliente_nombre'),
                                'periodo': periodo,
                                'fecha_cache': datos_informe.get('_metadata', {}).get('cached_at'),
                                'kpis_principales': datos_informe.get('kpis_principales', {}),
                                'informe_id': datos_informe.get('informe_id')
                            })
                except Exception as e:
                    logger.debug(f"Error procesando cliente {cliente_id}: {e}")
                    continue
        
        return JsonResponse({
            'success': True,
            'informes': sorted(informes_disponibles, key=lambda x: x['fecha_cache'], reverse=True),
            'total': len(informes_disponibles)
        })
        
    except Exception as e:
        logger.error(f"❌ Error listando informes Redis: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def health_check_redis(request):
    """
    ❤️ Endpoint para verificar salud del sistema Redis
    
    GET /api/nomina/redis/health/
    """
    try:
        cache_system = get_cache_system_nomina()
        health = cache_system.health_check()
        
        status_code = 200 if health['status'] == 'healthy' else 503
        
        return JsonResponse(health, status=status_code)
        
    except Exception as e:
        logger.error(f"❌ Error en health check Redis: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)
