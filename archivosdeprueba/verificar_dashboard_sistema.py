#!/usr/bin/env python3
"""
Script de verificación del dashboard integrado con el sistema de cierre
"""

import os
import sys
import json
from datetime import datetime

# Agregar el directorio del backend al path
sys.path.insert(0, '/root/SGM/backend')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
import django
django.setup()

def verificar_conexion_redis():
    """Verificar la conexión a Redis"""
    print("🔍 Verificando conexión a Redis...")
    
    try:
        from contabilidad.cache_redis import get_cache_system
        cache_system = get_cache_system()
        
        if cache_system.check_connection():
            print("✅ Conexión a Redis exitosa")
            return True
        else:
            print("❌ No se pudo conectar a Redis")
            return False
    except Exception as e:
        print(f"❌ Error al conectar a Redis: {e}")
        return False

def verificar_datos_cache():
    """Verificar que hay datos en el cache"""
    print("\n🔍 Verificando datos en cache...")
    
    try:
        from contabilidad.cache_redis import get_cache_system
        cache_system = get_cache_system()
        
        cliente_id = 1
        periodo = "2025-07"
        
        # Verificar cada tipo de dato
        tipos_datos = {
            'ESF': lambda: cache_system.get_estado_financiero(cliente_id, periodo, 'esf'),
            'ESR': lambda: cache_system.get_estado_financiero(cliente_id, periodo, 'esr'),
            'KPIs': lambda: cache_system.get_kpis(cliente_id, periodo),
            'Alertas': lambda: cache_system.get_alertas(cliente_id, periodo),
            'Procesamiento': lambda: cache_system.get_procesamiento_status(cliente_id, periodo)
        }
        
        datos_encontrados = 0
        
        for nombre, obtener_func in tipos_datos.items():
            try:
                datos = obtener_func()
                if datos:
                    print(f"✅ {nombre}: Datos disponibles")
                    datos_encontrados += 1
                else:
                    print(f"❌ {nombre}: No hay datos")
            except Exception as e:
                print(f"❌ {nombre}: Error - {e}")
        
        print(f"\n📊 Total de tipos de datos disponibles: {datos_encontrados}/{len(tipos_datos)}")
        
        if datos_encontrados > 0:
            print("✅ Cache tiene datos disponibles")
            return True
        else:
            print("⚠️ No hay datos en cache")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

def verificar_estructura_esf():
    """Verificar la estructura del ESF en detalle"""
    print("\n🔍 Verificando estructura del ESF...")
    
    try:
        from contabilidad.cache_redis import get_cache_system
        cache_system = get_cache_system()
        
        esf_data = cache_system.get_estado_financiero(1, "2025-07", 'esf')
        
        if not esf_data:
            print("❌ No hay datos de ESF para verificar")
            return False
        
        # Verificar estructura esperada
        secciones_esperadas = ['metadata', 'activos', 'pasivos', 'patrimonio', 'totales']
        secciones_encontradas = 0
        
        for seccion in secciones_esperadas:
            if seccion in esf_data:
                print(f"✅ {seccion}: Presente")
                secciones_encontradas += 1
                
                # Verificar subsecciones para activos, pasivos y patrimonio
                if seccion in ['activos', 'pasivos', 'patrimonio']:
                    datos_seccion = esf_data[seccion]
                    if isinstance(datos_seccion, dict):
                        subsecciones = len([k for k in datos_seccion.keys() if k != 'total'])
                        print(f"   📋 {subsecciones} subsecciones encontradas")
                        
                        # Verificar total
                        total_key = f'total_{seccion}' if seccion != 'patrimonio' else 'total_patrimonio'
                        if total_key in datos_seccion or 'total' in datos_seccion:
                            total_valor = datos_seccion.get(total_key, datos_seccion.get('total', 0))
                            print(f"   💰 Total: ${total_valor:,.0f}")
            else:
                print(f"❌ {seccion}: Faltante")
        
        print(f"\n📊 Estructura ESF: {secciones_encontradas}/{len(secciones_esperadas)} secciones completas")
        
        # Verificar que el balance cuadra
        if 'totales' in esf_data:
            diferencia = esf_data['totales'].get('diferencia', 0)
            if abs(diferencia) < 1:
                print("✅ Balance cuadrado correctamente")
            else:
                print(f"⚠️ Diferencia en balance: ${diferencia:,.0f}")
        
        return secciones_encontradas >= 4  # Al menos 4 de 5 secciones
        
    except Exception as e:
        print(f"❌ Error verificando estructura ESF: {e}")
        return False

def verificar_loader_streamlit():
    """Verificar que el loader de Streamlit funciona"""
    print("\n🔍 Verificando loader de Streamlit...")
    
    try:
        sys.path.insert(0, '/root/SGM/streamlit_conta')
        from data.loader_contabilidad import cargar_datos_sistema_cierre, cargar_datos_redis
        
        # Probar carga del sistema de cierre
        print("📊 Probando carga del sistema de cierre...")
        datos_sistema = cargar_datos_sistema_cierre(1, "2025-07")
        
        if datos_sistema:
            print("✅ Sistema de cierre: Datos cargados exitosamente")
            tipos_disponibles = [k for k, v in datos_sistema.items() if v]
            print(f"   📋 Tipos disponibles: {', '.join(tipos_disponibles)}")
        else:
            print("❌ Sistema de cierre: No se pudieron cargar datos")
        
        # Probar carga completa de Redis
        print("\n📊 Probando carga completa...")
        datos_completos = cargar_datos_redis(1, "2025-07", "sistema_cierre")
        
        if datos_completos:
            fuente = datos_completos.get('fuente', 'desconocida')
            print(f"✅ Carga completa exitosa - Fuente: {fuente}")
            
            if 'metadata' in datos_completos:
                metadata = datos_completos['metadata']
                completitud = metadata.get('completitud', 0)
                estados = metadata.get('estados_disponibles', [])
                print(f"   📊 Completitud: {completitud} tipos de datos")
                if estados:
                    print(f"   🏛️ Estados financieros: {', '.join(estados)}")
        else:
            print("❌ No se pudieron cargar datos completos")
        
        return datos_sistema is not None
        
    except Exception as e:
        print(f"❌ Error verificando loader: {e}")
        return False

def verificar_estadisticas_cache():
    """Mostrar estadísticas del cache"""
    print("\n📊 Estadísticas del cache Redis...")
    
    try:
        from contabilidad.cache_redis import get_cache_system
        cache_system = get_cache_system()
        
        stats = cache_system.get_cache_stats()
        
        if stats:
            print("📈 Estadísticas de uso:")
            for key, value in stats.items():
                print(f"   • {key}: {value}")
        else:
            print("⚠️ No hay estadísticas disponibles")
        
        # Health check
        health = cache_system.health_check()
        if health:
            print("\n🏥 Estado de salud:")
            for key, value in health.items():
                if key == 'connected':
                    emoji = "✅" if value else "❌"
                    print(f"   {emoji} {key}: {value}")
                else:
                    print(f"   • {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return False

def mostrar_instrucciones_streamlit():
    """Mostrar instrucciones para usar Streamlit"""
    print("\n🚀 Instrucciones para usar el dashboard:")
    print("=" * 50)
    print("1. Navegar al directorio de Streamlit:")
    print("   cd /root/SGM/streamlit_conta")
    print()
    print("2. Ejecutar Streamlit:")
    print("   streamlit run app.py --server.port 8501 --server.address 0.0.0.0")
    print()
    print("3. Abrir en el navegador:")
    print("   http://localhost:8501")
    print()
    print("4. Configurar en el sidebar:")
    print("   • Fuente: 🔴 Sistema de Cierre (Redis)")
    print("   • Cliente ID: 1")
    print("   • Período: 2025-07")
    print()
    print("5. Explorar reportes disponibles:")
    print("   • 📊 Dashboard General")
    print("   • 🏛️ Estado de Situación Financiera (ESF)")
    print("   • 📈 Estado de Resultados (ESR)")
    print("   • ⚠️ Alertas y KPIs")

def main():
    """Función principal de verificación"""
    print("🔧 Verificador del Dashboard Integrado SGM")
    print("=" * 50)
    
    resultados = []
    
    # 1. Verificar conexión Redis
    resultados.append(("Conexión Redis", verificar_conexion_redis()))
    
    # 2. Verificar datos en cache
    resultados.append(("Datos en Cache", verificar_datos_cache()))
    
    # 3. Verificar estructura ESF
    resultados.append(("Estructura ESF", verificar_estructura_esf()))
    
    # 4. Verificar loader Streamlit
    resultados.append(("Loader Streamlit", verificar_loader_streamlit()))
    
    # 5. Estadísticas
    resultados.append(("Estadísticas Cache", verificar_estadisticas_cache()))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    total_pruebas = len(resultados)
    pruebas_exitosas = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        emoji = "✅" if resultado else "❌"
        print(f"{emoji} {nombre}")
    
    print(f"\n📊 Resultado: {pruebas_exitosas}/{total_pruebas} verificaciones exitosas")
    
    if pruebas_exitosas == total_pruebas:
        print("🎉 ¡Todas las verificaciones pasaron! El sistema está listo.")
        mostrar_instrucciones_streamlit()
    elif pruebas_exitosas >= total_pruebas - 1:
        print("✅ Sistema funcional con advertencias menores.")
        mostrar_instrucciones_streamlit()
    else:
        print("⚠️ Se encontraron problemas. Revisa los errores arriba.")
        print("\n💡 Sugerencias:")
        print("   • Ejecutar: python poblar_cache_dashboard.py")
        print("   • Verificar que Redis esté corriendo")
        print("   • Revisar configuración de conexión")

if __name__ == "__main__":
    main()
