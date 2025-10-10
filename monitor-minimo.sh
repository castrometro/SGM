#!/bin/bash

echo "🔥 MONITOR SUPER SIMPLE - SOLO LOGS"
echo "=================================="
echo ""

CONTADOR=0

while true; do
    CONTADOR=$((CONTADOR + 1))
    TIMESTAMP=$(date '+%H:%M:%S.%3N')
    
    # Buscar actividad en logs recientes
    DJANGO_ACTIVITY=$(docker logs sgm-django-1 --since="1s" 2>/dev/null | grep -i "rindegastos\|excel\|upload" | head -1)
    CELERY_ACTIVITY=$(docker logs sgm-celery_worker-1 --since="1s" 2>/dev/null | grep -i "rg_procesar\|step1\|received\|started" | head -1)
    
    # Si encontramos algo, mostrarlo
    if [ ! -z "$DJANGO_ACTIVITY" ]; then
        echo "🚀 [$TIMESTAMP] DJANGO: $DJANGO_ACTIVITY"
    fi
    
    if [ ! -z "$CELERY_ACTIVITY" ]; then
        echo "⚙️  [$TIMESTAMP] CELERY: $CELERY_ACTIVITY"
    fi
    
    # Status cada 100 iteraciones (10 segundos)
    if [ $((CONTADOR % 100)) -eq 0 ]; then
        printf "\r🔍 [$TIMESTAMP] Monitoreando... muestras: $CONTADOR"
    fi
    
    sleep 0.1
done