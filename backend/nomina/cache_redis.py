"""
Sistema de cache Redis para SGM - Nómina
========================================

ESTRUCTURA ORGANIZADA (DB 2):
sgm:nomina:{cliente_id}:{periodo}:{componente}:{archivo/tipo}

COMPONENTES POR FASES:
├── fase1_headers:analisis          -> Análisis de headers detectados
├── fase1_headers:mapeo_automatico  -> Mapeos automáticos aplicados  
├── fase1_headers:mapeo_manual      -> Mapeos manuales del analista
├── fase1_headers:mapeo_final       -> Mapeo consolidado final
├── fase2_movimientos:talana        -> Movimientos de Talana
├── fase3_analista:archivos         -> Archivos del analista
├── fase4_novedades:mapeo           -> Mapeo headers analista-libro
├── fase5_verificacion:discrepancias -> Resultados de comparación
├── estado:procesamiento            -> Estado actual del cierre
└── archivo:libro_excel             -> Datos temporales del Excel

LOGS DE ACTIVIDAD:
sgm:nomina:logs:{timestamp}:{id} -> Logs de actividad de nómina

Autor: Sistema SGM - Módulo Nómina  
Fecha: 21 de julio de 2025 - Reorganización por fases
"""

import json
import logging
import redis
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Any, Optional, List, Union

# Configurar logging
logger = logging.getLogger(__name__)

class CacheNominaSGM:
    """Sistema de cache Redis para SGM - Nómina (DB 2)"""
    
    def __init__(self):
        """Inicializar conexión a Redis DB 2 (nómina)"""
        try:
            self.redis_client = redis.Redis(
                host='redis',
                port=6379,
                db=2,  # DB 2 dedicada para nómina
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            if not self.redis_client.ping():
                raise redis.ConnectionError("No se pudo conectar a Redis DB 2")
                
            logger.info("🚀 Cache Nómina SGM inicializado correctamente en Redis DB 2")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Cache Nómina SGM: {e}")
            raise
        
        # Configuración de TTL por defecto
        self.default_ttl = 7200   # 2 horas para datos de validación
        self.long_ttl = 21600     # 6 horas para datos consolidados
        self.short_ttl = 600      # 10 minutos para datos temporales
        self.validation_ttl = 3600  # 1 hora para proceso de validación
        
    def _get_key(self, cliente_id: int, cierre_id: int, componente: str, tipo: str) -> str:
        """
        Generar clave Redis siguiendo estructura organizada por fases
        Formato: sgm:nomina:{cliente_id}:{cierre_id}:{componente}:{tipo}
        
        Ejemplos:
        - sgm:nomina:1:123:fase1_headers:analisis
        - sgm:nomina:1:123:fase1_headers:mapeo_final
        - sgm:nomina:1:123:estado:procesamiento
        - sgm:nomina:1:123:archivo:libro_excel
        """
        return f"sgm:nomina:{cliente_id}:{cierre_id}:{componente}:{tipo}"
    
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
    
    # ========== LIBRO DE REMUNERACIONES ==========
    def guardar_libro_remuneraciones(self, cliente_id: int, periodo: str, 
                                    archivo_data: Dict[str, Any], 
                                    libro_id: int = None,
                                    ttl: int = None) -> bool:
        """
        Guardar datos del libro de remuneraciones subido
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina (ej: "2025-07")
            archivo_data: Datos del archivo Excel/CSV procesado
            libro_id: ID del LibroRemuneracionesUpload (opcional)
            ttl: Tiempo de vida en segundos (opcional)
        
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "libro_remuneraciones")
        ttl = ttl or self.default_ttl
        
        try:
            # Agregar metadata
            libro_with_meta = {
                **archivo_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'libro_id': libro_id,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'libro_remuneraciones',
                    'source': 'archivo_subido'
                }
            }
            
            serialized_data = self._serialize_data(libro_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("libro_remuneraciones_cached")
            
            logger.info(f"📚 Libro de remuneraciones guardado: cliente={cliente_id}, periodo={periodo}, empleados={len(archivo_data.get('empleados', []))}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando libro de remuneraciones: {e}")
            return False
    
    def obtener_libro_remuneraciones(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos del libro de remuneraciones del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con datos del libro o None si no existe
        """
        key = self._get_key(cliente_id, periodo, "libro_remuneraciones")
        
        try:
            data = self.redis_client.get(key)
            if data:
                libro = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("libro_remuneraciones_retrieved")
                
                logger.debug(f"📚 Libro obtenido del cache: cliente={cliente_id}, periodo={periodo}")
                return libro
            else:
                self._increment_stat("cache_misses")
                logger.debug(f"📚 Libro no encontrado en cache: cliente={cliente_id}, periodo={periodo}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo libro de remuneraciones: {e}")
            self._increment_stat("cache_errors")
            return None
    
    # ========== EMPLEADOS TALANA ==========
    def guardar_empleados_talana(self, cliente_id: int, periodo: str, 
                               empleados_data: List[Dict[str, Any]], 
                               ttl: int = None) -> bool:
        """
        Guardar datos de empleados extraídos de Talana API
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            empleados_data: Lista de empleados con sus datos de Talana
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "empleados_talana")
        ttl = ttl or self.default_ttl
        
        try:
            talana_with_meta = {
                'empleados': empleados_data,
                'count': len(empleados_data),
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'empleados_talana',
                    'source': 'talana_api'
                }
            }
            
            serialized_data = self._serialize_data(talana_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("empleados_talana_cached")
            
            logger.info(f"👥 Empleados Talana guardados: cliente={cliente_id}, periodo={periodo}, count={len(empleados_data)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando empleados Talana: {e}")
            return False
    
    def obtener_empleados_talana(self, cliente_id: int, periodo: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener empleados de Talana del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Lista de empleados Talana o None
        """
        key = self._get_key(cliente_id, periodo, "empleados_talana")
        
        try:
            data = self.redis_client.get(key)
            if data:
                talana_data = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("empleados_talana_retrieved")
                
                logger.debug(f"👥 Empleados Talana obtenidos: cliente={cliente_id}, periodo={periodo}")
                return talana_data.get('empleados', [])
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo empleados Talana: {e}")
            return None
    
    # ========== EMPLEADOS ANALISTA ==========
    def guardar_empleados_analista(self, cliente_id: int, periodo: str, 
                                 empleados_data: List[Dict[str, Any]], 
                                 analista_id: int = None,
                                 ttl: int = None) -> bool:
        """
        Guardar datos de empleados ingresados por el analista
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            empleados_data: Lista de empleados con datos del analista
            analista_id: ID del usuario analista (opcional)
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "empleados_analista")
        ttl = ttl or self.default_ttl
        
        try:
            analista_with_meta = {
                'empleados': empleados_data,
                'count': len(empleados_data),
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'analista_id': analista_id,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'empleados_analista',
                    'source': 'analista_input'
                }
            }
            
            serialized_data = self._serialize_data(analista_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("empleados_analista_cached")
            
            logger.info(f"📝 Empleados Analista guardados: cliente={cliente_id}, periodo={periodo}, count={len(empleados_data)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando empleados Analista: {e}")
            return False
    
    def obtener_empleados_analista(self, cliente_id: int, periodo: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtener empleados del analista del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Lista de empleados del analista o None
        """
        key = self._get_key(cliente_id, periodo, "empleados_analista")
        
        try:
            data = self.redis_client.get(key)
            if data:
                analista_data = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("empleados_analista_retrieved")
                
                logger.debug(f"📝 Empleados Analista obtenidos: cliente={cliente_id}, periodo={periodo}")
                return analista_data.get('empleados', [])
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo empleados Analista: {e}")
            return None
    
    # ========== DISCREPANCIAS ==========
    def detectar_y_guardar_discrepancias(self, cliente_id: int, periodo: str) -> Dict[str, Any]:
        """
        Detectar discrepancias entre Talana y Analista y guardar resultados
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con resultado de la detección de discrepancias
        """
        try:
            # Obtener datos de ambas fuentes
            empleados_talana = self.obtener_empleados_talana(cliente_id, periodo)
            empleados_analista = self.obtener_empleados_analista(cliente_id, periodo)
            
            if not empleados_talana or not empleados_analista:
                return {
                    'success': False,
                    'error': 'Faltan datos de Talana o Analista para comparar',
                    'discrepancias_count': 0,
                    'discrepancias': []
                }
            
            # Algoritmo de detección de discrepancias
            discrepancias = []
            empleados_analista_dict = {emp.get('rut'): emp for emp in empleados_analista}
            
            for emp_talana in empleados_talana:
                rut = emp_talana.get('rut')
                emp_analista = empleados_analista_dict.get(rut)
                
                if not emp_analista:
                    # Empleado en Talana pero no en analista
                    discrepancias.append({
                        'tipo': 'empleado_faltante_analista',
                        'rut': rut,
                        'empleado_talana': emp_talana,
                        'empleado_analista': None,
                        'descripcion': f"Empleado {rut} existe en Talana pero no en datos del analista"
                    })
                    continue
                
                # Comparar conceptos y valores
                conceptos_talana = emp_talana.get('conceptos', {})
                conceptos_analista = emp_analista.get('conceptos', {})
                
                for codigo_concepto, valor_talana in conceptos_talana.items():
                    valor_analista = conceptos_analista.get(codigo_concepto)
                    
                    if valor_analista is None:
                        discrepancias.append({
                            'tipo': 'concepto_faltante_analista',
                            'rut': rut,
                            'codigo_concepto': codigo_concepto,
                            'valor_talana': valor_talana,
                            'valor_analista': None,
                            'descripcion': f"Concepto {codigo_concepto} falta en datos del analista para {rut}"
                        })
                    elif str(valor_talana) != str(valor_analista):
                        discrepancias.append({
                            'tipo': 'valor_diferente',
                            'rut': rut,
                            'codigo_concepto': codigo_concepto,
                            'valor_talana': valor_talana,
                            'valor_analista': valor_analista,
                            'diferencia': float(valor_analista) - float(valor_talana) if isinstance(valor_talana, (int, float)) and isinstance(valor_analista, (int, float)) else None,
                            'descripcion': f"Valor diferente en concepto {codigo_concepto} para {rut}: Talana={valor_talana}, Analista={valor_analista}"
                        })
            
            # Verificar empleados en analista que no están en Talana
            empleados_talana_dict = {emp.get('rut'): emp for emp in empleados_talana}
            for emp_analista in empleados_analista:
                rut = emp_analista.get('rut')
                if rut not in empleados_talana_dict:
                    discrepancias.append({
                        'tipo': 'empleado_faltante_talana',
                        'rut': rut,
                        'empleado_talana': None,
                        'empleado_analista': emp_analista,
                        'descripcion': f"Empleado {rut} existe en datos del analista pero no en Talana"
                    })
            
            # Guardar discrepancias en Redis
            resultado_discrepancias = {
                'success': True,
                'cliente_id': cliente_id,
                'periodo': periodo,
                'discrepancias_count': len(discrepancias),
                'discrepancias': discrepancias,
                'comparacion_timestamp': datetime.now().isoformat(),
                'total_empleados_talana': len(empleados_talana),
                'total_empleados_analista': len(empleados_analista),
                'status': 'con_discrepancias' if len(discrepancias) > 0 else 'sin_discrepancias'
            }
            
            # Guardar en cache
            self.guardar_discrepancias(cliente_id, periodo, resultado_discrepancias)
            
            logger.info(f"🔍 Discrepancias detectadas: cliente={cliente_id}, periodo={periodo}, count={len(discrepancias)}")
            return resultado_discrepancias
            
        except Exception as e:
            logger.error(f"❌ Error detectando discrepancias: {e}")
            return {
                'success': False,
                'error': str(e),
                'discrepancias_count': 0,
                'discrepancias': []
            }
    
    def guardar_discrepancias(self, cliente_id: int, periodo: str, 
                            discrepancias_data: Dict[str, Any], 
                            ttl: int = None) -> bool:
        """
        Guardar resultado de discrepancias en Redis
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            discrepancias_data: Datos de las discrepancias detectadas
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "discrepancias")
        ttl = ttl or self.validation_ttl
        
        try:
            discrepancias_with_meta = {
                **discrepancias_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'discrepancias'
                }
            }
            
            serialized_data = self._serialize_data(discrepancias_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("discrepancias_cached")
            
            logger.info(f"🔍 Discrepancias guardadas: cliente={cliente_id}, periodo={periodo}, count={discrepancias_data.get('discrepancias_count', 0)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando discrepancias: {e}")
            return False
    
    def obtener_discrepancias(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener discrepancias del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con discrepancias o None
        """
        key = self._get_key(cliente_id, periodo, "discrepancias")
        
        try:
            data = self.redis_client.get(key)
            if data:
                discrepancias = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("discrepancias_retrieved")
                
                logger.debug(f"🔍 Discrepancias obtenidas: cliente={cliente_id}, periodo={periodo}")
                return discrepancias
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo discrepancias: {e}")
            return None
    
    def obtener_discrepancias_para_dashboard(self, cliente_id: int, periodo: str) -> Dict[str, Any]:
        """
        Obtener discrepancias formateadas para mostrar en dashboard
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con datos listos para dashboard
        """
        discrepancias_data = self.obtener_discrepancias(cliente_id, periodo)
        
        if not discrepancias_data:
            return {
                'has_discrepancias': False,
                'total_discrepancias': 0,
                'discrepancias_by_type': {},
                'discrepancias_list': [],
                'status': 'no_data'
            }
        
        # Agrupar discrepancias por tipo para dashboard
        discrepancias_by_type = {}
        for disc in discrepancias_data.get('discrepancias', []):
            tipo = disc.get('tipo', 'desconocido')
            if tipo not in discrepancias_by_type:
                discrepancias_by_type[tipo] = []
            discrepancias_by_type[tipo].append(disc)
        
        return {
            'has_discrepancias': discrepancias_data.get('discrepancias_count', 0) > 0,
            'total_discrepancias': discrepancias_data.get('discrepancias_count', 0),
            'discrepancias_by_type': {tipo: len(items) for tipo, items in discrepancias_by_type.items()},
            'discrepancias_list': discrepancias_data.get('discrepancias', []),
            'comparacion_timestamp': discrepancias_data.get('comparacion_timestamp'),
            'total_empleados_talana': discrepancias_data.get('total_empleados_talana', 0),
            'total_empleados_analista': discrepancias_data.get('total_empleados_analista', 0),
            'status': discrepancias_data.get('status', 'unknown'),
            'cliente_id': cliente_id,
            'periodo': periodo
        }
    
    # ========== ESTADO DE VALIDACIÓN ==========
    def set_validacion_status(self, cliente_id: int, periodo: str, 
                            status_data: Dict[str, Any]) -> bool:
        """
        Guardar estado actual del proceso de validación
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            status_data: Estado del proceso de validación
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "validacion_status")
        
        try:
            status_with_meta = {
                **status_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'updated_at': datetime.now().isoformat(),
                    'ttl': self.short_ttl,
                    'tipo': 'validacion_status'
                }
            }
            
            serialized_data = self._serialize_data(status_with_meta)
            # Estado de validación con TTL corto (10 minutos)
            self.redis_client.setex(key, self.short_ttl, serialized_data)
            
            self._increment_stat("validacion_status_updates")
            
            logger.debug(f"⚡ Estado de validación actualizado: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando estado de validación: {e}")
            return False
    
    def get_validacion_status(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener estado actual de validación
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con estado de validación o None
        """
        key = self._get_key(cliente_id, periodo, "validacion_status")
        
        try:
            data = self.redis_client.get(key)
            if data:
                status = self._deserialize_data(data)
                logger.debug(f"⚡ Estado de validación obtenido: cliente={cliente_id}, periodo={periodo}")
                return status
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de validación: {e}")
            return None
    
    # ========== RESUMEN DE CONCEPTOS ==========
    def guardar_resumen_conceptos(self, cliente_id: int, periodo: str, 
                                resumen_data: Dict[str, Any], 
                                ttl: int = None) -> bool:
        """
        Guardar resumen de conceptos por empleado
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            resumen_data: Resumen agregado de conceptos
            ttl: Tiempo de vida en segundos
            
        Returns:
            bool: True si se guardó exitosamente
        """
        key = self._get_key(cliente_id, periodo, "resumen_conceptos")
        ttl = ttl or self.default_ttl
        
        try:
            resumen_with_meta = {
                **resumen_data,
                '_metadata': {
                    'cliente_id': cliente_id,
                    'periodo': periodo,
                    'created_at': datetime.now().isoformat(),
                    'ttl': ttl,
                    'tipo': 'resumen_conceptos'
                }
            }
            
            serialized_data = self._serialize_data(resumen_with_meta)
            self.redis_client.setex(key, ttl, serialized_data)
            
            self._increment_stat("cache_writes")
            self._increment_stat("resumen_conceptos_cached")
            
            logger.info(f"📊 Resumen de conceptos guardado: cliente={cliente_id}, periodo={periodo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando resumen de conceptos: {e}")
            return False
    
    def obtener_resumen_conceptos(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener resumen de conceptos del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con resumen de conceptos o None
        """
        key = self._get_key(cliente_id, periodo, "resumen_conceptos")
        
        try:
            data = self.redis_client.get(key)
            if data:
                resumen = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("resumen_conceptos_retrieved")
                
                logger.debug(f"📊 Resumen de conceptos obtenido: cliente={cliente_id}, periodo={periodo}")
                return resumen
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de conceptos: {e}")
            return None
    
    # ========== CONSOLIDACIÓN ==========
    def preparar_consolidacion(self, cliente_id: int, periodo: str) -> Dict[str, Any]:
        """
        Preparar datos consolidados listos para guardar en BD
        Solo se ejecuta cuando discrepancias = 0
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con datos consolidados o error
        """
        try:
            # Verificar que no hay discrepancias
            discrepancias_data = self.obtener_discrepancias(cliente_id, periodo)
            if not discrepancias_data or discrepancias_data.get('discrepancias_count', 0) > 0:
                return {
                    'success': False,
                    'error': 'No se puede consolidar: aún hay discrepancias pendientes',
                    'discrepancias_count': discrepancias_data.get('discrepancias_count', 0) if discrepancias_data else 'unknown'
                }
            
            # Obtener datos validados
            empleados_talana = self.obtener_empleados_talana(cliente_id, periodo)
            empleados_analista = self.obtener_empleados_analista(cliente_id, periodo)
            libro_data = self.obtener_libro_remuneraciones(cliente_id, periodo)
            
            if not empleados_talana or not empleados_analista:
                return {
                    'success': False,
                    'error': 'Faltan datos de empleados para consolidar'
                }
            
            # Preparar datos consolidados
            consolidacion = {
                'success': True,
                'cliente_id': cliente_id,
                'periodo': periodo,
                'libro_remuneraciones': libro_data,
                'empleados_consolidados': empleados_analista,  # Los datos del analista son la fuente final
                'empleados_talana_ref': empleados_talana,      # Referencia para auditoría
                'total_empleados': len(empleados_analista),
                'consolidacion_timestamp': datetime.now().isoformat(),
                'validacion_passed': True,
                'discrepancias_count': 0,
                'listo_para_bd': True
            }
            
            # Guardar datos de consolidación
            key = self._get_key(cliente_id, periodo, "consolidacion")
            serialized_data = self._serialize_data(consolidacion)
            # TTL más largo para datos consolidados
            self.redis_client.setex(key, self.long_ttl, serialized_data)
            
            self._increment_stat("consolidaciones_preparadas")
            
            logger.info(f"✅ Consolidación preparada: cliente={cliente_id}, periodo={periodo}, empleados={len(empleados_analista)}")
            return consolidacion
            
        except Exception as e:
            logger.error(f"❌ Error preparando consolidación: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_consolidacion(self, cliente_id: int, periodo: str) -> Optional[Dict[str, Any]]:
        """
        Obtener datos de consolidación del cache
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            Dict con datos de consolidación o None
        """
        key = self._get_key(cliente_id, periodo, "consolidacion")
        
        try:
            data = self.redis_client.get(key)
            if data:
                consolidacion = self._deserialize_data(data)
                self._increment_stat("cache_hits")
                self._increment_stat("consolidaciones_retrieved")
                
                logger.debug(f"✅ Consolidación obtenida: cliente={cliente_id}, periodo={periodo}")
                return consolidacion
            else:
                self._increment_stat("cache_misses")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo consolidación: {e}")
            return None
    
    def limpiar_cache_consolidado(self, cliente_id: int, periodo: str) -> bool:
        """
        Limpiar cache después de que los datos se han guardado exitosamente en BD
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            bool: True si se limpió exitosamente
        """
        try:
            # Claves a limpiar después de consolidación exitosa
            claves_a_limpiar = [
                "libro_remuneraciones",
                "empleados_talana", 
                "empleados_analista",
                "discrepancias",
                "validacion_status",
                "resumen_conceptos",
                "consolidacion"
            ]
            
            keys_to_delete = []
            for tipo in claves_a_limpiar:
                key = self._get_key(cliente_id, periodo, tipo)
                keys_to_delete.append(key)
            
            # Eliminar todas las claves
            if keys_to_delete:
                deleted_count = self.redis_client.delete(*keys_to_delete)
                self._increment_stat("cache_cleanups")
                
                logger.info(f"🧹 Cache limpiado después de consolidación: cliente={cliente_id}, periodo={periodo}, claves_eliminadas={deleted_count}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache consolidado: {e}")
            return False
    
    # ========== MÉTODOS PARA VIEWSET ==========
    
    def obtener_estado_cierre(self, cierre_id: int) -> Dict[str, Any]:
        """
        Obtener el estado actual de un cierre en Redis
        
        Args:
            cierre_id: ID del cierre
            
        Returns:
            Dict con información del estado en cache
        """
        try:
            # Obtener información del cierre desde la BD
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Verificar qué datos existen en Redis
            key_prefix = f"sgm:nomina:{cierre.cliente.id}:{cierre.periodo}"
            
            estado = {
                'cierre_id': cierre_id,
                'cliente_id': cierre.cliente.id,
                'periodo': cierre.periodo,
                'en_cache': False,
                'datos_disponibles': {},
                'ultima_actividad': None
            }
            
            # Verificar cada tipo de dato
            tipos_datos = [
                'libro_remuneraciones',
                'empleados_talana', 
                'empleados_analista',
                'discrepancias',
                'validacion_status',
                'resumen_conceptos',
                'consolidacion'
            ]
            
            for tipo_dato in tipos_datos:
                key = f"{key_prefix}/{tipo_dato}"
                existe = self.redis_client.exists(key)
                if existe:
                    estado['en_cache'] = True
                    ttl = self.redis_client.ttl(key)
                    estado['datos_disponibles'][tipo_dato] = {
                        'existe': True,
                        'ttl': ttl if ttl > 0 else 'sin_expiracion'
                    }
                else:
                    estado['datos_disponibles'][tipo_dato] = {
                        'existe': False
                    }
            
            # Obtener timestamp de última actividad si existe
            status_key = f"{key_prefix}/validacion_status"
            if self.redis_client.exists(status_key):
                status_data = self._deserialize_data(self.redis_client.get(status_key))
                estado['ultima_actividad'] = status_data.get('timestamp')
            
            return estado
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del cierre {cierre_id}: {e}")
            return {
                'cierre_id': cierre_id,
                'error': str(e),
                'en_cache': False
            }
    
    def inicializar_cierre(self, cierre_id: int, forzar: bool = False) -> Dict[str, Any]:
        """
        Inicializar un cierre en Redis
        
        Args:
            cierre_id: ID del cierre
            forzar: Si True, reinicializa aunque ya exista
            
        Returns:
            Dict con resultado de la inicialización
        """
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            key_prefix = f"sgm:nomina:{cierre.cliente.id}:{cierre.periodo}"
            
            # Verificar si ya existe
            status_key = f"{key_prefix}/validacion_status"
            if self.redis_client.exists(status_key) and not forzar:
                return {
                    'success': True,
                    'mensaje': 'Cierre ya estaba inicializado',
                    'ya_existia': True
                }
            
            # Inicializar estado
            status_inicial = {
                'cierre_id': cierre_id,
                'cliente_id': cierre.cliente.id,
                'periodo': cierre.periodo,
                'estado': 'inicializado',
                'timestamp': datetime.now().isoformat(),
                'datos_cargados': {
                    'libro_remuneraciones': False,
                    'empleados_talana': False,
                    'empleados_analista': False
                },
                'consolidacion_realizada': False
            }
            
            self.set_validacion_status(
                cierre.cliente.id,
                cierre.periodo,
                status_inicial['estado'],
                status_inicial
            )
            
            logger.info(f"Cierre {cierre_id} inicializado en Redis correctamente")
            
            return {
                'success': True,
                'mensaje': 'Cierre inicializado exitosamente',
                'datos': status_inicial
            }
            
        except Exception as e:
            logger.error(f"Error inicializando cierre {cierre_id} en Redis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def consolidar_cierre(self, cierre_id: int) -> Dict[str, Any]:
        """
        Consolidar datos del cierre
        
        Args:
            cierre_id: ID del cierre
            
        Returns:
            Dict con resultado de la consolidación
        """
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Por ahora, simular consolidación exitosa
            resultado = self.preparar_consolidacion(cierre.cliente.id, cierre.periodo)
            
            # Actualizar estado
            self.set_validacion_status(
                cierre.cliente.id,
                cierre.periodo,
                'consolidado',
                {
                    'timestamp': datetime.now().isoformat(),
                    'consolidacion_realizada': True,
                    'resultado': resultado
                }
            )
            
            logger.info(f"Cierre {cierre_id} consolidado exitosamente")
            
            return {
                'success': True,
                'mensaje': 'Consolidación completada exitosamente',
                'datos_procesados': resultado.get('total_empleados', 0),
                'discrepancias_detectadas': len(resultado.get('discrepancias', []))
            }
            
        except Exception as e:
            logger.error(f"Error consolidando cierre {cierre_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def actualizar_estado_cierre(self, cierre_id: int, nuevo_estado: str) -> bool:
        """
        Actualizar el estado de un cierre en Redis
        
        Args:
            cierre_id: ID del cierre
            nuevo_estado: Nuevo estado del cierre
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Obtener estado actual
            status_actual = self.get_validacion_status(cierre.cliente.id, cierre.periodo)
            if not status_actual:
                status_actual = {}
            
            # Actualizar estado
            status_actual.update({
                'estado': nuevo_estado,
                'timestamp': datetime.now().isoformat()
            })
            
            self.set_validacion_status(
                cierre.cliente.id,
                cierre.periodo,
                nuevo_estado,
                status_actual
            )
            
            logger.info(f"Estado del cierre {cierre_id} actualizado a: {nuevo_estado}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado del cierre {cierre_id}: {e}")
            return False
    
    def archivar_cierre(self, cierre_id: int) -> bool:
        """
        Archivar un cierre (mover a almacenamiento de largo plazo)
        
        Args:
            cierre_id: ID del cierre
            
        Returns:
            True si se archivó correctamente
        """
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Por ahora solo actualizar el estado
            return self.actualizar_estado_cierre(cierre_id, 'archivado')
            
        except Exception as e:
            logger.error(f"Error archivando cierre {cierre_id}: {e}")
            return False

    # ========== RE-UPLOAD DE ARCHIVOS ==========
    def reemplazar_archivo(self, cliente_id: int, periodo: str, 
                          nuevo_archivo_data: Dict[str, Any], 
                          libro_id: int = None) -> Dict[str, Any]:
        """
        Reemplazar archivo y reiniciar proceso de validación
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            nuevo_archivo_data: Datos del nuevo archivo
            libro_id: ID del nuevo LibroRemuneracionesUpload
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info(f"🔄 Iniciando reemplazo de archivo: cliente={cliente_id}, periodo={periodo}")
            
            # 1. Limpiar datos anteriores
            limpieza_exitosa = self.limpiar_cache_consolidado(cliente_id, periodo)
            
            # 2. Guardar nuevo archivo
            archivo_guardado = self.guardar_libro_remuneraciones(
                cliente_id=cliente_id,
                periodo=periodo,
                archivo_data=nuevo_archivo_data,
                libro_id=libro_id
            )
            
            if not archivo_guardado:
                return {
                    'success': False,
                    'error': 'No se pudo guardar el nuevo archivo'
                }
            
            # 3. Resetear estado de validación
            status_reset = self.set_validacion_status(cliente_id, periodo, {
                'status': 'archivo_subido',
                'step': 'esperando_talana_analista',
                'archivo_reemplazado': True,
                'archivo_timestamp': datetime.now().isoformat(),
                'libro_id': libro_id
            })
            
            self._increment_stat("archivos_reemplazados")
            
            resultado = {
                'success': True,
                'cliente_id': cliente_id,
                'periodo': periodo,
                'libro_id': libro_id,
                'limpieza_exitosa': limpieza_exitosa,
                'archivo_guardado': archivo_guardado,
                'status_reset': status_reset,
                'mensaje': 'Archivo reemplazado exitosamente. El proceso de validación se ha reiniciado.'
            }
            
            logger.info(f"✅ Archivo reemplazado exitosamente: cliente={cliente_id}, periodo={periodo}")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error reemplazando archivo: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== LOGS DE ACTIVIDAD NÓMINA ==========
    def add_nomina_log(self, log_data: Dict[str, Any], max_logs: int = 5000) -> bool:
        """
        Agregar log de actividad específico de nómina
        
        Args:
            log_data: Datos del log a agregar
            max_logs: Máximo número de logs a mantener
            
        Returns:
            bool: True si se agregó exitosamente
        """
        try:
            # Generar clave única para este log
            timestamp = datetime.now().isoformat()
            log_id = log_data.get('id', f"nomina_{int(datetime.now().timestamp())}")
            
            # Formato: sgm:nomina:logs:{id}
            log_key = f"sgm:nomina:logs:{log_id}"
            
            # Agregar timestamp si no existe
            if 'timestamp' not in log_data:
                log_data['timestamp'] = timestamp
            
            # Serializar y guardar el log
            serialized_data = self._serialize_data(log_data)
            self.redis_client.set(log_key, serialized_data)
            
            # Aplicar política de retención
            self._apply_nomina_logs_retention_policy(max_logs)
            
            self._increment_stat("cache_writes")
            self._increment_stat("nomina_logs_cached")
            
            logger.debug(f"📝 Log de nómina agregado: {log_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando log de nómina: {e}")
            return False
    
    def _apply_nomina_logs_retention_policy(self, max_logs: int) -> None:
        """
        Aplicar política de retención para logs de nómina
        
        Args:
            max_logs: Máximo número de logs a mantener
        """
        try:
            # Obtener todas las claves de logs de nómina
            log_keys = self.redis_client.keys("sgm:nomina:logs:*")
            
            # Si no excedemos el límite, no hacer nada
            if len(log_keys) <= max_logs:
                return
            
            # Para determinar cuáles son los más antiguos, revisar timestamp
            logs_with_timestamps = []
            
            for key in log_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        log_data = self._deserialize_data(data)
                        timestamp = log_data.get('timestamp', '1970-01-01T00:00:00.000Z')
                        logs_with_timestamps.append((timestamp, key))
                except Exception:
                    # Si hay error, considerar como candidato para eliminar
                    logs_with_timestamps.append(('1970-01-01T00:00:00.000Z', key))
            
            # Ordenar por timestamp (más antiguos primero)
            logs_with_timestamps.sort(key=lambda x: x[0])
            
            # Calcular cuántos logs eliminar
            logs_to_delete = len(logs_with_timestamps) - max_logs
            old_logs = [key for _, key in logs_with_timestamps[:logs_to_delete]]
            
            # Eliminar logs antiguos
            if old_logs:
                deleted_count = self.redis_client.delete(*old_logs)
                logger.debug(f"🧹 Política de retención aplicada a logs de nómina: {deleted_count} logs eliminados")
                self._increment_stat("nomina_logs_retention_applied")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando política de retención: {e}")
    
    def get_nomina_logs(self, limit: int = None, 
                       cliente_id: int = None, 
                       periodo: str = None) -> List[Dict[str, Any]]:
        """
        Obtener logs de nómina filtrados
        
        Args:
            limit: Límite de logs a retornar
            cliente_id: Filtrar por cliente (opcional)
            periodo: Filtrar por período (opcional)
            
        Returns:
            Lista de logs filtrados
        """
        try:
            # Obtener todas las claves de logs de nómina
            log_keys = self.redis_client.keys("sgm:nomina:logs:*")
            
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
                    
                    if periodo and log_data.get('periodo') != periodo:
                        continue
                    
                    logs_with_timestamps.append((timestamp, log_data))
                    
                except Exception as e:
                    logger.warning(f"Error procesando log {key}: {e}")
                    continue
            
            # Ordenar por timestamp descendente (más recientes primero)
            logs_with_timestamps.sort(key=lambda x: x[0], reverse=True)
            
            # Extraer solo los datos del log y aplicar límite
            filtered_logs = [log_data for _, log_data in logs_with_timestamps]
            
            if limit:
                filtered_logs = filtered_logs[:limit]
            
            logger.debug(f"📝 Logs de nómina obtenidos: {len(filtered_logs)} de {len(log_keys)} claves")
            return filtered_logs
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo logs de nómina: {e}")
            return []
    
    # ========== UTILIDADES Y GESTIÓN ==========
    def invalidate_cliente_periodo(self, cliente_id: int, periodo: str) -> int:
        """
        Invalidar todo el cache de nómina para un cliente/periodo específico
        
        Args:
            cliente_id: ID del cliente
            periodo: Período de nómina
            
        Returns:
            int: Número de claves eliminadas
        """
        pattern = f"sgm:nomina:{cliente_id}:{periodo}:*"
        
        try:
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self._increment_stat("cache_invalidations")
                
                logger.info(f"🧹 Cache de nómina invalidado: cliente={cliente_id}, periodo={periodo}, claves_eliminadas={deleted_count}")
                return deleted_count
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error invalidando cache de nómina: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas del cache de nómina
        
        Returns:
            Dict con estadísticas del cache
        """
        try:
            # Estadísticas básicas
            basic_stats = {
                'cache_hits': int(self.redis_client.get('sgm:nomina:stats:cache_hits') or 0),
                'cache_misses': int(self.redis_client.get('sgm:nomina:stats:cache_misses') or 0),
                'cache_writes': int(self.redis_client.get('sgm:nomina:stats:cache_writes') or 0),
                'cache_errors': int(self.redis_client.get('sgm:nomina:stats:cache_errors') or 0),
                'cache_invalidations': int(self.redis_client.get('sgm:nomina:stats:cache_invalidations') or 0),
                'cache_cleanups': int(self.redis_client.get('sgm:nomina:stats:cache_cleanups') or 0),
            }
            
            # Estadísticas específicas de nómina
            nomina_stats = {
                'libro_remuneraciones_cached': int(self.redis_client.get('sgm:nomina:stats:libro_remuneraciones_cached') or 0),
                'empleados_talana_cached': int(self.redis_client.get('sgm:nomina:stats:empleados_talana_cached') or 0),
                'empleados_analista_cached': int(self.redis_client.get('sgm:nomina:stats:empleados_analista_cached') or 0),
                'discrepancias_cached': int(self.redis_client.get('sgm:nomina:stats:discrepancias_cached') or 0),
                'consolidaciones_preparadas': int(self.redis_client.get('sgm:nomina:stats:consolidaciones_preparadas') or 0),
                'archivos_reemplazados': int(self.redis_client.get('sgm:nomina:stats:archivos_reemplazados') or 0),
                'nomina_logs_cached': int(self.redis_client.get('sgm:nomina:stats:nomina_logs_cached') or 0),
            }
            
            # Contadores de claves por tipo
            nomina_keys = self.redis_client.keys('sgm:nomina:*')
            key_counts = {
                'total_keys': len(nomina_keys),
                'libro_keys': len([k for k in nomina_keys if ':libro_remuneraciones' in k]),
                'talana_keys': len([k for k in nomina_keys if ':empleados_talana' in k]),
                'analista_keys': len([k for k in nomina_keys if ':empleados_analista' in k]),
                'discrepancias_keys': len([k for k in nomina_keys if ':discrepancias' in k]),
                'consolidacion_keys': len([k for k in nomina_keys if ':consolidacion' in k]),
                'log_keys': len([k for k in nomina_keys if ':logs:' in k]),
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
                **nomina_stats,
                **key_counts,
                **memory_stats,
                'hit_rate_percent': hit_rate,
                'last_updated': datetime.now().isoformat(),
                'db_index': 2,
                'module': 'nomina',
                'cache_system_version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {'error': str(e)}
    
    def _increment_stat(self, stat_name: str) -> None:
        """
        Incrementar contador de estadísticas de forma segura
        
        Args:
            stat_name: Nombre de la estadística a incrementar
        """
        try:
            self.redis_client.incr(f"sgm:nomina:stats:{stat_name}")
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
            logger.error(f"❌ Error verificando conexión Redis: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verificación completa de salud del sistema de cache de nómina
        
        Returns:
            Dict con información de salud del sistema
        """
        try:
            start_time = datetime.now()
            
            # Test básico de conexión
            ping_success = self.redis_client.ping()
            
            # Test de escritura/lectura
            test_key = "sgm:nomina:health_check:test"
            test_value = {"timestamp": start_time.isoformat(), "test": True, "module": "nomina"}
            
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
                'db_index': 2,
                'module': 'nomina',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'module': 'nomina'
            }
    
    # ========== MÉTODOS ADICIONALES PARA DASHBOARD ==========
    
    def obtener_estado_cierre(self, cierre_id: int) -> Dict[str, Any]:
        """
        Obtener el estado actual de un cierre en Redis.
        
        Args:
            cierre_id: ID del cierre
            
        Returns:
            Dict con el estado del cierre en Redis
        """
        try:
            # Obtener información del cierre de la BD
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Verificar si hay datos en Redis
            validacion_status = self.get_validacion_status(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            libro_data = self.obtener_libro_remuneraciones(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            empleados_talana = self.obtener_empleados_talana(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            discrepancias = self.obtener_discrepancias(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            return {
                'cierre_id': cierre_id,
                'cliente_id': cierre.cliente.id,
                'periodo': cierre.periodo,
                'estado_bd': cierre.estado,
                'estado_redis': {
                    'validacion_status': validacion_status is not None,
                    'libro_remuneraciones': libro_data is not None,
                    'empleados_talana': empleados_talana is not None,
                    'discrepancias': discrepancias is not None,
                    'consolidacion_disponible': all([
                        validacion_status,
                        libro_data or empleados_talana
                    ])
                },
                'metadatos': {
                    'fecha_consulta': datetime.now().isoformat(),
                    'keys_activas': self._contar_keys_cierre(cierre.cliente.id, cierre.periodo)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del cierre {cierre_id}: {e}")
            return {
                'cierre_id': cierre_id,
                'error': str(e),
                'estado_redis': {},
                'metadatos': {
                    'fecha_consulta': datetime.now().isoformat(),
                    'error': True
                }
            }
    
    def consolidar_cierre(self, cierre_id: int) -> Dict[str, Any]:
        """
        Consolidar datos de un cierre desde Redis a la base de datos.
        
        Args:
            cierre_id: ID del cierre a consolidar
            
        Returns:
            Dict con el resultado de la consolidación
        """
        try:
            # Obtener información del cierre
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            logger.info(f"Iniciando consolidación del cierre {cierre_id}")
            
            # Preparar consolidación
            consolidacion = self.preparar_consolidacion(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            if not consolidacion.get('success', False):
                return {
                    'success': False,
                    'message': f"Error preparando consolidación: {consolidacion.get('message', 'Error desconocido')}",
                    'cierre_id': cierre_id
                }
            
            # Actualizar estado en Redis
            self.set_validacion_status(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                status_data={
                    'cierre_id': cierre_id,
                    'estado': 'consolidando',
                    'fecha_consolidacion_inicio': datetime.now().isoformat(),
                    'archivos_procesados': consolidacion.get('archivos_procesados', [])
                }
            )
            
            logger.info(f"Consolidación del cierre {cierre_id} completada")
            
            return {
                'success': True,
                'message': 'Cierre consolidado exitosamente desde Redis',
                'cierre_id': cierre_id,
                'datos_consolidados': consolidacion,
                'fecha_consolidacion': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error consolidando cierre {cierre_id}: {e}")
            return {
                'success': False,
                'message': f'Error durante consolidación: {str(e)}',
                'cierre_id': cierre_id,
                'error': str(e)
            }
    
    def actualizar_estado_cierre(self, cierre_id: int, nuevo_estado: str) -> bool:
        """
        Actualizar el estado de un cierre en Redis.
        
        Args:
            cierre_id: ID del cierre
            nuevo_estado: Nuevo estado del cierre
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Obtener información del cierre
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Actualizar estado en validacion_status
            status_actual = self.get_validacion_status(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo
            )
            
            if status_actual:
                status_actual['estado'] = nuevo_estado
                status_actual['fecha_actualizacion'] = datetime.now().isoformat()
                
                resultado = self.set_validacion_status(
                    cliente_id=cierre.cliente.id,
                    periodo=cierre.periodo,
                    status_data=status_actual
                )
                
                logger.info(f"Estado del cierre {cierre_id} actualizado a '{nuevo_estado}'")
                return resultado
            else:
                # Crear nuevo estado si no existe
                return self.set_validacion_status(
                    cliente_id=cierre.cliente.id,
                    periodo=cierre.periodo,
                    status_data={
                        'cierre_id': cierre_id,
                        'estado': nuevo_estado,
                        'fecha_creacion': datetime.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error actualizando estado del cierre {cierre_id}: {e}")
            return False
    
    def archivar_cierre(self, cierre_id: int) -> Dict[str, Any]:
        """
        Archivar un cierre cerrado en Redis (mover a archivo histórico).
        
        Args:
            cierre_id: ID del cierre a archivar
            
        Returns:
            Dict con el resultado del archivado
        """
        try:
            # Obtener información del cierre
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            if cierre.estado != 'cerrado':
                return {
                    'success': False,
                    'message': 'Solo se pueden archivar cierres cerrados',
                    'cierre_id': cierre_id
                }
            
            # Crear clave de archivo histórico
            archivo_key = f"sgm:nomina:archivo:{cierre.cliente.id}:{cierre.periodo}"
            
            # Recopilar todos los datos del cierre
            datos_archivo = {
                'cierre_id': cierre_id,
                'cliente_id': cierre.cliente.id,
                'periodo': cierre.periodo,
                'fecha_archivado': datetime.now().isoformat(),
                'estado_final': cierre.estado,
                'datos': {
                    'validacion_status': self.get_validacion_status(cierre.cliente.id, cierre.periodo),
                    'discrepancias_resumen': self.obtener_discrepancias_para_dashboard(cierre.cliente.id, cierre.periodo)
                }
            }
            
            # Guardar archivo
            self.redis_client.setex(
                archivo_key,
                timedelta(days=365).total_seconds(),  # Mantener por 1 año
                self._serialize_data(datos_archivo)
            )
            
            # Limpiar datos de trabajo (opcional)
            keys_trabajo = [
                f"sgm:nomina:{cierre.cliente.id}:{cierre.periodo}:validacion_status",
                f"sgm:nomina:{cierre.cliente.id}:{cierre.periodo}:procesamiento"
            ]
            
            keys_eliminadas = 0
            for key in keys_trabajo:
                if self.redis_client.delete(key):
                    keys_eliminadas += 1
            
            logger.info(f"Cierre {cierre_id} archivado exitosamente. Keys eliminadas: {keys_eliminadas}")
            
            return {
                'success': True,
                'message': 'Cierre archivado exitosamente',
                'cierre_id': cierre_id,
                'archivo_key': archivo_key,
                'keys_eliminadas': keys_eliminadas,
                'fecha_archivado': datos_archivo['fecha_archivado']
            }
            
        except Exception as e:
            logger.error(f"Error archivando cierre {cierre_id}: {e}")
            return {
                'success': False,
                'message': f'Error archivando cierre: {str(e)}',
                'cierre_id': cierre_id,
                'error': str(e)
            }
    
    def inicializar_cierre(self, cierre_id: int, forzar: bool = False) -> Dict[str, Any]:
        """
        Inicializar un cierre en Redis.
        
        Args:
            cierre_id: ID del cierre a inicializar
            forzar: Si True, sobrescribe datos existentes
            
        Returns:
            Dict con el resultado de la inicialización
        """
        try:
            # Obtener información del cierre
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            
            # Verificar si ya existe y no se está forzando
            if not forzar:
                status_existente = self.get_validacion_status(
                    cliente_id=cierre.cliente.id,
                    periodo=cierre.periodo
                )
                
                if status_existente:
                    return {
                        'success': False,
                        'message': 'El cierre ya está inicializado en Redis. Use forzar=True para reinicializar.',
                        'cierre_id': cierre_id,
                        'status_existente': status_existente
                    }
            
            # Inicializar estado de validación
            status_inicial = {
                'cierre_id': cierre_id,
                'estado': 'iniciado',
                'fecha_inicio': datetime.now().isoformat(),
                'archivos_esperados': ['libro_remuneraciones'],
                'archivos_recibidos': [],
                'discrepancias_detectadas': 0,
                'validacion_completada': False
            }
            
            resultado = self.set_validacion_status(
                cliente_id=cierre.cliente.id,
                periodo=cierre.periodo,
                status_data=status_inicial
            )
            
            if resultado:
                # Actualizar cache key en el modelo
                cierre.cache_key_redis = f"sgm:nomina:{cierre.cliente.id}:{cierre.periodo}"
                cierre.save(update_fields=['cache_key_redis'])
                
                logger.info(f"Cierre {cierre_id} inicializado exitosamente en Redis")
                
                return {
                    'success': True,
                    'message': 'Cierre inicializado exitosamente en Redis',
                    'cierre_id': cierre_id,
                    'cache_key': cierre.cache_key_redis,
                    'status_inicial': status_inicial
                }
            else:
                return {
                    'success': False,
                    'message': 'Error guardando estado inicial en Redis',
                    'cierre_id': cierre_id
                }
                
        except Exception as e:
            logger.error(f"Error inicializando cierre {cierre_id}: {e}")
            return {
                'success': False,
                'message': f'Error inicializando cierre: {str(e)}',
                'cierre_id': cierre_id,
                'error': str(e)
            }
    
    def _contar_keys_cierre(self, cliente_id: int, periodo: str) -> int:
        """
        Contar cuántas keys activas tiene un cierre en Redis.
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            int: Número de keys activas
        """
        try:
            pattern = f"sgm:nomina:{cliente_id}:{periodo}:*"
            keys = self.redis_client.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Error contando keys del cierre {cliente_id}:{periodo}: {e}")
            return 0

    # ===========================================
    # MÉTODOS ESPECÍFICOS PARA TARJETA LIBRO DE REMUNERACIONES
    # ===========================================
    
    def guardar_libro_excel(self, cliente_id: int, cierre_id: int, archivo_data: List[Dict[str, Any]], filename: str) -> bool:
        """Guarda datos temporales del Excel del libro de remuneraciones - FASE 1"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_archivo")
        
        archivo_info = {
            'filename': filename,
            'data': archivo_data,
            'timestamp': datetime.now().isoformat(),
            'total_filas': len(archivo_data),
            'estado': 'archivo_cargado',
            'tipo': 'libro_remuneraciones'
        }
        
        try:
            serialized_data = self._serialize_data(archivo_info)
            # TTL corto: solo temporal hasta análisis completo
            self.redis_client.setex(key, 3600, serialized_data) 
            
            logger.info(f"📁 TALANA: Libro Excel temporal guardado - {filename} ({len(archivo_data)} filas)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando libro Excel temporal: {e}")
            return False
    
    def obtener_libro_excel(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene datos temporales del Excel guardado - FASE 1"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_archivo")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo Excel: {e}")
            return None
    
    def guardar_analisis_headers(self, cliente_id: int, cierre_id: int, analisis: Dict[str, Any]) -> bool:
        """Guarda análisis de headers del libro de remuneraciones - FASE 1"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_headers")
        
        try:
            serialized_data = self._serialize_data(analisis)
            self.redis_client.setex(key, 7200, serialized_data)
            
            logger.info(f"🗺️ TALANA: Análisis headers libro guardado - {len(analisis.get('headers_mapeados', []))} mapeados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando análisis headers libro: {e}")
            return False
    
    def obtener_analisis_headers(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene análisis de headers del libro - FASE 1"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_headers")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo análisis headers: {e}")
            return None
    
    def guardar_mapeos_manuales(self, cliente_id: int, cierre_id: int, mapeos: Dict[str, str]) -> bool:
        """Guarda mapeos manuales hechos por el analista - Libro de remuneraciones"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_mapeo_manual")
        
        mapeo_info = {
            'mapeos': mapeos,
            'timestamp': datetime.now().isoformat(),
            'total_mapeos': len(mapeos),
            'origen': 'libro_remuneraciones'
        }
        
        try:
            serialized_data = self._serialize_data(mapeo_info)
            self.redis_client.setex(key, 7200, serialized_data)
            
            logger.info(f"✏️ TALANA: Mapeos manuales libro guardados - {len(mapeos)} conceptos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando mapeos manuales libro: {e}")
            return False
    
    def obtener_mapeos_manuales(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene mapeos manuales del libro"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_mapeo_manual")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo mapeos manuales: {e}")
            return None
    
    def guardar_mapeo_final(self, cliente_id: int, cierre_id: int, mapeo: Dict[str, Any]) -> bool:
        """
        Guarda mapeo final consolidado del libro de remuneraciones
        Optimizado para estrategia híbrida - FASE 1
        """
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_mapeo_final")
        
        try:
            serialized_data = self._serialize_data(mapeo)
            # TTL de 24 horas - suficiente para completar FASE 1
            self.redis_client.setex(key, 86400, serialized_data)
            
            logger.info(f"🎯 TALANA: Mapeo final libro guardado - {mapeo.get('total_conceptos_mapeados', 0)} conceptos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando mapeo final libro: {e}")
            return False
    
    def obtener_mapeo_final(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene mapeo final consolidado del libro"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_mapeo_final")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo mapeo final: {e}")
            return None
    
    def guardar_libro_empleados_conceptos(self, cliente_id: int, cierre_id: int, empleados_data: List[Dict[str, Any]]) -> bool:
        """
        Guarda empleados con conceptos del libro de remuneraciones - FASE 1
        Solo se llama cuando mapeos están completos y listos para verificación
        """
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_empleados_conceptos")
        
        empleados_info = {
            'empleados': empleados_data,
            'timestamp': datetime.now().isoformat(),
            'total_empleados': len(empleados_data),
            'total_conceptos': sum(len(emp.get('conceptos', {})) for emp in empleados_data),
            'estado': 'listos_verificacion'
        }
        
        try:
            serialized_data = self._serialize_data(empleados_info)
            # TTL largo para empleados procesados - necesarios para verificación
            self.redis_client.setex(key, 86400, serialized_data)  # 24 horas
            
            logger.info(f"👥 TALANA: Empleados libro guardados - {len(empleados_data)} empleados, {empleados_info['total_conceptos']} conceptos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando empleados libro: {e}")
            return False
    
    def obtener_libro_empleados_conceptos(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene empleados con conceptos del libro"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_empleados_conceptos")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo empleados libro: {e}")
            return None
    
    def limpiar_archivo_temporal_libro(self, cliente_id: int, cierre_id: int) -> bool:
        """Limpia archivo temporal del libro después de procesar headers"""
        key = self._get_key(cliente_id, cierre_id, "talana", "libro_archivo")
        
        try:
            eliminado = self.redis_client.delete(key)
            if eliminado:
                logger.info(f"🧹 TALANA: Archivo temporal libro limpiado")
            return bool(eliminado)
            
        except Exception as e:
            logger.error(f"❌ Error limpiando archivo temporal libro: {e}")
            return False
    
    def guardar_empleados_procesados(self, cliente_id: int, cierre_id: int, empleados: List[Dict[str, Any]]) -> bool:
        """Guarda empleados procesados con todos sus conceptos"""
        key = f"empleados_procesados:{cliente_id}:{cierre_id}"
        
        empleados_info = {
            'empleados': empleados,
            'timestamp': datetime.now().isoformat(),
            'total_empleados': len(empleados),
            'total_conceptos': sum(emp.get('total_conceptos', 0) for emp in empleados)
        }
        
        try:
            serialized_data = self._serialize_data(empleados_info)
            self.redis_client.setex(key, 7200, serialized_data)
            
            logger.info(f"👥 Empleados procesados guardados: {len(empleados)} empleados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando empleados procesados: {e}")
            return False
    
    def obtener_empleados_procesados(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene empleados procesados"""
        key = f"empleados_procesados:{cliente_id}:{cierre_id}"
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo empleados procesados: {e}")
            return None
    
    def actualizar_estado_libro(self, cliente_id: int, cierre_id: int, estado: str, info_adicional: Dict[str, Any] = None) -> bool:
        """Actualiza estado específico del procesamiento usando estructura organizada"""
        key = self._get_key(cliente_id, cierre_id, "estado", "procesamiento")
        
        estado_info = {
            'estado': estado,
            'timestamp': datetime.now().isoformat(),
            'info': info_adicional or {}
        }
        
        try:
            serialized_data = self._serialize_data(estado_info)
            self.redis_client.setex(key, 7200, serialized_data)
            
            logger.debug(f"📊 Estado procesamiento actualizado: {estado}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado procesamiento: {e}")
            return False
    
    def obtener_estado_libro(self, cliente_id: int, cierre_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene estado actual del procesamiento"""
        key = self._get_key(cliente_id, cierre_id, "estado", "procesamiento")
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            
            # Estado por defecto si no existe
            return {
                'estado': 'pendiente',
                'timestamp': datetime.now().isoformat(),
                'info': {'mensaje': 'Esperando archivo de libro de remuneraciones'}
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado libro: {e}")
            return None
    
    def limpiar_cache_libro_completo(self, cliente_id: int, cierre_id: int) -> bool:
        """Limpia todo el cache relacionado con un cierre usando estructura organizada"""
        try:
            # Usar patrón para encontrar todas las keys del cierre
            pattern = f"sgm:nomina:{cliente_id}:{cierre_id}:*"
            keys = self.redis_client.keys(pattern)
            
            eliminadas = 0
            for key in keys:
                if self.redis_client.delete(key):
                    eliminadas += 1
            
            logger.info(f"🧹 Cache limpiado: {eliminadas} keys eliminadas para cierre {cierre_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache: {e}")
            return False
    
    def limpiar_fase_especifica(self, cliente_id: int, cierre_id: int, fase: str) -> bool:
        """Limpia cache de una fase específica"""
        try:
            pattern = f"sgm:nomina:{cliente_id}:{cierre_id}:{fase}:*"
            keys = self.redis_client.keys(pattern)
            
            eliminadas = 0
            for key in keys:
                if self.redis_client.delete(key):
                    eliminadas += 1
            
            logger.info(f"🧹 Fase {fase} limpiada: {eliminadas} keys eliminadas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error limpiando fase {fase}: {e}")
            return False
    
    def obtener_keys_cierre(self, cliente_id: int, cierre_id: int) -> List[str]:
        """Obtiene todas las keys de un cierre para debugging"""
        try:
            pattern = f"sgm:nomina:{cliente_id}:{cierre_id}:*"
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"❌ Error obteniendo keys: {e}")
            return []
            
            logger.info(f"🧹 Cache libro limpiado: {eliminadas} claves eliminadas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error limpiando cache libro: {e}")
            return False
    
    def limpiar_archivos_expirados(self) -> int:
        """Limpia archivos expirados del cache"""
        try:
            # Buscar todas las claves relacionadas con libros
            pattern = "*libro*"
            keys = self.redis_client.keys(pattern)
            
            eliminadas = 0
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Clave expirada
                    self.redis_client.delete(key)
                    eliminadas += 1
            
            return eliminadas
            
        except Exception as e:
            logger.error(f"❌ Error limpiando archivos expirados: {e}")
            return 0

# ========== INSTANCIA GLOBAL ==========
# Instancia global del sistema de cache de nómina
# Se inicializa de forma lazy para evitar errores en import time
_cache_nomina_system = None

def get_cache_nomina_system() -> CacheNominaSGM:
    """
    Obtener instancia del sistema de cache de nómina (patrón singleton)
    
    Returns:
        CacheNominaSGM: Instancia del sistema de cache de nómina
    """
    global _cache_nomina_system
    if _cache_nomina_system is None:
        _cache_nomina_system = CacheNominaSGM()
    return _cache_nomina_system

# ========== FUNCIONES DE CONVENIENCIA ==========
def test_connection_nomina() -> bool:
    """
    Función de conveniencia para probar la conexión a Redis desde cualquier lugar
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        cache_system = get_cache_nomina_system()
        return cache_system.check_connection()
    except Exception as e:
        logger.error(f"❌ Error probando conexión de nómina: {e}")
        return False

def get_nomina_health() -> Dict[str, Any]:
    """
    Función de conveniencia para obtener health check desde cualquier lugar
    
    Returns:
        Dict con información de salud
    """
    try:
        cache_system = get_cache_nomina_system()
        return cache_system.health_check()
    except Exception as e:
        logger.error(f"❌ Error obteniendo health check de nómina: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
