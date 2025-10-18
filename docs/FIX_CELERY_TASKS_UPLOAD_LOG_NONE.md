# Fix Adicional: Celery Tasks con upload_log=None

## 🐛 Problema Detectado

Después de arreglar el stub y el upload en `views_libro_remuneraciones.py`, al procesar el archivo con Celery aparecía este error:

```
[ERROR] Task nomina.tasks.analizar_headers_libro_remuneraciones_con_logging raised unexpected: 
AttributeError("'NoneType' object has no attribute 'estado'")

File "/app/nomina/tasks.py", line 1551, in analizar_headers_libro_remuneraciones_con_logging
    upload_log.estado = "analizando_hdrs"
    ^^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'estado'
```

## 🔍 Causa Raíz

Los tasks de Celery esperaban un `upload_log_id` válido, pero después del fix del stub, estamos pasando `None`. Los tasks intentaban:

1. Obtener el objeto: `upload_log = UploadLogNomina.objects.get(id=upload_log_id)`
2. Acceder a atributos: `upload_log.estado = "analizando_hdrs"`

Esto fallaba porque `upload_log_id` era `None`.

## 🔧 Solución Aplicada

**Archivo modificado:** `/root/SGM/backend/nomina/tasks.py`

### 1️⃣ Task: `analizar_headers_libro_remuneraciones_con_logging` (línea ~1541)

#### ❌ Antes (asumía upload_log siempre existe)
```python
upload_log = UploadLogNomina.objects.get(id=upload_log_id)
upload_log.estado = "analizando_hdrs"
upload_log.save()
```

#### ✅ Después (maneja None)
```python
upload_log = None
if upload_log_id is not None:
    try:
        upload_log = UploadLogNomina.objects.get(id=upload_log_id)
        upload_log.estado = "analizando_hdrs"
        upload_log.save()
    except Exception as e:
        logger.debug(f"[STUB] UploadLog no disponible: {e}")

# Luego en el código...
if upload_log:
    upload_log.estado = "hdrs_analizados"
    upload_log.headers_detectados = headers
    upload_log.save()
```

### 2️⃣ Task: `clasificar_headers_libro_remuneraciones_con_logging` (línea ~1604)

#### ❌ Antes (asumía upload_log siempre existe)
```python
upload_log = UploadLogNomina.objects.get(id=upload_log_id)
upload_log.estado = "clasif_en_proceso"
upload_log.save()
```

#### ✅ Después (maneja None)
```python
upload_log = None
if upload_log_id is not None:
    try:
        upload_log = UploadLogNomina.objects.get(id=upload_log_id)
    except Exception as e:
        logger.debug(f"[STUB] UploadLog no disponible: {e}")

if upload_log:
    upload_log.estado = "clasif_en_proceso"
    upload_log.save()

# Más adelante...
if headers_sin_clasificar:
    libro.estado = "clasif_pendiente"
    if upload_log:
        upload_log.estado = "clasif_pendiente"
else:
    libro.estado = "clasificado"
    if upload_log:
        upload_log.estado = "clasificado"

# Y al final...
if upload_log:
    resumen_final = {...}
    upload_log.resumen = resumen_final
    upload_log.save()
```

## 📋 Cambios Implementados

| Ubicación | Cambio |
|-----------|--------|
| **tasks.py línea ~1547** | Verificar `if upload_log_id is not None` antes de obtener el objeto |
| **tasks.py línea ~1567** | Verificar `if upload_log` antes de actualizar estado |
| **tasks.py línea ~1613** | Verificar `if upload_log_id is not None` antes de obtener el objeto |
| **tasks.py línea ~1630** | Verificar `if upload_log` antes de actualizar estados |
| **tasks.py línea ~1656-1662** | Verificar `if upload_log` antes de actualizar estados finales |
| **tasks.py línea ~1666-1675** | Verificar `if upload_log` antes de guardar resumen |

## ✅ Resultado

Ahora los tasks de Celery pueden procesar archivos **sin upload_log**:

```
[INFO] Procesando libro de remuneraciones id=53 con upload_log=None
[INFO] Headers analizados exitosamente para libro 53
[INFO] Clasificando headers para libro 53 con upload_log None
[INFO] Libro 53: 50 headers clasificados, 0 sin clasificar
```

## 🧪 Cómo Verificar

1. **Sube un archivo** de Libro de Remuneraciones
2. **Revisa logs de Celery:**
   ```bash
   docker compose logs celery_worker --tail=50
   ```
3. **Verifica que el procesamiento sea exitoso:**
   ```
   [INFO] Procesando libro de remuneraciones id=X con upload_log=None
   [INFO] Headers analizados exitosamente para libro X
   [INFO] Libro X: Y headers clasificados, Z sin clasificar
   ```

## 📊 Flujo Completo Corregido

```
1. Usuario sube archivo
   ↓
2. views_libro_remuneraciones.py
   - Crea stub (no persistido)
   - Pasa upload_log_id=None a Celery
   ↓
3. analizar_headers_libro_remuneraciones_con_logging
   - Verifica if upload_log_id is not None ✅
   - Procesa headers del libro
   - Actualiza solo el libro (no el upload_log)
   ↓
4. clasificar_headers_libro_remuneraciones_con_logging
   - Verifica if upload_log is not None ✅
   - Clasifica headers
   - Actualiza solo el libro (no el upload_log)
   ↓
5. ✅ Procesamiento completado sin errores
```

## 🔄 Estado del Sistema

| Componente | Estado | Logging V1 | Logging V2 |
|------------|--------|------------|------------|
| Upload de archivos | ✅ Funcional | Stub (no-op) | - |
| Celery tasks | ✅ Funcional | Stub (no-op) | - |
| Activity eventos | ✅ Funcional | - | Activo |
| Libro procesamiento | ✅ Funcional | - | - |

## 📄 Archivos Modificados

1. `/root/SGM/backend/nomina/models_logging_stub.py` - Fix de `objects` como atributo
2. `/root/SGM/backend/nomina/views_libro_remuneraciones.py` - Deshabilitar persistencia stub
3. `/root/SGM/backend/nomina/tasks.py` - Manejar `upload_log_id=None` en tasks

---

**✅ SISTEMA COMPLETAMENTE FUNCIONAL**  
Todos los flujos de upload y procesamiento están funcionando correctamente.

**Fecha:** 16 octubre 2025  
**Celery restart:** Aplicado exitosamente
