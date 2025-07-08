#!/usr/bin/env python3
"""
Script para verificar que los upload logs se actualicen correctamente
después de los cambios en los tasks.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from nomina.models import UploadLogNomina, LibroRemuneracionesUpload, CierreNomina
from api.models import Cliente
from datetime import datetime

def verificar_logs_recientes():
    """Verifica los logs de upload más recientes"""
    print("🔍 Verificando logs de upload recientes...")
    
    # Obtener los logs más recientes
    logs = UploadLogNomina.objects.all().order_by('-fecha_creacion')[:10]
    
    if not logs:
        print("❌ No se encontraron logs de upload")
        return
    
    print(f"📊 Encontrados {len(logs)} logs recientes:")
    print("-" * 80)
    
    for log in logs:
        print(f"ID: {log.id}")
        print(f"Tipo: {log.tipo}")
        print(f"Estado: {log.estado}")
        print(f"Cliente: {log.cliente}")
        print(f"Fecha creación: {log.fecha_creacion}")
        print(f"Fecha procesamiento: {log.fecha_procesamiento}")
        print(f"Progreso: {log.progreso}%")
        print(f"Resumen: {log.resumen}")
        if log.errores:
            print(f"Errores: {log.errores}")
        print("-" * 40)
    
    # Verificar logs en estado "procesando"
    logs_procesando = UploadLogNomina.objects.filter(estado='procesando')
    if logs_procesando.exists():
        print(f"⚠️  Hay {logs_procesando.count()} logs en estado 'procesando':")
        for log in logs_procesando:
            print(f"  - ID {log.id}: {log.tipo} del cliente {log.cliente}")
    
    # Verificar logs completados recientemente
    logs_completados = UploadLogNomina.objects.filter(estado='completado').order_by('-fecha_procesamiento')[:5]
    if logs_completados.exists():
        print(f"✅ Logs completados recientemente ({logs_completados.count()}):")
        for log in logs_completados:
            print(f"  - ID {log.id}: {log.tipo} - {log.resumen}")

def verificar_libros_remuneraciones():
    """Verifica el estado de los libros de remuneraciones"""
    print("\n📚 Verificando libros de remuneraciones...")
    
    libros = LibroRemuneracionesUpload.objects.all().order_by('-fecha_subida')[:10]
    
    if not libros:
        print("❌ No se encontraron libros de remuneraciones")
        return
    
    print(f"📊 Encontrados {len(libros)} libros recientes:")
    print("-" * 80)
    
    for libro in libros:
        print(f"ID: {libro.id}")
        print(f"Estado: {libro.estado}")
        print(f"Fecha subida: {libro.fecha_subida}")
        print(f"Upload log: {libro.upload_log}")
        
        # Verificar si tiene upload log asociado
        if libro.upload_log:
            print(f"  - Log estado: {libro.upload_log.estado}")
            print(f"  - Log progreso: {libro.upload_log.progreso}%")
            print(f"  - Log resumen: {libro.upload_log.resumen}")
        else:
            print("  - ⚠️ Sin upload log asociado")
        
        # Verificar headers
        if libro.header_json:
            if isinstance(libro.header_json, dict):
                clasificados = len(libro.header_json.get('headers_clasificados', []))
                sin_clasificar = len(libro.header_json.get('headers_sin_clasificar', []))
                print(f"  - Headers: {clasificados} clasificados, {sin_clasificar} sin clasificar")
            else:
                print(f"  - Headers: {len(libro.header_json)} detectados")
        
        print("-" * 40)

def verificar_inconsistencias():
    """Busca inconsistencias entre libros y sus upload logs"""
    print("\n🔍 Verificando inconsistencias...")
    
    # Buscar libros con upload log en estado diferente
    libros_con_log = LibroRemuneracionesUpload.objects.filter(upload_log__isnull=False)
    
    inconsistencias = []
    
    for libro in libros_con_log:
        # Caso 1: Libro completado pero log procesando
        if libro.estado in ['clasif_pendiente', 'clasificado', 'procesado'] and libro.upload_log.estado == 'procesando':
            inconsistencias.append({
                'libro_id': libro.id,
                'problema': f"Libro en estado '{libro.estado}' pero log en 'procesando'",
                'libro_estado': libro.estado,
                'log_estado': libro.upload_log.estado
            })
        
        # Caso 2: Libro con error pero log sin error
        if libro.estado == 'con_error' and libro.upload_log.estado != 'error':
            inconsistencias.append({
                'libro_id': libro.id,
                'problema': f"Libro con error pero log en '{libro.upload_log.estado}'",
                'libro_estado': libro.estado,
                'log_estado': libro.upload_log.estado
            })
    
    if inconsistencias:
        print(f"❌ Encontradas {len(inconsistencias)} inconsistencias:")
        for inc in inconsistencias:
            print(f"  - Libro ID {inc['libro_id']}: {inc['problema']}")
    else:
        print("✅ No se encontraron inconsistencias")

def main():
    print("🔧 Verificador de Upload Logs - Nómina")
    print("=" * 50)
    
    verificar_logs_recientes()
    verificar_libros_remuneraciones()
    verificar_inconsistencias()
    
    print("\n✅ Verificación completada")

if __name__ == "__main__":
    main()
