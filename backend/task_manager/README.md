# Sistema de Gestión Global de Tareas Celery

## Descripción

Este sistema permite monitorear y gestionar todas las tareas de Celery de forma centralizada a través de:

- **Flower API**: Para obtener información en tiempo real
- **Base de datos local**: Para historial y tracking personalizado
- **API REST**: Para comunicación con el frontend React

## Instalación y Configuración

### 1. Base de datos ya configurada

Las migraciones ya están aplicadas. Las tablas creadas son:
- `task_manager_taskexecution`: Tracking de ejecuciones
- `task_manager_tasknotification`: Notificaciones
- `task_manager_tasktemplate`: Plantillas reutilizables

### 2. URLs disponibles

- `GET /api/tasks/executions/` - Lista de ejecuciones
- `GET /api/tasks/executions/{id}/` - Detalle de ejecución
- `GET /api/tasks/workers/` - Lista de workers activos
- `GET /api/tasks/flower-info/` - Info del Flower
- `POST /api/tasks/cancel/{task_id}/` - Cancelar tarea
- `GET /api/tasks/user-tasks/` - Tareas del usuario actual

## Ejemplos de Uso

### 1. Decorador para tareas existentes

```python
# En nomina/tasks.py
from celery import shared_task
from task_manager.utils import track_task

@shared_task
@track_task('nomina.consolidar', 'nomina', 'Consolidar nómina del período')
def consolidar_nomina(periodo_id, user_id):
    # Tu lógica existente
    return {'success': True, 'periodo_id': periodo_id}

@shared_task
@track_task('nomina.generar_reporte', 'nomina', 'Generar reporte de nómina')
def generar_reporte_nomina(parametros, user_id):
    # Tu lógica existente
    return {'reporte_url': '/path/to/report.pdf'}
```

### 2. Tracking manual dentro de tareas

```python
# En contabilidad/tasks.py
from celery import shared_task
from task_manager.utils import start_task_tracking, update_task_progress, finish_task

@shared_task(bind=True)
def procesar_contabilidad(self, datos, user_id):
    from django.contrib.auth.models import User
    
    user = User.objects.get(id=user_id)
    
    # Iniciar tracking
    task_execution = start_task_tracking(
        task_id=self.request.id,
        task_name='contabilidad.procesar',
        module='contabilidad',
        user=user,
        description='Procesando datos de contabilidad',
        parameters={'datos_count': len(datos)}
    )
    
    try:
        total_items = len(datos)
        
        for i, item in enumerate(datos):
            # Procesar item
            procesar_item(item)
            
            # Actualizar progreso
            progress = int((i + 1) / total_items * 100)
            update_task_progress(
                task_execution.id, 
                progress, 
                f"Procesando {i+1}/{total_items}"
            )
        
        # Finalizar con éxito
        result = {'procesados': total_items, 'errores': 0}
        finish_task(task_execution.id, success=True, result=result)
        
        return result
        
    except Exception as e:
        # Finalizar con error
        finish_task(task_execution.id, success=False, error_message=str(e))
        raise
```

### 3. Crear plantillas de tareas comunes

```python
# En tu management command o vista
from task_manager.utils import create_task_template

# Crear plantillas para tareas comunes
create_task_template(
    name='consolidacion_nomina',
    task_name='nomina.consolidar',
    module='nomina',
    description='Consolidación mensual de nómina',
    default_parameters={'notificar': True},
    estimated_duration=300,  # 5 minutos
    notification_settings={
        'notify_on_start': True,
        'notify_on_complete': True,
        'notify_on_error': True
    }
)

create_task_template(
    name='backup_contabilidad',
    task_name='contabilidad.backup',
    module='contabilidad',
    description='Backup de datos contables',
    estimated_duration=600,  # 10 minutos
)
```

### 4. Consultar tareas desde vistas Django

```python
# En tus views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from task_manager.utils import get_user_tasks, get_module_stats

@api_view(['GET'])
def mis_tareas_nomina(request):
    # Obtener tareas del usuario para el módulo de nómina
    user_tasks = get_user_tasks(
        user=request.user,
        module='nomina',
        limit=20
    )
    return Response(user_tasks)

@api_view(['GET'])
def estadisticas_modulo(request, modulo):
    # Obtener estadísticas del módulo
    stats = get_module_stats(modulo, days=30)
    return Response(stats)
```

### 5. Integración con React Frontend

```javascript
// En tu componente React
import { useState, useEffect } from 'react';

function TaskMonitor({ userId }) {
    const [tasks, setTasks] = useState([]);
    const [workers, setWorkers] = useState([]);
    
    useEffect(() => {
        // Polling cada 5 segundos para tareas del usuario
        const interval = setInterval(() => {
            fetch('/api/tasks/executions/?user=' + userId)
                .then(res => res.json())
                .then(data => setTasks(data.results));
                
            fetch('/api/tasks/workers/')
                .then(res => res.json())
                .then(data => setWorkers(data));
        }, 5000);
        
        return () => clearInterval(interval);
    }, [userId]);
    
    const cancelTask = (taskId) => {
        fetch(`/api/tasks/cancel/${taskId}/`, { method: 'POST' })
            .then(() => {
                // Actualizar lista
                setTasks(tasks.filter(t => t.task_id !== taskId));
            });
    };
    
    return (
        <div>
            <h3>Mis Tareas</h3>
            {tasks.map(task => (
                <div key={task.id} className="task-item">
                    <span>{task.task_name}</span>
                    <span className={`status-${task.status.toLowerCase()}`}>
                        {task.status}
                    </span>
                    {task.progress > 0 && (
                        <div className="progress-bar">
                            <div 
                                className="progress-fill" 
                                style={{width: `${task.progress}%`}}
                            />
                        </div>
                    )}
                    {task.status === 'STARTED' && (
                        <button onClick={() => cancelTask(task.task_id)}>
                            Cancelar
                        </button>
                    )}
                </div>
            ))}
            
            <h3>Workers Activos: {workers.length}</h3>
        </div>
    );
}
```

### 6. Cancelar tareas masivamente

```python
# En tus views o management commands
from task_manager.utils import cancel_user_tasks

# Cancelar todas las tareas pendientes de un usuario en nómina
result = cancel_user_tasks(
    user=request.user,
    module='nomina'
)
print(f"Canceladas: {result['cancelled']}, Fallidas: {result['failed']}")

# Cancelar tareas específicas
result = cancel_user_tasks(
    user=request.user,
    task_name='nomina.consolidar'
)
```

## Endpoints de la API

### GET `/api/tasks/executions/`
Parámetros de query:
- `user`: ID del usuario
- `task_module`: Filtrar por módulo
- `status`: Filtrar por estado
- `ordering`: Ordenar por campo (`-created_at` por defecto)

### GET `/api/tasks/workers/`
Lista workers activos con información de Flower

### GET `/api/tasks/flower-info/`
Información general del sistema Flower

### POST `/api/tasks/cancel/{task_id}/`
Cancela una tarea específica

### GET `/api/tasks/user-tasks/`
Tareas del usuario autenticado (requiere autenticación)

## Estados de Tareas

- **PENDING**: En cola, esperando worker
- **STARTED**: En ejecución
- **SUCCESS**: Completada exitosamente
- **FAILURE**: Falló con error
- **REVOKED**: Cancelada/revocada

## Notificaciones

El sistema soporta notificaciones configurables por plantilla:
- Al iniciar
- Al completar
- En caso de error
- Por progreso (cada X%)

## Integración con Módulos Existentes

Para integrar en tus módulos existentes:

1. **Importa las utilidades**: `from task_manager.utils import track_task`
2. **Agrega el decorador**: `@track_task('nombre.tarea', 'modulo')`
3. **Usa en el frontend**: Las URLs de la API están disponibles
4. **Configura plantillas**: Para tareas recurrentes

## Flower Dashboard

Acceso directo a Flower: `http://localhost:5555`
- Monitoring en tiempo real
- Estadísticas de workers
- Cola de tareas
- Historial detallado
