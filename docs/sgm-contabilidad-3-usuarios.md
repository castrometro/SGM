# SGM Contabilidad - Solo Rinde Gastos
## Configuración Docker Optimizada para 3 Usuarios Concurrentes

Este documento proporciona una configuración Docker optimizada específicamente para un SGM de contabilidad que maneja únicamente la funcionalidad de "rinde gastos" para 3 usuarios concurrentes.

## Arquitectura Simplificada

El sistema incluye solo los componentes esenciales:
- **Frontend React**: Interfaz de usuario para captura masiva de gastos
- **Backend Django**: API REST con endpoints de rinde gastos
- **PostgreSQL**: Base de datos para almacenar datos contables
- **Redis**: Cache y cola de tareas asíncronas
- **Celery Worker**: Procesamiento asíncrono de archivos Excel

## Configuración Docker para 3 Usuarios

### docker-compose-contabilidad.yml

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sgm_contabilidad
      POSTGRES_USER: sgm_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --maxmemory 128mb --maxmemory-policy allkeys-lru
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
        reservations:
          memory: 64M
          cpus: '0.1'

  django:
    build:
      context: ./backend
      dockerfile: Dockerfile.contabilidad
    command: bash -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn sgm_backend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --worker-class gevent --worker-connections 50"
    volumes:
      - ./backend:/app
      - static_files:/app/staticfiles
      - media_files:/app/media
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=sgm_backend.settings_contabilidad
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_DB=sgm_contabilidad
      - POSTGRES_USER=sgm_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - db
      - redis
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.contabilidad
    command: celery -A sgm_backend worker -l info -Q contabilidad,rindegastos --concurrency=2
    volumes:
      - ./backend:/app
      - media_files:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=sgm_backend.settings_contabilidad
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_DB=sgm_contabilidad
      - POSTGRES_USER=sgm_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - db
      - redis
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/contabilidad.conf:/etc/nginx/conf.d/default.conf
      - static_files:/var/www/static
      - media_files:/var/www/media
      - ./frontend/dist:/var/www/html
    depends_on:
      - django
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
        reservations:
          memory: 64M
          cpus: '0.1'

volumes:
  postgres_data:
  redis_data:
  static_files:
  media_files:
```

### Configuración de Nginx (nginx/contabilidad.conf)

```nginx
upstream django_backend {
    server django:8000;
}

server {
    listen 80;
    server_name localhost;
    client_max_body_size 100M;

    # Servir archivos estáticos del frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy para API Django
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Servir archivos media (uploads)
    location /media/ {
        alias /var/www/media/;
        expires 30d;
    }

    # Servir archivos estáticos de Django
    location /static/ {
        alias /var/www/static/;
        expires 30d;
    }
}
```

## Variables de Entorno (.env)

```bash
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui
SECRET_KEY=tu_secret_key_django_aqui

# Redis
REDIS_PASSWORD=tu_redis_password_aqui

# Django
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
CORS_ALLOWED_ORIGINS=http://localhost,https://tu-dominio.com

# Configuración para 3 usuarios
MAX_CONCURRENT_UPLOADS=3
MAX_FILE_SIZE=50MB
CELERY_WORKER_CONCURRENCY=2
```

## Dockerfile Optimizado (backend/Dockerfile.contabilidad)

```dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema solo las necesarias
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar solo los archivos de dependencias primero (para cache de Docker)
COPY requirements-contabilidad.txt .
RUN pip install --no-cache-dir -r requirements-contabilidad.txt

# Copiar el código de la aplicación
COPY . .

# Crear usuario no root para seguridad
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["gunicorn", "sgm_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Scripts de Despliegue

### deploy-contabilidad.sh

```bash
#!/bin/bash

echo "=== Desplegando SGM Contabilidad ==="

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "Error: Archivo .env no encontrado"
    exit 1
fi

# Construir y levantar servicios
echo "Construyendo contenedores..."
docker-compose -f docker-compose-contabilidad.yml build

echo "Iniciando servicios..."
docker-compose -f docker-compose-contabilidad.yml up -d

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
sleep 10

# Ejecutar migraciones
echo "Ejecutando migraciones..."
docker-compose -f docker-compose-contabilidad.yml exec django python manage.py migrate

# Crear superusuario si no existe
echo "Verificando superusuario..."
docker-compose -f docker-compose-contabilidad.yml exec django python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@empresa.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"

# Construir frontend
echo "Construyendo frontend..."
npm run build

echo "=== Despliegue completado ==="
echo "Accede a: http://localhost"
echo "Admin Django: http://localhost/admin (admin/admin123)"
```

### monitor-recursos.sh

```bash
#!/bin/bash

echo "=== Monitor de Recursos SGM Contabilidad ==="

while true; do
    clear
    echo "$(date)"
    echo "=================================="
    
    # Uso de CPU y memoria por contenedor
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo ""
    echo "=== Procesos Celery ==="
    docker-compose -f docker-compose-contabilidad.yml exec celery_worker celery -A sgm_backend inspect active
    
    echo ""
    echo "=== Estado Redis ==="
    docker-compose -f docker-compose-contabilidad.yml exec redis redis-cli -a $REDIS_PASSWORD info memory | grep used_memory_human
    
    sleep 5
done
```

## Configuración de Django para Contabilidad

### backend/sgm_backend/settings_contabilidad.py

```python
from .settings import *
import os

# Configuración específica para contabilidad
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Solo apps necesarias para contabilidad
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'contabilidad',
    'api',
]

# Configuración de Celery optimizada para 3 usuarios
CELERY_WORKER_CONCURRENCY = 2
CELERY_TASK_ROUTES = {
    'contabilidad.task_rindegastos.*': {'queue': 'rindegastos'},
    'contabilidad.tasks.*': {'queue': 'contabilidad'},
}

# Limitaciones para 3 usuarios
MAX_CONCURRENT_UPLOADS = 3
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Cache Redis optimizado
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST', 'localhost')}:6379/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 10,
                'retry_on_timeout': True,
            }
        }
    }
}

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/contabilidad.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'contabilidad': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Comandos de Administración

```bash
# Iniciar el sistema
./deploy-contabilidad.sh

# Ver logs en tiempo real
docker-compose -f docker-compose-contabilidad.yml logs -f

# Reiniciar solo el worker de Celery
docker-compose -f docker-compose-contabilidad.yml restart celery_worker

# Acceder al shell de Django
docker-compose -f docker-compose-contabilidad.yml exec django python manage.py shell

# Backup de la base de datos
docker-compose -f docker-compose-contabilidad.yml exec db pg_dump -U sgm_user sgm_contabilidad > backup_$(date +%Y%m%d).sql

# Limpiar cache de Redis
docker-compose -f docker-compose-contabilidad.yml exec redis redis-cli -a $REDIS_PASSWORD flushdb

# Monitor de recursos
./monitor-recursos.sh
```

Esta configuración está optimizada específicamente para manejar 3 usuarios concurrentes trabajando con el sistema de rinde gastos, con recursos limitados pero suficientes para la carga esperada.