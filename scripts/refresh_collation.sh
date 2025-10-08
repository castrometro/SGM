#!/usr/bin/env bash
set -euo pipefail

# Script para automatizar: backup -> reindex -> refresh collation version
# Requisitos: docker compose up con servicio `db` disponible, y un `.env` en la raíz

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
BACKUP_DIR="$ROOT/backups"
mkdir -p "$BACKUP_DIR"

if [ -f "$ROOT/.env" ]; then
  # exportar variables del .env local
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/.env"
  set +a
else
  echo ".env no encontrado en la raíz del repo. Defina POSTGRES_USER/POSTGRES_DB/POSTGRES_PASSWORD en el entorno o cree .env"
  exit 1
fi

TS=$(date -u +"%Y%m%dT%H%M%SZ")
FILE="${POSTGRES_DB}_${TS}.dump"

CONTAINER=$(docker compose ps -q db || true)
if [ -z "$CONTAINER" ]; then
  echo "Contenedor 'db' no encontrado. Asegúrate de que 'docker compose up' esté corriendo en la raíz del proyecto."
  exit 1
fi

echo "[info] Creando dump de la base '${POSTGRES_DB}' dentro del contenedor..."
docker compose exec -T db bash -lc "pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} -F c -Z 6 -f /tmp/${FILE}"

echo "[info] Copiando dump al host (${BACKUP_DIR}/${FILE})..."
docker cp "${CONTAINER}:/tmp/${FILE}" "${BACKUP_DIR}/${FILE}"
echo "[info] Dump guardado: ${BACKUP_DIR}/${FILE} (tamaño: $(du -h "${BACKUP_DIR}/${FILE}" | cut -f1))"

echo "[info] Reconstruyendo índices (REINDEX DATABASE ${POSTGRES_DB})..."
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "REINDEX DATABASE ${POSTGRES_DB};"

echo "[info] Actualizando versión de collation (ALTER DATABASE ... REFRESH COLLATION VERSION)..."
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "ALTER DATABASE ${POSTGRES_DB} REFRESH COLLATION VERSION;"

echo "[info] Verificando datcollversion..."
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT datname, datcollversion FROM pg_database WHERE datname='${POSTGRES_DB}';"

echo "[ok] Operación completada. Conserva el archivo ${BACKUP_DIR}/${FILE} en un lugar seguro."
