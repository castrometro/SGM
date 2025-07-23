#!/usr/bin/env python3
"""
Script de prueba para verificar el flujo de finalización de cierre de nómina
"""

import os
import django
import sys

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from nomina.models import CierreNomina

def verificar_flujo_finalizacion():
    """Verificar que el flujo de finalización funcione correctamente"""
    
    print("🔍 VERIFICANDO FLUJO DE FINALIZACIÓN DE CIERRE NOMINA:")
    print("=" * 60)
    
    # Buscar cierres en estado incidencias_resueltas
    cierres_resueltas = CierreNomina.objects.filter(estado='incidencias_resueltas')
    
    print(f"📊 Cierres en estado 'incidencias_resueltas': {cierres_resueltas.count()}")
    
    if cierres_resueltas.exists():
        cierre = cierres_resueltas.first()
        print(f"\n🏢 Cliente: {cierre.cliente.nombre}")
        print(f"📅 Periodo: {cierre.periodo}")
        print(f"📌 Estado principal: {cierre.estado}")
        print(f"🔄 Estado incidencias: {cierre.estado_incidencias}")
        print(f"📈 Total incidencias: {cierre.total_incidencias}")
        
        # Verificar que cumple las condiciones para finalizar
        print(f"\n✅ VALIDACIONES PARA FINALIZACIÓN:")
        print(f"  • Estado es 'incidencias_resueltas': {cierre.estado == 'incidencias_resueltas'}")
        print(f"  • Total incidencias es 0: {cierre.total_incidencias == 0}")
        
        # Verificar incidencias pendientes
        incidencias_pendientes = cierre.incidencias.filter(
            estado__in=['pendiente', 'en_revision']
        ).count()
        print(f"  • Incidencias pendientes: {incidencias_pendientes}")
        print(f"  • Puede finalizarse: {cierre.estado == 'incidencias_resueltas' and incidencias_pendientes == 0}")
        
        return cierre
    else:
        print("❌ No hay cierres en estado 'incidencias_resueltas' para probar")
        return None

def simular_finalizacion(cierre):
    """Simular el proceso de finalización"""
    
    if not cierre:
        return
        
    print(f"\n🚀 SIMULANDO FINALIZACIÓN DEL CIERRE {cierre.id}:")
    print("-" * 50)
    
    try:
        from django.utils import timezone
        
        # Verificar condiciones previas
        if cierre.estado != 'incidencias_resueltas':
            print(f"❌ Error: El cierre debe estar en 'incidencias_resueltas', actual: {cierre.estado}")
            return
            
        incidencias_pendientes = cierre.incidencias.filter(
            estado__in=['pendiente', 'en_revision']
        ).count()
        
        if incidencias_pendientes > 0:
            print(f"❌ Error: Hay {incidencias_pendientes} incidencias pendientes")
            return
        
        print("✅ Todas las validaciones pasaron")
        print("✅ El cierre puede ser finalizado exitosamente")
        print("\n🎯 CAMBIOS QUE SE REALIZARÍAN:")
        print(f"  • Estado: {cierre.estado} → finalizado")
        print(f"  • Estado incidencias: {cierre.estado_incidencias} → completado")
        print(f"  • Fecha finalización: {cierre.fecha_finalizacion} → {timezone.now()}")
        
        # NO realizamos los cambios reales, solo simulamos
        print("\n📝 NOTA: Esta es solo una simulación. No se realizaron cambios reales.")
        
    except Exception as e:
        print(f"❌ Error en simulación: {e}")

if __name__ == "__main__":
    cierre = verificar_flujo_finalizacion()
    simular_finalizacion(cierre)
