#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de las clasificaciones persistentes
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from api.models import Cliente
from contabilidad.models import (
    CuentaContable, 
    AccountClassification, 
    ClasificacionSet, 
    ClasificacionOption
)

def diagnosticar_clasificaciones():
    print("=== DIAGNÓSTICO DE CLASIFICACIONES PERSISTENTES ===\n")
    
    # Verificar clientes
    clientes = Cliente.objects.all()[:3]
    print(f"Clientes disponibles: {clientes.count()}")
    for cliente in clientes:
        print(f"  - Cliente {cliente.id}: {cliente.nombre}")
    
    if not clientes.exists():
        print("❌ No hay clientes en la base de datos")
        return
    
    cliente = clientes.first()
    print(f"\n🔍 Analizando cliente: {cliente.id} - {cliente.nombre}")
    
    # Verificar cuentas
    cuentas = CuentaContable.objects.filter(cliente=cliente)
    print(f"  📊 Cuentas del cliente: {cuentas.count()}")
    
    if cuentas.exists():
        print(f"    Ejemplos:")
        for cuenta in cuentas[:5]:
            print(f"      - {cuenta.codigo}: {cuenta.nombre}")
    
    # Verificar sets de clasificación
    sets_clasificacion = ClasificacionSet.objects.filter(cliente=cliente)
    print(f"  📋 Sets de clasificación: {sets_clasificacion.count()}")
    
    for set_clas in sets_clasificacion:
        opciones = ClasificacionOption.objects.filter(set_clas=set_clas)
        print(f"    - {set_clas.nombre}: {opciones.count()} opciones")
        for opcion in opciones[:3]:
            print(f"      * {opcion.valor}")
    
    # Verificar clasificaciones existentes
    clasificaciones = AccountClassification.objects.filter(cuenta__cliente=cliente)
    print(f"  🏷️ Clasificaciones existentes: {clasificaciones.count()}")
    
    if clasificaciones.exists():
        print(f"    Ejemplos:")
        for clasificacion in clasificaciones[:5]:
            print(f"      - {clasificacion.cuenta.codigo} → {clasificacion.set_clas.nombre}: {clasificacion.opcion.valor}")
    
    # Estadísticas
    total_cuentas = cuentas.count()
    cuentas_clasificadas = CuentaContable.objects.filter(
        cliente=cliente,
        clasificaciones__isnull=False
    ).distinct().count()
    
    if total_cuentas > 0:
        porcentaje = (cuentas_clasificadas / total_cuentas) * 100
        print(f"\n📈 Estadísticas:")
        print(f"    Total de cuentas: {total_cuentas}")
        print(f"    Cuentas clasificadas: {cuentas_clasificadas}")
        print(f"    Porcentaje clasificado: {porcentaje:.1f}%")
    
    # Crear algunas clasificaciones de prueba si no existen
    if clasificaciones.count() == 0 and sets_clasificacion.exists() and cuentas.exists():
        print(f"\n🔧 Creando clasificaciones de prueba...")
        
        set_prueba = sets_clasificacion.first()
        opciones = ClasificacionOption.objects.filter(set_clas=set_prueba)
        
        if opciones.exists():
            opcion_prueba = opciones.first()
            cuentas_prueba = cuentas[:3]
            
            for cuenta in cuentas_prueba:
                clasificacion, created = AccountClassification.objects.get_or_create(
                    cuenta=cuenta,
                    set_clas=set_prueba,
                    defaults={'opcion': opcion_prueba}
                )
                if created:
                    print(f"    ✅ Creada: {cuenta.codigo} → {set_prueba.nombre}: {opcion_prueba.valor}")
    
    print(f"\n✅ Diagnóstico completado para cliente {cliente.id}")

if __name__ == "__main__":
    diagnosticar_clasificaciones()
