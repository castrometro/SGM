#!/bin/bash

# Monitor Inteligente de Procesamiento Excel SGM
# Detecta automáticamente cuando se procesan archivos Excel y captura métricas
# Autor: SGM Team
# Uso: ./monitor-excel-inteligente.sh

set -e

echo "🤖 MONITOR INTELIGENTE SGM - DETECCIÓN AUTOMÁTICA DE PROCESAMIENTO EXCEL"
echo "========================================================================"

# Configuración
INTERVALO_MONITOREO=3  # segundos
UMBRAL_CPU_CELERY=3  # % CPU en Celery para detectar procesamiento
UMBRAL_CPU_SISTEMA=50  # % CPU total del sistema para detectar procesamiento
UMBRAL_MEMORIA_PROCESAMIENTO=100  # MB adicionales para detectar procesamiento
TIEMPO_MAX_PROCESAMIENTO=600  # 10 minutos máximo
LOG_DIR="monitor_excel_$(date +%Y%m%d_%H%M%S)"

# Crear directorio de logs
mkdir -p "$LOG_DIR"
echo "📁 Logs guardados en: $LOG_DIR/"

# Archivos de log
LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_METRICAS="$LOG_DIR/metricas_detalladas.csv"
LOG_EVENTOS="$LOG_DIR/eventos_procesamiento.log"
LOG_CELERY="$LOG_DIR/celery_tasks.log"

# Estado del monitor
ESTADO_ANTERIOR="idle"
PROCESAMIENTO_INICIADO=""
CONTADOR_PROCESAMIENTO=0
METRICAS_BASE_CPU=0
METRICAS_BASE_MEM=0

# Función para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_GENERAL"
}

# Función para capturar métricas del sistema
capturar_metricas_sistema() {
    local timestamp=$(date '+%H:%M:%S')
    
    # CPU total del sistema
    local cpu_total=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | sed 's/%us,//' | sed 's/%sy,//' | awk '{print $1}')
    
    # Memoria total
    local mem_total_mb=$(free -m | awk 'NR==2{print $3}')
    local mem_percent=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    # Docker stats específicos
    local django_cpu=$(docker stats --no-stream sgm-django-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' || echo "0")
    local django_mem=$(docker stats --no-stream sgm-django-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' || echo "0")
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' || echo "0")
    local celery_mem=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' || echo "0")
    
    # Guardar en CSV
    echo "$timestamp,$cpu_total,$mem_total_mb,$mem_percent,$django_cpu,$django_mem,$celery_cpu,$celery_mem" >> "$LOG_METRICAS"
    
    # Retornar valores para detección
    echo "$cpu_total,$mem_total_mb,$django_cpu,$celery_cpu"
}

# Función para detectar tareas de Celery activas
detectar_celery_activo() {
    local celery_inspect=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null || echo "{}")
    local tareas_activas=$(echo "$celery_inspect" | grep -o '"uuid"' | wc -l)
    
    if [ "$tareas_activas" -gt 0 ]; then
        echo "$tareas_activas"
        echo "[$(date '+%H:%M:%S')] Celery - $tareas_activas tareas activas" >> "$LOG_CELERY"
        return 0
    else
        return 1
    fi
}

# Función para detectar procesamiento de Excel
detectar_procesamiento_excel() {
    local metricas="$1"
    local cpu_total=$(echo "$metricas" | cut -d',' -f1)
    local mem_total=$(echo "$metricas" | cut -d',' -f2)
    local django_cpu=$(echo "$metricas" | cut -d',' -f3)
    local celery_cpu=$(echo "$metricas" | cut -d',' -f4)
    
    # Convertir a números enteros para comparación
    cpu_total=${cpu_total%.*}
    celery_cpu=${celery_cpu%.*}
    
    # Detectar tareas Celery
    local celery_activo=false
    if detectar_celery_activo >/dev/null 2>&1; then
        celery_activo=true
    fi
    
    # Condiciones para detectar procesamiento
    local procesando=false
    local razon=""
    
    # Condición 1: CPU alto en Celery (MÁS ESPECÍFICO)
    if (( $(echo "$celery_cpu > $UMBRAL_CPU_CELERY" | bc -l) )); then
        procesando=true
        razon="CPU alto en Celery (${celery_cpu}%)"
    fi
    
    # Condición 2: Tareas Celery activas (MÁS CONFIABLE)
    if [ "$celery_activo" = true ]; then
        procesando=true
        razon="Tareas Celery activas"
    fi
    
    # Condición 3: CPU total del sistema MUY alto (solo picos grandes)
    if (( $(echo "$cpu_total > $UMBRAL_CPU_SISTEMA" | bc -l) )) && (( $(echo "$celery_cpu > 1" | bc -l) )); then
        procesando=true
        razon="CPU sistema alto (${cpu_total}%) con Celery activo"
    fi
    
    # Solo loggear cuando hay cambio de estado o detección específica
    if [ "$procesando" = true ] && [ "$razon" != "" ]; then
        if [ "$ESTADO_ANTERIOR" = "idle" ]; then
            log "🔍 DETECCIÓN: $razon"
        fi
    fi
    
    if [ "$procesando" = true ]; then
        echo "procesando"
    else
        echo "idle"
    fi
}

# Función para manejar inicio de procesamiento
iniciar_deteccion_procesamiento() {
    PROCESAMIENTO_INICIADO=$(date '+%H:%M:%S')
    CONTADOR_PROCESAMIENTO=0
    
    log "🚀 ¡PROCESAMIENTO EXCEL DETECTADO!"
    log "   Hora inicio: $PROCESAMIENTO_INICIADO"
    log "   Iniciando captura intensiva de métricas..."
    
    echo "evento,timestamp,descripcion" > "$LOG_DIR/eventos_detallados.csv"
    echo "inicio_procesamiento,$(date '+%H:%M:%S'),Procesamiento Excel iniciado" >> "$LOG_DIR/eventos_detallados.csv"
    
    # Notificación visual
    echo ""
    echo "🔥🔥🔥 PROCESAMIENTO DETECTADO 🔥🔥🔥"
    echo "Capturando métricas cada $INTERVALO_MONITOREO segundos..."
    echo "Presiona Ctrl+C para parar el monitor"
    echo "======================================"
}

# Función para manejar fin de procesamiento
finalizar_deteccion_procesamiento() {
    local tiempo_fin=$(date '+%H:%M:%S')
    local duracion_segundos=$CONTADOR_PROCESAMIENTO
    local duracion_minutos=$(echo "scale=1; $duracion_segundos * $INTERVALO_MONITOREO / 60" | bc)
    
    log "✅ PROCESAMIENTO COMPLETADO"
    log "   Hora fin: $tiempo_fin"
    log "   Duración: ${duracion_minutos} minutos"
    log "   Muestras capturadas: $duracion_segundos"
    
    echo "fin_procesamiento,$tiempo_fin,Procesamiento completado - Duración: ${duracion_minutos} min" >> "$LOG_DIR/eventos_detallados.csv"
    
    # Análisis automático de los datos
    analizar_procesamiento
    
    echo ""
    echo "✅✅✅ PROCESAMIENTO COMPLETADO ✅✅✅"
    echo "Duración: ${duracion_minutos} minutos"
    echo "Ver análisis en: $LOG_DIR/"
    echo "======================================"
}

# Función para análisis automático
analizar_procesamiento() {
    log "📊 Iniciando análisis automático..."
    
    if [ ! -f "$LOG_METRICAS" ]; then
        log "❌ No hay datos de métricas para analizar"
        return 1
    fi
    
    # Análisis con awk
    awk -F',' 'NR>1 {
        if (NF >= 8) {
            cpu_sys[NR] = $2; 
            mem_total[NR] = $3;
            django_cpu[NR] = $5;
            celery_cpu[NR] = $7;
            count++
        }
    } 
    END {
        if (count > 0) {
            # CPU del sistema
            cpu_sum = 0; cpu_max = 0; cpu_min = 999;
            for(i=2; i<=count+1; i++) {
                if (cpu_sys[i] != "") {
                    cpu_sum += cpu_sys[i];
                    if(cpu_sys[i] > cpu_max) cpu_max = cpu_sys[i];
                    if(cpu_sys[i] < cpu_min) cpu_min = cpu_sys[i];
                }
            }
            cpu_avg = cpu_sum / count;
            
            # Memoria total
            mem_sum = 0; mem_max = 0; mem_min = 99999;
            for(i=2; i<=count+1; i++) {
                if (mem_total[i] != "") {
                    mem_sum += mem_total[i];
                    if(mem_total[i] > mem_max) mem_max = mem_total[i];
                    if(mem_total[i] < mem_min) mem_min = mem_total[i];
                }
            }
            mem_avg = mem_sum / count;
            
            # CPU Celery
            celery_cpu_sum = 0; celery_cpu_max = 0;
            for(i=2; i<=count+1; i++) {
                if (celery_cpu[i] != "") {
                    celery_cpu_sum += celery_cpu[i];
                    if(celery_cpu[i] > celery_cpu_max) celery_cpu_max = celery_cpu[i];
                }
            }
            celery_cpu_avg = celery_cpu_sum / count;
            
            print "📊 ANÁLISIS DEL PROCESAMIENTO:";
            print "==============================";
            print "";
            print "🖥️  CPU Sistema:";
            printf "   Promedio: %.1f%%\n", cpu_avg;
            printf "   Máximo:   %.1f%%\n", cpu_max;
            printf "   Mínimo:   %.1f%%\n", cpu_min;
            print "";
            print "💾 Memoria Total:";
            printf "   Promedio: %.0f MB\n", mem_avg;
            printf "   Máximo:   %.0f MB\n", mem_max;
            printf "   Mínimo:   %.0f MB\n", mem_min;
            print "";
            print "🌿 CPU Celery Worker:";
            printf "   Promedio: %.1f%%\n", celery_cpu_avg;
            printf "   Máximo:   %.1f%%\n", celery_cpu_max;
            print "";
            print "🎯 PROYECCIÓN PARA 3 USUARIOS:";
            printf "   CPU estimado: %.0f%%\n", celery_cpu_max * 3;
            printf "   RAM estimada: %.1f GB\n", mem_max * 3 / 1024;
        }
    }' "$LOG_METRICAS" | tee -a "$LOG_GENERAL"
}

# Función principal de monitoreo
monitor_principal() {
    log "🤖 Monitor inteligente iniciado"
    log "Umbrales: Celery CPU: ${UMBRAL_CPU_CELERY}% | Sistema CPU: ${UMBRAL_CPU_SISTEMA}% | Intervalo: ${INTERVALO_MONITOREO}s"
    
    # Header CSV
    echo "timestamp,cpu_sistema,memoria_total_mb,memoria_percent,django_cpu,django_mem_mb,celery_cpu,celery_mem_mb" > "$LOG_METRICAS"
    
    # Capturar métricas base
    local metricas_iniciales=$(capturar_metricas_sistema)
    METRICAS_BASE_CPU=$(echo "$metricas_iniciales" | cut -d',' -f1)
    METRICAS_BASE_MEM=$(echo "$metricas_iniciales" | cut -d',' -f2)
    
    log "📊 Métricas base - CPU: ${METRICAS_BASE_CPU}% | MEM: ${METRICAS_BASE_MEM}MB"
    
    echo ""
    echo "🔍 ESPERANDO PROCESAMIENTO DE EXCEL..."
    echo "Sube un archivo en: http://localhost:5174"
    echo "El monitor detectará automáticamente cuando inicie el procesamiento"
    echo ""
    
    while true; do
        # Capturar métricas actuales
        local metricas_actuales=$(capturar_metricas_sistema)
        
        # Detectar estado actual
        local estado_actual=$(detectar_procesamiento_excel "$metricas_actuales")
        
        # Mostrar estado en tiempo real (modo silencioso hasta detectar)
        if [ "$estado_actual" = "idle" ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
            # Modo silencioso - solo mostrar punto cada 30 segundos
            if (( $CONTADOR_PROCESAMIENTO % 15 == 0 )); then
                printf "."
            fi
        else
            # Mostrar métricas detalladas durante procesamiento
            local timestamp=$(date '+%H:%M:%S')
            local cpu_total=$(echo "$metricas_actuales" | cut -d',' -f1)
            local mem_total=$(echo "$metricas_actuales" | cut -d',' -f2)
            local celery_cpu=$(echo "$metricas_actuales" | cut -d',' -f4)
            
            printf "\r%s - CPU: %s%% | MEM: %sMB | Celery: %s%% | Estado: %s" \
                "$timestamp" "$cpu_total" "$mem_total" "$celery_cpu" "$estado_actual"
        fi
        
        # Manejar transiciones de estado
        if [ "$estado_actual" = "procesando" ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
            iniciar_deteccion_procesamiento
        elif [ "$estado_actual" = "idle" ] && [ "$ESTADO_ANTERIOR" = "procesando" ]; then
            finalizar_deteccion_procesamiento
        fi
        
        # Actualizar estado
        ESTADO_ANTERIOR="$estado_actual"
        
        # Incrementar contador durante procesamiento
        if [ "$estado_actual" = "procesando" ]; then
            CONTADOR_PROCESAMIENTO=$((CONTADOR_PROCESAMIENTO + 1))
            
            # Timeout de seguridad
            if [ $CONTADOR_PROCESAMIENTO -gt $((TIEMPO_MAX_PROCESAMIENTO / INTERVALO_MONITOREO)) ]; then
                log "⚠️ TIMEOUT: Procesamiento demasiado largo, finalizando detección"
                finalizar_deteccion_procesamiento
            fi
        fi
        
        sleep $INTERVALO_MONITOREO
    done
}

# Función de limpieza al salir
cleanup() {
    echo ""
    log "🛑 Monitor detenido por usuario"
    
    if [ "$ESTADO_ANTERIOR" = "procesando" ]; then
        log "⚠️ Procesamiento interrumpido"
        finalizar_deteccion_procesamiento
    fi
    
    echo ""
    echo "📁 Resultados guardados en: $LOG_DIR/"
    echo "   - monitor_general.log (log principal)"
    echo "   - metricas_detalladas.csv (datos para análisis)"
    echo "   - eventos_procesamiento.log (detección de eventos)"
    
    if [ -f "$LOG_METRICAS" ]; then
        local total_muestras=$(wc -l < "$LOG_METRICAS")
        echo "   - Total muestras capturadas: $((total_muestras - 1))"
    fi
    
    exit 0
}

# Configurar trap para limpieza
trap cleanup SIGINT SIGTERM

# Verificar dependencias
if ! command -v bc &> /dev/null; then
    echo "❌ Error: 'bc' no está instalado. Instala con: apt-get install bc"
    exit 1
fi

if ! docker ps | grep -q sgm; then
    echo "❌ Error: Contenedores SGM no están corriendo"
    echo "Inicia con: docker-compose up -d"
    exit 1
fi

# Ejecutar monitor principal
monitor_principal