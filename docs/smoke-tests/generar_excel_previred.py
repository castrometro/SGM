"""
Script para generar un Excel de prueba en formato Previred estándar
"""
import pandas as pd
from datetime import date

# Datos de prueba - 5 empleados con columnas obligatorias Previred
empleados = []

ruts = [
    "11111111-1",
    "22222222-2",
    "33333333-3",
    "44444444-4",
    "55555555-5"
]

datos_empleados = [
    {"nombre": "JUAN", "ape_pat": "PEREZ", "ape_mat": "GONZALEZ", "cargo": "ANALISTA", "centro": "CC-100", "area": "OPERACIONES"},
    {"nombre": "MARIA", "ape_pat": "LOPEZ", "ape_mat": "SILVA", "cargo": "CONTADOR", "centro": "CC-101", "area": "FINANZAS"},
    {"nombre": "PEDRO", "ape_pat": "RODRIGUEZ", "ape_mat": "MARTINEZ", "cargo": "SENIOR", "centro": "CC-102", "area": "OPERACIONES"},
    {"nombre": "ANA", "ape_pat": "GARCIA", "ape_mat": "FERNANDEZ", "cargo": "ASISTENTE", "centro": "CC-103", "area": "ADMINISTRACION"},
    {"nombre": "CARLOS", "ape_pat": "SANCHEZ", "ape_mat": "TORRES", "cargo": "GERENTE", "centro": "CC-104", "area": "ADMINISTRACION"}
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

for i, (rut, datos) in enumerate(zip(ruts, datos_empleados)):
    fila = {
        # COLUMNAS OBLIGATORIAS PREVIRED
        "Año": 2025,
        "Mes": 10,
        "Rut de la Empresa": "77777777-7",
        "Rut del Trabajador": rut,
        "Nombre": datos["nombre"],
        "Apellido Paterno": datos["ape_pat"],
        "Apellido Materno": datos["ape_mat"],
        # COLUMNAS ADICIONALES
        "CARGO": datos["cargo"],
        "CENTRO DE COSTO": datos["centro"],
        "AREA": datos["area"],
    }
    
    # Agregar conceptos
    for concepto, valores in conceptos.items():
        fila[concepto] = valores[i]
    
    empleados.append(fila)

# Crear DataFrame
df = pd.DataFrame(empleados)

# Guardar Excel
output_path = "/tmp/libro_remuneraciones_previred.xlsx"
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"✅ Excel generado: {output_path}")
print(f"📊 Empleados: {len(empleados)}")
print(f"📋 Columnas: {len(df.columns)}")
print(f"📌 Columnas obligatorias Previred: Año, Mes, Rut de la Empresa, Rut del Trabajador, Nombre, Apellido Paterno, Apellido Materno")
print(f"\n📄 Primeras columnas:")
print(df.columns.tolist()[:10])
