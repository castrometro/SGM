"""
🔍 SCRIPT DE PRUEBA: Sistema de Incidencias Consolidadas Completo

Este script simula el flujo completo del sistema de incidencias:
1. Consolidar datos
2. Generar incidencias
3. Finalizar cierre (si no hay incidencias)
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from nomina.models import CierreNomina, IncidenciaCierre
from nomina.utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidadas_task
from nomina.tasks import consolidar_datos_nomina_task

def probar_flujo_completo():
    """
    Prueba el flujo completo del sistema de incidencias
    """
    print("🔍 PRUEBA COMPLETA: Sistema de Incidencias Consolidadas")
    print("=" * 60)
    
    # 1. Buscar cierre consolidado para probar
    cierre_consolidado = CierreNomina.objects.filter(
        estado='datos_consolidados'
    ).order_by('-periodo').first()
    
    if not cierre_consolidado:
        print("❌ No se encontraron cierres consolidados para probar")
        
        # Buscar cierre sin consolidar y consolidarlo
        cierre_verificado = CierreNomina.objects.filter(
            estado='verificado_sin_discrepancias'
        ).order_by('-periodo').first()
        
        if cierre_verificado:
            print(f"🔄 Consolidando datos para cierre {cierre_verificado.id}...")
            resultado_consolidacion = consolidar_datos_nomina_task.delay(cierre_verificado.id)
            print(f"✅ Consolidación iniciada: task_id={resultado_consolidacion.id}")
            return
        else:
            print("❌ No se encontraron cierres en estado 'verificado_sin_discrepancias'")
            return
    
    print(f"🎯 Probando con cierre: {cierre_consolidado}")
    print(f"   Cliente: {cierre_consolidado.cliente.nombre}")
    print(f"   Periodo: {cierre_consolidado.periodo}")
    print(f"   Estado: {cierre_consolidado.estado}")
    print()
    
    # 2. Verificar datos consolidados
    empleados_consolidados = cierre_consolidado.nomina_consolidada.count()
    print(f"📊 Datos consolidados:")
    print(f"   - Empleados: {empleados_consolidados}")
    print(f"   - Headers-valores: {sum(nc.headervaloreempleado_set.count() for nc in cierre_consolidado.nomina_consolidada.all())}")
    print(f"   - Movimientos: {sum(nc.movimientopersonal_set.count() for nc in cierre_consolidado.nomina_consolidada.all())}")
    print(f"   - Conceptos: {sum(nc.conceptoconsolidado_set.count() for nc in cierre_consolidado.nomina_consolidada.all())}")
    print()
    
    # 3. Generar incidencias
    print("🔍 Generando incidencias...")
    incidencias_antes = cierre_consolidado.incidencias.count()
    print(f"   Incidencias antes: {incidencias_antes}")
    
    try:
        resultado_incidencias = generar_incidencias_consolidadas_task(cierre_consolidado.id)
        
        if resultado_incidencias['success']:
            print(f"✅ Incidencias generadas exitosamente:")
            print(f"   - Total: {resultado_incidencias['total_incidencias']}")
            print(f"   - Estado cierre: {resultado_incidencias['estado_cierre']}")
            print(f"   - Estado incidencias: {resultado_incidencias['estado_incidencias']}")
            print(f"   - Mensaje: {resultado_incidencias['mensaje']}")
            print(f"   - Siguiente acción: {resultado_incidencias['siguiente_accion']}")
            
            if resultado_incidencias['tipos_detectados']:
                print(f"   - Tipos detectados: {resultado_incidencias['tipos_detectados']}")
            
            # 4. Mostrar incidencias detectadas
            if resultado_incidencias['total_incidencias'] > 0:
                print(f"\n📋 Detalles de incidencias detectadas:")
                incidencias = cierre_consolidado.incidencias.all()[:5]  # Mostrar las primeras 5
                for inc in incidencias:
                    print(f"   🔴 {inc.get_tipo_incidencia_display()}")
                    print(f"      RUT: {inc.rut_empleado}")
                    print(f"      Descripción: {inc.descripcion}")
                    print(f"      Prioridad: {inc.get_prioridad_display()}")
                    if inc.impacto_monetario:
                        print(f"      Impacto: ${inc.impacto_monetario:,.0f}")
                    print()
                
                print("🔧 Sistema listo para resolución colaborativa de incidencias")
                
            else:
                print("\n🎉 No se detectaron incidencias!")
                print(f"   - Cierre en estado: {cierre_consolidado.estado}")
                if resultado_incidencias.get('puede_finalizar'):
                    print("   - ✅ Listo para finalizar con botón 'Generar Informes y Finalizar Cierre'")
                
        else:
            print(f"❌ Error generando incidencias: {resultado_incidencias['error']}")
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Prueba completada")

if __name__ == "__main__":
    probar_flujo_completo()
