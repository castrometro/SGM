#nomina/tasks.py
from .utils.LibroRemuneraciones import obtener_headers_libro_remuneraciones, clasificar_headers_libro_remuneraciones
from celery import shared_task
from .models import LibroRemuneracionesUpload, EmpleadosMes, RegistroNomina
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
            "libro_id": libro_id,
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


@shared_task
def actualizar_empleados_desde_libro(result):
    libro_id = result.get('libro_id') if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")

        rut_col = next((c for c in df.columns if 'rut' in c.lower() and 'trab' in c.lower()), None)
        dv_col = next((c for c in df.columns if 'dv' in c.lower() and 'trab' in c.lower()), None)
        ape_pat_col = next((c for c in df.columns if 'apellido' in c.lower() and 'pater' in c.lower()), None)
        ape_mat_col = next((c for c in df.columns if 'apellido' in c.lower() and 'mater' in c.lower()), None)
        nombres_col = next((c for c in df.columns if 'nombre' in c.lower()), None)
        ingreso_col = next((c for c in df.columns if 'ingreso' in c.lower()), None)

        cierre = libro.cierre
        periodo = cierre.periodo.split('-')
        ano = int(periodo[0])
        mes = int(periodo[1])
        count = 0
        for _, row in df.iterrows():
            rut_num = str(row.get(rut_col, '')).strip()
            dv = str(row.get(dv_col, '')).strip()
            rut = f"{rut_num}-{dv}" if dv else rut_num
            defaults = {
                'cliente': cierre.cliente,
                'ano': ano,
                'mes': mes,
                'rut_empresa': str(cierre.cliente.rut),
                'nombre': str(row.get(nombres_col, '')).strip(),
                'apellido_paterno': str(row.get(ape_pat_col, '')).strip(),
                'apellido_materno': str(row.get(ape_mat_col, '')).strip(),
            }
            EmpleadosMes.objects.update_or_create(
                cierre=cierre,
                rut_trabajador=rut,
                defaults=defaults,
            )
            count += 1
        logger.info(f"Actualizados {count} empleados desde libro {libro_id}")
        return {'libro_id': libro_id, 'empleados_actualizados': count}
    except Exception as e:
        logger.error(f"Error actualizando empleados para libro id={libro_id}: {e}")
        raise


@shared_task
def guardar_registros_nomina(result):
    libro_id = result.get('libro_id') if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")

        rut_col = next((c for c in df.columns if 'rut' in c.lower() and 'trab' in c.lower()), None)
        dv_col = next((c for c in df.columns if 'dv' in c.lower() and 'trab' in c.lower()), None)
        ape_pat_col = next((c for c in df.columns if 'apellido' in c.lower() and 'pater' in c.lower()), None)
        ape_mat_col = next((c for c in df.columns if 'apellido' in c.lower() and 'mater' in c.lower()), None)
        nombres_col = next((c for c in df.columns if 'nombre' in c.lower()), None)
        ingreso_col = next((c for c in df.columns if 'ingreso' in c.lower()), None)

        empleado_cols = {c for c in [rut_col, dv_col, ape_pat_col, ape_mat_col, nombres_col, ingreso_col] if c}

        headers = libro.header_json
        if isinstance(headers, dict):
            headers = headers.get("headers_clasificados", []) + headers.get("headers_sin_clasificar", [])
        if not headers:
            headers = [h for h in df.columns if h not in empleado_cols]

        count = 0
        for _, row in df.iterrows():
            rut_num = str(row.get(rut_col, "")).strip()
            dv = str(row.get(dv_col, "")).strip()
            rut = f"{rut_num}-{dv}" if dv else rut_num
            empleado = EmpleadosMes.objects.filter(cierre=libro.cierre, rut_trabajador=rut).first()
            if not empleado:
                continue

            data = {h: row.get(h) for h in headers}
            RegistroNomina.objects.update_or_create(
                cierre=libro.cierre,
                empleado=empleado,
                defaults={"data": data},
            )
            count += 1

        logger.info(f"Registros nómina guardados desde libro {libro_id}: {count}")
        return {"libro_id": libro_id, "registros_actualizados": count}
    except Exception as e:
        logger.error(f"Error guardando registros de nómina para libro id={libro_id}: {e}")
        raise
