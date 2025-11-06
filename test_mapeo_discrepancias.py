#!/usr/bin/env python3
"""
Script de prueba para verificar que la comparación Libro vs Novedades
esté usando correctamente el mapeo definido en ConceptoRemuneracionNovedades

Uso:
python test_mapeo_discrepancias.py [cierre_id]
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from nomina.models import (
    CierreNomina, 
    ConceptoRemuneracionNovedades, 
    RegistroConceptoEmpleadoNovedades,
    RegistroConceptoEmpleado,
    EmpleadoCierre,
    EmpleadoCierreNovedades
)

def analizar_mapeo_cierre(cierre_id):
    """Analiza el mapeo de conceptos para un cierre específico"""
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        print(f"🔍 Analizando mapeo para cierre {cierre_id} - {cierre.cliente.nombre}")
        print("=" * 80)
        
        # 1. Verificar empleados comunes
        empleados_libro = EmpleadoCierre.objects.filter(cierre=cierre)
        empleados_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre)
        
        print(f"📊 EMPLEADOS:")
        print(f"  - Libro: {empleados_libro.count()}")
        print(f"  - Novedades: {empleados_novedades.count()}")
        
        # Obtener algunos RUTs comunes para ejemplo
        ruts_libro = set(emp.rut for emp in empleados_libro)
        ruts_novedades = set(emp.rut for emp in empleados_novedades)
        ruts_comunes = ruts_libro & ruts_novedades
        
        print(f"  - RUTs comunes: {len(ruts_comunes)}")
        print()
        
        if not ruts_comunes:
            print("❌ No hay empleados comunes para analizar")
            return
        
        # 2. Analizar mapeos definidos
        mapeos = ConceptoRemuneracionNovedades.objects.filter(
            cliente=cierre.cliente,
            activo=True,
            concepto_libro__isnull=False
        )
        
        print(f"🗺️ MAPEOS DEFINIDOS: {mapeos.count()}")
        for mapeo in mapeos[:10]:  # Mostrar primeros 10
            print(f"  '{mapeo.nombre_concepto_novedades}' → '{mapeo.concepto_libro.nombre_concepto}'")
        if mapeos.count() > 10:
            print(f"  ... y {mapeos.count() - 10} más")
        print()
        
        # 3. Analizar un empleado específico
        rut_ejemplo = list(ruts_comunes)[0]
        emp_libro = empleados_libro.filter(rut=rut_ejemplo).first()
        emp_novedades = empleados_novedades.filter(rut=rut_ejemplo).first()
        
        print(f"👤 ANÁLISIS DETALLADO - RUT: {rut_ejemplo}")
        print(f"  Nombre: {emp_libro.nombre} {emp_libro.apellido_paterno}")
        print()
        
        # Conceptos en libro
        registros_libro = RegistroConceptoEmpleado.objects.filter(empleado=emp_libro)
        print(f"📖 CONCEPTOS EN LIBRO ({registros_libro.count()}):")
        for reg in registros_libro[:5]:
            concepto_nombre = reg.concepto.nombre_concepto if reg.concepto else reg.nombre_concepto_original
            print(f"  - {concepto_nombre}: {reg.monto}")
        if registros_libro.count() > 5:
            print(f"  ... y {registros_libro.count() - 5} más")
        print()
        
        # Conceptos en novedades
        registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(
            empleado=emp_novedades
        )
        print(f"📝 CONCEPTOS EN NOVEDADES ({registros_novedades.count()}):")
        for reg in registros_novedades[:5]:
            if reg.concepto and reg.concepto.concepto_libro:
                mapeo_info = f" → {reg.concepto.concepto_libro.nombre_concepto}"
            else:
                mapeo_info = " (sin mapeo)"
            print(f"  - {reg.nombre_concepto_original}: {reg.monto}{mapeo_info}")
        if registros_novedades.count() > 5:
            print(f"  ... y {registros_novedades.count() - 5} más")
        print()
        
        # 4. Verificar comparaciones que se realizarían
        registros_con_mapeo = RegistroConceptoEmpleadoNovedades.objects.filter(
            empleado=emp_novedades,
            concepto__isnull=False,
            concepto__concepto_libro__isnull=False
        )
        
        print(f"🔗 CONCEPTOS CON MAPEO VÁLIDO ({registros_con_mapeo.count()}):")
        comparaciones_posibles = 0
        dict_libro = {reg.concepto.id: reg for reg in registros_libro if reg.concepto}
        
        for reg_novedades in registros_con_mapeo[:5]:
            concepto_libro_eq = reg_novedades.concepto_libro_equivalente
            reg_libro = dict_libro.get(concepto_libro_eq.id) if concepto_libro_eq else None
            
            if reg_libro:
                comparaciones_posibles += 1
                print(f"  ✅ '{reg_novedades.nombre_concepto_original}' → '{concepto_libro_eq.nombre_concepto}'")
                print(f"     Novedades: {reg_novedades.monto} | Libro: {reg_libro.monto}")
                
                # Verificar si sería una discrepancia
                if reg_libro.es_numerico and reg_novedades.es_numerico:
                    diferencia = abs(reg_libro.monto_numerico - reg_novedades.monto_numerico)
                    if diferencia > 0.01:
                        print(f"     🚨 DISCREPANCIA: Diferencia de {diferencia}")
                    else:
                        print(f"     ✅ COINCIDE")
            else:
                print(f"  ❌ '{reg_novedades.nombre_concepto_original}' → '{concepto_libro_eq.nombre_concepto}' (no en libro)")
        
        print(f"\n📋 RESUMEN:")
        print(f"  - Comparaciones posibles: {comparaciones_posibles}")
        print(f"  - Total registros novedades con mapeo: {registros_con_mapeo.count()}")
        
    except CierreNomina.DoesNotExist:
        print(f"❌ Cierre {cierre_id} no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) > 1:
        cierre_id = int(sys.argv[1])
    else:
        # Buscar un cierre reciente con datos
        cierres = CierreNomina.objects.filter(
            estado__in=['archivos_completos', 'verificacion_datos', 'con_discrepancias']
        ).order_by('-id')
        
        if not cierres.exists():
            print("❌ No se encontraron cierres con datos para analizar")
            return
        
        cierre_id = cierres.first().id
        print(f"🔍 Usando cierre más reciente: {cierre_id}")
    
    analizar_mapeo_cierre(cierre_id)

if __name__ == "__main__":
    main()