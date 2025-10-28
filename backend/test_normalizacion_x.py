#!/usr/bin/env python
"""
Script de prueba para validar la normalización de valores "X" en novedades

Tests:
1. Valor "X" → "0"
2. Valor "x" → "0"  
3. Valor "-" → "0"
4. Valor "N/A" → "0"
5. Valor None → "0"
6. Valor numérico válido → mantener
7. Valor string numérico → mantener
"""

import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from nomina.utils.NovedadesRemuneraciones import normalizar_valor_concepto_novedades

def test_normalizacion():
    """Ejecuta tests de normalización de valores"""
    
    print("\n" + "="*70)
    print("🧪 TESTS DE NORMALIZACIÓN DE VALORES EN NOVEDADES")
    print("="*70 + "\n")
    
    tests = [
        # (input, expected_output, descripcion)
        ("X", "0", "Letra X mayúscula"),
        ("x", "0", "Letra x minúscula"),
        ("-", "0", "Guión"),
        ("N/A", "0", "N/A mayúsculas"),
        ("n/a", "0", "n/a minúsculas"),
        ("NA", "0", "NA sin slash"),
        ("", "0", "String vacío"),
        (None, "0", "None"),
        (pd.NA, "0", "pandas NA"),
        (150000, "150000", "Número entero"),
        ("150000", "150000", "String numérico"),
        ("0", "0", "Cero como string"),
        (0, "0", "Cero como número"),
        ("  X  ", "0", "X con espacios"),
        ("  150000  ", "  150000  ", "Número con espacios (se mantiene)"),
    ]
    
    passed = 0
    failed = 0
    
    for valor_input, expected, descripcion in tests:
        resultado = normalizar_valor_concepto_novedades(valor_input)
        
        if resultado == expected:
            print(f"✅ PASS: {descripcion}")
            print(f"   Input: {repr(valor_input)} → Output: {repr(resultado)}")
            passed += 1
        else:
            print(f"❌ FAIL: {descripcion}")
            print(f"   Input: {repr(valor_input)}")
            print(f"   Expected: {repr(expected)}")
            print(f"   Got: {repr(resultado)}")
            failed += 1
        print()
    
    print("="*70)
    print(f"📊 RESUMEN: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    if failed == 0:
        print("🎉 ¡Todos los tests pasaron!")
        return True
    else:
        print("⚠️ Algunos tests fallaron")
        return False


if __name__ == "__main__":
    success = test_normalizacion()
    exit(0 if success else 1)
