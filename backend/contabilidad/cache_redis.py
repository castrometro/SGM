"""
Sistema de cache Redis para SGM - Contabilidad
==============================================

Estructura de cache:
sgm:contabilidad:{cliente_id}:{periodo}/
├── kpis
├── procesamiento
├── alertas
├── esf (Estado de Situación Financiera)
├── esr (Estado de Resultados)
├── eri (Estado de Resultados Integral)
├── ecp (Estado de Cambios en el Patrimonio)
├── movimientos
├── cuentas
└── pruebas (Datos de prueba y testing)

Logs de actividad:
sgm:logs:{timestamp}:{id} -> Logs individuales con claves separadas
- Ejemplo: sgm:logs:2025-07-17T20:29:59.974025+00:00:123
- Ordenación natural por timestamp para eficiencia
- Políticas de retención automática

Autor: Sistema SGM
Fecha: 8 de julio de 2025
"""

import redis
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Any, Optional, List, Union

# Configurar logging
logger = logging.getLogger(__name__)

class SGMCacheSystem:
    """Sistema de cache Redis para SGM - Contabilidad"""
    
    def __init__(self):
        """Inicializar conexión a Redis DB 1 (contabilidad)"""
        try:
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                db=1,  # DB 1 dedicada para contabilidad
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            if not self.redis_client.ping():
                raise redis.ConnectionError("No se pudo conectar a Redis")
                
            logger.info("SGM Cache System inicializado correctamente en Redis DB 1")
            
        except Exception as e:
            logger.error(f"Error inicializando SGM Cache System: {e}")
            raise
        
        # Configuración de TTL por defecto
        self.default_ttl = 3600  # 1 hora
        self.long_ttl = 14400    # 4 horas para datos estables
        self.short_ttl = 300     # 5 minutos para datos temporales
        
    def _get_key(self, cliente_id: int, periodo: str, tipo_dato: str) -> str:
        """
        Generar clave Redis siguiendo el patrón del sistema SGM
        Formato: sgm:contabilidad:{cliente_id}:{periodo}:{tipo_dato}
        """
        return f"sgm:contabilidad:{cliente_id}:{periodo}:{tipo_dato}"
    
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
    
    # ========== KPIs ==========
    def set_kpis(self, cliente_id: int, periodo: str, kpis: Dict[str, Any], ttl: int = None) -> bool:
        """
        Guardar KPIs del cliente/periodo
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable (ej: "2025-07")
            kpis: Diccionario con KPIs calculados
            ttl: Tiempo de vida en segundos (opcional)
        
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "kpis")
        ttl = ttl or self.default_ttl
        
        try:
            # Agregar metadata
            kpis_with_meta = {
                **kpis,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'kpis'
                }
            }
            
            serialized_data = self._serialize_data(kpis_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("kpis_cached")
            
            logger.info(f"KPIs guardados en cache: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando KPIs: {e}")
            return False
    
    def get_kpis(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener KPIs del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            Dict con KPIs o None si no existe en cache
        """
        key = self._get_key(cliente_id, periodo, "kpis")
        
        try:
            data = self.redis_client.get(key)
            if data:
                kpis = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("kpis_retrieved")
                
                logger.debug(f"KPIs obtenidos del cache: cliente={cliente_id}, periodo={periodo}")
                return kpis
            else:
                self._increment_stat("cache_misses")
                logger.debug(f"KPIs no encontrados en cache: cliente={cliente_id}, periodo={periodo}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo KPIs: {e}")
            self._increment_stat("cache_errors")
            return None
    
    # ========== Estados Financieros ==========
    def set_estado_financiero(self, cliente_id: int, periodo: str, tipo_estado: str, 
                             datos: Dict[str, Any], ttl: int = None) -> bool:
        """
        Guardar estado financiero (ESF, ESR, ERI, ECP)
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            tipo_estado: Tipo de estado ('esf', 'esr', 'eri', 'ecp')
            datos: Datos del estado financiero
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        # Validar tipo de estado
        estados_validos = ['esf', 'esr', 'eri', 'ecp']
        if tipo_estado not in estados_validos:
            raise ValueError(f"Tipo de estado inválido: {tipo_estado}. Válidos: {estados_validos}")
            
        key = self._get_key(cliente_id, periodo, tipo_estado)
        ttl = ttl or self.long_ttl  # Estados financieros con mayor TTL
        
        try:
            # Agregar metadata específica para estados financieros
            datos_with_meta = {
                **datos,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'tipo_estado': tipo_estado,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'estado_financiero'
                }
            }
            
            serialized_data = self._serialize_data(datos_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat(f"{tipo_estado}_cached")
            
            logger.info(f"Estado financiero {tipo_estado.upper()} guardado: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando estado {tipo_estado}: {e}")
            return False
    
    def get_estado_financiero(self, cliente_id: int, periodo: str, tipo_estado: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado financiero del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            tipo_estado: Tipo de estado ('esf', 'esr', 'eri', 'ecp')
            
        Returns:
            Dict con datos del estado o None si no existe
        """
        key = self._get_key(cliente_id, periodo, tipo_estado)
        
        try:
            data = self.redis_client.get(key)
            if data:
                estado = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat(f"{tipo_estado}_retrieved")
                
                logger.debug(f"Estado {tipo_estado.upper()} obtenido del cache: cliente={cliente_id}, periodo={periodo}")
                return estado
            else:
                self._increment_stat("cache_misses")
                logger.debug(f"Estado {tipo_estado.upper()} no encontrado en cache: cliente={cliente_id}, periodo={periodo}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo estado {tipo_estado}: {e}")
            self._increment_stat("cache_errors")
            return None
    
    # ========== Procesamiento ==========
    def set_procesamiento_status(self, cliente_id: int, periodo: str, status: Dict[str, Any]) -> bool:
        """
        Guardar estado de procesamiento (datos temporales)
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            status: Estado del procesamiento
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "procesamiento")
        
        try:
            status_with_meta = {
                **status,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'updated_at': datetime.now().isoformat(),
                    'ttl': self.short_ttl,
                    'tipo': 'procesamiento'
                }
            }
            
            serialized_data = self._serialize_data(status_with_meta)
            # Procesamiento con TTL corto (5 minutos)
            self.redis_client.setex(key, self.short_ttl, serialized_data)
            
            self._increment_stat("procesamiento_updates")
            
            logger.debug(f"Estado de procesamiento actualizado: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando procesamiento: {e}")
            return False
    
    def get_procesamiento_status(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado de procesamiento
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            Dict con estado de procesamiento o None
        """
        key = self._get_key(cliente_id, periodo, "procesamiento")
        
        try:
            data = self.redis_client.get(key)
            if data:
                status = self._deserialize_data(data)
                logger.debug(f"Estado de procesamiento obtenido: cliente={cliente_id}, periodo={periodo}")
                return status
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo procesamiento: {e}")
            return None
    
    # ========== Alertas ==========
    def set_alertas(self, cliente_id: int, periodo: str, alertas: List[Dict[str, Any]]) -> bool:
        """
        Guardar alertas del periodo
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            alertas: Lista de alertas
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "alertas")
        
        try:
            alertas_with_meta = {
                'alertas': alertas,
                'count': len(alertas),
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': self.default_ttl,
                    'tipo': 'alertas'
                }
            }
            
            serialized_data = self._serialize_data(alertas_with_meta)
            self.redis_client.setex(key, self.default_ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("alertas_cached")
            
            logger.info(f"Alertas guardadas en cache: cliente={cliente_id}, periodo={periodo}, count={len(alertas)}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando alertas: {e}")
            return False
    
    def get_alertas(self, cliente_id: int, periodo: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener alertas del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            Lista de alertas o None
        """
        key = self._get_key(cliente_id, periodo, "alertas")
        
        try:
            data = self.redis_client.get(key)
            if data:
                alertas_data = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("alertas_retrieved")
                
                logger.debug(f"Alertas obtenidas del cache: cliente={cliente_id}, periodo={periodo}")
                return alertas_data.get('alertas', [])
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {e}")
            return None
    
    # ========== Movimientos ==========
    def set_movimientos(self, cliente_id: int, periodo: str, movimientos: List[Dict[str, Any]], 
                       ttl: int = None) -> bool:
        """
        Guardar movimientos del periodo
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            movimientos: Lista de movimientos contables
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "movimientos")
        ttl = ttl or self.default_ttl
        
        try:
            movimientos_with_meta = {
                'movimientos': movimientos,
                'count': len(movimientos),
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'movimientos'
                }
            }
            
            serialized_data = self._serialize_data(movimientos_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("movimientos_cached")
            
            logger.info(f"Movimientos guardados en cache: cliente={cliente_id}, periodo={periodo}, count={len(movimientos)}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando movimientos: {e}")
            return False
    
    def get_movimientos(self, cliente_id: int, periodo: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener movimientos del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            Lista de movimientos o None
        """
        key = self._get_key(cliente_id, periodo, "movimientos")
        
        try:
            data = self.redis_client.get(key)
            if data:
                movimientos_data = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("movimientos_retrieved")
                
                logger.debug(f"Movimientos obtenidos del cache: cliente={cliente_id}, periodo={periodo}")
                return movimientos_data.get('movimientos', [])
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo movimientos: {e}")
            return None
    
    # ========== Cuentas ==========
    def set_cuentas(self, cliente_id: int, periodo: str, cuentas: Dict[str, Any], 
                   ttl: int = None) -> bool:
        """
        Guardar catálogo de cuentas
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            cuentas: Diccionario con catálogo de cuentas
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "cuentas")
        ttl = ttl or self.long_ttl  # Cuentas son datos más estables
        
        try:
            cuentas_with_meta = {
                **cuentas,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'cuentas'
                }
            }
            
            serialized_data = self._serialize_data(cuentas_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("cuentas_cached")
            
            logger.info(f"Cuentas guardadas en cache: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando cuentas: {e}")
            return False
    
    def get_cuentas(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener catálogo de cuentas del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            Dict con catálogo de cuentas o None
        """
        key = self._get_key(cliente_id, periodo, "cuentas")
        
        try:
            data = self.redis_client.get(key)
            if data:
                cuentas = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("cuentas_retrieved")
                
                logger.debug(f"Cuentas obtenidas del cache: cliente={cliente_id}, periodo={periodo}")
                return cuentas
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo cuentas: {e}")
            return None
    
    # ========== Logs de Actividad Globales ==========
    def add_log(self, log_data: Dict[str, Any], max_logs: int = 10000) -> bool:
        """
        Agregar un log usando claves individuales sgm:logs:{id}
        
        Args:
            log_data: Datos del log a agregar
            max_logs: Máximo número de logs a mantener (política de retención)
            
        Returns:
            bool: True si se agregó exitosamente
        """
        try:
            # Generar clave única para este log
            log_id = log_data.get('id', 'unknown')
            
            # Formato simplificado: sgm:logs:{id}
            log_key = f"sgm:logs:{log_id}"
            
            # Serializar y guardar el log individual
            serialized_data = self._serialize_data(log_data)
            self.redis_client.set(log_key, serialized_data)
            
            # Aplicar política de retención si es necesario
            self._apply_logs_retention_policy(max_logs)
            
            self._increment_stat("cache_writes")
            self._increment_stat("logs_cached")
            
            logger.debug(f"Log agregado: {log_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando log: {e}")
            return False
    
    def _apply_logs_retention_policy(self, max_logs: int) -> None:
        """
        Aplicar política de retención eliminando logs antiguos si se excede el límite
        
        Args:
            max_logs: Máximo número de logs a mantener
        """
        try:
            # Obtener todas las claves de logs
            log_keys = self.redis_client.keys("sgm:logs:*")
            
            # Si no excedemos el límite, no hacer nada
            if len(log_keys) <= max_logs:
                return
            
            # Para determinar cuáles son los más antiguos, necesitamos revisar el timestamp dentro del log
            # Obtener una muestra de logs para ordenar por timestamp
            logs_with_timestamps = []
            
            for key in log_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        log_data = self._deserialize_data(data)
                        timestamp = log_data.get('timestamp', '1970-01-01T00:00:00.000Z')
                        logs_with_timestamps.append((timestamp, key))
                except Exception:
                    # Si hay error deserializando, considerar este log como candidato para eliminar
                    logs_with_timestamps.append(('1970-01-01T00:00:00.000Z', key))
            
            # Ordenar por timestamp (más antiguos primero)
            logs_with_timestamps.sort(key=lambda x: x[0])
            
            # Calcular cuántos logs eliminar
            logs_to_delete = len(logs_with_timestamps) - max_logs
            old_logs = [key for _, key in logs_with_timestamps[:logs_to_delete]]
            
            # Eliminar logs antiguos
            if old_logs:
                deleted_count = self.redis_client.delete(*old_logs)
                logger.debug(f"Política de retención aplicada: {deleted_count} logs eliminados")
                self._increment_stat("logs_retention_applied")
            
        except Exception as e:
            logger.error(f"Error aplicando política de retención: {e}")
    
    def get_all_logs(self, limit: int = None) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener todos los logs ordenados por timestamp (más recientes primero)
        
        Args:
            limit: Límite de logs a retornar (opcional)
            
        Returns:
            Lista de logs ordenados o None
        """
        try:
            # Obtener todas las claves de logs
            log_keys = self.redis_client.keys("sgm:logs:*")
            
            if not log_keys:
                self._increment_stat("cache_misses")
                return None
            
            # Obtener logs con timestamp para ordenar
            logs_with_timestamps = []
            
            for key in log_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        log_data = self._deserialize_data(data)
                        timestamp = log_data.get('timestamp', '1970-01-01T00:00:00.000Z')
                        logs_with_timestamps.append((timestamp, log_data))
                except Exception as e:
                    logger.warning(f"Error deserializando log {key}: {e}")
                    continue
            
            # Ordenar por timestamp descendente (más recientes primero)
            logs_with_timestamps.sort(key=lambda x: x[0], reverse=True)
            
            # Extraer solo los datos del log
            logs = [log_data for _, log_data in logs_with_timestamps]
            
            # Aplicar límite si se especifica
            if limit:
                logs = logs[:limit]
            
            self._increment_stat("cache_hits")
            self._increment_stat("logs_retrieved")
            
            logger.debug(f"Logs obtenidos: {len(logs)} de {len(log_keys)} claves")
            return logs
                
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return None
    
    def get_logs_filtered(self, cliente_id: int = None, periodo: str = None, 
                         tarjeta: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtener logs filtrados
        
        Args:
            cliente_id: Filtrar por cliente (opcional)
            periodo: Filtrar por período (opcional)
            tarjeta: Filtrar por tipo de tarjeta (opcional)
            limit: Límite de resultados
            
        Returns:
            Lista de logs filtrados
        """
        try:
            # Obtener todas las claves de logs
            log_keys = self.redis_client.keys("sgm:logs:*")
            
            if not log_keys:
                return []
            
            # Obtener logs con timestamp para ordenar
            logs_with_timestamps = []
            
            for key in log_keys:
                try:
                    data = self.redis_client.get(key)
                    if not data:
                        continue
                    
                    log_data = self._deserialize_data(data)
                    timestamp = log_data.get('timestamp', '1970-01-01T00:00:00.000Z')
                    
                    # Aplicar filtros
                    if cliente_id and log_data.get('cliente_id') != cliente_id:
                        continue
                    
                    if periodo and log_data.get('periodo_cierre') != periodo:
                        continue
                    
                    if tarjeta and log_data.get('tarjeta') != tarjeta:
                        continue
                    
                    logs_with_timestamps.append((timestamp, log_data))
                    
                except Exception as e:
                    logger.warning(f"Error procesando log {key}: {e}")
                    continue
            
            # Ordenar por timestamp descendente (más recientes primero)
            logs_with_timestamps.sort(key=lambda x: x[0], reverse=True)
            
            # Extraer solo los datos del log y aplicar límite
            filtered_logs = [log_data for _, log_data in logs_with_timestamps[:limit]]
            
            logger.debug(f"Logs filtrados: {len(filtered_logs)} de {len(log_keys)} claves, filtros: cliente={cliente_id}, periodo={periodo}, tarjeta={tarjeta}")
            return filtered_logs
            
        except Exception as e:
            logger.error(f"Error filtrando logs: {e}")
            return []
    
    def clear_logs(self) -> bool:
        """
        Limpiar todos los logs
        
        Returns:
            bool: True si se limpiaron exitosamente
        """
        try:
            # Obtener todas las claves de logs
            log_keys = self.redis_client.keys("sgm:logs:*")
            
            if log_keys:
                deleted_count = self.redis_client.delete(*log_keys)
                self._increment_stat("logs_cleared")
                
                logger.info(f"Logs limpiados: {deleted_count} claves eliminadas")
                return True
            else:
                logger.info("No hay logs para limpiar")
                return True
            
        except Exception as e:
            logger.error(f"Error limpiando logs: {e}")
            return False
    
    def get_logs_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de los logs usando operaciones eficientes de Redis
        
        Returns:
            Dict con estadísticas de logs
        """
        try:
            # Obtener todas las claves de logs
            log_keys = self.redis_client.keys("sgm:logs:*")
            
            # Estadísticas básicas
            stats = {
                'total_logs': len(log_keys),
                'oldest_log': None,
                'newest_log': None,
                'logs_by_cliente': {},
                'logs_by_tarjeta': {},
                'logs_by_accion': {},
                'logs_by_resultado': {},
                'sample_keys': log_keys[:5] if log_keys else []  # Muestra de claves
            }
            
            if not log_keys:
                return stats
            
            # Ordenar claves para obtener el más antiguo y más nuevo
            log_keys.sort()
            
            # Extraer timestamp del más antiguo y más nuevo
            if log_keys:
                # Para obtener timestamps, necesitamos revisar el contenido de las claves
                # Obtener una muestra pequeña para no afectar performance
                sample_size = min(10, len(log_keys))
                sample_keys = log_keys[:sample_size] + log_keys[-sample_size:] if len(log_keys) > sample_size else log_keys
                
                timestamps = []
                for key in sample_keys:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            log_data = self._deserialize_data(data)
                            timestamps.append(log_data.get('timestamp', '1970-01-01T00:00:00.000Z'))
                    except Exception:
                        continue
                
                if timestamps:
                    timestamps.sort()
                    stats['oldest_log'] = timestamps[0]
                    stats['newest_log'] = timestamps[-1]
            
            # Para estadísticas detalladas, procesar una muestra o todos si son pocos
            sample_size = min(1000, len(log_keys))  # Limitar a 1000 para performance
            sample_keys = log_keys[-sample_size:] if sample_size < len(log_keys) else log_keys
            
            for key in sample_keys:
                try:
                    data = self.redis_client.get(key)
                    if not data:
                        continue
                    
                    log_data = self._deserialize_data(data)
                    
                    # Contadores por categoría
                    cliente_id = log_data.get('cliente_id')
                    if cliente_id:
                        stats['logs_by_cliente'][str(cliente_id)] = stats['logs_by_cliente'].get(str(cliente_id), 0) + 1
                    
                    tarjeta = log_data.get('tarjeta')
                    if tarjeta:
                        stats['logs_by_tarjeta'][tarjeta] = stats['logs_by_tarjeta'].get(tarjeta, 0) + 1
                    
                    accion = log_data.get('accion')
                    if accion:
                        stats['logs_by_accion'][accion] = stats['logs_by_accion'].get(accion, 0) + 1
                    
                    resultado = log_data.get('resultado', 'exito')
                    stats['logs_by_resultado'][resultado] = stats['logs_by_resultado'].get(resultado, 0) + 1
                    
                except Exception as e:
                    logger.warning(f"Error procesando estadísticas de log {key}: {e}")
                    continue
            
            # Indicar si es una muestra
            if sample_size < len(log_keys):
                stats['_note'] = f"Estadísticas basadas en muestra de {sample_size} logs de {len(log_keys)} totales"
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de logs: {e}")
            return {'error': str(e)}
    
    def get_logs_count(self) -> int:
        """
        Obtener el número total de logs de forma eficiente
        
        Returns:
            int: Número total de logs
        """
        try:
            log_keys = self.redis_client.keys("sgm:logs:*")
            return len(log_keys)
        except Exception as e:
            logger.error(f"Error contando logs: {e}")
            return 0

    # ========== Pruebas y Testing ==========
    def set_prueba_esf(self, cliente_id: int, periodo: str, esf_data: Dict[str, Any], 
                       test_type: str = "current_system", ttl: int = None) -> bool:
        """
        Guardar ESF de prueba generado por el sistema actual
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            esf_data: Datos del ESF generado por el sistema
            test_type: Tipo de prueba ("current_system", "manual", "testing")
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        # Usar subclave para organizar diferentes tipos de pruebas
        key = self._get_key(cliente_id, periodo, f"pruebas:esf:{test_type}")
        ttl = ttl or self.default_ttl
        
        try:
            # Agregar metadata específica para pruebas
            prueba_data = {
                **esf_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'test_type': test_type,
                    'source': 'sistema_actual',
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'prueba_esf'
                }
            }
            
            serialized_data = self._serialize_data(prueba_data)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("pruebas_cached")
            self._increment_stat("pruebas_esf_cached")
            
            logger.info(f"ESF de prueba guardado: cliente={cliente_id}, periodo={periodo}, tipo={test_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando ESF de prueba: {e}")
            return False
    
    def get_prueba_esf(self, cliente_id: int, periodo: str, test_type: str = "current_system") -> Optional[Dict[str, Any]]:
        """
        Obtener ESF de prueba del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            test_type: Tipo de prueba
            
        Returns:
            Dict con ESF de prueba o None
        """
        key = self._get_key(cliente_id, periodo, f"pruebas:esf:{test_type}")
        
        try:
            data = self.redis_client.get(key)
            if data:
                esf_prueba = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("pruebas_retrieved")
                self._increment_stat("pruebas_esf_retrieved")
                
                logger.debug(f"ESF de prueba obtenido: cliente={cliente_id}, periodo={periodo}, tipo={test_type}")
                return esf_prueba
            else:
                self._increment_stat("cache_misses")
                logger.debug(f"ESF de prueba no encontrado: cliente={cliente_id}, periodo={periodo}, tipo={test_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo ESF de prueba: {e}")
            self._increment_stat("cache_errors")
            return None
    
    def set_prueba_data(self, cliente_id: int, periodo: str, data_type: str, 
                       datos: Dict[str, Any], test_type: str = "general", ttl: int = None) -> bool:
        """
        Guardar datos de prueba genéricos (no solo ESF)
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            data_type: Tipo de datos ("esf", "eri", "kpis", "movimientos", etc.)
            datos: Datos a guardar
            test_type: Tipo de prueba
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, f"pruebas:{data_type}:{test_type}")
        ttl = ttl or self.default_ttl
        
        try:
            prueba_data = {
                **datos,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'data_type': data_type,
                    'test_type': test_type,
                    'source': 'sistema_pruebas',
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'prueba_data'
                }
            }
            
            serialized_data = self._serialize_data(prueba_data)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("pruebas_cached")
            self._increment_stat(f"pruebas_{data_type}_cached")
            
            logger.info(f"Datos de prueba guardados: cliente={cliente_id}, periodo={periodo}, tipo={data_type}, test={test_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando datos de prueba {data_type}: {e}")
            return False
    
    def get_prueba_data(self, cliente_id: int, periodo: str, data_type: str, 
                       test_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Obtener datos de prueba genéricos del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            data_type: Tipo de datos
            test_type: Tipo de prueba
            
        Returns:
            Dict con datos de prueba o None
        """
        key = self._get_key(cliente_id, periodo, f"pruebas:{data_type}:{test_type}")
        
        try:
            data = self.redis_client.get(key)
            if data:
                prueba_data = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("pruebas_retrieved")
                self._increment_stat(f"pruebas_{data_type}_retrieved")
                
                logger.debug(f"Datos de prueba obtenidos: cliente={cliente_id}, periodo={periodo}, tipo={data_type}, test={test_type}")
                return prueba_data
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo datos de prueba {data_type}: {e}")
            self._increment_stat("cache_errors")
            return None
    
    def list_pruebas_cliente(self, cliente_id: int, periodo: str = None) -> List[Dict[str, str]]:
        """
        Listar todas las pruebas disponibles para un cliente
        
        Args:
            cliente_id: ID del cliente
            periodo: Período específico (opcional)
            
        Returns:
            Lista de pruebas disponibles con metadata
        """
        try:
            if periodo:
                pattern = f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:*"
            else:
                pattern = f"sgm:contabilidad:{cliente_id}:*:pruebas:*"
            
            keys = self.redis_client.keys(pattern)
            pruebas = []
            
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 6:  # sgm:contabilidad:cliente:periodo:pruebas:tipo:subtipo
                    prueba_info = {
                        'cliente_id': parts[2],
                        'periodo': parts[3],
                        'data_type': parts[5],
                        'test_type': parts[6] if len(parts) > 6 else 'general',
                        'redis_key': key
                    }
                    pruebas.append(prueba_info)
            
            logger.debug(f"Pruebas listadas para cliente {cliente_id}: {len(pruebas)} encontradas")
            return pruebas
            
        except Exception as e:
            logger.error(f"Error listando pruebas del cliente {cliente_id}: {e}")
            return []
    
    def invalidate_pruebas_cliente(self, cliente_id: int, periodo: str = None) -> int:
        """
        Invalidar todas las pruebas de un cliente (o período específico)
        
        Args:
            cliente_id: ID del cliente
            periodo: Período específico (opcional)
            
        Returns:
            int: Número de claves eliminadas
        """
        try:
            if periodo:
                pattern = f"sgm:contabilidad:{cliente_id}:{periodo}:pruebas:*"
            else:
                pattern = f"sgm:contabilidad:{cliente_id}:*:pruebas:*"
            
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self._increment_stat("cache_invalidations")
                self._increment_stat("pruebas_invalidated")
                
                logger.info(f"Pruebas invalidadas: cliente={cliente_id}, periodo={periodo or 'todos'}, claves_eliminadas={deleted_count}")
                return deleted_count
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidando pruebas: {e}")
            return 0

    # ========== Utilidades y Gestión ==========
    def invalidate_cliente_periodo(self, cliente_id: int, periodo: str) -> int:
        """
        Invalidar todo el cache de un cliente/periodo específico
        
        Args:
            cliente_id: ID del cliente
            periodo: Período contable
            
        Returns:
            int: Número de claves eliminadas
        """
        pattern = f"sgm:contabilidad:{cliente_id}:{periodo}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self._increment_stat("cache_invalidations")
                
                logger.info(f"Cache invalidado: cliente={cliente_id}, periodo={periodo}, claves_eliminadas={deleted_count}")
                return deleted_count
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
        pattern = f"sgm:contabilidad:{cliente_id}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self._increment_stat("cache_invalidations")
                
                logger.info(f"Cache completo invalidado: cliente={cliente_id}, claves_eliminadas={deleted_count}")
                return deleted_count
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidando cache completo: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas del cache
        
        Returns:
            Dict con estadísticas del cache
        """
        try:
            # Estadísticas básicas
            basic_stats = {
                'cache_hits': int(self.redis_client.get('sgm:stats:cache_hits') or 0),
                'cache_misses': int(self.redis_client.get('sgm:stats:cache_misses') or 0),
                'cache_writes': int(self.redis_client.get('sgm:stats:cache_writes') or 0),
                'cache_errors': int(self.redis_client.get('sgm:stats:cache_errors') or 0),
                'cache_invalidations': int(self.redis_client.get('sgm:stats:cache_invalidations') or 0),
            }
            
            # Estadísticas específicas por tipo
            specific_stats = {
                'kpis_cached': int(self.redis_client.get('sgm:stats:kpis_cached') or 0),
                'kpis_retrieved': int(self.redis_client.get('sgm:stats:kpis_retrieved') or 0),
                'esf_cached': int(self.redis_client.get('sgm:stats:esf_cached') or 0),
                'esf_retrieved': int(self.redis_client.get('sgm:stats:esf_retrieved') or 0),
                'movimientos_cached': int(self.redis_client.get('sgm:stats:movimientos_cached') or 0),
                'movimientos_retrieved': int(self.redis_client.get('sgm:stats:movimientos_retrieved') or 0),
                'procesamiento_updates': int(self.redis_client.get('sgm:stats:procesamiento_updates') or 0),
                'pruebas_cached': int(self.redis_client.get('sgm:stats:pruebas_cached') or 0),
                'pruebas_retrieved': int(self.redis_client.get('sgm:stats:pruebas_retrieved') or 0),
                'pruebas_esf_cached': int(self.redis_client.get('sgm:stats:pruebas_esf_cached') or 0),
                'pruebas_esf_retrieved': int(self.redis_client.get('sgm:stats:pruebas_esf_retrieved') or 0),
            }
            
            # Contadores de claves por tipo
            contabilidad_keys = self.redis_client.keys('sgm:contabilidad:*')
            key_counts = {
                'total_keys': len(contabilidad_keys),
                'kpis_keys': len([k for k in contabilidad_keys if ':kpis' in k]),
                'esf_keys': len([k for k in contabilidad_keys if ':esf' in k]),
                'movimientos_keys': len([k for k in contabilidad_keys if ':movimientos' in k]),
                'cuentas_keys': len([k for k in contabilidad_keys if ':cuentas' in k]),
                'procesamiento_keys': len([k for k in contabilidad_keys if ':procesamiento' in k]),
                'pruebas_keys': len([k for k in contabilidad_keys if ':pruebas:' in k]),
                'pruebas_esf_keys': len([k for k in contabilidad_keys if ':pruebas:esf:' in k]),
            }
            
            # Cálculos derivados
            total_requests = basic_stats['cache_hits'] + basic_stats['cache_misses']
            hit_rate = round((basic_stats['cache_hits'] / total_requests * 100), 2) if total_requests > 0 else 0
            
            # Información del sistema Redis
            redis_info = self.redis_client.info('memory')
            memory_stats = {
                'used_memory_human': redis_info.get('used_memory_human', 'N/A'),
                'used_memory_peak_human': redis_info.get('used_memory_peak_human', 'N/A'),
                'connected_clients': self.redis_client.info('clients').get('connected_clients', 0),
            }
            
            return {
                **basic_stats,
                **specific_stats,
                **key_counts,
                **memory_stats,
                'hit_rate_percent': hit_rate,
                'last_updated': datetime.now().isoformat(),
                'db_index': 1,
                'cache_system_version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}
    
    def get_client_periods(self, cliente_id: int) -> List[str]:
        """
        Obtener lista de períodos en cache para un cliente
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de períodos disponibles en cache
        """
        try:
            pattern = f"sgm:contabilidad:{cliente_id}:*"
            keys = self.redis_client.keys(pattern)
            
            # Extraer períodos únicos
            periods = set()
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 4:
                    period = parts[3]  # sgm:contabilidad:{cliente_id}:{periodo}:{tipo}
                    periods.add(period)
            
            return sorted(list(periods))
            
        except Exception as e:
            logger.error(f"Error obteniendo períodos del cliente {cliente_id}: {e}")
            return []
    
    def _increment_stat(self, stat_name: str) -> None:
        """
        Incrementar contador de estadísticas de forma segura
        
        Args:
            stat_name: Nombre de la estadística a incrementar
        """
        try:
            self.redis_client.incr(f"sgm:stats:{stat_name}")
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
            start_time = datetime.now()
            
            # Test básico de conexión
            ping_success = self.redis_client.ping()
            
            # Test de escritura/lectura
            test_key = "sgm:health_check:test"
            test_value = {"timestamp": start_time.isoformat(), "test": True}
            
            write_success = self.redis_client.setex(test_key, 60, json.dumps(test_value))
            read_data = self.redis_client.get(test_key)
            read_success = read_data is not None
            
            # Limpiar test
            self.redis_client.delete(test_key)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy' if (ping_success and write_success and read_success) else 'unhealthy',
                'ping': ping_success,
                'write': write_success,
                'read': read_success,
                'response_time_ms': round(response_time, 2),
                'db_index': 1,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # ========== Retención de Cierres con TTL ==========
    def set_estado_financiero_with_retention(self, cliente_id: int, periodo: str, 
                                       datos_esf: Dict[str, Any], datos_eri: Dict[str, Any],
                                       max_cierres_por_cliente: int = 2, 
                                       ttl_hours: int = 24*30) -> Dict[str, Any]:
        """
        Guardar ESF y ERI con retención automática de solo los N cierres más recientes por cliente.
        
        Funcionalidad:
        1. Guarda ESF y ERI para el período especificado con TTL
        2. Mantiene solo los max_cierres_por_cliente más recientes por cliente en Redis
        3. Elimina automáticamente cierres antiguos cuando se excede el límite
        4. Los datos eliminados de Redis permanecen en la base de datos
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre (formato YYYY-MM)
            datos_esf: Datos del Estado de Situación Financiera
            datos_eri: Datos del Estado de Resultados Integral
            max_cierres_por_cliente: Máximo de cierres a mantener en Redis por cliente (default: 2)
            ttl_hours: Tiempo de vida en horas para cada cierre (default: 30 días)
            
        Returns:
            Dict con información del resultado de la operación
        """
        try:
            ttl_seconds = ttl_hours * 3600
            resultado = {
                'success': True,
                'cliente_id': cliente_id,
                'periodo': periodo,
                'cierres_eliminados': [],
                'cierres_mantenidos': [],
                'error': None
            }
            
            logger.info(f"🔄 Iniciando retención de cierres para cliente {cliente_id}, período {periodo}")
            
            # 1. PRIMERO guardar el nuevo cierre (ESF y ERI)
            logger.info(f"💾 Guardando nuevo cierre: cliente {cliente_id}, período {periodo}")
            
            # Guardar ESF con TTL
            esf_guardado = self.set_estado_financiero(
                cliente_id=cliente_id,
                periodo=periodo,
                tipo_estado='esf',
                datos=datos_esf,
                ttl=ttl_seconds
            )
            
            # Guardar ERI con TTL
            eri_guardado = self.set_estado_financiero(
                cliente_id=cliente_id,
                periodo=periodo,
                tipo_estado='eri',
                datos=datos_eri,
                ttl=ttl_seconds
            )
            
            if not (esf_guardado and eri_guardado):
                resultado['success'] = False
                resultado['error'] = 'Error guardando ESF o ERI'
                return resultado
            
            # 2. LUEGO obtener todos los períodos COMPLETOS (que tengan ESF Y ERI)
            periodos_completos = self._obtener_periodos_completos(cliente_id)
            
            logger.info(f"📊 Períodos completos encontrados: {periodos_completos}")
            logger.info(f"📊 Total de períodos completos: {len(periodos_completos)}")
            logger.info(f"📊 Límite máximo configurado: {max_cierres_por_cliente}")
            
            # 3. Solo aplicar retención si tenemos MÁS períodos que el límite
            if len(periodos_completos) > max_cierres_por_cliente:
                logger.info(f"🔄 Aplicando retención: {len(periodos_completos)} períodos > límite de {max_cierres_por_cliente}")
                
                # Ordenar períodos (más antiguos primero)
                periodos_ordenados = sorted(periodos_completos)
                
                # Identificar períodos a eliminar (los más antiguos)
                periodos_a_eliminar = periodos_ordenados[:len(periodos_ordenados) - max_cierres_por_cliente]
                periodos_a_mantener = periodos_ordenados[-max_cierres_por_cliente:]
                
                # 4. Eliminar períodos antiguos de Redis
                for periodo_viejo in periodos_a_eliminar:
                    try:
                        # Eliminar TODO el período (ESF, ERI, KPIs, etc.)
                        eliminados = self.invalidate_cliente_periodo(cliente_id, periodo_viejo)
                        
                        resultado['cierres_eliminados'].append({
                            'periodo': periodo_viejo,
                            'claves_eliminadas': eliminados
                        })
                        
                        logger.info(f"🗑️ Período completo eliminado de Redis: cliente {cliente_id}, período {periodo_viejo} ({eliminados} claves)")
                        
                    except Exception as e:
                        logger.error(f"Error eliminando período {periodo_viejo}: {e}")
                
                # 5. Registrar períodos mantenidos
                for periodo_actual in periodos_a_mantener:
                    resultado['cierres_mantenidos'].append({
                        'periodo': periodo_actual
                    })
                
                # 6. Incrementar estadísticas
                self._increment_stat("retention_operations")
                for _ in range(len(periodos_a_eliminar)):
                    self._increment_stat("cierres_eliminados")
            
            else:
                logger.info(f"✅ No se aplica retención: {len(periodos_completos)} períodos <= límite de {max_cierres_por_cliente}")
                resultado['cierres_mantenidos'] = [{'periodo': p} for p in periodos_completos]
            
            logger.info(f"✅ Retención completada para cliente {cliente_id}:")
            logger.info(f"   📁 Períodos mantenidos: {len(resultado['cierres_mantenidos'])}")
            logger.info(f"   🗑️ Períodos eliminados: {len(resultado['cierres_eliminados'])}")
            logger.info(f"   ⏰ TTL configurado: {ttl_hours} horas")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en retención de cierres para cliente {cliente_id}: {e}")
            return {
                'success': False,
                'cliente_id': cliente_id,
                'periodo': periodo,
                'error': str(e),
                'cierres_eliminados': [],
                'cierres_mantenidos': []
            }

    def _obtener_periodos_completos(self, cliente_id: int) -> List[str]:
        """
        Obtener solo los períodos que tienen TANTO ESF como ERI completos.
        
        Args:
            cliente_id: ID del cliente
            
        Returns:
            Lista de períodos que tienen ambos reportes
        """
        try:
            # Obtener todas las claves ESF y ERI del cliente
            pattern_esf = f"sgm:contabilidad:{cliente_id}:*:esf"
            pattern_eri = f"sgm:contabilidad:{cliente_id}:*:eri"
            
            claves_esf = self.redis_client.keys(pattern_esf)
            claves_eri = self.redis_client.keys(pattern_eri)
            
            # Extraer períodos de las claves
            periodos_esf = set()
            for clave in claves_esf:
                partes = clave.split(':')
                if len(partes) >= 5 and partes[4] == 'esf':  # Verificar que es ESF directo, no de pruebas
                    periodo = partes[3]  # sgm:contabilidad:{cliente_id}:{periodo}:esf
                    periodos_esf.add(periodo)
            
            periodos_eri = set()
            for clave in claves_eri:
                partes = clave.split(':')
                if len(partes) >= 5 and partes[4] == 'eri':  # Verificar que es ERI directo, no de pruebas
                    periodo = partes[3]  # sgm:contabilidad:{cliente_id}:{periodo}:eri
                    periodos_eri.add(periodo)
            
            # Solo devolver períodos que tienen AMBOS reportes
            periodos_completos = periodos_esf.intersection(periodos_eri)
            
            logger.debug(f"Períodos con ESF: {sorted(periodos_esf)}")
            logger.debug(f"Períodos con ERI: {sorted(periodos_eri)}")
            logger.debug(f"Períodos completos (ESF + ERI): {sorted(periodos_completos)}")
            
            return sorted(list(periodos_completos))
            
        except Exception as e:
            logger.error(f"Error obteniendo períodos completos para cliente {cliente_id}: {e}")
            return []

# Instancia global del sistema de cache
# Se inicializa de forma lazy para evitar errores en import time
_cache_system = None

def get_cache_system() -> SGMCacheSystem:
    """
    Obtener instancia del sistema de cache (patrón singleton)
    
    Returns:
        SGMCacheSystem: Instancia del sistema de cache
    """
    global _cache_system
    if _cache_system is None:
        _cache_system = SGMCacheSystem()
    return _cache_system
