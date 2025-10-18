# 🔍 Análisis: Sistema de Logging en Eliminación de Libros

**Fecha**: 17 de octubre de 2025  
**Problema**: Los eventos de eliminación no tienen `cierre` normalizado

---

## 🔬 Hallazgos

### **1. Sistema Dual de Logging Activo**

Hay **dos sistemas** registrando eventos simultáneamente:

| Sistema | Ubicación | `cierre` | `action` Type | Estado |
|---------|-----------|----------|---------------|--------|
| **Legacy** | Frontend → `/api/nomina/activity-log/log/` | ❌ NULL | String con dict | ⚠️ Activo |
| **Nuevo (V2)** | Backend → `ActivityEvent.log()` | ✅ ForeignKey | String simple | ✅ Activo |

### **2. Eventos de Eliminación Encontrados**

#### Eventos Legacy (Frontend)
```python
ID: 100
Timestamp: 2025-10-17 16:47:15
User: Cecilia
Cliente: World Courier
Cierre ID: None  # ❌ No normalizado
Event Type: nomina
Action: "{'action': 'delete_completed', 'resourceType': 'libro_remuneraciones', ...}"  # ❌ Dict en string
Resource Type: cierre
Resource ID: 30
Details: {}  # ❌ Vacío
```

#### Eventos Nuevo Sistema (Backend)
```python
# ❌ NO ENCONTRADOS
# El perform_destroy tiene el código pero no se ejecutó
```

---

## 🧪 Pruebas Realizadas

### **Test 1: ActivityEvent.log() Funciona**
```bash
$ python test_activity_event_delete.py
✅ Evento creado exitosamente!
   Event ID: 101
   Cierre ID: 4  # ✅ Normalizado
   Action: test_eliminacion
   Details: {'libro_id': 19, 'test': True}
```

**Conclusión**: El método `ActivityEvent.log()` funciona correctamente.

### **Test 2: Análisis de Logs Django**
```
[INFO] === ELIMINANDO LIBRO DE REMUNERACIONES 60 ===
[DEBUG] STUB: registrar_actividad_tarjeta_nomina()  # ← Sistema legacy
[INFO] Eliminados 71 registros de conceptos...
... (sin "✅ ActivityEvent registrado")
```

**Conclusión**: El log "✅ ActivityEvent registrado" nunca apareció, lo que indica que `ActivityEvent.log()` no se ejecutó en `perform_destroy`.

---

## 🕵️ Causa Raíz

### **Código en `perform_destroy` (views_libro_remuneraciones.py:253-289)**

```python
def perform_destroy(self, instance):
    logger.info(f"=== ELIMINANDO LIBRO {instance.id} ===")
    
    # ✅ Código está presente
    ActivityEvent.log(
        user=self.request.user,
        cliente=instance.cierre.cliente,
        cierre=instance.cierre,  # Normalizado
        event_type='delete',
        action='archivo_eliminado',
        resource_type='libro_remuneraciones',
        resource_id=str(libro_id),
        details={...},
        request=self.request
    )
    logger.info(f"✅ ActivityEvent registrado: archivo_eliminado para libro {libro_id}")
    
    instance.delete()
    logger.info(f"=== LIBRO {libro_id} ELIMINADO CORRECTAMENTE ===")
```

### **¿Por qué no se ejecutó?**

**Hipótesis más probable**: El código fue actualizado DESPUÉS de la eliminación del libro 60.

#### Timeline de Eventos:
1. **16:39** - Código original (sin `ActivityEvent.log()` en perform_destroy)
2. **16:40-16:47** - Libro 60 subido y eliminado
3. **16:47** - Eliminación registrada con sistema legacy ❌
4. **Post 16:47** - Código actualizado con `ActivityEvent.log()`
5. **17:08** - Django reiniciado con código nuevo

### **Evidencia Supporting**:
- ✅ `ActivityEvent.log()` funciona en prueba manual
- ✅ Código actual de `perform_destroy` tiene logging V2
- ❌ Log "✅ ActivityEvent registrado" no apareció en eliminación de libro 60
- ⚠️ Evento de eliminación en BD es del sistema legacy

---

## ✅ Solución

### **Acción 1: Desactivar Logging Frontend (Eliminar Duplicados)**

El frontend NO debería llamar `activityLogger.log()` para operaciones CRUD porque el backend ya lo hace en `perform_destroy`.

**Archivo**: `src/components/TarjetasCierreNomina/LibroRemuneracionesCard.jsx`

**Líneas a comentar/eliminar**: 233-262

```jsx
// ❌ ELIMINAR ESTO (duplica logging del backend)
const handleEliminarArchivo = async () => {
  setEliminando(true);
  setError("");
  
  // ❌ Logging legacy - ELIMINAR
  // if (activityLogger.current) {
  //   await activityLogger.current.log({
  //     action: 'delete_started',
  //     resourceType: 'libro_remuneraciones',
  //     details: {...}
  //   });
  // }
  
  try {
    await onEliminarArchivo();  // ✅ Solo esto
    
    // ❌ Logging legacy - ELIMINAR
    // if (activityLogger.current) {
    //   await activityLogger.current.log({...});
    // }
    
  } catch (err) {
    setError("Error eliminando el archivo.");
  } finally {
    setEliminando(false);
  }
};
```

### **Acción 2: Verificar con Nueva Eliminación**

1. Subir un nuevo libro
2. Eliminarlo desde el frontend
3. Verificar que se crea evento con `cierre` normalizado:

```sql
SELECT id, timestamp, cierre_id, event_type, action, resource_id
FROM nomina_activity_event
WHERE action = 'archivo_eliminado'
ORDER BY timestamp DESC
LIMIT 1;
```

**Resultado esperado**:
```
cierre_id: <not null>  # ✅
event_type: delete     # ✅
action: archivo_eliminado  # ✅
```

---

## 📊 Comparación de Sistemas

| Aspecto | Sistema Legacy (Frontend) | Sistema V2 (Backend) |
|---------|--------------------------|----------------------|
| **Trigger** | `activityLogger.current.log()` | `ActivityEvent.log()` en ViewSet |
| **Endpoint** | `/api/nomina/activity-log/log/` | N/A (directo a modelo) |
| **cierre** | ❌ NULL | ✅ ForeignKey normalizado |
| **action** | ❌ Dict serializado a string | ✅ String simple |
| **event_type** | ❌ 'nomina' (genérico) | ✅ 'delete', 'upload', etc. |
| **details** | ❌ Vacío {} | ✅ JSON con contexto |
| **IP tracking** | ❌ No | ✅ Desde request |
| **User agent** | ❌ No | ✅ Desde request |

---

## 🎯 Próximos Pasos

1. **[ALTA]** Eliminar llamadas a `activityLogger.log()` en frontend para operaciones CRUD
   - LibroRemuneracionesCard.jsx
   - MovimientosMesCard.jsx  
   - ArchivosAnalistaCard.jsx
   - NovedadesCard.jsx

2. **[MEDIA]** Probar eliminación end-to-end con sistema nuevo

3. **[BAJA]** Migrar datos legacy (poblar `cierre_id` en eventos antiguos)

4. **[BAJA]** Deprecar endpoint `/api/nomina/activity-log/log/`

---

## 📝 Comandos Útiles

### Verificar Eventos Recientes
```bash
docker compose exec -T django python manage.py shell << 'EOF'
from nomina.models import ActivityEvent

# Sistema nuevo (con cierre)
new_events = ActivityEvent.objects.filter(cierre__isnull=False).count()

# Sistema legacy (sin cierre)
legacy_events = ActivityEvent.objects.filter(cierre__isnull=True).count()

print(f"Nuevo: {new_events}, Legacy: {legacy_events}")
EOF
```

### Crear Evento de Test
```bash
docker compose exec -T django python backend/test_activity_event_delete.py
```

---

**Conclusión**: El sistema V2 está implementado correctamente pero el frontend sigue usando el sistema legacy para algunos eventos. Necesitamos desactivar el logging frontend para operaciones CRUD.
