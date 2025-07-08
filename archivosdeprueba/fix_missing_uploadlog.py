#!/usr/bin/env python3
"""
Script to create missing UploadLog records for existing ClasificacionCuentaArchivo data
This fixes the issue where data exists but no UploadLog records were created
"""

import os
import sys
import django
from datetime import datetime
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.models import ClasificacionCuentaArchivo, UploadLog, Cliente
from django.db.models import Max, Min, Count

def create_missing_uploadlog_records():
    """
    Create UploadLog records for existing ClasificacionCuentaArchivo records
    that don't have an associated UploadLog
    """
    print("🔍 Analyzing existing ClasificacionCuentaArchivo records...")
    
    # Find all records without UploadLog
    orphaned_records = ClasificacionCuentaArchivo.objects.filter(upload_log__isnull=True)
    
    if not orphaned_records.exists():
        print("✅ No orphaned records found. All records have UploadLog associations.")
        return
    
    print(f"📊 Found {orphaned_records.count()} records without UploadLog")
    
    # Group by client
    clients_with_orphaned = orphaned_records.values('cliente').annotate(
        count=Count('id'),
        first_date=Min('fecha_subida'),
        last_date=Max('fecha_subida')
    )
    
    created_uploads = []
    
    for client_data in clients_with_orphaned:
        cliente_id = client_data['cliente']
        count = client_data['count']
        first_date = client_data['first_date'] or timezone.now()
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            print(f"\n🏢 Processing client: {cliente.razon_social} (ID: {cliente_id})")
            print(f"   📊 Records to process: {count}")
            print(f"   📅 Date range: {first_date}")
            
            # Create a new UploadLog for this client's classification data
            upload_log = UploadLog.objects.create(
                tipo_upload="clasificacion",
                cliente=cliente,
                cierre=None,  # Can be null for classification uploads
                usuario=None,  # Unknown user for retroactive creation
                nombre_archivo_original=f"Clasificaciones_Migradas_{cliente.rut}.xlsx",
                tamaño_archivo=0,  # Unknown size
                estado="completado",
                fecha_subida=first_date,
                tiempo_procesamiento=timezone.timedelta(seconds=1),
                resumen={
                    "migrado": True,
                    "registros_guardados": count,
                    "total_filas": count,
                    "filas_vacias": 0,
                    "sets_encontrados": [],
                    "errores_count": 0,
                    "descripcion": "UploadLog creado retroactivamente para datos existentes"
                },
                hash_archivo="migrated_data",
                ruta_archivo="",
                errores=""
            )
            
            # Associate all orphaned records with this UploadLog
            updated_count = ClasificacionCuentaArchivo.objects.filter(
                cliente=cliente,
                upload_log__isnull=True
            ).update(upload_log=upload_log)
            
            print(f"   ✅ Created UploadLog ID: {upload_log.id}")
            print(f"   🔗 Associated {updated_count} records")
            
            created_uploads.append({
                'upload_log_id': upload_log.id,
                'cliente': cliente.razon_social,
                'records_count': updated_count
            })
            
        except Cliente.DoesNotExist:
            print(f"   ❌ Cliente with ID {cliente_id} not found")
        except Exception as e:
            print(f"   💥 Error processing client {cliente_id}: {e}")
    
    print(f"\n🎉 Migration completed!")
    print(f"📊 Created {len(created_uploads)} UploadLog records:")
    for upload in created_uploads:
        print(f"   - UploadLog {upload['upload_log_id']}: {upload['cliente']} ({upload['records_count']} records)")
    
    return created_uploads

def verify_fix():
    """
    Verify that the fix worked correctly
    """
    print("\n🔍 Verifying the fix...")
    
    # Check UploadLog records for clasificacion
    clasificacion_uploads = UploadLog.objects.filter(tipo_upload="clasificacion")
    print(f"📊 UploadLog records for clasificacion: {clasificacion_uploads.count()}")
    
    # Check orphaned records
    orphaned_records = ClasificacionCuentaArchivo.objects.filter(upload_log__isnull=True)
    print(f"📊 Orphaned ClasificacionCuentaArchivo records: {orphaned_records.count()}")
    
    if clasificacion_uploads.exists() and orphaned_records.count() == 0:
        print("✅ Fix successful! All records now have UploadLog associations.")
        
        # Show details of created uploads
        for upload in clasificacion_uploads:
            records_count = ClasificacionCuentaArchivo.objects.filter(upload_log=upload).count()
            print(f"   - UploadLog {upload.id}: {upload.cliente.razon_social} ({records_count} records)")
        
        return True
    else:
        print("❌ Fix incomplete. Some issues remain.")
        return False

if __name__ == "__main__":
    print("🚀 Starting UploadLog migration for ClasificacionCuentaArchivo records...")
    
    try:
        created_uploads = create_missing_uploadlog_records()
        success = verify_fix()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("💡 You can now use the 'Ver Clasificaciones' button in the frontend.")
        else:
            print("\n⚠️ Migration completed with issues. Please check the output above.")
            
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        import traceback
        traceback.print_exc()
