#!/usr/bin/env python3
"""
Script de prueba para verificar la integración completa ESF + ERI en Excel
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

def crear_datos_eri_realistas():
    """Crear datos de prueba del ERI que simulan los reales"""
    return {
        'ganancias_brutas': {
            'nombre_es': 'Ganancias Brutas',
            'grupos': {
                'Ingresos por Ventas': {
                    'total': 1200000000,
                    'cuentas': [
                        {
                            'codigo': '4101001',
                            'nombre_es': 'Ventas Nacionales',
                            'saldo_final': 800000000
                        },
                        {
                            'codigo': '4101002', 
                            'nombre_es': 'Ventas Exportación',
                            'saldo_final': 400000000
                        }
                    ]
                }
            },
            'total': 1200000000
        },
        'ganancia_perdida': {
            'nombre_es': 'Ganancia/Pérdida Operacional',
            'grupos': {
                'Costos de Ventas': {
                    'total': -500000000,
                    'cuentas': [
                        {
                            'codigo': '5001001',
                            'nombre_es': 'Costo de Mercaderías',
                            'saldo_final': -500000000
                        }
                    ]
                },
                'Gastos Operacionales': {
                    'total': -233110856,
                    'cuentas': [
                        {
                            'codigo': '5101001',
                            'nombre_es': 'Gastos de Administración',
                            'saldo_final': -133110856
                        },
                        {
                            'codigo': '5101002',
                            'nombre_es': 'Gastos de Ventas',
                            'saldo_final': -100000000
                        }
                    ]
                }
            },
            'total': -733110856
        },
        'ganancia_perdida_antes_impuestos': {
            'nombre_es': 'Ganancia antes de Impuestos',
            'grupos': {},
            'total': 0
        }
    }

def crear_datos_esf_realistas():
    """Crear datos de prueba del ESF que simulan los reales"""
    return {
        'metadata': {
            'cliente_id': 1,
            'cliente_nombre': 'Empresa de Prueba SA',
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
                            },
                            {
                                'codigo': '1-01-001-001-0004',
                                'nombre_es': 'Crédito consignado para rendir',
                                'nombre_en': 'Bank Account',
                                'saldo_final': 0
                            },
                            {
                                'codigo': '1-01-001-002-0001',
                                'nombre_es': 'Banco Chile CLP',
                                'nombre_en': 'Bank Chile',
                                'saldo_final': 605112931
                            },
                            {
                                'codigo': '1-01-001-002-0006',
                                'nombre_es': 'Banco Santander-Chile',
                                'nombre_en': 'Bank Santander',
                                'saldo_final': 552518
                            },
                            {
                                'codigo': '1-01-001-002-0007',
                                'nombre_es': 'Banco Estado',
                                'nombre_en': 'Banco Estado',
                                'saldo_final': 1500000
                            }
                        ]
                    },
                    'Cuentas por Cobrar': {
                        'nombre_es': 'Cuentas por Cobrar',
                        'nombre_en': 'Accounts Receivable',
                        'total': 15000000,
                        'cuentas': [
                            {
                                'codigo': '1201001',
                                'nombre_es': 'Clientes Nacionales',
                                'nombre_en': 'Domestic Customers',
                                'saldo_final': 15000000
                            }
                        ]
                    }
                },
                'total': 23000000
            },
            'no_corrientes': {
                'nombre_es': 'Activos No Corrientes',
                'nombre_en': 'Non-Current Assets',
                'grupos': {
                    'Propiedades, Planta y Equipo': {
                        'nombre_es': 'Propiedades, Planta y Equipo',
                        'nombre_en': 'Property, Plant and Equipment',
                        'total': 45000000,
                        'cuentas': [
                            {
                                'codigo': '1501001',
                                'nombre_es': 'Terrenos',
                                'nombre_en': 'Land',
                                'saldo_final': 20000000
                            },
                            {
                                'codigo': '1502001',
                                'nombre_es': 'Edificios',
                                'nombre_en': 'Buildings',
                                'saldo_final': 25000000
                            }
                        ]
                    }
                },
                'total': 45000000
            },
            'total_activos': 68000000
        },
        'pasivos': {
            'corrientes': {
                'nombre_es': 'Pasivos Corrientes',
                'nombre_en': 'Current Liabilities',
                'grupos': {
                    'Cuentas por Pagar': {
                        'nombre_es': 'Cuentas por Pagar',
                        'nombre_en': 'Accounts Payable',
                        'total': 5000000,
                        'cuentas': [
                            {
                                'codigo': '2101001',
                                'nombre_es': 'Proveedores',
                                'nombre_en': 'Suppliers',
                                'saldo_final': 5000000
                            }
                        ]
                    }
                },
                'total': 5000000
            },
            'no_corrientes': {
                'nombre_es': 'Pasivos No Corrientes',
                'nombre_en': 'Non-Current Liabilities',
                'grupos': {},
                'total': 0
            },
            'total_pasivos': 5000000
        },
        'patrimonio': {
            'capital': {
                'nombre_es': 'Capital',
                'nombre_en': 'Capital',
                'grupos': {
                    'Capital Pagado': {
                        'nombre_es': 'Capital Pagado',
                        'nombre_en': 'Paid Capital',
                        'total': 50000000,
                        'cuentas': [
                            {
                                'codigo': '3101001',
                                'nombre_es': 'Capital Inicial',
                                'nombre_en': 'Initial Capital',
                                'saldo_final': 50000000
                            }
                        ]
                    },
                    'Utilidades Retenidas': {
                        'nombre_es': 'Utilidades Retenidas',
                        'nombre_en': 'Retained Earnings',
                        'total': 13000000,
                        'cuentas': [
                            {
                                'codigo': '3201001',
                                'nombre_es': 'Utilidades Ejercicios Anteriores',
                                'nombre_en': 'Prior Years Earnings',
                                'saldo_final': 13000000
                            }
                        ]
                    }
                },
                'total': 63000000
            },
            'total_patrimonio': 63000000
        },
        'totales': {
            'total_pasivos_patrimonio': 68000000,
            'diferencia': 0
        }
    }

def probar_integracion_esf_eri():
    """Probar la integración completa ESF + ERI en Excel"""
    print("🧪 PROBANDO INTEGRACIÓN ESF + ERI EN EXCEL")
    print("=" * 70)
    
    # Crear datos de prueba
    data_esf = crear_datos_esf_realistas()
    data_eri = crear_datos_eri_realistas()
    metadata = {
        'cliente_nombre': 'Empresa de Prueba SA',
        'periodo': 'Diciembre 2024',
        'moneda': 'CLP',
        'idioma': 'Español'
    }
    
    # Calcular total ERI esperado
    total_eri = 1200000000 - 733110856  # Ganancias brutas - gastos = 466,889,144
    print(f"💰 TOTAL ERI CALCULADO ESPERADO: ${total_eri:,.0f} CLP")
    
    # Calcular patrimonio total esperado
    patrimonio_original = 63000000
    patrimonio_con_eri = patrimonio_original + total_eri
    print(f"🏦 PATRIMONIO ORIGINAL: ${patrimonio_original:,.0f} CLP")
    print(f"🏦 PATRIMONIO CON ERI: ${patrimonio_con_eri:,.0f} CLP")
    print()
    
    # Generar Excel
    try:
        generator = ExcelTemplateGenerator()
        workbook = generator.generate_esf_template(data_esf, metadata, data_eri)
        
        # Guardar archivo de prueba
        output_path = '/root/SGM/archivosdeprueba/test_esf_completo_con_eri.xlsx'
        workbook.save(output_path)
        
        print(f"✅ Excel generado exitosamente: {output_path}")
        
        # Verificar contenido específico
        ws = workbook.active
        print("\n📋 BÚSQUEDA DE CONTENIDO ESPECÍFICO:")
        
        # Buscar líneas importantes
        lineas_importantes = []
        for row in range(1, ws.max_row + 1):
            cell_a = ws.cell(row=row, column=1)
            cell_b = ws.cell(row=row, column=2)
            
            if cell_a.value:
                valor_celda = str(cell_a.value).lower()
                if any(palabra in valor_celda for palabra in [
                    'total activos', 'total pasivos', 'total patrimonio', 
                    'total pasivos y patrimonio', 'ganancia', 'pérdida', 
                    'resultado del ejercicio', 'diferencia'
                ]):
                    lineas_importantes.append({
                        'fila': row,
                        'concepto': cell_a.value,
                        'valor': cell_b.value if cell_b.value else ''
                    })
        
        print("📊 LÍNEAS IMPORTANTES ENCONTRADAS:")
        for linea in lineas_importantes:
            print(f"  Fila {linea['fila']:2d}: {linea['concepto']} | {linea['valor']}")
        
        # Verificar balance
        total_activos_encontrado = None
        total_pasivos_patrimonio_encontrado = None
        
        for linea in lineas_importantes:
            if 'total activos' in str(linea['concepto']).lower() and 'patrimonio' not in str(linea['concepto']).lower():
                total_activos_encontrado = linea['valor']
            elif 'total pasivos y patrimonio' in str(linea['concepto']).lower():
                total_pasivos_patrimonio_encontrado = linea['valor']
        
        print(f"\n⚖️  VERIFICACIÓN DE BALANCE:")
        print(f"  - Total Activos: {total_activos_encontrado}")
        print(f"  - Total Pasivos y Patrimonio: {total_pasivos_patrimonio_encontrado}")
        
        if total_activos_encontrado and total_pasivos_patrimonio_encontrado:
            if total_activos_encontrado == total_pasivos_patrimonio_encontrado:
                print("  ✅ EL BALANCE CUADRA CORRECTAMENTE")
            else:
                print("  ⚠️  EL BALANCE NO CUADRA")
        else:
            print("  ❓ No se pudieron verificar los totales")
        
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"  - Total filas: {ws.max_row}")
        print(f"  - Total columnas: {ws.max_column}")
        print(f"  - Hojas: {workbook.sheetnames}")
        
        return True, output_path
        
    except Exception as e:
        print(f"❌ Error al generar Excel: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBA DE INTEGRACIÓN ESF + ERI")
    print("=" * 70)
    
    success, output_path = probar_integracion_esf_eri()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print(f"📁 Archivo generado: {output_path}")
        print("🔍 Verifica que aparezca:")
        print("   - Ganancia/Pérdida del Ejercicio (Del ERI): $466,889,144")
        print("   - Total Patrimonio incluya este monto")
    else:
        print("❌ PRUEBA FALLÓ")
    
    return success

if __name__ == "__main__":
    main()
