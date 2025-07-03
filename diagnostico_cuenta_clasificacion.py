#!/usr/bin/env python3
"""
Script de diagnóstico para investigar por qué una cuenta aparece como no clasificada
cuando aparentemente sí lo está.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM/backend')
django.setup()

from contabilidad.models import (
    CuentaContable, ClasificacionSet, AccountClassification, 
    CierreContabilidad, ExcepcionClasificacionSet
)
from api.models import Cliente

def diagnosticar_cuenta_clasificacion(cliente_nombre, codigo_cuenta, set_nombre):
    """
    Diagnostica por qué una cuenta aparece como no clasificada
    """
    print(f"\n{'='*60}")
    print(f"🔍 DIAGNÓSTICO PARA CUENTA: {codigo_cuenta}")
    print(f"📊 SET: {set_nombre}")
    print(f"🏢 CLIENTE: {cliente_nombre}")
    print(f"{'='*60}\n")
    
    try:
        # 1. Verificar que el cliente existe
        cliente = Cliente.objects.filter(nombre__icontains=cliente_nombre).first()
        if not cliente:
            print(f"❌ ERROR: Cliente '{cliente_nombre}' no encontrado")
            clientes = Cliente.objects.all()[:5]
            print("📝 Clientes disponibles:")
            for c in clientes:
                print(f"   - {c.nombre}")
            return
        
        print(f"✅ Cliente encontrado: {cliente.nombre} (ID: {cliente.id})")
        
        # 2. Verificar que la cuenta existe
        cuenta = CuentaContable.objects.filter(
            cliente=cliente,
            codigo=codigo_cuenta
        ).first()
        
        if not cuenta:
            print(f"❌ ERROR: Cuenta '{codigo_cuenta}' no encontrada para cliente {cliente.nombre}")
            cuentas_similares = CuentaContable.objects.filter(
                cliente=cliente,
                codigo__startswith=codigo_cuenta[:5]
            )[:5]
            print("📝 Cuentas similares:")
            for c in cuentas_similares:
                print(f"   - {c.codigo}: {c.nombre}")
            return
        
        print(f"✅ Cuenta encontrada: {cuenta.codigo} - {cuenta.nombre}")
        
        # 3. Verificar que el set de clasificación existe
        set_clasificacion = ClasificacionSet.objects.filter(
            cliente=cliente,
            nombre__icontains=set_nombre
        ).first()
        
        if not set_clasificacion:
            print(f"❌ ERROR: Set '{set_nombre}' no encontrado para cliente {cliente.nombre}")
            sets_disponibles = ClasificacionSet.objects.filter(cliente=cliente)
            print("📝 Sets disponibles:")
            for s in sets_disponibles:
                print(f"   - {s.nombre} (ID: {s.id})")
            return
        
        print(f"✅ Set encontrado: {set_clasificacion.nombre} (ID: {set_clasificacion.id})")
        
        # 4. Verificar si existe la clasificación
        clasificacion = AccountClassification.objects.filter(
            cuenta=cuenta,
            set_clas=set_clasificacion
        ).first()
        
        if clasificacion:
            print(f"✅ CLASIFICACIÓN ENCONTRADA:")
            print(f"   - Opción: {clasificacion.opcion.valor}")
            print(f"   - Descripción: {clasificacion.opcion.descripcion}")
            print(f"   - Fecha creación: {clasificacion.fecha_creacion}")
        else:
            print(f"❌ NO SE ENCONTRÓ CLASIFICACIÓN para esta cuenta en este set")
            
            # Verificar si hay clasificaciones en otros sets
            otras_clasificaciones = AccountClassification.objects.filter(cuenta=cuenta)
            if otras_clasificaciones:
                print("📝 Clasificaciones en otros sets:")
                for c in otras_clasificaciones:
                    print(f"   - Set: {c.set_clas.nombre} | Opción: {c.opcion.valor}")
            else:
                print("📝 Esta cuenta NO tiene clasificaciones en ningún set")
        
        # 5. Verificar excepciones
        excepcion = ExcepcionClasificacionSet.objects.filter(
            cliente=cliente,
            cuenta_codigo=codigo_cuenta,
            set_clasificacion=set_clasificacion,
            activa=True
        ).first()
        
        if excepcion:
            print(f"⚠️  EXCEPCIÓN ACTIVA:")
            print(f"   - Motivo: {excepcion.motivo}")
            print(f"   - Fecha: {excepcion.fecha_creacion}")
            print(f"   - Usuario: {excepcion.usuario_creador}")
        else:
            print(f"✅ No hay excepciones activas para esta cuenta en este set")
        
        # 6. Verificar todas las clasificaciones de la cuenta
        print(f"\n📊 RESUMEN COMPLETO DE CLASIFICACIONES:")
        todas_clasificaciones = AccountClassification.objects.filter(cuenta=cuenta)
        if todas_clasificaciones:
            for c in todas_clasificaciones:
                print(f"   ✓ Set: {c.set_clas.nombre} → {c.opcion.valor}")
        else:
            print(f"   ❌ Esta cuenta NO tiene ninguna clasificación")
        
        # 7. Verificar todas las excepciones de la cuenta
        print(f"\n⚠️  EXCEPCIONES ACTIVAS:")
        excepciones = ExcepcionClasificacionSet.objects.filter(
            cliente=cliente,
            cuenta_codigo=codigo_cuenta,
            activa=True
        )
        if excepciones:
            for exc in excepciones:
                print(f"   - Set: {exc.set_clasificacion.nombre} | Motivo: {exc.motivo}")
        else:
            print(f"   ✅ No hay excepciones activas para esta cuenta")
        
        # 8. Diagnóstico final
        print(f"\n🎯 DIAGNÓSTICO FINAL:")
        if clasificacion and not excepcion:
            print(f"   ✅ La cuenta ESTÁ correctamente clasificada")
            print(f"   🤔 Si aparece como incidencia, puede ser:")
            print(f"      - Cache no actualizado")
            print(f"      - Diferencia en códigos de cuenta (espacios, mayúsculas)")
            print(f"      - Problema en la lógica de validación")
        elif excepcion:
            print(f"   ⚠️  La cuenta tiene excepción activa - NO debería aparecer como incidencia")
        else:
            print(f"   ❌ La cuenta NO está clasificada en este set")
        
    except Exception as e:
        print(f"💥 ERROR en diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Usar los datos del problema reportado
    diagnosticar_cuenta_clasificacion(
        cliente_nombre="",  # Agregar nombre del cliente aquí
        codigo_cuenta="1-02-003-001-0001",
        set_nombre="estado de situacion financiera"
    )
