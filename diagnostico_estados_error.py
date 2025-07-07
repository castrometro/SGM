#!/usr/bin/env python3
"""
Script para probar que los estados de error se manejan correctamente
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def verificar_estados_error():
    """
    Verifica que los estados de error se mantengan correctamente
    """
    print("🔍 VERIFICANDO ESTADOS DE ERROR EN LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        from backend.nomina.models import UploadLogNomina, LibroRemuneracionesUpload
        
        # Verificar UploadLogNomina con estado error
        upload_logs_error = UploadLogNomina.objects.filter(estado="error")
        print(f"📋 UploadLogNomina con estado 'error': {upload_logs_error.count()}")
        
        for upload_log in upload_logs_error[:5]:  # Mostrar solo los primeros 5
            print(f"   - ID: {upload_log.id}, Creado: {upload_log.created_at}")
            print(f"     Error: {upload_log.errores}")
            print(f"     Archivo: {upload_log.nombre_archivo_original}")
            print(f"     Resumen: {upload_log.resumen}")
            print()
        
        # Verificar LibroRemuneracionesUpload con estado error
        libros_error = LibroRemuneracionesUpload.objects.filter(estado="con_error")
        print(f"📚 LibroRemuneracionesUpload con estado 'con_error': {libros_error.count()}")
        
        for libro in libros_error[:5]:  # Mostrar solo los primeros 5
            print(f"   - ID: {libro.id}, Creado: {libro.created_at}")
            print(f"     Cierre: {libro.cierre.id if libro.cierre else 'N/A'}")
            print(f"     Upload Log: {libro.upload_log.id if libro.upload_log else 'N/A'}")
            print()
        
        # Verificar correlación entre upload_log y libro
        print("🔗 CORRELACIÓN ENTRE UPLOAD_LOG Y LIBRO:")
        for upload_log in upload_logs_error:
            if upload_log.resumen and 'libro_id' in upload_log.resumen:
                libro_id = upload_log.resumen['libro_id']
                try:
                    libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
                    print(f"   ✅ UploadLog {upload_log.id} -> Libro {libro.id} (estado: {libro.estado})")
                except LibroRemuneracionesUpload.DoesNotExist:
                    print(f"   ❌ UploadLog {upload_log.id} -> Libro {libro_id} (NO ENCONTRADO)")
        
        # Verificar libros en estado "analizando_hdrs"
        libros_analizando = LibroRemuneracionesUpload.objects.filter(estado="analizando_hdrs")
        print(f"\n🔄 LibroRemuneracionesUpload con estado 'analizando_hdrs': {libros_analizando.count()}")
        
        for libro in libros_analizando[:5]:
            print(f"   - ID: {libro.id}, Creado: {libro.created_at}")
            print(f"     Cierre: {libro.cierre.id if libro.cierre else 'N/A'}")
            print(f"     Upload Log: {libro.upload_log.id if libro.upload_log else 'N/A'}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def verificar_cierres_periodos():
    """
    Verifica los períodos de los cierres para debugging
    """
    print("\n🗓️ VERIFICANDO PERÍODOS DE CIERRES")
    print("=" * 60)
    
    try:
        from backend.nomina.models import CierreNomina
        
        cierres = CierreNomina.objects.all()[:10]  # Mostrar primeros 10
        print(f"📅 Total de cierres: {CierreNomina.objects.count()}")
        print("\nPrimeros 10 cierres:")
        
        for cierre in cierres:
            print(f"   - ID: {cierre.id}, Período: {cierre.periodo}")
            print(f"     Cliente: {cierre.cliente.razon_social if cierre.cliente else 'N/A'}")
            print(f"     Estado: {cierre.estado}")
            print()
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Función principal
    """
    print("🔍 DIAGNÓSTICO DE ESTADOS DE ERROR")
    print("=" * 70)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    verificar_estados_error()
    verificar_cierres_periodos()
    
    print("\n✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 70)

if __name__ == "__main__":
    main()
