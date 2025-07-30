#!/usr/bin/env python3
"""
Script de monitoreo para analizar el rendimiento de Celery Chord en consolidación
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from celery import Celery
from nomina.models import CierreNomina

def monitorear_consolidacion():
    """Monitorea el rendimiento de la consolidación con Chord"""
    
    print("🔍 Monitor de Rendimiento - Consolidación con Celery Chord")
    print("=" * 60)
    
    # Obtener estadísticas de cierres recientes
    cierres_recientes = CierreNomina.objects.filter(
        fecha_creacion__gte=datetime.now() - timedelta(days=1)
    ).order_by('-fecha_creacion')[:5]
    
    if not cierres_recientes:
        print("❌ No se encontraron cierres recientes para analizar")
        return
    
    print(f"📊 Analizando {len(cierres_recientes)} cierres recientes:")
    print()
    
    for cierre in cierres_recientes:
        print(f"🏢 {cierre.cliente.razon_social} - {cierre.periodo}")
        print(f"   📅 Creado: {cierre.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📊 Estado: {cierre.estado}")
        
        # Estadísticas de consolidación
        empleados_count = cierre.nominas_consolidadas.count() if hasattr(cierre, 'nominas_consolidadas') else 0
        movimientos_count = cierre.movimientos_personal.count() if hasattr(cierre, 'movimientos_personal') else 0
        
        print(f"   👥 Empleados consolidados: {empleados_count}")
        print(f"   🔄 Movimientos detectados: {movimientos_count}")
        
        # Calcular eficiencia aproximada
        if empleados_count > 0:
            if empleados_count < 50:
                rendimiento = "🟢 Excelente (< 50 empleados)"
            elif empleados_count < 150:
                rendimiento = "🟡 Bueno (50-150 empleados)"
            else:
                rendimiento = "🔴 Moderado (> 150 empleados)"
            
            print(f"   ⚡ Rendimiento esperado: {rendimiento}")
        
        print("-" * 40)
        print()
    
    print("💡 Recomendaciones de Optimización:")
    print("   • Para > 200 empleados: Considerar chunks más pequeños")
    print("   • Para > 500 empleados: Implementar procesamiento por lotes")
    print("   • Para > 1000 empleados: Usar queue dedicada para consolidación")
    print()
    
    # Verificar configuración de Celery
    print("🔧 Configuración Celery recomendada:")
    print("   • Workers: 4-8 procesos paralelos")
    print("   • Concurrency: 2-4 por worker")
    print("   • Queue: Dedicada para consolidación")
    print("   • Timeout: 300s para tareas largas")

def sugerir_optimizaciones():
    """Sugiere optimizaciones basadas en el uso actual"""
    
    print("\n🚀 Optimizaciones Adicionales Disponibles:")
    print("=" * 50)
    
    optimizaciones = [
        {
            "titulo": "1. Chunk Size Dinámico",
            "descripcion": "Ajustar tamaño de lotes según número de empleados",
            "beneficio": "Optimización automática del rendimiento"
        },
        {
            "titulo": "2. Cache de Conceptos",
            "descripcion": "Cachear clasificaciones de conceptos frecuentes",
            "beneficio": "Reducir consultas DB en ~40%"
        },
        {
            "titulo": "3. Bulk Operations",
            "descripcion": "Usar bulk_create para inserciones masivas",
            "beneficio": "Acelerar escritura DB en ~60%"
        },
        {
            "titulo": "4. Queue Prioritizada",
            "descripcion": "Queue dedicada con alta prioridad para consolidación",
            "beneficio": "Garantizar recursos para consolidación"
        },
        {
            "titulo": "5. Monitoreo Real-time",
            "descripcion": "WebSocket para tracking de progreso",
            "beneficio": "Mejor UX durante consolidación"
        }
    ]
    
    for opt in optimizaciones:
        print(f"🔹 {opt['titulo']}")
        print(f"   📋 {opt['descripcion']}")
        print(f"   ✅ Beneficio: {opt['beneficio']}")
        print()

if __name__ == "__main__":
    try:
        monitorear_consolidacion()
        sugerir_optimizaciones()
    except Exception as e:
        print(f"❌ Error en monitoreo: {e}")
        sys.exit(1)
