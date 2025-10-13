#!/usr/bin/env python3
"""
Script para limpiar todos los imports del sistema V1 de activity logging
y redirigirlos a los stubs correspondientes.
"""
import os
import re
import subprocess

def backup_file(filepath):
    """Crear backup del archivo antes de modificarlo"""
    backup_path = f"{filepath}.backup"
    if not os.path.exists(backup_path):
        subprocess.run(['cp', filepath, backup_path])
        print(f"✅ Backup creado: {backup_path}")

def replace_imports_in_file(filepath, replacements):
    """Reemplazar imports específicos en un archivo"""
    if not os.path.exists(filepath):
        print(f"❌ Archivo no encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        for old_import, new_import in replacements.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                modified = True
                print(f"  ✅ Reemplazado: {old_import} → {new_import}")
        
        if modified:
            backup_file(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Archivo actualizado: {filepath}")
            return True
        else:
            print(f"ℹ️  Sin cambios necesarios: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error procesando {filepath}: {e}")
        return False

def main():
    # Definir los reemplazos necesarios
    IMPORT_REPLACEMENTS = {
        # Models
        'from .models_logging import': 'from .models_logging_stub import',
        'from nomina.models_logging import': 'from nomina.models_logging_stub import',
        'from .utils.activity_logger import registrar_actividad_tarjeta_nomina': 'from .models_logging_stub import registrar_actividad_tarjeta_nomina',
        
        # Views
        'from .views_logging import': 'from .views_logging_stub import',
        'from nomina.views_logging import': 'from nomina.views_logging_stub import',
        
        # API
        'from .api_logging import': 'from .api_logging_stub import',
        'from nomina.api_logging import': 'from nomina.api_logging_stub import',
        
        # Mixins
        'from .utils.mixins import': 'from .utils.mixins_stub import',
        'from nomina.utils.mixins import': 'from nomina.utils.mixins_stub import',
        
        # Funciones específicas
        'registrar_actividad_tarjeta_nomina': 'registrar_actividad_tarjeta_nomina',  # Ya está en stub
    }
    
    # Archivos a procesar en nomina
    NOMINA_FILES = [
        '/root/SGM/backend/nomina/views.py',
        '/root/SGM/backend/nomina/tasks.py',
        '/root/SGM/backend/nomina/urls.py',
        '/root/SGM/backend/nomina/views_archivos_analista.py',
        '/root/SGM/backend/nomina/views_archivos_gerente.py',
        '/root/SGM/backend/nomina/tests.py',
    ]
    
    # Archivos a procesar en contabilidad (que referencian nomina)
    CONTABILIDAD_FILES = [
        '/root/SGM/backend/contabilidad/tasks_de_tipo_doc.py',
        '/root/SGM/backend/contabilidad/tests.py',
        '/root/SGM/backend/contabilidad/urls.py',
    ]
    
    print("🧹 Iniciando limpieza del sistema V1 de activity logging...")
    print("="*60)
    
    # Procesar archivos de nomina
    print("\n📁 Procesando archivos de NOMINA:")
    for filepath in NOMINA_FILES:
        print(f"\n🔍 Procesando: {filepath}")
        replace_imports_in_file(filepath, IMPORT_REPLACEMENTS)
    
    # Procesar archivos de contabilidad
    print("\n📁 Procesando archivos de CONTABILIDAD:")
    contabilidad_replacements = {
        'from contabilidad.utils.activity_logger import registrar_actividad_tarjeta': 'from nomina.models_logging_stub import registrar_actividad_tarjeta_nomina as registrar_actividad_tarjeta',
    }
    
    for filepath in CONTABILIDAD_FILES:
        print(f"\n🔍 Procesando: {filepath}")
        replace_imports_in_file(filepath, contabilidad_replacements)
    
    print("\n" + "="*60)
    print("✅ Limpieza completada!")
    print("\n📝 Archivos de backup creados con extensión .backup")
    print("🔧 Siguiente paso: Verificar que no haya errores de import")

if __name__ == "__main__":
    main()