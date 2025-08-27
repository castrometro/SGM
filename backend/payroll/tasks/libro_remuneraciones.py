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
        
        # Procesar cada columna
        for idx, columna in enumerate(df.columns):
            # Detectar tipo de concepto
            tipo_concepto = detectar_tipo_concepto(str(columna))
            
            # Crear registro
            header = ItemsRemuneraciones_stg.objects.create(
                archivo_subido=archivo,
                codigo_columna=_get_excel_column_name(idx),
                nombre_concepto=str(columna),
                nombre_normalizado=normalizar_concepto(str(columna)),
                tipo_concepto=tipo_concepto,
                orden=idx,
                fila_header=1
            )
        
        headers_count = ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo).count()
        logger.info(f"✅ Headers extraídos: {headers_count} conceptos")
        return archivo_subido_id  # Retornar ID para la siguiente tarea en CHAIN
        
    except Exception as e:
        error_msg = f"❌ Error extrayendo headers: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def extraer_empleados_task(self, resultado_anterior, archivo_subido_id):
    """
    Extrae la lista de empleados del Excel → ListaEmpleados_stg
    
    CHAIN: Recibe resultado de tarea anterior + archivo_subido_id explícito
    """
    logger.info(f"👥 Extrayendo empleados de archivo {archivo_subido_id}")
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_subido_id)
        
        # LIMPIAR datos previos para evitar duplicados
        ListaEmpleados_stg.objects.filter(archivo_subido=archivo).delete()
        logger.info(f"🧹 Empleados previos eliminados para archivo {archivo_subido_id}")
        
        # Leer Excel (saltando header)
        df = pd.read_excel(archivo.archivo.path, header=0)
        
        # Asumir que las primeras columnas son: RUT, Nombre, Apellido Paterno, Apellido Materno
        for idx, row in df.iterrows():
            # Obtener datos básicos (ajustar según estructura real del Excel)
            rut = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
            nombre = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ""
            apellido_pat = str(row.iloc[2]) if not pd.isna(row.iloc[2]) else ""
            apellido_mat = str(row.iloc[3]) if len(row) > 3 and not pd.isna(row.iloc[3]) else ""
            
            # Validar RUT básico
            rut_limpio = limpiar_rut(rut)
            if not rut_limpio:
                continue
            
            # Crear registro
            empleado = ListaEmpleados_stg.objects.create(
                archivo_subido=archivo,
                rut_trabajador=rut_limpio,
                nombre=nombre,
                apellido_paterno=apellido_pat,
                apellido_materno=apellido_mat,
                fila_excel=idx + 2  # +2 porque pandas es 0-indexed y hay header
            )
        
        empleados_count = ListaEmpleados_stg.objects.filter(archivo_subido=archivo).count()
        logger.info(f"✅ Empleados extraídos: {empleados_count}")
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
