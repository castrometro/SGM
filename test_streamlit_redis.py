#!/usr/bin/env python3
"""
Test script para verificar la integración de Redis con Streamlit
"""

import sys
import os
import json
import logging

# Agregar las rutas necesarias
sys.path.append('/root/SGM')
sys.path.append('/root/SGM/streamlit_conta')

from streamlit_conta.data.loader_contabilidad import (
    conectar_redis, 
    cargar_esf_desde_redis, 
    listar_esf_disponibles,
    cargar_datos_redis
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test conexión a Redis"""
    print("🔍 Probando conexión a Redis...")
    
    redis_client = conectar_redis()
    if redis_client:
        print("✅ Conexión a Redis exitosa")
        return True
    else:
        print("❌ No se pudo conectar a Redis")
        return False

def test_listar_esf():
    """Test listar ESF disponibles"""
    print("\n🔍 Probando listar ESF disponibles...")
    
    try:
        esf_info = listar_esf_disponibles(cliente_id=1)
        print(f"📊 Total ESF encontrados: {esf_info.get('total_esf', 0)}")
        
        if esf_info.get('esf_disponibles'):
            print("📋 ESF disponibles:")
            for esf in esf_info['esf_disponibles']:
                print(f"  - Cliente: {esf['cliente_id']}, Período: {esf['periodo']}, Tipo: {esf['test_type']}")
        else:
            print("⚠️ No se encontraron ESF disponibles")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al listar ESF: {e}")
        return False

def test_cargar_esf():
    """Test cargar ESF específico"""
    print("\n🔍 Probando cargar ESF específico...")
    
    try:
        # Intentar cargar ESF de finalizacion_automatica
        esf_data = cargar_esf_desde_redis(
            cliente_id=1,
            periodo="2025-07",
            test_type="finalizacion_automatica"
        )
        
        if esf_data:
            print("✅ ESF cargado exitosamente")
            print(f"📊 Total activos: {esf_data.get('total_activos', 'N/A')}")
            print(f"⚖️ Balance cuadrado: {esf_data.get('balance_cuadrado', 'N/A')}")
            print(f"📅 Generado el: {esf_data.get('generated_at', 'N/A')}")
            return True
        else:
            print("⚠️ No se encontró ESF para los parámetros especificados")
            return False
            
    except Exception as e:
        print(f"❌ Error al cargar ESF: {e}")
        return False

def test_cargar_datos_redis():
    """Test cargar datos para Streamlit"""
    print("\n🔍 Probando cargar datos para Streamlit...")
    
    try:
        datos = cargar_datos_redis(
            cliente_id=1,
            periodo="2025-07",
            test_type="finalizacion_automatica"
        )
        
        print(f"📊 Fuente de datos: {datos.get('fuente', 'N/A')}")
        print(f"👤 Cliente: {datos.get('cliente', {}).get('nombre', 'N/A')}")
        print(f"📅 Período: {datos.get('cierre', {}).get('periodo', 'N/A')}")
        print(f"🔄 Estado: {datos.get('cierre', {}).get('estado', 'N/A')}")
        
        # Verificar si tiene raw_json
        if 'raw_json' in datos:
            print("✅ JSON raw disponible para mostrar en sidebar")
        else:
            print("⚠️ No hay JSON raw disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al cargar datos para Streamlit: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de integración Streamlit-Redis")
    print("=" * 50)
    
    tests = [
        ("Conexión Redis", test_redis_connection),
        ("Listar ESF", test_listar_esf),
        ("Cargar ESF", test_cargar_esf),
        ("Cargar datos Streamlit", test_cargar_datos_redis)
    ]
    
    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error crítico en {nombre}: {e}")
            resultados.append((nombre, False))
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 50)
    
    for nombre, resultado in resultados:
        estado = "✅ EXITOSO" if resultado else "❌ FALLIDO"
        print(f"{nombre}: {estado}")
    
    exitosos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    print(f"\n🎯 Resultado final: {exitosos}/{total} pruebas exitosas")
    
    if exitosos == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo para usar en Streamlit.")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los logs para más detalles.")

if __name__ == "__main__":
    main()
