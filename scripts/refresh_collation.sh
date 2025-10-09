#!/usr/bin/env bash
set -euo pipefail

# Script para automatizar: backup -> reindex -> refresh collation version
# Requisitos: docker compose up con servicio `db` disponible, y un `.env` en la raíz

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
BACKUP_DIR="$ROOT/backups"
mkdir -p "$BACKUP_DIR"

if [ -f "$ROOT/.env" ]; then
  # Cargar solo variables necesarias desde .env (evita errores por caracteres especiales en otras vars como SECRET_KEY)
  while IFS='=' read -r key value; do
    case "$key" in
      POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_HOST|POSTGRES_PORT)
        # Quitar comillas si existen
        value="${value%\"}"
        value="${value#\"}"
        export "$key=$value"
        ;;
    esac
  done < <(grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_HOST|POSTGRES_PORT)=' "$ROOT/.env")
else
  echo ".env no encontrado en la raíz del repo. Defina POSTGRES_USER/POSTGRES_DB/POSTGRES_PASSWORD en el entorno o cree .env"
  exit 1
fi

TS=$(date -u +"%Y%m%dT%H%M%SZ")

# Permite pasar lista de bases por argumento: ./scripts/refresh_collation.sh "db1 db2 ..."
# Si no se especifica, por defecto procesa POSTGRES_DB y la base "postgres" (para limpiar el warning típico)
DB_LIST_INPUT=${1:-}
if [ -n "$DB_LIST_INPUT" ]; then
  read -r -a DB_LIST <<< "$DB_LIST_INPUT"
else
  # Evita duplicar si POSTGRES_DB ya es 'postgres'
  if [ "${POSTGRES_DB}" = "postgres" ]; then
    DB_LIST=("postgres")
  else
    DB_LIST=("${POSTGRES_DB}" "postgres")
  fi
fi

CONTAINER=$(docker compose ps -q db || true)
if [ -z "$CONTAINER" ]; then
  echo "Contenedor 'db' no encontrado. Asegúrate de que 'docker compose up' esté corriendo en la raíz del proyecto."
  exit 1
fi

# Helper para pasar PGPASSWORD a herramientas de cliente
DOCKER_EXEC=(docker compose exec -T -e "PGPASSWORD=${POSTGRES_PASSWORD}" db)

for DB_NAME in "${DB_LIST[@]}"; do
  FILE="${DB_NAME}_${TS}.dump"

  echo "[info] Creando dump de la base '${DB_NAME}' dentro del contenedor..."
  "${DOCKER_EXEC[@]}" bash -lc "pg_dump -U ${POSTGRES_USER} -d ${DB_NAME} -F c -Z 6 -f /tmp/${FILE}"

  echo "[info] Copiando dump al host (${BACKUP_DIR}/${FILE})..."
  docker cp "${CONTAINER}:/tmp/${FILE}" "${BACKUP_DIR}/${FILE}"
  echo "[info] Dump guardado: ${BACKUP_DIR}/${FILE} (tamaño: $(du -h \"${BACKUP_DIR}/${FILE}\" | cut -f1))"

  echo "[info] Reconstruyendo índices (REINDEX DATABASE ${DB_NAME})..."
  "${DOCKER_EXEC[@]}" psql -U "${POSTGRES_USER}" -d "${DB_NAME}" -c "REINDEX DATABASE ${DB_NAME};"

  echo "[info] Actualizando versión de collation (ALTER DATABASE ${DB_NAME} REFRESH COLLATION VERSION)..."
  "${DOCKER_EXEC[@]}" psql -U "${POSTGRES_USER}" -d "${DB_NAME}" -c "ALTER DATABASE ${DB_NAME} REFRESH COLLATION VERSION;"

  echo "[info] Verificando datcollversion para '${DB_NAME}'..."
  "${DOCKER_EXEC[@]}" psql -U "${POSTGRES_USER}" -d "${DB_NAME}" -c "SELECT datname, datcollversion FROM pg_database WHERE datname='${DB_NAME}';"
done

echo "[ok] Operación completada. Conserva los archivos ${BACKUP_DIR}/*_${TS}.dump en un lugar seguro."
