"""
Tasks Celery para Procesamiento de Libro de Remuneraciones - Nueva Arquitectura
============================================================================

Implementación de Celery chains para el procesamiento del libro:

Chain automático (al subir archivo):
1. analizar_headers_libro → Analiza headers y mapea automáticamente
2. extraer_cierre_id → Extrae ID para siguiente paso

Task manual (cuando usuario hace click "Procesar"):
3. procesar_empleados_libro → Procesa empleados cuando mapeos están completos

Autor: Sistema SGM - Módulo Nómina
Fecha: 21 de julio de 2025
"""

import pandas as pd
import logging
import json
import tempfile
import os
from datetime import datetime
from celery import shared_task, chain
from django.conf import settings

from .models import CierreNomina, MapeoConcepto
from .cache_redis import CacheNominaSGM
# Importamos solo las funciones que necesitamos, evitando el problema de importación
# from .utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones, _es_rut_valido
from .utils.uploads import guardar_temporal, limpiar_archivo_temporal

logger = logging.getLogger(__name__)

# ========== FUNCIONES AUXILIARES ADAPTADAS ==========

def _es_rut_valido(valor_rut):
    """
    Determina si un valor de RUT es válido para procesamiento.
    Retorna False para valores NaN, vacíos, o palabras como "total" que usa Talana.
    """
    if valor_rut is None:
        return False
    
    # Verificar si es NaN de pandas
    if pd.isna(valor_rut):
        return False
    
    # Convertir a string y limpiar
    rut_str = str(valor_rut).strip().lower()
    
    # Verificar si está vacío
    if not rut_str:
        return False
    
    # Verificar si es "nan" como string
    if rut_str == "nan":
        return False
    
    # Verificar palabras típicas de filas de totales que usa Talana
    palabras_invalidas = [
        "total", "totales", "suma", "sumatoria", 
        "resumen", "consolidado", "subtotal"
    ]
    
    if rut_str in palabras_invalidas:
        return False
    
    return True

def obtener_headers_libro_remuneraciones_adaptado(path_archivo):
    """
    Obtiene los encabezados de un libro de remuneraciones.
    Versión adaptada que filtra las columnas básicas de empleado.
    """
    logger.info(f"Abriendo archivo de libro de remuneraciones: {path_archivo}")
    try:
        df = pd.read_excel(path_archivo, engine="openpyxl")
        headers = list(df.columns)

        # --- Heuristics for common employee columns ---
        rut_col = next((c for c in headers if 'rut' in c.lower() and 'trab' in c.lower()), None)
        dv_col = next((c for c in headers if 'dv' in c.lower() and 'trab' in c.lower()), None)
        ape_pat_col = next((c for c in headers if 'apellido' in c.lower() and 'pater' in c.lower()), None)
        ape_mat_col = next((c for c in headers if 'apellido' in c.lower() and 'mater' in c.lower()), None)
        nombres_col = next((c for c in headers if 'nombre' in c.lower()), None)
        ingreso_col = next((c for c in headers if 'ingreso' in c.lower()), None)

        heuristic_cols = {c for c in [rut_col, dv_col, ape_pat_col, ape_mat_col, nombres_col, ingreso_col] if c}

        # --- Explicit columns to drop regardless of heuristics ---
        explicit_drop = {
            'año',
            'mes',
            'rut de la empresa',
            'rut del trabajador',
            'nombre',
            'apellido paterno',
            'apellido materno',
        }
        explicit_cols = {h for h in headers if h.strip().lower() in explicit_drop}

        empleado_cols = heuristic_cols.union(explicit_cols)
        filtered_headers = [h for h in headers if h not in empleado_cols]

        logger.info(f"Headers encontrados: {filtered_headers}")
        return filtered_headers
    except Exception as e:
        logger.error(f"Error al leer el archivo: {e}")
        raise

# ========== TASK 1: ANALIZAR HEADERS DEL EXCEL ==========

@shared_task(bind=True, name='nomina.analizar_headers_libro')
def analizar_headers_libro(self, cierre_id, archivo_data, filename):
    """
    Primera tarea del chain: Analiza headers del Excel y mapea automáticamente.
    
    Args:
        cierre_id: ID del cierre
        archivo_data: Datos del archivo (base64 o path)
        filename: Nombre del archivo
    
    Returns:
        Dict con resultado del análisis
    """
    logger.info(f"🔍 Iniciando análisis headers para cierre {cierre_id} - {filename}")
    
    try:
        # Obtener instancia del cierre
        cierre = CierreNomina.objects.get(id=cierre_id)
        cache = CacheNominaSGM()
        
        # Actualizar estado inicial
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'analizando', {
            'filename': filename,
            'progreso': 10,
            'mensaje': 'Analizando headers del Excel...'
        })
        
        # Guardar archivo temporal para procesamiento
        temp_path = None
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                if isinstance(archivo_data, str):
                    # Si viene como base64, decodificar
                    import base64
                    tmp_file.write(base64.b64decode(archivo_data))
                else:
                    # Si viene como bytes directos
                    tmp_file.write(archivo_data)
                temp_path = tmp_file.name
            
            # Usar la función adaptada para obtener headers
            headers_filtrados = obtener_headers_libro_remuneraciones_adaptado(temp_path)
            
            # Leer el Excel para obtener datos completos
            df = pd.read_excel(temp_path, engine="openpyxl")
            
            # Convertir datos a formato serializable
            datos_archivo = []
            total_filas = len(df)
            filas_validas = 0
            
            for _, row in df.iterrows():
                # Validar si la fila tiene un RUT válido
                rut_col = next((col for col in df.columns if 'rut' in col.lower() and 'trab' in col.lower()), None)
                if rut_col and _es_rut_valido(row.get(rut_col)):
                    # Convertir fila a dict, manejando valores NaN
                    row_dict = {}
                    for col, val in row.items():
                        if pd.isna(val):
                            row_dict[col] = ""
                        else:
                            row_dict[col] = str(val).strip()
                    datos_archivo.append(row_dict)
                    filas_validas += 1
            
            logger.info(f"📊 Archivo procesado: {filas_validas} filas válidas de {total_filas} totales")
            
        finally:
            # Limpiar archivo temporal
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        
        # ✨ NUEVA FUNCIONALIDAD: Clasificar headers usando mapeos precargados en Redis
        headers_mapeados, headers_no_mapeados = clasificar_headers_con_mapeo_concepto_redis(
            headers_filtrados, cierre.cliente.id, cierre_id
        )
        
        # Guardar archivo y análisis en Redis
        archivo_guardado = cache.guardar_libro_excel(
            cliente_id=cierre.cliente.id,
            cierre_id=cierre_id,
            archivo_data=datos_archivo,
            filename=filename
        )
        
        if not archivo_guardado:
            raise Exception("Error guardando archivo en Redis")
        
        # Guardar análisis de headers
        analisis_headers = {
            'headers_mapeados': headers_mapeados,
            'headers_no_mapeados': headers_no_mapeados,
            'total_headers': len(headers_filtrados),
            'mapeados_automaticamente': len(headers_mapeados),
            'pendientes_mapeo': len(headers_no_mapeados),
            'timestamp': datetime.now().isoformat()
        }
        
        headers_guardados = cache.guardar_analisis_headers(
            cliente_id=cierre.cliente.id,
            cierre_id=cierre_id,
            analisis=analisis_headers
        )
        
        if not headers_guardados:
            raise Exception("Error guardando análisis headers en Redis")
        
        # Determinar siguiente estado
        if headers_no_mapeados:
            # Hay headers sin mapear, requiere intervención manual
            nuevo_estado = 'mapeo_requerido'
            mensaje = f'{len(headers_no_mapeados)} conceptos requieren mapeo manual'
        else:
            # Todos mapeados, puede proceder automáticamente
            nuevo_estado = 'listo_procesar'
            mensaje = 'Todos los conceptos fueron mapeados automáticamente'
        
        # Actualizar estado final
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, nuevo_estado, {
            'filename': filename,
            'progreso': 50,
            'mensaje': mensaje,
            'headers_analysis': analisis_headers,
            'empleados_detectados': filas_validas
        })
        
        resultado = {
            'success': True,
            'cierre_id': cierre_id,
            'filename': filename,
            'headers_mapeados': headers_mapeados,
            'headers_no_mapeados': headers_no_mapeados,
            'empleados_detectados': filas_validas,
            'estado_siguiente': nuevo_estado,
            'mensaje': mensaje
        }
        
        logger.info(f"✅ Análisis completado para cierre {cierre_id}: {len(headers_mapeados)} mapeados, {len(headers_no_mapeados)} pendientes")
        return resultado
        
    except Exception as e:
        error_msg = f"Error analizando headers para cierre {cierre_id}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        try:
            cache = CacheNominaSGM()
            cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'error', {
                'filename': filename,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        except:
            pass
        
        # En Celery, lanzamos la excepción para que se maneje apropiadamente
        raise self.retry(exc=e, countdown=60, max_retries=3)

# ========== TASK 2: PROCESAR EMPLEADOS DEL LIBRO ==========

@shared_task(bind=True, name='nomina.procesar_empleados_libro')
def procesar_empleados_libro(self, cierre_id):
    """
    Procesa empleados del libro de remuneraciones con mapeos completos.
    Solo se ejecuta cuando todos los headers están mapeados.
    
    Args:
        cierre_id: ID del cierre
        
    Returns:
        Dict con resultado del procesamiento de empleados
    """
    logger.info(f"👥 LIBRO: Procesando empleados con conceptos para cierre {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        cache = CacheNominaSGM()
        
        # Actualizar estado
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'procesando_empleados', {
            'progreso': 80,
            'mensaje': 'Procesando empleados del libro con mapeos aplicados...'
        })
        
        # Obtener datos del archivo temporal
        datos_archivo = cache.obtener_libro_excel(cierre.cliente.id, cierre_id)
        if not datos_archivo:
            raise Exception("No se encontraron datos del archivo temporal en Redis")
        
        # Obtener mapeo final
        mapeo_final = cache.obtener_mapeo_final(cierre.cliente.id, cierre_id)
        if not mapeo_final:
            raise Exception("No se encontró mapeo final - headers deben estar mapeados primero")
        
        mapeos_completos = mapeo_final.get('mapeos_completos', {})
        
        # Procesar cada empleado
        empleados_procesados = []
        filas_procesadas = 0
        errores_procesamiento = []
        
        for fila_data in datos_archivo.get('data', []):
            try:
                # Identificar datos básicos del empleado
                empleado_data = _extraer_datos_empleado(fila_data, cierre.cliente)
                
                if not empleado_data:
                    continue  # Saltar filas sin datos válidos de empleado
                
                # Procesar conceptos aplicando mapeos
                conceptos_empleado = {}
                for header_original, valor in fila_data.items():
                    if header_original in mapeos_completos:
                        concepto_estandar = mapeos_completos[header_original]
                        # Limpiar y validar valor
                        valor_limpio = _limpiar_valor_concepto(valor)
                        if valor_limpio is not None:  # Solo agregar si hay valor válido
                            conceptos_empleado[concepto_estandar] = valor_limpio
                
                # Crear estructura final del empleado
                empleado_final = {
                    **empleado_data,
                    'conceptos': conceptos_empleado,
                    'total_conceptos': len(conceptos_empleado),
                    'origen': 'libro_remuneraciones'
                }
                
                empleados_procesados.append(empleado_final)
                filas_procesadas += 1
                
            except Exception as e:
                error_fila = {
                    'fila': filas_procesadas + 1,
                    'error': str(e),
                    'datos_fila': fila_data
                }
                errores_procesamiento.append(error_fila)
                logger.warning(f"⚠️ Error procesando empleado fila {filas_procesadas + 1}: {e}")
        
        # Guardar empleados procesados en Redis
        empleados_guardados = cache.guardar_libro_empleados_conceptos(
            cliente_id=cierre.cliente.id,
            cierre_id=cierre_id,
            empleados=empleados_procesados
        )
        
        if not empleados_guardados:
            raise Exception("Error guardando empleados procesados en Redis")
        
        # Limpiar archivo temporal (ya no necesario)
        cache.limpiar_archivo_temporal_libro(cierre.cliente.id, cierre_id)
        
        # Calcular estadísticas
        total_conceptos = sum(emp.get('total_conceptos', 0) for emp in empleados_procesados)
        promedio_conceptos = total_conceptos / len(empleados_procesados) if empleados_procesados else 0
        
        # Actualizar estado final
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'libro_procesado', {
            'progreso': 100,
            'mensaje': 'Libro de remuneraciones procesado exitosamente',
            'empleados_procesados': len(empleados_procesados),
            'total_conceptos': total_conceptos,
            'promedio_conceptos_por_empleado': round(promedio_conceptos, 2),
            'errores': len(errores_procesamiento),
            'listo_verificacion': True,
            'timestamp_completado': datetime.now().isoformat()
        })
        
        resultado = {
            'success': True,
            'cierre_id': cierre_id,
            'empleados_procesados': len(empleados_procesados),
            'total_conceptos': total_conceptos,
            'errores': errores_procesamiento,
            'listo_verificacion': True,
            'estadisticas': {
                'filas_procesadas': filas_procesadas,
                'promedio_conceptos': promedio_conceptos,
                'mapeos_aplicados': len(mapeos_completos)
            }
        }
        
        logger.info(f"✅ LIBRO: Procesamiento completado - {len(empleados_procesados)} empleados, {total_conceptos} conceptos")
        return resultado
        
    except Exception as e:
        error_msg = f"Error procesando empleados libro para cierre {cierre_id}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        try:
            cache = CacheNominaSGM()
            cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'error', {
                'error': str(e),
                'fase': 'procesamiento_empleados_libro',
                'timestamp': datetime.now().isoformat()
            })
        except:
            pass
        
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task(bind=True, name='nomina.procesar_empleados_libro')
def procesar_empleados_libro(self, cierre_id):
    """
    FASE 1: Solo procesa headers y mapeo - NO empleados (optimización de escalabilidad).
    Los empleados se procesarán en fases posteriores según flujo del negocio.
    
    Args:
        cierre_id: ID del cierre
        
    Returns:
        Dict con resultado del procesamiento de headers
    """
    logger.info(f"📋 FASE 1: Procesando headers y mapeo para cierre {cierre_id} (sin empleados)")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        cache = CacheNominaSGM()
        
        # Actualizar estado
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'procesando_headers', {
            'progreso': 70,
            'mensaje': 'FASE 1: Procesando mapeo de conceptos (sin empleados)...'
        })
        
        # Obtener análisis de headers
        analisis_headers = cache.obtener_analisis_headers(cierre.cliente.id, cierre_id)
        if not analisis_headers:
            raise Exception("No se encontró análisis de headers en Redis")
        
        # Obtener mapeos manuales (si los hay)
        mapeos_manuales = cache.obtener_mapeos_manuales(cierre.cliente.id, cierre_id)
        
        # Combinar todos los mapeos
        mapeos_completos = {}
        
        # 1. Mapeos automáticos (basados en ConceptoRemuneracion)
        for header in analisis_headers.get('headers_mapeados', []):
            concepto = MapeoConcepto.objects.filter(
                cliente=cierre.cliente,
                concepto_original=header,
                activo=True
            ).first()
            if concepto:
                mapeos_completos[header] = concepto.concepto_estandar
            else:
                # Usar el header como está si no hay mapeo específico
                mapeos_completos[header] = header
        
        # 2. Mapeos manuales (sobrescriben automáticos si hay conflicto)
        if mapeos_manuales:
            mapeos_completos.update(mapeos_manuales.get('mapeos', {}))
        
        # FASE 1: Solo guardar mapeos finales - NO procesar empleados
        mapeo_final = {
            'mapeos_automaticos': analisis_headers.get('headers_mapeados', []),
            'mapeos_manuales': mapeos_manuales.get('mapeos', {}) if mapeos_manuales else {},
            'mapeos_completos': mapeos_completos,
            'total_conceptos_mapeados': len(mapeos_completos),
            'fase_completada': 'headers_y_mapeo',
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar mapeo final en Redis (estructura optimizada)
        mapeo_guardado = cache.guardar_mapeo_final(
            cliente_id=cierre.cliente.id,
            cierre_id=cierre_id,
            mapeo=mapeo_final
        )
        
        if not mapeo_guardado:
            raise Exception("Error guardando mapeo final en Redis")
        
        # Obtener información básica del archivo solo para estadísticas
        datos_archivo = cache.obtener_libro_excel(cierre.cliente.id, cierre_id)
        empleados_detectados = len(datos_archivo.get('data', [])) if datos_archivo else 0
        
        # Actualizar estado final - FASE 1 completa
        cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'fase1_completa', {
            'progreso': 100,
            'mensaje': 'FASE 1 completada: Headers mapeados, listo para siguientes fases',
            'conceptos_mapeados': len(mapeos_completos),
            'empleados_detectados': empleados_detectados,
            'fase_completada': 'headers_y_mapeo',
            'siguiente_fase': 'movimientos_talana',
            'timestamp_completado': datetime.now().isoformat()
        })
        
        resultado = {
            'success': True,
            'fase': 1,
            'cierre_id': cierre_id,
            'conceptos_mapeados': len(mapeos_completos),
            'empleados_detectados': empleados_detectados,
            'mapeos_aplicados': mapeos_completos,
            'siguiente_fase': 'movimientos_talana',
            'optimizacion': 'empleados_no_procesados_aun',
            'estadisticas': {
                'mapeos_automaticos': len(analisis_headers.get('headers_mapeados', [])),
                'mapeos_manuales': len(mapeos_manuales.get('mapeos', {})) if mapeos_manuales else 0,
                'total_mapeos': len(mapeos_completos)
            }
        }
        
        logger.info(f"✅ FASE 1 completada para cierre {cierre_id}: {len(mapeos_completos)} conceptos mapeados, {empleados_detectados} empleados detectados")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en FASE 1 para cierre {cierre_id}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        try:
            cache = CacheNominaSGM()
            cache.actualizar_estado_libro(cierre.cliente.id, cierre_id, 'error', {
                'fase': 1,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        except:
            pass
        
        raise self.retry(exc=e, countdown=60, max_retries=3)

# ========== FUNCIONES AUXILIARES ==========

def _extraer_datos_empleado(fila_data, cliente):
    """
    Extrae datos básicos del empleado de una fila del Excel.
    Usa heurísticas para encontrar columnas de RUT, nombre, etc.
    """
    # Buscar columna de RUT
    rut_col = None
    for col in fila_data.keys():
        if 'rut' in col.lower() and 'trab' in col.lower():
            rut_col = col
            break
    
    if not rut_col:
        return None
    
    rut_value = fila_data.get(rut_col)
    if not _es_rut_valido(rut_value):
        return None
    
    # Buscar columnas de nombre
    nombre_completo = ""
    
    # Buscar nombre
    nombre_col = next((col for col in fila_data.keys() if 'nombre' in col.lower()), None)
    if nombre_col:
        nombre_completo += fila_data.get(nombre_col, "").strip()
    
    # Buscar apellidos
    apellido_pat_col = next((col for col in fila_data.keys() 
                           if 'apellido' in col.lower() and 'pater' in col.lower()), None)
    apellido_mat_col = next((col for col in fila_data.keys() 
                           if 'apellido' in col.lower() and 'mater' in col.lower()), None)
    
    if apellido_pat_col:
        apellido_pat = fila_data.get(apellido_pat_col, "").strip()
        if apellido_pat:
            nombre_completo += f" {apellido_pat}"
    
    if apellido_mat_col:
        apellido_mat = fila_data.get(apellido_mat_col, "").strip()
        if apellido_mat:
            nombre_completo += f" {apellido_mat}"
    
    return {
        'rut': str(rut_value).strip(),
        'nombre': nombre_completo.strip(),
        'cliente_id': cliente.id
    }

def _limpiar_valor_concepto(valor):
    """
    Limpia y valida valores de conceptos.
    Retorna None si el valor no es válido.
    """
    if pd.isna(valor) or valor == '' or str(valor).lower() == 'nan':
        return None
    
    valor_str = str(valor).strip()
    if not valor_str:
        return None
    
    # Intentar convertir a numérico si es posible
    try:
        # Limpiar caracteres de formato
        valor_limpio = valor_str.replace(',', '').replace('$', '').replace(' ', '')
        if valor_limpio:
            return float(valor_limpio)
    except:
        pass
    
    # Retornar como string si no es numérico
    return valor_str

# ========== FUNCIONES DE CLASIFICACIÓN ==========

def clasificar_headers_con_mapeo_concepto_redis(headers, cliente_id, cierre_id):
    """
    Clasifica los headers usando mapeos precargados en Redis (más eficiente).
    Retorna dos listas: clasificados y sin clasificar.
    
    NUEVA ESTRATEGIA:
    1. Usar mapeos precargados en Redis (no consulta BD concepto x concepto)
    2. Fallback a BD solo si no hay cache Redis
    
    Args:
        headers: Lista de headers del Excel
        cliente_id: ID del cliente
        cierre_id: ID del cierre
        
    Returns:
        Tuple: (headers_clasificados, headers_sin_clasificar)
    """
    from .cache_redis import CacheNominaSGM
    
    try:
        cache = CacheNominaSGM()
        
        # 1. Intentar obtener mapeos precargados de Redis
        key_mapeos_conocidos = f"sgm:nomina:{cliente_id}:{cierre_id}:mapeos_conocidos"
        mapeos_conocidos = cache.redis_client.hgetall(key_mapeos_conocidos)
        
        # Convertir bytes a string si es necesario
        if mapeos_conocidos:
            mapeos_conocidos = {
                k.decode() if isinstance(k, bytes) else k: 
                v.decode() if isinstance(v, bytes) else v
                for k, v in mapeos_conocidos.items()
            }
            logger.info(f"📋 Usando {len(mapeos_conocidos)} mapeos precargados desde Redis")
        else:
            # 2. Fallback: obtener desde BD si no hay cache
            logger.info(f"⚠️ No hay mapeos precargados, consultando BD como fallback")
            from nomina.models import MapeoConcepto
            mapeos_bd = MapeoConcepto.objects.filter(cliente_id=cliente_id, activo=True)
            mapeos_conocidos = {
                mapeo.header_excel: mapeo.clasificacion_sugerida
                for mapeo in mapeos_bd
            }
        
        # 3. Clasificar headers usando mapeos
        headers_clasificados = []
        headers_sin_clasificar = []
        
        for header in headers:
            # Normalizar para comparación
            header_normalizado = header.strip().lower()
            
            # Buscar mapeo (comparación case-insensitive)
            mapeo_encontrado = None
            for header_conocido, clasificacion in mapeos_conocidos.items():
                if header_conocido.strip().lower() == header_normalizado:
                    mapeo_encontrado = clasificacion
                    break
            
            if mapeo_encontrado:
                headers_clasificados.append(header)
                logger.debug(f"✅ {header} → {mapeo_encontrado} (automático)")
            else:
                headers_sin_clasificar.append(header)
                logger.debug(f"❓ {header} → requiere mapeo manual")
        
        logger.info(f"🎯 Clasificación: {len(headers_clasificados)} automáticos, {len(headers_sin_clasificar)} manuales")
        return headers_clasificados, headers_sin_clasificar
        
    except Exception as e:
        logger.error(f"Error en clasificación con Redis: {e}")
        # Fallback completo a función original
        return clasificar_headers_con_mapeo_concepto_original(headers, cliente_id)

def clasificar_headers_con_mapeo_concepto_original(headers, cliente_id):
    """
    Función original como fallback en caso de error con Redis.
    """
    try:
        from nomina.models import MapeoConcepto
        
        # Obtén los conceptos vigentes del cliente, normalizados a lower y sin espacios
        conceptos_vigentes = set(
            c.header_excel.strip().lower()
            for c in MapeoConcepto.objects.filter(cliente_id=cliente_id, activo=True)
        )
        
        headers_clasificados = []
        headers_sin_clasificar = []

        for h in headers:
            if h.strip().lower() in conceptos_vigentes:
                headers_clasificados.append(h)
            else:
                headers_sin_clasificar.append(h)

        logger.info(f"📊 Clasificación BD fallback: {len(headers_clasificados)} clasificados, {len(headers_sin_clasificar)} sin clasificar")
        return headers_clasificados, headers_sin_clasificar
        
    except Exception as e:
        logger.error(f"Error en clasificación BD fallback: {e}")
        # En caso de error total, todos requieren mapeo manual
        return [], headers

def clasificar_headers_con_mapeo_concepto(headers, cliente):
    """
    Función original mantenida para compatibilidad.
    DEPRECATED: Usar clasificar_headers_con_mapeo_concepto_redis para nuevos desarrollos.
    """
    # Obtén los conceptos vigentes del cliente, normalizados a lower y sin espacios
    conceptos_vigentes = set(
        c.concepto_original.strip().lower()
        for c in MapeoConcepto.objects.filter(cliente=cliente, activo=True)
    )
    
    headers_clasificados = []
    headers_sin_clasificar = []

    for h in headers:
        if h.strip().lower() in conceptos_vigentes:
            headers_clasificados.append(h)
        else:
            headers_sin_clasificar.append(h)

    logger.info(
        f"Clasificación automática: {len(headers_clasificados)} clasificados, {len(headers_sin_clasificar)} sin clasificar"
    )
    return headers_clasificados, headers_sin_clasificar

# ========== HELPER TASK: EXTRAER CIERRE_ID ==========

@shared_task(name='nomina.extraer_cierre_id')
def extraer_cierre_id(resultado_anterior):
    """
    Tarea helper para extraer cierre_id del resultado de analizar_headers_libro.
    
    Args:
        resultado_anterior: Dict resultado de analizar_headers_libro
        
    Returns:
        int: cierre_id extraído
    """
    if isinstance(resultado_anterior, dict) and 'cierre_id' in resultado_anterior:
        return resultado_anterior['cierre_id']
    else:
        # Si no es dict o no tiene cierre_id, asumir que ya es el cierre_id
        return resultado_anterior

# ========== CHAIN FACTORY ==========

def crear_chain_procesamiento_libro(cierre_id, archivo_data, filename):
    """
    Crea el chain de procesamiento inicial de libro de remuneraciones.
    
    Chain: analizar_headers_libro → extraer_cierre_id
    
    NOTA: procesar_empleados_libro se ejecuta por separado cuando el usuario hace click en "Procesar"
    
    Args:
        cierre_id: ID del cierre
        archivo_data: Datos del archivo
        filename: Nombre del archivo
    
    Returns:
        Celery chain ready to execute
    """
    return chain(
        analizar_headers_libro.s(cierre_id, archivo_data, filename),
        extraer_cierre_id.s()  # Extrae solo cierre_id del resultado
        # procesar_empleados_libro.s() se ejecuta por separado via endpoint /procesar/
    )

# ========== TASK DE LIMPIEZA ==========

@shared_task(name='nomina.limpiar_archivos_temporales')
def limpiar_archivos_temporales():
    """
    Tarea periódica para limpiar archivos temporales expirados.
    """
    logger.info("🧹 Iniciando limpieza de archivos temporales")
    
    try:
        cache = CacheNominaSGM()
        archivos_limpiados = cache.limpiar_archivos_expirados()
        
        logger.info(f"✅ Limpieza completada: {archivos_limpiados} archivos eliminados")
        return {'archivos_limpiados': archivos_limpiados}
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de archivos: {e}")
        return {'error': str(e)}
