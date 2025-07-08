import json
import pathlib
import os


def cargar_datos(archivo_nombre=None):
    current_dir = pathlib.Path(__file__).parent.resolve()
    
    if archivo_nombre is None:
        archivo_nombre = "payroll_prueba.json"
    
    json_file_path = current_dir / archivo_nombre
    
    if not json_file_path.exists():
        archivos_disponibles = [
            "payroll_prueba.json",
            "payroll_marzo.json"
        ]
        
        for archivo in archivos_disponibles:
            archivo_path = current_dir / archivo
            if archivo_path.exists():
                json_file_path = archivo_path
                break
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return {}


def obtener_archivos_disponibles():
    current_dir = pathlib.Path(__file__).parent.resolve()
    archivos = []
    
    for archivo in current_dir.glob("*.json"):
        if archivo.name.startswith("payroll_"):
            archivos.append(archivo.name)
    
    return sorted(archivos)
