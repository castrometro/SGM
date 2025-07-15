#!/usr/bin/env python3
"""
Script para corregir clasificaciones huérfanas que tienen cuenta=NULL
pero sí tienen cuenta_codigo que coincide con cuentas reales existentes
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import transaction
from contabilidad.models import AccountClassification, CuentaContable
import django.db.models as models


def main():
    print("=== REPARACIÓN DE CLASIFICACIONES HUÉRFANAS ===")
    
    # 1. Buscar clasificaciones con cuenta=NULL pero con cuenta_codigo
    clasificaciones_huerfanas = AccountClassification.objects.filter(
        cuenta__isnull=True,
        cuenta_codigo__isnull=False
    ).exclude(cuenta_codigo='')
    
    print(f"🔍 Encontradas {clasificaciones_huerfanas.count()} clasificaciones huérfanas")
    
    # 2. Agrupar por cliente y código para optimizar
    codigos_por_cliente = {}
    for cls in clasificaciones_huerfanas:
        cliente_id = cls.cliente_id
        if cliente_id not in codigos_por_cliente:
            codigos_por_cliente[cliente_id] = set()
        codigos_por_cliente[cliente_id].add(cls.cuenta_codigo)
    
    reparadas = 0
    no_encontradas = 0
    
    # 3. Para cada cliente, buscar las cuentas que coinciden
    for cliente_id, codigos in codigos_por_cliente.items():
        print(f"\n📋 Cliente ID {cliente_id}: {len(codigos)} códigos únicos")
        
        # Buscar todas las cuentas de este cliente que coinciden con los códigos
        cuentas_existentes = CuentaContable.objects.filter(
            cliente_id=cliente_id,
            codigo__in=codigos
        )
        
        # Crear mapa de código -> cuenta_id
        mapa_codigo_cuenta = {cuenta.codigo: cuenta.id for cuenta in cuentas_existentes}
        
        print(f"   ✅ Encontradas {len(mapa_codigo_cuenta)} cuentas reales de {len(codigos)} códigos")
        
        # 4. Actualizar clasificaciones de este cliente
        clasificaciones_cliente = clasificaciones_huerfanas.filter(cliente_id=cliente_id)
        
        with transaction.atomic():
            for cls in clasificaciones_cliente:
                if cls.cuenta_codigo in mapa_codigo_cuenta:
                    cuenta_id = mapa_codigo_cuenta[cls.cuenta_codigo]
                    cls.cuenta_id = cuenta_id
                    cls.save(update_fields=['cuenta_id'])
                    reparadas += 1
                    
                    if reparadas <= 10:  # Solo mostrar las primeras 10
                        print(f"   🔧 Reparada: ID {cls.id}, código '{cls.cuenta_codigo}' -> cuenta_id {cuenta_id}")
                else:
                    no_encontradas += 1
                    if no_encontradas <= 5:  # Solo mostrar las primeras 5
                        print(f"   ❌ No encontrada: código '{cls.cuenta_codigo}'")
    
    print(f"\n=== RESUMEN ===")
    print(f"✅ Clasificaciones reparadas: {reparadas}")
    print(f"❌ Códigos no encontrados: {no_encontradas}")
    print(f"📊 Total procesadas: {reparadas + no_encontradas}")
    
    # 5. Verificar resultado
    clasificaciones_aun_huerfanas = AccountClassification.objects.filter(
        cuenta__isnull=True,
        cuenta_codigo__isnull=False
    ).exclude(cuenta_codigo='').count()
    
    print(f"🔍 Clasificaciones aún huérfanas: {clasificaciones_aun_huerfanas}")
    
    if clasificaciones_aun_huerfanas == 0:
        print("🎉 ¡TODAS LAS CLASIFICACIONES REPARADAS EXITOSAMENTE!")
    else:
        print("⚠️  Aún quedan clasificaciones huérfanas por revisar")


if __name__ == "__main__":
    main()
