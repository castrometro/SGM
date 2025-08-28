"""
Comando de gestión para probar la finalización de cierres contables.

Este comando permite probar el sistema de finalización:
1. Simula la ejecución de tareas de Celery
2. Verifica que el flujo completo funcione
3. Útil para debugging y desarrollo

Uso:
    python manage.py test_finalizacion --cierre_id=123
    python manage.py test_finalizacion --cierre_id=123 --sync  # Ejecutar sincrónicamente
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from contabilidad.models import CierreContabilidad
from contabilidad.tasks_finalizacion import finalizar_cierre_y_generar_reportes
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prueba el sistema de finalización de cierres contables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cierre_id',
            type=int,
            required=True,
            help='ID del cierre a finalizar'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Ejecutar la tarea sincrónicamente (sin Celery)'
        )
        parser.add_argument(
            '--usuario_id',
            type=int,
            help='ID del usuario que ejecuta la finalización'
        )

    def handle(self, *args, **options):
        cierre_id = options['cierre_id']
        usuario_id = options.get('usuario_id')
        ejecutar_sync = options['sync']

        try:
            # Verificar que el cierre existe
            cierre = CierreContabilidad.objects.get(id=cierre_id)
            
            self.stdout.write(
                self.style.SUCCESS(f'🔍 Cierre encontrado: {cierre.cliente.nombre} - {cierre.periodo}')
            )
            
            # Verificar que puede ser finalizado
            puede, mensaje = cierre.puede_finalizar()
            if not puede:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Cierre no puede ser finalizado: {mensaje}')
                )
                self.stdout.write(
                    self.style.WARNING(f'   Estado actual: {cierre.estado}')
                )
                
                # Preguntar si quiere forzar la ejecución
                respuesta = input('¿Desea continuar de todas formas? (y/N): ')
                if respuesta.lower() != 'y':
                    self.stdout.write(
                        self.style.ERROR('❌ Operación cancelada')
                    )
                    return
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Cierre puede ser finalizado')
            )
            
            # Ejecutar la tarea
            inicio = timezone.now()
            
            if ejecutar_sync:
                self.stdout.write(
                    self.style.WARNING('🔄 Ejecutando sincrónicamente (sin Celery)...')
                )
                
                # Ejecutar directamente la función
                resultado = finalizar_cierre_y_generar_reportes(
                    cierre_id=cierre_id,
                    usuario_id=usuario_id
                )
                
                fin = timezone.now()
                duracion = (fin - inicio).total_seconds()
                
                if resultado.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(f'🎉 Finalización completada exitosamente!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'   Duración: {duracion:.2f} segundos')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'   Resultados: {resultado}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error en finalización: {resultado.get("error")}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('🚀 Enviando tarea a Celery...')
                )
                
                # Ejecutar con Celery
                task = finalizar_cierre_y_generar_reportes.delay(
                    cierre_id=cierre_id,
                    usuario_id=usuario_id
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'📋 Tarea enviada a Celery')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   Task ID: {task.id}')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   Estado inicial: {task.state}')
                )
                
                # Monitorear la tarea por unos segundos
                self.stdout.write(
                    self.style.WARNING('👁️  Monitoreando progreso por 30 segundos...')
                )
                
                import time
                for i in range(30):
                    estado = task.state
                    
                    if estado == 'PENDING':
                        self.stdout.write(f'   [{i+1:2d}s] Estado: PENDIENTE (en cola)')
                    elif estado == 'PROGRESS':
                        info = task.info or {}
                        descripcion = info.get('descripcion', 'Procesando...')
                        porcentaje = info.get('porcentaje', 0)
                        self.stdout.write(f'   [{i+1:2d}s] Estado: PROGRESO ({porcentaje}%) - {descripcion}')
                    elif estado == 'SUCCESS':
                        resultado = task.result
                        self.stdout.write(
                            self.style.SUCCESS(f'🎉 Tarea completada exitosamente!')
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'   Resultado: {resultado}')
                        )
                        break
                    elif estado == 'FAILURE':
                        self.stdout.write(
                            self.style.ERROR(f'❌ Tarea falló: {task.info}')
                        )
                        break
                    else:
                        self.stdout.write(f'   [{i+1:2d}s] Estado: {estado}')
                    
                    time.sleep(1)
                
                if task.state in ['PENDING', 'PROGRESS']:
                    self.stdout.write(
                        self.style.WARNING('⏰ Tarea aún en ejecución después de 30 segundos')
                    )
                    self.stdout.write(
                        self.style.WARNING(f'   Puedes consultar el progreso con: python manage.py celery_status {task.id}')
                    )

        except CierreContabilidad.DoesNotExist:
            raise CommandError(f'Cierre con ID {cierre_id} no encontrado')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado: {str(e)}')
            )
            raise CommandError(str(e))
