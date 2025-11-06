#!/bin/bash

# Script de monitoreo Redis Cache - Sistema Cache Especializado SGM
# Inspecciona BD 2 (cache nómina especializado) con comandos estructurados

echo "🔍 MONITOR REDIS CACHE ESPECIALIZADO SGM"
echo "========================================"
echo

# Función para ejecutar comandos Redis con formato limpio
redis_exec() {
    REDISCLI_AUTH=Redis_Password_2025! docker exec -i sgm-redis-1 redis-cli -n 2 "$@" 2>/dev/null
}

echo "📊 ESTADÍSTICAS GENERALES"
echo "========================"
echo "Cache hits: $(redis_exec get sgm:nomina:stats:cache_hits)"
echo "Cache misses: $(redis_exec get sgm:nomina:stats:cache_misses)"
echo "Cache writes: $(redis_exec get sgm:nomina:stats:cache_writes)"
echo "Cache clears: $(redis_exec get sgm:nomina:stats:cache_clears)"
echo "Informes cached: $(redis_exec get sgm:nomina:stats:informes_cached)"
echo "Consolidados cached: $(redis_exec get sgm:nomina:stats:consolidados_cached)"
echo

echo "🗂️ KEYS CACHE PREVIEW (situación 1 - TTL 15min)"
echo "==============================================="
preview_libro=$(redis_exec keys "*_cache_libro")
preview_mov=$(redis_exec keys "*_cache_mov")

if [ -n "$preview_libro" ] || [ -n "$preview_mov" ]; then
    echo "Keys de preview encontradas:"
    [ -n "$preview_libro" ] && echo "$preview_libro" | sed 's/^/  /'
    [ -n "$preview_mov" ] && echo "$preview_mov" | sed 's/^/  /'
    echo
    echo "TTL de keys preview:"
    for key in $preview_libro $preview_mov; do
        if [ -n "$key" ]; then
            ttl=$(redis_exec ttl "$key")
            echo "  $key: $ttl segundos"
        fi
    done
else
    echo "No hay keys de preview actualmente"
fi
echo

echo "📈 CACHE OFICIAL (situación 2-3 - permanente)"
echo "============================================="
oficial_keys=$(redis_exec keys "*:informe")
if [ -n "$oficial_keys" ]; then
    echo "Informes oficiales cacheados:"
    echo "$oficial_keys" | while read -r key; do
        if [ -n "$key" ]; then
            size=$(redis_exec memory usage "$key" 2>/dev/null || echo "N/A")
            echo "  $key (tamaño: $size bytes)"
        fi
    done
else
    echo "No hay informes oficiales cacheados"
fi
echo

echo "🔄 INVALIDACIÓN AUTOMÁTICA"
echo "=========================="
echo "Las siguientes operaciones invalidan cache preview automáticamente:"
echo "- Reclasificación de conceptos (views_reclasificacion.py)"
echo "- Corrección de libro (views_correcciones.py)"
echo "- Finalización de cierre (tasks_refactored/informes.py)"
echo

# Monitoreo en tiempo real opcional
if [ "$1" = "--watch" ]; then
    echo "🔄 MODO WATCH - Actualizando cada 5 segundos..."
    echo "Presiona Ctrl+C para salir"
    echo
    while true; do
        clear
        bash monitor-redis-cache.sh
        sleep 5
    done
fi

echo "💡 USO:"
echo "  ./monitor-redis-cache.sh           # Vista estática"
echo "  ./monitor-redis-cache.sh --watch   # Monitoreo continuo"
echo