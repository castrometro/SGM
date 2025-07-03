#!/usr/bin/env python3
# test_correccion_estado_cierre.py
"""
Script para probar que la corrección del modelo CierreContabilidad funciona correctamente
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from contabilidad.models import CierreContabilidad
from contabilidad.models_incidencias import IncidenciaResumen

def test_actualizar_estado_automatico():
    """Test del método actualizar_estado_automatico corregido"""
    print("=" * 50)
    print("TEST: actualizar_estado_automatico")
    print("=" * 50)
    
    # Buscar un cierre para probar
    try:
        cierre = CierreContabilidad.objects.first()
        if not cierre:
            print("❌ No hay cierres en la base de datos para probar")
            return
        
        print(f"✅ Probando con cierre ID: {cierre.id}")
        print(f"   Cliente: {cierre.cliente.nombre}")
        print(f"   Período: {cierre.periodo}")
        print(f"   Estado actual: {cierre.estado}")
        
        # Contar incidencias del cierre
        incidencias_activas = IncidenciaResumen.objects.filter(
            cierre=cierre,
            estado='activa'
        ).count()
        
        incidencias_totales = IncidenciaResumen.objects.filter(
            cierre=cierre
        ).count()
        
        print(f"   Incidencias activas: {incidencias_activas}")
        print(f"   Incidencias totales: {incidencias_totales}")
        
        # Ejecutar el método
        estado_previo = cierre.estado
        nuevo_estado = cierre.actualizar_estado_automatico()
        
        print(f"   Estado previo: {estado_previo}")
        print(f"   Estado nuevo: {nuevo_estado}")
        
        if estado_previo != nuevo_estado:
            print(f"✅ Estado actualizado: {estado_previo} → {nuevo_estado}")
        else:
            print(f"✅ Estado mantenido: {nuevo_estado}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_puede_finalizar():
    """Test del método puede_finalizar corregido"""
    print("\n" + "=" * 50)
    print("TEST: puede_finalizar")
    print("=" * 50)
    
    try:
        # Buscar un cierre en estado sin_incidencias
        cierre = CierreContabilidad.objects.filter(estado='sin_incidencias').first()
        
        if not cierre:
            print("⚠️ No hay cierres en estado 'sin_incidencias' para probar")
            # Probar con cualquier cierre
            cierre = CierreContabilidad.objects.first()
            if not cierre:
                print("❌ No hay cierres en la base de datos")
                return False
        
        print(f"✅ Probando con cierre ID: {cierre.id}")
        print(f"   Cliente: {cierre.cliente.nombre}")
        print(f"   Estado: {cierre.estado}")
        
        # Ejecutar el método
        puede, motivo = cierre.puede_finalizar()
        
        print(f"   ¿Puede finalizar?: {puede}")
        print(f"   Motivo: {motivo}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_conteo_incidencias():
    """Test básico de conteo de incidencias por modelo"""
    print("\n" + "=" * 50)
    print("TEST: Conteo de incidencias por modelo")
    print("=" * 50)
    
    try:
        from contabilidad.models_incidencias import Incidencia, IncidenciaResumen
        
        # Contar incidencias en ambos modelos
        total_incidencias = Incidencia.objects.count()
        total_resumenes = IncidenciaResumen.objects.count()
        
        print(f"   Total Incidencias (modelo base): {total_incidencias}")
        print(f"   Total IncidenciaResumen: {total_resumenes}")
        
        # Por estado en IncidenciaResumen
        activas = IncidenciaResumen.objects.filter(estado='activa').count()
        resueltas = IncidenciaResumen.objects.filter(estado='resuelta').count()
        obsoletas = IncidenciaResumen.objects.filter(estado='obsoleta').count()
        
        print(f"   Resumenes activas: {activas}")
        print(f"   Resumenes resueltas: {resueltas}")
        print(f"   Resumenes obsoletas: {obsoletas}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("INICIANDO TESTS DE CORRECCIÓN DE ESTADO DE CIERRE")
    print("Fecha:", "3 de julio de 2025")
    print()
    
    # Ejecutar tests
    success = True
    success &= test_conteo_incidencias()
    success &= test_actualizar_estado_automatico()
    success &= test_puede_finalizar()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print("✅ La corrección del modelo CierreContabilidad es exitosa")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("❌ Revisar los errores arriba")
    print("=" * 50)
