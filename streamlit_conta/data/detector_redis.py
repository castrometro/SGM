import redis
import json
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def conectar_redis():
    """Conectar a Redis DB 1 (contabilidad)"""
    try:
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=1,
            password='Redis_Password_2025!',
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        if redis_client.ping():
            return redis_client
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error conectando a Redis: {e}")
        return None

def detectar_clientes_y_periodos() -> Dict:
    """
    Detectar automáticamente todos los clientes y períodos disponibles en Redis
    
    Returns:
        Dict con estructura: {
            'clientes': {
                cliente_id: {
                    'nombre': 'Nombre del cliente',
                    'periodos': ['2025-08', '2025-07', ...],
                    'datos_disponibles': ['esf', 'kpis', ...]
                }
            }
        }
    """
    redis_client = conectar_redis()
    if not redis_client:
        return {'error': 'No se pudo conectar a Redis', 'clientes': {}}
    
    try:
        # Buscar específicamente las claves de ESF de finalizacion_automatica
        pattern = "sgm:contabilidad:*:*:pruebas:esf:finalizacion_automatica"
        keys = redis_client.keys(pattern)
        
        clientes_data = {}
        
        for key in keys:
            parts = key.split(':')
            
            # Validar estructura: sgm:contabilidad:clienteid:periodo:pruebas:esf:finalizacion_automatica
            if len(parts) != 7:
                continue
            
            try:
                cliente_id = int(parts[2])
                periodo = parts[3]
                
                # Solo considerar períodos válidos (formato YYYY-MM)
                if len(periodo) == 7 and periodo[4] == '-':
                    # Inicializar cliente si no existe
                    if cliente_id not in clientes_data:
                        clientes_data[cliente_id] = {
                            'nombre': f'Cliente {cliente_id}',
                            'periodos': set(),
                            'datos_disponibles': set()
                        }
                    
                    clientes_data[cliente_id]['periodos'].add(periodo)
                    clientes_data[cliente_id]['datos_disponibles'].add('esf')
                    
                    # Intentar obtener el nombre real del cliente desde ESF
                    try:
                        esf_data = redis_client.get(key)
                        if esf_data:
                            esf_json = json.loads(esf_data)
                            
                            # Buscar nombre del cliente en los metadatos
                            cliente_nombre = None
                            if 'metadata' in esf_json:
                                cliente_nombre = esf_json['metadata'].get('cliente_nombre')
                            
                            if cliente_nombre:
                                clientes_data[cliente_id]['nombre'] = cliente_nombre
                                        
                    except Exception as e:
                        logger.debug(f"No se pudo extraer nombre del cliente de {key}: {e}")
                                
            except (ValueError, IndexError):
                continue
        
        # Convertir sets a listas ordenadas
        for cliente_id in clientes_data:
            clientes_data[cliente_id]['periodos'] = sorted(list(clientes_data[cliente_id]['periodos']), reverse=True)
            clientes_data[cliente_id]['datos_disponibles'] = sorted(list(clientes_data[cliente_id]['datos_disponibles']))
        
        return {
            'clientes': clientes_data,
            'total_clientes': len(clientes_data),
            'detalle': f"Encontrados {len(clientes_data)} clientes con datos en Redis"
        }
        
    except Exception as e:
        logger.error(f"Error detectando clientes y períodos: {e}")
        return {'error': str(e), 'clientes': {}}

def cargar_datos_cliente_periodo(cliente_id: int, periodo: str) -> Optional[Dict]:
    """
    Cargar todos los datos disponibles para un cliente y período específico
    
    Args:
        cliente_id: ID del cliente
        periodo: Período en formato YYYY-MM
        
    Returns:
        Dict con todos los datos disponibles o None si no se encuentra
    """
    redis_client = conectar_redis()
    if not redis_client:
        return None
    
    try:
        datos_completos = {
            'cliente_id': cliente_id,
            'periodo': periodo,
            'datos_encontrados': []
        }
        
        # Cargar ESF desde la clave específica de finalizacion_automatica
        key_esf = f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:esf:finalizacion_automatica"
        esf_data = redis_client.get(key_esf)
        
        if esf_data:
            try:
                esf_json = json.loads(esf_data)
                datos_completos['esf'] = esf_json
                datos_completos['datos_encontrados'].append('esf')
                
                # Extraer información del cliente desde metadata
                if 'metadata' in esf_json:
                    metadata = esf_json['metadata']
                    if 'cliente_nombre' in metadata:
                        datos_completos['cliente_nombre'] = metadata['cliente_nombre']
                    
                    # Información general del ESF
                    datos_completos['info_esf'] = {
                        'total_activos': esf_json.get('activos', {}).get('total_activos') or esf_json.get('total_activos'),
                        'total_pasivos': esf_json.get('pasivos', {}).get('total_pasivos') or esf_json.get('totales', {}).get('total_pasivos'),
                        'total_patrimonio': esf_json.get('patrimonio', {}).get('total_patrimonio') or esf_json.get('totales', {}).get('patrimonio'),
                        'fecha_generacion': metadata.get('fecha_generacion'),
                        'cierre_id': metadata.get('cierre_id'),
                        'moneda': metadata.get('moneda', 'CLP')
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"Error decodificando JSON ESF para {key_esf}: {e}")
        
        # Intentar cargar otros tipos de datos si existen
        otros_tipos = ['kpis', 'esr', 'eri', 'ecp']
        for tipo_dato in otros_tipos:
            key = f"sgm:contabilidad:{cliente_id}:{periodo}:{tipo_dato}"
            data_raw = redis_client.get(key)
            
            if data_raw:
                try:
                    data_json = json.loads(data_raw)
                    datos_completos[tipo_dato] = data_json
                    datos_completos['datos_encontrados'].append(tipo_dato)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando JSON para {key}: {e}")
                    continue
        
        return datos_completos if datos_completos['datos_encontrados'] else None
        
    except Exception as e:
        logger.error(f"Error cargando datos para cliente {cliente_id}, período {periodo}: {e}")
        return None

def obtener_resumen_redis() -> Dict:
    """
    Obtener un resumen completo de todos los datos disponibles en Redis
    """
    clientes_info = detectar_clientes_y_periodos()
    
    if 'error' in clientes_info:
        return clientes_info
    
    resumen = {
        'total_clientes': len(clientes_info['clientes']),
        'clientes_detalle': [],
        'periodos_unicos': set(),
        'tipos_datos_disponibles': set()
    }
    
    for cliente_id, cliente_data in clientes_info['clientes'].items():
        cliente_resumen = {
            'id': cliente_id,
            'nombre': cliente_data['nombre'],
            'total_periodos': len(cliente_data['periodos']),
            'periodos': cliente_data['periodos'],
            'datos_disponibles': cliente_data['datos_disponibles']
        }
        
        resumen['clientes_detalle'].append(cliente_resumen)
        resumen['periodos_unicos'].update(cliente_data['periodos'])
        resumen['tipos_datos_disponibles'].update(cliente_data['datos_disponibles'])
    
    # Convertir sets a listas ordenadas
    resumen['periodos_unicos'] = sorted(list(resumen['periodos_unicos']), reverse=True)
    resumen['tipos_datos_disponibles'] = sorted(list(resumen['tipos_datos_disponibles']))
    
    return resumen
