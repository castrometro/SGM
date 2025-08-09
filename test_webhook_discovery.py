#!/usr/bin/env python3
"""
Probar diferentes URLs de webhook para encontrar la correcta
"""
import requests

def test_webhook_paths():
    print("🔍 Probando diferentes paths de webhook...")
    
    base_urls = [
        'http://172.17.11.18:5678/webhook/upload-excel',
        'http://172.17.11.18:5678/webhook-test/upload-excel', 
        'http://172.17.11.18:5678/webhook/My%20workflow',
        'http://172.17.11.18:5678/webhook/excel',
        'http://172.17.11.18:5678/webhook/test'
    ]
    
    for url in base_urls:
        try:
            print(f"\n📤 Probando: {url}")
            response = requests.post(url, json={"test": "simple"}, timeout=3)
            print(f"✅ Status: {response.status_code}")
            if response.status_code != 404:
                print(f"📄 Response: {response.text[:200]}...")
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout (webhook existe pero no responde)")
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}...")

if __name__ == "__main__":
    test_webhook_paths()
