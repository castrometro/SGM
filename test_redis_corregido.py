#!/usr/bin/env python
"""
Test corregido: Verificar que el sistema Redis funciona sin errores de username
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from nomina.models import CierreNomina
from nomina.models_informe import InformeNomina

def test_redis_corregido():
    """Test para verificar que el error de username está corregido"""
    
    print("🧪 Iniciando test de Redis corregido...")
    
    # Buscar un cierre finalizado
    cierre = CierreNomina.objects.filter(estado='finalizado').first()
    
    if not cierre:
        print("❌ No hay cierres finalizados para probar")
        return
    
    print(f"📋 Cierre encontrado: {cierre.cliente.nombre} - {cierre.periodo}")
    
    # Verificar si tiene informe
    if hasattr(cierre, 'informe'):
        informe = cierre.informe
        print(f"📊 Informe encontrado ID: {informe.id}")
        
        # Probar envío a Redis
        try:
            resultado = informe.enviar_a_redis(ttl_hours=1)
            
            if resultado['success']:
                print(f"✅ ÉXITO: Informe enviado a Redis")
                print(f"🗝️  Clave: {resultado['clave_redis']}")
                print(f"📏 Tamaño: {resultado['size_kb']:.1f} KB")
                print(f"⏱️  TTL: {resultado['ttl_hours']} horas")
                
                # Verificar que se puede obtener
                informe_redis = InformeNomina.obtener_desde_redis(
                    cierre.cliente.id, 
                    cierre.periodo
                )
                
                if informe_redis:
                    print(f"✅ VERIFICADO: Informe recuperado desde Redis")
                    print(f"👤 Usuario finalizó: {informe_redis['usuario_finalizacion']}")
                else:
                    print("⚠️ No se pudo recuperar desde Redis")
                    
            else:
                print(f"❌ FALLO: {resultado['error']}")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("📋 El cierre no tiene informe generado")

if __name__ == "__main__":
    test_redis_corregido()
