#!/usr/bin/env python3
"""
Script de diagnóstico para revisar por qué los informes están llegando vacíos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.contabilidad.models import (
    CierreContabilidad, 
    CuentaContable, 
    MovimientoContable,
    AperturaCuenta,
    AccountClassification,
    ClasificacionSet,
    ReporteFinanciero
)

def diagnosticar_cierres():
    """Diagnostica los cierres y sus datos"""
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE CIERRES CONTABLES")
    print("=" * 80)
    
    # 1. Verificar cierres existentes
    cierres = CierreContabilidad.objects.all().order_by('-id')[:5]
    print(f"\n📊 CIERRES RECIENTES ({len(cierres)} de últimos 5):")
    for cierre in cierres:
        print(f"   ID: {cierre.id} | Cliente: {cierre.cliente.nombre} | Período: {cierre.periodo} | Estado: {cierre.estado}")
    
    if not cierres:
        print("❌ No hay cierres disponibles")
        return
    
    # Usar el cierre más reciente para diagnóstico
    cierre = cierres[0]
    print(f"\n🔍 DIAGNOSTICANDO CIERRE: {cierre.id} ({cierre.cliente.nombre} - {cierre.periodo})")
    
    # 2. Verificar cuentas
    cuentas_cliente = CuentaContable.objects.filter(cliente=cierre.cliente)
    print(f"\n📋 CUENTAS DEL CLIENTE:")
    print(f"   Total cuentas: {cuentas_cliente.count()}")
    if cuentas_cliente.exists():
        print(f"   Primeras 5 cuentas:")
        for cuenta in cuentas_cliente[:5]:
            print(f"   - {cuenta.codigo}: {cuenta.nombre}")
    
    # 3. Verificar movimientos
    movimientos = MovimientoContable.objects.filter(cierre=cierre)
    print(f"\n💰 MOVIMIENTOS DEL CIERRE:")
    print(f"   Total movimientos: {movimientos.count()}")
    if movimientos.exists():
        cuentas_con_movimientos = movimientos.values_list('cuenta_id', flat=True).distinct().count()
        print(f"   Cuentas con movimientos: {cuentas_con_movimientos}")
        
        # Mostrar algunos movimientos
        print(f"   Primeros 3 movimientos:")
        for mov in movimientos[:3]:
            print(f"   - Cuenta: {mov.cuenta.codigo} | Debe: ${mov.debe} | Haber: ${mov.haber} | Desc: {mov.descripcion[:50]}...")
    
    # 4. Verificar aperturas
    aperturas = AperturaCuenta.objects.filter(cierre=cierre)
    print(f"\n🏦 APERTURAS DEL CIERRE:")
    print(f"   Total aperturas: {aperturas.count()}")
    if aperturas.exists():
        print(f"   Primeras 3 aperturas:")
        for apertura in aperturas[:3]:
            print(f"   - Cuenta: {apertura.cuenta.codigo} | Saldo anterior: ${apertura.saldo_anterior}")
    
    # 5. Verificar sets de clasificación
    sets_clasificacion = ClasificacionSet.objects.filter(cliente=cierre.cliente)
    print(f"\n🏷️ SETS DE CLASIFICACIÓN:")
    print(f"   Total sets: {sets_clasificacion.count()}")
    for set_cls in sets_clasificacion:
        clasificaciones_count = AccountClassification.objects.filter(set_clas=set_cls).count()
        print(f"   - {set_cls.nombre}: {clasificaciones_count} clasificaciones")
    
    # 6. Verificar clasificaciones específicas
    if sets_clasificacion.exists():
        set_ejemplo = sets_clasificacion.first()
        clasificaciones = AccountClassification.objects.filter(
            set_clas=set_ejemplo,
            cuenta__cliente=cierre.cliente
        )[:5]
        print(f"\n🔗 CLASIFICACIONES DEL SET '{set_ejemplo.nombre}':")
        for cls in clasificaciones:
            print(f"   - Cuenta {cls.cuenta.codigo}: {cls.opcion.valor}")
    
    # 7. Verificar reportes generados
    reportes = ReporteFinanciero.objects.filter(cierre=cierre)
    print(f"\n📄 REPORTES GENERADOS:")
    print(f"   Total reportes: {reportes.count()}")
    for reporte in reportes:
        datos_size = len(str(reporte.datos_json)) if reporte.datos_json else 0
        print(f"   - {reporte.tipo_reporte}: {reporte.estado} | Datos: {datos_size} chars")
        if reporte.error_mensaje:
            print(f"     Error: {reporte.error_mensaje}")
    
    # 8. Prueba de función _obtener_cuentas_con_datos
    print(f"\n🧪 PRUEBA DE FUNCIÓN _obtener_cuentas_con_datos:")
    try:
        from backend.contabilidad.tasks_reportes import _obtener_cuentas_con_datos
        cuentas_data = _obtener_cuentas_con_datos(cierre)
        print(f"   ✅ Función ejecutada correctamente")
        print(f"   📊 Total cuentas obtenidas: {len(cuentas_data)}")
        
        if cuentas_data:
            print(f"   📋 Primeras 3 cuentas:")
            for i, (cuenta_id, datos) in enumerate(list(cuentas_data.items())[:3]):
                print(f"   - ID: {cuenta_id} | Código: {datos['codigo']} | Saldo final: ${datos['saldo_final']}")
                print(f"     Debe: ${datos['total_debe']} | Haber: ${datos['total_haber']} | Movimientos: {len(datos['movimientos'])}")
        else:
            print("   ❌ No se obtuvieron cuentas - ESTE ES EL PROBLEMA")
            
    except Exception as e:
        print(f"   ❌ Error ejecutando función: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnosticar_cierres()
