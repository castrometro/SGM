from datetime import datetime
import glob
import os
import time

from django.core.files.storage import default_storage

from ..models import UploadLog


def validar_nombre_archivo(nombre_archivo: str, tipo_upload: str, cliente):
    """Wrapper util para validar nombre usando el modelo UploadLog."""
    return UploadLog.validar_archivo_cliente_estatico(nombre_archivo, tipo_upload, cliente)


def limpiar_temporales(pattern: str = "temp/*.xlsx", max_age_hours: int = 24) -> int:
    """Elimina archivos temporales que superen ``max_age_hours``"""
    base = default_storage.location
    ruta = os.path.join(base, pattern)
    count = 0
    for path in glob.glob(ruta):
        try:
            if (time.time() - os.path.getmtime(path)) > max_age_hours * 3600:
                os.remove(path)
                count += 1
        except OSError:
            continue
    return count


def guardar_temporal(nombre: str, archivo) -> str:
    """Guarda ``archivo`` en ``media/temp`` y devuelve la ruta relativa."""
    nombre = os.path.join("temp", nombre)
    return default_storage.save(nombre, archivo)
