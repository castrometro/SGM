#!/usr/bin/env python3
"""
Script para diagnosticar movimientos faltantes en AnalisisLibro
"""

import os
import sys
import django
from django.db.models import Count, Sum, Q

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.models import MovimientoContable, CierreContabilidad, CuentaContable, AccountClassification, SetClasificacion

def diagnosticar_movimientos(cierre_id):
    """
    Diagnostica posibles problemas con movimientos faltantes
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        print(f"🔍 Analizando cierre: {cierre} (ID: {cierre_id})")
        print(f"   Cliente: {cierre.cliente.nombre}")
        print(f"   Período: {cierre.periodo}")
        print()
        
        # 1. Contar total de movimientos en el cierre
        total_movimientos = MovimientoContable.objects.filter(cierre=cierre).count()
        print(f"📊 Total movimientos en el cierre: {total_movimientos}")
        
        # 2. Contar cuentas únicas con movimientos
        cuentas_con_movimientos = MovimientoContable.objects.filter(
            cierre=cierre
        ).values('cuenta_id').distinct().count()
        print(f"📁 Cuentas únicas con movimientos: {cuentas_con_movimientos}")
        
        # 3. Contar total de cuentas del cliente
        total_cuentas = CuentaContable.objects.filter(cliente=cierre.cliente).count()
        print(f"📋 Total cuentas del cliente: {total_cuentas}")
        
        # 4. Verificar si hay cuentas sin movimientos
        cuentas_sin_movimientos = total_cuentas - cuentas_con_movimientos
        print(f"⚠️  Cuentas sin movimientos: {cuentas_sin_movimientos}")
        
        # 5. Mostrar algunas cuentas con más movimientos
        print("\n🔥 Top 10 cuentas con más movimientos:")
        top_cuentas = MovimientoContable.objects.filter(cierre=cierre).values(
            'cuenta__codigo', 'cuenta__nombre'
        ).annotate(
            num_movimientos=Count('id'),
            total_debe=Sum('debe'),
            total_haber=Sum('haber')
        ).order_by('-num_movimientos')[:10]
        
        for cuenta in top_cuentas:
            print(f"   {cuenta['cuenta__codigo']} - {cuenta['cuenta__nombre']}: {cuenta['num_movimientos']} movimientos")
        
        # 6. Verificar si hay clasificaciones que filtren datos
        clasificaciones = AccountClassification.objects.filter(
            cuenta__cliente=cierre.cliente
        ).values('set_clas__nombre').annotate(
            num_cuentas=Count('cuenta_id', distinct=True)
        ).order_by('-num_cuentas')
        
        print("\n🏷️  Sets de clasificación disponibles:")
        for cls in clasificaciones:
            print(f"   {cls['set_clas__nombre']}: {cls['num_cuentas']} cuentas clasificadas")
        
        # 7. Verificar movimientos con flag_incompleto
        movimientos_incompletos = MovimientoContable.objects.filter(
            cierre=cierre, flag_incompleto=True
        ).count()
        print(f"\n⚠️  Movimientos marcados como incompletos: {movimientos_incompletos}")
        
        # 8. Simular exactamente lo que ve AnalisisLibro (sin filtros de clasificación)
        print("\n🎯 Simulando datos de AnalisisLibro (cuentas con movimientos):")
        resumen_query = """
        SELECT 
            c.id as cuenta_id,
            c.codigo,
            c.nombre,
            COALESCE(SUM(CASE WHEN m.debe > 0 THEN m.debe ELSE 0 END), 0) as total_debe,
            COALESCE(SUM(CASE WHEN m.haber > 0 THEN m.haber ELSE 0 END), 0) as total_haber,
            COUNT(m.id) as num_movimientos
        FROM contabilidad_cuentacontable c
        INNER JOIN contabilidad_movimientocontable m ON c.id = m.cuenta_id
        WHERE m.cierre_id = %s AND c.cliente_id = %s
        GROUP BY c.id, c.codigo, c.nombre
        ORDER BY c.codigo
        """
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(resumen_query, [cierre.id, cierre.cliente.id])
            resultados = cursor.fetchall()
            
        print(f"   Total cuentas mostradas en AnalisisLibro: {len(resultados)}")
        
        if len(resultados) > 0:
            print("   Primeras 5 cuentas que aparecen:")
            for i, row in enumerate(resultados[:5]):
                cuenta_id, codigo, nombre, total_debe, total_haber, num_mov = row
                saldo_final = total_debe - total_haber
                print(f"   {i+1}. {codigo} - {nombre}: {num_mov} mov, Saldo: ${saldo_final:,.2f}")
        
        # 9. Verificar si hay diferencias entre movimientos esperados vs encontrados
        print(f"\n📈 Resumen de validación:")
        print(f"   ✅ Movimientos totales en BD: {total_movimientos}")
        print(f"   ✅ Cuentas con movimientos (que ve AnalisisLibro): {len(resultados)}")
        print(f"   ℹ️  Cuentas sin movimientos (no aparecen en AnalisisLibro): {cuentas_sin_movimientos}")
        
        return True
        
    except CierreContabilidad.DoesNotExist:
        print(f"❌ No se encontró el cierre con ID: {cierre_id}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def listar_cierres_recientes():
    """Lista los cierres más recientes para facilitar el diagnóstico"""
    print("📅 Cierres recientes disponibles:")
    cierres = CierreContabilidad.objects.select_related('cliente').order_by('-fecha_creacion')[:10]
    
    for cierre in cierres:
        print(f"   ID: {cierre.id} | {cierre.cliente.nombre} | {cierre.periodo}")

def comparar_con_api_analisis_libro(cierre_id, set_id=None, opcion_id=None):
    """
    Compara los datos exactos que devuelve el endpoint de AnalisisLibro
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        print(f"\n🔍 Comparando con API de AnalisisLibro")
        print(f"   Filtros aplicados: Set={set_id}, Opción={opcion_id}")
        
        # Replicar exactamente la query del endpoint movimientos_resumen
        from django.db import connection
        
        base_query = """
        SELECT 
            c.id as cuenta_id,
            c.codigo,
            c.nombre,
            COALESCE(mov_data.saldo_anterior, 0) as saldo_anterior,
            COALESCE(mov_data.total_debe, 0) as total_debe,
            COALESCE(mov_data.total_haber, 0) as total_haber,
            COALESCE(mov_data.saldo_final, 0) as saldo_final
        FROM contabilidad_cuentacontable c
        INNER JOIN (
            SELECT 
                m.cuenta_id,
                SUM(CASE WHEN m.debe > 0 THEN m.debe ELSE 0 END) as total_debe,
                SUM(CASE WHEN m.haber > 0 THEN m.haber ELSE 0 END) as total_haber,
                SUM(m.debe) - SUM(m.haber) as saldo_final,
                0 as saldo_anterior
            FROM contabilidad_movimientocontable m
            WHERE m.cierre_id = %s
            GROUP BY m.cuenta_id
        ) mov_data ON c.id = mov_data.cuenta_id
        WHERE c.cliente_id = %s
        """
        
        params = [cierre.id, cierre.cliente.id]
        
        # Agregar filtros de clasificación si se especifican
        if set_id:
            base_query += """
            AND EXISTS (
                SELECT 1 FROM contabilidad_accountclassification ac
                WHERE ac.cuenta_id = c.id AND ac.set_clas_id = %s
            )
            """
            params.append(set_id)
            
        if opcion_id:
            base_query += """
            AND EXISTS (
                SELECT 1 FROM contabilidad_accountclassification ac
                WHERE ac.cuenta_id = c.id AND ac.opcion_clas_id = %s
            )
            """
            params.append(opcion_id)
            
        base_query += " ORDER BY c.codigo"
        
        with connection.cursor() as cursor:
            cursor.execute(base_query, params)
            resultados = cursor.fetchall()
            
        print(f"   📊 Cuentas devueltas por la API: {len(resultados)}")
        
        if len(resultados) > 0:
            print("   Muestra de los primeros 3 resultados:")
            for i, row in enumerate(resultados[:3]):
                cuenta_id, codigo, nombre, saldo_ant, total_debe, total_haber, saldo_final = row
                print(f"   {i+1}. {codigo} - {nombre}")
                print(f"      Debe: ${total_debe:,.2f} | Haber: ${total_haber:,.2f} | Saldo: ${saldo_final:,.2f}")
        else:
            print("   ⚠️  No se encontraron resultados con estos filtros")
            
        return len(resultados)
        
    except Exception as e:
        print(f"   ❌ Error al comparar con API: {e}")
        return 0

if __name__ == "__main__":
    print("🔧 Diagnóstico de movimientos en AnalisisLibro\n")
    
    if len(sys.argv) > 1:
        cierre_id = int(sys.argv[1])
        print("=" * 60)
        diagnosticar_movimientos(cierre_id)
        print("\n" + "=" * 60)
        
        # Comparar también con diferentes filtros de clasificación
        print("🔎 Comparando con diferentes filtros de AnalisisLibro:")
        comparar_con_api_analisis_libro(cierre_id)  # Sin filtros
        
        # Si hay sets de clasificación, probar con el primero
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
            sets = SetClasificacion.objects.filter(cliente=cierre.cliente).first()
            if sets:
                print(f"\n🏷️  Probando con Set de clasificación: {sets.nombre}")
                comparar_con_api_analisis_libro(cierre_id, set_id=sets.id)
        except:
            pass
        
    else:
        print("Uso: python debug_movimientos_faltantes.py <cierre_id>")
        print("\nCierres disponibles:")
        listar_cierres_recientes()
