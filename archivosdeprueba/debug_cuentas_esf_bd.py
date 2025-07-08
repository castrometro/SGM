#!/usr/bin/env python
"""
Script para analizar todas las cuentas ESF en la base de datos
y entender por qué el saldo anterior ESF es tan alto.
"""

import os
import sys
import logging
from decimal import Decimal
from collections import defaultdict

# Configurar el entorno Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')

import django
django.setup()

from django.db import transaction
from contabilidad.models import (
    CuentaContable, AccountClassification, ClasificacionSet, 
    ClasificacionOption, AperturaCuenta, CierreContable, Cliente
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analizar_cuentas_esf_bd(cliente_id=None):
    """Analiza todas las cuentas ESF en la base de datos"""
    
    print(f"\n{'='*80}")
    print(f"ANÁLISIS DE CUENTAS ESF EN LA BASE DE DATOS")
    print(f"{'='*80}")
    
    # Si no se especifica cliente, usar el primero disponible
    if cliente_id is None:
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No se encontró ningún cliente en la base de datos")
            return
        cliente_id = cliente.id
    else:
        cliente = Cliente.objects.get(id=cliente_id)
    
    print(f"👤 Cliente: {cliente.nombre} (ID: {cliente_id})")
    
    # Buscar todas las cuentas ESF
    cuentas_esf = CuentaContable.objects.filter(
        cliente_id=cliente_id,
        accountclassification__set_clas__nombre='ESF',
        accountclassification__opcion__valor='1'
    ).exclude(
        accountclassification__set_clas__nombre='ERI',
        accountclassification__opcion__valor='1'
    ).distinct()
    
    print(f"📊 Total cuentas ESF encontradas: {cuentas_esf.count()}")
    
    # Analizar cada cuenta ESF
    cuentas_con_saldo = []
    cuentas_sin_saldo = []
    total_saldo_anterior = Decimal('0')
    
    # Buscar el último cierre
    ultimo_cierre = CierreContable.objects.filter(
        cliente_id=cliente_id
    ).order_by('-fecha_cierre').first()
    
    if ultimo_cierre:
        print(f"📅 Último cierre encontrado: {ultimo_cierre.fecha_cierre} (ID: {ultimo_cierre.id})")
        
        # Buscar aperturas de cuentas para este cierre
        aperturas = AperturaCuenta.objects.filter(
            cierre=ultimo_cierre,
            cuenta__in=cuentas_esf
        ).select_related('cuenta')
        
        print(f"🔍 Aperturas ESF encontradas para este cierre: {aperturas.count()}")
        
        for apertura in aperturas:
            saldo = apertura.saldo_anterior or Decimal('0')
            total_saldo_anterior += saldo
            
            cuenta_info = {
                'codigo': apertura.cuenta.codigo,
                'nombre': apertura.cuenta.nombre,
                'saldo_anterior': saldo,
                'es_patrimonio': 'patrimonio' in (apertura.cuenta.nombre or '').lower() or 'capital' in (apertura.cuenta.nombre or '').lower(),
                'tiene_apertura': True
            }
            
            if saldo != 0:
                cuentas_con_saldo.append(cuenta_info)
            else:
                cuentas_sin_saldo.append(cuenta_info)
    
    # Buscar cuentas ESF que no tienen apertura
    cuentas_con_apertura_ids = [a.cuenta.id for a in aperturas] if ultimo_cierre else []
    cuentas_sin_apertura = cuentas_esf.exclude(id__in=cuentas_con_apertura_ids)
    
    for cuenta in cuentas_sin_apertura:
        cuenta_info = {
            'codigo': cuenta.codigo,
            'nombre': cuenta.nombre,
            'saldo_anterior': 'N/A',
            'es_patrimonio': 'patrimonio' in (cuenta.nombre or '').lower() or 'capital' in (cuenta.nombre or '').lower(),
            'tiene_apertura': False
        }
        cuentas_sin_saldo.append(cuenta_info)
    
    # Mostrar resultados
    print(f"\n📋 RESUMEN DE ANÁLISIS:")
    print(f"  - Total cuentas ESF en BD: {cuentas_esf.count()}")
    print(f"  - Cuentas ESF con saldo anterior: {len(cuentas_con_saldo)}")
    print(f"  - Cuentas ESF sin saldo anterior: {len(cuentas_sin_saldo)}")
    print(f"  - Total saldo anterior ESF: ${total_saldo_anterior:,.2f}")
    
    # Mostrar cuentas con saldo anterior
    if cuentas_con_saldo:
        print(f"\n✅ CUENTAS ESF CON SALDO ANTERIOR:")
        print(f"{'Código':<15} {'Saldo Anterior':<15} {'Patrimonio':<10} {'Nombre'}")
        print("-" * 100)
        
        # Ordenar por saldo absoluto descendente
        cuentas_ordenadas = sorted(cuentas_con_saldo, key=lambda x: abs(x['saldo_anterior']), reverse=True)
        
        for cuenta in cuentas_ordenadas:
            patrimonio_mark = "SÍ" if cuenta['es_patrimonio'] else "NO"
            print(f"{cuenta['codigo']:<15} ${cuenta['saldo_anterior']:>12,.2f} {patrimonio_mark:<10} {cuenta['nombre']}")
    
    # Mostrar top 5 cuentas con mayor saldo
    if cuentas_con_saldo:
        print(f"\n🔝 TOP 5 CUENTAS ESF CON MAYOR SALDO ABSOLUTO:")
        cuentas_top = sorted(cuentas_con_saldo, key=lambda x: abs(x['saldo_anterior']), reverse=True)[:5]
        for i, cuenta in enumerate(cuentas_top):
            print(f"{i+1}. {cuenta['codigo']} - ${cuenta['saldo_anterior']:,.2f} - {cuenta['nombre']}")
    
    # Análisis especial de cuentas patrimonio
    cuentas_patrimonio = [c for c in cuentas_con_saldo if c['es_patrimonio']]
    if cuentas_patrimonio:
        print(f"\n🏦 CUENTAS DE PATRIMONIO CON SALDO ESF:")
        total_patrimonio = sum(c['saldo_anterior'] for c in cuentas_patrimonio)
        print(f"  Total cuentas patrimonio: {len(cuentas_patrimonio)}")
        print(f"  Saldo total patrimonio: ${total_patrimonio:,.2f}")
        print(f"  Porcentaje del total ESF: {(total_patrimonio / total_saldo_anterior * 100):.1f}%")
        
        for cuenta in cuentas_patrimonio:
            print(f"    - {cuenta['codigo']}: ${cuenta['saldo_anterior']:,.2f} - {cuenta['nombre']}")
    
    # Mostrar cuentas sin saldo anterior
    if cuentas_sin_saldo:
        print(f"\n❌ CUENTAS ESF SIN SALDO ANTERIOR (primeras 10):")
        print(f"{'Código':<15} {'Tiene Apertura':<15} {'Patrimonio':<10} {'Nombre'}")
        print("-" * 100)
        
        for cuenta in cuentas_sin_saldo[:10]:
            apertura_mark = "SÍ" if cuenta['tiene_apertura'] else "NO"
            patrimonio_mark = "SÍ" if cuenta['es_patrimonio'] else "NO"
            print(f"{cuenta['codigo']:<15} {apertura_mark:<15} {patrimonio_mark:<10} {cuenta['nombre']}")
        
        if len(cuentas_sin_saldo) > 10:
            print(f"... y {len(cuentas_sin_saldo) - 10} más")
    
    # Buscar cuentas ERI para comparación
    cuentas_eri = CuentaContable.objects.filter(
        cliente_id=cliente_id,
        accountclassification__set_clas__nombre='ERI',
        accountclassification__opcion__valor='1'
    ).exclude(
        accountclassification__set_clas__nombre='ESF',
        accountclassification__opcion__valor='1'
    ).distinct()
    
    total_saldo_eri = Decimal('0')
    if ultimo_cierre:
        aperturas_eri = AperturaCuenta.objects.filter(
            cierre=ultimo_cierre,
            cuenta__in=cuentas_eri
        )
        total_saldo_eri = sum(a.saldo_anterior or Decimal('0') for a in aperturas_eri)
    
    print(f"\n🔄 COMPARACIÓN ESF vs ERI:")
    print(f"  - Total ESF: ${total_saldo_anterior:,.2f}")
    print(f"  - Total ERI: ${total_saldo_eri:,.2f}")
    print(f"  - Balance (ESF + ERI): ${total_saldo_anterior + total_saldo_eri:,.2f}")
    
    return {
        'total_cuentas_esf': cuentas_esf.count(),
        'cuentas_con_saldo': len(cuentas_con_saldo),
        'cuentas_sin_saldo': len(cuentas_sin_saldo),
        'total_saldo_anterior': total_saldo_anterior,
        'total_saldo_eri': total_saldo_eri,
        'balance_total': total_saldo_anterior + total_saldo_eri,
        'cuentas_patrimonio': len(cuentas_patrimonio) if cuentas_patrimonio else 0
    }

if __name__ == "__main__":
    cliente_id = None
    if len(sys.argv) > 1:
        cliente_id = int(sys.argv[1])
    
    print(f"Iniciando análisis de cuentas ESF...")
    if cliente_id:
        print(f"Cliente ID: {cliente_id}")
    else:
        print("Cliente ID: Auto-detectar")
    
    try:
        resultado = analizar_cuentas_esf_bd(cliente_id)
        print(f"\n✅ Análisis completado exitosamente")
        print(f"📊 Estadísticas finales: {resultado}")
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
