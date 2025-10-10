# Requisitos Mínimos de Sistema - SGM Contabilidad (Rinde Gastos)
## Especificaciones para 3 Usuarios Concurrentes

### Resumen Ejecutivo

Este documento especifica los requisitos mínimos de hardware y software para ejecutar un SGM de contabilidad dedicado exclusivamente a la funcionalidad de "rinde gastos" con capacidad para 3 usuarios concurrentes.

## Especificaciones Mínimas de Hardware

### Servidor Principal

| Componente | Mínimo | Recomendado | Observaciones |
|------------|--------|-------------|---------------|
| **CPU** | 2 cores / 4 threads | 4 cores / 8 threads | Intel i5-8400 o AMD Ryzen 5 2600 mínimo |
| **RAM** | 4 GB | 8 GB | 6 GB utilizables después del OS |
| **Almacenamiento** | 50 GB SSD | 100 GB SSD | Incluye OS, aplicación y datos |
| **Red** | 100 Mbps | 1 Gbps | Para subida de archivos Excel |

### Breakdown de Uso de Memoria

| Servicio | RAM Mínima | RAM Recomendada | Descripción |
|----------|------------|-----------------|-------------|
| **Sistema Operativo** | 1 GB | 2 GB | Linux Ubuntu/CentOS |
| **PostgreSQL** | 256 MB | 512 MB | Base de datos contable |
| **Redis** | 64 MB | 128 MB | Cache y cola de tareas |
| **Django Backend** | 512 MB | 1 GB | API REST + 2 workers |
| **Celery Worker** | 512 MB | 1 GB | Procesamiento Excel |
| **Nginx** | 64 MB | 128 MB | Proxy reverso |
| **Frontend (estático)** | 0 MB | 0 MB | Servido por Nginx |
| **Buffer del sistema** | 512 MB | 1 GB | Cache de archivos y overhead |
| **TOTAL** | **2.9 GB** | **5.8 GB** | |

### Breakdown de Uso de CPU

| Escenario | CPU Esperado | Observaciones |
|-----------|-------------|---------------|
| **Sistema en reposo** | 5-10% | Solo servicios base |
| **1 usuario procesando Excel** | 30-50% | Celery + pandas/openpyxl |
| **3 usuarios concurrentes** | 70-90% | Peak de uso máximo |
| **Solo navegación/consultas** | 10-20% | Sin procesamiento pesado |

## Especificaciones Detalladas por Componente

### PostgreSQL Database
```yaml
Configuración mínima:
- shared_buffers: 128MB
- effective_cache_size: 512MB
- work_mem: 16MB
- max_connections: 20
- checkpoint_segments: 8

Espacio en disco:
- Instalación: 200MB
- Datos iniciales: 100MB
- Crecimiento mensual estimado: 50MB (500 registros/mes)
- Logs: 100MB
```

### Redis Cache
```yaml
Configuración mínima:
- maxmemory: 64MB
- maxmemory-policy: allkeys-lru
- appendonly: yes (persistencia)
- save: 900 1 300 10 60 10000

Uso típico:
- Sessions: 5MB (3 usuarios × 1.5MB)
- Cache de consultas: 20MB
- Cola de tareas: 10MB
- Buffer: 29MB
```

### Django + Gunicorn
```yaml
Configuración para 3 usuarios:
- Workers: 2 (gevent)
- Worker connections: 50
- Max file size: 50MB
- Timeout: 300s
- Memory per worker: 256MB

Librerías críticas:
- pandas: ~100MB memoria base
- openpyxl: ~50MB por archivo Excel procesado
- Django: ~80MB por worker
```

### Celery Workers
```yaml
Configuración optimizada:
- Concurrency: 2 workers
- Queues: rindegastos, contabilidad
- Memory per task: 200-300MB
- Max tasks per child: 50 (para evitar memory leaks)

Procesamiento típico:
- Archivo 1000 filas: 2-5 minutos
- Memoria peak: 400MB por archivo
- CPU intensivo durante procesamiento
```

## Benchmarks de Rendimiento

### Tiempos de Procesamiento Esperados

| Tamaño Archivo Excel | Filas | Tiempo Procesamiento | Memoria Utilizada |
|---------------------|-------|---------------------|-------------------|
| 1 MB | 100 registros | 15-30 segundos | 150MB |
| 5 MB | 500 registros | 1-2 minutos | 250MB |
| 10 MB | 1000 registros | 2-5 minutos | 400MB |
| 25 MB | 2500 registros | 5-12 minutos | 600MB |
| 50 MB | 5000 registros | 10-25 minutos | 800MB |

### Capacidad Concurrente

| Usuarios Simultáneos | CPU Utilizada | RAM Utilizada | Tiempo Respuesta Web |
|---------------------|---------------|---------------|---------------------|
| 1 usuario | 30-40% | 3.5 GB | < 2 segundos |
| 2 usuarios | 50-70% | 4.2 GB | < 3 segundos |
| 3 usuarios | 70-90% | 5.0 GB | < 5 segundos |
| 4+ usuarios | 90%+ | 5.5 GB+ | > 10 segundos (degradado) |

## Configuraciones de Red y Almacenamiento

### Requisitos de Red
```
Ancho de banda por usuario:
- Subida de archivos: 5-10 Mbps (archivos 10-50MB)
- Navegación normal: 1-2 Mbps
- Descarga de resultados: 2-5 Mbps

Total recomendado: 50 Mbps subida / 25 Mbps bajada
```

### Almacenamiento por Tipos de Datos
```
/app/media/uploads/     # Archivos Excel subidos
├── retention: 30 días
├── growth: 500MB/mes
└── backup: diario

/var/lib/postgresql/    # Base de datos
├── growth: 50MB/mes
├── backup: diario
└── archival: anual

/var/log/              # Logs del sistema
├── retention: 7 días
├── rotation: diario
└── size: 1GB/mes

/app/static/           # Archivos estáticos (frontend)
├── size: 50MB
├── retention: permanent
└── cdn: recomendado para producción
```

## Configuraciones Específicas del SO

### Linux (Ubuntu 20.04/22.04)
```bash
# Configuraciones del kernel para mejor rendimiento
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf

# Límites de archivos abiertos
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf

# Configuración de red para múltiples conexiones
echo 'net.core.somaxconn=1024' >> /etc/sysctl.conf
echo 'net.ipv4.ip_local_port_range=10240 65535' >> /etc/sysctl.conf
```

### Docker Resource Limits
```yaml
# Limites por servicio para evitar monopolización
services:
  django:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
  
  celery_worker:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
  
  postgres:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## Scripts de Monitoreo

### Monitor de recursos en tiempo real
```bash
#!/bin/bash
# monitor-sgm-contabilidad.sh

echo "=== SGM Contabilidad - Monitor de Recursos ==="

while true; do
    clear
    echo "$(date) - Monitoreo cada 5 segundos"
    echo "=========================================="
    
    # CPU y memoria total del sistema
    echo "=== SISTEMA ==="
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "RAM: $(free -h | awk 'NR==2{printf "%.1f/%.1fGB (%.1f%%)", $3/1024/1024,$2/1024/1024,$3*100/$2}')"
    echo "Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"
    
    echo ""
    echo "=== DOCKER CONTAINERS ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | head -n 7
    
    echo ""
    echo "=== USUARIOS ACTIVOS ==="
    docker-compose -f docker-compose-contabilidad.yml exec django python manage.py shell -c "
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
active_sessions = Session.objects.filter(expire_date__gte=timezone.now() - timedelta(minutes=15))
print(f'Sesiones activas (últimos 15 min): {active_sessions.count()}')
"
    
    echo ""
    echo "=== CELERY TASKS ==="
    docker-compose -f docker-compose-contabilidad.yml exec celery_worker celery -A sgm_backend inspect active --quiet | grep -c "tasks" || echo "0 tareas activas"
    
    echo ""
    echo "=== PRESIONA CTRL+C PARA SALIR ==="
    sleep 5
done
```

### Monitor de alertas
```bash
#!/bin/bash
# alertas-sgm.sh

CPU_THRESHOLD=85
MEM_THRESHOLD=85
DISK_THRESHOLD=90

check_resources() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'.' -f1)
    MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    DISK_USAGE=$(df / | awk 'NR==2{print $5}' | cut -d'%' -f1)
    
    if [ $CPU_USAGE -gt $CPU_THRESHOLD ]; then
        echo "ALERTA: CPU alto: ${CPU_USAGE}%" | tee -a /var/log/sgm-alerts.log
    fi
    
    if [ $MEM_USAGE -gt $MEM_THRESHOLD ]; then
        echo "ALERTA: Memoria alta: ${MEM_USAGE}%" | tee -a /var/log/sgm-alerts.log
    fi
    
    if [ $DISK_USAGE -gt $DISK_THRESHOLD ]; then
        echo "ALERTA: Disco lleno: ${DISK_USAGE}%" | tee -a /var/log/sgm-alerts.log
    fi
}

# Ejecutar cada minuto
while true; do
    check_resources
    sleep 60
done
```

## Recomendaciones de Implementación

### Fase de Pruebas (Entorno Mínimo)
- **Hardware**: 2 cores, 4GB RAM, 50GB SSD
- **Usuarios**: 1-2 usuarios de prueba
- **Archivos**: Máximo 1000 registros
- **Duración**: 2-4 semanas de testing

### Fase de Producción (Entorno Recomendado)
- **Hardware**: 4 cores, 8GB RAM, 100GB SSD
- **Usuarios**: 3 usuarios concurrentes
- **Archivos**: Hasta 5000 registros por archivo
- **Monitoreo**: Alertas automáticas configuradas

### Escalabilidad Futura
- **+1 usuario adicional**: +1GB RAM, +0.5 cores
- **Archivos más grandes**: +2GB RAM, +SSD más rápido
- **Alta disponibilidad**: Load balancer + 2+ servidores

## Conclusión

Para un SGM de contabilidad dedicado a rinde gastos con 3 usuarios concurrentes, los requisitos mínimos absolutos son **2 cores CPU y 4GB RAM**, pero se recomienda fuertemente **4 cores y 8GB RAM** para un funcionamiento óptimo y margen de crecimiento.

El costo-beneficio óptimo se logra con la configuración recomendada, que proporciona un rendimiento fluido y capacidad de expansión sin sobre-dimensionar los recursos.