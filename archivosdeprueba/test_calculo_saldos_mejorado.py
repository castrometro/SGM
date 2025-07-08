#!/usr/bin/env python3
"""
Script de prueba para validar el cálculo de saldos mejorado.
Simula el comportamiento del cálculo usando el modelo AperturaCuenta correcto.
"""

import sys
import os
from decimal import Decimal

# Agregar el path del proyecto
sys.path.append('/root/SGM/backend')

def test_calculo_saldos_mejorado():
    """
    Función de prueba para validar el cálculo de saldos con el modelo correcto.
    """
    print("🧪 PRUEBA DEL CÁLCULO DE SALDOS MEJORADO")
    print("=" * 60)
    
    # Simular datos de ejemplo
    cuentas_ejemplo = [
        {'codigo': '1101', 'nombre': 'Caja', 'naturaleza': 'activo'},
        {'codigo': '1102', 'nombre': 'Banco', 'naturaleza': 'activo'},
        {'codigo': '2101', 'nombre': 'Proveedores', 'naturaleza': 'pasivo'},
        {'codigo': '3101', 'nombre': 'Capital', 'naturaleza': 'patrimonio'},
        {'codigo': '4101', 'nombre': 'Ventas', 'naturaleza': 'ingreso'},
        {'codigo': '5101', 'nombre': 'Gastos Admin', 'naturaleza': 'gasto'},
    ]
    
    # Simular apertura de cuentas (campo saldo_anterior del modelo AperturaCuenta)
    apertura_ejemplo = {
        '1101': Decimal('10000.00'),    # Caja con saldo inicial
        '1102': Decimal('50000.00'),    # Banco con saldo inicial
        '2101': Decimal('15000.00'),    # Proveedores con saldo inicial
        '3101': Decimal('45000.00'),    # Capital con saldo inicial
        '4101': Decimal('0.00'),        # Ventas sin saldo inicial
        '5101': Decimal('0.00'),        # Gastos sin saldo inicial
    }
    
    # Simular movimientos del período
    movimientos_ejemplo = {
        '1101': {'debe': Decimal('5000.00'), 'haber': Decimal('8000.00')},
        '1102': {'debe': Decimal('20000.00'), 'haber': Decimal('12000.00')},
        '2101': {'debe': Decimal('5000.00'), 'haber': Decimal('10000.00')},
        '3101': {'debe': Decimal('0.00'), 'haber': Decimal('0.00')},
        '4101': {'debe': Decimal('0.00'), 'haber': Decimal('25000.00')},
        '5101': {'debe': Decimal('15000.00'), 'haber': Decimal('2000.00')},
    }
    
    print("📋 CALCULANDO SALDOS FINALES:")
    print("-" * 60)
    
    saldos_calculados = {}
    
    for cuenta in cuentas_ejemplo:
        codigo = cuenta['codigo']
        nombre = cuenta['nombre']
        naturaleza = cuenta['naturaleza']
        
        # Obtener saldo inicial (campo saldo_anterior del modelo)
        saldo_inicial = apertura_ejemplo.get(codigo, Decimal('0'))
        
        # Obtener movimientos
        movs = movimientos_ejemplo.get(codigo, {'debe': Decimal('0'), 'haber': Decimal('0')})
        debe_movimientos = movs['debe']
        haber_movimientos = movs['haber']
        
        # =================== NUEVA LÓGICA DE CÁLCULO UNIVERSAL ===================
        # Fórmula universal: Saldo Final = Saldo inicial + (Debe Total - Haber Total)
        saldo_final = saldo_inicial + debe_movimientos - haber_movimientos
        
        saldos_calculados[codigo] = {
            'saldo_final': saldo_final,
            'naturaleza': naturaleza
        }
        
        print(f"💰 {codigo} - {nombre} ({naturaleza}):")
        print(f"   📅 Saldo Inicial (saldo_anterior): ${saldo_inicial:,.2f}")
        print(f"   📊 Movimientos del Período:")
        print(f"      - Debe: ${debe_movimientos:,.2f}")
        print(f"      - Haber: ${haber_movimientos:,.2f}")
        print(f"   🏁 Cálculo Final (Fórmula Universal):")
        print(f"      - Fórmula: Saldo Inicial + (Debe Total - Haber Total)")
        print(f"      - Cálculo: ${saldo_inicial:,.2f} + (${debe_movimientos:,.2f} - ${haber_movimientos:,.2f})")
        print(f"      - Resultado: ${saldo_inicial:,.2f} + ${debe_movimientos - haber_movimientos:,.2f} = ${saldo_final:,.2f}")
        print(f"   ✅ Saldo Final: ${saldo_final:,.2f}")
        print("-" * 40)
    
    # Verificar balance
    print("\n⚖️  VERIFICACIÓN DE BALANCE:")
    print("=" * 60)
    
    activos = saldos_calculados['1101']['saldo_final'] + saldos_calculados['1102']['saldo_final']
    pasivos = saldos_calculados['2101']['saldo_final']
    patrimonio = saldos_calculados['3101']['saldo_final']
    ingresos = saldos_calculados['4101']['saldo_final']
    gastos = saldos_calculados['5101']['saldo_final']
    
    print(f"📊 SALDOS FINALES POR NATURALEZA:")
    print(f"   Activos: ${activos:,.2f}")
    print(f"   Pasivos: ${pasivos:,.2f}")
    print(f"   Patrimonio: ${patrimonio:,.2f}")
    print(f"   Ingresos: ${ingresos:,.2f}")
    print(f"   Gastos: ${gastos:,.2f}")
    
    # Balance contable básico
    resultado = ingresos - gastos
    patrimonio_ajustado = patrimonio + resultado
    balance_activos = activos
    balance_pasivo_patrimonio = pasivos + patrimonio_ajustado
    
    print(f"\n📈 ESTADO DE RESULTADOS:")
    print(f"   Ingresos: ${ingresos:,.2f}")
    print(f"   Gastos: ${gastos:,.2f}")
    print(f"   Resultado: ${resultado:,.2f}")
    
    print(f"\n🏦 ESTADO DE SITUACIÓN FINANCIERA:")
    print(f"   Activos: ${balance_activos:,.2f}")
    print(f"   Pasivos: ${pasivos:,.2f}")
    print(f"   Patrimonio (inicial): ${patrimonio:,.2f}")
    print(f"   Patrimonio (ajustado): ${patrimonio_ajustado:,.2f}")
    print(f"   Total Pasivos + Patrimonio: ${balance_pasivo_patrimonio:,.2f}")
    
    diferencia = balance_activos - balance_pasivo_patrimonio
    print(f"\n⚖️  VERIFICACIÓN FINAL:")
    print(f"   Activos: ${balance_activos:,.2f}")
    print(f"   Pasivos + Patrimonio: ${balance_pasivo_patrimonio:,.2f}")
    print(f"   Diferencia: ${diferencia:,.2f}")
    
    if abs(diferencia) <= Decimal('1.00'):
        print("   ✅ BALANCE CUADRADO")
    else:
        print("   ❌ BALANCE NO CUADRA")
    
    print("\n🎉 PRUEBA COMPLETADA")
    print("=" * 60)
    
    return {
        'saldos': saldos_calculados,
        'balance_cuadrado': abs(diferencia) <= Decimal('1.00'),
        'activos': activos,
        'pasivos': pasivos,
        'patrimonio': patrimonio_ajustado,
        'resultado': resultado
    }

if __name__ == "__main__":
    resultado = test_calculo_saldos_mejorado()
    print(f"\n🏆 RESULTADO DE LA PRUEBA:")
    print(f"   Balance cuadrado: {resultado['balance_cuadrado']}")
    print(f"   Activos totales: ${resultado['activos']:,.2f}")
    print(f"   Pasivos totales: ${resultado['pasivos']:,.2f}")
    print(f"   Patrimonio total: ${resultado['patrimonio']:,.2f}")
    print(f"   Resultado del período: ${resultado['resultado']:,.2f}")
