#!/usr/bin/env python3
"""
Script para corregir el campo 'cliente' faltante en AccountClassification

Este script actualiza los registros de AccountClassification que no tienen
el campo 'cliente' establecido, extrayéndolo de la cuenta relacionada.

Uso:
    python fix_account_classification_cliente_field.py
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/root/SGM')
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from backend.contabilidad.models import AccountClassification

def fix_missing_cliente_field():
    """
    Corrige el campo 'cliente' faltante en AccountClassification
    """
    print("🔄 Iniciando corrección de campo 'cliente' en AccountClassification...")
    
    # Encontrar registros sin cliente pero con cuenta
    registros_sin_cliente = AccountClassification.objects.filter(
        cliente__isnull=True,
        cuenta__isnull=False  # Solo los que tienen cuenta FK
    )
    
    total_registros = registros_sin_cliente.count()
    print(f"📊 Encontrados {total_registros} registros sin campo cliente")
    
    if total_registros == 0:
        print("✅ No hay registros para corregir")
        return 0
    
    registros_corregidos = 0
    
    for registro in registros_sin_cliente:
        try:
            if registro.cuenta and registro.cuenta.cliente:
                # Extraer cliente de la cuenta
                registro.cliente = registro.cuenta.cliente
                
                # También sincronizar cuenta_codigo si no lo tiene
                if not registro.cuenta_codigo:
                    registro.cuenta_codigo = registro.cuenta.codigo
                
                registro.save(update_fields=['cliente', 'cuenta_codigo'])
                registros_corregidos += 1
                
                if registros_corregidos % 100 == 0:
                    print(f"   Procesados {registros_corregidos}/{total_registros} registros...")
                    
        except Exception as e:
            print(f"❌ Error procesando registro {registro.id}: {str(e)}")
    
    print(f"✅ Corrección completada: {registros_corregidos} registros corregidos")
    return registros_corregidos

def verificar_correccion():
    """
    Verifica que la corrección se haya ejecutado correctamente
    """
    print("\n🔍 Verificando corrección...")
    
    # Contar registros sin cliente
    sin_cliente_con_cuenta = AccountClassification.objects.filter(
        cliente__isnull=True,
        cuenta__isnull=False
    ).count()
    
    sin_cliente_sin_cuenta = AccountClassification.objects.filter(
        cliente__isnull=True,
        cuenta__isnull=True
    ).count()
    
    total_con_cliente = AccountClassification.objects.filter(
        cliente__isnull=False
    ).count()
    
    print(f"📊 Registros sin cliente (con cuenta FK): {sin_cliente_con_cuenta}")
    print(f"📊 Registros sin cliente (sin cuenta FK - temporales): {sin_cliente_sin_cuenta}")
    print(f"📊 Registros con cliente: {total_con_cliente}")
    
    if sin_cliente_con_cuenta == 0:
        print("✅ Todos los registros con cuenta FK tienen campo cliente")
    else:
        print("❌ Aún hay registros con cuenta FK sin campo cliente")

def mostrar_estadisticas():
    """
    Muestra estadísticas generales de AccountClassification
    """
    print("\n📊 ESTADÍSTICAS GENERALES:")
    
    total_registros = AccountClassification.objects.count()
    con_fk = AccountClassification.objects.filter(cuenta__isnull=False).count()
    temporales = AccountClassification.objects.filter(cuenta__isnull=True).count()
    
    print(f"Total registros: {total_registros}")
    print(f"Con FK a cuenta: {con_fk}")
    print(f"Temporales (sin FK): {temporales}")
    
    # Registros por cliente
    clientes_stats = AccountClassification.objects.values(
        'cliente__nombre'
    ).annotate(
        count=django.db.models.Count('id')
    ).order_by('-count')[:10]
    
    print("\n🏢 Top 10 clientes con más clasificaciones:")
    for stat in clientes_stats:
        cliente_nombre = stat['cliente__nombre'] or "SIN CLIENTE"
        print(f"  {cliente_nombre}: {stat['count']} registros")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando script de corrección de AccountClassification...")
        
        # Mostrar estadísticas iniciales
        mostrar_estadisticas()
        
        # Ejecutar corrección
        registros_corregidos = fix_missing_cliente_field()
        
        # Verificar resultado
        verificar_correccion()
        
        print(f"\n🎉 Script completado exitosamente")
        print(f"📝 Total registros corregidos: {registros_corregidos}")
        
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
