#!/usr/bin/env python3
"""
Script para probar el sistema de snapshots de incidencias
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from contabilidad.models import UploadLog, CierreContabilidad
from contabilidad.tasks_libro_mayor import crear_snapshot_incidencias_consolidadas
from contabilidad.views.incidencias import obtener_incidencias_consolidadas_optimizado
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from api.models import Usuario

def probar_sistema_snapshots():
    print("=== Probando Sistema de Snapshots de Incidencias ===\n")
    
    # 1. Verificar datos existentes
    print("1. Verificando datos existentes...")
    cierres = CierreContabilidad.objects.all()
    print(f"   - Total cierres: {cierres.count()}")
    
    for cierre in cierres:
        upload_logs = UploadLog.objects.filter(
            cierre=cierre,
            tipo_upload='libro_mayor'
        )
        print(f"   - Cierre {cierre.id} ({cierre.periodo}): {upload_logs.count()} upload logs")
        
        for upload in upload_logs:
            snapshot_exists = (
                upload.resumen and 
                'incidencias_snapshot' in upload.resumen
            )
            print(f"     * Upload {upload.id} (iteración {upload.iteracion}): "
                 f"Snapshot: {'✓' if snapshot_exists else '✗'}")
    
    # 2. Si hay upload logs sin snapshot, crearlos
    print("\n2. Creando snapshots faltantes...")
    uploads_sin_snapshot = UploadLog.objects.filter(
        tipo_upload='libro_mayor',
        estado='completado'
    ).exclude(
        resumen__has_key='incidencias_snapshot'
    )
    
    print(f"   - Upload logs sin snapshot: {uploads_sin_snapshot.count()}")
    
    for upload in uploads_sin_snapshot:
        try:
            print(f"   - Creando snapshot para upload {upload.id}...")
            snapshot = crear_snapshot_incidencias_consolidadas(upload.id)
            print(f"     ✓ Snapshot creado con {len(snapshot.get('incidencias_detectadas', []))} tipos de incidencias")
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    # 3. Probar endpoint optimizado
    print("\n3. Probando endpoint optimizado...")
    factory = RequestFactory()
    
    try:
        usuario = Usuario.objects.first()
        print(f"   - Usuario de prueba: {usuario.correo_bdo if usuario else 'None'}")
    except:
        usuario = None
        print("   - Sin usuario de prueba")
    
    for cierre in cierres:
        print(f"\n   - Probando cierre {cierre.id} ({cierre.periodo}):")
        
        request = factory.get(f'/api/contabilidad/libro-mayor/{cierre.id}/incidencias-optimizado/')
        request.user = usuario if usuario else AnonymousUser()
        
        try:
            response = obtener_incidencias_consolidadas_optimizado(request, cierre.id)
            print(f"     Status: {response.status_code}")
            
            if hasattr(response, 'data'):
                data = response.data
                if 'error' in data:
                    print(f"     Error: {data['error']}")
                else:
                    incidencias = data.get('incidencias', [])
                    fuente = data.get('fuente_datos', 'unknown')
                    print(f"     Incidencias: {len(incidencias)}")
                    print(f"     Fuente: {fuente}")
                    
                    if 'iteracion_info' in data:
                        iter_info = data['iteracion_info']
                        print(f"     Iteración: {iter_info.get('iteracion_numero', 'unknown')}")
                        print(f"     Es principal: {iter_info.get('es_principal', False)}")
            
        except Exception as e:
            print(f"     ✗ Error en endpoint: {e}")
    
    print("\n=== Prueba completada ===")

if __name__ == '__main__':
    probar_sistema_snapshots()
