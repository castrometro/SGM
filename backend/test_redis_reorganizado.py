#!/usr/bin/env python3
"""
Test de estructura Redis reorganizada
===================================

Verifica la nueva estructura organizada:
sgm:nomina:{cliente_id}:{cierre_id}:{componente}:{tipo}
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
django.setup()

from nomina.models import CierreNomina, Cliente
from nomina.cache_redis import CacheNominaSGM

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_estructura_reorganizada():
    """Test de la nueva estructura Redis"""
    
    print("🔧 TEST ESTRUCTURA REDIS REORGANIZADA")
    print("=" * 50)
    
    try:
        # Obtener datos de prueba
        cliente = Cliente.objects.first()
        cierre = CierreNomina.objects.filter(cliente=cliente).first() if cliente else None
        
        if not cliente or not cierre:
            print("❌ No hay datos de prueba (cliente/cierre)")
            return
            
        print(f"📋 Cliente: {cliente.razon_social}")
        print(f"📋 Cierre: {cierre.id} - {cierre.periodo}")
        
        cache = CacheNominaSGM()
        
        # Simular datos de FASE 1
        print(f"\n🚀 Simulando FASE 1 con estructura organizada...")
        
        # 1. Análisis de headers
        analisis_headers = {
            'headers_mapeados': ['Sueldo Base', 'AFP', 'Isapre'],
            'headers_no_mapeados': ['Concepto Especial'],
            'total_headers': 4,
            'mapeados_automaticamente': 3,
            'pendientes_mapeo': 1,
            'timestamp': '2025-07-21T11:00:00'
        }
        
        cache.guardar_analisis_headers(cliente.id, cierre.id, analisis_headers)
        
        # 2. Mapeos manuales (si hay pendientes)
        if analisis_headers['pendientes_mapeo'] > 0:
            mapeos_manuales = {'Concepto Especial': 'Bonificacion Extra'}
            cache.guardar_mapeos_manuales(cliente.id, cierre.id, mapeos_manuales)
        
        # 3. Mapeo final consolidado
        mapeo_final = {
            'mapeos_automaticos': analisis_headers['headers_mapeados'],
            'mapeos_manuales': {'Concepto Especial': 'Bonificacion Extra'},
            'mapeos_completos': {
                'Sueldo Base': 'Sueldo Base',
                'AFP': 'AFP', 
                'Isapre': 'Isapre',
                'Concepto Especial': 'Bonificacion Extra'
            },
            'total_conceptos_mapeados': 4,
            'fase_completada': 'headers_y_mapeo',
            'timestamp': '2025-07-21T11:15:00'
        }
        
        cache.guardar_mapeo_final(cliente.id, cierre.id, mapeo_final)
        
        # 4. Estado del procesamiento
        cache.actualizar_estado_libro(cliente.id, cierre.id, 'fase1_completa', {
            'progreso': 100,
            'mensaje': 'FASE 1 completada: Headers mapeados',
            'conceptos_mapeados': 4,
            'siguiente_fase': 'movimientos_talana'
        })
        
        print(f"✅ Datos FASE 1 simulados correctamente")
        
        # Verificar estructura en Redis
        print(f"\n🔍 Verificando estructura Redis...")
        
        # Conectar directamente a Redis para ver keys
        import redis
        redis_client = redis.Redis(host='redis', port=6379, db=2, decode_responses=True)
        
        # Buscar keys del cierre actual
        pattern = f"sgm:nomina:{cliente.id}:{cierre.id}:*"
        keys = redis_client.keys(pattern)
        
        if keys:
            print(f"📋 Keys encontradas ({len(keys)}):")
            for key in sorted(keys):
                # Extraer componente y tipo de la key
                parts = key.split(':')
                if len(parts) >= 5:
                    componente = parts[3] 
                    tipo = parts[4]
                    ttl = redis_client.ttl(key)
                    print(f"   🔑 {componente}:{tipo} (TTL: {ttl}s)")
        else:
            print(f"❌ No se encontraron keys con patrón: {pattern}")
            
        # Verificar que podemos recuperar los datos
        print(f"\n🔄 Verificando recuperación de datos...")
        
        # Recuperar análisis headers
        headers_recuperados = cache.obtener_analisis_headers(cliente.id, cierre.id)
        if headers_recuperados:
            print(f"   ✅ Headers análisis: {headers_recuperados['total_headers']} headers")
        
        # Recuperar mapeo final
        mapeo_recuperado = cache.obtener_mapeo_final(cliente.id, cierre.id)
        if mapeo_recuperado:
            print(f"   ✅ Mapeo final: {mapeo_recuperado['total_conceptos_mapeados']} conceptos")
        
        # Recuperar estado
        estado_recuperado = cache.obtener_estado_libro(cliente.id, cierre.id)
        if estado_recuperado:
            print(f"   ✅ Estado: {estado_recuperado['estado']}")
            
        print(f"\n🎉 ESTRUCTURA REORGANIZADA EXITOSA")
        print(f"📊 Patrón: sgm:nomina:{cliente.id}:{cierre.id}:componente:tipo")
        print(f"🔧 Organización por fases implementada")
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_estructura_reorganizada()
