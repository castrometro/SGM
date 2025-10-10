#!/bin/bash

echo "⚡ MONITOR ALTA FRECUENCIA - DETECCIÓN RÁPIDA"
echo "============================================="
echo "Muestreo cada 0.1 segundos para capturar tareas rápidas"
echo ""

# Variables
LOG_DIR="monitor_rapido_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_EVENTOS="$LOG_DIR/eventos_detectados.log"

# Contadores
CONTADOR=0
EVENTOS_DETECTADOS=0

# Estado
PROCESAMIENTO_DETECTADO=false
INICIO_PROCESAMIENTO=""

# Función de logging
log() {
    echo "[$(date '+%H:%M:%S.%3N')] $1" | tee -a "$LOG_GENERAL"
}

log "⚡ Monitor de alta frecuencia iniciado"
log "📁 Logs en: $LOG_DIR"

echo "🎯 DETECTANDO ACTIVIDAD CADA 0.1 SEGUNDOS..."
echo "Sube un archivo Excel en: http://172.17.11.18:5174/"
echo ""

# Capturar estado inicial
CPU_BASE=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" | sed 's/%//' | tr -d '\n\r' | head -c 10)
CPU_BASE=${CPU_BASE:-0}

# Función de detección rápida
detectar_actividad() {
    local timestamp=$(date '+%H:%M:%S.%3N')
    
    # CPU actual
    local cpu_actual=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" | sed 's/%//' | tr -d '\n\r' | head -c 10)
    cpu_actual=${cpu_actual:-0}
    
    # Calcular diferencia de CPU
    local cpu_diff=$(echo "$cpu_actual - $CPU_BASE" | bc -l 2>/dev/null || echo "0")
    
    # Detectar tareas Celery (más rápido)
    local tareas_activas=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null | grep -c '"uuid"' || echo "0")
    
    # Logs recientes (últimos 2 segundos)
    local logs_django=$(docker logs sgm-django-1 --since="2s" 2>/dev/null | grep -i -E "(rindegastos|step1|excel|upload)" | wc -l)
    local logs_celery=$(docker logs sgm-celery_worker-1 --since="2s" 2>/dev/null | grep -i -E "(rg_procesar|step1|task.*received)" | wc -l)
    
    # Detección por múltiples señales
    local actividad_detectada=false
    local razon=""
    
    # 1. Tareas activas
    if [ "$tareas_activas" -gt 0 ]; then
        actividad_detectada=true
        razon="$razon[Tareas:$tareas_activas]"
    fi
    
    # 2. Spike de CPU (diferencia > 1%)
    if (( $(echo "$cpu_diff > 1" | bc -l) )); then
        actividad_detectada=true
        razon="$razon[CPU:+${cpu_diff}%]"
    fi
    
    # 3. Logs recientes
    if [ "$logs_django" -gt 0 ] || [ "$logs_celery" -gt 0 ]; then
        actividad_detectada=true
        razon="$razon[Logs:D$logs_django/C$logs_celery]"
    fi
    
    # Actualizar estado
    if [ "$actividad_detectada" = true ]; then
        if [ "$PROCESAMIENTO_DETECTADO" = false ]; then
            PROCESAMIENTO_DETECTADO=true
            INICIO_PROCESAMIENTO="$timestamp"
            EVENTOS_DETECTADOS=$((EVENTOS_DETECTADOS + 1))
            
            echo "🚀 [$timestamp] INICIO PROCESAMIENTO #$EVENTOS_DETECTADOS $razon" | tee -a "$LOG_EVENTOS"
            log "🚀 EVENTO #$EVENTOS_DETECTADOS - INICIO: $razon"
        fi
    else
        if [ "$PROCESAMIENTO_DETECTADO" = true ]; then
            local duracion=$(echo "scale=3; ($(date +%s.%3N) - $(date -d "$INICIO_PROCESAMIENTO" +%s.%3N))" | bc -l 2>/dev/null || echo "N/A")
            
            echo "✅ [$timestamp] FIN PROCESAMIENTO #$EVENTOS_DETECTADOS (${duracion}s)" | tee -a "$LOG_EVENTOS"
            log "✅ EVENTO #$EVENTOS_DETECTADOS - FIN: Duración ${duracion}s"
            
            PROCESAMIENTO_DETECTADO=false
        fi
    fi
    
    # Mostrar estado cada 50 muestras (5 segundos)
    if [ $((CONTADOR % 50)) -eq 0 ]; then
        printf "\r🔍 [%s] CPU:%s%% Base:%s%% Eventos:%d Muestras:%d" "$timestamp" "$cpu_actual" "$CPU_BASE" "$EVENTOS_DETECTADOS" "$CONTADOR"
    fi
}

# Manejo de señales
cleanup() {
    echo ""
    log "🛑 Monitor detenido"
    log "📊 Total eventos detectados: $EVENTOS_DETECTADOS"
    log "📊 Total muestras: $CONTADOR"
    echo ""
    echo "📁 Resultados en: $LOG_DIR/"
    echo "   - monitor_general.log"
    echo "   - eventos_detectados.log"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Loop principal - muestreo cada 0.1 segundos
while true; do
    detectar_actividad
    CONTADOR=$((CONTADOR + 1))
    sleep 0.1
done