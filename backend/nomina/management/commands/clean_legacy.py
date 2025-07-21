"""
Comando de gestión Django para limpiar completamente el modelo legacy de nómina.
"""

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Elimina completamente todas las tablas legacy de nómina y resetea migraciones'

    def handle(self, *args, **options):
        self.stdout.write("🧹 Iniciando limpieza completa de nómina legacy...")
        
        cursor = connection.cursor()
        
        try:
            # 1. Listar todas las tablas de nómina existentes
            self.stdout.write("\n📋 Tablas de nómina encontradas:")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'nomina_%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            for table in tables:
                self.stdout.write(f"   - {table[0]}")
            
            if not tables:
                self.stdout.write(self.style.SUCCESS("   ✅ No hay tablas de nómina para eliminar"))
                return
            
            # 2. Eliminar todas las tablas de nómina
            self.stdout.write(f"\n🗑️  Eliminando {len(tables)} tablas de nómina...")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                self.stdout.write(f"   ✅ Eliminada: {table_name}")
            
            # 3. Limpiar registros de migraciones
            self.stdout.write("\n🧹 Limpiando registros de migraciones...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'nomina'")
            affected = cursor.rowcount
            self.stdout.write(f"   ✅ Eliminadas {affected} migraciones de nómina")
            
            # 4. Confirmación final
            self.stdout.write(self.style.SUCCESS(f"\n🎉 LIMPIEZA COMPLETADA EXITOSAMENTE!"))
            self.stdout.write(f"   - Tablas eliminadas: {len(tables)}")
            self.stdout.write(f"   - Registros de migración eliminados: {affected}")
            self.stdout.write(self.style.SUCCESS("\n✨ Listo para generar nuevas migraciones del modelo nuevo!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ ERROR durante la limpieza: {e}"))
            raise
        
        finally:
            cursor.close()
