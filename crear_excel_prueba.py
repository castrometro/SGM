import pandas as pd
import random
import os

print('🧪 Creando archivo Excel de prueba realista...')

# Crear datos realistas
empleados = [f'Empleado {i}' for i in range(1, 51)]
ruts = [f'1{random.randint(1000000, 9999999)}-{random.randint(0, 9)}' for _ in range(50)]
centros_costo = ['CC001', 'CC002', 'CC003', 'CC100', 'CC200']
tipos_gasto = ['Combustible', 'Alimentacion', 'Transporte', 'Hospedaje', 'Otros']

data = []
for i in range(1500):  # 1500 registros
    data.append({
        'Fecha': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
        'RUT': random.choice(ruts),
        'Nombre': random.choice(empleados),
        'Centro_Costo': random.choice(centros_costo),
        'Tipo_Gasto': random.choice(tipos_gasto),
        'Monto': random.randint(5000, 50000),
        'Descripcion': f'Gasto {i+1} - descripcion detallada para el registro',
        'Proveedor': f'Proveedor {random.randint(1, 20)} Ltda.',
        'Numero_Documento': f'DOC{random.randint(100000, 999999)}'
    })

df = pd.DataFrame(data)
archivo = 'test_rindegastos_1500.xlsx'
df.to_excel(archivo, index=False)

size_mb = os.path.getsize(archivo) / (1024 * 1024)
print(f'✅ Archivo creado: {archivo}')
print(f'📊 {len(df)} registros')
print(f'💾 {size_mb:.2f} MB')
print(f'💰 Monto total: ${df["Monto"].sum():,.0f}')
print(f'📁 Archivo listo para el test de carga')