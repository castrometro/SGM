#!/usr/bin/env python3
"""
Prueba simple de webhook con archivo mínimo
"""

import requests
import io
import pandas as pd

def crear_excel_minimo():
    """Crear Excel mínimo en memoria"""
    datos = {'A': [1], 'B': [2]}
    df = pd.DataFrame(datos)
    
    # Crear en memoria
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    
    return buffer

def test_webhook_simple():
    """Prueba básica del webhook"""
    url = 'http://localhost:5678/webhook-test/upload-excel'
    
    # Crear archivo Excel mínimo
    excel_buffer = crear_excel_minimo()
    
    files = {
        'data': ('test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    try:
        print(f"🔗 Conectando a: {url}")
        response = requests.post(url, files=files, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ ¡Webhook funcionando!")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar a n8n. ¿Está ejecutándose?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook_simple()
