#!/usr/bin/env python
"""
Script para migrar clientes existentes de servicios contratados a áreas directas
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

from api.models import Cliente, Area, ServicioCliente, Servicio

def migrar_clientes_a_areas_directas():
    """
    Migra todos los clientes que tienen servicios contratados a áreas directas
    """
    print("🔄 Iniciando migración de clientes a áreas directas...")
    
    # Obtener todos los clientes que tienen servicios contratados pero no áreas directas
    clientes_para_migrar = Cliente.objects.filter(
        servicios_contratados__isnull=False,
        areas__isnull=True
    ).distinct()
    
    print(f"📊 Clientes encontrados para migrar: {clientes_para_migrar.count()}")
    
    migrados = 0
    errores = 0
    
    for cliente in clientes_para_migrar:
        try:
            # Obtener áreas de los servicios contratados
            areas_servicios = Area.objects.filter(
                servicios__precios_cliente__cliente=cliente
            ).distinct()
            
            if areas_servicios.exists():
                print(f"🔄 Migrando {cliente.nombre} ({cliente.rut})")
                
                # Mostrar servicios actuales
                servicios = cliente.servicios_contratados.all()
                print(f"   📋 Servicios: {[f'{s.servicio.nombre} ({s.servicio.area.nombre})' for s in servicios]}")
                
                # Asignar áreas directas
                cliente.areas.set(areas_servicios)
                
                areas_asignadas = [area.nombre for area in areas_servicios]
                print(f"   ✅ Áreas asignadas: {areas_asignadas}")
                
                migrados += 1
            else:
                print(f"⚠️  {cliente.nombre} ({cliente.rut}) - No tiene áreas en servicios")
                
        except Exception as e:
            print(f"❌ Error al migrar {cliente.nombre}: {e}")
            errores += 1
    
    print(f"\n{'='*50}")
    print("RESUMEN DE MIGRACIÓN")
    print(f"{'='*50}")
    print(f"✅ Clientes migrados: {migrados}")
    print(f"❌ Errores: {errores}")
    print(f"📊 Total procesados: {migrados + errores}")
    
    return migrados, errores

def crear_clientes_ejemplo():
    """
    Crear algunos clientes de ejemplo con áreas directas
    """
    print("\n🏗️  Creando clientes de ejemplo...")
    
    # Obtener áreas
    try:
        area_contabilidad = Area.objects.get(nombre='Contabilidad')
        area_nomina = Area.objects.get(nombre='Nomina')
    except Area.DoesNotExist:
        print("❌ No se encontraron las áreas Contabilidad y/o Nomina")
        return
    
    clientes_ejemplo = [
        {
            'nombre': 'Empresa ABC SpA',
            'rut': '12345678-9',
            'areas': [area_contabilidad]
        },
        {
            'nombre': 'Constructora XYZ Ltda',
            'rut': '87654321-0',
            'areas': [area_nomina]
        },
        {
            'nombre': 'Servicios Integrales DEF',
            'rut': '11111111-1',
            'areas': [area_contabilidad, area_nomina]
        }
    ]
    
    for cliente_data in clientes_ejemplo:
        cliente, created = Cliente.objects.get_or_create(
            rut=cliente_data['rut'],
            defaults={
                'nombre': cliente_data['nombre'],
                'bilingue': False
            }
        )
        
        if created:
            print(f"✅ Cliente creado: {cliente.nombre} ({cliente.rut})")
        else:
            print(f"ℹ️  Cliente existente: {cliente.nombre} ({cliente.rut})")
        
        # Asignar áreas
        cliente.areas.set(cliente_data['areas'])
        areas_nombres = [area.nombre for area in cliente_data['areas']]
        print(f"   📍 Áreas asignadas: {areas_nombres}")

def mostrar_estado_actual():
    """
    Muestra el estado actual de los clientes y sus áreas
    """
    print("\n📊 ESTADO ACTUAL DE CLIENTES")
    print("="*60)
    
    # Clientes con áreas directas
    clientes_con_areas = Cliente.objects.filter(areas__isnull=False).distinct()
    print(f"✅ Clientes con áreas directas: {clientes_con_areas.count()}")
    
    for cliente in clientes_con_areas:
        areas = [area.nombre for area in cliente.areas.all()]
        print(f"   🏢 {cliente.nombre} ({cliente.rut}) - Áreas: {areas}")
    
    # Clientes sin áreas directas pero con servicios
    clientes_sin_areas = Cliente.objects.filter(
        areas__isnull=True,
        servicios_contratados__isnull=False
    ).distinct()
    print(f"\n⚠️  Clientes sin áreas directas (con servicios): {clientes_sin_areas.count()}")
    
    for cliente in clientes_sin_areas:
        servicios = cliente.servicios_contratados.all()
        areas_servicios = [s.servicio.area.nombre for s in servicios]
        print(f"   🏢 {cliente.nombre} ({cliente.rut}) - Servicios en áreas: {areas_servicios}")
    
    # Clientes sin áreas ni servicios
    clientes_vacios = Cliente.objects.filter(
        areas__isnull=True,
        servicios_contratados__isnull=True
    )
    print(f"\n🚫 Clientes sin áreas ni servicios: {clientes_vacios.count()}")
    
    for cliente in clientes_vacios:
        print(f"   🏢 {cliente.nombre} ({cliente.rut})")

def main():
    print("🔧 HERRAMIENTAS DE MIGRACIÓN - BYPASS DE SERVICIOS")
    print("="*60)
    
    mostrar_estado_actual()
    
    print("\n" + "="*60)
    print("OPCIONES:")
    print("1. Migrar clientes existentes (servicios → áreas directas)")
    print("2. Crear clientes de ejemplo")
    print("3. Solo mostrar estado actual")
    print("="*60)
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    if opcion == "1":
        confirmacion = input("¿Confirmas la migración? (y/N): ").strip().lower()
        if confirmacion == 'y':
            with transaction.atomic():
                migrar_clientes_a_areas_directas()
        else:
            print("Migración cancelada")
    
    elif opcion == "2":
        crear_clientes_ejemplo()
    
    elif opcion == "3":
        print("Estado mostrado arriba")
    
    else:
        print("Opción no válida")
    
    print("\n" + "="*60)
    print("🔧 Proceso completado")

if __name__ == "__main__":
    main()
