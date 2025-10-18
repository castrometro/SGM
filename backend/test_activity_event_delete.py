#!/usr/bin/env python3
"""
Test para verificar si ActivityEvent.log() funciona en perform_destroy
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from nomina.models import ActivityEvent, LibroRemuneracionesUpload, CierreNomina
from api.models import Usuario

# Obtener datos de test
libro = LibroRemuneracionesUpload.objects.first()
if not libro:
    print("❌ No hay libros en la BD")
    sys.exit(1)

user = Usuario.objects.first()
cierre = libro.cierre
cliente = cierre.cliente

print(f"📋 Datos de test:")
print(f"   Libro ID: {libro.id}")
print(f"   Cierre ID: {cierre.id}")
print(f"   Cliente: {cliente.nombre}")
print(f"   User: {user.nombre}")

# Intentar crear el evento
print(f"\n🧪 Probando ActivityEvent.log()...")

try:
    event = ActivityEvent.log(
        user=user,
        cliente=cliente,
        cierre=cierre,
        event_type='delete',
        action='test_eliminacion',
        resource_type='libro_remuneraciones',
        resource_id=str(libro.id),
        details={
            'libro_id': libro.id,
            'test': True
        }
    )
    
    print(f"✅ Evento creado exitosamente!")
    print(f"   Event ID: {event.id}")
    print(f"   Cierre ID: {event.cierre_id}")
    print(f"   Action: {event.action}")
    print(f"   Details: {event.details}")
    
except Exception as e:
    print(f"❌ Error creando evento:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
