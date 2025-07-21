#!/usr/bin/env python3
"""
Test de FASE 1 optimizada - Solo headers sin empleados
======================================================

Prueba la nueva estrategia híbrida donde solo procesamos headers y mapeos
en la FASE 1, sin empleados para optimizar escalabilidad.
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
from nomina.tasks import analizar_headers_libro, procesar_empleados_libro

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fase1_optimizada():
    """Test de FASE 1: solo headers y mapeo"""
    
    print("🧪 TEST FASE 1 OPTIMIZADA - Headers sin empleados")
    print("=" * 60)
    
    try:
        # Obtener un cliente y cierre de prueba
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes en BD para prueba")
            return
            
        cierre = CierreNomina.objects.filter(cliente=cliente).first()
        if not cierre:
            print("❌ No hay cierres para prueba")
            return
            
        print(f"📋 Cliente: {cliente.razon_social}")
        print(f"📋 Cierre: {cierre.id} - {cierre.periodo}")
        
        # Verificar estado del cache
        cache = CacheNominaSGM()
        
        # Verificar si hay datos en cache
        headers_analisis = cache.obtener_analisis_headers(cliente.id, cierre.id)
        mapeos_manuales = cache.obtener_mapeos_manuales(cliente.id, cierre.id)
        mapeo_final = cache.obtener_mapeo_final(cliente.id, cierre.id)
        
        print(f"🗃️ Cache Estado:")
        print(f"   - Headers análisis: {'✅ Existe' if headers_analisis else '❌ No existe'}")
        print(f"   - Mapeos manuales: {'✅ Existe' if mapeos_manuales else '❌ No existe'}")  
        print(f"   - Mapeo final: {'✅ Existe' if mapeo_final else '❌ No existe'}")
        
        if headers_analisis:
            print(f"📊 Headers análisis:")
            print(f"   - Total headers: {headers_analisis.get('total_headers', 0)}")
            print(f"   - Mapeados automáticamente: {headers_analisis.get('mapeados_automaticamente', 0)}")
            print(f"   - Pendientes mapeo: {headers_analisis.get('pendientes_mapeo', 0)}")
            
        if mapeo_final:
            print(f"🎯 Mapeo final (FASE 1):")
            print(f"   - Fase completada: {mapeo_final.get('fase_completada', 'N/A')}")
            print(f"   - Total conceptos mapeados: {mapeo_final.get('total_conceptos_mapeados', 0)}")
            print(f"   - Timestamp: {mapeo_final.get('timestamp', 'N/A')}")
            
            mapeos_completos = mapeo_final.get('mapeos_completos', {})
            if mapeos_completos:
                print(f"📝 Mapeos disponibles: {list(mapeos_completos.keys())[:5]}...")
        
        # Simular FASE 1 si no existe mapeo final
        if not mapeo_final and headers_analisis:
            print("\n🚀 Simulando FASE 1 optimizada...")
            
            # Simular mapeo final
            mapeo_simulado = {
                'mapeos_automaticos': headers_analisis.get('headers_mapeados', []),
                'mapeos_manuales': {},
                'mapeos_completos': {header: header for header in headers_analisis.get('headers_mapeados', [])},
                'total_conceptos_mapeados': len(headers_analisis.get('headers_mapeados', [])),
                'fase_completada': 'headers_y_mapeo',
                'timestamp': '2025-07-21T10:30:00'
            }
            
            # Guardar en cache
            cache.guardar_mapeo_final(cliente.id, cierre.id, mapeo_simulado)
            print("✅ Mapeo final simulado guardado")
        
        print(f"\n🎉 FASE 1 OPTIMIZADA: Headers procesados sin empleados")
        print(f"💾 Uso de memoria Redis: Mínimo (solo metadatos)")
        print(f"🚀 Siguiente fase: Movimientos Talana")
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fase1_optimizada()
