#!/usr/bin/env bash
# Crea un Project clásico (a nivel de repo), columnas y agrega issues existentes como tarjetas.
# Requisitos: gh CLI autenticado (gh auth login) y permisos en el repo.
# Nota: Projects clásicos son por repo; los Projects (v2) son a nivel de usuario/org.
set -euo pipefail

OWNER=${OWNER:-castrometro}
REPO=${REPO:-SGM}
PROJECT_NAME=${PROJECT_NAME:-"SGM - Kanban"}
PROJECT_BODY=${PROJECT_BODY:-"Tablero Kanban de bugs y mejoras de nómina (Celery, libro, novedades, analista, movimientos)."}
ISSUES=${ISSUES:-"93 94 95 96 97 99 100"}

# Crear Project clásico en el repo (REST v3: Inertia API)
PROJECT_JSON=$(gh api -X POST \
  -H "Accept: application/vnd.github.inertia+json" \
  repos/$OWNER/$REPO/projects \
  -f name="$PROJECT_NAME" \
  -f body="$PROJECT_BODY")
PROJECT_ID=$(echo "$PROJECT_JSON" | jq -r .id)
HTML_URL=$(echo "$PROJECT_JSON" | jq -r .html_url)

echo "Proyecto creado: $HTML_URL (id=$PROJECT_ID)"

# Crear columnas
for COL in "To do" "In progress" "Blocked" "Done"; do
  gh api -X POST \
    -H "Accept: application/vnd.github.inertia+json" \
    repos/$OWNER/$REPO/projects/$PROJECT_ID/columns \
    -f name="$COL" >/dev/null
  echo "Columna creada: $COL"
done

# Obtener IDs de columnas
TO_DO_ID=$(gh api -H "Accept: application/vnd.github.inertia+json" repos/$OWNER/$REPO/projects/$PROJECT_ID/columns | jq -r '.[] | select(.name=="To do") | .id')
IN_PROGRESS_ID=$(gh api -H "Accept: application/vnd.github.inertia+json" repos/$OWNER/$REPO/projects/$PROJECT_ID/columns | jq -r '.[] | select(.name=="In progress") | .id')

# Agregar issues como tarjetas en "To do"
for N in $ISSUES; do
  # Obtener node id del issue (content_id para cards clásicas es el ID entero de la issue, no el node_id)
  ISSUE_JSON=$(gh api repos/$OWNER/$REPO/issues/$N)
  ISSUE_ID=$(echo "$ISSUE_JSON" | jq -r .id)
  TITLE=$(echo "$ISSUE_JSON" | jq -r .title)

  gh api -X POST \
    -H "Accept: application/vnd.github.inertia+json" \
    projects/columns/$TO_DO_ID/cards \
    -f content_id="$ISSUE_ID" \
    -f content_type=Issue >/dev/null
  echo "Tarjeta creada desde issue #$N: $TITLE"

done

echo "Listo. Revisa el tablero: $HTML_URL"
