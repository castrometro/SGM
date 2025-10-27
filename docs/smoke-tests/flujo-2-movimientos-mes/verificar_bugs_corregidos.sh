#!/bin/bash
# Script para verificar los bugs corregidos en Flujo 2

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║     🔧 VERIFICACIÓN DE BUGS CORREGIDOS - FLUJO 2                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Bugs a verificar:"
echo "   1. ❌ Mapeo de hojas: 'altas_bajas' no reconocida"
echo "   2. ❌ Fechas: Se guardan con un día menos"
echo ""

# Variables
CIERRE_ID=35
CLIENTE_ID=20

echo "🔧 Preparación:"
echo "   • Cierre ID: $CIERRE_ID"
echo "   • Cliente ID: $CLIENTE_ID"
echo ""

# Limpiar datos anteriores
echo "🧹 Limpiando datos anteriores..."
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import MovimientosMesUpload, MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones, MovimientoVariacionSueldo, MovimientoVariacionContrato, CierreNomina

cierre = CierreNomina.objects.get(id=$CIERRE_ID)

# Eliminar movimientos anteriores
MovimientoAltaBaja.objects.filter(cierre=cierre).delete()
MovimientoAusentismo.objects.filter(cierre=cierre).delete()
MovimientoVacaciones.objects.filter(cierre=cierre).delete()
MovimientoVariacionSueldo.objects.filter(cierre=cierre).delete()
MovimientoVariacionContrato.objects.filter(cierre=cierre).delete()

# Eliminar upload anterior
MovimientosMesUpload.objects.filter(cierre=cierre).delete()

print("✅ Datos anteriores eliminados")
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}⏳ SUBIENDO ARCHIVO VIA API...${NC}"
echo "   Frontend URL: http://172.17.11.18:5174"
echo ""
echo "   🚨 ACCIÓN REQUERIDA:"
echo "   1. Ve a: http://172.17.11.18:5174"
echo "   2. Navega a la sección de Movimientos del Mes"
echo "   3. Sube el archivo: flujo-2-movimientos-mes/movimientos_mes_smoke_test.xlsx"
echo "   4. Espera a que el procesamiento termine"
echo ""
read -p "   Presiona ENTER cuando hayas subido el archivo y termine el procesamiento..."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 VERIFICANDO RESULTADOS..."
echo ""

# Verificar resultados
docker compose exec -T django python manage.py shell <<'PYEOF'
from nomina.models import (
    MovimientosMesUpload, 
    MovimientoAltaBaja, 
    MovimientoAusentismo, 
    MovimientoVacaciones, 
    MovimientoVariacionSueldo, 
    MovimientoVariacionContrato,
    CierreNomina
)
from datetime import date

cierre = CierreNomina.objects.get(id=35)
upload = MovimientosMesUpload.objects.filter(cierre=cierre).first()

print("╔══════════════════════════════════════════════════════════════════════════╗")
print("║                     📊 RESULTADOS DE VERIFICACIÓN                        ║")
print("╚══════════════════════════════════════════════════════════════════════════╝")
print()

if not upload:
    print("❌ ERROR: No se encontró el upload")
    exit(1)

print(f"✅ Upload encontrado: ID {upload.id}")
print(f"   Estado: {upload.estado}")
print(f"   Archivo: {upload.archivo.name}")
print()

# Contar registros
altas_bajas = MovimientoAltaBaja.objects.filter(cierre=cierre).count()
ausentismos = MovimientoAusentismo.objects.filter(cierre=cierre).count()
vacaciones = MovimientoVacaciones.objects.filter(cierre=cierre).count()
var_sueldo = MovimientoVariacionSueldo.objects.filter(cierre=cierre).count()
var_contrato = MovimientoVariacionContrato.objects.filter(cierre=cierre).count()

total = altas_bajas + ausentismos + vacaciones + var_sueldo + var_contrato

print("📦 CONTEO DE MOVIMIENTOS:")
print(f"   👤 Altas/Bajas:            {altas_bajas}/5  {'✅' if altas_bajas == 5 else '❌ BUG 1'}")
print(f"   🏥 Ausentismos:            {ausentismos}/2  {'✅' if ausentismos == 2 else '❌'}")
print(f"   🏖️  Vacaciones:             {vacaciones}/1  {'✅' if vacaciones == 1 else '❌'}")
print(f"   💰 Variaciones Sueldo:     {var_sueldo}/2  {'✅' if var_sueldo == 2 else '❌'}")
print(f"   📄 Variaciones Contrato:   {var_contrato}/2  {'✅' if var_contrato == 2 else '❌'}")
print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"   TOTAL:                     {total}/12 {'✅ 100%' if total == 12 else f'❌ {int(total/12*100)}%'}")
print()

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 1: MAPEO DE HOJAS (Bug de altas_bajas)
# ═══════════════════════════════════════════════════════════════════════════
print("╔══════════════════════════════════════════════════════════════════════════╗")
print("║       🔍 VERIFICACIÓN 1: MAPEO DE HOJAS (altas_bajas)                   ║")
print("╚══════════════════════════════════════════════════════════════════════════╝")
print()

if altas_bajas == 5:
    print("✅ BUG 1 CORREGIDO: Hoja 'ALTAS_BAJAS' reconocida correctamente")
    print()
    
    # Mostrar detalles
    print("📋 Detalle de Altas/Bajas procesados:")
    for mov in MovimientoAltaBaja.objects.filter(cierre=cierre):
        tipo_emoji = "🆕" if mov.alta_o_baja == "ALTA" else "📤"
        print(f"   {tipo_emoji} {mov.alta_o_baja}: {mov.nombres_apellidos} ({mov.rut})")
    print()
else:
    print(f"❌ BUG 1 AÚN PRESENTE: Solo se procesaron {altas_bajas}/5 registros de Altas/Bajas")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# VERIFICACIÓN 2: FECHAS CON UN DÍA MENOS
# ═══════════════════════════════════════════════════════════════════════════
print("╔══════════════════════════════════════════════════════════════════════════╗")
print("║       🔍 VERIFICACIÓN 2: FECHAS (un día menos)                           ║")
print("╚══════════════════════════════════════════════════════════════════════════╝")
print()

# Datos esperados del Excel (ver generar_excel_movimientos_mes.py)
fechas_esperadas = {
    'vacaciones': {
        'fecha_inicio': date(2025, 10, 15),
        'fecha_fin': date(2025, 10, 25),
        'fecha_retorno': date(2025, 10, 26),
    },
    'ausentismos': [
        {'inicio': date(2025, 10, 10), 'fin': date(2025, 10, 13)},  # Licencia Médica
        {'inicio': date(2025, 10, 5), 'fin': date(2025, 10, 5)},    # Permiso Personal
    ],
    'altas_bajas': [
        {'ingreso': date(2025, 10, 1)},   # Alta 1
        {'ingreso': date(2025, 10, 5)},   # Alta 2
        {'ingreso': date(2025, 10, 10)},  # Alta 3
        {'retiro': date(2025, 10, 15)},   # Baja 1
        {'retiro': date(2025, 10, 20)},   # Baja 2
    ]
}

errores_fechas = []

# Verificar Vacaciones
vac = MovimientoVacaciones.objects.filter(cierre=cierre).first()
if vac:
    if vac.fecha_inicio != fechas_esperadas['vacaciones']['fecha_inicio']:
        errores_fechas.append(f"   ❌ Vacaciones - Fecha Inicio: Esperada {fechas_esperadas['vacaciones']['fecha_inicio']}, Guardada {vac.fecha_inicio}")
    else:
        print(f"   ✅ Vacaciones - Fecha Inicio: {vac.fecha_inicio} (correcto)")
    
    if vac.fecha_fin != fechas_esperadas['vacaciones']['fecha_fin']:
        errores_fechas.append(f"   ❌ Vacaciones - Fecha Fin: Esperada {fechas_esperadas['vacaciones']['fecha_fin']}, Guardada {vac.fecha_fin}")
    else:
        print(f"   ✅ Vacaciones - Fecha Fin: {vac.fecha_fin} (correcto)")
    
    if vac.fecha_retorno != fechas_esperadas['vacaciones']['fecha_retorno']:
        errores_fechas.append(f"   ❌ Vacaciones - Fecha Retorno: Esperada {fechas_esperadas['vacaciones']['fecha_retorno']}, Guardada {vac.fecha_retorno}")
    else:
        print(f"   ✅ Vacaciones - Fecha Retorno: {vac.fecha_retorno} (correcto)")

# Verificar Ausentismos
print()
for i, aus in enumerate(MovimientoAusentismo.objects.filter(cierre=cierre).order_by('id')):
    esperado = fechas_esperadas['ausentismos'][i]
    tipo = "Licencia Médica" if i == 0 else "Permiso Personal"
    
    if aus.fecha_inicio_ausencia != esperado['inicio']:
        errores_fechas.append(f"   ❌ {tipo} - Fecha Inicio: Esperada {esperado['inicio']}, Guardada {aus.fecha_inicio_ausencia}")
    else:
        print(f"   ✅ {tipo} - Fecha Inicio: {aus.fecha_inicio_ausencia} (correcto)")
    
    if aus.fecha_fin_ausencia != esperado['fin']:
        errores_fechas.append(f"   ❌ {tipo} - Fecha Fin: Esperada {esperado['fin']}, Guardada {aus.fecha_fin_ausencia}")
    else:
        print(f"   ✅ {tipo} - Fecha Fin: {aus.fecha_fin_ausencia} (correcto)")

# Verificar Altas/Bajas (solo si se procesaron)
if altas_bajas == 5:
    print()
    altas = MovimientoAltaBaja.objects.filter(cierre=cierre, alta_o_baja='ALTA').order_by('id')
    for i, alta in enumerate(altas):
        esperado = fechas_esperadas['altas_bajas'][i]
        if alta.fecha_ingreso != esperado['ingreso']:
            errores_fechas.append(f"   ❌ Alta {i+1} - Fecha Ingreso: Esperada {esperado['ingreso']}, Guardada {alta.fecha_ingreso}")
        else:
            print(f"   ✅ Alta {i+1} - Fecha Ingreso: {alta.fecha_ingreso} (correcto)")
    
    bajas = MovimientoAltaBaja.objects.filter(cierre=cierre, alta_o_baja='BAJA').order_by('id')
    for i, baja in enumerate(bajas):
        esperado = fechas_esperadas['altas_bajas'][3+i]  # Las bajas son índices 3 y 4
        if baja.fecha_retiro != esperado['retiro']:
            errores_fechas.append(f"   ❌ Baja {i+1} - Fecha Retiro: Esperada {esperado['retiro']}, Guardada {baja.fecha_retiro}")
        else:
            print(f"   ✅ Baja {i+1} - Fecha Retiro: {baja.fecha_retiro} (correcto)")

print()
if errores_fechas:
    print("❌ BUG 2 AÚN PRESENTE: Hay fechas incorrectas")
    for error in errores_fechas:
        print(error)
else:
    print("✅ BUG 2 CORREGIDO: Todas las fechas son correctas")

print()

# ═══════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════════════════
print("╔══════════════════════════════════════════════════════════════════════════╗")
print("║                     🎯 RESUMEN DE CORRECCIONES                           ║")
print("╚══════════════════════════════════════════════════════════════════════════╝")
print()

bugs_corregidos = 0
if altas_bajas == 5:
    print("✅ BUG 1: Mapeo de hojas 'altas_bajas' → CORREGIDO")
    bugs_corregidos += 1
else:
    print("❌ BUG 1: Mapeo de hojas 'altas_bajas' → NO CORREGIDO")

if not errores_fechas:
    print("✅ BUG 2: Fechas con un día menos → CORREGIDO")
    bugs_corregidos += 1
else:
    print("❌ BUG 2: Fechas con un día menos → NO CORREGIDO")

print()
print(f"📊 ESTADO: {bugs_corregidos}/2 bugs corregidos")
print()

if bugs_corregidos == 2 and total == 12:
    print("🎉 ¡ÉXITO TOTAL! Todos los bugs corregidos, 12/12 movimientos procesados")
    print()
    print("═══════════════════════════════════════════════════════════════════════════")
    print("   Smoke Test Flujo 2: ✅ 100% EXITOSO")
    print("═══════════════════════════════════════════════════════════════════════════")
elif bugs_corregidos == 2:
    print("✅ Bugs corregidos, pero hay otros problemas en el procesamiento")
elif total == 12:
    print("✅ Todos los movimientos procesados, pero hay problemas con las fechas")
else:
    print("⚠️  Aún hay bugs pendientes")

print()

PYEOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Verificación completada"
echo ""
