"""
Script para generar archivo Excel de prueba para Flujo 5: Ausentismos/Incidencias
Genera 6 registros con diferentes tipos de ausentismo
"""

import pandas as pd
from datetime import datetime, timedelta

# Datos de prueba: 6 incidencias con diferentes tipos de ausentismo
data = {
    'Rut': [
        '19111111-1',
        '19222222-2',
        '19333333-3',
        '19444444-4',
        '19555555-5',
        '19666666-6'
    ],
    'Nombre': [
        'Juan Carlos Pérez López',
        'María Francisca González Muñoz',
        'Pedro Antonio Silva Rojas',
        'Ana María Torres Castro',
        'Carlos Alberto Ramírez Flores',
        'Sofía Isabel Morales Vega'
    ],
    'Fecha Inicio Ausencia': [
        datetime(2025, 10, 1),   # 01/10/2025
        datetime(2025, 10, 5),   # 05/10/2025
        datetime(2025, 10, 10),  # 10/10/2025
        datetime(2025, 10, 15),  # 15/10/2025
        datetime(2025, 10, 20),  # 20/10/2025
        datetime(2025, 10, 25),  # 25/10/2025
    ],
    'Fecha Fin Ausencia': [
        datetime(2025, 10, 3),   # 3 días
        datetime(2025, 10, 7),   # 3 días
        datetime(2025, 10, 14),  # 5 días
        datetime(2025, 10, 16),  # 2 días
        datetime(2025, 10, 24),  # 5 días
        datetime(2025, 10, 27),  # 3 días
    ],
    'Dias': [3, 3, 5, 2, 5, 3],
    'Tipo Ausentismo': [
        'Licencia Médica',
        'Vacaciones',
        'Permiso Sin Goce de Sueldo',
        'Permiso Administrativo',
        'Licencia Médica',
        'Capacitación'
    ]
}

# Crear DataFrame
df = pd.DataFrame(data)

# Guardar como Excel
output_path = '/tmp/incidencias_smoke_test.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"✅ Archivo generado: {output_path}")
print(f"📊 {len(df)} registros de incidencias creados")
print("\n📋 Contenido:")
for i, row in df.iterrows():
    print(f"{i+1}. {row['Rut']} - {row['Nombre']}")
    print(f"   Ausencia: {row['Fecha Inicio Ausencia'].strftime('%d/%m/%Y')} - {row['Fecha Fin Ausencia'].strftime('%d/%m/%Y')} ({row['Dias']} días)")
    print(f"   Tipo: {row['Tipo Ausentismo']}")
