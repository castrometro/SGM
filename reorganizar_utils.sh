#!/bin/bash
# Script para reorganizar utils/ sin duplicar funcionalidad

echo "🔧 Reorganizando utils/ de nómina..."

# Crear carpetas
mkdir -p backend/nomina/utils/processors
mkdir -p backend/nomina/utils/analyzers  
mkdir -p backend/nomina/utils/common

# PROCESSORS - Mover archivos de procesamiento de archivos
echo "📁 Moviendo procesadores..."
mv backend/nomina/utils/LibroRemuneraciones.py backend/nomina/utils/processors/libro_remuneraciones.py
mv backend/nomina/utils/LibroRemuneracionesOptimizado.py backend/nomina/utils/processors/libro_remuneraciones_optimizado.py
mv backend/nomina/utils/MovimientoMes.py backend/nomina/utils/processors/movimiento_mes.py
mv backend/nomina/utils/NovedadesRemuneraciones.py backend/nomina/utils/processors/novedades_remuneraciones.py
mv backend/nomina/utils/NovedadesOptimizado.py backend/nomina/utils/processors/novedades_optimizado.py
mv backend/nomina/utils/ArchivosAnalista.py backend/nomina/utils/processors/archivos_analista.py

# ANALYZERS - Mover archivos de análisis e incidencias
echo "📊 Moviendo analizadores..."
mv backend/nomina/utils/DetectarIncidencias.py backend/nomina/utils/analyzers/detectar_incidencias.py
mv backend/nomina/utils/DetectarIncidenciasConsolidadas.py backend/nomina/utils/analyzers/detectar_incidencias_consolidadas.py
mv backend/nomina/utils/GenerarIncidencias.py backend/nomina/utils/analyzers/generar_incidencias.py
mv backend/nomina/utils/GenerarDiscrepancias.py backend/nomina/utils/analyzers/generar_discrepancias.py
mv backend/nomina/utils/AnalisisCompletoIncidencias.py backend/nomina/utils/analyzers/analisis_completo_incidencias.py
mv backend/nomina/utils/ConsolidarInformacion.py backend/nomina/utils/analyzers/consolidar_informacion.py

# COMMON - Mover utilidades comunes
echo "🛠️ Moviendo utilidades comunes..."
mv backend/nomina/utils/validaciones.py backend/nomina/utils/common/validaciones.py
mv backend/nomina/utils/uploads.py backend/nomina/utils/common/uploads.py
mv backend/nomina/utils/mixins.py backend/nomina/utils/common/mixins.py
mv backend/nomina/utils/activity_logging.py backend/nomina/utils/common/activity_logging.py
mv backend/nomina/utils/clientes.py backend/nomina/utils/common/clientes.py

# Crear __init__.py files
touch backend/nomina/utils/processors/__init__.py
touch backend/nomina/utils/analyzers/__init__.py
touch backend/nomina/utils/common/__init__.py

echo "✅ Reorganización de utils/ completada"
echo "⚠️  SIGUIENTE: Actualizar imports en archivos que usen estas utilidades"
