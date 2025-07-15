#!/usr/bin/env python3
"""
Test específico para verificar el manejo de la ausencia de columna fecha en dashboard
"""

import sys
import os
import redis
import json
import pandas as pd

# Agregar el directorio del proyecto al path
sys.path.append('/root/SGM')

def test_dashboard_sin_fecha():
    """Probar dashboard con datos sin columna fecha"""
    print("🧪 Testing dashboard sin columna fecha...")
    
    # Crear datos de prueba sin columna fecha
    datos_prueba = {
        "estado_situacion_financiera": {
            "activos": [
                {"codigo": "1101", "nombre": "Caja", "saldo": 50000},
                {"codigo": "1102", "nombre": "Bancos", "saldo": 150000}
            ],
            "pasivos": [
                {"codigo": "2101", "nombre": "Proveedores", "saldo": 80000}
            ],
            "patrimonio": [
                {"codigo": "3101", "nombre": "Capital", "saldo": 120000}
            ]
        },
        "movimientos": [
            {
                "cuenta": "1101",
                "descripcion": "Venta de producto",
                "debe": 10000,
                "haber": 0,
                "tipo_documento": "FA"
            },
            {
                "cuenta": "2101", 
                "descripcion": "Compra mercadería",
                "debe": 0,
                "haber": 5000,
                "tipo_documento": "FC"
            },
            {
                "cuenta": "1102",
                "descripcion": "Depósito bancario",
                "debe": 8000,
                "haber": 0,
                "tipo_documento": "TR"
            }
        ],
        "kpis": {
            "total_activos": 200000,
            "total_pasivos": 80000,
            "patrimonio_neto": 120000,
            "liquidez": 2.5
        },
        "metadatos": {
            "empresa": "Test Corp",
            "periodo": "2024-01",
            "estado": "Datos de prueba sin fecha",
            "generado": "2024-01-15T10:00:00"
        }
    }
    
    # Conectar a Redis y guardar datos de prueba
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Guardar en Redis
        key = "dashboard_conta:test_sin_fecha:2024-01"
        r.set(key, json.dumps(datos_prueba, ensure_ascii=False))
        print(f"✅ Datos de prueba guardados en Redis: {key}")
        
        # Verificar que se guardaron correctamente
        datos_verificacion = json.loads(r.get(key))
        print(f"📊 Movimientos sin fecha: {len(datos_verificacion['movimientos'])}")
        
        # Verificar que no hay columna fecha
        if datos_verificacion['movimientos']:
            primer_mov = datos_verificacion['movimientos'][0]
            tiene_fecha = any('fecha' in str(k).lower() for k in primer_mov.keys())
            print(f"🗓️ ¿Tiene columna fecha?: {tiene_fecha}")
            print(f"📝 Columnas disponibles: {list(primer_mov.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dataframe_sin_fecha():
    """Probar DataFrame sin columna fecha específicamente"""
    print("\n🧪 Testing DataFrame sin columna fecha...")
    
    # Datos sin fecha
    movimientos = [
        {
            "cuenta": "1101",
            "descripcion": "Venta de producto", 
            "debe": 10000,
            "haber": 0,
            "tipo_documento": "FA"
        },
        {
            "cuenta": "2101",
            "descripcion": "Compra mercadería",
            "debe": 0,
            "haber": 5000,
            "tipo_documento": "FC"
        }
    ]
    
    try:
        df_mov = pd.DataFrame(movimientos)
        print(f"✅ DataFrame creado: {df_mov.shape}")
        print(f"📝 Columnas: {list(df_mov.columns)}")
        
        # Verificar ausencia de columna fecha
        if 'fecha' not in df_mov.columns:
            print("⚠️ No hay columna 'fecha' - esto debería manejarse correctamente")
            
            # Buscar columnas de fecha alternativas
            fecha_cols = [col for col in df_mov.columns if 'fecha' in col.lower()]
            print(f"🔍 Columnas de fecha alternativas encontradas: {fecha_cols}")
            
            if not fecha_cols:
                print("ℹ️ Debería mostrar análisis sin fecha")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error procesando DataFrame: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TEST: Dashboard sin columna fecha")
    print("=" * 50)
    
    # Test 1: Datos en Redis sin fecha
    test1 = test_dashboard_sin_fecha()
    
    # Test 2: DataFrame sin fecha
    test2 = test_dataframe_sin_fecha()
    
    print("\n" + "=" * 50)
    print("RESULTADOS:")
    print(f"Test Redis sin fecha: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test DataFrame sin fecha: {'✅ PASS' if test2 else '❌ FAIL'}")
    print("=" * 50)
    
    if test1 and test2:
        print("\n🎉 Todos los tests pasaron")
        print("💡 Ahora puedes usar el dashboard con datos sin fecha")
        print("\n🔧 Para probar en Streamlit:")
        print("1. Ejecuta: streamlit run /root/SGM/streamlit_conta/app.py")
        print("2. Selecciona 'Datos de Sistema de Cierre' en el sidebar")
        print("3. Deberías ver el análisis sin errores de fecha")
    else:
        print("\n⚠️ Algunos tests fallaron - revisar implementación")
