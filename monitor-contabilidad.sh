#!/bin/bash

echo "🌸 MONITOR FLOWER - COLA CONTABILIDAD"
echo "===================================="
echo "Detectando tareas específicamente en contabilidad_queue"
echo ""

# Configuración
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_contabilidad_$TIMESTAMP"
mkdir -p "$LOG_DIR"

LOG_EVENTOS="$LOG_DIR/eventos_contabilidad.log"
LOG_METRICAS="$LOG_DIR/metricas_contabilidad.csv"

FLOWER_URL="http://localhost:5555"
EVENTOS=0

echo "timestamp,tareas_contabilidad,tareas_total,cpu_celery,descripcion" > "$LOG_METRICAS"

echo "🌸 Monitor Contabilidad iniciado"
echo "📁 Logs en: $LOG_DIR"
echo "🌐 Flower UI: http://172.17.11.18:5555"
echo "🎯 Detectando específicamente: contabilidad_queue"
echo ""

# Función para detectar tareas de contabilidad
check_contabilidad() {
    local timestamp=$(date '+%H:%M:%S.%3N')
    
    # Obtener todas las tareas activas desde Flower
    local response=$(curl -s "$FLOWER_URL/api/tasks?state=PENDING,RECEIVED,STARTED,RETRY" 2>/dev/null)
    
    # Contar tareas totales
    local tareas_totales=$(echo "$response" | grep -o '"uuid"' | wc -l || echo "0")
    
    # Buscar tareas específicas de contabilidad
    local tareas_contabilidad=$(echo "$response" | grep -c "contabilidad" || echo "0")
    
    # Buscar específicamente rg_procesar
    local tiene_rg_procesar="NO"
    if echo "$response" | grep -q "rg_procesar"; then
        tiene_rg_procesar="SI"
    fi
    
    # Buscar step1_task
    local tiene_step1="NO"  
    if echo "$response" | grep -q "step1_task"; then
        tiene_step1="SI"
    fi
    
    # CPU de Celery
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | head -1)
    celery_cpu=${celery_cpu:-"0%"}
    
    # Detectar actividad específica de contabilidad
    if [ "$tareas_contabilidad" != "0" ] || [ "$tiene_rg_procesar" = "SI" ] || [ "$tiene_step1" = "SI" ]; then
        EVENTOS=$((EVENTOS + 1))
        echo "🚀 [$timestamp] CONTABILIDAD ACTIVA! Total:$tareas_totales | Conta:$tareas_contabilidad | RG:$tiene_rg_procesar | Step1:$tiene_step1 | CPU:$celery_cpu"
        echo "[$timestamp] EVENTO #$EVENTOS - Contabilidad: $tareas_contabilidad | RG_Procesar: $tiene_rg_procesar | Step1: $tiene_step1" >> "$LOG_EVENTOS"
        
        # También mostrar el JSON raw para debug
        echo "[$timestamp] RAW_RESPONSE: $response" >> "$LOG_EVENTOS"
    fi
    
    # Guardar métricas
    echo "$timestamp,$tareas_contabilidad,$tareas_totales,$celery_cpu,RG:$tiene_rg_procesar|Step1:$tiene_step1" >> "$LOG_METRICAS"
    
    # Status periódico
    if [ $((EVENTOS % 5)) -eq 0 ] && [ "$EVENTOS" -gt 0 ]; then
        echo "📊 [$timestamp] Eventos de contabilidad detectados: $EVENTOS"
    fi
}

# También vamos a verificar directamente el worker
check_workers() {
    echo "🔍 Verificando workers activos:"
    docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null | head -20
    echo ""
    
    echo "🔍 Workers registrados:"
    docker exec sgm-celery_worker-1 celery -A sgm_backend inspect registered 2>/dev/null | grep -A5 -B5 "contabilidad"
    echo ""
}

echo "🎯 Monitoreando cola de contabilidad cada 0.5 segundos..."
echo "Sube Excel en: http://172.17.11.18:5174/"
echo ""

# Verificar workers inicialmente
check_workers

# Loop de detección rápida
contador=0
while true; do
    check_contabilidad
    contador=$((contador + 1))
    
    # Status cada 60 iteraciones (30 segundos)
    if [ $((contador % 60)) -eq 0 ]; then
        printf "\r🔍 [$(date '+%H:%M:%S')] Checks: $contador | Eventos contabilidad: $EVENTOS"
        # Re-verificar workers cada minuto
        if [ $((contador % 120)) -eq 0 ]; then
            echo ""
            check_workers
        fi
    fi
    
    sleep 0.5
done