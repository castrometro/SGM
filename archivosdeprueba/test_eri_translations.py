#!/usr/bin/env python3
"""
Prueba rápida para verificar que las traducciones ERI funcionen correctamente
"""
import sys
sys.path.append('/root/SGM')

def test_eri_translations():
    from streamlit_conta.utils.excel.translations import get_text, detect_language_improved
    
    # Datos de prueba
    metadata_es = {'idioma': 'es', 'lang_field': 'nombre_es'}
    metadata_en = {'idioma': 'en', 'lang_field': 'nombre_en'}
    
    # Probar detección de idioma
    print("=== DETECCIÓN DE IDIOMA ===")
    lang_es = detect_language_improved(metadata_es)
    lang_en = detect_language_improved(metadata_en)
    print(f"Español detectado: {lang_es}")
    print(f"Inglés detectado: {lang_en}")
    
    # Probar traducciones ERI
    print("\n=== TRADUCCIONES ERI ===")
    
    # Bloques ERI
    bloques = ['ganancias_brutas', 'ganancia_perdida', 'ganancia_perdida_antes_impuestos', 'total_general']
    
    for bloque in bloques:
        texto_es = get_text(bloque, 'es', metadata_es)
        texto_en = get_text(bloque, 'en', metadata_en)
        print(f"{bloque}:")
        print(f"  ES: {texto_es}")
        print(f"  EN: {texto_en}")
        print()
    
    # Verificar que coincidan con excel_templates.py
    print("=== VERIFICACIÓN DE CONSISTENCIA ===")
    expected_es = {
        'ganancias_brutas': 'Ganancias Brutas',
        'ganancia_perdida': 'Ganancia (Pérdida)',
        'ganancia_perdida_antes_impuestos': 'Ganancia (Pérdida) Antes de Impuestos',
        'total_general': 'TOTAL GENERAL (Ganancia/Pérdida)'
    }
    
    expected_en = {
        'ganancias_brutas': 'Gross Earnings',
        'ganancia_perdida': 'Earnings (Loss)',
        'ganancia_perdida_antes_impuestos': 'Earnings (Loss) Before Taxes',
        'total_general': 'TOTAL GENERAL (Profit/Loss)'
    }
    
    for bloque in bloques:
        texto_es = get_text(bloque, 'es', metadata_es)
        texto_en = get_text(bloque, 'en', metadata_en)
        
        if texto_es == expected_es[bloque]:
            print(f"✅ {bloque} ES: {texto_es}")
        else:
            print(f"❌ {bloque} ES: esperado '{expected_es[bloque]}', obtenido '{texto_es}'")
            
        if texto_en == expected_en[bloque]:
            print(f"✅ {bloque} EN: {texto_en}")
        else:
            print(f"❌ {bloque} EN: esperado '{expected_en[bloque]}', obtenido '{texto_en}'")
    
    print("\n=== PRUEBA TERMINADA ===")

if __name__ == "__main__":
    test_eri_translations()
