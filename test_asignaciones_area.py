#!/usr/bin/env python
"""
Script de prueba para validar la nueva lógica de asignaciones por área
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Usuario, Cliente, Area, AsignacionClienteUsuario, Servicio, ServicioCliente
from rest_framework.exceptions import ValidationError

def test_asignacion_areas():
    print("🧪 Iniciando pruebas de asignación por áreas...")
    
    # Crear áreas de prueba
    area_contabilidad, _ = Area.objects.get_or_create(nombre="Contabilidad")
    area_nomina, _ = Area.objects.get_or_create(nombre="Nomina")
    
    # Crear usuarios de prueba
    gerente, _ = Usuario.objects.get_or_create(
        correo_bdo="gerente@test.com",
        defaults={
            'nombre': 'Gerente',
            'apellido': 'Test',
            'tipo_usuario': 'gerente',
            'cargo_bdo': 'Gerente'
        }
    )
    gerente.areas.add(area_contabilidad, area_nomina)
    
    # Analista solo de contabilidad
    analista1, _ = Usuario.objects.get_or_create(
        correo_bdo="analista1@test.com",
        defaults={
            'nombre': 'Analista1',
            'apellido': 'Contabilidad',
            'tipo_usuario': 'analista',
            'cargo_bdo': 'Analista'
        }
    )
    analista1.areas.add(area_contabilidad)
    
    # Analista solo de nómina
    analista2, _ = Usuario.objects.get_or_create(
        correo_bdo="analista2@test.com",
        defaults={
            'nombre': 'Analista2',
            'apellido': 'Nomina',
            'tipo_usuario': 'analista',
            'cargo_bdo': 'Analista'
        }
    )
    analista2.areas.add(area_nomina)
    
    # Analista de ambas áreas
    analista3, _ = Usuario.objects.get_or_create(
        correo_bdo="analista3@test.com",
        defaults={
            'nombre': 'Analista3',
            'apellido': 'Mixto',
            'tipo_usuario': 'analista',
            'cargo_bdo': 'Analista'
        }
    )
    analista3.areas.add(area_contabilidad, area_nomina)
    
    # Crear cliente de prueba
    cliente, _ = Cliente.objects.get_or_create(
        rut="12345678-9",
        defaults={
            'nombre': 'Cliente Test',
            'email': 'cliente@test.com',
            'telefono': '123456789'
        }
    )
    
    print("✅ Datos de prueba creados")
    
    # Test 1: Asignar cliente a analista de contabilidad
    print("\n📝 Test 1: Asignar cliente a analista de contabilidad")
    try:
        asignacion1 = AsignacionClienteUsuario.objects.create(
            cliente=cliente,
            usuario=analista1
        )
        print(f"✅ Asignación exitosa: {asignacion1}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Intentar asignar el mismo cliente a otro analista de contabilidad (debería fallar)
    print("\n📝 Test 2: Intentar asignar el mismo cliente a otro analista de contabilidad")
    try:
        asignacion2 = AsignacionClienteUsuario.objects.create(
            cliente=cliente,
            usuario=analista3  # Tiene contabilidad, debería fallar
        )
        print(f"❌ NO DEBERÍA permitir esta asignación: {asignacion2}")
    except Exception as e:
        print(f"✅ Correcto! Validación funcionó: {e}")
    
    # Test 3: Asignar el mismo cliente a analista de nómina (debería permitirse)
    print("\n📝 Test 3: Asignar el mismo cliente a analista de nómina")
    try:
        asignacion3 = AsignacionClienteUsuario.objects.create(
            cliente=cliente,
            usuario=analista2  # Solo nómina, debería permitirse
        )
        print(f"✅ Asignación exitosa en área diferente: {asignacion3}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    print("\n🧹 Limpiando datos de prueba...")
    AsignacionClienteUsuario.objects.filter(cliente=cliente).delete()
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    test_asignacion_areas()
