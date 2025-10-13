# backend/nomina/management/commands/cleanup_activity_logs.py
"""
Management command para limpieza automática de logs de actividad

Uso:
    python manage.py cleanup_activity_logs --days 30
    python manage.py cleanup_activity_logs --days 7 --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import logging

from nomina.models_activity_v2 import ActivityEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia logs de actividad antiguos para mantener la base de datos optimizada'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días de logs a mantener (por defecto: 30)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin eliminar realmente'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Tamaño del lote para eliminación (por defecto: 1000)'
        )
    
    def handle(self, *args, **options):
        days_to_keep = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if days_to_keep < 1:
            raise CommandError('Los días deben ser un número positivo')
        
        # Calcular fecha límite
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Contar registros a eliminar
        queryset = ActivityEvent.objects.filter(timestamp__lt=cutoff_date)
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ No hay logs de actividad anteriores a {cutoff_date.strftime("%Y-%m-%d %H:%M")}'
                )
            )
            return
        
        # Mostrar estadísticas antes de eliminar
        self.stdout.write(f'📊 Estadísticas de logs a eliminar:')
        self.stdout.write(f'   - Fecha límite: {cutoff_date.strftime("%Y-%m-%d %H:%M")}')
        self.stdout.write(f'   - Total registros: {total_count:,}')
        
        # Estadísticas por módulo
        stats_by_module = queryset.values('modulo').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        for stat in stats_by_module:
            self.stdout.write(f'   - {stat["modulo"]}: {stat["count"]:,} registros')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'🔍 DRY RUN: Se eliminarían {total_count:,} registros '
                    f'(ejecutar sin --dry-run para eliminar realmente)'
                )
            )
            return
        
        # Confirmar eliminación
        confirm = input(
            f'\n❓ ¿Confirmar eliminación de {total_count:,} registros? [y/N]: '
        )
        
        if confirm.lower() != 'y':
            self.stdout.write(
                self.style.WARNING('❌ Operación cancelada por el usuario')
            )
            return
        
        # Eliminar en lotes para evitar problemas de memoria
        self.stdout.write(f'🗑️  Eliminando en lotes de {batch_size:,} registros...')
        
        deleted_total = 0
        batch_num = 1
        
        while True:
            # Obtener IDs del lote actual
            batch_ids = list(
                queryset.values_list('id', flat=True)[:batch_size]
            )
            
            if not batch_ids:
                break
            
            # Eliminar el lote
            deleted_count, _ = ActivityEvent.objects.filter(
                id__in=batch_ids
            ).delete()
            
            deleted_total += deleted_count
            
            self.stdout.write(
                f'   Lote {batch_num}: {deleted_count:,} registros eliminados '
                f'(total: {deleted_total:,}/{total_count:,})'
            )
            
            batch_num += 1
            
            # Evitar loop infinito
            if deleted_count == 0:
                break
        
        # Resultado final
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Limpieza completada: {deleted_total:,} registros eliminados'
            )
        )
        
        # Mostrar estadísticas post-limpieza
        remaining_count = ActivityEvent.objects.count()
        self.stdout.write(f'📈 Registros restantes: {remaining_count:,}')
        
        if remaining_count > 0:
            oldest_remaining = ActivityEvent.objects.order_by('timestamp').first()
            self.stdout.write(
                f'📅 Log más antiguo restante: {oldest_remaining.timestamp.strftime("%Y-%m-%d %H:%M")}'
            )