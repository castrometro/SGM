#!/usr/bin/env python
"""
Diagnóstico de Estados de Cierre Nómina
=====================================

Este script diagnostica los problemas de estado cruzados en el sistema de cierres de nómina.

PROBLEMAS IDENTIFICADOS:
1. Estado 'estado' del CierreNomina se actualiza automáticamente
2. Estado 'estado_incidencias' se modifica por procesos que no tienen que ver con incidencias
3. Estado 'estado_consolidacion' se superpone con otros estados
4. Múltiples callbacks y actualizaciones automáticas pueden crear conflictos

ANÁLISIS:
- actualizarEstadoCierreNomina() se llama desde VerificadorDatosSection cuando hay 0 discrepancias
- Los archivos también pueden actualizar estados via onActualizarEstado callbacks
- Los estados de incidencias se pueden ver afectados por el flujo de verificación
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
django.setup()

from nomina.models import CierreNomina

def diagnosticar_estados():
    print("🔍 DIAGNÓSTICO DE ESTADOS DE CIERRE NÓMINA")
    print("=" * 50)
    
    # Obtener todos los cierres activos
    cierres = CierreNomina.objects.all().order_by('-created_at')
    
    for cierre in cierres[:10]:  # Solo los últimos 10
        print(f"\n📋 CIERRE: {cierre.cliente.nombre} - {cierre.periodo}")
        print(f"   Estado Principal: {cierre.estado}")
        print(f"   Estado Incidencias: {cierre.estado_incidencias}")
        print(f"   Estado Consolidación: {cierre.estado_consolidacion}")
        print(f"   Puede Consolidar: {cierre.puede_consolidar}")
        
        # Verificar archivos
        archivos_estado = cierre._verificar_archivos_listos()
        print(f"   Archivos Completos: {archivos_estado['todos_listos']}")
        if archivos_estado['archivos_faltantes']:
            print(f"   ⚠️  Faltantes: {', '.join(archivos_estado['archivos_faltantes'])}")
        
        # Verificar si hay discrepancias
        try:
            from nomina.models import DiscrepanciaCierre
            discrepancias = DiscrepanciaCierre.objects.filter(cierre=cierre).count()
            print(f"   Discrepancias: {discrepancias}")
        except Exception as e:
            print(f"   Discrepancias: Error - {e}")
        
        # Verificar incidencias
        try:
            from nomina.models import IncidenciaCierre
            incidencias = IncidenciaCierre.objects.filter(cierre=cierre).count()
            print(f"   Incidencias: {incidencias}")
        except Exception as e:
            print(f"   Incidencias: Error - {e}")
        
        # Detectar estados inconsistentes
        inconsistencias = []
        
        if cierre.estado == 'verificado_sin_discrepancias' and cierre.estado_incidencias != 'pendiente':
            inconsistencias.append("Estado incidencias no coincide con verificación sin discrepancias")
        
        if cierre.estado == 'datos_consolidados' and cierre.estado_consolidacion != 'consolidado':
            inconsistencias.append("Estado consolidación no coincide con datos consolidados")
        
        if cierre.puede_consolidar and cierre.estado != 'verificado_sin_discrepancias':
            inconsistencias.append("Puede consolidar pero estado no es verificado_sin_discrepancias")
        
        if inconsistencias:
            print(f"   🚨 INCONSISTENCIAS:")
            for inconsistencia in inconsistencias:
                print(f"      - {inconsistencia}")

def mostrar_flujos_problematicos():
    print("\n\n🔄 FLUJOS PROBLEMÁTICOS IDENTIFICADOS")
    print("=" * 50)
    
    print("""
1. FLUJO DE VERIFICACIÓN DE DATOS:
   - VerificadorDatosSection detecta 0 discrepancias
   - Llama actualizarEstadoCierreNomina()
   - Backend cambia estado a siguiente fase
   - ❌ PROBLEMA: También puede cambiar estado_incidencias sin razón
   
2. FLUJO DE ACTUALIZACIÓN DE ARCHIVOS:
   - Archivos completados activan onActualizarEstado
   - Backend recalcula estados automáticamente
   - ❌ PROBLEMA: Puede interferir con estados manuales
   
3. FLUJO DE CONSOLIDACIÓN:
   - Botón "Consolidar Datos" aparece con verificado_sin_discrepancias
   - ❌ PROBLEMA: consolidar-datos endpoint no existe (404)
   - Estado consolidación separado del estado principal
   
4. FLUJO DE INCIDENCIAS:
   - Estado incidencias se modifica por verificación
   - ❌ PROBLEMA: No tiene relación directa con generación de incidencias
   """)

def sugerir_soluciones():
    print("\n\n💡 SOLUCIONES SUGERIDAS")
    print("=" * 50)
    
    print("""
1. SEPARAR RESPONSABILIDADES:
   - estado: Solo para flujo de archivos y verificación
   - estado_incidencias: Solo para sistema de incidencias
   - estado_consolidacion: Solo para consolidación final
   
2. EVITAR AUTO-ACTUALIZACIONES CRUZADAS:
   - actualizar_estado_automatico() no debe tocar estado_incidencias
   - Verificación de discrepancias no debe activar incidencias automáticamente
   
3. IMPLEMENTAR ENDPOINT FALTANTE:
   - Crear /api/nomina/cierres/{id}/consolidar-datos/
   - Validar estado prerequisito correctamente
   
4. DEFINIR TRANSICIONES CLARAS:
   - Estado inicial → Archivos → Verificación → Consolidación
   - Incidencias como flujo paralelo independiente
   """)

if __name__ == "__main__":
    diagnosticar_estados()
    mostrar_flujos_problematicos()
    sugerir_soluciones()
