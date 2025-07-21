#!/usr/bin/env python
"""
Script para eliminar completamente todas las tablas legacy de nómina
y resetear las migraciones para empezar limpio con la nueva arquitectura.
"""

import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def main():
    print("🧹 Iniciando limpieza completa de nómina legacy...")
    
    # Obtener cursor de base de datos
    cursor = connection.cursor()
    
    try:
        # 1. Listar todas las tablas de nómina existentes
        print("\n📋 Tablas de nómina encontradas:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'nomina_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"   - {table[0]}")
        
        if not tables:
            print("   ✅ No hay tablas de nómina para eliminar")
            return
        
        # 2. Eliminar todas las tablas de nómina
        print(f"\n🗑️  Eliminando {len(tables)} tablas de nómina...")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"   ✅ Eliminada: {table_name}")
        
        # 3. Limpiar registros de migraciones
        print("\n🧹 Limpiando registros de migraciones...")
        cursor.execute("DELETE FROM django_migrations WHERE app = 'nomina'")
        affected = cursor.rowcount
        print(f"   ✅ Eliminadas {affected} migraciones de nómina")
        
        # 4. Eliminar archivos de migración físicos
        print("\n📁 Eliminando archivos de migración...")
        migrations_dir = "/app/nomina/migrations"
        migration_files = []
        
        if os.path.exists(migrations_dir):
            for filename in os.listdir(migrations_dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    filepath = os.path.join(migrations_dir, filename)
                    os.remove(filepath)
                    migration_files.append(filename)
                    print(f"   ✅ Eliminado: {filename}")
        
        if not migration_files:
            print("   ✅ No hay archivos de migración para eliminar")
        
        # 5. Confirmación final
        print(f"\n🎉 LIMPIEZA COMPLETADA EXITOSAMENTE!")
        print(f"   - Tablas eliminadas: {len(tables)}")
        print(f"   - Registros de migración eliminados: {affected}")
        print(f"   - Archivos de migración eliminados: {len(migration_files)}")
        print("\n✨ Listo para generar nuevas migraciones del modelo nuevo!")
        
        # Commit de los cambios
        connection.commit()
        
    except Exception as e:
        print(f"\n❌ ERROR durante la limpieza: {e}")
        connection.rollback()
        sys.exit(1)
    
    finally:
        cursor.close()

if __name__ == "__main__":
    main()
