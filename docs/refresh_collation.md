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

Esto generará un archivo en `backups/` con el dump (`<POSTGRES_DB>_YYYYMMDDThhmmssZ.dump`), ejecutará `REINDEX DATABASE` y luego `ALTER DATABASE ... REFRESH COLLATION VERSION`.

Notas y recomendaciones

- Haz este procedimiento en ventana de baja carga en entornos de producción; `REINDEX` puede ser costoso para bases grandes.
- Siempre conserva el dump fuera del host si es crítico (por ejemplo, copiar a storage externo).
- Si usas replicas o streaming replication, consulta la docs de PostgreSQL para aplicar cambios de collation de forma segura en replicación.
- Si el usuario de la base no es superuser, necesitarás ejecutar estos comandos con un rol superuser.

Referencias

- Documentación oficial de PostgreSQL: https://www.postgresql.org/docs/current/collation.html
