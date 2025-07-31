#!/usr/bin/env python3
"""
🧪 TEST SIMPLE: Verificar Sistema Dual de Incidencias

Test simplificado para verificar que el sistema dual funcione correctamente.
"""

import os
import sys
import time
from datetime import datetime

# Configurar el entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM/backend')

import django
django.setup()

from nomina.models import CierreNomina, IncidenciaCierre

def test_simple():
    """Test simple del sistema"""
    print("🧪 TEST SIMPLE - SISTEMA DUAL DE INCIDENCIAS")
    print("=" * 50)
    
    # 1. Encontrar cierre de prueba
    cierre = CierreNomina.objects.filter(
        estado__in=['datos_consolidados', 'con_incidencias']
    ).order_by('-fecha_creacion').first()
    
    if not cierre:
        print("❌ No hay cierres válidos para prueba")
        return False
    
    print(f"✅ Usando cierre: {cierre.id} ({cierre.mes}/{cierre.año})")
    
    # 2. Verificar campo tipo_comparacion
    try:
        # Contar incidencias por tipo
        total_incidencias = IncidenciaCierre.objects.filter(cierre=cierre).count()
        individuales = IncidenciaCierre.objects.filter(
            cierre=cierre, 
            tipo_comparacion='individual'
        ).count()
        suma_total = IncidenciaCierre.objects.filter(
            cierre=cierre, 
            tipo_comparacion='suma_total'
        ).count()
        
        print(f"📊 Total incidencias: {total_incidencias}")
        print(f"📋 Individuales: {individuales}")
        print(f"📈 Suma total: {suma_total}")
        print("✅ Campo tipo_comparacion disponible")
        
        # 3. Mostrar ejemplos
        if total_incidencias > 0:
            print("\n📄 EJEMPLOS DE INCIDENCIAS:")
            for inc in IncidenciaCierre.objects.filter(cierre=cierre)[:3]:
                tipo = getattr(inc, 'tipo_comparacion', 'legacy')
                print(f"   • [{tipo}] {inc.tipo_incidencia}: {inc.descripcion[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando campo: {e}")
        print("⚠️  Puede que falte aplicar migraciones")
        return False

def test_celery_task():
    """Test de tarea Celery"""
    print("\n🎵 TEST TAREA CELERY")
    print("-" * 30)
    
    try:
        from nomina.tasks import generar_incidencias_cierre_paralelo
        
        # Encontrar cierre
        cierre = CierreNomina.objects.filter(
            estado__in=['datos_consolidados', 'con_incidencias']
        ).first()
        
        if not cierre:
            print("❌ No hay cierre para probar")
            return False
        
        print(f"🎯 Probando con cierre {cierre.id}")
        
        # Ejecutar tarea
        resultado = generar_incidencias_cierre_paralelo(
            cierre_id=cierre.id,
            clasificaciones_seleccionadas=['haberes_imponibles']
        )
        
        print("✅ Tarea ejecutada exitosamente")
        print(f"📊 Resultado: {resultado.get('success', False)}")
        
        if 'configuracion_completada' in resultado:
            print("🎯 Sistema paralelo configurado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando tarea: {e}")
        return False

def test_direct_function():
    """Test de función directa"""
    print("\n🔧 TEST FUNCIÓN DIRECTA")
    print("-" * 30)
    
    try:
        from nomina.utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidados_v2
        
        # Encontrar cierre
        cierre = CierreNomina.objects.filter(
            estado__in=['datos_consolidados', 'con_incidencias']
        ).first()
        
        if not cierre:
            print("❌ No hay cierre para probar")
            return False
        
        print(f"🎯 Probando con cierre {cierre.id}")
        
        # Ejecutar función
        inicio = time.time()
        resultado = generar_incidencias_consolidados_v2(
            cierre_id=cierre.id,
            clasificaciones_seleccionadas=['haberes_imponibles']
        )
        tiempo = time.time() - inicio
        
        print(f"✅ Función ejecutada en {tiempo:.2f}s")
        print(f"📊 Éxito: {resultado.get('success', False)}")
        print(f"🎯 Total incidencias: {resultado.get('total_incidencias', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando función: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SISTEMA DUAL - VERIFICACIÓN COMPLETA")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar tests
    tests = [
        ("Campo tipo_comparacion", test_simple),
        ("Tarea Celery", test_celery_task),
        ("Función directa", test_direct_function)
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        print(f"🧪 EJECUTANDO: {nombre}")
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
            print(f"{'✅' if resultado else '❌'} {nombre}: {'ÉXITO' if resultado else 'FALLO'}")
        except Exception as e:
            resultados.append((nombre, False))
            print(f"💥 {nombre}: ERROR - {e}")
        print()
    
    # Resumen final
    print("📊 RESUMEN FINAL")
    print("=" * 30)
    exitosos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        print(f"{'✅' if resultado else '❌'} {nombre}")
    
    print()
    print(f"🎯 Resultado: {exitosos}/{total} tests exitosos")
    
    if exitosos == total:
        print("🎉 TODOS LOS TESTS PASARON")
        sys.exit(0)
    else:
        print("⚠️  ALGUNOS TESTS FALLARON")
        sys.exit(1)
