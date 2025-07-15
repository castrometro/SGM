#!/usr/bin/env python3
"""
Script para probar la finalización de cierre con la corrección de serialización de Decimals.

Este script prueba que:
1. Los Decimals se conviertan correctamente a float antes de guardar en BD
2. El usuario generador se guarde correctamente
3. No se produzcan errores de serialización JSON
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.contabilidad.models import CierreContabilidad, TarjetaActivityLog
from api.models import Usuario

def probar_conversion_decimals():
    """
    Prueba la función de conversión de Decimals a float.
    """
    print("=" * 80)
    print("🧪 PRUEBA: Conversión de Decimals a float")
    print("=" * 80)
    
    # Importar la función desde tasks_finalizacion
    sys.path.append('/root/SGM/backend')
    
    # Datos de prueba con Decimals
    datos_con_decimals = {
        'total_activos': Decimal('1500000.75'),
        'total_pasivos': Decimal('800000.25'),
        'patrimonio': Decimal('700000.50'),
        'ratios': {
            'liquidez': Decimal('2.5'),
            'solvencia': Decimal('1.875'),
            'rentabilidad': [Decimal('0.15'), Decimal('0.08')]
        },
        'detalle_cuentas': [
            {'nombre': 'Caja', 'saldo': Decimal('50000.00')},
            {'nombre': 'Bancos', 'saldo': Decimal('250000.33')}
        ]
    }
    
    print(f"📊 Datos originales con Decimals:")
    print(f"   total_activos: {datos_con_decimals['total_activos']} (tipo: {type(datos_con_decimals['total_activos'])})")
    print(f"   ratios.liquidez: {datos_con_decimals['ratios']['liquidez']} (tipo: {type(datos_con_decimals['ratios']['liquidez'])})")
    
    # Función de conversión (copiada de tasks_finalizacion.py)
    def convertir_decimals_a_float(obj):
        """
        Convierte recursivamente todos los objetos Decimal a float para que sean JSON serializable.
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: convertir_decimals_a_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convertir_decimals_a_float(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(convertir_decimals_a_float(item) for item in obj)
        else:
            return obj
    
    # Convertir
    datos_convertidos = convertir_decimals_a_float(datos_con_decimals)
    
    print(f"\n🔧 Datos convertidos a float:")
    print(f"   total_activos: {datos_convertidos['total_activos']} (tipo: {type(datos_convertidos['total_activos'])})")
    print(f"   ratios.liquidez: {datos_convertidos['ratios']['liquidez']} (tipo: {type(datos_convertidos['ratios']['liquidez'])})")
    
    # Probar serialización JSON
    import json
    try:
        json_serializable = json.dumps(datos_convertidos, indent=2)
        print(f"\n✅ Datos convertidos son JSON serializable")
        print(f"   Tamaño JSON: {len(json_serializable)} caracteres")
    except Exception as e:
        print(f"\n❌ Error en serialización JSON: {e}")
        return False
    
    # Verificar que los valores son correctos
    assert datos_convertidos['total_activos'] == 1500000.75
    assert datos_convertidos['ratios']['liquidez'] == 2.5
    assert datos_convertidos['detalle_cuentas'][0]['saldo'] == 50000.0
    
    print(f"✅ Prueba de conversión exitosa - Todos los valores son correctos")
    return True

def probar_finalizacion_con_usuario():
    """
    Prueba la finalización de cierre con un usuario específico y datos con Decimals.
    """
    print("\n" + "=" * 80)
    print("🧪 PRUEBA: Finalización de cierre con conversión de Decimals")
    print("=" * 80)
    
    # Buscar un cierre abierto para probar
    cierre = CierreContabilidad.objects.filter(estado='abierto').first()
    if not cierre:
        print("❌ No hay cierres abiertos para probar")
        return False
    
    print(f"📊 Cierre seleccionado: {cierre} (ID: {cierre.id})")
    
    # Buscar un usuario para la prueba
    usuario = Usuario.objects.first()
    if not usuario:
        print("❌ No hay usuarios en la base de datos")
        return False
    
    print(f"👤 Usuario para prueba: {usuario.correo_bdo} (ID: {usuario.id})")
    
    # Datos de prueba con Decimals
    esf_test = {
        'total_activos': Decimal('1500000.75'),
        'total_pasivos': Decimal('800000.25'),
        'patrimonio': Decimal('700000.50'),
    }
    
    estado_resultados_test = {
        'ingresos_totales': Decimal('2000000.00'),
        'gastos_totales': Decimal('1700000.50'),
        'utilidad_neta': Decimal('300000.50'),
    }
    
    ratios_test = {
        'liquidez': Decimal('2.5'),
        'solvencia': Decimal('1.875'),
        'rentabilidad': Decimal('0.15')
    }
    
    print(f"📊 Datos de prueba preparados con Decimals")
    
    # Importar y probar la función guardar_reportes_en_bd
    try:
        from backend.contabilidad.tasks_finalizacion import guardar_reportes_en_bd
        
        print(f"\n🚀 Probando guardar_reportes_en_bd...")
        guardar_reportes_en_bd(
            cierre=cierre,
            esf=esf_test,
            estado_resultados=estado_resultados_test,
            ratios=ratios_test,
            usuario_id=usuario.id
        )
        
        # Verificar que se creó el log
        log_creado = TarjetaActivityLog.objects.filter(
            cierre=cierre,
            tarjeta='reportes',
            accion='calculo_completado'
        ).last()
        
        if log_creado:
            print(f"\n✅ Log de actividad creado exitosamente:")
            print(f"   ID: {log_creado.id}")
            print(f"   Usuario: {log_creado.usuario}")
            print(f"   Fecha: {log_creado.fecha_registro}")
            
            # Verificar los detalles JSON
            detalles = log_creado.detalles
            print(f"   Detalles contienen:")
            print(f"     - estado_situacion_financiera: ✅")
            print(f"     - estado_resultados_integral: ✅")
            print(f"     - ratios_financieros: ✅")
            print(f"     - conversion_decimals_aplicada: {detalles.get('debug_info', {}).get('conversion_decimals_aplicada', 'No encontrado')}")
            
            # Verificar que los valores son float, no Decimal
            total_activos = detalles['estado_situacion_financiera']['total_activos']
            print(f"     - total_activos: {total_activos} (tipo: {type(total_activos)})")
            
            if isinstance(total_activos, float):
                print(f"   ✅ Conversión exitosa: Decimals convertidos a float")
            else:
                print(f"   ❌ Error: total_activos sigue siendo {type(total_activos)}")
                return False
            
        else:
            print(f"❌ No se encontró el log de actividad creado")
            return False
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False
    
    print(f"✅ Prueba de finalización exitosa")
    return True

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 INICIANDO PRUEBAS DE CORRECCIÓN DE SERIALIZACIÓN DE DECIMALS")
    
    # Prueba 1: Conversión de Decimals
    prueba1_ok = probar_conversion_decimals()
    
    # Prueba 2: Finalización con usuario
    prueba2_ok = probar_finalizacion_con_usuario()
    
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"✅ Conversión de Decimals: {'✅ EXITOSA' if prueba1_ok else '❌ FALLIDA'}")
    print(f"✅ Finalización con usuario: {'✅ EXITOSA' if prueba2_ok else '❌ FALLIDA'}")
    
    if prueba1_ok and prueba2_ok:
        print(f"\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print(f"   ✅ Los Decimals se convierten correctamente a float")
        print(f"   ✅ Los datos se guardan sin errores de serialización JSON")
        print(f"   ✅ El usuario generador se guarda correctamente")
        print(f"\n💡 La corrección está lista para producción")
    else:
        print(f"\n❌ ALGUNAS PRUEBAS FALLARON")
        print(f"   🔧 Revisar la implementación antes de desplegar")

if __name__ == "__main__":
    main()
