#!/bin/bash

echo "📊 MONITOR COMPLETO CON GUARDADO DE DATOS"
echo "========================================"

# Configuración
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="monitor_completo_$TIMESTAMP"
mkdir -p "$LOG_DIR"

# Archivos de salida
LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_METRICAS="$LOG_DIR/metricas_sistema.csv"
LOG_EVENTOS="$LOG_DIR/eventos_deteccion.csv"
LOG_RESUMEN="$LOG_DIR/resumen_sesion.txt"

# Variables
EVENTOS_DETECTADOS=0
MUESTRAS_TOTAL=0
INICIO_SESION=$(date '+%Y-%m-%d %H:%M:%S')

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_GENERAL"
}

# Inicializar archivos CSV
echo "timestamp,cpu_sistema,memoria_total_mb,memoria_percent,django_cpu,django_mem_mb,celery_cpu,celery_mem_mb" > "$LOG_METRICAS"
echo "timestamp,tipo_evento,descripcion,duracion_ms" > "$LOG_EVENTOS"

log "📊 Monitor completo iniciado"
log "📁 Directorio de datos: $LOG_DIR"

# Función para capturar métricas del sistema
capturar_metricas() {
    local timestamp=$(date '+%H:%M:%S')
    
    # Métricas del sistema
    local cpu_sistema=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | sed 's/%us,//' | sed 's/%sy,//' | head -1)
    cpu_sistema=${cpu_sistema:-0}
    
    local mem_total_mb=$(free -m | awk 'NR==2{print $3}')
    local mem_percent=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    # Métricas de Docker (simplificadas)
    local django_cpu=$(docker stats --no-stream sgm-django-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | head -1)
    django_cpu=${django_cpu:-0}
    local django_mem=$(docker stats --no-stream sgm-django-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | head -1)
    django_mem=${django_mem:-0}
    
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | head -1)
    celery_cpu=${celery_cpu:-0}
    local celery_mem=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | head -1)
    celery_mem=${celery_mem:-0}
    
    # Guardar en CSV
    echo "$timestamp,$cpu_sistema,$mem_total_mb,$mem_percent,$django_cpu,$django_mem,$celery_cpu,$celery_mem" >> "$LOG_METRICAS"
    
    MUESTRAS_TOTAL=$((MUESTRAS_TOTAL + 1))
}

# Función de detección de eventos
detectar_eventos() {
    local timestamp=$(date '+%H:%M:%S.%3N')
    
    # Buscar en logs recientes
    local django_logs=$(docker logs sgm-django-1 --since="2s" 2>/dev/null | grep -i "rindegastos\|excel\|upload\|step1")
    local celery_logs=$(docker logs sgm-celery_worker-1 --since="2s" 2>/dev/null | grep -i "rg_procesar\|step1\|received\|started")
    
    # Si hay actividad en Django
    if [ ! -z "$django_logs" ]; then
        EVENTOS_DETECTADOS=$((EVENTOS_DETECTADOS + 1))
        echo "🚀 [$timestamp] DJANGO: $(echo "$django_logs" | head -1)"
        echo "$timestamp,DJANGO_UPLOAD,$(echo "$django_logs" | head -1 | tr ',' ' '),N/A" >> "$LOG_EVENTOS"
        log "🚀 EVENTO #$EVENTOS_DETECTADOS - DJANGO: Actividad detectada"
    fi
    
    # Si hay actividad en Celery
    if [ ! -z "$celery_logs" ]; then
        EVENTOS_DETECTADOS=$((EVENTOS_DETECTADOS + 1))
        echo "⚙️  [$timestamp] CELERY: $(echo "$celery_logs" | head -1)"
        echo "$timestamp,CELERY_TASK,$(echo "$celery_logs" | head -1 | tr ',' ' '),200" >> "$LOG_EVENTOS"
        log "⚙️ EVENTO #$EVENTOS_DETECTADOS - CELERY: Tarea procesada"
    fi
}

# Función de resumen final
generar_resumen() {
    local fin_sesion=$(date '+%Y-%m-%d %H:%M:%S')
    local duracion_total=$(( $(date +%s) - $(date -d "$INICIO_SESION" +%s) ))
    
    cat > "$LOG_RESUMEN" << EOF
📊 RESUMEN DE SESIÓN DE MONITOREO SGM
=====================================

🕐 Sesión iniciada: $INICIO_SESION
🕐 Sesión finalizada: $fin_sesion
⏱️  Duración total: ${duracion_total} segundos

📈 ESTADÍSTICAS:
- Total muestras capturadas: $MUESTRAS_TOTAL
- Eventos detectados: $EVENTOS_DETECTADOS
- Frecuencia de muestreo: cada 3 segundos

📁 ARCHIVOS GENERADOS:
- monitor_general.log: Log completo de la sesión
- metricas_sistema.csv: Datos de CPU/RAM por timestamp  
- eventos_deteccion.csv: Log de eventos de procesamiento Excel
- resumen_sesion.txt: Este archivo de resumen

💡 ANÁLISIS RECOMENDADO:
1. Abrir metricas_sistema.csv en Excel/LibreOffice
2. Crear gráficos de CPU y memoria vs tiempo
3. Correlacionar picos con eventos_deteccion.csv
4. Calcular requisitos mínimos basado en picos detectados

🎯 PRÓXIMOS PASOS:
- Ejecutar pruebas con múltiples usuarios simultáneos
- Medir bajo carga de 3 usuarios procesando Excel
- Calcular requisitos hardware definitivos
EOF

    log "📊 Resumen generado en: $LOG_RESUMEN"
}

# Manejo de señales para cleanup
cleanup() {
    echo ""
    log "🛑 Monitor detenido por usuario"
    generar_resumen
    echo ""
    echo "📁 Datos guardados en: $LOG_DIR/"
    echo "   📋 monitor_general.log     - Log principal"
    echo "   📊 metricas_sistema.csv    - Datos CPU/RAM"  
    echo "   🎯 eventos_deteccion.csv   - Eventos Excel"
    echo "   📝 resumen_sesion.txt      - Resumen completo"
    echo ""
    echo "💡 Abre metricas_sistema.csv en Excel para análisis"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
log "🎯 Monitor completo activo - muestreando cada 3 segundos"
echo "📋 Logs en tiempo real:"
echo "   - Métricas del sistema cada 3s"
echo "   - Detección de eventos cada 0.5s"
echo ""
echo "🌐 Sube archivos Excel en: http://172.17.11.18:5174/"
echo "📊 Datos se guardan automáticamente en: $LOG_DIR/"
echo ""

# Loop principal
while true; do
    # Capturar métricas cada 3 segundos
    capturar_metricas
    
    # Detectar eventos cada 0.5 segundos (6 veces por cada métrica)
    for i in {1..6}; do
        detectar_eventos
        sleep 0.5
    done
    
    # Status cada minuto
    if [ $((MUESTRAS_TOTAL % 20)) -eq 0 ]; then
        echo "📊 [$(date '+%H:%M:%S')] Muestras: $MUESTRAS_TOTAL | Eventos: $EVENTOS_DETECTADOS"
    fi
done