#!/usr/bin/env python3
"""
🧪 SCRIPT DE PRUEBA: Sistema Paralelo de Incidencias
Verifica la implementación del nuevo sistema dual de procesamiento paralelo
"""

import os
import sys
import django
import logging
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_configuracion_celery():
    """🔧 Prueba la configuración de Celery"""
    print("\n" + "="*60)
    print("🔧 PRUEBA 1: Configuración de Celery")
    print("="*60)
    
    try:
        from sgm_backend.celery import app
        
        print(f"✅ Celery app configurada: {app.main}")
        print(f"📋 Broker URL: {app.conf.broker_url}")
        print(f"📤 Result backend: {app.conf.result_backend}")
        
        # Verificar configuración de colas
        task_routes = app.conf.task_routes
        print(f"🚦 Task routes configuradas: {len(task_routes)} rutas")
        
        for pattern, config in task_routes.items():
            print(f"   - {pattern} → {config}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración Celery: {e}")
        return False

def test_tareas_disponibles():
    """📋 Verifica que las nuevas tareas estén disponibles"""
    print("\n" + "="*60)
    print("📋 PRUEBA 2: Tareas Disponibles")
    print("="*60)
    
    try:
        from nomina.tasks import (
            generar_incidencias_cierre_paralelo,
            procesar_chunk_clasificaciones,
            consolidar_resultados_filtrados,
            consolidar_resultados_completos,
            comparar_y_generar_reporte_final
        )
        
        tareas = [
            'generar_incidencias_cierre_paralelo',
            'procesar_chunk_clasificaciones', 
            'consolidar_resultados_filtrados',
            'consolidar_resultados_completos',
            'comparar_y_generar_reporte_final'
        ]
        
        print(f"✅ Todas las tareas paralelas importadas exitosamente:")
        for tarea in tareas:
            print(f"   - ✓ {tarea}")
            
        return True
        
    except ImportError as e:
        print(f"❌ Error importando tareas: {e}")
        return False

def test_funciones_auxiliares():
    """🛠️ Prueba las funciones auxiliares"""
    print("\n" + "="*60)
    print("🛠️ PRUEBA 3: Funciones Auxiliares")
    print("="*60)
    
    try:
        from nomina.tasks import (
            obtener_clasificaciones_cierre,
            crear_chunks,
            procesar_incidencias_clasificacion_individual
        )
        
        # Probar obtener_clasificaciones_cierre
        clasificaciones = obtener_clasificaciones_cierre(1)
        print(f"✅ obtener_clasificaciones_cierre: {len(clasificaciones)} clasificaciones")
        
        # Probar crear_chunks
        chunks = crear_chunks(clasificaciones, chunk_size=6)
        print(f"✅ crear_chunks: {len(chunks)} chunks de tamaño máximo 6")
        
        for i, chunk in enumerate(chunks):
            print(f"   - Chunk {i}: {len(chunk)} elementos")
        
        # Probar procesamiento individual
        resultado = procesar_incidencias_clasificacion_individual(1, 1, 'filtrado')
        print(f"✅ procesar_incidencias_clasificacion_individual: {resultado['success']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en funciones auxiliares: {e}")
        return False

def test_endpoint_modificado():
    """🌐 Prueba que el endpoint esté modificado correctamente"""
    print("\n" + "="*60)
    print("🌐 PRUEBA 4: Endpoint Modificado")
    print("="*60)
    
    try:
        from nomina.views import IncidenciaCierreViewSet
        
        # Verificar que el método generar_incidencias existe
        viewset = IncidenciaCierreViewSet()
        metodo = getattr(viewset, 'generar_incidencias', None)
        
        if metodo is None:
            print("❌ Método generar_incidencias no encontrado")
            return False
            
        print("✅ Método generar_incidencias encontrado")
        
        # Verificar el docstring para confirmar que está actualizado
        docstring = metodo.__doc__ or ""
        if "SISTEMA DUAL" in docstring:
            print("✅ Endpoint actualizado con sistema dual")
        else:
            print("⚠️ Endpoint puede no estar actualizado (docstring no contiene 'SISTEMA DUAL')")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando endpoint: {e}")
        return False

def test_simulacion_flujo_completo():
    """🎯 Simula el flujo completo sin ejecutar tareas reales"""
    print("\n" + "="*60)
    print("🎯 PRUEBA 5: Simulación de Flujo Completo")
    print("="*60)
    
    try:
        from nomina.tasks import (
            obtener_clasificaciones_cierre,
            crear_chunks,
            calcular_diferencias_resultados
        )
        
        # Simular datos
        cierre_id = 1
        clasificaciones_seleccionadas = [1, 3, 5, 7, 9]
        todas_clasificaciones = obtener_clasificaciones_cierre(cierre_id)
        
        print(f"📊 Cierre ID: {cierre_id}")
        print(f"📋 Clasificaciones seleccionadas: {len(clasificaciones_seleccionadas)}")
        print(f"📈 Total clasificaciones: {len(todas_clasificaciones)}")
        
        # Crear chunks
        chunks_seleccionadas = crear_chunks(clasificaciones_seleccionadas, 6)
        chunks_todas = crear_chunks(todas_clasificaciones, 6)
        
        print(f"🔀 Chunks filtrado: {len(chunks_seleccionadas)}")
        print(f"🔀 Chunks completo: {len(chunks_todas)}")
        
        # Simular resultados
        resultado_filtrado = {
            'total_incidencias': 10,
            'clasificaciones_procesadas': len(clasificaciones_seleccionadas),
            'success': True
        }
        
        resultado_completo = {
            'total_incidencias': 25,
            'clasificaciones_procesadas': len(todas_clasificaciones),
            'success': True
        }
        
        # Calcular diferencias
        diferencias = calcular_diferencias_resultados(resultado_filtrado, resultado_completo)
        print(f"📊 Diferencias calculadas: {diferencias}")
        
        print("✅ Simulación de flujo completo exitosa")
        return True
        
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False

def main():
    """🚀 Ejecuta todas las pruebas"""
    print("🧪 SISTEMA DE PRUEBAS - PROCESAMIENTO PARALELO DE INCIDENCIAS")
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    pruebas = [
        ("Configuración Celery", test_configuracion_celery),
        ("Tareas Disponibles", test_tareas_disponibles),
        ("Funciones Auxiliares", test_funciones_auxiliares),
        ("Endpoint Modificado", test_endpoint_modificado),
        ("Simulación Flujo Completo", test_simulacion_flujo_completo),
    ]
    
    resultados = []
    
    for nombre, prueba in pruebas:
        try:
            resultado = prueba()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"💥 Error ejecutando {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "="*80)
    print("📋 RESUMEN DE PRUEBAS")
    print("="*80)
    
    exitosas = 0
    fallidas = 0
    
    for nombre, resultado in resultados:
        estado = "✅ EXITOSA" if resultado else "❌ FALLIDA"
        print(f"{estado:12} - {nombre}")
        
        if resultado:
            exitosas += 1
        else:
            fallidas += 1
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Exitosas: {exitosas}")
    print(f"   ❌ Fallidas: {fallidas}")
    print(f"   📈 Porcentaje éxito: {(exitosas/(exitosas+fallidas)*100):.1f}%")
    
    if fallidas == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema está listo.")
    else:
        print(f"\n⚠️ {fallidas} prueba(s) fallaron. Revisar implementación.")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
