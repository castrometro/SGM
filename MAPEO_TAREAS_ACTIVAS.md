# 🗺️ Mapeo de Tareas ACTIVAS en SGM

**Fecha Creación**: 17 de octubre de 2025  
**Última Actualización**: 18 de octubre de 2025  
**Objetivo**: Identificar qué tareas de `tasks.py` se usan REALMENTE en las views  
**Estrategia**: Extraer SOLO las activas, mantener `tasks.py` original intacto

**Estado Refactorización**: 2 de 8 módulos completados (25%) ✅

---

## 📊 Metodología de Mapeo

```bash
# Buscar llamadas .delay() y .apply_async() en todas las views
grep -rn "\.delay\|\.apply_async" backend/nomina/views*.py

# Buscar imports de tasks
grep -rn "from .tasks import" backend/nomina/views*.py
```

**Total encontrado**: 34 llamadas a tareas Celery

---

## ✅ Tareas ACTIVAS (Usadas en Views)

### **1. Libro de Remuneraciones** (10 tareas) ✅ REFACTORIZADO

**Estado**: ✅ COMPLETADO - Extraído a `tasks_refactored/libro_remuneraciones.py`  
**Fecha Extracción**: 17-18 de octubre de 2025  
**Archivo**: `views_libro_remuneraciones.py`

```python
# ANTES (tasks.py original)
from .tasks import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    # ...
)

# AHORA (tasks_refactored)
from .tasks_refactored.libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,      # ✅ REFACTORIZADA
    clasificar_headers_libro_remuneraciones_con_logging,    # ✅ REFACTORIZADA
    actualizar_empleados_desde_libro,                       # ✅ REFACTORIZADA
    guardar_registros_nomina,                               # ✅ REFACTORIZADA
    actualizar_empleados_desde_libro_optimizado,            # ✅ REFACTORIZADA (chord)
    guardar_registros_nomina_optimizado,                    # ✅ REFACTORIZADA (chord)
    # + 4 helper tasks (procesar_chunk_*, consolidar_*)
)
```

**Mejoras implementadas**:
- ✅ Logging dual (TarjetaActivityLogNomina + ActivityEvent)
- ✅ Usuario correcto propagado (no más Pablo Castro ID 1)
- ✅ Estado "procesado" (no "completado") para consistencia con frontend
- ✅ 807 líneas en archivo dedicado

**Flujo**:
```
Upload Libro
    ↓
analizar_headers_libro_remuneraciones_con_logging (usuario_id)
    ↓
clasificar_headers_libro_remuneraciones_con_logging (usuario_id)
    ↓ (chord)
actualizar_empleados_desde_libro_optimizado (usuario_id)
    ↓
guardar_registros_nomina_optimizado (usuario_id)
```

---

### **2. Movimientos del Mes** (1 tarea) ✅ REFACTORIZADO

**Estado**: ✅ COMPLETADO - Extraído a `tasks_refactored/movimientos_mes.py`  
**Fecha Extracción**: 18 de octubre de 2025  
**Archivo**: `views_movimientos_mes.py`

```python
# ANTES (tasks.py original)
from .tasks import procesar_movimientos_mes

# AHORA (tasks_refactored)
from .tasks_refactored.movimientos_mes import procesar_movimientos_mes_con_logging

# Llamada simplificada (2 parámetros vs 3):
# ANTES: procesar_movimientos_mes.delay(instance.id, None, request.user.id)
# AHORA: procesar_movimientos_mes_con_logging.delay(instance.id, request.user.id)
```

**Mejoras implementadas**:
- ✅ Logging dual completo (TarjetaActivityLogNomina + ActivityEvent)
- ✅ Usuario correcto propagado (verificado con Cecilia Reyes ID 24)
- ✅ Estado "procesado" para consistencia con frontend
- ✅ Eliminado parámetro obsoleto `upload_log_id`
- ✅ 309 líneas en archivo dedicado
- ✅ **VALIDADO EN PRODUCCIÓN**: Procesamiento real ejecutado exitosamente

**Evidencia de Ejecución Real**:
```
[INFO] Usuario: cecilia.reyes@bdo.cl (ID: 24)
[INFO] Resultados: {'ausentismos': 1, 'vacaciones': 1, 'variaciones_contrato': 2}
[INFO] ✅ Estado: procesado (0.158s)
```

---

### **3. Archivos Analista** (1 tarea)

**Archivo**: `views_archivos_analista.py`

```python
from .tasks import procesar_archivo_analista  # ✅ ACTIVA

# Llamadas (3 lugares):
procesar_archivo_analista.delay(archivo_analista.id)      # línea 102
procesar_archivo_analista.delay(archivo.id)               # línea 123
procesar_archivo_analista.delay(archivo_id, upload_log.id) # línea 255
```

---

### **4. Novedades** (1 tarea principal + workflow)

**Archivo**: `views_archivos_novedades.py`, `views.py`

```python
from .tasks import procesar_archivo_novedades  # ✅ ACTIVA

# Llamadas directas:
procesar_archivo_novedades.delay(archivo_novedades.id)    # views_archivos_novedades.py:162
procesar_archivo_novedades.delay(archivo.id)              # views_archivos_novedades.py:189
procesar_archivo_novedades.delay(archivo_id, upload_log.id) # views_upload_con_logging.py:341

# Workflow complejo (views_archivos_novedades.py):
workflow = chain(
    analizar_headers_archivo_novedades.si(...),
    clasificar_headers_archivo_novedades_task.si(...),
    chord(
        [procesar_chunk_empleados_novedades_task.si(...) for chunk in chunks],
        procesar_chunk_registros_novedades_task.si(...)
    ),
    finalizar_procesamiento_novedades_task.si(...)
).apply_async()
```

**Tareas del workflow**:
- `analizar_headers_archivo_novedades` ✅
- `clasificar_headers_archivo_novedades_task` ✅
- `procesar_chunk_empleados_novedades_task` ✅
- `procesar_chunk_registros_novedades_task` ✅
- `finalizar_procesamiento_novedades_task` ✅

---

### **5. Consolidación** (1 tarea)

**Archivo**: `views.py:314`

```python
from .tasks import consolidar_datos_nomina_task  # ✅ ACTIVA

# Llamada:
task = consolidar_datos_nomina_task.delay(cierre.id, modo=modo_consolidacion)
```

**Nota**: Recibe parámetro `modo` → puede ser 'optimizado', 'secuencial', 'paralelo'

---

### **6. Incidencias** (3 tareas)

**Archivo**: `views.py`

```python
from .tasks import (
    generar_incidencias_consolidados_v2,      # ✅ ACTIVA
    generar_incidencias_totales_simple,       # ✅ ACTIVA
    generar_incidencias_cierre_task,          # ✅ ACTIVA
)

# Llamadas:
generar_incidencias_consolidados_v2.delay(cierre.id, clasificaciones)  # línea 571
generar_incidencias_totales_simple.delay(cierre.id)                    # línea 2186
generar_incidencias_cierre_task.delay(pk)                              # línea 3267
```

---

### **7. Discrepancias** (2 tareas)

**Archivo**: `views.py`

```python
from .tasks import (
    analizar_datos_cierre_task,              # ✅ ACTIVA
    generar_discrepancias_cierre_paralelo,   # ✅ ACTIVA
    generar_discrepancias_cierre_task,       # ✅ ACTIVA
)

# Llamadas:
analizar_datos_cierre_task.delay(cierre_id, tolerancia_variacion)     # línea 2612
generar_discrepancias_cierre_paralelo.delay(cierre_id, usuario_id)    # línea 3492
generar_discrepancias_cierre_task.delay(pk)                           # línea 3624
```

---

### **8. Informes** (3 tareas)

**Archivo**: `views_informes.py`

```python
from .tasks import (
    build_informe_libro,           # ✅ ACTIVA
    build_informe_movimientos,     # ✅ ACTIVA
    unir_y_guardar_informe,        # ✅ ACTIVA
)

# Usado en workflows de generación de informes
```

---

## 📋 Resumen de Tareas ACTIVAS

| Dominio | Tareas Activas | Total |
|---------|----------------|-------|
| **Libro Remuneraciones** | analizar_headers_con_logging, clasificar_headers_con_logging, actualizar_empleados, guardar_registros, actualizar_empleados_optimizado, guardar_registros_optimizado | **6** |
| **Movimientos Mes** | procesar_movimientos_mes | **1** |
| **Archivos Analista** | procesar_archivo_analista | **1** |
| **Novedades** | procesar_archivo_novedades, analizar_headers, clasificar_headers, procesar_chunk_empleados, procesar_chunk_registros, finalizar_procesamiento | **6** |
| **Consolidación** | consolidar_datos_nomina_task | **1** |
| **Incidencias** | generar_incidencias_consolidados_v2, generar_incidencias_totales_simple, generar_incidencias_cierre_task | **3** |
| **Discrepancias** | analizar_datos_cierre_task, generar_discrepancias_cierre_paralelo, generar_discrepancias_cierre_task | **3** |
| **Informes** | build_informe_libro, build_informe_movimientos, unir_y_guardar_informe | **3** |
| **TOTAL** | | **24** |

---

## 🗑️ Tareas POTENCIALMENTE NO USADAS

En `tasks.py` hay **59 tareas**, pero solo **24 se usan activamente**.

**Candidatos a deprecated** (~35 tareas):

### **Versiones obsoletas de consolidación**:
- `consolidar_datos_nomina_task_optimizado` (si `consolidar_datos_nomina_task` ya maneja el modo)
- `consolidar_datos_nomina_task_secuencial`
- `procesar_empleados_libro_paralelo` (standalone, no llamado)
- `procesar_movimientos_personal_paralelo`
- `procesar_conceptos_consolidados_paralelo`
- `finalizar_consolidacion_post_movimientos`
- `consolidar_resultados_finales`

### **Versiones sin logging** (duplicadas):
- `analizar_headers_libro_remuneraciones` (sin `_con_logging`)
- `clasificar_headers_libro_remuneraciones_task` (sin `_con_logging`)

### **Versiones de incidencias sin usar**:
- `procesar_chunk_comparacion_individual_task`
- `procesar_comparacion_suma_total_task`
- `consolidar_resultados_incidencias_task`
- `generar_incidencias_cierre_paralelo`
- `obtener_resultado_procesamiento_dual`
- `procesar_chunk_clasificaciones`
- `consolidar_resultados_filtrados`
- `consolidar_resultados_completos`
- `procesar_resultado_vacio`
- `comparar_y_generar_reporte_final`

### **Helpers que podrían ser funciones privadas**:
- `obtener_clasificaciones_cierre`
- `crear_chunks`
- `procesar_incidencias_clasificacion_individual`
- `consolidar_resultados_chunks`
- `calcular_diferencias_resultados`
- `guardar_comparacion_incidencias`
- `actualizar_estado_cierre_post_procesamiento`

---

## 📦 Plan de Extracción CONSERVADOR

### **Estrategia**:

1. **NO tocar `tasks.py` original** ✅
2. **Crear `nomina/tasks/` paralelo** con SOLO las 24 activas
3. **Mantener imports compatibles** en `__init__.py`
4. **Actualizar views gradualmente** (opcional)

### **Estructura Nueva**:

```
backend/nomina/
├── tasks.py                           # ⚠️ MANTENER INTACTO (legacy)
│
└── tasks/                             # 🆕 NUEVO PAQUETE
    ├── __init__.py                    # Exporta las 24 activas
    │
    ├── libro_remuneraciones.py        # 6 tareas
    │   ├── analizar_headers_con_logging
    │   ├── clasificar_headers_con_logging
    │   ├── actualizar_empleados
    │   ├── guardar_registros
    │   ├── actualizar_empleados_optimizado
    │   └── guardar_registros_optimizado
    │
    ├── movimientos_mes.py             # 1 tarea
    │   └── procesar_movimientos_mes
    │
    ├── archivos_analista.py           # 1 tarea
    │   └── procesar_archivo_analista
    │
    ├── novedades.py                   # 6 tareas
    │   ├── procesar_archivo_novedades
    │   ├── analizar_headers
    │   ├── clasificar_headers_task
    │   ├── procesar_chunk_empleados_task
    │   ├── procesar_chunk_registros_task
    │   └── finalizar_procesamiento_task
    │
    ├── consolidacion.py               # 1 tarea
    │   └── consolidar_datos_nomina_task
    │
    ├── incidencias.py                 # 3 tareas
    │   ├── generar_incidencias_consolidados_v2
    │   ├── generar_incidencias_totales_simple
    │   └── generar_incidencias_cierre_task
    │
    ├── discrepancias.py               # 3 tareas
    │   ├── analizar_datos_cierre_task
    │   ├── generar_discrepancias_cierre_paralelo
    │   └── generar_discrepancias_cierre_task
    │
    └── informes.py                    # 3 tareas
        ├── build_informe_libro
        ├── build_informe_movimientos
        └── unir_y_guardar_informe
```

### **`tasks/__init__.py`** (Retrocompatibilidad):

```python
# backend/nomina/tasks/__init__.py

"""
🔄 Tareas Celery Refactorizadas - Solo tareas ACTIVAS

Este paquete contiene las 24 tareas que se usan activamente en las views.
El archivo tasks.py original se mantiene intacto como fallback.
"""

# Libro de Remuneraciones (6)
from .libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
)

# Movimientos del Mes (1)
from .movimientos_mes import (
    procesar_movimientos_mes,
)

# Archivos Analista (1)
from .archivos_analista import (
    procesar_archivo_analista,
)

# Novedades (6)
from .novedades import (
    procesar_archivo_novedades,
    analizar_headers_archivo_novedades,
    clasificar_headers_archivo_novedades_task,
    procesar_chunk_empleados_novedades_task,
    procesar_chunk_registros_novedades_task,
    finalizar_procesamiento_novedades_task,
)

# Consolidación (1)
from .consolidacion import (
    consolidar_datos_nomina_task,
)

# Incidencias (3)
from .incidencias import (
    generar_incidencias_consolidados_v2,
    generar_incidencias_totales_simple,
    generar_incidencias_cierre_task,
)

# Discrepancias (3)
from .discrepancias import (
    analizar_datos_cierre_task,
    generar_discrepancias_cierre_paralelo,
    generar_discrepancias_cierre_task,
)

# Informes (3)
from .informes import (
    build_informe_libro,
    build_informe_movimientos,
    unir_y_guardar_informe,
)

__all__ = [
    # Libro (6)
    'analizar_headers_libro_remuneraciones_con_logging',
    'clasificar_headers_libro_remuneraciones_con_logging',
    'actualizar_empleados_desde_libro',
    'guardar_registros_nomina',
    'actualizar_empleados_desde_libro_optimizado',
    'guardar_registros_nomina_optimizado',
    # Movimientos (1)
    'procesar_movimientos_mes',
    # Analista (1)
    'procesar_archivo_analista',
    # Novedades (6)
    'procesar_archivo_novedades',
    'analizar_headers_archivo_novedades',
    'clasificar_headers_archivo_novedades_task',
    'procesar_chunk_empleados_novedades_task',
    'procesar_chunk_registros_novedades_task',
    'finalizar_procesamiento_novedades_task',
    # Consolidación (1)
    'consolidar_datos_nomina_task',
    # Incidencias (3)
    'generar_incidencias_consolidados_v2',
    'generar_incidencias_totales_simple',
    'generar_incidencias_cierre_task',
    # Discrepancias (3)
    'analizar_datos_cierre_task',
    'generar_discrepancias_cierre_paralelo',
    'generar_discrepancias_cierre_task',
    # Informes (3)
    'build_informe_libro',
    'build_informe_movimientos',
    'unir_y_guardar_informe',
]
```

---

## ✅ Ventajas de Este Enfoque

1. **Seguro**: `tasks.py` original intacto como fallback
2. **Limpio**: Solo 24 tareas activas, bien organizadas
3. **Compatible**: Views siguen funcionando (`from .tasks import X`)
4. **Gradual**: Podemos migrar views poco a poco
5. **Documentado**: Sabemos exactamente qué se usa

---

## 🚀 Próximos Pasos

### **Fase 1: Crear estructura** (30 min)
```bash
mkdir backend/nomina/tasks
touch backend/nomina/tasks/__init__.py
```

### **Fase 2: Extraer Libro (PRIMERO)** (2h)
- Copiar 6 tareas a `tasks/libro_remuneraciones.py`
- Limpiar código, agregar ActivityEvent integrado
- Test: Subir libro → Verificar funciona

### **Fase 3: Extraer resto** (4h)
- Consolidación (1 tarea)
- Movimientos (1 tarea)
- Novedades (6 tareas)
- Incidencias (3 tareas)
- Discrepancias (3 tareas)
- Informes (3 tareas)
- Analista (1 tarea)

### **Fase 4: Validación** (1h)
- Verificar Celery registra las 24 tareas
- Test end-to-end de cada flujo
- Logs limpios sin errores

---

## 📊 Comparación Final

| Métrica | ANTES | DESPUÉS |
|---------|-------|---------|
| Archivo principal | 5,279 líneas | ~50 líneas (mantener como está) |
| Tareas expuestas | 59 tareas mezcladas | 24 tareas activas organizadas |
| Archivos | 1 monolito | 8 módulos especializados |
| Código muerto | ~35 tareas sin usar | 0 (no extraído) |
| Mantenibilidad | ❌ Imposible | ✅ Alta |

---

**Estado**: Mapeo completo ✅  
**Próximo**: Crear estructura y extraer Libro de Remuneraciones  
**Tiempo estimado**: 8 horas total
