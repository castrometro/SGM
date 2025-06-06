from contabilidad.models import Cliente, TipoDocumento
from django.core.files.storage import default_storage
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def parsear_tipo_documento_excel(cliente_id, ruta_relativa):
    path = default_storage.path(ruta_relativa)

    try:
        df = pd.read_excel(path, engine="openpyxl")
        df.columns = df.columns.str.lower()
        df = df.dropna(subset=["codigo"])
    except Exception as e:
        logger.error("[ERROR XLSX] %s", e)
        default_storage.delete(ruta_relativa)
        return False, f"Error leyendo archivo: {e}"

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        default_storage.delete(ruta_relativa)
        return False, "Cliente no existe"

    # Eliminar anteriores
    TipoDocumento.objects.filter(cliente=cliente).delete()

    # Crear nuevos
    objetos = [
        TipoDocumento(cliente=cliente, codigo=row["codigo"], descripcion=row["descripcion"])
        for _, row in df.iterrows()
    ]
    TipoDocumento.objects.bulk_create(objetos)

    # Borrar archivo
    default_storage.delete(ruta_relativa)

    logger.info("✅ Procesados %s tipos para cliente %s", len(objetos), cliente.nombre)
    return True, f"{len(objetos)} tipos creados"
