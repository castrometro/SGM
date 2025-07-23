"""
Script de prueba para el sistema de incidencias consolidadas

Este script prueba que el sistema de detección de incidencias esté funcionando correctamente.
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from nomina.models import CierreNomina, IncidenciaCierre
from nomina.utils.DetectarIncidenciasConsolidadas import detectar_incidencias_consolidadas

def probar_sistema_incidencias():
    """
    Prueba el sistema de incidencias consolidadas
    """
    print("🔍 Probando sistema de detección de incidencias consolidadas...")
    
    # Buscar cierres consolidados
    cierres_consolidados = CierreNomina.objects.filter(estado='datos_consolidados').order_by('-periodo')
    
    print(f"📊 Encontrados {cierres_consolidados.count()} cierres consolidados")
    
    for cierre in cierres_consolidados[:3]:  # Probar los 3 más recientes
        print(f"\n🎯 Probando cierre: {cierre} - Estado: {cierre.estado}")
        
        try:
            # Detectar incidencias
            incidencias = detectar_incidencias_consolidadas(cierre)
            
            print(f"✅ Detección exitosa: {len(incidencias)} incidencias detectadas")
            
            # Mostrar tipos de incidencias detectadas
            tipos = {}
            for inc in incidencias:
                tipo = inc.tipo_incidencia
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            for tipo, cantidad in tipos.items():
                print(f"   - {tipo}: {cantidad} incidencias")
            
            # Verificar incidencias guardadas en BD
            incidencias_bd = cierre.incidencias.count()
            print(f"💾 Incidencias en BD: {incidencias_bd}")
            
        except Exception as e:
            print(f"❌ Error probando cierre {cierre.id}: {e}")
    
    print("\n🎯 Prueba del sistema completada")
    return True

if __name__ == "__main__":
    probar_sistema_incidencias()
