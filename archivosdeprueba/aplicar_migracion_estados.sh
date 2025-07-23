#!/bin/bash

# Script para aplicar la migración que cambia el estado de 'incidencias_generadas' a 'con_discrepancias'

echo "🔄 Aplicando migración para cambiar estado 'incidencias_generadas' a 'con_discrepancias'..."

# Ejecutar la migración
docker compose exec django python manage.py migrate nomina 0025

echo "✅ Migración completada."

# Verificar el cambio
echo "🔍 Verificando cierres actualizados..."
docker compose exec django python manage.py shell -c "
from nomina.models import CierreNomina
con_discrepancias = CierreNomina.objects.filter(estado='con_discrepancias').count()
print(f'Cierres con estado \"con_discrepancias\": {con_discrepancias}')

incidencias_generadas = CierreNomina.objects.filter(estado='incidencias_generadas').count()  
print(f'Cierres con estado \"incidencias_generadas\" (deberían ser 0): {incidencias_generadas}')
"

echo "✅ Verificación completada."
