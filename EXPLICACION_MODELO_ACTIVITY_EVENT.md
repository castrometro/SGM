# 📊 Modelo ActivityEvent - Explicación Completa

**Fecha**: 17 de octubre de 2025  
**Sistema**: SGM Contabilidad & Nómina  
**Versión**: V2 (Normalizado con ForeignKey a CierreNomina)

---

## 🎯 ¿Qué es ActivityEvent?

`ActivityEvent` es el **sistema unificado de logging de actividades** para todo el sistema SGM. Registra **cada acción importante** que un usuario realiza en el sistema, permitiendo:

1. **Auditoría completa**: ¿Quién hizo qué y cuándo?
2. **Timeline de cierres**: Ver toda la historia de un cierre
3. **Debugging**: Rastrear problemas en procesamiento
4. **Análisis de uso**: Entender patrones de usuarios

---

## 🏗️ Estructura del Modelo

### **Ubicación**: `/backend/nomina/models.py` (líneas 1806-1938)

```python
class ActivityEvent(models.Model):
    # === QUIÉN Y DÓNDE ===
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    
    # === RELACIÓN NORMALIZADA (Nuevo en V2) ===
    cierre = models.ForeignKey('CierreNomina', 
                                on_delete=models.CASCADE, 
                                null=True, blank=True, 
                                db_index=True)
    
    # === QUÉ PASÓ ===
    event_type = models.CharField(max_length=50, db_index=True)
    action = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True)
    
    # === DETALLES ADICIONALES ===
    details = models.JSONField(default=dict, blank=True)
    
    # === METADATOS DE SESIÓN ===
    session_id = models.CharField(max_length=255, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
```

---

## 📝 Campos Explicados

| Campo | Tipo | Propósito | Ejemplo |
|-------|------|-----------|---------|
| **timestamp** | DateTime | Cuándo pasó | `2025-10-17 14:23:45` |
| **user** | FK(User) | Quién lo hizo | `User(admin)` |
| **cliente** | FK(Cliente) | Para qué cliente | `Cliente(ABC LTDA)` |
| **cierre** | FK(CierreNomina) | **[V2]** Qué cierre | `CierreNomina(30)` ✅ |
| **event_type** | String(50) | Categoría del evento | `upload`, `process`, `delete`, `view` |
| **action** | String(255) | Acción específica | `archivo_validado`, `procesamiento_iniciado` |
| **resource_type** | String(50) | Tipo de recurso | `libro_remuneraciones`, `movimientos_mes` |
| **resource_id** | String(255) | ID del recurso | `61`, `archivo_2025.xlsx` |
| **details** | JSON | Info adicional | `{"libro_id": 61, "filas": 150}` |
| **session_id** | String(255) | Agrupar eventos | UUID de sesión de upload |
| **ip_address** | IP | Desde dónde | `172.17.11.18` |
| **user_agent** | Text | Con qué navegador | `Mozilla/5.0...` |

---

## 🔑 El Campo Clave: `cierre` (Normalizado)

### **Problema Anterior (V1)**:
```json
{
  "details": {
    "cierre_id": 30,  // ❌ Dentro del JSON
    "archivo": "libro.xlsx",
    "filas": 150
  }
}
```

**Problemas**:
- ❌ No se puede hacer `WHERE cierre_id = 30` eficientemente
- ❌ Queries lentos (full table scan)
- ❌ No hay integridad referencial (si eliminas cierre, datos quedan huérfanos)
- ❌ No puedes hacer `.filter(cierre=cierre)` directamente

### **Solución V2 (Normalizado)**:
```python
ActivityEvent.objects.create(
    cierre=cierre,  # ✅ ForeignKey directo
    details={
        "archivo": "libro.xlsx",  # Solo info contextual
        "filas": 150
    }
)
```

**Beneficios**:
- ✅ Query rápido: `ActivityEvent.objects.filter(cierre=cierre)`
- ✅ Index en base de datos: `(cierre_id, timestamp)`
- ✅ Integridad: Si eliminas cierre, elimina eventos automáticamente
- ✅ ORM feliz: `cierre.activityevent_set.all()` funciona directo

---

## 🎬 Cómo Se USA (El Método `.log()`)

### **Firma del método**:

```python
@staticmethod
def log(user, cliente, event_type, action, 
        resource_type='general', resource_id='', 
        details=None, session_id='', 
        request=None, cierre=None):
    """
    Registra un evento de actividad.
    
    Args:
        user: Usuario (request.user o User.objects.get())
        cliente: Cliente (cierre.cliente)
        cierre: CierreNomina (NORMALIZADO) ✅
        event_type: Categoría (upload/process/delete/view)
        action: Acción específica (archivo_validado/procesamiento_iniciado)
        resource_type: Tipo (libro_remuneraciones/movimientos_mes)
        resource_id: ID del recurso (str(libro.id))
        details: Dict con info adicional (NO incluir cierre_id aquí)
        session_id: UUID de sesión (para agrupar)
        request: HttpRequest (para extraer IP y user_agent)
    
    Returns:
        ActivityEvent: El evento creado
    """
```

---

## 📚 Ejemplos de Uso CORRECTOS

### **1. Upload Iniciado**

```python
# En views_libro_remuneraciones.py - create()
ActivityEvent.log(
    user=request.user,
    cliente=cierre.cliente,
    cierre=cierre,  # ✅ Normalizado
    event_type='upload',
    action='upload_iniciado',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'archivo': archivo.name,
        'tamano': archivo.size
    },
    session_id=session_id,
    request=request
)
```

### **2. Validación Exitosa**

```python
ActivityEvent.log(
    user=request.user,
    cliente=cierre.cliente,
    cierre=cierre,  # ✅
    event_type='validation',
    action='archivo_validado',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'columnas': list(df.columns),
        'filas': len(df)
    },
    session_id=session_id,
    request=request
)
```

### **3. Procesamiento con Celery (Sin Request)**

```python
# En tasks.py - analizar_headers_libro_remuneraciones_con_logging
sistema_user = User.objects.filter(is_staff=True).first()

ActivityEvent.log(
    user=sistema_user,  # ⚠️ Usuario sistema (no hay request.user)
    cliente=libro.cierre.cliente,
    cierre=libro.cierre,  # ✅
    event_type='process',
    action='analisis_headers_iniciado',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'task_id': self.request.id,
        'archivo': archivo_path
    },
    request=None  # ⚠️ No request en Celery
)
```

### **4. Eliminación (perform_destroy)**

```python
# En views_libro_remuneraciones.py - perform_destroy()
ActivityEvent.log(
    user=request.user,
    cliente=instance.cierre.cliente,
    cierre=instance.cierre,  # ✅
    event_type='delete',
    action='archivo_eliminado',
    resource_type='libro_remuneraciones',
    resource_id=str(instance.id),
    details={
        'libro_id': instance.id,
        'archivo': archivo_nombre,
        'motivo': motivo,
        'estado_previo': instance.estado
    },
    request=request
)
```

---

## 🔍 Queries Comunes

### **1. Timeline de un Cierre**

```python
# Obtener todos los eventos de un cierre específico
eventos = ActivityEvent.objects.filter(
    cierre_id=30
).order_by('timestamp')

# Resultado:
# [upload_iniciado → archivo_validado → upload_completado → 
#  procesamiento_iniciado → analisis_headers_iniciado → ...]
```

### **2. Eventos de un Usuario**

```python
# ¿Qué ha hecho este usuario hoy?
from django.utils import timezone
from datetime import timedelta

hoy = timezone.now().date()
eventos = ActivityEvent.objects.filter(
    user=user,
    timestamp__date=hoy
).order_by('-timestamp')
```

### **3. Últimos Uploads**

```python
# Últimos 10 uploads en el sistema
uploads = ActivityEvent.objects.filter(
    event_type='upload',
    action='upload_iniciado'
).order_by('-timestamp')[:10]
```

### **4. Eventos por Sesión**

```python
# Todos los eventos de una sesión de upload
eventos = ActivityEvent.objects.filter(
    session_id='uuid-1234-5678'
).order_by('timestamp')
```

---

## ⚡ Índices y Performance

El modelo tiene **7 índices** para queries rápidos:

```python
indexes = [
    models.Index(fields=['timestamp']),           # Por fecha
    models.Index(fields=['user', 'timestamp']),   # Por usuario + fecha
    models.Index(fields=['cliente', 'timestamp']), # Por cliente + fecha
    models.Index(fields=['cierre', 'timestamp']),  # ✅ Por cierre + fecha (NUEVO)
    models.Index(fields=['event_type', 'timestamp']), # Por tipo + fecha
    models.Index(fields=['resource_type', 'resource_id']), # Por recurso
    models.Index(fields=['session_id']),          # Por sesión
]
```

**Query eficiente** gracias al índice `(cierre, timestamp)`:
```python
# ✅ Usa el índice compuesto
ActivityEvent.objects.filter(cierre=cierre).order_by('timestamp')

# Execution plan:
# Index Scan using nomina_activity_event_cierre_timestamp_idx
# (cost=0.42..10.53 rows=5 width=534)
```

---

## 🚫 Qué NO Hacer

### ❌ **1. NO guardar cierre_id en details**

```python
# ❌ MAL
ActivityEvent.log(
    cierre=cierre,
    details={
        'cierre_id': cierre.id,  # ❌ Duplicado innecesario
        'archivo': 'libro.xlsx'
    }
)

# ✅ BIEN
ActivityEvent.log(
    cierre=cierre,  # Ya está normalizado
    details={
        'archivo': 'libro.xlsx'  # Solo info contextual
    }
)
```

### ❌ **2. NO olvidar el parámetro cierre**

```python
# ❌ MAL
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    # cierre=cierre,  ❌ FALTA
    event_type='upload',
    action='upload_iniciado'
)

# ✅ BIEN
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,  # ✅ Siempre incluir
    event_type='upload',
    action='upload_iniciado'
)
```

### ❌ **3. NO llamar desde el frontend**

```jsx
// ❌ MAL - El frontend NO debe hacer logging directo
await activityLogger.log({
  action: 'delete_completed',
  resourceType: 'libro_remuneraciones'
});

// ✅ BIEN - El backend maneja el logging automáticamente
await onEliminarArchivo(); // perform_destroy hace el logging
```

---

## 🔄 Flujo Completo de un Upload

```
1. Usuario sube archivo
   ↓
2. Frontend: POST /api/nomina/libros-remuneraciones/
   ↓
3. Backend ViewSet.create()
   └─> ActivityEvent.log(event_type='upload', action='upload_iniciado')
   ↓
4. Validación de archivo
   └─> ActivityEvent.log(event_type='validation', action='archivo_validado')
   ↓
5. Guardar archivo
   └─> ActivityEvent.log(event_type='upload', action='upload_completado')
   ↓
6. Lanzar tarea Celery
   └─> ActivityEvent.log(event_type='process', action='procesamiento_iniciado')
   ↓
7. Celery Task: analizar_headers
   └─> ActivityEvent.log(event_type='process', action='analisis_headers_iniciado')
   └─> Procesa archivo...
   └─> ActivityEvent.log(event_type='process', action='analisis_headers_exitoso')
   ↓
8. Celery Task: clasificar_headers
   └─> ActivityEvent.log(event_type='process', action='clasificacion_headers_iniciada')
   └─> Clasifica columnas...
   └─> ActivityEvent.log(event_type='process', action='clasificacion_headers_exitosa')
   ↓
9. Usuario ve resultado en frontend
```

**Resultado**: 8 eventos registrados para un solo upload ✅

---

## 🛠️ Métodos Auxiliares

### **1. cleanup_old_events()**

```python
# Limpiar eventos mayores a 90 días
deleted = ActivityEvent.cleanup_old_events(days=90)
print(f"Eliminados {deleted} eventos antiguos")

# Puedes ejecutar esto en Celery periódicamente
@periodic_task(run_every=timedelta(days=7))
def limpiar_logs_antiguos():
    ActivityEvent.cleanup_old_events(days=90)
```

### **2. get_related_events()**

```python
# Buscar eventos relacionados en ±5 minutos
evento = ActivityEvent.objects.get(id=100)
relacionados = evento.get_related_events(time_window_minutes=5)

# Útil para debugging: "¿Qué más pasó en ese momento?"
```

---

## 📊 Reportes y Analytics

### **Eventos por tipo**

```python
from django.db.models import Count

resumen = ActivityEvent.objects.values('event_type').annotate(
    total=Count('id')
).order_by('-total')

# Resultado:
# [{'event_type': 'upload', 'total': 1523},
#  {'event_type': 'process', 'total': 845},
#  {'event_type': 'validation', 'total': 712}]
```

### **Actividad por usuario**

```python
actividad_usuarios = ActivityEvent.objects.values(
    'user__username'
).annotate(
    uploads=Count('id', filter=models.Q(event_type='upload')),
    procesos=Count('id', filter=models.Q(event_type='process')),
    total=Count('id')
).order_by('-total')[:10]
```

### **Timeline JSON para frontend**

```python
def get_timeline_data(cierre_id):
    eventos = ActivityEvent.objects.filter(
        cierre_id=cierre_id
    ).select_related('user').order_by('timestamp')
    
    return [{
        'id': e.id,
        'timestamp': e.timestamp.isoformat(),
        'user': e.user.username,
        'event_type': e.event_type,
        'action': e.action,
        'resource_type': e.resource_type,
        'details': e.details
    } for e in eventos]
```

---

## 🎯 Resumen: Cómo Debería Funcionar

### **Principios del Diseño**

1. **Single Source of Truth**: Solo el backend hace logging
2. **Normalización**: `cierre` es ForeignKey, no JSON
3. **Consistencia**: Todos los eventos siguen el mismo patrón
4. **Performance**: Índices optimizados para queries comunes
5. **Auditoría**: Quién, qué, cuándo, dónde - todo registrado

### **Checklist para Nuevos Eventos**

```python
# ✅ Checklist al agregar logging nuevo

ActivityEvent.log(
    user=request.user,          # ✅ Usuario correcto (sistema_user en Celery)
    cliente=cierre.cliente,     # ✅ Cliente del cierre
    cierre=cierre,              # ✅ Normalizado (NO en details)
    event_type='upload',        # ✅ Categoría clara
    action='upload_iniciado',   # ✅ Acción específica
    resource_type='libro_...',  # ✅ Tipo de recurso
    resource_id=str(libro.id),  # ✅ ID como string
    details={                   # ✅ Solo info contextual
        'archivo': archivo.name,
        'tamano': archivo.size
        # NO 'cierre_id' aquí ❌
    },
    session_id=session_id,      # ✅ UUID de sesión
    request=request             # ✅ Para IP y user_agent
)
```

---

## 🚀 Estado Actual

- ✅ Modelo migrado (migration 0251)
- ✅ 24 llamadas actualizadas con `cierre=`
- ✅ Frontend limpio (sin logging duplicado en LibroRemuneracionesCard)
- ✅ Tests pasando (test_activity_event_delete.py)
- ⏳ **Pendiente**: Probar delete end-to-end

---

**¿Dudas?** Este modelo es la **columna vertebral** del sistema de auditoría. Todos los eventos importantes pasan por aquí. 🎯
