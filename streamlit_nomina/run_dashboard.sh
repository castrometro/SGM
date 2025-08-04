#!/bin/bash

# Script para ejecutar el Dashboard de Nómina SGM
# Funcionamiento igual al de contabilidad, pero conectado a Redis DB2

echo "🚀 Iniciando Dashboard de Nómina SGM"
echo "=================================="

# Configurar variables de entorno para Redis
export REDIS_HOST=${REDIS_HOST:-redis}
export REDIS_PORT=${REDIS_PORT:-6379} 
export REDIS_PASSWORD=${REDIS_PASSWORD:-Redis_Password_2025!}
export REDIS_DB_NOMINA=${REDIS_DB_NOMINA:-2}

echo "📡 Configuración Redis:"
echo "  Host: $REDIS_HOST"
echo "  Puerto: $REDIS_PORT"
echo "  BD Nómina: $REDIS_DB_NOMINA"

# Cambiar al directorio del proyecto
cd /root/SGM/streamlit_nomina

# Ejecutar Streamlit
echo ""
echo "📊 Iniciando dashboard..."
echo "🌐 URL: http://localhost:8503"
echo "📝 Para un cliente específico: http://localhost:8503/?cliente_id=6"
echo ""
echo "Presiona Ctrl+C para detener"

streamlit run app.py --server.port=8503 --server.address=0.0.0.0
