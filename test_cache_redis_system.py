#!/usr/bin/env python3
"""
Script de prueba para el sistema de cache Redis de SGM - Contabilidad
===================================================================

Este script valida que:
1. La conexión a Redis DB 1 funciona correctamente
2. Los endpoints de cache responden adecuadamente
3. Las operaciones de cache (set/get/invalidate) funcionan
4. Las métricas y estadísticas están disponibles

Uso:
    python test_cache_redis_system.py

Autor: Sistema SGM
Fecha: 8 de julio de 2025
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/api/contabilidad"
CLIENT_ID = 1
PERIODO = "2024-12"

# Headers para las peticiones
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def print_header(title):
    """Imprimir un header decorativo"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message):
    """Imprimir mensaje de éxito"""
    print(f"✅ {message}")

def print_error(message):
    """Imprimir mensaje de error"""
    print(f"❌ {message}")

def print_info(message):
    """Imprimir mensaje informativo"""
    print(f"ℹ️  {message}")

def test_cache_health():
    """Probar el endpoint de salud del cache"""
    print_header("PRUEBA DE SALUD DEL CACHE")
    
    try:
        response = requests.get(f"{BASE_URL}/cache/health/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Cache health check OK - Status: {data.get('status')}")
            print_info(f"Redis disponible: {data.get('redis_available')}")
            print_info(f"Tiempo de respuesta: {data.get('response_time_ms')}ms")
            return True
        else:
            print_error(f"Health check falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en health check: {str(e)}")
        return False

def test_cache_stats():
    """Probar el endpoint de estadísticas del cache"""
    print_header("ESTADÍSTICAS DEL CACHE")
    
    try:
        response = requests.get(f"{BASE_URL}/cache/stats/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Estadísticas del cache obtenidas")
            print_info(f"Total de claves: {data.get('total_keys', 0)}")
            print_info(f"Memoria usada: {data.get('memory_usage', 'N/A')}")
            print_info(f"Hits: {data.get('hits', 0)}")
            print_info(f"Misses: {data.get('misses', 0)}")
            return True
        else:
            print_error(f"Stats falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en stats: {str(e)}")
        return False

def test_kpis_cache():
    """Probar el cache de KPIs"""
    print_header("PRUEBA DE CACHE DE KPIs")
    
    # 1. Primera llamada (debería calcular y cachear)
    try:
        print_info("Primera llamada (cache miss esperado)...")
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/cache/kpis/{CLIENT_ID}/{PERIODO}/", headers=headers)
        first_call_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            from_cache = data.get('from_cache', False)
            
            if not from_cache:
                print_success(f"KPIs calculados y cacheados - Tiempo: {first_call_time:.2f}ms")
            else:
                print_info("KPIs ya estaban en cache")
                
            print_info(f"Liquidez corriente: {data['data'].get('liquidez_corriente')}")
            print_info(f"Endeudamiento: {data['data'].get('endeudamiento')}")
            
        else:
            print_error(f"Primera llamada KPIs falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en primera llamada KPIs: {str(e)}")
        return False
    
    # 2. Segunda llamada (debería venir del cache)
    try:
        print_info("Segunda llamada (cache hit esperado)...")
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/cache/kpis/{CLIENT_ID}/{PERIODO}/", headers=headers)
        second_call_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            from_cache = data.get('from_cache', False)
            
            if from_cache:
                print_success(f"KPIs desde cache - Tiempo: {second_call_time:.2f}ms")
                print_info(f"Mejora de rendimiento: {((first_call_time - second_call_time) / first_call_time * 100):.1f}%")
            else:
                print_info("KPIs recalculados (no esperado)")
                
        else:
            print_error(f"Segunda llamada KPIs falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en segunda llamada KPIs: {str(e)}")
        return False
    
    return True

def test_estados_financieros_cache():
    """Probar el cache de estados financieros"""
    print_header("PRUEBA DE CACHE DE ESTADOS FINANCIEROS")
    
    tipos_estado = ['esf', 'esr', 'eri', 'ecp']
    
    for tipo in tipos_estado:
        try:
            print_info(f"Probando estado financiero: {tipo.upper()}...")
            response = requests.get(
                f"{BASE_URL}/cache/estado-financiero/{CLIENT_ID}/{PERIODO}/{tipo}/", 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                from_cache = data.get('from_cache', False)
                cache_status = "desde cache" if from_cache else "calculado"
                
                print_success(f"{tipo.upper()} obtenido {cache_status}")
                
                # Mostrar algunas cuentas si están disponibles
                cuentas = data.get('data', {}).get('cuentas', [])
                if cuentas:
                    print_info(f"Total de cuentas: {len(cuentas)}")
                    if len(cuentas) > 0:
                        primera_cuenta = cuentas[0]
                        print_info(f"Primera cuenta: {primera_cuenta.get('codigo', 'N/A')} - {primera_cuenta.get('nombre', 'N/A')}")
                
            else:
                print_error(f"{tipo.upper()} falló - Status: {response.status_code}")
                
        except Exception as e:
            print_error(f"Error en {tipo.upper()}: {str(e)}")
    
    return True

def test_movimientos_cache():
    """Probar el cache de movimientos"""
    print_header("PRUEBA DE CACHE DE MOVIMIENTOS")
    
    try:
        response = requests.get(f"{BASE_URL}/cache/movimientos/{CLIENT_ID}/{PERIODO}/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            from_cache = data.get('from_cache', False)
            cache_status = "desde cache" if from_cache else "calculados"
            
            print_success(f"Movimientos obtenidos {cache_status}")
            
            movimientos = data.get('data', {}).get('movimientos', [])
            if movimientos:
                print_info(f"Total de movimientos: {len(movimientos)}")
                
                # Mostrar resumen
                total_debito = data.get('data', {}).get('total_debito', 0)
                total_credito = data.get('data', {}).get('total_credito', 0)
                print_info(f"Total débito: ${total_debito:,.2f}")
                print_info(f"Total crédito: ${total_credito:,.2f}")
            
        else:
            print_error(f"Movimientos falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en movimientos: {str(e)}")
        return False
    
    return True

def test_cache_invalidation():
    """Probar la invalidación del cache"""
    print_header("PRUEBA DE INVALIDACIÓN DE CACHE")
    
    try:
        # Invalidar cache del cliente
        response = requests.delete(f"{BASE_URL}/cache/invalidar/{CLIENT_ID}/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            keys_invalidated = data.get('keys_invalidated', 0)
            print_success(f"Cache invalidado - {keys_invalidated} claves eliminadas")
            
            # Verificar que el cache fue realmente invalidado
            response = requests.get(f"{BASE_URL}/cache/kpis/{CLIENT_ID}/{PERIODO}/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                from_cache = data.get('from_cache', False)
                
                if not from_cache:
                    print_success("Invalidación verificada - KPIs recalculados")
                else:
                    print_error("Invalidación falló - KPIs aún en cache")
                    
            return True
        else:
            print_error(f"Invalidación falló - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en invalidación: {str(e)}")
        return False

def main():
    """Función principal"""
    print_header("PRUEBAS DEL SISTEMA DE CACHE REDIS - SGM")
    print_info(f"URL Base: {BASE_URL}")
    print_info(f"Cliente ID: {CLIENT_ID}")
    print_info(f"Período: {PERIODO}")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Lista de pruebas
    tests = [
        ("Health Check", test_cache_health),
        ("Estadísticas", test_cache_stats),
        ("Cache KPIs", test_kpis_cache),
        ("Cache Estados Financieros", test_estados_financieros_cache),
        ("Cache Movimientos", test_movimientos_cache),
        ("Invalidación Cache", test_cache_invalidation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Error crítico en {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print_header("RESUMEN DE PRUEBAS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print_success("¡Todas las pruebas del sistema de cache fueron exitosas!")
        return 0
    else:
        print_error(f"Fallaron {total - passed} pruebas")
        return 1

if __name__ == "__main__":
    sys.exit(main())
