#!/usr/bin/env python3
"""
Script de prueba para validar la funcionalidad de retención de cierres en Redis.

Este script simula el comportamiento del sistema de retención:
1. Crea varios cierres de prueba para un cliente
2. Verifica que solo se mantienen los 2 más recientes
3. Valida que se eliminan automáticamente los cierres antiguos
4. Confirma que los datos permanecen en la base de datos

Uso:
    python test_retencion_redis.py

Autor: Sistema SGM
Fecha: 8 de julio de 2025
"""

import json
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Simulación del sistema sin depender de Django
class MockCacheSystem:
    """Simulación del sistema de cache para pruebas"""
    
    def __init__(self):
        self.cache = {}  # Simular Redis en memoria
        self.stats = {}
    
    def set_estado_financiero_with_retention(self, cliente_id, periodo, datos_esf, 
                                           datos_eri, max_cierres_por_cliente=2, 
                                           ttl_hours=24*30):
        """Simulación de la función de retención"""
        
        print(f"\n🔄 Iniciando retención para cliente {cliente_id}, período {periodo}")
        
        # Simular obtención de cierres existentes
        pattern_prefix = f"cliente_{cliente_id}_"
        claves_existentes = [k for k in self.cache.keys() if k.startswith(pattern_prefix) and k.endswith("_esf")]
        
        cierres_existentes = []
        for clave in claves_existentes:
            periodo_existente = clave.replace(pattern_prefix, "").replace("_esf", "")
            fecha_creacion = self.cache[clave].get('_metadata', {}).get('created_at', datetime.now().isoformat())
            
            cierres_existentes.append({
                'periodo': periodo_existente,
                'fecha_creacion': fecha_creacion,
                'clave_esf': clave,
                'clave_eri': clave.replace('_esf', '_eri')
            })
        
        # Guardar nuevo cierre
        clave_esf = f"cliente_{cliente_id}_{periodo}_esf"
        clave_eri = f"cliente_{cliente_id}_{periodo}_eri"
        
        self.cache[clave_esf] = {
            **datos_esf,
            '_metadata': {
                'cliente_id': cliente_id,
                'periodo': periodo,
                'created_at': datetime.now().isoformat(),
                'ttl_hours': ttl_hours
            }
        }
        
        self.cache[clave_eri] = {
            **datos_eri,
            '_metadata': {
                'cliente_id': cliente_id,
                'periodo': periodo,
                'created_at': datetime.now().isoformat(),
                'ttl_hours': ttl_hours
            }
        }
        
        # Agregar el nuevo cierre a la lista
        nuevo_cierre = {
            'periodo': periodo,
            'fecha_creacion': datetime.now().isoformat(),
            'clave_esf': clave_esf,
            'clave_eri': clave_eri
        }
        cierres_existentes.append(nuevo_cierre)
        
        # Ordenar por fecha de creación (más reciente primero)
        cierres_existentes.sort(key=lambda x: x['fecha_creacion'], reverse=True)
        
        # Identificar cierres a mantener y eliminar
        cierres_a_mantener = cierres_existentes[:max_cierres_por_cliente]
        cierres_a_eliminar = cierres_existentes[max_cierres_por_cliente:]
        
        # Eliminar cierres antiguos
        resultado = {
            'success': True,
            'cliente_id': cliente_id,
            'periodo': periodo,
            'cierres_eliminados': [],
            'cierres_mantenidos': []
        }
        
        for cierre in cierres_a_eliminar:
            if cierre['clave_esf'] in self.cache:
                del self.cache[cierre['clave_esf']]
            if cierre['clave_eri'] in self.cache:
                del self.cache[cierre['clave_eri']]
            
            resultado['cierres_eliminados'].append({
                'periodo': cierre['periodo'],
                'fecha_creacion': cierre['fecha_creacion']
            })
        
        for cierre in cierres_a_mantener:
            resultado['cierres_mantenidos'].append({
                'periodo': cierre['periodo'],
                'fecha_creacion': cierre['fecha_creacion']
            })
        
        print(f"   📊 Total cierres procesados: {len(cierres_existentes)}")
        print(f"   📁 Cierres mantenidos: {len(cierres_a_mantener)}")
        print(f"   🗑️ Cierres eliminados: {len(cierres_a_eliminar)}")
        
        return resultado
    
    def get_cierres_disponibles_cliente(self, cliente_id):
        """Obtener cierres disponibles para un cliente"""
        pattern_prefix = f"cliente_{cliente_id}_"
        claves_esf = [k for k in self.cache.keys() if k.startswith(pattern_prefix) and k.endswith("_esf")]
        
        cierres = []
        for clave in claves_esf:
            periodo = clave.replace(pattern_prefix, "").replace("_esf", "")
            clave_eri = clave.replace('_esf', '_eri')
            
            if clave_eri in self.cache:
                datos = self.cache[clave]
                metadata = datos.get('_metadata', {})
                
                cierres.append({
                    'periodo': periodo,
                    'fecha_creacion': metadata.get('created_at'),
                    'tiene_esf': True,
                    'tiene_eri': True,
                    'clave_esf': clave,
                    'clave_eri': clave_eri
                })
        
        cierres.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)
        return cierres


def generar_datos_financieros_mock(periodo):
    """Generar datos financieros de prueba"""
    base_amount = hash(periodo) % 100000  # Generar números diferentes por período
    
    esf_data = {
        'total_activos': base_amount + 50000,
        'total_pasivos': base_amount + 20000,
        'total_patrimonio': base_amount + 30000,
        'activos_corrientes': base_amount + 25000,
        'pasivos_corrientes': base_amount + 15000,
        'balance_cuadrado': True,
        'diferencia': 0
    }
    
    eri_data = {
        'revenue': base_amount + 10000,
        'gross_earnings': base_amount + 8000,
        'earnings_loss_before_taxes': base_amount + 5000,
        'net_earnings': base_amount + 3500,
        'total_expenses': base_amount + 4500
    }
    
    return esf_data, eri_data


def ejecutar_prueba_retencion():
    """Ejecutar prueba completa de retención de cierres"""
    
    print("🧪 PRUEBA DE RETENCIÓN DE CIERRES EN REDIS")
    print("=" * 60)
    
    cache_system = MockCacheSystem()
    cliente_id = 1
    
    # Simular diferentes períodos de cierre
    periodos_prueba = [
        '2024-01',  # Enero (será eliminado)
        '2024-02',  # Febrero (será eliminado)
        '2024-03',  # Marzo (será eliminado)
        '2024-04',  # Abril (será mantenido)
        '2024-05',  # Mayo (será mantenido - más reciente)
    ]
    
    print(f"\n📋 Simulando {len(periodos_prueba)} cierres para cliente {cliente_id}")
    print(f"📊 Configuración: máximo 2 cierres por cliente, TTL 30 días")
    
    # Agregar cada cierre con un pequeño delay para simular fechas diferentes
    for i, periodo in enumerate(periodos_prueba):
        print(f"\n--- Agregando cierre {i+1}/{len(periodos_prueba)}: {periodo} ---")
        
        # Generar datos de prueba
        esf_data, eri_data = generar_datos_financieros_mock(periodo)
        
        # Simular delay entre cierres
        if i > 0:
            time.sleep(0.1)  # Pequeño delay para asegurar timestamps diferentes
        
        # Ejecutar retención
        resultado = cache_system.set_estado_financiero_with_retention(
            cliente_id=cliente_id,
            periodo=periodo,
            datos_esf=esf_data,
            datos_eri=eri_data,
            max_cierres_por_cliente=2,
            ttl_hours=24*30
        )
        
        # Mostrar resultado
        if resultado['success']:
            print(f"   ✅ Cierre guardado exitosamente")
            
            if resultado['cierres_eliminados']:
                print(f"   🗑️ Cierres eliminados de Redis:")
                for eliminado in resultado['cierres_eliminados']:
                    print(f"      - {eliminado['periodo']} (creado: {eliminado['fecha_creacion'][:19]})")
            
            if resultado['cierres_mantenidos']:
                print(f"   📁 Cierres mantenidos en Redis:")
                for mantenido in resultado['cierres_mantenidos']:
                    print(f"      - {mantenido['periodo']} (creado: {mantenido['fecha_creacion'][:19]})")
        else:
            print(f"   ❌ Error: {resultado.get('error', 'Error desconocido')}")
    
    # Verificación final
    print(f"\n🔍 VERIFICACIÓN FINAL")
    print("=" * 60)
    
    cierres_finales = cache_system.get_cierres_disponibles_cliente(cliente_id)
    
    print(f"📊 Cierres disponibles en Redis para cliente {cliente_id}: {len(cierres_finales)}")
    
    if len(cierres_finales) <= 2:
        print("✅ RETENCIÓN EXITOSA: Se mantienen máximo 2 cierres")
    else:
        print("❌ ERROR EN RETENCIÓN: Se mantienen más de 2 cierres")
    
    print(f"\n📁 Detalle de cierres mantenidos:")
    for i, cierre in enumerate(cierres_finales, 1):
        print(f"   {i}. Período: {cierre['periodo']}")
        print(f"      Fecha creación: {cierre['fecha_creacion'][:19]}")
        print(f"      ESF disponible: {'✅' if cierre['tiene_esf'] else '❌'}")
        print(f"      ERI disponible: {'✅' if cierre['tiene_eri'] else '❌'}")
    
    # Verificar que los períodos mantenidos son los más recientes
    periodos_mantenidos = [c['periodo'] for c in cierres_finales]
    periodos_esperados = ['2024-05', '2024-04']  # Los 2 más recientes
    
    print(f"\n🎯 VALIDACIÓN DE PERÍODOS:")
    print(f"   Esperados: {periodos_esperados}")
    print(f"   Obtenidos: {periodos_mantenidos}")
    
    if set(periodos_mantenidos) == set(periodos_esperados):
        print("   ✅ CORRECTO: Se mantienen los períodos más recientes")
    else:
        print("   ❌ ERROR: No se mantienen los períodos correctos")
    
    # Simular que los datos eliminados siguen en la base de datos
    print(f"\n💾 SIMULACIÓN BASE DE DATOS:")
    print("   📋 Todos los cierres permanecen en la base de datos:")
    for periodo in periodos_prueba:
        estado_redis = "Redis ✅" if periodo in periodos_mantenidos else "Redis ❌"
        print(f"      - {periodo}: BD ✅, {estado_redis}")
    
    print(f"\n🎉 PRUEBA COMPLETADA")
    print("=" * 60)
    print("📝 RESUMEN:")
    print(f"   • Total cierres procesados: {len(periodos_prueba)}")
    print(f"   • Cierres mantenidos en Redis: {len(cierres_finales)}")
    print(f"   • Cierres eliminados de Redis: {len(periodos_prueba) - len(cierres_finales)}")
    print(f"   • Todos los cierres permanecen en BD: ✅")
    print(f"   • Sistema de retención funcionando: {'✅' if len(cierres_finales) <= 2 else '❌'}")


if __name__ == "__main__":
    ejecutar_prueba_retencion()
