#!/usr/bin/env python3
"""
Script de diagnóstico mejorado para investigar problemas de clasificación de cuentas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Cliente
from backend.contabilidad.models import (
    CuentaContable, 
    ClasificacionSet, 
    AccountClassification,
    ExcepcionClasificacionSet,
    CierreContabilidad
)

def diagnosticar_cuenta_clasificacion(codigo_cuenta, cliente_id=None, cliente_nombre=None):
    """
    Diagnostica por qué una cuenta aparece como no clasificada
    """
    print(f"\n🔍 DIAGNÓSTICO DE CLASIFICACIÓN")
    print(f"═══════════════════════════════════")
    print(f"Cuenta: {codigo_cuenta}")
    
    # 1. Buscar el cliente
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            print(f"❌ Cliente con ID {cliente_id} no encontrado")
            return
    elif cliente_nombre:
        try:
            cliente = Cliente.objects.get(nombre__icontains=cliente_nombre)
        except Cliente.DoesNotExist:
            print(f"❌ Cliente con nombre '{cliente_nombre}' no encontrado")
            return
        except Cliente.MultipleObjectsReturned:
            clientes = Cliente.objects.filter(nombre__icontains=cliente_nombre)
            print(f"❌ Múltiples clientes encontrados:")
            for c in clientes:
                print(f"   - {c.id}: {c.nombre}")
            return
    else:
        print("❌ Debe proporcionar cliente_id o cliente_nombre")
        return
    
    print(f"Cliente: {cliente.id} - {cliente.nombre}")
    
    # 2. Verificar si la cuenta existe
    try:
        cuenta = CuentaContable.objects.get(cliente=cliente, codigo=codigo_cuenta)
        print(f"✅ Cuenta encontrada: {cuenta.codigo} - {cuenta.nombre}")
    except CuentaContable.DoesNotExist:
        print(f"❌ Cuenta {codigo_cuenta} no encontrada para el cliente {cliente.nombre}")
        return
    
    # 3. Obtener todos los sets de clasificación del cliente
    sets_clasificacion = ClasificacionSet.objects.filter(cliente=cliente)
    print(f"\n📋 SETS DE CLASIFICACIÓN ({sets_clasificacion.count()} total)")
    print(f"─────────────────────────────────")
    
    if not sets_clasificacion.exists():
        print("❌ No hay sets de clasificación configurados para este cliente")
        return
    
    sets_problema = []
    
    for set_clas in sets_clasificacion:
        print(f"\n🔹 Set: {set_clas.id} - {set_clas.nombre}")
        
        # 4. Verificar si tiene clasificación en este set
        clasificacion = AccountClassification.objects.filter(
            cuenta=cuenta,
            set_clas=set_clas
        ).first()
        
        if clasificacion:
            print(f"   ✅ Clasificada: {clasificacion.opcion.valor} - {clasificacion.opcion.descripcion}")
        else:
            print(f"   ❌ NO clasificada en este set")
            sets_problema.append(set_clas)
        
        # 5. Verificar si tiene excepción para este set
        excepcion = ExcepcionClasificacionSet.objects.filter(
            cliente=cliente,
            cuenta_codigo=codigo_cuenta,
            set_clasificacion=set_clas,
            activa=True
        ).first()
        
        if excepcion:
            print(f"   🚫 Tiene excepción: {excepcion.motivo}")
        else:
            print(f"   ⚪ Sin excepción")
    
    # 6. Resumen del problema
    print(f"\n📊 RESUMEN")
    print(f"─────────────")
    if sets_problema:
        print(f"❌ Problemas en {len(sets_problema)} sets:")
        for set_prob in sets_problema:
            print(f"   - {set_prob.nombre}")
    else:
        print(f"✅ Cuenta correctamente clasificada en todos los sets")
    
    # 7. Verificar en cierres recientes
    cierres_recientes = CierreContabilidad.objects.filter(cliente=cliente).order_by('-id')[:3]
    print(f"\n🗓️ CIERRES RECIENTES")
    print(f"─────────────────────")
    for cierre in cierres_recientes:
        print(f"   - {cierre.id}: {cierre.periodo} ({cierre.estado})")
    
    # 8. Sugerencias
    print(f"\n💡 POSIBLES SOLUCIONES")
    print(f"─────────────────────────")
    if sets_problema:
        print(f"1. Clasificar manualmente la cuenta en los sets problemáticos")
        print(f"2. Marcar como 'No aplica' si la cuenta no debe clasificarse en esos sets")
        print(f"3. Verificar si hay inconsistencias en los datos")
    else:
        print(f"La cuenta parece estar bien clasificada. El problema puede ser:")
        print(f"1. Cache/sincronización del sistema")
        print(f"2. Diferencia entre datos y validación en tiempo real")
        print(f"3. Problema en la lógica de validación")

def main():
    print("🔍 DIAGNÓSTICO DE CLASIFICACIÓN DE CUENTAS")
    print("═══════════════════════════════════════════")
    
    # Lista de clientes disponibles
    clientes = Cliente.objects.all()
    print("\nClientes disponibles:")
    for cliente in clientes:
        print(f"- {cliente.id}: {cliente.nombre}")
    
    # Investigar cuenta específica
    codigo_cuenta = "1-02-003-001-0001"
    
    # Probar con cada cliente
    for cliente in clientes:
        print(f"\n{'='*60}")
        diagnosticar_cuenta_clasificacion(codigo_cuenta, cliente_id=cliente.id)

if __name__ == "__main__":
    main()
