# nomina/tasks.py
from .utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
)
from celery import shared_task, chain
from .models import (
    LibroRemuneracionesUpload,
    EmpleadoCierre,
    RegistroConceptoEmpleado,
    ConceptoRemuneracion,
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
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")

        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_empresa": "Rut de la Empresa",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }

        missing = [v for v in expected.values() if v not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas en el Excel: {', '.join(missing)}")

        cierre = libro.cierre
        primera_col = df.columns[0]
        count = 0
        for _, row in df.iterrows():
            if not str(row.get(primera_col, "")).strip():
                continue
            rut = str(row.get(expected["rut_trabajador"], "")).strip()
            defaults = {
                "rut_empresa": str(row.get(expected["rut_empresa"], "")).strip(),
                "nombre": str(row.get(expected["nombre"], "")).strip(),
                "apellido_paterno": str(row.get(expected["ape_pat"], "")).strip(),
                "apellido_materno": str(row.get(expected["ape_mat"], "")).strip(),
            }
            EmpleadoCierre.objects.update_or_create(
                cierre=cierre,
                rut=rut,
                defaults=defaults,
            )
            count += 1
        logger.info(f"Actualizados {count} empleados desde libro {libro_id}")
        return {"libro_id": libro_id, "empleados_actualizados": count}
    except Exception as e:
        logger.error(f"Error actualizando empleados para libro id={libro_id}: {e}")
        raise


@shared_task
def guardar_registros_nomina(result):
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")

        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_empresa": "Rut de la Empresa",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }

        missing = [v for v in expected.values() if v not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas en el Excel: {', '.join(missing)}")

        empleado_cols = set(expected.values())

        headers = libro.header_json
        if isinstance(headers, dict):
            headers = headers.get("headers_clasificados", []) + headers.get(
                "headers_sin_clasificar", []
            )
        if not headers:
            headers = [h for h in df.columns if h not in empleado_cols]

        primera_col = df.columns[0]
        count = 0
        for _, row in df.iterrows():
            if not str(row.get(primera_col, "")).strip():
                continue
            rut = str(row.get(expected["rut_trabajador"], "")).strip()
            empleado = EmpleadoCierre.objects.filter(
                cierre=libro.cierre, rut=rut
            ).first()
            if not empleado:
                continue

            for h in headers:
                monto = row.get(h)
                concepto = ConceptoRemuneracion.objects.filter(
                    cliente=libro.cierre.cliente, nombre_concepto=h, vigente=True
                ).first()
                RegistroConceptoEmpleado.objects.update_or_create(
                    empleado=empleado,
                    nombre_concepto_original=h,
                    defaults={"monto": monto, "concepto": concepto},
                )
            count += 1

        logger.info(f"Registros nómina guardados desde libro {libro_id}: {count}")
        return {"libro_id": libro_id, "registros_actualizados": count}
    except Exception as e:
        logger.error(
            f"Error guardando registros de nómina para libro id={libro_id}: {e}"
        )
        raise


@shared_task
def procesar_libro_remuneraciones(libro_id):
    """Ejecuta el flujo completo de procesamiento de un libro."""
    return chain(
        actualizar_empleados_desde_libro.s(libro_id),
        guardar_registros_nomina.s(),
    )()
