#!/usr/bin/env python3
"""
Test para verificar funcionalidad de idiomas en Excel templates
"""

import sys
import os
sys.path.append('/root/SGM')

from streamlit_conta.utils.excel_templates import excel_generator
from datetime import datetime

def crear_datos_prueba_bilingue():
    """Crear datos de prueba con nombres en español e inglés"""
    return {
        'metadata': {
            'cliente_id': 1,
            'cliente_nombre': 'Empresa Bilingüe SA',
            'cierre_id': 123,
            'periodo': '2024-12',
            'fecha_generacion': datetime.now().isoformat(),
            'moneda': 'CLP',
            'idioma': 'es'  # Cambiar a 'en' para inglés
        },
        'activos': {
            'corrientes': {
                'nombre_es': 'Activos Corrientes',
                'nombre_en': 'Current Assets',
                'grupos': {
                    'Cash and Cash Equivalent': {
                        'nombre_es': 'Efectivo y Equivalentes',
                        'nombre_en': 'Cash and Cash Equivalents',
                        'total': 607884264,
                        'cuentas': [
                            {
                                'codigo': '1-01-001-001-0001',
                                'nombre_es': 'Caja pesos',
                                'nombre_en': 'Cash',
                                'saldo_final': 718815
                            },
                            {
                                'codigo': '1-01-001-002-0001',
                                'nombre_es': 'Banco Chile CLP',
                                'nombre_en': 'Bank Chile CLP',
                                'saldo_final': 605112931
                            },
                            {
                                'codigo': '1-01-001-002-0006',
                                'nombre_es': 'Banco Santander-Chile',
                                'nombre_en': 'Bank Santander-Chile',
                                'saldo_final': 552518
                            },
                            {
                                'codigo': '1-01-001-002-0007',
                                'nombre_es': 'Banco Estado',
                                'nombre_en': 'State Bank',
                                'saldo_final': 1500000
                            }
                        ]
                    },
                    'Accounts Receivable': {
                        'nombre_es': 'Cuentas por Cobrar',
                        'nombre_en': 'Accounts Receivable',
                        'total': 15000000,
                        'cuentas': [
                            {
                                'codigo': '1-01-002-001-0001',
                                'nombre_es': 'Facturas por cobrar nacionales',
                                'nombre_en': 'Domestic Receivables',
                                'saldo_final': 12000000
                            },
                            {
                                'codigo': '1-01-002-001-0002',
                                'nombre_es': 'Facturas por cobrar extranjeras',
                                'nombre_en': 'Foreign Receivables',
                                'saldo_final': 3000000
                            }
                        ]
                    }
                },
                'total': 622884264
            },
            'no_corrientes': {
                'nombre_es': 'Activos No Corrientes',
                'nombre_en': 'Non-Current Assets',
                'grupos': {
                    'Property Plant Equipment': {
                        'nombre_es': 'Propiedades, Planta y Equipo',
                        'nombre_en': 'Property, Plant and Equipment',
                        'total': 45000000,
                        'cuentas': [
                            {
                                'codigo': '1-02-001-001-0001',
                                'nombre_es': 'Terrenos',
                                'nombre_en': 'Land',
                                'saldo_final': 20000000
                            },
                            {
                                'codigo': '1-02-001-002-0001',
                                'nombre_es': 'Edificios',
                                'nombre_en': 'Buildings',
                                'saldo_final': 25000000
                            }
                        ]
                    }
                },
                'total': 45000000
            },
            'total_activos': 667884264
        },
        'pasivos': {
            'corrientes': {
                'nombre_es': 'Pasivos Corrientes',
                'nombre_en': 'Current Liabilities',
                'grupos': {
                    'Accounts Payable': {
                        'nombre_es': 'Cuentas por Pagar',
                        'nombre_en': 'Accounts Payable',
                        'total': 25000000,
                        'cuentas': [
                            {
                                'codigo': '2-01-001-001-0001',
                                'nombre_es': 'Proveedores nacionales',
                                'nombre_en': 'Domestic Suppliers',
                                'saldo_final': 20000000
                            },
                            {
                                'codigo': '2-01-001-001-0002',
                                'nombre_es': 'Proveedores extranjeros',
                                'nombre_en': 'Foreign Suppliers',
                                'saldo_final': 5000000
                            }
                        ]
                    }
                },
                'total': 25000000
            },
            'no_corrientes': {
                'nombre_es': 'Pasivos No Corrientes',
                'nombre_en': 'Non-Current Liabilities',
                'grupos': {},
                'total': 0
            },
            'total_pasivos': 25000000
        },
        'patrimonio': {
            'capital': {
                'nombre_es': 'Capital',
                'nombre_en': 'Capital',
                'grupos': {
                    'Share Capital': {
                        'nombre_es': 'Capital Pagado',
                        'nombre_en': 'Paid-in Capital',
                        'total': 176995120,
                        'cuentas': [
                            {
                                'codigo': '3-01-001-001-0001',
                                'nombre_es': 'Capital suscrito y pagado',
                                'nombre_en': 'Subscribed and Paid Capital',
                                'saldo_final': 176995120
                            }
                        ]
                    }
                },
                'total': 176995120
            }
        }
    }

def crear_datos_eri():
    """Crear datos de ERI de prueba"""
    return {
        'ganancia_perdida': {
            'total': 466889144,
            'grupos': {
                'Revenue': {
                    'nombre_es': 'Ingresos',
                    'nombre_en': 'Revenue',
                    'total': 500000000,
                    'cuentas': [
                        {
                            'codigo': '4-01-001-001-0001',
                            'nombre_es': 'Ventas',
                            'nombre_en': 'Sales',
                            'saldo_final': 500000000
                        }
                    ]
                }
            }
        }
    }

def test_excel_espanol():
    """Test generación Excel en español"""
    print("=== Test Excel en Español ===")
    
    datos = crear_datos_prueba_bilingue()
    datos['metadata']['idioma'] = 'es'
    datos_eri = crear_datos_eri()
    
    try:
        workbook = excel_generator.generate_esf_template(
            datos, 
            datos['metadata'], 
            datos_eri
        )
        
        # Guardar archivo
        filename = '/root/SGM/archivosdeprueba/test_esf_espanol.xlsx'
        workbook.save(filename)
        print(f"✓ Excel en español generado: {filename}")
        
    except Exception as e:
        print(f"✗ Error generando Excel en español: {e}")
        import traceback
        traceback.print_exc()

def test_excel_ingles():
    """Test generación Excel en inglés"""
    print("\n=== Test Excel en Inglés ===")
    
    datos = crear_datos_prueba_bilingue()
    datos['metadata']['idioma'] = 'en'
    datos_eri = crear_datos_eri()
    
    try:
        workbook = excel_generator.generate_esf_template(
            datos, 
            datos['metadata'], 
            datos_eri
        )
        
        # Guardar archivo
        filename = '/root/SGM/archivosdeprueba/test_esf_english.xlsx'
        workbook.save(filename)
        print(f"✓ Excel en inglés generado: {filename}")
        
    except Exception as e:
        print(f"✗ Error generando Excel en inglés: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Función principal de prueba"""
    print("Iniciando pruebas de idiomas en Excel templates...")
    
    test_excel_espanol()
    test_excel_ingles()
    
    print("\n=== Pruebas completadas ===")
    print("Archivos generados:")
    print("- /root/SGM/archivosdeprueba/test_esf_espanol.xlsx")
    print("- /root/SGM/archivosdeprueba/test_esf_english.xlsx")

if __name__ == "__main__":
    main()
