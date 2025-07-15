#!/usr/bin/env python
"""
Script para verificar que los logs de actividad CRUD se están registrando correctamente
en la base de datos para las tarjetas de cierre contable.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from contabilidad.models import TarjetaActivityLog
from api.models import Cliente

def verificar_logs_crud():
    """Verifica los logs de actividad CRUD más recientes"""
    print("🔍 Verificando logs de actividad CRUD...")
    
    # Buscar logs de los últimos 30 minutos
    hace_30_min = datetime.now() - timedelta(minutes=30)
    
    # Buscar logs CRUD recientes
    logs_crud = TarjetaActivityLog.objects.filter(
        fecha_creacion__gte=hace_30_min,
        accion__in=['manual_create', 'manual_edit', 'manual_delete']
    ).order_by('-fecha_creacion')
    
    print(f"\n📊 Total de logs CRUD encontrados (últimos 30 min): {logs_crud.count()}")
    
    if logs_crud.exists():
        print("\n📝 Logs CRUD registrados:")
        print("-" * 80)
        
        for log in logs_crud[:10]:  # Mostrar solo los 10 más recientes
            cliente_nombre = "N/A"
            try:
                if log.cliente_id:
                    cliente = Cliente.objects.get(id=log.cliente_id)
                    cliente_nombre = cliente.nombre[:30]
            except:
                pass
                
            print(f"🎯 {log.tarjeta.upper()} | {log.accion}")
            print(f"   Cliente: {cliente_nombre}")
            print(f"   Período: {log.periodo}")
            print(f"   Descripción: {log.descripcion}")
            print(f"   Usuario: {log.usuario.correo_bdo if log.usuario else 'N/A'}")
            print(f"   Fecha: {log.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Resultado: {log.resultado}")
            if log.detalles:
                print(f"   Detalles: {log.detalles}")
            print("-" * 40)
    else:
        print("❌ No se encontraron logs CRUD en los últimos 30 minutos")
    
    # Verificar logs por tarjeta
    print("\n📋 Resumen por tarjeta (últimos 30 min):")
    tarjetas = ['tipo_documento', 'nombres_ingles', 'clasificacion']
    
    for tarjeta in tarjetas:
        logs_tarjeta = logs_crud.filter(tarjeta=tarjeta)
        print(f"   {tarjeta}: {logs_tarjeta.count()} logs CRUD")
        
        if logs_tarjeta.exists():
            acciones = logs_tarjeta.values_list('accion', flat=True)
            for accion in set(acciones):
                count = acciones.filter(accion=accion).count() if hasattr(acciones, 'filter') else list(acciones).count(accion)
                print(f"     - {accion}: {count}")

def verificar_logs_view():
    """Verifica los logs de visualización más recientes"""
    print("\n🔍 Verificando logs de visualización...")
    
    # Buscar logs de los últimos 30 minutos
    hace_30_min = datetime.now() - timedelta(minutes=30)
    
    # Buscar logs de visualización recientes
    logs_view = TarjetaActivityLog.objects.filter(
        fecha_creacion__gte=hace_30_min,
        accion__in=['view_data', 'view_list']
    ).order_by('-fecha_creacion')
    
    print(f"\n📊 Total de logs de visualización (últimos 30 min): {logs_view.count()}")
    
    if logs_view.exists():
        print("\n📝 Logs de visualización más recientes:")
        print("-" * 80)
        
        for log in logs_view[:5]:  # Mostrar solo los 5 más recientes
            cliente_nombre = "N/A"
            try:
                if log.cliente_id:
                    cliente = Cliente.objects.get(id=log.cliente_id)
                    cliente_nombre = cliente.nombre[:30]
            except:
                pass
                
            print(f"👁️  {log.tarjeta.upper()} | {log.accion}")
            print(f"   Cliente: {cliente_nombre}")
            print(f"   Descripción: {log.descripcion}")
            print(f"   Fecha: {log.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 40)

def main():
    """Función principal"""
    print("=" * 80)
    print("🔍 VERIFICACIÓN FINAL DE LOGS DE ACTIVIDAD CRUD")
    print("=" * 80)
    
    verificar_logs_crud()
    verificar_logs_view()
    
    print("\n" + "=" * 80)
    print("✅ Verificación completada")
    print("=" * 80)

if __name__ == "__main__":
    main()
