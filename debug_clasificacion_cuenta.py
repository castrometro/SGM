#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué una cuenta aparece como no clasificada
cuando debería estar clasificada.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from contabilidad.models import (
    CuentaContable, 
    ClasificacionSet, 
    AccountClassification,
    ExcepcionClasificacionSet,
    CierreContabilidad
)
from api.models import Cliente

def diagnosticar_cuenta_clasificacion(codigo_cuenta, cliente_id, set_nombre=None):
    """
    Diagnóstica por qué una cuenta aparece como no clasificada
    """
    print(f"\n🔍 DIAGNÓSTICO PARA CUENTA: {codigo_cuenta}")
    print(f"📋 Cliente ID: {cliente_id}")
    print("="*60)
    
    try:
        # 1. Verificar que existe el cliente
        cliente = Cliente.objects.get(id=cliente_id)
        print(f"✅ Cliente encontrado: {cliente.nombre}")
        
        # 2. Verificar que existe la cuenta
        try:
            cuenta = CuentaContable.objects.get(codigo=codigo_cuenta, cliente=cliente)
            print(f"✅ Cuenta encontrada: {cuenta.codigo} - {cuenta.nombre}")
        except CuentaContable.DoesNotExist:
            print(f"❌ ERROR: Cuenta {codigo_cuenta} no encontrada para el cliente {cliente.nombre}")
            return
        
        # 3. Listar todos los sets de clasificación del cliente
        sets = ClasificacionSet.objects.filter(cliente=cliente)
        print(f"\n📊 Sets de clasificación disponibles ({len(sets)}):")
        for s in sets:
            print(f"  - ID {s.id}: {s.nombre}")
        
        # 4. Si se especifica un set, enfocarse en ese
        if set_nombre:
            try:
                set_objetivo = ClasificacionSet.objects.get(cliente=cliente, nombre__icontains=set_nombre)
                print(f"\n🎯 Analizando set específico: {set_objetivo.nombre} (ID: {set_objetivo.id})")
                
                # Verificar clasificación en este set
                clasificacion = AccountClassification.objects.filter(
                    cuenta=cuenta,
                    set_clas=set_objetivo
                ).first()
                
                if clasificacion:
                    print(f"✅ CUENTA SÍ ESTÁ CLASIFICADA en {set_objetivo.nombre}")
                    print(f"   - Opción: {clasificacion.opcion.valor}")
                    print(f"   - Descripción: {clasificacion.opcion.descripcion}")
                    print(f"   - Fecha creación: {clasificacion.created_at}")
                else:
                    print(f"❌ CUENTA NO CLASIFICADA en {set_objetivo.nombre}")
                
                # Verificar excepciones
                excepcion = ExcepcionClasificacionSet.objects.filter(
                    cliente=cliente,
                    cuenta_codigo=codigo_cuenta,
                    set_clasificacion=set_objetivo,
                    activa=True
                ).first()
                
                if excepcion:
                    print(f"⚠️  CUENTA TIENE EXCEPCIÓN ACTIVA en {set_objetivo.nombre}")
                    print(f"   - Motivo: {excepcion.motivo}")
                    print(f"   - Fecha: {excepcion.fecha_creacion}")
                    print(f"   - Usuario: {excepcion.usuario_creador}")
                else:
                    print(f"✅ No hay excepciones activas para este set")
                    
            except ClasificacionSet.DoesNotExist:
                print(f"❌ ERROR: Set '{set_nombre}' no encontrado")
                return
        else:
            # 5. Verificar clasificaciones en TODOS los sets
            print(f"\n📋 Estado de clasificación en todos los sets:")
            for s in sets:
                clasificacion = AccountClassification.objects.filter(
                    cuenta=cuenta,
                    set_clas=s
                ).first()
                
                if clasificacion:
                    print(f"  ✅ {s.nombre}: {clasificacion.opcion.valor}")
                else:
                    # Verificar excepción
                    excepcion = ExcepcionClasificacionSet.objects.filter(
                        cliente=cliente,
                        cuenta_codigo=codigo_cuenta,
                        set_clasificacion=s,
                        activa=True
                    ).first()
                    
                    if excepcion:
                        print(f"  ⚠️  {s.nombre}: EXCEPCIÓN ACTIVA ({excepcion.motivo})")
                    else:
                        print(f"  ❌ {s.nombre}: NO CLASIFICADA")
        
        # 6. Verificar la lógica de validación (simular el código del task)
        print(f"\n🔬 SIMULANDO LÓGICA DE VALIDACIÓN:")
        if set_nombre:
            set_obj = ClasificacionSet.objects.get(cliente=cliente, nombre__icontains=set_nombre)
            
            # Verificar excepción
            excepcion = ExcepcionClasificacionSet.objects.filter(
                cliente=cliente,
                cuenta_codigo=codigo_cuenta,
                set_clasificacion=set_obj,
                activa=True
            ).exists()
            
            if excepcion:
                print(f"  🔄 Cuenta {codigo_cuenta} tiene excepción para {set_obj.nombre} - NO se validará")
            else:
                tiene_clasificacion = AccountClassification.objects.filter(
                    cuenta=cuenta,
                    set_clas=set_obj
                ).exists()
                
                if tiene_clasificacion:
                    print(f"  ✅ Cuenta {codigo_cuenta} ESTÁ clasificada en {set_obj.nombre}")
                else:
                    print(f"  ❌ Cuenta {codigo_cuenta} NO ESTÁ clasificada en {set_obj.nombre}")
                    print(f"      → Se generaría incidencia")
        
        # 7. Información adicional de debugging
        print(f"\n🔧 INFORMACIÓN DE DEBUG:")
        print(f"  - Cuenta ID: {cuenta.id}")
        print(f"  - Cliente ID: {cliente.id}")
        
        # Verificar si hay algún problema con las foreign keys
        all_classifications = AccountClassification.objects.filter(cuenta=cuenta)
        print(f"  - Total clasificaciones de esta cuenta: {all_classifications.count()}")
        
        for cl in all_classifications:
            print(f"    · Set: {cl.set_clas.nombre} (ID: {cl.set_clas.id})")
            print(f"      Opción: {cl.opcion.valor} (ID: {cl.opcion.id})")
        
    except Cliente.DoesNotExist:
        print(f"❌ ERROR: Cliente {cliente_id} no encontrado")
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Usar parámetros de línea de comandos o valores por defecto
    if len(sys.argv) >= 3:
        codigo_cuenta = sys.argv[1]
        cliente_id = int(sys.argv[2])
        set_nombre = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        # Valores por defecto basados en tu problema
        codigo_cuenta = "1-02-003-001-0001"
        cliente_id = 1  # Ajustar según tu cliente
        set_nombre = "estado de situacion financiera"
    
    diagnosticar_cuenta_clasificacion(codigo_cuenta, cliente_id, set_nombre)
