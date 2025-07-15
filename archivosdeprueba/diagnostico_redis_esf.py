#!/usr/bin/env python3
"""
Script para probar la conexión a Redis y el guardado de datos ESF
"""

import redis
import json
import sys
import os

# Agregar el path del backend Django
sys.path.append('/root/SGM/backend')
sys.path.append('/root/SGM')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from contabilidad.models import CierreContabilidad, ReporteFinanciero

def probar_conexion_redis():
    """Probar las diferentes configuraciones de Redis"""
    
    configuraciones = [
        {
            'nombre': 'Redis DB 0 (localhost)',
            'config': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'decode_responses': True
            }
        },
        {
            'nombre': 'Redis DB 1 (localhost)',
            'config': {
                'host': 'localhost',
                'port': 6379,
                'db': 1,
                'decode_responses': True
            }
        },
        {
            'nombre': 'Redis DB 1 (redis + password)',
            'config': {
                'host': 'redis',
                'port': 6379,
                'db': 1,
                'password': 'Redis_Password_2025!',
                'decode_responses': True,
                'socket_connect_timeout': 10,
                'socket_timeout': 10,
                'retry_on_timeout': True
            }
        },
        {
            'nombre': 'Redis DB 0 (redis + password)',
            'config': {
                'host': 'redis',
                'port': 6379,
                'db': 0,
                'password': 'Redis_Password_2025!',
                'decode_responses': True,
                'socket_connect_timeout': 10,
                'socket_timeout': 10,
                'retry_on_timeout': True
            }
        }
    ]
    
    for config_info in configuraciones:
        print(f"\n🔍 Probando: {config_info['nombre']}")
        
        try:
            redis_client = redis.Redis(**config_info['config'])
            
            # Probar ping
            redis_client.ping()
            print(f"   ✅ Ping exitoso")
            
            # Probar escribir una clave de prueba
            clave_test = "sgm:test:conexion"
            valor_test = json.dumps({
                'timestamp': '2025-07-08T10:00:00',
                'test': True,
                'config': config_info['nombre']
            })
            
            redis_client.set(clave_test, valor_test, ex=60)  # 1 minuto TTL
            print(f"   ✅ Escritura exitosa")
            
            # Probar leer la clave
            valor_leido = redis_client.get(clave_test)
            if valor_leido:
                data = json.loads(valor_leido)
                print(f"   ✅ Lectura exitosa: {data['config']}")
            else:
                print(f"   ❌ No se pudo leer la clave")
            
            # Limpiar
            redis_client.delete(clave_test)
            
            # Buscar claves existentes con patrón ESF
            pattern = "sgm:contabilidad:*:*:*esf*"
            keys = redis_client.keys(pattern)
            print(f"   📋 Claves ESF encontradas: {len(keys)}")
            
            if keys:
                for i, key in enumerate(keys[:3], 1):  # Mostrar máximo 3
                    print(f"      {i}. {key}")
            
            print(f"   🎯 CONFIGURACIÓN VÁLIDA")
            return redis_client, config_info['nombre']
            
        except redis.ConnectionError as e:
            print(f"   ❌ Error de conexión: {e}")
        except redis.AuthenticationError as e:
            print(f"   ❌ Error de autenticación: {e}")
        except Exception as e:
            print(f"   ❌ Error general: {e}")
    
    return None, None

def probar_guardado_esf(redis_client, config_nombre):
    """Probar el guardado de un ESF de prueba"""
    
    print(f"\n🧪 Probando guardado ESF con configuración: {config_nombre}")
    
    # Crear datos ESF de prueba
    datos_esf_prueba = {
        'metadata': {
            'cliente_id': 999,
            'cliente_nombre': 'Cliente de Prueba',
            'cierre_id': 888,
            'periodo': '2025-07',
            'fecha_generacion': '2025-07-08T10:00:00',
            'moneda': 'CLP'
        },
        'activos': {
            'corrientes': {
                'grupos': {
                    'Efectivo y Equivalentes': {
                        'total': 1000000,
                        'cuentas': [
                            {
                                'codigo': '11001',
                                'nombre_es': 'Caja',
                                'nombre_en': 'Cash',
                                'saldo_final': 500000,
                                'movimientos': []
                            },
                            {
                                'codigo': '11002',
                                'nombre_es': 'Banco',
                                'nombre_en': 'Bank',
                                'saldo_final': 500000,
                                'movimientos': []
                            }
                        ]
                    }
                },
                'total': 1000000
            },
            'total_activos': 1000000
        },
        'pasivos': {
            'corrientes': {
                'grupos': {
                    'Cuentas por Pagar': {
                        'total': 300000,
                        'cuentas': [
                            {
                                'codigo': '21001',
                                'nombre_es': 'Proveedores',
                                'nombre_en': 'Suppliers',
                                'saldo_final': 300000,
                                'movimientos': []
                            }
                        ]
                    }
                },
                'total': 300000
            },
            'total_pasivos': 300000
        },
        'patrimonio': {
            'capital': {
                'grupos': {
                    'Capital Pagado': {
                        'total': 700000,
                        'cuentas': [
                            {
                                'codigo': '31001',
                                'nombre_es': 'Capital',
                                'nombre_en': 'Capital',
                                'saldo_final': 700000,
                                'movimientos': []
                            }
                        ]
                    }
                },
                'total': 700000
            },
            'total_patrimonio': 700000
        },
        'totales': {
            'total_pasivos_patrimonio': 1000000,
            'diferencia': 0
        }
    }
    
    try:
        # Guardar bajo la clave de pruebas
        clave_pruebas = f"sgm:contabilidad:999:2025-07:pruebas:esf:finalizacion_automatica"
        
        json_data = json.dumps(datos_esf_prueba, ensure_ascii=False, indent=2)
        redis_client.set(clave_pruebas, json_data, ex=300)  # 5 minutos TTL
        
        print(f"   ✅ ESF de prueba guardado en: {clave_pruebas}")
        print(f"   📊 Tamaño del JSON: {len(json_data)} caracteres")
        
        # Verificar que se guardó
        verificacion = redis_client.get(clave_pruebas)
        if verificacion:
            data_verificada = json.loads(verificacion)
            cliente_nombre = data_verificada['metadata']['cliente_nombre']
            total_activos = data_verificada['activos']['total_activos']
            
            print(f"   ✅ Verificación exitosa:")
            print(f"      Cliente: {cliente_nombre}")
            print(f"      Total Activos: {total_activos:,}")
            
            return True
        else:
            print(f"   ❌ No se pudo verificar el guardado")
            return False
            
    except Exception as e:
        print(f"   ❌ Error guardando ESF: {e}")
        return False

def verificar_reportes_bd():
    """Verificar reportes existentes en la base de datos"""
    
    print(f"\n📊 Verificando reportes en la base de datos...")
    
    try:
        # Contar reportes por estado
        reportes_total = ReporteFinanciero.objects.count()
        reportes_esf = ReporteFinanciero.objects.filter(tipo_reporte='esf').count()
        reportes_completados = ReporteFinanciero.objects.filter(estado='completado').count()
        reportes_error = ReporteFinanciero.objects.filter(estado='error').count()
        
        print(f"   📋 Total reportes: {reportes_total}")
        print(f"   🏛️ Reportes ESF: {reportes_esf}")
        print(f"   ✅ Completados: {reportes_completados}")
        print(f"   ❌ Con error: {reportes_error}")
        
        # Mostrar últimos reportes ESF
        ultimos_esf = ReporteFinanciero.objects.filter(
            tipo_reporte='esf'
        ).select_related('cierre', 'cierre__cliente').order_by('-fecha_actualizacion')[:5]
        
        print(f"\n   📋 Últimos 5 reportes ESF:")
        for i, reporte in enumerate(ultimos_esf, 1):
            cliente_nombre = reporte.cierre.cliente.nombre
            periodo = reporte.cierre.periodo
            estado = reporte.estado
            fecha = reporte.fecha_actualizacion.strftime('%Y-%m-%d %H:%M')
            
            print(f"      {i}. Cliente: {cliente_nombre}, Período: {periodo}, Estado: {estado}, Fecha: {fecha}")
            
            if reporte.estado == 'completado' and reporte.datos:
                # Verificar si tiene metadata
                if isinstance(reporte.datos, dict) and 'metadata' in reporte.datos:
                    print(f"         ✅ Tiene metadata completa")
                else:
                    print(f"         ⚠️ Sin metadata o estructura incompleta")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando BD: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando diagnóstico de Redis y ESF...")
    print("=" * 60)
    
    # Verificar reportes en BD
    verificar_reportes_bd()
    
    # Probar conexiones Redis
    redis_client, config_nombre = probar_conexion_redis()
    
    if redis_client:
        # Probar guardado ESF
        exito_guardado = probar_guardado_esf(redis_client, config_nombre)
        
        if exito_guardado:
            print(f"\n🎯 DIAGNÓSTICO EXITOSO")
            print(f"   Redis funcional con: {config_nombre}")
            print(f"   Guardado ESF confirmado")
        else:
            print(f"\n⚠️ Redis conecta pero falla el guardado")
    else:
        print(f"\n❌ No se pudo establecer conexión a Redis")
        print(f"   Revisa la configuración del contenedor Redis")
    
    print("\n✅ Diagnóstico completado")
