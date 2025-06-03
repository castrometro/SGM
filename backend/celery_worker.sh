#!/bin/sh

echo "🚀 Iniciando Celery Worker..."
celery -A sgm_backend worker --loglevel=info
