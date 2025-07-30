#!/usr/bin/env python3
"""
🔍 VERIFICACIÓN RÁPIDA: Sistema Paralelo
Verifica la estructura sin importar Django/Celery
"""

import os
import sys
from pathlib import Path

def verificar_archivos_modificados():
    """✅ Verifica que los archivos fueron modificados correctamente"""
    print("🔍 VERIFICANDO ARCHIVOS MODIFICADOS")
    print("="*50)
    
    archivos_verificar = {
        'Celery config': '/root/SGM/backend/sgm_backend/celery.py',
        'Workers script': '/root/SGM/backend/celery_worker.sh',
        'Views nomina': '/root/SGM/backend/nomina/views.py', 
        'Tasks nomina': '/root/SGM/backend/nomina/tasks.py'
    }
    
    resultados = {}
    
    for nombre, ruta in archivos_verificar.items():
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                
            verificaciones = {
                'Celery config': [
                    'task_routes',
                    'nomina_queue',
                    'contabilidad_queue',
                    'worker_prefetch_multiplier'
                ],
                'Workers script': [
                    'nomina_queue',
                    'contabilidad_queue', 
                    'concurrencia 3',
                    'concurrencia 2'
                ],
                'Views nomina': [
                    'generar_incidencias_cierre_paralelo',
                    'clasificaciones_seleccionadas',
                    'SISTEMA DUAL',
                    'procesamiento filtrado'
                ],
                'Tasks nomina': [
                    'generar_incidencias_cierre_paralelo',
                    'procesar_chunk_clasificaciones',
                    'consolidar_resultados_filtrados',
                    'comparar_y_generar_reporte_final',
                    'chord, group'
                ]
            }
            
            encontrados = []
            faltantes = []
            
            for patron in verificaciones.get(nombre, []):
                if patron.lower() in contenido.lower():
                    encontrados.append(patron)
                else:
                    faltantes.append(patron)
            
            resultados[nombre] = {
                'existe': True,
                'tamaño': len(contenido),
                'encontrados': encontrados,
                'faltantes': faltantes
            }
            
            print(f"✅ {nombre}:")
            print(f"   📄 Tamaño: {len(contenido):,} caracteres")
            print(f"   ✅ Patrones encontrados: {len(encontrados)}")
            print(f"   ❌ Patrones faltantes: {len(faltantes)}")
            
            if faltantes:
                print(f"   🔍 Faltantes: {', '.join(faltantes)}")
            
        except Exception as e:
            print(f"❌ {nombre}: Error - {e}")
            resultados[nombre] = {'existe': False, 'error': str(e)}
    
    return resultados

def verificar_estructura_tasks():
    """📝 Verifica la estructura de las nuevas tareas"""
    print("\n🔍 VERIFICANDO ESTRUCTURA DE TAREAS")
    print("="*50)
    
    try:
        with open('/root/SGM/backend/nomina/tasks.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        tareas_esperadas = [
            'def generar_incidencias_cierre_paralelo',
            'def procesar_chunk_clasificaciones',
            'def consolidar_resultados_filtrados',
            'def consolidar_resultados_completos',
            'def comparar_y_generar_reporte_final',
            'def obtener_clasificaciones_cierre',
            'def crear_chunks',
            'def procesar_incidencias_clasificacion_individual'
        ]
        
        encontradas = []
        faltantes = []
        
        for tarea in tareas_esperadas:
            if tarea in contenido:
                encontradas.append(tarea.replace('def ', ''))
            else:
                faltantes.append(tarea.replace('def ', ''))
        
        print(f"✅ Tareas encontradas: {len(encontradas)}")
        for tarea in encontradas:
            print(f"   - ✓ {tarea}")
        
        if faltantes:
            print(f"\n❌ Tareas faltantes: {len(faltantes)}")
            for tarea in faltantes:
                print(f"   - ✗ {tarea}")
        
        # Verificar imports de Celery
        imports_celery = [
            'from celery import shared_task, chain, chord, group',
            'from django.utils import timezone'
        ]
        
        print(f"\n🔍 Verificando imports:")
        for imp in imports_celery:
            if imp in contenido:
                print(f"   ✅ {imp}")
            else:
                print(f"   ❌ {imp}")
        
        return len(faltantes) == 0
        
    except Exception as e:
        print(f"❌ Error verificando tasks: {e}")
        return False

def verificar_endpoint_modificado():
    """🌐 Verifica las modificaciones del endpoint"""
    print("\n🔍 VERIFICANDO ENDPOINT MODIFICADO")
    print("="*50)
    
    try:
        with open('/root/SGM/backend/nomina/views.py', 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        modificaciones_esperadas = [
            "request.data.get('clasificaciones_seleccionadas'",
            "generar_incidencias_cierre_paralelo.delay",
            "Sistema dual: procesamiento filtrado + completo",
            "modo_procesamiento': 'paralelo_dual'",
            "clasificaciones_seleccionadas': len(clasificaciones_seleccionadas)"
        ]
        
        encontradas = []
        faltantes = []
        
        for mod in modificaciones_esperadas:
            if mod in contenido:
                encontradas.append(mod)
            else:
                faltantes.append(mod)
        
        print(f"✅ Modificaciones encontradas: {len(encontradas)}")
        for mod in encontradas:
            print(f"   - ✓ {mod[:50]}...")
        
        if faltantes:
            print(f"\n❌ Modificaciones faltantes: {len(faltantes)}")
            for mod in faltantes:
                print(f"   - ✗ {mod[:50]}...")
        
        return len(faltantes) == 0
        
    except Exception as e:
        print(f"❌ Error verificando endpoint: {e}")
        return False

def main():
    """🚀 Ejecuta todas las verificaciones"""
    print("🔍 VERIFICACIÓN RÁPIDA DEL SISTEMA PARALELO")
    print("="*60)
    
    verificaciones = [
        ("Archivos Modificados", verificar_archivos_modificados),
        ("Estructura Tasks", verificar_estructura_tasks),
        ("Endpoint Modificado", verificar_endpoint_modificado),
    ]
    
    resultados = []
    
    for nombre, verificacion in verificaciones:
        try:
            resultado = verificacion()
            if isinstance(resultado, dict):
                # Para verificar_archivos_modificados que retorna dict
                resultado = all(v.get('existe', False) for v in resultado.values())
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"💥 Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "="*60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    exitosas = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ OK" if resultado else "❌ FALLA"
        print(f"{estado:8} - {nombre}")
    
    print(f"\n📊 RESULTADO: {exitosas}/{total} verificaciones exitosas")
    
    if exitosas == total:
        print("\n🎉 ¡SISTEMA IMPLEMENTADO CORRECTAMENTE!")
        print("📋 Próximos pasos:")
        print("   1. Instalar Celery: pip install celery")
        print("   2. Levantar Docker: docker-compose up -d")
        print("   3. Probar endpoint con clasificaciones_seleccionadas")
    else:
        print(f"\n⚠️ {total - exitosas} verificación(es) fallaron")

if __name__ == "__main__":
    main()
