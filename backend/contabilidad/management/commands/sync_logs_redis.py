# backend/contabilidad/management/commands/sync_logs_redis.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from contabilidad.models import TarjetaActivityLog
from contabilidad.utils.activity_logger import ActivityLogStorage
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza logs recientes con Redis para mejorar rendimiento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días de logs a sincronizar (default: 7)'
        )
        parser.add_argument(
            '--client-id',
            type=int,
            help='Sincronizar solo logs de un cliente específico'
        )
        parser.add_argument(
            '--clean-first',
            action='store_true',
            help='Limpiar Redis antes de sincronizar'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verificar datos después de sincronizar'
        )

    def handle(self, *args, **options):
        days = options['days']
        client_id = options.get('client_id')
        clean_first = options['clean_first']
        verify = options['verify']
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando sincronización de logs...'))
        
        # Limpiar Redis si se solicita
        if clean_first:
            self.stdout.write('Limpiando Redis...')
            if client_id:
                ActivityLogStorage.clear_client_logs(client_id)
                self.stdout.write(f'Redis limpiado para cliente {client_id}')
            else:
                self.stdout.write('Limpieza completa no implementada por seguridad')
        
        # Obtener logs recientes
        fecha_limite = timezone.now() - timedelta(days=days)
        logs_query = TarjetaActivityLog.objects.filter(
            timestamp__gte=fecha_limite
        ).select_related('cierre', 'cierre__cliente', 'usuario').order_by('-timestamp')
        
        if client_id:
            logs_query = logs_query.filter(cierre__cliente_id=client_id)
            self.stdout.write(f'Filtrando logs para cliente {client_id}')
        
        total_logs = logs_query.count()
        self.stdout.write(f'Encontrados {total_logs} logs para sincronizar')
        
        # Sincronizar por lotes
        batch_size = 100
        synced_count = 0
        error_count = 0
        
        for i in range(0, total_logs, batch_size):
            batch = logs_query[i:i + batch_size]
            
            for log in batch:
                try:
                    ActivityLogStorage.save_to_redis(log)
                    synced_count += 1
                    
                    if synced_count % 50 == 0:
                        self.stdout.write(f"Sincronizados {synced_count}/{total_logs} logs...")
                        
                except Exception as e:
                    error_count += 1
                    self.stderr.write(f"Error sincronizando log {log.id}: {e}")
                    
                    if error_count > 10:  # Limitar errores mostrados
                        self.stderr.write("Demasiados errores, revisa la configuración de Redis")
                        break
        
        # Mostrar resultados
        self.stdout.write(
            self.style.SUCCESS(f'Sincronización completada:')
        )
        self.stdout.write(f'  - Logs sincronizados: {synced_count}')
        self.stdout.write(f'  - Errores: {error_count}')
        
        # Verificar datos si se solicita
        if verify:
            self.stdout.write('\nVerificando datos en Redis...')
            
            stats = ActivityLogStorage.get_redis_stats()
            self.stdout.write(f'Redis disponible: {stats.get("redis_available", False)}')
            
            if stats.get("redis_available"):
                self.stdout.write(f'Logs globales en Redis: {stats.get("global_logs_count", 0)}')
                self.stdout.write(f'Memoria usada: {stats.get("memory_used", "N/A")}')
                self.stdout.write(f'Total keys: {stats.get("total_keys", 0)}')
                
                # Probar consulta
                if client_id:
                    redis_logs = ActivityLogStorage.get_recent_logs(cliente_id=client_id, limit=10)
                    self.stdout.write(f'Logs recientes para cliente {client_id}: {len(redis_logs)}')
                else:
                    redis_logs = ActivityLogStorage.get_recent_logs(limit=10)
                    self.stdout.write(f'Logs recientes globales: {len(redis_logs)}')
            else:
                self.stderr.write('Redis no disponible para verificación')
        
        self.stdout.write(self.style.SUCCESS('Comando completado'))
