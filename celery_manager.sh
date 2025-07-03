#!/bin/bash

# Script para gestionar Celery de manera fácil
# Este script incluye varias opciones para trabajar con Celery

PROJECT_DIR="/root/SGM/backend"

case "$1" in
    "start")
        echo "🚀 Iniciando Celery Worker..."
        cd $PROJECT_DIR
        celery -A sgm_backend worker --loglevel=info --concurrency=2
        ;;
    
    "stop")
        echo "🛑 Deteniendo Celery Worker..."
        pkill -f "celery.*worker"
        ;;
    
    "restart")
        echo "🔄 Reiniciando Celery Worker..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    "status")
        echo "📊 Estado de Celery:"
        cd $PROJECT_DIR
        celery -A sgm_backend inspect active
        ;;
    
    "monitor")
        echo "👁️  Monitoreando Celery (presiona Ctrl+C para salir)..."
        cd $PROJECT_DIR
        celery -A sgm_backend events
        ;;
    
    "test")
        echo "🧪 Ejecutando test de finalización..."
        if [ -z "$2" ]; then
            echo "❌ Error: Debes especificar un cierre_id"
            echo "   Uso: $0 test <cierre_id>"
            exit 1
        fi
        cd $PROJECT_DIR
        python manage.py test_finalizacion --cierre_id=$2
        ;;
    
    "test-sync")
        echo "🧪 Ejecutando test de finalización (sincrónicamente)..."
        if [ -z "$2" ]; then
            echo "❌ Error: Debes especificar un cierre_id"
            echo "   Uso: $0 test-sync <cierre_id>"
            exit 1
        fi
        cd $PROJECT_DIR
        python manage.py test_finalizacion --cierre_id=$2 --sync
        ;;
    
    "purge")
        echo "🗑️  Limpiando cola de tareas..."
        cd $PROJECT_DIR
        celery -A sgm_backend purge
        ;;
    
    *)
        echo "🔧 Gestor de Celery para SGM"
        echo ""
        echo "Uso: $0 {start|stop|restart|status|monitor|test|test-sync|purge}"
        echo ""
        echo "Comandos disponibles:"
        echo "  start      - Inicia el worker de Celery"
        echo "  stop       - Detiene el worker de Celery"
        echo "  restart    - Reinicia el worker de Celery"
        echo "  status     - Muestra el estado de las tareas activas"
        echo "  monitor    - Monitorea las tareas en tiempo real"
        echo "  test       - Prueba la finalización de un cierre (con Celery)"
        echo "  test-sync  - Prueba la finalización de un cierre (sin Celery)"
        echo "  purge      - Limpia la cola de tareas pendientes"
        echo ""
        echo "Ejemplos:"
        echo "  $0 start"
        echo "  $0 test 123"
        echo "  $0 test-sync 123"
        exit 1
        ;;
esac
