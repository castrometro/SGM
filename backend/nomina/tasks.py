# nomina/tasks.py
from .utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
    actualizar_empleados_desde_libro_util,
    guardar_registros_nomina_util,
)
# ✨ NUEVOS IMPORTS PARA OPTIMIZACIÓN CON CHORD
from .utils.LibroRemuneracionesOptimizado import (
    dividir_dataframe_empleados,
    procesar_chunk_empleados_util,
    procesar_chunk_registros_util,
    consolidar_stats_empleados,
    consolidar_stats_registros,
)
from .utils.NovedadesRemuneraciones import (
    obtener_headers_archivo_novedades,
    clasificar_headers_archivo_novedades,
    actualizar_empleados_desde_novedades,
    guardar_registros_novedades,
)
from .utils.MovimientoMes import procesar_archivo_movimientos_mes_util
from .utils.ArchivosAnalista import procesar_archivo_analista_util
from celery import shared_task, chain, chord, group
from .models import (
    LibroRemuneracionesUpload,
    MovimientosMesUpload,
    ArchivoAnalistaUpload,
    ArchivoNovedadesUpload,
)
import logging
import pandas as pd
from django.utils import timezone
import json

logger = logging.getLogger(__name__)


def calcular_chunk_size_dinamico(empleados_count):
    """
    🧮 Calcula el tamaño de chunk óptimo basado en el número de empleados
    
    Args:
        empleados_count: Número total de empleados a procesar
        
    Returns:
        int: Tamaño de chunk optimizado
    """
    if empleados_count <= 50:
        return 25  # Chunks pequeños para pocos empleados
    elif empleados_count <= 200:
        return 50  # Chunks medianos para empresas pequeñas-medianas
    elif empleados_count <= 500:
        return 100  # Chunks grandes para empresas medianas
    elif empleados_count <= 1000:
        return 150  # Chunks muy grandes para empresas grandes
    else:
        return 200  # Chunks extremos para corporaciones


@shared_task
def analizar_headers_libro_remuneraciones(libro_id):
    logger.info(f"Procesando libro de remuneraciones id={libro_id}")
    libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
    libro.estado = "analizando_hdrs"
    libro.save()

    try:
        headers = obtener_headers_libro_remuneraciones(libro.archivo.path)
        libro.header_json = headers
        libro.estado = "hdrs_analizados"
        libro.save()
        logger.info(f"Procesamiento exitoso libro id={libro_id}")
        # ¡Retornamos libro_id y headers!
        return {"libro_id": libro_id, "headers": headers}
    except Exception as e:
        libro.estado = "con_error"
        libro.save()
        logger.error(f"Error procesando libro id={libro_id}: {e}")
        raise


@shared_task
def clasificar_headers_libro_remuneraciones_task(result):
    """
    Tarea de clasificación de headers mejorada con logging
    Mantiene compatibilidad con el resultado de la tarea anterior
    """
    from .utils.mixins import UploadLogNominaMixin
    from .models_logging import registrar_actividad_tarjeta_nomina
    
    # Extraer datos del resultado
    libro_id = result["libro_id"]
    upload_log_id = result.get("upload_log_id", None)
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        cierre = libro.cierre
        cliente = cierre.cliente
        
        # Inicializar mixin solo si tenemos upload_log_id
        mixin = UploadLogNominaMixin() if upload_log_id else None

        # 1. Marcamos estado "en proceso de clasificación"
        libro.estado = "clasif_en_proceso"
        libro.save()
        
        if mixin and upload_log_id:
            mixin.actualizar_upload_log(upload_log_id, estado='clasif_en_proceso')

        # 2. Registrar inicio de clasificación
        if upload_log_id:
            from .models_logging import UploadLogNomina
            upload_log = UploadLogNomina.objects.get(id=upload_log_id)
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="libro_remuneraciones",
                accion="classification_start",
                descripcion="Inicio de clasificación de conceptos",
                upload_log=upload_log
            )

        # 3. Obtener headers
        headers = (
            libro.header_json
            if isinstance(libro.header_json, list)
            else result["headers"]
        )

        # 4. Ejecutar clasificación
        headers_clasificados, headers_sin_clasificar = (
            clasificar_headers_libro_remuneraciones(headers, cliente)
        )

        # 5. Guardar resultados
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }

        # 6. Determinar estado final
        if headers_sin_clasificar:
            libro.estado = "clasif_pendiente"
            estado_desc = f"Clasificación parcial: {len(headers_clasificados)} clasificados, {len(headers_sin_clasificar)} pendientes"
        else:
            libro.estado = "clasificado"
            estado_desc = f"Clasificación completa: {len(headers_clasificados)} conceptos clasificados"

        libro.save()
        
        # 7. Actualizar upload log con estadísticas
        if mixin and upload_log_id:
            mixin.actualizar_upload_log(
                upload_log_id, 
                estado=libro.estado,
                resumen={
                    **libro.upload_log.resumen,
                    "headers_clasificados": len(headers_clasificados),
                    "headers_sin_clasificar": len(headers_sin_clasificar),
                    "fase": "clasificacion_completada"
                }
            )

        # 8. Registrar resultado
        if upload_log_id:
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="libro_remuneraciones",
                accion="classification_complete",
                descripcion=estado_desc,
                resultado="exito",
                detalles={
                    "headers_clasificados": len(headers_clasificados),
                    "headers_sin_clasificar": len(headers_sin_clasificar),
                    "clasificacion_completa": len(headers_sin_clasificar) == 0
                },
                upload_log=upload_log
            )

        logger.info(
            f"Libro {libro_id}: {len(headers_clasificados)} headers clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        
        return {
            "libro_id": libro_id,
            "upload_log_id": upload_log_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
        }
        
    except Exception as e:
        error_msg = f"Error clasificando headers para libro id={libro_id}: {e}"
        logger.error(error_msg)
        
        # Actualizar estados de error
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save()
        except Exception as ex:
            logger.error(f"Error guardando estado 'con_error' para libro id={libro_id}: {ex}")
        
        # Actualizar upload log si existe
        if mixin and upload_log_id:
            mixin.marcar_como_error(upload_log_id, error_msg)
        
        # Registrar error en actividades si tenemos upload_log_id
        if upload_log_id:
            try:
                registrar_actividad_tarjeta_nomina(
                    cierre_id=libro.cierre.id,
                    tarjeta="libro_remuneraciones",
                    accion="classification_complete",
                    descripcion=f"Error en clasificación: {str(e)}",
                    resultado="error",
                    detalles={"error": str(e)},
                    upload_log=upload_log if upload_log_id else None
                )
            except Exception:
                pass  # No fallar si no se puede registrar la actividad
        
        raise
        raise


@shared_task
def actualizar_empleados_desde_libro(result):
    """Task para actualizar empleados desde libro - solo maneja try/except"""
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        count = actualizar_empleados_desde_libro_util(libro)
        logger.info(f"Actualizados {count} empleados desde libro {libro_id}")
        return {"libro_id": libro_id, "empleados_actualizados": count}
    except Exception as e:
        logger.error(f"Error actualizando empleados para libro id={libro_id}: {e}")
        raise


@shared_task
def guardar_registros_nomina(result):
    """Task para guardar registros de nómina - solo maneja try/except"""
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        count = guardar_registros_nomina_util(libro)
        
        # ✅ ACTUALIZAR ESTADO AL FINAL
        libro.estado = "procesado"
        libro.save()
        
        return {
            "libro_id": libro_id, 
            "registros_actualizados": count,
            "estado": "procesado"
        }
    except Exception as e:
        logger.error(f"Error guardando registros de nómina para libro id={libro_id}: {e}")
        # Marcar como error
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save()
        except:
            pass
        raise


@shared_task
def procesar_movimientos_mes(movimiento_id, upload_log_id=None):
    """Procesa un archivo de movimientos del mes con logging completo"""
    from .utils.mixins import UploadLogNominaMixin
    from .models_logging import registrar_actividad_tarjeta_nomina, UploadLogNomina
    
    logger.info(f"Procesando archivo movimientos mes id={movimiento_id} con upload_log={upload_log_id}")
    
    mixin = UploadLogNominaMixin() if upload_log_id else None
    upload_log = None
    
    try:
        # Obtener referencias
        movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
        if upload_log_id:
            upload_log = UploadLogNomina.objects.get(id=upload_log_id)
        
        # Cambiar estado a procesando
        movimiento.estado = 'en_proceso'
        movimiento.save()
        
        if mixin and upload_log:
            mixin.actualizar_upload_log(upload_log_id, estado='procesando', resumen={
                'fase': 'procesamiento_iniciado',
                'movimiento_id': movimiento_id
            })
        
        # Registrar inicio de procesamiento
        registrar_actividad_tarjeta_nomina(
            cierre_id=movimiento.cierre.id,
            tarjeta="movimientos_mes",
            accion="process_start",
            descripcion="Iniciando procesamiento de archivo de movimientos del mes",
            detalles={
                "movimiento_id": movimiento_id,
                "upload_log_id": upload_log_id,
                "archivo_nombre": movimiento.archivo.name if movimiento.archivo else "N/A"
            },
            upload_log=upload_log
        )
        
        # Procesar archivo
        resultados = procesar_archivo_movimientos_mes_util(movimiento)
        
        # Guardar resultados
        movimiento.resultados_procesamiento = resultados
        
        # Determinar estado final
        if resultados.get('errores'):
            if any(v > 0 for k, v in resultados.items() if k != 'errores' and isinstance(v, int)):
                estado_final = 'con_errores_parciales'
                resultado_actividad = 'warning'
            else:
                estado_final = 'con_error'
                resultado_actividad = 'error'
        else:
            estado_final = 'procesado'
            resultado_actividad = 'exito'
        
        movimiento.estado = estado_final
        movimiento.save()
        
        # Actualizar UploadLog
        if mixin and upload_log:
            mixin.actualizar_upload_log(upload_log_id, 
                estado='completado' if estado_final == 'procesado' else 'error',
                resumen={
                    'fase': 'procesamiento_completado',
                    'estado_final': estado_final,
                    'resultados': resultados,
                    'registros_procesados': sum(v for k, v in resultados.items() if k != 'errores' and isinstance(v, int))
                }
            )
        
        # Registrar finalización
        descripcion = f"Procesamiento completado con estado: {estado_final}"
        if resultados.get('errores'):
            descripcion += f". Errores: {len(resultados['errores'])}"
        
        registrar_actividad_tarjeta_nomina(
            cierre_id=movimiento.cierre.id,
            tarjeta="movimientos_mes",
            accion="process_complete",
            descripcion=descripcion,
            resultado=resultado_actividad,
            detalles={
                "movimiento_id": movimiento_id,
                "upload_log_id": upload_log_id,
                "estado_final": estado_final,
                "resultados": resultados,
                "registros_totales": sum(v for k, v in resultados.items() if k != 'errores' and isinstance(v, int)),
                "errores_count": len(resultados.get('errores', []))
            },
            upload_log=upload_log
        )
        
        logger.info(f"Procesamiento exitoso movimientos mes id={movimiento_id}, estado: {estado_final}")
        return resultados
        
    except Exception as e:
        error_msg = f"Error procesando movimientos mes id={movimiento_id}: {e}"
        logger.error(error_msg)
        
        # Actualizar estados de error
        try:
            movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
            movimiento.estado = 'con_error'
            movimiento.resultados_procesamiento = {'errores': [str(e)]}
            movimiento.save()
        except:
            pass
        
        # Marcar UploadLog como error
        if mixin and upload_log_id:
            mixin.marcar_como_error(upload_log_id, error_msg)
        
        # Registrar error en actividades
        if upload_log_id:
            try:
                registrar_actividad_tarjeta_nomina(
                    cierre_id=movimiento.cierre.id,
                    tarjeta="movimientos_mes",
                    accion="process_complete",
                    descripcion=f"Error en procesamiento: {str(e)}",
                    resultado="error",
                    detalles={
                        "movimiento_id": movimiento_id,
                        "upload_log_id": upload_log_id,
                        "error": str(e)
                    },
                    upload_log=upload_log
                )
            except Exception:
                pass  # No fallar si no se puede registrar la actividad
        
        raise


# Nuevas tasks para archivos del analista

@shared_task
def procesar_archivo_analista(archivo_id):
    """Procesa un archivo subido por el analista (finiquitos, incidencias o ingresos)"""
    logger.info(f"Procesando archivo analista id={archivo_id}")
    
    try:
        archivo = ArchivoAnalistaUpload.objects.get(id=archivo_id)
        archivo.estado = 'en_proceso'
        archivo.save()
        
        resultados = procesar_archivo_analista_util(archivo)
        
        # Determinar estado final
        if resultados.get('errores'):
            if resultados.get('procesados', 0) > 0:
                archivo.estado = 'procesado'  # Parcialmente exitoso
            else:
                archivo.estado = 'con_error'  # Totalmente fallido
        else:
            archivo.estado = 'procesado'
        
        archivo.save()
        
        logger.info(f"Procesamiento exitoso archivo analista id={archivo_id}: {resultados['procesados']} registros procesados")
        return resultados
        
    except Exception as e:
        archivo = ArchivoAnalistaUpload.objects.get(id=archivo_id)
        archivo.estado = 'con_error'
        archivo.save()
        logger.error(f"Error procesando archivo analista id={archivo_id}: {e}")
        raise


@shared_task
def procesar_archivo_novedades(archivo_id):
    """Procesa un archivo de novedades - solo hasta clasificación inicial"""
    logger.info(f"Iniciando procesamiento inicial archivo de novedades id={archivo_id}")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # ✅ SOLO ejecutar análisis y clasificación inicial - NO las tareas finales
        workflow = chain(
            analizar_headers_archivo_novedades.s(archivo_id),
            clasificar_headers_archivo_novedades_task.s()
        )
        
        # Ejecutar la cadena parcial
        workflow.apply_async()
        
        logger.info(f"Cadena de análisis y clasificación iniciada para archivo novedades id={archivo_id}")
        return {"archivo_id": archivo_id, "estado": "cadena_iniciada"}
        
    except Exception as e:
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = 'con_error'
            archivo.save()
        except Exception as ex:
            logger.error(f"Error guardando estado 'con_error' para archivo novedades id={archivo_id}: {ex}")
        
        logger.error(f"Error iniciando procesamiento archivo de novedades id={archivo_id}: {e}")
        raise


@shared_task
def analizar_headers_archivo_novedades(archivo_id):
    """Analiza headers de un archivo de novedades"""
    logger.info(f"Procesando archivo de novedades id={archivo_id}")
    archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
    archivo.estado = "analizando_hdrs"
    archivo.save()

    try:
        headers = obtener_headers_archivo_novedades(archivo.archivo.path)
        archivo.header_json = headers
        archivo.estado = "hdrs_analizados"
        archivo.save()
        logger.info(f"Procesamiento exitoso archivo novedades id={archivo_id}")
        # Retornamos archivo_id y headers
        return {"archivo_id": archivo_id, "headers": headers}
    except Exception as e:
        archivo.estado = "con_error"
        archivo.save()
        logger.error(f"Error procesando archivo novedades id={archivo_id}: {e}")
        raise


@shared_task
def clasificar_headers_archivo_novedades_task(result):
    """Clasifica headers de un archivo de novedades"""
    archivo_id = result["archivo_id"]
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        cierre = archivo.cierre
        cliente = cierre.cliente

        # Marcamos estado "en proceso de clasificación"
        archivo.estado = "clasif_en_proceso"
        archivo.save()

        headers = (
            archivo.header_json
            if isinstance(archivo.header_json, list)
            else result["headers"]
        )

        headers_clasificados, headers_sin_clasificar = (
            clasificar_headers_archivo_novedades(headers, cliente)
        )

        # Escribe el resultado final en el campo JSON
        archivo.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }

        # Cambia el estado según si quedan pendientes o no
        if headers_sin_clasificar:
            archivo.estado = "clasif_pendiente"
        else:
            archivo.estado = "clasificado"
            
            # ✅ CAMBIO: NO ejecutar automáticamente el procesamiento final
            # El usuario debe decidir cuándo procesar mediante el botón "Procesar Final"
            logger.info(f"Archivo novedades {archivo_id}: Todos los headers clasificados automáticamente. Estado: 'clasificado' - esperando acción del usuario")

        archivo.save()
        logger.info(
            f"Archivo novedades {archivo_id}: {len(headers_clasificados)} headers clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        return {
            "archivo_id": archivo_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
        }
    except Exception as e:
        logger.error(f"Error clasificando headers para archivo novedades id={archivo_id}: {e}")
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
        except Exception as ex:
            logger.error(
                f"Error guardando estado 'con_error' para archivo novedades id={archivo_id}: {ex}"
            )
        raise


@shared_task
def actualizar_empleados_desde_novedades_task(result):
    """Task para actualizar empleados desde archivo de novedades"""
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        count = actualizar_empleados_desde_novedades(archivo)
        logger.info(f"Actualizados {count} empleados desde archivo novedades {archivo_id}")
        return {"archivo_id": archivo_id, "empleados_actualizados": count}
    except Exception as e:
        logger.error(f"Error actualizando empleados para archivo novedades id={archivo_id}: {e}")
        raise


@shared_task
def guardar_registros_novedades_task(result):
    """Task para guardar registros de novedades"""
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        count = guardar_registros_novedades(archivo)
        
        # ✅ ACTUALIZAR ESTADO AL FINAL
        archivo.estado = "procesado"
        archivo.save()
        
        return {
            "archivo_id": archivo_id, 
            "registros_actualizados": count,
            "estado": "procesado"
        }
    except Exception as e:
        logger.error(f"Error guardando registros de novedades para archivo id={archivo_id}: {e}")
        # Marcar como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
        except:
            pass
        raise


# ===== 🚀 TASKS OPTIMIZADAS PARA NOVEDADES CON CELERY CHORD =====

@shared_task
def procesar_chunk_empleados_novedades_task(archivo_id, chunk_data):
    """
    👥 Task para procesar un chunk específico de empleados de novedades en paralelo
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento del chunk
    """
    from .utils.NovedadesOptimizado import procesar_chunk_empleados_novedades_util, validar_chunk_data
    
    logger.info(f"🔄 Iniciando procesamiento de chunk empleados novedades {chunk_data.get('chunk_id')}")
    
    # Validar datos del chunk
    if not validar_chunk_data(chunk_data):
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'empleados_actualizados': 0,
            'errores': ['Datos del chunk inválidos'],
            'archivo_id': archivo_id,
            'success': False
        }
    
    try:
        resultado = procesar_chunk_empleados_novedades_util(archivo_id, chunk_data)
        logger.info(f"✅ Chunk empleados novedades {chunk_data.get('chunk_id')} completado exitosamente")
        return resultado
    except Exception as e:
        error_msg = f"Error en chunk empleados novedades {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'empleados_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': 0,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


@shared_task
def procesar_chunk_registros_novedades_task(archivo_id, chunk_data):
    """
    📝 Task para procesar un chunk específico de registros de novedades en paralelo
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento del chunk
    """
    from .utils.NovedadesOptimizado import procesar_chunk_registros_novedades_util, validar_chunk_data
    
    logger.info(f"💾 Iniciando procesamiento de chunk registros novedades {chunk_data.get('chunk_id')}")
    
    # Validar datos del chunk
    if not validar_chunk_data(chunk_data):
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'registros_creados': 0,
            'registros_actualizados': 0,
            'errores': ['Datos del chunk inválidos'],
            'archivo_id': archivo_id,
            'success': False
        }
    
    try:
        resultado = procesar_chunk_registros_novedades_util(archivo_id, chunk_data)
        logger.info(f"✅ Chunk registros novedades {chunk_data.get('chunk_id')} completado exitosamente")
        return resultado
    except Exception as e:
        error_msg = f"Error en chunk registros novedades {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'registros_creados': 0,
            'registros_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': 0,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


@shared_task
def consolidar_empleados_novedades_task(resultados_chunks):
    """
    📊 Consolida los resultados de múltiples chunks de empleados de novedades
    
    Args:
        resultados_chunks: Lista de resultados de chunks de empleados
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    from .utils.NovedadesOptimizado import consolidar_stats_novedades
    
    logger.info(f"📊 Consolidando resultados de {len(resultados_chunks)} chunks de empleados novedades")
    
    try:
        consolidado = consolidar_stats_novedades(resultados_chunks, 'empleados')
        
        # Obtener archivo_id del primer resultado
        archivo_id = resultados_chunks[0].get('archivo_id') if resultados_chunks else None
        
        # Agregar información específica para la siguiente fase
        consolidado.update({
            'fase': 'empleados_completada',
            'archivo_id': archivo_id,
            'listo_para_registros': True
        })
        
        logger.info(f"✅ Consolidación empleados completada: {consolidado.get('empleados_actualizados', 0)} empleados actualizados")
        
        return consolidado
        
    except Exception as e:
        logger.error(f"❌ Error consolidando empleados novedades: {e}")
        return {
            'fase': 'empleados_error',
            'archivo_id': resultados_chunks[0].get('archivo_id') if resultados_chunks else None,
            'errores': [str(e)],
            'success': False
        }


@shared_task
def finalizar_procesamiento_novedades_task(resultados_chunks):
    """
    🎯 Finaliza el procesamiento de novedades y actualiza el estado del archivo
    
    Args:
        resultados_chunks: Lista de resultados de chunks de registros
        
    Returns:
        Dict: Resultado final del procesamiento
    """
    from .utils.NovedadesOptimizado import consolidar_stats_novedades
    from .models_logging import registrar_actividad_tarjeta_nomina
    
    logger.info(f"🎯 Finalizando procesamiento de novedades con {len(resultados_chunks)} chunks")
    
    try:
        # Consolidar estadísticas de registros
        consolidado = consolidar_stats_novedades(resultados_chunks, 'registros')
        archivo_id = consolidado.get('archivo_id') or (resultados_chunks[0].get('archivo_id') if resultados_chunks else None)
        
        if not archivo_id:
            raise ValueError("No se pudo obtener archivo_id de los resultados")
        
        # Obtener archivo y actualizar estado
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Determinar estado final basado en errores
        errores_totales = consolidado.get('errores_totales', 0)
        registros_creados = consolidado.get('registros_creados', 0)
        registros_actualizados = consolidado.get('registros_actualizados', 0)
        
        if errores_totales > 0 and (registros_creados > 0 or registros_actualizados > 0):
            estado_final = "con_errores_parciales"
            resultado_actividad = "warning"
        elif errores_totales > 0:
            estado_final = "con_error"
            resultado_actividad = "error"
        else:
            estado_final = "procesado"
            resultado_actividad = "exito"
        
        # Actualizar estado del archivo
        archivo.estado = estado_final
        archivo.save()
        
        # Registrar actividad de finalización
        try:
            registrar_actividad_tarjeta_nomina(
                cierre_id=archivo.cierre.id,
                tarjeta="novedades",
                accion="procesamiento_paralelo_completado",
                descripcion=f"Procesamiento paralelo completado: {registros_creados} registros creados, {registros_actualizados} actualizados",
                resultado=resultado_actividad,
                detalles={
                    "archivo_id": archivo_id,
                    "estado_final": estado_final,
                    "estadisticas": consolidado,
                    "modo": "chord_paralelo"
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Error registrando actividad final: {e}")
        
        resultado_final = {
            'archivo_id': archivo_id,
            'estado_final': estado_final,
            'estadisticas_consolidadas': consolidado,
            'timestamp_finalizacion': timezone.now().isoformat(),
            'success': True
        }
        
        logger.info(f"🎯 Procesamiento novedades finalizado exitosamente:")
        logger.info(f"  - Estado final: {estado_final}")
        logger.info(f"  - Registros creados: {registros_creados}")
        logger.info(f"  - Registros actualizados: {registros_actualizados}")
        logger.info(f"  - Errores totales: {errores_totales}")
        
        return resultado_final
        
    except Exception as e:
        logger.error(f"❌ Error finalizando procesamiento novedades: {e}")
        
        # Intentar marcar archivo como error
        try:
            if 'archivo_id' in locals():
                archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
                archivo.estado = "con_error"
                archivo.save()
        except:
            pass
        
        return {
            'archivo_id': archivo_id if 'archivo_id' in locals() else None,
            'estado_final': 'con_error',
            'errores': [str(e)],
            'success': False
        }


@shared_task
def actualizar_empleados_desde_novedades_task_optimizado(result):
    """
    🚀 Versión optimizada que usa Celery Chord para procesar empleados en chunks paralelos
    
    Args:
        result: Resultado de la task anterior (contiene archivo_id)
        
    Returns:
        Dict: Información del procesamiento o referencia al chord
    """
    from .utils.NovedadesOptimizado import dividir_dataframe_novedades, obtener_archivo_novedades_path
    
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    
    logger.info(f"🚀 Iniciando actualización optimizada empleados novedades archivo {archivo_id}")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Obtener ruta del archivo
        ruta_archivo = obtener_archivo_novedades_path(archivo_id)
        if not ruta_archivo:
            raise ValueError(f"No se pudo obtener ruta del archivo {archivo_id}")
        
        # Leer archivo para calcular chunk size
        import pandas as pd
        df = pd.read_excel(ruta_archivo, engine="openpyxl")
        total_filas = len(df)
        
        # Calcular chunk size dinámico
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"📊 Total filas novedades: {total_filas}, Chunk size calculado: {chunk_size}")
        
        # Para archivos pequeños, usar procesamiento directo
        if total_filas <= 50:
            logger.info(f"📝 Archivo pequeño ({total_filas} filas), usando procesamiento directo")
            from .utils.NovedadesRemuneraciones import actualizar_empleados_desde_novedades
            count = actualizar_empleados_desde_novedades(archivo)
            return {
                "archivo_id": archivo_id,
                "empleados_actualizados": count,
                "modo": "directo",
                "timestamp": timezone.now().isoformat()
            }
        
        # Dividir en chunks para procesamiento paralelo
        chunks = dividir_dataframe_novedades(ruta_archivo, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se crearon chunks válidos para archivo {archivo_id}")
            raise ValueError("No se pudieron crear chunks para el archivo")
        
        logger.info(f"📦 Creados {len(chunks)} chunks para procesamiento paralelo")
        
        # Crear tasks paralelas usando chord
        tasks_paralelas = [
            procesar_chunk_empleados_novedades_task.s(archivo_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback
        callback = consolidar_empleados_novedades_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"🚀 Chord empleados iniciado para archivo {archivo_id}: {len(chunks)} chunks en paralelo")
        
        return {
            "archivo_id": archivo_id,
            "chord_id": str(resultado_chord),
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord_empleados",
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en empleados optimizado archivo {archivo_id}: {e}")
        
        # Marcar archivo como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
        except:
            pass
        
        raise


@shared_task
def guardar_registros_novedades_task_optimizado(result):
    """
    🚀 Versión optimizada que usa Celery Chord para guardar registros en chunks paralelos
    
    Args:
        result: Resultado de la task anterior (contiene archivo_id)
        
    Returns:
        Dict: Información del procesamiento o referencia al chord
    """
    from .utils.NovedadesOptimizado import dividir_dataframe_novedades, obtener_archivo_novedades_path
    
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    
    logger.info(f"🚀 Iniciando guardado optimizado registros novedades archivo {archivo_id}")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Verificar que el archivo esté en estado correcto
        if archivo.estado not in ['clasificado', 'empleados_actualizados']:
            logger.warning(f"⚠️ Archivo en estado {archivo.estado}, continuando con registros")
        
        # Obtener ruta del archivo
        ruta_archivo = obtener_archivo_novedades_path(archivo_id)
        if not ruta_archivo:
            raise ValueError(f"No se pudo obtener ruta del archivo {archivo_id}")
        
        # Leer archivo para calcular chunk size
        import pandas as pd
        df = pd.read_excel(ruta_archivo, engine="openpyxl")
        total_filas = len(df)
        
        # Calcular chunk size dinámico
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"💾 Iniciando guardado de registros en chunks: {total_filas} filas, chunk size: {chunk_size}")
        
        # Para archivos pequeños, usar procesamiento directo
        if total_filas <= 50:
            logger.info(f"📝 Archivo pequeño ({total_filas} filas), guardado directo")
            from .utils.NovedadesRemuneraciones import guardar_registros_novedades
            count = guardar_registros_novedades(archivo)
            
            # Actualizar estado final
            archivo.estado = "procesado"
            archivo.save()
            
            return {
                "archivo_id": archivo_id,
                "registros_guardados": count,
                "estado_final": "procesado",
                "modo": "directo",
                "timestamp": timezone.now().isoformat()
            }
        
        # Dividir en chunks para procesamiento paralelo
        chunks = dividir_dataframe_novedades(ruta_archivo, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se crearon chunks válidos para registros archivo {archivo_id}")
            raise ValueError("No se pudieron crear chunks para registros")
        
        logger.info(f"📦 Creados {len(chunks)} chunks para guardado paralelo de registros")
        
        # Crear tasks paralelas para registros
        tasks_paralelas = [
            procesar_chunk_registros_novedades_task.s(archivo_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord para registros
        callback = finalizar_procesamiento_novedades_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"🚀 Chord registros iniciado para archivo {archivo_id}: {len(chunks)} chunks en paralelo")
        
        return {
            "archivo_id": archivo_id,
            "chord_id": str(resultado_chord),
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord_registros",
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en registros optimizado archivo {archivo_id}: {e}")
        
        # Marcar archivo como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
        except:
            pass
        
        raise


# ===== TAREAS PARA SISTEMA DE INCIDENCIAS =====

@shared_task
def generar_incidencias_cierre_task(cierre_id):
    """
    🔍 TASK: GENERACIÓN DE INCIDENCIAS CONSOLIDADAS
    
    Genera incidencias comparando datos consolidados del mes actual con el mes anterior.
    Implementa las 4 reglas principales:
    1. Variaciones de valor header-empleado superior a ±30%
    2. Ausentismos del mes anterior que deberían continuar
    3. Personas que ingresaron el mes anterior y no están presentes  
    4. Personas que finiquitaron el mes anterior y siguen presentes
    """
    from .utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidadas_task
    from .models import CierreNomina
    
    logger.info(f"🔍 Iniciando generación de incidencias para cierre consolidado {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar que el cierre esté en un estado válido para generar incidencias
        estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas'] 
        if cierre.estado not in estados_validos:
            raise ValueError(f"El cierre debe estar en estado válido para generar incidencias. Estado actual: {cierre.estado}, Estados válidos: {estados_validos}")
        
        # Ejecutar detección de incidencias
        resultado = generar_incidencias_consolidadas_task(cierre_id)
        
        if resultado['success']:
            logger.info(f"✅ Incidencias generadas exitosamente para cierre {cierre_id}: {resultado['total_incidencias']} incidencias")
            return resultado
        else:
            logger.error(f"❌ Error en detección de incidencias para cierre {cierre_id}: {resultado.get('error', 'Error desconocido')}")
            return resultado
        
    except Exception as e:
        logger.error(f"❌ Error crítico generando incidencias para cierre {cierre_id}: {e}")
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            # No cambiar estado en caso de error, mantener consolidado
        except:
            pass
        
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


# ===== NUEVAS TAREAS PARA SISTEMA DUAL DE INCIDENCIAS (CELERY CHORD) =====

@shared_task
def generar_incidencias_consolidados_v2_task(cierre_id, clasificaciones_seleccionadas=None):
    """
    🔄 TASK: GENERACIÓN DUAL DE INCIDENCIAS (CELERY CHORD)
    
    Implementa el sistema dual de detección de incidencias:
    - Comparación individual (elemento por elemento) para clasificaciones seleccionadas
    - Comparación por suma total para todas las clasificaciones
    
    Utiliza Celery Chord para procesamiento paralelo optimizado.
    Performance target: ~183% improvement (8.2s → 2.9s)
    """
    from .utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidados_v2
    from .models import CierreNomina
    
    logger.info(f"🔄 Iniciando generación dual de incidencias para cierre {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar estado válido
        estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas'] 
        if cierre.estado not in estados_validos:
            raise ValueError(f"Estado inválido: {cierre.estado}. Válidos: {estados_validos}")
        
        # Ejecutar detección dual con Celery Chord
        resultado = generar_incidencias_consolidados_v2(
            cierre_id=cierre_id,
            clasificaciones_seleccionadas=clasificaciones_seleccionadas
        )
        
        if resultado['success']:
            logger.info(f"✅ Sistema dual completado para cierre {cierre_id}:")
            logger.info(f"   📋 Incidencias individuales: {resultado.get('total_incidencias_individuales', 0)}")
            logger.info(f"   📊 Incidencias suma total: {resultado.get('total_incidencias_suma', 0)}")
            logger.info(f"   🎯 Total: {resultado.get('total_incidencias', 0)}")
            logger.info(f"   ⏱️ Tiempo procesamiento: {resultado.get('tiempo_procesamiento', 'N/A')}")
            
            return resultado
        else:
            logger.error(f"❌ Error en sistema dual para cierre {cierre_id}: {resultado.get('error')}")
            return resultado
        
    except Exception as e:
        logger.error(f"❌ Error crítico en sistema dual para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_chunk_comparacion_individual_task(chunk_data, cierre_id, clasificaciones_seleccionadas):
    """
    🔍 TASK: PROCESAMIENTO DE CHUNK INDIVIDUAL
    
    Procesa un chunk de empleados para comparación individual (elemento por elemento).
    Parte del Celery Chord para procesamiento paralelo.
    """
    from .utils.DetectarIncidenciasConsolidadas import procesar_chunk_comparacion_individual
    
    try:
        resultado = procesar_chunk_comparacion_individual(
            chunk_data=chunk_data,
            cierre_id=cierre_id,
            clasificaciones_seleccionadas=clasificaciones_seleccionadas
        )
        
        logger.info(f"✅ Chunk individual procesado: {len(resultado)} incidencias")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error procesando chunk individual: {e}")
        return []


@shared_task
def procesar_comparacion_suma_total_task(cierre_id):
    """
    📊 TASK: PROCESAMIENTO DE SUMA TOTAL
    
    Procesa la comparación por suma total de todas las clasificaciones.
    Ejecuta en paralelo con las comparaciones individuales.
    """
    from .utils.DetectarIncidenciasConsolidadas import procesar_comparacion_suma_total
    
    try:
        resultado = procesar_comparacion_suma_total(cierre_id)
        
        logger.info(f"✅ Suma total procesada: {len(resultado)} incidencias")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error procesando suma total: {e}")
        return []


@shared_task
def consolidar_resultados_incidencias_task(resultados_individuales, resultados_suma_total, cierre_id):
    """
    🎯 TASK: CONSOLIDACIÓN DE RESULTADOS
    
    Consolida los resultados de todas las tareas paralelas del Celery Chord.
    Callback final que unifica todos los resultados.
    """
    from .utils.DetectarIncidenciasConsolidadas import consolidar_resultados_incidencias
    
    try:
        resultado_final = consolidar_resultados_incidencias(
            resultados_individuales=resultados_individuales,
            resultados_suma_total=resultados_suma_total,
            cierre_id=cierre_id
        )
        
        logger.info(f"🎯 Consolidación completada para cierre {cierre_id}:")
        logger.info(f"   📋 Total incidencias: {resultado_final.get('total_incidencias', 0)}")
        logger.info(f"   🔄 Individuales: {resultado_final.get('total_incidencias_individuales', 0)}")
        logger.info(f"   📊 Suma total: {resultado_final.get('total_incidencias_suma', 0)}")
        
        return resultado_final
        
    except Exception as e:
        logger.error(f"❌ Error consolidando resultados para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }
    
    # CÓDIGO ORIGINAL COMENTADO:
    # from .utils.GenerarIncidencias import generar_todas_incidencias
    # from .models import CierreNomina
    # 
    # logger.info(f"Iniciando generación de incidencias para cierre {cierre_id}")
    # 
    # try:
    #     cierre = CierreNomina.objects.get(id=cierre_id)
    #     
    #     # Verificar que el cierre tenga los archivos necesarios procesados
    #     if not _verificar_archivos_listos_para_incidencias(cierre):
    #         raise ValueError("No todos los archivos están procesados para generar incidencias")
    #     
    #     # FALTA: Verificar que discrepancias = 0 antes de continuar
    #     # FALTA: Implementar comparación contra mes anterior específicamente
    #     
    #     resultado = generar_todas_incidencias(cierre)
    #     
    #     logger.info(f"Incidencias generadas exitosamente para cierre {cierre_id}: {resultado['total_incidencias']} incidencias")
    #     return resultado
    #     
    # except Exception as e:
    #     logger.error(f"Error generando incidencias para cierre {cierre_id}: {e}")
    #     try:
    #         cierre = CierreNomina.objects.get(id=cierre_id)
    #         cierre.estado_incidencias = 'pendiente'
    #         cierre.save(update_fields=['estado_incidencias'])
    #     except:
    #         pass
    #     raise

def _verificar_archivos_listos_para_incidencias(cierre):
    """Verifica que los archivos necesarios estén procesados"""
    from .models import LibroRemuneracionesUpload, MovimientosMesUpload
    
    # Verificar libro de remuneraciones procesado
    libro = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
    if not libro or libro.estado != 'procesado':
        logger.warning(f"Libro de remuneraciones no procesado para cierre {cierre.id}")
        return False
    
    # Verificar movimientos del mes procesados
    movimientos = MovimientosMesUpload.objects.filter(cierre=cierre).first()
    if not movimientos or movimientos.estado != 'procesado':
        logger.warning(f"Movimientos del mes no procesados para cierre {cierre.id}")
        return False
    
    return True


# ===== NUEVAS TAREAS CON SISTEMA DE LOGGING INTEGRADO =====

@shared_task
def analizar_headers_libro_remuneraciones_con_logging(libro_id, upload_log_id):
    """
    Analiza headers del libro de remuneraciones con logging integrado
    """
    from .models_logging import UploadLogNomina
    logger.info(f"Procesando libro de remuneraciones id={libro_id} con upload_log={upload_log_id}")
    
    try:
        # Obtener upload_log y actualizar estado
        upload_log = UploadLogNomina.objects.get(id=upload_log_id)
        upload_log.estado = "analizando_hdrs"
        upload_log.save()
        
        # Obtener libro
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        libro.estado = "analizando_hdrs"
        libro.save()
        
        # Procesar headers
        headers = obtener_headers_libro_remuneraciones(libro.archivo.path)
        libro.header_json = headers
        libro.estado = "hdrs_analizados"
        libro.save()
        
        # Actualizar upload_log
        upload_log.estado = "hdrs_analizados"
        upload_log.headers_detectados = headers
        upload_log.save()
        
        logger.info(f"Headers analizados exitosamente para libro {libro_id}")
        return {
            "libro_id": libro_id, 
            "upload_log_id": upload_log_id,
            "headers": headers
        }
        
    except Exception as e:
        logger.error(f"Error analizando headers libro {libro_id}: {e}")
        
        # Marcar errores en ambos modelos
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save()
        except:
            pass
            
        try:
            upload_log = UploadLogNomina.objects.get(id=upload_log_id)
            upload_log.marcar_como_error(f"Error analizando headers: {str(e)}")
        except:
            pass
            
        raise


@shared_task  
def clasificar_headers_libro_remuneraciones_con_logging(result):
    """
    Clasifica headers del libro de remuneraciones con logging integrado
    """
    from .models_logging import UploadLogNomina
    
    libro_id = result["libro_id"]
    upload_log_id = result["upload_log_id"]
    
    logger.info(f"Clasificando headers para libro {libro_id} con upload_log {upload_log_id}")
    
    try:
        # Obtener modelos
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        upload_log = UploadLogNomina.objects.get(id=upload_log_id)
        cierre = libro.cierre
        cliente = cierre.cliente
        
        # Actualizar estados
        libro.estado = "clasif_en_proceso"
        libro.save()
        upload_log.estado = "clasif_en_proceso"
        upload_log.save()
        
        # Obtener headers
        headers = (
            libro.header_json
            if isinstance(libro.header_json, list)
            else result["headers"]
        )
        
        # Clasificar headers
        headers_clasificados, headers_sin_clasificar = (
            clasificar_headers_libro_remuneraciones(headers, cliente)
        )
        
        # Actualizar libro
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }
        
        # Determinar estado final
        if headers_sin_clasificar:
            libro.estado = "clasif_pendiente"
            upload_log.estado = "clasif_pendiente"
        else:
            libro.estado = "clasificado"
            upload_log.estado = "clasificado"
        
        libro.save()
        
        # Actualizar upload_log con resumen
        resumen_final = {
            "libro_id": libro_id,
            "headers_total": len(headers),
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
            "clasificados": headers_clasificados,
            "sin_clasificar": headers_sin_clasificar
        }
        
        upload_log.resumen = resumen_final
        upload_log.save()
        
        logger.info(
            f"Libro {libro_id}: {len(headers_clasificados)} headers clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        
        return {
            "libro_id": libro_id,
            "upload_log_id": upload_log_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
            "estado_final": libro.estado
        }
        
    except Exception as e:
        logger.error(f"Error clasificando headers para libro {libro_id}: {e}")
        
        # Marcar errores en ambos modelos
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save()
        except:
            pass
            
        try:
            upload_log = UploadLogNomina.objects.get(id=upload_log_id)
            upload_log.marcar_como_error(f"Error clasificando headers: {str(e)}")
        except:
            pass
            
        raise


# ======== TAREAS DE ANÁLISIS DE DATOS ========

@shared_task
def analizar_datos_cierre_task(cierre_id, tolerancia_variacion=30.0):
    """
    Tarea para analizar datos del cierre actual vs mes anterior
    y generar incidencias de variación salarial
    """
    from .models import CierreNomina, AnalisisDatosCierre, IncidenciaVariacionSalarial
    from .models import EmpleadoCierre, AnalistaIngreso, AnalistaFiniquito, AnalistaIncidencia
    from django.utils import timezone
    from decimal import Decimal
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Iniciando análisis de datos para cierre {cierre_id}")
    
    try:
        # Obtener cierre actual
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Crear o actualizar análisis
        analisis, created = AnalisisDatosCierre.objects.get_or_create(
            cierre=cierre,
            defaults={
                'tolerancia_variacion_salarial': Decimal(str(tolerancia_variacion)),
                'estado': 'procesando',
                'analista': cierre.analista_asignado if hasattr(cierre, 'analista_asignado') else None
            }
        )
        
        if not created:
            analisis.estado = 'procesando'
            analisis.tolerancia_variacion_salarial = Decimal(str(tolerancia_variacion))
            analisis.save()
        
        # 1. ANÁLISIS DE DATOS ACTUALES
        logger.info(f"Analizando datos actuales del cierre {cierre_id}")
        
        # Contar empleados actuales
        empleados_actuales = EmpleadoCierre.objects.filter(cierre=cierre).count()
        
        # Contar ingresos actuales
        ingresos_actuales = AnalistaIngreso.objects.filter(cierre=cierre).count()
        
        # Contar finiquitos actuales
        finiquitos_actuales = AnalistaFiniquito.objects.filter(cierre=cierre).count()
        
        # Contar ausentismos actuales por tipo
        ausentismos_actuales = AnalistaIncidencia.objects.filter(cierre=cierre)
        ausentismos_por_tipo_actual = {}
        ausentismos_total_actual = 0
        
        for ausentismo in ausentismos_actuales:
            tipo = ausentismo.tipo_ausentismo or 'Sin especificar'
            ausentismos_por_tipo_actual[tipo] = ausentismos_por_tipo_actual.get(tipo, 0) + 1
            ausentismos_total_actual += 1
        
        # 2. ANÁLISIS DE DATOS MES ANTERIOR
        logger.info(f"Analizando datos del mes anterior para cliente {cierre.cliente.id}")
        
        # Obtener cierre del mes anterior
        cierre_anterior = CierreNomina.objects.filter(
            cliente=cierre.cliente,
            periodo__lt=cierre.periodo
        ).order_by('-periodo').first()
        
        empleados_anterior = 0
        ingresos_anterior = 0
        finiquitos_anterior = 0
        ausentismos_por_tipo_anterior = {}
        ausentismos_total_anterior = 0
        
        if cierre_anterior:
            empleados_anterior = EmpleadoCierre.objects.filter(cierre=cierre_anterior).count()
            ingresos_anterior = AnalistaIngreso.objects.filter(cierre=cierre_anterior).count()
            finiquitos_anterior = AnalistaFiniquito.objects.filter(cierre=cierre_anterior).count()
            
            ausentismos_anteriores = AnalistaIncidencia.objects.filter(cierre=cierre_anterior)
            for ausentismo in ausentismos_anteriores:
                tipo = ausentismo.tipo_ausentismo or 'Sin especificar'
                ausentismos_por_tipo_anterior[tipo] = ausentismos_por_tipo_anterior.get(tipo, 0) + 1
                ausentismos_total_anterior += 1
        
        # 3. ACTUALIZAR ANÁLISIS CON DATOS RECOPILADOS
        analisis.cantidad_empleados_actual = empleados_actuales
        analisis.cantidad_ingresos_actual = ingresos_actuales
        analisis.cantidad_finiquitos_actual = finiquitos_actuales
        analisis.cantidad_ausentismos_actual = ausentismos_total_actual
        
        analisis.cantidad_empleados_anterior = empleados_anterior
        analisis.cantidad_ingresos_anterior = ingresos_anterior
        analisis.cantidad_finiquitos_anterior = finiquitos_anterior
        analisis.cantidad_ausentismos_anterior = ausentismos_total_anterior
        
        analisis.ausentismos_por_tipo_actual = ausentismos_por_tipo_actual
        analisis.ausentismos_por_tipo_anterior = ausentismos_por_tipo_anterior
        
        analisis.save()
        
        logger.info(f"Datos recopilados - Empleados: {empleados_actuales}, "
                   f"Ingresos: {ingresos_actuales}, Finiquitos: {finiquitos_actuales}, "
                   f"Ausentismos: {ausentismos_total_actual}")
        
        # 4. GENERAR INCIDENCIAS DE VARIACIÓN SALARIAL
        logger.info(f"Generando incidencias de variación salarial con tolerancia {tolerancia_variacion}%")
        
        # Limpiar incidencias existentes
        IncidenciaVariacionSalarial.objects.filter(cierre=cierre).delete()
        
        if cierre_anterior:
            # Obtener empleados de ambos meses
            empleados_actual = EmpleadoCierre.objects.filter(cierre=cierre).select_related('empleado')
            empleados_anterior = EmpleadoCierre.objects.filter(cierre=cierre_anterior).select_related('empleado')
            
            # Crear mapas por RUT
            empleados_actual_map = {emp.rut: emp for emp in empleados_actual}
            empleados_anterior_map = {emp.rut: emp for emp in empleados_anterior}
            
            incidencias_creadas = 0
            
            # Comparar empleados que existen en ambos meses
            for rut, empleado_actual in empleados_actual_map.items():
                if rut in empleados_anterior_map:
                    empleado_anterior = empleados_anterior_map[rut]
                    
                    sueldo_actual = empleado_actual.sueldo_base or 0
                    sueldo_anterior = empleado_anterior.sueldo_base or 0
                    
                    if sueldo_anterior > 0:  # Evitar división por cero
                        variacion = ((sueldo_actual - sueldo_anterior) / sueldo_anterior) * 100
                        
                        if abs(variacion) > tolerancia_variacion:
                            # Crear incidencia
                            IncidenciaVariacionSalarial.objects.create(
                                analisis=analisis,
                                cierre=cierre,
                                rut_empleado=rut,
                                nombre_empleado=empleado_actual.nombre_completo,
                                sueldo_base_actual=sueldo_actual,
                                sueldo_base_anterior=sueldo_anterior,
                                porcentaje_variacion=Decimal(str(round(variacion, 2))),
                                tipo_variacion='aumento' if variacion > 0 else 'disminucion',
                                estado='pendiente'
                            )
                            incidencias_creadas += 1
            
            logger.info(f"Creadas {incidencias_creadas} incidencias de variación salarial")
        
        # 5. FINALIZAR ANÁLISIS
        analisis.estado = 'completado'
        analisis.fecha_completado = timezone.now()
        analisis.save()
        
        # 6. ACTUALIZAR ESTADO DEL CIERRE
        incidencias_variacion_count = IncidenciaVariacionSalarial.objects.filter(cierre=cierre).count()
        
        if incidencias_variacion_count > 0:
            # Hay incidencias de variación salarial que resolver
            cierre.estado = 'validacion_incidencias'
            cierre.estado_incidencias = 'en_revision'
        else:
            # No hay incidencias de variación salarial
            cierre.estado = 'listo_para_entrega'
            cierre.estado_incidencias = 'resueltas'
        
        cierre.save(update_fields=['estado', 'estado_incidencias'])
        
        logger.info(f"Análisis completado para cierre {cierre_id}. Estado: {cierre.estado}, Estado incidencias: {cierre.estado_incidencias}")
        
        return {
            "cierre_id": cierre_id,
            "analisis_id": analisis.id,
            "empleados_actual": empleados_actuales,
            "empleados_anterior": empleados_anterior,
            "ingresos_actual": ingresos_actuales,
            "finiquitos_actual": finiquitos_actuales,
            "ausentismos_actual": ausentismos_total_actual,
            "incidencias_variacion_creadas": incidencias_variacion_count,
            "estado": "completado",
            "estado_incidencias": cierre.estado_incidencias
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de datos para cierre {cierre_id}: {e}")
        
        # Marcar análisis como error
        try:
            analisis = AnalisisDatosCierre.objects.get(cierre_id=cierre_id)
            analisis.estado = 'error'
            analisis.save()
        except:
            pass
            
        raise


# ===== TAREAS PARA SISTEMA DE DISCREPANCIAS (VERIFICACIÓN DE DATOS) =====

@shared_task
def generar_discrepancias_cierre_task(cierre_id):
    """
    Tarea para generar discrepancias en la verificación de datos de un cierre.
    Sistema simplificado - solo detecta y registra diferencias.
    """
    from .utils.GenerarDiscrepancias import generar_todas_discrepancias
    from .models import CierreNomina
    
    logger.info(f"Iniciando generación de discrepancias para cierre {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Cambiar estado a verificacion_datos al iniciar
        cierre.estado = 'verificacion_datos'
        cierre.save(update_fields=['estado'])
        
        # Verificar que el cierre tenga los archivos necesarios procesados
        if not _verificar_archivos_listos_para_discrepancias(cierre):
            raise ValueError("No todos los archivos están procesados para generar discrepancias")
        
        # Eliminar discrepancias anteriores si existen
        cierre.discrepancias.all().delete()
        
        # Generar nuevas discrepancias
        resultado = generar_todas_discrepancias(cierre)
        
        # Actualizar estado del cierre
        if resultado['total_discrepancias'] == 0:
            # Sin discrepancias - datos verificados
            cierre.estado = 'verificado_sin_discrepancias'
        else:
            # Con discrepancias - requiere corrección
            cierre.estado = 'con_discrepancias'
        
        cierre.save(update_fields=['estado'])
        
        logger.info(f"Discrepancias generadas exitosamente para cierre {cierre_id}: {resultado['total_discrepancias']} discrepancias")
        return resultado
        
    except Exception as e:
        logger.error(f"Error generando discrepancias para cierre {cierre_id}: {e}")
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'archivos_completos'  # Volver al estado anterior correcto
            cierre.save(update_fields=['estado'])
        except:
            pass
        raise

def _verificar_archivos_listos_para_discrepancias(cierre):
    """Verifica que los archivos necesarios estén procesados para generar discrepancias"""
    from .models import LibroRemuneracionesUpload, MovimientosMesUpload
    
    # Verificar libro de remuneraciones procesado
    libro = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
    if not libro or libro.estado not in ['clasificado', 'procesado']:
        logger.warning(f"Libro de remuneraciones no procesado para cierre {cierre.id}")
        return False
    
    # Verificar movimientos del mes procesados
    movimientos = MovimientosMesUpload.objects.filter(cierre=cierre).first()
    if not movimientos or movimientos.estado != 'procesado':
        logger.warning(f"Movimientos del mes no procesados para cierre {cierre.id}")
        return False
    
    # Verificar al menos un archivo del analista procesado
    archivos_analista = cierre.archivos_analista.filter(estado='procesado')
    if archivos_analista.count() == 0:
        logger.warning(f"No hay archivos del analista procesados para cierre {cierre.id}")
        return False
    
    # Archivo de novedades es opcional - si existe debe estar procesado
    archivo_novedades = cierre.archivos_novedades.first()
    if archivo_novedades and archivo_novedades.estado not in ['clasificado', 'procesado']:
        logger.warning(f"Archivo de novedades no procesado para cierre {cierre.id}")
        return False
    
    return True


# ===== TAREAS PARA CONSOLIDACIÓN DE INFORMACIÓN =====

@shared_task
def consolidar_cierre_task(cierre_id, usuario_id=None):
    """
    🎯 TASK PARA CONSOLIDAR INFORMACIÓN DE UN CIERRE
    
    Ejecuta el proceso de consolidación después de resolver discrepancias.
    """
    from .utils.ConsolidarInformacion import consolidar_cierre_completo
    from .models import CierreNomina
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    usuario = None
    if usuario_id:
        try:
            usuario = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            pass
    
    logger.info(f"🚀 Iniciando consolidación para cierre {cierre_id}")
    
    try:
        # Ejecutar consolidación
        resultado = consolidar_cierre_completo(cierre_id, usuario)
        
        logger.info(f"✅ Consolidación exitosa para cierre {cierre_id}: {resultado['estadisticas']}")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en consolidación de cierre {cierre_id}: {e}")
        
        # Marcar cierre con error
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado_consolidacion = 'error_consolidacion'
            cierre.save(update_fields=['estado_consolidacion'])
        except:
            pass
            
        raise


@shared_task
def generar_incidencias_consolidadas_task(cierre_id):
    """
    Tarea para generar incidencias de un cierre consolidado
    """
    from .utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidadas_task as detectar_incidencias
    
    logger.info(f"🔍 Iniciando detección de incidencias consolidadas para cierre {cierre_id}")
    
    try:
        # Ejecutar detección de incidencias
        resultado = detectar_incidencias(cierre_id)
        
        if resultado['success']:
            logger.info(f"✅ Detección exitosa para cierre {cierre_id}: {resultado['total_incidencias']} incidencias")
        else:
            logger.error(f"❌ Error en detección para cierre {cierre_id}: {resultado.get('error', 'Error desconocido')}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error crítico en detección de incidencias para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def consolidar_datos_nomina_task_optimizado(cierre_id):
    """
    🚀 TAREA OPTIMIZADA: CONSOLIDACIÓN DE DATOS DE NÓMINA CON CELERY CHORD
    
    Utiliza paralelización para optimizar el proceso de consolidación:
    1. Ejecuta tareas en paralelo usando chord
    2. Consolida resultados al final
    3. Reduce significativamente el tiempo de procesamiento
    """
    import logging
    from django.utils import timezone
    from celery import chord
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Iniciando consolidación OPTIMIZADA de datos para cierre {cierre_id}")
    
    try:
        # 1. VERIFICAR PRERREQUISITOS
        from .models import CierreNomina, NominaConsolidada, HeaderValorEmpleado, MovimientoPersonal
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        logger.info(f"📋 Cierre obtenido: {cierre} - Estado: {cierre.estado}")
        
        # Verificar estado
        if cierre.estado not in ['verificado_sin_discrepancias', 'datos_consolidados']:
            raise ValueError(f"El cierre debe estar en 'verificado_sin_discrepancias' o 'datos_consolidados', actual: {cierre.estado}")
        
        # Cambiar estado a procesando
        cierre.estado = 'consolidando'
        cierre.save(update_fields=['estado'])
        
        # 2. VERIFICAR ARCHIVOS PROCESADOS
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        if not movimientos:
            raise ValueError("No hay archivo de movimientos procesado")
            
        logger.info(f"📚 Libro: {libro.archivo.name}")
        logger.info(f"🔄 Movimientos: {movimientos.archivo.name}")
        
        # 3. LIMPIAR CONSOLIDACIÓN ANTERIOR (SI EXISTE)
        consolidaciones_eliminadas = cierre.nomina_consolidada.count()
        if consolidaciones_eliminadas > 0:
            logger.info(f"🗑️ Eliminando {consolidaciones_eliminadas} registros de consolidación anterior...")
            # Limpiar también MovimientoPersonal relacionados
            movimientos_eliminados = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).count()
            MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).delete()
            
            cierre.nomina_consolidada.all().delete()
            logger.info(f"✅ {consolidaciones_eliminadas} registros de consolidación anterior eliminados exitosamente")
            logger.info(f"✅ {movimientos_eliminados} movimientos de personal anteriores eliminados exitosamente")
        else:
            logger.info("ℹ️ No hay consolidación anterior que eliminar")
        
        # 3.5. CÁLCULO DINÁMICO DE CHUNKS
        from .models import EmpleadoCierre
        empleados_count = EmpleadoCierre.objects.filter(cierre=cierre).count()
        chunk_size = calcular_chunk_size_dinamico(empleados_count)
        logger.info(f"📊 Procesando {empleados_count} empleados con chunk size dinámico: {chunk_size}")
        
        # 4. INICIAR PROCESAMIENTO PARALELO CON CHORD
        logger.info("🎯 Iniciando procesamiento paralelo con Celery Chord...")
        
        # Definir el chord con tareas que pueden ejecutarse realmente en paralelo
        # NOTA: procesar_conceptos_consolidados_paralelo se ejecutará en consolidar_resultados_finales
        chord_procesamiento = chord([
            procesar_empleados_libro_paralelo.s(cierre_id, chunk_size),
            procesar_movimientos_personal_paralelo.s(cierre_id)
        ])(consolidar_resultados_finales.s(cierre_id))
        
        logger.info(f"📊 Chord de consolidación iniciado para cierre {cierre_id}")
        logger.info(f"🔗 Chord ID: {chord_procesamiento}")
        logger.info("📝 Nota: Conceptos consolidados se procesarán después de empleados")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'chord_id': str(chord_procesamiento),
            'modo': 'optimizado_paralelo',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en consolidación optimizada para cierre {cierre_id}: {e}")
        
        # Revertir estado en caso de error
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.save(update_fields=['estado'])
        except:
            pass
            
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'modo': 'optimizado_paralelo'
        }


@shared_task
def procesar_empleados_libro_paralelo(cierre_id, chunk_size=50):
    """
    📚 TAREA PARALELA: Procesar empleados del libro de remuneraciones
    
    Args:
        cierre_id: ID del cierre a procesar
        chunk_size: Tamaño dinámico de chunks para optimizar el procesamiento
    """
    import logging
    from django.utils import timezone
    from decimal import Decimal, InvalidOperation
    
    logger = logging.getLogger(__name__)
    logger.info(f"📚 [PARALELO] Procesando empleados del libro para cierre {cierre_id} (chunk_size: {chunk_size})")
    
    try:
        from .models import CierreNomina, NominaConsolidada, HeaderValorEmpleado
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        
        empleados_consolidados = 0
        headers_consolidados = 0
        
        # Procesar empleados del libro en lotes para optimizar
        empleados = cierre.empleados.all()
        total_empleados = empleados.count()
        logger.info(f"👥 Procesando {total_empleados} empleados en lotes (chunk_size: {chunk_size})")
        
        # Procesar en lotes usando el chunk_size dinámico
        for i in range(0, total_empleados, chunk_size):
            batch_empleados = empleados[i:i + chunk_size]
            
            # Crear registros de nómina consolidada en lote
            nominas_batch = []
            headers_batch = []
            
            for empleado in batch_empleados:
                # Crear registro de nómina consolidada
                nomina_consolidada = NominaConsolidada(
                    cierre=cierre,
                    rut_empleado=empleado.rut,
                    nombre_empleado=f"{empleado.nombre} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                    estado_empleado='activo',
                    dias_trabajados=empleado.dias_trabajados,
                    fecha_consolidacion=timezone.now(),
                    fuente_datos={
                        'libro_id': libro.id,
                        'consolidacion_version': '2.0_optimizada',
                        'procesamiento': 'paralelo'
                    }
                )
                nominas_batch.append(nomina_consolidada)
            
            # Bulk create nóminas
            NominaConsolidada.objects.bulk_create(nominas_batch)
            empleados_consolidados += len(nominas_batch)
            
            # Procesar headers para este lote
            for j, empleado in enumerate(batch_empleados):
                nomina_consolidada = nominas_batch[j]
                # Necesitamos obtener el ID después del bulk_create
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=empleado.rut
                )
                
                # Crear HeaderValorEmpleado para cada concepto
                conceptos_empleado = empleado.registroconceptoempleado_set.all()
                
                for concepto in conceptos_empleado:
                    # Determinar si es numérico
                    valor_numerico = None
                    es_numerico = False
                    
                    if concepto.monto:
                        try:
                            # Limpiar el valor mejorado
                            valor_limpio = str(concepto.monto).replace('$', '').replace(',', '').strip()
                            if valor_limpio and (valor_limpio.replace('-', '').replace('.', '').isdigit()):
                                valor_numerico = Decimal(valor_limpio)
                                es_numerico = True
                        except (ValueError, InvalidOperation, AttributeError):
                            pass
                    
                    # Crear registro HeaderValorEmpleado
                    header = HeaderValorEmpleado(
                        nomina_consolidada=nomina_consolidada,
                        nombre_header=concepto.nombre_concepto_original,
                        concepto_remuneracion=concepto.concepto,
                        valor_original=concepto.monto or '',
                        valor_numerico=valor_numerico,
                        es_numerico=es_numerico,
                        fuente_archivo='libro_remuneraciones',
                        fecha_consolidacion=timezone.now()
                    )
                    headers_batch.append(header)
            
            # Bulk create headers cada cierto número para evitar memoria excesiva
            if len(headers_batch) >= 500:
                HeaderValorEmpleado.objects.bulk_create(headers_batch)
                headers_consolidados += len(headers_batch)
                headers_batch = []
                
            logger.info(f"📊 Progreso: {empleados_consolidados}/{total_empleados} empleados procesados")
        
        # Insertar headers restantes
        if headers_batch:
            HeaderValorEmpleado.objects.bulk_create(headers_batch)
            headers_consolidados += len(headers_batch)
        
        logger.info(f"✅ [PARALELO] Empleados procesados: {empleados_consolidados}, Headers: {headers_consolidados}")
        
        return {
            'success': True,
            'task': 'procesar_empleados_libro',
            'empleados_consolidados': empleados_consolidados,
            'headers_consolidados': headers_consolidados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando empleados para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_empleados_libro',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_movimientos_personal_paralelo(cierre_id):
    """
    🔄 TAREA PARALELA: Procesar movimientos de personal
    """
    import logging
    from django.utils import timezone
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 [PARALELO] Procesando movimientos de personal para cierre {cierre_id}")
    
    try:
        from .models import (
            CierreNomina, NominaConsolidada, MovimientoPersonal,
            MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
            MovimientoVariacionSueldo, MovimientoVariacionContrato
        )
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        movimientos_creados = 0
        
        # Verificar si hay archivo de movimientos procesado
        movimientos_archivo = cierre.movimientos_mes.filter(estado='procesado').first()
        if not movimientos_archivo:
            logger.warning(f"⚠️ [PARALELO] No hay archivo de movimientos procesado para cierre {cierre_id}")
            return {
                'success': True,
                'task': 'procesar_movimientos_personal',
                'movimientos_creados': 0,
                'cierre_id': cierre_id,
                'info': 'No hay archivo de movimientos procesado'
            }
        
        logger.info(f"📁 [PARALELO] Archivo de movimientos encontrado: {movimientos_archivo.archivo.name}")
        
        # Crear lista para bulk_create y contadores
        movimientos_batch = []
        contador_altas_bajas = 0
        contador_ausentismos = 0
        contador_vacaciones = 0
        contador_variaciones_sueldo = 0
        contador_variaciones_contrato = 0
        
        # 1. Procesar ALTAS y BAJAS
        altas_bajas = MovimientoAltaBaja.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {altas_bajas.count()} registros de altas/bajas en BD")
        
        for movimiento in altas_bajas:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=movimiento.rut
                )
                
                # Actualizar estado del empleado
                if movimiento.alta_o_baja == 'ALTA':
                    nomina_consolidada.estado_empleado = 'nueva_incorporacion'
                elif movimiento.alta_o_baja == 'BAJA':
                    nomina_consolidada.estado_empleado = 'finiquito'
                
                nomina_consolidada.save(update_fields=['estado_empleado'])
                
                # Crear MovimientoPersonal
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='ingreso' if movimiento.alta_o_baja == 'ALTA' else 'finiquito',
                    motivo=movimiento.motivo,
                    fecha_movimiento=movimiento.fecha_ingreso if movimiento.alta_o_baja == 'ALTA' else movimiento.fecha_retiro,
                    observaciones=f"Tipo contrato: {movimiento.tipo_contrato}, Sueldo base: ${movimiento.sueldo_base:,.0f}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_paralela_v2'
                )
                movimientos_batch.append(mov_personal)
                contador_altas_bajas += 1
                
            except NominaConsolidada.DoesNotExist:
                # Crear empleado si no existe (caso de finiquitos)
                if movimiento.alta_o_baja == 'BAJA':
                    nomina_consolidada = NominaConsolidada.objects.create(
                        cierre=cierre,
                        rut_empleado=movimiento.rut,
                        nombre_empleado=movimiento.nombres_apellidos,
                        estado_empleado='finiquito',
                        fecha_consolidacion=timezone.now(),
                        fuente_datos={'movimiento_finiquito': True}
                    )
                    
                    mov_personal = MovimientoPersonal(
                        nomina_consolidada=nomina_consolidada,
                        tipo_movimiento='finiquito',
                        motivo=movimiento.motivo,
                        fecha_movimiento=movimiento.fecha_retiro,
                        fecha_deteccion=timezone.now(),
                        detectado_por_sistema='consolidacion_paralela_v2'
                    )
                    movimientos_batch.append(mov_personal)
                    contador_altas_bajas += 1
        
        logger.info(f"✅ [PARALELO] {contador_altas_bajas} movimientos de altas/bajas procesados")
        
        # 2. Procesar AUSENTISMOS
        ausentismos = MovimientoAusentismo.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {ausentismos.count()} registros de ausentismo en BD")
        
        for ausentismo in ausentismos:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=ausentismo.rut
                )
                
                # Actualizar estado si es ausencia total
                if ausentismo.dias >= 30:
                    nomina_consolidada.estado_empleado = 'ausente_total'
                    nomina_consolidada.dias_ausencia = ausentismo.dias
                else:
                    nomina_consolidada.estado_empleado = 'ausente_parcial'
                    nomina_consolidada.dias_ausencia = ausentismo.dias
                
                nomina_consolidada.save(update_fields=['estado_empleado', 'dias_ausencia'])
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='ausentismo',
                    motivo=f"{ausentismo.tipo} - {ausentismo.motivo}",
                    dias_ausencia=ausentismo.dias,
                    fecha_movimiento=ausentismo.fecha_inicio_ausencia,
                    observaciones=f"Desde: {ausentismo.fecha_inicio_ausencia} hasta: {ausentismo.fecha_fin_ausencia}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_paralela_v2'
                )
                movimientos_batch.append(mov_personal)
                contador_ausentismos += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {ausentismo.rut} en ausentismo")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_ausentismos} movimientos de ausentismo procesados")
        
        # 3. Procesar VACACIONES
        vacaciones = MovimientoVacaciones.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {vacaciones.count()} registros de vacaciones en BD")
        
        for vacacion in vacaciones:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=vacacion.rut
                )
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='ausentismo',
                    motivo='Vacaciones',
                    dias_ausencia=vacacion.cantidad_dias,
                    fecha_movimiento=vacacion.fecha_inicio,
                    observaciones=f"Vacaciones desde: {vacacion.fecha_inicio} hasta: {vacacion.fecha_fin_vacaciones}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_paralela_v2'
                )
                movimientos_batch.append(mov_personal)
                contador_vacaciones += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {vacacion.rut} en vacaciones")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_vacaciones} movimientos de vacaciones procesados")
        
        # 4. Procesar VARIACIONES DE SUELDO
        variaciones_sueldo = MovimientoVariacionSueldo.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {variaciones_sueldo.count()} registros de variaciones de sueldo en BD")
        
        for variacion in variaciones_sueldo:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=variacion.rut
                )
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='cambio_sueldo',
                    motivo=f"Cambio de sueldo: {variacion.motivo}",
                    fecha_movimiento=variacion.fecha_cambio,
                    observaciones=f"De ${variacion.sueldo_anterior:,.0f} a ${variacion.sueldo_nuevo:,.0f}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_paralela_v2'
                )
                movimientos_batch.append(mov_personal)
                contador_variaciones_sueldo += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación sueldo")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_variaciones_sueldo} movimientos de variación de sueldo procesados")
        
        # 5. Procesar VARIACIONES DE CONTRATO
        variaciones_contrato = MovimientoVariacionContrato.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {variaciones_contrato.count()} registros de variaciones de contrato en BD")
        
        for variacion in variaciones_contrato:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=variacion.rut
                )
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='cambio_contrato',
                    motivo=f"Cambio de contrato: {variacion.motivo}",
                    fecha_movimiento=variacion.fecha_cambio,
                    observaciones=f"De {variacion.tipo_contrato_anterior} a {variacion.tipo_contrato_nuevo}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_paralela_v2'
                )
                movimientos_batch.append(mov_personal)
                contador_variaciones_contrato += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación contrato")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_variaciones_contrato} movimientos de variación de contrato procesados")
        
        # Bulk create movimientos en lotes
        if movimientos_batch:
            batch_size = 100
            for i in range(0, len(movimientos_batch), batch_size):
                batch = movimientos_batch[i:i + batch_size]
                MovimientoPersonal.objects.bulk_create(batch)
                movimientos_creados += len(batch)
        
        # Resumen detallado
        total_tipos = contador_altas_bajas + contador_ausentismos + contador_vacaciones + contador_variaciones_sueldo + contador_variaciones_contrato
        logger.info(f"📋 [PARALELO] RESUMEN DETALLADO DE MOVIMIENTOS:")
        logger.info(f"    ⬆️ Altas/Bajas: {contador_altas_bajas}")
        logger.info(f"    🏥 Ausentismos: {contador_ausentismos}")
        logger.info(f"    🏖️ Vacaciones: {contador_vacaciones}")
        logger.info(f"    💰 Variaciones Sueldo: {contador_variaciones_sueldo}")
        logger.info(f"    📑 Variaciones Contrato: {contador_variaciones_contrato}")
        logger.info(f"    📊 TOTAL TIPOS: {total_tipos}")
        logger.info(f"    ✅ TOTAL CREADOS: {movimientos_creados}")
        
        if total_tipos != movimientos_creados:
            logger.warning(f"⚠️ [PARALELO] DISCREPANCIA: {total_tipos} tipos procesados vs {movimientos_creados} movimientos creados")
        
        return {
            'success': True,
            'task': 'procesar_movimientos_personal',
            'movimientos_creados': movimientos_creados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando movimientos para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_movimientos_personal',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_conceptos_consolidados_paralelo(cierre_id):
    """
    💰 TAREA PARALELA: Procesar conceptos consolidados y calcular totales
    """
    import logging
    from django.utils import timezone
    from decimal import Decimal
    
    logger = logging.getLogger(__name__)
    logger.info(f"💰 [PARALELO] Procesando conceptos consolidados para cierre {cierre_id}")
    
    try:
        from .models import CierreNomina, NominaConsolidada, HeaderValorEmpleado, ConceptoConsolidado
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        conceptos_consolidados = 0
        
        # Obtener todas las nóminas consolidadas
        nominas = NominaConsolidada.objects.filter(cierre=cierre).prefetch_related(
            'header_valores__concepto_remuneracion'
        )
        
        conceptos_batch = []
        
        logger.info(f"📊 Procesando conceptos para {nominas.count()} empleados")
        
        for nomina_consolidada in nominas:
            # Obtener todos los headers para este empleado
            headers_empleado = nomina_consolidada.header_valores.filter(
                es_numerico=True,
                concepto_remuneracion__isnull=False
            )
            
            total_haberes = Decimal('0')
            total_descuentos = Decimal('0')
            
            # Agrupar por concepto y sumar
            conceptos_agrupados = {}
            
            for header in headers_empleado:
                concepto_nombre = header.concepto_remuneracion.nombre_concepto
                clasificacion = header.concepto_remuneracion.clasificacion
                
                if concepto_nombre not in conceptos_agrupados:
                    conceptos_agrupados[concepto_nombre] = {
                        'clasificacion': clasificacion,
                        'monto_total': Decimal('0'),
                        'cantidad': 0,
                        'concepto_obj': header.concepto_remuneracion
                    }
                
                conceptos_agrupados[concepto_nombre]['monto_total'] += header.valor_numerico
                conceptos_agrupados[concepto_nombre]['cantidad'] += 1
                
                # Sumar a haberes o descuentos según clasificación
                if clasificacion in ['haberes_imponibles', 'haberes_no_imponibles', 'horas_extras']:
                    total_haberes += header.valor_numerico
                elif clasificacion in ['descuentos_legales', 'otros_descuentos']:
                    total_descuentos += header.valor_numerico
            
            # Crear ConceptoConsolidado para cada concepto agrupado
            for concepto_nombre, datos in conceptos_agrupados.items():
                # Mapear clasificación a tipo_concepto
                clasificacion_mapping = {
                    'haberes_imponibles': 'haber_imponible',
                    'haberes_no_imponibles': 'haber_no_imponible',
                    'descuentos_legales': 'descuento_legal',
                    'otros_descuentos': 'otro_descuento'
                }
                
                tipo_concepto = clasificacion_mapping.get(datos['clasificacion'], 'informativo')
                codigo_concepto = str(datos['concepto_obj'].id) if datos['concepto_obj'] else None
                
                concepto_consolidado = ConceptoConsolidado(
                    nomina_consolidada=nomina_consolidada,
                    codigo_concepto=codigo_concepto,
                    nombre_concepto=concepto_nombre,
                    tipo_concepto=tipo_concepto,
                    monto_total=datos['monto_total'],
                    cantidad=datos['cantidad'],
                    es_numerico=True,
                    fuente_archivo='libro_remuneraciones'
                )
                conceptos_batch.append(concepto_consolidado)
            
            # Actualizar totales en la nómina consolidada
            nomina_consolidada.total_haberes = total_haberes
            nomina_consolidada.total_descuentos = total_descuentos
            nomina_consolidada.liquido_pagar = total_haberes - total_descuentos
            nomina_consolidada.save(update_fields=['total_haberes', 'total_descuentos', 'liquido_pagar'])
        
        # Bulk create conceptos
        if conceptos_batch:
            batch_size = 200
            for i in range(0, len(conceptos_batch), batch_size):
                batch = conceptos_batch[i:i + batch_size]
                ConceptoConsolidado.objects.bulk_create(batch)
                conceptos_consolidados += len(batch)
        
        logger.info(f"✅ [PARALELO] Conceptos consolidados procesados: {conceptos_consolidados}")
        
        return {
            'success': True,
            'task': 'procesar_conceptos_consolidados',
            'conceptos_consolidados': conceptos_consolidados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando conceptos para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_conceptos_consolidados',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def consolidar_resultados_finales(resultados_paralelos, cierre_id):
    """
    🎯 TAREA FINAL: Consolidar resultados de todas las tareas paralelas
    """
    import logging
    from django.utils import timezone
    
    logger = logging.getLogger(__name__)
    logger.info(f"🎯 [FINAL] Consolidando resultados finales para cierre {cierre_id}")
    
    try:
        from .models import CierreNomina
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Procesar resultados de todas las tareas paralelas
        empleados_consolidados = 0
        headers_consolidados = 0
        movimientos_creados = 0
        conceptos_consolidados = 0
        
        errores = []
        tareas_exitosas = 0
        
        for resultado in resultados_paralelos:
            if resultado.get('success', False):
                tareas_exitosas += 1
                task_name = resultado.get('task', 'unknown')
                
                if task_name == 'procesar_empleados_libro':
                    empleados_consolidados = resultado.get('empleados_consolidados', 0)
                    headers_consolidados = resultado.get('headers_consolidados', 0)
                elif task_name == 'procesar_movimientos_personal':
                    movimientos_creados = resultado.get('movimientos_creados', 0)
                elif task_name == 'procesar_conceptos_consolidados':
                    conceptos_consolidados = resultado.get('conceptos_consolidados', 0)
                    
                logger.info(f"✅ Tarea {task_name} completada exitosamente")
            else:
                error = resultado.get('error', 'Error desconocido')
                task_name = resultado.get('task', 'unknown')
                errores.append(f"{task_name}: {error}")
                logger.error(f"❌ Error en tarea {task_name}: {error}")
        
        # Verificar si todas las tareas fueron exitosas
        if len(errores) > 0:
            logger.error(f"❌ Consolidación falló. Errores en {len(errores)} tareas:")
            for error in errores:
                logger.error(f"  - {error}")
            
            # Cambiar estado a error
            cierre.estado = 'error_consolidacion'
            cierre.save(update_fields=['estado'])
            
            return {
                'success': False,
                'cierre_id': cierre_id,
                'errores': errores,
                'tareas_exitosas': tareas_exitosas,
                'total_tareas': len(resultados_paralelos)
            }
        
        # 🎯 EJECUTAR PROCESAMIENTO DE CONCEPTOS CONSOLIDADOS
        # (Ahora que los empleados ya están consolidados)
        logger.info("💰 [FINAL] Iniciando procesamiento de conceptos consolidados...")
        try:
            resultado_conceptos = procesar_conceptos_consolidados_paralelo(cierre_id)
            if resultado_conceptos.get('success', False):
                conceptos_consolidados = resultado_conceptos.get('conceptos_consolidados', 0)
                logger.info(f"✅ [FINAL] Conceptos consolidados procesados: {conceptos_consolidados}")
            else:
                logger.error(f"❌ [FINAL] Error procesando conceptos: {resultado_conceptos.get('error', 'Error desconocido')}")
                conceptos_consolidados = 0
        except Exception as e:
            logger.error(f"❌ [FINAL] Excepción procesando conceptos: {e}")
            conceptos_consolidados = 0
        
        # FINALIZAR CONSOLIDACIÓN EXITOSA
        cierre.estado = 'datos_consolidados'
        cierre.fecha_consolidacion = timezone.now()
        cierre.save(update_fields=['estado', 'fecha_consolidacion'])
        
        logger.info(f"✅ [FINAL] Consolidación OPTIMIZADA completada exitosamente:")
        logger.info(f"   📊 {empleados_consolidados} empleados consolidados")
        logger.info(f"   📋 {headers_consolidados} headers-valores creados")
        logger.info(f"   🔄 {movimientos_creados} movimientos de personal creados")
        logger.info(f"   💰 {conceptos_consolidados} conceptos consolidados creados")
        logger.info(f"   ⚡ Todas las tareas ejecutadas en PARALELO")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'modo': 'optimizado_paralelo',
            'empleados_consolidados': empleados_consolidados,
            'headers_consolidados': headers_consolidados,
            'movimientos_creados': movimientos_creados,
            'conceptos_consolidados': conceptos_consolidados,
            'tareas_exitosas': tareas_exitosas,
            'tiempo_finalizacion': timezone.now().isoformat(),
            'nuevo_estado': cierre.estado
        }
        
    except Exception as e:
        logger.error(f"❌ [FINAL] Error crítico consolidando resultados para cierre {cierre_id}: {e}")
        
        # Revertir estado en caso de error crítico
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.save(update_fields=['estado'])
        except:
            pass
            
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'modo': 'optimizado_paralelo'
        }


@shared_task
def consolidar_datos_nomina_task(cierre_id, modo='optimizado'):
    """
    🔄 TAREA: CONSOLIDACIÓN DE DATOS DE NÓMINA
    
    Ahora con soporte para dos modos:
    - 'optimizado': Usa Celery Chord para procesamiento paralelo (RECOMENDADO)
    - 'secuencial': Versión original con procesamiento secuencial
    
    Toma un cierre en estado 'verificado_sin_discrepancias' y:
    1. Lee los archivos procesados (Libro, Movimientos, Analista)
    2. Genera registros de NominaConsolidada
    3. Genera registros de HeaderValorEmpleado (mapeo 1:1 Excel)
    4. Genera registros de MovimientoPersonal
    5. Cambia estado a 'datos_consolidados'
    """
    import logging
    from django.utils import timezone
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Iniciando consolidación de datos para cierre {cierre_id} - Modo: {modo}")
    
    # Elegir versión según el modo
    if modo == 'optimizado':
        logger.info("🚀 Usando versión OPTIMIZADA con Celery Chord")
        return consolidar_datos_nomina_task_optimizado(cierre_id)
    else:
        logger.info("⏳ Usando versión SECUENCIAL (original)")
        return consolidar_datos_nomina_task_secuencial(cierre_id)


@shared_task
def consolidar_datos_nomina_task_secuencial(cierre_id):
    """
    🔄 TAREA: CONSOLIDACIÓN DE DATOS DE NÓMINA
    
    Toma un cierre en estado 'verificado_sin_discrepancias' y:
    1. Lee los archivos procesados (Libro, Movimientos, Analista)
    2. Genera registros de NominaConsolidada
    3. Genera registros de HeaderValorEmpleado (mapeo 1:1 Excel)
    4. Genera registros de MovimientoPersonal
    5. Cambia estado a 'datos_consolidados'
    """
    import logging
    from django.utils import timezone
    from decimal import Decimal, InvalidOperation
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Iniciando consolidación de datos para cierre {cierre_id}")
    
    try:
        # 1. OBTENER EL CIERRE
        from .models import CierreNomina, NominaConsolidada, HeaderValorEmpleado, MovimientoPersonal
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        logger.info(f"📋 Cierre obtenido: {cierre} - Estado: {cierre.estado}")
        
        # Verificar estado
        if cierre.estado not in ['verificado_sin_discrepancias', 'datos_consolidados']:
            raise ValueError(f"El cierre debe estar en 'verificado_sin_discrepancias' o 'datos_consolidados', actual: {cierre.estado}")
        
        # Cambiar estado a procesando
        cierre.estado = 'consolidando'
        cierre.save(update_fields=['estado'])
        
        # 2. OBTENER ARCHIVOS PROCESADOS
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        if not movimientos:
            raise ValueError("No hay archivo de movimientos procesado")
            
        logger.info(f"📚 Libro: {libro.archivo.name}")
        logger.info(f"🔄 Movimientos: {movimientos.archivo.name}")
        
        # 3. LIMPIAR CONSOLIDACIÓN ANTERIOR (SI EXISTE)
        consolidaciones_eliminadas = cierre.nomina_consolidada.count()
        if consolidaciones_eliminadas > 0:
            logger.info(f"🗑️ Eliminando {consolidaciones_eliminadas} registros de consolidación anterior...")
            # Limpiar también MovimientoPersonal relacionados
            from .models import MovimientoPersonal
            movimientos_eliminados = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).count()
            MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).delete()
            
            cierre.nomina_consolidada.all().delete()
            logger.info(f"✅ {consolidaciones_eliminadas} registros de consolidación anterior eliminados exitosamente")
            logger.info(f"✅ {movimientos_eliminados} movimientos de personal anteriores eliminados exitosamente")
        else:
            logger.info("ℹ️ No hay consolidación anterior que eliminar")
        
        logger.info("🔄 Iniciando nueva consolidación desde cero...")
        
        # 4. CONSOLIDAR DATOS DEL LIBRO DE REMUNERACIONES
        empleados_consolidados = 0
        headers_consolidados = 0
        
        # Obtener empleados del libro
        empleados = cierre.empleados.all()
        logger.info(f"👥 Procesando {empleados.count()} empleados")
        
        for empleado in empleados:
            # Crear registro de nómina consolidada
            nomina_consolidada = NominaConsolidada.objects.create(
                cierre=cierre,
                rut_empleado=empleado.rut,
                nombre_empleado=f"{empleado.nombre} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                estado_empleado='activo',  # TODO: Detectar estado según movimientos
                dias_trabajados=empleado.dias_trabajados,
                fecha_consolidacion=timezone.now(),
                fuente_datos={
                    'libro_id': libro.id,
                    'movimientos_id': movimientos.id,
                    'consolidacion_version': '1.0'
                }
            )
            
            # Obtener registros de conceptos del empleado
            conceptos_empleado = empleado.registroconceptoempleado_set.all()
            
            # Crear HeaderValorEmpleado para cada concepto
            for concepto in conceptos_empleado:
                # Determinar si es numérico
                valor_numerico = None
                es_numerico = False
                
                if concepto.monto:
                    try:
                        # Limpiar el valor (remover $, comas, pero MANTENER puntos decimales)
                        valor_limpio = str(concepto.monto).replace('$', '').replace(',', '').strip()
                        # Verificar si es un número válido (entero o decimal)
                        if valor_limpio and (valor_limpio.replace('-', '').replace('.', '').isdigit()):
                            valor_numerico = Decimal(valor_limpio)
                            es_numerico = True
                    except (ValueError, InvalidOperation, AttributeError):
                        pass
                
                # Crear registro HeaderValorEmpleado
                HeaderValorEmpleado.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    nombre_header=concepto.nombre_concepto_original,
                    concepto_remuneracion=concepto.concepto,
                    valor_original=concepto.monto or '',
                    valor_numerico=valor_numerico,
                    es_numerico=es_numerico,
                    fuente_archivo='libro_remuneraciones',
                    fecha_consolidacion=timezone.now()
                )
                headers_consolidados += 1
            
            empleados_consolidados += 1
            
            if empleados_consolidados % 100 == 0:
                logger.info(f"📊 Progreso: {empleados_consolidados} empleados consolidados")
        
        # 5. CONSOLIDAR MOVIMIENTOS DE PERSONAL
        movimientos_creados = 0
        
        # Importar modelos de movimientos
        from .models import (
            MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
            MovimientoVariacionSueldo, MovimientoVariacionContrato, ConceptoConsolidado
        )
        
        logger.info("🔄 Iniciando consolidación de movimientos de personal...")
        
        # 5.1 Procesar ALTAS y BAJAS (Ingresos y Finiquitos)
        altas_bajas = MovimientoAltaBaja.objects.filter(cierre=cierre)
        logger.info(f"📊 Procesando {altas_bajas.count()} movimientos de altas/bajas")
        
        for movimiento in altas_bajas:
            # Buscar o crear el empleado consolidado
            nomina_consolidada = None
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=movimiento.rut
                )
            except NominaConsolidada.DoesNotExist:
                # Si no existe, crear uno nuevo para este movimiento
                nomina_consolidada = NominaConsolidada.objects.create(
                    cierre=cierre,
                    rut_empleado=movimiento.rut,
                    nombre_empleado=movimiento.nombres_apellidos,
                    cargo=movimiento.cargo,
                    centro_costo=movimiento.centro_de_costo,
                    estado_empleado='nueva_incorporacion' if movimiento.alta_o_baja == 'ALTA' else 'finiquito',
                    dias_trabajados=movimiento.dias_trabajados,
                    total_haberes=movimiento.sueldo_base,
                    liquido_pagar=movimiento.sueldo_base,
                    fecha_consolidacion=timezone.now(),
                    fuente_datos={
                        'libro_id': libro.id,
                        'movimientos_id': movimientos.id,
                        'consolidacion_version': '1.0',
                        'movimiento_tipo': 'alta_baja'
                    }
                )
            
            # Actualizar estado según el movimiento
            if movimiento.alta_o_baja == 'ALTA':
                nomina_consolidada.estado_empleado = 'nueva_incorporacion'
            elif movimiento.alta_o_baja == 'BAJA':
                nomina_consolidada.estado_empleado = 'finiquito'
            
            nomina_consolidada.save(update_fields=['estado_empleado'])
            
            # Crear MovimientoPersonal
            MovimientoPersonal.objects.create(
                nomina_consolidada=nomina_consolidada,
                tipo_movimiento='ingreso' if movimiento.alta_o_baja == 'ALTA' else 'finiquito',
                motivo=movimiento.motivo,
                fecha_movimiento=movimiento.fecha_ingreso if movimiento.alta_o_baja == 'ALTA' else movimiento.fecha_retiro,
                observaciones=f"Tipo contrato: {movimiento.tipo_contrato}, Sueldo base: ${movimiento.sueldo_base:,.0f}",
                fecha_deteccion=timezone.now(),
                detectado_por_sistema='consolidacion_automatica_v1'
            )
            
            movimientos_creados += 1
        
        # 5.2 Procesar AUSENTISMOS
        ausentismos = MovimientoAusentismo.objects.filter(cierre=cierre)
        logger.info(f"📊 Procesando {ausentismos.count()} movimientos de ausentismo")
        
        for ausentismo in ausentismos:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=ausentismo.rut
                )
                
                # Actualizar estado si es ausencia total
                if ausentismo.dias >= 30:  # Más de 30 días = ausencia total
                    nomina_consolidada.estado_empleado = 'ausente_total'
                    nomina_consolidada.dias_ausencia = ausentismo.dias
                else:
                    nomina_consolidada.estado_empleado = 'ausente_parcial'
                    nomina_consolidada.dias_ausencia = ausentismo.dias
                
                nomina_consolidada.save(update_fields=['estado_empleado', 'dias_ausencia'])
                
                # Crear MovimientoPersonal
                MovimientoPersonal.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='ausentismo',
                    motivo=f"{ausentismo.tipo} - {ausentismo.motivo}",
                    dias_ausencia=ausentismo.dias,
                    fecha_movimiento=ausentismo.fecha_inicio_ausencia,
                    observaciones=f"Desde: {ausentismo.fecha_inicio_ausencia} hasta: {ausentismo.fecha_fin_ausencia}. {ausentismo.observaciones}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_automatica_v1'
                )
                
                movimientos_creados += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {ausentismo.rut} en ausentismo")
                continue
        
        # 5.3 Procesar VACACIONES
        vacaciones = MovimientoVacaciones.objects.filter(cierre=cierre)
        logger.info(f"📊 Procesando {vacaciones.count()} movimientos de vacaciones")
        
        for vacacion in vacaciones:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=vacacion.rut
                )
                
                # Crear MovimientoPersonal para vacaciones
                MovimientoPersonal.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='ausentismo',
                    motivo='Vacaciones',
                    dias_ausencia=vacacion.cantidad_dias,
                    fecha_movimiento=vacacion.fecha_inicio,
                    observaciones=f"Vacaciones desde: {vacacion.fecha_inicio} hasta: {vacacion.fecha_fin_vacaciones}. Retorno: {vacacion.fecha_retorno}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_automatica_v1'
                )
                
                movimientos_creados += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {vacacion.rut} en vacaciones")
                continue
        
        # 5.4 Procesar VARIACIONES DE SUELDO
        variaciones_sueldo = MovimientoVariacionSueldo.objects.filter(cierre=cierre)
        logger.info(f"📊 Procesando {variaciones_sueldo.count()} variaciones de sueldo")
        
        for variacion in variaciones_sueldo:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=variacion.rut
                )
                
                # Crear MovimientoPersonal
                MovimientoPersonal.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='cambio_datos',
                    motivo=f"Variación de sueldo: {variacion.porcentaje_reajuste}%",
                    fecha_movimiento=cierre.fecha_creacion.date(),
                    observaciones=f"Sueldo anterior: ${variacion.sueldo_base_anterior:,.0f} → Sueldo actual: ${variacion.sueldo_base_actual:,.0f} (Variación: ${variacion.variacion_pesos:,.0f})",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_automatica_v1'
                )
                
                movimientos_creados += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación de sueldo")
                continue
        
        # 5.5 Procesar VARIACIONES DE CONTRATO
        variaciones_contrato = MovimientoVariacionContrato.objects.filter(cierre=cierre)
        logger.info(f"📊 Procesando {variaciones_contrato.count()} variaciones de contrato")
        
        for variacion in variaciones_contrato:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=variacion.rut
                )
                
                # Crear MovimientoPersonal
                MovimientoPersonal.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    tipo_movimiento='cambio_datos',
                    motivo='Cambio de tipo de contrato',
                    fecha_movimiento=cierre.fecha_creacion.date(),
                    observaciones=f"Contrato anterior: {variacion.tipo_contrato_anterior} → Contrato actual: {variacion.tipo_contrato_actual}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_automatica_v1'
                )
                
                movimientos_creados += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación de contrato")
                continue
        
        # 5.6 CONSOLIDAR CONCEPTOS POR EMPLEADO
        logger.info("💰 Consolidando conceptos y totales por empleado...")
        conceptos_consolidados = 0
        
        for nomina_consolidada in NominaConsolidada.objects.filter(cierre=cierre):
            # Obtener todos los headers para este empleado
            headers_empleado = HeaderValorEmpleado.objects.filter(nomina_consolidada=nomina_consolidada)
            
            total_haberes = Decimal('0')
            total_descuentos = Decimal('0')
            
            # Agrupar por concepto y sumar
            conceptos_agrupados = {}
            
            for header in headers_empleado:
                if header.concepto_remuneracion and header.valor_numerico:
                    concepto_nombre = header.concepto_remuneracion.nombre_concepto  # Corregido: usar nombre_concepto
                    clasificacion = header.concepto_remuneracion.clasificacion
                    
                    if concepto_nombre not in conceptos_agrupados:
                        conceptos_agrupados[concepto_nombre] = {
                            'clasificacion': clasificacion,
                            'monto_total': Decimal('0'),
                            'cantidad': 0,
                            'concepto_obj': header.concepto_remuneracion
                        }
                    
                    conceptos_agrupados[concepto_nombre]['monto_total'] += header.valor_numerico
                    conceptos_agrupados[concepto_nombre]['cantidad'] += 1
                    
                    # Sumar a haberes o descuentos según clasificación
                    if clasificacion in ['haberes_imponibles', 'haberes_no_imponibles', 'horas_extras']:
                        total_haberes += header.valor_numerico
                    elif clasificacion in ['descuentos_legales', 'otros_descuentos']:
                        total_descuentos += header.valor_numerico
            
            # Crear ConceptoConsolidado para cada concepto agrupado
            for concepto_nombre, datos in conceptos_agrupados.items():
                # Mapear clasificación a tipo_concepto
                clasificacion_mapping = {
                    'haberes_imponibles': 'haber_imponible',
                    'haberes_no_imponibles': 'haber_no_imponible',
                    'descuentos_legales': 'descuento_legal',
                    'otros_descuentos': 'otro_descuento'
                }
                
                tipo_concepto = clasificacion_mapping.get(datos['clasificacion'], 'informativo')
                # ConceptoRemuneracion no tiene campo codigo, usar id o dejarlo None
                codigo_concepto = str(datos['concepto_obj'].id) if datos['concepto_obj'] else None
                
                ConceptoConsolidado.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    codigo_concepto=codigo_concepto,
                    nombre_concepto=concepto_nombre,
                    tipo_concepto=tipo_concepto,
                    monto_total=datos['monto_total'],
                    cantidad=datos['cantidad'],
                    es_numerico=True,
                    fuente_archivo='libro_remuneraciones'
                )
                conceptos_consolidados += 1
            
            # Actualizar totales en la nómina consolidada
            nomina_consolidada.total_haberes = total_haberes
            nomina_consolidada.total_descuentos = total_descuentos
            nomina_consolidada.liquido_pagar = total_haberes - total_descuentos
            nomina_consolidada.save(update_fields=['total_haberes', 'total_descuentos', 'liquido_pagar'])
        
        logger.info(f"💰 {conceptos_consolidados} conceptos consolidados creados")
        
        # 6. FINALIZAR CONSOLIDACIÓN
        cierre.estado = 'datos_consolidados'
        cierre.fecha_consolidacion = timezone.now()
        cierre.save(update_fields=['estado', 'fecha_consolidacion'])
        
        logger.info(f"✅ Consolidación completada:")
        logger.info(f"   📊 {empleados_consolidados} empleados consolidados")
        logger.info(f"   📋 {headers_consolidados} headers-valores creados")
        logger.info(f"   🔄 {movimientos_creados} movimientos de personal creados")
        logger.info(f"   💰 {conceptos_consolidados} conceptos consolidados creados")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'empleados_consolidados': empleados_consolidados,
            'headers_consolidados': headers_consolidados,
            'movimientos_creados': movimientos_creados,
            'conceptos_consolidados': conceptos_consolidados,
            'nuevo_estado': cierre.estado
        }
        
    except Exception as e:
        logger.error(f"❌ Error en consolidación para cierre {cierre_id}: {e}")
        
        # Revertir estado en caso de error
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.save(update_fields=['estado'])
        except:
            pass
            
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


# ===== 🚀 NUEVO SISTEMA PARALELO DE INCIDENCIAS =====

@shared_task
def generar_incidencias_cierre_paralelo(cierre_id, clasificaciones_seleccionadas):
    """
    🚀 TASK PRINCIPAL: Sistema dual de procesamiento paralelo
    
    Coordina dos procesamientos simultáneos:
    1. Filtrado: Solo clasificaciones seleccionadas
    2. Completo: Todas las clasificaciones
    3. Comparación: Validación cruzada de resultados
    """
    logger.info(f"🚀 Iniciando procesamiento paralelo dual para cierre {cierre_id}")
    logger.info(f"📋 Clasificaciones seleccionadas: {len(clasificaciones_seleccionadas)}")
    
    try:
        from .models import CierreNomina
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Obtener todas las clasificaciones disponibles para este cierre
        todas_clasificaciones = obtener_clasificaciones_cierre(cierre_id)
        logger.info(f"📊 Total clasificaciones disponibles: {len(todas_clasificaciones)}")
        
        # Crear chunks para procesamiento eficiente
        chunks_seleccionadas = crear_chunks(clasificaciones_seleccionadas, chunk_size=6)
        chunks_todas = crear_chunks(todas_clasificaciones, chunk_size=6)
        
        logger.info(f"🔀 Chunks filtrado: {len(chunks_seleccionadas)}, Chunks completo: {len(chunks_todas)}")
        
        # Ejecutar ambos procesamientos en paralelo usando chord
        # NO PODEMOS USAR .get() dentro de una tarea Celery
        # En su lugar, configuramos el chord para que se ejecute de forma asíncrona
        
        logger.info("🔄 Configurando ejecución asíncrona con callback...")
        
        # 1. Configurar procesamiento filtrado
        if chunks_seleccionadas:
            logger.info("🔍 Configurando procesamiento filtrado...")
            chord_filtrado = chord([
                procesar_chunk_clasificaciones.s(cierre_id, chunk, 'filtrado', idx)
                for idx, chunk in enumerate(chunks_seleccionadas)
            ])(consolidar_resultados_filtrados.s(cierre_id))
        else:
            # Si no hay clasificaciones seleccionadas, crear resultado vacío
            chord_filtrado = None
        
        # 2. Configurar procesamiento completo
        logger.info("📊 Configurando procesamiento completo...")
        chord_completo = chord([
            procesar_chunk_clasificaciones.s(cierre_id, chunk, 'completo', idx)
            for idx, chunk in enumerate(chunks_todas)
        ])(consolidar_resultados_completos.s(cierre_id))
        
        # 3. Retornar información de la configuración sin esperar resultados
        resultado_inmediato = {
            'success': True,
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat(),
            'configuracion_completada': True,
            'chunks_filtrado': len(chunks_seleccionadas) if chunks_seleccionadas else 0,
            'chunks_completo': len(chunks_todas),
            'clasificaciones_seleccionadas': len(clasificaciones_seleccionadas),
            'clasificaciones_totales': len(todas_clasificaciones),
            'chord_filtrado_id': chord_filtrado.id if chord_filtrado else None,
            'chord_completo_id': chord_completo.id,
            'mensaje': 'Procesamiento configurado y ejecutándose de forma asíncrona'
        }
        
        logger.info(f"✅ Configuración completada para cierre {cierre_id}")
        logger.info(f"📊 Chunks configurados: {len(chunks_seleccionadas) if chunks_seleccionadas else 0} filtrado, {len(chunks_todas)} completo")
        
        return resultado_inmediato
        
    except Exception as e:
        logger.error(f"❌ Error configurando procesamiento paralelo para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def obtener_resultado_procesamiento_dual(cierre_id, chord_filtrado_id=None, chord_completo_id=None):
    """
    🎯 TASK: Obtener resultado final del procesamiento dual
    
    Esta tarea se puede llamar para obtener el estado final del procesamiento
    después de que los chords hayan terminado.
    """
    from celery.result import AsyncResult
    
    logger.info(f"🔍 Obteniendo resultados finales para cierre {cierre_id}")
    
    try:
        resultados_finales = {}
        
        # Obtener resultado filtrado si existe
        if chord_filtrado_id:
            result_filtrado = AsyncResult(chord_filtrado_id)
            if result_filtrado.ready():
                resultados_finales['filtrado'] = result_filtrado.result
            else:
                resultados_finales['filtrado'] = {'pendiente': True}
        else:
            resultados_finales['filtrado'] = {
                'success': True,
                'total_incidencias': 0,
                'mensaje': 'No se procesaron clasificaciones filtradas'
            }
        
        # Obtener resultado completo
        if chord_completo_id:
            result_completo = AsyncResult(chord_completo_id)
            if result_completo.ready():
                resultados_finales['completo'] = result_completo.result
            else:
                resultados_finales['completo'] = {'pendiente': True}
        
        # Generar reporte final
        resultado_filtrado = resultados_finales.get('filtrado', {})
        resultado_completo = resultados_finales.get('completo', {})
        
        reporte_final = {
            'success': True,
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat(),
            'total_incidencias': (resultado_filtrado.get('total_incidencias', 0) + 
                                resultado_completo.get('total_incidencias', 0)),
            'total_incidencias_individuales': resultado_filtrado.get('total_incidencias', 0),
            'total_incidencias_suma': resultado_completo.get('total_incidencias', 0),
            'resultados_detallados': resultados_finales,
            'ambos_listos': (not resultado_filtrado.get('pendiente', False) and 
                           not resultado_completo.get('pendiente', False))
        }
        
        logger.info(f"📊 Reporte dual generado para cierre {cierre_id}")
        logger.info(f"✅ Total incidencias: {reporte_final['total_incidencias']}")
        
        return reporte_final
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resultados duales para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_chunk_clasificaciones(cierre_id, chunk_clasificaciones, tipo_procesamiento, chunk_idx):
    """
    🔧 TASK: Procesa un chunk de clasificaciones
    
    Args:
        cierre_id: ID del cierre
        chunk_clasificaciones: Lista de IDs de clasificaciones a procesar
        tipo_procesamiento: 'filtrado' o 'completo'
        chunk_idx: Índice del chunk para tracking
    """
    logger.info(f"🔧 Procesando chunk {chunk_idx} tipo '{tipo_procesamiento}' con {len(chunk_clasificaciones)} clasificaciones")
    
    try:
        resultados_chunk = []
        
        for clasificacion_id in chunk_clasificaciones:
            logger.debug(f"   📝 Procesando clasificación {clasificacion_id}")
            
            # Ejecutar la lógica de detección de incidencias para esta clasificación
            resultado_clasificacion = procesar_incidencias_clasificacion_individual(
                cierre_id, 
                clasificacion_id, 
                tipo_procesamiento
            )
            
            resultados_chunk.append({
                'clasificacion_id': clasificacion_id,
                'resultado': resultado_clasificacion,
                'timestamp': timezone.now().isoformat()
            })
        
        logger.info(f"✅ Chunk {chunk_idx} procesado: {len(resultados_chunk)} clasificaciones")
        
        return {
            'chunk_idx': chunk_idx,
            'tipo_procesamiento': tipo_procesamiento,
            'clasificaciones_procesadas': len(resultados_chunk),
            'resultados': resultados_chunk,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando chunk {chunk_idx}: {e}")
        return {
            'chunk_idx': chunk_idx,
            'tipo_procesamiento': tipo_procesamiento,
            'success': False,
            'error': str(e)
        }


@shared_task
def consolidar_resultados_filtrados(resultados_chunks, cierre_id):
    """
    📊 TASK: Consolida resultados del procesamiento filtrado
    """
    logger.info(f"📊 Consolidando resultados filtrados para cierre {cierre_id}")
    return consolidar_resultados_chunks(resultados_chunks, cierre_id, 'filtrado')


@shared_task
def consolidar_resultados_completos(resultados_chunks, cierre_id):
    """
    📊 TASK: Consolida resultados del procesamiento completo
    """
    logger.info(f"📊 Consolidando resultados completos para cierre {cierre_id}")
    return consolidar_resultados_chunks(resultados_chunks, cierre_id, 'completo')


@shared_task
def procesar_resultado_vacio(cierre_id, tipo_procesamiento):
    """
    📝 TASK: Genera resultado vacío cuando no hay clasificaciones seleccionadas
    """
    logger.info(f"📝 Generando resultado vacío para tipo '{tipo_procesamiento}'")
    return {
        'cierre_id': cierre_id,
        'tipo_procesamiento': tipo_procesamiento,
        'total_incidencias': 0,
        'incidencias_por_regla': {
            'variaciones_conceptos': 0,
            'ausentismos_continuos': 0,
            'ingresos_faltantes': 0,
            'finiquitos_presentes': 0
        },
        'clasificaciones_procesadas': 0,
        'success': True,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def comparar_y_generar_reporte_final(cierre_id, resultado_filtrado, resultado_completo, 
                                   total_seleccionadas, total_disponibles):
    """
    🎯 TASK FINAL: Compara ambos resultados y genera reporte unificado
    """
    logger.info(f"🎯 Generando reporte final para cierre {cierre_id}")
    logger.info(f"📊 Seleccionadas: {total_seleccionadas}, Disponibles: {total_disponibles}")
    
    try:
        # Calcular diferencias y métricas
        comparacion = {
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat(),
            'configuracion': {
                'clasificaciones_seleccionadas': total_seleccionadas,
                'clasificaciones_disponibles': total_disponibles,
                'modo_procesamiento': 'paralelo_dual'
            },
            'resultados': {
                'filtrado': resultado_filtrado,
                'completo': resultado_completo
            },
            'analisis_comparativo': calcular_diferencias_resultados(resultado_filtrado, resultado_completo),
            'metricas_rendimiento': {
                'cobertura_porcentaje': (total_seleccionadas / total_disponibles * 100) if total_disponibles > 0 else 0,
                'clasificaciones_no_procesadas': total_disponibles - total_seleccionadas
            }
        }
        
        # Guardar comparación en base de datos
        guardar_comparacion_incidencias(cierre_id, comparacion)
        
        # Actualizar estado del cierre
        actualizar_estado_cierre_post_procesamiento(cierre_id, comparacion)
        
        logger.info(f"✅ Reporte final generado exitosamente para cierre {cierre_id}")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'comparacion': comparacion,
            'resumen': {
                'incidencias_filtrado': resultado_filtrado.get('total_incidencias', 0),
                'incidencias_completo': resultado_completo.get('total_incidencias', 0),
                'cobertura_porcentaje': comparacion['metricas_rendimiento']['cobertura_porcentaje']
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando reporte final para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


# ===== 🛠️ FUNCIONES AUXILIARES =====

def obtener_clasificaciones_cierre(cierre_id):
    """Obtiene todas las clasificaciones disponibles para un cierre"""
    try:
        from .models import CierreNomina
        # Aquí implementarías la lógica específica para obtener clasificaciones
        # Por ahora devuelvo un ejemplo
        return list(range(1, 21))  # Ejemplo: 20 clasificaciones
    except Exception as e:
        logger.error(f"Error obteniendo clasificaciones: {e}")
        return []


def crear_chunks(lista, chunk_size=6):
    """Divide una lista en chunks del tamaño especificado"""
    if not lista:
        return []
    return [lista[i:i + chunk_size] for i in range(0, len(lista), chunk_size)]


def procesar_incidencias_clasificacion_individual(cierre_id, clasificacion_id, tipo_procesamiento):
    """Procesa incidencias para una clasificación individual"""
    try:
        # Aquí va la lógica específica de detección de incidencias
        # Por ahora simulo el procesamiento
        logger.debug(f"Procesando incidencias para clasificación {clasificacion_id} (tipo: {tipo_procesamiento})")
        
        return {
            'clasificacion_id': clasificacion_id,
            'incidencias_encontradas': 0,  # Simulado
            'reglas_aplicadas': ['variaciones_conceptos', 'ausentismos_continuos'],
            'success': True
        }
    except Exception as e:
        logger.error(f"Error procesando clasificación {clasificacion_id}: {e}")
        return {
            'clasificacion_id': clasificacion_id,
            'success': False,
            'error': str(e)
        }


def consolidar_resultados_chunks(resultados_chunks, cierre_id, tipo_procesamiento):
    """Consolida los resultados de múltiples chunks"""
    try:
        total_incidencias = 0
        clasificaciones_procesadas = 0
        incidencias_por_regla = {
            'variaciones_conceptos': 0,
            'ausentismos_continuos': 0,
            'ingresos_faltantes': 0,
            'finiquitos_presentes': 0
        }
        
        chunks_exitosos = 0
        
        for chunk_resultado in resultados_chunks:
            if chunk_resultado.get('success', False):
                chunks_exitosos += 1
                clasificaciones_procesadas += chunk_resultado.get('clasificaciones_procesadas', 0)
                # Aquí sumarías las incidencias específicas según tu lógica
        
        logger.info(f"📊 Consolidación {tipo_procesamiento}: {chunks_exitosos} chunks, {clasificaciones_procesadas} clasificaciones")
        
        return {
            'cierre_id': cierre_id,
            'tipo_procesamiento': tipo_procesamiento,
            'total_incidencias': total_incidencias,
            'incidencias_por_regla': incidencias_por_regla,
            'clasificaciones_procesadas': clasificaciones_procesadas,
            'chunks_exitosos': chunks_exitosos,
            'success': True,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error consolidando resultados {tipo_procesamiento}: {e}")
        return {
            'success': False,
            'error': str(e),
            'tipo_procesamiento': tipo_procesamiento
        }


def calcular_diferencias_resultados(resultado_filtrado, resultado_completo):
    """Calcula las diferencias entre el procesamiento filtrado y completo"""
    try:
        return {
            'diferencia_incidencias': (
                resultado_completo.get('total_incidencias', 0) - 
                resultado_filtrado.get('total_incidencias', 0)
            ),
            'diferencia_clasificaciones': (
                resultado_completo.get('clasificaciones_procesadas', 0) - 
                resultado_filtrado.get('clasificaciones_procesadas', 0)
            ),
            'coherencia_resultados': (
                resultado_filtrado.get('success', False) and 
                resultado_completo.get('success', False)
            )
        }
    except Exception as e:
        logger.error(f"Error calculando diferencias: {e}")
        return {'error': str(e)}


def guardar_comparacion_incidencias(cierre_id, comparacion):
    """Guarda la comparación en la base de datos"""
    try:
        # Aquí implementarías el guardado en tu modelo de base de datos
        logger.info(f"💾 Guardando comparación para cierre {cierre_id}")
        pass
    except Exception as e:
        logger.error(f"Error guardando comparación: {e}")


def actualizar_estado_cierre_post_procesamiento(cierre_id, comparacion):
    """Actualiza el estado del cierre después del procesamiento"""
    try:
        from .models import CierreNomina
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        if comparacion['resultados']['completo'].get('success') and comparacion['resultados']['filtrado'].get('success'):
            cierre.estado = 'con_incidencias'
            cierre.save(update_fields=['estado'])
            logger.info(f"✅ Estado del cierre {cierre_id} actualizado a 'con_incidencias'")
        
    except Exception as e:
        logger.error(f"Error actualizando estado del cierre: {e}")


# ===== 🚀 NUEVO SISTEMA PARALELO DE DISCREPANCIAS =====

@shared_task
def generar_discrepancias_cierre_paralelo(cierre_id):
    """
    🚀 TASK PRINCIPAL: Sistema paralelo de generación de discrepancias
    
    Coordina dos procesamientos simultáneos usando Celery Chord:
    1. Chunk 1: Discrepancias Libro vs Novedades
    2. Chunk 2: Discrepancias Movimientos vs Analista
    3. Consolidación: Unificación y actualización del estado
    """
    logger.info(f"🚀 Iniciando generación paralela de discrepancias para cierre {cierre_id}")
    
    try:
        from .models import CierreNomina
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Cambiar estado a verificacion_datos al iniciar
        cierre.estado = 'verificacion_datos'
        cierre.save(update_fields=['estado'])
        
        # Eliminar discrepancias anteriores si existen
        cierre.discrepancias.all().delete()
        logger.info(f"🧹 Discrepancias anteriores limpiadas para cierre {cierre_id}")
        
        # Ejecutar procesamientos en paralelo usando chord
        chord_paralelo = chord([
            procesar_discrepancias_chunk.s(cierre_id, 'libro_vs_novedades'),
            procesar_discrepancias_chunk.s(cierre_id, 'movimientos_vs_analista')
        ])(consolidar_discrepancias_finales.s(cierre_id))
        
        logger.info(f"📊 Chord de discrepancias iniciado para cierre {cierre_id}")
        return {
            'success': True,
            'cierre_id': cierre_id,
            'chord_id': str(chord_paralelo),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en generación paralela de discrepancias para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def procesar_discrepancias_chunk(cierre_id, tipo_chunk):
    """
    🔧 TASK: Procesa un chunk específico de discrepancias
    
    Args:
        cierre_id: ID del cierre
        tipo_chunk: 'libro_vs_novedades' o 'movimientos_vs_analista'
    """
    logger.info(f"🔧 Procesando chunk '{tipo_chunk}' para cierre {cierre_id}")
    
    try:
        from .models import CierreNomina
        from .utils.GenerarDiscrepancias import (
            generar_discrepancias_libro_vs_novedades,
            generar_discrepancias_movimientos_vs_analista
        )
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        if tipo_chunk == 'libro_vs_novedades':
            resultado = generar_discrepancias_libro_vs_novedades(cierre)
            logger.info(f"📚 Libro vs Novedades: {resultado['total_discrepancias']} discrepancias")
            
        elif tipo_chunk == 'movimientos_vs_analista':
            resultado = generar_discrepancias_movimientos_vs_analista(cierre)
            logger.info(f"📋 Movimientos vs Analista: {resultado['total_discrepancias']} discrepancias")
            
        else:
            raise ValueError(f"Tipo de chunk desconocido: {tipo_chunk}")
        
        return {
            'chunk_tipo': tipo_chunk,
            'cierre_id': cierre_id,
            'total_discrepancias': resultado['total_discrepancias'],
            'detalle': resultado,
            'success': True,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando chunk '{tipo_chunk}' para cierre {cierre_id}: {e}")
        return {
            'chunk_tipo': tipo_chunk,
            'cierre_id': cierre_id,
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def consolidar_discrepancias_finales(resultados_chunks, cierre_id):
    """
    🎯 TASK FINAL: Consolida los resultados de ambos chunks y actualiza el estado
    """
    logger.info(f"🎯 Consolidando discrepancias finales para cierre {cierre_id}")
    
    try:
        from .models import CierreNomina
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Procesar resultados de ambos chunks
        total_discrepancias = 0
        resultados_detallados = {}
        chunks_exitosos = 0
        
        for resultado in resultados_chunks:
            if resultado.get('success', False):
                chunks_exitosos += 1
                chunk_tipo = resultado['chunk_tipo']
                chunk_total = resultado['total_discrepancias']
                
                total_discrepancias += chunk_total
                resultados_detallados[chunk_tipo] = resultado['detalle']
                
                logger.info(f"✅ Chunk '{chunk_tipo}': {chunk_total} discrepancias")
            else:
                logger.error(f"❌ Chunk fallido: {resultado}")
        
        # Actualizar estado del cierre según los resultados
        if chunks_exitosos == 2:  # Ambos chunks exitosos
            if total_discrepancias == 0:
                cierre.estado = 'verificado_sin_discrepancias'
                mensaje = "Sin discrepancias - Datos verificados exitosamente"
            else:
                cierre.estado = 'con_discrepancias'
                mensaje = f"Con discrepancias - {total_discrepancias} diferencias detectadas"
        else:
            cierre.estado = 'con_discrepancias'  # Por seguridad
            mensaje = "Error en verificación - Estado de seguridad activado"
        
        cierre.save(update_fields=['estado'])
        
        consolidacion_final = {
            'cierre_id': cierre_id,
            'total_discrepancias': total_discrepancias,
            'chunks_exitosos': chunks_exitosos,
            'chunks_procesados': len(resultados_chunks),
            'estado_final': cierre.estado,
            'mensaje': mensaje,
            'resultados_detallados': resultados_detallados,
            'timestamp': timezone.now().isoformat(),
            'success': True
        }
        
        logger.info(f"✅ Consolidación completada para cierre {cierre_id}: {mensaje}")
        
        return consolidacion_final
        
    except Exception as e:
        logger.error(f"❌ Error consolidando discrepancias para cierre {cierre_id}: {e}")
        
        # En caso de error, establecer estado de seguridad
        try:
            from .models import CierreNomina
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'con_discrepancias'  # Estado de seguridad
            cierre.save(update_fields=['estado'])
        except:
            pass


# ========================================
# 🚀 TASKS OPTIMIZADAS CON CELERY CHORD
# ========================================

@shared_task
def procesar_chunk_empleados_task(libro_id, chunk_data):
    """
    👥 Task para procesar un chunk específico de empleados en paralelo.
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento del chunk
    """
    from .utils.LibroRemuneracionesOptimizado import procesar_chunk_empleados_util
    
    logger.info(f"🔄 Iniciando procesamiento de chunk empleados {chunk_data.get('chunk_id')}")
    
    try:
        resultado = procesar_chunk_empleados_util(libro_id, chunk_data)
        logger.info(f"✅ Chunk empleados {chunk_data.get('chunk_id')} completado exitosamente")
        return resultado
    except Exception as e:
        error_msg = f"Error en chunk empleados {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'empleados_procesados': 0,
            'errores': [error_msg],
            'libro_id': libro_id
        }


@shared_task
def procesar_chunk_registros_task(libro_id, chunk_data):
    """
    📝 Task para procesar registros de nómina de un chunk específico en paralelo.
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento del chunk
    """
    from .utils.LibroRemuneracionesOptimizado import procesar_chunk_registros_util
    
    logger.info(f"🔄 Iniciando procesamiento de chunk registros {chunk_data.get('chunk_id')}")
    
    try:
        resultado = procesar_chunk_registros_util(libro_id, chunk_data)
        logger.info(f"✅ Chunk registros {chunk_data.get('chunk_id')} completado exitosamente")
        return resultado
    except Exception as e:
        error_msg = f"Error en chunk registros {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'registros_procesados': 0,
            'errores': [error_msg],
            'libro_id': libro_id
        }


@shared_task
def consolidar_empleados_task(resultados_chunks):
    """
    📊 Task callback para consolidar resultados de procesamiento de empleados.
    
    Args:
        resultados_chunks: Lista de resultados de todos los chunks
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    from .utils.LibroRemuneracionesOptimizado import consolidar_stats_empleados
    
    logger.info(f"📊 Consolidando resultados de {len(resultados_chunks)} chunks de empleados")
    
    try:
        consolidado = consolidar_stats_empleados(resultados_chunks)
        
        # Log resultado final
        logger.info(
            f"✅ Consolidación empleados: {consolidado['total_empleados_procesados']} empleados, "
            f"{consolidado['chunks_exitosos']}/{consolidado['total_chunks']} chunks exitosos"
        )
        
        return consolidado
        
    except Exception as e:
        error_msg = f"Error consolidando empleados: {str(e)}"
        logger.error(error_msg)
        return {
            'total_empleados_procesados': 0,
            'chunks_exitosos': 0,
            'total_chunks': len(resultados_chunks),
            'errores': [error_msg],
            'procesamiento_exitoso': False
        }


@shared_task
def consolidar_registros_task(resultados_chunks):
    """
    📊 Task callback para consolidar resultados de procesamiento de registros.
    
    Args:
        resultados_chunks: Lista de resultados de todos los chunks
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    from .utils.LibroRemuneracionesOptimizado import consolidar_stats_registros
    
    logger.info(f"📊 Consolidando resultados de {len(resultados_chunks)} chunks de registros")
    
    try:
        consolidado = consolidar_stats_registros(resultados_chunks)
        
        # Actualizar estado del libro a "procesado" si todo salió bien
        if consolidado.get('procesamiento_exitoso') and consolidado.get('libro_id'):
            try:
                libro = LibroRemuneracionesUpload.objects.get(id=consolidado['libro_id'])
                libro.estado = "procesado"
                libro.save(update_fields=['estado'])
                logger.info(f"✅ Estado del libro {consolidado['libro_id']} actualizado a 'procesado'")
            except Exception as e:
                logger.error(f"Error actualizando estado del libro: {e}")
        
        # Log resultado final
        logger.info(
            f"✅ Consolidación registros: {consolidado['total_registros_procesados']} registros, "
            f"{consolidado['chunks_exitosos']}/{consolidado['total_chunks']} chunks exitosos"
        )
        
        return consolidado
        
    except Exception as e:
        error_msg = f"Error consolidando registros: {str(e)}"
        logger.error(error_msg)
        return {
            'total_registros_procesados': 0,
            'chunks_exitosos': 0,
            'total_chunks': len(resultados_chunks),
            'errores': [error_msg],
            'procesamiento_exitoso': False
        }


@shared_task
def actualizar_empleados_desde_libro_optimizado(result, usar_chord=True):
    """
    🚀 Versión optimizada que usa Celery Chord para procesar empleados en paralelo.
    
    Args:
        result: Resultado de la task anterior (contiene libro_id)
        usar_chord: Si usar chord (True) o procesamiento secuencial (False)
        
    Returns:
        Dict: Estadísticas del procesamiento o resultado del chord
    """
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        if not usar_chord:
            # Fallback al método original
            logger.info(f"📝 Usando método secuencial para empleados del libro {libro_id}")
            count = actualizar_empleados_desde_libro_util(libro)
            return {"libro_id": libro_id, "empleados_actualizados": count}
        
        # 🚀 USAR CHORD PARA PARALELIZACIÓN
        from .utils.LibroRemuneracionesOptimizado import dividir_dataframe_empleados
        
        logger.info(f"🚀 Iniciando procesamiento optimizado con Chord para libro {libro_id}")
        
        # Calcular chunk size dinámico
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"📊 Total filas: {total_filas}, Chunk size: {chunk_size}")
        
        # Dividir en chunks
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se encontraron chunks válidos para libro {libro_id}")
            return {"libro_id": libro_id, "empleados_actualizados": 0}
        
        # Crear tasks paralelas usando chord
        tasks_paralelas = [
            procesar_chunk_empleados_task.s(libro_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback
        callback = consolidar_empleados_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(
            f"🚀 Chord iniciado para libro {libro_id}: {len(chunks)} chunks en paralelo"
        )
        
        # Retornar referencia al chord para monitoreo
        return {
            "libro_id": libro_id,
            "chord_id": resultado_chord.id if hasattr(resultado_chord, 'id') else None,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord"
        }
        
    except Exception as e:
        error_msg = f"Error en procesamiento optimizado de empleados para libro {libro_id}: {e}"
        logger.error(error_msg)
        
        # Fallback al método original en caso de error
        try:
            logger.info(f"🔄 Fallback a método secuencial para libro {libro_id}")
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            count = actualizar_empleados_desde_libro_util(libro)
            return {"libro_id": libro_id, "empleados_actualizados": count, "fallback": True}
        except Exception as fallback_error:
            logger.error(f"Error en fallback: {fallback_error}")
            raise


@shared_task
def guardar_registros_nomina_optimizado(result, usar_chord=True):
    """
    🚀 Versión optimizada que usa Celery Chord para procesar registros en paralelo.
    
    Args:
        result: Resultado de la task anterior (contiene libro_id)
        usar_chord: Si usar chord (True) o procesamiento secuencial (False)
        
    Returns:
        Dict: Estadísticas del procesamiento o resultado del chord
    """
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        if not usar_chord:
            # Fallback al método original
            logger.info(f"📝 Usando método secuencial para registros del libro {libro_id}")
            count = guardar_registros_nomina_util(libro)
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id, 
                "registros_actualizados": count,
                "estado": "procesado"
            }
        
        # 🚀 USAR CHORD PARA PARALELIZACIÓN
        from .utils.LibroRemuneracionesOptimizado import dividir_dataframe_empleados
        
        logger.info(f"🚀 Iniciando procesamiento optimizado de registros con Chord para libro {libro_id}")
        
        # Calcular chunk size dinámico
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"📊 Total filas: {total_filas}, Chunk size: {chunk_size}")
        
        # Dividir en chunks
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se encontraron chunks válidos para libro {libro_id}")
            # Actualizar estado y retornar
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id, 
                "registros_actualizados": 0,
                "estado": "procesado"
            }
        
        # Crear tasks paralelas usando chord
        tasks_paralelas = [
            procesar_chunk_registros_task.s(libro_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback
        callback = consolidar_registros_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(
            f"🚀 Chord de registros iniciado para libro {libro_id}: {len(chunks)} chunks en paralelo"
        )
        
        # Retornar referencia al chord para monitoreo
        return {
            "libro_id": libro_id,
            "chord_id": resultado_chord.id if hasattr(resultado_chord, 'id') else None,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord",
            "estado": "procesando"  # El estado se actualizará en el callback
        }
        
    except Exception as e:
        error_msg = f"Error en procesamiento optimizado de registros para libro {libro_id}: {e}"
        logger.error(error_msg)
        
        # Fallback al método original en caso de error
        try:
            logger.info(f"🔄 Fallback a método secuencial para registros del libro {libro_id}")
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            count = guardar_registros_nomina_util(libro)
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id, 
                "registros_actualizados": count,
                "estado": "procesado",
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"Error en fallback: {fallback_error}")
            # Marcar como error
            try:
                libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
                libro.estado = "con_error"
                libro.save(update_fields=['estado'])
            except:
                pass
            raise
        
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'timestamp': timezone.now().isoformat()
        }
