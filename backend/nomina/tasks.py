# nomina/tasks.py
from .utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
    actualizar_empleados_desde_libro_util,
    guardar_registros_nomina_util,
)
from .utils.MovimientoMes import procesar_archivo_movimientos_mes_util
from celery import shared_task, chain
from .models import (
    LibroRemuneracionesUpload,
    MovimientosMesUpload,
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
    """Task para procesar archivo de movimientos del mes"""
    logger.info(f"Procesando movimientos del mes id={movimiento_id}")
    
    try:
        movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
        movimiento.estado = 'en_proceso'
        movimiento.save()
        
        # Procesar el archivo usando la utilidad
        resultados = procesar_archivo_movimientos_mes_util(movimiento)
        
        # Verificar si hubo errores
        if resultados.get('errores'):
            # Si hay errores, marcar como error parcial pero guardar los resultados
            movimiento.estado = 'con_errores_parciales'
            logger.warning(f"Movimientos procesados con errores parciales id={movimiento_id}: {resultados['errores']}")
        else:
            movimiento.estado = 'procesado'
            logger.info(f"Movimientos del mes procesados exitosamente id={movimiento_id}")
        
        # Guardar información del procesamiento
        movimiento.resultados_procesamiento = resultados
        movimiento.save()
        
        # Preparar respuesta con resumen
        total_procesados = sum([v for k, v in resultados.items() if k != 'errores' and isinstance(v, int)])
        
        return {
            "movimiento_id": movimiento_id, 
            "estado": movimiento.estado,
            "total_procesados": total_procesados,
            "detalle": {
                "altas_bajas": resultados.get('altas_bajas', 0),
                "ausentismos": resultados.get('ausentismos', 0),
                "vacaciones": resultados.get('vacaciones', 0),
                "variaciones_sueldo": resultados.get('variaciones_sueldo', 0),
                "variaciones_contrato": resultados.get('variaciones_contrato', 0),
            },
            "errores": resultados.get('errores', [])
        }
        
    except MovimientosMesUpload.DoesNotExist:
        logger.error(f"MovimientosMesUpload con id={movimiento_id} no encontrado")
        raise
    except Exception as e:
        # En caso de error, marcar como error
        try:
            movimiento = MovimientosMesUpload.objects.get(id=movimiento_id)
            movimiento.estado = 'con_error'
            movimiento.save()
        except:
            pass
        logger.error(f"Error procesando movimientos del mes id={movimiento_id}: {e}")
        raise
