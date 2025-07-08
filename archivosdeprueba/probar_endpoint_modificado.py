#!/usr/bin/env python3
"""
Script para probar el endpoint modificado de movimientos-resumen
"""

import os
import sys
import django
import requests
from django.conf import settings

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.models import CierreContabilidad, CuentaContable

def probar_endpoint_modificado():
    """
    Prueba el endpoint modificado para verificar que incluye todas las cuentas
    """
    # Obtener el último cierre disponible
    cierre = CierreContabilidad.objects.last()
    if not cierre:
        print("❌ No hay cierres disponibles para probar")
        return
    
    print(f"🧪 Probando endpoint modificado con cierre ID: {cierre.id}")
    print(f"   Cliente: {cierre.cliente.nombre}")
    print(f"   Período: {cierre.periodo}")
    
    # Contar cuentas totales del cliente
    total_cuentas = CuentaContable.objects.filter(cliente=cierre.cliente).count()
    print(f"   Total cuentas del cliente: {total_cuentas}")
    
    # Simular la llamada al endpoint (sin hacer HTTP request real)
    from contabilidad.views.cierre import CierreContabilidadViewSet
    from django.http import HttpRequest
    from django.contrib.auth.models import AnonymousUser
    
    # Crear un request mock
    request = HttpRequest()
    request.user = AnonymousUser()
    request.method = 'GET'
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    
    # Crear una instancia del ViewSet
    viewset = CierreContabilidadViewSet()
    viewset.request = request
    
    try:
        # Llamar al método directamente
        response = viewset.movimientos_resumen(request, pk=cierre.id)
        
        if hasattr(response, 'data'):
            resultados = response.data
            if isinstance(resultados, list):
                print(f"✅ Endpoint devuelve {len(resultados)} cuentas")
                
                # Verificar que incluye cuentas sin movimientos
                cuentas_sin_movimientos = [r for r in resultados if r['total_debe'] == 0 and r['total_haber'] == 0]
                print(f"   Cuentas sin movimientos incluidas: {len(cuentas_sin_movimientos)}")
                
                if len(cuentas_sin_movimientos) > 0:
                    print("   ✅ El endpoint ahora incluye cuentas sin movimientos!")
                    print("   Ejemplos de cuentas sin movimientos:")
                    for i, cuenta in enumerate(cuentas_sin_movimientos[:3]):
                        print(f"      {i+1}. {cuenta['codigo']} - {cuenta['nombre']}")
                else:
                    print("   ℹ️  Todas las cuentas tienen movimientos en este cierre")
                
                # Mostrar algunas cuentas con movimientos
                cuentas_con_movimientos = [r for r in resultados if r['total_debe'] > 0 or r['total_haber'] > 0]
                print(f"   Cuentas con movimientos: {len(cuentas_con_movimientos)}")
                
                if len(cuentas_con_movimientos) > 0:
                    print("   Ejemplos de cuentas con movimientos:")
                    for i, cuenta in enumerate(cuentas_con_movimientos[:3]):
                        print(f"      {i+1}. {cuenta['codigo']} - {cuenta['nombre']}: D${cuenta['total_debe']:.2f} H${cuenta['total_haber']:.2f}")
                
            else:
                print(f"⚠️  Respuesta inesperada: {type(resultados)}")
        else:
            print(f"⚠️  Response sin data: {response}")
            
    except Exception as e:
        print(f"❌ Error al probar endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    probar_endpoint_modificado()
