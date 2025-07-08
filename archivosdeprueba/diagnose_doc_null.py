#!/usr/bin/env python3
"""
Script para diagnosticar incidencias DOC_NULL en el Libro Mayor
"""
import os
import sys
import django

# Setup Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from contabilidad.models import (
    CierreContable, MovimientoContable, Incidencia, 
    ExcepcionValidacion, UploadLog
)

def diagnosticar_doc_null():
    print("=== DIAGNÓSTICO DE INCIDENCIAS DOC_NULL ===\n")
    
    # Obtener el último cierre
    ultimo_cierre = CierreContable.objects.order_by('-fecha_cierre').first()
    if not ultimo_cierre:
        print("❌ No se encontraron cierres contables")
        return
    
    print(f"📅 Cierre analizado: {ultimo_cierre.fecha_cierre} (ID: {ultimo_cierre.id})")
    print(f"🏢 Cliente: {ultimo_cierre.cliente.nombre}\n")
    
    # Contar movimientos totales
    total_movimientos = MovimientoContable.objects.filter(cierre=ultimo_cierre).count()
    print(f"📊 Total de movimientos: {total_movimientos}")
    
    # Contar movimientos sin tipo_doc_codigo
    movimientos_sin_tipo = MovimientoContable.objects.filter(
        cierre=ultimo_cierre,
        tipo_doc_codigo__isnull=True
    ).count()
    
    movimientos_tipo_vacio = MovimientoContable.objects.filter(
        cierre=ultimo_cierre,
        tipo_doc_codigo=''
    ).count()
    
    movimientos_sin_tipo_total = MovimientoContable.objects.filter(
        cierre=ultimo_cierre
    ).filter(
        models.Q(tipo_doc_codigo__isnull=True) | models.Q(tipo_doc_codigo='')
    ).count()
    
    print(f"🔍 Movimientos con tipo_doc_codigo NULL: {movimientos_sin_tipo}")
    print(f"🔍 Movimientos con tipo_doc_codigo vacío: {movimientos_tipo_vacio}")
    print(f"🔍 Total movimientos sin tipo de documento: {movimientos_sin_tipo_total}")
    
    # Verificar excepciones
    excepciones = ExcepcionValidacion.objects.filter(
        cliente=ultimo_cierre.cliente,
        tipo_excepcion='movimientos_tipodoc_nulo',
        activa=True
    )
    print(f"🚫 Excepciones activas para DOC_NULL: {excepciones.count()}")
    
    if excepciones.exists():
        print("   Cuentas con excepción:")
        for exc in excepciones:
            print(f"   - {exc.codigo_cuenta}")
    
    # Verificar incidencias DOC_NULL actuales
    incidencias_doc_null = Incidencia.objects.filter(
        cierre=ultimo_cierre,
        tipo=Incidencia.DOC_NULL
    ).count()
    print(f"⚠️  Incidencias DOC_NULL registradas: {incidencias_doc_null}")
    
    # Mostrar muestra de movimientos problemáticos
    print("\n🔎 MUESTRA DE MOVIMIENTOS SIN TIPO DE DOCUMENTO:")
    movimientos_problema = MovimientoContable.objects.filter(
        cierre=ultimo_cierre
    ).filter(
        models.Q(tipo_doc_codigo__isnull=True) | models.Q(tipo_doc_codigo='')
    ).select_related('cuenta')[:10]
    
    for mov in movimientos_problema:
        print(f"   ID: {mov.id}, Cuenta: {mov.cuenta.codigo}, "
              f"Tipo Doc: '{mov.tipo_doc_codigo}', Monto: {mov.monto}")
    
    # Análisis por cuenta
    print("\n📋 ANÁLISIS POR CUENTA (Top 10):")
    from django.db.models import Count
    
    cuentas_problema = MovimientoContable.objects.filter(
        cierre=ultimo_cierre
    ).filter(
        models.Q(tipo_doc_codigo__isnull=True) | models.Q(tipo_doc_codigo='')
    ).values('cuenta__codigo').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for cuenta in cuentas_problema:
        print(f"   Cuenta {cuenta['cuenta__codigo']}: {cuenta['count']} movimientos")
    
    print("\n✅ Diagnóstico completado")

if __name__ == '__main__':
    from django.db import models
    diagnosticar_doc_null()
