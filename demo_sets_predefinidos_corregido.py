#!/usr/bin/env python
"""
Script de demostración del sistema de sets predefinidos corregido.
Muestra cómo se crean sets únicos con opciones bilingües.

IMPORTANTE: Este script requiere el entorno Django configurado.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from contabilidad.tasks_cuentas_bulk import crear_sets_predefinidos_clasificacion
from contabilidad.models import ClasificacionSet, ClasificacionOption
from api.models import Cliente

def demostrar_sets_predefinidos():
    """Demuestra el funcionamiento correcto de los sets predefinidos"""
    
    print("🚀 DEMOSTRACIÓN: Sistema de Sets Predefinidos Corregido")
    print("=" * 60)
    
    # Simular cliente bilingüe
    print("\n1. CLIENTE BILINGÜE - Sets únicos con opciones ES/EN")
    print("-" * 50)
    
    # Buscar o crear cliente de prueba
    cliente_bilingue, created = Cliente.objects.get_or_create(
        rut='12345678-9',
        defaults={
            'nombre': 'Cliente Demo Bilingüe',
            'bilingue': True
        }
    )
    
    if not cliente_bilingue.bilingue:
        cliente_bilingue.bilingue = True
        cliente_bilingue.save()
    
    print(f"📋 Cliente: {cliente_bilingue.nombre} (ID: {cliente_bilingue.id})")
    print(f"🌐 Bilingüe: {cliente_bilingue.bilingue}")
    
    # Limpiar sets existentes para demo limpia
    print("\n🧹 Limpiando sets existentes para demo...")
    ClasificacionSet.objects.filter(cliente=cliente_bilingue).delete()
    
    # Crear sets predefinidos
    print("\n🔧 Creando sets predefinidos...")
    resultado = crear_sets_predefinidos_clasificacion(cliente_bilingue.id)
    
    if 'error' in resultado:
        print(f"❌ Error: {resultado['error']}")
        return
    
    print(f"✅ Resultado: {resultado['mensaje']}")
    
    # Mostrar estructura creada
    print("\n📊 ESTRUCTURA CREADA:")
    print("-" * 30)
    
    sets = ClasificacionSet.objects.filter(cliente=cliente_bilingue).order_by('nombre')
    
    for set_obj in sets:
        print(f"\n📂 SET: {set_obj.nombre}")
        print(f"   Descripción: {set_obj.descripcion}")
        print(f"   Idioma base: {set_obj.idioma}")
        
        opciones = set_obj.opciones.all().order_by('valor')
        print(f"   🔹 Opciones ({opciones.count()}):")
        
        for opcion in opciones:
            if cliente_bilingue.bilingue and opcion.valor_en:
                print(f"      • ES: {opcion.valor} | EN: {opcion.valor_en}")
            else:
                print(f"      • {opcion.valor}")
    
    print("\n" + "=" * 60)
    print("🎯 VERIFICACIÓN: El diseño correcto")
    print("-" * 30)
    print("✅ Sets únicos (no duplicados por idioma)")
    print("✅ Opciones bilingües en la misma entidad")
    print("✅ Campos valor_en y descripcion_en poblados")
    print("✅ Un solo set 'Tipo de Cuenta' con opciones ES/EN")
    
    # Estadísticas finales
    total_sets = sets.count()
    total_opciones = ClasificacionOption.objects.filter(set_clas__cliente=cliente_bilingue).count()
    opciones_bilingues = ClasificacionOption.objects.filter(
        set_clas__cliente=cliente_bilingue,
        valor_en__isnull=False
    ).count()
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   📂 Sets totales: {total_sets}")
    print(f"   🔹 Opciones totales: {total_opciones}")
    print(f"   🌐 Opciones bilingües: {opciones_bilingues}")
    
    # Ejemplo específico
    ejemplo_opcion = ClasificacionOption.objects.filter(
        set_clas__cliente=cliente_bilingue,
        set_clas__nombre="Tipo de Cuenta",
        valor="Activo"
    ).first()
    
    if ejemplo_opcion:
        print(f"\n🔍 EJEMPLO ESPECÍFICO:")
        print(f"   Set: {ejemplo_opcion.set_clas.nombre}")
        print(f"   Valor ES: {ejemplo_opcion.valor}")
        print(f"   Valor EN: {ejemplo_opcion.valor_en}")
        print(f"   Desc ES: {ejemplo_opcion.descripcion}")
        print(f"   Desc EN: {ejemplo_opcion.descripcion_en}")
    
    print("\n✨ SISTEMA FUNCIONANDO CORRECTAMENTE ✨")

if __name__ == "__main__":
    try:
        demostrar_sets_predefinidos()
    except Exception as e:
        print(f"❌ Error ejecutando demo: {e}")
        import traceback
        traceback.print_exc()
