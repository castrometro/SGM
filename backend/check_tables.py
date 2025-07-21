#!/usr/bin/env python
"""
Script para verificar las tablas de nómina en la base de datos
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from django.db import connection

def listar_tablas_nomina():
    """Listar todas las tablas que empiecen con nomina_"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'nomina_%'
            ORDER BY table_name;
        """)
        
        tablas = cursor.fetchall()
        
        print("=== TABLAS DE NÓMINA ===")
        if tablas:
            for tabla in tablas:
                print(f"  - {tabla[0]}")
        else:
            print("  No se encontraron tablas de nómina")
        
        print(f"\nTotal: {len(tablas)} tablas")

def verificar_modelo_ausentismo():
    """Verificar si existe la tabla de ausentismo específicamente"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT COUNT(*) FROM nomina_ausentismo;")
            count = cursor.fetchone()[0]
            print(f"\n=== TABLA AUSENTISMO ===")
            print(f"  Existe: SÍ")
            print(f"  Registros: {count}")
        except Exception as e:
            print(f"\n=== TABLA AUSENTISMO ===")
            print(f"  Existe: NO")
            print(f"  Error: {e}")

def listar_migraciones_aplicadas():
    """Listar migraciones aplicadas de nómina"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, applied 
            FROM django_migrations 
            WHERE app = 'nomina'
            ORDER BY applied;
        """)
        
        migraciones = cursor.fetchall()
        
        print("\n=== MIGRACIONES DE NÓMINA ===")
        if migraciones:
            for migracion in migraciones:
                print(f"  - {migracion[0]} (aplicada: {migracion[1]})")
        else:
            print("  No se encontraron migraciones de nómina")

if __name__ == "__main__":
    try:
        listar_tablas_nomina()
        verificar_modelo_ausentismo()
        listar_migraciones_aplicadas()
    except Exception as e:
        print(f"Error ejecutando script: {e}")
        import traceback
        traceback.print_exc()
