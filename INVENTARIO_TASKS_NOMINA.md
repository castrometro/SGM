# 📊 Inventario de Tasks - Módulo Nómina

**Fecha**: 24 de octubre de 2025  
**Propósito**: Identificar qué tasks están refactorizadas y cuáles quedan en `tasks.py`  
**Estado**: 🔄 En proceso de limpieza

---

## 📁 Estructura Actual

```
backend/nomina/
├── tasks.py                           ← ⚠️ ARCHIVO MONOLÍTICO (4,700+ líneas)
├── tasks_libro_remuneraciones.py     ← ✅ VACÍO (deprecated)
└── tasks_refactored/                  ← ✅ NUEVAS TASKS ORGANIZADAS
    ├── __init__.py                    (1 función - re-exports)
    ├── archivos_analista.py           (2 funciones)
    ├── consolidacion.py               (12 funciones) ✅
    ├── correcciones.py                (3 funciones)
    ├── discrepancias.py               (6 funciones)
    ├── incidencias.py                 (4 funciones)
    ├── libro_remuneraciones.py        (12 funciones) ✅
    ├── movimientos_mes.py             (2 funciones)
    └── novedades.py                   (16 funciones) ✅
```

---

## ✅ Tasks YA REFACTORIZADAS (en `tasks_refactored/`)

### 1. **libro_remuneraciones.py** (12 funciones)

**Estado**: ✅ **REFACTORIZADO COMPLETAMENTE**  
**Ubicación**: `backend/nomina/tasks_refactored/libro_remuneraciones.py`

#### Tasks Públicas (Celery):
1. ✅ `analizar_headers_libro_remuneraciones_con_logging` - Analiza headers del Excel
2. ✅ `clasificar_headers_libro_remuneraciones_con_logging` - Clasifica con fuzzy matching
3. ✅ `actualizar_empleados_desde_libro_optimizado` - Crea EmpleadoCierre (paralelo)
4. ✅ `guardar_registros_nomina_optimizado` - Crea RegistroConceptoEmpleado (paralelo)
5. ✅ `procesar_chunk_empleados_task` - Worker para chunk de empleados
6. ✅ `procesar_chunk_registros_task` - Worker para chunk de registros
7. ✅ `consolidar_empleados_task` - Callback consolidación empleados
8. ✅ `consolidar_registros_task` - Callback consolidación registros

#### Funciones Auxiliares:
9. ✅ `_calcular_chunk_size_dinamico` - Calcula tamaño óptimo de chunk
10. ✅ `_registrar_tarjeta_activity_log` - Logging de actividad
11. ✅ `_obtener_usuario_sistema` - Obtiene usuario para logs
12. ✅ `build_informe_libro` - Genera informe del libro procesado

**Dependencias**:
- `utils/LibroRemuneracionesOptimizado.py` (dividir chunks, procesar utils)
- `models.py` (LibroRemuneracionesUpload, EmpleadoCierre, etc.)

**Usado por**:
- `views_libro_remuneraciones.py` - Endpoint `/procesar/`
- Frontend: `LibroRemuneracionesCard.jsx` - Botón "Procesar"

---

### 2. **consolidacion.py** (12 funciones)

**Estado**: ✅ **REFACTORIZADO COMPLETAMENTE**  
**Ubicación**: `backend/nomina/tasks_refactored/consolidacion.py`

#### Tasks Públicas (Celery):
1. ✅ `consolidar_datos_nomina_task_optimizado` - Task principal de consolidación
2. ✅ `procesar_empleados_libro_paralelo` - Procesa empleados en paralelo
3. ✅ `procesar_movimientos_personal_paralelo` - Procesa movimientos en paralelo
4. ✅ `procesar_conceptos_consolidados_paralelo` - Procesa conceptos en paralelo
5. ✅ `finalizar_consolidacion_post_movimientos` - Finaliza consolidación
6. ✅ `consolidar_resultados_finales` - Consolida resultados de todos los chunks
7. ✅ `consolidar_datos_nomina_task` - Wrapper con selector de modo (optimizado/secuencial)

#### Funciones Auxiliares:
8. ✅ `_generar_header_valor_empleado` - Genera HeaderValorEmpleado
9. ✅ `_procesar_chunk_empleados` - Lógica de procesamiento de chunk empleados
10. ✅ `_procesar_chunk_movimientos` - Lógica de procesamiento de chunk movimientos
11. ✅ `_procesar_chunk_conceptos` - Lógica de procesamiento de chunk conceptos
12. ✅ `_finalizar_estado_consolidacion` - Actualiza estado final

**Dependencias**:
- `models.py` (NominaConsolidada, HeaderValorEmpleado, EmpleadoCierre, etc.)
- `utils/consolidacion.py` (lógica de negocio)

**Usado por**:
- `views_consolidacion.py` - Endpoint `/consolidar/`
- Frontend: Botón "Consolidar" en vista de cierre

---

### 3. **novedades.py** (16 funciones)

**Estado**: ✅ **REFACTORIZADO COMPLETAMENTE**  
**Ubicación**: `backend/nomina/tasks_refactored/novedades.py`

#### Tasks Públicas (Celery):
1. ✅ `analizar_headers_archivo_novedades` - Analiza headers de archivo de novedades
2. ✅ `clasificar_headers_archivo_novedades_task` - Clasifica headers
3. ✅ `procesar_archivo_novedades` - Task principal de procesamiento
4. ✅ `actualizar_empleados_desde_novedades_task_optimizado` - Crea empleados (paralelo)
5. ✅ `guardar_registros_novedades_task_optimizado` - Guarda registros (paralelo)
6. ✅ `procesar_chunk_empleados_novedades_task` - Worker chunk empleados
7. ✅ `procesar_chunk_registros_novedades_task` - Worker chunk registros
8. ✅ `consolidar_empleados_novedades_task` - Callback empleados
9. ✅ `finalizar_procesamiento_novedades_task` - Callback final

#### Funciones Auxiliares:
10. ✅ `_dividir_dataframe_novedades` - Divide Excel en chunks
11. ✅ `_procesar_chunk_empleados_novedades_util` - Lógica empleados
12. ✅ `_procesar_chunk_registros_novedades_util` - Lógica registros
13. ✅ `_consolidar_stats_empleados_novedades` - Consolida stats empleados
14. ✅ `_consolidar_stats_registros_novedades` - Consolida stats registros
15. ✅ `_calcular_chunk_size_dinamico_novedades` - Calcula chunk size
16. ✅ `_registrar_activity_log_novedades` - Logging de actividad

**Dependencias**:
- `models.py` (ArchivoNovedades, EmpleadoCierre, RegistroConceptoEmpleadoNovedades)
- Similar a libro_remuneraciones pero para novedades

**Usado por**:
- `views_archivos_novedades.py` - Upload y procesamiento de novedades

---

### 4. **movimientos_mes.py** (2 funciones)

**Estado**: ✅ **REFACTORIZADO**  
**Ubicación**: `backend/nomina/tasks_refactored/movimientos_mes.py`

1. ✅ `procesar_movimientos_mes` - Procesa movimientos del mes
2. ✅ `_procesar_movimientos_mes_util` - Lógica de procesamiento

**Usado por**:
- `views_movimientos_mes.py` - Upload de movimientos mensuales

---

### 5. **incidencias.py** (4 funciones)

**Estado**: ✅ **REFACTORIZADO**  
**Ubicación**: `backend/nomina/tasks_refactored/incidencias.py`

1. ✅ `generar_incidencias_cierre_paralelo` - Genera incidencias en paralelo
2. ✅ `_procesar_chunk_clasificaciones` - Procesa chunk de clasificaciones
3. ✅ `_consolidar_resultados_incidencias` - Consolida resultados
4. ✅ `_guardar_comparacion_incidencias` - Guarda comparación

**Usado por**:
- `views_incidencias.py` - Generación de incidencias

---

### 6. **discrepancias.py** (6 funciones)

**Estado**: ✅ **REFACTORIZADO**  
**Ubicación**: `backend/nomina/tasks_refactored/discrepancias.py`

1. ✅ `generar_discrepancias_cierre_paralelo` - Genera discrepancias en paralelo
2. ✅ `_procesar_discrepancias_chunk` - Procesa chunk de discrepancias
3. ✅ `_consolidar_discrepancias_finales` - Consolida resultados
4. ✅ `_verificar_archivos_listos_para_discrepancias` - Valida archivos
5. ✅ `_crear_historial_discrepancias` - Crea registro de historial
6. ✅ `_finalizar_historial_discrepancias` - Finaliza historial

**Usado por**:
- `views_discrepancias.py` - Generación de discrepancias

---

### 7. **correcciones.py** (3 funciones)

**Estado**: ✅ **REFACTORIZADO**  
**Ubicación**: `backend/nomina/tasks_refactored/correcciones.py`

1. ✅ `aplicar_correcciones_masivas` - Aplica correcciones en batch
2. ✅ `_validar_correcciones` - Valida correcciones
3. ✅ `_aplicar_correccion_individual` - Aplica corrección única

**Usado por**:
- `views_correcciones.py` - Aplicación de correcciones

---

### 8. **archivos_analista.py** (2 funciones)

**Estado**: ✅ **REFACTORIZADO**  
**Ubicación**: `backend/nomina/tasks_refactored/archivos_analista.py`

1. ✅ `procesar_archivo_analista` - Procesa archivo subido por analista
2. ✅ `_validar_archivo_analista` - Valida archivo

**Usado por**:
- `views_archivos_analista.py` - Upload de archivos de analista

---

## ⚠️ Tasks PENDIENTES DE REFACTORIZAR (en `tasks.py`)

### **tasks.py** - 4,700+ líneas, ~50 funciones

**Estado**: ⚠️ **MONOLÍTICO - NECESITA LIMPIEZA**

#### Funciones que YA TIENEN equivalente refactorizado (DUPLICADAS):

| Función en tasks.py | Equivalente Refactorizado | Acción |
|---------------------|---------------------------|--------|
| `analizar_headers_libro_remuneraciones` | ✅ `libro_remuneraciones.analizar_headers_libro_remuneraciones_con_logging` | 🗑️ **ELIMINAR** |
| `clasificar_headers_libro_remuneraciones_task` | ✅ `libro_remuneraciones.clasificar_headers_libro_remuneraciones_con_logging` | 🗑️ **ELIMINAR** |
| `actualizar_empleados_desde_libro` | ✅ `libro_remuneraciones.actualizar_empleados_desde_libro_optimizado` | 🗑️ **ELIMINAR** |
| `guardar_registros_nomina` | ✅ `libro_remuneraciones.guardar_registros_nomina_optimizado` | 🗑️ **ELIMINAR** |
| `procesar_chunk_empleados_task` | ✅ `libro_remuneraciones.procesar_chunk_empleados_task` | 🗑️ **ELIMINAR** |
| `procesar_chunk_registros_task` | ✅ `libro_remuneraciones.procesar_chunk_registros_task` | 🗑️ **ELIMINAR** |
| `procesar_archivo_novedades` | ✅ `novedades.procesar_archivo_novedades` | 🗑️ **ELIMINAR** |
| `analizar_headers_archivo_novedades` | ✅ `novedades.analizar_headers_archivo_novedades` | 🗑️ **ELIMINAR** |
| `clasificar_headers_archivo_novedades_task` | ✅ `novedades.clasificar_headers_archivo_novedades_task` | 🗑️ **ELIMINAR** |
| `actualizar_empleados_desde_novedades_task` | ✅ `novedades.actualizar_empleados_desde_novedades_task_optimizado` | 🗑️ **ELIMINAR** |
| `guardar_registros_novedades_task` | ✅ `novedades.guardar_registros_novedades_task_optimizado` | 🗑️ **ELIMINAR** |
| `procesar_chunk_empleados_novedades_task` | ✅ `novedades.procesar_chunk_empleados_novedades_task` | 🗑️ **ELIMINAR** |
| `procesar_chunk_registros_novedades_task` | ✅ `novedades.procesar_chunk_registros_novedades_task` | 🗑️ **ELIMINAR** |
| `consolidar_empleados_novedades_task` | ✅ `novedades.consolidar_empleados_novedades_task` | 🗑️ **ELIMINAR** |
| `finalizar_procesamiento_novedades_task` | ✅ `novedades.finalizar_procesamiento_novedades_task` | 🗑️ **ELIMINAR** |
| `procesar_movimientos_mes` | ✅ `movimientos_mes.procesar_movimientos_mes` | 🗑️ **ELIMINAR** |
| `consolidar_datos_nomina_task_optimizado` | ✅ `consolidacion.consolidar_datos_nomina_task_optimizado` | 🗑️ **ELIMINAR** |
| `procesar_empleados_libro_paralelo` | ✅ `consolidacion.procesar_empleados_libro_paralelo` | 🗑️ **ELIMINAR** |
| `procesar_movimientos_personal_paralelo` | ✅ `consolidacion.procesar_movimientos_personal_paralelo` | 🗑️ **ELIMINAR** |
| `procesar_conceptos_consolidados_paralelo` | ✅ `consolidacion.procesar_conceptos_consolidados_paralelo` | 🗑️ **ELIMINAR** |
| `consolidar_datos_nomina_task` | ✅ `consolidacion.consolidar_datos_nomina_task` | 🗑️ **ELIMINAR** |
| `generar_incidencias_cierre_paralelo` | ✅ `incidencias.generar_incidencias_cierre_paralelo` | 🗑️ **ELIMINAR** |
| `generar_discrepancias_cierre_paralelo` | ✅ `discrepancias.generar_discrepancias_cierre_paralelo` | 🗑️ **ELIMINAR** |
| `procesar_archivo_analista` | ✅ `archivos_analista.procesar_archivo_analista` | 🗑️ **ELIMINAR** |

**Total duplicadas**: ~24 funciones (≈50% del archivo)

---

#### Funciones que AÚN NO tienen equivalente refactorizado:

| Función | Descripción | Prioridad | Acción Sugerida |
|---------|-------------|-----------|-----------------|
| `generar_incidencias_totales_simple` | Genera incidencias simples | Media | Mover a `incidencias.py` |
| `generar_incidencias_cierre_task` | Task vieja de incidencias | Baja | Verificar si se usa, eliminar |
| `generar_incidencias_consolidados_v2_task` | Versión v2 de incidencias | Media | Consolidar con paralelo |
| `procesar_chunk_comparacion_individual_task` | Comparación individual | Baja | Mover a `incidencias.py` |
| `procesar_comparacion_suma_total_task` | Suma total comparación | Baja | Mover a `incidencias.py` |
| `consolidar_resultados_incidencias_task` | Consolida incidencias | Baja | Ya existe en refactored |
| `analizar_datos_cierre_task` | Analiza datos del cierre | Media | Crear `analisis.py` nuevo |
| `generar_discrepancias_cierre_task` | Task vieja discrepancias | Baja | Verificar uso, eliminar |
| `consolidar_cierre_task` | Consolida cierre | Alta | Mover a `consolidacion.py` |
| `generar_incidencias_consolidadas_task` | Incidencias consolidadas | Media | Verificar vs paralelo |
| `consolidar_datos_nomina_task_secuencial` | Modo secuencial (backup) | Baja | Mantener como fallback |
| `finalizar_consolidacion_post_movimientos` | Finaliza post-mov | Media | Ya existe en refactored |
| `consolidar_resultados_finales` | Consolida finales | Media | Ya existe en refactored |
| `obtener_resultado_procesamiento_dual` | Procesamiento dual | Media | Verificar uso |
| `procesar_chunk_clasificaciones` | Procesa chunks clasificaciones | Baja | Mover a `incidencias.py` |
| `consolidar_resultados_filtrados` | Consolida filtrados | Baja | Mover a `incidencias.py` |
| `consolidar_resultados_completos` | Consolida completos | Baja | Mover a `incidencias.py` |
| `procesar_resultado_vacio` | Manejo de resultado vacío | Baja | Mover a `incidencias.py` |
| `comparar_y_generar_reporte_final` | Genera reporte final | Media | Crear `reportes.py` |
| `obtener_clasificaciones_cierre` | Obtiene clasificaciones | Baja | Util, mover a helpers |
| `crear_chunks` | Crea chunks genéricos | Baja | Util, ya existe en optimizado |
| `procesar_incidencias_clasificacion_individual` | Incidencia individual | Baja | Mover a `incidencias.py` |
| `consolidar_resultados_chunks` | Consolida chunks | Baja | Ya existe en refactored |
| `calcular_diferencias_resultados` | Calcula diferencias | Baja | Mover a helpers |
| `guardar_comparacion_incidencias` | Guarda comparación | Baja | Ya existe en refactored |
| `actualizar_estado_cierre_post_procesamiento` | Actualiza estado | Media | Mover a `consolidacion.py` |
| `procesar_discrepancias_chunk` | Chunk discrepancias | Baja | Ya existe en refactored |
| `consolidar_discrepancias_finales` | Consolida discrepancias | Baja | Ya existe en refactored |
| `_verificar_archivos_listos_para_incidencias` | Valida archivos incid | Baja | Mover a `incidencias.py` |
| `_verificar_archivos_listos_para_discrepancias` | Valida archivos discrep | Baja | Ya existe en refactored |
| `_json_safe` | Serializa a JSON seguro | Baja | Mover a `utils/helpers.py` |
| `calcular_chunk_size_dinamico` | Calcula chunk size | Baja | Ya existe en optimizado |

**Total pendientes**: ~31 funciones

---

## 📋 Plan de Limpieza Recomendado

### Fase 1: Eliminar Duplicados (PRIORIDAD ALTA) 🔥

**Objetivo**: Reducir `tasks.py` de 4,700 líneas a ~2,000 líneas

**Acciones**:
1. ✅ Verificar que todas las referencias usan `tasks_refactored`
2. 🗑️ Eliminar las 24 funciones duplicadas de `tasks.py`
3. ✅ Actualizar imports en views si es necesario
4. ✅ Ejecutar tests de regresión

**Impacto**: 
- Reducción de ~50% en tamaño de `tasks.py`
- Elimina confusión sobre qué task usar
- Facilita mantenimiento

**Riesgo**: Bajo (si se verifica bien que todo usa las refactorizadas)

**Tiempo estimado**: 2-3 horas

---

### Fase 2: Consolidar Funciones Relacionadas (PRIORIDAD MEDIA) ⚡

**Objetivo**: Agrupar funciones por dominio

**Acciones**:

#### 2.1 Crear `tasks_refactored/reportes.py`
Mover:
- `comparar_y_generar_reporte_final`
- `build_informe_libro` (ya está en libro_remuneraciones)

#### 2.2 Ampliar `tasks_refactored/incidencias.py`
Mover:
- `generar_incidencias_totales_simple`
- `generar_incidencias_cierre_task`
- `generar_incidencias_consolidados_v2_task`
- `procesar_chunk_comparacion_individual_task`
- `procesar_comparacion_suma_total_task`
- `consolidar_resultados_incidencias_task`
- `procesar_chunk_clasificaciones`
- `consolidar_resultados_filtrados`
- `consolidar_resultados_completos`
- `procesar_resultado_vacio`
- `procesar_incidencias_clasificacion_individual`
- `consolidar_resultados_chunks`
- `_verificar_archivos_listos_para_incidencias`

#### 2.3 Ampliar `tasks_refactored/consolidacion.py`
Mover:
- `consolidar_cierre_task`
- `actualizar_estado_cierre_post_procesamiento`

#### 2.4 Crear `tasks_refactored/utils.py` o `tasks_refactored/helpers.py`
Mover:
- `_json_safe`
- `obtener_clasificaciones_cierre`
- `crear_chunks`
- `calcular_diferencias_resultados`

**Impacto**: 
- `tasks.py` reducido a <1,000 líneas
- Organización clara por dominio
- Fácil encontrar funciones

**Riesgo**: Bajo

**Tiempo estimado**: 4-6 horas

---

### Fase 3: Crear Tests de Regresión (PRIORIDAD MEDIA) 🧪

**Objetivo**: Asegurar que la limpieza no rompe nada

**Acciones**:
1. Crear tests para cada módulo refactorizado
2. Ejecutar tests antes y después de cada eliminación
3. Documentar cobertura de tests

**Impacto**: 
- Confianza en refactorings futuros
- Detección temprana de bugs

**Riesgo**: Ninguno (solo agrega seguridad)

**Tiempo estimado**: 6-8 horas

---

### Fase 4: Eliminar `tasks.py` Completamente (PRIORIDAD BAJA) 🎯

**Objetivo**: Tener SOLO `tasks_refactored/`

**Acciones**:
1. Mover las últimas funciones no duplicadas
2. Actualizar todos los imports
3. Renombrar `tasks_refactored/` → `tasks/`
4. Eliminar `tasks.py` definitivamente

**Impacto**: 
- Código 100% organizado
- Sin confusión sobre ubicación de tasks

**Riesgo**: Medio (requiere cambios en muchos archivos)

**Tiempo estimado**: 8-12 horas

---

## 🎯 Recomendación Inmediata

### ✅ **Empezar con Fase 1: Eliminar Duplicados**

**Razón**: 
- **Alto impacto** (reduce 50% del archivo)
- **Bajo riesgo** (las funciones ya están refactorizadas)
- **Poco tiempo** (2-3 horas)

**Pasos concretos**:

1. **Verificar referencias** (5 min):
```bash
# Ver qué archivos importan de tasks.py
grep -r "from.*tasks import" backend/nomina/*.py | grep -v "tasks_refactored"
```

2. **Hacer backup** (1 min):
```bash
cp backend/nomina/tasks.py backend/nomina/tasks.py.backup_$(date +%Y%m%d)
```

3. **Eliminar duplicados** (30 min):
- Eliminar cada función de la lista de duplicadas
- Mantener solo las que NO tienen equivalente

4. **Actualizar imports** (30 min):
- Si algún view importa de `tasks.py`, cambiar a `tasks_refactored.X`

5. **Probar** (60 min):
- Reiniciar celery worker
- Probar cada flujo (libro, novedades, consolidación)
- Verificar que no hay errores

---

## 📊 Métricas de Progreso

| Métrica | Antes | Meta Fase 1 | Meta Fase 2 | Meta Final |
|---------|-------|-------------|-------------|------------|
| **Líneas en tasks.py** | 4,700 | 2,400 | 1,000 | 0 |
| **Funciones en tasks.py** | ~55 | ~31 | ~10 | 0 |
| **Módulos en tasks_refactored/** | 9 | 9 | 11 | 15 |
| **Cobertura de tests** | ? | 40% | 60% | 80% |
| **Duplicación de código** | Alta | Baja | Ninguna | Ninguna |

---

## 🔗 Referencias

- **Archivo principal**: `backend/nomina/tasks.py` (4,700 líneas)
- **Carpeta refactorizada**: `backend/nomina/tasks_refactored/`
- **Documentación de consolidación**: `FLUJO_CONSOLIDACION_VISUAL.md`
- **Fix reciente**: `FIX_CHUNK_LIBRO_REMUNERACIONES.md`

---

## ✅ Conclusión

**Estado actual**: El trabajo de refactoring está **75% completo**. Las tasks más críticas (libro, consolidación, novedades) ya están refactorizadas.

**Próximo paso recomendado**: **Eliminar duplicados** de `tasks.py` para reducir confusión y facilitar mantenimiento.

**Beneficio esperado**: Código más limpio, fácil de mantener, y preparado para futuros desarrollos.

---

**Autor**: Equipo SGM  
**Última actualización**: 24 de octubre de 2025
