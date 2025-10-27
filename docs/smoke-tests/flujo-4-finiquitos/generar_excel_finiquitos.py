#!/usr/bin/env python3
"""
Generador de archivo Excel de prueba para Flujo 4: Finiquitos
Crea un archivo con datos de ejemplo para smoke testing
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def generar_excel_finiquitos():
    """Genera archivo Excel con datos de prueba de finiquitos"""
    
    # Datos de prueba: 5 finiquitos
    datos = [
        {
            'Rut': '19111111-1',
            'Nombre': 'Juan Carlos Pérez López',
            'Fecha Retiro': datetime(2025, 10, 31),  # Fin de mes
            'Motivo': 'Renuncia Voluntaria'
        },
        {
            'Rut': '19222222-2',
            'Nombre': 'María Francisca González Muñoz',
            'Fecha Retiro': datetime(2025, 10, 15),  # Mitad de mes
            'Motivo': 'Término de Contrato'
        },
        {
            'Rut': '19333333-3',
            'Nombre': 'Pedro Antonio Silva Rojas',
            'Fecha Retiro': datetime(2025, 10, 20),
            'Motivo': 'Mutuo Acuerdo'
        },
        {
            'Rut': '19444444-4',
            'Nombre': 'Ana María Torres Castro',
            'Fecha Retiro': datetime(2025, 10, 10),
            'Motivo': 'Necesidades de la Empresa'
        },
        {
            'Rut': '19555555-5',
            'Nombre': 'Carlos Alberto Ramírez Flores',
            'Fecha Retiro': datetime(2025, 10, 25),
            'Motivo': 'Renuncia Voluntaria'
        }
    ]
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    
    # Formatear fechas como DD/MM/YYYY
    df['Fecha Retiro'] = pd.to_datetime(df['Fecha Retiro']).dt.strftime('%d/%m/%Y')
    
    # Guardar Excel
    output_dir = Path(__file__).parent
    output_file = output_dir / 'finiquitos_smoke_test.xlsx'
    
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"✅ Archivo generado: {output_file}")
    print(f"📊 Total de registros: {len(df)}")
    print("\n📋 Estructura del archivo:")
    print(f"   • Columnas: {list(df.columns)}")
    print(f"   • Filas de datos: {len(df)}")
    print("\n🎯 Datos de prueba:")
    for idx, row in df.iterrows():
        print(f"   {idx + 1}. {row['Rut']} - {row['Nombre']}")
        print(f"      Fecha: {row['Fecha Retiro']}, Motivo: {row['Motivo']}")
    
    return output_file

if __name__ == '__main__':
    print("🔧 Generando archivo de prueba para Flujo 4: Finiquitos\n")
    generar_excel_finiquitos()
    print("\n✨ Generación completada")
