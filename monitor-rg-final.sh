#!/bin/bash

echo "🎯 MONITOR FINAL RINDE GASTOS"
echo "==========================="
echo "Detección ultra precisa solo cuando hay tareas reales"
echo ""

# Configuración
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_rg_final_$TIMESTAMP"
mkdir -p "$LOG_DIR"

LOG_EVENTOS="$LOG_DIR/detecciones_rindegastos.log"
LOG_METRICAS="$LOG_DIR/metricas_finales.csv"

FLOWER_URL="http://localhost:5555"
EVENTOS=0

echo "timestamp,tiene_tareas,cpu_celery,detalle" > "$LOG_METRICAS"

echo "🎯 Monitor RindeGastos iniciado"
echo "📁 Logs en: $LOG_DIR"
echo "🌐 Flower: http://172.17.11.18:5555"
echo ""

# Función de detección simplificada y precisa
detectar_rindegastos() {
    local timestamp=$(date '+%H:%M:%S.%3N')
    
    # Obtener tareas activas desde Flower
    local response=$(curl -s "$FLOWER_URL/api/tasks?state=PENDING,RECEIVED,STARTED,RETRY" 2>/dev/null)
    
    # Solo detectar si realmente hay tareas
    local tiene_tareas=false
    local detalle="idle"
    
    # Verificar si hay contenido real en la respuesta
    if echo "$response" | grep -q '"uuid"'; then
        # Hay tareas activas, verificar si son de rinde gastos
        if echo "$response" | grep -q "rg_procesar_step1_task"; then
            tiene_tareas=true
            detalle="RG_STEP1_ACTIVA"
        elif echo "$response" | grep -q "rg_procesar"; then
            tiene_tareas=true
            detalle="RG_PROCESAR_ACTIVA"
        elif echo "$response" | grep -q "contabilidad"; then
            tiene_tareas=true
            detalle="CONTABILIDAD_ACTIVA"
        else
            tiene_tareas=true
            detalle="OTRA_TAREA_ACTIVA"
        fi
    fi
    
    # CPU solo si hay tareas
    local celery_cpu="0%"
    if [ "$tiene_tareas" = true ]; then
        celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | head -1)
        celery_cpu=${celery_cpu:-"0%"}
    fi
    
    # Solo mostrar cuando hay actividad real
    if [ "$tiene_tareas" = true ]; then
        EVENTOS=$((EVENTOS + 1))
        echo "🚀 [$timestamp] DETECCIÓN #$EVENTOS: $detalle | CPU: $celery_cpu"
        echo "[$timestamp] EVENTO #$EVENTOS - $detalle - CPU: $celery_cpu" >> "$LOG_EVENTOS"
        
        # Capturar métricas del sistema durante la actividad
        local cpu_sistema=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | head -1 | tr -d '\n' || echo "0")
        local mem_total=$(free -m | awk 'NR==2{print $3}' || echo "0")
        
        echo "[$timestamp] MÉTRICAS - CPU Sistema: ${cpu_sistema}% | RAM: ${mem_total}MB | CPU Celery: $celery_cpu" >> "$LOG_EVENTOS"
    fi
    
    # Guardar en CSV (solo cuando hay actividad)
    if [ "$tiene_tareas" = true ]; then
        echo "$timestamp,SI,$celery_cpu,$detalle" >> "$LOG_METRICAS"
    fi
}

echo "🎯 Monitoreando tareas reales cada 0.2 segundos..."
echo "💡 Solo mostrará actividad cuando haya tareas REALES ejecutándose"
echo "Sube Excel en: http://172.17.11.18:5174/"
echo ""

# Loop ultra rápido para capturar tareas de 0.2 segundos
contador=0
while true; do
    detectar_rindegastos
    contador=$((contador + 1))
    
    # Status silencioso cada 300 iteraciones (1 minuto)
    if [ $((contador % 300)) -eq 0 ]; then
        printf "\r⏱️  [$(date '+%H:%M:%S')] Monitoreando... checks: $contador | detecciones: $EVENTOS"
    fi
    
    sleep 0.2
done