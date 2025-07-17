# backend/contabilidad/utils/activity_logger.py
"""
Activity Logger para Sistema de Gestión de Movimientos (SGM)

Sistema de logging híbrido que prioriza Redis SGM Cache y tiene fallback a Django Cache.
Utiliza claves individuales para cada log para mayor eficiencia y escalabilidad.

Arquitectura:
- Redis DB1 como cache principal
- Claves individuales por log: sgm:logs:{id}
- Retención automática de logs
- Fallback a Django Cache si Redis no está disponible

Funcionalidades:
- Registro de actividades con timestamp
- Filtrado por cliente_id y período
- Limpieza automática de logs antiguos
- Estadísticas de logs por cliente

Estructura de claves Redis:
- sgm:logs:{id} - Log individual
- sgm:logs:stats:{cliente_id} - Estadísticas por cliente (opcional)

Ejemplo de uso:
    ActivityLogStorage.log_activity(
        cliente_id=123,
        periodo="2024-01",
        action="abrir_modal",
        details={"tipo_documento": "factura"}
    )
"""
from ..models import TarjetaActivityLog, CierreContabilidad
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.cache import cache
import logging
import json
from datetime import datetime, timedelta

# Importar el sistema SGM Cache para consistencia
try:
    from ..cache_redis import get_cache_system
    SGM_CACHE_AVAILABLE = True
except ImportError:
    SGM_CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

Usuario = get_user_model()

# Verificar si Redis está disponible a través del cache de Django
try:
    # Intentar una operación simple con el cache
    cache.set('test_redis_connection', 'ok', timeout=1)
    result = cache.get('test_redis_connection')
    REDIS_AVAILABLE = result == 'ok'
    if REDIS_AVAILABLE:
        logger.info("Redis conectado para logs a través del cache Django (DB1)")
    else:
        logger.warning("Cache Django no está usando Redis")
except Exception as e:
    logger.warning(f"Redis no disponible para logs: {e}")
    REDIS_AVAILABLE = False

# Verificar si el sistema SGM Cache está disponible
if SGM_CACHE_AVAILABLE:
    try:
        sgm_cache = get_cache_system()
        logger.info("Sistema SGM Cache disponible para logs")
    except Exception as e:
        logger.warning(f"Sistema SGM Cache no disponible: {e}")
        SGM_CACHE_AVAILABLE = False

class ActivityLogStorage:
    """Gestión de almacenamiento híbrido para logs de actividad usando Django Cache"""
    
    RECENT_LOGS_TTL = 7 * 24 * 60 * 60  # 7 días en segundos
    MAX_LOGS_PER_CLIENT = 1000
    
    @staticmethod
    def _get_redis_client():
        """Obtiene el cliente Redis a través del cache de Django"""
        if not REDIS_AVAILABLE:
            return None
        try:
            # Acceder al cliente Redis subyacente si está disponible
            if hasattr(cache, '_cache') and hasattr(cache._cache, '_cache'):
                return cache._cache._cache
            return None
        except Exception:
            return None
    
    @staticmethod
    def save_to_redis(log_entry):
        """Guarda log usando el sistema SGM Cache global o fallback a Django cache"""
        
        # Prioridad 1: Usar sistema SGM Cache (estructura global sgm:logs)
        if SGM_CACHE_AVAILABLE:
            try:
                sgm_cache = get_cache_system()
                
                # Serializar el log para el sistema SGM
                log_data = {
                    'id': log_entry.id,
                    'cliente_id': log_entry.cierre.cliente.id,
                    'cliente_nombre': log_entry.cierre.cliente.nombre,
                    'usuario_id': log_entry.usuario.id if log_entry.usuario else None,
                    'usuario_nombre': f"{log_entry.usuario.nombre} {log_entry.usuario.apellido}" if log_entry.usuario else 'Sistema',
                    'usuario_email': log_entry.usuario.correo_bdo if log_entry.usuario else None,
                    'tarjeta': log_entry.tarjeta,
                    'accion': log_entry.accion,
                    'descripcion': log_entry.descripcion,
                    'resultado': log_entry.resultado,
                    'timestamp': log_entry.timestamp.isoformat(),
                    'ip_address': log_entry.ip_address,
                    'detalles': log_entry.detalles,
                    'estado_cierre': log_entry.cierre.estado,
                    'periodo_cierre': log_entry.cierre.periodo,
                }
                
                # Agregar a la lista global sgm:logs
                sgm_cache.add_log(log_data, max_logs=ActivityLogStorage.MAX_LOGS_PER_CLIENT)
                
                logger.debug(f"Log {log_entry.id} guardado en SGM Cache global")
                return
                
            except Exception as e:
                logger.error(f"Error guardando log en SGM Cache: {e}")
                # Continuar con fallback
        
        # Fallback: Usar Django cache (método anterior)
        if not REDIS_AVAILABLE:
            return
            
        try:
            # Serializar el log para cache (JSON simple, no cifrado)
            log_data = {
                'id': log_entry.id,
                'cliente_id': log_entry.cierre.cliente.id,
                'cliente_nombre': log_entry.cierre.cliente.nombre,
                'usuario_id': log_entry.usuario.id if log_entry.usuario else None,
                'usuario_nombre': f"{log_entry.usuario.nombre} {log_entry.usuario.apellido}" if log_entry.usuario else 'Sistema',
                'usuario_email': log_entry.usuario.correo_bdo if log_entry.usuario else None,
                'tarjeta': log_entry.tarjeta,
                'accion': log_entry.accion,
                'descripcion': log_entry.descripcion,
                'resultado': log_entry.resultado,
                'timestamp': log_entry.timestamp.isoformat(),
                'ip_address': log_entry.ip_address,
                'detalles': log_entry.detalles,
                'estado_cierre': log_entry.cierre.estado,
                'periodo_cierre': log_entry.cierre.periodo,
            }
            
            # Una sola lista global con namespace claro
            ActivityLogStorage._add_to_global_list(log_data)
            
            logger.debug(f"Log {log_entry.id} guardado en Django cache (fallback)")
                
        except Exception as e:
            logger.error(f"Error guardando log {log_entry.id} en cache: {e}")
    
    @staticmethod
    def _add_to_global_list(log_data):
        """Agrega un log a la lista global de logs recientes"""
        try:
            # Clave con el patrón consistente con los cierres
            list_key = "sgm:contabilidad:logs"
            
            # Obtener lista existente usando cache raw (sin prefijo Django)
            logs_list = cache.get(list_key, [])
            
            # Agregar nuevo log al inicio (más reciente)
            logs_list.insert(0, log_data)
            
            # Limitar a los más recientes solamente
            if len(logs_list) > ActivityLogStorage.MAX_LOGS_PER_CLIENT:
                logs_list = logs_list[:ActivityLogStorage.MAX_LOGS_PER_CLIENT]
            
            # Guardar lista actualizada
            cache.set(list_key, logs_list, timeout=ActivityLogStorage.RECENT_LOGS_TTL)
            
        except Exception as e:
            logger.error(f"Error actualizando lista global: {e}")
    
    @staticmethod
    def get_recent_logs(cliente_id=None, periodo=None, limit=100):
        """Obtiene logs recientes usando SGM Cache global o fallback a Django cache"""
        
        # Prioridad 1: Usar sistema SGM Cache (estructura global sgm:logs)
        if SGM_CACHE_AVAILABLE:
            try:
                sgm_cache = get_cache_system()
                
                # Obtener logs filtrados de la lista global
                logs = sgm_cache.get_logs_filtered(
                    cliente_id=cliente_id, 
                    periodo=periodo, 
                    limit=limit
                )
                
                logger.debug(f"Logs obtenidos desde SGM Cache global: {len(logs)} logs")
                return logs
                    
            except Exception as e:
                logger.error(f"Error obteniendo logs desde SGM Cache: {e}")
                # Continuar con fallback
        
        # Fallback: Usar Django cache (método anterior)
        if not REDIS_AVAILABLE:
            return []
            
        try:
            # Obtener lista global con patrón consistente
            logs = cache.get("sgm:contabilidad:logs", [])
            
            # Aplicar filtros si se proporcionan
            if cliente_id:
                logs = [log for log in logs if log.get('cliente_id') == cliente_id]
            
            if periodo:
                logs = [log for log in logs if log.get('periodo_cierre') == periodo]
            
            # Limitar cantidad y devolver
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo logs desde cache: {e}")
            return []
    
    @staticmethod
    def clear_client_logs(cliente_id):
        """Limpia logs de un cliente específico usando SGM Cache o fallback"""
        
        # Prioridad 1: Usar sistema SGM Cache
        if SGM_CACHE_AVAILABLE:
            try:
                sgm_cache = get_cache_system()
                
                # Con la nueva estructura de claves individuales sgm:logs:{id}, 
                # necesitamos obtener logs filtrados y eliminarlos
                logs_cliente = sgm_cache.get_logs_filtered(cliente_id=cliente_id, limit=None)
                
                if logs_cliente:
                    # Obtener IDs de logs a eliminar
                    logs_to_delete = []
                    for log in logs_cliente:
                        log_id = log.get('id')
                        if log_id:
                            log_key = f"sgm:logs:{log_id}"
                            logs_to_delete.append(log_key)
                    
                    # Eliminar logs específicos del cliente
                    if logs_to_delete:
                        deleted_count = sgm_cache.redis_client.delete(*logs_to_delete)
                        logger.info(f"Limpiados {deleted_count} logs de cliente {cliente_id} en SGM Cache")
                    else:
                        logger.info(f"No se encontraron logs para eliminar del cliente {cliente_id}")
                else:
                    logger.info(f"No hay logs del cliente {cliente_id} para eliminar")
                
                return
                
            except Exception as e:
                logger.error(f"Error limpiando logs de cliente en SGM Cache: {e}")
                # Continuar con fallback
        
        # Fallback: Django cache
        if not REDIS_AVAILABLE:
            return
            
        try:
            # Obtener lista global
            logs = cache.get("sgm:contabilidad:logs", [])
            
            # Filtrar para remover logs del cliente
            filtered_logs = [log for log in logs if log.get('cliente_id') != cliente_id]
            
            # Guardar lista filtrada
            cache.set("sgm:contabilidad:logs", filtered_logs, timeout=ActivityLogStorage.RECENT_LOGS_TTL)
            
            logger.info(f"Limpiados logs de cliente {cliente_id} en Django cache")
            
        except Exception as e:
            logger.error(f"Error limpiando logs de cliente {cliente_id}: {e}")
    
    @staticmethod
    def get_redis_stats():
        """Obtiene estadísticas de la lista global de logs"""
        
        # Prioridad 1: Usar sistema SGM Cache
        if SGM_CACHE_AVAILABLE:
            try:
                sgm_cache = get_cache_system()
                
                # Obtener estadísticas completas del sistema SGM
                logs_stats = sgm_cache.get_logs_stats()
                cache_stats = sgm_cache.get_cache_stats()
                
                return {
                    "redis_available": True,
                    "system": "SGM_Cache",
                    "logs_structure": "global",
                    "logs_key": "sgm:logs",
                    "database": 1,
                    **logs_stats,
                    "cache_system_stats": cache_stats,
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo stats SGM Cache: {e}")
                # Continuar con fallback
        
        # Fallback: Django cache
        if not REDIS_AVAILABLE:
            return {"redis_available": False}
            
        try:
            # Contar logs en lista global
            global_logs = cache.get("sgm:contabilidad:logs", [])
            global_count = len(global_logs)
            
            # Obtener cliente Redis subyacente si está disponible
            redis_client = ActivityLogStorage._get_redis_client()
            if redis_client:
                try:
                    info = redis_client.info()
                    return {
                        "redis_available": True,
                        "system": "Django_Cache",
                        "memory_used": info.get('used_memory_human', 'N/A'),
                        "total_keys": info.get('db1', {}).get('keys', 0) if 'db1' in info else 0,
                        "global_logs_count": global_count,
                        "redis_version": info.get('redis_version', 'N/A'),
                        "database": 1,
                        "structure": "single_global_list",
                        "key": "sgm:contabilidad:logs"
                    }
                except Exception:
                    pass
            
            return {
                "redis_available": True,
                "system": "Django_Cache",
                "memory_used": "N/A",
                "total_keys": "N/A",
                "global_logs_count": global_count,
                "redis_version": "N/A",
                "database": 1,
                "using_django_cache": True,
                "structure": "single_global_list",
                "key": "sgm:contabilidad:logs"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo stats del cache: {e}")
            return {"redis_available": False, "error": str(e)}

def registrar_actividad_tarjeta(
    cliente_id,
    periodo,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado='exito',
    ip_address=None
):
    """
    Registra una actividad en una tarjeta específica usando almacenamiento híbrido
    
    Args:
        cliente_id: ID del cliente
        periodo: Periodo del cierre (ej: "2025-06")
        tarjeta: Tipo de tarjeta ('tipo_documento', 'libro_mayor', etc.)
        accion: Acción realizada ('manual_create', 'upload_excel', etc.)
        descripcion: Descripción legible de la acción
        usuario: Usuario que realizó la acción (opcional)
        detalles: Dict con información adicional (opcional)
        resultado: 'exito', 'error', 'warning'
        ip_address: IP del usuario (opcional)
    
    Returns:
        TarjetaActivityLog: El log creado
    """
    try:
        logger.debug(
            "registrar_actividad_tarjeta cliente=%s periodo=%s tarjeta=%s accion=%s",
            cliente_id,
            periodo,
            tarjeta,
            accion,
        )

        # Buscar el cierre (no crearlo implícitamente)
        cierre = CierreContabilidad.objects.filter(
            cliente_id=cliente_id,
            periodo=periodo,
        ).first()

        if not cierre:
            # Si no existe el cierre, no registrar actividad para evitar
            # crearlo de forma involuntaria
            logger.warning(
                "Se intentó registrar actividad para un cierre inexistente (%s - %s)",
                cliente_id,
                periodo,
            )
            return None
        
        # Crear el log en PostgreSQL (persistencia)
        log_entry = TarjetaActivityLog.objects.create(
            cierre=cierre,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles or {},
            resultado=resultado,
            ip_address=ip_address
        )
        
        # Guardar en Redis para acceso rápido (no bloqueante)
        try:
            ActivityLogStorage.save_to_redis(log_entry)
        except Exception as e:
            logger.error(f"Error guardando en Redis (continuando): {e}")
        
        return log_entry
        
    except Exception as e:
        # En caso de error, no fallar la operación principal
        logger.error("Error registrando actividad: %s", e)
        return None

def obtener_logs_tarjeta(cliente_id, periodo, tarjeta=None):
    """
    Obtiene los logs de actividad para un cierre específico
    
    Args:
        cliente_id: ID del cliente
        periodo: Periodo del cierre
        tarjeta: Filtrar por tarjeta específica (opcional)
    
    Returns:
        QuerySet: Logs de actividad ordenados por timestamp
    """
    try:
        cierre = CierreContabilidad.objects.get(
            cliente_id=cliente_id,
            periodo=periodo
        )
        
        logs = TarjetaActivityLog.objects.filter(cierre=cierre)
        
        if tarjeta:
            logs = logs.filter(tarjeta=tarjeta)
            
        return logs.select_related('usuario').order_by('-timestamp')
        
    except CierreContabilidad.DoesNotExist:
        return TarjetaActivityLog.objects.none()
