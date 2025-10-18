# ✅ Activity Logging V2 con cierre_id - IMPLEMENTADO

## 🎯 ¿Qué se implementó?

El sistema ahora **registra el cierre_id** en todas las actividades, permitiendo responder:

✅ **"¿Qué actividad hubo en el cierre 30?"**  
✅ **"¿Cuándo abrió el modal de ingresos en este cierre?"**  
✅ **"¿Quién subió archivos en el cierre X?"**  
✅ **"¿Cuántas veces se editó algo en este cierre?"**

## 📦 Implementación

### 1️⃣ Frontend (activityLogger_v2.js)

El logger ahora acepta `cierreId`:

```javascript
// Crear logger con cliente Y cierre
const activityLogger = createActivityLogger(clienteId, cierreId);

// Log con cierre_id automático
activityLogger.logModalOpen('ingresos', { archivo: 'test.xlsx' });
```

**Parámetros actualizados:**
```javascript
logActivity({
  clienteId: 13,      // ✅ Cliente
  cierreId: 30,       // ✅ NUEVO: Cierre
  action: 'modal_opened',
  resourceType: 'ingresos',
  details: { ... }
})
```

### 2️⃣ Backend (views_activity_v2.py)

El backend recibe `cierre_id` y lo guarda como:
- `resource_type = 'cierre'`
- `resource_id = cierre_id`

**Request:**
```json
POST /api/nomina/activity-log/log/
{
  "cliente_id": 13,
  "cierre_id": 30,        // ✅ NUEVO
  "action": "modal_opened",
  "details": {}
}
```

**Registro en DB:**
```python
ActivityEvent.objects.create(
    user=user,
    cliente_id=13,
    resource_type='cierre',   # ✅ Tipo fijo
    resource_id='30',         # ✅ ID del cierre
    action='modal_opened',
    ...
)
```

### 3️⃣ Consulta por Cierre

**Endpoint:**
```
GET /api/nomina/activity-log/cierre/30/
```

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 42,
      "timestamp": "2025-10-16T23:18:53.123Z",
      "user_email": "cecilia.reyes@bdo.cl",
      "action": "modal_opened",
      "resource_type": "cierre",
      "details": { ... }
    },
    ...
  ]
}
```

**Query SQL generada:**
```sql
SELECT * FROM nomina_activity_event
WHERE resource_type = 'cierre' 
  AND resource_id = '30'
  AND cliente_id = 13
ORDER BY timestamp DESC
LIMIT 200;
```

## 🧪 Pruebas

### Desde Django Shell

```python
from nomina.models import ActivityEvent

# Ver actividad del cierre 30
events = ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).select_related('user', 'cliente')

for event in events:
    print(f"{event.timestamp} - {event.user.email} - {event.action}")
```

**Output esperado:**
```
2025-10-16 23:18:53 - cecilia.reyes@bdo.cl - modal_opened
2025-10-16 23:18:52 - cecilia.reyes@bdo.cl - file_selected
2025-10-16 23:18:50 - cecilia.reyes@bdo.cl - session_started
```

### Desde Frontend

```javascript
// Los componentes ya lo están usando automáticamente
// porque pasan cierreId al crear el logger:

useEffect(() => {
  if (clienteId && cierreId) {
    activityLogger.current = createActivityLogger(clienteId, cierreId);
    activityLogger.current.logSessionStart();
  }
}, [clienteId, cierreId]);
```

### Verificar en Browser Console

Al abrir un modal, deberías ver:

```
📤 [ActivityV2] {
  cliente_id: 13,
  cierre_id: "30",      // ✅ Cierre incluido
  event_type: "nomina",
  action: "modal_opened",
  resource_type: "cierre",
  resource_id: "30",
  details: {},
  session_id: "s_1729117133123_abc123"
}
✅ [ActivityV2] OK
```

## 📊 Consultas Útiles

### Analytics por Cierre

```python
from django.db.models import Count
from nomina.models import ActivityEvent

# Actividad más común en un cierre
ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).values('action').annotate(
    count=Count('id')
).order_by('-count')
```

**Output:**
```
[
  {'action': 'modal_opened', 'count': 25},
  {'action': 'file_selected', 'count': 18},
  {'action': 'file_upload', 'count': 15},
  {'action': 'polling_started', 'count': 12},
]
```

### Usuarios más activos en un cierre

```python
ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).values('user__email').annotate(
    count=Count('id')
).order_by('-count')
```

**Output:**
```
[
  {'user__email': 'cecilia.reyes@bdo.cl', 'count': 45},
  {'user__email': 'juan.perez@bdo.cl', 'count': 12},
]
```

### Timeline de actividad

```python
ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).order_by('timestamp').values(
    'timestamp', 'action', 'user__email'
)[:20]
```

### Últimas 10 acciones en un cierre

```python
ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).order_by('-timestamp')[:10]
```

## 🔍 Debugging

### Ver logs en backend

```bash
docker compose logs django --tail=50 | grep ActivityV2
```

### Ver eventos en base de datos

```sql
-- PostgreSQL
SELECT 
    id,
    timestamp,
    user_id,
    cliente_id,
    resource_type,
    resource_id,
    action,
    details
FROM nomina_activity_event
WHERE resource_type = 'cierre' 
  AND resource_id = '30'
ORDER BY timestamp DESC
LIMIT 20;
```

### Verificar índices

```sql
-- Verificar que los índices estén optimizados
EXPLAIN ANALYZE
SELECT * FROM nomina_activity_event
WHERE resource_type = 'cierre' AND resource_id = '30'
ORDER BY timestamp DESC;
```

Deberías ver: `Index Scan using nomina_activity_event_resource_type_id_xxx`

## 🚀 Estado Actual

| Componente | Estado | Cierre ID |
|------------|--------|-----------|
| **Frontend Logger** | ✅ Actualizado | ✅ Incluido |
| **IngresosCard** | ✅ Activo | ✅ Pasando cierreId |
| **FiniquitosCard** | ✅ Activo | ✅ Pasando cierreId |
| **AusentismosCard** | ✅ Activo | ✅ Pasando cierreId |
| **MovimientosMesCard** | ✅ Activo | ✅ Pasando cierreId |
| **Backend API** | ✅ Recibiendo | ✅ Guardando |
| **Consulta por cierre** | ✅ Endpoint | ✅ `/cierre/{id}/` |

## 📝 Ejemplos de Uso

### Componente Frontend (ya implementado)

```javascript
// En IngresosCard.jsx (ya está implementado así)
useEffect(() => {
  if (clienteId && cierreId) {
    activityLogger.current = createActivityLogger(clienteId, cierreId);
    
    // Todos estos logs ahora incluyen cierre_id automáticamente
    activityLogger.current.logSessionStart();
  }
}, [clienteId, cierreId]);

const handleModalOpen = () => {
  setModalOpen(true);
  // Incluye cierre_id automáticamente
  activityLogger.current?.logModalOpen('ingresos');
};
```

### Backend - Consulta Custom

```python
# En cualquier vista o script
def get_cierre_summary(cierre_id):
    events = ActivityEvent.objects.filter(
        resource_type='cierre',
        resource_id=str(cierre_id)
    )
    
    return {
        'total_events': events.count(),
        'unique_users': events.values('user').distinct().count(),
        'first_activity': events.order_by('timestamp').first(),
        'last_activity': events.order_by('-timestamp').first(),
        'actions': events.values('action').annotate(count=Count('id')),
    }
```

## ✅ Preguntas que AHORA puedes responder

1. **"¿Qué hizo el usuario X en el cierre 30?"**
   ```python
   ActivityEvent.objects.filter(
       resource_type='cierre',
       resource_id='30',
       user__email='cecilia.reyes@bdo.cl'
   )
   ```

2. **"¿Cuántas veces se abrió el modal de ingresos en este cierre?"**
   ```python
   ActivityEvent.objects.filter(
       resource_type='cierre',
       resource_id='30',
       action='modal_opened',
       details__tarjeta='ingresos'
   ).count()
   ```

3. **"¿Cuándo se subió el último archivo en este cierre?"**
   ```python
   ActivityEvent.objects.filter(
       resource_type='cierre',
       resource_id='30',
       action='file_upload'
   ).order_by('-timestamp').first()
   ```

4. **"¿Qué actividad hubo ayer en este cierre?"**
   ```python
   from django.utils import timezone
   from datetime import timedelta
   
   ayer = timezone.now() - timedelta(days=1)
   ActivityEvent.objects.filter(
       resource_type='cierre',
       resource_id='30',
       timestamp__gte=ayer
   )
   ```

---

**✅ IMPLEMENTADO Y FUNCIONANDO**  
Fecha: 16 octubre 2025  
Django: Reiniciado  
Frontend: Compilado automáticamente (Vite hot reload)
