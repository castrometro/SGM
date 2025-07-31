"""
Sistema de cache Redis para SGM - Nómina
========================================

Estructura de cache:
sgm:nomina:{cliente_id}:{periodo}/
├── informes
├── kpis
├── consolidados
├── incidencias
└── estadisticas

Logs de actividad:
sgm:logs:nomina:{timestamp}:{id} -> Logs individuales con claves separadas

Autor: Sistema SGM
Fecha: 31 de julio de 2025
"""

import redis
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Any, Optional, List, Union

# Configurar logging
logger = logging.getLogger(__name__)

class SGMCacheSystemNomina:
    """Sistema de cache Redis para SGM - Nómina"""
    
    def __init__(self):
        """Inicializar conexión a Redis DB 2 (nómina)"""
        try:
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                db=2,  # DB específica para nómina
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            if not self.redis_client.ping():
                raise ConnectionError("No se pudo conectar a Redis DB 2")
                
            logger.info("SGM Cache System Nómina inicializado correctamente en Redis DB 2")
            
        except Exception as e:
            logger.error(f"Error inicializando SGM Cache System Nómina: {e}")
            raise
        
        # Configuración de TTL por defecto
        self.default_ttl = 3600  # 1 hora
        self.long_ttl = 86400    # 24 horas para informes
        self.short_ttl = 300     # 5 minutos para datos temporales
        
    def _get_key(self, cliente_id: int, periodo: str, tipo_dato: str) -> str:
        """
        Generar clave Redis siguiendo el patrón del sistema SGM
        Formato: sgm:nomina:{cliente_id}:{periodo}:{tipo_dato}
        """
        return f"sgm:nomina:{cliente_id}:{periodo}:{tipo_dato}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serializar datos para almacenar en Redis"""
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"Error serializando datos: {e}")
            raise
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserializar datos desde Redis"""
        try:
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error deserializando datos: {e}")
            raise
    
    # ========== INFORMES DE NÓMINA ==========
    def set_informe_nomina(self, cliente_id: int, periodo: str, informe_data: Dict[str, Any], 
                          ttl: int = None) -> bool:
        """
        Guardar informe completo de nómina en Redis
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre (ej: "2025-07")
            informe_data: Datos completos del informe
            ttl: Tiempo de vida en segundos (opcional)
        
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "informe")
        ttl = ttl or self.long_ttl  # Informes con TTL largo (24 horas)
        
        try:
            # Agregar metadata
            informe_with_meta = {
                **informe_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'cached_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'informe_nomina',
                    'version': '1.0'
                }
            }
            
            serialized_data = self._serialize_data(informe_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("informes_cached")
            self._increment_stat("cache_writes")
            
            logger.info(f"Informe de nómina guardado en Redis: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando informe de nómina: {e}")
            return False
    
    def get_informe_nomina(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener informe de nómina del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            Dict con informe o None si no existe en cache
        """
        key = self._get_key(cliente_id, periodo, "informe")
        
        try:
            data = self.redis_client.get(key)
            if data:
                informe = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                logger.debug(f"Informe de nómina obtenido desde Redis: cliente={cliente_id}, periodo={periodo}")
                return informe
            else:
                self._increment_stat("cache_misses")
                logger.debug(f"Informe de nómina no encontrado en Redis: cliente={cliente_id}, periodo={periodo}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo informe de nómina: {e}")
            self._increment_stat("cache_errors")
            return None
    
    # ========== KPIs DE NÓMINA ==========
    def set_kpis_nomina(self, cliente_id: int, periodo: str, kpis: Dict[str, Any], 
                       ttl: int = None) -> bool:
        """
        Guardar KPIs de nómina
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            kpis: KPIs calculados
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "kpis")
        ttl = ttl or self.default_ttl
        
        try:
            kpis_with_meta = {
                **kpis,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'cached_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'kpis_nomina'
                }
            }
            
            serialized_data = self._serialize_data(kpis_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("kpis_cached")
            self._increment_stat("cache_writes")
            
            logger.info(f"KPIs de nómina guardados en Redis: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando KPIs de nómina: {e}")
            return False
    
    def get_kpis_nomina(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener KPIs de nómina del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            Dict con KPIs o None si no existe
        """
        key = self._get_key(cliente_id, periodo, "kpis")
        
        try:
            data = self.redis_client.get(key)
            if data:
                kpis = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                return kpis
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo KPIs de nómina: {e}")
            return None
    
    # ========== DATOS CONSOLIDADOS ==========
    def set_datos_consolidados(self, cliente_id: int, periodo: str, datos: Dict[str, Any],
                              ttl: int = None) -> bool:
        """
        Guardar datos consolidados de nómina
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            datos: Datos consolidados
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "consolidados")
        ttl = ttl or self.default_ttl
        
        try:
            datos_with_meta = {
                **datos,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'cached_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'datos_consolidados'
                }
            }
            
            serialized_data = self._serialize_data(datos_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("consolidados_cached")
            
            logger.info(f"Datos consolidados guardados en Redis: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando datos consolidados: {e}")
            return False
    
    # ========== GESTIÓN DE CACHE ==========
    def invalidate_cliente_periodo(self, cliente_id: int, periodo: str) -> int:
        """
        Invalidar todo el cache de un cliente/periodo específico
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            int: Número de claves eliminadas
        """
        pattern = f"sgm:nomina:{cliente_id}:{periodo}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache invalidado para cliente {cliente_id}, periodo {periodo}: {deleted} claves eliminadas")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidando cache: {e}")
            return 0
    
    def invalidate_cliente_all(self, cliente_id: int) -> int:
        """
        Invalidar todo el cache de un cliente (todos los períodos)
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            int: Número de claves eliminadas
        """
        pattern = f"sgm:nomina:{cliente_id}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache completo invalidado para cliente {cliente_id}: {deleted} claves eliminadas")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidando cache completo: {e}")
            return 0
    
    def get_client_periods(self, cliente_id: int) -> List[str]:
        """
        Obtener lista de períodos en cache para un cliente
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de períodos disponibles en cache
        """
        try:
            pattern = f"sgm:nomina:{cliente_id}:*:informe"
            keys = self.redis_client.keys(pattern)
            
            periods = []
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 4:
                    period = parts[3]
                    if period not in periods:
                        periods.append(period)
            
            return sorted(periods)
            
        except Exception as e:
            logger.error(f"Error obteniendo períodos del cliente: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cache de nómina
        
        Returns:
            Dict con estadísticas del cache
        """
        try:
            stats = {}
            
            # Estadísticas de Redis
            info = self.redis_client.info()
            stats['redis_info'] = {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'db_keys': info.get('db2', {}).get('keys', 0) if 'db2' in info else 0
            }
            
            # Contadores de nómina
            counters = [
                'informes_cached', 'kpis_cached', 'consolidados_cached',
                'cache_hits', 'cache_misses', 'cache_errors', 'cache_writes'
            ]
            
            stats['nomina_counters'] = {}
            for counter in counters:
                value = self.redis_client.get(f"sgm:nomina:stats:{counter}")
                stats['nomina_counters'][counter] = int(value) if value else 0
            
            # Claves por cliente
            pattern = "sgm:nomina:*"
            keys = self.redis_client.keys(pattern)
            stats['total_keys'] = len(keys)
            
            clientes = {}
            for key in keys:
                if not key.startswith('sgm:nomina:stats:'):
                    parts = key.split(':')
                    if len(parts) >= 3:
                        cliente_id = parts[2]
                        if cliente_id not in clientes:
                            clientes[cliente_id] = 0
                        clientes[cliente_id] += 1
            
            stats['keys_by_client'] = clientes
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}
    
    def _increment_stat(self, stat_name: str) -> None:
        """
        Incrementar contador de estadísticas de forma segura
        
        Args:
            stat_name: Nombre de la estadística a incrementar
        """
        try:
            key = f"sgm:nomina:stats:{stat_name}"
            self.redis_client.incr(key)
            # Establecer TTL de 24 horas para estadísticas
            self.redis_client.expire(key, 86400)
        except Exception as e:
            logger.debug(f"Error incrementando estadística {stat_name}: {e}")
    
    def check_connection(self) -> bool:
        """
        Verificar conexión a Redis
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Error verificando conexión Redis: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificación completa de salud del sistema de cache
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            health = {
                'status': 'healthy',
                'redis_connected': self.check_connection(),
                'timestamp': datetime.now().isoformat(),
                'db': 2
            }
            
            if health['redis_connected']:
                info = self.redis_client.info()
                health['redis_version'] = info.get('redis_version', 'unknown')
                health['used_memory'] = info.get('used_memory_human', 'unknown')
                health['uptime'] = info.get('uptime_in_seconds', 0)
            else:
                health['status'] = 'unhealthy'
                health['error'] = 'No se puede conectar a Redis'
            
            return health
            
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Instancia global del sistema de cache de nómina
# Se inicializa de forma lazy para evitar errores en import time
_cache_system_nomina = None

def get_cache_system_nomina() -> SGMCacheSystemNomina:
    """
    Obtener instancia del sistema de cache de nómina (patrón singleton)
    
    Returns:
        SGMCacheSystemNomina: Instancia del sistema de cache
    """
    global _cache_system_nomina
    if _cache_system_nomina is None:
        _cache_system_nomina = SGMCacheSystemNomina()
    return _cache_system_nomina
