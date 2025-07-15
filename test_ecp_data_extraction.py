#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de datos ECP
"""

from streamlit_conta.utils.excel_templates import ExcelTemplateGenerator
import logging

# Configurar logging para ver el debug
logging.basicConfig(level=logging.INFO)

def test_ecp_data_extraction():
    """Probar la extracción de datos para ECP"""
    generator = ExcelTemplateGenerator()
    
    # Datos de prueba ECP - estructura típica esperada
    data_ecp_test = {
        "patrimonio": {
            "capital": {
                "saldo_inicial": 10000000,
                "cambios": 2000000,
                "saldo_final": 12000000
            },
            "otras_reservas": {
                "saldo_inicial": 5000000,
                "cambios": 500000,
                "saldo_final": 5500000
            },
            "resultados_acumulados": {
                "saldo_inicial": 3000000,
                "cambios": 100000,
                "saldo_final": 3100000
            }
        }
    }
    
    # Datos ERI de prueba
    data_eri_test = {
        "ganancias_brutas": {"total": 8000000},
        "ganancia_perdida": {"total": -2000000},
        "ganancia_perdida_antes_impuestos": {"total": 1500000}
    }
    
    # Metadatos de prueba
    metadata_test = {
        "cliente_nombre": "Cliente Prueba ECP",
        "periodo": "2024",
        "moneda": "CLP",
        "idioma": "es"
    }
    
    print("=== PRUEBA DE EXTRACCIÓN DE DATOS ECP ===")
    print()
    
    try:
        # Generar el template
        workbook = generator.generate_ecp_template(data_ecp_test, metadata_test, data_eri_test)
        
        # Guardar archivo de prueba
        workbook.save("/root/SGM/test_ecp_output.xlsx")
        print("✅ Template ECP generado exitosamente")
        print("📁 Archivo guardado: /root/SGM/test_ecp_output.xlsx")
        
        # Mostrar estructura de datos procesada
        print()
        print("📊 DATOS PROCESADOS:")
        patrimonio_data = data_ecp_test.get("patrimonio", data_ecp_test)
        
        capital_data = patrimonio_data.get("capital", {})
        print(f"Capital - Inicial: ${capital_data.get('saldo_inicial', 0):,}")
        print(f"Capital - Cambios: ${capital_data.get('cambios', 0):,}")
        
        reservas_data = patrimonio_data.get("otras_reservas", {})
        print(f"Otras Reservas - Inicial: ${reservas_data.get('saldo_inicial', 0):,}")
        print(f"Otras Reservas - Cambios: ${reservas_data.get('cambios', 0):,}")
        
        resultados_data = patrimonio_data.get("resultados_acumulados", {})
        print(f"Resultados Acumulados - Inicial: ${resultados_data.get('saldo_inicial', 0):,}")
        print(f"Resultados Acumulados - Cambios: ${resultados_data.get('cambios', 0):,}")
        
        # Calcular total ERI
        total_eri = sum(bloque.get("total", 0) for bloque in data_eri_test.values())
        print(f"Total ERI: ${total_eri:,}")
        
    except Exception as e:
        print(f"❌ Error al generar template ECP: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ecp_data_extraction()
