#!/usr/bin/env python3
"""
Script de debugging para verificar el estado de UploadLog
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.models import UploadLog
from nomina.models import LibroRemuneracionesUpload
from api.models import Cliente

def verificar_upload_logs():
    """
    Verifica el estado de los UploadLogs
    """
    print("🔍 VERIFICANDO UPLOAD LOGS")
    print("=" * 50)
    
    try:
        # Obtener todos los upload logs
        upload_logs = UploadLog.objects.all().order_by('-fecha_creacion')
        
        print(f"Total de UploadLogs: {upload_logs.count()}")
        print()
        
        for log in upload_logs[:10]:  # Mostrar últimos 10
            print(f"ID: {log.id}")
            print(f"Cliente: {log.cliente}")
            print(f"Archivo: {log.nombre_archivo_original}")
            print(f"Estado: {log.estado}")
            print(f"Tipo Upload: {log.tipo_upload}")
            print(f"Fecha: {log.fecha_creacion}")
            print(f"Ruta Archivo: {log.ruta_archivo}")
            print(f"Resumen: {log.resumen}")
            print(f"Errores: {log.errores}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error verificando upload logs: {e}")

def verificar_libros_remuneraciones():
    """
    Verifica el estado de los LibroRemuneracionesUpload
    """
    print("\n📚 VERIFICANDO LIBROS DE REMUNERACIONES")
    print("=" * 50)
    
    try:
        libros = LibroRemuneracionesUpload.objects.all().order_by('-id')
        
        print(f"Total de Libros: {libros.count()}")
        print()
        
        for libro in libros[:10]:  # Mostrar últimos 10
            print(f"ID: {libro.id}")
            print(f"Cierre: {libro.cierre}")
            print(f"Estado: {libro.estado}")
            print(f"Upload Log: {libro.upload_log}")
            print(f"Archivo: {libro.archivo}")
            print(f"Headers JSON: {libro.header_json is not None}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error verificando libros: {e}")

def verificar_clientes():
    """
    Verifica el estado de los clientes
    """
    print("\n👥 VERIFICANDO CLIENTES")
    print("=" * 50)
    
    try:
        clientes = Cliente.objects.all()
        
        print(f"Total de Clientes: {clientes.count()}")
        print()
        
        for cliente in clientes[:5]:  # Mostrar primeros 5
            print(f"ID: {cliente.id}")
            print(f"Nombre: {cliente.nombre}")
            print(f"RUT: {cliente.rut}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error verificando clientes: {e}")

def crear_upload_log_test():
    """
    Crear un UploadLog de prueba para verificar que funciona
    """
    print("\n🧪 CREANDO UPLOAD LOG DE PRUEBA")
    print("=" * 50)
    
    try:
        # Obtener primer cliente
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes disponibles")
            return
        
        # Crear upload log de prueba
        upload_log = UploadLog.objects.create(
            cliente=cliente,
            nombre_archivo_original="test_libro.xlsx",
            tipo_upload="libro_remuneraciones",
            estado="pendiente",
            ruta_archivo="test/path/libro.xlsx",
            resumen={"test": True}
        )
        
        print(f"✅ Upload log creado exitosamente con ID: {upload_log.id}")
        
        # Verificar que se puede recuperar
        upload_log_retrieved = UploadLog.objects.get(id=upload_log.id)
        print(f"✅ Upload log recuperado exitosamente: {upload_log_retrieved}")
        
        # Limpiar
        upload_log.delete()
        print("🧹 Upload log de prueba eliminado")
        
    except Exception as e:
        print(f"❌ Error creando upload log de prueba: {e}")

def main():
    """
    Función principal
    """
    print("🔍 SCRIPT DE DEBUGGING - UPLOAD LOGS")
    print("=" * 60)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    verificar_upload_logs()
    verificar_libros_remuneraciones()
    verificar_clientes()
    crear_upload_log_test()
    
    print("\n✅ DEBUGGING COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main()
