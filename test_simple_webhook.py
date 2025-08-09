#!/usr/bin/env python3
"""
Prueba simple para webhook n8n
"""
import requests

def test_simple():
    print("🧪 Prueba simple del webhook...")
    
    try:
        # Prueba POST simple sin archivo
        url = 'http://172.17.11.18:5678/webhook/simple-test'  # Corregir IP y URL
        data = {"test": "simple"}
        
        print(f"📤 Enviando datos simples a: {url}")
        response = requests.post(url, json=data, timeout=5)  # Timeout más corto para probar
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple()
