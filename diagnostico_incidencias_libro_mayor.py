#!/usr/bin/env python
"""
Diagnóstico completo de incidencias del Libro Mayor.
Analiza por qué se generan 74 incidencias en los logs pero solo aparece 1 en el admin.
"""
import os
import sys
import django
from django.db import connection

# Configurar Django
sys.path.append('/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from api.models import Cliente, UploadLog
from contabilidad.models import CierreContable, MovimientoContable, CuentaContable, Incidencia
from contabilidad.models_incidencias import IncidenciaResumen

def analizar_upload_log_128():
    """Analiza específicamente el UploadLog 128 que aparece en los logs"""
    print("🔍 ANÁLISIS DEL UPLOAD_LOG 128")
    print("=" * 50)
    
    try:
        upload_log = UploadLog.objects.get(id=128)
        print(f"✅ UploadLog encontrado: {upload_log}")
        print(f"   Cliente: {upload_log.cliente}")
        print(f"   Estado: {upload_log.estado}")
        print(f"   Tipo: {upload_log.tipo_archivo}")
        print(f"   Cierre: {upload_log.cierre}")
        
        # Analizar resumen
        resumen = upload_log.resumen or {}
        movimientos = resumen.get('movimientos_creados', 0)
        incidencias = resumen.get('incidencias_creadas', 0)
        
        print(f"\n📊 RESUMEN DEL UPLOAD_LOG:")
        print(f"   Movimientos creados: {movimientos}")
        print(f"   Incidencias creadas: {incidencias}")
        
        # Verificar incidencias reales en BD
        print(f"\n🔎 VERIFICACIÓN EN BASE DE DATOS:")
        
        # Incidencias clásicas
        incidencias_clasicas = Incidencia.objects.filter(cierre=upload_log.cierre)
        print(f"   Incidencias clásicas en BD: {incidencias_clasicas.count()}")
        
        if incidencias_clasicas.exists():
            print(f"   📋 Listado de incidencias clásicas:")
            for inc in incidencias_clasicas[:10]:  # Mostrar primeras 10
                print(f"      - ID: {inc.id}, Tipo: {inc.tipo}, Descripción: {inc.descripcion[:100]}...")
        
        # Incidencias resumen
        incidencias_resumen = IncidenciaResumen.objects.filter(upload_log=upload_log)
        print(f"   Incidencias resumen en BD: {incidencias_resumen.count()}")
        
        if incidencias_resumen.exists():
            print(f"   📋 Listado de incidencias resumen:")
            for inc in incidencias_resumen:
                print(f"      - ID: {inc.id}, Tipo: {inc.tipo_incidencia}, Cantidad: {inc.cantidad_afectada}")
        
        return upload_log
        
    except UploadLog.DoesNotExist:
        print("❌ UploadLog 128 no encontrado")
        return None

def analizar_movimientos_incompletos(upload_log):
    """Analiza los movimientos incompletos que deberían generar incidencias"""
    if not upload_log or not upload_log.cierre:
        return
    
    print(f"\n🔍 ANÁLISIS DE MOVIMIENTOS INCOMPLETOS")
    print("=" * 50)
    
    # Buscar movimientos incompletos igual que en la task
    movimientos_incompletos = MovimientoContable.objects.filter(
        cierre=upload_log.cierre,
        flag_incompleto=True
    ).select_related('cuenta')
    
    print(f"Movimientos con flag_incompleto=True: {movimientos_incompletos.count()}")
    
    # Analizar tipos de problemas
    mov_sin_tipo_doc = 0
    mov_sin_nombre_ingles = 0
    mov_sin_clasificacion = 0
    
    for mov in movimientos_incompletos[:20]:  # Revisar primeros 20
        problemas = []
        
        if mov.tipo_doc_codigo and not mov.tipo_documento:
            mov_sin_tipo_doc += 1
            problemas.append("Sin tipo documento")
        
        if upload_log.cliente.bilingue and not mov.cuenta.nombre_en:
            mov_sin_nombre_ingles += 1
            problemas.append("Sin nombre en inglés")
        
        from contabilidad.models import AccountClassification
        if not AccountClassification.objects.filter(cuenta=mov.cuenta).exists():
            mov_sin_clasificacion += 1
            problemas.append("Sin clasificación")
        
        if problemas:
            print(f"   Movimiento ID {mov.id}, Cuenta {mov.cuenta.codigo}: {', '.join(problemas)}")
    
    print(f"\n📊 RESUMEN DE PROBLEMAS DETECTADOS:")
    print(f"   Movimientos sin tipo documento: {mov_sin_tipo_doc}")
    print(f"   Movimientos sin nombre inglés: {mov_sin_nombre_ingles}")
    print(f"   Movimientos sin clasificación: {mov_sin_clasificacion}")
    
    # Verificar si el cliente es bilingüe
    print(f"\n🌐 CONFIGURACIÓN CLIENTE:")
    print(f"   Cliente bilingüe: {upload_log.cliente.bilingue}")

def analizar_cuentas_sin_nombres_ingles(upload_log):
    """Analiza las cuentas sin nombres en inglés"""
    if not upload_log or not upload_log.cierre:
        return
    
    print(f"\n🔍 ANÁLISIS DE CUENTAS SIN NOMBRES EN INGLÉS")
    print("=" * 50)
    
    # Buscar cuentas sin nombres igual que en la task
    cuentas_sin_nombres = CuentaContable.objects.filter(
        cliente=upload_log.cliente,
        movimientocontable__cierre=upload_log.cierre,
        nombre_en__isnull=True
    ).distinct()
    
    print(f"Cuentas sin nombres en inglés: {cuentas_sin_nombres.count()}")
    
    for cuenta in cuentas_sin_nombres[:10]:  # Mostrar primeras 10
        print(f"   - Cuenta {cuenta.codigo}: {cuenta.nombre}")

def verificar_duplicados_incidencias(upload_log):
    """Verifica si hay duplicados en las incidencias"""
    if not upload_log or not upload_log.cierre:
        return
    
    print(f"\n🔍 VERIFICACIÓN DE DUPLICADOS")
    print("=" * 50)
    
    # Contar incidencias por descripción
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT descripcion, COUNT(*) as cantidad
            FROM contabilidad_incidencia
            WHERE cierre_id = %s
            GROUP BY descripcion
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        """, [upload_log.cierre.id])
        
        duplicados = cursor.fetchall()
        
        if duplicados:
            print("❌ DUPLICADOS ENCONTRADOS:")
            for desc, count in duplicados:
                print(f"   - '{desc[:100]}...' : {count} veces")
        else:
            print("✅ No se encontraron duplicados")

def simular_creacion_incidencias(upload_log):
    """Simula el proceso de creación de incidencias para debugging"""
    if not upload_log or not upload_log.cierre:
        return
    
    print(f"\n🔍 SIMULACIÓN DE CREACIÓN DE INCIDENCIAS")
    print("=" * 50)
    
    incidencias_creadas = 0
    
    # Simular buscar movimientos incompletos
    movimientos_incompletos = MovimientoContable.objects.filter(
        cierre=upload_log.cierre,
        flag_incompleto=True
    ).select_related('cuenta')
    
    print(f"Movimientos incompletos encontrados: {movimientos_incompletos.count()}")
    
    for mov in movimientos_incompletos:
        # Simular crear incidencia por tipo de documento faltante
        if mov.tipo_doc_codigo and not mov.tipo_documento:
            descripcion = f"Tipo de documento '{mov.tipo_doc_codigo}' no encontrado para cuenta {mov.cuenta.codigo}"
            print(f"   Intentaría crear incidencia: {descripcion}")
            
            # Verificar si ya existe
            existe = Incidencia.objects.filter(
                cierre=upload_log.cierre,
                descripcion=descripcion
            ).exists()
            
            if existe:
                print(f"     ⚠️  Ya existe esta incidencia")
            else:
                print(f"     ✅ Sería nueva incidencia")
                incidencias_creadas += 1
    
    # Simular buscar cuentas sin nombres en inglés
    cuentas_sin_nombres = CuentaContable.objects.filter(
        cliente=upload_log.cliente,
        movimientocontable__cierre=upload_log.cierre,
        nombre_en__isnull=True
    ).distinct()
    
    print(f"Cuentas sin nombres en inglés: {cuentas_sin_nombres.count()}")
    
    for cuenta in cuentas_sin_nombres:
        descripcion = f"Nombre en inglés faltante para cuenta {cuenta.codigo}"
        print(f"   Intentaría crear incidencia: {descripcion}")
        
        # Verificar si ya existe
        existe = Incidencia.objects.filter(
            cierre=upload_log.cierre,
            descripcion=descripcion
        ).exists()
        
        if existe:
            print(f"     ⚠️  Ya existe esta incidencia")
        else:
            print(f"     ✅ Sería nueva incidencia")
            incidencias_creadas += 1
    
    print(f"\n📊 RESUMEN SIMULACIÓN:")
    print(f"   Incidencias que se crearían: {incidencias_creadas}")

def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO COMPLETO DE INCIDENCIAS LIBRO MAYOR 🚀")
    print("=" * 70)
    
    # 1. Analizar UploadLog específico
    upload_log = analizar_upload_log_128()
    
    if upload_log:
        # 2. Analizar movimientos incompletos
        analizar_movimientos_incompletos(upload_log)
        
        # 3. Analizar cuentas sin nombres en inglés
        analizar_cuentas_sin_nombres_ingles(upload_log)
        
        # 4. Verificar duplicados
        verificar_duplicados_incidencias(upload_log)
        
        # 5. Simular creación de incidencias
        simular_creacion_incidencias(upload_log)
    
    # 6. Estadísticas generales
    print(f"\n📊 ESTADÍSTICAS GENERALES")
    print("=" * 50)
    print(f"Total incidencias clásicas en BD: {Incidencia.objects.count()}")
    print(f"Total incidencias resumen en BD: {IncidenciaResumen.objects.count()}")
    print(f"Total UploadLogs: {UploadLog.objects.count()}")
    print(f"Total CierresContables: {CierreContable.objects.count()}")

if __name__ == "__main__":
    main()
