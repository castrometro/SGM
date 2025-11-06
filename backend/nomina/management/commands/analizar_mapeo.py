from django.core.management.base import BaseCommand
from nomina.models import (
    CierreNomina, 
    ConceptoRemuneracionNovedades, 
    RegistroConceptoEmpleadoNovedades,
    RegistroConceptoEmpleado,
    EmpleadoCierre,
    EmpleadoCierreNovedades
)

class Command(BaseCommand):
    help = 'Analiza el mapeo de conceptos para verificar discrepancias'

    def add_arguments(self, parser):
        parser.add_argument('--cierre', type=int, help='ID del cierre a analizar')

    def handle(self, *args, **options):
        self.stdout.write("🔍 Analizando mapeo de discrepancias...")
        self.stdout.write("=" * 50)
        
        # Buscar cierre
        if options['cierre']:
            try:
                cierre = CierreNomina.objects.get(id=options['cierre'])
            except CierreNomina.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Cierre {options['cierre']} no encontrado"))
                return
        else:
            cierres = CierreNomina.objects.filter(
                estado__in=['archivos_completos', 'verificacion_datos', 'con_discrepancias']
            ).order_by('-id')
            
            if not cierres.exists():
                self.stdout.write(self.style.ERROR("❌ No se encontraron cierres con datos"))
                return
            
            cierre = cierres.first()
        
        self.stdout.write(f"📊 Cierre: {cierre.id} - {cierre.cliente.nombre}")
        self.stdout.write(f"   Estado: {cierre.estado}")
        self.stdout.write(f"   Periodo: {cierre.periodo}")
        self.stdout.write("")
        
        # Verificar empleados
        emp_libro = EmpleadoCierre.objects.filter(cierre=cierre).count()
        emp_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre).count()
        
        self.stdout.write(f"👥 Empleados:")
        self.stdout.write(f"   Libro: {emp_libro}")
        self.stdout.write(f"   Novedades: {emp_novedades}")
        self.stdout.write("")
        
        # Verificar mapeos
        mapeos = ConceptoRemuneracionNovedades.objects.filter(
            cliente=cierre.cliente,
            activo=True
        )
        
        self.stdout.write(f"🗺️ Mapeos definidos: {mapeos.count()}")
        for i, mapeo in enumerate(mapeos[:5]):
            libro_nombre = mapeo.concepto_libro.nombre_concepto if mapeo.concepto_libro else "Sin mapeo"
            self.stdout.write(f"   {i+1}. '{mapeo.nombre_concepto_novedades}' → '{libro_nombre}'")
        
        if mapeos.count() > 5:
            self.stdout.write(f"   ... y {mapeos.count() - 5} más")
        self.stdout.write("")
        
        # Verificar registros con mapeo
        registros_con_mapeo = RegistroConceptoEmpleadoNovedades.objects.filter(
            empleado__cierre=cierre,
            concepto__isnull=False,
            concepto__concepto_libro__isnull=False
        ).count()
        
        total_registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(
            empleado__cierre=cierre
        ).count()
        
        self.stdout.write(f"📋 Registros de novedades:")
        self.stdout.write(f"   Total: {total_registros_novedades}")
        self.stdout.write(f"   Con mapeo válido: {registros_con_mapeo}")
        self.stdout.write(f"   Sin mapeo: {total_registros_novedades - registros_con_mapeo}")
        self.stdout.write("")
        
        # Ejemplo específico
        if emp_novedades > 0:
            emp_ejemplo = EmpleadoCierreNovedades.objects.filter(cierre=cierre).first()
            registros_ej = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_ejemplo)[:3]
            
            self.stdout.write(f"📝 Ejemplo - RUT {emp_ejemplo.rut}:")
            for reg in registros_ej:
                if reg.concepto and reg.concepto.concepto_libro:
                    mapeo_txt = f" → {reg.concepto.concepto_libro.nombre_concepto}"
                else:
                    mapeo_txt = " (sin mapeo)"
                self.stdout.write(f"   {reg.nombre_concepto_original}: {reg.monto}{mapeo_txt}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Análisis completado"))