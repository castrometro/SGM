from django.core.management.base import BaseCommand
from django.db import transaction
from nomina.models import RegistroConceptoEmpleado, CierreNomina
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Limpia registros de conceptos de empleados masivamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cierre-id',
            type=int,
            help='ID específico del cierre de nómina a limpiar'
        )
        parser.add_argument(
            '--periodo',
            type=str,
            help='Período específico (ej: 2025-08) a limpiar'
        )
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID del cliente para limpiar todos sus registros'
        )
        parser.add_argument(
            '--dias-antiguedad',
            type=int,
            help='Eliminar registros más antiguos que X días'
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar eliminación (sin este flag solo muestra estadísticas)'
        )
        parser.add_argument(
            '--todo',
            action='store_true',
            help='⚠️ PELIGROSO: Eliminar TODOS los registros de conceptos'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🧹 HERRAMIENTA DE LIMPIEZA DE REGISTROS DE CONCEPTOS')
        )
        self.stdout.write(
            self.style.WARNING('=' * 60)
        )

        # Construir queryset base
        queryset = RegistroConceptoEmpleado.objects.all()
        filtros_aplicados = []

        # Aplicar filtros
        if options['cierre_id']:
            queryset = queryset.filter(empleado__cierre_id=options['cierre_id'])
            filtros_aplicados.append(f"Cierre ID: {options['cierre_id']}")

        if options['periodo']:
            queryset = queryset.filter(empleado__cierre__periodo=options['periodo'])
            filtros_aplicados.append(f"Período: {options['periodo']}")

        if options['cliente_id']:
            queryset = queryset.filter(empleado__cierre__cliente_id=options['cliente_id'])
            filtros_aplicados.append(f"Cliente ID: {options['cliente_id']}")

        if options['dias_antiguedad']:
            fecha_limite = datetime.now() - timedelta(days=options['dias_antiguedad'])
            queryset = queryset.filter(fecha_registro__lt=fecha_limite)
            filtros_aplicados.append(f"Más antiguos que {options['dias_antiguedad']} días")

        # Mostrar estadísticas
        total_registros = queryset.count()
        
        if filtros_aplicados:
            self.stdout.write("📋 Filtros aplicados:")
            for filtro in filtros_aplicados:
                self.stdout.write(f"   • {filtro}")
        else:
            self.stdout.write("⚠️ Sin filtros específicos aplicados")

        self.stdout.write(f"\n📊 ESTADÍSTICAS:")
        self.stdout.write(f"   • Total de registros a eliminar: {total_registros:,}")

        if total_registros == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ No hay registros que cumplan los criterios.")
            )
            return

        # Mostrar distribución por cierre
        cierres_afectados = queryset.values(
            'empleado__cierre__cliente__nombre',
            'empleado__cierre__periodo'
        ).distinct()

        self.stdout.write(f"\n🏢 Cierres afectados ({cierres_afectados.count()}):")
        for cierre in cierres_afectados[:10]:  # Mostrar solo los primeros 10
            count = queryset.filter(
                empleado__cierre__cliente__nombre=cierre['empleado__cierre__cliente__nombre'],
                empleado__cierre__periodo=cierre['empleado__cierre__periodo']
            ).count()
            self.stdout.write(
                f"   • {cierre['empleado__cierre__cliente__nombre']} - "
                f"{cierre['empleado__cierre__periodo']}: {count:,} registros"
            )

        if cierres_afectados.count() > 10:
            self.stdout.write(f"   ... y {cierres_afectados.count() - 10} más")

        # Verificar confirmación
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING("\n⚠️ MODO SIMULACIÓN - Agregue --confirmar para ejecutar eliminación")
            )
            return

        # Confirmación de seguridad para operaciones peligrosas
        if options['todo'] or total_registros > 10000:
            self.stdout.write(
                self.style.ERROR(f"\n🚨 OPERACIÓN PELIGROSA: {total_registros:,} registros")
            )
            confirmacion = input("Escriba 'ELIMINAR' para confirmar: ")
            if confirmacion != 'ELIMINAR':
                self.stdout.write(self.style.ERROR("❌ Operación cancelada"))
                return

        # Ejecutar eliminación
        self.stdout.write(f"\n🗑️ Iniciando eliminación de {total_registros:,} registros...")
        
        try:
            with transaction.atomic():
                eliminados, detalles = queryset.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ ELIMINACIÓN COMPLETADA")
                )
                self.stdout.write(f"   • Registros eliminados: {eliminados:,}")
                self.stdout.write(f"   • Detalles: {detalles}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error durante eliminación: {e}")
            )
