#!/usr/bin/env python3
"""
Script de prueba para el sistema simplificado de Streamlit
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, '/app/streamlit_conta')

def test_detector_redis():
    """Probar el detector de Redis"""
    print("🔍 Probando detector de Redis...")
    
    try:
        from data.detector_redis import detectar_clientes_y_periodos, cargar_datos_cliente_periodo
        
        # Detectar clientes
        clientes_info = detectar_clientes_y_periodos()
        
        if 'error' in clientes_info:
            print(f"❌ Error: {clientes_info['error']}")
            return False
        
        print(f"✅ Clientes detectados: {clientes_info['total_clientes']}")
        
        # Mostrar detalles
        for cliente_id, cliente_data in clientes_info['clientes'].items():
            print(f"  📋 Cliente {cliente_id}: {cliente_data['nombre']}")
            print(f"     Períodos: {', '.join(cliente_data['periodos'])}")
            print(f"     Datos: {', '.join(cliente_data['datos_disponibles'])}")
        
        # Probar carga de datos del primer cliente
        if clientes_info['clientes']:
            primer_cliente_id = list(clientes_info['clientes'].keys())[0]
            primer_periodo = clientes_info['clientes'][primer_cliente_id]['periodos'][0]
            
            print(f"\n📊 Probando carga de datos para Cliente {primer_cliente_id}, Período {primer_periodo}...")
            
            datos = cargar_datos_cliente_periodo(primer_cliente_id, primer_periodo)
            
            if datos:
                print(f"✅ Datos cargados exitosamente")
                print(f"   Datos encontrados: {', '.join(datos.get('datos_encontrados', []))}")
                if 'cliente_nombre' in datos:
                    print(f"   Cliente: {datos['cliente_nombre']}")
                
                # Probar extracción de movimientos
                if 'esf' in datos:
                    print(f"\n🧾 Probando extracción de movimientos...")
                    try:
                        # Importar la función de extracción
                        sys.path.insert(0, '/app/streamlit_conta/views')
                        from movimientos import extraer_movimientos_de_esf
                        
                        movimientos = extraer_movimientos_de_esf(datos['esf'])
                        print(f"✅ Movimientos extraídos: {len(movimientos)}")
                        
                        if movimientos:
                            primer_mov = movimientos[0]
                            print(f"   Estructura del primer movimiento:")
                            for key, value in primer_mov.items():
                                print(f"     - {key}: {value}")
                        
                        return True
                        
                    except Exception as e:
                        print(f"❌ Error extrayendo movimientos: {e}")
                        return False
            else:
                print(f"❌ No se pudieron cargar datos")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en detector de Redis: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Probar imports del sistema"""
    print("📦 Probando imports del sistema...")
    
    try:
        # Test detector
        from data.detector_redis import detectar_clientes_y_periodos
        print("✅ detector_redis importado")
        
        # Test views
        from views import dashboard_general, movimientos, estado_situacion_financiera
        print("✅ views importadas")
        
        # Test layout
        from layout.sidebar import mostrar_sidebar
        from layout.header import mostrar_header
        print("✅ layout importado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando tests del sistema simplificado...")
    
    # Test 1: Imports
    if not test_imports():
        print("❌ Los imports fallaron, abortando tests")
        sys.exit(1)
    
    # Test 2: Detector Redis
    if not test_detector_redis():
        print("❌ El detector de Redis falló")
        sys.exit(1)
    
    print("\n🎉 Todos los tests pasaron exitosamente!")
    print("El sistema simplificado está listo para usar.")
