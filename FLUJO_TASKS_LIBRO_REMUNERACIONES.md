# 🔄 Análisis del Flujo de Tasks - Libro de Remuneraciones

## 📊 Estado Actual

### **Tasks Existentes (Duplicadas)**

| Task | Versión | Estado | Usado en |
|------|---------|--------|----------|
| `analizar_headers_libro_remuneraciones` | Sin logging | ⚠️ Legacy | No usado |
| `analizar_headers_libro_remuneraciones_con_logging` | Con logging | ✅ Activo | views_libro_remuneraciones.py |
| `clasificar_headers_libro_remuneraciones_task` | Sin logging | ⚠️ Legacy | No usado |
| `clasificar_headers_libro_remuneraciones_con_logging` | Con logging | ✅ Activo | views_libro_remuneraciones.py |

### **Flujo Actual en `views_libro_remuneraciones.py`**

```python
chain(
    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, None),
    clasificar_headers_libro_remuneraciones_con_logging.s(),
).apply_async()
```

---

## ✅ Correcciones Aplicadas

### 1. **`analizar_headers_libro_remuneraciones_con_logging`**

**Problema**: Variable `cierre` no definida al inicio

**Solución Aplicada**:
```python
# ANTES (ERROR)
cierre_id = libro.cierre.id
cliente = libro.cierre.cliente

# DESPUÉS (CORRECTO)
cierre = libro.cierre  # ✅ Definir cierre primero
cliente = cierre.cliente
```

**Logs Generados**:
- `analisis_headers_iniciado` (event_type='process')
- `analisis_headers_exitoso` (event_type='process')
- `analisis_headers_error` (event_type='error')

**Details Limpiados**:
```python
# ANTES
details={
    'cierre_id': cierre_id,  # ❌ Redundante
    'libro_id': libro_id,
    ...
}

# DESPUÉS
details={
    'libro_id': libro_id,  # ✅ cierre_id ya está en campo normalizado
    ...
}
```

---

### 2. **`clasificar_headers_libro_remuneraciones_con_logging`**

**Problema 1**: Variable `cierre` definida DESPUÉS de usarla

**Solución Aplicada**:
```python
# ANTES (ERROR)
try:
    libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
    cierre_id = libro.cierre.id
    cliente = libro.cierre.cliente
    # ... uso de ActivityEvent.log con cierre=cierre ...
    cierre = libro.cierre  # ❌ Definido aquí (tarde)

# DESPUÉS (CORRECTO)
try:
    libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
    cierre = libro.cierre  # ✅ Definir al inicio
    cliente = cierre.cliente
```

**Logs Generados**:
- `clasificacion_headers_iniciada` (event_type='process')
- `clasificacion_headers_exitosa` (event_type='process')
- `clasificacion_headers_error` (event_type='error')

**Details Limpiados**:
- Removido `'cierre_id': cierre_id` (redundante)

---

## 🔄 Flujo Completo Actualizado

### **Fase 1: Upload (Frontend → Django)**

```
Usuario sube archivo
    ↓
views_libro_remuneraciones.subir()
    ↓
1. ActivityEvent: upload_iniciado
2. Validar archivo
3. ActivityEvent: archivo_validado (o validacion_fallida)
4. Crear LibroRemuneracionesUpload
5. ActivityEvent: upload_completado
6. ActivityEvent: procesamiento_iniciado
7. Lanzar Celery chain
```

### **Fase 2: Análisis de Headers (Celery)**

```
analizar_headers_libro_remuneraciones_con_logging(libro_id, None)
    ↓
1. ActivityEvent: analisis_headers_iniciado
    cierre=libro.cierre ✅
    user=sistema_user ✅
    event_type='process' ✅
2. Actualizar libro.estado = 'analizando_hdrs'
3. Ejecutar obtener_headers_libro_remuneraciones()
4. Guardar libro.header_json = headers
5. Actualizar libro.estado = 'hdrs_analizados'
6. ActivityEvent: analisis_headers_exitoso (o error)
7. Return {"libro_id": libro_id, "upload_log_id": None, "headers": headers}
```

### **Fase 3: Clasificación de Headers (Celery)**

```
clasificar_headers_libro_remuneraciones_con_logging(result)
    ↓
1. Extraer libro_id del result
2. ActivityEvent: clasificacion_headers_iniciada
    cierre=libro.cierre ✅
    user=sistema_user ✅
    event_type='process' ✅
3. Actualizar libro.estado = 'clasif_en_proceso'
4. Ejecutar clasificar_headers_libro_remuneraciones()
5. Guardar libro.header_json = {
       "headers_clasificados": [...],
       "headers_sin_clasificar": [...]
   }
6. Determinar estado final:
   - Si headers_sin_clasificar: 'clasif_pendiente'
   - Si no: 'clasificado'
7. ActivityEvent: clasificacion_headers_exitosa (o error)
8. Return result actualizado
```

---

## 📝 Variables Normalizadas

### **En Tasks (Celery)**

```python
# ✅ Patrón estándar para todas las tasks
from django.contrib.auth import get_user_model
User = get_user_model()

libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
cierre = libro.cierre              # ✅ Objeto completo
cliente = cierre.cliente            # ✅ Objeto completo
sistema_user = User.objects.filter(is_staff=True).first() or User.objects.first()

# Logging
ActivityEvent.log(
    user=sistema_user,  # ✅ Usuario del sistema
    cliente=cliente,    # ✅ Cliente normalizado
    cierre=cierre,      # ✅ Cierre normalizado (NO cierre_id)
    event_type='process',
    action='...',
    resource_type='libro_remuneraciones',
    resource_id=str(libro_id),
    details={
        'libro_id': libro_id,  # ✅ NO incluir 'cierre_id'
        ...
    }
    # NO request (Celery no tiene HTTP request)
)
```

### **En Views (Django)**

```python
# ✅ Patrón estándar para views
ActivityEvent.log(
    user=request.user,     # ✅ Usuario actual del request
    cliente=cliente,       # ✅ Cliente normalizado
    cierre=cierre,         # ✅ Cierre normalizado
    event_type='upload',
    action='...',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'libro_id': libro.id,  # ✅ NO incluir 'cierre_id'
        'archivo': archivo.name,
        ...
    },
    request=request  # ✅ Para capturar IP y user agent
)
```

---

## ⚠️ Tasks Legacy (Marcar para Deprecación)

Estas tasks NO se usan actualmente pero existen en el código:

1. `analizar_headers_libro_remuneraciones(libro_id)` - Línea 336
2. `clasificar_headers_libro_remuneraciones_task(result)` - Línea 357

**Recomendación**: Agregar decorator `@deprecated` o comentar con TODO.

---

## 🧪 Testing del Flujo

### **Test 1: Upload exitoso**
```python
# 1. Subir archivo libro.xlsx
# 2. Verificar eventos creados:
events = ActivityEvent.objects.filter(cierre=cierre_id).order_by('timestamp')

assert events[0].action == 'upload_iniciado'
assert events[1].action == 'archivo_validado'
assert events[2].action == 'upload_completado'
assert events[3].action == 'procesamiento_iniciado'

# 3. Esperar a que Celery complete
time.sleep(5)

# 4. Verificar eventos de Celery
assert events.filter(action='analisis_headers_iniciado').exists()
assert events.filter(action='analisis_headers_exitoso').exists()
assert events.filter(action='clasificacion_headers_iniciada').exists()
assert events.filter(action='clasificacion_headers_exitosa').exists()

# 5. Verificar que TODOS tienen cierre normalizado
for event in events:
    assert event.cierre_id == cierre_id
    assert event.cierre is not None
```

### **Test 2: Error en análisis**
```python
# 1. Subir archivo corrupto
# 2. Verificar evento de error:
error_event = ActivityEvent.objects.filter(
    cierre=cierre_id,
    event_type='error',
    action='analisis_headers_error'
).first()

assert error_event is not None
assert error_event.cierre == cierre
assert 'error' in error_event.details
```

---

## ✅ Estado de Correcciones

- [x] `analizar_headers_libro_remuneraciones_con_logging`: Variable `cierre` definida correctamente
- [x] `clasificar_headers_libro_remuneraciones_con_logging`: Variable `cierre` definida al inicio
- [x] Removido `'cierre_id'` redundante de todos los `details`
- [x] Cambiado `event_type='process'` a `'error'` en logs de error
- [x] Sintaxis Python validada
- [x] Flujo documentado

---

## 🔜 Próximos Pasos

1. **Reiniciar Celery** para cargar cambios
2. **Probar flujo completo** con upload real
3. **Verificar timeline** en base de datos
4. **Marcar tasks legacy** como deprecated
5. **Implementar endpoint API** para timeline

---

**Última actualización**: 17 de octubre de 2025
**Archivos modificados**: `backend/nomina/tasks.py`
**Cambios**: 6 correcciones en variables y logging
