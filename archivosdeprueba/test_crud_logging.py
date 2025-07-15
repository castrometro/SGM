#!/usr/bin/env python3
"""
Script de prueba para verificar que las operaciones CRUD 
de las tarjetas registren actividad correctamente.
"""

import requests
import json
import sys

# Configuración
BASE_URL = "http://localhost:8001/api/contabilidad"
CLIENTE_ID = 2  # Cliente de prueba

def test_tipo_documento_crud():
    """Probar CRUD de tipos de documento"""
    print("🔍 Probando CRUD de Tipos de Documento...")
    
    # 1. Crear tipo documento
    print("  ➤ Creando tipo documento...")
    create_data = {
        "codigo": "TEST001",
        "descripcion": "Tipo de prueba para logging",
        "cliente": CLIENTE_ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tipos-documento/", json=create_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            tipo_id = response.json().get('id')
            print(f"    ✅ Tipo documento creado con ID: {tipo_id}")
            
            # 2. Actualizar tipo documento
            print("  ➤ Actualizando tipo documento...")
            update_data = {
                "codigo": "TEST001",
                "descripcion": "Tipo actualizado para prueba de logging",
                "cliente": CLIENTE_ID
            }
            
            response = requests.put(f"{BASE_URL}/tipos-documento/{tipo_id}/", json=update_data)
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                print("    ✅ Tipo documento actualizado")
            
            # 3. Eliminar tipo documento
            print("  ➤ Eliminando tipo documento...")
            response = requests.delete(f"{BASE_URL}/tipos-documento/{tipo_id}/")
            print(f"    Status: {response.status_code}")
            if response.status_code == 204:
                print("    ✅ Tipo documento eliminado")
        else:
            print(f"    ❌ Error creando: {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_nombres_ingles_crud():
    """Probar CRUD de nombres en inglés"""
    print("\n🔍 Probando CRUD de Nombres en Inglés...")
    
    # 1. Crear nombre en inglés
    print("  ➤ Creando nombre en inglés...")
    create_data = {
        "cuenta_codigo": "1001001",
        "nombre_ingles": "Test Account for Logging",
        "cliente": CLIENTE_ID
    }
    
    try:
        response = requests.post(f"{BASE_URL}/nombres-ingles/", json=create_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 201:
            nombre_id = response.json().get('id')
            print(f"    ✅ Nombre en inglés creado con ID: {nombre_id}")
            
            # 2. Actualizar nombre en inglés
            print("  ➤ Actualizando nombre en inglés...")
            update_data = {
                "cuenta_codigo": "1001001",
                "nombre_ingles": "Updated Test Account for Logging",
                "cliente": CLIENTE_ID
            }
            
            response = requests.put(f"{BASE_URL}/nombres-ingles/{nombre_id}/", json=update_data)
            print(f"    Status: {response.status_code}")
            if response.status_code == 200:
                print("    ✅ Nombre en inglés actualizado")
            
            # 3. Eliminar nombre en inglés
            print("  ➤ Eliminando nombre en inglés...")
            response = requests.delete(f"{BASE_URL}/nombres-ingles/{nombre_id}/")
            print(f"    Status: {response.status_code}")
            if response.status_code == 204:
                print("    ✅ Nombre en inglés eliminado")
        else:
            print(f"    ❌ Error creando: {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def verificar_logs():
    """Verificar que se crearon logs de actividad"""
    print("\n🔍 Verificando logs de actividad...")
    
    try:
        # Obtener logs recientes
        response = requests.get(f"{BASE_URL}/activity-logs/?ordering=-timestamp&limit=10")
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            logs = response.json().get('results', [])
            print(f"    📋 Encontrados {len(logs)} logs recientes")
            
            # Filtrar logs de prueba
            test_logs = [log for log in logs if 'prueba' in log.get('descripcion', '').lower() or 'test' in log.get('descripcion', '').lower()]
            
            if test_logs:
                print("    ✅ Logs de prueba encontrados:")
                for log in test_logs:
                    print(f"      - {log['timestamp']}: {log['tarjeta']} - {log['accion']} - {log['descripcion']}")
            else:
                print("    ⚠️  No se encontraron logs específicos de prueba")
        else:
            print(f"    ❌ Error obteniendo logs: {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de logging CRUD...")
    
    # Ejecutar pruebas
    test_tipo_documento_crud()
    test_nombres_ingles_crud()
    verificar_logs()
    
    print("\n✅ Pruebas completadas. Revisa los logs en el admin de Django para ver la actividad registrada.")
