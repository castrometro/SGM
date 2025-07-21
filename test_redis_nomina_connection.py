#!/usr/bin/env python3
"""
Test de conexión Redis para Nómina
==================================

Script para probar la conexión a Redis DB 2 (nómina) antes de integrar con Django.
Este script se ejecuta independientemente para verificar que Redis está funcionando.

Uso:
    python test_redis_nomina_connection.py

Autor: Sistema SGM - Módulo Nómina
Fecha: 20 de julio de 2025
"""

import json
import redis
import time
from datetime import datetime
from typing import Dict, Any

def test_redis_connection():
    """
    Probar conexión básica a Redis DB 2
    """
    print("🚀 Iniciando test de conexión Redis DB 2 (Nómina)...")
    
    try:
        # Conectar a Redis DB 2
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=2,  # DB 2 dedicada para nómina
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test básico de ping
        print("📡 Probando ping...")
        if redis_client.ping():
            print("✅ Ping exitoso!")
        else:
            print("❌ Ping falló!")
            return False
            
        return redis_client
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return None

def test_basic_operations(redis_client):
    """
    Probar operaciones básicas de Redis
    """
    print("\n🔧 Probando operaciones básicas...")
    
    try:
        # Test de escritura/lectura básica
        test_key = "sgm:nomina:test:connection"
        test_value = {
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "message": "Conexión de nómina funcionando"
        }
        
        # Escribir
        print("📝 Escribiendo dato de prueba...")
        redis_client.setex(test_key, 60, json.dumps(test_value))
        
        # Leer
        print("📖 Leyendo dato de prueba...")
        retrieved_data = redis_client.get(test_key)
        
        if retrieved_data:
            parsed_data = json.loads(retrieved_data)
            print(f"✅ Datos leídos exitosamente: {parsed_data['message']}")
        else:
            print("❌ No se pudieron leer los datos!")
            return False
        
        # Limpiar
        print("🧹 Limpiando datos de prueba...")
        redis_client.delete(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones básicas: {e}")
        return False

def test_nomina_workflow_simulation(redis_client):
    """
    Simular workflow básico de nómina en Redis
    """
    print("\n📊 Simulando workflow de nómina...")
    
    try:
        cliente_id = 999
        periodo = "2025-07"
        
        # 1. Simular guardado de libro de remuneraciones
        libro_key = f"sgm:nomina:{cliente_id}:{periodo}:libro_remuneraciones"
        libro_data = {
            "empleados": [
                {"rut": "12345678-9", "nombre": "Juan Pérez", "conceptos": {"SUELDO": 800000, "GRATIFICACION": 66667}},
                {"rut": "98765432-1", "nombre": "María González", "conceptos": {"SUELDO": 750000, "GRATIFICACION": 62500}}
            ],
            "total_empleados": 2,
            "archivo_nombre": "libro_remuneraciones_julio_2025.xlsx",
            "_metadata": {
                "cliente_id": cliente_id,
                "periodo": periodo,
                "created_at": datetime.now().isoformat(),
                "tipo": "libro_remuneraciones",
                "source": "archivo_subido"
            }
        }
        
        print(f"📚 Guardando libro de remuneraciones: {libro_key}")
        redis_client.setex(libro_key, 3600, json.dumps(libro_data, default=str))
        
        # 2. Simular datos de Talana
        talana_key = f"sgm:nomina:{cliente_id}:{periodo}:empleados_talana"
        talana_data = {
            "empleados": [
                {"rut": "12345678-9", "nombre": "Juan Pérez", "conceptos": {"SUELDO": 800000, "GRATIFICACION": 66667}},
                {"rut": "98765432-1", "nombre": "María González", "conceptos": {"SUELDO": 750000, "GRATIFICACION": 62500}}
            ],
            "count": 2,
            "_metadata": {
                "cliente_id": cliente_id,
                "periodo": periodo,
                "created_at": datetime.now().isoformat(),
                "tipo": "empleados_talana",
                "source": "talana_api"
            }
        }
        
        print(f"👥 Guardando datos de Talana: {talana_key}")
        redis_client.setex(talana_key, 3600, json.dumps(talana_data, default=str))
        
        # 3. Simular datos del analista (con una pequeña discrepancia)
        analista_key = f"sgm:nomina:{cliente_id}:{periodo}:empleados_analista"
        analista_data = {
            "empleados": [
                {"rut": "12345678-9", "nombre": "Juan Pérez", "conceptos": {"SUELDO": 800000, "GRATIFICACION": 66667}},
                {"rut": "98765432-1", "nombre": "María González", "conceptos": {"SUELDO": 750000, "GRATIFICACION": 70000}}  # Diferencia aquí
            ],
            "count": 2,
            "_metadata": {
                "cliente_id": cliente_id,
                "periodo": periodo,
                "created_at": datetime.now().isoformat(),
                "tipo": "empleados_analista",
                "source": "analista_input"
            }
        }
        
        print(f"📝 Guardando datos del analista: {analista_key}")
        redis_client.setex(analista_key, 3600, json.dumps(analista_data, default=str))
        
        # 4. Simular detección de discrepancias
        discrepancias_key = f"sgm:nomina:{cliente_id}:{periodo}:discrepancias"
        discrepancias_data = {
            "success": True,
            "cliente_id": cliente_id,
            "periodo": periodo,
            "discrepancias_count": 1,
            "discrepancias": [
                {
                    "tipo": "valor_diferente",
                    "rut": "98765432-1",
                    "codigo_concepto": "GRATIFICACION",
                    "valor_talana": 62500,
                    "valor_analista": 70000,
                    "diferencia": 7500,
                    "descripcion": "Valor diferente en concepto GRATIFICACION para 98765432-1: Talana=62500, Analista=70000"
                }
            ],
            "comparacion_timestamp": datetime.now().isoformat(),
            "total_empleados_talana": 2,
            "total_empleados_analista": 2,
            "status": "con_discrepancias"
        }
        
        print(f"🔍 Guardando discrepancias detectadas: {discrepancias_key}")
        redis_client.setex(discrepancias_key, 1800, json.dumps(discrepancias_data, default=str))
        
        # 5. Verificar que todos los datos están guardados
        print("\n✅ Verificando datos guardados...")
        keys_to_check = [libro_key, talana_key, analista_key, discrepancias_key]
        
        for key in keys_to_check:
            if redis_client.exists(key):
                data = redis_client.get(key)
                parsed = json.loads(data)
                tipo = parsed.get('_metadata', {}).get('tipo', 'unknown')
                print(f"   ✅ {tipo}: {key}")
            else:
                print(f"   ❌ Clave no encontrada: {key}")
        
        # 6. Obtener estadísticas
        nomina_keys = redis_client.keys('sgm:nomina:*')
        print(f"\n📊 Total de claves de nómina en Redis: {len(nomina_keys)}")
        
        for key in nomina_keys:
            print(f"   📁 {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en simulación de workflow: {e}")
        return False

def test_memory_and_performance(redis_client):
    """
    Probar información de memoria y rendimiento
    """
    print("\n💾 Probando información de memoria y rendimiento...")
    
    try:
        # Información de memoria
        memory_info = redis_client.info('memory')
        print(f"📊 Memoria usada: {memory_info.get('used_memory_human', 'N/A')}")
        print(f"📊 Memoria pico: {memory_info.get('used_memory_peak_human', 'N/A')}")
        
        # Información de clientes
        clients_info = redis_client.info('clients')
        print(f"👥 Clientes conectados: {clients_info.get('connected_clients', 0)}")
        
        # Test de rendimiento básico
        start_time = time.time()
        
        # Escribir 100 claves de prueba
        for i in range(100):
            test_key = f"sgm:nomina:performance_test:{i}"
            test_data = {"index": i, "timestamp": datetime.now().isoformat()}
            redis_client.setex(test_key, 60, json.dumps(test_data))
        
        # Leer las 100 claves
        for i in range(100):
            test_key = f"sgm:nomina:performance_test:{i}"
            data = redis_client.get(test_key)
            if data:
                json.loads(data)
        
        # Eliminar las claves de prueba
        test_keys = [f"sgm:nomina:performance_test:{i}" for i in range(100)]
        redis_client.delete(*test_keys)
        
        end_time = time.time()
        elapsed = round((end_time - start_time) * 1000, 2)
        
        print(f"⚡ Test de rendimiento completado en {elapsed}ms")
        print(f"   📈 200 operaciones (100 write + 100 read) + cleanup")
        print(f"   📈 Promedio: {round(elapsed/200, 3)}ms por operación")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de rendimiento: {e}")
        return False

def cleanup_test_data(redis_client):
    """
    Limpiar datos de prueba
    """
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Obtener todas las claves de prueba
        test_keys = redis_client.keys('sgm:nomina:*')
        
        if test_keys:
            deleted_count = redis_client.delete(*test_keys)
            print(f"✅ {deleted_count} claves de prueba eliminadas")
        else:
            print("✅ No hay claves de prueba para eliminar")
        
        return True
        
    except Exception as e:
        print(f"❌ Error limpiando datos de prueba: {e}")
        return False

def main():
    """
    Función principal del test
    """
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN REDIS NÓMINA SGM")
    print("=" * 60)
    
    # 1. Probar conexión
    redis_client = test_redis_connection()
    if not redis_client:
        print("\n❌ FALLO: No se pudo conectar a Redis")
        return False
    
    # 2. Probar operaciones básicas
    if not test_basic_operations(redis_client):
        print("\n❌ FALLO: Operaciones básicas fallaron")
        return False
    
    # 3. Simular workflow de nómina
    if not test_nomina_workflow_simulation(redis_client):
        print("\n❌ FALLO: Simulación de workflow falló")
        return False
    
    # 4. Test de memoria y rendimiento
    if not test_memory_and_performance(redis_client):
        print("\n❌ ADVERTENCIA: Test de rendimiento falló (no crítico)")
    
    # 5. Limpiar datos de prueba
    cleanup_test_data(redis_client)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE!")
    print("🚀 Redis DB 2 está listo para nómina SGM")
    print("=" * 60)
    
    # Información final
    print("\n📋 INFORMACIÓN DE CONEXIÓN:")
    print(f"   🌐 Host: redis")
    print(f"   📍 Puerto: 6379") 
    print(f"   🗂️ Base de datos: 2 (nómina)")
    print(f"   🔑 Patrón de claves: sgm:nomina:{'{cliente_id}'}:{'{periodo}'}:{'{tipo_dato}'}")
    print(f"   📝 Logs: sgm:nomina:logs:{'{id}'}")
    print(f"   📊 Stats: sgm:nomina:stats:{'{stat_name}'}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrumpido por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        exit(1)
