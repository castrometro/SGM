#!/usr/bin/env python3
"""
Script de diagnóstico para verificar las clasificaciones persistentes
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
sys.path.append('/root/SGM/backend')
django.setup()

from api.models import Cliente
from contabilidad.models import AccountClassification, CuentaContable, ClasificacionSet, ClasificacionOption

def diagnosticar_clasificaciones_persistentes():
    print("🔍 DIAGNÓSTICO DE CLASIFICACIONES PERSISTENTES")
    print("=" * 60)
    
    # Listar todos los clientes
    clientes = Cliente.objects.all()
    print(f"\n📋 CLIENTES TOTALES: {clientes.count()}")
    
    for cliente in clientes[:5]:  # Solo los primeros 5
        print(f"\n🏢 Cliente: {cliente.id} - {cliente.nombre}")
        
        # Contar cuentas del cliente
        cuentas_count = CuentaContable.objects.filter(cliente=cliente).count()
        print(f"   💰 Cuentas: {cuentas_count}")
        
        # Contar sets del cliente
        sets_count = ClasificacionSet.objects.filter(cliente=cliente).count()
        print(f"   📊 Sets de clasificación: {sets_count}")
        
        # Mostrar algunos sets
        sets = ClasificacionSet.objects.filter(cliente=cliente)[:3]
        for set_cls in sets:
            opciones_count = ClasificacionOption.objects.filter(set_clas=set_cls).count()
            print(f"     - Set: {set_cls.nombre} (opciones: {opciones_count})")
        
        # Contar clasificaciones del cliente
        clasificaciones_count = AccountClassification.objects.filter(
            cuenta__cliente=cliente
        ).count()
        print(f"   🎯 Clasificaciones persistentes: {clasificaciones_count}")
        
        # Mostrar algunas clasificaciones
        if clasificaciones_count > 0:
            clasificaciones = AccountClassification.objects.filter(
                cuenta__cliente=cliente
            ).select_related('cuenta', 'set_clas', 'opcion')[:3]
            
            print("   📝 Ejemplos de clasificaciones:")
            for cls in clasificaciones:
                print(f"     - Cuenta {cls.cuenta.codigo}: {cls.set_clas.nombre} -> {cls.opcion.valor}")
        
        print()
    
    # Estadísticas globales
    total_clasificaciones = AccountClassification.objects.count()
    total_cuentas = CuentaContable.objects.count()
    total_sets = ClasificacionSet.objects.count()
    
    print(f"\n📊 ESTADÍSTICAS GLOBALES:")
    print(f"   Total clasificaciones: {total_clasificaciones}")
    print(f"   Total cuentas: {total_cuentas}")
    print(f"   Total sets: {total_sets}")
    
    if total_clasificaciones > 0:
        # Mostrar algunas clasificaciones recientes
        clasificaciones_recientes = AccountClassification.objects.select_related(
            'cuenta', 'cuenta__cliente', 'set_clas', 'opcion'
        ).order_by('-fecha_creacion')[:5]
        
        print(f"\n🕒 CLASIFICACIONES RECIENTES:")
        for cls in clasificaciones_recientes:
            print(f"   - Cliente {cls.cuenta.cliente.nombre} | Cuenta {cls.cuenta.codigo} | {cls.set_clas.nombre} -> {cls.opcion.valor} | {cls.fecha_creacion}")

if __name__ == "__main__":
    diagnosticar_clasificaciones_persistentes()
