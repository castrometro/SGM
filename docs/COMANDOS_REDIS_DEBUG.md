# 🔐 Comandos Redis para Debugging - SGM

## ⚠️ Autenticación Requerida

Redis está protegido con password:
```bash
Password: Redis_Password_2025!
```

## 📋 Bases de Datos Redis

- **DB 0**: Sesiones Django
- **DB 1**: Logs del sistema
- **DB 2**: Cache de nómina (el más importante para debugging)

## 🚀 Script de Inspección Rápida

```bash
# Ejecutar inspector completo
/tmp/redis_inspector_auth.sh
```

Este script muestra:
- Estado de todas las bases de datos
- Claves en cache de nómina (DB 2)
- TTL y tamaño de cada clave
- Uso de memoria

## 🔍 Comandos Individuales

### 1. Conexión Básica

```bash
# Método 1: Conectar interactivamente
docker exec -it sgm-redis-1 redis-cli
> AUTH Redis_Password_2025!
> SELECT 2

# Método 2: Conectar directamente a DB 2
docker exec -it sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2

# Método 3: Usar variable de entorno (para múltiples comandos)
export REDISCLI_AUTH="Redis_Password_2025!"
docker exec -it sgm-redis-1 redis-cli -n 2
```

### 2. Explorar Cache de Nómina

```bash
# Ver TODAS las claves de cache nómina
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:*"

# Ver claves de un cliente específico (ej: cliente 20)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:20:*"

# Ver claves de un período (ej: 2025-10)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:*:2025-10*"

# Contar claves en cache
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 DBSIZE
```

### 3. Inspeccionar Cache Específico

```bash
# Ver contenido del cache (cliente 20, período 2025-10)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 GET "sgm:nomina:20:2025-10"

# Ver TTL (tiempo de vida restante en segundos)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 TTL "sgm:nomina:20:2025-10"
# Resultado: -2 = no existe, -1 = sin expiración, >0 = segundos restantes

# Ver tamaño en memoria
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 MEMORY USAGE "sgm:nomina:20:2025-10"

# Ver tipo de dato
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 TYPE "sgm:nomina:20:2025-10"
```

### 4. Estadísticas del Cache

```bash
# Ver estadísticas de uso
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 GET "sgm:nomina:stats:cache_hits"
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 GET "sgm:nomina:stats:cache_misses"
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 GET "sgm:nomina:stats:cache_clears"

# Ver informes cacheados
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:*:informe"
```

### 5. Limpiar Cache Manualmente

```bash
# Eliminar cache de un cierre específico
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 DEL "sgm:nomina:20:2025-10"

# Eliminar todas las claves de un cliente
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 --eval "return redis.call('del', unpack(redis.call('keys', 'sgm:nomina:20:*')))"

# Limpiar TODA la DB 2 (¡CUIDADO!)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 FLUSHDB
```

### 6. Monitoreo en Tiempo Real

```bash
# Ver comandos ejecutándose en Redis
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! MONITOR

# Ver info general de Redis
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! INFO

# Ver uso de memoria
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! INFO memory

# Ver estadísticas de keyspace
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! INFO keyspace
```

## 🔧 Casos de Uso Comunes

### Verificar si Dashboard usa Cache o BD

```bash
# 1. Ver si existe cache para cierre 35 (cliente 20, período 2025-10)
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 EXISTS "sgm:nomina:20:2025-10"
# Resultado: 0 = no existe (usará BD), 1 = existe (usará cache)

# 2. Consultar dashboard en frontend
# 3. Verificar campo _metadata.fuente en respuesta API:
#    - "query_directo_bd" = consultó BD directamente
#    - "cache_redis" = usó cache
#    - "informe_persistente" = usó informe histórico
```

### Debug: Dashboard muestra datos viejos

```bash
# 1. Verificar si hay cache para el cierre
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:20:2025-10*"

# 2. Ver TTL del cache
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 TTL "sgm:nomina:20:2025-10"

# 3. Eliminar cache para forzar consulta a BD
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 DEL "sgm:nomina:20:2025-10"

# 4. Recargar dashboard y verificar _metadata.fuente = "query_directo_bd"
```

### Verificar Cleanup después de Consolidación

```bash
# Antes de consolidar
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:20:*"

# Consolidar cierre 35 via API
# POST /api/nomina/consolidacion/35/consolidar/

# Verificar que cache fue eliminado
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:20:*"
# Resultado esperado: (empty array) o solo keys sin "2025-10"

# Verificar en logs de Celery
docker logs sgm-celery-1 --tail 50 | grep "Cache Redis limpiado"
```

### Comparar Cache vs BD

```bash
# 1. Ver contenido del cache
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 GET "sgm:nomina:20:2025-10" | jq

# 2. Ver datos en BD
docker exec -it sgm-db-1 psql -U contabilidad -d sgm_db -c "
SELECT COUNT(*) FROM nomina_conceptoconsolidado 
WHERE cierre_id = 35;
"

# 3. Comparar totales
# Cache: ver campo "total_liquido" en JSON
# BD: sumar campo "monto" en tabla
```

## 📊 Estructura de Claves

### Formato de Claves

```
sgm:nomina:{cliente_id}:{periodo}          # Cache principal de cierre
sgm:nomina:{cliente_id}:{periodo}:informe  # Informe histórico persistente
sgm:nomina:stats:cache_hits                # Estadísticas de aciertos
sgm:nomina:stats:cache_misses              # Estadísticas de fallos
sgm:nomina:stats:cache_clears              # Contador de limpiezas
sgm:nomina:stats:cache_writes              # Contador de escrituras
sgm:nomina:stats:consolidados_cached       # Consolidados en cache
sgm:nomina:stats:informes_cached           # Informes en cache
```

### TTL por Tipo

```
Cache principal:     300-600 segundos (5-10 minutos)
Informe persistente: -1 (sin expiración)
Estadísticas:        24 horas
```

## 🐛 Debugging Tips

### 1. Dashboard muestra "0" después de consolidar

**Causa**: Cache no fue limpiado antes de consolidar

**Solución**:
```bash
# Verificar logs de consolidación
docker logs sgm-celery-1 --tail 100 | grep -i "cache"

# Buscar línea: "🗑️ Cache Redis limpiado para cierre X"
# Si no aparece, el fix de cache cleanup no está aplicado
```

### 2. _metadata.fuente = "cache_redis" pero datos incorrectos

**Causa**: Cache contiene datos viejos

**Solución**:
```bash
# Limpiar cache manualmente
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 DEL "sgm:nomina:20:2025-10"

# Recargar dashboard (debe mostrar _metadata.fuente = "query_directo_bd")
```

### 3. Redis responde "NOAUTH Authentication required"

**Causa**: Falta parámetro `-a` con password

**Solución**:
```bash
# Agregar -a Redis_Password_2025! a todos los comandos
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "*"

# O usar --no-auth-warning para suprimir advertencia
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! --no-auth-warning -n 2 KEYS "*"
```

## 📝 Referencia Rápida

```bash
# Ver estado completo
/tmp/redis_inspector_auth.sh

# Verificar cache de un cierre
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 KEYS "sgm:nomina:{cliente}:{periodo}*"

# Eliminar cache de un cierre
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! -n 2 DEL "sgm:nomina:{cliente}:{periodo}"

# Monitorear actividad
docker exec sgm-redis-1 redis-cli -a Redis_Password_2025! MONITOR
```

## 🔗 Referencias

- **Código cache**: `backend/nomina/cache_redis.py`
- **Cleanup en consolidación**: `backend/nomina/tasks_refactored/consolidacion.py` (líneas ~463, ~1290)
- **Uso en dashboards**: `backend/nomina/views_resumen_libro.py`, `backend/nomina/views_resumen_movimientos.py`
- **Configuración Redis**: `backend/sgm_backend/settings.py`, `docker-compose.yml`

---

**Última actualización**: 29/10/2025  
**Autor**: Smoke Test - Flujo 9 (Dashboards)
