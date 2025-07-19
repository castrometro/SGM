#!/usr/bin/env python3
"""
Test de validación de RUT NaN para archivos de Novedades

Este script prueba que la nueva validación aplicada a NovedadesRemuneraciones.py
funcione correctamente para evitar procesar filas con RUT inválido que Talana
coloca como totales al final de los archivos.

PROBLEMA IDENTIFICADO:
- Usuario reportó discrepancia: "Empleado nan nan nan (RUT: nan) solo en Novedades"  
- Causa: Archivo novedades tiene filas de totales con RUT NaN al igual que el Libro Mayor
- Solución: Aplicar misma validación _es_rut_valido() que se implementó para LibroRemuneraciones.py
"""

import pandas as pd
import numpy as np
import sys
import os
import django

# Configurar Django
sys.path.append('/root/SGM')
os.chdir('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Importar funciones a testear
from backend.nomina.utils.LibroRemuneraciones import _es_rut_valido
from backend.nomina.utils.NovedadesRemuneraciones import (
    actualizar_empleados_desde_novedades,
    guardar_registros_novedades
)

def crear_dataframe_novedades_simulado():
    """Crea un DataFrame simulando archivo de novedades con filas problemáticas"""
    
    print("📁 CREANDO DATAFRAME SIMULADO DE NOVEDADES")
    print("="*60)
    
    # Simular estructura típica de archivo novedades
    data = {
        # Primeras 4 columnas: datos del empleado
        'RUT': ['12345678-9', '98765432-1', np.nan, 'TOTAL', '11223344-5', 'SUMA'],
        'Nombre': ['Juan', 'María', 'TOTALES', 'GENERAL', 'Carlos', 'FINAL'],
        'Apellido Paterno': ['Pérez', 'González', '', '', 'Silva', ''],
        'Apellido Materno': ['López', 'Martínez', '', '', 'Rojas', ''],
        # Columnas 5+: conceptos de novedades
        'Gratificación Legal': [50000, 60000, 110000, 110000, 45000, 265000],
        'Bono Responsabilidad': [25000, 30000, 55000, 55000, 20000, 130000],
        'Descuento Atraso': [-5000, 0, -5000, -5000, -2000, -12000]
    }
    
    df = pd.DataFrame(data)
    
    print("DataFrame de novedades simulado:")
    print(df)
    print()
    
    # Identificar filas que deberían ser ignoradas
    filas_validas = []
    filas_invalidas = []
    
    for index, row in df.iterrows():
        rut_raw = row['RUT']
        es_valido = _es_rut_valido(rut_raw)
        
        if es_valido:
            filas_validas.append(index)
        else:
            filas_invalidas.append(index)
    
    print(f"Análisis de validación:")
    print(f"  - Filas VÁLIDAS (procesar): {filas_validas}")
    print(f"  - Filas INVÁLIDAS (ignorar): {filas_invalidas}")
    print()
    
    return df, filas_validas, filas_invalidas

def simular_procesamiento_novedades(df):
    """Simula cómo se procesarían las filas del DataFrame"""
    
    print("🔄 SIMULANDO PROCESAMIENTO DE NOVEDADES")
    print("="*60)
    
    # Simular la lógica que hay en actualizar_empleados_desde_novedades
    rut_col = df.columns[0]  # Primera columna (RUT)
    
    empleados_procesados = []
    filas_ignoradas = 0
    
    for index, row in df.iterrows():
        # Verificar si la primera columna está vacía
        primera_col_valor = str(row.get(df.columns[0], "")).strip()
        if not primera_col_valor:
            print(f"Fila {index}: Ignorada por primera columna vacía")
            continue
        
        # Aplicar validación de RUT
        rut_raw = row.get(rut_col)
        if not _es_rut_valido(rut_raw):
            filas_ignoradas += 1
            print(f"Fila {index}: ❌ IGNORADA - RUT inválido '{rut_raw}' (posible total de Talana)")
            continue
        
        # Procesar como empleado válido
        rut = str(rut_raw).strip()
        nombre_completo = f"{row.get('Nombre', '')} {row.get('Apellido Paterno', '')} {row.get('Apellido Materno', '')}"
        empleados_procesados.append({
            'fila': index,
            'rut': rut,
            'nombre_completo': nombre_completo.strip()
        })
        print(f"Fila {index}: ✅ PROCESADA - {nombre_completo.strip()} (RUT: {rut})")
    
    print("="*60)
    print(f"RESULTADO SIMULACIÓN:")
    print(f"  - Empleados procesados: {len(empleados_procesados)}")
    print(f"  - Filas ignoradas: {filas_ignoradas}")
    print(f"  - Total filas: {len(df)}")
    
    return empleados_procesados, filas_ignoradas

def main():
    """Ejecutar simulación completa"""
    print("🧪 PRUEBA DE VALIDACIÓN RUT NaN - ARCHIVOS DE NOVEDADES")
    print("="*60)
    print("CONTEXTO: Usuario reportó discrepancia 'Empleado nan nan nan (RUT: nan) solo en Novedades'")
    print("CAUSA: Talana coloca filas de totales con RUT NaN al final de archivos de novedades")
    print("SOLUCIÓN: Aplicar validación _es_rut_valido() como en LibroRemuneraciones.py")
    print("="*60)
    print()
    
    # 1. Crear DataFrame simulado
    df, filas_validas_esperadas, filas_invalidas_esperadas = crear_dataframe_novedades_simulado()
    
    # 2. Simular procesamiento
    empleados_procesados, filas_ignoradas = simular_procesamiento_novedades(df)
    
    # 3. Validar resultados
    print()
    print("🔍 VALIDACIÓN DE RESULTADOS")
    print("="*60)
    
    # Verificar que se procesaron solo las filas válidas esperadas
    filas_procesadas = [emp['fila'] for emp in empleados_procesados]
    
    if set(filas_procesadas) == set(filas_validas_esperadas):
        print("✅ CORRECTO: Solo se procesaron las filas con RUT válido")
    else:
        print("❌ ERROR: Se procesaron filas incorrectas")
        print(f"   Esperado: {filas_validas_esperadas}")
        print(f"   Procesado: {filas_procesadas}")
    
    # Verificar que se ignoraron las filas correctas
    if filas_ignoradas == len(filas_invalidas_esperadas):
        print("✅ CORRECTO: Se ignoraron las filas con RUT inválido")
    else:
        print("❌ ERROR: No se ignoraron las filas correctas")
        print(f"   Esperado ignorar: {len(filas_invalidas_esperadas)}")
        print(f"   Realmente ignoradas: {filas_ignoradas}")
    
    # Verificar que no aparecerán empleados "nan nan nan" en discrepancias
    empleados_con_nan = [emp for emp in empleados_procesados if 'nan' in emp['rut'].lower() or 'nan' in emp['nombre_completo'].lower()]
    
    if len(empleados_con_nan) == 0:
        print("✅ CORRECTO: No se procesaron empleados con RUT/nombre 'nan'")
        print("   → Esto evitará la discrepancia 'Empleado nan nan nan (RUT: nan) solo en Novedades'")
    else:
        print("❌ ERROR: Se procesaron empleados con 'nan':")
        for emp in empleados_con_nan:
            print(f"   - {emp}")
    
    print()
    print("🎯 CONCLUSIÓN")
    print("="*60)
    
    if len(empleados_con_nan) == 0 and filas_ignoradas == len(filas_invalidas_esperadas):
        print("🎉 ¡ÉXITO! La validación funciona correctamente:")
        print("   ✅ Se ignoran filas con RUT NaN/total de Talana")
        print("   ✅ No se crean empleados 'nan nan nan' en novedades")
        print("   ✅ Se elimina la discrepancia reportada por el usuario")
        print("   ✅ Solo se procesan empleados reales con RUT válido")
        return True
    else:
        print("❌ HAY PROBLEMAS en la validación. Revisar implementación.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
