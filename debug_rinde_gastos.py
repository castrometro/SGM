#!/usr/bin/env python3
"""
Script de debug para verificar el endpoint de estado de captura de gastos
"""
import requests
import json

# Configuración
task_id = "aa17692d-c2b3-43a5-9b3b-1678f40fd37e"
base_url = "http://localhost:8000"

def test_estado_endpoint():
    """Probar el endpoint de estado sin autenticación para debug"""
    url = f"{base_url}/api/estado-captura-gastos/{task_id}/"
    
    try:
        # Primero sin autenticación para ver el error
        response = requests.get(url)
        print(f"Status Code (sin auth): {response.status_code}")
        print(f"Response (sin auth): {response.text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def test_direct_redis():
    """Verificar directamente desde Redis"""
    import redis
    
    try:
        # Conectar a Redis
        r = redis.Redis(host='localhost', port=6379, db=1, password='Redis_Password_2025!')
        
        # Obtener metadatos
        key = f"captura_gastos_meta:10:{task_id}"
        metadata_raw = r.get(key)
        
        if metadata_raw:
            metadata = json.loads(metadata_raw.decode('utf-8'))
            print(f"\n=== METADATA DESDE REDIS ===")
            print(json.dumps(metadata, indent=2))
            print(f"\narchivo_excel_disponible: {metadata.get('archivo_excel_disponible')}")
        else:
            print(f"No se encontraron metadatos para la clave: {key}")
            
    except Exception as e:
        print(f"Error conectando a Redis: {str(e)}")

if __name__ == "__main__":
    print("=== TEST ENDPOINT ESTADO ===")
    test_estado_endpoint()
    
    print("\n=== TEST REDIS DIRECTO ===")
    test_direct_redis()
