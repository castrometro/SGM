from contabilidad.models import Cliente, TipoDocumento, TipoDocumentoArchivo
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import logging
import os
import shutil

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

    # Guardar archivo permanentemente antes de eliminar
    try:
        # Eliminar archivo anterior si existe
        try:
            archivo_anterior = TipoDocumentoArchivo.objects.get(cliente=cliente)
            if archivo_anterior.archivo:
                archivo_anterior.archivo.delete()
            archivo_anterior.delete()
        except TipoDocumentoArchivo.DoesNotExist:
            pass
        
        # Copiar archivo temporal a ubicación permanente
        with open(path, 'rb') as temp_file:
            contenido = temp_file.read()
            nombre_permanente = f"tipo_documento/cliente_{cliente_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Crear registro permanente
            archivo_permanente = TipoDocumentoArchivo.objects.create(
                cliente=cliente,
                archivo=ContentFile(contenido, name=nombre_permanente)
            )
            
        logger.info("📁 Archivo guardado permanentemente: %s", nombre_permanente)
        
    except Exception as e:
        logger.warning("⚠️ No se pudo guardar archivo permanente: %s", str(e))
        # Continuar aunque falle el guardado del archivo

    # Borrar archivo temporal
    default_storage.delete(ruta_relativa)

    logger.info("✅ Procesados %s tipos para cliente %s", len(objetos), cliente.nombre)
    return True, f"{len(objetos)} tipos creados"
