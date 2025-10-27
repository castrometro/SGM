#!/usr/bin/env python3
"""
Script de verificación para Flujo 3 - Ingresos
"""
import os
import sys
import django

# Configuración Django
sys.path.insert(0, '/root/SGM/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')
django.setup()

from nomina.models import ArchivoAnalistaUpload, AnalistaIngreso, TarjetaActivityLogNomina
from contabilidad.models import CierreContable

print("\n" + "=" * 80)
print("🧪  VERIFICACIÓN FLUJO 3 - INGRESOS")
print("=" * 80 + "\n")

# Configuración de prueba
CIERRE_ID = 35
CLIENTE_ID = 20
PERIODO = '202510'

print(f"📋 PARÁMETROS DE PRUEBA:")
print(f"   Cierre ID: {CIERRE_ID}")
print(f"   Cliente ID: {CLIENTE_ID}")
print(f"   Período: {PERIODO}\n")

# 1. Verificar cierre existe
print("1️⃣  VERIFICACIÓN DE CIERRE:")
try:
    cierre = CierreContable.objects.get(id=CIERRE_ID, cliente_id=CLIENTE_ID)
    print(f"   ✅ Cierre encontrado: {cierre.periodo}")
except CierreContable.DoesNotExist:
    print(f"   ❌ ERROR: Cierre {CIERRE_ID} no encontrado")
    sys.exit(1)

# 2. Verificar archivo subido
print("\n2️⃣  VERIFICACIÓN DE ARCHIVO:")
archivos = ArchivoAnalistaUpload.objects.filter(
    cierre=cierre,
    tipo_archivo='ingresos'
).order_by('-fecha_subida')

if not archivos.exists():
    print("   ❌ ERROR: No se encontró archivo de ingresos procesado")
    sys.exit(1)

archivo = archivos.first()
print(f"   ✅ Archivo encontrado: ID {archivo.id}")
print(f"   Nombre: {archivo.nombre_archivo}")
print(f"   Estado: {archivo.estado}")
print(f"   Fecha: {archivo.fecha_subida}")
usuario_nombre = archivo.usuario.correo_bdo if archivo.usuario else 'None'
print(f"   Usuario: {usuario_nombre}")

# 3. Verificar registros creados
print("\n3️⃣  VERIFICACIÓN DE REGISTROS:")
ingresos = AnalistaIngreso.objects.filter(archivo_origen=archivo)
total_ingresos = ingresos.count()

print(f"   Total de ingresos: {total_ingresos}")

if total_ingresos == 0:
    print("   ❌ ERROR: No se crearon registros de ingresos")
    sys.exit(1)

print(f"   ✅ Registros encontrados: {total_ingresos}")

# Mostrar algunos ejemplos
print("\n   📊 MUESTRA DE REGISTROS:")
for ing in ingresos[:5]:
    empleado_nombre = ing.empleado.nombre_completo if ing.empleado else 'N/A'
    print(f"      • {ing.fecha_ingreso} - {empleado_nombre}")
    print(f"        RUT: {ing.rut_empleado}, Concepto: {ing.concepto_pago}")

# 4. Verificar fechas
print("\n4️⃣  VERIFICACIÓN DE FECHAS:")
fechas_encontradas = ingresos.values_list('fecha_ingreso', flat=True).distinct()
print(f"   Total de fechas únicas: {len(fechas_encontradas)}")

for fecha in sorted(fechas_encontradas):
    count = ingresos.filter(fecha_ingreso=fecha).count()
    print(f"      • {fecha}: {count} ingreso(s)")

# 5. Verificar Logs
print("\n5️⃣  VERIFICACIÓN DE LOGS:")
logs = TarjetaActivityLogNomina.objects.filter(
    cierre=cierre,
    tarjeta='archivo_analista'
).order_by('-timestamp')[:10]

log_count = logs.count()
print(f"   Total de logs recientes: {log_count}")

if log_count >= 1:
    print(f"   ✅ Logs registrados")
    for log in logs[:5]:
        usuario_log = log.usuario.correo_bdo if log.usuario else 'None'
        print(f"      • {log.accion}: {log.descripcion[:50]}...")
        print(f"        Usuario: {usuario_log}")
else:
    print(f"   ⚠️  Pocos logs encontrados")

# 6. Verificar usuario propagado
print("\n6️⃣  VERIFICACIÓN DE USUARIO:")
usuario_archivo = archivo.usuario
print(f"   Usuario del archivo: {usuario_archivo.correo_bdo if usuario_archivo else 'None'}")

# Verificar propagación a registros
usuarios_en_registros = ingresos.exclude(usuario__isnull=True).count()
print(f"   Registros con usuario propagado: {usuarios_en_registros}/{total_ingresos}")

if usuarios_en_registros == total_ingresos:
    print(f"   ✅ Usuario propagado correctamente a todos los registros")
elif usuarios_en_registros > 0:
    print(f"   ⚠️  Usuario propagado parcialmente")
else:
    print(f"   ⚠️  No se propagó el usuario a los registros")

# Resumen final
print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 80)
print(f"\n📊 RESUMEN:")
print(f"   • Archivo procesado: {archivo.nombre_archivo}")
print(f"   • Estado: {archivo.estado}")
print(f"   • Registros creados: {total_ingresos}")
print(f"   • Fechas únicas: {len(fechas_encontradas)}")
print(f"   • Logs registrados: {log_count}")
print(f"   • Usuario propagado: {usuarios_en_registros}/{total_ingresos}")
print()
