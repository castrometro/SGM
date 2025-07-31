"""
🚀 LibroRemuneracionesOptimizado.py
Utilidades optimizadas para procesar Libro de Remuneraciones usando Celery Chord.
Esta versión divide el procesamiento en chunks paralelos para mejor rendimiento.
"""

import pandas as pd
import logging
from django.db import transaction
from nomina.models import (
    ConceptoRemuneracion, 
    LibroRemuneracionesUpload, 
    EmpleadoCierre, 
    RegistroConceptoEmpleado
)

logger = logging.getLogger(__name__)


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


def dividir_dataframe_empleados(archivo_path, chunk_size):
    """
    🔀 Divide el DataFrame en chunks para procesamiento paralelo.
    
    Args:
        archivo_path: Ruta al archivo Excel
        chunk_size: Tamaño de cada chunk
        
    Returns:
        List[Dict]: Lista de chunks con metadatos
    """
    logger.info(f"📊 Dividiendo DataFrame en chunks de tamaño {chunk_size}")
    
    df = pd.read_excel(archivo_path, engine="openpyxl")
    
    # Filtrar filas con RUT válido
    expected = {
        "rut_trabajador": "Rut del Trabajador",
    }
    
    if expected["rut_trabajador"] not in df.columns:
        raise ValueError(f"Falta columna {expected['rut_trabajador']} en el Excel")
    
    # Pre-filtrar filas válidas
    primera_col = df.columns[0]
    filas_validas = []
    
    for idx, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        
        rut_raw = row.get(expected["rut_trabajador"])
        if not _es_rut_valido(rut_raw):
            continue
            
        filas_validas.append(idx)
    
    logger.info(f"✅ {len(filas_validas)} filas válidas de {len(df)} total")
    
    # Crear chunks
    chunks = []
    total_chunks = len(filas_validas) // chunk_size + (1 if len(filas_validas) % chunk_size > 0 else 0)
    
    for i in range(0, len(filas_validas), chunk_size):
        chunk_indices = filas_validas[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        
        chunks.append({
            'chunk_id': chunk_num,
            'total_chunks': total_chunks,
            'indices': chunk_indices,
            'size': len(chunk_indices)
        })
    
    logger.info(f"🔀 DataFrame dividido en {len(chunks)} chunks")
    return chunks


def procesar_chunk_empleados_util(libro_id, chunk_data):
    """
    👥 Procesa un chunk específico de empleados.
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento
    """
    chunk_id = chunk_data['chunk_id']
    logger.info(f"👥 Procesando chunk de empleados {chunk_id}/{chunk_data['total_chunks']}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_empresa": "Rut de la Empresa",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }
        
        missing = [v for v in expected.values() if v not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas en el Excel: {', '.join(missing)}")
        
        cierre = libro.cierre
        count = 0
        errores = []
        
        # Procesar solo las filas de este chunk
        chunk_indices = chunk_data['indices']
        chunk_df = df.iloc[chunk_indices]
        
        with transaction.atomic():
            for _, row in chunk_df.iterrows():
                try:
                    rut = str(row.get(expected["rut_trabajador"])).strip()
                    defaults = {
                        "rut_empresa": str(row.get(expected["rut_empresa"], "")).strip(),
                        "nombre": str(row.get(expected["nombre"], "")).strip(),
                        "apellido_paterno": str(row.get(expected["ape_pat"], "")).strip(),
                        "apellido_materno": str(row.get(expected["ape_mat"], "")).strip(),
                    }
                    
                    EmpleadoCierre.objects.update_or_create(
                        cierre=cierre,
                        rut=rut,
                        defaults=defaults,
                    )
                    count += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando empleado RUT {rut}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
        
        resultado = {
            'chunk_id': chunk_id,
            'empleados_procesados': count,
            'errores': errores,
            'libro_id': libro_id
        }
        
        logger.info(f"✅ Chunk {chunk_id} completado: {count} empleados procesados")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en chunk {chunk_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_id,
            'empleados_procesados': 0,
            'errores': [error_msg],
            'libro_id': libro_id
        }


def procesar_chunk_registros_util(libro_id, chunk_data):
    """
    📝 Procesa registros de nómina para un chunk específico de empleados.
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento
    """
    chunk_id = chunk_data['chunk_id']
    logger.info(f"📝 Procesando registros para chunk {chunk_id}/{chunk_data['total_chunks']}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_empresa": "Rut de la Empresa",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }
        
        empleado_cols = set(expected.values())
        
        # Obtener headers
        headers = libro.header_json
        if isinstance(headers, dict):
            headers = headers.get("headers_clasificados", []) + headers.get(
                "headers_sin_clasificar", []
            )
        if not headers:
            headers = [h for h in df.columns if h not in empleado_cols]
        
        count = 0
        errores = []
        
        # Procesar solo las filas de este chunk
        chunk_indices = chunk_data['indices']
        chunk_df = df.iloc[chunk_indices]
        
        with transaction.atomic():
            for _, row in chunk_df.iterrows():
                try:
                    rut = str(row.get(expected["rut_trabajador"])).strip()
                    empleado = EmpleadoCierre.objects.filter(
                        cierre=libro.cierre, rut=rut
                    ).first()
                    
                    if not empleado:
                        continue
                    
                    # Procesar todos los headers para este empleado
                    for h in headers:
                        try:
                            valor_raw = row.get(h)
                            
                            # Procesamiento mejorado de valores
                            if pd.isna(valor_raw) or valor_raw == '':
                                valor = ""
                            else:
                                # Si es un número, preservar su precisión original
                                if isinstance(valor_raw, (int, float)):
                                    if isinstance(valor_raw, int) or (isinstance(valor_raw, float) and valor_raw.is_integer()):
                                        valor = str(int(valor_raw))
                                    else:
                                        valor = f"{valor_raw:.2f}".rstrip('0').rstrip('.')
                                else:
                                    # Para strings, limpiar y validar
                                    valor = str(valor_raw).strip()
                                    if valor.lower() == 'nan':
                                        valor = ""
                                    elif valor:
                                        # Intentar limpiar formato monetario si existe
                                        valor_limpio = valor.replace('$', '').replace(',', '').replace('.', '').strip()
                                        try:
                                            numero = float(valor_limpio) if '.' in valor else int(valor_limpio)
                                            if isinstance(numero, int) or numero.is_integer():
                                                valor = str(int(numero))
                                            else:
                                                valor = f"{numero:.2f}".rstrip('0').rstrip('.')
                                        except (ValueError, TypeError):
                                            pass
                            
                            concepto = ConceptoRemuneracion.objects.filter(
                                cliente=libro.cierre.cliente, nombre_concepto=h, vigente=True
                            ).first()
                            
                            RegistroConceptoEmpleado.objects.update_or_create(
                                empleado=empleado,
                                nombre_concepto_original=h,
                                defaults={"monto": valor, "concepto": concepto},
                            )
                            
                        except Exception as concepto_error:
                            error_msg = f"Error en concepto '{h}' para RUT {rut}: {str(concepto_error)}"
                            errores.append(error_msg)
                            logger.error(error_msg)
                    
                    count += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando registros para RUT {rut}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
        
        resultado = {
            'chunk_id': chunk_id,
            'registros_procesados': count,
            'errores': errores,
            'libro_id': libro_id
        }
        
        logger.info(f"✅ Chunk registros {chunk_id} completado: {count} empleados procesados")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en chunk registros {chunk_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_id,
            'registros_procesados': 0,
            'errores': [error_msg],
            'libro_id': libro_id
        }


def consolidar_stats_empleados(resultados_chunks):
    """
    📊 Consolida las estadísticas de procesamiento de empleados de todos los chunks.
    
    Args:
        resultados_chunks: Lista de resultados de cada chunk
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    logger.info("📊 Consolidando estadísticas de empleados...")
    
    total_empleados = 0
    total_errores = []
    chunks_exitosos = 0
    libro_id = None
    
    for resultado in resultados_chunks:
        if isinstance(resultado, dict):
            total_empleados += resultado.get('empleados_procesados', 0)
            total_errores.extend(resultado.get('errores', []))
            
            if resultado.get('empleados_procesados', 0) > 0:
                chunks_exitosos += 1
            
            if not libro_id and resultado.get('libro_id'):
                libro_id = resultado['libro_id']
    
    consolidado = {
        'libro_id': libro_id,
        'total_empleados_procesados': total_empleados,
        'chunks_exitosos': chunks_exitosos,
        'total_chunks': len(resultados_chunks),
        'total_errores': len(total_errores),
        'errores': total_errores[:10],  # Limitar errores para logging
        'procesamiento_exitoso': len(total_errores) == 0
    }
    
    logger.info(f"✅ Consolidación empleados completada: {total_empleados} empleados, {chunks_exitosos}/{len(resultados_chunks)} chunks exitosos")
    
    return consolidado


def consolidar_stats_registros(resultados_chunks):
    """
    📊 Consolida las estadísticas de procesamiento de registros de todos los chunks.
    
    Args:
        resultados_chunks: Lista de resultados de cada chunk
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    logger.info("📊 Consolidando estadísticas de registros...")
    
    total_registros = 0
    total_errores = []
    chunks_exitosos = 0
    libro_id = None
    
    for resultado in resultados_chunks:
        if isinstance(resultado, dict):
            total_registros += resultado.get('registros_procesados', 0)
            total_errores.extend(resultado.get('errores', []))
            
            if resultado.get('registros_procesados', 0) > 0:
                chunks_exitosos += 1
            
            if not libro_id and resultado.get('libro_id'):
                libro_id = resultado['libro_id']
    
    consolidado = {
        'libro_id': libro_id,
        'total_registros_procesados': total_registros,
        'chunks_exitosos': chunks_exitosos,
        'total_chunks': len(resultados_chunks),
        'total_errores': len(total_errores),
        'errores': total_errores[:10],  # Limitar errores para logging
        'procesamiento_exitoso': len(total_errores) == 0
    }
    
    logger.info(f"✅ Consolidación registros completada: {total_registros} registros, {chunks_exitosos}/{len(resultados_chunks)} chunks exitosos")
    
    return consolidado
