#nomina/tasks.py
from .utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones, clasificar_headers_libro_remuneraciones
from celery import shared_task
from .models import LibroRemuneracionesUpload
import logging
import pandas as pd

logger = logging.getLogger(__name__)

@shared_task
def analizar_headers_libro_remuneraciones(libro_id):
    logger.info(f"Procesando libro de remuneraciones id={libro_id}")
    libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
    libro.estado = 'analizando_hdrs'
    libro.save()

    try:
        headers = obtener_headers_libro_remuneraciones(libro.archivo.path)
        libro.header_json = headers
        libro.estado = 'hdrs_analizados'
        libro.save()
        logger.info(f"Procesamiento exitoso libro id={libro_id}")
        # ¡Retornamos libro_id y headers!
        return {'libro_id': libro_id, 'headers': headers}
    except Exception as e:
        libro.estado = 'con_error'
        libro.save()
        logger.error(f"Error procesando libro id={libro_id}: {e}")
        raise

@shared_task
def clasificar_headers_libro_remuneraciones_task(result):
    libro_id = result['libro_id']
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        cierre = libro.cierre
        cliente = cierre.cliente

        # Marcamos estado "en proceso de clasificación"
        libro.estado = 'clasif_en_proceso'
        libro.save()

        headers = libro.header_json if isinstance(libro.header_json, list) else result['headers']

        headers_clasificados, headers_sin_clasificar = clasificar_headers_libro_remuneraciones(headers, cliente)

        # Escribe el resultado final en el campo JSON
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar
        }

        # Cambia el estado según si quedan pendientes o no
        if headers_sin_clasificar:
            libro.estado = 'clasif_pendiente'
        else:
            libro.estado = 'clasificado'

        libro.save()
        logger.info(
            f"Libro {libro_id}: {len(headers_clasificados)} headers clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        return {
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar)
        }
    except Exception as e:
        logger.error(f"Error clasificando headers para libro id={libro_id}: {e}")
        # Intenta dejar el libro en estado error, pero no interrumpe la excepción.
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = 'con_error'
            libro.save()
        except Exception as ex:
            logger.error(f"Error guardando estado 'con_error' para libro id={libro_id}: {ex}")
        raise
