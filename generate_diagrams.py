#!/usr/bin/env python3
"""
Script para generar diagramas de modelos Django usando django-extensions
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - COMPLETADO")
            if result.stdout:
                print(f"📄 Salida: {result.stdout.strip()}")
        else:
            print(f"❌ Error en {description}:")
            print(f"📄 Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"❌ Excepción en {description}: {e}")


def main():
    """Función principal"""
    print("🚀 Generador de Diagramas Django con django-extensions")
    print("="*60)
    
    # Cambiar al directorio del proyecto Django
    os.chdir('/app')
    diagrams_dir = Path('/app/diagrams')
    diagrams_dir.mkdir(exist_ok=True)
    
    # Lista de comandos para generar diferentes diagramas
    commands = [
        # Diagrama completo de todos los modelos
        {
            'cmd': 'python manage.py graph_models -a -g -o diagrams/all_models.png',
            'desc': 'Generando diagrama completo de todos los modelos'
        },
        # Diagrama de la aplicación de contabilidad
        {
            'cmd': 'python manage.py graph_models contabilidad -o diagrams/contabilidad_models.png',
            'desc': 'Generando diagrama de modelos de Contabilidad'
        },
        # Diagrama de la aplicación de nomina
        {
            'cmd': 'python manage.py graph_models nomina -o diagrams/nomina_models.png',
            'desc': 'Generando diagrama de modelos de Nómina'
        },
        # Diagrama de la API
        {
            'cmd': 'python manage.py graph_models api -o diagrams/api_models.png',
            'desc': 'Generando diagrama de modelos de API'
        },
        # Diagrama sin etiquetas de relaciones (más limpio)
        {
            'cmd': 'python manage.py graph_models -a -g --hide-edge-labels -o diagrams/clean_models.png',
            'desc': 'Generando diagrama limpio (sin etiquetas de relaciones)'
        },
        # Diagrama en formato DOT para personalización
        {
            'cmd': 'python manage.py graph_models -a -g > diagrams/models.dot',
            'desc': 'Generando archivo DOT para personalización'
        },
        # Diagrama con colores
        {
            'cmd': 'python manage.py graph_models -a -g --color-code-deletions -o diagrams/colored_models.png',
            'desc': 'Generando diagrama con códigos de color'
        },
        # Diagrama en formato SVG (escalable)
        {
            'cmd': 'python manage.py graph_models -a -g -o diagrams/models.svg',
            'desc': 'Generando diagrama en formato SVG (escalable)'
        }
    ]
    
    # Verificar que django-extensions esté instalado
    print("\n🔍 Verificando instalación de django-extensions...")
    result = subprocess.run(['python', '-c', 'import django_extensions; print("django-extensions instalado correctamente")'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ django-extensions no está instalado")
        sys.exit(1)
    
    print("✅ django-extensions instalado correctamente")
    
    # Verificar que GraphViz esté disponible
    print("\n🔍 Verificando instalación de GraphViz...")
    result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ GraphViz no está instalado")
        sys.exit(1)
    
    print("✅ GraphViz instalado correctamente")
    print(f"📄 Versión: {result.stderr.strip()}")
    
    # Ejecutar comandos de generación de diagramas
    for command in commands:
        run_command(command['cmd'], command['desc'])
    
    # Mostrar archivos generados
    print(f"\n{'='*60}")
    print("📂 ARCHIVOS GENERADOS:")
    print(f"{'='*60}")
    
    if diagrams_dir.exists():
        for file in sorted(diagrams_dir.iterdir()):
            if file.is_file():
                size = file.stat().st_size
                print(f"📄 {file.name} ({size} bytes)")
    
    print(f"\n✨ ¡Diagramas generados exitosamente en /app/diagrams/!")
    print("💡 Puedes copiar los archivos desde el contenedor usando:")
    print("   docker cp <container_name>:/app/diagrams ./diagrams")


if __name__ == "__main__":
    main()
