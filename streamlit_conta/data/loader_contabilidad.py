import json
import pathlib
import redis
import logging
import os
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def conectar_redis():
    """Conectar a Redis DB 1 (contabilidad)"""
    try:
        # Obtener configuración de Redis desde variables de entorno
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD', 'Redis_Password_2025!')
        redis_db = int(os.getenv('REDIS_DB_CONTABILIDAD', '1'))
        
        logger.info(f"🔗 Intentando conectar a Redis: {redis_host}:{redis_port} DB:{redis_db}")
        
        redis_client = redis.Redis(
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
        if redis_client.ping():
            logger.info("✅ Conectado a Redis DB 1 (contabilidad)")
            return redis_client
        else:
            logger.error("❌ No se pudo conectar a Redis")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        return None


def cargar_esf_desde_redis(cliente_id: int = 1, periodo: str = "2025-07", test_type: str = "finalizacion_automatica") -> Optional[Dict[str, Any]]:
    """
    Cargar ESF desde Redis carpeta de pruebas
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        test_type: Tipo de test ("finalizacion_automatica", "current_system", etc.)
        
    Returns:
        Dict con ESF o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        return None
    
    try:
        # Construir la clave Redis
        key = f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:esf:{test_type}"
        
        # Obtener datos
        data = redis_client.get(key)
        if data:
            esf_data = json.loads(data)
            logger.info(f"✅ ESF cargado desde Redis: {key}")
            return esf_data
        else:
            logger.warning(f"⚠️ No se encontró ESF en Redis: {key}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error cargando ESF desde Redis: {e}")
        return None


def listar_esf_disponibles(cliente_id: int = 1) -> Dict[str, Any]:
    """
    Listar todos los ESF disponibles en Redis para un cliente
    
    Args:
        cliente_id: ID del cliente
        
    Returns:
        Dict con información de ESF disponibles
    """
    redis_client = conectar_redis()
    if not redis_client:
        return {"error": "No se pudo conectar a Redis", "esf_disponibles": []}
    
    try:
        # Buscar todas las claves de ESF de prueba para el cliente
        pattern = f"sgm:contabilidad:{cliente_id}:*:pruebas:esf:*"
        keys = redis_client.keys(pattern)
        
        esf_disponibles = []
        for key in keys:
            parts = key.split(':')
            if len(parts) >= 7:
                periodo = parts[3]
                test_type = parts[6]
                
                # Obtener metadata básica
                try:
                    data = redis_client.get(key)
                    if data:
                        esf_data = json.loads(data)
                        esf_info = {
                            'cliente_id': cliente_id,
                            'periodo': periodo,
                            'test_type': test_type,
                            'redis_key': key,
                            'generated_at': esf_data.get('generated_at', 'N/A'),
                            'generated_by': esf_data.get('generated_by', 'N/A'),
                            'source': esf_data.get('source', 'N/A'),
                            'total_activos': esf_data.get('total_activos', 0),
                            'balance_cuadrado': esf_data.get('balance_cuadrado', False)
                        }
                        esf_disponibles.append(esf_info)
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando clave {key}: {e}")
        
        logger.info(f"✅ Encontrados {len(esf_disponibles)} ESF para cliente {cliente_id}")
        return {
            "cliente_id": cliente_id,
            "total_esf": len(esf_disponibles),
            "esf_disponibles": esf_disponibles
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando ESF: {e}")
        return {"error": str(e), "esf_disponibles": []}


def cargar_datos():
    """Load example accounting data for the Streamlit dashboard."""

    base = pathlib.Path(__file__).parent
    with open(base / "contabilidad_ejemplo.json", encoding="utf-8") as f:
        raw = json.load(f)

    cierre_actual = raw.get("cierres", [{}])[0]
    return {
        "cliente": raw.get("cliente"),
        "clasificaciones": raw.get("clasificaciones", []),
        "centros_costo": raw.get("centros_costo", []),
        "tipos_documento": raw.get("tipos_documento", []),
        "cierre": {
            k: cierre_actual.get(k)
            for k in [
                "id",
                "cliente",
                "periodo",
                "estado",
                "fecha_inicio_libro",
                "fecha_fin_libro",
                "cuentas_nuevas",
                "parsing_completado",
            ]
        },
        "plan_cuentas": cierre_actual.get("plan_cuentas", []),
        "movimientos": cierre_actual.get("movimientos", []),
        "resumen_financiero": cierre_actual.get("resumen_financiero", {})
    }


def cargar_datos_redis(cliente_id: int = 1, periodo: str = "2025-07", test_type: str = "finalizacion_automatica") -> Dict[str, Any]:
    """
    Cargar datos contables desde Redis (carpeta de pruebas)
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable  
        test_type: Tipo de test
        
    Returns:
        Dict con datos contables desde Redis o datos de ejemplo como fallback
    """
    # Intentar cargar desde Redis
    esf_redis = cargar_esf_desde_redis(cliente_id, periodo, test_type)
    
    if esf_redis:
        logger.info(f"✅ Usando datos de Redis para cliente {cliente_id}, período {periodo}")
        
        # Construir estructura compatible con Streamlit
        return {
            "fuente": "redis",
            "cliente": {
                "id": esf_redis.get("cliente_id", cliente_id),
                "nombre": esf_redis.get("cliente_nombre", f"Cliente {cliente_id}")
            },
            "cierre": {
                "id": esf_redis.get("cierre_id", None),
                "cliente": cliente_id,
                "periodo": periodo,
                "estado": "finalizado" if esf_redis.get("balance_cuadrado", False) else "en_proceso",
                "fecha_generacion": esf_redis.get("generated_at"),
                "source": esf_redis.get("source", test_type)
            },
            "estado_financiero": esf_redis,
            "metadata": {
                "test_type": test_type,
                "generated_by": esf_redis.get("generated_by"),
                "redis_key": f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:esf:{test_type}",
                "metadata_prueba": esf_redis.get("metadata_prueba", {}),
                "contexto_generacion": esf_redis.get("contexto_generacion", {})
            },
            "raw_json": esf_redis  # JSON completo para mostrar en sidebar
        }
    else:
        logger.warning(f"⚠️ No se encontraron datos Redis, usando datos de ejemplo")
        # Fallback a datos de ejemplo
        datos_ejemplo = cargar_datos()
        datos_ejemplo["fuente"] = "archivo_ejemplo"
        datos_ejemplo["metadata"] = {
            "test_type": "ejemplo",
            "generated_by": "archivo_estatico",
            "redis_key": "N/A"
        }
        datos_ejemplo["raw_json"] = datos_ejemplo  # JSON completo para mostrar
        return datos_ejemplo
