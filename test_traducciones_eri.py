#!/usr/bin/env python3
"""
Script de prueba para verificar las traducciones de los bloques ERI
"""

from streamlit_conta.utils.excel_templates import ExcelTemplateGenerator

def test_traducciones():
    """Probar las traducciones de los bloques ERI"""
    generator = ExcelTemplateGenerator()
    
    bloques = [
        'ganancias_brutas',
        'ganancia_perdida', 
        'ganancia_perdida_antes_impuestos'
    ]
    
    print("=== PRUEBA DE TRADUCCIONES ERI ===")
    print()
    
    print("📝 ESPAÑOL:")
    for bloque in bloques:
        traduccion = generator._get_text(bloque, 'es')
        print(f"  • {bloque} → {traduccion}")
    
    print()
    print("🌎 INGLÉS:")
    for bloque in bloques:
        traduccion = generator._get_text(bloque, 'en')
        print(f"  • {bloque} → {traduccion}")
    
    print()
    print("✅ Prueba de traducciones completada")

if __name__ == "__main__":
    test_traducciones()
