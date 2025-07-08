#!/usr/bin/env python3
"""
Script de prueba para verificar la normalización de texto
"""

import unicodedata
import re

def normalizar_texto(texto):
    """
    Normaliza texto para comparaciones ignorando:
    - Mayúsculas/minúsculas
    - Tildes y acentos
    - Guiones, puntos, espacios extra
    - Caracteres especiales
    """
    if not texto:
        return ""
    
    # Convertir a string y minúsculas
    texto = str(texto).lower().strip()
    
    # Quitar acentos/tildes usando unicodedata
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    
    # Quitar guiones, puntos, comas y caracteres especiales
    texto = re.sub(r'[-.,;:()\'\"]+', ' ', texto)
    
    # Normalizar espacios múltiples a uno solo
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def textos_son_equivalentes(texto1, texto2):
    """Compara si dos textos son equivalentes después de normalización"""
    return normalizar_texto(texto1) == normalizar_texto(texto2)

# Casos de prueba
casos_prueba = [
    ("Michel Francoise Ollivet-Besson", "Michel Francoise Ollivet-besson"),
    ("José María", "Jose Maria"),
    ("María-José Pérez", "Maria Jose Perez"),
    ("Ana Sofía", "Ana Sofia"),
    ("Juan  Carlos", "Juan Carlos"),
    ("PEDRO GONZÁLEZ", "pedro gonzalez"),
    ("O'Connor", "O Connor"),
    ("Jean-Pierre", "Jean Pierre"),
]

print("=== PRUEBA DE NORMALIZACIÓN DE TEXTO ===\n")

for texto1, texto2 in casos_prueba:
    norm1 = normalizar_texto(texto1)
    norm2 = normalizar_texto(texto2)
    equivalentes = textos_son_equivalentes(texto1, texto2)
    
    print(f"Texto 1: '{texto1}'")
    print(f"Texto 2: '{texto2}'")
    print(f"Normalizado 1: '{norm1}'")
    print(f"Normalizado 2: '{norm2}'")
    print(f"¿Son equivalentes? {'✅ SÍ' if equivalentes else '❌ NO'}")
    print("-" * 50)

print("\n=== CASOS ESPECÍFICOS ===")

# Caso específico del error reportado
caso_especifico = ("Michel Francoise Ollivet-Besson", "Michel Francoise Ollivet-besson")
print(f"Caso reportado:")
print(f"Libro: '{caso_especifico[0]}'")
print(f"Novedades: '{caso_especifico[1]}'")
print(f"¿Deberían ser iguales? {'✅ SÍ' if textos_son_equivalentes(*caso_especifico) else '❌ NO'}")
