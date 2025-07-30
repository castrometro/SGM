#!/bin/bash

# 🚀 SCRIPT DE INICIO: WORKERS OPTIMIZADOS PARA CONSOLIDACIÓN
# 
# Este script inicia workers Celery optimizados para el procesamiento
# paralelo de consolidación de datos de nómina.
#
# CONFIGURACIÓN:
# - Worker dedicado para consolidación con 4 procesos concurrentes
# - Worker general para otras tareas con 2 procesos
# - Configuración optimizada para rendimiento

echo "🚀 INICIANDO WORKERS CELERY OPTIMIZADOS PARA CONSOLIDACIÓN..."

# Verificar que Redis esté corriendo
if ! pgrep -x "redis-server" > /dev/null; then
    echo "❌ ERROR: Redis no está ejecutándose"
    echo "Por favor inicia Redis primero: sudo systemctl start redis"
    exit 1
fi

# Función para manejar señales de interrupción
cleanup() {
    echo ""
    echo "🛑 Deteniendo workers Celery..."
    pkill -f "celery.*worker"
    sleep 2
    echo "✅ Workers detenidos correctamente"
    exit 0
}

# Capturar señales de interrupción
trap cleanup SIGINT SIGTERM

# Navegar al directorio backend
cd /root/SGM/backend || {
    echo "❌ ERROR: No se puede acceder al directorio backend"
    exit 1
}

echo "📁 Directorio de trabajo: $(pwd)"

# Verificar que el archivo manage.py existe
if [ ! -f "manage.py" ]; then
    echo "❌ ERROR: manage.py no encontrado en el directorio backend"
    exit 1
fi

echo "🔧 Configuración:"
echo "   • Worker consolidación: 4 procesos concurrentes"
echo "   • Worker general: 2 procesos concurrentes"
echo "   • Cola dedicada: 'consolidacion'"
echo "   • Broker: Redis"

# Iniciar worker dedicado para consolidación EN SEGUNDO PLANO
echo ""
echo "🚀 Iniciando worker para CONSOLIDACIÓN (cola: consolidacion)..."
celery -A backend worker -Q consolidacion -c 4 \
    --loglevel=info \
    --hostname=consolidacion-worker@%h \
    --logfile=logs/celery-consolidacion.log \
    --pidfile=pids/celery-consolidacion.pid &

CONSOLIDACION_PID=$!
echo "   └── Worker consolidación iniciado (PID: $CONSOLIDACION_PID)"

# Esperar un momento para que se inicie
sleep 3

# Iniciar worker general EN SEGUNDO PLANO
echo ""
echo "🚀 Iniciando worker GENERAL (cola: celery)..."
celery -A backend worker -Q celery -c 2 \
    --loglevel=info \
    --hostname=general-worker@%h \
    --logfile=logs/celery-general.log \
    --pidfile=pids/celery-general.pid &

GENERAL_PID=$!
echo "   └── Worker general iniciado (PID: $GENERAL_PID)"

# Crear directorios para logs y pids si no existen
mkdir -p logs pids

echo ""
echo "✅ WORKERS CELERY INICIADOS CORRECTAMENTE"
echo "=" * 50
echo "📊 ESTADO:"
echo "   • Worker Consolidación: ACTIVO (PID: $CONSOLIDACION_PID)"
echo "   • Worker General: ACTIVO (PID: $GENERAL_PID)"
echo ""
echo "📋 MONITOREO:"
echo "   • Logs consolidación: tail -f logs/celery-consolidacion.log"
echo "   • Logs general: tail -f logs/celery-general.log"
echo "   • Monitor Celery: celery -A backend monitor"
echo ""
echo "🔧 USO:"
echo "   • La consolidación optimizada usará automáticamente"
echo "     el worker dedicado con 4 procesos paralelos"
echo "   • Otras tareas usarán el worker general"
echo ""
echo "⏹️  Para detener: Ctrl+C o enviar señal SIGTERM"
echo "=" * 50

# Función para mostrar estadísticas cada 30 segundos
mostrar_estadisticas() {
    while true; do
        sleep 30
        echo ""
        echo "📊 ESTADÍSTICAS ($(date '+%H:%M:%S')):"
        
        # Verificar si los procesos siguen activos
        if kill -0 $CONSOLIDACION_PID 2>/dev/null; then
            echo "   ✅ Worker Consolidación: ACTIVO"
        else
            echo "   ❌ Worker Consolidación: DETENIDO"
        fi
        
        if kill -0 $GENERAL_PID 2>/dev/null; then
            echo "   ✅ Worker General: ACTIVO"
        else
            echo "   ❌ Worker General: DETENIDO"
        fi
        
        # Mostrar workers activos de Celery
        echo "   📋 Workers Celery activos:"
        celery -A backend inspect active --timeout=5 2>/dev/null | grep -E "(consolidacion|general)" || echo "     Sin información disponible"
    done
}

# Iniciar monitoring en segundo plano
mostrar_estadisticas &
MONITOR_PID=$!

# Mantener el script corriendo
wait

# Limpiar proceso de monitoring al salir
kill $MONITOR_PID 2>/dev/null
