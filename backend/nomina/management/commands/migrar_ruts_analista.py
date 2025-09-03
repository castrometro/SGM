from django.core.management.base import BaseCommand
from django.db import transaction
from nomina.models import AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso
from nomina.utils.GenerarIncidencias import formatear_rut_con_guion


class Command(BaseCommand):
    help = 'Migra RUTs de modelos de analista para que tengan formato con guión'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar migración (sin este flag solo muestra estadísticas)'
        )
        parser.add_argument(
            '--modelo',
            type=str,
            choices=['finiquitos', 'incidencias', 'ingresos', 'todos'],
            default='todos',
            help='Modelo específico a migrar (default: todos)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🔄 MIGRACIÓN DE RUTS DE ANALISTA A FORMATO CON GUIÓN')
        )
        self.stdout.write('=' * 60)

        modelos_info = {
            'finiquitos': {
                'modelo': AnalistaFiniquito,
                'nombre': 'Analista Finiquitos'
            },
            'incidencias': {
                'modelo': AnalistaIncidencia,
                'nombre': 'Analista Incidencias'
            },
            'ingresos': {
                'modelo': AnalistaIngreso,
                'nombre': 'Analista Ingresos'
            }
        }

        # Determinar qué modelos procesar
        if options['modelo'] == 'todos':
            modelos_a_procesar = modelos_info.keys()
        else:
            modelos_a_procesar = [options['modelo']]

        total_registros = 0
        total_actualizados = 0

        for modelo_key in modelos_a_procesar:
            info = modelos_info[modelo_key]
            modelo = info['modelo']
            nombre = info['nombre']

            self.stdout.write(f"\n📋 Procesando: {nombre}")
            self.stdout.write("-" * 40)

            # Obtener todos los registros
            registros = modelo.objects.all()
            count_total = registros.count()
            count_actualizados = 0
            
            self.stdout.write(f"Total registros: {count_total:,}")

            if count_total == 0:
                self.stdout.write("   ✅ No hay registros para procesar")
                continue

            # Analizar cuántos necesitan actualización
            registros_a_actualizar = []
            for registro in registros:
                rut_actual = registro.rut
                rut_formateado = formatear_rut_con_guion(rut_actual)
                
                if rut_actual != rut_formateado:
                    registros_a_actualizar.append({
                        'registro': registro,
                        'rut_actual': rut_actual,
                        'rut_nuevo': rut_formateado
                    })

            self.stdout.write(f"Registros que necesitan actualización: {len(registros_a_actualizar):,}")
            
            # Mostrar ejemplos
            if registros_a_actualizar:
                self.stdout.write("📝 Ejemplos de cambios:")
                for i, item in enumerate(registros_a_actualizar[:5]):
                    self.stdout.write(
                        f"   • '{item['rut_actual']}' → '{item['rut_nuevo']}'"
                    )
                if len(registros_a_actualizar) > 5:
                    self.stdout.write(f"   ... y {len(registros_a_actualizar) - 5} más")

            total_registros += count_total
            
            # Ejecutar migración si se confirma
            if options['confirmar'] and registros_a_actualizar:
                self.stdout.write(f"\n🔄 Actualizando {len(registros_a_actualizar)} registros...")
                
                try:
                    with transaction.atomic():
                        for item in registros_a_actualizar:
                            registro = item['registro']
                            registro.rut = item['rut_nuevo']
                            registro.save(update_fields=['rut'])
                            count_actualizados += 1
                            
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {count_actualizados} registros actualizados en {nombre}")
                        )
                        total_actualizados += count_actualizados
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error actualizando {nombre}: {e}")
                    )
            elif not options['confirmar'] and registros_a_actualizar:
                self.stdout.write(
                    self.style.WARNING("⚠️ Modo simulación - use --confirmar para aplicar cambios")
                )

        # Resumen final
        self.stdout.write(f"\n📊 RESUMEN FINAL:")
        self.stdout.write(f"   • Total registros analizados: {total_registros:,}")
        
        if options['confirmar']:
            self.stdout.write(f"   • Total registros actualizados: {total_actualizados:,}")
            self.stdout.write(
                self.style.SUCCESS("✅ Migración completada exitosamente")
            )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ Migración en modo simulación - use --confirmar para ejecutar")
            )
