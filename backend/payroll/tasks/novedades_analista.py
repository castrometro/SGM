# backend/payroll/tasks/novedades_analista.py
# Tareas de Celery para procesar archivos de novedades del analista

import pandas as pd
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from ..models.models_fase_1 import ArchivoSubido
from ..models.models_staging import (
    Empleados_Novedades_stg,
    Items_Novedades_stg,
    Valores_item_empleado_analista_stg,
    limpiar_novedades_analista_por_archivo
)
from ..utils.rut_validator import limpiar_rut, validar_rut

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def procesar_novedades_analista(self, archivo_id: int):
    """
    📊 Procesa archivo de novedades del analista con estructura similar al libro de remuneraciones.
    
    Formato esperado:
    Fila 1: Headers (RUT | Nombre | Apellido Paterno | Apellido Materno | Concepto1 | Concepto2 | ...)
    Fila 2+: Datos de empleados y valores
    
    Args:
        archivo_id: ID del archivo a procesar
        
    Returns:
        Dict con estadísticas del procesamiento
    """
    
    logger.info(f"🚀 Iniciando procesamiento de novedades del analista - Archivo ID: {archivo_id}")
    
    try:
        # Obtener el archivo
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        archivo.estado_procesamiento = 'procesando'
        archivo.save()
        
        # Actualizar progreso
        self.update_state(state='PROGRESS', meta={
            'step': 'reading_file',
            'message': 'Leyendo archivo Excel...',
            'progress': 10
        })
        
        # Leer el archivo Excel
        df = pd.read_excel(archivo.archivo.path, engine='openpyxl')
        
        logger.info(f"📋 Archivo leído: {df.shape[0]} filas, {df.shape[1]} columnas")
        
        # Validar estructura básica
        if df.shape[0] < 1:
            raise ValueError("El archivo no tiene suficientes filas de datos")
        
        if df.shape[1] < 4:
            raise ValueError("El archivo debe tener al menos 4 columnas (RUT, Nombre, Apellido Paterno, Apellido Materno)")
        
        # Limpiar datos staging existentes del archivo
        limpiar_novedades_analista_por_archivo(archivo)
        
        # Actualizar progreso
        self.update_state(state='PROGRESS', meta={
            'step': 'processing_headers',
            'message': 'Procesando headers...',
            'progress': 20
        })
        
        # Procesar headers (fila 1)
        headers = df.columns.tolist()
        items_creados = procesar_headers_novedades(archivo, headers)
        
        logger.info(f"📊 Headers procesados: {len(items_creados)} conceptos identificados")
        
        # Actualizar progreso
        self.update_state(state='PROGRESS', meta={
            'step': 'processing_employees',
            'message': 'Procesando empleados...',
            'progress': 40
        })
        
        # Procesar empleados y valores
        empleados_procesados, valores_procesados, errores = procesar_datos_novedades(
            archivo, df, items_creados, self
        )
        
        # Actualizar estadísticas del archivo
        archivo.registros_procesados = empleados_procesados
        archivo.errores_detectados = len(errores)
        archivo.estado_procesamiento = 'completado' if len(errores) == 0 else 'completado_con_errores'
        archivo.fecha_procesamiento = timezone.now()
        
        # Agregar estadísticas a metadatos
        archivo.metadatos = archivo.metadatos or {}
        archivo.metadatos.update({
            'empleados_procesados': empleados_procesados,
            'conceptos_procesados': len(items_creados),
            'valores_procesados': valores_procesados,
            'errores_encontrados': len(errores),
            'fecha_procesamiento': timezone.now().isoformat(),
            'tipo_procesamiento': 'novedades_analista'
        })
        
        if errores:
            archivo.log_errores = '\n'.join([f"Fila {e['fila']}: {e['error']}" for e in errores[:50]])
        
        archivo.save()
        
        logger.info(f"✅ Procesamiento completado - Empleados: {empleados_procesados}, Valores: {valores_procesados}, Errores: {len(errores)}")
        
        return {
            'estado': 'completado',
            'empleados_procesados': empleados_procesados,
            'conceptos_procesados': len(items_creados),
            'valores_procesados': valores_procesados,
            'errores_encontrados': len(errores),
            'archivo_id': archivo_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando archivo {archivo_id}: {str(e)}")
        
        # Actualizar estado del archivo
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_id)
            archivo.estado_procesamiento = 'error'
            archivo.log_errores = f"Error general: {str(e)}"
            archivo.save()
        except:
            pass
        
        # Re-raise para que Celery maneje el error
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'traceback': str(e.__traceback__) if hasattr(e, '__traceback__') else None
            }
        )
        raise


def procesar_headers_novedades(archivo: ArchivoSubido, headers: List[str]) -> Dict[str, Items_Novedades_stg]:
    """
    🏷️ Procesa los headers del archivo de novedades (fila 1).
    
    Args:
        archivo: Instancia del archivo subido
        headers: Lista de headers del Excel
        
    Returns:
        Dict mapeando código de columna a instancia del modelo
    """
    
    logger.info(f"🏷️ Procesando headers de novedades: {len(headers)} columnas")
    
    items_creados = {}
    
    # Mapeo de columnas esperadas (primeras 4 son fijas)
    columnas_empleado = {
        0: 'RUT',
        1: 'Nombre', 
        2: 'Apellido Paterno',
        3: 'Apellido Materno'
    }
    
    for idx, header in enumerate(headers):
        # Limpiar el header
        header_limpio = str(header).strip() if pd.notna(header) else f"Columna_{idx}"
        
        # Determinar el código de columna (A, B, C, ...)
        codigo_columna = chr(65 + idx)  # A=65, B=66, etc.
        
        # Clasificar el tipo de concepto
        if idx < 4:
            # Columnas de datos del empleado - no crear item
            continue
        else:
            # Columnas de conceptos/valores
            tipo_concepto = clasificar_concepto_novedad(header_limpio)
        
        # Crear el item
        item = Items_Novedades_stg.objects.create(
            archivo_subido=archivo,
            codigo_columna=codigo_columna,
            nombre_concepto=header_limpio,
            nombre_normalizado=normalizar_nombre_concepto(header_limpio),
            tipo_concepto=tipo_concepto,
            orden=idx,
            fila_header=1  # Headers en fila 1 para novedades del analista
        )
        
        items_creados[codigo_columna] = item
        
        logger.debug(f"📋 Item creado: [{codigo_columna}] {header_limpio} ({tipo_concepto})")
    
    return items_creados


def procesar_datos_novedades(
    archivo: ArchivoSubido, 
    df: pd.DataFrame, 
    items_creados: Dict[str, Items_Novedades_stg],
    task_instance
) -> Tuple[int, int, List[Dict]]:
    """
    👥 Procesa los datos de empleados y valores del archivo de novedades.
    
    Args:
        archivo: Instancia del archivo subido
        df: DataFrame con los datos
        items_creados: Diccionario de items creados
        task_instance: Instancia de la tarea para actualizar progreso
        
    Returns:
        Tupla (empleados_procesados, valores_procesados, errores)
    """
    
    logger.info(f"👥 Procesando datos de empleados: {len(df)} filas")
    
    empleados_procesados = 0
    valores_procesados = 0
    errores = []
    
    total_filas = len(df)
    
    for idx, fila in df.iterrows():
        fila_excel = idx + 2  # +2 porque idx es 0-based y headers están en fila 1
        
        try:
            # Actualizar progreso cada 50 filas
            if idx % 50 == 0 and task_instance:
                progreso = 40 + int((idx / total_filas) * 50)  # 40-90%
                task_instance.update_state(state='PROGRESS', meta={
                    'step': 'processing_data',
                    'message': f'Procesando empleado {idx + 1} de {total_filas}...',
                    'progress': progreso
                })
            
            # Extraer datos del empleado (primeras 4 columnas)
            rut_raw = fila.iloc[0] if len(fila) > 0 else None
            nombre = fila.iloc[1] if len(fila) > 1 else None
            apellido_paterno = fila.iloc[2] if len(fila) > 2 else None  
            apellido_materno = fila.iloc[3] if len(fila) > 3 else None
            
            # Validar datos básicos del empleado
            if pd.isna(rut_raw) or pd.isna(nombre):
                errores.append({
                    'fila': fila_excel,
                    'error': 'RUT o nombre vacío'
                })
                continue
            
            # Limpiar y validar RUT
            rut_limpio = limpiar_rut(str(rut_raw))
            if not rut_limpio or not validar_rut(rut_limpio):
                errores.append({
                    'fila': fila_excel,
                    'error': f'RUT inválido: {rut_raw}'
                })
                continue
            
            # Crear el empleado
            with transaction.atomic():
                empleado, creado = Empleados_Novedades_stg.objects.get_or_create(
                    archivo_subido=archivo,
                    rut_trabajador=rut_limpio,
                    defaults={
                        'nombre': str(nombre).strip(),
                        'apellido_paterno': str(apellido_paterno).strip() if pd.notna(apellido_paterno) else '',
                        'apellido_materno': str(apellido_materno).strip() if pd.notna(apellido_materno) else '',
                        'fila_excel': fila_excel
                    }
                )
                
                if creado:
                    empleados_procesados += 1
                    logger.debug(f"👤 Empleado creado: {rut_limpio} - {nombre}")
                
                # Procesar valores (columnas 5 en adelante)
                for col_idx in range(4, len(fila)):
                    codigo_columna = chr(65 + col_idx)  # E, F, G, ...
                    
                    if codigo_columna not in items_creados:
                        continue
                    
                    valor_raw = fila.iloc[col_idx]
                    
                    # Saltar valores vacíos
                    if pd.isna(valor_raw) or str(valor_raw).strip() == '':
                        continue
                    
                    # Procesar el valor
                    valor_original = str(valor_raw).strip()
                    valor_numerico, valor_texto, es_numerico = procesar_valor_novedad(valor_original)
                    
                    # Crear el valor
                    Valores_item_empleado_analista_stg.objects.create(
                        archivo_subido=archivo,
                        empleado=empleado,
                        item_novedad=items_creados[codigo_columna],
                        valor_original=valor_original,
                        valor_numerico=valor_numerico,
                        valor_texto=valor_texto,
                        es_numerico=es_numerico,
                        fila_excel=fila_excel,
                        columna_excel=codigo_columna
                    )
                    
                    valores_procesados += 1
                    
        except Exception as e:
            logger.error(f"❌ Error procesando fila {fila_excel}: {str(e)}")
            errores.append({
                'fila': fila_excel,
                'error': f'Error general: {str(e)}'
            })
    
    logger.info(f"✅ Procesamiento completado: {empleados_procesados} empleados, {valores_procesados} valores, {len(errores)} errores")
    
    return empleados_procesados, valores_procesados, errores


def clasificar_concepto_novedad(nombre_concepto: str) -> str:
    """
    🏷️ Clasifica un concepto de novedad según su nombre.
    
    Args:
        nombre_concepto: Nombre del concepto
        
    Returns:
        Tipo de concepto
    """
    
    nombre_lower = nombre_concepto.lower()
    
    # Palabras clave para clasificación
    haberes = ['sueldo', 'gratificacion', 'bono', 'comision', 'premio', 'asignacion', 'sobresueldo', 'horas extras']
    descuentos = ['descuento', 'afc', 'apv', 'prestamo', 'cuota', 'multa', 'retención']
    totales = ['total', 'líquido', 'bruto', 'imponible']
    informativos = ['rut', 'nombre', 'codigo', 'centro', 'cargo']
    
    for palabra in haberes:
        if palabra in nombre_lower:
            return 'haber'
    
    for palabra in descuentos:
        if palabra in nombre_lower:
            return 'descuento'
    
    for palabra in totales:
        if palabra in nombre_lower:
            return 'total'
    
    for palabra in informativos:
        if palabra in nombre_lower:
            return 'informativo'
    
    # Por defecto, clasificar como novedad
    return 'novedad'


def normalizar_nombre_concepto(nombre: str) -> str:
    """
    🔧 Normaliza el nombre de un concepto.
    
    Args:
        nombre: Nombre original del concepto
        
    Returns:
        Nombre normalizado
    """
    
    import re
    
    # Limpiar caracteres especiales y espacios múltiples
    nombre_limpio = re.sub(r'[^\w\s-]', ' ', nombre)
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)
    
    return nombre_limpio.strip().title()


def procesar_valor_novedad(valor_str: str) -> Tuple[Optional[Decimal], str, bool]:
    """
    💰 Procesa un valor de novedad, determinando si es numérico o texto.
    
    Args:
        valor_str: Valor como string
        
    Returns:
        Tupla (valor_numerico, valor_texto, es_numerico)
    """
    
    # Limpiar el valor
    valor_limpio = str(valor_str).strip()
    
    # Intentar convertir a número
    # Remover caracteres no numéricos comunes
    valor_para_numero = valor_limpio.replace('.', '').replace(',', '.').replace('$', '').replace(' ', '')
    valor_para_numero = ''.join(c for c in valor_para_numero if c.isdigit() or c in '.-')
    
    try:
        if valor_para_numero:
            valor_numerico = Decimal(valor_para_numero)
            return valor_numerico, valor_limpio, True
    except (ValueError, InvalidOperation):
        pass
    
    # Si no es numérico, almacenar como texto
    return None, valor_limpio, False
