#!/usr/bin/env python3
"""
Script para probar la subida de Excel a n8n
"""
import requests
import json
from pathlib import Path

def test_upload_excel():
    """Prueba la subida de un archivo Excel al webhook de n8n"""
    
    # URL del webhook de n8n
    webhook_url = "http://localhost:5678/webhook-test/upload-excel"
    
    # Crear un archivo Excel de prueba si no existe
    sample_excel_path = "/root/SGM/sample_data.xlsx"
    
    if not Path(sample_excel_path).exists():
        print("🔄 Creando archivo Excel de prueba...")
        import pandas as pd
        
        # Datos de ejemplo
        data = {
            'Nombre': ['Juan Pérez', 'María González', 'Carlos López'],
            'Edad': [25, 30, 35],
            'Departamento': ['IT', 'RRHH', 'Finanzas'],
            'Salario': [50000, 55000, 60000]
        }
        
        df = pd.DataFrame(data)
        df.to_excel(sample_excel_path, index=False)
        print(f"✅ Archivo creado: {sample_excel_path}")
    
    try:
        # Enviar archivo al webhook
        print(f"📤 Enviando archivo a: {webhook_url}")
        
        with open(sample_excel_path, 'rb') as file:
            files = {'data': file}
            response = requests.post(webhook_url, files=files, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ ¡Archivo enviado exitosamente!")
            try:
                result = response.json()
                print(f"📄 Respuesta JSON: {json.dumps(result, indent=2)}")
            except:
                print(f"📄 Respuesta texto: {response.text}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload_excel()
