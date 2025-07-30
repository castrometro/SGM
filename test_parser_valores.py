#!/usr/bin/env python3
"""
Script de prueba para validar el parser mejorado de valores en nómina
"""

import pandas as pd

def test_procesamiento_valores():
    """Prueba el procesamiento de diferentes tipos de valores"""
    
    # Casos de prueba que pueden causar el problema del cero extra
    casos_prueba = [
        # (valor_raw, esperado, descripcion)
        (123456, "123456", "Entero normal"),
        (123456.0, "123456", "Float que es entero"),
        (123456.78, "123456.78", "Float con decimales"),
        (123456.00, "123456", "Float con ceros decimales"),
        ("123456", "123456", "String numérico"),
        ("123456.0", "123456", "String float que es entero"),
        ("$123,456", "123456", "String con formato monetario"),
        ("", "", "String vacío"),
        (None, "", "Valor None"),
        ("nan", "", "String 'nan'"),
        (1234567890, "1234567890", "Número muy grande"),
        (12345678901234567890, "12345678901234567890", "Número extremadamente grande"),
    ]
    
    print("🧪 Probando procesamiento de valores mejorado:")
    print("=" * 60)
    
    for valor_raw, esperado, descripcion in casos_prueba:
        # Simulación del procesamiento mejorado
        if pd.isna(valor_raw) if pd.api.types.is_scalar(valor_raw) else valor_raw is None or valor_raw == '':
            valor = ""
        else:
            # Si es un número, preservar su precisión original
            if isinstance(valor_raw, (int, float)):
                # Para números enteros, mantener sin decimales
                if isinstance(valor_raw, int) or (isinstance(valor_raw, float) and valor_raw.is_integer()):
                    valor = str(int(valor_raw))
                else:
                    # Para decimales, usar precisión limitada
                    valor = f"{valor_raw:.2f}".rstrip('0').rstrip('.')
            else:
                # Para strings, limpiar y validar
                valor = str(valor_raw).strip()
                # Si es "nan" como string, convertir a vacío
                if valor.lower() == 'nan':
                    valor = ""
                # Intentar limpiar formato monetario si existe
                elif valor:
                    # Remover símbolos de moneda y espacios
                    valor_limpio = valor.replace('$', '').replace(',', '').replace('.', '').strip()
                    # Si después de limpiar es un número válido, usar esa representación
                    try:
                        numero = float(valor_limpio) if '.' in valor else int(valor_limpio)
                        if isinstance(numero, int) or numero.is_integer():
                            valor_final = str(int(numero))
                        else:
                            valor_final = f"{numero:.2f}".rstrip('0').rstrip('.')
                        valor = valor_final
                    except (ValueError, TypeError):
                        # Si no se puede convertir a número, mantener el valor original limpio
                        pass
        
        # Verificar resultado
        resultado = "✅ CORRECTO" if valor == esperado else f"❌ ERROR - Esperado: '{esperado}'"
        print(f"{descripcion:25} | Input: {str(valor_raw):15} | Output: '{valor:15}' | {resultado}")
    
    print("=" * 60)
    print("🎯 Prueba completada")

if __name__ == "__main__":
    test_procesamiento_valores()
