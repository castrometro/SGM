#!/bin/bash
# Script de verificación para Flujo 3: Ingresos

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║     🔍 VERIFICACIÓN SMOKE TEST - FLUJO 3: INGRESOS                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Variables
CIERRE_ID=35
CLIENTE_ID=20

echo "🔧 Configuración:"
echo "   • Cierre ID: $CIERRE_ID"
echo "   • Cliente ID: $CLIENTE_ID"
echo ""

# Ejecutar verificación en Django shell
docker compose exec -T django python manage.py shell <<'PYEOF'
from nomina.models import (
    ArchivoAnalistaUpload, 
    AnalistaIngreso, 
    CierreNomina
)
from nomina.models_logging import TarjetaActivityLogNomina
from datetime import date

cierre = CierreNomina.objects.get(id=35)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 VERIFICACIÓN DE RESULTADOS")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# 1. Verificar Upload
print("1️⃣  UPLOAD DE ARCHIVO:")
archivo = ArchivoAnalistaUpload.objects.filter(
    cierre=cierre, 
    tipo_archivo='ingresos'
).order_by('-id').first()

if archivo:
    print(f"   ✅ Upload encontrado: ID {archivo.id}")
    print(f"      Estado: {archivo.estado}")
    print(f"      Fecha: {archivo.fecha_subida}")
    print(f"      Analista: {archivo.analista.correo_bdo if archivo.analista else 'None'}")
    print(f"      Archivo: {archivo.archivo.name}")
    
    if archivo.estado == 'procesado':
        print(f"      ✅ Estado CORRECTO: procesado")
    else:
        print(f"      ❌ Estado INCORRECTO: {archivo.estado} (esperado: procesado)")
else:
    print("   ❌ ERROR: No se encontró el upload")
    exit(1)

print()

# 2. Verificar Registros
print("2️⃣  REGISTROS DE INGRESOS:")
ingresos = AnalistaIngreso.objects.filter(cierre=cierre).order_by('rut')
count = ingresos.count()

print(f"   Total registros: {count}/5")
if count == 5:
    print(f"   ✅ Cantidad CORRECTA")
else:
    print(f"   ❌ Cantidad INCORRECTA (esperado: 5)")

print()
print("   Detalle de registros:")
for ing in ingresos:
    print(f"      • {ing.rut}: {ing.nombre}")
    print(f"        Fecha ingreso: {ing.fecha_ingreso}")
    print(f"        Archivo origen: {ing.archivo_origen_id}")

print()

# 3. Verificar Fechas
print("3️⃣  VERIFICACIÓN DE FECHAS:")
fechas_esperadas = {
    '19111111-1': date(2025, 10, 1),
    '19222222-2': date(2025, 10, 5),
    '19333333-3': date(2025, 10, 10),
    '19444444-4': date(2025, 10, 15),
    '19555555-5': date(2025, 10, 20),
}

errores_fecha = 0
for rut, fecha_esperada in fechas_esperadas.items():
    ing = ingresos.filter(rut=rut).first()
    if ing:
        if ing.fecha_ingreso == fecha_esperada:
            print(f"   ✅ {rut}: {ing.fecha_ingreso} (correcto)")
        else:
            print(f"   ❌ {rut}: {ing.fecha_ingreso} (esperado: {fecha_esperada})")
            errores_fecha += 1
    else:
        print(f"   ⚠️  {rut}: No encontrado")
        errores_fecha += 1

print()

# 4. Verificar Usuario
print("4️⃣  VERIFICACIÓN DE USUARIO:")
if archivo.analista:
    usuario_correo = archivo.analista.correo_bdo
    usuario_id = archivo.analista.id
    print(f"   Usuario upload: {usuario_correo} (ID: {usuario_id})")
    
    if usuario_correo == 'analista.nomina@bdo.cl' and usuario_id == 2:
        print(f"   ✅ Usuario CORRECTO")
    else:
        print(f"   ❌ Usuario INCORRECTO (esperado: analista.nomina@bdo.cl, ID: 2)")
else:
    print(f"   ❌ ERROR: No hay usuario asociado")

print()

# 5. Verificar Logs
print("5️⃣  VERIFICACIÓN DE LOGS:")
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

print()

# 6. Verificar asociación archivo_origen
print("6️⃣  VERIFICACIÓN DE ASOCIACIÓN:")
ingresos_sin_archivo = ingresos.filter(archivo_origen__isnull=True).count()
if ingresos_sin_archivo == 0:
    print(f"   ✅ Todos los ingresos tienen archivo_origen")
else:
    print(f"   ❌ {ingresos_sin_archivo} ingresos sin archivo_origen")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Resumen final
print("╔══════════════════════════════════════════════════════════════════════════╗")
print("║                          🎯 RESUMEN FINAL                                ║")
print("╚══════════════════════════════════════════════════════════════════════════╝")
print()

# Calcular resultado
checks_passed = 0
checks_total = 6

if archivo and archivo.estado == 'procesado':
    checks_passed += 1
if count == 5:
    checks_passed += 1
if errores_fecha == 0:
    checks_passed += 1
if archivo.analista and archivo.analista.correo_bdo == 'analista.nomina@bdo.cl':
    checks_passed += 1
if log_count >= 2:
    checks_passed += 1
if ingresos_sin_archivo == 0:
    checks_passed += 1

print(f"   Checks pasados: {checks_passed}/{checks_total}")
print()

if checks_passed == checks_total:
    print("   🎉 ¡ÉXITO TOTAL!")
    print("   ✅ Upload procesado correctamente")
    print("   ✅ 5/5 ingresos registrados")
    print("   ✅ Fechas correctas")
    print("   ✅ Usuario correcto")
    print("   ✅ Logs completos")
    print("   ✅ Asociaciones correctas")
    print()
    print("   ✨ El Flujo 3 (Ingresos) está 100% funcional ✨")
elif checks_passed >= 4:
    print("   ✅ ÉXITO PARCIAL")
    print(f"   {checks_passed}/{checks_total} verificaciones pasadas")
    print("   ⚠️  Revisar puntos fallidos arriba")
else:
    print("   ❌ FALLOS DETECTADOS")
    print(f"   Solo {checks_passed}/{checks_total} verificaciones pasadas")
    print("   🔧 Revisar logs de Celery y errores arriba")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

PYEOF

echo ""
echo "✅ Verificación completada"
