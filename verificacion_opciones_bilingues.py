#!/usr/bin/env python3
"""
Script para verificar que la creación de opciones bilingües funcione correctamente
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
django.setup()

from contabilidad.models import Cliente, ClasificacionSet, ClasificacionOption
from contabilidad.serializers import ClasificacionOptionSerializer

def print_header(title):
    print("="*80)
    print(f" {title}")
    print("="*80)

def print_section(title):
    print("\n" + "-"*60)
    print(f" {title}")
    print("-"*60)

def test_backend_direct():
    """Test directo en el backend usando Django ORM"""
    print_header("🧪 TEST DIRECTO EN BACKEND (Django ORM)")
    
    try:
        # 1. Encontrar o crear un cliente de prueba
        cliente, created = Cliente.objects.get_or_create(
            nombre="Test Bilingüe",
            defaults={
                'bilingue': True,
                'activo': True
            }
        )
        
        if created:
            print(f"✅ Cliente de prueba creado: {cliente.nombre} (ID: {cliente.id})")
        else:
            print(f"✅ Cliente de prueba encontrado: {cliente.nombre} (ID: {cliente.id})")
            
        # Asegurar que el cliente es bilingüe
        if not cliente.bilingue:
            cliente.bilingue = True
            cliente.save()
            print("✅ Cliente configurado como bilingüe")
        
        # 2. Encontrar o crear un set de prueba
        set_test, created = ClasificacionSet.objects.get_or_create(
            cliente=cliente,
            nombre="Test Set Bilingüe",
            defaults={
                'descripcion': 'Set de prueba para verificar funcionalidad bilingüe'
            }
        )
        
        if created:
            print(f"✅ Set de prueba creado: {set_test.nombre} (ID: {set_test.id})")
        else:
            print(f"✅ Set de prueba encontrado: {set_test.nombre} (ID: {set_test.id})")
        
        # 3. Crear opción bilingüe usando ORM directo
        print_section("📝 Creando opción bilingüe con ORM directo")
        
        timestamp = datetime.now().strftime("%H%M%S")
        
        opcion_data = {
            'set_clas': set_test,
            'valor': f'Test ES {timestamp}',
            'valor_en': f'Test EN {timestamp}',
            'descripcion': f'Descripción en español {timestamp}',
            'descripcion_en': f'Description in English {timestamp}'
        }
        
        print("📤 Datos a crear:")
        for key, value in opcion_data.items():
            if key != 'set_clas':
                print(f"   {key}: '{value}'")
        
        opcion_orm = ClasificacionOption.objects.create(**opcion_data)
        
        print(f"✅ Opción creada con ORM directo - ID: {opcion_orm.id}")
        print("🔍 Valores guardados en DB:")
        print(f"   valor (ES): '{opcion_orm.valor}'")
        print(f"   valor_en (EN): '{opcion_orm.valor_en}'")
        print(f"   descripcion (ES): '{opcion_orm.descripcion}'")
        print(f"   descripcion_en (EN): '{opcion_orm.descripcion_en}'")
        
        # Verificar que ambos idiomas se guardaron
        if opcion_orm.valor and opcion_orm.valor_en:
            print("✅ ¡Ambos idiomas se guardaron correctamente!")
        else:
            print("❌ PROBLEMA: No se guardaron ambos idiomas")
            return False
            
        # 4. Probar el serializer
        print_section("📝 Probando serializer para creación")
        
        serializer_data = {
            'set_clas': set_test.id,
            'valor': f'Serializer ES {timestamp}',
            'valor_en': f'Serializer EN {timestamp}',
            'descripcion': f'Desc serializer ES {timestamp}',
            'descripcion_en': f'Desc serializer EN {timestamp}'
        }
        
        print("📤 Datos para serializer:")
        for key, value in serializer_data.items():
            print(f"   {key}: '{value}'")
        
        serializer = ClasificacionOptionSerializer(data=serializer_data)
        
        if serializer.is_valid():
            opcion_serializer = serializer.save()
            print(f"✅ Opción creada con serializer - ID: {opcion_serializer.id}")
            print("🔍 Valores guardados en DB:")
            print(f"   valor (ES): '{opcion_serializer.valor}'")
            print(f"   valor_en (EN): '{opcion_serializer.valor_en}'")
            print(f"   descripcion (ES): '{opcion_serializer.descripcion}'")
            print(f"   descripcion_en (EN): '{opcion_serializer.descripcion_en}'")
            
            if opcion_serializer.valor and opcion_serializer.valor_en:
                print("✅ ¡Serializer también funciona correctamente!")
            else:
                print("❌ PROBLEMA: El serializer no guardó ambos idiomas")
                return False
        else:
            print("❌ ERROR: Serializer no válido")
            print(f"   Errores: {serializer.errors}")
            return False
            
        # 5. Probar lectura bilingüe
        print_section("📖 Probando lectura de opciones bilingües")
        
        opciones = ClasificacionOption.objects.filter(set_clas=set_test)
        print(f"📋 Opciones encontradas en el set: {opciones.count()}")
        
        for opcion in opciones:
            serializer_read = ClasificacionOptionSerializer(opcion)
            data = serializer_read.data
            
            print(f"\n🔍 Opción ID {opcion.id}:")
            print(f"   valor: '{data.get('valor')}'")
            print(f"   valor_en: '{data.get('valor_en')}'")
            print(f"   valor_es: '{data.get('valor_es')}'")
            print(f"   tiene_es: {data.get('tiene_es')}")
            print(f"   tiene_en: {data.get('tiene_en')}")
            print(f"   es_bilingue: {data.get('es_bilingue')}")
        
        print("\n✅ Pruebas de backend completadas exitosamente")
        return True, cliente.id, set_test.id
        
    except Exception as e:
        print(f"❌ ERROR en test de backend: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_api_endpoint(cliente_id, set_id):
    """Test del endpoint de API"""
    print_header("🌐 TEST DE ENDPOINT API")
    
    try:
        # URL del endpoint
        url = "http://localhost:8000/api/contabilidad/clasificaciones-opcion/"
        
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Datos para crear opción bilingüe
        payload = {
            'set_clas': set_id,
            'valor': f'API ES {timestamp}',
            'valor_en': f'API EN {timestamp}',
            'descripcion': f'Desc API ES {timestamp}',
            'descripcion_en': f'Desc API EN {timestamp}'
        }
        
        print("📤 Enviando request al API:")
        print(f"   URL: {url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        # Hacer la request (necesitarías autenticación en un entorno real)
        # Por ahora solo mostrar qué se enviaría
        print("\n⚠️  NOTA: Para probar el API endpoint, necesitarías:")
        print("   1. El servidor Django ejecutándose")
        print("   2. Autenticación configurada")
        print("   3. Headers apropiados")
        
        print("\n📋 Ejemplo de cURL para probar manualmente:")
        print(f"""
curl -X POST {url} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer <tu-token>" \\
  -d '{json.dumps(payload)}'
        """)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test de API: {e}")
        return False

def main():
    print_header("🔍 VERIFICACIÓN DE OPCIONES BILINGÜES")
    print("Este script verifica que la creación de opciones bilingües funcione correctamente")
    print("en el backend de Django y a través del API.")
    
    # Test 1: Backend directo
    backend_success, cliente_id, set_id = test_backend_direct()
    
    if not backend_success:
        print("\n❌ Las pruebas de backend fallaron. No se puede continuar.")
        return
    
    # Test 2: API endpoint
    api_success = test_api_endpoint(cliente_id, set_id)
    
    # Resumen
    print_header("📊 RESUMEN DE PRUEBAS")
    print(f"✅ Backend Django ORM: {'EXITOSO' if backend_success else 'FALLIDO'}")
    print(f"ℹ️  API Endpoint: {'CONFIGURADO' if api_success else 'ERROR'}")
    
    if backend_success:
        print("\n🎉 ¡El backend está configurado correctamente para opciones bilingües!")
        print("\n📋 Próximos pasos:")
        print("   1. Verificar que el frontend envíe los datos correctamente")
        print("   2. Comprobar que el servidor Django esté ejecutándose")
        print("   3. Verificar autenticación y permisos en el API")
        print(f"\n🔗 Cliente de prueba ID: {cliente_id}")
        print(f"🔗 Set de prueba ID: {set_id}")
    else:
        print("\n❌ Hay problemas en el backend que necesitan resolverse")

if __name__ == "__main__":
    main()
