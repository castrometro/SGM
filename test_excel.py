#!/usr/bin/env python3
import pandas as pd
import requests
import os

# Crear un Excel de prueba
data = {
    'Nombre': ['Juan Pérez', 'María García', 'Carlos López'],
    'Edad': [25, 30, 35],
    'Departamento': ['Ventas', 'Marketing', 'IT'],
    'Salario': [50000, 60000, 70000]
}

df = pd.DataFrame(data)
excel_file = '/root/SGM/empleados_prueba.xlsx'
df.to_excel(excel_file, index=False)

print(f"✅ Archivo Excel creado: {excel_file}")

# Probar el webhook de n8n
webhook_url = 'http://localhost:5678/webhook-test/upload-excel'

try:
    with open(excel_file, 'rb') as f:
        files = {'data': f}
        response = requests.post(webhook_url, files=files)
    
    print(f"🚀 Respuesta del webhook: {response.status_code}")
    if response.text:
        print(f"📝 Contenido: {response.text}")
        
except Exception as e:
    print(f"❌ Error al enviar archivo: {e}")
