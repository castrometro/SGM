#!/usr/bin/env python3
"""
Generador de Excel de Prueba - Ingresos (Flujo 3)

Genera un archivo Excel con datos de nuevos ingresos de empleados
para probar el procesamiento del sistema.

Uso:
    python generar_excel_ingresos.py
"""

import pandas as pd
from datetime import date, timedelta
import os

# Datos de prueba para Ingresos
ingresos = [
    {
        "Rut": "19111111-1",
        "Nombre": "Juan Carlos Pérez López",
        "Fecha Ingreso": date(2025, 10, 1)
    },
    {
        "Rut": "19222222-2",
        "Nombre": "María Francisca González Muñoz",
        "Fecha Ingreso": date(2025, 10, 5)
    },
    {
        "Rut": "19333333-3",
        "Nombre": "Pedro Antonio Silva Rojas",
        "Fecha Ingreso": date(2025, 10, 10)
    },
    {
        "Rut": "19444444-4",
        "Nombre": "Ana María Torres Castro",
        "Fecha Ingreso": date(2025, 10, 15)
    },
    {
        "Rut": "19555555-5",
        "Nombre": "Carlos Alberto Ramírez Flores",
        "Fecha Ingreso": date(2025, 10, 20)
    },
]

def generar_excel():
    """Genera el archivo Excel con datos de ingresos"""
    
    print("📝 Generando Excel de Ingresos...")
    print(f"   Registros: {len(ingresos)}")
    
    # Crear DataFrame
    df = pd.DataFrame(ingresos)
    
    # Nombre del archivo
    output_path = os.path.join(
        os.path.dirname(__file__), 
        "ingresos_smoke_test.xlsx"
    )
    
    # Guardar Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ingresos')
    
    # Obtener tamaño del archivo
    file_size = os.path.getsize(output_path)
    file_size_kb = file_size / 1024
    
    print(f"\n✅ Archivo generado exitosamente:")
    print(f"   Ubicación: {output_path}")
    print(f"   Tamaño: {file_size_kb:.1f} KB")
    print(f"\n📊 Contenido:")
    print(f"   • Ingresos: {len(ingresos)}")
    print(f"\n📋 Columnas:")
    print(f"   • Rut")
    print(f"   • Nombre")
    print(f"   • Fecha Ingreso")
    print(f"\n🎯 Listo para usar en pruebas")
    
    return output_path

if __name__ == "__main__":
    generar_excel()
