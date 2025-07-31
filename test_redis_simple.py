#!/usr/bin/env python3
"""
Prueba rápida del sistema Redis de nómina
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def test_redis_nomina():
    """Prueba básica del sistema Redis"""
    try:
        print("🔍 Probando conexión a Redis DB 2...")
        
        from nomina.cache_redis import get_cache_system_nomina
        cache_system = get_cache_system_nomina()
        
        # Health check
        health = cache_system.health_check()
        print(f"✅ Estado: {health['status']}")
        print(f"📊 Redis conectado: {health['redis_connected']}")
        
        if health['redis_connected']:
            print(f"🐧 Versión Redis: {health.get('redis_version', 'N/A')}")
            print(f"💾 Memoria usada: {health.get('used_memory', 'N/A')}")
            
            # Buscar informe existente
            print("\n📋 Buscando informes existentes...")
            from nomina.models_informe import InformeNomina
            informe = InformeNomina.objects.first()
            
            if informe:
                print(f"📊 Informe encontrado: {informe.cierre.cliente.nombre} - {informe.cierre.periodo}")
                
                # Probar envío a Redis
                print("🚀 Probando envío a Redis...")
                resultado = informe.enviar_a_redis(ttl_hours=1)
                
                if resultado['success']:
                    print(f"✅ Enviado exitosamente!")
                    print(f"🔑 Clave: {resultado['clave_redis']}")
                    print(f"📏 Tamaño: {resultado['size_kb']:.1f} KB")
                    
                    # Probar recuperación
                    print("\n📥 Probando recuperación desde Redis...")
                    datos_redis = InformeNomina.obtener_desde_redis(
                        informe.cierre.cliente.id, 
                        informe.cierre.periodo
                    )
                    
                    if datos_redis:
                        print("✅ Datos recuperados exitosamente!")
                        print(f"👥 Dotación: {datos_redis.get('kpis_principales', {}).get('dotacion_total', 'N/A')}")
                        print(f"💰 Costo empresa: ${datos_redis.get('kpis_principales', {}).get('costo_empresa_total', 0):,.0f}")
                    else:
                        print("❌ No se pudieron recuperar datos")
                        
                else:
                    print(f"❌ Error enviando: {resultado['error']}")
            else:
                print("❌ No hay informes disponibles para probar")
        else:
            print("❌ No se pudo conectar a Redis")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_redis_nomina()
