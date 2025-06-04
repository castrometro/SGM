import pandas as pd
import logging

from nomina.models import ConceptoRemuneracion, LibroRemuneracionesUpload

logger = logging.getLogger(__name__)

def obtener_headers_libro_remuneraciones(path_archivo):
    """Obtiene los encabezados de un libro de remuneraciones.

    Filtra las columnas que se utilizan para poblar el modelo ``Empleado``
    antes de retornar el listado.
    """
    logger.info(f"Abriendo archivo de libro de remuneraciones: {path_archivo}")
    try:
        df = pd.read_excel(path_archivo)
        headers = list(df.columns)

        rut_col = next((c for c in headers if 'rut' in c.lower() and 'trab' in c.lower()), None)
        dv_col = next((c for c in headers if 'dv' in c.lower() and 'trab' in c.lower()), None)
        ape_pat_col = next((c for c in headers if 'apellido' in c.lower() and 'pater' in c.lower()), None)
        ape_mat_col = next((c for c in headers if 'apellido' in c.lower() and 'mater' in c.lower()), None)
        nombres_col = next((c for c in headers if 'nombre' in c.lower()), None)
        ingreso_col = next((c for c in headers if 'ingreso' in c.lower()), None)

        empleado_cols = {c for c in [rut_col, dv_col, ape_pat_col, ape_mat_col, nombres_col, ingreso_col] if c}
        filtered_headers = [h for h in headers if h not in empleado_cols]

        logger.info(f"Headers encontrados: {filtered_headers}")
        return filtered_headers
    except Exception as e:
        logger.error(f"Error al leer el archivo: {e}")
        raise

def clasificar_headers_libro_remuneraciones(headers, cliente):
    """
    Clasifica los headers usando los ConceptoRemuneracion vigentes del cliente.
    Retorna dos listas: clasificados y sin clasificar.
    """
    # Obtén los conceptos vigentes del cliente, normalizados a lower y sin espacios
    conceptos_vigentes = set(
        c.nombre_concepto.strip().lower()
        for c in ConceptoRemuneracion.objects.filter(cliente=cliente, vigente=True)
    )
    headers_clasificados = []
    headers_sin_clasificar = []

    for h in headers:
        if h.strip().lower() in conceptos_vigentes:
            headers_clasificados.append(h)
        else:
            headers_sin_clasificar.append(h)

    logger.info(
        f"Clasificación automática: {len(headers_clasificados)} clasificados, {len(headers_sin_clasificar)} sin clasificar"
    )
    return headers_clasificados, headers_sin_clasificar