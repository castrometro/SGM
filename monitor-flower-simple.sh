#!/bin/bash

echo "🌸 MONITOR FLOWER SIMPLE"
echo "======================="
echo ""

# Configuración
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_flower_simple_$TIMESTAMP"
mkdir -p "$LOG_DIR"

LOG_EVENTOS="$LOG_DIR/eventos_tareas.log"
LOG_METRICAS="$LOG_DIR/metricas_simples.csv"

FLOWER_URL="http://localhost:5555"
EVENTOS=0

echo "timestamp,estado_tareas,cpu_celery,descripcion" > "$LOG_METRICAS"

echo "🌸 Monitor Flower Simple iniciado"
echo "📁 Logs en: $LOG_DIR"
echo "🌐 Flower UI: http://172.17.11.18:5555"
echo ""

# Función simple para obtener tareas
check_flower() {
    local timestamp=$(date '+%H:%M:%S')
    
    # Obtener tareas activas desde Flower API
    local response=$(curl -s "$FLOWER_URL/api/tasks?state=PENDING,RECEIVED,STARTED" 2>/dev/null)
    
    # Contar tareas simples
    local num_tareas=$(echo "$response" | grep -o '"uuid"' | wc -l || echo "0")
    
    # Buscar rindegastos específicamente  
    local tiene_rindegastos="NO"
    if echo "$response" | grep -q "rg_procesar_step1_task"; then
        tiene_rindegastos="SI"
    fi
    
    # CPU de Celery simple
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | head -1)
    celery_cpu=${celery_cpu:-"0%"}
    
    # Si hay tareas o RindeGastos activo
    if [ "$num_tareas" != "0" ] || [ "$tiene_rindegastos" = "SI" ]; then
        EVENTOS=$((EVENTOS + 1))
        echo "🚀 [$timestamp] ACTIVIDAD! Tareas: $num_tareas | RG: $tiene_rindegastos | CPU: $celery_cpu"
        echo "[$timestamp] EVENTO #$EVENTOS - Tareas activas: $num_tareas | RindeGastos: $tiene_rindegastos" >> "$LOG_EVENTOS"
    fi
    
    # Guardar métricas simples
    echo "$timestamp,$num_tareas,$celery_cpu,RG:$tiene_rindegastos" >> "$LOG_METRICAS"
    
    # Status cada 10 iteraciones
    if [ $((EVENTOS % 10)) -eq 0 ] && [ "$EVENTOS" -gt 0 ]; then
        echo "📊 [$timestamp] Total eventos detectados: $EVENTOS"
    fi
}

echo "🎯 Monitoreando Flower API cada 1 segundo..."
echo "Sube Excel en: http://172.17.11.18:5174/"
echo ""

# Loop simple
contador=0
while true; do
    check_flower
    contador=$((contador + 1))
    
    # Status cada 30 segundos
    if [ $((contador % 30)) -eq 0 ]; then
        printf "\r🔍 [$(date '+%H:%M:%S')] Monitoreando... checks: $contador | eventos: $EVENTOS"
    fi
    
    sleep 1
done