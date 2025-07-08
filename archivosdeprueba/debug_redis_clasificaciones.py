#!/usr/bin/env python3
"""
Script para debuggear Redis y clasificaciones que pueden estar afectando 
el cálculo de saldos ESF/ERI
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm.settings')
django.setup()

from django.core.cache import cache
from contabilidad.models import (
    CuentaContable, AccountClassification, ClasificacionSet, 
    ClasificacionOption, UploadLog, AperturaCuenta
)

def revisar_redis():
    """Revisar qué hay en Redis que pueda afectar clasificaciones"""
    print("🔍 REVISANDO REDIS/CACHÉ")
    print("="*80)
    
    try:
        # Intentar obtener algunas claves comunes que podrían estar en caché
        claves_a_revisar = [
            'clasificaciones_esf_eri',
            'cuentas_esf',
            'cuentas_eri',
            'saldos_anteriores',
            'balance_esf_eri'
        ]
        
        for clave in claves_a_revisar:
            valor = cache.get(clave)
            if valor is not None:
                print(f"⚠️  ENCONTRADO EN CACHÉ: {clave} = {valor}")
            else:
                print(f"✓ No hay datos en caché para: {clave}")
                
        # Limpiar caché por si acaso
        cache.clear()
        print("🧹 Caché limpiado completamente")
        
    except Exception as e:
        print(f"❌ Error revisando Redis: {e}")

def revisar_clasificaciones_patrimonio():
    """Revisar específicamente las cuentas patrimonio y su clasificación"""
    print("\n🏛️  REVISANDO CLASIFICACIONES DE PATRIMONIO")
    print("="*80)
    
    # Buscar cuentas que contengan "patrimonio" en el nombre
    cuentas_patrimonio = CuentaContable.objects.filter(
        nombre__icontains='patrimonio'
    ).order_by('codigo')
    
    print(f"Encontradas {cuentas_patrimonio.count()} cuentas con 'patrimonio' en el nombre:")
    
    for cuenta in cuentas_patrimonio:
        print(f"\n📋 Cuenta: {cuenta.codigo} | {cuenta.nombre}")
        
        # Revisar clasificaciones
        clasificaciones = AccountClassification.objects.filter(cuenta=cuenta)
        if clasificaciones.exists():
            for clasif in clasificaciones:
                set_nombre = clasif.set_clas.nombre
                valor = clasif.opcion.valor if clasif.opcion else "SIN VALOR"
                print(f"   🏷️  Set: {set_nombre} | Valor: {valor}")
        else:
            print("   ⚠️  Sin clasificaciones")
            
        # Revisar si tiene saldo anterior en el último procesamiento
        ultimo_upload = UploadLog.objects.filter(
            cliente=cuenta.cliente,
            estado='completado'
        ).order_by('-id').first()
        
        if ultimo_upload:
            apertura = AperturaCuenta.objects.filter(
                cuenta=cuenta,
                cierre=ultimo_upload.cierre
            ).first()
            
            if apertura:
                print(f"   💰 Saldo anterior: ${apertura.saldo_anterior:,.2f}")
            else:
                print("   💰 Sin saldo anterior registrado")

def revisar_sets_clasificacion():
    """Revisar todos los sets de clasificación disponibles"""
    print("\n📚 SETS DE CLASIFICACIÓN DISPONIBLES")
    print("="*80)
    
    sets = ClasificacionSet.objects.all().order_by('nombre')
    
    for set_clas in sets:
        print(f"\n🏷️  Set: {set_clas.nombre} (Cliente: {set_clas.cliente})")
        
        opciones = ClasificacionOption.objects.filter(set_clas=set_clas)
        print(f"   Opciones disponibles ({opciones.count()}):")
        
        for opcion in opciones[:10]:  # Mostrar solo las primeras 10
            cuentas_count = AccountClassification.objects.filter(
                set_clas=set_clas,
                opcion=opcion
            ).count()
            print(f"     - {opcion.valor} ({cuentas_count} cuentas)")
        
        if opciones.count() > 10:
            print(f"     ... y {opciones.count() - 10} opciones más")

def buscar_cuenta_especifica():
    """Buscar la cuenta específica que mencionaste con saldo 2,433,300,613"""
    print("\n🔍 BUSCANDO CUENTA CON SALDO ESPECÍFICO")
    print("="*80)
    
    # Buscar en aperturas el saldo específico
    saldo_buscado = 2433300613.00
    
    aperturas = AperturaCuenta.objects.filter(
        saldo_anterior=saldo_buscado
    )
    
    if aperturas.exists():
        for apertura in aperturas:
            cuenta = apertura.cuenta
            print(f"🎯 ENCONTRADA: {cuenta.codigo} | {cuenta.nombre}")
            print(f"   💰 Saldo: ${apertura.saldo_anterior:,.2f}")
            print(f"   🏢 Cliente: {cuenta.cliente}")
            print(f"   📅 Cierre: {apertura.cierre}")
            
            # Revisar clasificaciones de esta cuenta
            clasificaciones = AccountClassification.objects.filter(cuenta=cuenta)
            for clasif in clasificaciones:
                set_nombre = clasif.set_clas.nombre
                valor = clasif.opcion.valor if clasif.opcion else "SIN VALOR"
                print(f"   🏷️  Set: {set_nombre} | Valor: {valor}")
                
                # Verificar si se clasificaría como ESF o ERI
                if ('ESTADO' in set_nombre.upper() and 'SITUACION' in set_nombre.upper() and 'FINANCIERA' in set_nombre.upper()) or \
                   ('BALANCE' in set_nombre.upper()) or \
                   (valor.upper() in ['PATRIMONIO', 'PAID-IN CAPITAL', 'OTHER RESERVES']):
                    print("   ✅ Esta cuenta se clasificaría como ESF")
                elif ('RESULTADO' in set_nombre.upper()) or ('INCOME' in set_nombre.upper()):
                    print("   ⚠️  Esta cuenta se clasificaría como ERI (¿ERROR?)")
                else:
                    print("   ❓ Clasificación ambigua")
    else:
        print(f"❌ No se encontró ninguna cuenta con saldo anterior = ${saldo_buscado:,.2f}")
        
        # Buscar saldos similares
        print("\n🔍 Buscando saldos similares...")
        aperturas_similares = AperturaCuenta.objects.filter(
            saldo_anterior__gte=saldo_buscado - 1000,
            saldo_anterior__lte=saldo_buscado + 1000
        )
        
        for apertura in aperturas_similares[:5]:
            print(f"   📋 {apertura.cuenta.codigo} | ${apertura.saldo_anterior:,.2f}")

if __name__ == "__main__":
    print("🚀 INICIANDO DIAGNÓSTICO DE REDIS Y CLASIFICACIONES")
    print("="*80)
    
    revisar_redis()
    revisar_sets_clasificacion()
    revisar_clasificaciones_patrimonio()
    buscar_cuenta_especifica()
    
    print("\n✅ DIAGNÓSTICO COMPLETADO")
