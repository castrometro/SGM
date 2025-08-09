#!/usr/bin/env python3
"""
Script para crear un archivo Excel de prueba y enviarlo al webhook de n8n
"""

import pandas as pd
import requests
import os

def crear_excel_prueba():
    """Crear un archivo Excel de prueba"""
    # Datos de ejemplo
    datos = {
        'ID': [1, 2, 3, 4, 5],
        'Nombre': ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martín', 'Luis Rodríguez'],
        'Departamento': ['Ventas', 'Marketing', 'IT', 'RRHH', 'Finanzas'],
        'Salario': [3000, 3500, 4000, 2800, 4500],
        'Fecha_Ingreso': ['2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05', '2023-05-12']
    }
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    
    # Guardar como Excel
    archivo_excel = '/root/SGM/empleados_prueba.xlsx'
    df.to_excel(archivo_excel, index=False, sheet_name='Empleados')
    
    print(f"✅ Archivo Excel creado: {archivo_excel}")
    return archivo_excel

def enviar_a_n8n(archivo_excel):
    """Enviar archivo Excel al webhook de n8n"""
    url = 'http://localhost:5678/webhook-test/WEBHOOK_PATH'
    # Primero probar si n8n responde
    print("🔍 Probando conectividad con n8n...")
    try:
        test_response = requests.get('http://localhost:5678', timeout=10)
        print(f"✅ n8n está accesible: {test_response.status_code}")
    except Exception as e:
        print(f"❌ No se puede conectar a n8n: {e}")
        return  # Cambiar a localhost
    
    try:
        with open(archivo_excel, 'rb') as f:
            files = {'data': (os.path.basename(archivo_excel), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"📤 Enviando archivo a: {url}")
            print(f"📄 Tamaño del archivo: {os.path.getsize(archivo_excel)} bytes")
            
            response = requests.post(url, files=files, timeout=60)  # Aumentar timeout
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Archivo enviado correctamente!")
                try:
                    response_json = response.json()
                    print(f"📄 Respuesta JSON:")
                    import json
                    print(json.dumps(response_json, indent=2, ensure_ascii=False))
                except:
                    print(f"📄 Respuesta texto: {response.text}")
            else:
                print(f"❌ Error al enviar archivo: {response.status_code}")
                print(f"📄 Respuesta: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {archivo_excel}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def main():
    print("🚀 Iniciando prueba de upload Excel a n8n")
    print("=" * 50)
    
    # Crear archivo Excel
    archivo = crear_excel_prueba()
    
    # Enviar a n8n
    enviar_a_n8n(archivo)
    
    print("=" * 50)
    print("✅ Prueba completada")

if __name__ == "__main__":
    main()
