# nomina/tasks.py
from .utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
    actualizar_empleados_desde_libro_util,
    guardar_registros_nomina_util,
)
from .utils.NovedadesRemuneraciones import (
    obtener_headers_archivo_novedades,
    clasificar_headers_archivo_novedades,
    actualizar_empleados_desde_novedades,
    guardar_registros_novedades,
)
from .utils.MovimientoMes import procesar_archivo_movimientos_mes_util
from .utils.ArchivosAnalista import procesar_archivo_analista_util
from celery import shared_task, chain
from .models import (
    LibroRemuneracionesUpload,
    MovimientosMesUpload,
    ArchivoAnalistaUpload,
    ArchivoNovedadesUpload,
)
import logging
import pandas as pd

logger = logging.getLogger(__name__)


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
    libro_id = result["libro_id"]
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        cierre = libro.cierre
        cliente = cierre.cliente

        # Marcamos estado "en proceso de clasificación"
        libro.estado = "clasif_en_proceso"
        libro.save()

        headers = (
            libro.header_json
            if isinstance(libro.header_json, list)
            else result["headers"]
        )

        headers_clasificados, headers_sin_clasificar = (
            clasificar_headers_libro_remuneraciones(headers, cliente)
        )

        # Escribe el resultado final en el campo JSON
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }

        # Cambia el estado según si quedan pendientes o no
        if headers_sin_clasificar:
            libro.estado = "clasif_pendiente"
        else:
            libro.estado = "clasificado"

        libro.save()
        logger.info(
            f"Libro {libro_id}: {len(headers_clasificados)} headers clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        return {
            "libro_id": libro_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
        }
    except Exception as e:
        logger.error(f"Error clasificando headers para libro id={libro_id}: {e}")
        # Intenta dejar el libro en estado error, pero no interrumpe la excepción.
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save()
        except Exception as ex:
            logger.error(
                f"Error guardando estado 'con_error' para libro id={libro_id}: {ex}"
            )
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
def procesar_movimientos_mes(movimiento_id):
    """Procesa un archivo de movimientos del mes"""
    logger.info(f"Procesando archivo movimientos mes id={movimiento_id}")
    
    try:
        movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
        movimiento.estado = 'en_proceso'
        movimiento.save()
        
        resultados = procesar_archivo_movimientos_mes_util(movimiento)
        
        # Guardar resultados
        movimiento.resultados_procesamiento = resultados
        
        # Determinar estado final
        if resultados.get('errores'):
            if any(v > 0 for k, v in resultados.items() if k != 'errores' and isinstance(v, int)):
                movimiento.estado = 'con_errores_parciales'
            else:
                movimiento.estado = 'con_error'
        else:
            movimiento.estado = 'procesado'
        
        movimiento.save()
        logger.info(f"Procesamiento exitoso movimientos mes id={movimiento_id}")
        return resultados
        
    except Exception as e:
        movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
        movimiento.estado = 'con_error'
        movimiento.resultados_procesamiento = {'errores': [str(e)]}
        movimiento.save()
        logger.error(f"Error procesando movimientos mes id={movimiento_id}: {e}")
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
            
            # ✅ Si todos los headers se clasificaron automáticamente, continuar con las tareas finales
            from celery import chain
            workflow_final = chain(
                actualizar_empleados_desde_novedades_task.s({"archivo_id": archivo_id}),
                guardar_registros_novedades_task.s()
            )
            workflow_final.apply_async()
            logger.info(f"Todos los headers se clasificaron automáticamente. Iniciando procesamiento final para archivo {archivo_id}")

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


# ===== TAREAS PARA SISTEMA DE INCIDENCIAS =====

@shared_task
def generar_incidencias_cierre_task(cierre_id):
    """Task para generar incidencias de un cierre"""
    from .utils.GenerarIncidencias import generar_todas_incidencias
    from .models import CierreNomina
    
    logger.info(f"Iniciando generación de incidencias para cierre {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar que el cierre tenga los archivos necesarios procesados
        if not _verificar_archivos_listos_para_incidencias(cierre):
            raise ValueError("No todos los archivos están procesados para generar incidencias")
        
        resultado = generar_todas_incidencias(cierre)
        
        logger.info(f"Incidencias generadas exitosamente para cierre {cierre_id}: {resultado['total_incidencias']} incidencias")
        return resultado
        
    except Exception as e:
        logger.error(f"Error generando incidencias para cierre {cierre_id}: {e}")
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado_incidencias = 'analisis_pendiente'
            cierre.save(update_fields=['estado_incidencias'])
        except:
            pass
        raise

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
