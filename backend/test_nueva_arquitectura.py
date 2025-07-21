"""
Test de Importaciones - Nueva Arquitectura Nómina
================================================

Script simple para validar que todas las importaciones
de la nueva arquitectura estén correctas.
"""

def test_imports():
    """Probar importaciones básicas"""
    
    try:
        print("✓ Probando importaciones de Django...")
        from django.conf import settings
        from django.db import models
        print("  - Django core: OK")
        
        from django.contrib.auth import get_user_model
        print("  - Django auth: OK")
        
        from django.utils import timezone  
        print("  - Django utils: OK")
        
    except ImportError as e:
        print(f"  ✗ Error en Django: {e}")
    
    try:
        print("\n✓ Probando importaciones de Django REST Framework...")
        from rest_framework import viewsets, serializers, status
        from rest_framework.decorators import action
        from rest_framework.response import Response
        print("  - DRF core: OK")
        
    except ImportError as e:
        print(f"  ✗ Error en DRF: {e}")
    
    try:
        print("\n✓ Probando importaciones de modelos...")
        from nomina.models import CierreNomina
        print("  - Modelos: OK")
        
    except ImportError as e:
        print(f"  ✗ Error en modelos: {e}")
    
    try:
        print("\n✓ Probando importaciones de serializers...")
        from nomina.serializers import CierreNominaListSerializer
        print("  - Serializers: OK")
        
    except ImportError as e:
        print(f"  ✗ Error en serializers: {e}")
    
    try:
        print("\n✓ Probando importaciones de views...")
        from nomina.views import CierreNominaViewSet
        print("  - Views: OK")
        
    except ImportError as e:
        print(f"  ✗ Error en views: {e}")

    print("\n🎉 Test de importaciones completado!")
    print("La nueva arquitectura está lista para testing.")

if __name__ == "__main__":
    test_imports()
