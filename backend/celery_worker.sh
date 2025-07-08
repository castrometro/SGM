#!/bin/bash

echo "Iniciando Celery worker en 5 segundos..."
sleep 5

celery -A sgm_backend worker --loglevel=info --concurrency=2