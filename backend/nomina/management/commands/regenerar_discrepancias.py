from django.core.management.base import BaseCommand
from nomina.models import CierreNomina, DiscrepanciaCierre
from nomina.tasks_refactored.discrepancias import generar_discrepancias_cierre_con_logging
import time

class Command(BaseCommand):
    help = 'Regenera discrepancias usando la lógica corregida'

    def add_arguments(self, parser):
        parser.add_argument('--cierre', type=int, required=True, help='ID del cierre')
        parser.add_argument('--async', action='store_true', help='Ejecutar de forma asíncrona (Celery)')

    def handle(self, *args, **options):
        cierre_id = options['cierre']
        es_async = options['async']
        
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Cierre {cierre_id} no encontrado"))
            return
        
        self.stdout.write(f"🔄 REGENERANDO DISCREPANCIAS - Cierre {cierre_id}")
        self.stdout.write(f"Cliente: {cierre.cliente.nombre}")
        self.stdout.write(f"Estado actual: {cierre.estado}")
        self.stdout.write("=" * 60)
        
        # Mostrar discrepancias ANTES
        discrepancias_antes = DiscrepanciaCierre.objects.filter(cierre=cierre)
        self.stdout.write(f"📊 ANTES - Discrepancias existentes: {discrepancias_antes.count()}")
        
        if discrepancias_antes.count() > 0:
            # Mostrar algunos ejemplos
            for disc in discrepancias_antes[:3]:
                self.stdout.write(f"   - {disc.concepto_afectado}: Libro {disc.valor_libro} vs Novedades {disc.valor_novedades}")
            if discrepancias_antes.count() > 3:
                self.stdout.write(f"   ... y {discrepancias_antes.count() - 3} más")
        self.stdout.write("")
        
        if es_async:
            # Ejecutar usando Celery (como desde el frontend)
            self.stdout.write("🚀 Ejecutando con Celery (simulando frontend)...")
            task = generar_discrepancias_cierre_con_logging.delay(cierre_id, None)
            self.stdout.write(f"Task ID: {task.id}")
            
            # Esperar resultado
            self.stdout.write("⏳ Esperando resultado...")
            resultado = task.get(timeout=120)  # 2 minutos timeout
            
            self.stdout.write(f"✅ Task completada:")
            self.stdout.write(f"   Total discrepancias: {resultado.get('total_discrepancias', 0)}")
            self.stdout.write(f"   Estado final: {resultado.get('estado_final', 'N/A')}")
            
        else:
            # Ejecutar directamente (más rápido para testing)
            self.stdout.write("⚡ Ejecutando directamente...")
            from nomina.utils.GenerarDiscrepancias import generar_todas_discrepancias
            
            # Limpiar discrepancias anteriores
            cantidad_eliminada = discrepancias_antes.count()
            discrepancias_antes.delete()
            self.stdout.write(f"🗑️ Eliminadas {cantidad_eliminada} discrepancias anteriores")
            
            # Regenerar
            resultado = generar_todas_discrepancias(cierre)
            
            self.stdout.write(f"✅ Regeneración completada:")
            self.stdout.write(f"   Total discrepancias: {resultado.get('total_discrepancias', 0)}")
        
        # Recargar cierre y mostrar estado DESPUÉS
        cierre.refresh_from_db()
        discrepancias_despues = DiscrepanciaCierre.objects.filter(cierre=cierre)
        
        self.stdout.write("")
        self.stdout.write(f"📊 DESPUÉS - Discrepancias generadas: {discrepancias_despues.count()}")
        self.stdout.write(f"Estado del cierre: {cierre.estado}")
        
        if discrepancias_despues.count() > 0:
            self.stdout.write("\n📝 NUEVAS DISCREPANCIAS (primeras 5):")
            for i, disc in enumerate(discrepancias_despues[:5], 1):
                self.stdout.write(f"   {i}. {disc.concepto_afectado}")
                self.stdout.write(f"      RUT: {disc.rut_empleado}")
                self.stdout.write(f"      Libro: {disc.valor_libro} | Novedades: {disc.valor_novedades}")
                self.stdout.write(f"      Descripción: {disc.descripcion}")
                self.stdout.write("")
            
            if discrepancias_despues.count() > 5:
                self.stdout.write(f"   ... y {discrepancias_despues.count() - 5} más")
        else:
            self.stdout.write(self.style.SUCCESS("\n🎉 ¡No se encontraron discrepancias! Datos consistentes."))
        
        # Comparación antes vs después
        diferencia = discrepancias_despues.count() - cantidad_eliminada
        if diferencia < 0:
            self.stdout.write(self.style.SUCCESS(f"\n📉 MEJORA: {abs(diferencia)} discrepancias menos ({cantidad_eliminada} → {discrepancias_despues.count()})"))
        elif diferencia > 0:
            self.stdout.write(self.style.WARNING(f"\n📈 INCREMENTO: {diferencia} discrepancias más ({cantidad_eliminada} → {discrepancias_despues.count()})"))
        else:
            self.stdout.write(f"\n➡️ SIN CAMBIOS: {discrepancias_despues.count()} discrepancias")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Regeneración completada"))