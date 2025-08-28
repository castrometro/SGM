"""
Tasks especializadas para el procesamiento de archivos de nombres en inglés.
Implementa Celery Chains para robustez, escalabilidad y mantenimiento.

Flujo del Chain:
1. validar_nombre_archivo_nombres_ingles: Valida que el nombre del archivo sea correcto
2. verificar_archivo_nombres_ingles: Verifica que el archivo exista y no esté vacío
3. validar_contenido_nombres_ingles: Valida la estructura y contenido del Excel
4. procesar_nombres_ingles_raw: Procesa y almacena los nombres en inglés
5. finalizar_procesamiento_nombres_ingles: Marca como completado y limpia archivos temporales

Cada task del chain recibe y retorna únicamente el upload_log_id para mantener
la cadena de procesamiento robusta y escalable.
"""

import os
import hashlib
import pandas as pd
import re
from django.utils import timezone
from django.core.files.storage import default_storage
from celery import shared_task, chain
from celery.utils.log import get_task_logger

from .models import UploadLog, NombreIngles

logger = get_task_logger(__name__)


# =============================================================================
# CHAIN PRINCIPAL
# =============================================================================

def crear_chain_nombres_ingles(upload_log_id):
    """
    Crea y retorna el chain de tasks para procesar nombres en inglés.
    
    Args:
        upload_log_id (int): ID del UploadLog creado
        
    Returns:
        celery.chain: Chain configurado con todas las tasks
    """
    return chain(
        validar_nombre_archivo_nombres_ingles.s(upload_log_id),
        verificar_archivo_nombres_ingles.s(),
        validar_contenido_nombres_ingles.s(),
        procesar_nombres_ingles_raw.s(),
        finalizar_procesamiento_nombres_ingles.s()
    )


# =============================================================================
# TASKS DEL CHAIN
# =============================================================================

@shared_task(bind=True)
def validar_nombre_archivo_nombres_ingles(self, upload_log_id):
    """
    Task 1: Valida que el nombre del archivo sea apropiado para nombres en inglés.
    
    Args:
        upload_log_id (int): ID del UploadLog
        
    Returns:
        int: upload_log_id para continuar el chain
        
    Raises:
        Exception: Si el nombre del archivo no es válido
    """
    logger.info(f"Iniciando validación de nombre de archivo para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        error_msg = f"UploadLog con id {upload_log_id} no encontrado"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Actualizar estado
    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    
    # Obtener nombre del archivo original
    nombre_archivo = upload_log.nombre_archivo_original
    if not nombre_archivo:
        error_msg = "No se encontró el nombre del archivo original"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Validar extensión
    if not nombre_archivo.lower().endswith(('.xlsx', '.xls')):
        error_msg = f"Formato de archivo no soportado: {nombre_archivo}. Solo se aceptan archivos Excel (.xlsx, .xls)"
        upload_log.estado = "error" 
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Validar que no contenga caracteres especiales problemáticos
    caracteres_problematicos = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in nombre_archivo for char in caracteres_problematicos):
        error_msg = f"El nombre del archivo contiene caracteres no permitidos: {nombre_archivo}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    logger.info(f"Nombre de archivo validado correctamente: {nombre_archivo}")
    return upload_log_id


@shared_task(bind=True)
def verificar_archivo_nombres_ingles(self, upload_log_id):
    """
    Task 2: Verifica que el archivo exista, sea accesible y no esté vacío.
    
    Args:
        upload_log_id (int): ID del UploadLog
        
    Returns:
        int: upload_log_id para continuar el chain
        
    Raises:
        Exception: Si el archivo no existe o no es accesible
    """
    logger.info(f"Verificando archivo para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        error_msg = f"UploadLog con id {upload_log_id} no encontrado"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Verificar ruta del archivo
    ruta_relativa = upload_log.ruta_archivo
    if not ruta_relativa:
        error_msg = "No se encontró la ruta del archivo en el upload_log"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    try:
        ruta_completa = default_storage.path(ruta_relativa)
    except Exception as e:
        error_msg = f"Error obteniendo ruta completa del archivo: {str(e)}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Verificar que el archivo existe
    if not os.path.exists(ruta_completa):
        error_msg = f"El archivo no existe en la ruta: {ruta_completa}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Verificar que el archivo no esté vacío
    try:
        tamaño = os.path.getsize(ruta_completa)
        if tamaño == 0:
            error_msg = "El archivo está vacío (0 bytes)"
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.save()
            logger.error(error_msg)
            raise Exception(error_msg)
    except OSError as e:
        error_msg = f"Error accediendo al archivo: {str(e)}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # Calcular y guardar hash del archivo
    try:
        with open(ruta_completa, 'rb') as f:
            archivo_hash = hashlib.sha256(f.read()).hexdigest()
        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])
        logger.info(f"Hash del archivo calculado: {archivo_hash}")
    except Exception as e:
        logger.warning(f"No se pudo calcular el hash del archivo: {str(e)}")
    
    logger.info(f"Archivo verificado correctamente. Tamaño: {tamaño} bytes")
    return upload_log_id


@shared_task(bind=True)
def validar_contenido_nombres_ingles(self, upload_log_id):
    """
    Task 3: Valida la estructura y contenido del archivo Excel de nombres en inglés.
    
    Args:
        upload_log_id (int): ID del UploadLog
        
    Returns:
        int: upload_log_id para continuar el chain
        
    Raises:
        Exception: Si el contenido del archivo no es válido
    """
    logger.info(f"Validando contenido del archivo para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        error_msg = f"UploadLog con id {upload_log_id} no encontrado"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    ruta_completa = default_storage.path(upload_log.ruta_archivo)
    
    # Ejecutar validación completa
    validacion = _validar_archivo_nombres_ingles_excel(ruta_completa)
    
    # Guardar resultados de validación en el resumen
    resumen_actual = upload_log.resumen or {}
    resumen_actual.update({
        'validacion': validacion,
        'hash_archivo': upload_log.hash_archivo
    })
    upload_log.resumen = resumen_actual
    upload_log.save(update_fields=["resumen"])
    
    # Si no es válido, marcar como error
    if not validacion['es_valido']:
        error_msg = "Archivo inválido: " + "; ".join(validacion['errores'])
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.error(f"Validación falló: {error_msg}")
        raise Exception(error_msg)
    
    logger.info(f"Contenido validado correctamente. Estadísticas: {validacion['estadisticas']}")
    return upload_log_id


@shared_task(bind=True)
def procesar_nombres_ingles_raw(self, upload_log_id):
    """
    Task 4: Procesa el archivo y almacena los nombres en inglés en la base de datos.
    
    Args:
        upload_log_id (int): ID del UploadLog
        
    Returns:
        int: upload_log_id para continuar el chain
        
    Raises:
        Exception: Si hay error en el procesamiento
    """
    logger.info(f"Procesando nombres en inglés para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        error_msg = f"UploadLog con id {upload_log_id} no encontrado"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    ruta_completa = default_storage.path(upload_log.ruta_archivo)
    inicio_procesamiento = timezone.now()
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(ruta_completa, skiprows=1, header=None)
        logger.info(f"Archivo Excel leído con {len(df)} filas")
        
        # Validar que tenga al menos 2 columnas
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas: código y nombre en inglés")
        
        # Asignar nombres a las columnas
        df.columns = ['cuenta_codigo', 'nombre_ingles'] + [f'col_{i}' for i in range(2, len(df.columns))]
        
        # Limpiar datos
        df = df.dropna(subset=['cuenta_codigo', 'nombre_ingles'])
        df['cuenta_codigo'] = df['cuenta_codigo'].astype(str).str.strip()
        df['nombre_ingles'] = df['nombre_ingles'].astype(str).str.strip()
        
        # Filtrar filas vacías o inválidas
        df = df[
            (df['cuenta_codigo'] != '') & 
            (df['cuenta_codigo'] != 'nan') & 
            (df['nombre_ingles'] != '') & 
            (df['nombre_ingles'] != 'nan')
        ]
        
        # Eliminar nombres en inglés previos del cliente
        eliminados = NombreIngles.objects.filter(cliente=upload_log.cliente).count()
        NombreIngles.objects.filter(cliente=upload_log.cliente).delete()
        logger.info(f"Eliminados {eliminados} nombres en inglés previos del cliente")
        
        # Eliminar duplicados manteniendo el último registro de cada código
        df = df.drop_duplicates(subset=['cuenta_codigo'], keep='last')
        
        # Procesar cada fila
        creados = 0
        errores = []
        
        for idx, row in df.iterrows():
            try:
                NombreIngles.objects.update_or_create(
                    cliente=upload_log.cliente,
                    cuenta_codigo=row['cuenta_codigo'],
                    defaults={'nombre_ingles': row['nombre_ingles']}
                )
                creados += 1
            except Exception as e:
                error_msg = f"Fila {idx + 3}: {str(e)}"
                errores.append(error_msg)
                logger.warning(error_msg)
        
        # Actualizar resumen con resultados del procesamiento
        resumen_actual = upload_log.resumen or {}
        resumen_actual.update({
            'procesamiento': {
                'total_filas': len(df),
                'nombres_creados': creados,
                'nombres_eliminados_previos': eliminados,
                'errores_count': len(errores),
                'errores': errores[:10] if errores else []  # Solo primeros 10 errores
            }
        })
        
        upload_log.resumen = resumen_actual
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.save(update_fields=["resumen", "tiempo_procesamiento"])
        
        if errores:
            upload_log.errores = "\n".join(errores[:10])
            upload_log.save(update_fields=["errores"])
        
        logger.info(f"Procesamiento completado: {creados} nombres creados, {len(errores)} errores")
        return upload_log_id
        
    except Exception as e:
        error_msg = f"Error en procesamiento: {str(e)}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.save()
        logger.exception("Error en procesamiento de nombres en inglés")
        raise Exception(error_msg)


@shared_task(bind=True)
def finalizar_procesamiento_nombres_ingles(self, upload_log_id):
    """
    Task 5: Marca el procesamiento como completado y limpia archivos temporales.
    
    Args:
        upload_log_id (int): ID del UploadLog
        
    Returns:
        str: Mensaje de finalización exitosa
    """
    logger.info(f"Finalizando procesamiento para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        error_msg = f"UploadLog con id {upload_log_id} no encontrado"
        logger.error(error_msg)
        return error_msg
    
    try:
        # Marcar como completado
        upload_log.estado = "completado"
        upload_log.save(update_fields=["estado"])
        
        # Limpiar archivo temporal
        ruta_completa = default_storage.path(upload_log.ruta_archivo)
        if os.path.exists(ruta_completa):
            try:
                os.remove(ruta_completa)
                logger.info(f"Archivo temporal eliminado: {ruta_completa}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")
        
        # Obtener estadísticas finales del resumen
        resumen = upload_log.resumen or {}
        procesamiento = resumen.get('procesamiento', {})
        nombres_creados = procesamiento.get('nombres_creados', 0)
        errores_count = procesamiento.get('errores_count', 0)
        
        mensaje_final = f"Procesamiento de nombres en inglés completado: {nombres_creados} nombres procesados"
        if errores_count > 0:
            mensaje_final += f", {errores_count} errores"
        
        logger.info(mensaje_final)
        return mensaje_final
        
    except Exception as e:
        error_msg = f"Error en finalización: {str(e)}"
        upload_log.estado = "error"
        upload_log.errores = error_msg
        upload_log.save()
        logger.exception("Error finalizando procesamiento de nombres en inglés")
        return error_msg


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _validar_archivo_nombres_ingles_excel(ruta_archivo):
    """
    Valida un archivo Excel de nombres en inglés.
    
    Args:
        ruta_archivo (str): Ruta completa al archivo Excel
        
    Returns:
        dict: Resultado de validación con estructura:
            - es_valido (bool)
            - errores (list)
            - advertencias (list)
            - estadisticas (dict)
    """
    errores = []
    advertencias = []
    
    # Verificar existencia y tamaño del archivo
    if not os.path.exists(ruta_archivo):
        errores.append("El archivo no existe en la ruta especificada")
        return {
            "es_valido": False,
            "errores": errores,
            "advertencias": advertencias,
            "estadisticas": {}
        }
    
    if os.path.getsize(ruta_archivo) == 0:
        errores.append("El archivo está vacío (0 bytes)")
        return {
            "es_valido": False,
            "errores": errores,
            "advertencias": advertencias,
            "estadisticas": {}
        }
    
    # Leer archivo Excel
    try:
        df = pd.read_excel(ruta_archivo, skiprows=1, header=None)
    except Exception as e:
        errores.append(f"Error leyendo el archivo Excel: {str(e)}")
        return {
            "es_valido": False,
            "errores": errores,
            "advertencias": advertencias,
            "estadisticas": {}
        }
    
    # Validar contenido básico
    if len(df) == 0:
        errores.append("El archivo no contiene filas de datos")
        return {
            "es_valido": False,
            "errores": errores,
            "advertencias": advertencias,
            "estadisticas": {}
        }
    
    if len(df.columns) < 2:
        errores.append("El archivo debe tener al menos 2 columnas: código y nombre en inglés")
        return {
            "es_valido": False,
            "errores": errores,
            "advertencias": advertencias,
            "estadisticas": {}
        }
    
    # Validar datos en columnas
    col_codigo = df.columns[0]
    col_nombre = df.columns[1]
    
    codigos_vacios = 0
    codigos_duplicados = []
    codigos_invalidos = []
    codigos_vistos = set()
    
    # Patrón para validar códigos de cuenta (números y guiones)
    patron_codigo = r'^[\d\-]+$'
    
    for idx, codigo in df[col_codigo].items():
        fila = idx + 2  # +2 porque skiprows=1 y las filas empiezan en 1
        
        if pd.isna(codigo) or str(codigo).strip() == '':
            codigos_vacios += 1
            continue
            
        codigo_str = str(codigo).strip()
        
        # Validar formato del código
        if not re.match(patron_codigo, codigo_str):
            codigos_invalidos.append(f"Fila {fila}: '{codigo_str}'")
            continue
            
        # Verificar duplicados
        if codigo_str in codigos_vistos:
            codigos_duplicados.append(f"Fila {fila}: '{codigo_str}'")
        codigos_vistos.add(codigo_str)
    
    # Contar nombres vacíos
    nombres_vacios = int(df[col_nombre].apply(
        lambda x: pd.isna(x) or str(x).strip() == ''
    ).sum())
    
    # Reportar errores críticos
    if codigos_invalidos:
        errores.append(
            f"Códigos con formato inválido ({len(codigos_invalidos)}): "
            f"{', '.join(codigos_invalidos[:3])}"
        )
    
    if codigos_duplicados:
        errores.append(
            f"Códigos duplicados ({len(codigos_duplicados)}): "
            f"{', '.join(codigos_duplicados[:3])}"
        )
    
    # Preparar estadísticas
    estadisticas = {
        'total_filas': len(df),
        'codigos_vacios': codigos_vacios,
        'codigos_invalidos': len(codigos_invalidos),
        'codigos_duplicados': len(codigos_duplicados),
        'nombres_vacios': nombres_vacios,
    }
    
    # Determinar si es válido
    es_valido = len(errores) == 0 and (len(df) - codigos_vacios) > 0
    
    return {
        'es_valido': es_valido,
        'errores': errores,
        'advertencias': advertencias,
        'estadisticas': estadisticas
    }
