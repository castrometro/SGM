#!/usr/bin/env python
"""
Script para corregir clasificaciones del cliente ID=2 que perdieron su cuenta_codigo
después de ser migradas de temporales a FK.

Este script restaura el cuenta_codigo usando el código de la cuenta FK,
para que el modal CRUD pueda mostrar todas las clasificaciones correctamente.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_contable.settings')
django.setup()

from contabilidad.models import AccountClassification, Cliente

def main():
    CLIENTE_ID = 2
    
    print(f"🔧 Corrección de clasificaciones para cliente ID={CLIENTE_ID}")
    print("=" * 60)
    
    try:
        # Verificar que el cliente existe
        cliente = Cliente.objects.get(id=CLIENTE_ID)
        print(f"✅ Cliente encontrado: {cliente.nombre}")
        print()
        
        # Buscar clasificaciones con FK pero sin cuenta_codigo
        clasificaciones_problema = AccountClassification.objects.filter(
            cliente_id=CLIENTE_ID,
            cuenta__isnull=False,  # Tienen FK
            cuenta_codigo__in=['', None]  # Pero no tienen codigo o está vacío
        )
        
        total_problema = clasificaciones_problema.count()
        print(f"🔍 Clasificaciones con FK sin cuenta_codigo: {total_problema}")
        
        if total_problema == 0:
            print("✅ No hay clasificaciones que necesiten corrección.")
            return
        
        # Mostrar ejemplos
        print("\n📋 Primeras 5 clasificaciones a corregir:")
        for i, c in enumerate(clasificaciones_problema[:5], 1):
            print(f"  {i}. ID={c.id}, cuenta_id={c.cuenta_id}, cuenta.codigo='{c.cuenta.codigo}', cuenta_codigo='{c.cuenta_codigo}'")
        
        if total_problema > 5:
            print(f"  ... y {total_problema - 5} más")
        
        print(f"\n🚀 Procediendo a corregir {total_problema} clasificaciones...")
        
        # Corregir las clasificaciones
        corregidas = 0
        errores = 0
        
        for clasificacion in clasificaciones_problema:
            try:
                # Asignar el código de la cuenta FK al campo cuenta_codigo
                clasificacion.cuenta_codigo = clasificacion.cuenta.codigo
                clasificacion.save(update_fields=['cuenta_codigo'])
                corregidas += 1
                
                if corregidas <= 5:  # Mostrar solo las primeras 5
                    print(f"  ✓ ID={clasificacion.id}: cuenta_codigo = '{clasificacion.cuenta.codigo}'")
                
            except Exception as e:
                errores += 1
                print(f"  ❌ Error en ID={clasificacion.id}: {e}")
        
        print(f"\n📊 Resultado:")
        print(f"  ✅ Corregidas: {corregidas}")
        print(f"  ❌ Errores: {errores}")
        print(f"  📈 Total procesadas: {corregidas + errores}")
        
        # Verificación final
        clasificaciones_verificacion = AccountClassification.objects.filter(
            cliente_id=CLIENTE_ID,
            cuenta__isnull=False,
            cuenta_codigo__in=['', None]
        ).count()
        
        print(f"\n🔍 Verificación final:")
        print(f"  Clasificaciones FK sin cuenta_codigo restantes: {clasificaciones_verificacion}")
        
        if clasificaciones_verificacion == 0:
            print("🎉 ¡Corrección completada exitosamente!")
            print("   El modal ahora debería mostrar todas las clasificaciones.")
        else:
            print("⚠️  Aún quedan clasificaciones sin corregir.")
        
        # Mostrar estadísticas finales del cliente
        total_clasificaciones = AccountClassification.objects.filter(cliente_id=CLIENTE_ID).count()
        con_fk = AccountClassification.objects.filter(cliente_id=CLIENTE_ID, cuenta__isnull=False).count()
        temporales = AccountClassification.objects.filter(cliente_id=CLIENTE_ID, cuenta__isnull=True).count()
        
        print(f"\n📈 Estadísticas finales cliente {cliente.nombre}:")
        print(f"  Total clasificaciones: {total_clasificaciones}")
        print(f"  Con FK: {con_fk}")
        print(f"  Temporales: {temporales}")
        
    except Cliente.DoesNotExist:
        print(f"❌ Error: Cliente con ID={CLIENTE_ID} no encontrado.")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
