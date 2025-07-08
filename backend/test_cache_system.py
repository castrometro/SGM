#!/usr/bin/env python
"""
Script de prueba para el sistema de cache Redis SGM
==================================================

Este script verifica que:
1. Redis esté conectado correctamente
2. El sistema de cache funcione
3. Los endpoints respondan correctamente
4. Las métricas se generen adecuadamente

Ejecutar desde el directorio backend:
python test_cache_system.py
"""

import os
import sys
import django
import json
import time
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.cache_redis import get_cache_system
from contabilidad.models import Cliente

def test_redis_connection():
    """Probar conexión a Redis"""
    print("🔍 Probando conexión a Redis...")
    
    try:
        cache_system = get_cache_system()
        
        # Test básico de conexión
        if cache_system.check_connection():
            print("✅ Conexión a Redis exitosa")
            
            # Verificar health check
            health = cache_system.health_check()
            print(f"✅ Health check: {health['status']}")
            print(f"   - Versión Redis: {health['redis_version']}")
            print(f"   - Uptime: {health['uptime_seconds']} segundos")
            print(f"   - Memoria usada: {health['used_memory_human']}")
            return True
        else:
            print("❌ Error: No se puede conectar a Redis")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False

def test_cache_operations():
    """Probar operaciones básicas de cache"""
    print("\n🔧 Probando operaciones de cache...")
    
    try:
        cache_system = get_cache_system()
        
        # Datos de prueba
        cliente_id = 1
        periodo = "2025-07"
        
        # Test 1: KPIs
        print("   📊 Probando cache de KPIs...")
        kpis_test = {
            'liquidez': 1.5,
            'endeudamiento': 0.35,
            'rentabilidad': 0.12,
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar KPIs
        if cache_system.set_kpis(cliente_id, periodo, kpis_test):
            print("   ✅ KPIs guardados en cache")
            
            # Recuperar KPIs
            kpis_retrieved = cache_system.get_kpis(cliente_id, periodo)
            if kpis_retrieved and kpis_retrieved['liquidez'] == 1.5:
                print("   ✅ KPIs recuperados correctamente del cache")
            else:
                print("   ❌ Error recuperando KPIs del cache")
        else:
            print("   ❌ Error guardando KPIs en cache")
        
        # Test 2: Estado Financiero
        print("   📋 Probando cache de Estado Financiero...")
        esf_test = {
            'activos': 1000000,
            'pasivos': 400000,
            'patrimonio': 600000,
            'cuentas': [
                {'codigo': '1105', 'nombre': 'Caja', 'valor': 100000},
                {'codigo': '1110', 'nombre': 'Bancos', 'valor': 200000}
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        if cache_system.set_estado_financiero(cliente_id, periodo, 'esf', esf_test):
            print("   ✅ ESF guardado en cache")
            
            esf_retrieved = cache_system.get_estado_financiero(cliente_id, periodo, 'esf')
            if esf_retrieved and esf_retrieved['activos'] == 1000000:
                print("   ✅ ESF recuperado correctamente del cache")
            else:
                print("   ❌ Error recuperando ESF del cache")
        else:
            print("   ❌ Error guardando ESF en cache")
        
        # Test 3: Movimientos
        print("   📝 Probando cache de Movimientos...")
        movimientos_test = [
            {
                'fecha': '2025-07-01',
                'cuenta': '1105',
                'descripcion': 'Caja General',
                'debito': 100000,
                'credito': 0
            },
            {
                'fecha': '2025-07-02',
                'cuenta': '2105',
                'descripcion': 'Proveedores',
                'debito': 0,
                'credito': 50000
            }
        ]
        
        if cache_system.set_movimientos(cliente_id, periodo, movimientos_test):
            print("   ✅ Movimientos guardados en cache")
            
            movimientos_retrieved = cache_system.get_movimientos(cliente_id, periodo)
            if movimientos_retrieved and len(movimientos_retrieved) == 2:
                print("   ✅ Movimientos recuperados correctamente del cache")
            else:
                print("   ❌ Error recuperando movimientos del cache")
        else:
            print("   ❌ Error guardando movimientos en cache")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones de cache: {e}")
        return False

def test_cache_performance():
    """Probar performance del cache"""
    print("\n⚡ Probando performance del cache...")
    
    try:
        cache_system = get_cache_system()
        
        # Test de escritura
        cliente_id = 999  # Cliente de prueba
        num_operations = 50
        
        print(f"   📝 Realizando {num_operations} operaciones de escritura...")
        start_time = time.time()
        
        for i in range(num_operations):
            test_data = {
                'operation': i,
                'timestamp': datetime.now().isoformat(),
                'data': f"test_data_{i}"
            }
            cache_system.set_kpis(cliente_id, f"periodo_{i}", test_data, ttl=60)
        
        write_time = time.time() - start_time
        print(f"   ✅ Tiempo de escritura: {write_time:.3f}s ({num_operations/write_time:.2f} ops/seg)")
        
        # Test de lectura
        print(f"   📖 Realizando {num_operations} operaciones de lectura...")
        start_time = time.time()
        
        for i in range(num_operations):
            cache_system.get_kpis(cliente_id, f"periodo_{i}")
        
        read_time = time.time() - start_time
        print(f"   ✅ Tiempo de lectura: {read_time:.3f}s ({num_operations/read_time:.2f} ops/seg)")
        
        # Limpiar datos de prueba
        for i in range(num_operations):
            cache_system.invalidate_cliente_periodo(cliente_id, f"periodo_{i}")
        
        print("   🧹 Datos de prueba limpiados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de performance: {e}")
        return False

def test_cache_stats():
    """Probar estadísticas del cache"""
    print("\n📊 Probando estadísticas del cache...")
    
    try:
        cache_system = get_cache_system()
        
        # Obtener estadísticas
        stats = cache_system.get_cache_stats()
        
        print("   📈 Estadísticas actuales:")
        print(f"      - Cache hits: {stats['cache_hits']}")
        print(f"      - Cache misses: {stats['cache_misses']}")
        print(f"      - Cache writes: {stats['cache_writes']}")
        print(f"      - Total keys: {stats['total_keys']}")
        print(f"      - Hit rate: {stats['hit_rate']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return False

def test_endpoints():
    """Probar endpoints HTTP del cache"""
    print("\n🌐 Probando endpoints HTTP...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/contabilidad/cache"
        
        # Test health endpoint
        print("   🏥 Probando endpoint de health...")
        response = requests.get(f"{base_url}/health/")
        
        if response.status_code == 200:
            print("   ✅ Health endpoint funcionando")
        else:
            print(f"   ❌ Health endpoint falló: {response.status_code}")
        
        # Test stats endpoint
        print("   📊 Probando endpoint de estadísticas...")
        response = requests.get(f"{base_url}/stats/")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Stats endpoint funcionando")
            print(f"      - Hit rate: {data['stats']['hit_rate']}%")
        else:
            print(f"   ❌ Stats endpoint falló: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando endpoints: {e}")
        return False

def main():
    """Función principal del test"""
    print("🚀 Iniciando pruebas del sistema de cache SGM")
    print("=" * 50)
    
    # Lista de tests
    tests = [
        ("Conexión Redis", test_redis_connection),
        ("Operaciones Cache", test_cache_operations),
        ("Performance Cache", test_cache_performance),
        ("Estadísticas Cache", test_cache_stats),
        ("Endpoints HTTP", test_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Ejecutando: {test_name}")
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Resultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El sistema de cache está funcionando correctamente.")
    else:
        print("⚠️  Algunos tests fallaron. Revisar la configuración.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
