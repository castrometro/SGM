#!/bin/bash

# Monitor Redis Cache SGM - Versión Simplificada
# Inspecciona el cache especializado de nómina

echo "🔍 REDIS CACHE MONITOR SGM"
echo "=========================="
echo

# Función helper Redis (silencia warnings)
redis_cmd() {
    docker exec sgm-redis-1 redis-cli -n 2 --no-auth-warning -a Redis_Password_2025! "$@" 2>/dev/null
}

echo "📊 ESTADÍSTICAS DE CACHE"
echo "========================"
echo "Cache hits: $(redis_cmd get sgm:nomina:stats:cache_hits)"
echo "Cache misses: $(redis_cmd get sgm:nomina:stats:cache_misses)"
echo "Informes oficiales: $(redis_cmd get sgm:nomina:stats:informes_cached)"
echo

echo "🗂️ KEYS ACTUALES EN CACHE"
echo "========================="
redis_cmd keys "*" | sort
echo

echo "⏰ PREVIEW CACHE (TTL 15min)"
echo "============================"
preview_keys=$(redis_cmd keys "*_cache_*")
if [ -n "$preview_keys" ]; then
    echo "$preview_keys" | while IFS= read -r key; do
        ttl=$(redis_cmd ttl "$key")
        echo "$key: $ttl segundos"
    done
else
    echo "No hay cache preview activo"
fi
echo

echo "📈 INFORMES OFICIALES (permanente)"
echo "=================================="
oficial_keys=$(redis_cmd keys "*:informe")
if [ -n "$oficial_keys" ]; then
    echo "$oficial_keys" | while IFS= read -r key; do
        echo "✓ $key"
    done
else
    echo "No hay informes oficiales cacheados"
fi
echo

if [ "$1" = "--detail" ]; then
    echo "🔍 DETALLE DE UN INFORME"
    echo "======================="
    first_informe=$(redis_cmd keys "*:informe" | head -1)
    if [ -n "$first_informe" ]; then
        echo "Contenido de: $first_informe"
        redis_cmd get "$first_informe" | jq -r '.cliente_nombre, .periodo, .estado_cierre' 2>/dev/null || echo "JSON no válido"
    fi
fi

echo "💡 Uso: ./monitor-redis-simple.sh [--detail]"