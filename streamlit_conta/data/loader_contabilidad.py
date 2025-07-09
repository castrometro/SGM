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


def cargar_esf_desde_redis(cliente_id: int = 2, periodo: str = "2025-08", test_type: str = "finalizacion_automatica") -> Optional[Dict[str, Any]]:
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
        # Construir la clave Redis para finalizacion_automatica
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
        # Buscar todas las claves de ESF de prueba para el cliente (finalizacion_automatica)
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


def cargar_datos_sistema_cierre(cliente_id: int = 2, periodo: str = "2025-08") -> Optional[Dict[str, Any]]:
    """
    Cargar datos completos del sistema de cierre desde Redis (datos finales del sistema)
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        
    Returns:
        Dict con datos completos del cierre o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        return None
    
    try:
        # Buscar datos del cierre finalizado
        datos_cierre = {}
        
        # 1. KPIs del cierre
        key_kpis = f"sgm:contabilidad:{cliente_id}:{periodo}:kpis"
        kpis_data = redis_client.get(key_kpis)
        if kpis_data:
            datos_cierre['kpis'] = json.loads(kpis_data)
            logger.info(f"✅ KPIs cargados desde {key_kpis}")
        
        # 2. Estado de Situación Financiera (ESF) desde finalizacion_automatica
        key_esf = f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:esf:finalizacion_automatica"
        esf_data = redis_client.get(key_esf)
        if esf_data:
            datos_cierre['esf'] = json.loads(esf_data)
            logger.info(f"✅ ESF cargado desde {key_esf}")
        else:
            # Fallback: intentar la clave directa
            key_esf_directo = f"sgm:contabilidad:{cliente_id}:{periodo}:esf"
            esf_data_directo = redis_client.get(key_esf_directo)
            if esf_data_directo:
                datos_cierre['esf'] = json.loads(esf_data_directo)
                logger.info(f"✅ ESF cargado desde {key_esf_directo}")
        
        # 3. Estado de Resultados (ESR)
        key_esr = f"sgm:contabilidad:{cliente_id}:{periodo}:esr"
        esr_data = redis_client.get(key_esr)
        if esr_data:
            datos_cierre['esr'] = json.loads(esr_data)
            logger.info(f"✅ ESR cargado desde {key_esr}")
        
        # 4. Estado de Resultados Integral (ERI)
        key_eri = f"sgm:contabilidad:{cliente_id}:{periodo}:eri"
        eri_data = redis_client.get(key_eri)
        if eri_data:
            datos_cierre['eri'] = json.loads(eri_data)
            logger.info(f"✅ ERI cargado desde {key_eri}")
        
        # 5. Estado de Cambios en el Patrimonio (ECP)
        key_ecp = f"sgm:contabilidad:{cliente_id}:{periodo}:ecp"
        ecp_data = redis_client.get(key_ecp)
        if ecp_data:
            datos_cierre['ecp'] = json.loads(ecp_data)
            logger.info(f"✅ ECP cargado desde {key_ecp}")
        
        # 6. Alertas del cierre
        key_alertas = f"sgm:contabilidad:{cliente_id}:{periodo}:alertas"
        alertas_data = redis_client.get(key_alertas)
        if alertas_data:
            datos_cierre['alertas'] = json.loads(alertas_data)
            logger.info(f"✅ Alertas cargadas desde {key_alertas}")
        
        # 7. Estado de procesamiento
        key_procesamiento = f"sgm:contabilidad:{cliente_id}:{periodo}:procesamiento"
        procesamiento_data = redis_client.get(key_procesamiento)
        if procesamiento_data:
            datos_cierre['procesamiento'] = json.loads(procesamiento_data)
            logger.info(f"✅ Estado de procesamiento cargado desde {key_procesamiento}")
        
        # 8. Movimientos
        key_movimientos = f"sgm:contabilidad:{cliente_id}:{periodo}:movimientos"
        movimientos_data = redis_client.get(key_movimientos)
        if movimientos_data:
            datos_cierre['movimientos'] = json.loads(movimientos_data)
            logger.info(f"✅ Movimientos cargados desde {key_movimientos}")
        
        # 9. Catálogo de cuentas
        key_cuentas = f"sgm:contabilidad:{cliente_id}:{periodo}:cuentas"
        cuentas_data = redis_client.get(key_cuentas)
        if cuentas_data:
            datos_cierre['cuentas'] = json.loads(cuentas_data)
            logger.info(f"✅ Cuentas cargadas desde {key_cuentas}")
        
        if datos_cierre:
            logger.info(f"✅ Datos del sistema de cierre cargados para cliente {cliente_id}, período {periodo}")
            return datos_cierre
        else:
            logger.warning(f"⚠️ No se encontraron datos del sistema de cierre")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error cargando datos del sistema de cierre: {e}")
        return None


def cargar_datos_redis(cliente_id: int = 2, periodo: str = "2025-08", test_type: str = "finalizacion_automatica") -> Dict[str, Any]:
    """
    Cargar datos contables desde Redis (primero sistema de cierre, luego carpeta de pruebas)
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable  
        test_type: Tipo de test
        
    Returns:
        Dict con datos contables desde Redis o datos de ejemplo como fallback
    """
    # 1. Intentar cargar desde el sistema de cierre completo
    datos_sistema = cargar_datos_sistema_cierre(cliente_id, periodo)
    
    if datos_sistema:
        logger.info(f"✅ Usando datos del sistema de cierre para cliente {cliente_id}, período {periodo}")
        
        # Estructurar datos para Streamlit
        return {
            "fuente": "sistema_cierre",
            "cliente": {
                "id": cliente_id,
                "nombre": datos_sistema.get("esf", {}).get("metadata", {}).get("cliente_nombre", f"Cliente {cliente_id}")
            },
            "cierre": {
                "id": datos_sistema.get("esf", {}).get("metadata", {}).get("cierre_id", None),
                "cliente": cliente_id,
                "periodo": periodo,
                "estado": "finalizado",
                "fecha_generacion": datos_sistema.get("esf", {}).get("metadata", {}).get("fecha_generacion"),
                "source": "sistema_cierre"
            },
            "esf": datos_sistema.get("esf", {}),
            "esr": datos_sistema.get("esr", {}),
            "eri": datos_sistema.get("eri", {}),
            "ecp": datos_sistema.get("ecp", {}),
            "kpis": datos_sistema.get("kpis", {}),
            "alertas": datos_sistema.get("alertas", []),
            "procesamiento": datos_sistema.get("procesamiento", {}),
            "movimientos": datos_sistema.get("movimientos", []),
            "cuentas": datos_sistema.get("cuentas", {}),
            "metadata": {
                "fuente": "sistema_cierre",
                "completitud": len([k for k, v in datos_sistema.items() if v]),
                "estados_disponibles": [k for k, v in datos_sistema.items() if v and k in ['esf', 'esr', 'eri', 'ecp']]
            },
            "raw_json": datos_sistema  # JSON completo para mostrar en sidebar
        }
    
    # 2. Fallback: Intentar cargar desde carpeta de pruebas
    esf_redis = cargar_esf_desde_redis(cliente_id, periodo, test_type)
    
    if esf_redis:
        logger.info(f"✅ Usando datos de pruebas Redis para cliente {cliente_id}, período {periodo}")
        
        # Construir estructura compatible con Streamlit
        return {
            "fuente": "redis_pruebas",
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
            "esf": esf_redis,
            "estado_financiero": esf_redis,  # Backward compatibility
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
