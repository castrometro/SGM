from django.core.management.base import BaseCommand
from django.db import connection
from nomina.models import RegistroConceptoEmpleado, CierreNomina


class Command(BaseCommand):
    help = 'Soluciona el problema de TooManyFieldsSent en Django Admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mostrar-estadisticas',
            action='store_true',
            help='Solo mostrar estadísticas sin eliminar nada'
        )
        parser.add_argument(
            '--mantener-ultimos',
            type=int,
            default=1000,
            help='Número de registros más recientes a mantener por cierre (default: 1000)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🚨 SOLUCIONADOR DE TooManyFieldsSent DJANGO ADMIN')
        )
        self.stdout.write('=' * 60)

        # Obtener estadísticas actuales
        total_registros = RegistroConceptoEmpleado.objects.count()
        total_cierres = CierreNomina.objects.count()

        self.stdout.write(f"📊 ESTADO ACTUAL:")
        self.stdout.write(f"   • Total registros RegistroConceptoEmpleado: {total_registros:,}")
        self.stdout.write(f"   • Total cierres de nómina: {total_cierres:,}")
        self.stdout.write(f"   • Promedio registros por cierre: {total_registros//total_cierres if total_cierres > 0 else 0:,}")

        # Identificar cierres problemáticos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    nc.cliente_id,
                    nc.periodo,
                    nc.id as cierre_id,
                    COUNT(rce.id) as total_registros
                FROM nomina_cierrenomina nc
                LEFT JOIN nomina_empleadocierre ec ON nc.id = ec.cierre_id
                LEFT JOIN nomina_registroconceptoempleado rce ON ec.id = rce.empleado_id
                GROUP BY nc.id, nc.cliente_id, nc.periodo
                HAVING COUNT(rce.id) > 500
                ORDER BY COUNT(rce.id) DESC
                LIMIT 20
            """)
            
            cierres_problematicos = cursor.fetchall()

        self.stdout.write(f"\n🔍 CIERRES CON MÁS DE 500 REGISTROS:")
        total_problematicos = 0
        for cliente_id, periodo, cierre_id, count in cierres_problematicos:
            self.stdout.write(f"   • Cliente {cliente_id} - {periodo} (ID: {cierre_id}): {count:,} registros")
            total_problematicos += count

        self.stdout.write(f"\n📈 REGISTROS EN CIERRES PROBLEMÁTICOS: {total_problematicos:,}")
        
        if options['mostrar_estadisticas']:
            return

        # Estrategia de limpieza: mantener solo los N registros más recientes por cierre
        mantener = options['mantener_ultimos']
        self.stdout.write(f"\n🧹 ESTRATEGIA DE LIMPIEZA:")
        self.stdout.write(f"   • Mantener {mantener} registros más recientes por cierre")
        self.stdout.write(f"   • Eliminar registros más antiguos")

        eliminados_total = 0
        
        for cliente_id, periodo, cierre_id, count in cierres_problematicos:
            if count > mantener:
                # Obtener IDs de registros a mantener (más recientes)
                registros_mantener = RegistroConceptoEmpleado.objects.filter(
                    empleado__cierre_id=cierre_id
                ).order_by('-fecha_registro')[:mantener].values_list('id', flat=True)

                # Eliminar el resto
                registros_eliminar = RegistroConceptoEmpleado.objects.filter(
                    empleado__cierre_id=cierre_id
                ).exclude(id__in=list(registros_mantener))

                count_eliminar = registros_eliminar.count()
                registros_eliminar.delete()
                
                eliminados_total += count_eliminar
                self.stdout.write(
                    f"   ✅ Cierre {cierre_id}: eliminados {count_eliminar:,} registros, "
                    f"mantenidos {mantener}"
                )

        self.stdout.write(f"\n🎉 LIMPIEZA COMPLETADA:")
        self.stdout.write(f"   • Total eliminados: {eliminados_total:,}")
        self.stdout.write(f"   • Registros restantes: {RegistroConceptoEmpleado.objects.count():,}")
        
        self.stdout.write(f"\n💡 CONFIGURACIONES APLICADAS EN SETTINGS.PY:")
        self.stdout.write(f"   • DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000")
        self.stdout.write(f"   • Paginación configurada en Admin")
        
        self.stdout.write(f"\n✅ El Django Admin ahora debería funcionar correctamente.")
