import openpyxl
from contabilidad.models import CuentaContable
from django.core.files.storage import default_storage
import logging

logger = logging.getLogger(__name__)

def procesar_archivo_nombres_ingles(cliente_id, path_archivo):
    path = default_storage.path(path_archivo)
    logger.info("Procesando archivo de nombres en inglés: %s", path)
    wb = openpyxl.load_workbook(filename=path)
    ws = wb.active
    actualizados = 0
    for idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        codigo = str(row[0].value).strip() if row[0].value else ""
        nombre_en = str(row[1].value).strip() if len(row) > 1 and row[1].value else ""
        logger.debug("[Fila %s] codigo: '%s' | nombre_en: '%s'", idx, codigo, nombre_en)
        if codigo and nombre_en:
            try:
                cuenta = CuentaContable.objects.get(cliente_id=cliente_id, codigo=codigo)
                cuenta.nombre_en = nombre_en
                cuenta.save(update_fields=["nombre_en"])
                actualizados += 1
            except CuentaContable.DoesNotExist:
                logger.warning("[Fila %s] No existe cuenta con código: '%s' para cliente: %s", idx, codigo, cliente_id)
                continue
        else:
            logger.warning("[Fila %s] Código vacío o nombre_en vacío: '%s', '%s'", idx, codigo, nombre_en)
    default_storage.delete(path_archivo)
    logger.info("✅ Procesados %s nombres en inglés para cliente %s", actualizados, cliente_id)
    return actualizados
