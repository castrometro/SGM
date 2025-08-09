#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crear archivo Excel de prueba para Captura Masiva RindeGastos 
con formato de centros de costos XX-XXX
"""

import pandas as pd
from datetime import date, datetime
import random

# Datos de prueba
datos = [
    # Tipo Doc 33 con diferentes cantidades de CC
    ["Juan Pérez", "33", "Ñuñoa", "Viáticos", "2025-05-30T00:00:00", 15000.50, "USD", "Taxi aeropuerto", "Gastos de viaje", "01-003", "02-004", "-"],
    ["María García", "33", "Santiago", "Alimentación", "2025-06-15T00:00:00", 8500.75, "CLP", "Almuerzo cliente", "Comida de trabajo", "01-003", "-", "-"],
    ["Carlos López", "33", "Valparaíso", "Transporte", "2025-07-01T00:00:00", 12300.25, "CLP", "Combustible", "Traslado oficina", "01-003", "02-004", "03-005"],
    ["Ana Rodríguez", "33", "Concepción", "Hospedaje", "2025-07-20T00:00:00", 45000.00, "CLP", "Hotel noche", "Estadía trabajo", "-", "-", "-"],
    
    # Tipo Doc 34 con diferentes cantidades de CC  
    ["Luis Silva", "34", "La Serena", "Materiales", "2025-08-01T00:00:00", 25000.50, "CLP", "Papelería oficina", "Suministros", "04-006", "05-007", "-"],
    ["Carmen Díaz", "34", "Temuco", "Tecnología", "2025-08-05T00:00:00", 35000.00, "USD", "Software licencia", "Herramientas trabajo", "04-006", "-", "-"],
    ["Roberto Muñoz", "34", "Antofagasta", "Comunicaciones", "2025-08-10T00:00:00", 18500.25, "CLP", "Internet móvil", "Conectividad", "-", "-", "-"],
    
    # Tipo Doc 61 con diferentes cantidades de CC
    ["Patricia Vega", "61", "Puerto Montt", "Capacitación", "2025-08-15T00:00:00", 120000.00, "CLP", "Curso especialización", "Formación personal", "06-008", "07-009", "08-010"],
    ["Andrés Castro", "61", "Iquique", "Consultoría", "2025-08-20T00:00:00", 85000.75, "USD", "Asesoría técnica", "Consultor externo", "06-008", "-", "-"]
]

# Headers del Excel
headers = [
    "Empleado",          # Columna 1
    "Tipo Doc",          # Columna 2 - Para agrupación
    "Ciudad",            # Columna 3
    "Categoría",         # Columna 4
    "Fecha",             # Columna 5
    "Monto",             # Columna 6
    "Moneda",            # Columna 7
    "Descripción",       # Columna 8
    "Observaciones",     # Columna 9
    "Centro Costo 1",    # Columna 10 - CC formato XX-XXX
    "Centro Costo 2",    # Columna 11 - CC formato XX-XXX
    "Centro Costo 3"     # Columna 12 - CC formato XX-XXX
]

# Crear DataFrame
df = pd.DataFrame(datos, columns=headers)

# Crear el archivo Excel
archivo_excel = "/root/SGM/gastos_prueba_formato_cc.xlsx"

with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Gastos', index=False)

print(f"✅ Archivo creado: {archivo_excel}")
print(f"📊 Total de filas: {len(df)}")
print(f"📋 Headers: {headers}")

# Mostrar resumen de agrupación esperada
print("\n📈 Resumen de agrupación esperada:")
agrupacion = df.groupby(['Tipo Doc']).size()
print(agrupacion)

print("\n🏢 Resumen de centros de costos por fila:")
for idx, row in df.iterrows():
    cc_count = 0
    cc_list = []
    for col in ['Centro Costo 1', 'Centro Costo 2', 'Centro Costo 3']:
        valor = row[col]
        if valor and valor != '-' and valor != 0 and str(valor).strip() != '':
            cc_count += 1
            cc_list.append(valor)
    
    tipo_doc = row['Tipo Doc']
    empleado = row['Empleado']
    print(f"  • {empleado} - Tipo {tipo_doc} con {cc_count}CC: {cc_list}")

print(f"\n🎯 Grupos esperados por Tipo Doc + CC:")
grupos_esperados = {}
for idx, row in df.iterrows():
    cc_count = 0
    for col in ['Centro Costo 1', 'Centro Costo 2', 'Centro Costo 3']:
        valor = row[col]
        if valor and valor != '-' and valor != 0 and str(valor).strip() != '':
            cc_count += 1
    
    tipo_doc = row['Tipo Doc']
    grupo_key = f"{tipo_doc} con {cc_count}CC"
    if grupo_key not in grupos_esperados:
        grupos_esperados[grupo_key] = 0
    grupos_esperados[grupo_key] += 1

for grupo, cantidad in grupos_esperados.items():
    print(f"  • {grupo}: {cantidad} registros")
