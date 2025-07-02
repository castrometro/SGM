#!/usr/bin/env python3
"""
Test rápido para verificar que los endpoints de opciones estén funcionando
"""

import requests
import json

def test_obtener_opciones(set_id, base_url="http://localhost:8000"):
    """Test básico para verificar endpoints de opciones"""
    
    print(f"🔍 Testeando opciones para set {set_id}")
    
    # Test endpoint normal
    try:
        url_normal = f"{base_url}/api/contabilidad/sets/{set_id}/opciones/"
        print(f"📡 GET {url_normal}")
        
        response = requests.get(url_normal)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Opciones normales: {len(data)} items")
            if data:
                print(f"   Ejemplo: {data[0] if data else 'N/A'}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception en endpoint normal: {e}")
    
    # Test endpoint bilingüe
    try:
        url_bilingue = f"{base_url}/api/contabilidad/clasificacion/opciones-bilingues/{set_id}/"
        print(f"📡 GET {url_bilingue}")
        
        response = requests.get(url_bilingue)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Opciones bilingües: {len(data)} items")
            if data:
                print(f"   Ejemplo: {data[0] if data else 'N/A'}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception en endpoint bilingüe: {e}")

def test_obtener_sets(cliente_id, base_url="http://localhost:8000"):
    """Test para obtener sets de un cliente"""
    
    print(f"🔍 Testeando sets para cliente {cliente_id}")
    
    try:
        url = f"{base_url}/api/contabilidad/sets/cliente/{cliente_id}/"
        print(f"📡 GET {url}")
        
        response = requests.get(url)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sets encontrados: {len(data)}")
            
            for set_data in data[:3]:  # Solo los primeros 3 para no spamear
                print(f"   📋 Set: {set_data.get('id')} - {set_data.get('nombre')}")
                test_obtener_opciones(set_data.get('id'), base_url)
                print()
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🧪 Test de endpoints de opciones")
    print("=" * 50)
    
    # Cambiar estos valores según sea necesario
    CLIENTE_ID = 1  # Cambiar por un cliente ID válido
    
    test_obtener_sets(CLIENTE_ID)
