"""
Script para generar un Excel de prueba para el Libro de Remuneraciones
"""
import pandas as pd
from datetime import date

# Datos de prueba - 5 empleados con 10 conceptos cada uno
empleados = []

ruts = [
    "11111111-1",
    "22222222-2",
    "33333333-3",
    "44444444-4",
    "55555555-5"
]

nombres = [
    "JUAN PEREZ GONZALEZ",
    "MARIA LOPEZ SILVA",
    "PEDRO RODRIGUEZ MARTINEZ",
    "ANA GARCIA FERNANDEZ",
    "CARLOS SANCHEZ TORRES"
]

# Conceptos de nómina típicos
conceptos = {
    "SUELDO BASE": [1500000, 1200000, 1800000, 1000000, 2000000],
    "BONO PRODUCTIVIDAD": [150000, 120000, 180000, 100000, 200000],
    "COLACION": [50000, 50000, 50000, 50000, 50000],
    "MOVILIZACION": [30000, 30000, 30000, 30000, 30000],
    "GRATIFICACION": [100000, 80000, 120000, 70000, 150000],
    "AFP": [-180000, -144000, -216000, -120000, -240000],
    "SALUD": [-105000, -84000, -126000, -70000, -140000],
    "IMPUESTO": [-75000, -60000, -90000, -50000, -100000],
    "ANTICIPO": [-50000, 0, -100000, 0, -150000],
    "LIQUIDO A PAGAR": [1420000, 1192000, 1678000, 1010000, 1800000]
}

for i, (rut, nombre) in enumerate(zip(ruts, nombres)):
    fila = {
        "RUT": rut,
        "NOMBRE COMPLETO": nombre,
        "CARGO": "ANALISTA" if i < 2 else "SENIOR" if i < 4 else "GERENTE",
        "CENTRO DE COSTO": f"CC-{100 + i}",
        "AREA": "OPERACIONES" if i < 3 else "ADMINISTRACION",
    }
    
    # Agregar conceptos
    for concepto, valores in conceptos.items():
        fila[concepto] = valores[i]
    
    empleados.append(fila)

# Crear DataFrame
df = pd.DataFrame(empleados)

# Guardar Excel
output_file = "/tmp/libro_remuneraciones_smoke_test.xlsx"
df.to_excel(output_file, index=False, sheet_name="Nomina")

print(f"✅ Excel generado: {output_file}")
print(f"📊 Empleados: {len(empleados)}")
print(f"📋 Conceptos: {len(conceptos)}")
print(f"📄 Columnas totales: {len(df.columns)}")
print("\nPrimeras 2 filas:")
print(df.head(2).to_string())
