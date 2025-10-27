"""
Script para crear un cierre de prueba completo para el smoke test
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Cliente
from nomina.models import CierreNomina
from datetime import date

User = get_user_model()

# 1. Obtener o crear cliente de prueba
print("=" * 60)
print("CREANDO ENTORNO DE PRUEBA - SMOKE TEST")
print("=" * 60)

cliente, created = Cliente.objects.get_or_create(
    rut="77777777-7",
    defaults={
        "nombre": "EMPRESA SMOKE TEST"
    }
)
print(f"\n✅ Cliente: {cliente.nombre} (RUT: {cliente.rut})")
if created:
    print("   [NUEVO] Cliente creado")
else:
    print("   [EXISTENTE] Cliente encontrado")

# 2. Crear cierre de prueba
periodo = "2025-10"  # Formato: "YYYY-MM"

cierre, created = CierreNomina.objects.get_or_create(
    cliente=cliente,
    periodo=periodo,
    defaults={
        "estado": "pendiente",
    }
)
print(f"\n✅ Cierre: ID={cierre.id} | Periodo={periodo}")
if created:
    print("   [NUEVO] Cierre creado")
else:
    print(f"   [EXISTENTE] Estado actual: {cierre.estado}")
    # Limpiar si ya existe
    if cierre.estado != "pendiente":
        cierre.estado = "pendiente"
        cierre.save()
        print("   [RESET] Cierre marcado como 'pendiente'")

# 3. Obtener usuario de prueba
usuario = User.objects.filter(is_superuser=True).first()
if not usuario:
    usuario = User.objects.first()
print(f"\n✅ Usuario: {usuario.correo_bdo} (ID: {usuario.id}) - {usuario.tipo_usuario}")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print(f"Cliente ID: {cliente.id}")
print(f"Cierre ID: {cierre.id}")
print(f"Usuario ID: {usuario.id}")
print(f"Periodo: {periodo}")
print("=" * 60)
print("\n✅ Entorno listo para pruebas\n")

# Guardar info para siguiente script
with open('/tmp/smoke_test_info.txt', 'w') as f:
    f.write(f"CLIENTE_ID={cliente.id}\n")
    f.write(f"CIERRE_ID={cierre.id}\n")
    f.write(f"USUARIO_ID={usuario.id}\n")
    f.write(f"PERIODO={periodo}\n")

