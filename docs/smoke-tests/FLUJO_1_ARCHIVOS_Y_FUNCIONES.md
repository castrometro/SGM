# Flujo 1: Libro de Remuneraciones - Archivos y Funciones

## 📁 Frontend

### Página Principal
**Archivo:** `src/pages/Nomina/CierreDetalleNomina.jsx`

**Funciones:**
- `handleSubirLibro(file)` - Maneja la subida del archivo Excel
- `handleProcesarLibro()` - Dispara el procesamiento

### Componente de Progreso
**Archivo:** `src/pages/Nomina/CierreProgresoNomina.jsx`

**Funciones:**
- `pollLibroStatus()` - Polling del estado del libro cada 3s
- `renderEstadoLibro()` - Renderiza UI según estado

### API Client
**Archivo:** `src/api/nomina.js`

**Funciones:**
- `subirLibroRemuneraciones(formData)` → `POST /api/nomina/libros-remuneraciones/`
- `procesarLibroRemuneraciones(libroId)` → `POST /api/nomina/libros-remuneraciones/${libroId}/procesar/`

---

## 🔌 Backend API

### ViewSet
**Archivo:** `backend/nomina/views_libro_remuneraciones.py`

**Clase:** `LibroRemuneracionesUploadViewSet`

**Métodos:**
- `perform_create(serializer)` - Crea libro, valida archivo, registra ActivityEvent y dispara análisis
- `procesar(request, pk)` - Valida estado, dispara cadena de procesamiento

---

## ⚙️ Tareas Celery

### Archivo Principal
**Ubicación:** `backend/nomina/tasks_refactored/libro_remuneraciones.py`

### Tarea 1: Análisis de Headers
**Función:** `analizar_headers_libro_remuneraciones_con_logging(libro_id, usuario_id)`

**Proceso:**
1. `LibroRemuneracionesUpload.objects.get(id=libro_id)`
2. `pd.read_excel(libro.archivo.path)`
3. `libro.header_json = df.columns.tolist()`
4. `libro.estado = "analizado"`

**Queue:** `nomina_queue`

---

### Tarea 2: Clasificación de Headers
**Función:** `clasificar_headers_libro_remuneraciones_con_logging(result_anterior)`

**Proceso:**
1. Extrae `libro_id` del resultado anterior
2. Itera sobre `libro.header_json`
3. Busca coincidencias en `ConceptoRemuneracion.objects.filter()`
4. Crea `HeaderValorEmpleado` para cada match
5. `libro.estado = "clasificado"`

**Queue:** `nomina_queue`

---

### Tarea 3: Actualizar Empleados
**Función:** `actualizar_empleados_desde_libro_optimizado(libro_id, usuario_id)`

**Proceso:**
1. `pd.read_excel(libro.archivo.path)`
2. Valida columnas obligatorias Previred:
   - Año, Mes, Rut de la Empresa
   - Rut del Trabajador, Nombre
   - Apellido Paterno, Apellido Materno
3. `EmpleadoCierre.objects.update_or_create()` para cada fila
4. Retorna `{'libro_id': libro_id, 'empleados_creados': count}`

**Fallback:** `actualizar_empleados_desde_libro_util()` si falla optimizado

**Queue:** `nomina_queue`

---

### Tarea 4: Guardar Registros
**Función:** `guardar_registros_nomina_optimizado(result_anterior)`

**Proceso:**
1. Extrae `libro_id` del resultado anterior
2. `EmpleadoCierre.objects.filter(cierre=libro.cierre)`
3. `HeaderValorEmpleado.objects.filter(libro=libro)`
4. Lee Excel y extrae valores para cada empleado/concepto
5. `RegistroConceptoEmpleado.objects.bulk_create(registros)`
6. `libro.estado = "procesado"`

**Queue:** `nomina_queue`

---

## 🗄️ Modelos de Base de Datos

### Archivo de Modelos
**Ubicación:** `backend/nomina/models.py`

### Modelos Principales

**1. LibroRemuneracionesUpload**
- `id` (PK)
- `cierre` (FK → CierreNomina)
- `archivo` (FileField)
- `header_json` (JSONField)
- `estado` (CharField: pendiente/analizado/clasificado/procesando/procesado)

**2. EmpleadoCierre**
- `id` (PK)
- `cierre` (FK → CierreNomina)
- `rut` (CharField)
- `nombre` (CharField)
- `apellido_paterno` (CharField)
- `apellido_materno` (CharField)

**3. RegistroConceptoEmpleado**
- `id` (PK)
- `empleado` (FK → EmpleadoCierre)
- `concepto` (FK → ConceptoRemuneracion)
- `valor` (DecimalField)

**4. HeaderValorEmpleado**
- `id` (PK)
- `libro` (FK → LibroRemuneracionesUpload)
- `concepto` (FK → ConceptoRemuneracion)
- `nombre_header` (CharField)

**5. ConceptoRemuneracion**
- `id` (PK)
- `nombre_concepto` (CharField)
- `clasificacion` (CharField: haber/descuento/informacion)

---

## 🔄 Cadena de Ejecución

### Subida (Upload)
```
Frontend: handleSubirLibro()
    ↓
API Client: subirLibroRemuneraciones(formData)
    ↓
Backend ViewSet: LibroRemuneracionesUploadViewSet.perform_create()
    ↓
Celery: analizar_headers_libro_remuneraciones_con_logging.apply_async()
```

### Análisis y Clasificación (Automático)
```
Task 1: analizar_headers_libro_remuneraciones_con_logging
    ↓ (Chain)
Task 2: clasificar_headers_libro_remuneraciones_con_logging
```

### Procesamiento (Manual - Botón)
```
Frontend: handleProcesarLibro()
    ↓
API Client: procesarLibroRemuneraciones(libroId)
    ↓
Backend ViewSet: LibroRemuneracionesUploadViewSet.procesar()
    ↓
Celery Chain:
    Task 3: actualizar_empleados_desde_libro_optimizado
        ↓
    Task 4: guardar_registros_nomina_optimizado
```

---

## 📦 Utilidades

### Archivo
**Ubicación:** `backend/nomina/utils/LibroRemuneraciones.py`

### Funciones Auxiliares

**`actualizar_empleados_desde_libro_util(libro)`**
- Validación de columnas obligatorias
- Limpieza de empleados existentes
- Creación de EmpleadoCierre
- Validación de RUT

**`dividir_dataframe_empleados(archivo_path, chunk_size)`**
- Divide Excel en chunks para procesamiento paralelo
- Retorna lista de chunks

**`dividir_dataframe_conceptos(archivo_path, chunk_size)`**
- Divide conceptos en chunks
- Para procesamiento con Chord

---

## 🔀 Proxy de Tareas

### Archivo
**Ubicación:** `backend/nomina/tasks.py`

### Re-exportaciones
```python
from nomina.tasks_refactored.libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
)
```

---

## 📊 Estados del Libro

```
pendiente → analizado → clasificado → procesando → procesado
   ↑            ↑            ↑            ↑            ↑
   |            |            |            |            |
  Upload     Task 1       Task 2    Task 3 inicia  Task 4 completa
```

---

## 🎯 Archivos Clave por Capa

| Capa | Archivo | Propósito |
|------|---------|-----------|
| **Frontend** | `src/pages/Nomina/CierreDetalleNomina.jsx` | Página principal |
| **Frontend** | `src/pages/Nomina/CierreProgresoNomina.jsx` | UI de progreso |
| **Frontend** | `src/api/nomina.js` | API client |
| **Backend API** | `backend/nomina/views_libro_remuneraciones.py` | ViewSet endpoints |
| **Backend Models** | `backend/nomina/models.py` | Modelos de BD |
| **Backend Utils** | `backend/nomina/utils/LibroRemuneraciones.py` | Funciones auxiliares |
| **Celery Tasks** | `backend/nomina/tasks_refactored/libro_remuneraciones.py` | Tareas asíncronas |
| **Celery Proxy** | `backend/nomina/tasks.py` | Re-exportaciones |

---

**Total de funciones principales:** 8  
**Total de archivos involucrados:** 8  
**Total de modelos de BD:** 5
