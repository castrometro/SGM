#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema modular de Excel templates
"""

import sys
import os
sys.path.append('/root/SGM')

def test_modular_system():
    print("=== PROBANDO SISTEMA MODULAR DE EXCEL TEMPLATES ===")
    
    try:
        # Importar el nuevo sistema modular
        from streamlit_conta.utils.excel import excel_generator
        print("✅ Import del sistema modular exitoso")
        
        # Datos de prueba para ESF
        datos_esf = {
            'metadata': {
                'cliente_id': 1,
                'cliente_nombre': 'Empresa Prueba SA',
                'cierre_id': 123,
                'periodo': '2024-12',
                'moneda': 'CLP',
                'idioma': 'es'
            },
            'activos': {
                'corrientes': {
                    'nombre_es': 'Activos Corrientes',
                    'nombre_en': 'Current Assets',
                    'grupos': {
                        'Cash and Cash Equivalent': {
                            'nombre_es': 'Efectivo y Equivalentes',
                            'nombre_en': 'Cash and Cash Equivalents',
                            'total': 8000000,
                            'cuentas': [
                                {
                                    'codigo': '1-01-001-001-0001',
                                    'nombre_es': 'Caja pesos',
                                    'nombre_en': 'Cash',
                                    'saldo_final': 718815
                                }
                            ]
                        }
                    },
                    'total': 8000000
                },
                'total_activos': 8000000
            },
            'pasivos': {
                'corrientes': {
                    'grupos': {},
                    'total': 0
                },
                'total_pasivos': 0
            },
            'patrimonio': {
                'capital': {
                    'nombre_es': 'Capital',
                    'nombre_en': 'Capital',
                    'grupos': {},
                    'total': 8000000
                }
            }
        }
        
        # Probar generación ESF
        print("🔄 Generando ESF...")
        workbook_esf = excel_generator.generate_esf_template(
            data_esf=datos_esf,
            metadata=datos_esf['metadata']
        )
        print("✅ ESF generado exitosamente")
        
        # Probar generación ERI
        datos_eri = {
            'ganancias_brutas': {
                'grupos': {
                    'Ingresos': {
                        'nombre_es': 'Ingresos Operacionales',
                        'nombre_en': 'Operating Revenue',
                        'total': 1000000,
                        'cuentas': [
                            {
                                'codigo': '4-01-001',
                                'nombre_es': 'Ventas',
                                'nombre_en': 'Sales',
                                'saldo_final': 1000000
                            }
                        ]
                    }
                },
                'total': 1000000
            }
        }
        
        print("🔄 Generando ERI...")
        workbook_eri = excel_generator.generate_eri_template(
            data_eri=datos_eri,
            metadata=datos_esf['metadata']
        )
        print("✅ ERI generado exitosamente")
        
        # Probar conversión a bytes
        print("🔄 Convirtiendo a bytes...")
        bytes_data = excel_generator.workbook_to_bytes(workbook_esf)
        print(f"✅ Conversión exitosa: {len(bytes_data)} bytes")
        
        print("\n🎉 TODAS LAS PRUEBAS DEL SISTEMA MODULAR PASARON")
        return True
        
    except Exception as e:
        print(f"❌ Error en sistema modular: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_system():
    print("\n=== PROBANDO SISTEMA FALLBACK ===")
    
    try:
        # Forzar error para probar fallback
        import streamlit_conta.utils.excel_templates as old_system
        if hasattr(old_system, 'ExcelTemplateGenerator'):
            print("✅ Sistema fallback disponible")
            return True
        else:
            print("⚠️  Sistema fallback no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error en sistema fallback: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando pruebas de sistema modular de Excel...")
    
    # Probar sistema modular
    modular_ok = test_modular_system()
    
    # Probar sistema fallback
    fallback_ok = test_fallback_system()
    
    if modular_ok:
        print("\n🎉 SISTEMA MODULAR FUNCIONANDO CORRECTAMENTE")
        print("El sistema está listo para usar los templates modulares")
    elif fallback_ok:
        print("\n⚠️  USANDO SISTEMA FALLBACK")
        print("El sistema modular tiene problemas, pero el fallback funciona")
    else:
        print("\n❌ AMBOS SISTEMAS FALLARON")
        print("Revisar configuración e imports")
    
    print("\n=== ESTRUCTURA MODULAR CREADA ===")
    print("📁 streamlit_conta/utils/excel/")
    print("├── __init__.py          (Exportaciones y compatibilidad)")
    print("├── base.py              (Clase base con estilos comunes)")
    print("├── translations.py      (Traducciones centralizadas)")
    print("├── esf_template.py      (Template específico ESF)")
    print("├── eri_template.py      (Template específico ERI)")
    print("├── ecp_template.py      (TODO: Template ECP)")
    print("└── movimientos_template.py (TODO: Template movimientos)")
    
    print("\n=== PRÓXIMOS PASOS ===")
    print("1. ✅ Implementar ERI con traducciones")
    print("2. 🔄 Migrar ECP template")
    print("3. 🔄 Migrar movimientos template")
    print("4. 🔄 Actualizar imports en toda la aplicación")
    print("5. 🔄 Eliminar código duplicado del archivo original")
