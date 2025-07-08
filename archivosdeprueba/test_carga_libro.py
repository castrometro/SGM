#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de carga de libro de remuneraciones
"""

import os
import requests
import pandas as pd
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/nomina/upload/libro-remuneraciones/"
USERNAME = "admin"  # Cambiar por tu usuario
PASSWORD = "admin"  # Cambiar por tu contraseña

def obtener_token():
    """Obtener token de autenticación"""
    print("🔐 Obteniendo token de autenticación...")
    
    response = requests.post(
        f"{BASE_URL}/api/token/",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access"]
        print("✅ Token obtenido exitosamente")
        return token
    else:
        print(f"❌ Error obteniendo token: {response.status_code}")
        print(response.text)
        return None

def crear_archivo_prueba():
    """Crear archivo Excel de prueba"""
    print("📄 Creando archivo de prueba...")
    
    # Crear datos de prueba
    data = {
        "Año": [2024] * 5,
        "Mes": [12] * 5,
        "Rut de la Empresa": ["12345678-9"] * 5,
        "Rut del Trabajador": ["98765432-1", "87654321-2", "76543210-3", "65432109-4", "54321098-5"],
        "Nombre": ["Juan", "María", "Carlos", "Ana", "Pedro"],
        "Apellido Paterno": ["Pérez", "González", "Rodríguez", "Martínez", "López"],
        "Apellido Materno": ["Silva", "Morales", "Hernández", "Castillo", "Vargas"],
        "Sueldo Base": [800000, 900000, 750000, 850000, 700000],
        "Horas Extras": [50000, 75000, 0, 25000, 100000],
        "Bono Asistencia": [30000, 30000, 30000, 30000, 30000],
        "Descuento AFP": [80000, 90000, 75000, 85000, 70000],
        "Descuento Salud": [64000, 72000, 60000, 68000, 56000],
    }
    
    df = pd.DataFrame(data)
    archivo_prueba = "/tmp/12345678_LibroRemuneraciones.xlsx"
    df.to_excel(archivo_prueba, index=False, engine='openpyxl')
    
    print(f"✅ Archivo de prueba creado: {archivo_prueba}")
    return archivo_prueba

def probar_carga_libro():
    """Probar la carga del libro de remuneraciones"""
    print("🧪 PROBANDO CARGA DE LIBRO DE REMUNERACIONES")
    print("=" * 50)
    
    # Obtener token
    token = obtener_token()
    if not token:
        return False
    
    # Crear archivo de prueba
    archivo_prueba = crear_archivo_prueba()
    if not os.path.exists(archivo_prueba):
        print(f"❌ Error: No se pudo crear el archivo de prueba")
        return False
    
    # Preparar headers
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Preparar datos
    data = {
        "cierre_id": 1  # Usar un ID de cierre que exista
    }
    
    # Preparar archivo
    files = {
        "archivo": ("12345678_LibroRemuneraciones.xlsx", open(archivo_prueba, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    
    try:
        print(f"📤 Enviando archivo a: {API_URL}")
        print(f"📋 Datos: {data}")
        
        response = requests.post(
            API_URL,
            headers=headers,
            data=data,
            files=files
        )
        
        print(f"📊 Respuesta: {response.status_code}")
        print(f"📄 Contenido: {response.text}")
        
        if response.status_code == 200:
            print("✅ Archivo cargado exitosamente")
            return True
        else:
            print(f"❌ Error en la carga: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Error durante la prueba: {str(e)}")
        return False
    
    finally:
        # Limpiar archivo
        files["archivo"][1].close()
        if os.path.exists(archivo_prueba):
            os.remove(archivo_prueba)
            print("🧹 Archivo de prueba eliminado")

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBA DE CARGA DE LIBRO DE REMUNERACIONES")
    print("=" * 60)
    
    # Verificar que pandas esté disponible
    try:
        import pandas as pd
        print("✅ Pandas disponible")
    except ImportError:
        print("❌ Pandas no está disponible")
        print("💡 Instálalo con: pip install pandas openpyxl")
        return
    
    # Verificar que requests esté disponible
    try:
        import requests
        print("✅ Requests disponible")
    except ImportError:
        print("❌ Requests no está disponible")
        print("💡 Instálalo con: pip install requests")
        return
    
    # Ejecutar prueba
    resultado = probar_carga_libro()
    
    if resultado:
        print("\n🎉 PRUEBA EXITOSA")
    else:
        print("\n💥 PRUEBA FALLIDA")
        print("💡 Verifica:")
        print("   - El servidor está corriendo")
        print("   - Las credenciales son correctas")
        print("   - El cierre_id existe")
        print("   - Los logs del servidor para más detalles")

if __name__ == "__main__":
    main()
