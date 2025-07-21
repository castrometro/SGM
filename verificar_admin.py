#!/usr/bin/env python
"""
Script para verificar que todos los modelos estén registrados en admin
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.apps import apps
from django.contrib import admin

def main():
    print("=== VERIFICACIÓN DE ADMIN ===")
    
    # Obtener todos los modelos de la app nomina
    nomina_models = apps.get_app_config('nomina').get_models()
    
    print(f"\n📋 MODELOS EN NOMINA ({len(nomina_models)}):")
    for model in nomina_models:
        print(f"- {model.__name__}")
    
    # Obtener modelos registrados en admin
    registered_models = admin.site._registry
    nomina_registered = []
    
    for model, admin_class in registered_models.items():
        if model._meta.app_label == 'nomina':
            nomina_registered.append((model.__name__, admin_class.__class__.__name__))
    
    print(f"\n✅ MODELOS REGISTRADOS EN ADMIN ({len(nomina_registered)}):")
    for model_name, admin_name in sorted(nomina_registered):
        print(f"- {model_name}: {admin_name}")
    
    # Encontrar modelos no registrados
    registered_names = {name for name, _ in nomina_registered}
    all_model_names = {model.__name__ for model in nomina_models}
    
    not_registered = all_model_names - registered_names
    
    if not_registered:
        print(f"\n❌ MODELOS NO REGISTRADOS ({len(not_registered)}):")
        for model_name in sorted(not_registered):
            print(f"- {model_name}")
    else:
        print(f"\n🎉 TODOS LOS MODELOS ESTÁN REGISTRADOS EN ADMIN")
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total modelos: {len(nomina_models)}")
    print(f"   Registrados:   {len(nomina_registered)}")
    print(f"   Sin registrar: {len(not_registered)}")

if __name__ == "__main__":
    main()
