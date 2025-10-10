#!/bin/bash

# Monitor de recursos en tiempo real para test de carga
echo "🔥 INICIANDO MONITOR DE RECURSOS - TEST DE CARGA"
echo "==============================================="
echo "Sistema: $(date)"
echo "Usuario: $(whoami)"
echo ""

# Crear archivo de log
LOGFILE="test_carga_$(date +%H%M%S).log"
echo "📊 Guardando datos en: $LOGFILE"

# Función para capturar métricas
capturar_metricas() {
    local timestamp=$(date '+%H:%M:%S')
    
    # CPU total
    local cpu_total=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | cut -d'%' -f1)
    
    # Memoria total
    local mem_info=$(free | awk 'NR==2{printf "%.2f,%.1f", $3/1024/1024, $3*100/$2}')
    
    # Docker stats
    local docker_stats=$(docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" | tr '\n' ';')
    
    echo "$timestamp,$cpu_total,$mem_info,$docker_stats" >> "$LOGFILE"
    
    # Mostrar en pantalla
    echo "$(date '+%H:%M:%S') - CPU: ${cpu_total}% | Memoria: ${mem_info%,*}GB | Docker: $(echo $docker_stats | wc -c) chars"
}

echo "🎯 INSTRUCCIONES PARA EL TEST:"
echo "=============================="
echo "1. Abre tu navegador en: http://localhost:5174"
echo "2. Ve a 'Captura Masiva de Gastos'"
echo "3. Cuando veas la pantalla de subida, presiona ENTER aquí"
echo "4. Sube el archivo: backend/movimientos_mes_prueba.xlsx (9KB)"
echo "5. Observa los recursos mientras se procesa"
echo "6. Presiona Ctrl+C cuando termine el procesamiento"
echo ""

read -p "Presiona ENTER cuando estés en la pantalla de subida de archivos..." -r

echo ""
echo "🚀 INICIANDO MONITOREO - ¡SUBE TU ARCHIVO AHORA!"
echo "Archivo recomendado: backend/movimientos_mes_prueba.xlsx"
echo "=============================================="

# Header del CSV
echo "timestamp,cpu_total,memory_gb,memory_percent,docker_stats" > "$LOGFILE"

# Capturar estado inicial
echo ""
echo "📊 ESTADO INICIAL:"
capturar_metricas

echo ""
echo "🔍 MONITOREANDO (Ctrl+C para parar)..."
echo "Timestamp    CPU%   RAM(GB)  Estado"
echo "=================================="

# Loop de monitoreo
while true; do
    capturar_metricas
    sleep 2
done