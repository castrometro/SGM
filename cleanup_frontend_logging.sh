#!/bin/bash

# Script para limpiar imports y llamadas del ActivityLogger V1 en frontend
# Comentar temporalmente en lugar de eliminar para fácil reversión

echo "🧹 Limpiando ActivityLogger V1 del frontend..."

# Archivos a limpiar
files=(
    "src/components/TarjetasCierreNomina/IngresosCard.jsx"
    "src/components/TarjetasCierreNomina/AusentismosCard.jsx"  
    "src/components/TarjetasCierreNomina/FiniquitosCard.jsx"
    "src/components/TarjetasCierreNomina/MovimientosMesCard.jsx"
    "src/components/TarjetasCierreNomina/LibroRemuneracionesCardConLogging.jsx"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Procesando $file..."
        
        # Comentar import del activityLogger
        sed -i 's|import { createActivityLogger } from "../../utils/activityLogger";|// TODO: Migrar a ActivityLogger V2\n// import { createActivityLogger } from "../../utils/activityLogger";|g' "$file"
        
        # Comentar declaración de activityLogger
        sed -i 's|const activityLogger = useRef(null);|// TODO: Migrar a ActivityLogger V2\n  // const activityLogger = useRef(null);|g' "$file"
        
        # Comentar todas las líneas que contienen activityLogger.current
        sed -i 's|.*activityLogger\.current.*|    // TODO: ActivityLogger V2 - &|g' "$file"
        
        echo "✅ $file limpiado"
    else
        echo "⚠️  $file no encontrado"
    fi
done

echo "🎉 Limpieza de frontend completada"
echo "💡 Los imports están comentados, no eliminados"
echo "🔄 Para revertir: buscar '// TODO: Migrar a ActivityLogger V2' y descomentar"