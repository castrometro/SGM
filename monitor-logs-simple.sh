#!/bin/bash

echo "📡 MONITOR LOGS ULTRA RÁPIDO"
echo "============================"
echo "Detectando por logs cada 0.1s"
echo ""

# Variables
LOG_DIR="monitor_logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
LOG_GENERAL="$LOG_DIR/detecciones.log"

EVENTOS=0
ULTIMA_DETECCION=""

# Función de logging
log_evento() {
    local timestamp=$(date '+%H:%M:%S.%3N')
    echo "[$timestamp] $1" | tee -a "$LOG_GENERAL"
}

echo "🎯 Monitoreando logs cada 0.1 segundos..."
echo "Sube archivo Excel en: http://172.17.11.18:5174/"
echo ""

# Obtener timestamp inicial para logs
INICIO=$(date -d "1 minute ago" --iso-8601=seconds)

while true; do
    # Buscar en logs de Django (últimos 2 segundos)
    LOGS_DJANGO=$(docker logs sgm-django-1 --since="2s" 2>/dev/null | grep -i -E "(rindegastos|excel|upload|step1)" | wc -l)
    
    # Buscar en logs de Celery (últimos 2 segundos)  
    LOGS_CELERY=$(docker logs sgm-celery_worker-1 --since="2s" 2>/dev/null | grep -i -E "(rg_procesar|step1|task.*received|task.*started)" | wc -l)
    
    # Detectar tareas activas
    TAREAS=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null | grep -c '"task"' 2>/dev/null || echo "0")
    
    # Si hay actividad
    if [ "$LOGS_DJANGO" -gt 0 ] || [ "$LOGS_CELERY" -gt 0 ] || [ "$TAREAS" -gt 0 ]; then
        EVENTOS=$((EVENTOS + 1))
        TIMESTAMP=$(date '+%H:%M:%S.%3N')
        
        # Solo mostrar si no es muy seguido (evitar spam)
        if [ -z "$ULTIMA_DETECCION" ] || [ $(($(date +%s) - $(date -d "$ULTIMA_DETECCION" +%s))) -gt 1 ]; then
            echo "🚀 [$TIMESTAMP] EVENTO #$EVENTOS - Django:$LOGS_DJANGO Celery:$LOGS_CELERY Tareas:$TAREAS"
            log_evento "DETECCIÓN #$EVENTOS - Django:$LOGS_DJANGO Celery:$LOGS_CELERY Tareas:$TAREAS"
            ULTIMA_DETECCION="$TIMESTAMP"
        fi
    fi
    
    sleep 0.1
done