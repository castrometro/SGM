import json
import redis
import logging
import os
from typing import Optional, Dict, Any
from functools import lru_cache

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache global para reutilizar conexión Redis
_redis_client = None


def conectar_redis():
    """Conectar a Redis DB 2 (nómina) con reutilización de conexión"""
    global _redis_client
    
    # Reutilizar conexión existente si está activa
    if _redis_client is not None:
        try:
            _redis_client.ping()
            logger.debug("🔄 Reutilizando conexión Redis existente")
            return _redis_client
        except:
            logger.info("🔄 Conexión Redis caducada, reconectando...")
            _redis_client = None
    
    try:
        # Obtener configuración de Redis desde variables de entorno
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', 'Redis_Password_2025!')
        redis_db = int(os.getenv('REDIS_DB_NOMINA', '2'))
        
        logger.info(f"🔗 Conectando a Redis: {redis_host}:{redis_port} DB:{redis_db}")
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,  # DB 2 para nómina
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Verificar conexión
        if _redis_client.ping():
            logger.info("✅ Conectado a Redis DB 2 (nómina)")
            return _redis_client
        else:
            logger.error("❌ No se pudo conectar a Redis")
            _redis_client = None
            return None
            
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        _redis_client = None
        return None


def obtener_informes_disponibles_redis(cliente_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Obtener lista de informes de nómina disponibles en Redis
    
    Args:
        cliente_id: ID del cliente específico (opcional)
        
    Returns:
        Dict con información de informes disponibles
    """
    redis_client = conectar_redis()
    if not redis_client:
        return {'error': 'No se pudo conectar a Redis', 'informes': []}
    
    try:
        # Buscar claves que coincidan con el patrón de nómina
        if cliente_id:
            pattern = f"sgm:nomina:{cliente_id}:*:informe"
        else:
            pattern = "sgm:nomina:*:*:informe"
        
        claves = redis_client.keys(pattern)
        informes = []
        
        for clave in claves:
            try:
                # Extraer información de la clave: sgm:nomina:cliente_id:periodo:informe
                partes = clave.split(':')
                if len(partes) >= 4:
                    cliente_id_key = partes[2]
                    periodo_key = partes[3]
                    
                    # Obtener TTL para mostrar tiempo restante
                    ttl = redis_client.ttl(clave)
                    
                    # Obtener metadatos básicos sin cargar el informe completo
                    data_raw = redis_client.get(clave)
                    if data_raw:
                        data = json.loads(data_raw)
                        informes.append({
                            'cliente_id': int(cliente_id_key),
                            'periodo': periodo_key,
                            'cliente_nombre': data.get('cliente_nombre', f'Cliente {cliente_id_key}'),
                            'fecha_generacion': data.get('fecha_generacion'),
                            'usuario_finalizacion': data.get('usuario_finalizacion'),
                            'ttl_segundos': ttl,
                            'clave_redis': clave,
                            'size_kb': len(data_raw) / 1024
                        })
            except Exception as e:
                logger.warning(f"⚠️ Error procesando clave {clave}: {e}")
        
        return {
            'informes': sorted(informes, key=lambda x: x['fecha_generacion'], reverse=True),
            'total': len(informes),
            'ruta_redis': f'{redis_client.connection_pool.connection_kwargs["host"]}:{redis_client.connection_pool.connection_kwargs["port"]}/DB{redis_client.connection_pool.connection_kwargs["db"]}'
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo informes disponibles: {e}")
        return {'error': str(e), 'informes': []}


def cargar_datos_redis(cliente_id: int = 6, periodo: str = "2025-03") -> Optional[Dict[str, Any]]:
    """
    🚀 Cargar informe de nómina desde Redis
    
    Args:
        cliente_id: ID del cliente
        periodo: Período de nómina (formato YYYY-MM)
        
    Returns:
        Dict con datos del informe de nómina desde Redis o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        logger.warning(f"⚠️ No se pudo conectar a Redis")
        return None

    # Construir clave Redis para nómina
    clave_redis = f"sgm:nomina:{cliente_id}:{periodo}:informe"
    
    try:
        logger.info(f"🔍 Buscando informe en Redis: {clave_redis}")
        
        # Obtener datos desde Redis
        data_raw = redis_client.get(clave_redis)
        
        if not data_raw:
            logger.warning(f"❌ No se encontró informe en Redis para cliente {cliente_id}, período {periodo}")
            return None
        
        # Parsear JSON
        data = json.loads(data_raw)
        
        logger.info(f"✅ Informe encontrado en Redis: {data.get('cliente_nombre')} - {periodo}")
        logger.info(f"📏 Tamaño: {len(data_raw)/1024:.1f} KB")
        
        # Verificar que tiene la estructura esperada
        if 'datos_cierre' not in data:
            logger.warning(f"⚠️ Estructura de datos incompleta en Redis")
            return None
        
        # Estructurar datos para Streamlit (compatibilidad con data_real.json)
        datos_streamlit = {
            "fuente": "redis",
            "informe_id": data.get('informe_id'),
            "cliente_id": data.get('cliente_id'),
            "cliente_nombre": data.get('cliente_nombre'),
            "periodo": data.get('periodo'),
            "estado_cierre": data.get('estado_cierre'),
            "fecha_generacion": data.get('fecha_generacion'),
            "fecha_finalizacion": data.get('fecha_finalizacion'),
            "usuario_finalizacion": data.get('usuario_finalizacion'),
            "version_calculo": data.get('version_calculo'),
            "tiempo_calculo_segundos": data.get('tiempo_calculo_segundos'),
            
            # Datos del cierre completos
            "datos_cierre": data.get('datos_cierre', {}),
            
            # KPIs principales
            "kpis_principales": data.get('kpis_principales', {}),
            
            # Metadatos adicionales
            "_metadata": {
                "cliente_id": cliente_id,
                "periodo": periodo,
                "cached_at": data.get('fecha_generacion'),
                "ttl": redis_client.ttl(clave_redis),
                "tipo": "informe_nomina",
                "version": data.get('version_calculo', '1.0'),
                "clave_redis": clave_redis,
                "size_kb": len(data_raw) / 1024
            }
        }
        
        return datos_streamlit
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON desde Redis: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error cargando datos desde Redis: {e}")
        return None


def obtener_info_redis_completa(cliente_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Obtener información completa de Redis incluyendo informes disponibles
    
    Args:
        cliente_id: ID del cliente específico (opcional)
        
    Returns:
        Dict con información completa de Redis
    """
    redis_client = conectar_redis()
    
    if not redis_client:
        return {
            'error': 'No se pudo conectar a Redis',
            'ruta_redis': 'redis:6379/DB2 (Error de conexión)',
            'cliente_id': cliente_id,
            'cierres_disponibles': []
        }
    
    # Obtener informes disponibles
    info_informes = obtener_informes_disponibles_redis(cliente_id)
    
    try:
        return {
            'ruta_redis': f'{redis_client.connection_pool.connection_kwargs["host"]}:{redis_client.connection_pool.connection_kwargs["port"]}/DB{redis_client.connection_pool.connection_kwargs["db"]}',
            'cliente_id': cliente_id,
            'cierres_disponibles': [
                {
                    'periodo': informe['periodo'],
                    'cliente_id': informe['cliente_id'],
                    'cliente_nombre': informe['cliente_nombre'],
                    'fecha_generacion': informe['fecha_generacion'],
                    'ttl_segundos': informe['ttl_segundos']
                }
                for informe in info_informes.get('informes', [])
            ],
            'total_informes': info_informes.get('total', 0),
            'error': info_informes.get('error')
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo información completa: {e}")
        return {
            'error': str(e),
            'ruta_redis': 'Error',
            'cliente_id': cliente_id,
            'cierres_disponibles': []
        }
