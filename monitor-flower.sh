#!/bin/bash

echo "🌸 MONITOR SGM CON FLOWER API"
echo "============================"
echo "Usando Flower API para detección precisa de tareas Celery"
echo ""

# Configuración
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_flower_$TIMESTAMP"
mkdir -p "$LOG_DIR"

# Archivos de salida
LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_METRICAS="$LOG_DIR/metricas_sistema.csv" 
LOG_TAREAS="$LOG_DIR/tareas_celery.csv"
LOG_EVENTOS="$LOG_DIR/eventos_procesamiento.log"

# Variables
FLOWER_URL="http://localhost:5555"
EVENTOS_DETECTADOS=0
MUESTRAS_TOTAL=0
TAREAS_ACTIVAS_ANTERIOR=0

# Función de logging
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_GENERAL"
}

# Inicializar archivos CSV
echo "timestamp,cpu_sistema,memoria_total_mb,memoria_percent,django_cpu,django_mem_mb,celery_cpu,celery_mem_mb" > "$LOG_METRICAS"
echo "timestamp,task_id,task_name,state,worker,runtime_seconds" > "$LOG_TAREAS"

log "🌸 Monitor con Flower API iniciado"
log "📁 Directorio de datos: $LOG_DIR"
log "🌐 Flower UI: $FLOWER_URL"

# Función para obtener tareas activas desde Flower
obtener_tareas_flower() {
    # Obtener tareas activas via API de Flower
    local tareas_json=$(curl -s "$FLOWER_URL/api/tasks?state=PENDING,RECEIVED,STARTED,RETRY" 2>/dev/null || echo "{}")
    
    # Contar tareas totales
    local total_tareas=$(echo "$tareas_json" | grep -o '"uuid"' | wc -l)
    
    # Buscar específicamente tareas de rinde gastos
    local tareas_rindegastos=$(echo "$tareas_json" | grep -c "rg_procesar_step1_task" || echo "0")
    
    # Buscar tareas de contabilidad en general
    local tareas_contabilidad=$(echo "$tareas_json" | grep -c "contabilidad\." || echo "0")
    
    echo "$total_tareas,$tareas_rindegastos,$tareas_contabilidad"
}

# Función para capturar métricas del sistema
capturar_metricas() {
    local timestamp=$(date '+%H:%M:%S')
    
    # Métricas del sistema
    local cpu_sistema=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | sed 's/%us,//' | sed 's/%sy,//' | head -1 | tr -d '\n')
    cpu_sistema=${cpu_sistema:-0}
    
    local mem_total_mb=$(free -m | awk 'NR==2{print $3}')
    local mem_percent=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    # Métricas de Docker 
    local django_cpu=$(docker stats --no-stream sgm-django-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | head -1 | tr -d '\n')
    django_cpu=${django_cpu:-0}
    local django_mem=$(docker stats --no-stream sgm-django-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | head -1 | tr -d '\n')
    django_mem=${django_mem:-0}
    
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | head -1 | tr -d '\n')
    celery_cpu=${celery_cpu:-0}
    local celery_mem=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | head -1 | tr -d '\n')
    celery_mem=${celery_mem:-0}
    
    # Obtener tareas desde Flower
    local tareas_info=$(obtener_tareas_flower)
    local total_tareas=$(echo "$tareas_info" | cut -d',' -f1)
    local tareas_rindegastos=$(echo "$tareas_info" | cut -d',' -f2)
    local tareas_contabilidad=$(echo "$tareas_info" | cut -d',' -f3)
    
    # Detectar cambios en tareas activas
    if [ "$total_tareas" -gt "$TAREAS_ACTIVAS_ANTERIOR" ]; then
        EVENTOS_DETECTADOS=$((EVENTOS_DETECTADOS + 1))
        echo "🚀 [$timestamp] NUEVA TAREA CELERY DETECTADA!" | tee -a "$LOG_EVENTOS"
        log "🚀 EVENTO #$EVENTOS_DETECTADOS - Tareas activas: $total_tareas (RG: $tareas_rindegastos, Conta: $tareas_contabilidad)"
        
        # Guardar detalle de tarea
        echo "$timestamp,NUEVA_TAREA,rg_procesar_step1_task,STARTED,worker1,0" >> "$LOG_TAREAS"
    elif [ "$total_tareas" -lt "$TAREAS_ACTIVAS_ANTERIOR" ] && [ "$TAREAS_ACTIVAS_ANTERIOR" -gt 0 ]; then
        echo "✅ [$timestamp] TAREA CELERY COMPLETADA!" | tee -a "$LOG_EVENTOS"
        log "✅ Tarea completada - Tareas activas restantes: $total_tareas"
    fi
    
    TAREAS_ACTIVAS_ANTERIOR=$total_tareas
    
    # Guardar métricas en CSV
    echo "$timestamp,$cpu_sistema,$mem_total_mb,$mem_percent,$django_cpu,$django_mem,$celery_cpu,$celery_mem" >> "$LOG_METRICAS"
    
    MUESTRAS_TOTAL=$((MUESTRAS_TOTAL + 1))
    
    # Mostrar status en línea
    printf "\r🔍 [$timestamp] CPU: ${cpu_sistema}%% | RAM: ${mem_total_mb}MB | Tareas: $total_tareas | Eventos: $EVENTOS_DETECTADOS"
}

# Cleanup function
cleanup() {
    echo ""
    log "🛑 Monitor detenido por usuario"
    echo ""
    echo "📁 Datos guardados en: $LOG_DIR/"
    echo "   📋 monitor_general.log        - Log principal"
    echo "   📊 metricas_sistema.csv       - CPU/RAM por timestamp"
    echo "   ⚙️  tareas_celery.csv          - Tareas Celery detectadas"
    echo "   🎯 eventos_procesamiento.log  - Eventos de procesamiento"
    echo ""
    echo "🌸 También revisa Flower UI: $FLOWER_URL"
    echo "💡 Abre metricas_sistema.csv en Excel para análisis"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "🎯 MONITOR ACTIVO - Detectando via Flower API"
echo "📊 Muestreando cada 2 segundos para mayor precisión"
echo ""
echo "🌐 Sube archivos Excel en: http://172.17.11.18:5174/"
echo "🌸 Monitorea tareas en: $FLOWER_URL"
echo "📁 Datos en: $LOG_DIR/"
echo ""

# Loop principal - cada 2 segundos para mejor detección
while true; do
    capturar_metricas
    sleep 2
done