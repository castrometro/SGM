#!/usr/bin/env python3
"""
Script de prueba para verificar la normalización de RUTs
"""

import re

def normalizar_rut(rut):
    """
    Normaliza RUT para comparaciones removiendo puntos, guiones y espacios
    """
    if not rut:
        return ""
    
    # Convertir a string y limpiar
    rut_limpio = str(rut).strip()
    
    # Remover puntos, guiones, espacios
    rut_limpio = re.sub(r'[.\-\s]', '', rut_limpio)
    
    # Convertir a mayúsculas (por si el dígito verificador es 'k')
    rut_limpio = rut_limpio.upper()
    
    return rut_limpio

def ruts_son_equivalentes(rut1, rut2):
    """Compara si dos RUTs son equivalentes después de normalización"""
    return normalizar_rut(rut1) == normalizar_rut(rut2)

# Casos de prueba
casos_prueba = [
    ("12.345.678-9", "123456789", True),
    ("12345678-9", "123456789", True),
    (" 12.345.678-9 ", "123456789", True),
    ("12.345.678-K", "12345678k", True),
    ("12.345.678-k", "12345678K", True),
    ("12.345.678-9", "12.345.678-0", False),
    ("", "", True),
    ("", "123456789", False),
    ("12 345 678-9", "123456789", True),
]

print("=== PRUEBA DE NORMALIZACIÓN DE RUT ===\n")

for i, (rut1, rut2, esperado) in enumerate(casos_prueba, 1):
    resultado = ruts_son_equivalentes(rut1, rut2)
    status = "✅ PASS" if resultado == esperado else "❌ FAIL"
    
    print(f"Caso {i}: {status}")
    print(f"  RUT 1: '{rut1}' -> '{normalizar_rut(rut1)}'")
    print(f"  RUT 2: '{rut2}' -> '{normalizar_rut(rut2)}'")
    print(f"  Esperado: {esperado}, Obtenido: {resultado}")
    print()

print("=== FIN DE PRUEBAS ===")
