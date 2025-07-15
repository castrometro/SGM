#!/usr/bin/env python3
"""
Demostración: Cómo Redis maneja las "carpetas" (que no existen)
================================================================

Este script muestra cómo Redis realmente funciona sin carpetas.
"""

import redis
import json

def demo_redis_structure():
    """Demostrar cómo Redis maneja la estructura jerárquica"""
    
    print("🔍 DEMOSTRACIÓN: CÓMO REDIS MANEJA LAS 'CARPETAS'")
    print("=" * 60)
    
    # Conectar a Redis (simulado - no ejecutar en producción)
    print("1. Conectando a Redis...")
    print("   redis_client = redis.Redis(host='redis', port=6379, db=1)")
    
    print("\n2. Redis es CLAVE-VALOR, no tiene carpetas:")
    print("   ❌ NO existe: crear_carpeta('contabilidad')")
    print("   ✅ SÍ existe: set('clave', 'valor')")
    
    print("\n3. Simulamos estructura con nombres de claves:")
    
    # Ejemplos de claves que simularían nuestra estructura
    claves_ejemplo = [
        "sgm:contabilidad:1:2025-07:kpis",
        "sgm:contabilidad:1:2025-07:esf", 
        "sgm:contabilidad:1:2025-07:pruebas:esf:current_system",
        "sgm:contabilidad:1:2025-07:pruebas:kpis:scenario_test",
        "sgm:contabilidad:2:2025-08:kpis",
    ]
    
    print("\n   CLAVES QUE SE CREAN EN REDIS:")
    for i, clave in enumerate(claves_ejemplo, 1):
        print(f"   {i}. {clave}")
    
    print("\n4. Cómo nuestro código 'crea' la estructura:")
    print("""
   def _get_key(self, cliente_id, periodo, tipo_dato):
       return f"sgm:contabilidad:{cliente_id}:{periodo}:{tipo_dato}"
   
   # Cuando llamamos:
   cache_system.set_prueba_esf(1, "2025-07", esf_data, "current_system")
   
   # Internamente genera la clave:
   key = "sgm:contabilidad:1:2025-07:pruebas:esf:current_system"
   
   # Y ejecuta:
   redis_client.setex(key, ttl, datos_serializados)
   """)
    
    print("\n5. Navegación por 'carpetas' usando patrones:")
    print("""
   # Para listar todas las "pruebas" de un cliente:
   pattern = "sgm:contabilidad:1:*:pruebas:*"
   keys = redis_client.keys(pattern)
   
   # Redis retorna:
   # ['sgm:contabilidad:1:2025-07:pruebas:esf:current_system',
   #  'sgm:contabilidad:1:2025-07:pruebas:kpis:scenario_test']
   """)
    
    print("\n6. En RedisInsight verías:")
    print("   📁 sgm")
    print("   └── 📁 contabilidad") 
    print("       └── 📁 1")
    print("           └── 📁 2025-07")
    print("               ├── 📄 kpis")
    print("               ├── 📄 esf")
    print("               └── 📁 pruebas")
    print("                   ├── 📁 esf")
    print("                   │   └── 📄 current_system")
    print("                   └── 📁 kpis")
    print("                       └── 📄 scenario_test")
    
    print("\n   ⚠️  PERO EN REALIDAD Redis solo tiene 5 claves string!")
    
    print("\n7. Ventajas de esta convención:")
    print("   ✅ Organización visual clara")
    print("   ✅ Fácil filtrado con patrones")
    print("   ✅ Búsquedas eficientes")
    print("   ✅ Compatibilidad con herramientas como RedisInsight")
    
    print("\n8. Cómo se 'crean' las pruebas en nuestro sistema:")
    
    # Simular el proceso
    ejemplo_datos = {
        'total_activos': 1000000,
        'balance_cuadrado': True
    }
    
    print(f"""
   # 1. Usuario llama:
   cache_system.set_prueba_esf(1, "2025-07", esf_data, "current_system")
   
   # 2. Sistema genera clave:
   key = "sgm:contabilidad:1:2025-07:pruebas:esf:current_system"
   
   # 3. Serializa datos:
   data = json.dumps(esf_data)
   
   # 4. Guarda en Redis:
   redis_client.setex(key, 3600, data)
   
   # 5. La "carpeta" pruebas existe porque hay una clave que la contiene!
   """)
    
    print("\n🎯 CONCLUSIÓN:")
    print("   Las 'carpetas' se crean automáticamente cuando guardamos")
    print("   datos con claves que siguen nuestro patrón de nombres.")
    print("   ¡No hay que crear carpetas explícitamente!")

if __name__ == "__main__":
    demo_redis_structure()
