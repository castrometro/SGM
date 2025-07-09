#!/usr/bin/env python3
"""
Script para poblar clasificaciones persistentes de prueba
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
sys.path.append('/root/SGM/backend')
django.setup()

from api.models import Cliente
from contabilidad.models import (
    AccountClassification, 
    CuentaContable, 
    ClasificacionSet, 
    ClasificacionOption
)

def poblar_clasificaciones_prueba():
    print("🔧 POBLANDO CLASIFICACIONES DE PRUEBA")
    print("=" * 50)
    
    # Buscar cliente con ID 2 (que parece ser el que estás usando)
    try:
        cliente = Cliente.objects.get(id=2)
        print(f"✅ Cliente encontrado: {cliente.nombre}")
    except Cliente.DoesNotExist:
        print("❌ Cliente con ID 2 no encontrado")
        return
    
    # Obtener algunas cuentas del cliente
    cuentas = CuentaContable.objects.filter(cliente=cliente)[:10]
    if not cuentas:
        print("❌ No hay cuentas para este cliente")
        return
    
    print(f"📋 Cuentas disponibles: {cuentas.count()}")
    
    # Obtener sets de clasificación del cliente
    sets = ClasificacionSet.objects.filter(cliente=cliente)
    if not sets:
        print("❌ No hay sets de clasificación para este cliente")
        return
    
    print(f"📊 Sets disponibles: {sets.count()}")
    for set_cls in sets:
        opciones_count = ClasificacionOption.objects.filter(set_clas=set_cls).count()
        print(f"  - {set_cls.nombre}: {opciones_count} opciones")
    
    # Crear algunas clasificaciones de prueba
    clasificaciones_creadas = 0
    clasificaciones_existentes = 0
    
    for cuenta in cuentas:
        for set_cls in sets:
            # Verificar si ya existe una clasificación
            if AccountClassification.objects.filter(cuenta=cuenta, set_clas=set_cls).exists():
                clasificaciones_existentes += 1
                continue
            
            # Obtener una opción aleatoria del set
            opciones = ClasificacionOption.objects.filter(set_clas=set_cls)
            if not opciones:
                continue
            
            opcion = opciones.first()  # Tomar la primera opción
            
            # Crear la clasificación
            AccountClassification.objects.create(
                cuenta=cuenta,
                set_clas=set_cls,
                opcion=opcion,
                asignado_por=None
            )
            clasificaciones_creadas += 1
            
            print(f"  ✅ Creada: {cuenta.codigo} -> {set_cls.nombre} -> {opcion.valor}")
    
    print(f"\n📊 RESUMEN:")
    print(f"  Clasificaciones creadas: {clasificaciones_creadas}")
    print(f"  Clasificaciones existentes: {clasificaciones_existentes}")
    print(f"  Total clasificaciones: {AccountClassification.objects.filter(cuenta__cliente=cliente).count()}")

if __name__ == "__main__":
    poblar_clasificaciones_prueba()
