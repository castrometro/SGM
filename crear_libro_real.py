import pandas as pd
import numpy as np

# Crear estructura del libro de remuneraciones real
print("🏗️ Creando libro de remuneraciones con formato real...")

# Headers según el formato real especificado
headers = [
    'Rut del Trabajador',      # A
    'Nombre',                  # B  
    'Apellido Paterno',        # C
    'Apellido Materno',        # D
    'Centro de Costo',         # E
    'Cargo',                   # F
    'Fecha Ingreso',           # G
    'Sueldo Base',             # H - INICIA ITEMS REMUNERACIONES
    'Gratificación Legal',     # I
    'Bono de Producción',      # J
    'Horas Extras 50%',        # K
    'Horas Extras 100%',       # L
    'Asignación Familiar',     # M
    'Movilización',            # N
    'Colación',                # O
    'Descuento AFP',           # P
    'Descuento Salud',         # Q
    'Descuento Impuesto',      # R
    'Préstamo Empresa',        # S
    'Total Haberes',           # T
    'Total Descuentos',        # U
    'Líquido a Pagar'          # V
]

# Datos de empleados de prueba
empleados_data = [
    ['12345678-9', 'Juan Carlos', 'Pérez', 'González', 'Administración', 'Analista', '2023-01-15', 850000, 70833, 45000, 25000, 15000, 12500, 30000, 25000, 102000, 76500, 45000, 0, 1042833, 223500, 819333],
    ['87654321-K', 'María Elena', 'García', 'López', 'Ventas', 'Ejecutiva', '2022-06-10', 720000, 60000, 0, 18000, 22000, 8750, 25000, 20000, 86400, 64800, 32000, 25000, 853750, 208200, 645550],
    ['11111111-1', 'Pedro Antonio', 'Martínez', 'Silva', 'Producción', 'Supervisor', '2021-03-20', 950000, 79167, 60000, 35000, 28000, 15000, 35000, 30000, 114000, 85500, 52000, 0, 1182167, 251500, 930667],
    ['22222222-2', 'Ana Sofía', 'Rodríguez', 'Hernández', 'RRHH', 'Coordinadora', '2020-11-05', 680000, 56667, 0, 12000, 8000, 10000, 20000, 18000, 81600, 61200, 28000, 15000, 804667, 185800, 618867],
    ['33333333-3', 'Carlos Eduardo', 'Morales', 'Castro', 'IT', 'Desarrollador', '2023-08-12', 1100000, 91667, 75000, 40000, 35000, 20000, 40000, 35000, 132000, 99000, 68000, 0, 1361667, 299000, 1062667],
]

# Crear DataFrame
df = pd.DataFrame(empleados_data, columns=headers)

# Guardar como Excel
archivo_excel = '/root/SGM/libro_remuneraciones_real.xlsx'
df.to_excel(archivo_excel, index=False)

print(f"✅ Archivo creado: {archivo_excel}")
print(f"📊 Estructura:")
print(f"   - Headers empleados: A-D (Rut, Nombre, Apellidos)")
print(f"   - Items remuneraciones: H-V (desde Sueldo Base)")
print(f"   - Empleados: {len(empleados_data)} registros")
print(f"   - Columnas totales: {len(headers)}")

# Mostrar vista previa
print("\n📋 Vista previa:")
print(df[['Rut del Trabajador', 'Nombre', 'Apellido Paterno', 'Apellido Materno', 'Sueldo Base', 'Total Haberes', 'Líquido a Pagar']].head())
