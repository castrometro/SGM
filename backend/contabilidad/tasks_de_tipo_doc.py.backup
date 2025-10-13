# backend/contabilidad/tasks.py


import datetime
import hashlib
import logging
import os
import re
import time
from datetime import datetime, timedelta, date

import pandas as pd
from celery import shared_task, chain
from django.core.files.base import ContentFile
from contabilidad.models import (
    TipoDocumento,
    CierreContabilidad,
    UploadLog,
    TipoDocumentoArchivo,  # Agregado para definir TipoDocumentoArchivo
)
from api.models import Cliente
from contabilidad.utils.parser_tipo_documento import parsear_tipo_documento_excel
from contabilidad.utils.activity_logger import registrar_actividad_tarjeta
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger(__name__)



def validar_archivo_tipo_documento_excel(ruta_archivo):
    """Valida un Excel de tipos de documento."""
    errores = []
    advertencias = []

    if not os.path.exists(ruta_archivo):
        errores.append("El archivo no existe en la ruta especificada")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}

    if os.path.getsize(ruta_archivo) == 0:
        errores.append("El archivo está vacío (0 bytes)")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}

    try:
        df = pd.read_excel(ruta_archivo)
    except Exception as e:
        errores.append(f"Error leyendo el archivo Excel: {str(e)}")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}

    if len(df) == 0:
        errores.append("El archivo no contiene filas de datos")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}

    if len(df.columns) < 2:
        errores.append("El archivo debe tener al menos 2 columnas: código y descripción")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}

    col_codigo = df.columns[0]
    col_desc = df.columns[1]

    codigos_vacios = 0
    codigos_duplicados = []
    codigos_largos = []
    codigos_vistos = set()

    for idx, codigo in df[col_codigo].items():
        fila = idx + 2
        if pd.isna(codigo) or str(codigo).strip() == "":
            codigos_vacios += 1
            continue
        codigo_str = str(codigo).strip()
        if len(codigo_str) > 10:
            codigos_largos.append(f"Fila {fila}: '{codigo_str}'")
        if codigo_str in codigos_vistos:
            codigos_duplicados.append(f"Fila {fila}: '{codigo_str}'")
        codigos_vistos.add(codigo_str)

    descripciones_vacias = int(
        df[col_desc].apply(lambda x: pd.isna(x) or str(x).strip() == "").sum()
    )

    if codigos_largos:
        errores.append(
            f"Códigos demasiado largos (máximo 10 caracteres): {', '.join(codigos_largos[:3])}"
        )

    if codigos_duplicados:
        errores.append(
            f"Códigos duplicados ({len(codigos_duplicados)}): {', '.join(codigos_duplicados[:3])}"
        )

    estadisticas = {
        "total_filas": len(df),
        "codigos_vacios": codigos_vacios,
        "codigos_duplicados": len(codigos_duplicados),
        "codigos_largos": len(codigos_largos),
        "descripciones_vacias": descripciones_vacias,
    }

    es_valido = len(errores) == 0 and (len(df) - codigos_vacios) > 0

    return {
        "es_valido": es_valido,
        "errores": errores,
        "advertencias": advertencias,
        "estadisticas": estadisticas,
    }

@shared_task
def procesar_tipo_documento_con_upload_log(upload_log_id):
    """
    Task optimizada: Procesa tipo documento (sin validaciones duplicadas del chain)
    """
    logger.info(f"🔄 Procesando archivo de tipo documento para upload_log_id: {upload_log_id}")

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return upload_log_id  # Retornar ID para el chain

    # Marcar como procesando
    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    inicio_procesamiento = timezone.now()

    try:
        # ✅ VALIDACIONES YA HECHAS EN CHAIN ANTERIOR:
        # - Datos existentes (validar_datos_existentes_task)
        # - Nombre archivo (validar_nombre_archivo_task)
        # - Cierre relacionado (guardar_archivo_y_procesar_task)

        # 1. OBTENER ARCHIVO TEMPORAL
        ruta_relativa = upload_log.ruta_archivo
        if not ruta_relativa:
            error_msg = "No hay ruta de archivo especificada en el upload_log"
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(error_msg)
            return upload_log.id

        ruta_completa = default_storage.path(ruta_relativa)
        if not os.path.exists(ruta_completa):
            error_msg = f"Archivo temporal no encontrado en: {ruta_relativa}"
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(error_msg)
            return upload_log.id

        # 2. CALCULAR HASH DEL ARCHIVO
        with open(ruta_completa, "rb") as f:
            archivo_hash = hashlib.sha256(f.read()).hexdigest()
        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])

        # 3. VALIDAR ESTRUCTURA DEL EXCEL
        logger.info(f"📋 Validando estructura del Excel: {ruta_completa}")
        validacion = validar_archivo_tipo_documento_excel(ruta_completa)
        if not validacion["es_valido"]:
            error_msg = "Archivo inválido: " + "; ".join(validacion["errores"])
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.resumen = {"validacion": validacion, "archivo_hash": archivo_hash}
            upload_log.save()
            logger.error(f"Validación estructura falló: {error_msg}")
            
            # Registrar actividad de error
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Validación estructura falló: {len(validacion['errores'])} errores",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id, "errores": validacion["errores"]},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return upload_log.id

        # 4. PROCESAR ARCHIVO CON PARSER
        logger.info(f"⚙️ Procesando archivo con parser: {ruta_completa}")
        ok, msg = parsear_tipo_documento_excel(upload_log.cliente.id, ruta_relativa)

        if not ok:
            upload_log.estado = "error"
            upload_log.errores = f"Error en procesamiento: {msg}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(f"Error en parser: {msg}")
            
            # Registrar actividad de error
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Error en procesamiento: {msg}",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return upload_log.id

        # 5. FINALIZAR PROCESAMIENTO EXITOSO
        tipos_creados = TipoDocumento.objects.filter(cliente=upload_log.cliente).count()

        # Actualizar/crear registro de archivo actual
        archivo_actual, created = TipoDocumentoArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            defaults={"upload_log": upload_log, "fecha_subida": timezone.now()},
        )
        if not created:
            archivo_actual.upload_log = upload_log
            archivo_actual.fecha_subida = timezone.now()
            archivo_actual.save()

        # Marcar como completado
        upload_log.estado = "completado"
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.resumen = {
            "tipos_documento_creados": tipos_creados,
            "archivo_hash": archivo_hash,
            "procesamiento_exitoso": True,
            "mensaje_parser": msg,
        }
        upload_log.save()

        # Registrar actividad exitosa
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="process_excel",
            descripcion=f"Procesado archivo de tipo documento: {tipos_creados} tipos creados",
            usuario=upload_log.usuario,
            detalles={
                "upload_log_id": upload_log.id,
                "tipos_creados": tipos_creados,
                "archivo_hash": archivo_hash,
            },
            resultado="exito",
            ip_address=upload_log.ip_usuario,
        )

        logger.info(f"✅ Procesamiento completado: {tipos_creados} tipos de documento creados")
        return upload_log.id

    except Exception as e:
        # Error inesperado durante el procesamiento
        upload_log.estado = "error"
        upload_log.errores = f"Error inesperado: {str(e)}"
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.save()
        logger.exception(f"Error inesperado en procesamiento: {str(e)}")
        
        # Registrar actividad de error
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="process_excel",
            descripcion=f"Error inesperado en procesamiento: {str(e)}",
            usuario=upload_log.usuario,
            detalles={"upload_log_id": upload_log.id, "error": str(e)},
            resultado="error",
            ip_address=upload_log.ip_usuario,
        )
        
        return upload_log.id

# ============================================
# 🔗 CELERY CHAINS PARA TIPO DOCUMENTO
# ============================================

@shared_task
def validar_datos_existentes_task(upload_log_id):
    """
    Task 1: Validar que no existan datos previos para el cliente
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        cliente = upload_log.cliente
        
        logger.info(f"🔍 Validando datos existentes para cliente {cliente.rut}")
        
        # Verificar datos existentes
        tipos_existentes_count = (TipoDocumento.objects
                                 .filter(cliente=cliente)
                                 .count())
        
        if tipos_existentes_count > 0:
            upload_log.estado = "error"
            upload_log.errores = f"Ya existen {tipos_existentes_count} tipos de documento para este cliente"
            upload_log.save()
            
            # Registrar actividad de error
            registrar_actividad_tarjeta(
                cliente_id=cliente.id,
                periodo=upload_log.cierre.periodo if upload_log.cierre else "",
                tarjeta="tipo_documento",
                accion="validar_datos",
                descripcion=f"Error: Cliente ya tiene {tipos_existentes_count} tipos de documento",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id, "tipos_existentes": tipos_existentes_count},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            
            raise Exception(f"Cliente ya tiene {tipos_existentes_count} tipos de documento existentes")
        
        logger.info(f"✅ Validación datos existentes OK para cliente {cliente.rut}")
        # ✅ Retornar solo upload_log_id para simplificar el chain
        return upload_log_id
        
    except UploadLog.DoesNotExist:
        logger.error(f"❌ UploadLog {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")
    except Exception as e:
        logger.error(f"❌ Error validando datos existentes: {str(e)}")
        raise


@shared_task
def validar_nombre_archivo_task(upload_log_id):
    """
    Task 2: Validar nombre de archivo
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        cliente = upload_log.cliente
        
        logger.info(f"🔍 Validando nombre archivo: {upload_log.nombre_archivo_original}")
        
        # Usar validación estándar
        es_valido, resultado_validacion = UploadLog.validar_nombre_archivo(
            upload_log.nombre_archivo_original, "TipoDocumento", cliente.rut
        )
        
        if not es_valido:
            upload_log.estado = "error"
            upload_log.errores = f"Nombre de archivo inválido: {resultado_validacion}"
            upload_log.save()
            
            # Registrar actividad de error
            registrar_actividad_tarjeta(
                cliente_id=cliente.id,
                periodo=upload_log.cierre.periodo if upload_log.cierre else "",
                tarjeta="tipo_documento",
                accion="validar_nombre",
                descripcion=f"Error validación nombre archivo: {resultado_validacion}",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            
            raise Exception(f"Nombre de archivo inválido: {resultado_validacion}")
        
        logger.info(f"✅ Validación nombre archivo OK: {resultado_validacion}")
        return upload_log_id
        
    except Exception as e:
        logger.error(f"❌ Error validando nombre archivo: {str(e)}")
        raise


@shared_task  
def guardar_archivo_y_procesar_task(upload_log_id):
    """
    Task 3: Preparar procesamiento
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        cliente = upload_log.cliente
        
        logger.info(f"💾 Preparando procesamiento para upload_log {upload_log_id}")
        
        # Buscar cierre relacionado
        cierre_relacionado = (CierreContabilidad.objects
                             .filter(cliente=cliente)
                             .filter(estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision'])
                             .select_related('cliente')
                             .order_by('-fecha_creacion')
                             .first())
        
        upload_log.cierre = cierre_relacionado
        upload_log.save()
        
        # El archivo ya debería estar guardado en el upload_log
        if not upload_log.ruta_archivo:
            raise Exception("No se encontró archivo en upload_log")
        
        logger.info(f"📁 Preparación completada, iniciando procesamiento")
        
        # Registrar actividad de inicio
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=cierre_relacionado.periodo if cierre_relacionado else "",
            tarjeta="tipo_documento",
            accion="upload_excel",
            descripcion=f"Iniciando procesamiento de tipos de documento",
            usuario=upload_log.usuario,
            detalles={"upload_log_id": upload_log.id},
            resultado="procesando",
            ip_address=upload_log.ip_usuario,
        )
        
        return upload_log_id
        
    except Exception as e:
        logger.error(f"❌ Error guardando archivo: {str(e)}")
        raise


@shared_task
def limpiar_archivos_temporales_task(upload_log_id):
    """
    Task 4: Limpiar archivos temporales al final del procesamiento exitoso
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        
        if upload_log.estado == "completado":
            logger.info(f"🧹 Limpiando archivos temporales para upload_log {upload_log_id}")
            
            # Limpiar archivo temporal si existe
            if upload_log.ruta_archivo:
                ruta_completa = default_storage.path(upload_log.ruta_archivo)
                if os.path.exists(ruta_completa):
                    try:
                        os.remove(ruta_completa)
                        logger.info("✅ Archivo temporal eliminado")
                    except OSError as e:
                        logger.warning(f"⚠️ No se pudo eliminar archivo temporal: {str(e)}")
        
        return f"Limpieza completada para upload_log {upload_log_id}"
        
    except Exception as e:
        logger.error(f"❌ Error limpiando archivos: {str(e)}")
        # No lanzar excepción aquí para no fallar el chain completo
        return f"Error en limpieza: {str(e)}"


@shared_task
def iniciar_procesamiento_tipo_documento_chain(upload_log_id, nombre_archivo, nombre_temporal):
    """
    🔗 CHAIN PRINCIPAL: Orquesta todo el flujo de procesamiento
    """
    logger.info(f"🚀 Iniciando Celery Chain para upload_log {upload_log_id}")
    
    # Crear el chain de tareas - ahora solo pasa upload_log_id entre tasks
    processing_chain = chain(
        validar_datos_existentes_task.si(upload_log_id),
        validar_nombre_archivo_task.s(),
        guardar_archivo_y_procesar_task.s(),
        procesar_tipo_documento_con_upload_log.s(),  # Task existente
        limpiar_archivos_temporales_task.s()
    )
    
    # Ejecutar el chain
    result = processing_chain.apply_async()
    
    logger.info(f"🔗 Chain iniciado con ID: {result.id}")
    return f"Chain iniciado para upload_log {upload_log_id}"