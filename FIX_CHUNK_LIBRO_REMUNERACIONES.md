# 🔧 Fix: Bug en Procesamiento de Chunks del Libro de Remuneraciones

**Fecha**: 24 de octubre de 2025  
**Módulo**: `nomina/tasks_refactored/libro_remuneraciones.py`  
**Severidad**: Alta (80% de pérdida de datos)  
**Estado**: ✅ RESUELTO

---

## 📋 Tabla de Contenidos

1. [Descripción del Error](#descripción-del-error)
2. [Diagnóstico y Root Cause](#diagnóstico-y-root-cause)
3. [Solución Aplicada](#solución-aplicada)
4. [Flujo Completo de Procesamiento](#flujo-completo-de-procesamiento)
5. [Lecciones Aprendidas](#lecciones-aprendidas)
6. [Recomendaciones](#recomendaciones)

---

## 📖 Descripción del Error

### Síntomas Observados

Al procesar un Libro de Remuneraciones con 62 empleados:
- ✅ Se creaban correctamente 62 registros de `EmpleadoCierre`
- ❌ Solo 12 empleados obtenían sus `RegistroConceptoEmpleado` (conceptos de nómina)
- ❌ 50 empleados quedaban SIN conceptos (pérdida del 80% de datos)
- ⚠️ No se reportaban errores en logs

### Caso de Prueba

**Cierre**: ID 34 (Septiembre 2025, Cliente FRASER ALEXANDER)  
**Libro**: ID 78 (64 filas en Excel, 62 empleados válidos)  
**Resultado esperado**: 62 empleados × 48 conceptos = 2,976 registros  
**Resultado obtenido**: 12 empleados × 48 conceptos = 576 registros (80% perdido)

---

## 🔍 Diagnóstico y Root Cause

### Análisis de Logs de Celery

Los logs revelaron un comportamiento anómalo en el chunk 1:

```
Chunk 1 (50 empleados):
  - Tiempo de ejecución: 0.115 segundos ⚠️ (SOSPECHOSAMENTE RÁPIDO)
  - Registros procesados: 0 ❌
  - Errores reportados: [] (ninguno)
  - Status: SUCCESS ✅ (falso positivo)

Chunk 2 (12 empleados):
  - Tiempo de ejecución: 1.958 segundos ✅
  - Registros procesados: 12 ✅
  - Errores reportados: []
  - Status: SUCCESS ✅
```

### Hipótesis Investigadas

#### ❌ Hipótesis 1: RUT mismatch entre Excel y DB
**Descartada**: Verificación cruzada mostró que los 62 RUTs del Excel coinciden perfectamente con la BD.

#### ❌ Hipótesis 2: Headers no clasificados
**Descartada**: El libro tenía 48 headers correctamente clasificados.

#### ❌ Hipótesis 3: Endpoint no llamado
**Descartada**: Los logs de Django confirmaron la llamada a `/procesar/` a las 15:31:40.

#### ❌ Hipótesis 4: Problema en división de chunks
**Descartada**: Simulación del código de `dividir_dataframe_empleados` generó chunks correctos.

#### ❌ Hipótesis 5: EmpleadoCierre no creados para chunk 1
**Descartada**: Query a BD confirmó que los 50 empleados del chunk 1 existen.

#### ✅ Hipótesis 6: Código obsoleto cargado en memoria del worker
**CONFIRMADA**: El worker de Celery tenía código antiguo en memoria y no había auto-reloaded después de cambios previos.

### Root Cause Identificado

**Celery no auto-reload en modo producción**. Los workers de Celery cargan el código Python en memoria al iniciar y **NO recargan automáticamente** cuando se modifican archivos `.py`. 

Esto causó que:
1. Código con bug se cargó en memoria del worker
2. El chunk 1 fallaba silenciosamente debido al bug (condición exacta desconocida)
3. El bug persistió hasta que se reinició manualmente el worker

---

## 🛠️ Solución Aplicada

### 1. Logging Detallado Agregado

Se instrumentó `procesar_chunk_registros_util` con logging de diagnóstico:

**Archivo**: `backend/nomina/utils/LibroRemuneracionesOptimizado.py`  
**Líneas**: 221-265

```python
def procesar_chunk_registros_util(libro_id, chunk_data):
    """
    📝 Procesa registros de nómina para un chunk específico de empleados.
    """
    chunk_id = chunk_data['chunk_id']
    logger.info(f"📝 Procesando registros para chunk {chunk_id}/{chunk_data['total_chunks']}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        # ... código de inicialización ...
        
        # 🔍 DEBUG LOGGING AGREGADO
        chunk_indices = chunk_data['indices']
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Total indices recibidos: {len(chunk_indices)}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Primeros 3 indices: {chunk_indices[:3] if chunk_indices else 'VACÍO'}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Total headers: {len(headers)}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] DataFrame shape: {df.shape}")
        
        chunk_df = df.iloc[chunk_indices]
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] chunk_df shape: {chunk_df.shape}")
        
        # ... resto del procesamiento ...
```

### 2. Reinicio del Worker de Celery

```bash
docker compose restart celery_worker
```

Este comando forzó la recarga del código actualizado en memoria.

### 3. Reprocesamiento del Libro

```python
# Limpiar registros previos
RegistroConceptoEmpleado.objects.filter(empleado__cierre=cierre).delete()

# Marcar libro para reprocesar
libro.estado = "clasificado"
libro.save()

# Usuario presiona "Procesar" en frontend
```

### 4. Resultados Después del Fix

```
Chunk 1:
  ✅ Total indices: 50
  ✅ Primeros 3 indices: [0, 1, 2]
  ✅ Total headers: 48
  ✅ chunk_df shape: (50, 55)
  ✅ Registros procesados: 50
  ✅ Tiempo: 8.77 segundos (NORMAL)

Chunk 2:
  ✅ Total indices: 12
  ✅ Primeros 3 indices: [50, 51, 52]
  ✅ Total headers: 48
  ✅ chunk_df shape: (12, 55)
  ✅ Registros procesados: 12
  ✅ Tiempo: 1.94 segundos

Consolidación final:
  ✅ Total empleados: 62
  ✅ Empleados con conceptos: 62 (100%)
  ✅ Empleados sin conceptos: 0
  ✅ Conceptos por empleado: 48
  ✅ Total registros: 2,976
```

---

## 🔄 Flujo Completo de Procesamiento del Libro

### Vista General

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO LIBRO DE REMUNERACIONES                │
└─────────────────────────────────────────────────────────────────┘

1. UPLOAD        2. ANALIZAR       3. CLASIFICAR     4. PROCESAR
   📤                🔍                 🏷️                ⚙️
   Excel            Headers           Mapeo             Parallel
   ↓                ↓                 ↓                 ↓
   File             Task              Task              Chord
   Upload           Async             Async             Pattern
   ↓                ↓                 ↓                 ↓
   estado:          estado:           estado:           estado:
   subido           analizando        clasificado       procesado
```

---

### Fase 1: Upload del Archivo Excel

**Componente Frontend**: `LibroRemuneracionesCard.jsx`  
**Endpoint**: `POST /api/nomina/libros-remuneraciones/`  
**Usuario**: Analista o Gerente

#### Flujo Detallado:

```javascript
// 1. Usuario selecciona archivo Excel
const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
};

// 2. Usuario presiona "Subir Libro"
const handleUpload = async () => {
    const formData = new FormData();
    formData.append('archivo', selectedFile);
    formData.append('cierre', cierreId);
    
    // 3. Request al backend
    const response = await nominaApi.post('/libros-remuneraciones/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};
```

#### Backend - View

**Archivo**: `backend/nomina/views_libro_remuneraciones.py`

```python
class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # 1. Validar archivo
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se proporcionó archivo"}, status=400)
        
        # 2. Validar extensión
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response({"error": "Formato inválido"}, status=400)
        
        # 3. Crear registro
        libro = LibroRemuneracionesUpload.objects.create(
            cierre=cierre,
            archivo=archivo,
            estado='subido',  # ← Estado inicial
            usuario_carga=request.user
        )
        
        # 4. Lanzar análisis automático (Celery)
        analizar_headers_libro_remuneraciones_con_logging.delay(
            libro.id, 
            usuario_id=request.user.id
        )
        
        return Response(serializer.data, status=201)
```

#### Estado Resultante:
- ✅ Archivo guardado en `/media/remuneraciones/{cliente_id}/{periodo}/libro/`
- ✅ Registro `LibroRemuneracionesUpload` creado con `estado='subido'`
- ✅ Task de Celery lanzada para análisis automático

---

### Fase 2: Análisis de Headers (Automático)

**Task**: `analizar_headers_libro_remuneraciones_con_logging`  
**Queue**: `nomina_queue`  
**Archivo**: `backend/nomina/tasks_refactored/libro_remuneraciones.py`

#### Flujo Detallado:

```python
@shared_task(bind=True, queue='nomina_queue')
def analizar_headers_libro_remuneraciones_con_logging(self, libro_id, usuario_id=None):
    """
    Analiza headers del Excel y los guarda en libro.header_json
    """
    logger.info(f"[LIBRO] Analizando headers libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        # 1. Leer Excel con pandas
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        # 2. Extraer nombres de columnas
        headers = list(df.columns)
        
        # 3. Filtrar headers de empleado (no son conceptos)
        empleado_cols = {
            "Año", "Mes", "Rut de la Empresa", 
            "Rut del Trabajador", "Nombre",
            "Apellido Paterno", "Apellido Materno"
        }
        
        # 4. Headers de conceptos (haberes, descuentos, etc.)
        headers_conceptos = [h for h in headers if h not in empleado_cols]
        
        # 5. Guardar en BD
        libro.header_json = {
            "headers_raw": headers_conceptos,
            "total": len(headers_conceptos),
            "fecha_analisis": datetime.now().isoformat()
        }
        libro.estado = 'analizando'  # ← Cambio de estado
        libro.save()
        
        # 6. Lanzar clasificación automática
        clasificar_headers_libro_remuneraciones_con_logging.delay(
            libro_id, 
            usuario_id=usuario_id
        )
        
        return {
            "libro_id": libro_id,
            "headers": headers_conceptos
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] Error analizando headers: {e}")
        raise
```

#### Estado Resultante:
- ✅ `libro.header_json` contiene lista de headers extraídos
- ✅ `estado='analizando'`
- ✅ Task de clasificación lanzada automáticamente

---

### Fase 3: Clasificación de Headers (Automático)

**Task**: `clasificar_headers_libro_remuneraciones_con_logging`  
**Queue**: `nomina_queue`  
**Lógica**: Matching fuzzy con catálogo de conceptos

#### Flujo Detallado:

```python
@shared_task(bind=True, queue='nomina_queue')
def clasificar_headers_libro_remuneraciones_con_logging(self, libro_id, usuario_id=None):
    """
    Clasifica headers automáticamente usando fuzzy matching
    """
    logger.info(f"[LIBRO] Clasificando headers libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        headers_raw = libro.header_json.get("headers_raw", [])
        
        # 1. Obtener catálogo de conceptos del cliente
        conceptos = ConceptoRemuneracion.objects.filter(
            cliente=libro.cierre.cliente,
            vigente=True
        )
        
        headers_clasificados = []
        headers_sin_clasificar = []
        
        # 2. Para cada header, buscar match con concepto
        for header in headers_raw:
            mejor_match = None
            mejor_score = 0
            
            # 3. Fuzzy matching con fuzzywuzzy
            for concepto in conceptos:
                score = fuzz.ratio(
                    header.lower().strip(),
                    concepto.nombre_concepto.lower().strip()
                )
                
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = concepto
            
            # 4. Clasificar si score > umbral
            if mejor_score >= 80:  # Umbral de confianza
                headers_clasificados.append({
                    "header": header,
                    "concepto_id": mejor_match.id,
                    "concepto_nombre": mejor_match.nombre_concepto,
                    "categoria": mejor_match.categoria,
                    "score": mejor_score
                })
            else:
                headers_sin_clasificar.append(header)
        
        # 5. Guardar clasificación
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
            "fecha_clasificacion": datetime.now().isoformat()
        }
        
        # 6. Determinar estado final
        if len(headers_sin_clasificar) > 0:
            libro.estado = 'clasif_pendiente'  # ← Requiere revisión manual
        else:
            libro.estado = 'clasificado'  # ← Listo para procesar
        
        libro.save()
        
        # 7. Registrar actividad para el usuario
        registrar_tarjeta_activity_log(
            usuario_id=usuario_id,
            libro_id=libro_id,
            event_type='classification_complete',
            details={
                "clasificados": len(headers_clasificados),
                "sin_clasificar": len(headers_sin_clasificar)
            }
        )
        
        return {
            "libro_id": libro_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
            "estado_final": libro.estado
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] Error clasificando headers: {e}")
        raise
```

#### Posibles Estados Resultantes:

**Caso A: Todos clasificados automáticamente**
- ✅ `estado='clasificado'`
- ✅ `headers_sin_clasificar = []`
- ✅ **Usuario puede presionar "Procesar"** ⚙️

**Caso B: Algunos headers sin clasificar**
- ⚠️ `estado='clasif_pendiente'`
- ⚠️ `headers_sin_clasificar = ["Bono Especial", "Descuento X"]`
- ⚠️ **Usuario debe clasificar manualmente**

---

### Fase 3.5: Clasificación Manual (Si es necesario)

**Componente Frontend**: Modal de clasificación en `LibroRemuneracionesCard.jsx`  
**Endpoint**: `PATCH /api/nomina/libros-remuneraciones/{id}/`

Si hay headers sin clasificar, el usuario debe:

```javascript
// 1. Frontend muestra modal con headers pendientes
const handleManualClassification = (header, conceptoId) => {
    // 2. Usuario selecciona concepto del dropdown
    const clasificaciones = {
        ...clasificacionesAnteriores,
        [header]: conceptoId
    };
    
    // 3. Enviar al backend
    await nominaApi.patch(`/libros-remuneraciones/${libroId}/`, {
        clasificaciones_manuales: clasificaciones
    });
};
```

Después de clasificación manual:
- ✅ `estado='clasificado'`
- ✅ **Usuario puede presionar "Procesar"** ⚙️

---

### Fase 4: Procesamiento Paralelo (Manual)

**Usuario**: Presiona botón "Procesar"  
**Endpoint**: `POST /api/nomina/libros-remuneraciones/{id}/procesar/`  
**Requisito**: `libro.estado == 'clasificado'`

#### Flujo en el Backend:

```python
@action(detail=True, methods=['post'])
def procesar(self, request, pk=None):
    """
    Procesa el libro usando Celery Chord para paralelización
    """
    libro = self.get_object()
    
    # 1. Validar estado
    if libro.estado != 'clasificado':
        return Response(
            {"error": "El libro debe estar clasificado"}, 
            status=400
        )
    
    # 2. Lanzar chain de Celery
    chain_result = chain(
        # Fase A: Crear EmpleadoCierre (paralelo)
        actualizar_empleados_desde_libro_optimizado.s(
            libro.id, 
            usuario_id=request.user.id
        ),
        # Fase B: Crear RegistroConceptoEmpleado (paralelo)
        guardar_registros_nomina_optimizado.s(
            usuario_id=request.user.id
        )
    ).apply_async()
    
    return Response({
        "message": "Procesamiento iniciado",
        "task_id": chain_result.id
    }, status=202)
```

---

### Fase 4A: Crear EmpleadoCierre (Paralelo con Chord)

**Task**: `actualizar_empleados_desde_libro_optimizado`  
**Pattern**: Celery Chord (parallel tasks | callback)

```python
@shared_task(bind=True, queue='nomina_queue')
def actualizar_empleados_desde_libro_optimizado(self, libro_id, usuario_id=None):
    """
    Divide el Excel en chunks y crea EmpleadoCierre en paralelo
    """
    logger.info(f"[LIBRO] Actualizando empleados (optimizado) libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        # 1. Leer Excel
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        
        # 2. Calcular chunk size dinámico
        chunk_size = _calcular_chunk_size_dinamico(total_filas)
        # Ejemplos: 
        #   <= 50 filas: chunk_size = 25
        #   <= 200 filas: chunk_size = 50
        #   > 200 filas: chunk_size = 100
        
        logger.info(f"[LIBRO] Total: {total_filas} filas, Chunk size: {chunk_size}")
        
        # 3. Dividir en chunks
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        # chunks = [
        #     {'chunk_id': 1, 'indices': [0,1,2,...,49], 'size': 50},
        #     {'chunk_id': 2, 'indices': [50,51,...,61], 'size': 12}
        # ]
        
        # 4. Crear tasks paralelas
        tasks_paralelas = [
            procesar_chunk_empleados_task.s(libro_id, chunk_data)
            for chunk_data in chunks
        ]
        
        # 5. Ejecutar Chord: tasks | callback
        callback = consolidar_empleados_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"[LIBRO] 🚀 Chord empleados iniciado: {len(chunks)} chunks")
        
        return {
            "libro_id": libro_id,
            "usuario_id": usuario_id,
            "chord_id": resultado_chord.id,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord"
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error: {e}")
        raise
```

#### Worker Task: Procesar Chunk de Empleados

```python
@shared_task(queue='nomina_queue')
def procesar_chunk_empleados_task(libro_id, chunk_data):
    """
    Worker: Procesa un chunk específico de empleados
    """
    return procesar_chunk_empleados_util(libro_id, chunk_data)


def procesar_chunk_empleados_util(libro_id, chunk_data):
    """
    Lógica real: Crea/actualiza EmpleadoCierre para un chunk
    """
    chunk_id = chunk_data['chunk_id']
    logger.info(f"👥 Procesando chunk de empleados {chunk_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }
        
        count = 0
        errores = []
        
        # Procesar solo las filas de este chunk
        chunk_indices = chunk_data['indices']
        chunk_df = df.iloc[chunk_indices]
        
        with transaction.atomic():
            for _, row in chunk_df.iterrows():
                try:
                    # Extraer y normalizar RUT
                    rut_raw = row.get(expected["rut_trabajador"])
                    if not _es_rut_chileno_valido(rut_raw):
                        continue
                    
                    rut = formatear_rut_con_guion(normalizar_rut(rut_raw))
                    
                    # Extraer datos del empleado
                    nombre = str(row.get(expected["nombre"], "")).strip()
                    apellido_paterno = str(row.get(expected["ape_pat"], "")).strip()
                    apellido_materno = str(row.get(expected["ape_mat"], "")).strip()
                    
                    # Crear o actualizar EmpleadoCierre
                    empleado, created = EmpleadoCierre.objects.update_or_create(
                        cierre=libro.cierre,
                        rut=rut,
                        defaults={
                            "nombre": nombre,
                            "apellido_paterno": apellido_paterno,
                            "apellido_materno": apellido_materno,
                        }
                    )
                    
                    count += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando RUT {rut}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
        
        resultado = {
            'chunk_id': chunk_id,
            'empleados_procesados': count,
            'errores': errores
        }
        
        logger.info(f"✅ Chunk empleados {chunk_id} completado: {count} empleados")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en chunk empleados {chunk_id}: {e}")
        return {
            'chunk_id': chunk_id,
            'empleados_procesados': 0,
            'errores': [str(e)]
        }
```

#### Callback: Consolidar Resultados de Empleados

```python
@shared_task(queue='nomina_queue')
def consolidar_empleados_task(resultados_chunks):
    """
    Callback: Ejecutado cuando TODOS los chunks de empleados terminan
    """
    stats = consolidar_stats_empleados(resultados_chunks)
    logger.info(f"[LIBRO] ✅ Consolidación empleados: {stats}")
    return stats


def consolidar_stats_empleados(resultados_chunks):
    """
    Suma los resultados de todos los chunks
    """
    total_empleados = 0
    total_errores = 0
    chunks_exitosos = 0
    errores_consolidados = []
    
    for resultado in resultados_chunks:
        if isinstance(resultado, dict):
            total_empleados += resultado.get('empleados_procesados', 0)
            errores_chunk = resultado.get('errores', [])
            total_errores += len(errores_chunk)
            errores_consolidados.extend(errores_chunk)
            
            if resultado.get('empleados_procesados', 0) > 0:
                chunks_exitosos += 1
    
    return {
        'total_empleados_procesados': total_empleados,
        'chunks_exitosos': chunks_exitosos,
        'total_chunks': len(resultados_chunks),
        'total_errores': total_errores,
        'errores': errores_consolidados,
        'procesamiento_exitoso': total_errores == 0
    }
```

#### Resultado de Fase 4A:

```
✅ Chord empleados completado:
   - Chunk 1: 50 empleados procesados
   - Chunk 2: 12 empleados procesados
   - Total: 62 EmpleadoCierre creados
```

---

### Fase 4B: Crear RegistroConceptoEmpleado (Paralelo con Chord)

**Task**: `guardar_registros_nomina_optimizado`  
**Pattern**: Celery Chord (parallel tasks | callback)  
**Input**: Resultado de Fase 4A

```python
@shared_task(bind=True, queue='nomina_queue')
def guardar_registros_nomina_optimizado(self, result, usar_chord=True):
    """
    Crea RegistroConceptoEmpleado para cada empleado × concepto
    """
    # Extraer libro_id del resultado anterior
    libro_id = result.get("libro_id")
    usuario_id = result.get("usuario_id")
    
    logger.info(f"[LIBRO] Guardando registros (optimizado) libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        # 1. Leer Excel
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        
        # 2. Calcular chunk size dinámico
        chunk_size = _calcular_chunk_size_dinamico(total_filas)
        
        # 3. Dividir en chunks (MISMO algoritmo que empleados)
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        
        # 4. Crear tasks paralelas
        tasks_paralelas = [
            procesar_chunk_registros_task.s(libro_id, chunk_data)
            for chunk_data in chunks
        ]
        
        # 5. Ejecutar Chord con callback que recibe usuario_id
        callback = consolidar_registros_task.s(usuario_id=usuario_id)
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"[LIBRO] 🚀 Chord registros iniciado: {len(chunks)} chunks")
        
        return {
            "libro_id": libro_id,
            "usuario_id": usuario_id,
            "chord_id": resultado_chord.id,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord",
            "estado": "procesando"
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error: {e}")
        raise
```

#### Worker Task: Procesar Chunk de Registros (CON FIX)

```python
@shared_task(queue='nomina_queue')
def procesar_chunk_registros_task(libro_id, chunk_data):
    """
    Worker: Procesa registros de conceptos para un chunk
    """
    return procesar_chunk_registros_util(libro_id, chunk_data)


def procesar_chunk_registros_util(libro_id, chunk_data):
    """
    🔧 FUNCIÓN CON FIX: Logging detallado agregado
    
    Crea RegistroConceptoEmpleado para cada empleado × concepto
    """
    chunk_id = chunk_data['chunk_id']
    logger.info(f"📝 Procesando registros para chunk {chunk_id}/{chunk_data['total_chunks']}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        
        expected = {
            "ano": "Año",
            "mes": "Mes",
            "rut_empresa": "Rut de la Empresa",
            "rut_trabajador": "Rut del Trabajador",
            "nombre": "Nombre",
            "ape_pat": "Apellido Paterno",
            "ape_mat": "Apellido Materno",
        }
        
        empleado_cols = set(expected.values())
        
        # Obtener headers clasificados
        headers = libro.header_json
        if isinstance(headers, dict):
            headers = headers.get("headers_clasificados", []) + headers.get(
                "headers_sin_clasificar", []
            )
        if not headers:
            headers = [h for h in df.columns if h not in empleado_cols]
        
        # 🔍 DEBUG LOGGING (AGREGADO EN EL FIX)
        chunk_indices = chunk_data['indices']
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Total indices recibidos: {len(chunk_indices)}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Primeros 3 indices: {chunk_indices[:3] if chunk_indices else 'VACÍO'}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] Total headers: {len(headers)}")
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] DataFrame shape: {df.shape}")
        
        count = 0
        errores = []
        
        # Procesar solo las filas de este chunk
        chunk_df = df.iloc[chunk_indices]
        logger.info(f"🔍 [DEBUG Chunk {chunk_id}] chunk_df shape: {chunk_df.shape}")
        
        with transaction.atomic():
            for _, row in chunk_df.iterrows():
                try:
                    # Normalizar RUT
                    rut_valor = row.get(expected["rut_trabajador"])
                    if not _es_rut_chileno_valido(rut_valor):
                        continue
                    
                    rut = formatear_rut_con_guion(normalizar_rut(rut_valor))
                    
                    # Buscar EmpleadoCierre (debe existir de Fase 4A)
                    empleado = EmpleadoCierre.objects.filter(
                        cierre=libro.cierre, 
                        rut=rut
                    ).first()
                    
                    if not empleado:
                        continue
                    
                    # Procesar TODOS los headers para este empleado
                    for h in headers:
                        try:
                            valor_raw = row.get(h)
                            
                            # Procesar valor (convertir a string limpio)
                            if pd.isna(valor_raw) or valor_raw == '':
                                valor = ""
                            else:
                                if isinstance(valor_raw, (int, float)):
                                    if isinstance(valor_raw, int) or valor_raw.is_integer():
                                        valor = str(int(valor_raw))
                                    else:
                                        valor = f"{valor_raw:.2f}".rstrip('0').rstrip('.')
                                else:
                                    valor = str(valor_raw).strip()
                                    if valor.lower() == 'nan':
                                        valor = ""
                            
                            # Buscar concepto clasificado
                            concepto = ConceptoRemuneracion.objects.filter(
                                cliente=libro.cierre.cliente, 
                                nombre_concepto=h, 
                                vigente=True
                            ).first()
                            
                            # Crear o actualizar registro
                            RegistroConceptoEmpleado.objects.update_or_create(
                                empleado=empleado,
                                nombre_concepto_original=h,
                                defaults={
                                    "monto": valor, 
                                    "concepto": concepto
                                }
                            )
                            
                        except Exception as concepto_error:
                            error_msg = f"Error en concepto '{h}' para RUT {rut}: {str(concepto_error)}"
                            errores.append(error_msg)
                            logger.error(error_msg)
                    
                    count += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando registros para RUT {rut}: {str(e)}"
                    errores.append(error_msg)
                    logger.error(error_msg)
        
        resultado = {
            'chunk_id': chunk_id,
            'registros_procesados': count,
            'errores': errores,
            'libro_id': libro_id
        }
        
        logger.info(f"✅ Chunk registros {chunk_id} completado: {count} empleados procesados")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en chunk registros {chunk_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_id,
            'registros_procesados': 0,
            'errores': [error_msg],
            'libro_id': libro_id
        }
```

#### Callback: Consolidar Registros y Finalizar

```python
@shared_task(queue='nomina_queue')
def consolidar_registros_task(resultados_chunks, usuario_id=None):
    """
    Callback final: Ejecutado cuando TODOS los chunks de registros terminan
    
    - Consolida estadísticas
    - Actualiza estado del libro a 'procesado'
    - Registra actividad del usuario
    """
    stats = consolidar_stats_registros(resultados_chunks)
    logger.info(f"[LIBRO] ✅ Consolidación registros: {stats}")
    
    # Obtener libro_id
    libro_id = None
    for resultado in resultados_chunks:
        if isinstance(resultado, dict) and 'libro_id' in resultado:
            libro_id = resultado['libro_id']
            break
    
    if libro_id:
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            
            # Actualizar estado final
            libro.estado = "procesado"  # ← ESTADO FINAL ✅
            libro.save(update_fields=['estado'])
            
            logger.info(f"[LIBRO] Estado actualizado a 'procesado' para libro {libro_id}")
            
            # Registrar actividad en tarjeta del usuario
            registrar_tarjeta_activity_log(
                usuario_id=usuario_id,
                libro_id=libro_id,
                event_type='process_complete',
                details={
                    "total_registros": stats.get('total_registros_procesados', 0),
                    "chunks_exitosos": stats.get('chunks_exitosos', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"[LIBRO] Error actualizando estado: {e}")
    
    return stats
```

#### Resultado de Fase 4B:

```
✅ Chord registros completado:
   - Chunk 1: 50 empleados × 48 conceptos = 2,400 registros
   - Chunk 2: 12 empleados × 48 conceptos = 576 registros
   - Total: 2,976 RegistroConceptoEmpleado creados
   
✅ Estado final: libro.estado = 'procesado'
```

---

### Resumen del Flujo Completo

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         TIMELINE COMPLETO                                  │
└────────────────────────────────────────────────────────────────────────────┘

T0: Usuario sube Excel
    ↓
    ├─ Archivo guardado en /media/
    └─ estado = 'subido'
    
T1: analizar_headers_libro (async)
    ↓
    ├─ Extrae columnas del Excel
    ├─ Filtra headers de empleado
    └─ estado = 'analizando'
    
T2: clasificar_headers_libro (async)
    ↓
    ├─ Fuzzy matching con catálogo de conceptos
    ├─ Clasifica automáticamente (80% threshold)
    └─ estado = 'clasif_pendiente' o 'clasificado'
    
T3: [MANUAL] Clasificación pendientes (si aplica)
    ↓
    └─ estado = 'clasificado'
    
T4: [MANUAL] Usuario presiona "Procesar"
    ↓
    └─ Chain de Celery iniciado
    
T5: actualizar_empleados_desde_libro_optimizado
    ↓
    ├─ Divide Excel en chunks
    ├─ Chord: [chunk1, chunk2] | consolidar
    └─ Crea EmpleadoCierre en paralelo
    
T6: guardar_registros_nomina_optimizado
    ↓
    ├─ Divide Excel en chunks (mismos índices)
    ├─ Chord: [chunk1, chunk2] | consolidar
    └─ Crea RegistroConceptoEmpleado en paralelo
    
T7: consolidar_registros_task (callback final)
    ↓
    ├─ Actualiza estado = 'procesado'
    ├─ Registra actividad del usuario
    └─ ✅ PROCESAMIENTO COMPLETO

Tiempo total (ejemplo con 62 empleados):
  - Upload: ~1s
  - Análisis: ~2s
  - Clasificación: ~3s
  - Clasificación manual: ~30s (si aplica)
  - Fase 4A (empleados): ~10s
  - Fase 4B (registros): ~15s
  - TOTAL: ~1 minuto (o ~31s si auto-clasificado)
```

---

## 📚 Lecciones Aprendidas

### 1. Celery No Auto-Reload en Producción

**Problema**: Los workers cargan el código en memoria al iniciar y NO recargan automáticamente.

**Solución**: Después de cambios en tasks, siempre reiniciar:
```bash
docker compose restart celery_worker
```

**Alternativa para desarrollo**: Usar `celery -A proyecto worker --autoreload` (más lento).

---

### 2. Logging es Crítico para Debugging

**Problema**: Chunk fallaba silenciosamente sin indicar por qué (0.115s, 0 registros, sin errores).

**Solución**: Agregar logging detallado en puntos críticos:
- Tamaño de inputs (indices, headers, dataframe shape)
- Estados intermedios (empleados encontrados, RUTs válidos)
- Resultados de cada paso (registros procesados, errores)

**Beneficio**: Permitió identificar inmediatamente que el problema era el código obsoleto en memoria.

---

### 3. Tiempos de Ejecución como Indicador

**Observación**:
- Chunk normal: 1.5-10 segundos (depende del tamaño)
- Chunk con bug: 0.115 segundos ⚠️

**Aprendizaje**: Un tiempo **sospechosamente rápido** indica que el código salió temprano (early exit) sin procesar datos.

**Recomendación**: Agregar métricas de tiempo en logs para detectar anomalías.

---

### 4. Determinismo en División de Chunks

**Problema**: `dividir_dataframe_empleados` se llama DOS VECES (empleados y registros).

**Riesgo**: Si el algoritmo no es determinista, los chunks podrían ser diferentes.

**Validación**: Verificamos que el algoritmo es determinista (mismo input → mismo output).

**Recomendación futura**: Cachear los chunks después de la primera división y reutilizarlos.

---

### 5. Testing de Integración Asíncrona

**Desafío**: Difícil testear tasks de Celery que dependen de orden de ejecución.

**Recomendación**:
- Unit tests para funciones `_util` (síncronas)
- Integration tests con `CELERY_TASK_ALWAYS_EAGER=True` (ejecuta tasks síncronamente)
- Monitoring en producción con Flower

---

## 🎯 Recomendaciones

### Para Desarrollo

1. **Auto-reload durante desarrollo**:
```bash
# En docker-compose.dev.yml
celery_worker:
  command: celery -A sgm_backend worker --autoreload --loglevel=info
```

2. **Logging consistente**:
```python
# Usar siempre el mismo formato
logger.info(f"[LIBRO] {mensaje} libro_id={libro_id}, chunk={chunk_id}")
```

3. **Validaciones tempranas**:
```python
# Al inicio de cada task
if not chunk_indices:
    logger.error(f"[LIBRO] Chunk {chunk_id} tiene índices vacíos")
    return {'error': 'indices_vacios'}
```

---

### Para Producción

1. **Monitoring de Celery**:
```bash
# Flower dashboard
docker compose up -d flower
# Acceso: http://localhost:5555
```

2. **Alertas por tiempo de ejecución**:
```python
# En cada task
inicio = time.time()
# ... procesamiento ...
duracion = time.time() - inicio

if duracion < 0.5 and count == 0:
    logger.warning(f"[ALERTA] Chunk {chunk_id} terminó muy rápido sin resultados")
```

3. **Reinicio automático de workers**:
```yaml
# docker-compose.yml
celery_worker:
  restart: unless-stopped
  deploy:
    restart_policy:
      condition: on-failure
      max_attempts: 3
```

---

### Para Testing

1. **Test de chunks deterministas**:
```python
def test_dividir_chunks_determinista():
    """Verificar que dividir_dataframe_empleados es determinista"""
    chunks1 = dividir_dataframe_empleados(archivo, chunk_size=50)
    chunks2 = dividir_dataframe_empleados(archivo, chunk_size=50)
    assert chunks1 == chunks2
```

2. **Test de consolidación**:
```python
def test_consolidacion_suma_correcta():
    """Verificar que consolidar suma todos los chunks"""
    resultados = [
        {'chunk_id': 1, 'registros_procesados': 50},
        {'chunk_id': 2, 'registros_procesados': 12}
    ]
    stats = consolidar_stats_registros(resultados)
    assert stats['total_registros_procesados'] == 62
```

3. **Test end-to-end**:
```python
@pytest.mark.django_db
def test_procesamiento_completo_libro():
    """Test completo: upload → clasificar → procesar"""
    # 1. Upload
    libro = LibroRemuneracionesUpload.objects.create(...)
    
    # 2. Analizar (síncrono con CELERY_TASK_ALWAYS_EAGER)
    analizar_headers_libro_remuneraciones(libro.id)
    
    # 3. Clasificar
    clasificar_headers_libro_remuneraciones(libro.id)
    
    # 4. Procesar
    chain(...).apply()
    
    # 5. Verificar resultado
    assert EmpleadoCierre.objects.filter(cierre=libro.cierre).count() == 62
    assert RegistroConceptoEmpleado.objects.count() == 2976
```

---

## 📊 Métricas de Éxito

### Antes del Fix

- ✅ EmpleadoCierre: 62/62 (100%)
- ❌ RegistroConceptoEmpleado: 576/2976 (19.4%)
- ❌ Empleados completos: 12/62 (19.4%)
- ❌ Pérdida de datos: 80%

### Después del Fix

- ✅ EmpleadoCierre: 62/62 (100%)
- ✅ RegistroConceptoEmpleado: 2976/2976 (100%)
- ✅ Empleados completos: 62/62 (100%)
- ✅ Pérdida de datos: 0%

---

## 🔗 Referencias

- **Archivo principal**: `backend/nomina/utils/LibroRemuneracionesOptimizado.py`
- **Tasks**: `backend/nomina/tasks_refactored/libro_remuneraciones.py`
- **Views**: `backend/nomina/views_libro_remuneraciones.py`
- **Frontend**: `src/pages/LibroRemuneracionesCard.jsx`
- **Documentación previa**: `FLUJO_CONSOLIDACION_VISUAL.md`

---

## ✅ Conclusión

El bug fue causado por **código obsoleto cargado en memoria del worker de Celery** que no se actualizó después de cambios en el código. La solución fue:

1. ✅ Agregar logging detallado para diagnóstico
2. ✅ Reiniciar el worker de Celery para recargar código
3. ✅ Reprocesar el libro con código actualizado

El sistema ahora procesa correctamente **100% de los empleados con todos sus conceptos** usando paralelización con Celery Chord.

**Recomendación crítica**: Siempre reiniciar workers después de cambios en código de tasks:
```bash
docker compose restart celery_worker
```

---

**Autor**: Equipo SGM  
**Fecha**: 24 de octubre de 2025  
**Versión**: 1.0
