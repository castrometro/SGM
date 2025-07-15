#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del Excel ESF con patrimonio
"""

import os
import sys
import logging
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Importar después de configurar Django
from streamlit_conta.utils.excel_templates import ExcelTemplateGenerator

def crear_datos_eri_prueba():
    """Crear datos de prueba del ERI"""
    return {
        'ganancias_brutas': {
            'nombre_es': 'Ganancias Brutas',
            'grupos': {
                'Ingresos por Ventas': {
                    'total': 800000000,
                    'cuentas': [
                        {
                            'codigo': '4101001',
                            'nombre_es': 'Ventas Nacionales',
                            'saldo_final': 800000000
                        }
                    ]
                }
            },
            'total': 800000000
        },
        'ganancia_perdida': {
            'nombre_es': 'Ganancia/Pérdida Operacional',
            'grupos': {
                'Gastos Operacionales': {
                    'total': -333110856,
                    'cuentas': [
                        {
                            'codigo': '5101001',
                            'nombre_es': 'Gastos de Administración',
                            'saldo_final': -333110856
                        }
                    ]
                }
            },
            'total': -333110856
        },
        'ganancia_perdida_antes_impuestos': {
            'nombre_es': 'Ganancia antes de Impuestos',
            'grupos': {},
            'total': 0
        }
    }

def crear_datos_esf_prueba():
    """Crear datos de prueba que simulan la estructura real del ESF"""
    return {
        'metadata': {
            'cliente_id': 1,
            'cliente_nombre': 'Empresa de Prueba',
            'cierre_id': 123,
            'periodo': '2024-12',
            'fecha_generacion': datetime.now().isoformat(),
            'moneda': 'CLP',
            'es_bilingue': False
        },
        'activos': {
            'corrientes': {
                'nombre_es': 'Activos Corrientes',
                'nombre_en': 'Current Assets',
                'grupos': {
                    'Efectivo y Equivalentes': {
                        'nombre_es': 'Efectivo y Equivalentes',
                        'nombre_en': 'Cash and Cash Equivalents',
                        'total': 5000000,
                        'cuentas': [
                            {
                                'codigo': '1101001',
                                'nombre_es': 'Caja',
                                'nombre_en': 'Cash',
                                'saldo_final': 1000000
                            },
                            {
                                'codigo': '1101002',
                                'nombre_es': 'Banco Estado',
                                'nombre_en': 'Bank Account',
                                'saldo_final': 4000000
                            }
                        ]
                    }
                },
                'total': 5000000
            },
            'no_corrientes': {
                'nombre_es': 'Activos No Corrientes',
                'nombre_en': 'Non-Current Assets',
                'grupos': {},
                'total': 0
            },
            'total_activos': 5000000
        },
        'pasivos': {
            'corrientes': {
                'nombre_es': 'Pasivos Corrientes',
                'nombre_en': 'Current Liabilities',
                'grupos': {},
                'total': 0
            },
            'no_corrientes': {
                'nombre_es': 'Pasivos No Corrientes',
                'nombre_en': 'Non-Current Liabilities',
                'grupos': {},
                'total': 0
            },
            'total_pasivos': 0
        },
        'patrimonio': {
            'capital': {
                'nombre_es': 'Capital',
                'nombre_en': 'Capital',
                'grupos': {
                    'Capital Pagado': {
                        'nombre_es': 'Capital Pagado',
                        'nombre_en': 'Paid Capital',
                        'total': 3000000,
                        'cuentas': [
                            {
                                'codigo': '3101001',
                                'nombre_es': 'Capital Inicial',
                                'nombre_en': 'Initial Capital',
                                'saldo_final': 3000000
                            }
                        ]
                    },
                    'Utilidades Retenidas': {
                        'nombre_es': 'Utilidades Retenidas',
                        'nombre_en': 'Retained Earnings',
                        'total': 2000000,
                        'cuentas': [
                            {
                                'codigo': '3201001',
                                'nombre_es': 'Utilidades del Ejercicio',
                                'nombre_en': 'Current Year Earnings',
                                'saldo_final': 2000000
                            }
                        ]
                    }
                },
                'total': 5000000
            },
            'total_patrimonio': 5000000
        },
        'totales': {
            'total_pasivos_patrimonio': 5000000,
            'diferencia': 0
        }
    }

def probar_excel_patrimonio():
    """Probar la generación de Excel con datos de patrimonio"""
    print("🧪 PROBANDO CORRECCIÓN DE EXCEL PATRIMONIO")
    print("=" * 60)
    
    # Crear datos de prueba
    data_esf = crear_datos_esf_prueba()
    data_eri = crear_datos_eri_prueba()
    metadata = {
        'cliente_nombre': 'Empresa de Prueba SA',
        'periodo': 'Diciembre 2024',
        'moneda': 'CLP',
        'idioma': 'Español'
    }
    
    # Calcular total ERI
    total_eri = 800000000 - 333110856  # Ganancias brutas - gastos = 466,889,144
    print(f"💰 TOTAL ERI CALCULADO: ${total_eri:,.0f} CLP")
    
    # Mostrar estructura de patrimonio
    print("📊 ESTRUCTURA DE PATRIMONIO:")
    print(json.dumps(data_esf['patrimonio'], indent=2, ensure_ascii=False))
    print()
    
    # Generar Excel
    try:
        generator = ExcelTemplateGenerator()
        workbook = generator.generate_esf_template(data_esf, metadata, data_eri)
        
        # Guardar archivo de prueba
        output_path = '/root/SGM/archivosdeprueba/test_esf_patrimonio_con_eri.xlsx'
        workbook.save(output_path)
        
        print(f"✅ Excel generado exitosamente: {output_path}")
        
        # Verificar contenido
        ws = workbook.active
        print("\n📋 CONTENIDO DEL EXCEL:")
        for row in range(1, min(50, ws.max_row + 1)):  # Mostrar primeras 50 filas
            row_data = []
            for col in range(1, min(5, ws.max_column + 1)):  # Primeras 5 columnas
                cell = ws.cell(row=row, column=col)
                if cell.value:
                    row_data.append(str(cell.value))
            if row_data:
                print(f"Fila {row:2d}: {' | '.join(row_data)}")
        
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"  - Total filas: {ws.max_row}")
        print(f"  - Total columnas: {ws.max_column}")
        print(f"  - Hojas: {workbook.sheetnames}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBA DE CORRECCIÓN EXCEL PATRIMONIO")
    print("=" * 70)
    
    success = probar_excel_patrimonio()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("📁 Archivo generado: /root/SGM/archivosdeprueba/test_esf_patrimonio.xlsx")
    else:
        print("❌ PRUEBA FALLÓ")
    
    return success

if __name__ == "__main__":
    main()
