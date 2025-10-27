#!/bin/bash
# Script para verificar los resultados del Flujo 2: Movimientos del Mes
# Uso: ./verificar_flujo2.sh

echo "🔍 VERIFICANDO RESULTADOS FLUJO 2: MOVIMIENTOS DEL MES"
echo "======================================================="
echo ""

# Verificar Upload
echo "📤 1. VERIFICANDO UPLOAD..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientosMesUpload

upload = MovimientosMesUpload.objects.filter(cierre_id=35).order_by('-id').first()
if upload:
    print(f"✅ Upload ID: {upload.id}")
    print(f"   Estado: {upload.estado}")
    print(f"   Archivo: {upload.archivo.name if upload.archivo else 'N/A'}")
    print(f"   Fecha: {upload.fecha_subida}")
else:
    print("❌ No se encontró upload")
EOF

echo ""
echo "👤 2. VERIFICANDO ALTAS/BAJAS..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoAltaBaja

movimientos = MovimientoAltaBaja.objects.filter(cierre_id=35)
print(f"Total: {movimientos.count()}")

altas = movimientos.filter(tipo_movimiento='ingreso')
print(f"📥 Altas: {altas.count()}")
for mov in altas:
    print(f"   - {mov.rut}: {mov.fecha_movimiento}")

bajas = movimientos.filter(tipo_movimiento='finiquito')
print(f"📤 Bajas: {bajas.count()}")
for mov in bajas:
    print(f"   - {mov.rut}: {mov.fecha_movimiento}")
EOF

echo ""
echo "🏥 3. VERIFICANDO AUSENTISMOS..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoAusentismo

ausentismos = MovimientoAusentismo.objects.filter(cierre_id=35)
print(f"Total: {ausentismos.count()}")
for aus in ausentismos:
    print(f"   - {aus.rut}: {aus.tipo_ausentismo} ({aus.dias} días)")
EOF

echo ""
echo "🏖️  4. VERIFICANDO VACACIONES..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVacaciones

vacaciones = MovimientoVacaciones.objects.filter(cierre_id=35)
print(f"Total: {vacaciones.count()}")
for vac in vacaciones:
    print(f"   - {vac.rut}: {vac.fecha_inicial} a {vac.fecha_fin} ({vac.cantidad_dias} días)")
EOF

echo ""
echo "💰 5. VERIFICANDO VARIACIONES DE SUELDO..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVariacionSueldo

variaciones = MovimientoVariacionSueldo.objects.filter(cierre_id=35)
print(f"Total: {variaciones.count()}")
for var in variaciones:
    print(f"   - {var.rut}: ${var.sueldo_anterior:,.0f} → ${var.sueldo_actual:,.0f}")
EOF

echo ""
echo "📄 6. VERIFICANDO VARIACIONES DE CONTRATO..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVariacionContrato

variaciones = MovimientoVariacionContrato.objects.filter(cierre_id=35)
print(f"Total: {variaciones.count()}")
for var in variaciones:
    print(f"   - {var.rut}: {var.tipo_contrato_anterior} → {var.tipo_contrato_actual}")
EOF

echo ""
echo "📊 7. VERIFICANDO LOGGING..."
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models_logging import TarjetaActivityLogNomina

logs = TarjetaActivityLogNomina.objects.filter(
    tarjeta='movimientos_mes',
    cierre_id=35
).order_by('timestamp')

print(f"Total logs: {logs.count()}")
for log in logs:
    usuario_id = log.usuario.id if log.usuario else 'N/A'
    usuario_correo = log.usuario.correo_bdo if log.usuario else 'N/A'
    print(f"   - {log.accion}: {usuario_correo} (ID: {usuario_id})")
    if usuario_id == 1:
        print("      ⚠️  WARNING: Usuario ID 1 (Pablo Castro) - BUG!")
EOF

echo ""
echo "======================================================="
echo "✅ VERIFICACIÓN COMPLETA"
echo ""
