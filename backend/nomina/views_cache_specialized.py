"""
Views especializados para manejo de caché por situación
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import CierreNomina
from .cache_redis import get_cache_system_nomina
from .views_resumen_libro import libro_resumen_v2 as libro_resumen_query
from .views_resumen_movimientos import movimientos_personal_detalle_v3 as movimientos_query


# ================================
# SITUACIÓN 1: PREVIEW (En trabajo)
# ================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def libro_preview_cached(request, cierre_id: int):
    """
    📘 SITUACIÓN 1: Preview de libro para cierres en trabajo
    
    Cache Key: {cierre_id}_cache_libro
    TTL: 15 minutos
    Estados válidos: datos_consolidados, con_incidencias, incidencias_resueltas
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)
    
    # Solo para cierres no finalizados
    if cierre.estado == 'finalizado':
        return Response({
            'error': 'Cierre finalizado. Use endpoint de reporte oficial.',
            'redirect_to': f'/api/nomina/cierres/{cierre_id}/reporte-oficial/'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache = get_cache_system_nomina()
    cache_key = f"{cierre_id}_cache_libro"
    
    # Intentar desde cache
    cached_data = cache.redis_client.get(cache_key)
    if cached_data:
        try:
            data = cache._deserialize_data(cached_data)
            data['_metadata'] = {
                'fuente': 'cache_preview',
                'cache_key': cache_key,
                'tipo': 'preview',
                'volatile': True
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            pass
    
    # Cache miss - calcular y cachear
    # Reutilizar lógica existente pero sin el caché interno
    request_copy = request._request if hasattr(request, '_request') else request
    response = libro_resumen_query(request_copy, cierre_id)
    
    if response.status_code == 200:
        data = response.data
        # Marcar como preview
        data['_metadata'] = {
            'fuente': 'query_directo_cached',
            'cache_key': cache_key,
            'tipo': 'preview',
            'volatile': True,
            'cached_at': timezone.now().isoformat()
        }
        
        # Cachear por 15 minutos
        try:
            cache.redis_client.setex(
                cache_key, 
                900,  # 15 minutos
                cache._serialize_data(data)
            )
        except Exception:
            pass
        
        return Response(data, status=status.HTTP_200_OK)
    
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movimientos_preview_cached(request, cierre_id: int):
    """
    🔄 SITUACIÓN 1: Preview de movimientos para cierres en trabajo
    
    Cache Key: {cierre_id}_cache_mov
    TTL: 15 minutos
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)
    
    if cierre.estado == 'finalizado':
        return Response({
            'error': 'Cierre finalizado. Use endpoint de reporte oficial.',
            'redirect_to': f'/api/nomina/cierres/{cierre_id}/reporte-oficial/'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache = get_cache_system_nomina()
    cache_key = f"{cierre_id}_cache_mov"
    
    # Intentar desde cache
    cached_data = cache.redis_client.get(cache_key)
    if cached_data:
        try:
            data = cache._deserialize_data(cached_data)
            data['_metadata'] = {
                'fuente': 'cache_preview',
                'cache_key': cache_key,
                'tipo': 'preview',
                'volatile': True
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            pass
    
    # Cache miss - calcular y cachear
    request_copy = request._request if hasattr(request, '_request') else request
    response = movimientos_query(request_copy, cierre_id)
    
    if response.status_code == 200:
        data = response.data
        data['_metadata'] = {
            'fuente': 'query_directo_cached',
            'cache_key': cache_key,
            'tipo': 'preview',
            'volatile': True,
            'cached_at': timezone.now().isoformat()
        }
        
        # Cachear por 15 minutos
        try:
            cache.redis_client.setex(
                cache_key,
                900,  # 15 minutos
                cache._serialize_data(data)
            )
        except Exception:
            pass
        
        return Response(data, status=status.HTTP_200_OK)
    
    return response


# ================================
# SITUACIÓN 2-3: REPORTE OFICIAL
# ================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reporte_oficial_cached(request, cierre_id: int):
    """
    📋 SITUACIÓN 2-3: Reporte oficial para cierres finalizados
    
    Cache Key: {cierre_id}_informe_oficial
    TTL: Permanente
    Fuente: InformeNomina.datos_cierre
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)
    
    if cierre.estado != 'finalizado':
        return Response({
            'error': 'Cierre no finalizado. Use endpoints de preview.',
            'libro_preview': f'/api/nomina/cierres/{cierre_id}/libro-preview/',
            'movimientos_preview': f'/api/nomina/cierres/{cierre_id}/movimientos-preview/'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache = get_cache_system_nomina()
    cache_key = f"{cierre_id}_informe_oficial"
    
    # Intentar desde cache
    cached_data = cache.redis_client.get(cache_key)
    if cached_data:
        try:
            data = cache._deserialize_data(cached_data)
            data['_metadata'] = {
                'fuente': 'cache_oficial',
                'cache_key': cache_key,
                'tipo': 'reporte_oficial',
                'volatile': False
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            pass
    
    # Cache miss - buscar en BD
    try:
        informe = getattr(cierre, 'informe', None)
        if not informe or not isinstance(informe.datos_cierre, dict):
            return Response({
                'error': 'Informe no encontrado en BD',
                'cierre_id': cierre_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = informe.datos_cierre
        data['_metadata'] = {
            'fuente': 'bd_cached',
            'cache_key': cache_key,
            'tipo': 'reporte_oficial',
            'volatile': False,
            'cached_at': timezone.now().isoformat()
        }
        
        # Cachear permanentemente
        try:
            cache.redis_client.set(
                cache_key,
                cache._serialize_data(data)
            )
        except Exception:
            pass
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Error obteniendo informe',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# DASHBOARD UNIFICADO
# ================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_unificado(request, cierre_id: int):
    """
    🎯 DASHBOARD PRINCIPAL: Redirección inteligente según estado
    
    Finalizado → reporte_oficial_cached
    No finalizado → libro_preview_cached + movimientos_preview_cached
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)
    
    if cierre.estado == 'finalizado':
        # Redirigir a reporte oficial
        return reporte_oficial_cached(request, cierre_id)
    else:
        # Combinar ambos previews
        libro_response = libro_preview_cached(request, cierre_id)
        mov_response = movimientos_preview_cached(request, cierre_id)
        
        if libro_response.status_code == 200 and mov_response.status_code == 200:
            return Response({
                'cierre': {
                    'id': cierre.id,
                    'estado': cierre.estado,
                    'periodo': cierre.periodo
                },
                'libro_resumen_v2': libro_response.data,
                'movimientos_v3': mov_response.data,
                '_metadata': {
                    'fuente': 'preview_combinado',
                    'tipo': 'dashboard_preview',
                    'volatile': True
                }
            })
        else:
            return Response({
                'error': 'Error cargando datos preview',
                'libro_status': libro_response.status_code,
                'movimientos_status': mov_response.status_code
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# UTILIDADES DE INVALIDACIÓN
# ================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invalidar_cache_preview(request, cierre_id: int):
    """
    🗑️ Invalidar cache preview específico
    
    Usado por: reclasificación, corregir libro
    """
    cache = get_cache_system_nomina()
    
    keys_to_delete = [
        f"{cierre_id}_cache_libro",
        f"{cierre_id}_cache_mov"
    ]
    
    deleted_count = 0
    for key in keys_to_delete:
        try:
            if cache.redis_client.delete(key):
                deleted_count += 1
        except Exception:
            pass
    
    return Response({
        'mensaje': 'Cache preview invalidado',
        'cierre_id': cierre_id,
        'keys_deleted': deleted_count,
        'keys_attempted': keys_to_delete
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def promover_a_oficial(request, cierre_id: int):
    """
    🎓 Al finalizar cierre: eliminar preview + crear oficial
    
    Llamar desde tasks de finalización
    """
    # Eliminar cache preview
    invalidar_cache_preview(request, cierre_id)
    
    # El cache oficial se creará automáticamente en el primer acceso
    # via reporte_oficial_cached()
    
    return Response({
        'mensaje': 'Cache preview eliminado, listo para reporte oficial',
        'cierre_id': cierre_id
    })