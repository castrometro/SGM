# 📋 FLUJO 6: NOVEDADES - ARQUITECTURA Y LÓGICA COMPLETA

**Fecha:** 27 octubre 2025  
**Estado:** ✅ **COMPLETADO** (27/10/2025)  
**Familia:** Archivo de Novedades (Sistema independiente, no Archivos Analista)  
**Resultado:** 7/7 verificaciones ✅ | 0 bugs | [Ver resultados](RESULTADOS.md)

---

## 📊 RESUMEN EJECUTIVO

### Propósito
Procesar archivo Excel con **novedades de remuneraciones** (cambios salariales, bonos, ajustes) subido por analistas para actualizar datos de empleados en el cierre mensual.

### Diferencias clave vs Flujos 3-5
**⚠️ IMPORTANTE:** Novedades **NO** usa el sistema de Archivos Analista:
- ✅ ViewSet propio: `ArchivoNovedadesUploadViewSet`
- ✅ Modelo propio: `ArchivoNovedadesUpload`
- ✅ Tasks propias: `tasks_refactored/novedades.py` (11 tareas)
- ✅ Utils propias: `NovedadesRemuneraciones.py`, `NovedadesOptimizado.py`

### Complejidad
**ALTA** - Similar a Libro de Remuneraciones:
- 📄 Primeras 4 columnas fijas: RUT, Nombre, Apellido Paterno, Apellido Materno
- 💰 Columnas 5+: Conceptos de remuneración (dinámicos, clasificados por cliente)
- 🔄 Procesamiento masivo con chunking para archivos grandes (>50 filas)
- 🎯 Clasificación automática de headers usando mapeos del cliente

---

## 🏗️ ARQUITECTURA

### Modelos Involucrados

```python
# Modelo principal
ArchivoNovedadesUpload
├── cierre (ForeignKey → CierreNomina)
├── archivo (FileField)
├── analista (ForeignKey → User)
├── estado (CharField: pendiente → procesado)
└── header_json (JSONField: {headers_clasificados, headers_sin_clasificar})

# Empleados con novedades
EmpleadoCierreNovedades
├── cierre (ForeignKey → CierreNomina)
├── rut (CharField)
├── nombre (CharField)
├── apellido_paterno (CharField)
└── apellido_materno (CharField)

# Conceptos de novedades (mapeo)
ConceptoRemuneracionNovedades
├── cliente (ForeignKey → Cliente)
├── nombre_concepto_novedades (CharField)
├── concepto_libro (ForeignKey → ConceptoRemuneracion)
└── usuario_mapea (ForeignKey → User)

# Registros de conceptos
RegistroConceptoEmpleadoNovedades
├── empleado (ForeignKey → EmpleadoCierreNovedades)
├── concepto (ForeignKey → ConceptoRemuneracionNovedades)
└── valor_novedades (CharField)
```

### ViewSet y Endpoints

**Archivo:** `backend/nomina/views_archivos_novedades.py`

```python
ArchivoNovedadesUploadViewSet
├── GET /api/nomina/archivos-novedades/estado/{cierre_id}/
│   └── Obtiene estado del archivo para un cierre
├── POST /api/nomina/archivos-novedades/subir/{cierre_id}/
│   └── Sube archivo Excel de novedades
├── POST /api/nomina/archivos-novedades/{id}/procesar/
│   └── Inicia procesamiento (dispara Celery task)
└── POST /api/nomina/archivos-novedades/{id}/mapear_headers/
    └── Mapea headers sin clasificar manualmente
```

---

## 🔄 FLUJO DE PROCESAMIENTO COMPLETO

### Fase 1: Subida y Análisis (Automático)

```
Usuario Frontend
    │
    ├─► POST /api/nomina/archivos-novedades/subir/{cierre_id}/
    │   ├─ Validaciones:
    │   │  ├─ Archivo existe y es Excel
    │   │  ├─ Nombre del archivo válido (formato estándar)
    │   │  └─ Cierre existe y está activo
    │   │
    │   ├─ Limpiar datos anteriores (si resubida):
    │   │  ├─ Eliminar RegistroConceptoEmpleadoNovedades
    │   │  └─ Eliminar EmpleadoCierreNovedades
    │   │
    │   ├─ Crear/actualizar ArchivoNovedadesUpload
    │   │  └─ estado = 'pendiente'
    │   │
    │   └─► Dispatch Chain Celery:
           │
           ├─► procesar_archivo_novedades_con_logging
           │   ├─ Log: TarjetaActivityLogNomina (process_start)
           │   ├─ Log: ActivityEvent (procesamiento_celery_iniciado)
           │   │
           │   └─► CHAIN:
                   │
                   ├─► analizar_headers_archivo_novedades
                   │   ├─ Leer Excel con pandas
                   │   ├─ Extraer columnas 5+ como headers
                   │   ├─ Guardar en archivo.header_json (list)
                   │   ├─ estado → 'hdrs_analizados'
                   │   └─ Log: TarjetaActivityLogNomina + ActivityEvent
                   │
                   └─► clasificar_headers_archivo_novedades_task
                       ├─ Buscar mapeos ConceptoRemuneracionNovedades del cliente
                       ├─ Clasificar headers automáticamente:
                       │  ├─ headers_clasificados (ya mapeados)
                       │  └─ headers_sin_clasificar (requieren mapeo manual)
                       ├─ Actualizar header_json a dict
                       ├─ estado → 'clasificado' (o 'clasif_pendiente' si hay sin clasificar)
                       └─ Log: TarjetaActivityLogNomina + ActivityEvent
```

### Fase 2: Procesamiento (Manual - Usuario decide)

```
Usuario Frontend
    │
    └─► POST /api/nomina/archivos-novedades/{id}/procesar/
        │
        ├─ Validación: archivo.estado debe ser 'clasificado'
        │
        └─► Dispatch Task (modo según tamaño):
            │
            ├─► MODO SIMPLE (<50 filas):
            │   │
            │   ├─► actualizar_empleados_desde_novedades_task
            │   │   ├─ Leer Excel (primeras 4 columnas)
            │   │   ├─ Validar RUTs (ignorar totales, vacíos)
            │   │   ├─ Crear/actualizar EmpleadoCierreNovedades
            │   │   ├─ Log progreso por chunk
            │   │   └─ Return: {empleados_creados, empleados_actualizados}
            │   │
            │   └─► guardar_registros_novedades_task
            │       ├─ Leer Excel completo (col 5+)
            │       ├─ Para cada empleado:
            │       │  └─ Para cada concepto en header_json:
            │       │     ├─ Extraer valor del Excel
            │       │     └─ Crear RegistroConceptoEmpleadoNovedades
            │       ├─ Log progreso
            │       ├─ estado → 'procesado'
            │       └─ Log: TarjetaActivityLogNomina (process_complete)
            │
            └─► MODO OPTIMIZADO (≥50 filas):
                │
                ├─► CHORD empleados:
                │   ├─ Dividir DataFrame en chunks (tamaño dinámico)
                │   ├─ procesar_chunk_empleados_novedades_task (paralelo)
                │   └─ consolidar_empleados_novedades_task (callback)
                │
                └─► CHORD registros:
                    ├─ Dividir DataFrame en chunks
                    ├─ procesar_chunk_registros_novedades_task (paralelo)
                    └─ finalizar_procesamiento_novedades_task (callback)
                        ├─ Consolidar stats
                        ├─ estado → 'procesado'
                        └─ Log: TarjetaActivityLogNomina (process_complete)
```

---

## 📝 FORMATO DEL EXCEL

### Estructura Esperada

```
| RUT          | Nombre | Apellido Paterno | Apellido Materno | Concepto1 | Concepto2 | ... |
|--------------|--------|------------------|------------------|-----------|-----------|-----|
| 12345678-9   | Juan   | Pérez            | González         | 50000     | 25000     | ... |
| 98765432-1   | María  | López            | Silva            | 60000     | 30000     | ... |
| ...          | ...    | ...              | ...              | ...       | ...       | ... |
```

### Columnas Fijas (1-4)

| # | Nombre | Tipo | Descripción | Validación |
|---|--------|------|-------------|------------|
| 1 | RUT | Text | RUT del empleado | Obligatorio, formato chileno, ignora "total" |
| 2 | Nombre | Text | Nombre del empleado | Obligatorio |
| 3 | Apellido Paterno | Text | Apellido paterno | Obligatorio |
| 4 | Apellido Materno | Text | Apellido materno | Obligatorio |

### Columnas Dinámicas (5+)

- **Conceptos de remuneración** (dinámicos según cliente)
- Ejemplos: "Sueldo Base", "Bono Producción", "Gratificación", etc.
- Clasificados automáticamente usando `ConceptoRemuneracionNovedades`
- Headers sin clasificar requieren mapeo manual antes de procesar

---

## 🎯 LÓGICA DE NEGOCIO

### 1. Análisis de Headers
**Función:** `analizar_headers_archivo_novedades()`

**Qué hace:**
- Lee archivo Excel con pandas
- Extrae columnas 5+ como headers de conceptos
- Filtra headers vacíos

**Por qué:**
- Identificar qué conceptos vienen en el archivo
- Preparar para clasificación automática

**Input:** `archivo_id`  
**Output:** `list` de headers  
**BD Changes:** `archivo.header_json` = list, `archivo.estado` = 'hdrs_analizados'

### 2. Clasificación Automática
**Función:** `clasificar_headers_archivo_novedades()`

**Qué hace:**
- Busca mapeos `ConceptoRemuneracionNovedades` del cliente
- Compara headers del Excel con mapeos existentes (normalizado)
- Clasifica en: `headers_clasificados` y `headers_sin_clasificar`

**Por qué:**
- Automatizar mapeo de conceptos conocidos
- Identificar conceptos nuevos que necesitan mapeo manual

**Input:** `headers (list)`, `cliente_id`  
**Output:** `(headers_clasificados, headers_sin_clasificar)`  
**BD Changes:** `archivo.header_json` = dict, `archivo.estado` = 'clasificado' o 'clasif_pendiente'

### 3. Actualizar Empleados
**Función:** `actualizar_empleados_desde_novedades()`

**Qué hace:**
- Lee primeras 4 columnas del Excel
- Valida RUTs (ignora filas de totales, vacíos)
- Crea o actualiza `EmpleadoCierreNovedades`

**Por qué:**
- Registrar empleados con novedades en el cierre
- Base para asociar conceptos posteriormente

**Input:** `archivo_id`  
**Output:** `{empleados_creados, empleados_actualizados, filas_ignoradas}`  
**BD Changes:** Registros en `EmpleadoCierreNovedades`

### 4. Guardar Registros de Conceptos
**Función:** `guardar_registros_novedades()`

**Qué hace:**
- Lee Excel completo (columnas 5+)
- Para cada empleado y cada concepto:
  - Extrae valor del Excel
  - Crea `RegistroConceptoEmpleadoNovedades`

**Por qué:**
- Registrar valores de cada concepto para cada empleado
- Trazabilidad de novedades aplicadas

**Input:** `archivo_id`  
**Output:** `{registros_guardados, registros_sin_valor}`  
**BD Changes:** Registros en `RegistroConceptoEmpleadoNovedades`

---

## 🔧 CARACTERÍSTICAS TÉCNICAS

### Chunking Dinámico (Archivos Grandes)

```python
def calcular_chunk_size_dinamico(empleados_count):
    if empleados_count <= 50:
        return 25  # MODO SIMPLE (sin chunking)
    elif empleados_count <= 200:
        return 50
    elif empleados_count <= 500:
        return 100
    elif empleados_count <= 1000:
        return 150
    else:
        return 200
```

### Logging Dual

**TarjetaActivityLogNomina (User-facing):**
- `process_start`: Inicio de procesamiento
- `header_analysis`: Análisis de headers
- `classification_start`: Clasificación de headers
- `process_complete`: Procesamiento completado
- `validation_error`: Error de validación

**ActivityEvent (Audit trail):**
- `procesamiento_celery_iniciado`
- `analisis_headers_iniciado/exitoso/error`
- `clasificacion_headers_iniciada/exitosa/error`
- `actualizacion_empleados_iniciada/exitosa/error`
- `guardado_registros_iniciado/exitoso/error`
- `procesamiento_completado`
- `procesamiento_error`

### Validaciones

1. **RUT válido:** Ignora "total", NaN, vacíos (filas de totales Talana)
2. **Headers mínimos:** Al menos 5 columnas (4 empleado + 1 concepto)
3. **Estado del archivo:** Debe estar 'clasificado' para procesar
4. **Nombre archivo:** Formato estándar según validaciones del cliente

---

## 📊 RESULTADOS ESPERADOS

### Verificaciones (Estimadas: 6-7)

1. ✅ Archivo procesado sin errores
2. ✅ Task finalizada con SUCCESS
3. ✅ Empleados creados/actualizados correctamente
4. ✅ Registros de conceptos creados
5. ✅ Logging dual completo (TarjetaActivityLogNomina + ActivityEvent)
6. ✅ Estado final = 'procesado'
7. ✅ (Opcional) Headers clasificados correctamente

### Métricas Típicas

- **Empleados:** Variable (5-1000+)
- **Conceptos:** Variable (5-50)
- **Registros:** empleados × conceptos
- **Tiempo:** <1s (pocos) a varios minutos (miles)

---

## 🔗 DIFERENCIAS CON FLUJOS 3-5

| Aspecto | Flujos 3-5 (Archivos Analista) | Flujo 6 (Novedades) |
|---------|----------------------------------|---------------------|
| **ViewSet** | `ArchivoAnalistaUploadViewSet` | `ArchivoNovedadesUploadViewSet` |
| **Modelo** | `ArchivoAnalistaUpload` | `ArchivoNovedadesUpload` |
| **Task** | `procesar_archivo_analista_con_logging` | `procesar_archivo_novedades_con_logging` |
| **Tipo** | `tipo_archivo`: ingresos/finiquitos/incidencias | Modelo propio (sin tipo_archivo) |
| **Columnas** | Fijas (3-6 columnas) | Dinámicas (4 fijas + N conceptos) |
| **Complejidad** | Baja-Media | Alta (similar a Libro) |
| **Chunking** | No requiere | Sí (>50 filas) |
| **Clasificación** | No aplica | Sí (mapeo de conceptos) |

---

## 🎯 REUTILIZACIÓN DE ARQUITECTURA

### ✅ Patrones Compartidos (100% validados)

1. **Logging Dual:** TarjetaActivityLogNomina + ActivityEvent
2. **Chain Celery:** Análisis → Clasificación → Procesamiento
3. **Trazabilidad:** usuario_id propagado en todas las tasks
4. **Manejo de errores:** try-catch con logs detallados
5. **Validación de datos:** RUTs, valores nulos, formato

### ⚠️ Patrones Únicos de Novedades

1. **Clasificación automática de headers**
2. **Chunking dinámico según tamaño**
3. **Procesamiento en paralelo (CHORD)**
4. **Mapeo de conceptos cliente-específico**

---

## 💡 CONFIANZA EN LA ARQUITECTURA

**Expectativa de bugs:** 0

**Razones:**
- ✅ Sistema completo ya implementado (no es stub)
- ✅ Usa patrones validados 4 veces (Flujos 2-5)
- ✅ Logging dual probado y funcionando
- ✅ Chunking optimizado (basado en Libro Remuneraciones)
- ✅ Validaciones robustas (RUTs, valores, estado)

**Tiempo estimado de validación:** ~30 minutos
- 10 min: Generar Excel de prueba
- 10 min: Subir y procesar
- 10 min: Verificar resultados y documentar

---

## 🔗 RELACIONES CON OTROS FLUJOS

### Anterior
- **Flujo 5: Incidencias** - Mismo periodo mensual, diferentes datos

### Siguiente
- **Flujo 7: Verificación Discrepancias** - Compara Libro vs Movimientos vs Novedades

### Depende de
- **CierreNomina activo** (pre-requisito)
- **Mapeos ConceptoRemuneracionNovedades** (cliente configurado)

---

**Documentación completa:** ✅  
**Lista para validación:** ⏭️ Pendiente de ejecución
