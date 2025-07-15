#!/usr/bin/env python3
"""
Script de prueba para el sistema de cache Redis - Sección Pruebas
==================================================================

Este script prueba las nuevas funcionalidades de cache para datos de prueba,
específicamente para almacenar ESF generados por el sistema actual.

Ejecutar desde el directorio raíz del proyecto:
python test_cache_pruebas.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.cache_redis import get_cache_system
from datetime import datetime
from decimal import Decimal

def test_cache_pruebas():
    """Probar el sistema de cache para datos de prueba"""
    
    print("🧪 INICIANDO PRUEBAS DEL SISTEMA DE CACHE - SECCIÓN PRUEBAS")
    print("=" * 70)
    
    # Inicializar sistema de cache
    cache_system = get_cache_system()
    
    # Verificar conexión
    if not cache_system.check_connection():
        print("❌ Error: No se pudo conectar a Redis")
        return False
    
    print("✅ Conexión a Redis exitosa")
    
    # Datos de prueba
    cliente_id = 1
    periodo = "2025-07"
    
    # 1. Probar guardado de ESF de prueba
    print(f"\n📊 1. PROBANDO GUARDADO DE ESF DE PRUEBA")
    print("-" * 50)
    
    esf_prueba = {
        'tipo_estado': 'ESF',
        'cliente_id': cliente_id,
        'periodo': periodo,
        'source': 'sistema_actual',
        'assets': {
            'current_assets': 750000.00,
            'non_current_assets': 250000.00,
            'total_assets': 1000000.00,
            'current_assets_detail': {
                '1101': {'nombre': 'Caja', 'saldo': 50000.00},
                '1102': {'nombre': 'Bancos', 'saldo': 200000.00},
                '1103': {'nombre': 'Cuentas por Cobrar', 'saldo': 300000.00},
                '1104': {'nombre': 'Inventarios', 'saldo': 200000.00}
            },
            'non_current_assets_detail': {
                '1201': {'nombre': 'Propiedad Planta y Equipo', 'saldo': 250000.00}
            }
        },
        'liabilities': {
            'current_liabilities': 300000.00,
            'non_current_liabilities': 100000.00,
            'total_liabilities': 400000.00,
            'current_liabilities_detail': {
                '2101': {'nombre': 'Proveedores', 'saldo': 150000.00},
                '2102': {'nombre': 'Cuentas por Pagar', 'saldo': 100000.00},
                '2103': {'nombre': 'Obligaciones Laborales', 'saldo': 50000.00}
            },
            'non_current_liabilities_detail': {
                '2201': {'nombre': 'Préstamos Largo Plazo', 'saldo': 100000.00}
            }
        },
        'patrimony': {
            'total_patrimony': 600000.00,
            'patrimony_detail': {
                '3101': {'nombre': 'Capital Social', 'saldo': 500000.00},
                '3201': {'nombre': 'Utilidades Retenidas', 'saldo': 100000.00}
            }
        },
        'total_activos': 1000000.00,
        'total_pasivo_patrimonio': 1000000.00,
        'diferencia': 0.00,
        'balance_cuadrado': True,
        'generated_at': datetime.now().isoformat()
    }
    
    # Guardar ESF de prueba
    success = cache_system.set_prueba_esf(cliente_id, periodo, esf_prueba, "current_system")
    print(f"   Guardar ESF de prueba: {'✅ OK' if success else '❌ Error'}")
    
    # 2. Probar recuperación de ESF de prueba
    print(f"\n📊 2. PROBANDO RECUPERACIÓN DE ESF DE PRUEBA")
    print("-" * 50)
    
    esf_recuperado = cache_system.get_prueba_esf(cliente_id, periodo, "current_system")
    print(f"   Recuperar ESF de prueba: {'✅ OK' if esf_recuperado else '❌ Error'}")
    
    if esf_recuperado:
        print(f"   Total Activos: ${esf_recuperado.get('total_activos', 0):,.2f}")
        print(f"   Total Pasivos: ${esf_recuperado.get('liabilities', {}).get('total_liabilities', 0):,.2f}")
        print(f"   Total Patrimonio: ${esf_recuperado.get('patrimony', {}).get('total_patrimony', 0):,.2f}")
        print(f"   Balance Cuadrado: {esf_recuperado.get('balance_cuadrado', False)}")
    
    # 3. Probar guardado de datos de prueba genéricos
    print(f"\n📊 3. PROBANDO DATOS DE PRUEBA GENÉRICOS")
    print("-" * 50)
    
    kpis_prueba = {
        'liquidez_corriente': 2.5,
        'endeudamiento': 0.4,
        'rentabilidad': 0.15,
        'margen_operacional': 0.3,
        'test_scenario': 'optimista',
        'generated_at': datetime.now().isoformat()
    }
    
    success_kpis = cache_system.set_prueba_data(cliente_id, periodo, "kpis", kpis_prueba, "scenario_test")
    print(f"   Guardar KPIs de prueba: {'✅ OK' if success_kpis else '❌ Error'}")
    
    kpis_recuperados = cache_system.get_prueba_data(cliente_id, periodo, "kpis", "scenario_test")
    print(f"   Recuperar KPIs de prueba: {'✅ OK' if kpis_recuperados else '❌ Error'}")
    
    if kpis_recuperados:
        print(f"   Liquidez Corriente: {kpis_recuperados.get('liquidez_corriente', 0)}")
        print(f"   Endeudamiento: {kpis_recuperados.get('endeudamiento', 0)}")
        print(f"   Escenario: {kpis_recuperados.get('test_scenario', 'N/A')}")
    
    # 4. Probar listado de pruebas
    print(f"\n📊 4. PROBANDO LISTADO DE PRUEBAS")
    print("-" * 50)
    
    lista_pruebas = cache_system.list_pruebas_cliente(cliente_id, periodo)
    print(f"   Listar pruebas: {'✅ OK' if isinstance(lista_pruebas, list) else '❌ Error'}")
    print(f"   Total pruebas encontradas: {len(lista_pruebas)}")
    
    for prueba in lista_pruebas:
        print(f"   - {prueba.get('data_type', 'N/A')}:{prueba.get('test_type', 'N/A')} (Cliente {prueba.get('cliente_id', 'N/A')}, Período {prueba.get('periodo', 'N/A')})")
    
    # 5. Probar estadísticas actualizadas
    print(f"\n📊 5. PROBANDO ESTADÍSTICAS ACTUALIZADAS")
    print("-" * 50)
    
    stats = cache_system.get_cache_stats()
    if stats and not stats.get('error'):
        print(f"   Pruebas en cache: {stats.get('pruebas_cached', 0)}")
        print(f"   Pruebas recuperadas: {stats.get('pruebas_retrieved', 0)}")
        print(f"   Claves de prueba ESF: {stats.get('pruebas_esf_keys', 0)}")
        print(f"   Total claves de prueba: {stats.get('pruebas_keys', 0)}")
        print(f"   Hit rate: {stats.get('hit_rate_percent', 0)}%")
    else:
        print("   ❌ Error obteniendo estadísticas")
    
    # 6. Probar invalidación de pruebas
    print(f"\n📊 6. PROBANDO INVALIDACIÓN DE PRUEBAS")
    print("-" * 50)
    
    deleted_count = cache_system.invalidate_pruebas_cliente(cliente_id, periodo)
    print(f"   Claves de prueba eliminadas: {deleted_count}")
    
    # Verificar que se eliminaron
    esf_verificacion = cache_system.get_prueba_esf(cliente_id, periodo, "current_system")
    kpis_verificacion = cache_system.get_prueba_data(cliente_id, periodo, "kpis", "scenario_test")
    
    print(f"   Verificar eliminación ESF: {'✅ OK' if not esf_verificacion else '❌ Aún existe'}")
    print(f"   Verificar eliminación KPIs: {'✅ OK' if not kpis_verificacion else '❌ Aún existe'}")
    
    print(f"\n🎉 PRUEBAS COMPLETADAS")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        test_cache_pruebas()
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
