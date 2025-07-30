#!/bin/bash

echo "🚀 Iniciando sistema multi-worker de Celery..."
echo "📊 Configuración:"
echo "   - Worker Nómina: concurrencia 3 (nomina_queue)"
echo "   - Worker Contabilidad: concurrencia 2 (contabilidad_queue)" 
echo "   - Worker General: concurrencia 1 (default)"
echo ""

sleep 3

# Función para manejar la terminación limpia
cleanup() {
    echo "🛑 Deteniendo workers..."
    pkill -P $$
    exit 0
}

trap cleanup SIGTERM SIGINT

# Iniciar workers en background
echo "🔧 Iniciando Worker Nómina (concurrencia: 3)..."
celery -A sgm_backend worker -Q nomina_queue -c 3 --loglevel=info --hostname=nomina@%h &
NOMINA_PID=$!

echo "📊 Iniciando Worker Contabilidad (concurrencia: 2)..."
celery -A sgm_backend worker -Q contabilidad_queue -c 2 --loglevel=info --hostname=contabilidad@%h &
CONTABILIDAD_PID=$!

echo "⚙️ Iniciando Worker General (concurrencia: 1)..."
celery -A sgm_backend worker -Q default -c 1 --loglevel=info --hostname=general@%h &
GENERAL_PID=$!

echo ""
echo "✅ Todos los workers iniciados!"
echo "📈 PIDs: Nómina=$NOMINA_PID, Contabilidad=$CONTABILIDAD_PID, General=$GENERAL_PID"
echo "🔍 Monitoreando workers... (Ctrl+C para detener)"

# Esperar que todos los procesos terminen
wait