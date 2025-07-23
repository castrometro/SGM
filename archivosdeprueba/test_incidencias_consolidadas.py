#!/usr/bin/env python3
"""
Test script para probar el nuevo sistema de incidencias consolidadas
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, '/root/SGM/backend')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from nomina.models import (
    CierreNomina, 
    NominaConsolidada, 
    ConceptoConsolidado, 
    MovimientoPersonal,
    IncidenciaCierre,
    TipoIncidencia
)
from nomina.utils.DetectarIncidenciasConsolidadas import detectar_incidencias_consolidadas
from api.models import Cliente
from django.contrib.auth import get_user_model

User = get_user_model()

def crear_datos_prueba():
    """
    Crea datos de prueba para el sistema de incidencias consolidadas
    """
    print("📊 Creando datos de prueba...")
    
    # 1. Crear cliente de prueba
    cliente, _ = Cliente.objects.get_or_create(
        nombre="Empresa Test Incidencias",
        defaults={'estado': 'activo'}
    )
    
    # 2. Crear usuario analista
    analista, _ = User.objects.get_or_create(
        username="test_analista",
        defaults={
            'email': 'test@empresa.com',
            'tipo_usuario': 'analista',
            'is_active': True
        }
    )
    
    # 3. Crear cierre período anterior (febrero)
    cierre_anterior, _ = CierreNomina.objects.get_or_create(
        cliente=cliente,
        periodo=date(2024, 2, 1),
        defaults={
            'usuario_analista': analista,
            'estado': 'completado',
            'estado_consolidacion': 'consolidado',
            'estado_incidencias': 'sin_incidencias'
        }
    )
    
    # 4. Crear cierre período actual (marzo)
    cierre_actual, _ = CierreNomina.objects.get_or_create(
        cliente=cliente,
        periodo=date(2024, 3, 1),
        defaults={
            'usuario_analista': analista,
            'estado': 'completado',
            'estado_consolidacion': 'consolidado',
            'estado_incidencias': 'pendiente'
        }
    )
    
    # 5. Crear datos consolidados para período anterior
    crear_nomina_consolidada_anterior(cierre_anterior)
    
    # 6. Crear datos consolidados para período actual (con diferencias)
    crear_nomina_consolidada_actual(cierre_actual)
    
    print(f"✅ Datos creados: Cliente {cliente.id}, Cierres {cierre_anterior.id} (feb) y {cierre_actual.id} (mar)")
    return cierre_anterior, cierre_actual

def crear_nomina_consolidada_anterior(cierre):
    """
    Crea datos consolidados para el período anterior (febrero)
    """
    # Empleado 1: Juan Pérez (estable)
    nomina1 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="11111111-1",
        nombre_empleado="Juan Pérez",
        total_haberes=Decimal("1000000"),
        total_descuentos=Decimal("200000"),
        liquido_pagar=Decimal("800000")
    )
    
    # Conceptos de Juan
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina1,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("800000"),
        es_numerico=True
    )
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina1,
        nombre_concepto="Gratificación",
        monto_total=Decimal("200000"),
        es_numerico=True
    )
    
    # Empleado 2: María González (tendrá variación)
    nomina2 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="22222222-2",
        nombre_empleado="María González",
        total_haberes=Decimal("1200000"),
        total_descuentos=Decimal("240000"),
        liquido_pagar=Decimal("960000")
    )
    
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina2,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("1000000"),
        es_numerico=True
    )
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina2,
        nombre_concepto="Bono Productividad",
        monto_total=Decimal("200000"),
        es_numerico=True
    )
    
    # Empleado 3: Pedro Rodríguez (incorporación en feb, debería continuar en mar)
    nomina3 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="33333333-3",
        nombre_empleado="Pedro Rodríguez",
        total_haberes=Decimal("900000"),
        total_descuentos=Decimal("180000"),
        liquido_pagar=Decimal("720000")
    )
    
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina3,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("900000"),
        es_numerico=True
    )
    
    # Movimiento de incorporación de Pedro
    MovimientoPersonal.objects.create(
        nomina_consolidada=nomina3,
        tipo_movimiento='ingreso',
        fecha_movimiento=date(2024, 2, 1),
        observaciones='Incorporación febrero'
    )
    
    print(f"📋 Creados 3 empleados para período anterior (Feb 2024)")

def crear_nomina_consolidada_actual(cierre):
    """
    Crea datos consolidados para el período actual (marzo) con diferencias
    """
    # Empleado 1: Juan Pérez (sin cambios)
    nomina1 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="11111111-1",
        nombre_empleado="Juan Pérez",
        total_haberes=Decimal("1000000"),
        total_descuentos=Decimal("200000"),
        liquido_pagar=Decimal("800000")
    )
    
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina1,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("800000"),
        es_numerico=True
    )
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina1,
        nombre_concepto="Gratificación",
        monto_total=Decimal("200000"),
        es_numerico=True
    )
    
    # Empleado 2: María González (VARIACIÓN >30% en Bono Productividad)
    nomina2 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="22222222-2",
        nombre_empleado="María González",
        total_haberes=Decimal("1400000"),  # Aumentó
        total_descuentos=Decimal("280000"),
        liquido_pagar=Decimal("1120000")
    )
    
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina2,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("1000000"),  # Igual
        es_numerico=True
    )
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina2,
        nombre_concepto="Bono Productividad",
        monto_total=Decimal("400000"),  # Era 200K, ahora 400K = 100% de variación
        es_numerico=True
    )
    
    # CONCEPTO NUEVO: Asignación Especial para María
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina2,
        nombre_concepto="Asignación Especial",
        monto_total=Decimal("100000"),
        es_numerico=True
    )
    
    # Empleado 4: Ana Martínez (EMPLEADO NUEVO sin incorporación documentada)
    nomina4 = NominaConsolidada.objects.create(
        cierre=cierre,
        rut_empleado="44444444-4",
        nombre_empleado="Ana Martínez",
        total_haberes=Decimal("850000"),
        total_descuentos=Decimal("170000"),
        liquido_pagar=Decimal("680000")
    )
    
    ConceptoConsolidado.objects.create(
        nomina_consolidada=nomina4,
        nombre_concepto="Sueldo Base",
        monto_total=Decimal("850000"),
        es_numerico=True
    )
    
    # EMPLEADO 3 (Pedro) NO APARECE EN MARZO = debería ingresar pero no está
    
    print(f"📋 Creados datos para período actual (Mar 2024) con variaciones detectables")

def probar_deteccion_incidencias():
    """
    Prueba el sistema de detección de incidencias
    """
    print("\n🔍 Probando detección de incidencias...")
    
    # Obtener cierres
    cierre_actual = CierreNomina.objects.filter(periodo=date(2024, 3, 1)).first()
    
    if not cierre_actual:
        print("❌ No se encontró cierre actual")
        return
    
    # Verificar que puede generar incidencias
    if not cierre_actual.puede_generar_incidencias():
        print(f"❌ Cierre no puede generar incidencias. Estado: {cierre_actual.estado_consolidacion}")
        return
    
    # Detectar incidencias
    try:
        incidencias = detectar_incidencias_consolidadas(cierre_actual)
        
        print(f"✅ Detectadas {len(incidencias)} incidencias:")
        
        for i, incidencia in enumerate(incidencias, 1):
            print(f"\n{i}. {incidencia.tipo_incidencia}")
            print(f"   Empleado: {incidencia.rut_empleado}")
            print(f"   Descripción: {incidencia.descripcion}")
            print(f"   Prioridad: {incidencia.prioridad}")
            if incidencia.concepto_afectado:
                print(f"   Concepto: {incidencia.concepto_afectado}")
            if incidencia.valor_libro and incidencia.valor_novedades:
                print(f"   Valores: {incidencia.valor_libro} vs {incidencia.valor_novedades}")
        
        # Guardar incidencias para probar
        print(f"\n💾 Guardando {len(incidencias)} incidencias...")
        for incidencia in incidencias:
            incidencia.save()
        
        print("✅ Incidencias guardadas exitosamente")
        
        # Actualizar estado del cierre
        cierre_actual.estado_incidencias = 'incidencias_generadas'
        cierre_actual.total_incidencias = len(incidencias)
        cierre_actual.save(update_fields=['estado_incidencias', 'total_incidencias'])
        
        print(f"✅ Estado del cierre actualizado: {cierre_actual.estado_incidencias}")
        
    except Exception as e:
        print(f"❌ Error detectando incidencias: {e}")
        import traceback
        traceback.print_exc()

def probar_consulta_incidencias():
    """
    Prueba la consulta de incidencias generadas
    """
    print("\n📊 Consultando incidencias generadas...")
    
    cierre_actual = CierreNomina.objects.filter(periodo=date(2024, 3, 1)).first()
    if not cierre_actual:
        return
    
    incidencias = IncidenciaCierre.objects.filter(cierre=cierre_actual)
    
    print(f"Total incidencias: {incidencias.count()}")
    
    # Resumen por tipo
    tipos = {}
    for incidencia in incidencias:
        tipo = incidencia.tipo_incidencia
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    print("\nPor tipo:")
    for tipo, cantidad in tipos.items():
        print(f"  {tipo}: {cantidad}")
    
    # Resumen por prioridad
    prioridades = {}
    for incidencia in incidencias:
        prioridad = incidencia.prioridad
        prioridades[prioridad] = prioridades.get(prioridad, 0) + 1
    
    print("\nPor prioridad:")
    for prioridad, cantidad in prioridades.items():
        print(f"  {prioridad}: {cantidad}")

def limpiar_datos_prueba():
    """
    Limpia los datos de prueba
    """
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar incidencias
        IncidenciaCierre.objects.filter(
            cierre__cliente__nombre="Empresa Test Incidencias"
        ).delete()
        
        # Eliminar datos consolidados
        NominaConsolidada.objects.filter(
            cierre__cliente__nombre="Empresa Test Incidencias"
        ).delete()
        
        # Eliminar cierres
        CierreNomina.objects.filter(
            cliente__nombre="Empresa Test Incidencias"
        ).delete()
        
        # Eliminar cliente
        Cliente.objects.filter(
            nombre="Empresa Test Incidencias"
        ).delete()
        
        print("✅ Datos de prueba eliminados")
        
    except Exception as e:
        print(f"❌ Error limpiando datos: {e}")

def main():
    """
    Función principal del test
    """
    print("🚀 Iniciando test del sistema de incidencias consolidadas\n")
    
    # Limpiar datos previos
    limpiar_datos_prueba()
    
    try:
        # Crear datos de prueba
        cierre_anterior, cierre_actual = crear_datos_prueba()
        
        # Probar detección
        probar_deteccion_incidencias()
        
        # Probar consulta
        probar_consulta_incidencias()
        
        print("\n✅ Test completado exitosamente")
        
        # Preguntar si limpiar datos
        respuesta = input("\n¿Desea limpiar los datos de prueba? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            limpiar_datos_prueba()
        
    except Exception as e:
        print(f"\n❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
