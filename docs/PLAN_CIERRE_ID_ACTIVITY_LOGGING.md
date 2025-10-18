# 🎯 Plan: Agregar cierre_id a ActivityEvent

## ❌ Problema Actual

El modelo `ActivityEvent` actual NO puede responder:
> "¿Qué actividad hubo en el cierre 30?"

### Modelo Actual
```python
class ActivityEvent(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, ...)
    cliente = models.ForeignKey(Cliente, ...)  # ✅ Tiene cliente
    
    # Pero NO tiene cierre_id ❌
    resource_id = models.CharField(max_length=100)  # Generic string
```

### Frontend Actual
```javascript
// src/utils/activityLogger_v2.js
export async function logActivity({
  clienteId,        // ✅ Enviamos cliente
  eventType = 'nomina',
  action,
  resourceType = 'general',
  resourceId = '',   // ❌ Este es genérico, no específicamente cierre_id
  details = {},
})
```

## ✅ Solución: Agregar cierre_id

### Opción 1: Usar resource_id como cierre_id (RÁPIDO ⚡)

**Ventaja:** No requiere migración de base de datos
**Desventaja:** No es semánticamente claro

```python
# Backend - Guardar cierre_id en resource_id
ActivityEvent.log(
    resource_type='cierre',
    resource_id=str(cierre_id)  # ✅ Usar resource_id para cierre
)

# Consulta
events = ActivityEvent.objects.filter(
    cliente_id=cliente_id,
    resource_type='cierre',
    resource_id=str(cierre_id)
)
```

```javascript
// Frontend - Pasar cierre_id como resourceId
logActivity({
  clienteId: clienteId,
  resourceType: 'cierre',
  resourceId: cierreId,  // ✅ Pasar cierre como resourceId
  action: 'modal_opened'
})
```

### Opción 2: Agregar campo cierre_id (CORRECTO 🎯)

**Ventaja:** Semántica clara, mejor indexación, más consultas eficientes
**Desventaja:** Requiere migración de base de datos

```python
# models.py - Agregar nuevo campo
class ActivityEvent(models.Model):
    # ... campos existentes ...
    
    # ✅ NUEVO CAMPO
    cierre = models.ForeignKey(
        'CierreNomina', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        db_index=True,
        help_text="Cierre de nómina relacionado"
    )
```

```python
# Migración necesaria
python manage.py makemigrations nomina
python manage.py migrate
```

```python
# Backend - Usar cierre directamente
ActivityEvent.log(
    cierre=cierre,  # ✅ ForeignKey directo
    resource_type='ingresos',
    action='modal_opened'
)

# Consulta optimizada
events = ActivityEvent.objects.filter(
    cierre_id=cierre_id
).select_related('user', 'cliente', 'cierre')
```

```javascript
// Frontend - Pasar cierreId explícitamente
logActivity({
  clienteId: clienteId,
  cierreId: cierreId,  // ✅ Campo explícito
  resourceType: 'ingresos',
  action: 'modal_opened'
})
```

## 📊 Comparación

| Aspecto | Opción 1 (resource_id) | Opción 2 (cierre FK) |
|---------|------------------------|----------------------|
| **Velocidad** | ⚡ Inmediato | 🐢 Requiere migración |
| **Claridad** | 😕 Confuso | ✅ Muy claro |
| **Consultas** | 🔍 Joins manuales | 🚀 Optimizado con select_related |
| **Validación** | ❌ Ninguna | ✅ Django valida FK |
| **Reportes** | 😰 Complejos | 😊 Simples |
| **Indexación** | ⚠️ CharField index | ✅ Integer FK index |

## 🎯 Recomendación

**Opción 1 (resource_id) AHORA** → Funciona inmediatamente sin migración

**Opción 2 (cierre FK) DESPUÉS** → Migrar cuando tengas tiempo

## 🚀 Implementación Rápida (Opción 1)

### 1️⃣ Frontend - Actualizar activityLogger_v2.js

```javascript
export async function logActivity({
  clienteId,
  cierreId = '',     // ✅ NUEVO parámetro
  eventType = 'nomina',
  action,
  resourceType = 'general',
  resourceId = '',
  details = {},
  sessionId = ''
}) {
  const payload = {
    cliente_id: clienteId,
    cierre_id: cierreId || resourceId,  // ✅ Usar cierreId si está disponible
    event_type: eventType,
    action: action,
    resource_type: resourceType,
    resource_id: cierreId || resourceId,  // ✅ Duplicar en resource_id
    details: details,
    session_id: sessionId || generateSessionId(),
  };
}
```

### 2️⃣ Backend - Actualizar views_activity_v2.py

```python
@api_view(['POST'])
def log_activity(request):
    cierre_id = request.data.get('cierre_id')  # ✅ Leer cierre_id
    
    event = ActivityEvent.log(
        user=request.user,
        cliente=cliente,
        resource_type='cierre',           # ✅ Tipo = cierre
        resource_id=str(cierre_id),       # ✅ ID del cierre
        event_type=request.data.get('event_type'),
        action=request.data.get('action'),
        details=request.data.get('details', {}),
    )
```

### 3️⃣ Backend - Nueva vista para consultar por cierre

```python
@api_view(['GET'])
def get_cierre_activities(request, cierre_id):
    """
    GET /api/nomina/activity-log/cierre/{cierre_id}/
    """
    events = ActivityEvent.objects.filter(
        resource_type='cierre',
        resource_id=str(cierre_id)
    ).select_related('user', 'cliente').order_by('-timestamp')[:100]
    
    # Serializar...
```

## 🧪 Prueba

```bash
# Consulta SQL resultante
SELECT * FROM nomina_activity_event
WHERE resource_type = 'cierre' 
  AND resource_id = '30'
ORDER BY timestamp DESC;
```

```python
# Django ORM
from nomina.models import ActivityEvent

# Ver actividad del cierre 30
events = ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
)

for event in events:
    print(f"{event.timestamp} - {event.user.email} - {event.action}")
```

---

**✅ Con esta implementación puedes responder:**
- "¿Qué hizo el usuario X en el cierre 30?"
- "¿Cuántas veces se abrió el modal de ingresos en el cierre 30?"
- "¿Cuándo se subió el último archivo en el cierre 30?"
- "¿Qué actividad hubo en el cierre 30 el día de ayer?"
