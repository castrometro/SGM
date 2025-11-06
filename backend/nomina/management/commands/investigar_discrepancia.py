from django.core.management.base import BaseCommand
from nomina.models import (
    CierreNomina, 
    ConceptoRemuneracionNovedades, 
    RegistroConceptoEmpleadoNovedades,
    RegistroConceptoEmpleado,
    EmpleadoCierre,
    EmpleadoCierreNovedades,
    DiscrepanciaCierre
)

class Command(BaseCommand):
    help = 'Investiga profundamente una discrepancia específica'

    def add_arguments(self, parser):
        parser.add_argument('--cierre', type=int, required=True, help='ID del cierre')
        parser.add_argument('--rut', type=str, required=True, help='RUT del empleado')
        parser.add_argument('--concepto', type=str, required=True, help='Nombre del concepto')

    def handle(self, *args, **options):
        cierre_id = options['cierre']
        rut = options['rut']
        concepto_buscar = options['concepto']
        
        self.stdout.write(f"🔍 INVESTIGACIÓN PROFUNDA")
        self.stdout.write(f"Cierre: {cierre_id} | RUT: {rut} | Concepto: '{concepto_buscar}'")
        self.stdout.write("=" * 80)
        
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            emp_libro = EmpleadoCierre.objects.get(cierre=cierre, rut=rut)
            emp_novedades = EmpleadoCierreNovedades.objects.get(cierre=cierre, rut=rut)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            return
        
        self.stdout.write(f"👤 Empleado: {emp_libro.nombre} {emp_libro.apellido_paterno}")
        self.stdout.write("")
        
        # 1. Buscar todas las discrepancias existentes para este empleado
        discrepancias_existentes = DiscrepanciaCierre.objects.filter(
            cierre=cierre,
            rut_empleado=rut
        )
        
        self.stdout.write(f"📋 DISCREPANCIAS EXISTENTES ({discrepancias_existentes.count()}):")
        for disc in discrepancias_existentes:
            if concepto_buscar.lower() in disc.concepto_afectado.lower():
                self.stdout.write(f"   🎯 ENCONTRADA: {disc.concepto_afectado}")
                self.stdout.write(f"      Libro: {disc.valor_libro} | Novedades: {disc.valor_novedades}")
                self.stdout.write(f"      Descripción: {disc.descripcion}")
                self.stdout.write("")
        
        # 2. Buscar TODOS los conceptos en libro que contengan el término
        registros_libro_todos = RegistroConceptoEmpleado.objects.filter(empleado=emp_libro)
        conceptos_libro_relacionados = []
        
        for reg in registros_libro_todos:
            nombre_concepto = reg.concepto.nombre_concepto if reg.concepto else reg.nombre_concepto_original
            if concepto_buscar.lower() in nombre_concepto.lower():
                conceptos_libro_relacionados.append((nombre_concepto, reg.monto, reg))
        
        self.stdout.write(f"📖 CONCEPTOS EN LIBRO que contienen '{concepto_buscar}' ({len(conceptos_libro_relacionados)}):")
        for nombre, monto, reg in conceptos_libro_relacionados:
            self.stdout.write(f"   - {nombre}: {monto}")
        self.stdout.write("")
        
        # 3. Buscar TODOS los conceptos en novedades que contengan el término
        registros_novedades_todos = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_novedades)
        conceptos_novedades_relacionados = []
        
        for reg in registros_novedades_todos:
            if concepto_buscar.lower() in reg.nombre_concepto_original.lower():
                concepto_libro_eq = reg.concepto_libro_equivalente.nombre_concepto if reg.concepto_libro_equivalente else "Sin mapeo"
                conceptos_novedades_relacionados.append((reg.nombre_concepto_original, reg.monto, concepto_libro_eq, reg))
        
        self.stdout.write(f"📝 CONCEPTOS EN NOVEDADES que contienen '{concepto_buscar}' ({len(conceptos_novedades_relacionados)}):")
        for nombre, monto, mapeo, reg in conceptos_novedades_relacionados:
            self.stdout.write(f"   - {nombre}: {monto} → {mapeo}")
        self.stdout.write("")
        
        # 4. Análisis de mapeo específico
        mapeos_relacionados = ConceptoRemuneracionNovedades.objects.filter(
            cliente=cierre.cliente,
            nombre_concepto_novedades__icontains=concepto_buscar,
            activo=True
        )
        
        self.stdout.write(f"🗺️ MAPEOS RELACIONADOS ({mapeos_relacionados.count()}):")
        for mapeo in mapeos_relacionados:
            libro_nombre = mapeo.concepto_libro.nombre_concepto if mapeo.concepto_libro else "Sin mapeo"
            self.stdout.write(f"   '{mapeo.nombre_concepto_novedades}' → '{libro_nombre}'")
        self.stdout.write("")
        
        # 5. Comparación usando lógica anterior (por nombre directo)
        self.stdout.write("🔄 SIMULACIÓN LÓGICA ANTERIOR (por nombre directo):")
        
        # Buscar conceptos con nombres similares
        for nombre_nov, monto_nov, mapeo_nov, reg_nov in conceptos_novedades_relacionados:
            for nombre_lib, monto_lib, reg_lib in conceptos_libro_relacionados:
                # Normalizar nombres para comparación
                if self._nombres_similares(nombre_nov, nombre_lib):
                    self.stdout.write(f"   ⚠️ POSIBLE COMPARACIÓN INCORRECTA:")
                    self.stdout.write(f"      Novedades: '{nombre_nov}' = {monto_nov}")
                    self.stdout.write(f"      Libro: '{nombre_lib}' = {monto_lib}")
                    
                    if str(monto_nov) != str(monto_lib):
                        self.stdout.write(f"      🚨 DISCREPANCIA DETECTADA")
                    else:
                        self.stdout.write(f"      ✅ VALORES IGUALES")
                    self.stdout.write("")
        
        # 6. Comparación usando lógica corregida (por mapeo)
        self.stdout.write("✅ LÓGICA CORREGIDA (por mapeo):")
        
        for nombre_nov, monto_nov, mapeo_nov, reg_nov in conceptos_novedades_relacionados:
            if reg_nov.concepto_libro_equivalente:
                # Buscar el registro correspondiente en libro
                reg_libro_mapeado = None
                for nombre_lib, monto_lib, reg_lib in conceptos_libro_relacionados:
                    if reg_lib.concepto and reg_lib.concepto.id == reg_nov.concepto_libro_equivalente.id:
                        reg_libro_mapeado = (nombre_lib, monto_lib, reg_lib)
                        break
                
                if reg_libro_mapeado:
                    nombre_lib, monto_lib, reg_lib = reg_libro_mapeado
                    self.stdout.write(f"   ✅ COMPARACIÓN CORRECTA:")
                    self.stdout.write(f"      Novedades: '{nombre_nov}' = {monto_nov}")
                    self.stdout.write(f"      Libro: '{nombre_lib}' = {monto_lib} (mapeado)")
                    
                    if str(monto_nov) != str(monto_lib):
                        self.stdout.write(f"      🚨 DISCREPANCIA REAL")
                    else:
                        self.stdout.write(f"      ✅ VALORES IGUALES")
                    self.stdout.write("")
    
    def _nombres_similares(self, nombre1, nombre2):
        """Verifica si dos nombres son similares (lógica simplificada)"""
        # Normalizar
        n1 = nombre1.lower().replace(' ', '').replace('.', '')
        n2 = nombre2.lower().replace(' ', '').replace('.', '')
        
        # Verificar si uno contiene al otro o son iguales
        return n1 in n2 or n2 in n1 or n1 == n2