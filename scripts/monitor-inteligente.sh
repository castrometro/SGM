#!/bin/bash

# Monitor Inteligente SGM - Detecta automáticamente procesamiento Excel
# Reacciona cuando detecta actividad de Celery y cambios en recursos

set -e

echo "🤖 MONITOR INTELIGENTE SGM - AUTO DETECCIÓN"
echo "============================================"
echo "Fecha: $(date)"
echo "Sistema: $(uname -n)"
echo ""

# Configuración
UMBRAL_CPU=15          # % CPU para detectar procesamiento
UMBRAL_MEMORIA=600     # MB adicionales para detectar procesamiento  
INTERVALO_NORMAL=5     # Segundos entre mediciones normales
INTERVALO_ACTIVO=1     # Segundos cuando detecta procesamiento
TIMEOUT_PROCESAMIENTO=300  # Máximo 5 minutos monitoreando procesamiento

# Archivos de log
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_inteligente_$TIMESTAMP"
mkdir -p "$LOG_DIR"

LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_PROCESAMIENTO="$LOG_DIR/procesamiento_detectado.log"
LOG_ALERTAS="$LOG_DIR/alertas.log"

echo "📁 Logs guardados en: $LOG_DIR/"

# Función para obtener métricas actuales
obtener_metricas() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU total del sistema
    local cpu_total=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | sed 's/%//g' | sed 's/,/./g' | cut -d'.' -f1)
    
    # Memoria del sistema
    local mem_used_mb=$(free -m | awk 'NR==2{print $3}')
    local mem_total_mb=$(free -m | awk 'NR==2{print $2}')
    local mem_percent=$(echo "scale=1; $mem_used_mb * 100 / $mem_total_mb" | bc -l)
    
    # Métricas específicas de Docker/SGM
    local django_cpu=""
    local django_mem=""
    local celery_cpu=""
    local celery_mem=""
    local celery_tasks=""
    
    # Obtener stats de Docker si está disponible
    if command -v docker &> /dev/null && docker ps -q &> /dev/null; then
        # Stats de Django
        local django_stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" sgm-django-1 2>/dev/null || echo "0.00%,0MiB / 0GiB")
        django_cpu=$(echo "$django_stats" | cut -d',' -f1 | sed 's/%//g')
        django_mem=$(echo "$django_stats" | cut -d',' -f2 | cut -d'/' -f1 | sed 's/MiB//g')
        
        # Stats de Celery
        local celery_stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" sgm-celery_worker-1 2>/dev/null || echo "0.00%,0MiB / 0GiB")
        celery_cpu=$(echo "$celery_stats" | cut -d',' -f1 | sed 's/%//g')
        celery_mem=$(echo "$celery_stats" | cut -d',' -f2 | cut -d'/' -f1 | sed 's/MiB//g')
        
        # Tareas activas de Celery
        celery_tasks=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null | grep -c '"uuid"' 2>/dev/null || echo "0")
    fi
    
    # Detectar carga en Redis (indicador de actividad)
    local redis_connections=""
    if command -v docker &> /dev/null && docker ps -q | grep -q sgm-redis; then
        redis_connections=$(docker exec sgm-redis-1 redis-cli -a ${REDIS_PASSWORD:-""} info clients 2>/dev/null | grep "connected_clients:" | cut -d':' -f2 | tr -d '\r' || echo "0")
    fi
    
    # Devolver todas las métricas
    echo "$timestamp,$cpu_total,$mem_used_mb,$mem_percent,$django_cpu,$django_mem,$celery_cpu,$celery_mem,$celery_tasks,$redis_connections"
}

# Función para detectar si hay procesamiento activo
detectar_procesamiento() {
    local metricas="$1"
    
    local cpu_total=$(echo "$metricas" | cut -d',' -f2)
    local celery_cpu=$(echo "$metricas" | cut -d',' -f7)
    local celery_mem=$(echo "$metricas" | cut -d',' -f8)
    local celery_tasks=$(echo "$metricas" | cut -d',' -f9)
    
    # Criterios de detección de procesamiento
    local procesando=false
    
    # Criterio 1: Tareas activas de Celery
    if [ "${celery_tasks:-0}" -gt 0 ]; then
        procesando=true
    fi
    
    # Criterio 2: CPU alto en Celery
    if [ "${celery_cpu:-0}" != "" ] && (( $(echo "${celery_cpu:-0} > 5" | bc -l 2>/dev/null || echo "0") )); then
        procesando=true
    fi
    
    # Criterio 3: Memoria alta en Celery (más de 600MB)
    if [ "${celery_mem:-0}" != "" ] && (( $(echo "${celery_mem:-0} > 600" | bc -l 2>/dev/null || echo "0") )); then
        procesando=true
    fi
    
    # Criterio 4: CPU total del sistema alto
    if [ "${cpu_total:-0}" != "" ] && [ "${cpu_total:-0}" -gt 15 ]; then
        procesando=true
    fi
    
    echo "$procesando"
}

# Función para mostrar estado en tiempo real
mostrar_estado() {
    local metricas="$1"
    local procesando="$2"
    
    local timestamp=$(echo "$metricas" | cut -d',' -f1)
    local cpu_total=$(echo "$metricas" | cut -d',' -f2)
    local mem_used=$(echo "$metricas" | cut -d',' -f3)
    local mem_percent=$(echo "$metricas" | cut -d',' -f4)
    local django_cpu=$(echo "$metricas" | cut -d',' -f5)
    local celery_cpu=$(echo "$metricas" | cut -d',' -f7)
    local celery_tasks=$(echo "$metricas" | cut -d',' -f9)
    
    # Limpiar línea y mostrar estado
    printf "\r\033[K"  # Limpiar línea
    
    if [ "$procesando" = "true" ]; then
        printf "🔥 \033[1;31mPROCESANDO\033[0m | %s | CPU: %s%% | RAM: %sMB (%.1f%%) | Celery: %s%% | Tareas: %s" \
               "$(date '+%H:%M:%S')" \
               "${cpu_total:-0}" \
               "${mem_used:-0}" \
               "${mem_percent:-0}" \
               "${celery_cpu:-0}" \
               "${celery_tasks:-0}"
    else
        printf "💤 \033[1;32mREPOSO\033[0m    | %s | CPU: %s%% | RAM: %sMB (%.1f%%) | Celery: %s%% | Tareas: %s" \
               "$(date '+%H:%M:%S')" \
               "${cpu_total:-0}" \
               "${mem_used:-0}" \
               "${mem_percent:-0}" \
               "${celery_cpu:-0}" \
               "${celery_tasks:-0}"
    fi
}

# Función para procesar evento de procesamiento detectado
procesar_evento_procesamiento() {
    local inicio_procesamiento=$(date '+%Y-%m-%d %H:%M:%S')
    echo ""
    echo ""
    echo "🚨 ¡PROCESAMIENTO DETECTADO! - $inicio_procesamiento"
    echo "=================================================="
    
    # Log del evento
    echo "INICIO_PROCESAMIENTO,$inicio_procesamiento" >> "$LOG_ALERTAS"
    
    # Header para log detallado
    echo "timestamp,cpu_total,mem_mb,mem_percent,django_cpu,django_mem,celery_cpu,celery_mem,celery_tasks,redis_conn" >> "$LOG_PROCESAMIENTO"
    
    local tiempo_procesando=0
    local max_cpu=0
    local max_memoria=0
    local max_celery_cpu=0
    
    echo "📊 Monitoreando cada segundo..."
    echo "Tiempo | CPU% | RAM(MB) | Celery CPU% | Tareas"
    echo "=============================================="
    
    while [ $tiempo_procesando -lt $TIMEOUT_PROCESAMIENTO ]; do
        local metricas=$(obtener_metricas)
        local procesando=$(detectar_procesamiento "$metricas")
        
        # Guardar métricas detalladas
        echo "$metricas" >> "$LOG_PROCESAMIENTO"
        
        # Extraer valores para análisis
        local cpu_actual=$(echo "$metricas" | cut -d',' -f2)
        local mem_actual=$(echo "$metricas" | cut -d',' -f3)
        local celery_cpu_actual=$(echo "$metricas" | cut -d',' -f7)
        
        # Actualizar máximos
        if [ "${cpu_actual:-0}" -gt "$max_cpu" ]; then max_cpu=${cpu_actual:-0}; fi
        if [ "${mem_actual:-0}" -gt "$max_memoria" ]; then max_memoria=${mem_actual:-0}; fi
        if [ "${celery_cpu_actual:-0}" != "" ] && (( $(echo "${celery_cpu_actual:-0} > $max_celery_cpu" | bc -l 2>/dev/null || echo "0") )); then 
            max_celery_cpu=${celery_cpu_actual:-0}
        fi
        
        # Mostrar progreso
        printf "%02d:%02ds | %s%% | %sMB | %s%% | %s\n" \
               $((tiempo_procesando / 60)) \
               $((tiempo_procesando % 60)) \
               "${cpu_actual:-0}" \
               "${mem_actual:-0}" \
               "${celery_cpu_actual:-0}" \
               "$(echo "$metricas" | cut -d',' -f9)"
        
        # Si ya no está procesando, salir
        if [ "$procesando" = "false" ]; then
            echo ""
            echo "✅ Procesamiento terminado después de ${tiempo_procesando}s"
            break
        fi
        
        sleep $INTERVALO_ACTIVO
        tiempo_procesando=$((tiempo_procesando + INTERVALO_ACTIVO))
    done
    
    local fin_procesamiento=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Resumen del procesamiento
    echo ""
    echo "📋 RESUMEN DEL PROCESAMIENTO:"
    echo "============================="
    echo "⏱️  Duración: ${tiempo_procesando} segundos"
    echo "🔥 CPU máximo: ${max_cpu}%"
    echo "💾 RAM máxima: ${max_memoria} MB"
    echo "🌿 Celery CPU máximo: ${max_celery_cpu}%"
    echo "📅 Inicio: $inicio_procesamiento"
    echo "📅 Fin: $fin_procesamiento"
    
    # Log del resumen
    echo "FIN_PROCESAMIENTO,$fin_procesamiento,$tiempo_procesando,$max_cpu,$max_memoria,$max_celery_cpu" >> "$LOG_ALERTAS"
    
    echo ""
    echo "🔄 Volviendo al monitoreo normal..."
    echo ""
}

# Función principal de monitoreo
main() {
    echo "🎯 CONFIGURACIÓN DEL MONITOR:"
    echo "Umbral CPU: ${UMBRAL_CPU}%"
    echo "Umbral Memoria Celery: ${UMBRAL_MEMORIA}MB"
    echo "Intervalo normal: ${INTERVALO_NORMAL}s"
    echo "Intervalo activo: ${INTERVALO_ACTIVO}s"
    echo ""
    
    # Verificar prerrequisitos
    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker no detectado. Algunas métricas no estarán disponibles."
    fi
    
    if ! command -v bc &> /dev/null; then
        echo "⚠️  bc no detectado. Instalando..."
        apt-get update -qq && apt-get install -y bc -qq 2>/dev/null || echo "No se pudo instalar bc"
    fi
    
    # Headers para logs
    echo "timestamp,cpu_total,mem_mb,mem_percent,django_cpu,django_mem,celery_cpu,celery_mem,celery_tasks,redis_conn" > "$LOG_GENERAL"
    
    echo "🚀 INICIANDO MONITOR INTELIGENTE..."
    echo "=================================="
    echo "💡 El monitor detectará automáticamente cuando proceses Excel"
    echo "📊 Métricas guardadas en: $LOG_DIR/"
    echo "🛑 Presiona Ctrl+C para parar"
    echo ""
    echo "Estado | Timestamp | CPU | RAM | Celery | Tareas"
    echo "================================================"
    
    local estado_anterior="false"
    
    while true; do
        local metricas=$(obtener_metricas)
        local procesando=$(detectar_procesamiento "$metricas")
        
        # Guardar métricas generales
        echo "$metricas" >> "$LOG_GENERAL"
        
        # Detectar cambio de estado
        if [ "$procesando" = "true" ] && [ "$estado_anterior" = "false" ]; then
            # Inicio de procesamiento detectado
            procesar_evento_procesamiento
            estado_anterior="true"
        elif [ "$procesando" = "false" ] && [ "$estado_anterior" = "true" ]; then
            # Fin de procesamiento
            estado_anterior="false"
        fi
        
        # Mostrar estado actual
        mostrar_estado "$metricas" "$procesando"
        
        # Determinar intervalo según estado
        if [ "$procesando" = "true" ]; then
            sleep $INTERVALO_ACTIVO
        else
            sleep $INTERVALO_NORMAL
        fi
        
        estado_anterior="$procesando"
    done
}

# Manejar Ctrl+C
trap 'echo -e "\n\n🛑 Monitor detenido por el usuario"; echo "📁 Logs guardados en: $LOG_DIR/"; echo "📊 Para analizar: ls -la $LOG_DIR/"; exit 0' INT

# Ejecutar
main "$@"