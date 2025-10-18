# ✅ Fix: Eliminación de Logging Duplicado en Frontend

**Fecha**: 17 de octubre de 2025  
**Cambio**: Eliminar llamadas a `activityLogger.log()` para operaciones CRUD

---

## 🎯 Problema Identificado

El sistema tenía **logging duplicado**:

1. **Frontend** → `activityLogger.log()` → Endpoint legacy `/api/nomina/activity-log/log/`
   - ❌ No registra `cierre` (queda NULL)
   - ❌ `action` es un dict serializado
   - ❌ `event_type` genérico ('nomina')

2. **Backend** → `ActivityEvent.log()` en `perform_destroy()`
   - ✅ Registra `cierre` normalizado
   - ✅ `action` es string simple
   - ✅ `event_type` específico ('delete')

**Resultado**: Eventos duplicados con el sistema legacy dominando.

---

## 🔧 Cambios Aplicados

### **Archivo**: `src/components/TarjetasCierreNomina/LibroRemuneracionesCard.jsx`

**Líneas modificadas**: 230-275

**ANTES** (36 líneas de logging):
```jsx
const handleEliminarArchivo = async () => {
  setEliminando(true);
  setError("");
  
  // ✅ LOGGING: Eliminación iniciada
  if (activityLogger.current) {
    await activityLogger.current.log({
      action: 'delete_started',
      resourceType: 'libro_remuneraciones',
      details: { archivo: archivoNombre, libro_id: libroId }
    });
  }
  
  try {
    await onEliminarArchivo();
    
    // ✅ LOGGING: Eliminación completada
    if (activityLogger.current) {
      await activityLogger.current.log({
        action: 'delete_completed',
        resourceType: 'libro_remuneraciones',
        details: { archivo: archivoNombre }
      });
    }
    
  } catch (err) {
    // ✅ LOGGING: Error en eliminación
    if (activityLogger.current) {
      await activityLogger.current.log({
        action: 'delete_error',
        resourceType: 'libro_remuneraciones',
        details: { archivo: archivoNombre, error: err.message }
      });
    }
    
    setError("Error eliminando el archivo.");
  } finally {
    setEliminando(false);
  }
};
```

**DESPUÉS** (13 líneas, sin logging):
```jsx
const handleEliminarArchivo = async () => {
  setEliminando(true);
  setError("");
  
  // ℹ️ El logging se hace automáticamente en el backend (perform_destroy)
  // usando ActivityEvent.log() con cierre normalizado
  
  try {
    await onEliminarArchivo();
    
  } catch (err) {
    setError("Error eliminando el archivo.");
  } finally {
    setEliminando(false);
  }
};
```

**Reducción**: -23 líneas de código innecesario

---

## ✅ Flujo Correcto Ahora

```
Usuario hace click en "Eliminar"
    ↓
Frontend: handleEliminarArchivo()
    ↓
API Call: DELETE /api/nomina/libros-remuneraciones/{id}/
    ↓
Backend: LibroRemuneracionesViewSet.perform_destroy()
    ↓
1. ActivityEvent.log(
       cierre=instance.cierre,  ✅
       event_type='delete',     ✅
       action='archivo_eliminado', ✅
       details={libro_id, archivo, motivo, estado_previo}
   )
2. instance.delete()
3. Señal pre_delete → elimina archivo físico
    ↓
✅ UN SOLO EVENTO con cierre normalizado
```

---

## 🧪 Cómo Probar

### **Paso 1: Eliminar un Libro**
1. Ir a un cierre con libro subido
2. Click en "Eliminar archivo"
3. Confirmar eliminación

### **Paso 2: Verificar Evento en BD**

```bash
docker compose exec -T django python manage.py shell << 'EOF'
from nomina.models import ActivityEvent

# Buscar último evento de eliminación
event = ActivityEvent.objects.filter(
    action='archivo_eliminado'
).order_by('-timestamp').first()

if event:
    print(f"✅ Evento Encontrado")
    print(f"ID: {event.id}")
    print(f"Cierre ID: {event.cierre_id} {'✅' if event.cierre_id else '❌'}")
    print(f"Event Type: {event.event_type}")
    print(f"Action: {event.action}")
    print(f"Resource Type: {event.resource_type}")
    print(f"Details: {event.details}")
else:
    print("❌ No se encontró evento")
EOF
```

### **Resultado Esperado**:
```
✅ Evento Encontrado
ID: 102
Cierre ID: 30 ✅
Event Type: delete
Action: archivo_eliminado
Resource Type: libro_remuneraciones
Details: {'libro_id': 61, 'archivo': '...', 'motivo': 'No especificado', 'estado_previo': 'clasificado'}
```

---

## 📊 Comparación Antes/Después

| Campo | ANTES (Legacy) | DESPUÉS (V2) |
|-------|----------------|--------------|
| **cierre_id** | NULL ❌ | 30 ✅ |
| **event_type** | 'nomina' ❌ | 'delete' ✅ |
| **resource_type** | 'cierre' ❌ | 'libro_remuneraciones' ✅ |
| **action** | "{'action': 'delete_completed', ...}" ❌ | 'archivo_eliminado' ✅ |
| **details** | {} ❌ | {libro_id, archivo, motivo, estado_previo} ✅ |
| **Query eficiente** | NO ❌ | SÍ ✅ |

---

## 🚀 Beneficios

1. **Eliminación de duplicados**: Solo 1 evento por acción
2. **Cierre normalizado**: Queries eficientes por cierre
3. **Datos consistentes**: Mismo formato que upload/process
4. **Menos código frontend**: -23 líneas
5. **Single source of truth**: Backend controla el logging

---

## 📝 Archivos Revisados

- ✅ `LibroRemuneracionesCard.jsx` - Logging eliminado
- ✅ `MovimientosMesCard.jsx` - Solo logs de sesión/polling (OK)
- ⏭️ `ArchivosAnalistaCard.jsx` - Pendiente revisar
- ⏭️ `NovedadesCard.jsx` - Pendiente revisar

---

## 🔜 Próximos Pasos

1. **[AHORA]** Probar eliminación de libro → Verificar evento con cierre
2. **[SIGUIENTE]** Revisar otros componentes (ArchivosAnalista, Novedades)
3. **[FUTURO]** Deprecar endpoint `/api/nomina/activity-log/log/`
4. **[FUTURO]** Migrar eventos legacy (poblar cierre_id)

---

**Estado**: ✅ Cambio aplicado, pendiente prueba end-to-end
