# utils/llm.py
import requests
import json

def preguntar_ollama(mensaje, modelo="phi3"):
    url = "http://ollama:11434/api/chat"  # nombre del servicio dentro de docker
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": mensaje}]
    }
    try:
        response = requests.post(
            url,
            json=payload,
            stream=True  # 👈 importante
        )

        # Acumular todo el contenido de la respuesta
        contenido_completo = ""
        
        # Leer línea por línea y acumular el contenido
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if 'message' in data and 'content' in data['message']:
                        contenido_completo += data['message']['content']
                    
                    # Si el mensaje está completo (done=True), salir del bucle
                    if data.get('done', False):
                        break
                        
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON lines
        
        # Retornar todo el contenido acumulado
        if contenido_completo:
            return contenido_completo
        else:
            return "[Error] No se recibió respuesta válida del modelo"

    except Exception as e:
        return f"[Error llamando a Ollama] {e}"

