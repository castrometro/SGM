#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad bilingüe de opciones de clasificación.
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.models import Cliente, ClasificacionSet, ClasificacionOption
from django.contrib.auth import get_user_model

User = get_user_model()

def test_opcion_bilingue():
    print("🧪 Iniciando prueba de opciones bilingües...")
    
    # Buscar o crear un cliente bilingüe
    cliente = Cliente.objects.filter(bilingue=True).first()
    if not cliente:
        print("⚠️ No se encontró un cliente bilingüe, creando uno...")
        cliente = Cliente.objects.create(
            nombre="Cliente Prueba Bilingüe",
            bilingue=True
        )
    
    print(f"📋 Cliente seleccionado: {cliente.nombre} (bilingüe: {cliente.bilingue})")
    
    # Buscar o crear un set de clasificación
    set_test = ClasificacionSet.objects.filter(cliente=cliente, nombre="Test Bilingüe").first()
    if not set_test:
        set_test = ClasificacionSet.objects.create(
            cliente=cliente,
            nombre="Test Bilingüe"
        )
    
    print(f"🏷️ Set de prueba: {set_test.nombre}")
    
    # Crear opciones de prueba
    print("\n📝 Creando opciones de prueba...")
    
    # 1. Opción solo en español
    opcion_es = ClasificacionOption.objects.create(
        set_clas=set_test,
        valor="Activo",
        descripcion="Estado activo del elemento"
    )
    print(f"✅ Opción ES: {opcion_es.valor} | EN: {opcion_es.valor_en or 'None'}")
    
    # 2. Opción solo en inglés
    opcion_en = ClasificacionOption.objects.create(
        set_clas=set_test,
        valor_en="Inactive",
        descripcion_en="Inactive state of the element"
    )
    print(f"✅ Opción ES: {opcion_en.valor or 'None'} | EN: {opcion_en.valor_en}")
    
    # 3. Opción bilingüe
    opcion_bilingue = ClasificacionOption.objects.create(
        set_clas=set_test,
        valor="Pendiente",
        descripcion="Estado pendiente",
        valor_en="Pending",
        descripcion_en="Pending state"
    )
    print(f"✅ Opción ES: {opcion_bilingue.valor} | EN: {opcion_bilingue.valor_en}")
    
    # Verificar métodos del modelo
    print("\n🔍 Verificando métodos del modelo...")
    print(f"Opción bilingüe - get_valor('es'): {opcion_bilingue.get_valor('es')}")
    print(f"Opción bilingüe - get_valor('en'): {opcion_bilingue.get_valor('en')}")
    print(f"Opción bilingüe - tiene_traduccion_completa(): {opcion_bilingue.tiene_traduccion_completa()}")
    
    # Probar el serializer
    print("\n📊 Probando serializer...")
    from contabilidad.serializers import ClasificacionOptionSerializer
    
    serializer = ClasificacionOptionSerializer(opcion_bilingue)
    data = serializer.data
    print(f"Serializer - valor_es: {data['valor_es']}")
    print(f"Serializer - valor_en: {data['valor_en']}")
    print(f"Serializer - tiene_es: {data['tiene_es']}")
    print(f"Serializer - tiene_en: {data['tiene_en']}")
    print(f"Serializer - es_bilingue: {data['es_bilingue']}")
    
    print("\n✅ Prueba completada exitosamente!")
    print(f"📈 Creadas {ClasificacionOption.objects.filter(set_clas=set_test).count()} opciones en el set '{set_test.nombre}'")

if __name__ == "__main__":
    test_opcion_bilingue()
