#!/bin/bash

# Script para limpiar discrepancias innecesarias y regenerar con nueva lógica

echo "🧹 Limpiando discrepancias innecesarias y regenerando con nueva lógica..."

# Limpiar discrepancias existentes del cierre 13
echo "🗑️  Limpiando discrepancias existentes del cierre 13..."
docker compose exec django python manage.py shell -c "
from nomina.models import DiscrepanciaCierre, CierreNomina

# Obtener el cierre
cierre = CierreNomina.objects.get(id=13)
print(f'Discrepancias antes de limpiar: {cierre.discrepancias.count()}')

# Eliminar discrepancias existentes
cierre.discrepancias.all().delete()
print('✅ Discrepancias eliminadas')
"

# Regenerar discrepancias con nueva lógica
echo "🔄 Regenerando discrepancias con nueva lógica optimizada..."
docker compose exec django python manage.py shell -c "
from nomina.models import CierreNomina
from nomina.utils.GenerarDiscrepancias import generar_todas_discrepancias

# Regenerar discrepancias
cierre = CierreNomina.objects.get(id=13)
resultado = generar_todas_discrepancias(cierre)

print(f'✅ Nuevas discrepancias generadas:')
print(f'  - Total: {resultado[\"total_discrepancias\"]}')
print(f'  - Libro vs Novedades: {resultado[\"libro_vs_novedades\"]}')
print(f'  - MovimientosMes vs Analista: {resultado[\"movimientos_vs_analista\"]}')

# Cambiar estado del cierre a con_discrepancias si hay discrepancias
if resultado['total_discrepancias'] > 0:
    cierre.estado = 'con_discrepancias'
else:
    cierre.estado = 'verificado_sin_discrepancias'
cierre.save()
print(f'✅ Estado del cierre actualizado a: {cierre.estado}')
"

echo "✅ Proceso completado. Las discrepancias ahora incluyen solo información relevante:"
echo "   ✅ Empleados solo en novedades"
echo "   ✅ Diferencias en montos de conceptos comunes"
echo "   ✅ Ingresos/finiquitos/ausencias no reportadas por analista"
echo "   ✅ Diferencias en detalles de ausencias"
echo ""
echo "   ❌ Eliminados (no relevantes):"
echo "   ❌ Empleados solo en libro (normal)"
echo "   ❌ Diferencias en datos personales (variaciones menores)"
echo "   ❌ Conceptos solo en libro (normal)"
echo "   ❌ Conceptos solo en novedades (comportamiento esperado)"
