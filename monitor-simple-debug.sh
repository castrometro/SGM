#!/bin/bash

echo "🔍 MONITOR DEBUG - DETECCIÓN DIRECTA"
echo "==================================="

# Función simple para debug
debug_celery() {
    echo -n "Celery CPU: "
    local celery_cpu=$(docker stats --no-stream sgm-celery_worker-1 --format "{{.CPUPerc}}" | sed 's/%//' | tr -d '\n\r' | head -c 10)
    echo "$celery_cpu"
    
    echo -n "Tareas activas: "
    local celery_output=$(docker exec sgm-celery_worker-1 celery -A sgm_backend inspect active 2>/dev/null)
    local tareas=$(echo "$celery_output" | grep -c "rg_procesar_step1_task" 2>/dev/null || echo "0")
    echo "$tareas"
    
    echo -n "Logs Django (últimos 10s): "
    local logs_django=$(docker logs sgm-django-1 --since="10s" 2>/dev/null | grep -i -E "(rindegastos|step1|excel|upload.*xlsx)" | wc -l)
    echo "$logs_django"
    
    echo -n "Logs Celery (últimos 10s): "
    local logs_celery=$(docker logs sgm-celery_worker-1 --since="10s" 2>/dev/null | grep -i -E "(rg_procesar|step1|task.*received|task.*started)" | wc -l)
    echo "$logs_celery"
    
    echo "---"
}

echo "Monitoreando cada 5 segundos. Presiona Ctrl+C para detener"
echo ""

while true; do
    echo "[$(date '+%H:%M:%S')]"
    debug_celery
    sleep 5
done