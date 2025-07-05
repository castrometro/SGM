#!/usr/bin/env python3

import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from backend.contabilidad.models import (
    UploadLog, AperturaCuenta, CuentaContable, AccountClassification
)

def analizar_cuentas_esf_eri():
    """
    Analiza las cuentas ESF y ERI del último procesamiento de libro mayor
    """
    print("="*80)
    print("🔍 ANÁLISIS DETALLADO DE CUENTAS ESF/ERI")
    print("="*80)
    
    # Obtener el último upload_log de libro mayor completado
    ultimo_upload = UploadLog.objects.filter(
        tipo_upload='libro_mayor',
        estado='completado'
    ).order_by('-id').first()
    
    if not ultimo_upload:
        print("❌ No se encontró ningún upload_log de libro mayor completado")
        return
    
    print(f"📄 Upload Log ID: {ultimo_upload.id}")
    print(f"🏢 Cliente: {ultimo_upload.cliente}")
    print(f"📅 Cierre: {ultimo_upload.cierre}")
    print()
    
    # Obtener todas las aperturas de este cierre
    aperturas = AperturaCuenta.objects.filter(
        cierre=ultimo_upload.cierre
    ).select_related('cuenta')
    
    print(f"📊 Total aperturas encontradas: {aperturas.count()}")
    print()
    
    # Helper para identificar clasificación ESF/ERI
    def identificar_clasificacion_esf_eri(cuenta_obj):
        try:
            clasificaciones = AccountClassification.objects.filter(
                cuenta=cuenta_obj
            ).select_related('set_clas', 'opcion')
            
            if not clasificaciones.exists():
                return None
            
            for clasificacion in clasificaciones:
                if not clasificacion.opcion:
                    continue
                    
                set_nombre = clasificacion.set_clas.nombre.upper()
                valor = clasificacion.opcion.valor.upper()
                
                # Identificar ESF
                if ('ESTADO' in set_nombre and 'SITUACION' in set_nombre and 'FINANCIERA' in set_nombre) or \
                   ('BALANCE' in set_nombre) or \
                   (valor in ['ACTIVO CORRIENTE', 'ACTIVO NO CORRIENTE', 'PASIVO CORRIENTE', 'PASIVO NO CORRIENTE', 'PATRIMONIO']) or \
                   (valor in ['CASH AND CASH EQUIVALENT', 'OTHER CURRENT FINANCIAL ASSETS', 'INVENTORIES',
                             'COMMERCIAL DEBTORS AND OTHER RECEIVABLES, CURRENT', 'CURRENT TAX RECEIVABLE',
                             'OTHER CURRENT ASSETS', 'PROPERTIES, FACILITY AND EQUIPMENT', 'DEFERRED TAX ASSETS',
                             'OTHER NON-CURRENT ASSETS', 'OTHER FINANCIAL, NON-CURRENT ASSETS',
                             'COMMERCIAL ACCOUNTS AND OTHER ACCOUNTS PAYABLE, CURRENT', 'LIABILITY FOR CURRENT TAXES',
                             'OTHER LIABILITY, CURRENT', 'PROVISIONS', 'ACCOUNTS PAYABLE TO RELATED ENTITIES, NO CURRENT',
                             'DEFERRED TAX LIABILITY', 'PAID-IN CAPITAL', 'OTHER RESERVES']):
                    return 'ESF', set_nombre, valor
                
                # Identificar ERI
                elif ('RESULTADO' in set_nombre) or ('INCOME' in set_nombre) or \
                     (valor in ['INGRESOS', 'GASTOS', 'COSTOS', 'OTROS INGRESOS', 'OTROS GASTOS']) or \
                     (valor in ['ADMINISTRATION EXPENSES', 'COST SALE', 'FINANCIAL EXPENSES', 'FINANCIAL INCOME', 
                               'OTHER EXPENSES', 'INCOME', 'GANANCIAS', 'PERDIDAS', 'GAINS (LOSSES) ACCUMULATED',
                               'GANANCIAS (ANTES DE IMPUESTOS)', 'GANANCIAS (PERDIDAS)', 'GANANCIAS BRUTAS',
                               'INCOME / (LOSS) OF THE OPERATION', 'OTHER EXPENSES, BY FUNCTION', 'DIFFERENCE IN CHANGES']):
                    return 'ERI', set_nombre, valor
                
                elif valor in ['ESF', 'ERI']:
                    return valor, set_nombre, valor
            
            return None
        except Exception as e:
            return None
    
    # Clasificar todas las cuentas
    cuentas_esf = []
    cuentas_eri = []
    cuentas_sin_clasificacion = []
    
    total_saldo_esf = 0
    total_saldo_eri = 0
    
    for apertura in aperturas:
        cuenta = apertura.cuenta
        clasificacion_info = identificar_clasificacion_esf_eri(cuenta)
        
        if clasificacion_info and clasificacion_info[0] == 'ESF':
            cuentas_esf.append({
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'saldo_anterior': float(apertura.saldo_anterior),
                'set_nombre': clasificacion_info[1],
                'valor': clasificacion_info[2]
            })
            total_saldo_esf += float(apertura.saldo_anterior)
        elif clasificacion_info and clasificacion_info[0] == 'ERI':
            cuentas_eri.append({
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'saldo_anterior': float(apertura.saldo_anterior),
                'set_nombre': clasificacion_info[1],
                'valor': clasificacion_info[2]
            })
            total_saldo_eri += float(apertura.saldo_anterior)
        else:
            cuentas_sin_clasificacion.append({
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'saldo_anterior': float(apertura.saldo_anterior)
            })
    
    # Mostrar resultados
    print("🏛️  CUENTAS ESF (Estado de Situación Financiera):")
    print("="*80)
    for cuenta in sorted(cuentas_esf, key=lambda x: x['codigo']):
        print(f"  {cuenta['codigo']:<20} | {cuenta['nombre']:<40} | ${cuenta['saldo_anterior']:>15,.2f}")
        print(f"    └─ Set: {cuenta['set_nombre']} | Valor: {cuenta['valor']}")
    
    print(f"\n📊 TOTAL ESF: {len(cuentas_esf)} cuentas | Saldo total: ${total_saldo_esf:,.2f}")
    print("="*80)
    
    print("\n💼 CUENTAS ERI (Estado de Resultados Integrales):")
    print("="*80)
    for cuenta in sorted(cuentas_eri, key=lambda x: x['codigo']):
        print(f"  {cuenta['codigo']:<20} | {cuenta['nombre']:<40} | ${cuenta['saldo_anterior']:>15,.2f}")
        print(f"    └─ Set: {cuenta['set_nombre']} | Valor: {cuenta['valor']}")
        
        # Alertar sobre posibles errores de clasificación
        if 'PATRIMONIO' in cuenta['nombre'].upper() or 'CAPITAL' in cuenta['nombre'].upper():
            print(f"    ⚠️  WARNING: Esta cuenta parece ser de PATRIMONIO pero está clasificada como ERI")
    
    print(f"\n📊 TOTAL ERI: {len(cuentas_eri)} cuentas | Saldo total: ${total_saldo_eri:,.2f}")
    print("="*80)
    
    if cuentas_sin_clasificacion:
        print("\n❓ CUENTAS SIN CLASIFICACIÓN ESF/ERI:")
        print("="*80)
        for cuenta in sorted(cuentas_sin_clasificacion, key=lambda x: x['codigo']):
            print(f"  {cuenta['codigo']:<20} | {cuenta['nombre']:<40} | ${cuenta['saldo_anterior']:>15,.2f}")
        print(f"\n📊 TOTAL SIN CLASIFICACIÓN: {len(cuentas_sin_clasificacion)} cuentas")
        print("="*80)
    
    print(f"\n🔢 RESUMEN GENERAL:")
    print(f"  Total cuentas ESF: {len(cuentas_esf)} | Saldo: ${total_saldo_esf:,.2f}")
    print(f"  Total cuentas ERI: {len(cuentas_eri)} | Saldo: ${total_saldo_eri:,.2f}")
    print(f"  Balance total: ${total_saldo_esf + total_saldo_eri:,.2f}")
    print("="*80)

if __name__ == "__main__":
    analizar_cuentas_esf_eri()
