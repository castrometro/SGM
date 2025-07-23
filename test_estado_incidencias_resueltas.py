#!/usr/bin/env python3
"""
Script para probar el manejo del estado 'incidencias_resueltas' en el frontend
"""

import os
import django
import sys

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from nomina.models import CierreNomina

def verificar_estados_cierre():
    """Verificar qué cierres están en estado incidencias_resueltas"""
    
    print("🔍 VERIFICANDO ESTADOS DE CIERRE NOMINA:")
    print("=" * 60)
    
    # Buscar cierres en estado incidencias_resueltas
    cierres_resueltas = CierreNomina.objects.filter(estado='incidencias_resueltas')
    
    print(f"📊 Cierres en estado 'incidencias_resueltas': {cierres_resueltas.count()}")
    
    for cierre in cierres_resueltas:
        print(f"\n🏢 Cliente: {cierre.cliente.nombre}")
        print(f"📅 Periodo: {cierre.periodo}")
        print(f"📌 Estado principal: {cierre.estado}")
        print(f"🔄 Estado incidencias: {cierre.estado_incidencias}")
        print(f"📈 Total incidencias: {cierre.total_incidencias}")
        print(f"👤 Supervisor: {cierre.supervisor_asignado}")
        print(f"⏰ Última revisión: {cierre.fecha_ultima_revision}")
    
    # Mostrar también otros estados relevantes
    print(f"\n📋 RESUMEN DE TODOS LOS ESTADOS:")
    estados = CierreNomina.objects.values_list('estado', flat=True).distinct()
    
    for estado in sorted(estados):
        count = CierreNomina.objects.filter(estado=estado).count()
        print(f"  • {estado}: {count} cierres")
    
    # Mostrar estados de incidencias específicos
    print(f"\n🎯 ESTADOS DE INCIDENCIAS:")
    estados_inc = CierreNomina.objects.values_list('estado_incidencias', flat=True).distinct()
    
    for estado in sorted(estados_inc):
        count = CierreNomina.objects.filter(estado_incidencias=estado).count()
        print(f"  • {estado}: {count} cierres")

if __name__ == "__main__":
    verificar_estados_cierre()
