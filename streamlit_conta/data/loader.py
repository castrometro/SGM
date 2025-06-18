import json
import pathlib

def cargar_datos():
    current_dir = pathlib.Path(__file__).parent.resolve()
    json_file_path = current_dir / "proyectos_ejemplo.json"
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data
