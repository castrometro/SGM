"""
Management command para recuperar y reinstalar sets de clasificación predefinidos
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transactions
from contabilidad.tasks_cuentas_bulk import (
    recuperar_sets_clasificacion_cliente,
    crear_sets_predefinidos_clasificacion,
    reinstalar_sets_predefinidos_clasificacion
)
from clientes.models import Cliente


class Command(BaseCommand):
    help = 'Recuperar y reinstalar sets de clasificación predefinidos para clientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID del cliente específico (si no se especifica, procesa todos los clientes)'
        )
        parser.add_argument(
            '--limpiar-existentes',
            action='store_true',
            help='Limpiar sets existentes antes de recrear (usar con precaución)'
        )
        parser.add_argument(
            '--solo-predefinidos',
            action='store_true',
            help='Solo crear sets predefinidos, no los derivados de datos RAW'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular la operación sin realizar cambios'
        )

    def handle(self, *args, **options):
        cliente_id = options.get('cliente_id')
        limpiar_existentes = options.get('limpiar_existentes', False)
        solo_predefinidos = options.get('solo_predefinidos', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios reales')
            )

        try:
            if cliente_id:
                # Procesar cliente específico
                clientes = [Cliente.objects.get(id=cliente_id)]
                self.stdout.write(f'Procesando cliente ID: {cliente_id}')
            else:
                # Procesar todos los clientes
                clientes = Cliente.objects.all()
                self.stdout.write(f'Procesando todos los clientes ({clientes.count()} total)')

            if limpiar_existentes:
                self.stdout.write(
                    self.style.WARNING(
                        'ATENCIÓN: Se limpiarán sets existentes antes de recrear'
                    )
                )

            total_procesados = 0
            total_exitosos = 0
            total_errores = 0

            for cliente in clientes:
                try:
                    self.stdout.write(f'\n--- Procesando Cliente: {cliente.nombre} (ID: {cliente.id}) ---')
                    
                    if dry_run:
                        self.stdout.write('  [DRY-RUN] Simularía la creación de sets...')
                        total_procesados += 1
                        total_exitosos += 1
                        continue

                    with transaction.atomic():
                        if solo_predefinidos:
                            # Solo sets predefinidos
                            if limpiar_existentes:
                                resultado = reinstalar_sets_predefinidos_clasificacion(
                                    cliente.id, 
                                    limpiar_existentes=True
                                )
                            else:
                                resultado = crear_sets_predefinidos_clasificacion(cliente.id)
                        else:
                            # Sets completos (RAW + predefinidos)
                            resultado = recuperar_sets_clasificacion_cliente(
                                cliente.id,
                                incluir_predefinidos=True,
                                limpiar_existentes=limpiar_existentes
                            )

                        # Mostrar resultado
                        if isinstance(resultado, dict):
                            sets_creados = resultado.get('sets_creados', 0)
                            opciones_creadas = resultado.get('opciones_creadas', 0)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Sets creados: {sets_creados}, Opciones creadas: {opciones_creadas}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ {resultado}')
                            )

                    total_procesados += 1
                    total_exitosos += 1

                except Cliente.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Cliente ID {cliente_id} no encontrado')
                    )
                    total_errores += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error procesando cliente {cliente.id}: {str(e)}')
                    )
                    total_procesados += 1
                    total_errores += 1

            # Resumen final
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'RESUMEN:')
            self.stdout.write(f'  Clientes procesados: {total_procesados}')
            self.stdout.write(f'  Exitosos: {total_exitosos}')
            self.stdout.write(f'  Errores: {total_errores}')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('NOTA: Esta fue una simulación, no se realizaron cambios')
                )
            
            if total_errores == 0:
                self.stdout.write(
                    self.style.SUCCESS('✓ Proceso completado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Proceso completado con {total_errores} errores')
                )

        except Exception as e:
            raise CommandError(f'Error ejecutando comando: {str(e)}')
