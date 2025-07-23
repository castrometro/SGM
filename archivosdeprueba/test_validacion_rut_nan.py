#!/usr/bin/env python3
"""
Test de validación de RUTs para detectar valores NaN y filas de totales de Talana

Este script prueba la nueva función _es_rut_valido() implementada en LibroRemuneraciones.py
para asegurar que detecta correctamente valores inválidos que pueden causar confusión
en el procesamiento de empleados.
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

# Importar la función a testear
from backend.nomina.utils.LibroRemuneraciones import _es_rut_valido

def test_rut_valido():
    """Prueba la función _es_rut_valido con diferentes casos"""
    
    print("🧪 TESTING FUNCIÓN _es_rut_valido()")
    print("="*60)
    
    # Casos de prueba
    casos_prueba = [
        # Casos VÁLIDOS
        ("12345678-9", True, "RUT válido con guión"),
        ("12345678", True, "RUT válido sin guión"),  
        ("1234567890", True, "RUT válido largo"),
        ("   12345678-9   ", True, "RUT válido con espacios (se limpia)"),
        
        # Casos INVÁLIDOS
        (None, False, "None"),
        (np.nan, False, "NumPy NaN"),
        (pd.NA, False, "Pandas NA"),
        ("", False, "String vacío"),
        ("   ", False, "Solo espacios"),
        ("nan", False, "String 'nan' minúsculas"),
        ("NaN", False, "String 'NaN' mayúsculas"),
        ("NAN", False, "String 'NAN' mayúsculas"),
        ("total", False, "Palabra 'total'"),
        ("TOTAL", False, "Palabra 'TOTAL' mayúsculas"),
        ("totales", False, "Palabra 'totales'"),
        ("suma", False, "Palabra 'suma'"),
        ("SUMA", False, "Palabra 'SUMA' mayúsculas"),
        ("sumatoria", False, "Palabra 'sumatoria'"),
        ("resumen", False, "Palabra 'resumen'"),
        ("consolidado", False, "Palabra 'consolidado'"),
        ("subtotal", False, "Palabra 'subtotal'"),
    ]
    
    resultados_correctos = 0
    total_casos = len(casos_prueba)
    
    for valor, esperado, descripcion in casos_prueba:
        resultado = _es_rut_valido(valor)
        estado = "✅" if resultado == esperado else "❌"
        
        print(f"{estado} {descripcion}: '{valor}' -> {resultado} (esperado: {esperado})")
        
        if resultado == esperado:
            resultados_correctos += 1
        else:
            print(f"   ❌ ERROR: Se esperaba {esperado} pero se obtuvo {resultado}")
    
    print("="*60)
    print(f"RESUMEN: {resultados_correctos}/{total_casos} casos correctos")
    
    if resultados_correctos == total_casos:
        print("🎉 ¡Todos los casos de prueba pasaron correctamente!")
        return True
    else:
        print(f"⚠️  {total_casos - resultados_correctos} casos fallaron")
        return False

def test_pandas_dataframe():
    """Prueba con un DataFrame de pandas simulando datos de Talana"""
    
    print("\n🧪 TESTING CON DATAFRAME DE PANDAS (simulando Talana)")
    print("="*60)
    
    # Crear DataFrame simulando datos de Talana con filas problemáticas
    data = {
        'Año': [2024, 2024, 2024, 2024, 2024],
        'Mes': [12, 12, 12, 12, 12],
        'Rut de la Empresa': ['76123456-7', '76123456-7', '76123456-7', '76123456-7', '76123456-7'],
        'Rut del Trabajador': ['12345678-9', '98765432-1', np.nan, 'TOTAL', '11223344-5'],
        'Nombre': ['Juan Pérez', 'María González', 'TOTALES', 'SUMA GENERAL', 'Carlos Silva'],
        'Apellido Paterno': ['Pérez', 'González', '', '', 'Silva'],
        'Apellido Materno': ['López', 'Martínez', '', '', 'Rojas'],
        'Sueldo Base': [500000, 600000, 1100000, 1100000, 450000]
    }
    
    df = pd.DataFrame(data)
    print("DataFrame de prueba:")
    print(df)
    print()
    
    filas_validas = 0
    filas_invalidas = 0
    
    print("Procesando filas:")
    for index, row in df.iterrows():
        rut_raw = row['Rut del Trabajador']
        es_valido = _es_rut_valido(rut_raw)
        estado = "✅ PROCESAR" if es_valido else "❌ IGNORAR"
        
        print(f"Fila {index + 1}: RUT '{rut_raw}' -> {estado}")
        
        if es_valido:
            filas_validas += 1
        else:
            filas_invalidas += 1
    
    print("="*60)
    print(f"RESUMEN DATAFRAME:")
    print(f"  - Filas válidas (a procesar): {filas_validas}")
    print(f"  - Filas inválidas (ignorar): {filas_invalidas}")
    print(f"  - Total filas: {len(df)}")
    
    # Verificar que se ignoren las filas correctas (filas 2, 3 y 4 del DataFrame)
    expected_valid = 2  # Solo filas 0 y 4 deberían ser válidas
    expected_invalid = 3  # Filas 1, 2 y 3 deberían ser inválidas
    
    if filas_validas == expected_valid and filas_invalidas == expected_invalid:
        print("🎉 ¡El filtrado de DataFrame funciona correctamente!")
        return True
    else:
        print(f"⚠️  Filtrado incorrecto. Esperado: {expected_valid} válidas, {expected_invalid} inválidas")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🔍 VALIDACIÓN DE RUT NaN - PROTECCIÓN CONTRA TOTALES DE TALANA")
    print("="*60)
    print("Propósito: Evitar procesar filas de totales que Talana coloca al final")
    print("="*60)
    
    test1_ok = test_rut_valido()
    test2_ok = test_pandas_dataframe()
    
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    
    if test1_ok and test2_ok:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! La validación de RUT funciona correctamente.")
        print("✅ Las filas con RUT NaN, vacío o palabras como 'TOTAL' serán ignoradas")
        print("✅ Esto evitará confusión cuando Talana coloque filas de totales")
        return True
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON. Revisar la implementación.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
