#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos y los modelos
"""

import os
import sys
import django

# Setup Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def verificar_modelos():
    """Verificar que los modelos existen"""
    print("🔍 VERIFICANDO MODELOS")
    print("=" * 30)
    
    try:
        from backend.nomina.models import UploadLogNomina
        print("✅ UploadLogNomina importado correctamente")
        
        # Verificar campos
        campos = [field.name for field in UploadLogNomina._meta.fields]
        print(f"📋 Campos de UploadLogNomina: {campos}")
        
        # Contar registros
        count = UploadLogNomina.objects.count()
        print(f"📊 Registros en UploadLogNomina: {count}")
        
    except ImportError as e:
        print(f"❌ Error importando UploadLogNomina: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando UploadLogNomina: {e}")
        return False
    
    try:
        from backend.nomina.models import LibroRemuneracionesUpload
        print("✅ LibroRemuneracionesUpload importado correctamente")
        
        count = LibroRemuneracionesUpload.objects.count()
        print(f"📊 Registros en LibroRemuneracionesUpload: {count}")
        
    except ImportError as e:
        print(f"❌ Error importando LibroRemuneracionesUpload: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando LibroRemuneracionesUpload: {e}")
        return False
    
    try:
        from backend.nomina.models import CierreNomina
        print("✅ CierreNomina importado correctamente")
        
        count = CierreNomina.objects.count()
        print(f"📊 Registros en CierreNomina: {count}")
        
        if count > 0:
            primer_cierre = CierreNomina.objects.first()
            print(f"📋 Primer cierre: ID={primer_cierre.id}, Cliente={primer_cierre.cliente}")
        
    except ImportError as e:
        print(f"❌ Error importando CierreNomina: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando CierreNomina: {e}")
        return False
    
    return True

def verificar_tasks():
    """Verificar que las tasks están disponibles"""
    print("\n🔍 VERIFICANDO TASKS")
    print("=" * 30)
    
    try:
        from backend.nomina.tasks import (
            validar_nombre_archivo_libro_remuneraciones_task,
            verificar_archivo_libro_remuneraciones_task,
            validar_contenido_libro_remuneraciones_task,
            analizar_headers_libro_remuneraciones_con_validacion
        )
        print("✅ Tasks de validación importadas correctamente")
        
    except ImportError as e:
        print(f"❌ Error importando tasks: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando tasks: {e}")
        return False
    
    return True

def verificar_validaciones():
    """Verificar que las funciones de validación están disponibles"""
    print("\n🔍 VERIFICANDO VALIDACIONES")
    print("=" * 30)
    
    try:
        from backend.nomina.utils.validaciones import (
            validar_archivo_libro_remuneraciones_excel,
            validar_nombre_archivo_libro_remuneraciones
        )
        print("✅ Funciones de validación importadas correctamente")
        
        # Probar validación de nombre
        resultado = validar_nombre_archivo_libro_remuneraciones("12345678_LibroRemuneraciones.xlsx")
        print(f"📋 Validación de nombre: {resultado['es_valido']}")
        
    except ImportError as e:
        print(f"❌ Error importando validaciones: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando validaciones: {e}")
        return False
    
    return True

def verificar_mixins():
    """Verificar que los mixins están disponibles"""
    print("\n🔍 VERIFICANDO MIXINS")
    print("=" * 30)
    
    try:
        from backend.nomina.utils.mixins import UploadLogNominaMixin
        print("✅ UploadLogNominaMixin importado correctamente")
        
        # Crear instancia
        mixin = UploadLogNominaMixin()
        print("✅ Instancia de UploadLogNominaMixin creada")
        
    except ImportError as e:
        print(f"❌ Error importando UploadLogNominaMixin: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando UploadLogNominaMixin: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN DE COMPONENTES DEL SISTEMA")
    print("=" * 50)
    
    # Ejecutar verificaciones
    modelos_ok = verificar_modelos()
    tasks_ok = verificar_tasks()
    validaciones_ok = verificar_validaciones()
    mixins_ok = verificar_mixins()
    
    # Resumen
    print("\n📊 RESUMEN DE VERIFICACIONES")
    print("=" * 50)
    print(f"Modelos: {'✅' if modelos_ok else '❌'}")
    print(f"Tasks: {'✅' if tasks_ok else '❌'}")
    print(f"Validaciones: {'✅' if validaciones_ok else '❌'}")
    print(f"Mixins: {'✅' if mixins_ok else '❌'}")
    
    if all([modelos_ok, tasks_ok, validaciones_ok, mixins_ok]):
        print("\n🎉 TODOS LOS COMPONENTES ESTÁN FUNCIONANDO CORRECTAMENTE")
    else:
        print("\n💥 ALGUNOS COMPONENTES TIENEN PROBLEMAS")
        print("💡 Revisa los errores arriba para más detalles")

if __name__ == "__main__":
    main()
