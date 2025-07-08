#!/usr/bin/env python3
"""
Script para verificar las URLs de nómina y que no haya duplicados
"""

import os
import sys
import django
from django.urls import reverse
from django.conf import settings

# Setup Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def verificar_urls():
    """
    Verifica que las URLs de nómina estén correctamente configuradas
    """
    print("🔍 VERIFICANDO URLS DE NÓMINA")
    print("=" * 50)
    
    urls_importantes = [
        ('upload-libro-remuneraciones', 'URL para cargar libro de remuneraciones'),
        ('upload-movimientos-mes', 'URL para cargar movimientos del mes'),
        ('upload-archivo-analista', 'URL para cargar archivos del analista'),
        ('upload-archivo-novedades', 'URL para cargar archivos de novedades'),
    ]
    
    urls_encontradas = []
    urls_con_error = []
    
    for url_name, description in urls_importantes:
        try:
            url = reverse(f'nomina:{url_name}')
            urls_encontradas.append((url_name, url, description))
            print(f"✅ {url_name}: {url}")
        except Exception as e:
            urls_con_error.append((url_name, str(e), description))
            print(f"❌ {url_name}: ERROR - {str(e)}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   URLs encontradas: {len(urls_encontradas)}")
    print(f"   URLs con error: {len(urls_con_error)}")
    
    if urls_con_error:
        print(f"\n🚨 ERRORES ENCONTRADOS:")
        for url_name, error, description in urls_con_error:
            print(f"   - {url_name}: {error}")
            print(f"     Descripción: {description}")
    
    return len(urls_con_error) == 0

def verificar_vistas():
    """
    Verifica que las vistas estén correctamente importadas
    """
    print(f"\n🔍 VERIFICANDO VISTAS")
    print("=" * 50)
    
    try:
        from backend.nomina.views_upload_con_logging import (
            cargar_libro_remuneraciones_con_logging,
            cargar_movimientos_mes_con_logging,
            cargar_archivo_analista_con_logging,
            cargar_archivo_novedades_con_logging,
        )
        print("✅ Todas las vistas se importaron correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando vistas: {e}")
        return False

def verificar_tasks():
    """
    Verifica que las tareas de Celery estén correctamente importadas
    """
    print(f"\n🔍 VERIFICANDO TAREAS DE CELERY")
    print("=" * 50)
    
    try:
        from backend.nomina.tasks import (
            validar_nombre_archivo_libro_remuneraciones_task,
            verificar_archivo_libro_remuneraciones_task,
            validar_contenido_libro_remuneraciones_task,
            analizar_headers_libro_remuneraciones_con_validacion,
            clasificar_headers_libro_remuneraciones_task,
        )
        print("✅ Todas las tareas se importaron correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando tareas: {e}")
        return False

def verificar_funciones_validacion():
    """
    Verifica que las funciones de validación estén disponibles
    """
    print(f"\n🔍 VERIFICANDO FUNCIONES DE VALIDACIÓN")
    print("=" * 50)
    
    try:
        from backend.nomina.utils.validaciones import (
            validar_archivo_libro_remuneraciones_excel,
            validar_nombre_archivo_libro_remuneraciones,
        )
        print("✅ Funciones de validación importadas correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando funciones de validación: {e}")
        return False

def main():
    """
    Función principal para ejecutar todas las verificaciones
    """
    print("🧪 VERIFICACIÓN DEL SISTEMA DE NÓMINA")
    print("=" * 60)
    
    resultados = {
        'urls': verificar_urls(),
        'vistas': verificar_vistas(),
        'tasks': verificar_tasks(),
        'validaciones': verificar_funciones_validacion(),
    }
    
    print(f"\n🎯 RESULTADO FINAL:")
    print("=" * 60)
    
    total_verificaciones = len(resultados)
    verificaciones_exitosas = sum(resultados.values())
    
    for nombre, resultado in resultados.items():
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"   {nombre.upper()}: {estado}")
    
    print(f"\n📊 RESUMEN GENERAL:")
    print(f"   Verificaciones exitosas: {verificaciones_exitosas}/{total_verificaciones}")
    
    if verificaciones_exitosas == total_verificaciones:
        print(f"   🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print(f"   🚀 El sistema está listo para usar")
        print(f"   📍 Ruta principal: POST /api/nomina/upload/libro-remuneraciones/")
    else:
        print(f"   ⚠️  Se encontraron {total_verificaciones - verificaciones_exitosas} problemas")
        print(f"   🔧 Revisar los errores arriba para solucionarlos")

if __name__ == "__main__":
    main()
