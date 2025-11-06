#!/usr/bin/env python3
"""
Script simple para verificar el mapeo de discrepancias
"""

# Importaciones necesarias
from nomina.models import (
    CierreNomina, 
    ConceptoRemuneracionNovedades, 
    RegistroConceptoEmpleadoNovedades,
    RegistroConceptoEmpleado,
    EmpleadoCierre,
    EmpleadoCierreNovedades
)

def main():
    print("🔍 Analizando mapeo de discrepancias...")
    print("=" * 50)
    
    # Buscar cierres disponibles
    cierres = CierreNomina.objects.filter(
        estado__in=['archivos_completos', 'verificacion_datos', 'con_discrepancias']
    ).order_by('-id')
    
    if not cierres.exists():
        print("❌ No se encontraron cierres con datos")
        return
    
    cierre = cierres.first()
    print(f"📊 Cierre: {cierre.id} - {cierre.cliente.nombre}")
    print(f"   Estado: {cierre.estado}")
    print(f"   Periodo: {cierre.periodo}")
    print()
    
    # Verificar empleados
    emp_libro = EmpleadoCierre.objects.filter(cierre=cierre).count()
    emp_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre).count()
    
    print(f"👥 Empleados:")
    print(f"   Libro: {emp_libro}")
    print(f"   Novedades: {emp_novedades}")
    print()
    
    # Verificar mapeos
    mapeos = ConceptoRemuneracionNovedades.objects.filter(
        cliente=cierre.cliente,
        activo=True
    )
    
    print(f"🗺️ Mapeos definidos: {mapeos.count()}")
    for i, mapeo in enumerate(mapeos[:5]):
        libro_nombre = mapeo.concepto_libro.nombre_concepto if mapeo.concepto_libro else "Sin mapeo"
        print(f"   {i+1}. '{mapeo.nombre_concepto_novedades}' → '{libro_nombre}'")
    
    if mapeos.count() > 5:
        print(f"   ... y {mapeos.count() - 5} más")
    print()
    
    # Verificar registros con mapeo
    registros_con_mapeo = RegistroConceptoEmpleadoNovedades.objects.filter(
        empleado__cierre=cierre,
        concepto__isnull=False,
        concepto__concepto_libro__isnull=False
    ).count()
    
    total_registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(
        empleado__cierre=cierre
    ).count()
    
    print(f"📋 Registros de novedades:")
    print(f"   Total: {total_registros_novedades}")
    print(f"   Con mapeo válido: {registros_con_mapeo}")
    print(f"   Sin mapeo: {total_registros_novedades - registros_con_mapeo}")
    print()
    
    # Ejemplo específico
    if emp_novedades > 0:
        emp_ejemplo = EmpleadoCierreNovedades.objects.filter(cierre=cierre).first()
        registros_ej = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_ejemplo)[:3]
        
        print(f"📝 Ejemplo - RUT {emp_ejemplo.rut}:")
        for reg in registros_ej:
            if reg.concepto and reg.concepto.concepto_libro:
                mapeo_txt = f" → {reg.concepto.concepto_libro.nombre_concepto}"
            else:
                mapeo_txt = " (sin mapeo)"
            print(f"   {reg.nombre_concepto_original}: {reg.monto}{mapeo_txt}")
    
    print("\n✅ Análisis completado")

if __name__ == "__main__":
    main()