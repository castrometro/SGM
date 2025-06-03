import pandas as pd
import logging

from nomina.models import ConceptoRemuneracion, LibroRemuneracionesUpload

logger = logging.getLogger(__name__)

def obtener_headers_libro_remuneraciones(path_archivo):
    logger.info(f"Abriendo archivo de libro de remuneraciones: {path_archivo}")
    try:
        df = pd.read_excel(path_archivo)
        headers = list(df.columns)
        logger.info(f"Headers encontrados: {headers}")
        return headers
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