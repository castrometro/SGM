#!/usr/bin/env python3
"""
Script de debug para probar el procesamiento del Libro Mayor
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.models import UploadLog, LibroMayorArchivo, MovimientoContable, Incidencia
from contabilidad.tasks_libro_mayor import crear_chain_libro_mayor

def debug_ultimo_upload_log():
    """Debug del último upload log de libro mayor"""
    print("=== DEBUG ÚLTIMO UPLOAD LOG ===")
    
    # Buscar el último upload log de libro mayor
    ultimo_upload = UploadLog.objects.filter(
        tipo_upload="libro_mayor"
    ).order_by('-fecha_subida').first()
    
    if not ultimo_upload:
        print("❌ No se encontró ningún upload log de libro mayor")
        return
    
    print(f"📋 Upload Log ID: {ultimo_upload.id}")
    print(f"📅 Fecha: {ultimo_upload.fecha_subida}")
    print(f"📊 Estado: {ultimo_upload.estado}")
    print(f"👤 Cliente: {ultimo_upload.cliente.nombre if ultimo_upload.cliente else 'No definido'}")
    print(f"🔄 Cierre: {ultimo_upload.cierre.id if ultimo_upload.cierre else 'No definido'}")
    
    if ultimo_upload.errores:
        print(f"❌ Errores: {ultimo_upload.errores}")
    
    print(f"\n📝 Resumen:")
    resumen = ultimo_upload.resumen or {}
    
    # Campos de compatibilidad con frontend
    movimientos_creados = resumen.get('movimientos_creados', 0)
    incidencias_creadas = resumen.get('incidencias_creadas', 0)
    
    print(f"  • Movimientos creados: {movimientos_creados}")
    print(f"  • Incidencias creadas: {incidencias_creadas}")
    
    # Información detallada
    if 'procesamiento' in resumen:
        proc = resumen['procesamiento']
        print(f"  • Filas procesadas: {proc.get('filas_procesadas', 0)}")
        print(f"  • Aperturas creadas: {proc.get('aperturas_creadas', 0)}")
        print(f"  • Cuentas creadas: {proc.get('cuentas_creadas', 0)}")
        print(f"  • Errores: {proc.get('errores_count', 0)}")
    
    # Verificar LibroMayorArchivo asociado
    archivo_obj = LibroMayorArchivo.objects.filter(upload_log=ultimo_upload).first()
    if archivo_obj:
        print(f"\n📁 LibroMayorArchivo encontrado:")
        print(f"  • ID: {archivo_obj.id}")
        print(f"  • Estado: {archivo_obj.estado}")
        print(f"  • Procesado: {archivo_obj.procesado}")
        print(f"  • Upload Log ID: {archivo_obj.upload_log.id if archivo_obj.upload_log else 'No asignado'}")
    else:
        print(f"\n❌ No se encontró LibroMayorArchivo para este upload_log")
    
    # Verificar movimientos creados
    if ultimo_upload.cierre:
        movimientos_count = MovimientoContable.objects.filter(cierre=ultimo_upload.cierre).count()
        incidencias_count = Incidencia.objects.filter(cierre=ultimo_upload.cierre).count()
        print(f"\n📊 En base de datos:")
        print(f"  • Movimientos en cierre: {movimientos_count}")
        print(f"  • Incidencias en cierre: {incidencias_count}")
    
    return ultimo_upload

def debug_libros_mayor_cierre(cierre_id):
    """Debug de libros mayor para un cierre específico"""
    print(f"\n=== DEBUG LIBROS MAYOR CIERRE {cierre_id} ===")
    
    libros = LibroMayorArchivo.objects.filter(cierre_id=cierre_id).order_by('-fecha_subida')
    
    if not libros.exists():
        print("❌ No se encontraron libros mayor para este cierre")
        return
    
    for libro in libros:
        print(f"\n📁 Libro Mayor ID: {libro.id}")
        print(f"  • Estado: {libro.estado}")
        print(f"  • Procesado: {libro.procesado}")
        print(f"  • Fecha subida: {libro.fecha_subida}")
        print(f"  • Upload Log: {libro.upload_log.id if libro.upload_log else 'No asignado'}")
        
        if libro.upload_log:
            resumen = libro.upload_log.resumen or {}
            movimientos = resumen.get('movimientos_creados', 0)
            incidencias = resumen.get('incidencias_creadas', 0)
            print(f"  • Movimientos: {movimientos}")
            print(f"  • Incidencias: {incidencias}")
        
        if libro.errores:
            print(f"  • Errores: {libro.errores}")

if __name__ == "__main__":
    print("🔍 INICIANDO DEBUG DEL LIBRO MAYOR")
    
    # Debug del último upload log
    ultimo_upload = debug_ultimo_upload_log()
    
    # Si hay un upload log, debug del cierre asociado
    if ultimo_upload and ultimo_upload.cierre:
        debug_libros_mayor_cierre(ultimo_upload.cierre.id)
    
    print("\n✅ DEBUG COMPLETADO")
