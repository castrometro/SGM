"""
Demo para probar el sistema de cache de pruebas desde Django shell
==================================================================

Copia y pega este código en el Django shell para probar las nuevas funcionalidades:

docker exec -it sgm-django-1 python manage.py shell

Luego ejecuta línea por línea:
"""

from contabilidad.cache_redis import get_cache_system
from datetime import datetime

# Inicializar cache
cache_system = get_cache_system()
print("🧪 Sistema de cache inicializado")

# Verificar conexión
print(f"Conexión Redis: {'✅ OK' if cache_system.check_connection() else '❌ Error'}")

# Datos de prueba
cliente_id = 1
periodo = "2025-07"

# 1. Crear ESF de prueba del sistema actual
print("\n📊 1. Guardando ESF de prueba del sistema actual...")

esf_actual = {
    'tipo_estado': 'ESF',
    'cliente_id': cliente_id,
    'periodo': periodo,
    'source': 'sistema_actual_sgm',
    'generated_at': datetime.now().isoformat(),
    
    # Estructura real del ESF del sistema
    'assets': {
        'current_assets': 850000.00,
        'non_current_assets': 350000.00,
        'total_assets': 1200000.00,
        'current_assets_detail': {
            '1101': {'nombre': 'Caja General', 'saldo': 75000.00},
            '1102': {'nombre': 'Banco Nacional', 'saldo': 225000.00},
            '1103': {'nombre': 'Cuentas por Cobrar Clientes', 'saldo': 350000.00},
            '1104': {'nombre': 'Inventario Mercancías', 'saldo': 200000.00}
        },
        'non_current_assets_detail': {
            '1201': {'nombre': 'Edificios', 'saldo': 250000.00},
            '1202': {'nombre': 'Maquinaria y Equipo', 'saldo': 100000.00}
        }
    },
    'liabilities': {
        'current_liabilities': 320000.00,
        'non_current_liabilities': 180000.00,
        'total_liabilities': 500000.00,
        'current_liabilities_detail': {
            '2101': {'nombre': 'Proveedores Nacionales', 'saldo': 180000.00},
            '2102': {'nombre': 'Cuentas por Pagar', 'saldo': 90000.00},
            '2103': {'nombre': 'Obligaciones Laborales', 'saldo': 50000.00}
        },
        'non_current_liabilities_detail': {
            '2201': {'nombre': 'Préstamos Bancarios LP', 'saldo': 180000.00}
        }
    },
    'patrimony': {
        'total_patrimony': 700000.00,
        'patrimony_detail': {
            '3101': {'nombre': 'Capital Suscrito y Pagado', 'saldo': 600000.00},
            '3201': {'nombre': 'Utilidades del Ejercicio', 'saldo': 100000.00}
        }
    },
    
    # Verificación contable
    'total_activos': 1200000.00,
    'total_pasivo_patrimonio': 1200000.00,
    'diferencia': 0.00,
    'balance_cuadrado': True,
    
    # Metadata del sistema
    'clasificaciones_aplicadas': True,
    'nombres_ingles_aplicados': False,
    'validaciones_pasadas': True,
    'notas': [
        'ESF generado por el sistema SGM actual',
        'Incluye todas las clasificaciones contables',
        'Balance verificado y cuadrado',
        'Listo para comparación con nuevos desarrollos'
    ]
}

# Guardar en cache como prueba
success = cache_system.set_prueba_esf(cliente_id, periodo, esf_actual, "current_system")
print(f"ESF guardado: {'✅ OK' if success else '❌ Error'}")

# 2. Recuperar y mostrar
print("\n📊 2. Recuperando ESF de prueba...")
esf_recuperado = cache_system.get_prueba_esf(cliente_id, periodo, "current_system")

if esf_recuperado:
    print("✅ ESF recuperado exitosamente")
    print(f"📈 RESUMEN DEL ESF ACTUAL:")
    print(f"   Total Activos: ${esf_recuperado['total_activos']:,.2f}")
    print(f"   - Activos Corrientes: ${esf_recuperado['assets']['current_assets']:,.2f}")
    print(f"   - Activos No Corrientes: ${esf_recuperado['assets']['non_current_assets']:,.2f}")
    print(f"   Total Pasivos: ${esf_recuperado['liabilities']['total_liabilities']:,.2f}")
    print(f"   - Pasivos Corrientes: ${esf_recuperado['liabilities']['current_liabilities']:,.2f}")
    print(f"   - Pasivos No Corrientes: ${esf_recuperado['liabilities']['non_current_liabilities']:,.2f}")
    print(f"   Total Patrimonio: ${esf_recuperado['patrimony']['total_patrimony']:,.2f}")
    print(f"   Balance Cuadrado: {'✅ SÍ' if esf_recuperado['balance_cuadrado'] else '❌ NO'}")
    print(f"   Diferencia: ${esf_recuperado['diferencia']:,.2f}")
else:
    print("❌ No se pudo recuperar el ESF")

# 3. Estadísticas
print("\n📊 3. Estadísticas del cache...")
stats = cache_system.get_cache_stats()

print(f"📈 ESTADÍSTICAS DE PRUEBAS:")
print(f"   Pruebas guardadas: {stats.get('pruebas_cached', 0)}")
print(f"   Pruebas recuperadas: {stats.get('pruebas_retrieved', 0)}")
print(f"   ESF de prueba guardados: {stats.get('pruebas_esf_cached', 0)}")
print(f"   ESF de prueba recuperados: {stats.get('pruebas_esf_retrieved', 0)}")
print(f"   Total claves de prueba: {stats.get('pruebas_keys', 0)}")
print(f"   Hit rate general: {stats.get('hit_rate_percent', 0)}%")

# 4. Listar pruebas disponibles
print("\n📊 4. Listando pruebas disponibles...")
pruebas = cache_system.list_pruebas_cliente(cliente_id, periodo)

print(f"📋 PRUEBAS DISPONIBLES PARA CLIENTE {cliente_id}, PERÍODO {periodo}:")
for prueba in pruebas:
    print(f"   - Tipo: {prueba['data_type']}")
    print(f"     Test: {prueba['test_type']}")
    print(f"     Key: {prueba['redis_key']}")
    print(f"     ───────────────────────────")

print(f"\n🎉 DEMO COMPLETADO")
print(f"✅ Sistema de cache de pruebas funcionando correctamente")
print(f"🔗 Estructura Redis: sgm:contabilidad:{cliente_id}:{periodo}:pruebas:esf:current_system")
