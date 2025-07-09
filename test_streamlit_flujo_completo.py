#!/usr/bin/env python3
"""
Script para verificar el flujo completo de generación y visualización de reportes
- Verificar datos en Redis bajo las claves de pruebas
- Probar la detección automática de clientes/períodos  
- Validar la estructura del JSON para Streamlit
"""

import redis
import json
import sys
import os

# Agregar el path de streamlit_conta para importar módulos
sys.path.append('/root/SGM/streamlit_conta')

try:
    from data.detector_redis import detectar_clientes_y_periodos, cargar_datos_cliente_periodo
    print("✅ Módulos de Streamlit importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos de Streamlit: {e}")
    exit(1)

def conectar_redis():
    """Conectar a Redis DB 1 (contabilidad)"""
    try:
        redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=1,
            password='Redis_Password_2025!',
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        if redis_client.ping():
            print("✅ Conexión a Redis exitosa")
            return redis_client
        else:
            print("❌ No se pudo hacer ping a Redis")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return None

def verificar_claves_pruebas():
    """Verificar qué claves de pruebas existen en Redis"""
    redis_client = conectar_redis()
    if not redis_client:
        return
    
    print("\n🔍 Verificando claves de pruebas en Redis...")
    
    # Buscar claves de finalizacion_automatica
    pattern = "sgm:contabilidad:*:*:pruebas:esf:finalizacion_automatica"
    keys = redis_client.keys(pattern)
    
    print(f"📋 Claves encontradas con patrón '{pattern}': {len(keys)}")
    
    for i, key in enumerate(keys[:5], 1):  # Mostrar máximo 5
        print(f"  {i}. {key}")
        
        # Verificar si tiene datos
        try:
            data = redis_client.get(key)
            if data:
                json_data = json.loads(data)
                
                # Extraer información básica
                metadata = json_data.get('metadata', {})
                cliente_nombre = metadata.get('cliente_nombre', 'N/A')
                fecha_gen = metadata.get('fecha_generacion', 'N/A')
                total_activos = json_data.get('total_activos') or json_data.get('activos', {}).get('total_activos', 'N/A')
                
                print(f"     Cliente: {cliente_nombre}")
                print(f"     Fecha: {fecha_gen}")
                print(f"     Total Activos: {total_activos}")
                print(f"     Tamaño JSON: {len(str(json_data))} caracteres")
        except Exception as e:
            print(f"     ❌ Error leyendo datos: {e}")
        
        print()
    
    if len(keys) > 5:
        print(f"... y {len(keys) - 5} claves más")

def probar_detector_streamlit():
    """Probar el detector de clientes y períodos de Streamlit"""
    print("\n🧪 Probando detector de Streamlit...")
    
    try:
        resultado = detectar_clientes_y_periodos()
        
        if 'error' in resultado:
            print(f"❌ Error en detector: {resultado['error']}")
            return
        
        print(f"✅ Detector funcionando correctamente")
        print(f"📊 Total clientes encontrados: {resultado.get('total_clientes', 0)}")
        
        clientes = resultado.get('clientes', {})
        
        for cliente_id, cliente_data in clientes.items():
            print(f"\n👤 Cliente {cliente_id}:")
            print(f"   Nombre: {cliente_data['nombre']}")
            print(f"   Períodos: {cliente_data['periodos']}")
            print(f"   Datos: {cliente_data['datos_disponibles']}")
            
            # Probar carga de datos para el primer período
            if cliente_data['periodos']:
                primer_periodo = cliente_data['periodos'][0]
                print(f"\n   🔄 Probando carga de datos para {primer_periodo}...")
                
                datos = cargar_datos_cliente_periodo(cliente_id, primer_periodo)
                
                if datos:
                    print(f"   ✅ Datos cargados exitosamente")
                    print(f"   📋 Datos encontrados: {datos.get('datos_encontrados', [])}")
                    
                    if 'esf' in datos:
                        esf = datos['esf']
                        print(f"   🏛️ ESF disponible")
                        
                        # Verificar estructura básica del ESF
                        secciones = ['activos', 'pasivos', 'patrimonio']
                        for seccion in secciones:
                            if seccion in esf:
                                print(f"      ✅ Sección '{seccion}' presente")
                            else:
                                print(f"      ⚠️ Sección '{seccion}' ausente")
                        
                        # Verificar totales
                        total_activos = esf.get('total_activos') or esf.get('activos', {}).get('total_activos')
                        if total_activos:
                            print(f"      💰 Total Activos: {total_activos:,.0f}")
                        
                        # Verificar metadata
                        if 'metadata' in esf:
                            metadata = esf['metadata']
                            print(f"      📝 Metadata presente:")
                            print(f"         Cliente: {metadata.get('cliente_nombre', 'N/A')}")
                            print(f"         Fecha: {metadata.get('fecha_generacion', 'N/A')}")
                            print(f"         Cierre ID: {metadata.get('cierre_id', 'N/A')}")
                else:
                    print(f"   ❌ No se pudieron cargar datos")
                
                break  # Solo probar el primer cliente/período
    
    except Exception as e:
        print(f"❌ Error probando detector: {e}")
        import traceback
        traceback.print_exc()

def verificar_estructura_esf():
    """Verificar que la estructura del ESF sea compatible con las vistas de Streamlit"""
    print("\n🔍 Verificando compatibilidad estructura ESF...")
    
    # Obtener el primer cliente/período disponible
    resultado = detectar_clientes_y_periodos()
    
    if 'error' in resultado or not resultado.get('clientes'):
        print("❌ No hay datos para verificar")
        return
    
    # Tomar el primer cliente y período
    primer_cliente_id = list(resultado['clientes'].keys())[0]
    primer_periodo = resultado['clientes'][primer_cliente_id]['periodos'][0]
    
    print(f"📊 Verificando cliente {primer_cliente_id}, período {primer_periodo}")
    
    datos = cargar_datos_cliente_periodo(primer_cliente_id, primer_periodo)
    
    if not datos or 'esf' not in datos:
        print("❌ No hay datos ESF para verificar")
        return
    
    esf = datos['esf']
    
    print("🧪 Verificando compatibilidad con vistas de Streamlit...")
    
    # Verificar los campos que espera la vista de ESF
    campos_esperados = {
        'total_activos': esf.get('total_activos') or esf.get('activos', {}).get('total_activos'),
        'totales.pasivos': esf.get('totales', {}).get('pasivos'),
        'totales.patrimonio': esf.get('totales', {}).get('patrimonio'),
        'activos': esf.get('activos'),
        'pasivos': esf.get('pasivos'), 
        'patrimonio': esf.get('patrimonio'),
        'metadata': esf.get('metadata')
    }
    
    for campo, valor in campos_esperados.items():
        if valor is not None:
            print(f"   ✅ Campo '{campo}' presente")
        else:
            print(f"   ⚠️ Campo '{campo}' ausente o vacío")
    
    # Verificar estructura de secciones
    for seccion_nombre in ['activos', 'pasivos', 'patrimonio']:
        seccion = esf.get(seccion_nombre, {})
        if seccion:
            print(f"\n   📂 Sección '{seccion_nombre}':")
            
            # Buscar subsecciones comunes
            subsecciones = ['corrientes', 'no_corrientes', 'capital', 'reservas', 'resultados']
            for subseccion in subsecciones:
                if subseccion in seccion:
                    subseccion_data = seccion[subseccion]
                    if isinstance(subseccion_data, dict):
                        if 'grupos' in subseccion_data:
                            total_grupos = len(subseccion_data['grupos'])
                            print(f"      ✅ {subseccion}: {total_grupos} grupos")
                        elif 'cuentas' in subseccion_data:
                            total_cuentas = len(subseccion_data['cuentas']) if isinstance(subseccion_data['cuentas'], list) else 0
                            print(f"      ✅ {subseccion}: {total_cuentas} cuentas directas")
    
    print("\n✅ Verificación de estructura completada")

if __name__ == '__main__':
    print("🚀 Iniciando verificación del flujo completo de reportes...")
    print("=" * 60)
    
    verificar_claves_pruebas()
    probar_detector_streamlit()
    verificar_estructura_esf()
    
    print("\n🎯 Verificación completada")
