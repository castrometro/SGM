import json
import pathlib
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
    """Conectar a Redis DB 1 (contabilidad) con reutilización de conexión"""
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
        redis_db = int(os.getenv('REDIS_DB_CONTABILIDAD', '1'))
        
        logger.info(f"🔗 Conectando a Redis: {redis_host}:{redis_port} DB:{redis_db}")
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,  # DB 1 para contabilidad
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Verificar conexión
        if _redis_client.ping():
            logger.info("✅ Conectado a Redis DB 1 (contabilidad)")
            return _redis_client
        else:
            logger.error("❌ No se pudo conectar a Redis")
            _redis_client = None
            return None
            
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        _redis_client = None
        return None


def obtener_datos_batch_redis(cliente_id: int, periodo: str, redis_client) -> Dict[str, Any]:
    """
    🚀 OPTIMIZACIÓN: Obtener ESF, ERI y ECP de Redis en una sola consulta batch
    Simplificado para obtener solo los datos que realmente existen
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        redis_client: Cliente Redis conectado
        
    Returns:
        Dict con ESF, ERI y ECP disponibles
    """
    # Solo consultar los datos que realmente necesitamos: ESF, ERI y ECP
    claves_consulta = {
        'esf': f"sgm:contabilidad:{cliente_id}:{periodo}:esf",
        'eri': f"sgm:contabilidad:{cliente_id}:{periodo}:eri",
        'ecp': f"sgm:contabilidad:{cliente_id}:{periodo}:ecp"
    }
    
    datos_encontrados = {}
    
    try:
        # 🚀 USAR PIPELINE para consulta batch
        pipe = redis_client.pipeline()
        for clave in claves_consulta.values():
            pipe.get(clave)

        # Ejecutar las 3 consultas de una vez
        resultados = pipe.execute()
        
        # Procesar resultados
        for i, (nombre_dato, clave) in enumerate(claves_consulta.items()):
            if resultados[i]:
                try:
                    datos_encontrados[nombre_dato] = json.loads(resultados[i])
                    logger.info(f"✅ {nombre_dato.upper()} encontrado ({len(resultados[i])} bytes)")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Error parsing JSON para {nombre_dato}: {e}")
            else:
                logger.debug(f"❌ No encontrado: {nombre_dato}")
                
        #logger.info(f"🚀 Consulta batch completada: {len(datos_encontrados)}/3 datasets encontrados")
        
    except Exception as e:
        logger.error(f"❌ Error en consulta batch Redis: {e}")
    
    return datos_encontrados


def cargar_datos_redis(cliente_id: int = 2, periodo: str = "2025-08") -> Dict[str, Any]:
    """
    🚀 SIMPLIFICADO: Cargar ESF, ERI y ECP desde Redis
    Enfocado únicamente en los datos que realmente existen
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable  
        test_type: Tipo de test (mantenido por compatibilidad)
        
    Returns:
        Dict con ESF, ERI y ECP desde Redis o datos de ejemplo como fallback
    """
    redis_client = conectar_redis()
    if not redis_client:
        logger.warning(f"⚠️ No se pudo conectar a Redis, usando datos de ejemplo")
        return None

    # 🚀 UNA SOLA CONSULTA BATCH para ESF, ERI y ECP
    datos_redis = obtener_datos_batch_redis(cliente_id, periodo, redis_client)
    
    if datos_redis:
        logger.info(f"✅ Datos Redis encontrados para cliente {cliente_id}, período {periodo}")
        
        # Construir respuesta para Streamlit
        esf_data = datos_redis.get('esf', {})
        eri_data = datos_redis.get('eri', {})
        ecp_data = datos_redis.get('ecp', {})
        
        # Estructurar datos para Streamlit
        return {
            "fuente": "redis",
            "cliente": {
                "id": cliente_id,
                "nombre": esf_data.get("metadata", {}).get("cliente_nombre", f"Cliente {cliente_id}")
            },
            "cierre": {
                "id": esf_data.get("metadata", {}).get("cierre_id", None),
                "cliente": cliente_id,
                "periodo": periodo,
                "estado": "finalizado",
                "fecha_generacion": esf_data.get("metadata", {}).get("fecha_generacion"),
                "source": "redis"
            },
            "esf": esf_data,
            "eri": eri_data,
            "ecp": ecp_data,
            "metadata": {
                "fuente": "redis",
                "datos_disponibles": list(datos_redis.keys()),
                "total_datasets": len(datos_redis)
            },
            "raw_json": datos_redis
        }
    
    else:
        return None



def obtener_info_redis_completa(cliente_id) -> Dict[str, Any]:
    """
    Obtener información completa de Redis y cierres disponibles
    
    Returns:
        Dict con información detallada del sistema Redis
    """
    info = {
        'ruta_redis': 'redis:6379/DB1',
        'cliente_id': cliente_id,
        'cierres_disponibles': [],
        'error': None
    }
    
    try:
        # Obtener información de conexión Redis
        redis_client = conectar_redis()
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_db = os.getenv('REDIS_DB_CONTABILIDAD', '1')
        
        info['ruta_redis'] = f"{redis_host}:{redis_port}/DB{redis_db}"
        
        # Obtener cierres disponibles para el cliente
        pattern = f"sgm:contabilidad:{cliente_id}:*:esf"
        claves_esf = redis_client.keys(pattern)
        
        # Extraer períodos únicos
        periodos = []
        for clave in claves_esf:
            parts = clave.split(':')
            if len(parts) >= 4:
                periodo = parts[3]  # sgm:contabilidad:{cliente_id}:{periodo}:esf
                
                # Verificar que también existe ERI y opcionalmente ECP
                clave_eri = clave.replace(':esf', ':eri')
                if redis_client.exists(clave_eri):
                    periodos.append(periodo)
        
        # Ordenar períodos (más reciente primero)
        periodos_unicos = sorted(list(set(periodos)), reverse=True)
        info['cierres_disponibles'] = periodos_unicos
        
        #logger.info(f"✅ Redis info obtenida: {len(periodos_unicos)} cierres para cliente {cliente_id}")
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info Redis: {e}")
        info['error'] = str(e)
        # Fallback con datos de ejemplo
        #info['cierres_disponibles'] = ['2025-03', '2025-02', '2025-01']
    
    return info



def verificar_disponibilidad_redis(cliente_id: int, periodo: str) -> Dict[str, bool]:
    """
    Verificar si los datos de un cierre específico están disponibles en Redis
    
    Args:
        cliente_id: ID del cliente
        periodo: Período del cierre (ej: '2025-03')
    
    Returns:
        Dict con disponibilidad de ESF, ERI y ECP en Redis
    """
    disponibilidad = {
        'esf_disponible': False,
        'eri_disponible': False,
        'ecp_disponible': False,
        'dashboard_disponible': False,
        'error': None
    }
    
    try:
        redis_client = conectar_redis()
        
        # Verificar existencia de datos ESF
        clave_esf = f"sgm:contabilidad:{cliente_id}:{periodo}:esf"
        disponibilidad['esf_disponible'] = redis_client.exists(clave_esf)
        
        # Verificar existencia de datos ERI
        clave_eri = f"sgm:contabilidad:{cliente_id}:{periodo}:eri"
        disponibilidad['eri_disponible'] = redis_client.exists(clave_eri)
        
        # Verificar existencia de datos ECP
        clave_ecp = f"sgm:contabilidad:{cliente_id}:{periodo}:ecp"
        disponibilidad['ecp_disponible'] = redis_client.exists(clave_ecp)
        
        # Dashboard disponible si ESF y ERI existen (ECP es opcional)
        disponibilidad['dashboard_disponible'] = (
            disponibilidad['esf_disponible'] and 
            disponibilidad['eri_disponible']
        )
        
        logger.debug(f"📊 Disponibilidad Redis cliente {cliente_id} período {periodo}: "
                    f"ESF={disponibilidad['esf_disponible']}, "
                    f"ERI={disponibilidad['eri_disponible']}, "
                    f"ECP={disponibilidad['ecp_disponible']}")
        
    except Exception as e:
        logger.error(f"❌ Error verificando disponibilidad Redis: {e}")
        disponibilidad['error'] = str(e)
    
    return disponibilidad