#!/usr/bin/env python3
"""
Script para probar eliminación de archivos desde Django Admin para MovimientosMes
"""

import os
import sys
import django
from pathlib import Path

# Añadir el path del backend al sistema
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGM.settings')
django.setup()

from nomina.models import MovimientosMesUpload, CierreNomina, Cliente
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
from datetime import datetime

def test_eliminacion_archivo_movimientos():
    """
    Test para verificar que los signals eliminan archivos físicos
    """
    print("🧪 Iniciando test de eliminación de archivos MovimientosMes...")
    
    try:
        # 1. Crear o buscar un cliente y cierre de prueba
        cliente, created = Cliente.objects.get_or_create(
            id=999,
            defaults={
                'nombre': 'Cliente Test MovimientosMes',
                'rut': '99999999-9'
            }
        )
        print(f"✅ Cliente: {cliente.nombre}")
        
        cierre, created = CierreNomina.objects.get_or_create(
            cliente=cliente,
            periodo='2025-09',
            defaults={'estado': 'pendiente'}
        )
        print(f"✅ Cierre: {cierre.periodo}")
        
        # 2. Crear archivo temporal de prueba
        contenido_excel = b"fake excel content for testing"
        archivo_test = SimpleUploadedFile(
            "test_movimientos_mes.xlsx",
            contenido_excel,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # 3. Crear MovimientosMesUpload
        movimiento = MovimientosMesUpload.objects.create(
            cierre=cierre,
            archivo=archivo_test,
            estado='pendiente'
        )
        print(f"✅ MovimientosMes creado con ID: {movimiento.id}")
        
        # 4. Verificar que el archivo se guardó físicamente
        archivo_path = movimiento.archivo.path
        print(f"📁 Archivo guardado en: {archivo_path}")
        
        if os.path.exists(archivo_path):
            print(f"✅ Archivo existe físicamente: {os.path.getsize(archivo_path)} bytes")
        else:
            print(f"❌ ERROR: Archivo no existe físicamente")
            return False
        
        # 5. Eliminar el registro (simulando Django Admin)
        print("🗑️ Eliminando registro desde Django ORM (simula Django Admin)...")
        movimiento_id = movimiento.id
        movimiento.delete()
        print(f"✅ Registro MovimientosMes {movimiento_id} eliminado")
        
        # 6. Verificar que el archivo físico fue eliminado por el signal
        if os.path.exists(archivo_path):
            print(f"❌ ERROR: Archivo AÚN EXISTE después de eliminar registro")
            print(f"   Path: {archivo_path}")
            return False
        else:
            print(f"✅ SUCCESS: Archivo físico eliminado correctamente por signal")
            return True
            
    except Exception as e:
        print(f"❌ ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup: eliminar datos de prueba si aún existen
        try:
            MovimientosMesUpload.objects.filter(cierre__cliente__id=999).delete()
            CierreNomina.objects.filter(cliente__id=999).delete()
            Cliente.objects.filter(id=999).delete()
            print("🧹 Cleanup completado")
        except:
            pass

def test_actualizacion_archivo_movimientos():
    """
    Test para verificar que al actualizar archivo, se elimina el anterior
    """
    print("\n🧪 Iniciando test de actualización de archivos MovimientosMes...")
    
    try:
        # 1. Crear cliente y cierre
        cliente, created = Cliente.objects.get_or_create(
            id=998,
            defaults={
                'nombre': 'Cliente Test Update MovimientosMes',
                'rut': '99999998-8'
            }
        )
        
        cierre, created = CierreNomina.objects.get_or_create(
            cliente=cliente,
            periodo='2025-09',
            defaults={'estado': 'pendiente'}
        )
        
        # 2. Crear primer archivo
        archivo1 = SimpleUploadedFile(
            "movimientos_v1.xlsx",
            b"contenido archivo 1",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        movimiento = MovimientosMesUpload.objects.create(
            cierre=cierre,
            archivo=archivo1,
            estado='pendiente'
        )
        
        archivo1_path = movimiento.archivo.path
        print(f"📁 Archivo 1 guardado en: {archivo1_path}")
        
        if not os.path.exists(archivo1_path):
            print("❌ ERROR: Archivo 1 no se guardó")
            return False
        
        # 3. Actualizar con segundo archivo
        archivo2 = SimpleUploadedFile(
            "movimientos_v2.xlsx",
            b"contenido archivo 2",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        print("🔄 Actualizando archivo (simula resubida)...")
        movimiento.archivo = archivo2
        movimiento.save()
        
        archivo2_path = movimiento.archivo.path
        print(f"📁 Archivo 2 guardado en: {archivo2_path}")
        
        # 4. Verificar que archivo 1 fue eliminado y archivo 2 existe
        if os.path.exists(archivo1_path):
            print(f"❌ ERROR: Archivo anterior AÚN EXISTE: {archivo1_path}")
            return False
        else:
            print(f"✅ SUCCESS: Archivo anterior eliminado correctamente")
        
        if os.path.exists(archivo2_path):
            print(f"✅ SUCCESS: Archivo nuevo existe: {archivo2_path}")
        else:
            print(f"❌ ERROR: Archivo nuevo no existe")
            return False
        
        return True
            
    except Exception as e:
        print(f"❌ ERROR en test actualización: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            MovimientosMesUpload.objects.filter(cierre__cliente__id=998).delete()
            CierreNomina.objects.filter(cliente__id=998).delete()
            Cliente.objects.filter(id=998).delete()
            print("🧹 Cleanup test actualización completado")
        except:
            pass

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TEST DE SIGNALS DE ELIMINACIÓN - MOVIMIENTOS MES")
    print("=" * 70)
    
    # Test 1: Eliminación completa
    test1_success = test_eliminacion_archivo_movimientos()
    
    # Test 2: Actualización (elimina anterior)
    test2_success = test_actualizacion_archivo_movimientos()
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS:")
    print(f"   Test Eliminación:   {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Test Actualización: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS LOS TESTS PASARON - Signals funcionan correctamente")
        print("✅ Los archivos SE ELIMINAN desde Django Admin")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON - Revisar signals")
    
    print("=" * 70)
