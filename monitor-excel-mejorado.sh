#!/bin/bash

# Monitor Inteligente SGM - Versión Mejorada
# Detecta automáticamente inicio Y fin de procesamiento Excel
# Basado en el monitor original que funcionaba bien

echo "🤖 MONITOR INTELIGENTE SGM - DETECCIÓN AUTOMÁTICA"
echo "================================================"

# Configuración
INTERVALO_MONITOREO=3  # segundos
UMBRAL_CPU_CELERY=3  # % CPU en Celery para detectar procesamiento
TIEMPO_MAX_PROCESAMIENTO=600  # 10 minutos máximo
LOG_DIR="monitor_excel_$(date +%Y%m%d_%H%M%S)"

# Crear directorio de logs
mkdir -p "$LOG_DIR"
echo "📁 Logs guardados en: $LOG_DIR/"

# Archivos de log
LOG_GENERAL="$LOG_DIR/monitor_general.log"
LOG_METRICAS="$LOG_DIR/metricas_detalladas.csv"
LOG_EVENTOS="$LOG_DIR/eventos_procesamiento.log"

# Estado del monitor
ESTADO_ANTERIOR="idle"
PROCESAMIENTO_INICIADO=""
CONTADOR_PROCESAMIENTO=0
CONTADOR_IDLE=0  # Nuevo: contador para detectar fin

# Función para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_GENERAL"
}

# Función para capturar métricas del sistema
capturar_metricas_sistema() {
    local timestamp=$(date '+%H:%M:%S')
    
    # CPU total del sistema
    local cpu_total=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | sed 's/%us,//' | sed 's/%sy,//' | awk '{print $1}')
    cpu_total=${cpu_total:-0}
    
    # Memoria total
    local mem_total_mb=$(free -m | awk 'NR==2{print $3}')
    mem_total_mb=${mem_total_mb:-0}
    local mem_percent=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    mem_percent=${mem_percent:-0}
    
    # Docker stats específicos con manejo de errores y limpieza
    local django_cpu=$(docker stats --no-stream sgm-django-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | tr -d '\n\r' | head -c 10 || echo "0")
    django_cpu=${django_cpu:-0}
    local django_mem=$(docker stats --no-stream sgm-django-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | tr -d '\n\r' | head -c 10 || echo "0")
    django_mem=${django_mem:-0}
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" 2>/dev/null | sed 's/%//' | tr -d '\n\r' | head -c 10 || echo "0")
    celery_cpu=${celery_cpu:-0}
    local celery_mem=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.MemUsage}}" 2>/dev/null | awk '{print $1}' | sed 's/MiB//' | tr -d '\n\r' | head -c 10 || echo "0")
    celery_mem=${celery_mem:-0}
    
    # Validar que los valores son números válidos
    if ! [[ "$django_cpu" =~ ^[0-9]*\.?[0-9]+$ ]]; then django_cpu="0"; fi
    if ! [[ "$celery_cpu" =~ ^[0-9]*\.?[0-9]+$ ]]; then celery_cpu="0"; fi
    
    # Guardar en CSV
    echo "$timestamp,$cpu_total,$mem_total_mb,$mem_percent,$django_cpu,$django_mem,$celery_cpu,$celery_mem" >> "$LOG_METRICAS"
    
    # Retornar valores para detección
    echo "$cpu_total,$mem_total_mb,$django_cpu,$celery_cpu"
}

# Función mejorada para detectar tareas de Celery activas
detectar_celery_activo() {
    # Buscar específicamente el task de rinde gastos
    local celery_inspect=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null || echo "{}")
    
    # Buscar el task específico de rinde gastos
    local tareas_rindegastos=$(echo "$celery_inspect" | grep -c "rg_procesar_step1_task" || echo "0")
    
    # También buscar cualquier task de contabilidad como backup
    local tareas_contabilidad=$(echo "$celery_inspect" | grep -c "contabilidad\." || echo "0")
    
    # Contar total de tareas activas
    local tareas_totales=$(echo "$celery_inspect" | grep -o '"uuid"' | wc -l)
    
    if [ "$tareas_rindegastos" -gt 0 ]; then
        echo "$tareas_rindegastos"
        echo "[$(date '+%H:%M:%S')] ✅ DETECTADO: $tareas_rindegastos tareas rg_procesar_step1_task activas" >> "$LOG_GENERAL"
        return 0
    elif [ "$tareas_contabilidad" -gt 0 ]; then
        echo "$tareas_contabilidad"
        echo "[$(date '+%H:%M:%S')] 📊 DETECTADO: $tareas_contabilidad tareas contabilidad activas" >> "$LOG_GENERAL"
        return 0
    elif [ "$tareas_totales" -gt 0 ]; then
        echo "$tareas_totales"
        echo "[$(date '+%H:%M:%S')] 🔍 DETECTADO: $tareas_totales tareas Celery activas (genéricas)" >> "$LOG_GENERAL"
        return 0
    else
        return 1
    fi
}

# Función mejorada para detectar procesamiento de Excel
detectar_procesamiento_excel() {
    local metricas="$1"
    local cpu_total=$(echo "$metricas" | cut -d',' -f1)
    local mem_total=$(echo "$metricas" | cut -d',' -f2)
    local django_cpu=$(echo "$metricas" | cut -d',' -f3)
    local celery_cpu=$(echo "$metricas" | cut -d',' -f4)
    
    # Convertir a números enteros para comparación - limpiar caracteres extra
    local cpu_total_int=$(echo "$cpu_total" | tr -d '\n\r' | cut -d'.' -f1)
    cpu_total_int=${cpu_total_int:-0}
    local celery_cpu_int=$(echo "$celery_cpu" | tr -d '\n\r' | cut -d'.' -f1)
    celery_cpu_int=${celery_cpu_int:-0}
    
    # Validar que son números
    if ! [[ "$cpu_total_int" =~ ^[0-9]+$ ]]; then
        cpu_total_int=0
    fi
    if ! [[ "$celery_cpu_int" =~ ^[0-9]+$ ]]; then
        celery_cpu_int=0
    fi
    
    # Detectar tareas Celery específicas
    local celery_activo=false
    local num_tareas=0
    if num_tareas=$(detectar_celery_activo); then
        celery_activo=true
    fi
    
    # Detectar actividad en logs de Django (últimos 15 segundos)
    local logs_rindegastos=$(docker logs sgm-django-1 --since="15s" 2>/dev/null | grep -i -E "(rindegastos|step1|excel|upload.*xlsx)" | wc -l)
    
    # Detectar actividad en logs de Celery (últimos 15 segundos)
    local logs_celery=$(docker logs sgm-celery_worker-1 --since="15s" 2>/dev/null | grep -i -E "(rg_procesar|step1|task.*received|task.*started)" | wc -l)
    
    # Condiciones para detectar procesamiento
    local procesando=false
    local razon=""
    
    # Condición 1: Tareas Celery activas (MÁS CONFIABLE)
    if [ "$celery_activo" = true ]; then
        procesando=true
        razon="Tareas Celery activas ($num_tareas)"
    fi
    
    # Condición 2: CPU alto en Celery
    if [ "$celery_cpu_int" -gt "$UMBRAL_CPU_CELERY" ]; then
        procesando=true
        razon="${razon} + CPU alto en Celery (${celery_cpu}%)"
    fi
    
    # Condición 3: Actividad reciente en logs
    if [ "$logs_rindegastos" -gt 0 ] || [ "$logs_celery" -gt 0 ]; then
        procesando=true
        razon="${razon} + Actividad en logs (Django:$logs_rindegastos, Celery:$logs_celery)"
    fi
    
    # Solo loggear cuando hay cambio de estado significativo
    if [ "$procesando" = true ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
        log "🔍 DETECCIÓN: $razon"
    fi
    
    if [ "$procesando" = true ]; then
        echo "procesando"
        return 0
    else
        echo "idle"
        return 1
    fi
}

# Función para manejar inicio de procesamiento
iniciar_deteccion_procesamiento() {
    PROCESAMIENTO_INICIADO=$(date '+%H:%M:%S')
    CONTADOR_PROCESAMIENTO=0
    CONTADOR_IDLE=0  # Resetear contador idle
    
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
    local duracion_segundos=$(echo "$CONTADOR_PROCESAMIENTO * $INTERVALO_MONITOREO" | bc)
    local duracion_minutos=$(echo "scale=1; $duracion_segundos / 60" | bc)
    
    log "✅ PROCESAMIENTO COMPLETADO"
    log "   Hora fin: $tiempo_fin"
    log "   Duración: ${duracion_minutos} minutos"
    log "   Muestras capturadas: $CONTADOR_PROCESAMIENTO"
    
    echo "fin_procesamiento,$tiempo_fin,Procesamiento completado - Duración: ${duracion_minutos} min" >> "$LOG_DIR/eventos_detallados.csv"
    
    # Análisis automático de los datos
    analizar_procesamiento
    
    echo ""
    echo "✅✅✅ PROCESAMIENTO COMPLETADO ✅✅✅"
    echo "Duración: ${duracion_minutos} minutos"
    echo "Ver análisis en: $LOG_DIR/"
    echo "======================================"
    echo ""
    echo "🔍 ESPERANDO NUEVO PROCESAMIENTO..."
}

# Función para análisis automático
analizar_procesamiento() {
    log "📊 Iniciando análisis automático..."
    
    if [ ! -f "$LOG_METRICAS" ]; then
        log "❌ No hay datos de métricas para analizar"
        return 1
    fi
    
    # Análisis con awk de las últimas N líneas (durante procesamiento)
    local lineas_analizar=$CONTADOR_PROCESAMIENTO
    if [ "$lineas_analizar" -lt 1 ]; then
        lineas_analizar=10
    fi
    
    tail -n "$lineas_analizar" "$LOG_METRICAS" | awk -F',' 'NR>0 {
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
            for(i=1; i<=count; i++) {
                if (cpu_sys[i] != "") {
                    cpu_sum += cpu_sys[i];
                    if(cpu_sys[i] > cpu_max) cpu_max = cpu_sys[i];
                    if(cpu_sys[i] < cpu_min) cpu_min = cpu_sys[i];
                }
            }
            cpu_avg = cpu_sum / count;
            
            # Memoria total
            mem_sum = 0; mem_max = 0; mem_min = 99999;
            for(i=1; i<=count; i++) {
                if (mem_total[i] != "") {
                    mem_sum += mem_total[i];
                    if(mem_total[i] > mem_max) mem_max = mem_total[i];
                    if(mem_total[i] < mem_min) mem_min = mem_total[i];
                }
            }
            mem_avg = mem_sum / count;
            
            # CPU Celery
            celery_cpu_sum = 0; celery_cpu_max = 0;
            for(i=1; i<=count; i++) {
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
    }' | tee -a "$LOG_GENERAL"
}

# Función principal de monitoreo
monitor_principal() {
    log "🤖 Monitor inteligente iniciado"
    log "Umbrales: Celery CPU: ${UMBRAL_CPU_CELERY}% | Intervalo: ${INTERVALO_MONITOREO}s"
    
    # Header CSV
    echo "timestamp,cpu_sistema,memoria_total_mb,memoria_percent,django_cpu,django_mem_mb,celery_cpu,celery_mem_mb" > "$LOG_METRICAS"
    
    # Capturar métricas base
    local metricas_iniciales=$(capturar_metricas_sistema)
    
    log "📊 Sistema listo para monitoreo"
    
    echo ""
    echo "🔍 ESPERANDO PROCESAMIENTO DE EXCEL..."
    echo "Sube un archivo en: http://172.17.11.18:5174/"
    echo "El monitor detectará automáticamente cuando inicie y termine"
    echo ""
    
    while true; do
        # Capturar métricas actuales
        local metricas_actuales=$(capturar_metricas_sistema)
        
        # Detectar estado actual
        local estado_actual=$(detectar_procesamiento_excel "$metricas_actuales")
        
        # Mostrar estado en tiempo real
        if [ "$estado_actual" = "idle" ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
            # Modo silencioso - solo mostrar punto cada 10 segundos
            local segundos_actuales=$(date +%S | sed 's/^0//')
            segundos_actuales=${segundos_actuales:-0}
            if (( segundos_actuales % 10 == 0 )); then
                local timestamp=$(date '+%H:%M:%S')
                local cpu_total=$(echo "$metricas_actuales" | cut -d',' -f1)
                local mem_total=$(echo "$metricas_actuales" | cut -d',' -f2)
                printf "\r🔍 Esperando... %s - CPU: %s%% | RAM: %sMB    " \
                    "$timestamp" "$cpu_total" "$mem_total"
            fi
        else
            # Mostrar métricas detalladas durante procesamiento
            local timestamp=$(date '+%H:%M:%S')
            local cpu_total=$(echo "$metricas_actuales" | cut -d',' -f1)
            local mem_total=$(echo "$metricas_actuales" | cut -d',' -f2)
            local celery_cpu=$(echo "$metricas_actuales" | cut -d',' -f4)
            
            if [ "$estado_actual" = "procesando" ]; then
                local duracion_min=$(echo "scale=1; $CONTADOR_PROCESAMIENTO * $INTERVALO_MONITOREO / 60" | bc)
                printf "\r%s - 🔥 PROCESANDO | CPU: %s%% | RAM: %sMB | Celery: %s%% | Tiempo: %s min" \
                    "$timestamp" "$cpu_total" "$mem_total" "$celery_cpu" "$duracion_min"
            fi
        fi
        
        # Manejar transiciones de estado
        if [ "$estado_actual" = "procesando" ] && [ "$ESTADO_ANTERIOR" = "idle" ]; then
            iniciar_deteccion_procesamiento
            CONTADOR_IDLE=0
        elif [ "$estado_actual" = "idle" ] && [ "$ESTADO_ANTERIOR" = "procesando" ]; then
            # Incrementar contador idle para confirmar fin
            CONTADOR_IDLE=$((CONTADOR_IDLE + 1))
            
            # Confirmar fin solo después de 3 ciclos idle consecutivos (evita falsos positivos)
            if [ "$CONTADOR_IDLE" -ge 3 ]; then
                finalizar_deteccion_procesamiento
                CONTADOR_IDLE=0
            fi
        elif [ "$estado_actual" = "procesando" ]; then
            # Reset contador idle si vuelve a procesar
            CONTADOR_IDLE=0
        fi
        
        # Actualizar estado y contadores
        ESTADO_ANTERIOR="$estado_actual"
        
        # Incrementar contador durante procesamiento
        if [ "$estado_actual" = "procesando" ]; then
            CONTADOR_PROCESAMIENTO=$((CONTADOR_PROCESAMIENTO + 1))
            
            # Timeout de seguridad
            if [ $CONTADOR_PROCESAMIENTO -gt $((TIEMPO_MAX_PROCESAMIENTO / INTERVALO_MONITOREO)) ]; then
                log "⚠️ TIMEOUT: Procesamiento demasiado largo, finalizando detección"
                finalizar_deteccion_procesamiento
                CONTADOR_IDLE=0
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