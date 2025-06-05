#nomina/tasks.py
from .utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
)
from celery import shared_task
from .models import (
    LibroRemuneracionesUpload,
    MovimientosMesUpload,
    MovimientoAltaBaja,
    MovimientoAusentismo,
    MovimientoVacaciones,
    VariacionSueldoBase,
    VariacionTipoContrato,
    Empleado,
    IncidenciaComparacion,
)
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

        count = 0
        for _, row in df.iterrows():
            rut_num = str(row.get(rut_col, '')).strip()
            dv = str(row.get(dv_col, '')).strip()
            rut = f"{rut_num}-{dv}" if dv else rut_num
            defaults = {
                'nombres': str(row.get(nombres_col, '')).strip(),
                'apellido_paterno': str(row.get(ape_pat_col, '')).strip(),
                'apellido_materno': str(row.get(ape_mat_col, '')).strip(),
            }
            if ingreso_col:
                try:
                    defaults['fecha_ingreso'] = pd.to_datetime(row[ingreso_col]).date()
                except Exception:
                    pass
            Empleado.objects.update_or_create(rut=rut, defaults=defaults)
            count += 1
        logger.info(f"Actualizados {count} empleados desde libro {libro_id}")
        return {'libro_id': libro_id, 'empleados_actualizados': count}
    except Exception as e:
        logger.error(f"Error actualizando empleados para libro id={libro_id}: {e}")
        raise


def _find_column(df, *keywords):
    """Utility to find the first column containing all keywords."""
    for col in df.columns:
        col_l = str(col).lower()
        if all(k.lower() in col_l for k in keywords):
            return col
    return None


def _empleado_por_rut(rut):
    return Empleado.objects.filter(rut=rut).first()


def _parse_fecha(value):
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _procesar_alta_baja(df, upload):
    rut_col = _find_column(df, "rut")
    nombre_col = _find_column(df, "nombre")
    tipo_col = _find_column(df, "tipo")
    fecha_col = _find_column(df, "fecha")
    motivo_col = _find_column(df, "motivo")

    if not all([rut_col, nombre_col, tipo_col, fecha_col]):
        raise ValueError("Formato inválido hoja Altas y Bajas")

    count = 0
    for _, row in df.iterrows():
        rut = str(row.get(rut_col, "")).strip()
        if not rut:
            continue
        MovimientoAltaBaja.objects.create(
            movimientos_mes=upload,
            empleado=_empleado_por_rut(rut),
            rut=rut,
            nombre=str(row.get(nombre_col, "")).strip(),
            tipo_movimiento=str(row.get(tipo_col, "")).strip().lower(),
            fecha=_parse_fecha(row.get(fecha_col)),
            motivo=str(row.get(motivo_col, "")).strip() if motivo_col else None,
        )
        count += 1
    return count


def _procesar_ausentismo(df, upload):
    rut_col = _find_column(df, "rut")
    nombre_col = _find_column(df, "nombre")
    tipo_col = _find_column(df, "tipo")
    ini_col = _find_column(df, "inicio")
    fin_col = _find_column(df, "fin")
    dias_col = _find_column(df, "dias")

    if not all([rut_col, nombre_col, tipo_col, ini_col, fin_col]):
        raise ValueError("Formato inválido hoja Ausentismos")

    count = 0
    for _, row in df.iterrows():
        rut = str(row.get(rut_col, "")).strip()
        if not rut:
            continue
        MovimientoAusentismo.objects.create(
            movimientos_mes=upload,
            empleado=_empleado_por_rut(rut),
            rut=rut,
            nombre=str(row.get(nombre_col, "")).strip(),
            tipo_ausentismo=str(row.get(tipo_col, "")).strip(),
            fecha_inicio=_parse_fecha(row.get(ini_col)),
            fecha_fin=_parse_fecha(row.get(fin_col)),
            dias=int(row.get(dias_col)) if dias_col else 0,
        )
        count += 1
    return count


def _procesar_vacaciones(df, upload):
    rut_col = _find_column(df, "rut")
    nombre_col = _find_column(df, "nombre")
    ini_col = _find_column(df, "inicio")
    fin_col = _find_column(df, "fin")
    dias_col = _find_column(df, "dias")

    if not all([rut_col, nombre_col, ini_col, fin_col]):
        raise ValueError("Formato inválido hoja Vacaciones")

    count = 0
    for _, row in df.iterrows():
        rut = str(row.get(rut_col, "")).strip()
        if not rut:
            continue
        MovimientoVacaciones.objects.create(
            movimientos_mes=upload,
            empleado=_empleado_por_rut(rut),
            rut=rut,
            nombre=str(row.get(nombre_col, "")).strip(),
            fecha_inicio=_parse_fecha(row.get(ini_col)),
            fecha_fin=_parse_fecha(row.get(fin_col)),
            dias=int(row.get(dias_col)) if dias_col else 0,
        )
        count += 1
    return count


def _procesar_variacion_sueldo(df, upload):
    rut_col = _find_column(df, "rut")
    nombre_col = _find_column(df, "nombre")
    ant_col = _find_column(df, "anterior")
    nuevo_col = _find_column(df, "nuevo")
    fecha_col = _find_column(df, "fecha")

    if not all([rut_col, nombre_col, ant_col, nuevo_col, fecha_col]):
        raise ValueError("Formato inválido hoja Sueldo Base")

    count = 0
    for _, row in df.iterrows():
        rut = str(row.get(rut_col, "")).strip()
        if not rut:
            continue
        VariacionSueldoBase.objects.create(
            movimientos_mes=upload,
            empleado=_empleado_por_rut(rut),
            rut=rut,
            nombre=str(row.get(nombre_col, "")).strip(),
            sueldo_anterior=row.get(ant_col) or 0,
            sueldo_nuevo=row.get(nuevo_col) or 0,
            fecha=_parse_fecha(row.get(fecha_col)),
        )
        count += 1
    return count


def _procesar_variacion_contrato(df, upload):
    rut_col = _find_column(df, "rut")
    nombre_col = _find_column(df, "nombre")
    ant_col = _find_column(df, "anterior")
    nuevo_col = _find_column(df, "nuevo")
    fecha_col = _find_column(df, "fecha")

    if not all([rut_col, nombre_col, ant_col, nuevo_col, fecha_col]):
        raise ValueError("Formato inválido hoja Tipo Contrato")

    count = 0
    for _, row in df.iterrows():
        rut = str(row.get(rut_col, "")).strip()
        if not rut:
            continue
        VariacionTipoContrato.objects.create(
            movimientos_mes=upload,
            empleado=_empleado_por_rut(rut),
            rut=rut,
            nombre=str(row.get(nombre_col, "")).strip(),
            tipo_anterior=str(row.get(ant_col, "")).strip(),
            tipo_nuevo=str(row.get(nuevo_col, "")).strip(),
            fecha=_parse_fecha(row.get(fecha_col)),
        )
        count += 1
    return count


@shared_task
def procesar_movimientos_mes(upload_id):
    logger.info("Procesando movimientos mes id=%s", upload_id)
    upload = MovimientosMesUpload.objects.get(id=upload_id)
    upload.estado = "en_proceso"
    upload.save()

    try:
        hojas = pd.read_excel(upload.archivo.path, sheet_name=None, engine="openpyxl")
        total = 0
        for nombre, df in hojas.items():
            lname = nombre.lower()
            if "alta" in lname or "baja" in lname:
                total += _procesar_alta_baja(df, upload)
            elif "ausent" in lname:
                total += _procesar_ausentismo(df, upload)
            elif "vacacion" in lname:
                total += _procesar_vacaciones(df, upload)
            elif "sueldo" in lname:
                total += _procesar_variacion_sueldo(df, upload)
            elif "contrato" in lname:
                total += _procesar_variacion_contrato(df, upload)

        upload.estado = "procesado"
        upload.save()
        logger.info("Movimientos procesados (%s registros) para upload %s", total, upload_id)
        return {"upload_id": upload_id, "registros": total}
    except Exception as e:
        logger.error("Error procesando movimientos mes %s: %s", upload_id, e)
        upload.estado = "con_error"
        upload.save()
        IncidenciaComparacion.objects.create(
            cierre=upload.cierre,
            tipo_incidencia="formato_movimientos",
            rut="",
            detalle=str(e),
        )
        raise
