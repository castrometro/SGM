#!/usr/bin/env python
"""
Script para generar archivo Excel de prueba para Flujo 6: Novedades

Genera un archivo con:
- 6 empleados de prueba
- 4 columnas fijas: RUT, Nombre, Apellido Paterno, Apellido Materno
- 5 conceptos de remuneración: Sueldo Base, Bono Producción, Gratificación, Colación, Movilización
"""

import pandas as pd
from datetime import datetime
import os

def crear_excel_novedades():
    """Crea Excel de prueba para novedades"""
    
    # Datos de empleados (primeras 4 columnas fijas)
    data = {
        'RUT': [
            '12345678-9',
            '98765432-1',
            '11111111-1',
            '22222222-2',
            '33333333-3',
            '44444444-4',
        ],
        'Nombre': [
            'Juan',
            'María',
            'Pedro',
            'Ana',
            'Carlos',
            'Sofía',
        ],
        'Apellido Paterno': [
            'Pérez',
            'González',
            'Rodríguez',
            'Martínez',
            'López',
            'Fernández',
        ],
        'Apellido Materno': [
            'Silva',
            'Muñoz',
            'Soto',
            'Rojas',
            'Torres',
            'Vega',
        ],
        # Conceptos de novedades (columnas dinámicas)
        'Sueldo Base': [
            500000,
            600000,
            550000,
            580000,
            520000,
            590000,
        ],
        'Bono Producción': [
            50000,
            75000,
            60000,
            0,  # Ana no tiene bono este mes
            45000,
            80000,
        ],
        'Gratificación': [
            100000,
            120000,
            110000,
            115000,
            105000,
            125000,
        ],
        'Colación': [
            30000,
            30000,
            30000,
            30000,
            30000,
            30000,
        ],
        'Movilización': [
            20000,
            20000,
            20000,
            20000,
            20000,
            20000,
        ],
    }
    
    df = pd.DataFrame(data)
    
    # Crear directorio si no existe
    output_dir = '/root/SGM/docs/smoke-tests/flujo-6-novedades'
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'{output_dir}/novedades_prueba_{timestamp}.xlsx'
    df.to_excel(filename, index=False, engine='openpyxl')
    
    # Resumen
    print("="*70)
    print("✅ ARCHIVO EXCEL DE NOVEDADES GENERADO")
    print("="*70)
    print(f"📁 Archivo: {filename}")
    print(f"📊 Empleados: {len(df)}")
    print(f"📋 Columnas fijas: 4 (RUT, Nombre, Apellido Paterno, Apellido Materno)")
    print(f"💰 Conceptos: {len(df.columns) - 4}")
    print()
    print("Conceptos incluidos:")
    for col in df.columns[4:]:
        print(f"  - {col}")
    print()
    print("="*70)
    print("📄 PRIMERAS 3 FILAS:")
    print("="*70)
    print(df.head(3).to_string(index=False))
    print()
    print("="*70)
    print("💡 SIGUIENTE PASO:")
    print("="*70)
    print(f"1. Subir el archivo al frontend:")
    print(f"   http://172.17.11.18:5174/cierres/{{cierre_id}}")
    print(f"2. Procesar el archivo de novedades")
    print(f"3. Ejecutar script de verificación")
    print("="*70)
    
    return filename

if __name__ == '__main__':
    try:
        filename = crear_excel_novedades()
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        import traceback
        traceback.print_exc()
