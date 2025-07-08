#!/usr/bin/env python3
"""
Script para revisar el contenido de Redis/caché que pueda estar afectando las clasificaciones
"""
import os
import sys
import django
import redis
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/root/SGM')
django.setup()

from django.core.cache import cache
from django.conf import settings

def revisar_cache_django():
    """Revisar el caché de Django"""
    print("=" * 80)
    print("🔍 REVISANDO CACHÉ DE DJANGO")
    print("=" * 80)
    
    # Intentar obtener algunas claves conocidas que podrían afectar clasificaciones
    posibles_claves = [
        'clasificaciones_esf_eri',
        'cuentas_esf',
        'cuentas_eri',
        'saldos_anteriores',
        'totales_esf_eri',
        'balance_validacion',
        'clasificacion_cuentas',
        'AccountClassification',
        'ClasificacionSet',
        'ClasificacionOption',
    ]
    
    cache_encontrado = False
    for clave in posibles_claves:
        valor = cache.get(clave)
        if valor is not None:
            cache_encontrado = True
            print(f"🔑 CLAVE ENCONTRADA: {clave}")
            print(f"   Tipo: {type(valor)}")
            print(f"   Valor: {valor}")
            print()
    
    if not cache_encontrado:
        print("✅ No se encontraron claves específicas en el caché de Django")
    
    # Intentar limpiar todo el caché
    print("\n🧹 LIMPIANDO CACHÉ DE DJANGO...")
    cache.clear()
    print("✅ Caché de Django limpiado")

def revisar_redis_directo():
    """Revisar Redis directamente"""
    print("\n" + "=" * 80)
    print("🔍 REVISANDO REDIS DIRECTAMENTE")
    print("=" * 80)
    
    try:
        # Conectar a Redis usando la configuración de Django
        if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
            cache_config = settings.CACHES['default']
            if cache_config['BACKEND'] == 'django_redis.cache.RedisCache':
                location = cache_config['LOCATION']
                print(f"📍 Conectando a Redis: {location}")
                
                # Extraer host y puerto de la URL de Redis
                if location.startswith('redis://'):
                    location = location[8:]  # Remover 'redis://'
                
                host_port = location.split(':')
                host = host_port[0] if host_port[0] else 'localhost'
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                
                r = redis.Redis(host=host, port=port, decode_responses=True)
                
                # Obtener todas las claves
                claves = r.keys('*')
                print(f"📊 Total de claves en Redis: {len(claves)}")
                
                if claves:
                    print("\n🔑 CLAVES ENCONTRADAS:")
                    for clave in sorted(claves)[:20]:  # Mostrar solo las primeras 20
                        tipo = r.type(clave)
                        ttl = r.ttl(clave)
                        print(f"   {clave} (tipo: {tipo}, TTL: {ttl})")
                        
                        # Si la clave parece relacionada con clasificaciones, mostrar su valor
                        if any(keyword in clave.lower() for keyword in ['clasif', 'esf', 'eri', 'cuenta', 'balance']):
                            try:
                                valor = r.get(clave)
                                if valor:
                                    print(f"     🔍 VALOR: {valor[:200]}...")  # Primeros 200 caracteres
                            except:
                                pass
                    
                    if len(claves) > 20:
                        print(f"   ... y {len(claves) - 20} claves más")
                    
                    # Limpiar Redis
                    print(f"\n🧹 LIMPIANDO REDIS...")
                    r.flushdb()
                    print("✅ Redis limpiado")
                else:
                    print("✅ No se encontraron claves en Redis")
            else:
                print(f"⚠️  Backend de caché no es Redis: {cache_config['BACKEND']}")
        else:
            print("⚠️  No se encontró configuración de caché")
            
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        print("   Intentando con configuración por defecto...")
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            claves = r.keys('*')
            print(f"📊 Total de claves en Redis (localhost): {len(claves)}")
            if claves:
                print("🧹 Limpiando Redis localhost...")
                r.flushdb()
                print("✅ Redis localhost limpiado")
        except Exception as e2:
            print(f"❌ Error con Redis localhost: {e2}")

def revisar_variables_entorno():
    """Revisar variables de entorno que podrían afectar el caché"""
    print("\n" + "=" * 80)
    print("🔍 REVISANDO VARIABLES DE ENTORNO")
    print("=" * 80)
    
    variables_cache = [
        'REDIS_URL',
        'CACHE_URL', 
        'DJANGO_CACHE_BACKEND',
        'CELERY_BROKER_URL',
        'CELERY_RESULT_BACKEND'
    ]
    
    for var in variables_cache:
        valor = os.environ.get(var)
        if valor:
            print(f"🔧 {var}: {valor}")
        else:
            print(f"❌ {var}: No definida")

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE REDIS/CACHÉ")
    print("Este script revisa si hay datos en caché que puedan estar afectando las clasificaciones ESF/ERI")
    print()
    
    revisar_variables_entorno()
    revisar_cache_django()
    revisar_redis_directo()
    
    print("\n" + "=" * 80)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("Si había datos en caché, ya fueron limpiados.")
    print("Ahora puedes ejecutar el procesamiento nuevamente para ver si hay diferencias.")
    print("=" * 80)
