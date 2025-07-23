#!/usr/bin/env python3
"""
Script de prueba para verificar las traducciones del ECP en ambos idiomas
"""

from streamlit_conta.utils.excel_templates import ExcelTemplateGenerator

def test_ecp_translations():
    """Probar las traducciones del ECP"""
    generator = ExcelTemplateGenerator()
    
    # Claves de traducción del ECP
    ecp_keys = [
        'title_ecp',
        'initial_balance',
        'period_result_ecp', 
        'other_changes',
        'final_balance',
        'concept',
        'capital',
        'other_reserves',
        'accumulated_results',
        'attributable_capital',
        'non_controlling_interests',
        'totals'
    ]
    
    print("=== PRUEBA DE TRADUCCIONES ECP ===")
    print()
    
    print("📝 ESPAÑOL:")
    for key in ecp_keys:
        traduccion = generator._get_text(key, 'es')
        print(f"  • {key} → {traduccion}")
    
    print()
    print("🌎 INGLÉS:")
    for key in ecp_keys:
        traduccion = generator._get_text(key, 'en')
        print(f"  • {key} → {traduccion}")
    
    print()
    print("✅ Prueba de traducciones ECP completada")

def test_ecp_headers():
    """Probar los encabezados del ECP en ambos idiomas"""
    generator = ExcelTemplateGenerator()
    
    print()
    print("=== ENCABEZADOS ECP ===")
    
    # Simular creación de encabezados
    for language in ['es', 'en']:
        print(f"\n🗣️  IDIOMA: {language.upper()}")
        headers = [
            generator._get_text('concept', language),
            generator._get_text('capital', language),
            generator._get_text('other_reserves', language),
            generator._get_text('accumulated_results', language),
            generator._get_text('attributable_capital', language),
            generator._get_text('non_controlling_interests', language),
            generator._get_text('totals', language).replace(':', '')
        ]
        
        for i, header in enumerate(headers, 1):
            print(f"  {i}. {header}")

if __name__ == "__main__":
    test_ecp_translations()
    test_ecp_headers()
