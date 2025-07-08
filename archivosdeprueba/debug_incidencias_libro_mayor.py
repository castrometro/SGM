#!/usr/bin/env python
"""
Script para debuggear específicamente el problema de incidencias en Libro Mayor

Debug de los siguientes problemas:
1. Solo se crea 1 incidencia en el admin en lugar de las 74 detectadas
2. Nombres en inglés no se mapean para clientes bilingües  
3. IncidenciaResumen está vacío
4. El conteo final no coincide con lo que se muestra en el frontend
"""

import os
import sys
import django

# Configurar Django
project_root = '/root/SGM'
sys.path.insert(0, project_root)
os.chdir(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from backend.contabilidad.models import (
    UploadLog, CierreContabilidad, MovimientoContable, 
    CuentaContable, Incidencia, Cliente
)
from backend.contabilidad.models_incidencias import IncidenciaResumen
from django.db.models import Count, Q

def debug_incidencias_libro_mayor():
    """Debug específico de incidencias en Libro Mayor"""
    
    print("🔍 DEBUG: Problema de Incidencias en Libro Mayor")
    print("=" * 60)
    
    # 1. Buscar el último procesamiento de Libro Mayor
    ultimo_upload = UploadLog.objects.filter(
        tipo_archivo='libro_mayor',
        estado='completado'
    ).order_by('-fecha_subida').first()
    
    if not ultimo_upload:
        print("❌ No se encontró ningún UploadLog de Libro Mayor completado")
        return
    
    print(f"📋 Último UploadLog: {ultimo_upload.id}")
    print(f"   - Cliente: {ultimo_upload.cliente.nombre}")
    print(f"   - Es bilingüe: {ultimo_upload.cliente.bilingue}")
    print(f"   - Fecha: {ultimo_upload.fecha_subida}")
    print(f"   - Estado: {ultimo_upload.estado}")
    
    # 2. Verificar resumen del UploadLog
    resumen = ultimo_upload.resumen or {}
    print(f"\n📊 Resumen del UploadLog:")
    print(f"   - Movimientos creados: {resumen.get('movimientos_creados', 0)}")
    print(f"   - Incidencias creadas: {resumen.get('incidencias_creadas', 0)}")
    
    procesamiento = resumen.get('procesamiento', {})
    if procesamiento:
        print(f"   - Movimientos procesados: {procesamiento.get('movimientos_creados', 0)}")
        print(f"   - Errores: {procesamiento.get('errores_count', 0)}")
    
    incidencias_info = resumen.get('incidencias', {})
    if incidencias_info:
        print(f"   - Incidencias generadas: {incidencias_info.get('generadas', 0)}")
        print(f"   - Movimientos incompletos: {incidencias_info.get('movimientos_incompletos', 0)}")
        print(f"   - Cuentas sin nombres: {incidencias_info.get('cuentas_sin_nombres', 0)}")
    
    # 3. Verificar movimientos creados realmente
    movimientos_reales = MovimientoContable.objects.filter(
        cierre=ultimo_upload.cierre
    ).count()
    print(f"\n💾 Movimientos en BD: {movimientos_reales}")
    
    # 4. Verificar movimientos con flag_incompleto
    movimientos_incompletos = MovimientoContable.objects.filter(
        cierre=ultimo_upload.cierre,
        flag_incompleto=True
    )
    print(f"🚨 Movimientos incompletos: {movimientos_incompletos.count()}")
    
    # Mostrar detalles de algunos movimientos incompletos
    if movimientos_incompletos.exists():
        print("\n   Ejemplos de movimientos incompletos:")
        for mov in movimientos_incompletos[:5]:
            print(f"   - Cuenta: {mov.cuenta.codigo} | TipoDoc: {mov.tipo_doc_codigo} | Descripción: {mov.descripcion[:50]}")
    
    # 5. Verificar incidencias en el modelo Incidencia
    incidencias_bd = Incidencia.objects.filter(
        cierre=ultimo_upload.cierre
    )
    print(f"\n⚠️  Incidencias en BD (Modelo Incidencia): {incidencias_bd.count()}")
    
    if incidencias_bd.exists():
        print("   Incidencias encontradas:")
        for inc in incidencias_bd:
            print(f"   - Tipo: {inc.tipo} | Descripción: {inc.descripcion[:80]}")
    
    # 6. Verificar incidencias consolidadas (IncidenciaResumen)
    incidencias_resumen = IncidenciaResumen.objects.filter(
        upload_log=ultimo_upload
    )
    print(f"\n📋 Incidencias Resumen: {incidencias_resumen.count()}")
    
    if incidencias_resumen.exists():
        print("   Incidencias consolidadas:")
        for inc in incidencias_resumen:
            print(f"   - Tipo: {inc.tipo_incidencia} | Afectados: {inc.cantidad_afectada}")
    
    # 7. Verificar cuentas sin nombres en inglés para cliente bilingüe
    if ultimo_upload.cliente.bilingue:
        print(f"\n🌐 Mapeo de nombres en inglés (Cliente bilingüe):")
        
        # Cuentas totales del cliente en este cierre
        cuentas_totales = CuentaContable.objects.filter(
            cliente=ultimo_upload.cliente,
            movimientocontable__cierre=ultimo_upload.cierre
        ).distinct()
        print(f"   - Cuentas totales en este cierre: {cuentas_totales.count()}")
        
        # Cuentas sin nombre en inglés
        cuentas_sin_nombres = cuentas_totales.filter(nombre_en__isnull=True)
        print(f"   - Cuentas SIN nombre en inglés: {cuentas_sin_nombres.count()}")
        
        # Cuentas con nombre en inglés
        cuentas_con_nombres = cuentas_totales.filter(nombre_en__isnull=False)
        print(f"   - Cuentas CON nombre en inglés: {cuentas_con_nombres.count()}")
        
        # Mostrar ejemplos de cuentas sin nombres
        if cuentas_sin_nombres.exists():
            print("   Ejemplos de cuentas SIN nombre en inglés:")
            for cuenta in cuentas_sin_nombres[:5]:
                print(f"   - {cuenta.codigo}: {cuenta.nombre}")
    
    # 8. Verificar tipos de documento no reconocidos
    print(f"\n📄 Tipos de documento no reconocidos:")
    movimientos_sin_tipodoc = MovimientoContable.objects.filter(
        cierre=ultimo_upload.cierre,
        tipo_doc_codigo__isnull=False,
        tipo_documento__isnull=True
    )
    print(f"   - Movimientos con tipo_doc_codigo pero sin tipo_documento: {movimientos_sin_tipodoc.count()}")
    
    if movimientos_sin_tipodoc.exists():
        # Agrupar por código de tipo de documento
        tipos_no_reconocidos = movimientos_sin_tipodoc.values('tipo_doc_codigo').annotate(
            count=Count('id')
        ).order_by('-count')
        
        print("   Códigos de tipo documento no reconocidos:")
        for tipo in tipos_no_reconocidos[:10]:
            print(f"   - '{tipo['tipo_doc_codigo']}': {tipo['count']} ocurrencias")
    
    # 9. Análisis de discrepancia
    print(f"\n🔍 ANÁLISIS DE DISCREPANCIA:")
    print(f"   - Resumen dice {resumen.get('incidencias_creadas', 0)} incidencias creadas")
    print(f"   - BD tiene {incidencias_bd.count()} incidencias en modelo Incidencia")
    print(f"   - BD tiene {incidencias_resumen.count()} incidencias en modelo IncidenciaResumen")
    print(f"   - Movimientos incompletos detectados: {movimientos_incompletos.count()}")
    print(f"   - Cuentas sin nombres en inglés: {cuentas_sin_nombres.count() if ultimo_upload.cliente.bilingue else 'N/A (cliente no bilingüe)'}")
    
    # 10. Revisión de lógica de get_or_create
    print(f"\n🔧 VERIFICACIÓN DE DUPLICADOS:")
    incidencias_duplicadas = Incidencia.objects.filter(
        cierre=ultimo_upload.cierre
    ).values('descripcion').annotate(count=Count('id')).filter(count__gt=1)
    
    if incidencias_duplicadas.exists():
        print(f"   - Se encontraron {incidencias_duplicadas.count()} descripciones duplicadas")
        for dup in incidencias_duplicadas:
            print(f"   - '{dup['descripcion'][:80]}': {dup['count']} veces")
    else:
        print("   - No se encontraron incidencias duplicadas")

    print(f"\n" + "=" * 60)
    print("🎯 CONCLUSIONES:")
    
    total_problemas_detectados = movimientos_incompletos.count()
    if ultimo_upload.cliente.bilingue:
        total_problemas_detectados += cuentas_sin_nombres.count()
    
    print(f"   - Total de problemas que deberían generar incidencias: {total_problemas_detectados}")
    print(f"   - Incidencias realmente creadas en BD: {incidencias_bd.count()}")
    
    if total_problemas_detectados > incidencias_bd.count():
        print("   ❌ HAY UNA DISCREPANCIA: Se detectaron más problemas de los que se crearon como incidencias")
        print("   💡 Posibles causas:")
        print("      1. get_or_create no está funcionando como se espera")
        print("      2. Hay errores en la lógica de creación de incidencias")
        print("      3. Los problemas no cumplen con las condiciones para crear incidencias")
    else:
        print("   ✅ El número de incidencias coincide con los problemas detectados")

if __name__ == "__main__":
    debug_incidencias_libro_mayor()
