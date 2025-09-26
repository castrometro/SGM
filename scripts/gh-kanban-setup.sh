#!/usr/bin/env bash
# Script opcional para crear un GitHub Project (kanban) vía gh CLI.
# No ejecuta nada por sí solo; revisa, ajusta variables y luego ejecútalo manualmente.
# Requisitos: gh CLI autenticado (gh auth login) y permisos para crear Projects en la organización/repo.

set -euo pipefail

# Configura estos valores antes de usar
ORG_OR_USER="castrometro"     # organización o usuario dueño del repo
REPO_NAME="SGM"               # nombre del repo
PROJECT_TITLE="SGM Kanban"    # nombre del proyecto
PROJECT_DESC="Tablero Kanban de bugs y mejoras del pipeline de nómina."

# Crear proyecto (nota: GitHub Projects (beta) son a nivel org/usuario, no de repo)
# Descomenta una de las siguientes líneas según quieras crearlo en usuario u organización.

# Crear en usuario
# gh project create "$PROJECT_TITLE" --owner "$ORG_OR_USER" --format json | tee .project.json

# Crear en organización
# gh project create "$PROJECT_TITLE" --org "$ORG_OR_USER" --format json | tee .project.json

# Obtener ID del proyecto si ya existe (ejemplo)
# PROJECT_ID=$(gh project list --owner "$ORG_OR_USER" --format json | jq -r '.[] | select(.title=="'$PROJECT_TITLE'") | .id')
# echo "Project ID: $PROJECT_ID"

# Crear columnas (para Projects clásicos). Para Projects (beta) usa campos personalizados y vistas.
# gh project column create --project "$PROJECT_ID" --name "To Do"
# gh project column create --project "$PROJECT_ID" --name "In Progress"
# gh project column create --project "$PROJECT_ID" --name "Blocked"
# gh project column create --project "$PROJECT_ID" --name "Done"

# Crear issues/tarjetas a partir de las líneas principales del Kanban.md
# while read -r line; do
#   title=$(echo "$line" | sed 's/^- \[.*\] //')
#   body="Ver docs/Fixes de tareas celery.md para detalles."
#   gh issue create --repo "$ORG_OR_USER/$REPO_NAME" --title "$title" --body "$body" --label "kanban"
# done < <(grep '^-' docs/Kanban.md | grep -v 'Documentación:')

# Luego puedes añadir los issues al proyecto
# for ISSUE in $(gh issue list --repo "$ORG_OR_USER/$REPO_NAME" --label kanban --state open --json number --jq '.[].number'); do
#   gh project item-add --owner "$ORG_OR_USER" --project "$PROJECT_TITLE" --url "https://github.com/$ORG_OR_USER/$REPO_NAME/issues/$ISSUE"
# done

# Fin. Revisa y ejecuta manualmente los pasos necesarios.
