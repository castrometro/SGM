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
def consolidar_datos_nomina_task(cierre_id):
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
