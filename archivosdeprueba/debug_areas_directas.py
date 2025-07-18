#!/usr/bin/env python
"""
Debug: Verificar clientes con áreas directas y disponibilidad
"""

import os
import sys
import django
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('/root/SGM')
sys.path.append('/root/SGM/backend')

django.setup()

from api.models import Cliente, Usuario, AsignacionClienteUsuario, Area

def debug_clientes_areas_directas():
    """
    Debug de clientes con áreas directas
    """
    print("🔍 DEBUG: Clientes con áreas directas")
    print("="*60)
    
    # Obtener área de contabilidad
    try:
        area_contabilidad = Area.objects.get(nombre='Contabilidad')
        print(f"✅ Área de Contabilidad encontrada: {area_contabilidad.id}")
    except Area.DoesNotExist:
        print("❌ Área de Contabilidad no encontrada")
        return
    
    # Clientes con áreas directas
    clientes_con_areas = Cliente.objects.filter(areas__isnull=False).distinct()
    print(f"\n📊 Clientes con áreas directas: {clientes_con_areas.count()}")
    
    for cliente in clientes_con_areas:
        areas = [area.nombre for area in cliente.areas.all()]
        print(f"   🏢 {cliente.nombre} ({cliente.rut}) - Áreas: {areas}")
    
    # Clientes específicos del área de contabilidad
    clientes_contabilidad = Cliente.objects.filter(areas=area_contabilidad)
    print(f"\n📊 Clientes con área directa de Contabilidad: {clientes_contabilidad.count()}")
    
    for cliente in clientes_contabilidad:
        print(f"   🏢 {cliente.nombre} ({cliente.rut})")
        
        # Verificar si está asignado
        asignaciones = AsignacionClienteUsuario.objects.filter(cliente=cliente)
        if asignaciones.exists():
            for asignacion in asignaciones:
                print(f"      ✅ Asignado a: {asignacion.usuario.nombre} {asignacion.usuario.apellido}")
        else:
            print(f"      ⚠️  No asignado")
    
    # Verificar analistas de contabilidad
    print(f"\n👤 Analistas de Contabilidad:")
    analistas_contabilidad = Usuario.objects.filter(
        tipo_usuario='analista',
        areas=area_contabilidad,
        is_active=True
    )
    
    for analista in analistas_contabilidad:
        print(f"   👤 {analista.nombre} {analista.apellido} ({analista.correo_bdo})")
        
        # Contar clientes asignados
        clientes_asignados = AsignacionClienteUsuario.objects.filter(usuario=analista).count()
        print(f"      📊 Clientes asignados: {clientes_asignados}")
    
    # Verificar gerentes de contabilidad
    print(f"\n👑 Gerentes de Contabilidad:")
    gerentes_contabilidad = Usuario.objects.filter(
        tipo_usuario='gerente',
        areas=area_contabilidad,
        is_active=True
    )
    
    for gerente in gerentes_contabilidad:
        print(f"   👑 {gerente.nombre} {gerente.apellido} ({gerente.correo_bdo})")

def crear_cliente_ejemplo():
    """
    Crear un cliente de ejemplo con área directa de contabilidad
    """
    print("\n🏗️  Creando cliente de ejemplo...")
    
    try:
        area_contabilidad = Area.objects.get(nombre='Contabilidad')
        
        # Crear cliente
        cliente = Cliente.objects.create(
            nombre='Cliente Ejemplo Areas Directas',
            rut='99999999-9',
            bilingue=False
        )
        
        # Asignar área directa
        cliente.areas.add(area_contabilidad)
        
        print(f"✅ Cliente creado: {cliente.nombre} ({cliente.rut})")
        print(f"   📍 Área asignada: {area_contabilidad.nombre}")
        
        return cliente
        
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        return None

def main():
    print("🔧 SCRIPT DE DEBUG - ÁREAS DIRECTAS")
    print("="*60)
    
    debug_clientes_areas_directas()
    
    print("\n" + "="*60)
    print("¿Crear cliente de ejemplo? (y/N):")
    respuesta = input().strip().lower()
    
    if respuesta == 'y':
        crear_cliente_ejemplo()
        print("\n" + "="*60)
        print("DESPUÉS DE CREAR CLIENTE:")
        debug_clientes_areas_directas()

if __name__ == "__main__":
    main()
