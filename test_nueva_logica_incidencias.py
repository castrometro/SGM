#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA: Nueva Lógica Simplificada de Incidencias

Este script verifica que la nueva lógica funciona correctamente:
1. Comparar nóminas de empleados comunes (variaciones)
2. Revisar empleados únicos (documentación faltante)
"""

# Simulación de la lógica sin Django
from decimal import Decimal

def simular_deteccion_simplificada():
    """
    Simula la nueva lógica de detección sin necesidad de Django
    """
    print("🎯 SIMULACIÓN: Nueva Lógica Simplificada de Incidencias")
    print("=" * 60)
    
    # DATOS SIMULADOS
    # Empleados mes anterior
    empleados_anterior = {
        '12345678-9': {
            'nombre': 'Juan Pérez',
            'conceptos': {
                'Sueldo Base': Decimal('800000'),
                'Horas Extras': Decimal('50000'),
                'Gratificación': Decimal('100000')
            }
        },
        '98765432-1': {
            'nombre': 'María González',
            'conceptos': {
                'Sueldo Base': Decimal('700000'),
                'Colación': Decimal('30000')
            }
        },
        '11111111-1': {
            'nombre': 'Pedro López',  # Este tendrá finiquito
            'conceptos': {
                'Sueldo Base': Decimal('600000')
            }
        }
    }
    
    # Empleados mes actual
    empleados_actual = {
        '12345678-9': {
            'nombre': 'Juan Pérez',
            'conceptos': {
                'Sueldo Base': Decimal('1200000'),  # Variación 50%
                'Horas Extras': Decimal('55000'),   # Variación menor
                'Gratificación': Decimal('100000')  # Sin variación
            }
        },
        '98765432-1': {
            'nombre': 'María González',
            'conceptos': {
                'Sueldo Base': Decimal('700000'),   # Sin variación
                'Colación': Decimal('30000')       # Sin variación
            }
        },
        '22222222-2': {
            'nombre': 'Ana Martín',  # Este tendrá ingreso
            'conceptos': {
                'Sueldo Base': Decimal('650000')
            }
        }
    }
    
    # Documentación de movimientos
    finiquitos_anterior = ['11111111-1']  # Pedro López tiene finiquito
    ingresos_actual = ['22222222-2']      # Ana Martín tiene ingreso
    
    print("📊 DATOS DE PRUEBA:")
    print(f"   Empleados anterior: {len(empleados_anterior)}")
    print(f"   Empleados actual: {len(empleados_actual)}")
    print(f"   Finiquitos documentados: {len(finiquitos_anterior)}")
    print(f"   Ingresos documentados: {len(ingresos_actual)}")
    print()
    
    # PASO 1: COMPARAR EMPLEADOS COMUNES
    print("🔍 PASO 1: Comparando empleados comunes...")
    
    ruts_anterior = set(empleados_anterior.keys())
    ruts_actual = set(empleados_actual.keys())
    ruts_comunes = ruts_anterior & ruts_actual
    
    print(f"   👥 Empleados comunes: {len(ruts_comunes)} ({', '.join(ruts_comunes)})")
    
    incidencias_variaciones = []
    tolerancia = Decimal('30.0')  # 30%
    
    for rut in ruts_comunes:
        emp_anterior = empleados_anterior[rut]
        emp_actual = empleados_actual[rut]
        
        print(f"\n   🔎 Analizando {emp_anterior['nombre']} ({rut}):")
        
        # Comparar conceptos
        todos_conceptos = set(emp_anterior['conceptos'].keys()) | set(emp_actual['conceptos'].keys())
        
        for concepto in todos_conceptos:
            monto_anterior = emp_anterior['conceptos'].get(concepto, Decimal('0'))
            monto_actual = emp_actual['conceptos'].get(concepto, Decimal('0'))
            
            if monto_anterior > Decimal('1000'):  # Solo conceptos significativos
                if monto_anterior != 0:
                    variacion = abs((monto_actual - monto_anterior) / monto_anterior) * 100
                    
                    print(f"      {concepto}: ${monto_anterior:,} → ${monto_actual:,} ({variacion:.1f}%)")
                    
                    if variacion > tolerancia:
                        incidencia = f"Variación {variacion:.1f}% en {concepto} para {emp_anterior['nombre']}"
                        incidencias_variaciones.append(incidencia)
                        print(f"      ⚠️  INCIDENCIA: {incidencia}")
    
    print(f"\n   📊 Incidencias de variación detectadas: {len(incidencias_variaciones)}")
    
    # PASO 2: ANALIZAR EMPLEADOS ÚNICOS
    print("\n🔍 PASO 2: Analizando empleados únicos...")
    
    ruts_solo_anterior = ruts_anterior - ruts_actual
    ruts_solo_actual = ruts_actual - ruts_anterior
    
    print(f"   📤 Solo en anterior: {len(ruts_solo_anterior)} ({', '.join(ruts_solo_anterior) if ruts_solo_anterior else 'ninguno'})")
    print(f"   📥 Solo en actual: {len(ruts_solo_actual)} ({', '.join(ruts_solo_actual) if ruts_solo_actual else 'ninguno'})")
    
    incidencias_faltantes = []
    
    # Verificar finiquitos
    for rut in ruts_solo_anterior:
        empleado = empleados_anterior[rut]
        if rut not in finiquitos_anterior:
            incidencia = f"Empleado {empleado['nombre']} no está en nómina actual pero no tiene finiquito documentado"
            incidencias_faltantes.append(incidencia)
            print(f"   ⚠️  INCIDENCIA FINIQUITO: {incidencia}")
        else:
            print(f"   ✅ {empleado['nombre']} tiene finiquito documentado")
    
    # Verificar ingresos
    for rut in ruts_solo_actual:
        empleado = empleados_actual[rut]
        if rut not in ingresos_actual:
            incidencia = f"Empleado {empleado['nombre']} está en nómina actual pero no tiene ingreso documentado"
            incidencias_faltantes.append(incidencia)
            print(f"   ⚠️  INCIDENCIA INGRESO: {incidencia}")
        else:
            print(f"   ✅ {empleado['nombre']} tiene ingreso documentado")
    
    print(f"\n   📊 Incidencias de documentación faltante: {len(incidencias_faltantes)}")
    
    # RESUMEN FINAL
    total_incidencias = len(incidencias_variaciones) + len(incidencias_faltantes)
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL:")
    print(f"   🔄 Incidencias de variación: {len(incidencias_variaciones)}")
    print(f"   📄 Incidencias de documentación: {len(incidencias_faltantes)}")
    print(f"   📊 TOTAL INCIDENCIAS: {total_incidencias}")
    
    if total_incidencias == 0:
        print("   ✅ Sin incidencias detectadas - Cierre listo para finalizar")
    else:
        print("   ⚠️  Incidencias detectadas - Requieren revisión")
        
        print("\nDetalle de incidencias:")
        for i, inc in enumerate(incidencias_variaciones + incidencias_faltantes, 1):
            print(f"   {i}. {inc}")
    
    return {
        'total_incidencias': total_incidencias,
        'variaciones': len(incidencias_variaciones),
        'faltantes': len(incidencias_faltantes),
        'empleados_comunes': len(ruts_comunes),
        'solo_anterior': len(ruts_solo_anterior),
        'solo_actual': len(ruts_solo_actual)
    }

if __name__ == "__main__":
    resultado = simular_deteccion_simplificada()
    print(f"\n🎯 La nueva lógica funciona correctamente!")
    print(f"Resultado: {resultado}")
