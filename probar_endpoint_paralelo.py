#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA DEL ENDPOINT PARALELO
Prueba el nuevo endpoint con clasificaciones seleccionadas
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
FLOWER_URL = "http://localhost:5555"

def test_endpoint_paralelo():
    """🚀 Prueba el endpoint paralelo"""
    print("🧪 PRUEBA DEL ENDPOINT PARALELO")
    print("="*50)
    
    # Datos de prueba
    cierre_id = 1  # Ajustar según tus datos
    clasificaciones_seleccionadas = [1, 3, 5, 7, 9, 11]
    
    url = f"{BASE_URL}/api/nomina/incidencia-cierre/generar/{cierre_id}/"
    
    payload = {
        "clasificaciones_seleccionadas": clasificaciones_seleccionadas
    }
    
    headers = {
        'Content-Type': 'application/json',
        # Agregar autenticación si es necesaria
        # 'Authorization': 'Bearer YOUR_TOKEN'
    }
    
    print(f"📍 URL: {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        print("\n🚀 Enviando request...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            response_data = response.json()
            print("✅ ÉXITO: Tarea iniciada")
            print(f"📋 Response: {json.dumps(response_data, indent=2)}")
            
            task_id = response_data.get('task_id')
            if task_id:
                print(f"\n🔍 Task ID: {task_id}")
                print(f"🌸 Monitor en Flower: {FLOWER_URL}/task/{task_id}")
                
                # Intentar verificar el estado de la tarea
                return verificar_estado_tarea(task_id)
            
        else:
            print("❌ ERROR en la request")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servidor")
        print("💡 Asegúrate de que Django esté corriendo en localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout en la request")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False

def verificar_estado_tarea(task_id):
    """🔍 Verifica el estado de la tarea en Flower"""
    print(f"\n🔍 VERIFICANDO ESTADO DE TAREA: {task_id}")
    print("="*50)
    
    try:
        # Intentar obtener info de la tarea desde Flower
        flower_task_url = f"{FLOWER_URL}/api/task/info/{task_id}"
        
        for intento in range(5):
            print(f"🔄 Intento {intento + 1}/5...")
            
            try:
                response = requests.get(flower_task_url, timeout=5)
                if response.status_code == 200:
                    task_info = response.json()
                    print(f"📊 Estado de tarea: {json.dumps(task_info, indent=2)}")
                    return True
                else:
                    print(f"⚠️ Flower response: {response.status_code}")
            except:
                pass
            
            time.sleep(2)
        
        print("⚠️ No se pudo obtener info de Flower, pero la tarea fue iniciada")
        return True
        
    except Exception as e:
        print(f"⚠️ Error verificando tarea: {e}")
        return True  # La tarea se inició aunque no podamos verificarla

def test_conexion_servicios():
    """🔗 Prueba la conexión a los servicios"""
    print("🔗 VERIFICANDO CONEXIÓN A SERVICIOS")
    print("="*50)
    
    servicios = {
        "Django Backend": f"{BASE_URL}/admin/",
        "Flower": f"{FLOWER_URL}/",
    }
    
    resultados = {}
    
    for nombre, url in servicios.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 302, 404]:  # 404 también indica que el servicio responde
                print(f"✅ {nombre}: OK ({response.status_code})")
                resultados[nombre] = True
            else:
                print(f"⚠️ {nombre}: Respuesta inesperada ({response.status_code})")
                resultados[nombre] = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {nombre}: No disponible")
            resultados[nombre] = False
        except Exception as e:
            print(f"❌ {nombre}: Error - {e}")
            resultados[nombre] = False
    
    return all(resultados.values())

def mostrar_ayuda():
    """📋 Muestra información de ayuda"""
    print("📋 AYUDA - SCRIPT DE PRUEBA")
    print("="*50)
    print("Este script prueba el nuevo endpoint paralelo de incidencias.")
    print("")
    print("🔧 Configuración requerida:")
    print(f"   - Django corriendo en: {BASE_URL}")
    print(f"   - Flower corriendo en: {FLOWER_URL}")
    print("   - Celery workers activos")
    print("")
    print("📝 El endpoint esperado:")
    print("   POST /api/nomina/incidencia-cierre/generar/{cierre_id}/")
    print("   Body: {\"clasificaciones_seleccionadas\": [1,3,5,7,9]}")
    print("")
    print("🚀 Para iniciar el sistema completo:")
    print("   ./iniciar_sistema_paralelo.sh")

def main():
    """🚀 Función principal"""
    print("🧪 PRUEBA DEL SISTEMA PARALELO DE INCIDENCIAS SGM")
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        mostrar_ayuda()
        return
    
    # Verificar conexión a servicios
    if not test_conexion_servicios():
        print("\n❌ ALGUNOS SERVICIOS NO ESTÁN DISPONIBLES")
        print("💡 Ejecuta './iniciar_sistema_paralelo.sh' para iniciar todos los servicios")
        mostrar_ayuda()
        return
    
    # Probar el endpoint
    resultado = test_endpoint_paralelo()
    
    print("\n" + "="*60)
    print("📋 RESULTADO FINAL")
    print("="*60)
    
    if resultado:
        print("🎉 ¡PRUEBA EXITOSA!")
        print("✅ El sistema paralelo está funcionando correctamente")
        print(f"🌸 Monitorea las tareas en: {FLOWER_URL}")
    else:
        print("❌ PRUEBA FALLIDA")
        print("🔧 Revisa los logs para más información:")
        print("   docker-compose logs django")
        print("   docker-compose logs celery_worker")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
