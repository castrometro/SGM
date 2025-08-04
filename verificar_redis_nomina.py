#!/usr/bin/env python3
"""
Verificar datos de nómina en Redis DB2
"""

import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM/backend')
django.setup()

from django.conf import settings
import redis

def verificar_redis_nomina():
    """Verificar qué datos hay en Redis DB2"""
    print("🔍 Verificando Redis DB2 (Nómina)...")
    print("=" * 40)
    
    try:
        # Obtener configuración de Redis desde Django settings
        redis_config = getattr(settings, 'CACHES', {}).get('default', {})
        redis_host = redis_config.get('LOCATION', 'redis://redis:6379/0').split('//')[1].split(':')[0]
        redis_port = int(redis_config.get('LOCATION', 'redis://redis:6379/0').split(':')[1].split('/')[0])
        
        # Usar configuración específica para nómina
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=2,  # DB2 para nómina
            password='Redis_Password_2025!',
            decode_responses=True
        )
        
        # Verificar conexión
        r.ping()
        print(f"✅ Conectado a Redis: {redis_host}:{redis_port}/DB2")
        
        # Buscar claves de nómina
        claves = r.keys('sgm:nomina:*')
        print(f"\n📋 Encontradas {len(claves)} claves de nómina:")
        
        informes_encontrados = []
        
        for clave in sorted(claves):
            print(f"  • {clave}")
            
            # Si es un informe, obtener detalles
            if ':informe' in clave:
                try:
                    data_raw = r.get(clave)
                    if data_raw:
                        data = json.loads(data_raw)
                        metadatos = data.get('metadatos', {})
                        
                        informe_info = {
                            'clave': clave,
                            'cliente': metadatos.get('cliente', 'N/A'),
                            'periodo': metadatos.get('periodo', 'N/A'),
                            'fecha_calculo': metadatos.get('fecha_calculo', 'N/A'),
                            'estado': metadatos.get('estado_cierre', 'N/A')
                        }
                        informes_encontrados.append(informe_info)
                        
                        print(f"    ✅ Cliente: {informe_info['cliente']}")
                        print(f"    📅 Período: {informe_info['periodo']}")
                        print(f"    ⏰ Fecha: {informe_info['fecha_calculo']}")
                        
                except Exception as e:
                    print(f"    ❌ Error leyendo: {e}")
        
        print(f"\n📊 RESUMEN:")
        print(f"  • Total claves: {len(claves)}")
        print(f"  • Informes válidos: {len(informes_encontrados)}")
        
        if informes_encontrados:
            print(f"\n🎯 INFORMES DISPONIBLES:")
            for i, informe in enumerate(informes_encontrados, 1):
                print(f"  {i}. Cliente: {informe['cliente']}")
                print(f"     Período: {informe['periodo']}")
                print(f"     Clave: {informe['clave']}")
        else:
            print(f"\n⚠️  NO HAY INFORMES DE NÓMINA EN REDIS")
            print(f"    Posibles causas:")
            print(f"    - No se han generado informes aún")
            print(f"    - Los informes están en otra DB")
            print(f"    - Error en la generación de informes")
        
        return informes_encontrados
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return []

if __name__ == "__main__":
    informes = verificar_redis_nomina()
