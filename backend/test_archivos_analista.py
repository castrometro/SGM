# backend/test_archivos_analista.py
# Script de prueba para verificar las tareas del analista

import pandas as pd
import os
from datetime import datetime

def crear_archivo_finiquitos_test():
    """Crea un archivo Excel de prueba para finiquitos"""
    data = {
        'Rut': ['12345678-9', '98765432-1', '11111111-1'],
        'Nombre': ['Juan Pérez García', 'María González López', 'Carlos Rodriguez Silva'],
        'Fecha Retiro': ['2025-08-15', '2025-08-20', '2025-08-25'],
        'Motivo': ['Renuncia voluntaria', 'Término de contrato', 'Despido disciplinario']
    }
    
    df = pd.DataFrame(data)
    filename = 'test_finiquitos_analista.xlsx'
    df.to_excel(filename, index=False)
    print(f"✅ Archivo creado: {filename}")
    return filename

def crear_archivo_ausentismos_test():
    """Crea un archivo Excel de prueba para ausentismos"""
    data = {
        'Rut': ['12345678-9', '98765432-1', '11111111-1', '22222222-2'],
        'Nombre': ['Juan Pérez García', 'María González López', 'Carlos Rodriguez Silva', 'Ana Martínez Torres'],
        'Fecha Inicio Ausencia': ['2025-08-01', '2025-08-05', '2025-08-10', '2025-08-15'],
        'Fecha Fin Ausencia': ['2025-08-03', '2025-08-07', '2025-08-12', '2025-08-20'],
        'Dias': [3, 3, 3, 6],
        'Tipo de Ausentismo': ['Licencia Médica', 'Vacaciones', 'Permiso Personal', 'Licencia Maternal']
    }
    
    df = pd.DataFrame(data)
    filename = 'test_ausentismos_analista.xlsx'
    df.to_excel(filename, index=False)
    print(f"✅ Archivo creado: {filename}")
    return filename

def crear_archivo_ingresos_test():
    """Crea un archivo Excel de prueba para ingresos"""
    data = {
        'Rut': ['33333333-3', '44444444-4', '55555555-5'],
        'Nombre': ['Luis Morales Jiménez', 'Patricia Vargas Rojas', 'Roberto Castro Mendoza'],
        'Fecha Ingreso': ['2025-08-01', '2025-08-10', '2025-08-20']
    }
    
    df = pd.DataFrame(data)
    filename = 'test_ingresos_analista.xlsx'
    df.to_excel(filename, index=False)
    print(f"✅ Archivo creado: {filename}")
    return filename

if __name__ == "__main__":
    print("🧪 Creando archivos de prueba para analista...")
    
    # Crear archivos de prueba
    finiquitos_file = crear_archivo_finiquitos_test()
    ausentismos_file = crear_archivo_ausentismos_test()
    ingresos_file = crear_archivo_ingresos_test()
    
    print("\n📋 Archivos creados:")
    print(f"   - {finiquitos_file}")
    print(f"   - {ausentismos_file}")
    print(f"   - {ingresos_file}")
    
    print("\n📝 Para probar:")
    print("1. Sube estos archivos desde el frontend")
    print("2. Verifica que se procesen automáticamente")
    print("3. Revisa los datos en Django Admin")
    print("\n🔍 Paths para Django Admin:")
    print("   - /admin/payroll/finiquitos_analista_stg/")
    print("   - /admin/payroll/ausentismos_analista_stg/")
    print("   - /admin/payroll/ingresos_analista_stg/")
