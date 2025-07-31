#!/usr/bin/env python3
"""
🔧 SCRIPT: Crear Migración para Sistema Dual

Crear la migración de Django para los nuevos campos del sistema dual
sin tener que entrar al contenedor Docker.
"""

import subprocess
import sys

def crear_migracion():
    """
    Crear migración Django para el sistema dual
    """
    print("🔧 CREANDO MIGRACIÓN PARA SISTEMA DUAL")
    print("=" * 50)
    
    try:
        # Comando para crear migración dentro del contenedor Django
        comando = [
            "docker", "exec", "django-1", 
            "python", "manage.py", 
            "makemigrations", "nomina",
            "--name", "sistema_dual_incidencias"
        ]
        
        print("📋 Ejecutando: " + " ".join(comando))
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Migración creada exitosamente")
            print("📄 Output:")
            print(resultado.stdout)
            
            # Aplicar la migración
            print("\n🚀 APLICANDO MIGRACIÓN...")
            comando_migrate = [
                "docker", "exec", "django-1",
                "python", "manage.py",
                "migrate", "nomina"
            ]
            
            print("📋 Ejecutando: " + " ".join(comando_migrate))
            resultado_migrate = subprocess.run(comando_migrate, capture_output=True, text=True)
            
            if resultado_migrate.returncode == 0:
                print("✅ Migración aplicada exitosamente")
                print("📄 Output:")
                print(resultado_migrate.stdout)
                return True
            else:
                print("❌ Error aplicando migración:")
                print(resultado_migrate.stderr)
                return False
        else:
            print("❌ Error creando migración:")
            print(resultado.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def verificar_estado_migraciones():
    """
    Verificar estado actual de migraciones
    """
    print("\n📋 VERIFICANDO ESTADO DE MIGRACIONES")
    print("-" * 40)
    
    try:
        comando = [
            "docker", "exec", "django-1",
            "python", "manage.py", 
            "showmigrations", "nomina"
        ]
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("📄 Estado actual de migraciones nomina:")
            print(resultado.stdout)
        else:
            print("❌ Error verificando migraciones:")
            print(resultado.stderr)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔧 HERRAMIENTA DE MIGRACIÓN - SISTEMA DUAL")
    print("=" * 50)
    
    # Verificar estado actual
    verificar_estado_migraciones()
    
    # Crear y aplicar migración
    if crear_migracion():
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("💡 El sistema dual ya puede usar los nuevos campos")
        
        # Verificar estado final
        verificar_estado_migraciones()
        
        sys.exit(0)
    else:
        print("\n💥 ERROR EN MIGRACIÓN")
        print("💡 Revisa los errores arriba y corrige antes de continuar")
        sys.exit(1)
