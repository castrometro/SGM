# 📊 Estrategia de Dual Logging System

## 🎯 **Objetivo**

Implementar un sistema de logging dual que separe:
- **Historial de Usuario** (TarjetaActivityLogNomina) - Lo que ve el usuario
- **Auditoría Técnica** (ActivityEvent) - Debugging y monitoreo del sistema

---

## 📋 **División de Responsabilidades**

### **1. TarjetaActivityLogNomina → Historial de Usuario (UI)**

**Propósito:** Eventos que el usuario VE en el historial del cierre

**Características:**
- ✅ Solo eventos de **negocio** importantes
- ✅ Descripciones **legibles** para humanos
- ✅ Organizado por **tarjeta** (sección del cierre)
- ✅ Estados simples: `exito`, `error`, `warning`

**Modelo:**
```python
TarjetaActivityLogNomina(
    cierre=cierre,                    # Solo cierre (cliente se infiere)
    tarjeta="libro_remuneraciones",   # Sección
    accion="upload_excel",            # Acción predefinida
    descripcion="Usuario subió 202509_libro_remuneraciones_867433007.xlsx",
    usuario=request.user,             # Usuario real
    detalles={'archivo': 'nombre.xlsx', 'hora': '15:30:45'},
    resultado="exito",
    timestamp=auto
)
```

**Eventos a registrar:**
```python
# LIBRO DE REMUNERACIONES
- upload_excel         → Usuario sube archivo
- classification_complete → Clasificación automática completa
- process_start        → Usuario hace clic en "Procesar"
- process_complete     → Procesamiento completado
- delete_archivo       → Usuario elimina archivo
- validation_error     → Error en validación

# MOVIMIENTOS MES
- upload_excel
- process_complete
- delete_archivo

# NOVEDADES
- upload_excel
- process_complete
- delete_archivo

# etc...
```

---

### **2. ActivityEvent → Auditoría Técnica (Sistema)**

**Propósito:** Logs detallados para debugging, monitoreo y auditoría completa

**Características:**
- ✅ **Todos** los eventos del sistema (técnicos incluidos)
- ✅ Información detallada en `details` JSON
- ✅ Task IDs de Celery para troubleshooting
- ✅ Trazabilidad completa de procesos asíncronos

**Modelo:**
```python
ActivityEvent(
    user=user,
    cierre=cierre,
    cliente=cliente,  # Denormalizado para queries rápidas
    event_type='process',
    action='analisis_headers_exitoso',  # Puede ser muy técnico
    resource_type='libro_remuneraciones',
    resource_id='123',
    details={
        'task_id': 'abc-123',
        'headers_detectados': 71,
        'archivo': 'nombre.xlsx'
    }
)
```

**Eventos a registrar:**
```python
# Todos los eventos técnicos:
- upload_iniciado
- archivo_validado
- procesamiento_iniciado
- analisis_headers_iniciado
- analisis_headers_exitoso
- clasificacion_headers_iniciada
- clasificacion_headers_exitosa
- actualizacion_empleados_iniciada
- chunk_empleados_procesado
- actualizacion_empleados_exitosa
- guardado_registros_iniciado
- guardado_registros_exitoso
# etc...
```

---

## 🔄 **Flujo de Logging en Libro de Remuneraciones**

### **Ejemplo: Usuario sube un archivo**

```python
# En views_libro_remuneraciones.py - perform_create()

# 1. LOG TÉCNICO: Upload iniciado
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='upload_iniciado',
    resource_type='libro_remuneraciones',
    details={'archivo': archivo.name, 'tamano_bytes': archivo.size}
)

# 2. LOG TÉCNICO: Validación
ActivityEvent.log(
    event_type='validation',
    action='archivo_validado',
    details={'validaciones': ['formato', 'tamaño', 'nombre']}
)

# 3. LOG DE USUARIO: Upload completado ← Usuario lo ve
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="libro_remuneraciones",
    accion="upload_excel",
    descripcion=f"Subió {archivo.name}",
    usuario=request.user,
    detalles={'archivo': archivo.name, 'hora': timezone.now().strftime('%H:%M:%S')},
    resultado="exito",
    ip_address=get_client_ip(request)
)

# 4. LOG TÉCNICO: Chain iniciado
ActivityEvent.log(
    event_type='process',
    action='procesamiento_iniciado',
    details={'task_id': result.id}
)
```

### **Ejemplo: Clasificación automática completa**

```python
# En tasks_refactored/libro_remuneraciones.py - clasificar_headers_...()

# 1. LOG TÉCNICO: Inicio
ActivityEvent.log(
    user=sistema_user,
    cierre=cierre,
    cliente=cliente,
    event_type='process',
    action='clasificacion_headers_iniciada',
    resource_type='libro_remuneraciones',
    details={'task_id': self.request.id}
)

# 2. Procesar...

# 3. LOG TÉCNICO: Éxito
ActivityEvent.log(
    event_type='process',
    action='clasificacion_headers_exitosa',
    details={
        'headers_total': 71,
        'headers_clasificados': 71,
        'headers_sin_clasificar': 0
    }
)

# 4. LOG DE USUARIO: Libro listo ← Usuario lo ve
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="libro_remuneraciones",
    accion="classification_complete",
    descripcion=f"Libro clasificado automáticamente: {headers_clasificados} columnas",
    usuario=sistema_user,
    detalles={
        'headers_clasificados': 71,
        'estado': 'clasificado',
        'hora': timezone.now().strftime('%H:%M:%S')
    },
    resultado="exito"
)
```

### **Ejemplo: Procesamiento manual completo**

```python
# En tasks_refactored/libro_remuneraciones.py - consolidar_registros_task()

# 1. LOG TÉCNICO: Éxito final
ActivityEvent.log(
    user=sistema_user,
    cierre=cierre,
    cliente=cliente,
    event_type='process',
    action='guardado_registros_exitoso',
    resource_type='libro_remuneraciones',
    details={
        'task_id': self.request.id,
        'registros_guardados': 5680,
        'chunks_procesados': 4
    }
)

# 2. LOG DE USUARIO: Procesamiento completo ← Usuario lo ve
registrar_actividad_tarjeta_nomina(
    cierre_id=libro.cierre.id,
    tarjeta="libro_remuneraciones",
    accion="process_complete",
    descripcion=f"Procesamiento completado: {empleados} empleados, {registros} registros",
    usuario=sistema_user,  # Usuario original se guardó en upload
    detalles={
        'empleados_actualizados': empleados,
        'registros_guardados': registros,
        'estado_final': 'completado',
        'hora': timezone.now().strftime('%H:%M:%S')
    },
    resultado="exito"
)
```

---

## 📊 **Resumen de Eventos por Modelo**

### **TarjetaActivityLogNomina (6-8 eventos por ciclo)**

| Acción | Cuándo | Quién ve |
|--------|--------|----------|
| `upload_excel` | Usuario sube archivo | Usuario |
| `classification_complete` | Clasificación automática OK | Usuario |
| `process_start` | Usuario hace clic en "Procesar" | Usuario |
| `process_complete` | Procesamiento terminado | Usuario |
| `delete_archivo` | Usuario borra archivo | Usuario |
| `validation_error` | Error en validación | Usuario |

### **ActivityEvent (15-20 eventos por ciclo)**

| Action | Cuándo | Para qué |
|--------|--------|----------|
| `upload_iniciado` | Al recibir archivo | Auditoría |
| `archivo_validado` | Después de validar | Debugging |
| `upload_completado` | Archivo guardado | Auditoría |
| `procesamiento_iniciado` | Chain disparado | Debugging |
| `analisis_headers_iniciado` | Tarea 1 inicia | Debugging |
| `analisis_headers_exitoso` | Tarea 1 completa | Debugging |
| `clasificacion_headers_iniciada` | Tarea 2 inicia | Debugging |
| `clasificacion_headers_exitosa` | Tarea 2 completa | Debugging |
| `actualizacion_empleados_iniciada` | Tarea 3 inicia | Debugging |
| `chunk_empleados_procesado` | Por cada chunk | Monitoreo |
| `actualizacion_empleados_exitosa` | Tarea 3 completa | Debugging |
| `guardado_registros_iniciado` | Tarea 4 inicia | Debugging |
| `chunk_registros_procesado` | Por cada chunk | Monitoreo |
| `guardado_registros_exitoso` | Tarea 4 completa | Debugging |

---

## 🎨 **Uso en el Frontend**

### **Historial del Cierre (para usuario):**

```javascript
// GET /api/nomina/cierres/{id}/historial/
// Usa TarjetaActivityLogNomina

const response = await api.get(`/nomina/cierres/${cierreId}/historial/`);
// Retorna:
[
  {
    timestamp: "2025-10-18T15:30:45Z",
    tarjeta: "libro_remuneraciones",
    accion: "upload_excel",
    descripcion: "Subió 202509_libro_remuneraciones_867433007.xlsx",
    usuario: "analista@empresa.com",
    resultado: "exito"
  },
  {
    timestamp: "2025-10-18T15:30:46Z",
    tarjeta: "libro_remuneraciones",
    accion: "classification_complete",
    descripcion: "Libro clasificado automáticamente: 71 columnas",
    resultado: "exito"
  },
  // ...
]
```

### **Logs Técnicos (para admin/debugging):**

```javascript
// GET /api/nomina/activity-events/?cierre={id}
// Usa ActivityEvent

const response = await api.get(`/nomina/activity-events/?cierre=${cierreId}`);
// Retorna todos los eventos técnicos detallados
```

---

## 📝 **Próximos Pasos de Implementación**

### **Fase 1: Activar TarjetaActivityLogNomina (✅ HECHO)**
- [x] Cambiar import de `_stub` a `models_logging`

### **Fase 2: Agregar logs de usuario en ViewSet**
- [ ] `upload_excel` después de guardar archivo
- [ ] `delete_archivo` al eliminar libro
- [ ] `process_start` al iniciar procesamiento manual

### **Fase 3: Agregar logs de usuario en Tasks**
- [ ] `classification_complete` al terminar clasificación
- [ ] `process_complete` al terminar procesamiento

### **Fase 4: Simplificar ActivityEvent**
- [ ] Mantener solo los eventos técnicos necesarios
- [ ] Eliminar duplicados innecesarios

### **Fase 5: Crear endpoints API**
- [ ] `GET /api/nomina/cierres/{id}/historial/` → TarjetaActivityLogNomina
- [ ] `GET /api/nomina/activity-events/` → ActivityEvent (solo admin)

---

## 🎯 **Ventajas del Sistema Dual**

1. ✅ **Separación de concerns**: UI vs Sistema
2. ✅ **Performance**: Queries más rápidas (menos eventos en tabla de usuario)
3. ✅ **Claridad**: Usuario ve solo lo relevante
4. ✅ **Debugging**: Logs técnicos completos para troubleshooting
5. ✅ **Auditoría**: Trazabilidad completa del sistema
6. ✅ **Escalabilidad**: Puedes limpiar logs técnicos sin perder historial de usuario

---

**Fecha:** 18 de octubre de 2025  
**Estado:** En implementación  
**Progreso:** Fase 1 completada (import reactivado)
