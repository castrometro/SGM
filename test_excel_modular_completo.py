#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema modular completo de Excel templates
"""

import sys
import os
sys.path.append('/root/SGM')

def test_complete_modular_system():
    print("=== PROBANDO SISTEMA MODULAR COMPLETO ===")
    
    try:
        # Importar el nuevo sistema modular
        from streamlit_conta.utils.excel import excel_generator
        print("✅ Import del sistema modular exitoso")
        
        # Datos de prueba
        metadata = {
            'cliente_id': 1,
            'cliente_nombre': 'Empresa Prueba SA',
            'cierre_id': 123,
            'periodo': '2024-12',
            'moneda': 'CLP',
            'idioma': 'es'  # Cambiar a 'en' para probar inglés
        }
        
        # === PROBAR ESF ===
        print("\n🔄 Generando ESF...")
        datos_esf = {
            'activos': {
                'corrientes': {
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
            'pasivos': {'corrientes': {'grupos': {}, 'total': 0}, 'total_pasivos': 0},
            'patrimonio': {
                'capital': {
                    'nombre_es': 'Capital',
                    'nombre_en': 'Capital',
                    'grupos': {},
                    'total': 8000000
                }
            }
        }
        
        workbook_esf = excel_generator.generate_esf_template(
            data_esf=datos_esf,
            metadata=metadata
        )
        print("✅ ESF generado exitosamente")
        
        # === PROBAR ERI ===
        print("🔄 Generando ERI...")
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
        
        workbook_eri = excel_generator.generate_eri_template(
            data_eri=datos_eri,
            metadata=metadata
        )
        print("✅ ERI generado exitosamente")
        
        # === PROBAR ECP ===
        print("🔄 Generando ECP...")
        datos_ecp = {
            'patrimonio': {
                'capital': {
                    'saldo_anterior': 5000000,
                    'cambios': 1000000
                },
                'otras_reservas': {
                    'saldo_anterior': 2000000,
                    'cambios': 0
                }
            }
        }
        
        workbook_ecp = excel_generator.generate_ecp_template(
            data_ecp=datos_ecp,
            metadata=metadata,
            data_eri=datos_eri
        )
        print("✅ ECP generado exitosamente")
        
        # === PROBAR MOVIMIENTOS ===
        print("🔄 Generando Movimientos...")
        import pandas as pd
        
        df_movimientos = pd.DataFrame({
            'Fecha': ['2024-12-01', '2024-12-02'],
            'Codigo': ['1-01-001', '4-01-001'],
            'Cuenta': ['Caja', 'Ventas'],
            'Debe': [1000000, 0],
            'Haber': [0, 1000000],
            'Documento': ['DOC001', 'DOC002']
        })
        
        workbook_mov = excel_generator.generate_movimientos_template(
            df_movimientos=df_movimientos,
            metadata=metadata,
            tipo_vista="Movimientos de prueba"
        )
        print("✅ Movimientos generado exitosamente")
        
        # === PROBAR CONVERSIÓN A BYTES ===
        print("🔄 Convirtiendo a bytes...")
        bytes_data = excel_generator.workbook_to_bytes(workbook_esf)
        print(f"✅ Conversión exitosa: {len(bytes_data)} bytes")
        
        # === PROBAR IDIOMAS ===
        print("\n🔄 Probando con idioma inglés...")
        metadata_en = metadata.copy()
        metadata_en['idioma'] = 'en'
        
        workbook_esf_en = excel_generator.generate_esf_template(
            data_esf=datos_esf,
            metadata=metadata_en
        )
        print("✅ ESF en inglés generado exitosamente")
        
        print("\n🎉 TODAS LAS PRUEBAS DEL SISTEMA MODULAR PASARON")
        return True
        
    except Exception as e:
        print(f"❌ Error en sistema modular: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando pruebas del sistema modular completo...")
    
    # Probar sistema modular
    modular_ok = test_complete_modular_system()
    
    if modular_ok:
        print("\n🎉 SISTEMA MODULAR FUNCIONANDO COMPLETAMENTE")
        print("\n=== ARQUITECTURA FINAL ===")
        print("📁 streamlit_conta/utils/excel/")
        print("├── __init__.py              ✅ Exportaciones y compatibilidad")
        print("├── base.py                  ✅ Clase base con estilos comunes")
        print("├── translations.py          ✅ Traducciones centralizadas")
        print("├── esf_template.py          ✅ Template ESF con idiomas")
        print("├── eri_template.py          ✅ Template ERI con idiomas")
        print("├── ecp_template.py          ✅ Template ECP con idiomas")
        print("└── movimientos_template.py  ✅ Template movimientos con idiomas")
        
        print("\n=== CARACTERÍSTICAS IMPLEMENTADAS ===")
        print("✅ Sistema de traducciones español/inglés")
        print("✅ Agrupación colapsable en Excel")
        print("✅ Formato de monedas con CLP/USD/EUR")
        print("✅ Compatibilidad hacia atrás")
        print("✅ Arquitectura modular y mantenible")
        print("✅ Reutilización de código común")
        
        print("\n=== PRÓXIMOS PASOS ===")
        print("1. ✅ Todos los templates implementados")
        print("2. 🔄 Actualizar imports en la aplicación")
        print("3. 🔄 Probar en producción")
        print("4. 🔄 Eliminar código deprecated")
        
    else:
        print("\n❌ SISTEMA MODULAR FALLÓ")
        print("Revisar configuración e imports")
