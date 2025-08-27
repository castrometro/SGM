# backend/payroll/tasks/libro_remuneraciones.py
# Tareas Celery para procesar libros de remuneraciones con patrón CHAIN

from celery import shared_task, chain
from celery.exceptions import Retry
from django.db import transaction
import pandas as pd
import logging
from decimal import Decimal, InvalidOperation
import re

from ..models.models_fase_1 import ArchivoSubido
from ..models.models_staging import (
    ListaEmpleados_stg, 
    ItemsRemuneraciones_stg, 
    ValorItemEmpleado_stg,
    limpiar_staging_por_archivo
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def procesar_libro_remuneraciones(self, archivo_subido_id):
    """
    Tarea principal que orquesta el procesamiento usando patrón CHAIN.
    
    FLUJO SECUENCIAL:
    1. Headers → 2. Empleados → 3. Valores
    """
    logger.info(f"🚀 Iniciando procesamiento CHAIN de archivo {archivo_subido_id}")
    
    try:
        # Obtener archivo y cambiar estado
        archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
        archivo.estado_procesamiento = 'parseando'
        archivo.save()
        
        # Limpiar datos staging previos (si existen)
        limpiar_staging_por_archivo(archivo)
        
        logger.info(f"📋 Estado cambiado a 'parseando' para archivo {archivo_subido_id}")
        
        # CHAIN: Procesamiento secuencial
        result = chain(
            extraer_headers_task.s(archivo_subido_id),
            extraer_empleados_task.s(archivo_subido_id),
            extraer_valores_task.s(archivo_subido_id)
        ).apply_async()
        
        logger.info(f"🔗 CHAIN iniciado para archivo {archivo_subido_id}")
        return f"CHAIN iniciado para archivo {archivo_subido_id}"
        
    except ArchivoSubido.DoesNotExist:
        error_msg = f"❌ Archivo {archivo_subido_id} no encontrado"
        logger.error(error_msg)
        raise Exception(error_msg)
        
    except Exception as e:
        # Marcar como error en caso de falla
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        error_msg = f"❌ Error en procesamiento: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def extraer_headers_task(self, archivo_subido_id):
    """
    Extrae los headers/conceptos del Excel → ItemsRemuneraciones_stg
    FORMATO REAL: Headers de empleados A-D, Items remuneraciones desde H
    
    INDEPENDIENTE: No depende de otros tasks
    """
    logger.info(f"📋 Extrayendo headers de archivo {archivo_subido_id}")
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
        
        # LIMPIAR datos previos para evitar duplicados
        ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo).delete()
        logger.info(f"🧹 Headers previos eliminados para archivo {archivo_subido_id}")
        
        # Leer Excel (solo primera fila para headers)
        df = pd.read_excel(archivo.archivo.path, header=0, nrows=1)
        
        # Headers de empleados esperados (columnas A-D aprox)
        headers_empleados = [
            'Rut del Trabajador', 'Nombre', 'Apellido Paterno', 'Apellido Materno'
        ]
        
        empleados_count = 0
        remuneraciones_count = 0
        
        # Procesar cada columna
        for idx, columna in enumerate(df.columns):
            columna_str = str(columna).strip()
            codigo_columna = _get_excel_column_name(idx)
            
            # Determinar si es header de empleado o item de remuneración
            es_header_empleado = any(
                emp_header.lower() in columna_str.lower() 
                for emp_header in headers_empleados
            )
            
            # Items de remuneraciones desde columna H (índice 7)
            es_item_remuneracion = idx >= 7  # Columna H = índice 7
            
            # Asignar tipo basado en posición y contenido
            if es_header_empleado:
                tipo_asignado = 'empleado'
                empleados_count += 1
            elif es_item_remuneracion:
                tipo_asignado = None  # Se clasificará posteriormente
                remuneraciones_count += 1
            else:
                tipo_asignado = None  # Otras columnas
            
            # Crear registro
            header = ItemsRemuneraciones_stg.objects.create(
                archivo_subido=archivo,
                codigo_columna=codigo_columna,
                nombre_concepto=columna_str,
                nombre_normalizado=normalizar_concepto(columna_str),
                tipo_concepto=tipo_asignado,
                orden=idx,
                fila_header=1
            )
        
        headers_count = ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo).count()
        logger.info(f"✅ Headers extraídos: {headers_count} conceptos")
        logger.info(f"👥 Headers empleados: {empleados_count}")
        logger.info(f"💰 Items remuneraciones: {remuneraciones_count}")
        return archivo_subido_id  # Retornar ID para la siguiente tarea en CHAIN
        
    except Exception as e:
        error_msg = f"❌ Error extrayendo headers: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def extraer_empleados_task(self, resultado_anterior, archivo_subido_id):
    """
    Extrae la lista de empleados del Excel → ListaEmpleados_stg
    FORMATO REAL: Valida empleados con datos completos en headers específicos
    
    CHAIN: Recibe resultado de tarea anterior + archivo_subido_id explícito
    """
    logger.info(f"👥 Extrayendo empleados de archivo {archivo_subido_id}")
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
        
        # LIMPIAR datos previos para evitar duplicados
        ListaEmpleados_stg.objects.filter(archivo_subido=archivo).delete()
        logger.info(f"🧹 Empleados previos eliminados para archivo {archivo_subido_id}")
        
        # Obtener headers de empleados (tipo_concepto = 'empleado')
        headers_empleados = ItemsRemuneraciones_stg.objects.filter(
            archivo_subido=archivo,
            tipo_concepto='empleado'
        ).order_by('orden')
        
        if headers_empleados.count() < 4:
            raise Exception(f"❌ Se esperan al menos 4 headers de empleados, encontrados: {headers_empleados.count()}")
        
        # Mapear headers por contenido esperado
        header_map = {}
        for header in headers_empleados:
            nombre_lower = header.nombre_concepto.lower()
            if 'rut' in nombre_lower:
                header_map['rut'] = header.orden
            elif 'nombre' in nombre_lower and 'apellido' not in nombre_lower:
                header_map['nombre'] = header.orden
            elif 'paterno' in nombre_lower:
                header_map['apellido_paterno'] = header.orden
            elif 'materno' in nombre_lower:
                header_map['apellido_materno'] = header.orden
        
        logger.info(f"📋 Headers mapeados: {header_map}")
        
        # Leer Excel (saltando header)
        df = pd.read_excel(archivo.archivo.path, header=0)
        
        empleados_validos = 0
        empleados_omitidos = 0
        
        for idx, row in df.iterrows():
            # Extraer datos usando el mapeo de headers
            rut = str(row.iloc[header_map.get('rut', 0)]) if 'rut' in header_map and not pd.isna(row.iloc[header_map['rut']]) else ""
            nombre = str(row.iloc[header_map.get('nombre', 1)]) if 'nombre' in header_map and not pd.isna(row.iloc[header_map['nombre']]) else ""
            apellido_pat = str(row.iloc[header_map.get('apellido_paterno', 2)]) if 'apellido_paterno' in header_map and not pd.isna(row.iloc[header_map['apellido_paterno']]) else ""
            apellido_mat = str(row.iloc[header_map.get('apellido_materno', 3)]) if 'apellido_materno' in header_map and not pd.isna(row.iloc[header_map['apellido_materno']]) else ""
            
            # VALIDACIÓN: Empleado válido = datos completos en los 4 campos
            rut_limpio = limpiar_rut(rut)
            if not rut_limpio or not nombre or not apellido_pat or not apellido_mat:
                empleados_omitidos += 1
                logger.debug(f"⚠️ Empleado omitido fila {idx+2}: RUT={rut_limpio}, Nombre={nombre}, Pat={apellido_pat}, Mat={apellido_mat}")
                continue
            
            # Crear registro de empleado válido
            empleado = ListaEmpleados_stg.objects.create(
                archivo_subido=archivo,
                rut=rut_limpio,
                nombre=nombre.strip(),
                apellido_paterno=apellido_pat.strip(),
                apellido_materno=apellido_mat.strip(),
                numero_fila=idx + 2  # +2 porque pandas usa 0-index y hay header
            )
            empleados_validos += 1
        
        logger.info(f"✅ Empleados válidos procesados: {empleados_validos}")
        logger.info(f"⚠️ Empleados omitidos por datos incompletos: {empleados_omitidos}")
        return archivo_subido_id  # Retornar ID para la siguiente tarea en CHAIN
        
    except Exception as e:
        error_msg = f"❌ Error extrayendo empleados: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def extraer_valores_task(self, resultado_anterior, archivo_subido_id):
    """
    Extrae la matriz de valores Empleado x Concepto → ValorItemEmpleado_stg
    
    CHAIN: Recibe resultado de tarea anterior + archivo_subido_id explícito
    """
    logger.info(f"� Iniciando extracción de valores para archivo {archivo_subido_id}")
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
        
        # LIMPIAR datos previos para evitar duplicados
        ValorItemEmpleado_stg.objects.filter(archivo_subido=archivo).delete()
        logger.info(f"🧹 Valores previos eliminados para archivo {archivo_subido_id}")
        
        # Obtener registros staging ya creados por las tareas anteriores
        headers = ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo).order_by('orden')
        empleados = ListaEmpleados_stg.objects.filter(archivo_subido=archivo).order_by('fila_excel')
        
        logger.info(f"📋 Headers disponibles: {headers.count()}")
        logger.info(f"👥 Empleados disponibles: {empleados.count()}")
        
        if not headers.exists() or not empleados.exists():
            raise Exception("No hay headers o empleados en staging")
        
        # Leer Excel completo
        df = pd.read_excel(archivo.archivo.path, header=0)
        
        valores_extraidos = []
        
        # Para cada empleado
        for emp_idx, empleado in enumerate(empleados):
            if emp_idx >= len(df):
                break  # No más filas en el Excel
                
            fila_df = df.iloc[emp_idx]  # Fila correspondiente en el DataFrame
            
            # Para cada concepto/header (saltando las columnas de empleado)
            for header in headers:
                # Mapear código de columna a índice
                col_idx = _get_column_index(header.codigo_columna)
                
                # Saltar columnas de empleado (RUT, Nombre, Apellidos)
                if col_idx < 4:  # Ajustar según estructura real
                    continue
                
                # Verificar que el índice esté dentro del rango
                if col_idx >= len(fila_df):
                    continue
                
                # Obtener valor
                valor_original = str(fila_df.iloc[col_idx]) if not pd.isna(fila_df.iloc[col_idx]) else ""
                
                # Procesar valor
                valor_numerico, es_numerico = procesar_valor(valor_original)
                
                # Crear registro
                valor = ValorItemEmpleado_stg.objects.create(
                    archivo_subido=archivo,
                    empleado=empleado,
                    item_remuneracion=header,
                    valor_original=valor_original,
                    valor_numerico=valor_numerico,
                    valor_texto=valor_original if not es_numerico else "",
                    fila_excel=empleado.fila_excel,
                    columna_excel=header.codigo_columna,
                    es_numerico=es_numerico
                )
                
                valores_extraidos.append({
                    'empleado_rut': empleado.rut_trabajador,
                    'concepto': header.nombre_concepto,
                    'valor': valor_original,
                    'es_numerico': es_numerico
                })
        
        # Actualizar estado final del archivo
        archivo.estado_procesamiento = 'parsing_completo'
        archivo.save()
        
        logger.info(f"✅ Procesamiento CHAIN completo: {len(valores_extraidos)} valores extraídos")
        return archivo_subido_id  # Retornar ID (aunque sea el final del CHAIN)
        
    except Exception as e:
        # Marcar archivo como error
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        error_msg = f"❌ Error extrayendo valores: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# =============================================================================
# UTILIDADES DE PROCESAMIENTO
# =============================================================================

def detectar_tipo_concepto(nombre_concepto):
    """Detecta el tipo de concepto basado en el nombre"""
    nombre_lower = nombre_concepto.lower()
    
    if any(palabra in nombre_lower for palabra in ['descuento', 'desc', 'rebaja', 'multa']):
        return 'descuento'
    elif any(palabra in nombre_lower for palabra in ['total', 'liquido', 'líquido']):
        return 'total'
    elif any(palabra in nombre_lower for palabra in ['sueldo', 'gratif', 'bono', 'haber', 'asignacion']):
        return 'haber'
    else:
        return 'informativo'


def normalizar_concepto(nombre_concepto):
    """Normaliza el nombre del concepto"""
    return re.sub(r'\s+', ' ', nombre_concepto.strip().title())


def limpiar_rut(rut_raw):
    """Limpia y valida RUT"""
    if not rut_raw:
        return ""
    
    # Remover puntos y guiones
    rut_limpio = re.sub(r'[.-]', '', str(rut_raw).strip())
    
    # Formato básico: 8-9 dígitos + dígito verificador
    if len(rut_limpio) >= 8 and len(rut_limpio) <= 10:
        return rut_limpio
    
    return ""


def procesar_valor(valor_str):
    """Procesa un valor del Excel y determina si es numérico"""
    if pd.isna(valor_str) or valor_str == "" or str(valor_str).lower() in ['nan', 'none']:
        return None, False
    
    # Limpiar valor para detección numérica
    valor_limpio = str(valor_str).replace(',', '').replace('$', '').strip()
    
    try:
        # Intentar convertir a decimal
        valor_decimal = Decimal(valor_limpio)
        return valor_decimal, True
    except (InvalidOperation, ValueError):
        return None, False


def _get_excel_column_name(index):
    """Convierte índice numérico a nombre de columna Excel (A, B, C...)"""
    result = ""
    while index >= 0:
        result = chr(index % 26 + ord('A')) + result
        index = index // 26 - 1
    return result


def _get_column_index(column_name):
    """Convierte nombre de columna Excel a índice numérico"""
    result = 0
    for char in column_name:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1
