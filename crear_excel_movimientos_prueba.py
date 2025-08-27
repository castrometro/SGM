#!/usr/bin/env python3
"""
Script para crear un archivo Excel de prueba para movimientos del mes
con las hojas 'Altas y Bajas' y 'Ausentismo' con headers en la fila 3
"""

import pandas as pd
from datetime import datetime, timedelta
import random

def crear_excel_movimientos_prueba():
    """Crea un archivo Excel de prueba para movimientos del mes"""
    
    print("📊 Creando archivo Excel de prueba para movimientos del mes...")
    
    # Datos de prueba para Altas y Bajas
    altas_bajas_data = []
    
    for i in range(1, 16):  # 15 registros de prueba
        nombre = f"Empleado Test {i:02d}"
        rut = f"12345{i:03d}-{i % 10}"
        empresa = "Empresa Test SGM"
        cargo = random.choice(["Desarrollador", "Analista", "Supervisor", "Operario", "Administrativo"])
        centro_costo = random.choice(["CC001", "CC002", "CC003", "CC004"])
        sucursal = random.choice(["Santiago", "Valparaíso", "Concepción"])
        
        # Fecha de ingreso (últimos 30 días)
        fecha_ingreso = datetime.now() - timedelta(days=random.randint(1, 30))
        fecha_retiro = ""
        tipo_contrato = random.choice(["Indefinido", "Plazo Fijo", "Honorarios"])
        dias_trabajados = random.randint(1, 30)
        sueldo_base = random.randint(500000, 2000000)
        alta_baja = "Alta" if i <= 10 else "Baja"
        
        if alta_baja == "Baja":
            fecha_retiro = datetime.now() - timedelta(days=random.randint(1, 5))
            fecha_retiro = fecha_retiro.strftime("%d/%m/%Y")
        
        motivo = "Ingreso nuevo empleado" if alta_baja == "Alta" else "Renuncia voluntaria"
        
        altas_bajas_data.append([
            nombre, rut, empresa, cargo, centro_costo, sucursal,
            fecha_ingreso.strftime("%d/%m/%Y"), fecha_retiro, tipo_contrato,
            dias_trabajados, sueldo_base, alta_baja, motivo
        ])
    
    # Datos de prueba para Ausentismo
    ausentismo_data = []
    
    for i in range(1, 21):  # 20 registros de prueba
        nombre = f"Empleado Test {i:02d}"
        rut = f"98765{i:03d}-{i % 10}"
        empresa = "Empresa Test SGM"
        cargo = random.choice(["Desarrollador", "Analista", "Supervisor", "Operario", "Administrativo"])
        centro_costo = random.choice(["CC001", "CC002", "CC003", "CC004"])
        sucursal = random.choice(["Santiago", "Valparaíso", "Concepción"])
        
        # Fechas de ausencia
        fecha_inicio = datetime.now() - timedelta(days=random.randint(1, 30))
        dias_ausencia = random.randint(1, 5)
        fecha_fin = fecha_inicio + timedelta(days=dias_ausencia)
        
        tipo_ausentismo = random.choice([
            "Licencia Médica", "Vacaciones", "Permiso Personal", 
            "Capacitación", "Licencia Maternal/Paternal"
        ])
        motivo = f"Motivo para {tipo_ausentismo.lower()}"
        observaciones = f"Observaciones de {nombre} - {tipo_ausentismo}"
        
        ausentismo_data.append([
            nombre, rut, empresa, cargo, centro_costo, sucursal,
            fecha_inicio.strftime("%d/%m/%Y"), fecha_fin.strftime("%d/%m/%Y"),
            dias_ausencia, tipo_ausentismo, motivo, observaciones
        ])
    
    # Crear el archivo Excel con múltiples hojas
    with pd.ExcelWriter('movimientos_mes_prueba.xlsx', engine='openpyxl') as writer:
        
        # Hoja 1: Altas y Bajas
        print("  📋 Creando hoja 'Altas y Bajas'...")
        
        # Crear DataFrame con headers en fila 3 (índice 2)
        altas_bajas_headers = [
            "Nombre", "Rut", "Empresa", "Cargo", "Centro de Costo", "Sucursal",
            "Fecha Ingreso", "Fecha Retiro", "Tipo Contrato", "Dias Trabajados",
            "Sueldo Base", "Alta/Baja", "Motivo"
        ]
        
        # Crear DataFrame vacío y agregar filas de separación
        df_altas_bajas = pd.DataFrame()
        
        # Fila 1: Título
        df_altas_bajas.loc[0] = ["REPORTE DE ALTAS Y BAJAS"] + [""] * (len(altas_bajas_headers) - 1)
        
        # Fila 2: Vacía
        df_altas_bajas.loc[1] = [""] * len(altas_bajas_headers)
        
        # Fila 3: Headers
        df_altas_bajas.loc[2] = altas_bajas_headers
        
        # Agregar datos a partir de la fila 4
        for idx, row in enumerate(altas_bajas_data, start=3):
            df_altas_bajas.loc[idx] = row
        
        df_altas_bajas.to_excel(writer, sheet_name='Altas y Bajas', index=False, header=False)
        
        # Hoja 2: Ausentismo
        print("  📋 Creando hoja 'Ausentismo'...")
        
        ausentismo_headers = [
            "Nombre", "Rut", "Empresa", "Cargo", "Centro de Costo", "Sucursal",
            "Fecha Inicio Ausencia", "Fecha Fin Ausencia", "Dias", "Tipo de Ausentismo",
            "Motivo", "Observaciones"
        ]
        
        # Crear DataFrame vacío y agregar filas de separación
        df_ausentismo = pd.DataFrame()
        
        # Fila 1: Título
        df_ausentismo.loc[0] = ["REPORTE DE AUSENTISMO"] + [""] * (len(ausentismo_headers) - 1)
        
        # Fila 2: Vacía
        df_ausentismo.loc[1] = [""] * len(ausentismo_headers)
        
        # Fila 3: Headers
        df_ausentismo.loc[2] = ausentismo_headers
        
        # Agregar datos a partir de la fila 4
        for idx, row in enumerate(ausentismo_data, start=3):
            df_ausentismo.loc[idx] = row
        
        df_ausentismo.to_excel(writer, sheet_name='Ausentismo', index=False, header=False)
        
        # Hoja 3: Resumen (opcional)
        print("  📋 Creando hoja 'Resumen'...")
        
        resumen_data = {
            'Tipo': ['Altas', 'Bajas', 'Total Ausencias'],
            'Cantidad': [
                len([x for x in altas_bajas_data if x[11] == 'Alta']),
                len([x for x in altas_bajas_data if x[11] == 'Baja']),
                len(ausentismo_data)
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
    
    print("✅ Archivo 'movimientos_mes_prueba.xlsx' creado exitosamente")
    print("\nEstructura del archivo:")
    print("  📊 Hoja 'Altas y Bajas': 15 registros con headers en fila 3")
    print("  📊 Hoja 'Ausentismo': 20 registros con headers en fila 3")
    print("  📊 Hoja 'Resumen': Estadísticas generales")
    print("\n🔍 Headers utilizados:")
    print("  Altas y Bajas:", altas_bajas_headers)
    print("  Ausentismo:", ausentismo_headers)

if __name__ == "__main__":
    crear_excel_movimientos_prueba()
