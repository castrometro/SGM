#!/bin/bash

# Monitor Simple y Eficaz para Procesamiento Excel
# Se enfoca específicamente en detectar tareas Celery y cambios en recursos
# Uso: ./monitor-excel-simple.sh

echo "🎯 MONITOR EXCEL SGM - DETECCIÓN INTELIGENTE"
echo "==========================================="

# Configuración
LOG_DIR="monitor_$(date +%H%M%S)"
mkdir -p "$LOG_DIR"

ESTADO_ANTERIOR="idle"
INICIO_PROCESAMIENTO=""
CONTADOR=0

# Archivos de log
CSV_FILE="$LOG_DIR/metricas.csv"
LOG_FILE="$LOG_DIR/eventos.log"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para detectar procesamiento
detectar_procesamiento() {
    # Método 1: Verificar tareas Celery directamente
    celery_tasks=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null | grep -c '"uuid"' || echo "0")
    
    # Método 2: Verificar CPU del worker Celery
    celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' || echo "0")
    
    # Método 3: Verificar logs recientes de Django para uploads
    uploads_recientes=$(docker logs sgm-django-1 --since="30s" 2>/dev/null | grep -i -E "(upload|excel|rindegastos|procesando)" | wc -l)
    
    # Convertir a entero para evitar errores
    celery_tasks=${celery_tasks:-0}
    celery_cpu=${celery_cpu:-0}
    uploads_recientes=${uploads_recientes:-0}
    
    # Obtener parte entera del CPU
    celery_cpu_int=${celery_cpu%.*}
    celery_cpu_int=${celery_cpu_int:-0}
    
    # Decidir si hay procesamiento
    if [ "$celery_tasks" -gt 0 ] || [ "$celery_cpu_int" -gt 2 ] || [ "$uploads_recientes" -gt 0 ]; then
        echo "procesando,$celery_tasks,$celery_cpu,$uploads_recientes"
        return 0
    else
        echo "idle,0,$celery_cpu,0"
        return 1
    fi
}

# Función para capturar métricas
capturar_metricas() {
    timestamp=$(date '+%H:%M:%S')
    
    # Métricas del sistema con valores por defecto
    cpu_sistema=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | cut -d'%' -f1)
    cpu_sistema=${cpu_sistema:-0}
    
    mem_total=$(free -m | awk 'NR==2{print $3}')
    mem_total=${mem_total:-0}
    
    # Métricas Docker específicas con manejo de errores
    django_stats=$(docker stats --no-stream sgm-django-1 --format "{{.CPUPerc}},{{.MemUsage}}" 2>/dev/null | sed 's/%//g' | sed 's/MiB.*//g' || echo "0,0")
    celery_stats=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}},{{.MemUsage}}" 2>/dev/null | sed 's/%//g' | sed 's/MiB.*//g' || echo "0,0")
    
    django_cpu=$(echo "$django_stats" | cut -d',' -f1)
    django_cpu=${django_cpu:-0}
    django_mem=$(echo "$django_stats" | cut -d',' -f2)
    django_mem=${django_mem:-0}
    celery_cpu=$(echo "$celery_stats" | cut -d',' -f1)
    celery_cpu=${celery_cpu:-0}
    celery_mem=$(echo "$celery_stats" | cut -d',' -f2)
    celery_mem=${celery_mem:-0}
    
    echo "$timestamp,$cpu_sistema,$mem_total,$django_cpu,$django_mem,$celery_cpu,$celery_mem" >> "$CSV_FILE"
    echo "$cpu_sistema,$mem_total,$celery_cpu"
}

# Inicializar CSV
echo "timestamp,cpu_sistema,mem_total_mb,django_cpu,django_mem_mb,celery_cpu,celery_mem_mb" > "$CSV_FILE"

log "🚀 Monitor iniciado"
log "📁 Logs en: $LOG_DIR/"

echo ""
echo "🔍 ESPERANDO PROCESAMIENTO DE EXCEL..."
echo "💡 Sube un archivo en: http://localhost:5174"
echo "⚡ El monitor detectará automáticamente cuando inicie"
echo ""
echo "Estado: ESPERANDO..."

while true; do
    # Detectar estado actual
    deteccion=$(detectar_procesamiento)
    estado=$(echo "$deteccion" | cut -d',' -f1)
    celery_tasks=$(echo "$deteccion" | cut -d',' -f2)
    celery_cpu=$(echo "$deteccion" | cut -d',' -f3)
    uploads=$(echo "$deteccion" | cut -d',' -f4)
    
    # Capturar métricas
    metricas=$(capturar_metricas)
    cpu_sistema=$(echo "$metricas" | cut -d',' -f1)
    memoria=$(echo "$metricas" | cut -d',' -f2)
    celery_cpu_actual=$(echo "$metricas" | cut -d',' -f3)
    
    # Manejar transiciones
    if [ "$estado" = "procesando" ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
        INICIO_PROCESAMIENTO=$(date '+%H:%M:%S')
        CONTADOR=0
        log "🔥 ¡PROCESAMIENTO EXCEL DETECTADO!"
        log "   Tareas Celery: $celery_tasks | CPU Celery: ${celery_cpu}% | Uploads: $uploads"
        
        echo ""
        echo "🔥🔥🔥 PROCESAMIENTO DETECTADO 🔥🔥🔥"
        echo "Hora inicio: $INICIO_PROCESAMIENTO"
        echo "Capturando métricas detalladas..."
        echo "=================================="
        
    elif [ "$estado" = "idle" ] && [ "$ESTADO_ANTERIOR" = "procesando" ]; then
        duracion=$(echo "scale=1; $CONTADOR * 3 / 60" | bc)
        log "✅ PROCESAMIENTO COMPLETADO"
        log "   Duración: ${duracion} minutos | Muestras: $CONTADOR"
        
        # Análisis rápido
        echo ""
        echo "✅✅✅ PROCESAMIENTO COMPLETADO ✅✅✅"
        echo "Duración: ${duracion} minutos"
        echo ""
        echo "📊 ANÁLISIS RÁPIDO:"
        
        # CPU máximo durante procesamiento
        max_cpu=$(tail -n $CONTADOR "$CSV_FILE" | awk -F',' '{if($6>max) max=$6} END {print max}')
        max_mem=$(tail -n $CONTADOR "$CSV_FILE" | awk -F',' '{if($7>max) max=$7} END {print max}')
        
        echo "   CPU máximo Celery: ${max_cpu}%"
        echo "   RAM máxima Celery: ${max_mem}MB"
        echo "   Proyección 3 usuarios: CPU ~$(echo "$max_cpu * 3" | bc)%, RAM ~$(echo "scale=1; $max_mem * 3 / 1024" | bc)GB"
        echo ""
        echo "📁 Datos detallados en: $LOG_DIR/"
        echo "=================================="
        echo ""
        echo "🔍 ESPERANDO NUEVO PROCESAMIENTO..."
    fi
    
    # Mostrar estado en pantalla
    if [ "$estado" = "procesando" ]; then
        CONTADOR=$((CONTADOR + 1))
        duracion_actual=$(echo "scale=1; $CONTADOR * 3 / 60" | bc)
        printf "\r$(date '+%H:%M:%S') - CPU: %s%% | RAM: %sMB | Celery CPU: %s%% | Duración: %s min | Tasks: %s" \
            "$cpu_sistema" "$memoria" "$celery_cpu_actual" "$duracion_actual" "$celery_tasks"
    else
        # Modo silencioso cuando no hay procesamiento
        if (( $CONTADOR % 20 == 0 )); then
            printf "\r🔍 Esperando... $(date '+%H:%M:%S') - Sistema: CPU %s%%, RAM %sMB    " \
                "$cpu_sistema" "$memoria"
        fi
        CONTADOR=$((CONTADOR + 1))
    fi
    
    ESTADO_ANTERIOR="$estado"
    sleep 3
done