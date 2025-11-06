from django.core.management.base import BaseCommand
from nomina.models import (
    CierreNomina, 
    ConceptoRemuneracionNovedades, 
    RegistroConceptoEmpleadoNovedades,
    RegistroConceptoEmpleado,
    EmpleadoCierre,
    EmpleadoCierreNovedades
)
from nomina.utils.GenerarDiscrepancias import _comparar_solo_montos_conceptos, _es_valor_vacio

class Command(BaseCommand):
    help = 'Prueba la nueva lógica de comparación con mapeo'

    def add_arguments(self, parser):
        parser.add_argument('--cierre', type=int, help='ID del cierre a analizar')
        parser.add_argument('--rut', type=str, help='RUT específico a analizar')

    def handle(self, *args, **options):
        self.stdout.write("🧪 Probando nueva lógica de comparación con mapeo...")
        self.stdout.write("=" * 60)
        
        # Buscar cierre
        if options['cierre']:
            try:
                cierre = CierreNomina.objects.get(id=options['cierre'])
            except CierreNomina.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Cierre {options['cierre']} no encontrado"))
                return
        else:
            cierre = CierreNomina.objects.filter(
                estado__in=['archivos_completos', 'verificacion_datos', 'con_discrepancias']
            ).order_by('-id').first()
        
        if not cierre:
            self.stdout.write(self.style.ERROR("❌ No se encontraron cierres disponibles"))
            return
            
        self.stdout.write(f"📊 Cierre: {cierre.id} - {cierre.cliente.nombre}")
        self.stdout.write("")
        
        # Buscar empleado de ejemplo
        if options['rut']:
            emp_libro = EmpleadoCierre.objects.filter(cierre=cierre, rut=options['rut']).first()
            emp_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre, rut=options['rut']).first()
            
            if not emp_libro or not emp_novedades:
                self.stdout.write(self.style.ERROR(f"❌ RUT {options['rut']} no encontrado en ambos archivos"))
                return
        else:
            # Buscar empleados comunes
            ruts_libro = set(EmpleadoCierre.objects.filter(cierre=cierre).values_list('rut', flat=True))
            ruts_novedades = set(EmpleadoCierreNovedades.objects.filter(cierre=cierre).values_list('rut', flat=True))
            ruts_comunes = ruts_libro & ruts_novedades
            
            if not ruts_comunes:
                self.stdout.write(self.style.ERROR("❌ No hay empleados comunes"))
                return
            
            rut_ejemplo = list(ruts_comunes)[0]
            emp_libro = EmpleadoCierre.objects.filter(cierre=cierre, rut=rut_ejemplo).first()
            emp_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre, rut=rut_ejemplo).first()
        
        self.stdout.write(f"👤 Empleado: {emp_libro.nombre} {emp_libro.apellido_paterno}")
        self.stdout.write(f"   RUT: {emp_libro.rut}")
        self.stdout.write("")
        
        # Analizar conceptos ANTES (lógica anterior)
        self.stdout.write("📋 ANÁLISIS COMPARATIVO:")
        self.stdout.write("-" * 40)
        
        # 1. Conceptos en libro
        registros_libro = RegistroConceptoEmpleado.objects.filter(empleado=emp_libro)
        self.stdout.write(f"📖 Conceptos en Libro ({registros_libro.count()}):")
        dict_libro_id = {reg.concepto.id: reg for reg in registros_libro if reg.concepto}
        
        for reg in registros_libro[:5]:
            concepto_nombre = reg.concepto.nombre_concepto if reg.concepto else reg.nombre_concepto_original
            self.stdout.write(f"   - {concepto_nombre}: {reg.monto}")
        if registros_libro.count() > 5:
            self.stdout.write(f"   ... y {registros_libro.count() - 5} más")
        self.stdout.write("")
        
        # 2. Conceptos en novedades
        registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_novedades)
        registros_con_mapeo = registros_novedades.filter(
            concepto__isnull=False,
            concepto__concepto_libro__isnull=False
        )
        
        self.stdout.write(f"📝 Conceptos en Novedades ({registros_novedades.count()}):")
        self.stdout.write(f"   Con mapeo válido: {registros_con_mapeo.count()}")
        self.stdout.write(f"   Sin mapeo: {registros_novedades.count() - registros_con_mapeo.count()}")
        self.stdout.write("")
        
        # 3. Comparaciones que se realizarían
        self.stdout.write("🔄 COMPARACIONES CON MAPEO:")
        self.stdout.write("-" * 30)
        
        comparaciones = 0
        discrepancias_encontradas = 0
        omitidos_sin_valor = 0
        
        for reg_novedades in registros_con_mapeo:
            concepto_libro_eq = reg_novedades.concepto_libro_equivalente
            if not concepto_libro_eq:
                continue
                
            reg_libro = dict_libro_id.get(concepto_libro_eq.id)
            if not reg_libro:
                self.stdout.write(f"   ❌ '{reg_novedades.nombre_concepto_original}' → '{concepto_libro_eq.nombre_concepto}' (no en libro)")
                continue
            
            # Verificar si se omite por valor vacío
            if _es_valor_vacio(reg_novedades.monto):
                omitidos_sin_valor += 1
                continue
                
            comparaciones += 1
            
            # Mostrar comparación
            self.stdout.write(f"   🔍 '{reg_novedades.nombre_concepto_original}' → '{concepto_libro_eq.nombre_concepto}'")
            self.stdout.write(f"      Novedades: '{reg_novedades.monto}' | Libro: '{reg_libro.monto}'")
            
            # Verificar discrepancia
            if reg_libro.es_numerico and reg_novedades.es_numerico:
                diferencia = abs(reg_libro.monto_numerico - reg_novedades.monto_numerico)
                if diferencia > 0.01:
                    discrepancias_encontradas += 1
                    self.stdout.write(self.style.WARNING(f"      🚨 DISCREPANCIA: Diferencia de {diferencia}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"      ✅ COINCIDE"))
            elif str(reg_libro.monto) != str(reg_novedades.monto):
                discrepancias_encontradas += 1
                self.stdout.write(self.style.WARNING(f"      🚨 DISCREPANCIA TEXTUAL"))
            else:
                self.stdout.write(self.style.SUCCESS(f"      ✅ COINCIDE"))
            self.stdout.write("")
        
        # Resumen
        self.stdout.write("📊 RESUMEN:")
        self.stdout.write(f"   Registros novedades con mapeo: {registros_con_mapeo.count()}")
        self.stdout.write(f"   Omitidos (sin valor): {omitidos_sin_valor}")
        self.stdout.write(f"   Comparaciones realizadas: {comparaciones}")
        self.stdout.write(f"   Discrepancias encontradas: {discrepancias_encontradas}")
        
        if discrepancias_encontradas > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️ Se encontraron {discrepancias_encontradas} discrepancias usando el mapeo"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ No se encontraron discrepancias con el nuevo mapeo"))
        
        # Probar la función corregida
        self.stdout.write("\n🔧 PROBANDO FUNCIÓN CORREGIDA:")
        self.stdout.write("-" * 35)
        
        try:
            discrepancias_func = _comparar_solo_montos_conceptos(cierre, emp_libro, emp_novedades)
            self.stdout.write(f"   Discrepancias generadas por función: {len(discrepancias_func)}")
            
            for i, disc in enumerate(discrepancias_func[:3]):
                self.stdout.write(f"   {i+1}. {disc.concepto_afectado}")
                self.stdout.write(f"      {disc.descripcion}")
                self.stdout.write(f"      Libro: {disc.valor_libro} | Novedades: {disc.valor_novedades}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error en función: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Prueba completada"))