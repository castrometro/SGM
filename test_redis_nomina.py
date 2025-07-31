#!/usr/bin/env python3
"""
Script de prueba para el sistema de cache Redis de nómina
=========================================================

Prueba la funcionalidad completa:
1. Conexión a Redis DB 2
2. Envío de informes a Redis
3. Recuperación desde Redis
4. Estadísticas del cache

Uso:
    python test_redis_nomina.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from nomina.models_informe import InformeNomina
from nomina.cache_redis import get_cache_system_nomina
from nomina.models import CierreNomina
import json
from datetime import datetime

def test_redis_connection():
    """Probar conexión básica a Redis"""
    print("🔍 Probando conexión a Redis DB 2...")
    
    try:
        cache_system = get_cache_system_nomina()
        health = cache_system.health_check()
        
        print(f"✅ Conexión: {health['status']}")
        print(f"📊 Redis conectado: {health['redis_connected']}")
        if 'redis_version' in health:
            print(f"🐧 Versión Redis: {health['redis_version']}")
            print(f"💾 Memoria usada: {health['used_memory']}")
        
        return health['redis_connected']
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_envio_informe():
    """Probar envío de informe a Redis"""
    print("\n🚀 Probando envío de informe a Redis...")
    
    try:
        # Buscar el último informe generado
        informe = InformeNomina.objects.select_related('cierre', 'cierre__cliente').first()
        
        if not informe:
            print("❌ No hay informes disponibles para probar")
            return False
        
        print(f"📋 Informe encontrado: {informe.cierre.cliente.nombre} - {informe.cierre.periodo}")
        
        # Enviar a Redis
        resultado = informe.enviar_a_redis(ttl_hours=1)  # TTL corto para pruebas
        
        if resultado['success']:
            print(f"✅ Enviado exitosamente a Redis")
            print(f"🔑 Clave: {resultado['clave_redis']}")
            print(f"📏 Tamaño: {resultado['size_kb']:.1f} KB")
            print(f"⏰ TTL: {resultado['ttl_hours']} horas")
            return True
        else:
            print(f"❌ Error: {resultado['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_recuperacion_redis():
    """Probar recuperación desde Redis"""
    print("\n📥 Probando recuperación desde Redis...")
    
    try:
        # Usar el primer cierre disponible
        cierre = CierreNomina.objects.select_related('cliente').first()
        
        if not cierre:
            print("❌ No hay cierres disponibles")
            return False
        
        print(f"🔍 Buscando en Redis: cliente={cierre.cliente.id}, periodo={cierre.periodo}")
        
        # Recuperar desde Redis
        datos_redis = InformeNomina.obtener_desde_redis(
            cierre.cliente.id, 
            cierre.periodo
        )
        
        if datos_redis:
            print("✅ Datos encontrados en Redis")
            print(f"📊 Cliente: {datos_redis.get('cliente_nombre', 'N/A')}")
            print(f"📅 Período: {datos_redis.get('periodo', 'N/A')}")
            print(f"👥 Dotación: {datos_redis.get('kpis_principales', {}).get('dotacion_total', 'N/A')}")
            print(f"💰 Costo empresa: ${datos_redis.get('kpis_principales', {}).get('costo_empresa_total', 0):,.0f}")
            
            cached_at = datos_redis.get('_metadata', {}).get('cached_at', 'N/A')
            print(f"⏰ Cacheado el: {cached_at[:19] if cached_at != 'N/A' else 'N/A'}")
            
            return True
        else:
            print("❌ No se encontraron datos en Redis para este cliente/período")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_estadisticas_cache():
    """Probar estadísticas del cache"""
    print("\n📈 Probando estadísticas del cache...")
    
    try:
        cache_system = get_cache_system_nomina()
        stats = cache_system.get_cache_stats()
        
        print("📊 Estadísticas de Redis:")
        print(f"  🔑 Total de claves: {stats.get('total_keys', 0)}")
        print(f"  💾 Memoria usada: {stats.get('redis_info', {}).get('used_memory', 'N/A')}")
        print(f"  👥 Clientes conectados: {stats.get('redis_info', {}).get('connected_clients', 0)}")
        
        print("\n📊 Contadores de nómina:")
        counters = stats.get('nomina_counters', {})
        for key, value in counters.items():
            print(f"  📈 {key}: {value}")
        
        print("\n👤 Claves por cliente:")
        clients = stats.get('keys_by_client', {})
        for cliente_id, count in clients.items():
            print(f"  👤 Cliente {cliente_id}: {count} claves")
        
        return True
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return False

def test_operaciones_cache():
    """Probar operaciones específicas del cache"""
    print("\n🛠️ Probando operaciones del cache...")
    
    try:
        cache_system = get_cache_system_nomina()
        
        # Datos de prueba
        cliente_id = 999
        periodo = "2025-07"
        
        print(f"📝 Enviando datos de prueba: cliente={cliente_id}, periodo={periodo}")
        
        # Datos de prueba para KPIs
        kpis_test = {
            'dotacion_total': 100,
            'costo_empresa_total': 50000000,
            'rotacion_porcentaje': 5.2,
            'ausentismo_porcentaje': 8.1
        }
        
        # Enviar KPIs
        success_kpis = cache_system.set_kpis_nomina(cliente_id, periodo, kpis_test, ttl=300)
        print(f"  📊 KPIs enviados: {'✅' if success_kpis else '❌'}")
        
        # Recuperar KPIs
        kpis_recuperados = cache_system.get_kpis_nomina(cliente_id, periodo)
        if kpis_recuperados:
            print(f"  📊 KPIs recuperados: ✅")
            print(f"    👥 Dotación: {kpis_recuperados.get('dotacion_total', 'N/A')}")
        else:
            print(f"  📊 KPIs recuperados: ❌")
        
        # Limpiar datos de prueba
        deleted = cache_system.invalidate_cliente_periodo(cliente_id, periodo)
        print(f"  🗑️ Datos de prueba eliminados: {deleted} claves")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 PRUEBAS SISTEMA CACHE REDIS NÓMINA")
    print("=" * 60)
    
    # Ejecutar todas las pruebas
    tests = [
        ("Conexión Redis", test_redis_connection),
        ("Envío informe", test_envio_informe),
        ("Recuperación Redis", test_recuperacion_redis),
        ("Estadísticas cache", test_estadisticas_cache),
        ("Operaciones cache", test_operaciones_cache)
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error crítico en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    exitosas = 0
    for nombre, resultado in resultados:
        status = "✅ EXITOSA" if resultado else "❌ FALLIDA"
        print(f"{status:12} | {nombre}")
        if resultado:
            exitosas += 1
    
    print(f"\n🎯 Total: {exitosas}/{len(resultados)} pruebas exitosas")
    
    if exitosas == len(resultados):
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema está listo.")
    elif exitosas > 0:
        print("⚠️ Algunas pruebas fallaron. Revisar configuración.")
    else:
        print("💥 TODAS LAS PRUEBAS FALLARON. Verificar conexión Redis.")

if __name__ == "__main__":
    main()
