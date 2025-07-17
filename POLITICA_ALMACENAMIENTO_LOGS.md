# Política de Almacenamiento de Logs - Sistema Híbrido

## Arquitectura Propuesta

### 1. Base de Datos PostgreSQL (Persistencia)
- **Propósito**: Almacenamiento permanente de todos los logs
- **Retención**: Indefinida (con política de archivado opcional)
- **Uso**: Consultas históricas, auditoría, reportes

### 2. Redis Cache (Logs Recientes)
- **Propósito**: Acceso rápido a logs recientes
- **Retención**: Últimos 7 días o 1000 logs por cliente
- **Uso**: Dashboard en tiempo real, consultas frecuentes

## Flujo de Datos

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Aplicación    │───▶│   PostgreSQL    │───▶│     Redis       │
│   (Log Entry)   │    │   (Persistir)   │    │   (Cachear)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │    Dashboard    │
                                               │  (Consulta)     │
                                               └─────────────────┘
```

## Implementación

### 1. Modificación del Activity Logger

Archivo: `/backend/contabilidad/utils/activity_logger.py`

```python
import redis
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

# Configuración Redis
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB_LOGS,  # DB separada para logs
    decode_responses=True
)

class ActivityLogStorage:
    RECENT_LOGS_TTL = 7 * 24 * 60 * 60  # 7 días en segundos
    MAX_LOGS_PER_CLIENT = 1000
    
    @staticmethod
    def save_to_redis(log_entry):
        """Guarda log en Redis con TTL"""
        try:
            # Serializar el log
            log_data = {
                'id': log_entry.id,
                'cliente_id': log_entry.cierre.cliente.id,
                'cliente_nombre': log_entry.cierre.cliente.nombre,
                'usuario_id': log_entry.usuario.id if log_entry.usuario else None,
                'usuario_nombre': f"{log_entry.usuario.nombre} {log_entry.usuario.apellido}" if log_entry.usuario else 'Sistema',
                'usuario_email': log_entry.usuario.correo_bdo if log_entry.usuario else None,
                'tarjeta': log_entry.tarjeta,
                'accion': log_entry.accion,
                'descripcion': log_entry.descripcion,
                'resultado': log_entry.resultado,
                'timestamp': log_entry.timestamp.isoformat(),
                'ip_address': log_entry.ip_address,
                'detalles': log_entry.detalles,
                'estado_cierre': log_entry.cierre.estado,
                'periodo_cierre': log_entry.cierre.periodo,
            }
            
            # Claves Redis
            global_key = f"logs:recent:global"
            client_key = f"logs:recent:client:{log_entry.cierre.cliente.id}"
            period_key = f"logs:recent:period:{log_entry.cierre.periodo}"
            
            # Guardar en múltiples índices
            with redis_client.pipeline() as pipe:
                # Log individual
                pipe.set(
                    f"log:{log_entry.id}",
                    json.dumps(log_data, cls=DjangoJSONEncoder),
                    ex=ActivityLogStorage.RECENT_LOGS_TTL
                )
                
                # Índice global (últimos logs del sistema)
                pipe.zadd(global_key, {log_entry.id: log_entry.timestamp.timestamp()})
                pipe.expire(global_key, ActivityLogStorage.RECENT_LOGS_TTL)
                
                # Índice por cliente
                pipe.zadd(client_key, {log_entry.id: log_entry.timestamp.timestamp()})
                pipe.expire(client_key, ActivityLogStorage.RECENT_LOGS_TTL)
                
                # Índice por período
                pipe.zadd(period_key, {log_entry.id: log_entry.timestamp.timestamp()})
                pipe.expire(period_key, ActivityLogStorage.RECENT_LOGS_TTL)
                
                # Limitar cantidad por cliente
                pipe.zremrangebyrank(client_key, 0, -(ActivityLogStorage.MAX_LOGS_PER_CLIENT + 1))
                
                pipe.execute()
                
        except Exception as e:
            logger.error(f"Error guardando log en Redis: {e}")
    
    @staticmethod
    def get_recent_logs(cliente_id=None, periodo=None, limit=50):
        """Obtiene logs recientes desde Redis"""
        try:
            # Seleccionar clave según filtros
            if cliente_id and periodo:
                key = f"logs:recent:client:{cliente_id}:period:{periodo}"
            elif cliente_id:
                key = f"logs:recent:client:{cliente_id}"
            elif periodo:
                key = f"logs:recent:period:{periodo}"
            else:
                key = "logs:recent:global"
            
            # Obtener IDs de logs ordenados por timestamp (más recientes primero)
            log_ids = redis_client.zrevrange(key, 0, limit - 1)
            
            # Obtener datos de logs
            logs = []
            for log_id in log_ids:
                log_data = redis_client.get(f"log:{log_id}")
                if log_data:
                    logs.append(json.loads(log_data))
            
            return logs
            
        except Exception as e:
            logger.error(f"Error obteniendo logs desde Redis: {e}")
            return []

def registrar_actividad_tarjeta(
    cliente_id,
    periodo,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado='exito',
    ip_address=None
):
    """
    Versión mejorada que guarda en PostgreSQL y Redis
    """
    try:
        # Buscar el cierre
        cierre = CierreContabilidad.objects.filter(
            cliente_id=cliente_id,
            periodo=periodo,
        ).first()

        if not cierre:
            logger.warning(
                "Se intentó registrar actividad para un cierre inexistente (%s - %s)",
                cliente_id,
                periodo,
            )
            return None
        
        # Guardar en PostgreSQL (persistencia)
        log_entry = TarjetaActivityLog.objects.create(
            cierre=cierre,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles or {},
            resultado=resultado,
            ip_address=ip_address
        )
        
        # Guardar en Redis (cache reciente)
        ActivityLogStorage.save_to_redis(log_entry)
        
        return log_entry
        
    except Exception as e:
        logger.error("Error registrando actividad: %s", e)
        return None
```

### 2. Modificación del Endpoint de Logs

Archivo: `/backend/contabilidad/views/gerente.py`

```python
from ..utils.activity_logger import ActivityLogStorage

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_logs_actividad(request):
    """
    Obtiene logs usando estrategia híbrida:
    - Redis para logs recientes (últimos 7 días)
    - PostgreSQL para búsquedas históricas
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Obtener filtros
    cliente_id = request.GET.get('cliente_id')
    usuario_id = request.GET.get('usuario_id')
    tarjeta = request.GET.get('tarjeta')
    accion = request.GET.get('accion')
    cierre = request.GET.get('cierre')
    periodo = request.GET.get('periodo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # Determinar estrategia de consulta
    use_redis = should_use_redis_cache(fecha_desde, fecha_hasta)
    
    if use_redis:
        # Usar Redis para logs recientes
        logs_data = get_logs_from_redis(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            tarjeta=tarjeta,
            accion=accion,
            cierre=cierre,
            periodo=periodo,
            page=page,
            page_size=page_size
        )
    else:
        # Usar PostgreSQL para búsquedas históricas
        logs_data = get_logs_from_postgres(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            tarjeta=tarjeta,
            accion=accion,
            cierre=cierre,
            periodo=periodo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            page_size=page_size
        )
    
    return Response(logs_data)

def should_use_redis_cache(fecha_desde, fecha_hasta):
    """Determina si usar Redis o PostgreSQL según los filtros"""
    # Si no hay filtros de fecha, usar Redis (logs recientes)
    if not fecha_desde and not fecha_hasta:
        return True
    
    # Si hay filtros de fecha, verificar si están en el rango de Redis
    if fecha_desde:
        fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
        if fecha_desde_dt < datetime.now() - timedelta(days=7):
            return False
    
    return True

def get_logs_from_redis(cliente_id=None, usuario_id=None, tarjeta=None, 
                       accion=None, cierre=None, periodo=None, 
                       page=1, page_size=20):
    """Obtiene logs desde Redis con filtros"""
    try:
        # Obtener logs recientes
        logs = ActivityLogStorage.get_recent_logs(
            cliente_id=cliente_id,
            periodo=periodo,
            limit=1000  # Límite amplio para filtrado
        )
        
        # Aplicar filtros adicionales
        if usuario_id:
            logs = [log for log in logs if log.get('usuario_id') == int(usuario_id)]
        
        if tarjeta:
            logs = [log for log in logs if log.get('tarjeta') == tarjeta]
        
        if accion:
            logs = [log for log in logs if log.get('accion') == accion]
        
        if cierre:
            logs = [log for log in logs if log.get('estado_cierre') == cierre]
        
        # Paginación
        total_count = len(logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]
        
        return {
            'results': paginated_logs,
            'count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size,
            'current_page': page,
            'has_next': end_idx < total_count,
            'has_previous': page > 1,
            'source': 'redis'  # Para debugging
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo logs desde Redis: {e}")
        # Fallback a PostgreSQL
        return get_logs_from_postgres(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            tarjeta=tarjeta,
            accion=accion,
            cierre=cierre,
            periodo=periodo,
            page=page,
            page_size=page_size
        )

def get_logs_from_postgres(cliente_id=None, usuario_id=None, tarjeta=None,
                          accion=None, cierre=None, periodo=None,
                          fecha_desde=None, fecha_hasta=None,
                          page=1, page_size=20):
    """Obtiene logs desde PostgreSQL (método original)"""
    # Lógica existente de PostgreSQL
    logs = TarjetaActivityLog.objects.select_related(
        'cierre', 'cierre__cliente', 'usuario'
    ).all()
    
    # Aplicar filtros (código existente)
    if cliente_id:
        logs = logs.filter(cierre__cliente_id=cliente_id)
    
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    
    if tarjeta:
        logs = logs.filter(tarjeta=tarjeta)
    
    if accion:
        logs = logs.filter(accion=accion)
    
    if cierre:
        logs = logs.filter(cierre__estado=cierre)
    
    if periodo:
        logs = logs.filter(cierre__periodo=periodo)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            logs = logs.filter(timestamp__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    # Ordenar y paginar
    logs = logs.order_by('-timestamp')
    paginator = Paginator(logs, page_size)
    page_obj = paginator.get_page(page)
    
    # Serializar
    results = []
    for log in page_obj.object_list:
        results.append({
            'id': log.id,
            'cliente_id': log.cierre.cliente.id if log.cierre and log.cierre.cliente else None,
            'cliente_nombre': log.cierre.cliente.nombre if log.cierre and log.cierre.cliente else 'N/A',
            'usuario_nombre': f"{log.usuario.nombre} {log.usuario.apellido}" if log.usuario else 'Sistema',
            'usuario_email': log.usuario.correo_bdo if log.usuario else 'N/A',
            'tarjeta': log.tarjeta,
            'accion': log.accion,
            'descripcion': log.descripcion,
            'resultado': log.resultado,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'ip_address': log.ip_address,
            'detalles': log.detalles,
            'estado_cierre': log.cierre.estado if log.cierre else None,
            'periodo_cierre': log.cierre.periodo if log.cierre else None,
        })
    
    return {
        'results': results,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'source': 'postgres'  # Para debugging
    }
```

### 3. Configuración Redis

Archivo: `/backend/settings.py`

```python
# Configuración Redis para logs
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB_LOGS = int(os.getenv('REDIS_DB_LOGS', 1))  # DB1 para contabilidad

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'redis_logs': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/redis_activity.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'contabilidad.utils.activity_logger': {
            'handlers': ['redis_logs'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 4. Comando de Gestión para Sincronización

Archivo: `/backend/contabilidad/management/commands/sync_logs_redis.py`

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from contabilidad.models import TarjetaActivityLog
from contabilidad.utils.activity_logger import ActivityLogStorage

class Command(BaseCommand):
    help = 'Sincroniza logs recientes con Redis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días a sincronizar (default: 7)'
        )
        parser.add_argument(
            '--client-id',
            type=int,
            help='Sincronizar solo logs de un cliente específico'
        )

    def handle(self, *args, **options):
        days = options['days']
        client_id = options.get('client_id')
        
        # Filtrar logs recientes
        fecha_limite = timezone.now() - timedelta(days=days)
        logs = TarjetaActivityLog.objects.filter(
            timestamp__gte=fecha_limite
        ).select_related('cierre', 'cierre__cliente', 'usuario')
        
        if client_id:
            logs = logs.filter(cierre__cliente_id=client_id)
        
        # Sincronizar con Redis
        synced_count = 0
        for log in logs:
            try:
                ActivityLogStorage.save_to_redis(log)
                synced_count += 1
                
                if synced_count % 100 == 0:
                    self.stdout.write(f"Sincronizados {synced_count} logs...")
                    
            except Exception as e:
                self.stderr.write(f"Error sincronizando log {log.id}: {e}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Sincronización completada: {synced_count} logs')
        )
```

### 5. Mejoras en el Frontend

Archivo: `/frontend/src/components/Gerente/LogsActividad.jsx`

```javascript
// Agregar indicador de fuente de datos
const [dataSource, setDataSource] = useState(null);

// Modificar cargarDatos para mostrar fuente
const cargarDatos = async () => {
  try {
    setLoading(true);
    
    const logsData = await obtenerLogsActividad(filtros);
    
    // Mostrar fuente de datos
    setDataSource(logsData.source);
    
    // ... resto del código
  } catch (err) {
    console.error('Error cargando logs:', err);
  } finally {
    setLoading(false);
  }
};

// Agregar indicador en la UI
<div className="flex items-center justify-between mb-4">
  <div className="flex items-center">
    <Activity className="w-6 h-6 text-blue-500 mr-2" />
    <h3 className="text-lg font-semibold">Actividad Reciente</h3>
    {dataSource && (
      <span className={`ml-2 px-2 py-1 rounded text-xs ${
        dataSource === 'redis' 
          ? 'bg-green-100 text-green-800' 
          : 'bg-blue-100 text-blue-800'
      }`}>
        {dataSource === 'redis' ? 'Tiempo Real' : 'Histórico'}
      </span>
    )}
  </div>
  <button
    onClick={cargarDatos}
    disabled={loading}
    className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded text-sm"
  >
    <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
    Actualizar
  </button>
</div>
```

## Beneficios del Sistema Híbrido

### 1. Rendimiento
- ✅ **Consultas rápidas**: Redis para logs recientes
- ✅ **Escalabilidad**: PostgreSQL para almacenamiento masivo
- ✅ **Baja latencia**: Dashboard en tiempo real

### 2. Confiabilidad
- ✅ **Persistencia**: Todos los logs en PostgreSQL
- ✅ **Fallback**: Si Redis falla, usar PostgreSQL
- ✅ **Sincronización**: Comando para resincronizar

### 3. Flexibilidad
- ✅ **Consultas históricas**: PostgreSQL para auditoría
- ✅ **Tiempo real**: Redis para dashboard
- ✅ **Política configurable**: TTL y límites ajustables

### 4. Mantenimiento
- ✅ **Auto-limpieza**: TTL en Redis
- ✅ **Sincronización**: Comando de gestión
- ✅ **Monitoreo**: Logs de operaciones Redis

## Comandos de Gestión

```bash
# Sincronizar logs recientes
python manage.py sync_logs_redis

# Sincronizar solo un cliente
python manage.py sync_logs_redis --client-id 123

# Sincronizar últimos 3 días
python manage.py sync_logs_redis --days 3

# Limpiar cache Redis
redis-cli -n 2 FLUSHDB
```

Esta implementación te proporciona:
- **Rendimiento óptimo** para consultas frecuentes
- **Persistencia garantizada** en PostgreSQL
- **Flexibilidad** para diferentes tipos de consultas
- **Mantenibilidad** con comandos de gestión
- **Escalabilidad** para crecimiento futuro

¿Te gustaría que implemente alguna parte específica de este sistema?
