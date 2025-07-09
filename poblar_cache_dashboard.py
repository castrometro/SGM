#!/usr/bin/env python3
"""
Script para poblar el cache Redis con datos de ejemplo para el dashboard de Streamlit
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal

# Agregar el directorio del backend al path
sys.path.insert(0, '/root/SGM/backend')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
import django
django.setup()

from contabilidad.cache_redis import get_cache_system

def crear_datos_ejemplo_esf():
    """Crear datos de ejemplo para el ESF"""
    return {
        'metadata': {
            'cliente_id': 1,
            'cliente_nombre': 'Empresa Demo SGM',
            'cierre_id': 1,
            'periodo': '2025-07',
            'fecha_generacion': datetime.now().isoformat(),
            'moneda': 'CLP'
        },
        'activos': {
            'corrientes': {
                'grupos': {
                    'efectivo_equivalentes': {
                        'total': 25000000,
                        'cuentas': [
                            {'codigo': '1101', 'nombre': 'Caja', 'saldo': 1000000},
                            {'codigo': '1102', 'nombre': 'Banco Estado', 'saldo': 24000000}
                        ]
                    },
                    'cuentas_por_cobrar': {
                        'total': 45000000,
                        'cuentas': [
                            {'codigo': '1201', 'nombre': 'Clientes', 'saldo': 40000000},
                            {'codigo': '1202', 'nombre': 'Documentos por Cobrar', 'saldo': 5000000}
                        ]
                    },
                    'inventarios': {
                        'total': 30000000,
                        'cuentas': [
                            {'codigo': '1301', 'nombre': 'Mercaderías', 'saldo': 30000000}
                        ]
                    }
                },
                'total': 100000000
            },
            'no_corrientes': {
                'grupos': {
                    'propiedad_planta_equipo': {
                        'total': 80000000,
                        'cuentas': [
                            {'codigo': '1501', 'nombre': 'Terrenos', 'saldo': 40000000},
                            {'codigo': '1502', 'nombre': 'Edificios', 'saldo': 30000000},
                            {'codigo': '1503', 'nombre': 'Maquinaria', 'saldo': 10000000}
                        ]
                    },
                    'inversiones_largo_plazo': {
                        'total': 20000000,
                        'cuentas': [
                            {'codigo': '1601', 'nombre': 'Inversiones Financieras', 'saldo': 20000000}
                        ]
                    }
                },
                'total': 100000000
            },
            'total_activos': 200000000
        },
        'pasivos': {
            'corrientes': {
                'grupos': {
                    'cuentas_por_pagar': {
                        'total': 35000000,
                        'cuentas': [
                            {'codigo': '2101', 'nombre': 'Proveedores', 'saldo': 30000000},
                            {'codigo': '2102', 'nombre': 'Documentos por Pagar', 'saldo': 5000000}
                        ]
                    },
                    'obligaciones_laborales': {
                        'total': 15000000,
                        'cuentas': [
                            {'codigo': '2201', 'nombre': 'Sueldos por Pagar', 'saldo': 10000000},
                            {'codigo': '2202', 'nombre': 'Provisiones Laborales', 'saldo': 5000000}
                        ]
                    }
                },
                'total': 50000000
            },
            'no_corrientes': {
                'grupos': {
                    'deudas_largo_plazo': {
                        'total': 40000000,
                        'cuentas': [
                            {'codigo': '2301', 'nombre': 'Préstamos Bancarios LP', 'saldo': 40000000}
                        ]
                    }
                },
                'total': 40000000
            },
            'total_pasivos': 90000000
        },
        'patrimonio': {
            'capital': {
                'grupos': {
                    'capital_social': {
                        'total': 80000000,
                        'cuentas': [
                            {'codigo': '3101', 'nombre': 'Capital Pagado', 'saldo': 80000000}
                        ]
                    }
                },
                'total': 80000000
            },
            'resultados': {
                'grupos': {
                    'utilidades_retenidas': {
                        'total': 30000000,
                        'cuentas': [
                            {'codigo': '3201', 'nombre': 'Utilidades Acumuladas', 'saldo': 30000000}
                        ]
                    }
                },
                'total': 30000000
            },
            'total_patrimonio': 110000000
        },
        'totales': {
            'total_pasivos_patrimonio': 200000000,
            'diferencia': 0
        }
    }

def crear_datos_ejemplo_esr():
    """Crear datos de ejemplo para el ESR"""
    return {
        'metadata': {
            'cliente_id': 1,
            'periodo': '2025-07',
            'fecha_generacion': datetime.now().isoformat(),
            'moneda': 'CLP'
        },
        'ingresos': {
            'grupos': {
                'ingresos_operacionales': {
                    'total': 150000000,
                    'cuentas': [
                        {'codigo': '4101', 'nombre': 'Ventas', 'saldo': 145000000},
                        {'codigo': '4102', 'nombre': 'Servicios', 'saldo': 5000000}
                    ]
                },
                'otros_ingresos': {
                    'total': 5000000,
                    'cuentas': [
                        {'codigo': '4201', 'nombre': 'Ingresos Financieros', 'saldo': 5000000}
                    ]
                }
            },
            'total': 155000000
        },
        'gastos': {
            'grupos': {
                'costo_ventas': {
                    'total': -90000000,
                    'cuentas': [
                        {'codigo': '5101', 'nombre': 'Costo de Mercaderías', 'saldo': -90000000}
                    ]
                },
                'gastos_operacionales': {
                    'total': -40000000,
                    'cuentas': [
                        {'codigo': '5201', 'nombre': 'Gastos Administrativos', 'saldo': -25000000},
                        {'codigo': '5202', 'nombre': 'Gastos de Ventas', 'saldo': -15000000}
                    ]
                }
            },
            'total': -130000000
        },
        'resultado_periodo': 25000000,
        'margen_bruto': 38.7,  # (155M - 90M) / 155M * 100
        'margen_neto': 16.1    # 25M / 155M * 100
    }

def crear_datos_ejemplo_kpis():
    """Crear datos de ejemplo para KPIs"""
    return {
        'total_cuentas': 25,
        'total_movimientos': 1250,
        'total_transacciones': 850,
        'periodo_dias': 31,
        'promedio_transacciones_dia': 27.4,
        'total_debe': 2500000000,
        'total_haber': 2500000000,
        'diferencia_cuadre': 0,
        'cuentas_con_movimientos': 23,
        'cuentas_sin_movimientos': 2,
        'porcentaje_cuentas_activas': 92.0,
        'mayor_movimiento_debe': 150000000,
        'mayor_movimiento_haber': 145000000,
        'fecha_ultimo_movimiento': '2025-07-31',
        'fecha_primer_movimiento': '2025-07-01'
    }

def crear_datos_ejemplo_alertas():
    """Crear datos de ejemplo para alertas"""
    return [
        {
            'tipo': 'info',
            'mensaje': 'Cierre procesado exitosamente',
            'fecha': datetime.now().isoformat(),
            'categoria': 'procesamiento'
        },
        {
            'tipo': 'warning',
            'mensaje': 'Se encontraron 2 cuentas nuevas en el período',
            'fecha': datetime.now().isoformat(),
            'categoria': 'cuentas'
        },
        {
            'tipo': 'info',
            'mensaje': 'Balance cuadrado correctamente',
            'fecha': datetime.now().isoformat(),
            'categoria': 'balance'
        }
    ]

def crear_datos_ejemplo_procesamiento():
    """Crear datos de ejemplo para estado de procesamiento"""
    return {
        'estado': 'completado',
        'progreso': 100,
        'fecha_inicio': '2025-07-01T10:00:00',
        'fecha_fin': '2025-07-01T10:15:00',
        'tiempo_total_segundos': 900,
        'pasos_completados': [
            'Carga de archivo',
            'Parsing de movimientos',
            'Validación de datos',
            'Clasificación de cuentas',
            'Generación de reportes',
            'Finalización'
        ],
        'errores': [],
        'warnings': ['2 cuentas nuevas detectadas'],
        'metricas': {
            'lineas_procesadas': 1250,
            'movimientos_creados': 1250,
            'cuentas_procesadas': 25,
            'velocidad_procesamiento': 83.3  # movimientos por minuto
        }
    }

def poblar_cache_redis():
    """Poblar el cache Redis con datos de ejemplo"""
    print("🔄 Iniciando poblado del cache Redis...")
    
    try:
        # Obtener sistema de cache
        cache_system = get_cache_system()
        
        if not cache_system.check_connection():
            print("❌ No se pudo conectar a Redis")
            return False
        
        print("✅ Conectado a Redis")
        
        # Configuración de datos
        cliente_id = 1
        periodo = "2025-07"
        
        # 1. Guardar ESF
        print("📊 Guardando Estado de Situación Financiera...")
        esf_data = crear_datos_ejemplo_esf()
        if cache_system.set_estado_financiero(cliente_id, periodo, 'esf', esf_data):
            print("✅ ESF guardado exitosamente")
        else:
            print("❌ Error guardando ESF")
        
        # 2. Guardar ESR
        print("📈 Guardando Estado de Resultados...")
        esr_data = crear_datos_ejemplo_esr()
        if cache_system.set_estado_financiero(cliente_id, periodo, 'esr', esr_data):
            print("✅ ESR guardado exitosamente")
        else:
            print("❌ Error guardando ESR")
        
        # 3. Guardar KPIs
        print("📊 Guardando KPIs...")
        kpis_data = crear_datos_ejemplo_kpis()
        if cache_system.set_kpis(cliente_id, periodo, kpis_data):
            print("✅ KPIs guardados exitosamente")
        else:
            print("❌ Error guardando KPIs")
        
        # 4. Guardar alertas
        print("⚠️ Guardando alertas...")
        alertas_data = crear_datos_ejemplo_alertas()
        if cache_system.set_alertas(cliente_id, periodo, alertas_data):
            print("✅ Alertas guardadas exitosamente")
        else:
            print("❌ Error guardando alertas")
        
        # 5. Guardar estado de procesamiento
        print("⚙️ Guardando estado de procesamiento...")
        procesamiento_data = crear_datos_ejemplo_procesamiento()
        if cache_system.set_procesamiento_status(cliente_id, periodo, procesamiento_data):
            print("✅ Estado de procesamiento guardado exitosamente")
        else:
            print("❌ Error guardando estado de procesamiento")
        
        # 6. Verificar datos guardados
        print("\n🔍 Verificando datos guardados...")
        
        # Verificar ESF
        esf_verificado = cache_system.get_estado_financiero(cliente_id, periodo, 'esf')
        if esf_verificado:
            print(f"✅ ESF verificado: {len(esf_verificado)} keys")
        else:
            print("❌ ESF no se pudo verificar")
        
        # Verificar KPIs
        kpis_verificados = cache_system.get_kpis(cliente_id, periodo)
        if kpis_verificados:
            print(f"✅ KPIs verificados: {len(kpis_verificados)} indicadores")
        else:
            print("❌ KPIs no se pudieron verificar")
        
        # Mostrar estadísticas de cache
        print("\n📊 Estadísticas del cache:")
        stats = cache_system.get_cache_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        print("\n🎉 ¡Poblado del cache completado exitosamente!")
        print(f"📋 Datos disponibles para cliente {cliente_id}, período {periodo}")
        print("\n💡 Ahora puedes usar el dashboard de Streamlit con:")
        print("   • Fuente: Sistema de Cierre")
        print(f"   • Cliente ID: {cliente_id}")
        print(f"   • Período: {periodo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el poblado: {e}")
        return False

if __name__ == "__main__":
    poblar_cache_redis()
