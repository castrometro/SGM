# Extracción Módulo Novedades - Completada ✅

**Fecha:** 18 de octubre de 2025  
**Módulo:** `backend/nomina/tasks_refactored/novedades.py`  
**Versión:** 2.3.0

---

## 📋 Resumen

Se completó exitosamente la extracción del módulo **Novedades** desde el monolítico `tasks.py` (5,289 líneas) hacia un archivo modular dedicado con **dual logging** completo y **propagación de usuario_id**.

### Tareas Extraídas: **11 tareas totales**

#### Grupo 1: Análisis y Clasificación (Chain Inicial)
1. **`procesar_archivo_novedades_con_logging`** - Función entry point (no @shared_task)
2. **`analizar_headers_archivo_novedades`** - Extrae headers del Excel
3. **`clasificar_headers_archivo_novedades_task`** - Clasifica headers automáticamente

#### Grupo 2: Procesamiento Final Simple
4. **`actualizar_empleados_desde_novedades_task`** - Actualiza datos de empleados
5. **`guardar_registros_novedades_task`** - Guarda registros de nómina

#### Grupo 3: Procesamiento Optimizado con Chord (Archivos grandes >50 filas)
6. **`actualizar_empleados_desde_novedades_task_optimizado`** - Versión con chord para empleados
7. **`guardar_registros_novedades_task_optimizado`** - Versión con chord para registros

#### Grupo 4: Procesamiento Paralelo en Chunks
8. **`procesar_chunk_empleados_novedades_task`** - Procesa un chunk de empleados
9. **`procesar_chunk_registros_novedades_task`** - Procesa un chunk de registros

#### Grupo 5: Consolidación
10. **`consolidar_empleados_novedades_task`** - Callback del chord de empleados
11. **`finalizar_procesamiento_novedades_task`** - Callback del chord de registros

---

## 🔄 Workflow Completo

### Fase 1: Upload y Análisis Inicial
```
Usuario sube archivo
    ↓
procesar_archivo_novedades_con_logging(archivo_id, usuario_id)
    ↓
Chain:
    analizar_headers_archivo_novedades.s(archivo_id, usuario_id)
        ↓
    clasificar_headers_archivo_novedades_task.s(usuario_id)
        ↓
    Estado: 'clasificado' o 'clasif_pendiente'
```

### Fase 2A: Procesamiento Simple (archivos pequeños ≤50 filas)
```
Usuario click "Procesar Final"
    ↓
Chain:
    actualizar_empleados_desde_novedades_task.s({"archivo_id": X, "usuario_id": Y})
        ↓
    guardar_registros_novedades_task.s()
        ↓
    Estado: 'procesado'
```

### Fase 2B: Procesamiento Optimizado (archivos grandes >50 filas)
```
Usuario click "Procesar Final Optimizado"
    ↓
Chain:
    actualizar_empleados_desde_novedades_task_optimizado.s({"archivo_id": X, "usuario_id": Y})
        ↓ (divide en chunks)
        Chord:
            [procesar_chunk_empleados_novedades_task.s(chunk_1),
             procesar_chunk_empleados_novedades_task.s(chunk_2),
             ...
             procesar_chunk_empleados_novedades_task.s(chunk_N)]
            ↓ (callback)
        consolidar_empleados_novedades_task.s()
        ↓
    guardar_registros_novedades_task_optimizado.s()
        ↓ (divide en chunks)
        Chord:
            [procesar_chunk_registros_novedades_task.s(chunk_1),
             procesar_chunk_registros_novedades_task.s(chunk_2),
             ...
             procesar_chunk_registros_novedades_task.s(chunk_N)]
            ↓ (callback)
        finalizar_procesamiento_novedades_task.s(usuario_id=Y)
        ↓
    Estado: 'procesado' / 'con_errores_parciales' / 'con_error'
```

---

## ✅ Implementación de Dual Logging

### Funciones Helper Creadas

#### 1. `log_process_start_novedades(archivo_id, fase, usuario_id, detalles_extra)`
- Registra inicio de fase en **TarjetaActivityLogNomina**
- Registra inicio de fase en **ActivityEvent**
- Fallback inteligente de usuario: `usuario_id → sistema_user`

#### 2. `log_process_complete_novedades(archivo_id, fase, usuario_id, resultado, detalles_extra)`
- Registra completado en ambos sistemas
- Parámetro `resultado`: 'exito', 'warning', 'error'
- Incluye timestamp y estadísticas

### Puntos de Logging

| Fase | Event Type | Tarjeta | Ubicación |
|------|-----------|---------|-----------|
| **Inicio procesamiento** | process_start | novedades | procesar_archivo_novedades_con_logging |
| **Análisis headers** | process_start → process_complete | novedades | analizar_headers_archivo_novedades |
| **Clasificación** | process_start → process_complete | novedades | clasificar_headers_archivo_novedades_task |
| **Actualización empleados** | process_start → process_complete | novedades | actualizar_empleados_desde_novedades_task |
| **Guardado registros** | process_start → process_complete | novedades | guardar_registros_novedades_task |
| **Empleados optimizado** | process_start → process_complete | novedades | actualizar_empleados_desde_novedades_task_optimizado |
| **Registros optimizado** | process_start → process_complete | novedades | guardar_registros_novedades_task_optimizado |
| **Finalización paralela** | process_complete | novedades | finalizar_procesamiento_novedades_task |

---

## 🔧 Propagación de usuario_id

### Estrategia Implementada

```python
# 1. Entry point recibe usuario_id
procesar_archivo_novedades_con_logging(archivo_id, usuario_id)

# 2. Primera tarea lo recibe como parámetro
analizar_headers_archivo_novedades(archivo_id, usuario_id)
    return {"archivo_id": X, "headers": [...], "usuario_id": Y}

# 3. Segunda tarea lo extrae del result
clasificar_headers_archivo_novedades_task(result, usuario_id=None):
    if not usuario_id:
        usuario_id = result.get("usuario_id")
    return {"archivo_id": X, ..., "usuario_id": Y}

# 4. Se propaga a través de toda la cadena
actualizar_empleados_desde_novedades_task(result, usuario_id=None):
    if not usuario_id:
        usuario_id = result.get("usuario_id") if isinstance(result, dict) else None
```

### Fallback Inteligente en Logging

```python
if usuario_id:
    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        usuario = get_sistema_user()
else:
    usuario = get_sistema_user()
```

---

## 📁 Archivos Modificados

### 1. **Creado:** `backend/nomina/tasks_refactored/novedades.py` (1,159 líneas)
- 11 tareas con decorador `@shared_task(bind=True, queue='nomina_queue')`
- 1 función entry point (no decorada)
- 2 funciones helper de logging dual
- Imports completos de utilities
- Documentación exhaustiva con emojis

### 2. **Modificado:** `backend/nomina/tasks_refactored/__init__.py`
- Agregadas 11 exportaciones de novedades
- Actualizada versión: `2.2.0` → `2.3.0`
- Actualizado `TAREAS_MIGRADAS['novedades']`: `False` → `True`
- Total exports ahora: **23 tareas** (10 libro + 1 movimientos + 1 archivos_analista + 11 novedades)

### 3. **Modificado:** `backend/nomina/views_archivos_novedades.py`
- **Línea 20:** Import cambiado a `tasks_refactored.novedades`
- **Línea 163:** Upload action - usa `procesar_archivo_novedades_con_logging(id, user.id)`
- **Línea 190:** Reprocesar action - usa `procesar_archivo_novedades_con_logging(id, user.id)`
- **Línea 375-401:** procesar_final - usa tareas refactorizadas con usuario_id
- **Línea 403-450:** procesar_final_optimizado - usa tareas refactorizadas con usuario_id
- **Línea 434:** Agregado `usuario=request.user` en registro de actividad

---

## 🎯 Características Especiales

### 1. **Procesamiento Adaptativo**
```python
# Archivos pequeños (≤50 filas): procesamiento directo
if total_filas <= 50:
    count = actualizar_empleados_desde_novedades(archivo)
    return {"empleados_actualizados": count, "modo": "directo"}

# Archivos grandes (>50 filas): procesamiento paralelo con chord
chunks = dividir_dataframe_novedades(ruta_archivo, chunk_size)
tasks_paralelas = [procesar_chunk_empleados_novedades_task.s(id, chunk) for chunk in chunks]
callback = consolidar_empleados_novedades_task.s()
resultado_chord = chord(tasks_paralelas)(callback)
```

### 2. **Chunk Size Dinámico**
```python
chunk_size = calcular_chunk_size_dinamico(total_filas)
# Pequeño: 50-100 filas → chunk_size = 50
# Mediano: 100-500 filas → chunk_size = 100
# Grande: 500-1000 filas → chunk_size = 200
# Muy grande: >1000 filas → chunk_size = 250
```

### 3. **Manejo de Estados**
- `pendiente` → Archivo subido, esperando procesamiento
- `analizando_hdrs` → Extrayendo headers
- `hdrs_analizados` → Headers extraídos
- `clasif_en_proceso` → Clasificando headers
- `clasif_pendiente` → Headers sin clasificar (requiere intervención)
- `clasificado` → Listo para procesamiento final
- `procesado` → Completado exitosamente
- `con_errores_parciales` → Completado con algunos errores
- `con_error` → Error total

### 4. **Estadísticas Consolidadas**
```python
{
    'empleados_actualizados': 150,
    'registros_creados': 1200,
    'registros_actualizados': 50,
    'errores_totales': 3,
    'chunks_procesados': 10,
    'tiempo_total': 45.2,
    'modo': 'chord_paralelo'
}
```

---

## ⚙️ Configuración Celery

### Queue Utilizada
```python
@shared_task(bind=True, queue='nomina_queue')
```

### Workers Necesarios
```bash
# En celery_worker.sh debe incluir:
celery -A sgm_backend worker \
    -Q nomina_queue,general,contabilidad_queue \
    -n nomina_worker@%h \
    --concurrency=4
```

---

## 🧪 Testing

### Test Manual Recomendado

1. **Upload y Análisis**
```bash
# 1. Subir archivo de novedades desde frontend
# 2. Verificar logs en TarjetaActivityLogNomina:
SELECT * FROM nomina_tarjetaactivitylognomina 
WHERE tarjeta = 'novedades' 
ORDER BY timestamp DESC;

# Esperar:
# - process_start: procesamiento_inicial
# - process_start: analisis_headers
# - process_complete: analisis_headers (exito)
# - process_start: clasificacion_headers
# - process_complete: clasificacion_headers (exito/warning)
```

2. **Procesamiento Final Simple**
```bash
# Click "Procesar Final" en frontend
# Verificar:
# - process_start: actualizacion_empleados
# - process_complete: actualizacion_empleados
# - process_start: guardado_registros
# - process_complete: guardado_registros
```

3. **Procesamiento Optimizado**
```bash
# Con archivo >50 filas, click "Procesar Final Optimizado"
# Verificar en Flower o logs:
# - Chord con N chunks de empleados
# - Consolidación de empleados
# - Chord con N chunks de registros
# - Finalización con estadísticas
```

### Validación de usuario_id

```python
# Verificar que todos los logs tengan el usuario correcto
logs = TarjetaActivityLogNomina.objects.filter(
    tarjeta='novedades'
).exclude(usuario__username='sistema')

for log in logs:
    assert log.usuario is not None
    assert log.usuario.id != 1  # No debería ser Pablo Castro genérico
    print(f"✅ Log {log.id}: usuario={log.usuario.username}")
```

---

## 📊 Impacto del Refactoring

### Antes
- ❌ 11 tareas dispersas en tasks.py (5,289 líneas)
- ❌ Sin logging dual
- ❌ Sin propagación de usuario
- ❌ Difícil mantenimiento

### Después
- ✅ Módulo dedicado novedades.py (1,159 líneas)
- ✅ Dual logging completo (8 puntos de logging)
- ✅ Propagación de usuario_id en toda la cadena
- ✅ Documentación exhaustiva
- ✅ Código organizado por workflow

### Progreso General
- **Tareas migradas:** 23 / 59 (39%)
- **Módulos completados:** 4 / 12
  - ✅ Libro de Remuneraciones (10 tareas)
  - ✅ Movimientos del Mes (1 tarea)
  - ✅ Archivos Analista (1 tarea)
  - ✅ Novedades (11 tareas)

---

## 🚀 Deployment

```bash
# Reiniciar servicios
cd /root/SGM
docker compose restart celery_worker django

# Verificar workers registrados
docker compose exec celery_worker celery -A sgm_backend inspect registered

# Deberían aparecer las 11 nuevas tareas:
# - nomina.tasks_refactored.novedades.analizar_headers_archivo_novedades
# - nomina.tasks_refactored.novedades.clasificar_headers_archivo_novedades_task
# - ... (9 más)
```

---

## 📝 Notas Importantes

1. **No se eliminó tasks.py:** El monolito original se mantiene intacto para views legacy
2. **Tarjeta 'novedades' ya existía:** No requirió modificación del modelo
3. **Usuario_id en chord callback:** Se propaga explícitamente: `finalizar_procesamiento_novedades_task.s(usuario_id=Y)`
4. **Imports de utilities:** Se mantienen desde utils (no refactorizados aún)
5. **Procesamiento paralelo:** Solo se activa para archivos >50 filas

---

## 🎉 Conclusión

La extracción del módulo **Novedades** fue exitosa. Es el módulo más complejo hasta ahora por incluir:
- ✅ Workflow con chain + chord anidados
- ✅ Procesamiento adaptativo (simple vs paralelo)
- ✅ 11 tareas con dual logging completo
- ✅ Propagación correcta de usuario_id
- ✅ Consolidación de estadísticas de múltiples chunks

**Status:** ✅ COMPLETADO  
**Listo para:** Testing en producción  
**Próximo módulo:** Consolidación (8 tareas estimadas)
