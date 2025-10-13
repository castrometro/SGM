#!/bin/bash

# Script para reemplazar imports de logging V1 por stubs

echo "🧹 Limpiando imports de logging V1 en backend/nomina..."

# Lista de archivos a procesar
files=(
    "backend/nomina/utils/activity_logging.py"
    "backend/nomina/tasks.py"  
    "backend/nomina/views.py"
    "backend/nomina/views_archivos_novedades.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Procesando $file..."
        
        # Reemplazar imports en el nivel de función (dentro de funciones)
        sed -i 's|from \.models_logging import|# STUB TRANSICIÓN - from .models_logging_stub import|g' "$file"
        sed -i 's|from nomina\.models_logging import|# STUB TRANSICIÓN - from nomina.models_logging_stub import|g' "$file"
        sed -i 's|import.*models_logging|# STUB TRANSICIÓN - import models_logging_stub|g' "$file"
        
        echo "✅ $file actualizado"
    else
        echo "⚠️  Archivo no encontrado: $file"
    fi
done

echo ""
echo "🎯 Resumen de cambios:"
echo "- Todos los imports de models_logging fueron comentados y marcados como STUB TRANSICIÓN"
echo "- Las funciones ahora no harán logging real (comportamiento stub)"
echo "- Sistema listo para implementar Activity V2"

echo ""
echo "📋 Próximos pasos:"
echo "1. Implementar el sistema Activity V2 completo"
echo "2. Migrar progresivamente las funcionalidades"
echo "3. Eliminar definitivamente los archivos V1"