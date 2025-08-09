#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA - CAPTURA MASIVA GASTOS
Prueba el sistema completo de procesamiento de gastos con Celery Chord
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"

def test_captura_masiva_gastos():
    """🚀 Prueba el endpoint de captura masiva de gastos"""
    print("🧪 PRUEBA CAPTURA MASIVA GASTOS")
    print("="*50)
    
    # Verificar que el archivo de prueba existe
    archivo_prueba = "/root/SGM/empleados_prueba.xlsx"
    
    try:
        # 1. SUBIR ARCHIVO
        print("📤 1. SUBIENDO ARCHIVO...")
        url_upload = f"{BASE_URL}/api/captura-masiva-gastos/"
        
        with open(archivo_prueba, 'rb') as file:
            files = {'archivo': file}
            headers = {
                # Agregar autenticación si es necesaria
                # 'Authorization': 'Bearer YOUR_TOKEN'
            }
            
            response = requests.post(url_upload, files=files, headers=headers, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 202:
                response_data = response.json()
                task_id = response_data.get('task_id')
                print(f"✅ Archivo subido exitosamente!")
                print(f"🆔 Task ID: {task_id}")
                
                # 2. MONITOREAR PROGRESO
                print(f"\n📊 2. MONITOREANDO PROGRESO...")
                url_status = f"{BASE_URL}/api/estado-captura-gastos/{task_id}/"
                
                max_intentos = 30
                for intento in range(max_intentos):
                    time.sleep(2)  # Esperar 2 segundos entre consultas
                    
                    status_response = requests.get(url_status)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        estado = status_data.get('estado')
                        progreso = status_data.get('progreso', 0)
                        
                        print(f"⏱️ Intento {intento + 1}/{max_intentos} - Estado: {estado} - Progreso: {progreso}%")
                        
                        if estado == 'COMPLETADO':
                            print("✅ ¡PROCESAMIENTO COMPLETADO!")
                            
                            # 3. DESCARGAR RESULTADO
                            print(f"\n📥 3. DESCARGANDO RESULTADO...")
                            url_download = f"{BASE_URL}/api/descargar-resultado-gastos/{task_id}/"
                            
                            download_response = requests.get(url_download)
                            
                            if download_response.status_code == 200:
                                # Guardar archivo resultado
                                archivo_resultado = f"resultado_gastos_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                                with open(archivo_resultado, 'wb') as f:
                                    f.write(download_response.content)
                                
                                print(f"✅ Archivo descargado: {archivo_resultado}")
                                print(f"📊 Tamaño: {len(download_response.content)} bytes")
                                
                                return True
                            else:
                                print(f"❌ Error al descargar: {download_response.status_code}")
                                print(f"📄 Response: {download_response.text}")
                                return False
                                
                        elif estado == 'ERROR':
                            print(f"❌ ERROR EN PROCESAMIENTO!")
                            error_msg = status_data.get('mensaje', 'Error desconocido')
                            print(f"📄 Mensaje: {error_msg}")
                            return False
                        
                    else:
                        print(f"❌ Error al consultar estado: {status_response.status_code}")
                        print(f"📄 Response: {status_response.text}")
                
                print("⏰ Timeout - El procesamiento tardó más de lo esperado")
                return False
                
            else:
                print(f"❌ Error al subir archivo: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {archivo_prueba}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """🎯 Función principal"""
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    exito = test_captura_masiva_gastos()
    
    print("\n" + "="*50)
    print("📋 RESULTADO FINAL")
    print("="*50)
    
    if exito:
        print("✅ PRUEBA EXITOSA")
        print("🎉 El sistema de captura masiva funciona correctamente!")
    else:
        print("❌ PRUEBA FALLIDA")
        print("🔧 Revisa los logs para más información:")
        print("   docker-compose logs django")
        print("   docker-compose logs celery_worker")
    
    print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
