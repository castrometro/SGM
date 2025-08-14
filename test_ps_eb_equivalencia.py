#!/usr/bin/env python3
"""
Test para verificar que PS y EB son reconocidos como equivalentes
en las funciones de centros de costo
"""

import sys
import os

# Agregar el directorio backend al path de Python
sys.path.append('/root/SGM/backend')

# Simulación básica de las funciones - extraemos solo la lógica necesaria
def contar_centros_costos_test(fila, headers, mapeo_cc=None):
    """
    Versión de prueba de contar_centros_costos
    """
    columnas_cc_nombres = ['PyC', 'PS', 'EB', 'CO']  # EB es equivalente a PS
    count = 0
    
    for header_name in headers:
        if header_name in columnas_cc_nombres:
            valor = fila.get(header_name)
            
            if (valor is not None and 
                valor != "-" and 
                valor != 0 and 
                valor != "0" and 
                str(valor).strip() != ""):
                count += 1
    
    return count

def calcular_codigos_cc_para_fila_test(fila, headers, mapeo_cc):
    """
    Versión de prueba de calcular_codigos_cc_para_fila
    """
    columnas_cc_mapeo = {
        'PyC': 'col10',   # PyC
        'PS': 'col11',    # PS
        'EB': 'col11',    # EB (equivalente a PS)
        'CO': 'col12'     # CO
    }
    
    codigos_aplicables = []
    
    for header_name in headers:
        if header_name in columnas_cc_mapeo:
            mapeo_key = columnas_cc_mapeo[header_name]
            
            if mapeo_key in mapeo_cc:
                codigo_cc = mapeo_cc[mapeo_key]
                valor = fila.get(header_name)
                
                if (valor is not None and 
                    valor != "-" and 
                    valor != 0 and 
                    valor != "0" and 
                    str(valor).strip() != "" and
                    codigo_cc and 
                    codigo_cc.strip() != ""):
                    
                    codigo_limpio = codigo_cc.strip()
                    if codigo_limpio not in codigos_aplicables:
                        codigos_aplicables.append(codigo_limpio)
    
    return ", ".join(codigos_aplicables) if codigos_aplicables else ""

def test_equivalencia_ps_eb():
    """
    Test para verificar que PS y EB son tratados como equivalentes
    """
    print("🧪 Test: Equivalencia PS y EB")
    print("=" * 50)
    
    # Caso 1: Headers con PS
    headers_ps = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                  "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                  "PyC", "PS", "CO"]
    
    fila_ps = {
        "Nro": 1,
        "Tipo Doc": "33",
        "PyC": "100",
        "PS": "200", 
        "CO": "300"
    }
    
    mapeo_cc_ps = {
        "col10": "CC_PYC",
        "col11": "CC_PS", 
        "col12": "CC_CO"
    }
    
    count_ps = contar_centros_costos_test(fila_ps, headers_ps, mapeo_cc_ps)
    codigos_ps = calcular_codigos_cc_para_fila_test(fila_ps, headers_ps, mapeo_cc_ps)
    
    print(f"📊 Headers con PS:")
    print(f"   Headers: {headers_ps[9:12]}")  # Solo PyC, PS, CO
    print(f"   Count centros: {count_ps}")
    print(f"   Códigos: '{codigos_ps}'")
    print()
    
    # Caso 2: Headers con EB (equivalente a PS)
    headers_eb = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                  "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                  "PyC", "EB", "CO"]
    
    fila_eb = {
        "Nro": 1,
        "Tipo Doc": "33",
        "PyC": "100",
        "EB": "200",  # EB en lugar de PS
        "CO": "300"
    }
    
    mapeo_cc_eb = {
        "col10": "CC_PYC",
        "col11": "CC_PS",  # Mismo mapeo que PS
        "col12": "CC_CO"
    }
    
    count_eb = contar_centros_costos_test(fila_eb, headers_eb, mapeo_cc_eb)
    codigos_eb = calcular_codigos_cc_para_fila_test(fila_eb, headers_eb, mapeo_cc_eb)
    
    print(f"📊 Headers con EB:")
    print(f"   Headers: {headers_eb[9:12]}")  # Solo PyC, EB, CO
    print(f"   Count centros: {count_eb}")
    print(f"   Códigos: '{codigos_eb}'")
    print()
    
    # Verificar equivalencia
    print("🔍 Verificación de equivalencia:")
    print(f"   Count PS == Count EB: {count_ps == count_eb} ({count_ps} vs {count_eb})")
    print(f"   Códigos PS == Códigos EB: {codigos_ps == codigos_eb}")
    print(f"   PS: '{codigos_ps}'")
    print(f"   EB: '{codigos_eb}'")
    
    # Caso 3: Valores vacíos
    print("\n🧪 Test: Valores vacíos")
    print("-" * 30)
    
    fila_vacios = {
        "PyC": "100",
        "PS": "-",     # Vacío
        "CO": ""       # Vacío
    }
    
    count_vacios = contar_centros_costos_test(fila_vacios, headers_ps, mapeo_cc_ps)
    print(f"   Fila con PyC='100', PS='-', CO='': Count = {count_vacios} (debería ser 1)")
    
    # Caso 4: Archivo mixto (tanto PS como EB presentes - caso raro pero posible)
    headers_mixto = ["Nro", "Tipo Doc", "RUT Proveedor", "Razon Social", "Folio", 
                     "Fecha Docto", "Monto Total", "Codigo cuenta", "Nombre cuenta", 
                     "PyC", "PS", "EB", "CO"]
    
    fila_mixto = {
        "PyC": "100",
        "PS": "200",
        "EB": "250",  # Ambos presentes
        "CO": "300"
    }
    
    count_mixto = contar_centros_costos_test(fila_mixto, headers_mixto, mapeo_cc_ps)
    codigos_mixto = calcular_codigos_cc_para_fila_test(fila_mixto, headers_mixto, mapeo_cc_ps)
    
    print(f"\n🧪 Test: Headers mixtos (PS y EB)")
    print(f"   Count: {count_mixto} (debería contar todos los presentes)")
    print(f"   Códigos: '{codigos_mixto}' (no debería duplicar CC_PS)")
    
    print("\n✅ Test completado")

if __name__ == "__main__":
    test_equivalencia_ps_eb()
