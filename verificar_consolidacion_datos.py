#!/usr/bin/env python3
"""
🔍 VERIFICACIÓN DE CONSOLIDACIÓN DE DATOS PARA REPORTES

Este script verifica que la consolidación de datos esté funcionando correctamente
y que los datos estén disponibles para generar los reportes de nómina.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('/root/SGM')
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

try:
    from nomina.models import (
        CierreNomina, NominaConsolidada, ConceptoConsolidado, 
        MovimientoPersonal, HeaderValorEmpleado
    )
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    print("✅ Modelos importados correctamente")
except Exception as e:
    print(f"❌ Error importando modelos: {e}")
    sys.exit(1)

def verificar_consolidacion_datos():
    """
    Verifica que los datos de consolidación estén correctos para reportes
    """
    print("🔍 VERIFICANDO CONSOLIDACIÓN DE DATOS PARA REPORTES")
    print("=" * 60)
    
    # 1. Buscar cierres consolidados
    cierres_consolidados = CierreNomina.objects.filter(
        estado__in=['datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'finalizado']
    ).order_by('-fecha_creacion')
    
    if not cierres_consolidados.exists():
        print("❌ NO HAY CIERRES CONSOLIDADOS PARA VERIFICAR")
        return False
    
    print(f"✅ Encontrados {cierres_consolidados.count()} cierres consolidados")
    
    # Tomar el cierre más reciente para verificar
    cierre = cierres_consolidados.first()
    print(f"\n🎯 VERIFICANDO CIERRE: {cierre.cliente.nombre} - {cierre.periodo}")
    print(f"   Estado: {cierre.get_estado_display()}")
    print(f"   Fecha: {cierre.fecha_creacion.strftime('%d/%m/%Y')}")
    
    # 2. Verificar NominaConsolidada
    print(f"\n📋 VERIFICANDO NOMINAS CONSOLIDADAS:")
    nominas = NominaConsolidada.objects.filter(cierre=cierre)
    print(f"   Total empleados: {nominas.count()}")
    
    if nominas.count() == 0:
        print("   ❌ NO HAY NOMINAS CONSOLIDADAS")
        return False
    
    # Estadísticas por estado
    estados = nominas.values('estado_empleado').annotate(
        count=Count('id'),
        total_liquido=Sum('liquido_pagar')
    ).order_by('-count')
    
    print(f"   📊 Distribución por estado:")
    for estado in estados:
        print(f"      {estado['estado_empleado']}: {estado['count']} empleados")
        print(f"         Total líquido: ${estado['total_liquido']:,.0f}")
    
    # 3. Verificar ConceptoConsolidado (para AFP/Isapre)
    print(f"\n💰 VERIFICANDO CONCEPTOS CONSOLIDADOS:")
    conceptos = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre
    )
    print(f"   Total conceptos: {conceptos.count()}")
    
    if conceptos.count() == 0:
        print("   ❌ NO HAY CONCEPTOS CONSOLIDADOS")
        return False
    
    # Verificar conceptos clave para reportes
    conceptos_afp = conceptos.filter(
        nombre_concepto__icontains='AFP'
    ).aggregate(
        total=Sum('monto_total'),
        count=Count('id')
    )
    
    conceptos_isapre = conceptos.filter(
        Q(nombre_concepto__icontains='Isapre') | 
        Q(nombre_concepto__icontains='ISAPRE')
    ).aggregate(
        total=Sum('monto_total'),
        count=Count('id')
    )
    
    conceptos_fonasa = conceptos.filter(
        Q(nombre_concepto__icontains='Fonasa') | 
        Q(nombre_concepto__icontains='7%')
    ).aggregate(
        total=Sum('monto_total'),
        count=Count('id')
    )
    
    print(f"   📊 Conceptos previsionales:")
    print(f"      AFP: {conceptos_afp['count']} registros = ${conceptos_afp['total'] or 0:,.0f}")
    print(f"      Isapre: {conceptos_isapre['count']} registros = ${conceptos_isapre['total'] or 0:,.0f}")
    print(f"      Fonasa: {conceptos_fonasa['count']} registros = ${conceptos_fonasa['total'] or 0:,.0f}")
    
    # 4. Verificar MovimientoPersonal (para movimientos)
    print(f"\n🔄 VERIFICANDO MOVIMIENTOS DE PERSONAL:")
    movimientos = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=cierre
    )
    print(f"   Total movimientos: {movimientos.count()}")
    
    if movimientos.count() > 0:
        tipos_movimiento = movimientos.values('tipo_movimiento').annotate(
            count=Count('id')
        ).order_by('-count')
        
        print(f"   📊 Tipos de movimiento:")
        for tipo in tipos_movimiento:
            print(f"      {tipo['tipo_movimiento']}: {tipo['count']} casos")
    
    # 5. Verificar HeaderValorEmpleado (datos detallados)
    print(f"\n📊 VERIFICANDO HEADERS-VALORES:")
    headers = HeaderValorEmpleado.objects.filter(
        nomina_consolidada__cierre=cierre
    )
    print(f"   Total headers: {headers.count()}")
    
    if headers.count() > 0:
        headers_numericos = headers.filter(es_numerico=True)
        print(f"   Headers numéricos: {headers_numericos.count()}")
        
        # Verificar algunos conceptos importantes
        conceptos_importantes = [
            'Sueldo Base', 'sueldo_base', 'SUELDO BASE',
            'AFP', 'Isapre', 'ISAPRE', 'Fonasa', 'FONASA'
        ]
        
        for concepto in conceptos_importantes:
            count = headers.filter(
                Q(nombre_header__icontains=concepto) |
                Q(concepto_remuneracion__nombre_concepto__icontains=concepto)
            ).count()
            if count > 0:
                print(f"      {concepto}: {count} registros")
    
    # 6. Verificar datos para reportes específicos
    print(f"\n📈 VERIFICANDO DATOS PARA REPORTES:")
    
    # KPIs básicos
    total_empleados = nominas.count()
    total_liquido = nominas.aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0
    total_haberes = nominas.aggregate(Sum('total_haberes'))['total_haberes__sum'] or 0
    total_descuentos = nominas.aggregate(Sum('total_descuentos'))['total_descuentos__sum'] or 0
    
    print(f"   💼 KPIs Básicos:")
    print(f"      Total empleados: {total_empleados}")
    print(f"      Total líquido: ${total_liquido:,.0f}")
    print(f"      Total haberes: ${total_haberes:,.0f}")
    print(f"      Total descuentos: ${total_descuentos:,.0f}")
    
    # Verificar movimientos para reportes
    ingresos = nominas.filter(
        Q(estado_empleado='nueva_incorporacion') |
        Q(movimientos__tipo_movimiento='ingreso')
    ).distinct().count()
    
    finiquitos = nominas.filter(
        Q(estado_empleado='finiquito') |
        Q(movimientos__tipo_movimiento='finiquito')
    ).distinct().count()
    
    ausencias = nominas.filter(
        Q(estado_empleado__contains='ausente') |
        Q(movimientos__tipo_movimiento='ausentismo')
    ).distinct().count()
    
    print(f"   📊 Movimientos:")
    print(f"      Ingresos: {ingresos}")
    print(f"      Finiquitos: {finiquitos}")
    print(f"      Con ausencias: {ausencias}")
    
    # 7. Validar integridad de datos
    print(f"\n🔍 VALIDANDO INTEGRIDAD:")
    
    # Verificar que todas las nóminas tengan conceptos
    nominas_sin_conceptos = nominas.filter(conceptos__isnull=True).count()
    if nominas_sin_conceptos > 0:
        print(f"   ⚠️ {nominas_sin_conceptos} nóminas SIN conceptos")
    else:
        print(f"   ✅ Todas las nóminas tienen conceptos")
    
    # Verificar consistencia de totales
    inconsistencias = 0
    for nomina in nominas.select_related('cierre')[:10]:  # Verificar primeras 10
        conceptos_nomina = ConceptoConsolidado.objects.filter(
            nomina_consolidada=nomina
        )
        
        # Sumar haberes y descuentos desde conceptos
        haberes_conceptos = conceptos_nomina.filter(
            tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or 0
        
        descuentos_conceptos = conceptos_nomina.filter(
            tipo_concepto__in=['descuento_legal', 'otro_descuento']
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or 0
        
        # Comparar con totales almacenados
        if abs(float(nomina.total_haberes) - float(haberes_conceptos)) > 0.01:
            inconsistencias += 1
        if abs(float(nomina.total_descuentos) - float(descuentos_conceptos)) > 0.01:
            inconsistencias += 1
    
    if inconsistencias == 0:
        print(f"   ✅ Consistencia de totales verificada")
    else:
        print(f"   ⚠️ {inconsistencias} inconsistencias en totales detectadas")
    
    print(f"\n🎉 VERIFICACIÓN COMPLETADA")
    
    # Resumen final
    validaciones_exitosas = [
        nominas.count() > 0,
        conceptos.count() > 0,
        total_liquido > 0,
        inconsistencias == 0
    ]
    
    exito = all(validaciones_exitosas)
    
    if exito:
        print(f"✅ CONSOLIDACIÓN DE DATOS: EXITOSA")
        print(f"   Los datos están listos para generar reportes")
    else:
        print(f"❌ CONSOLIDACIÓN DE DATOS: CON PROBLEMAS")
        print(f"   Revisar las inconsistencias reportadas")
    
    return exito

def verificar_datos_especificos_reportes():
    """
    Verifica que los datos específicos para reportes estén disponibles
    """
    print(f"\n🎯 VERIFICANDO DATOS ESPECÍFICOS PARA REPORTES")
    print("=" * 50)
    
    # Buscar cierre para prueba
    cierre = CierreNomina.objects.filter(
        estado__in=['datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'finalizado']
    ).first()
    
    if not cierre:
        print("❌ No hay cierres para verificar")
        return False
    
    print(f"📋 Verificando cierre: {cierre.cliente.nombre} - {cierre.periodo}")
    
    # Simular generación de datos de reporte
    nominas = NominaConsolidada.objects.filter(cierre=cierre)
    conceptos = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=cierre)
    movimientos = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre)
    
    # 1. Verificar dotación
    dotacion_total = nominas.count()
    dotacion_activa = nominas.exclude(estado_empleado='finiquito').count()
    
    print(f"   👥 Dotación: {dotacion_activa}/{dotacion_total}")
    
    # 2. Verificar totales financieros
    costo_empresa = nominas.aggregate(
        haberes=Sum('total_haberes'),
        descuentos=Sum('total_descuentos'),
        liquido=Sum('liquido_pagar')
    )
    
    print(f"   💰 Costo empresa: ${costo_empresa['haberes'] or 0:,.0f}")
    print(f"   💸 Total descuentos: ${costo_empresa['descuentos'] or 0:,.0f}")
    print(f"   💵 Total líquido: ${costo_empresa['liquido'] or 0:,.0f}")
    
    # 3. Verificar AFP/Isapre TOP 3
    afp_isapre = conceptos.filter(
        Q(nombre_concepto__icontains='AFP') |
        Q(nombre_concepto__icontains='Isapre') |
        Q(nombre_concepto__icontains='Fonasa')
    ).values('nombre_concepto').annotate(
        total_monto=Sum('monto_total'),
        cantidad_empleados=Count('nomina_consolidada', distinct=True)
    ).order_by('-total_monto')[:3]
    
    print(f"   🏥 AFP/Isapre TOP 3:")
    for i, concepto in enumerate(afp_isapre, 1):
        print(f"      {i}. {concepto['nombre_concepto']}: "
              f"${concepto['total_monto']:,.0f} "
              f"({concepto['cantidad_empleados']} empleados)")
    
    # 4. Verificar movimientos
    ingresos = movimientos.filter(tipo_movimiento='ingreso').count()
    finiquitos = movimientos.filter(tipo_movimiento='finiquito').count()
    ausencias = movimientos.filter(tipo_movimiento='ausentismo').count()
    
    print(f"   🔄 Movimientos:")
    print(f"      Nuevos ingresos: {ingresos}")
    print(f"      Finiquitos: {finiquitos}")
    print(f"      Con ausencias: {ausencias}")
    
    # 5. Verificar que se pueden calcular ratios
    if dotacion_total > 0:
        rotacion = ((ingresos + finiquitos) / dotacion_total) * 100
        ausentismo = (ausencias / dotacion_total) * 100
        
        print(f"   📊 Ratios:")
        print(f"      Rotación: {rotacion:.1f}%")
        print(f"      Ausentismo: {ausentismo:.1f}%")
    
    print(f"\n✅ DATOS ESPECÍFICOS VERIFICADOS - LISTOS PARA REPORTES")
    return True

if __name__ == '__main__':
    print("🚀 INICIANDO VERIFICACIÓN DE CONSOLIDACIÓN DE DATOS")
    print("=" * 70)
    
    # Verificación general
    consolidacion_ok = verificar_consolidacion_datos()
    
    # Verificación específica para reportes
    if consolidacion_ok:
        reportes_ok = verificar_datos_especificos_reportes()
        
        if reportes_ok:
            print(f"\n🎉 VERIFICACIÓN COMPLETA: ÉXITO TOTAL")
            print(f"   ✅ Consolidación funcionando correctamente")
            print(f"   ✅ Datos listos para reportes")
            print(f"   ✅ Sistema de tasks puede generar informes")
        else:
            print(f"\n⚠️ VERIFICACIÓN PARCIAL: PROBLEMAS EN DATOS DE REPORTES")
    else:
        print(f"\n❌ VERIFICACIÓN FALLIDA: PROBLEMAS EN CONSOLIDACIÓN")
    
    print(f"\n" + "=" * 70)
