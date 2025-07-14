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
    🚀 OPTIMIZACIÓN: Obtener ESF y ERI de Redis en una sola consulta batch
    Simplificado para obtener solo los datos que realmente existen
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        redis_client: Cliente Redis conectado
        
    Returns:
        Dict con ESF y ERI disponibles
    """
    # Solo consultar los datos que realmente necesitamos: ESF y ERI
    claves_consulta = {
        'esf': f"sgm:contabilidad:{cliente_id}:{periodo}:esf",
        'eri': f"sgm:contabilidad:{cliente_id}:{periodo}:eri"
    }
    
    datos_encontrados = {}
    
    try:
        # 🚀 USAR PIPELINE para consulta batch
        pipe = redis_client.pipeline()
        for clave in claves_consulta.values():
            pipe.get(clave)
        
        # Ejecutar las 2 consultas de una vez
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
                
        logger.info(f"🚀 Consulta batch completada: {len(datos_encontrados)}/2 datasets encontrados")
        
    except Exception as e:
        logger.error(f"❌ Error en consulta batch Redis: {e}")
    
    return datos_encontrados


def cargar_esf_desde_redis(cliente_id: int = 2, periodo: str = "2025-08", test_type: str = "finalizacion_automatica") -> Optional[Dict[str, Any]]:
    """
    🚀 SIMPLIFICADO: Cargar solo ESF desde Redis 
    Wrapper para compatibilidad con código existente
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        test_type: Tipo de test (ignorado, mantenido por compatibilidad)
        
    Returns:
        Dict con ESF o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        return None
    
    try:
        # Usar la clave directa simplificada
        key = f"sgm:contabilidad:{cliente_id}:{periodo}:esf"
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
    🚀 SIMPLIFICADO: Listar ESF disponibles en Redis
    Busca directamente en las claves simplificadas
    
    Args:
        cliente_id: ID del cliente
        
    Returns:
        Dict con información de ESF disponibles
    """
    redis_client = conectar_redis()
    if not redis_client:
        return {"error": "No se pudo conectar a Redis", "esf_disponibles": []}
    
    try:
        # Buscar claves ESF directas para el cliente
        pattern = f"sgm:contabilidad:{cliente_id}:*:esf"
        keys = redis_client.keys(pattern)
        
        esf_disponibles = []
        
        if keys:
            # Usar pipeline para obtener metadata eficientemente
            pipe = redis_client.pipeline()
            for key in keys:
                pipe.get(key)
            
            resultados = pipe.execute()
            
            for i, key in enumerate(keys):
                if resultados[i]:
                    try:
                        parts = key.split(':')
                        if len(parts) >= 4:
                            periodo = parts[3]
                            
                            esf_data = json.loads(resultados[i])
                            esf_info = {
                                'cliente_id': cliente_id,
                                'periodo': periodo,
                                'redis_key': key,
                                'size_kb': round(len(resultados[i]) / 1024, 1),
                                'metadata': esf_data.get('metadata', {})
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
    🚀 SIMPLIFICADO: Cargar ESF y ERI desde Redis
    Solo busca los datos que realmente existen
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable
        
    Returns:
        Dict con ESF y ERI o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        return None
    
    try:
        # 🚀 Obtener solo ESF y ERI
        datos_disponibles = obtener_datos_batch_redis(cliente_id, periodo, redis_client)
        
        if not datos_disponibles:
            logger.warning(f"⚠️ No se encontraron datos en Redis")
            return None
        
        # Retornar datos encontrados
        logger.info(f"✅ Datos cargados: {list(datos_disponibles.keys())}")
        return datos_disponibles
            
    except Exception as e:
        logger.error(f"❌ Error cargando datos: {e}")
        return None


def cargar_datos_redis(cliente_id: int = 2, periodo: str = "2025-08", test_type: str = "finalizacion_automatica") -> Dict[str, Any]:
    """
    🚀 SIMPLIFICADO: Cargar ESF y ERI desde Redis
    Enfocado únicamente en los datos que realmente existen
    
    Args:
        cliente_id: ID del cliente
        periodo: Período contable  
        test_type: Tipo de test (mantenido por compatibilidad)
        
    Returns:
        Dict con ESF y ERI desde Redis o datos de ejemplo como fallback
    """
    redis_client = conectar_redis()
    if not redis_client:
        logger.warning(f"⚠️ No se pudo conectar a Redis, usando datos de ejemplo")
        datos_ejemplo = cargar_datos()
        datos_ejemplo["fuente"] = "archivo_ejemplo"
        datos_ejemplo["metadata"] = {"source": "archivo_estatico"}
        return datos_ejemplo
    
    # 🚀 UNA SOLA CONSULTA BATCH para ESF y ERI
    datos_redis = obtener_datos_batch_redis(cliente_id, periodo, redis_client)
    
    if datos_redis:
        logger.info(f"✅ Datos Redis encontrados para cliente {cliente_id}, período {periodo}")
        
        # Construir respuesta para Streamlit
        esf_data = datos_redis.get('esf', {})
        eri_data = datos_redis.get('eri', {})
        
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
            "metadata": {
                "fuente": "redis",
                "datos_disponibles": list(datos_redis.keys()),
                "total_datasets": len(datos_redis)
            },
            "raw_json": datos_redis
        }
    
    # Fallback: datos de ejemplo
    logger.warning(f"⚠️ No se encontraron datos Redis, usando datos de ejemplo")
    datos_ejemplo = cargar_datos()
    datos_ejemplo["fuente"] = "archivo_ejemplo"
    datos_ejemplo["metadata"] = {
        "source": "archivo_estatico",
        "datos_disponibles": ["ejemplo"]
    }
    return datos_ejemplo


def verificar_estado_redis(cliente_id: int = 2, periodo: str = "2025-03") -> Dict[str, Any]:
    """
    Verificar el estado de la conexión Redis y disponibilidad de datos
    
    Returns:
        Dict con el estado de cada componente del sistema
    """
    estado = {
        'redis_conectado': False,
        'cliente_encontrado': False,
        'cierres_disponibles': 0,
        'periodo_seleccionado': False,
        'error_mensaje': None
    }
    
    try:
        # 1. Verificar conexión Redis
        redis_client = conectar_redis()
        if redis_client:
            redis_client.ping()
            estado['redis_conectado'] = True
            logger.info("✅ Redis conectado correctamente")
        
        # 2. Verificar si el cliente tiene datos
        try:
            pattern = f"sgm:contabilidad:{cliente_id}:*:esf"
            claves_cliente = redis_client.keys(pattern)
            
            if claves_cliente:
                estado['cliente_encontrado'] = True
                estado['cierres_disponibles'] = len(claves_cliente)
                logger.info(f"✅ Cliente {cliente_id} encontrado con {len(claves_cliente)} cierres")
                
                # 3. Verificar si el período específico existe
                esf_key = f"sgm:contabilidad:{cliente_id}:{periodo}:esf"
                eri_key = f"sgm:contabilidad:{cliente_id}:{periodo}:eri"
                
                if redis_client.exists(esf_key) and redis_client.exists(eri_key):
                    estado['periodo_seleccionado'] = True
                    logger.info(f"✅ Período {periodo} disponible para cliente {cliente_id}")
                else:
                    logger.warning(f"⚠️ Período {periodo} no encontrado para cliente {cliente_id}")
            else:
                logger.warning(f"⚠️ No se encontraron datos para cliente {cliente_id}")
        
        except Exception as e:
            logger.error(f"❌ Error verificando datos del cliente: {e}")
            estado['error_mensaje'] = f"Error verificando cliente: {str(e)}"
    
    except Exception as e:
        logger.error(f"❌ Error conectando a Redis: {e}")
        estado['error_mensaje'] = f"Error Redis: {str(e)}"
    
    return estado


def obtener_info_redis_completa(cliente_id: int = 2) -> Dict[str, Any]:
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
                
                # Verificar que también existe ERI
                clave_eri = clave.replace(':esf', ':eri')
                if redis_client.exists(clave_eri):
                    periodos.append(periodo)
        
        # Ordenar períodos (más reciente primero)
        periodos_unicos = sorted(list(set(periodos)), reverse=True)
        info['cierres_disponibles'] = periodos_unicos
        
        logger.info(f"✅ Redis info obtenida: {len(periodos_unicos)} cierres para cliente {cliente_id}")
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info Redis: {e}")
        info['error'] = str(e)
        # Fallback con datos de ejemplo
        info['cierres_disponibles'] = ['2025-03', '2025-02', '2025-01']
    
    return info


def verificar_disponibilidad_redis(cliente_id: int, periodo: str) -> Dict[str, bool]:
    """
    Verificar si los datos de un cierre específico están disponibles en Redis
    
    Args:
        cliente_id: ID del cliente
        periodo: Período del cierre (ej: '2025-03')
    
    Returns:
        Dict con disponibilidad de ESF y ERI en Redis
    """
    disponibilidad = {
        'esf_disponible': False,
        'eri_disponible': False,
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
        
        # Dashboard disponible si ambos existen
        disponibilidad['dashboard_disponible'] = (
            disponibilidad['esf_disponible'] and 
            disponibilidad['eri_disponible']
        )
        
        logger.debug(f"📊 Disponibilidad Redis cliente {cliente_id} período {periodo}: "
                    f"ESF={disponibilidad['esf_disponible']}, "
                    f"ERI={disponibilidad['eri_disponible']}")
        
    except Exception as e:
        logger.error(f"❌ Error verificando disponibilidad Redis: {e}")
        disponibilidad['error'] = str(e)
    
    return disponibilidad
