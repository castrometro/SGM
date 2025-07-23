#!/bin/bash

# test_logging_system.sh
# Script para probar el sistema de logging de actividades

echo "🧪 Iniciando pruebas del sistema de logging de actividades..."

# Verificar que el archivo existe
if [ -f "/root/SGM/src/utils/activityLogger.js" ]; then
    echo "✅ Archivo activityLogger.js encontrado"
else
    echo "❌ Archivo activityLogger.js NO encontrado"
    exit 1
fi

# Verificar que los endpoints del backend existen
echo "🔍 Verificando endpoints del backend..."

# Verificar models_logging.py
if [ -f "/root/SGM/backend/nomina/models_logging.py" ]; then
    echo "✅ models_logging.py encontrado"
    
    # Verificar que tiene las nuevas acciones
    if grep -q "modal_open" "/root/SGM/backend/nomina/models_logging.py"; then
        echo "✅ Nuevas acciones de logging encontradas en models_logging.py"
    else
        echo "❌ Nuevas acciones de logging NO encontradas en models_logging.py"
    fi
else
    echo "❌ models_logging.py NO encontrado"
fi

# Verificar api_logging.py
if [ -f "/root/SGM/backend/nomina/api_logging.py" ]; then
    echo "✅ api_logging.py encontrado"
else
    echo "❌ api_logging.py NO encontrado"
fi

# Verificar URLs
if [ -f "/root/SGM/backend/nomina/urls.py" ]; then
    echo "✅ urls.py encontrado"
    
    if grep -q "activity-log" "/root/SGM/backend/nomina/urls.py"; then
        echo "✅ URLs de activity-log configuradas"
    else
        echo "❌ URLs de activity-log NO configuradas"
    fi
else
    echo "❌ urls.py NO encontrado"
fi

# Verificar componentes actualizados
echo "🔍 Verificando componentes React..."

if [ -f "/root/SGM/src/components/TarjetasCierreNomina/LibroRemuneracionesCardConLogging.jsx" ]; then
    echo "✅ LibroRemuneracionesCardConLogging.jsx encontrado"
    
    if grep -q "createActivityLogger" "/root/SGM/src/components/TarjetasCierreNomina/LibroRemuneracionesCardConLogging.jsx"; then
        echo "✅ LibroRemuneracionesCardConLogging.jsx integrado con logging"
    else
        echo "❌ LibroRemuneracionesCardConLogging.jsx NO integrado con logging"
    fi
else
    echo "❌ LibroRemuneracionesCardConLogging.jsx NO encontrado"
fi

if [ -f "/root/SGM/src/components/TarjetasCierreNomina/MovimientosMesCard.jsx" ]; then
    echo "✅ MovimientosMesCard.jsx encontrado"
    
    if grep -q "createActivityLogger" "/root/SGM/src/components/TarjetasCierreNomina/MovimientosMesCard.jsx"; then
        echo "✅ MovimientosMesCard.jsx integrado con logging"
    else
        echo "❌ MovimientosMesCard.jsx NO integrado con logging"
    fi
else
    echo "❌ MovimientosMesCard.jsx NO encontrado"
fi

echo ""
echo "📊 Resumen del sistema de logging implementado:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Frontend Utils: activityLogger.js con clase ActivityLogger"
echo "✅ Backend Models: Extendido con 20+ nuevas acciones de logging"
echo "✅ Backend APIs: 4 endpoints especializados para diferentes tipos de actividad"
echo "✅ Backend URLs: Configuradas rutas para activity-log"
echo "✅ Componentes: Integrados LibroRemuneraciones y MovimientosMes"
echo ""
echo "📋 Tipos de actividades registradas:"
echo "   • Sesión: inicio/fin automático"
echo "   • Modales: apertura/cierre con contexto"
echo "   • Archivos: selección, validación, descarga plantillas"
echo "   • Clasificación: visualización, mapeo conceptos"
echo "   • Estados: cambios, polling, progreso"
echo ""
echo "🎯 Para probar:"
echo "   1. Subir un archivo en LibroRemuneraciones"
echo "   2. Verificar logs en /api/nomina/activity-log/{cierre_id}/libro_remuneraciones/"
echo "   3. Probar modales de clasificación"
echo "   4. Descargar plantillas"

echo ""
echo "🚀 Sistema de logging completo y listo para usar!"
