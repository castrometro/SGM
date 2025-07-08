#!/usr/bin/env python3
"""
Script para medir el costo de la consulta de incidencias consolidadas
y diagnosticar problemas potenciales
"""

import time
import json
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q, Count, Sum
from django.test import Client
from django.contrib.auth import get_user_model
from contabilidad.models import CierreContabilidad, UploadLog
from contabilidad.models_incidencias import IncidenciaResumen

User = get_user_model()

def medir_consulta_incidencias(cierre_id, verbose=True):
    """
    Mide el tiempo de ejecución de la consulta de incidencias consolidadas
    """
    print(f"\n=== ANÁLISIS DE PERFORMANCE - INCIDENCIAS CONSOLIDADAS ===")
    print(f"Cierre ID: {cierre_id}")
    
    # Verificar que el cierre existe
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        print(f"✓ Cierre encontrado: {cierre.periodo} - {cierre.cliente.nombre}")
    except CierreContabilidad.DoesNotExist:
        print(f"✗ Error: Cierre {cierre_id} no encontrado")
        return
    
    # Contar registros base
    total_incidencias = IncidenciaResumen.objects.filter(
        upload_log__cierre_id=cierre_id
    ).count()
    print(f"Total incidencias en el cierre: {total_incidencias}")
    
    if total_incidencias == 0:
        print("⚠️  No hay incidencias para analizar")
        return
    
    # Medir consulta principal
    start_time = time.time()
    
    queryset = IncidenciaResumen.objects.filter(
        upload_log__cierre_id=cierre_id
    ).select_related('upload_log', 'resuelto_por', 'creada_por')
    
    # Simular el procesamiento del endpoint
    incidencias = []
    for inc in queryset.order_by('-severidad', '-fecha_deteccion'):
        # Simular construcción del objeto de respuesta
        incidencia_data = {
            'id': inc.id,
            'tipo_incidencia': inc.get_tipo_incidencia_display(),
            'tipo_codigo': inc.tipo_incidencia,
            'codigo_problema': inc.codigo_problema,
            'cantidad_afectada': inc.cantidad_afectada,
            'severidad': inc.get_severidad_display(),
            'severidad_codigo': inc.severidad,
            'estado': inc.get_estado_display(),
            'estado_codigo': inc.estado,
            'elementos_afectados': inc.elementos_afectados[:10],  # Limitar para performance
            'detalle_muestra': inc.detalle_muestra,
            'estadisticas': inc.estadisticas,  # Corregir nombre
            'fecha_deteccion': inc.fecha_deteccion,
            'fecha_resolucion': inc.fecha_resolucion,
            'resuelto_por': inc.resuelto_por.username if inc.resuelto_por else None,
            'creada_por': inc.creada_por.username if inc.creada_por else None,
            'upload_log': {
                'id': inc.upload_log.id,
                'nombre_archivo': inc.upload_log.nombre_archivo_original,
                'fecha_subida': inc.upload_log.fecha_subida,
            }
        }
        incidencias.append(incidencia_data)
    
    end_time = time.time()
    consulta_tiempo = end_time - start_time
    
    # Medir consultas de estadísticas
    start_stats = time.time()
    
    estadisticas = {
        'total_incidencias': queryset.count(),
        'por_estado': dict(queryset.values('estado').annotate(count=Count('id')).values_list('estado', 'count')),
        'por_severidad': dict(queryset.values('severidad').annotate(count=Count('id')).values_list('severidad', 'count')),
        'por_tipo': dict(queryset.values('tipo_incidencia').annotate(count=Count('id')).values_list('tipo_incidencia', 'count')),
    }
    
    total_elementos_afectados = sum(inc.cantidad_afectada for inc in queryset)
    
    end_stats = time.time()
    stats_tiempo = end_stats - start_stats
    
    total_tiempo = end_time - start_time
    
    # Mostrar resultados
    print(f"\n=== RESULTADOS DE PERFORMANCE ===")
    print(f"📊 Consulta principal: {consulta_tiempo:.4f}s")
    print(f"📈 Estadísticas: {stats_tiempo:.4f}s")
    print(f"⏱️  Tiempo total: {total_tiempo:.4f}s")
    print(f"📋 Registros procesados: {len(incidencias)}")
    print(f"🎯 Elementos afectados: {total_elementos_afectados}")
    
    # Análisis de performance
    print(f"\n=== ANÁLISIS DE PERFORMANCE ===")
    if total_tiempo < 0.1:
        print("🟢 EXCELENTE: Consulta muy rápida (< 100ms)")
    elif total_tiempo < 0.5:
        print("🟡 BUENA: Consulta rápida (< 500ms)")
    elif total_tiempo < 1.0:
        print("🟠 REGULAR: Consulta moderada (< 1s)")
    else:
        print("🔴 LENTA: Consulta lenta (> 1s) - Se recomienda optimización")
    
    print(f"📊 Promedio por registro: {total_tiempo/len(incidencias):.6f}s")
    
    # Mostrar consultas SQL ejecutadas
    if verbose:
        print(f"\n=== CONSULTAS SQL EJECUTADAS ===")
        for query in connection.queries[-10:]:  # Últimas 10 consultas
            print(f"⏱️  {query['time']}s: {query['sql'][:100]}...")
    
    # Estadísticas detalladas
    print(f"\n=== ESTADÍSTICAS DETALLADAS ===")
    print(f"Por estado: {estadisticas['por_estado']}")
    print(f"Por severidad: {estadisticas['por_severidad']}")
    print(f"Por tipo: {estadisticas['por_tipo']}")
    
    return {
        'tiempo_total': total_tiempo,
        'tiempo_consulta': consulta_tiempo,
        'tiempo_stats': stats_tiempo,
        'registros': len(incidencias),
        'elementos_afectados': total_elementos_afectados,
        'estadisticas': estadisticas
    }

def analizar_indices_db():
    """
    Analiza los índices disponibles en la tabla de incidencias
    """
    print(f"\n=== ANÁLISIS DE ÍNDICES ===")
    
    with connection.cursor() as cursor:
        # Obtener información de índices para la tabla de incidencias
        cursor.execute("""
            SELECT 
                indexname, 
                indexdef 
            FROM pg_indexes 
            WHERE tablename = 'contabilidad_incidenciaresumen'
        """)
        
        indices = cursor.fetchall()
        print(f"Índices encontrados en contabilidad_incidenciaresumen:")
        for nombre, definicion in indices:
            print(f"  📋 {nombre}: {definicion}")
        
        # Verificar si hay índice en upload_log__cierre_id
        cursor.execute("""
            SELECT COUNT(*)
            FROM pg_indexes 
            WHERE tablename = 'contabilidad_incidenciaresumen'
            AND indexdef LIKE '%upload_log_id%'
        """)
        
        tiene_indice_upload = cursor.fetchone()[0] > 0
        print(f"¿Tiene índice en upload_log_id? {'✓' if tiene_indice_upload else '✗'}")

def test_endpoint_performance(cierre_id):
    """
    Prueba el endpoint completo via HTTP
    """
    print(f"\n=== TEST ENDPOINT HTTP ===")
    
    # Crear cliente de prueba
    client = Client()
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_performance',
        defaults={'email': 'test@example.com'}
    )
    
    # Login
    client.force_login(user)
    
    # Medir endpoint
    start_time = time.time()
    response = client.get(f'/api/contabilidad/libro-mayor/{cierre_id}/incidencias-consolidadas/')
    end_time = time.time()
    
    endpoint_tiempo = end_time - start_time
    
    print(f"⏱️  Tiempo endpoint HTTP: {endpoint_tiempo:.4f}s")
    print(f"📊 Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📋 Incidencias devueltas: {len(data.get('incidencias', []))}")
        print(f"📈 Total elementos afectados: {data.get('total_elementos_afectados', 0)}")
    else:
        print(f"❌ Error en endpoint: {response.content}")
    
    return endpoint_tiempo

def main():
    """
    Función principal de análisis
    """
    print("🔍 ANÁLISIS DE PERFORMANCE - INCIDENCIAS CONSOLIDADAS")
    print("=" * 60)
    
    # Buscar cierres con incidencias
    cierres_con_incidencias = CierreContabilidad.objects.filter(
        uploadlog__incidenciaresumen__isnull=False
    ).distinct().order_by('-periodo')[:3]
    
    if not cierres_con_incidencias:
        print("❌ No se encontraron cierres con incidencias para analizar")
        return
    
    print(f"📋 Cierres encontrados con incidencias: {len(cierres_con_incidencias)}")
    
    # Analizar cada cierre
    resultados = []
    for cierre in cierres_con_incidencias:
        print(f"\n" + "="*60)
        resultado = medir_consulta_incidencias(cierre.id)
        if resultado:
            resultado['cierre_id'] = cierre.id
            resultado['periodo'] = cierre.periodo
            resultados.append(resultado)
            
            # Test endpoint HTTP
            try:
                tiempo_http = test_endpoint_performance(cierre.id)
                resultado['tiempo_http'] = tiempo_http
            except Exception as e:
                print(f"❌ Error testing endpoint: {e}")
    
    # Analizar índices
    analizar_indices_db()
    
    # Resumen final
    print(f"\n" + "="*60)
    print(f"🎯 RESUMEN FINAL")
    print(f"=" * 60)
    
    if resultados:
        tiempo_promedio = sum(r['tiempo_total'] for r in resultados) / len(resultados)
        registros_promedio = sum(r['registros'] for r in resultados) / len(resultados)
        
        print(f"📊 Tiempo promedio: {tiempo_promedio:.4f}s")
        print(f"📋 Registros promedio: {registros_promedio:.1f}")
        print(f"⚡ Throughput: {registros_promedio/tiempo_promedio:.1f} registros/s")
        
        # Recomendaciones
        print(f"\n🎯 RECOMENDACIONES:")
        if tiempo_promedio > 1.0:
            print("🔴 OPTIMIZACIÓN NECESARIA:")
            print("  - Implementar paginación")
            print("  - Agregar índices en campos de filtro")
            print("  - Considerar caché en Redis")
            print("  - Limitar elementos_afectados por defecto")
        elif tiempo_promedio > 0.5:
            print("🟡 OPTIMIZACIÓN RECOMENDADA:")
            print("  - Implementar paginación opcional")
            print("  - Considerar caché para estadísticas")
        else:
            print("🟢 PERFORMANCE ACEPTABLE")
            print("  - Monitorear con crecimiento de datos")
    
    print(f"\n✅ Análisis completado")

if __name__ == "__main__":
    import os
    import sys
    import django
    
    # Configurar Django
    sys.path.append('/root/SGM')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    main()
