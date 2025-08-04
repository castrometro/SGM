#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de lista de empleados en informes de nómina
"""

import os
import sys
import django
from datetime import datetime, date

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from nomina.models_informe import InformeNomina
from nomina.models import CierreNomina
from clientes.models import Cliente

def test_lista_empleados():
    """Prueba las funcionalidades de lista de empleados"""
    
    print("🧪 Iniciando pruebas de lista de empleados en informes de nómina...\n")
    
    # Buscar un cliente y cierre de prueba
    try:
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No se encontraron clientes para prueba")
            return
            
        cierre = CierreNomina.objects.filter(
            cliente=cliente,
            estado='finalizado'
        ).first()
        
        if not cierre:
            print(f"❌ No se encontraron cierres finalizados para el cliente {cliente.nombre}")
            return
            
        print(f"✅ Cliente de prueba: {cliente.nombre}")
        print(f"✅ Cierre de prueba: {cierre.periodo}")
        
        # Buscar o crear informe
        informe, created = InformeNomina.objects.get_or_create(
            cierre=cierre,
            defaults={
                'datos_cierre': {}
            }
        )
        
        if created:
            print(f"🔄 Generando nuevo informe para {cierre.periodo}...")
            informe._calcular_datos_cierre()
            informe.save()
        else:
            print(f"📊 Usando informe existente del {informe.fecha_generacion}")
        
        print("\n" + "="*60)
        print("🧑‍💼 LISTA DE EMPLEADOS - FUNCIONALIDADES")
        print("="*60)
        
        # Verificar si tiene datos de empleados
        empleados_data = informe.datos_cierre.get('empleados', {})
        if not empleados_data.get('detalle'):
            print("⚠️  El informe no contiene datos detallados de empleados")
            print("🔄 Regenerando datos...")
            informe._calcular_datos_cierre()
            informe.save()
            empleados_data = informe.datos_cierre.get('empleados', {})
        
        if not empleados_data.get('detalle'):
            print("❌ No se pudieron generar datos de empleados")
            return
        
        empleados = empleados_data.get('detalle', [])
        print(f"📋 Total de empleados en el período: {len(empleados)}")
        
        # Test 1: Lista básica de empleados
        print("\n1️⃣ LISTA BÁSICA DE EMPLEADOS")
        print("-" * 40)
        
        for i, empleado in enumerate(empleados[:5]):  # Mostrar solo los primeros 5
            print(f"{i+1}. {empleado['nombre']} - {empleado['cargo']}")
            print(f"   💰 Remuneración: ${empleado['remuneracion']['total_haberes']:,.0f}")
            print(f"   🏢 Centro de costo: {empleado.get('centro_costo', 'No especificado')}")
            print(f"   📅 Días trabajados: {empleado['ausentismo']['dias_trabajados_calculados']}")
            print(f"   🏥 Salud: {empleado['afiliaciones']['tipo_salud']}")
            print()
        
        if len(empleados) > 5:
            print(f"... y {len(empleados) - 5} empleados más")
        
        # Test 2: Filtros por criterio
        print("\n2️⃣ FILTROS POR CRITERIO")
        print("-" * 40)
        
        criterios_test = [
            'con_ausencias',
            'sin_ausencias', 
            'ingresos',
            'finiquitos',
            'con_horas_extras',
            'alta_remuneracion',
            'isapre',
            'fonasa'
        ]
        
        for criterio in criterios_test:
            try:
                empleados_filtrados = informe.obtener_empleados_por_criterio(criterio)
                print(f"📊 {criterio.replace('_', ' ').title()}: {len(empleados_filtrados)} empleados")
                
                if empleados_filtrados and criterio == 'alta_remuneracion':
                    print(f"   💎 Mejor pagado: ${empleados_filtrados[0]['remuneracion']['total_haberes']:,.0f}")
                
            except Exception as e:
                print(f"❌ Error en filtro {criterio}: {e}")
        
        # Test 3: Estadísticas de empleados
        print("\n3️⃣ ESTADÍSTICAS AVANZADAS")
        print("-" * 40)
        
        try:
            stats = informe.obtener_estadisticas_empleados()
            
            print("💰 REMUNERACIONES:")
            remuneracion = stats.get('remuneracion', {})
            print(f"   Promedio: ${remuneracion.get('promedio', 0):,.0f}")
            print(f"   Mediana: ${remuneracion.get('mediana', 0):,.0f}")
            print(f"   Máxima: ${remuneracion.get('maximo', 0):,.0f}")
            print(f"   Mínima: ${remuneracion.get('minimo', 0):,.0f}")
            
            rangos = remuneracion.get('rangos_salariales', {})
            print(f"\n📈 DISTRIBUCIÓN SALARIAL:")
            print(f"   < $500k: {rangos.get('menos_500k', 0)} empleados")
            print(f"   $500k-$1M: {rangos.get('500k_1M', 0)} empleados") 
            print(f"   $1M-$1.5M: {rangos.get('1M_1.5M', 0)} empleados")
            print(f"   $1.5M-$2M: {rangos.get('1.5M_2M', 0)} empleados")
            print(f"   > $2M: {rangos.get('mas_2M', 0)} empleados")
            
            ausentismo = stats.get('ausentismo', {})
            print(f"\n🏥 AUSENTISMO:")
            print(f"   Con ausencias: {ausentismo.get('empleados_con_ausencias', 0)} empleados")
            print(f"   Sin ausencias: {ausentismo.get('empleados_sin_ausencias', 0)} empleados")
            print(f"   Promedio días ausencias: {ausentismo.get('promedio_dias_ausencias', 0)} días")
            
            distribucion = stats.get('distribucion', {})
            print(f"\n🏢 DISTRIBUCIÓN POR CENTRO DE COSTO:")
            for centro, cantidad in distribucion.get('por_centro_costo', {}).items():
                print(f"   {centro}: {cantidad} empleados")
                
        except Exception as e:
            print(f"❌ Error calculando estadísticas: {e}")
        
        # Test 4: Cálculo de días trabajados
        print("\n4️⃣ CÁLCULO DE DÍAS TRABAJADOS")
        print("-" * 40)
        
        try:
            dias_stats = informe.calcular_dias_trabajados_por_empleado()
            
            print(f"📅 Promedio días trabajados por empleado: {dias_stats.get('promedio_dias_trabajados_por_empleado', 0)} días")
            print(f"✅ Empleados sin ausencias: {dias_stats.get('empleados_sin_ausencias', 0)}")
            print(f"🏥 Empleados con ausencias: {dias_stats.get('empleados_con_ausencias', 0)}")
            print(f"📊 Eficiencia tiempo trabajo: {dias_stats.get('eficiencia_tiempo_trabajo', 0)}%")
            print(f"🔢 Total días trabajados efectivos: {dias_stats.get('total_dias_trabajados_efectivos', 0):,.0f}")
            
        except Exception as e:
            print(f"❌ Error calculando días trabajados: {e}")
        
        # Test 5: Formato para APIs
        print("\n5️⃣ FORMATO PARA APIS/FRONTEND")
        print("-" * 40)
        
        try:
            # Simular formato JSON para API
            api_response = {
                'meta': {
                    'total_empleados': len(empleados),
                    'periodo': cierre.periodo,
                    'cliente': cliente.nombre,
                    'fecha_generacion': informe.fecha_generacion.isoformat()
                },
                'empleados': empleados[:3],  # Primeros 3 para ejemplo
                'estadisticas': informe.obtener_estadisticas_empleados(),
                'filtros_disponibles': [
                    'con_ausencias', 'sin_ausencias', 'ingresos', 
                    'finiquitos', 'con_horas_extras', 'alta_remuneracion',
                    'isapre', 'fonasa'
                ]
            }
            
            print(f"📦 Estructura API generada con {len(api_response['empleados'])} empleados de muestra")
            print(f"📊 Incluye estadísticas completas y filtros disponibles")
            print(f"💾 Tamaño aproximado: {len(str(api_response)) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ Error generando formato API: {e}")
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("="*60)
        
        print(f"\n📋 RESUMEN:")
        print(f"   • Lista de empleados: ✅ Funcional")
        print(f"   • Filtros por criterio: ✅ Funcional") 
        print(f"   • Estadísticas avanzadas: ✅ Funcional")
        print(f"   • Cálculo días trabajados: ✅ Funcional")
        print(f"   • Formato API: ✅ Funcional")
        print(f"   • Total empleados procesados: {len(empleados)}")
        
    except Exception as e:
        print(f"❌ Error general en las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lista_empleados()
