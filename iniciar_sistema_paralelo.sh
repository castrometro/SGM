#!/bin/bash

echo "🚀 INICIANDO SISTEMA PARALELO DE INCIDENCIAS SGM"
echo "================================================"
echo ""

# Función para mostrar el progreso
show_progress() {
    echo "⏳ $1..."
    sleep 2
}

# Función para verificar si un servicio está corriendo
check_service() {
    local service=$1
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service está corriendo"
        return 0
    else
        echo "❌ $service no está corriendo"
        return 1
    fi
}

# Verificar que Docker esté disponible
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

# Detener servicios existentes
show_progress "Deteniendo servicios existentes"
docker-compose down

# Construir imágenes
show_progress "Construyendo imágenes Docker"
docker-compose build

# Iniciar servicios base (BD y Redis)
show_progress "Iniciando servicios base (PostgreSQL y Redis)"
docker-compose up -d db redis

# Esperar a que los servicios base estén listos
echo "⏳ Esperando que PostgreSQL y Redis estén listos..."
sleep 10

# Verificar servicios base
echo "🔍 Verificando servicios base..."
if check_service "db" && check_service "redis"; then
    echo "✅ Servicios base iniciados correctamente"
else
    echo "❌ Error iniciando servicios base"
    exit 1
fi

# Iniciar Django
show_progress "Iniciando Django backend"
docker-compose up -d django

# Esperar a que Django esté listo
echo "⏳ Esperando que Django esté listo..."
sleep 15

# Iniciar workers de Celery con la nueva configuración
show_progress "Iniciando sistema multi-worker de Celery"
docker-compose up -d celery_worker

# Iniciar Flower para monitoreo
show_progress "Iniciando Flower (monitor de Celery)"
docker-compose up -d flower

# Iniciar servicios de análisis
show_progress "Iniciando servicios de análisis (Streamlit)"
docker-compose up -d streamlit_conta streamlit_nomina

# Iniciar RedisInsight para análisis de colas
show_progress "Iniciando RedisInsight"
docker-compose up -d redisinsight

# Verificación final
echo ""
echo "🔍 VERIFICACIÓN FINAL DE SERVICIOS"
echo "=================================="

services=("db" "redis" "django" "celery_worker" "flower")
all_services_ok=true

for service in "${services[@]}"; do
    if check_service "$service"; then
        continue
    else
        all_services_ok=false
    fi
done

echo ""
if [ "$all_services_ok" = true ]; then
    echo "🎉 ¡SISTEMA INICIADO EXITOSAMENTE!"
    echo ""
    echo "📋 SERVICIOS DISPONIBLES:"
    echo "=================================="
    echo "🌐 Django Backend:      http://localhost:8000"
    echo "🔍 Flower (Celery):     http://localhost:5555"
    echo "📊 Streamlit Conta:     http://localhost:8502"
    echo "📈 Streamlit Nómina:    http://localhost:8503"
    echo "🔧 RedisInsight:        http://localhost:8001"
    echo ""
    echo "🚀 NUEVA FUNCIONALIDAD:"
    echo "=================================="
    echo "✅ Sistema dual de procesamiento paralelo"
    echo "✅ Workers configurados: Nómina(3), Contabilidad(2), General(1)"
    echo "✅ Endpoint modificado para recibir clasificaciones_seleccionadas"
    echo "✅ Procesamiento con Celery Chord para paralelización"
    echo ""
    echo "📝 ENDPOINT DE PRUEBA:"
    echo "POST http://localhost:8000/api/nomina/incidencia-cierre/generar/{cierre_id}/"
    echo "Body: {"
    echo '  "clasificaciones_seleccionadas": [1, 3, 5, 7, 9]'
    echo "}"
    echo ""
    echo "📊 MONITOREO:"
    echo "- Flower: Ver tareas en tiempo real"
    echo "- RedisInsight: Analizar colas y rendimiento"
    echo "- Docker logs: docker-compose logs -f celery_worker"
    
else
    echo "❌ ALGUNOS SERVICIOS NO INICIARON CORRECTAMENTE"
    echo "🔧 Para debugging:"
    echo "   docker-compose logs [service_name]"
    echo "   docker-compose ps"
fi

echo ""
echo "🛑 Para detener todos los servicios:"
echo "   docker-compose down"
echo ""
