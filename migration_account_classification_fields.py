#!/usr/bin/env python3
"""
Script de migración para poblar nuevos campos en AccountClassification

Este script actualiza los registros existentes de AccountClassification
para agregar los nuevos campos de logging y auditoría.

Uso:
    python migration_account_classification_fields.py
"""

import os
import sys
import django
from datetime import datetime
from django.utils import timezone

# Configurar Django
sys.path.append('/root/SGM')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.contabilidad.models import AccountClassification, Cliente

def migrar_campos_account_classification():
    """
    Migra los campos nuevos en AccountClassification para registros existentes
    """
    print("🔄 Iniciando migración de campos AccountClassification...")
    
    # Obtener todos los registros existentes que necesitan migración
    registros_sin_migrar = AccountClassification.objects.filter(
        origen__isnull=True  # Los nuevos tienen origen, los viejos no
    )
    
    total_registros = registros_sin_migrar.count()
    print(f"📊 Encontrados {total_registros} registros para migrar")
    
    if total_registros == 0:
        print("✅ No hay registros para migrar")
        return
    
    fecha_migracion = timezone.now()
    registros_actualizados = 0
    
    for registro in registros_sin_migrar:
        try:
            # Poblar campos nuevos con valores por defecto razonables
            registro.origen = 'manual'  # Asumir que los existentes son manuales
            registro.fecha_creacion = fecha_migracion  # Usar fecha actual
            registro.fecha_actualizacion = fecha_migracion
            
            # Si tiene cuenta, extraer cliente de ahí
            if registro.cuenta:
                registro.cliente = registro.cuenta.cliente
                registro.cuenta_codigo = ''  # Limpiar código temporal
            else:
                # Si no tiene cuenta, necesitamos cliente explícito
                # Esto no debería pasar en registros existentes, pero por seguridad
                print(f"⚠️ Registro {registro.id} no tiene cuenta asignada")
                continue
            
            registro.save()
            registros_actualizados += 1
            
            if registros_actualizados % 100 == 0:
                print(f"   Procesados {registros_actualizados}/{total_registros} registros...")
                
        except Exception as e:
            print(f"❌ Error procesando registro {registro.id}: {str(e)}")
    
    print(f"✅ Migración completada: {registros_actualizados} registros actualizados")
    return registros_actualizados

def validar_migracion():
    """
    Valida que la migración se haya ejecutado correctamente
    """
    print("\n🔍 Validando migración...")
    
    # Contar registros con origen vacío
    sin_origen = AccountClassification.objects.filter(origen__isnull=True).count()
    sin_cliente = AccountClassification.objects.filter(cliente__isnull=True).count()
    sin_fecha_creacion = AccountClassification.objects.filter(fecha_creacion__isnull=True).count()
    
    total_registros = AccountClassification.objects.count()
    
    print(f"📊 Total de registros: {total_registros}")
    print(f"   Sin origen: {sin_origen}")
    print(f"   Sin cliente: {sin_cliente}")
    print(f"   Sin fecha_creacion: {sin_fecha_creacion}")
    
    if sin_origen == 0 and sin_cliente == 0 and sin_fecha_creacion == 0:
        print("✅ Validación exitosa: Todos los registros tienen los campos requeridos")
        return True
    else:
        print("❌ Validación fallida: Algunos registros necesitan corrección")
        return False

def mostrar_estadisticas():
    """
    Muestra estadísticas de los registros después de la migración
    """
    print("\n📈 Estadísticas post-migración:")
    
    total = AccountClassification.objects.count()
    por_origen = AccountClassification.objects.values('origen').annotate(
        count=django.db.models.Count('id')
    ).order_by('-count')
    
    temporales = AccountClassification.objects.filter(cuenta__isnull=True).count()
    definitivas = AccountClassification.objects.filter(cuenta__isnull=False).count()
    
    print(f"Total de clasificaciones: {total}")
    print(f"Clasificaciones definitivas (con FK): {definitivas}")
    print(f"Clasificaciones temporales (sin FK): {temporales}")
    print("\nPor origen:")
    for item in por_origen:
        print(f"  {item['origen']}: {item['count']}")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando migración de AccountClassification...")
        print(f"📅 Fecha de migración: {timezone.now()}")
        
        # Ejecutar migración
        registros_migrados = migrar_campos_account_classification()
        
        # Validar resultados
        validacion_ok = validar_migracion()
        
        # Mostrar estadísticas
        mostrar_estadisticas()
        
        if validacion_ok:
            print("\n🎉 Migración completada exitosamente!")
        else:
            print("\n⚠️ Migración completada con advertencias")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
