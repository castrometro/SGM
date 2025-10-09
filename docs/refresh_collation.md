# Refresh Collation Version (runbook breve)

Este documento describe el procedimiento para resolver avisos de "collation version mismatch" en PostgreSQL y proporciona un script automatizado.

Resumen rápido

- Problema: PostgreSQL muestra un warning similar a:

  "WARNING: database \"sgm_db\" has a collation version mismatch\nDETAIL: The database was created using collation version 2.36, but the operating system provides version 2.41."

- Solución general: crear backup → reconstruir índices (REINDEX) → actualizar metadata de la base con `ALTER DATABASE ... REFRESH COLLATION VERSION`.

Archivos incluidos

- `scripts/refresh_collation.sh` — script que ejecuta el flujo: dump -> reindex -> refresh. Requiere `docker compose` y un `.env` en la raíz con `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Uso

1. Asegúrate de tener los contenedores levantados: `docker compose up -d` desde la raíz del repo.
2. Ejecuta:

```bash
chmod +x scripts/refresh_collation.sh
./scripts/refresh_collation.sh
```

Esto generará archivos en `backups/` con los dumps (`<DBNAME>_YYYYMMDDThhmmssZ.dump`), ejecutará `REINDEX DATABASE` y luego `ALTER DATABASE ... REFRESH COLLATION VERSION` para cada base objetivo.

Por defecto, el script procesa la base definida en `POSTGRES_DB` y también la base `postgres` (que es la que suele mostrar el warning en logs del servidor). Si quieres limitar o ampliar las bases, pásalas como argumento separadas por espacios:

```bash
./scripts/refresh_collation.sh "postgres sgm_db otra_base"
```

Notas y recomendaciones

- Haz este procedimiento en ventana de baja carga en entornos de producción; `REINDEX` puede ser costoso para bases grandes.
- Siempre conserva el dump fuera del host si es crítico (por ejemplo, copiar a storage externo).
- Si usas replicas o streaming replication, consulta la docs de PostgreSQL para aplicar cambios de collation de forma segura en replicación.
- Si el usuario de la base no es superuser, necesitarás ejecutar estos comandos con un rol superuser.

Errores comunes

- Permisos: `ALTER DATABASE ... REFRESH COLLATION VERSION` requiere privilegios elevados; si falla, verifica el rol.
- Servicio no disponible: si `docker compose ps -q db` está vacío, levanta los servicios en la raíz del repo.

Referencias

- Documentación oficial de PostgreSQL: https://www.postgresql.org/docs/current/collation.html
