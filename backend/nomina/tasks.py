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
            cierre.estado = 'incidencias_abiertas'
            cierre.estado_incidencias = 'incidencias_abiertas'
        else:
            # No hay incidencias de variación salarial
            cierre.estado = 'sin_incidencias'
            cierre.estado_incidencias = 'sin_incidencias'
        
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
            cierre.estado = 'datos_verificados'
        else:
            # Con discrepancias - requiere corrección
            cierre.estado = 'discrepancias_detectadas'
        
        cierre.save(update_fields=['estado'])
        
        logger.info(f"Discrepancias generadas exitosamente para cierre {cierre_id}: {resultado['total_discrepancias']} discrepancias")
        return resultado
        
    except Exception as e:
        logger.error(f"Error generando discrepancias para cierre {cierre_id}: {e}")
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'datos_consolidados'  # Volver al estado anterior
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
