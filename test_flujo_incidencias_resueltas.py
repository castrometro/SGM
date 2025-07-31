#!/usr/bin/env python3
"""
Test para verificar el flujo cuando el cierre está en estado 'incidencias_resueltas'
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.nomina.models import CierreNomina

def verificar_flujo_incidencias_resueltas():
    """Verificar el flujo de cierres en estado incidencias_resueltas"""
    
    print("🔍 VERIFICANDO FLUJO DE ESTADO 'INCIDENCIAS_RESUELTAS':")
    print("=" * 60)
    
    # Buscar cierres en estado incidencias_resueltas
    cierres_resueltas = CierreNomina.objects.filter(estado='incidencias_resueltas')
    
    print(f"📊 Cierres en estado 'incidencias_resueltas': {cierres_resueltas.count()}")
    
    if cierres_resueltas.count() == 0:
        print("⚠️ No hay cierres en estado 'incidencias_resueltas' para probar")
        print("🔧 Creando un escenario de prueba...")
        
        # Buscar un cierre que esté en con_incidencias para simular el flujo
        cierre_con_incidencias = CierreNomina.objects.filter(estado='con_incidencias').first()
        
        if cierre_con_incidencias:
            print(f"📋 Encontrado cierre {cierre_con_incidencias.id} en estado 'con_incidencias'")
            print(f"🏢 Cliente: {cierre_con_incidencias.cliente.nombre}")
            print(f"📅 Periodo: {cierre_con_incidencias.periodo}")
            print(f"📈 Total incidencias: {cierre_con_incidencias.total_incidencias}")
            
            print("\n🎯 ESCENARIO ESPERADO CUANDO SE PONGA EN 'incidencias_resueltas':")
            print("✅ Frontend debería mostrar:")
            print("   - Sección de Incidencias: DESBLOQUEADA")
            print("   - Botón 'Finalizar Cierre': VISIBLE")
            print("   - Sección Archivos Talana: BLOQUEADA")
            print("   - Sección Archivos Analista: BLOQUEADA") 
            print("   - Sección Verificador: BLOQUEADA")
            
            print("\n🔧 Para probar manualmente:")
            print(f"   1. Ve al cierre {cierre_con_incidencias.id}")
            print("   2. Resuelve todas las incidencias")
            print("   3. El estado debería cambiar a 'incidencias_resueltas'")
            print("   4. Solo la sección de incidencias debería estar desbloqueada")
            print("   5. Debería aparecer el botón 'Finalizar Cierre'")
        else:
            print("❌ No hay cierres en estados apropiados para simular")
    
    for cierre in cierres_resueltas:
        print(f"\n🏢 Cliente: {cierre.cliente.nombre}")
        print(f"📅 Periodo: {cierre.periodo}")
        print(f"📌 Estado principal: {cierre.estado}")
        print(f"🔄 Estado incidencias: {cierre.estado_incidencias}")
        print(f"📈 Total incidencias: {cierre.total_incidencias}")
        print(f"⏰ Última revisión: {cierre.fecha_ultima_revision}")
        
        print("\n✅ COMPORTAMIENTO ESPERADO:")
        print("   - Solo sección de incidencias desbloqueada")
        print("   - Botón 'Finalizar Cierre' visible")
        print("   - Todas las demás secciones bloqueadas")
        
        # Verificar que está listo para finalizar
        if cierre.estado_incidencias in ['resueltas', 'pendiente']:
            print("   🎯 ESTADO CORRECTO: Listo para finalización")
        else:
            print(f"   ⚠️ ESTADO INESPERADO: {cierre.estado_incidencias}")
    
    print("\n📋 RESUMEN DEL CAMBIO IMPLEMENTADO:")
    print("- Modificado CierreProgresoNomina.jsx")
    print("- Agregado caso específico para estado 'incidencias_resueltas'")
    print("- Solo la sección 'incidencias' permanece desbloqueada")
    print("- Permite acceso al botón 'Finalizar Cierre'")
    print("- Bloquea modificaciones en otras secciones")

def verificar_estructura_estados():
    """Verificar la distribución de estados en el sistema"""
    
    print("\n\n🔍 DISTRIBUCIÓN DE ESTADOS EN EL SISTEMA:")
    print("=" * 50)
    
    from django.db.models import Count
    
    # Contar por estado principal
    estados_count = CierreNomina.objects.values('estado').annotate(
        count=Count('id')
    ).order_by('estado')
    
    print("📊 Estados principales:")
    for estado in estados_count:
        print(f"   {estado['estado']}: {estado['count']} cierres")
    
    # Contar por estado de incidencias
    estados_inc_count = CierreNomina.objects.values('estado_incidencias').annotate(
        count=Count('id')
    ).order_by('estado_incidencias')
    
    print("\n🎯 Estados de incidencias:")
    for estado in estados_inc_count:
        estado_inc = estado['estado_incidencias'] or 'NULL'
        print(f"   {estado_inc}: {estado['count']} cierres")

if __name__ == "__main__":
    try:
        verificar_flujo_incidencias_resueltas()
        verificar_estructura_estados()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
