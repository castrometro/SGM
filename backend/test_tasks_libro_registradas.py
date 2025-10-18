#!/usr/bin/env python
"""
Test: Verificar que las nuevas tareas de Libro están registradas en Celery
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from celery import current_app

print("=" * 80)
print("🔍 VERIFICANDO TAREAS DE LIBRO DE REMUNERACIONES")
print("=" * 80)

# Tareas esperadas (pueden tener cualquiera de estos prefijos)
expected_task_names = [
    'analizar_headers_libro',
    'clasificar_headers_libro',
    'procesar_empleados_libro',
    'procesar_registros_libro',
    'procesar_libro_completo',
    'eliminar_libro',
    'generar_informe_libro',
]

# Obtener todas las tareas registradas
all_tasks = current_app.tasks.keys()
libro_tasks = [t for t in all_tasks if any(name in t for name in expected_task_names)]

print(f"\n📋 Tareas de libro registradas: {len(libro_tasks)}")
print("-" * 80)

for task in sorted(libro_tasks):
    print(f"✅ {task}")

print("\n" + "=" * 80)
print(f"✅ Esperadas: {len(expected_task_names)}")
print(f"📊 Encontradas: {len(libro_tasks)}")

# Mostrar TODAS las tareas que contienen 'analizar' o 'clasificar' o 'libro'
print("\n🔍 BUSCANDO TAREAS RELACIONADAS...")
print("-" * 80)
related = [t for t in all_tasks if any(word in t.lower() for word in ['analizar', 'clasificar', 'libro', 'procesar', 'empleado', 'registro'])]
for task in sorted(related)[:30]:
    print(f"   {task}")

if len(libro_tasks) >= len(expected_task_names):
    print("\n✅ TODAS LAS TAREAS ESTÁN REGISTRADAS")
    sys.exit(0)
else:
    print("\n❌ FALTAN TAREAS")
    # Mostrar cuáles faltan
    found_names = set()
    for task in libro_tasks:
        for name in expected_task_names:
            if name in task:
                found_names.add(name)
    missing_names = set(expected_task_names) - found_names
    if missing_names:
        print(f"\n⚠️ Faltantes: {', '.join(missing_names)}")
    sys.exit(1)
