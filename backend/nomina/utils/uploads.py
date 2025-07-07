# backend/nomina/utils/uploads.py

import os
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage


def guardar_temporal(nombre_archivo, archivo):
    """
    Guarda un archivo en el directorio temporal
    """
    # Crear directorio temporal si no existe
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", "nomina")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Ruta completa del archivo
    ruta_completa = os.path.join(temp_dir, nombre_archivo)
    
    # Guardar archivo
    with open(ruta_completa, 'wb') as f:
        for chunk in archivo.chunks():
            f.write(chunk)
    
    return ruta_completa


def limpiar_archivo_temporal(ruta_archivo):
    """
    Elimina un archivo temporal
    """
    try:
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            return True
    except Exception as e:
        print(f"Error al eliminar archivo temporal {ruta_archivo}: {e}")
    
    return False


def obtener_ruta_temporal(nombre_archivo):
    """
    Obtiene la ruta temporal para un archivo
    """
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", "nomina")
    return os.path.join(temp_dir, nombre_archivo)


def validar_archivo_existe(ruta_archivo):
    """
    Valida que un archivo existe
    """
    return os.path.exists(ruta_archivo) and os.path.isfile(ruta_archivo)


def obtener_tamaño_archivo(ruta_archivo):
    """
    Obtiene el tamaño de un archivo en bytes
    """
    try:
        return os.path.getsize(ruta_archivo)
    except (OSError, FileNotFoundError):
        return 0


def crear_directorio_temporal(subdirectorio=None):
    """
    Crea un directorio temporal para nómina
    """
    if subdirectorio:
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", "nomina", subdirectorio)
    else:
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", "nomina")
    
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def limpiar_directorio_temporal(max_age_hours=24):
    """
    Limpia archivos temporales antiguos
    """
    import time
    
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", "nomina")
    
    if not os.path.exists(temp_dir):
        return []
    
    archivos_eliminados = []
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    archivos_eliminados.append(file_path)
                except Exception as e:
                    print(f"Error al eliminar archivo {file_path}: {e}")
    
    return archivos_eliminados
