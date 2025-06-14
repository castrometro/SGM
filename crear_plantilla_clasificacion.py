#!/usr/bin/env python3
"""
Script para crear plantilla Excel genérica para clasificación de cuentas
"""
import pandas as pd
from pathlib import Path

# Crear datos de ejemplo
data = {
    'Codigo_Cuenta': [
        '1.1.01.001',
        '1.1.01.002', 
        '1.1.02.001',
        '2.1.01.001',
        '2.1.01.002'
    ],
    'Tipo_Balance': [
        'Activo Corriente',
        'Activo Corriente',
        'Activo Corriente', 
        'Pasivo Corriente',
        'Pasivo Corriente'
    ],
    'Categoria_IFRS': [
        'Efectivo',
        'Cuentas por Cobrar',
        'Inventarios',
        'Cuentas por Pagar',
        'Provisiones'
    ],
    'Estado_Resultado': [
        '',
        '',
        '',
        '',
        ''
    ]
}

# Crear DataFrame
df = pd.DataFrame(data)

# Guardar en Excel
output_path = Path('backend/static/plantillas/plantilla_clasificacion.xlsx')
output_path.parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Clasificaciones')
    
    # Configurar el ancho de columnas
    worksheet = writer.sheets['Clasificaciones']
    for idx, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).str.len().max(), len(col))
        worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 30)

print(f"✅ Plantilla creada en: {output_path}")
print("📋 Estructura:")
print("   - Primera columna: Códigos de cuenta (cualquier nombre)")
print("   - Siguientes columnas: Sets de clasificación (cualquier nombre)")
print("   - El sistema tomará automáticamente la primera columna como cuentas")
