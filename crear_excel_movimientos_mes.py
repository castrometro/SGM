#!/usr/bin/env python3
"""
Script para crear un archivo Excel de prueba para Movimientos del Mes
con el formato de nombre correcto: 202507_movimientos_mes_965406905.xlsx
"""

import pandas as pd
from datetime import datetime, timedelta
import random

def crear_excel_movimientos_mes():
    # Datos de ejemplo para movimientos del mes
    tipos_movimientos = [
        'Horas Extra',
        'Bono Productividad', 
        'Descuento Atraso',
        'Comisión Ventas',
        'Aguinaldo',
        'Descuento Préstamo',
        'Bono Asistencia',
        'Descuento AFC'
    ]
    
    conceptos = [
        'Pago horas extras trabajadas',
        'Bono por cumplimiento de metas',
        'Descuento por llegadas tarde',
        'Comisión por ventas del mes',
        'Aguinaldo fiestas patrias',
        'Descuento cuota préstamo empresa',
        'Bono por asistencia perfecta',
        'Descuento AFC mensual'
    ]
    
    # Generar datos ficticios
    datos = []
    base_date = datetime(2025, 7, 1)
    
    # RUTs ficticios de empleados
    ruts_empleados = [
        '12345678-9',
        '11111111-1', 
        '22222222-2',
        '33333333-3',
        '44444444-4',
        '55555555-5'
    ]
    
    for i in range(50):  # 50 movimientos de ejemplo
        fecha = base_date + timedelta(days=random.randint(0, 30))
        tipo_mov = random.choice(tipos_movimientos)
        concepto = random.choice(conceptos)
        rut = random.choice(ruts_empleados)
        
        # Montos variados según el tipo
        if 'Descuento' in tipo_mov:
            monto = -random.randint(5000, 50000)
        else:
            monto = random.randint(10000, 200000)
        
        datos.append({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'tipo_movimiento': tipo_mov,
            'rut_empleado': rut,
            'concepto': concepto,
            'monto': monto
        })
    
    # Crear DataFrame
    df = pd.DataFrame(datos)
    
    # Ordenar por fecha
    df = df.sort_values('fecha')
    
    # Nombre del archivo con formato correcto
    nombre_archivo = '202507_movimientos_mes_965406905.xlsx'
    
    # Guardar Excel
    df.to_excel(nombre_archivo, index=False, sheet_name='Movimientos')
    
    print(f"✅ Archivo creado: {nombre_archivo}")
    print(f"📊 Registros: {len(df)}")
    print(f"📅 Período: {df['fecha'].min()} a {df['fecha'].max()}")
    print("\n📋 Primeras 5 filas:")
    print(df.head())
    
    return nombre_archivo

if __name__ == "__main__":
    crear_excel_movimientos_mes()
