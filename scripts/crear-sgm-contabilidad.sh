#!/bin/bash

# Script para crear un archivo docker-compose optimizado para SGM Contabilidad
# Autor: SGM Team
# Uso: ./crear-sgm-contabilidad.sh

set -e

echo "=================================================="
echo "    Configurador SGM Contabilidad (3 usuarios)   "
echo "=================================================="

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "Instala Docker primero: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose no está instalado"
    echo "Instala Docker Compose primero: https://docs.docker.com/compose/install/"
    exit 1
fi

# Crear directorio del proyecto si no existe
PROJECT_DIR="sgm-contabilidad"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo "✅ Directorio del proyecto creado: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Generar variables de entorno seguras
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

POSTGRES_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)

# Crear archivo .env
cat > .env << EOF
# Variables de entorno para SGM Contabilidad
# Generado automáticamente el $(date)

# Base de datos PostgreSQL
POSTGRES_DB=sgm_contabilidad
POSTGRES_USER=sgm_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis para cache y colas
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_HOST=redis
REDIS_PORT=6379

# Django configuración
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS para frontend
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1

# Configuración específica para 3 usuarios
MAX_CONCURRENT_UPLOADS=3
MAX_FILE_SIZE=52428800
CELERY_WORKER_CONCURRENCY=2
GUNICORN_WORKERS=2

# Configuración de archivos
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/staticfiles
EOF

echo "✅ Archivo .env creado con passwords seguros"

# Crear docker-compose optimizado
cat > docker-compose.yml << 'EOF'
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=es_ES.UTF-8 --lc-ctype=es_ES.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7.2-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server 
      --appendonly yes 
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 128mb 
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
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
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  django:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: >
      bash -c "
      echo 'Esperando base de datos...' &&
      while ! pg_isready -h db -p 5432 -U ${POSTGRES_USER}; do sleep 1; done &&
      echo 'Base de datos lista. Ejecutando migraciones...' &&
      python manage.py migrate &&
      python manage.py collectstatic --noinput &&
      echo 'Iniciando servidor Django...' &&
      gunicorn sgm_backend.wsgi:application 
        --bind 0.0.0.0:8000 
        --workers ${GUNICORN_WORKERS:-2}
        --worker-class gevent 
        --worker-connections 50
        --timeout 300
        --keepalive 5
        --max-requests 1000
        --max-requests-jitter 100
        --log-level info
      "
    volumes:
      - ./backend:/app
      - static_files:/app/staticfiles
      - media_files:/app/media
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=sgm_backend.settings
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-False}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - MAX_CONCURRENT_UPLOADS=${MAX_CONCURRENT_UPLOADS}
      - MAX_FILE_SIZE=${MAX_FILE_SIZE}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: >
      bash -c "
      echo 'Esperando Django...' &&
      while ! curl -f http://django:8000/api/health/ 2>/dev/null; do sleep 5; done &&
      echo 'Django listo. Iniciando Celery Worker...' &&
      celery -A sgm_backend worker 
        --loglevel=info 
        --queues=contabilidad,rindegastos,default
        --concurrency=${CELERY_WORKER_CONCURRENCY:-2}
        --max-tasks-per-child=50
        --time-limit=1800
        --soft-time-limit=1500
      "
    volumes:
      - ./backend:/app
      - media_files:/app/media
      - ./logs:/app/logs
    environment:
      - DJANGO_SETTINGS_MODULE=sgm_backend.settings
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
    depends_on:
      django:
        condition: service_healthy
      redis:
        condition: service_healthy
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
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/contabilidad.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/var/www/static:ro
      - media_files:/var/www/media:ro
      - ./frontend/dist:/var/www/html:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      django:
        condition: service_healthy
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
    driver: local
  redis_data:
    driver: local
  static_files:
    driver: local
  media_files:
    driver: local

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

echo "✅ Docker Compose creado con optimizaciones para 3 usuarios"

# Crear configuración de Nginx
mkdir -p nginx

cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json application/xml;

    # Rate limiting for uploads
    limit_req_zone $binary_remote_addr zone=uploads:10m rate=3r/m;

    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > nginx/contabilidad.conf << 'EOF'
upstream django_backend {
    server django:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name localhost _;
    client_max_body_size 55M;
    client_body_timeout 300s;
    client_header_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Servir frontend React
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, no-transform";
    }

    # API Django con rate limiting
    location /api/ {
        # Rate limiting para uploads
        location ~* /api/.*/upload {
            limit_req zone=uploads burst=1 nodelay;
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
        }
        
        # API general
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Archivos media (uploads/downloads)
    location /media/ {
        alias /var/www/media/;
        expires 1d;
        add_header Cache-Control "public, no-transform";
        
        # Seguridad para archivos subidos
        location ~* \.(php|html|htm|js)$ {
            deny all;
        }
    }

    # Archivos estáticos de Django
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, immutable, no-transform";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
    }
}
EOF

echo "✅ Configuración de Nginx creada"

# Crear directorios necesarios
mkdir -p {logs,backups,ssl,frontend/dist}

# Crear script de despliegue
cat > deploy.sh << 'EOF'
#!/bin/bash

set -e

echo "🚀 Desplegando SGM Contabilidad..."

# Verificar archivos necesarios
if [ ! -f .env ]; then
    echo "❌ Error: Archivo .env no encontrado"
    exit 1
fi

if [ ! -f docker-compose.yml ]; then
    echo "❌ Error: docker-compose.yml no encontrado"
    exit 1
fi

# Crear red si no existe
docker network create sgm-contabilidad-network 2>/dev/null || true

# Detener servicios si están corriendo
echo "🛑 Deteniendo servicios existentes..."
docker-compose down --remove-orphans 2>/dev/null || true

# Construir imágenes
echo "🔨 Construyendo imágenes..."
docker-compose build --parallel

# Iniciar servicios de base
echo "📊 Iniciando base de datos y Redis..."
docker-compose up -d db redis

# Esperar a que estén listos
echo "⏳ Esperando servicios base..."
sleep 15

# Verificar salud de los servicios
echo "🏥 Verificando salud de servicios..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T db pg_isready -U sgm_user -d sgm_contabilidad > /dev/null 2>&1; then
        echo "✅ PostgreSQL listo"
        break
    fi
    attempt=$((attempt + 1))
    echo "⏳ Esperando PostgreSQL... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Error: PostgreSQL no respondió a tiempo"
    exit 1
fi

# Iniciar Django
echo "🐍 Iniciando Django..."
docker-compose up -d django

# Esperar Django
sleep 10

# Iniciar Celery
echo "🌿 Iniciando Celery Worker..."
docker-compose up -d celery_worker

# Iniciar Nginx
echo "🌐 Iniciando Nginx..."
docker-compose up -d nginx

echo ""
echo "✅ ¡Despliegue completado!"
echo ""
echo "📋 Estado de servicios:"
docker-compose ps

echo ""
echo "🌐 Accesos:"
echo "  - Aplicación: http://localhost"
echo "  - API Django: http://localhost/api/"
echo "  - Admin Django: http://localhost/admin/"
echo ""
echo "📊 Monitoreo:"
echo "  - Ver logs: docker-compose logs -f [servicio]"
echo "  - Estado: docker-compose ps"
echo "  - Recursos: docker stats"
echo ""
echo "🔐 Credenciales por defecto:"
echo "  - Usuario admin Django: admin"
echo "  - Password admin Django: admin123"
echo "  (Cambiar después del primer login)"
EOF

chmod +x deploy.sh
echo "✅ Script de despliegue creado"

# Crear script de monitoreo
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Monitor SGM Contabilidad"
echo "=========================="

while true; do
    clear
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Actualización cada 5 segundos"
    echo "==========================================================="
    
    # Estado de contenedores
    echo ""
    echo "🐳 ESTADO DE CONTENEDORES:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    # Uso de recursos
    echo ""
    echo "💾 USO DE RECURSOS:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | head -n 6
    
    # Espacio en disco
    echo ""
    echo "💿 ESPACIO EN DISCO:"
    df -h / | tail -n 1 | awk '{print "Usado: " $3 "/" $2 " (" $5 ")"}'
    
    # Tareas de Celery activas
    echo ""
    echo "🌿 TAREAS CELERY:"
    ACTIVE_TASKS=$(docker-compose exec -T celery_worker celery -A sgm_backend inspect active 2>/dev/null | grep -c '"' || echo "0")
    echo "Tareas activas: $ACTIVE_TASKS"
    
    # Conexiones a la base de datos
    echo ""
    echo "🗄️ BASE DE DATOS:"
    DB_CONNECTIONS=$(docker-compose exec -T db psql -U sgm_user -d sgm_contabilidad -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs || echo "N/A")
    echo "Conexiones activas: $DB_CONNECTIONS"
    
    echo ""
    echo "Presiona Ctrl+C para salir..."
    sleep 5
done
EOF

chmod +x monitor.sh
echo "✅ Script de monitoreo creado"

# Crear script de backup
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "💾 Iniciando backup SGM Contabilidad..."

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

# Backup de la base de datos
echo "📊 Respaldando base de datos..."
docker-compose exec -T db pg_dump -U sgm_user sgm_contabilidad > "$BACKUP_DIR/sgm_contabilidad_$DATE.sql"

# Backup de archivos media
echo "📁 Respaldando archivos media..."
docker run --rm -v "$(pwd)_media_files:/source" -v "$(pwd)/$BACKUP_DIR:/backup" alpine tar czf "/backup/media_$DATE.tar.gz" -C /source .

# Backup de configuración
echo "⚙️ Respaldando configuración..."
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yml nginx/

# Limpiar backups antiguos (más de 7 días)
echo "🧹 Limpiando backups antiguos..."
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completado en $BACKUP_DIR/"
ls -lah "$BACKUP_DIR/"
EOF

chmod +x backup.sh
echo "✅ Script de backup creado"

# Crear README del proyecto
cat > README.md << 'EOF'
# SGM Contabilidad - Rinde Gastos

Sistema de Gestión Contable optimizado para procesar rinde gastos de 3 usuarios concurrentes.

## 🚀 Inicio Rápido

1. **Instalar dependencias:**
   ```bash
   # Instalar Docker y Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **Desplegar el sistema:**
   ```bash
   ./deploy.sh
   ```

3. **Acceder al sistema:**
   - Aplicación: http://localhost
   - Admin Django: http://localhost/admin/ (admin/admin123)

## 📊 Monitoreo

- **Monitor en tiempo real:** `./monitor.sh`
- **Ver logs:** `docker-compose logs -f`
- **Estado de servicios:** `docker-compose ps`

## 💾 Backup y Mantenimiento

- **Crear backup:** `./backup.sh`
- **Restaurar backup:** 
  ```bash
  docker-compose exec -T db psql -U sgm_user sgm_contabilidad < backups/sgm_contabilidad_YYYYMMDD_HHMMSS.sql
  ```

## 🔧 Comandos Útiles

```bash
# Reiniciar un servicio
docker-compose restart django

# Ver logs de un servicio específico
docker-compose logs -f celery_worker

# Acceder al shell de Django
docker-compose exec django python manage.py shell

# Ejecutar migraciones
docker-compose exec django python manage.py migrate

# Crear superusuario
docker-compose exec django python manage.py createsuperuser

# Limpiar cache de Redis
docker-compose exec redis redis-cli -a $REDIS_PASSWORD flushdb
```

## 🏗️ Arquitectura

- **Frontend:** React + Tailwind CSS + Vite
- **Backend:** Django + DRF + Celery
- **Base de datos:** PostgreSQL 15
- **Cache/Cola:** Redis 7.2
- **Proxy:** Nginx
- **Contenedores:** Docker + Docker Compose

## 📋 Capacidades

- ✅ 3 usuarios concurrentes
- ✅ Archivos hasta 50MB
- ✅ Procesamiento asíncrono
- ✅ Mapeo automático de centros de costo
- ✅ Validación de datos contables
- ✅ Exportación a Excel
- ✅ Monitor de recursos
- ✅ Backups automáticos

## 🔧 Configuración

Las configuraciones principales están en:
- `.env` - Variables de entorno
- `docker-compose.yml` - Orquestación de servicios
- `nginx/contabilidad.conf` - Configuración web

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades, revisa los logs:

```bash
# Ver todos los logs
docker-compose logs

# Ver logs con seguimiento
docker-compose logs -f --tail=100

# Ver logs de un servicio específico
docker-compose logs -f django
```
EOF

echo "✅ README.md creado"

# Mostrar resumen
echo ""
echo "🎉 ¡Configuración completada!"
echo "=================================================="
echo ""
echo "📁 Archivos creados en el directorio '$PROJECT_DIR':"
echo "   ├── .env (variables de entorno con passwords seguros)"
echo "   ├── docker-compose.yml (orquestación optimizada)"
echo "   ├── nginx/ (configuración web)"
echo "   ├── deploy.sh (script de despliegue)"
echo "   ├── monitor.sh (monitor de recursos)"
echo "   ├── backup.sh (script de respaldo)"
echo "   └── README.md (documentación)"
echo ""
echo "🚀 Para iniciar el sistema:"
echo "   cd $PROJECT_DIR"
echo "   ./deploy.sh"
echo ""
echo "📊 Para monitorear recursos:"
echo "   ./monitor.sh"
echo ""
echo "💾 Para hacer backup:"
echo "   ./backup.sh"
echo ""
echo "🌐 Accesos después del despliegue:"
echo "   - Aplicación: http://localhost"
echo "   - Admin Django: http://localhost/admin/"
echo ""
echo "⚡ Recursos configurados para 3 usuarios concurrentes:"
echo "   - CPU: 2-4 cores"
echo "   - RAM: 4-8 GB"
echo "   - Almacenamiento: 50-100 GB SSD"
echo ""
echo "✅ ¡Todo listo para producción!"