#!/usr/bin/env python3
"""
🚀 DEMO DEL SISTEMA DE TASKS PARA INFORMES DE NÓMINA

Este script demuestra el nuevo sistema asíncrono implementado para la generación
de informes de nómina, mostrando ambos modos: sincrónico y asíncrono.

Uso:
    python demo_tasks_nomina.py
"""

import os
import sys
import requests
import time
import json
from datetime import datetime

# Configuración de demo
API_BASE_URL = "http://localhost:8000/api/nomina"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN_HERE"  # Reemplazar con token real
}

def print_banner():
    """Imprime banner de inicio"""
    print("=" * 80)
    print("🚀 DEMO - SISTEMA DE TASKS PARA INFORMES DE NÓMINA")
    print("=" * 80)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API Base: {API_BASE_URL}")
    print()

def demo_finalizar_sincronico(cierre_id):
    """Demo de finalización sincrónica (modo original)"""
    print("1️⃣ FINALIZACIÓN SINCRÓNICA")
    print("-" * 50)
    
    print(f"📋 Finalizando cierre {cierre_id} en modo sincrónico...")
    
    # Simular request (en demo real usarías requests)
    demo_response = {
        "success": True,
        "modo": "sincrono",
        "informe_id": 123,
        "mensaje": "Cierre finalizado e informe generado exitosamente",
        "duracion_segundos": 0.056,
        "datos_cierre": {
            "kpis_principales": {
                "costo_empresa_total": 45500000,
                "dotacion_calculada": 133,
                "remuneracion_promedio_mes": 1200000,
                "tasa_ausentismo_porcentaje": 8.5
            }
        }
    }
    
    print(f"✅ Respuesta recibida inmediatamente:")
    print(f"   💰 Costo empresa: ${demo_response['datos_cierre']['kpis_principales']['costo_empresa_total']:,.0f}")
    print(f"   👥 Empleados: {demo_response['datos_cierre']['kpis_principales']['dotacion_calculada']}")
    print(f"   💵 Remuneración promedio: ${demo_response['datos_cierre']['kpis_principales']['remuneracion_promedio_mes']:,.0f}")
    print(f"   🏥 Ausentismo: {demo_response['datos_cierre']['kpis_principales']['tasa_ausentismo_porcentaje']}%")
    print(f"   ⏱️  Tiempo: {demo_response['duracion_segundos']} segundos")
    print()

def demo_finalizar_asincrono(cierre_id):
    """Demo de finalización asíncrona (modo nuevo)"""
    print("2️⃣ FINALIZACIÓN ASÍNCRONA")
    print("-" * 50)
    
    print(f"🚀 Iniciando finalización asíncrona para cierre {cierre_id}...")
    
    # Simular inicio de task
    task_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    
    print(f"✅ Task iniciado:")
    print(f"   📋 Task ID: {task_id}")
    print(f"   📊 Estado: INICIANDO")
    print()
    
    # Simular progreso
    pasos = [
        (10, "Validando cierre y obteniendo datos..."),
        (25, "Obteniendo datos de base de datos..."),
        (40, "Calculando KPIs principales..."),
        (60, "Generando lista detallada de empleados..."),
        (75, "Ejecutando cálculos avanzados..."),
        (90, "Guardando informe y enviando a Redis..."),
        (100, "Proceso completado exitosamente")
    ]
    
    print("📈 Progreso del task:")
    for porcentaje, descripcion in pasos:
        print(f"   [{porcentaje:3d}%] {descripcion}")
        time.sleep(0.5)  # Simular tiempo de procesamiento
    
    print()
    print("✅ Task completado exitosamente!")
    
    # Simular resultado final
    resultado_final = {
        "success": True,
        "informe_id": 124,
        "cierre_id": cierre_id,
        "duracion_segundos": 15.2,
        "estadisticas": {
            "total_empleados": 450,
            "total_conceptos": 2800,
            "kpis_calculados": 52,
            "tamaño_kb": 85.3,
            "modo_calculo": "completo",
            "redis_enviado": True
        },
        "datos_resumen": {
            "costo_empresa_total": 125000000,
            "dotacion_calculada": 450,
            "remuneracion_promedio": 1350000,
            "tasa_ausentismo": 6.8
        }
    }
    
    print(f"📊 Resultado final:")
    print(f"   💰 Costo empresa: ${resultado_final['datos_resumen']['costo_empresa_total']:,.0f}")
    print(f"   👥 Empleados: {resultado_final['datos_resumen']['dotacion_calculada']}")
    print(f"   💵 Remuneración promedio: ${resultado_final['datos_resumen']['remuneracion_promedio']:,.0f}")
    print(f"   🏥 Ausentismo: {resultado_final['datos_resumen']['tasa_ausentismo']}%")
    print(f"   ⏱️  Tiempo total: {resultado_final['duracion_segundos']} segundos")
    print(f"   💾 Tamaño informe: {resultado_final['estadisticas']['tamaño_kb']} KB")
    print(f"   🚀 Redis: {'✅' if resultado_final['estadisticas']['redis_enviado'] else '❌'}")
    print()

def demo_modo_hibrido():
    """Demo del modo híbrido que decide automáticamente"""
    print("3️⃣ MODO HÍBRIDO (AUTO-DECISIÓN)")
    print("-" * 50)
    
    casos = [
        {"empleados": 50, "modo_esperado": "sincrónico", "razon": "Pocos empleados"},
        {"empleados": 150, "modo_esperado": "sincrónico", "razon": "Cantidad moderada"},
        {"empleados": 250, "modo_esperado": "asíncrono", "razon": "Muchos empleados"},
        {"empleados": 500, "modo_esperado": "asíncrono", "razon": "Empresa grande"},
    ]
    
    print("📊 Decisión automática basada en número de empleados:")
    print(f"{'Empleados':<10} {'Modo':<12} {'Razón':<20}")
    print("-" * 45)
    
    for caso in casos:
        empleados = caso["empleados"]
        modo = caso["modo_esperado"]
        razon = caso["razon"]
        emoji = "⚡" if modo == "sincrónico" else "🚀"
        print(f"{empleados:<10} {emoji} {modo:<10} {razon}")
    
    print()
    print("🎯 Threshold configurable: 200 empleados (por defecto)")
    print("💡 El usuario puede forzar cualquier modo si lo desea")
    print()

def demo_endpoints_disponibles():
    """Muestra todos los endpoints disponibles"""
    print("4️⃣ ENDPOINTS DISPONIBLES")
    print("-" * 50)
    
    endpoints = [
        {
            "metodo": "POST",
            "url": "/cierres/{id}/finalizar/",
            "descripcion": "Finalización híbrida (auto-decide sync/async)",
            "nuevo": False
        },
        {
            "metodo": "POST", 
            "url": "/cierres/{id}/finalizar-async/",
            "descripcion": "Finalización asíncrona forzada",
            "nuevo": True
        },
        {
            "metodo": "GET",
            "url": "/tasks/{task_id}/progreso/",
            "descripcion": "Consultar progreso de task",
            "nuevo": True
        },
        {
            "metodo": "GET",
            "url": "/tasks/{task_id}/resultado/",
            "descripcion": "Obtener resultado final de task",
            "nuevo": True
        },
        {
            "metodo": "POST",
            "url": "/tasks/{task_id}/cancelar/",
            "descripcion": "Cancelar task en progreso",
            "nuevo": True
        },
        {
            "metodo": "POST",
            "url": "/cierres/{id}/regenerar-informe/",
            "descripcion": "Regenerar informe existente",
            "nuevo": True
        },
        {
            "metodo": "GET",
            "url": "/cierres/{id}/estado-informe/",
            "descripcion": "Consultar estado de informe",
            "nuevo": True
        },
        {
            "metodo": "GET",
            "url": "/tasks/activos/",
            "descripcion": "Listar tasks activos",
            "nuevo": True
        },
        {
            "metodo": "GET",
            "url": "/tasks/estadisticas/",
            "descripcion": "Estadísticas de uso de tasks",
            "nuevo": True
        }
    ]
    
    for endpoint in endpoints:
        estado = "🆕 NUEVO" if endpoint["nuevo"] else "📋 EXISTENTE"
        print(f"{estado} {endpoint['metodo']:<6} {endpoint['url']:<35} {endpoint['descripcion']}")
    
    print()

def demo_comparacion_modos():
    """Comparación detallada entre modos"""
    print("5️⃣ COMPARACIÓN SINCRÓNICO vs ASÍNCRONO")
    print("-" * 50)
    
    comparacion = [
        ("Característica", "Sincrónico", "Asíncrono"),
        ("━━━━━━━━━━━━━", "━━━━━━━━━━━", "━━━━━━━━━━"),
        ("Respuesta", "Inmediata", "Diferida"),
        ("Progress tracking", "❌ No", "✅ Sí"),
        ("Cancelación", "❌ No", "✅ Sí"),
        ("Timeout risk", "⚠️  Posible", "✅ No"),
        ("Escalabilidad", "📊 Limitada", "🚀 Alta"),
        ("Simplicidad", "✅ Alta", "📊 Media"),
        ("UX pequeños", "✅ Excelente", "📊 Buena"),
        ("UX grandes", "⚠️  Regular", "✅ Excelente"),
        ("Debugging", "✅ Fácil", "📊 Medio"),
        ("Recursos", "💾 Mínimos", "🔧 Moderados"),
    ]
    
    for fila in comparacion:
        print(f"{fila[0]:<16} {fila[1]:<12} {fila[2]:<12}")
    
    print()
    print("🎯 RECOMENDACIÓN:")
    print("   • Usar modo híbrido para mejor experiencia")
    print("   • Sincrónico para cierres <200 empleados")
    print("   • Asíncrono para cierres >200 empleados")
    print()

def demo_uso_frontend():
    """Ejemplo de uso desde frontend"""
    print("6️⃣ INTEGRACIÓN FRONTEND")
    print("-" * 50)
    
    print("📱 Código JavaScript para frontend:")
    print()
    
    js_code = '''
// 1. Finalización híbrida (recomendado)
async function finalizarCierre(cierreId) {
    const response = await fetch(`/api/nomina/cierres/${cierreId}/finalizar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    
    const result = await response.json();
    
    if (result.modo === 'sincrono') {
        // Respuesta inmediata
        console.log('Informe generado:', result.datos_cierre);
        mostrarInforme(result);
    } else {
        // Modo asíncrono - hacer polling
        monitoreartask(result.task_id);
    }
}

// 2. Monitoreo de task asíncrono
async function monitorearTask(taskId) {
    const intervalo = setInterval(async () => {
        const response = await fetch(`/api/nomina/tasks/${taskId}/progreso/`);
        const progreso = await response.json();
        
        // Actualizar UI con progreso
        actualizarBarraProgreso(progreso.porcentaje);
        actualizarTexto(progreso.descripcion);
        
        if (progreso.state === 'SUCCESS') {
            clearInterval(intervalo);
            obtenerResultadoFinal(taskId);
        }
    }, 1000);
}

// 3. Obtener resultado final
async function obtenerResultadoFinal(taskId) {
    const response = await fetch(`/api/nomina/tasks/${taskId}/resultado/`);
    const resultado = await response.json();
    
    if (resultado.state === 'SUCCESS') {
        console.log('Informe completado:', resultado.resultado);
        mostrarInforme(resultado.resultado);
    }
}
'''
    
    print(js_code)
    print()

def main():
    """Función principal del demo"""
    print_banner()
    
    # Demo con diferentes tamaños de cierre
    cierre_pequeno = 101  # <200 empleados
    cierre_grande = 102   # >200 empleados
    
    demo_finalizar_sincronico(cierre_pequeno)
    demo_finalizar_asincrono(cierre_grande)
    demo_modo_hibrido()
    demo_endpoints_disponibles()
    demo_comparacion_modos()
    demo_uso_frontend()
    
    print("=" * 80)
    print("✅ DEMO COMPLETADO")
    print("=" * 80)
    print()
    print("🎯 PRÓXIMOS PASOS:")
    print("   1. Probar endpoints en entorno de desarrollo")
    print("   2. Integrar frontend con nuevo sistema")
    print("   3. Configurar monitoreo de Celery")
    print("   4. Ajustar threshold según necesidades")
    print()
    print("📚 DOCUMENTACIÓN:")
    print("   • Ver ANALISIS_FLUJO_INFORMES_NOMINA.md")
    print("   • Ver tasks_informes.py para detalles técnicos")
    print("   • Ver views_tasks.py para implementación API")
    print()

if __name__ == "__main__":
    main()
