# Fixes de tareas Celery

Fecha: 2025-09-26

## Objetivo
Documentar los fixes y mejoras detectados en el pipeline de procesamiento de nómina con Celery (modos clásico y optimizado), priorizados y con criterios de aceptación.

## Resumen de hallazgos clave
- Concurrencia efectiva: se observan 3 workers activos para la cola de nómina (ForkPoolWorker-1/2/3) procesando en paralelo.
- Solapamiento de chords: en modo optimizado, el chord de registros arranca mientras aún corre el chord de empleados (compiten por los mismos 3 workers).
- Diferencia de semántica entre modos: clásico hace REPLACE (limpia y recrea), optimizado usa update_or_create (puede dejar datos obsoletos si no hay pre-limpieza).
- Manejo de estados/errores: riesgo de quedar en "procesando" o de no reflejar errores parciales por chunk.
- Bugs menores localizados en las tareas (duplicado de raise; return inalcanzable con variable no definida).

## Fixes prioritarios (bloqueantes)

1) Encadenar chords para orden estricto (si se requiere)
- Descripción: Garantizar que el chord de registros inicie solo cuando el chord de empleados haya finalizado su consolidación (y el libro esté listo para esa fase).
- Archivos involucrados:
  - `backend/nomina/tasks.py` (funciones: `actualizar_empleados_desde_libro_optimizado`, `guardar_registros_nomina_optimizado`, consolidadores `consolidar_empleados_task`, `consolidar_registros_task`).
  - Punto de orquestación en la vista que dispara el proceso (p. ej., `views_*` que invocan estas tasks).
- Criterios de aceptación:
  - No hay ejecución simultánea de ambos chords en un mismo libro.
  - Los logs muestran la consolidación de empleados terminada antes de iniciar el chord de registros.
  - El estado del libro refleja la transición secuencial (empleados → registros → procesado).
- Notas de implementación:
  - Usar chain para encadenar: chord(empleados) | consolidar_empleados | task_que_dispare chord(registros).
  - Alternativa: que `consolidar_empleados_task` dispare explícitamente `guardar_registros_nomina_optimizado.delay(...)`.

2) Alinear semántica optimizado vs clásico (REPLACE vs upsert)
- Descripción: Evitar divergencias funcionales. Si el clásico borra y recrea (REPLACE), el optimizado debería limpiar previamente empleados/registros obsoletos del cliente/período, o implementar una "sincronización" (marcar-vivos/y-eliminar-stale).
- Archivos involucrados:
  - `backend/nomina/utils/LibroRemuneraciones.py` (referencia del comportamiento clásico).
  - `backend/nomina/utils/LibroRemuneracionesOptimizado.py` (aplicar pre-clean o estrategia de sync antes de los upserts).
- Criterios de aceptación:
  - Tras re-procesar el mismo libro, no quedan empleados/registros fuera del set del archivo.
  - Resultados equivalentes entre modo clásico y optimizado en conteos y totales claves.

3) Estado final y errores parciales por chunk
- Descripción: Si falla un chunk de empleados o registros, reflejarlo en el estado del libro, acumular errores y marcar `con_error`. No dejar el libro sin cerrar estado.
- Archivos involucrados:
  - `backend/nomina/tasks.py` (`consolidar_empleados_task`, `consolidar_registros_task`).
- Criterios de aceptación:
  - Ante ≥1 chunk fallido, el estado del libro pasa a `con_error` y se registran detalles (upload_log o campo de errores).
  - Si todos los chunks exitosos, el estado termina en `procesado`.

4) Bug: Duplicado de `raise` en clasificación de headers
- Descripción: Existe un `raise` duplicado (o ruta de error redundante) en `clasificar_headers_libro_remuneraciones_task`.
- Archivo: `backend/nomina/tasks.py` (task de clasificación de headers con logging).
- Criterios de aceptación:
  - El bloque de error tiene un único `raise` claro o manejo uniforme.
  - Sin código muerto/redundante en ese bloque.

5) Bug: `return` inalcanzable con variable no definida (`cierre_id`) en registros optimizados
- Descripción: En `guardar_registros_nomina_optimizado` hay un `return` que hace referencia a una variable no definida (p. ej., `cierre_id`) y/o queda inalcanzable por la estructura del flujo.
- Archivo: `backend/nomina/tasks.py` (`guardar_registros_nomina_optimizado`).
- Criterios de aceptación:
  - No hay referencias a variables no definidas.
  - Todos los returns son alcanzables y consistentes con los caminos de ejecución.

## Mejoras y optimizaciones recomendadas

- Reducir relecturas del Excel/DataFrame
  - Leer el archivo una sola vez y pasar el DataFrame serializado (p. ej., a parquet/feather temporal) o cachearlo en Redis/archivo temporal accesible por workers.
  - Criterio: cada chunk no reabre el Excel desde disco; reducción notable de I/O.

- Tamaño de chunk configurable
  - Exponer `CHUNK_SIZE` por settings/env. Medir y ajustar según bound principal (DB vs CPU).

- Métricas y logging
  - Tiempos por chunk, throughput (registros/seg), contadores de reintentos, uso de workers.
  - Log estructurado con ids de libro/chord/chunk para correlación.

- Idempotencia y acks_late
  - Confirmar idempotencia de tasks (ya se usa `update_or_create`). Revisar efectos de reintentos con `acks_late=True` y `prefetch=1`.

- Secuenciación opcional de chords
  - Mantener flag para elegir entre ejecución solapada (mayor throughput) o encadenada (mayor coherencia/menor contención), según necesidad de negocio.

## Validaciones y pruebas sugeridas

- Prueba de humo con libro ~400 filas
  - Verificar tiempos totales, distribución de chunks entre 3 workers, y estados finales del libro.

- Prueba de error forzado
  - Inyectar fallo en un chunk y verificar que el estado pase a `con_error` y se registren detalles.

- Comparativa clásico vs optimizado
  - Mismo libro, comparar conteo de empleados/registros y totales. Deben coincidir.

- Verificación de ruteo
  - Confirmar que todas las tasks `nomina.*` caen en `nomina_queue` y son atendidas por el worker con concurrencia=3.

## Estado y próximos pasos

- Prioridad alta: (1) encadenar chords (si se requiere orden estricto), (2) alinear semántica REPLACE, (3) robustecer estado final ante errores parciales, (4) corregir bugs menores.
- Luego: optimizaciones de I/O y métricas. Ajuste de chunk_size y estrategia de cache de DataFrame.
- Entregables: PR con cambios en `tasks.py` y `utils/LibroRemuneracionesOptimizado.py`, y pruebas básicas de regresión en `backend/`.

## Análisis de consolidación de datos (Nómina)

Resumen del flujo y hallazgos específicos sobre la consolidación de datos de nómina.

### Flujo actual

- Entrada: `consolidar_datos_nomina_task(cierre_id, modo='optimizado'|'secuencial')`.
- Por defecto usa modo optimizado, que encadena (chain):
  1) `procesar_empleados_libro_paralelo(cierre_id, chunk_size)`
  2) `procesar_movimientos_personal_paralelo(cierre_id)`
  3) `finalizar_consolidacion_post_movimientos(cierre_id)` → ejecuta `procesar_conceptos_consolidados_paralelo` y marca `datos_consolidados`.
- Limpia consolidación previa (`NominaConsolidada` y `MovimientoPersonal`), asume CASCADE para conceptos.

### Problemas detectados y fixes propuestos

1) Pérdida de headers por lote en empleados (crítico)
- Causa: En `procesar_empleados_libro_paralelo`, los `HeaderValorEmpleado` se acumulan en `headers_batch` por lote de empleados, pero solo se hace `bulk_create` cuando `len(headers_batch) >= 500`. Con `chunk_size` típico (<500), se insertan solo los headers del último lote (flush final), perdiendo los anteriores.
- Fix: Hacer `bulk_create(headers_batch)` al final de cada lote (siempre), y resetear `headers_batch = []`. Mantener, adicionalmente, un flush final por seguridad si quedó remanente.
- Criterio de aceptación: el conteo de `HeaderValorEmpleado` tras consolidar debe coincidir con la suma esperada de conceptos por empleado en todos los lotes.

2) Acumuladores no inicializados en modo secuencial
- Causa: En `consolidar_datos_nomina_task_secuencial` (sección 5.6), los totales por categoría (`total_haberes_imponibles`, `total_haberes_no_imponibles`, `total_dctos_legales`, `total_otros_dctos`, `total_impuestos`, `total_horas_extras`, `total_aportes_patronales`) se usan sin inicialización.
- Fix: Inicializarlos a `Decimal('0')` al inicio del bucle por nómina.
- Criterio de aceptación: ejecución del modo secuencial sin `NameError` y totales por categoría persistidos correctamente.

3) Desalineación del resumen por tipo_concepto (optimizado vs otro flujo)
- Causa: El “resumen_totales” (via `utils.aggregate_by_tipo_concepto`) se genera en `consolidar_resultados_finales`, pero el chain optimizado actual finaliza en `finalizar_consolidacion_post_movimientos` y no ejecuta esa agregación.
- Fix: Integrar la generación del resumen por tipo de concepto dentro de `finalizar_consolidacion_post_movimientos` o reutilizar esa lógica (helper) al final del chain optimizado.
- Criterio de aceptación: ambas rutas (optimizada y alternativa) dejan `fuente_datos['resumen_totales']` por nómina consolidada.

4) Paralelismo nominal en empleados
- Observación: `procesar_empleados_libro_paralelo` no paraleliza a nivel de Celery; es batching interno en una sola tarea. El nombre/logs sugieren paralelismo.
- Mejora: Opcionalmente, migrar a un patrón real con chord (tasks por chunk + callback) para aprovechar los 3 workers.
- Criterio de aceptación: si se paraleliza, medir reducción de tiempo y uso de workers en logs/telemetría.

5) N+1 al cargar conceptos por empleado
- Riesgo: Acceso a `registroconceptoempleado_set` por empleado sin prefetch puede causar N+1 queries.
- Mejora: Aplicar `prefetch_related` sobre los empleados del cierre hacia los conceptos y sus relaciones necesarias.
- Criterio de aceptación: reducir el número de queries y/o tiempo en esa sección medido en logs.

6) Limpieza por cascada de conceptos
- Verificar que `ConceptoConsolidado` tenga FK con `on_delete=CASCADE` desde `NominaConsolidada` para evitar restos al limpiar consolidaciones previas.
- Criterio de aceptación: tras limpiar `NominaConsolidada` del cierre, no quedan `ConceptoConsolidado` huérfanos en ese cierre.

### Validaciones sugeridas (consolidación)

- Conteos consistentes: empleados, headers, movimientos, conceptos tras consolidar deben coincidir con expectativas del libro y movimientos procesados.
- Re-proceso idempotente: al correr consolidación dos veces seguidas, no deben aparecer duplicados; los conteos deben permanecer estables.
- Performance: registrar tiempos por etapa (empleados/movimientos/conceptos) y comparar antes/después de los fixes.

## Registro de bugs K-Users (diagnóstico + solución propuesta, sin implementación)

Esta sección se usará para documentar cada bug reportado durante las pruebas con K-Users. Por favor, al reportar un bug incluir logs/IDs de tareas si están disponibles.

Plantilla por bug (copiar y completar):

- Bug ID/Título: 
- Fecha/Entorno: (ej. prod/dev, versión/branch)
- Área afectada: (ej. libro, nómina, consolidación, incidencias, novedades)
- Síntomas observados:
  - Mensaje(s) de error visibles (UI/API)
  - Trazas/logs relevantes (task_id, chord_id, worker, timestamp)
- Pasos para reproducir:
  1. 
  2. 
  3. 
- Resultado esperado vs resultado actual:
  - Esperado:
  - Actual:
- Análisis raíz (por qué ocurre):
  - Código/lugar probable: (archivo, función, sección)
  - Causa técnica: (condición de carrera, variable no inicializada, mal ruteo, estado inconsistente, validación insuficiente, etc.)
- Solución propuesta (sin implementar):
  - Cambios sugeridos:
  - Archivos a tocar:
  - Consideraciones de compatibilidad/migración:
- Riesgos/impacto colateral:
- Pruebas de validación a ejecutar:
- Estado: (pendiente análisis / analizado / listo para implementar)

Casos reportados:

- K-Users-001 — Hashtags no implementados para clasificación/filtrado rápido
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: UI/Analista (flujo de validación y colaboración), API de incidencias/archivos/cierre
  - Síntomas observados:
    - Los analistas esperan poder agregar `#hashtags` en comentarios/notas para clasificar y luego filtrar vistas por esas etiquetas.
    - No existen campos en BD ni endpoints para persistir/consultar tags; no hay autocompletado ni filtros por hashtag en UI.
  - Pasos para reproducir:
    1. Intentar escribir `#algo` en comentarios/notas asociadas a incidencias/archivos/cierre.
    2. Buscar filtrar por ese `#algo` en la interfaz o API.
    3. No hay efecto ni soporte.
  - Resultado esperado vs resultado actual:
    - Esperado: Posibilidad de etiquetar (crear/usar) `#hashtags` y filtrar rápidamente listados (incidencias, nóminas, movimientos, archivos) por una o varias etiquetas; sugerencias/autocompletado con tags existentes.
    - Actual: Funcionalidad inexistente.
  - Análisis raíz (por qué ocurre):
    - Falta de modelo y capa de persistencia de tags; ausencia de endpoints/serializers para exponer y modificar tags; UI sin componente de entrada de chips/etiquetas.
  - Solución propuesta (sin implementar):
    - Diseño de tagging minimalista y escalable:
      - Opción A (genérica, recomendable): Modelo `Tag(id, nombre, slug)` + `TaggedItem(content_type, object_id, tag, created_at)` usando GenericForeignKey (ContentTypes) para reutilizar en múltiples entidades (Incidencia, NominaConsolidada, MovimientoPersonal, ArchivoAnalistaUpload, CierreNomina, etc.). Índice compuesto `(content_type, object_id)` y `(tag)`; unique por (content_type, object_id, tag).
      - Opción B (simple en Postgres): Campo `ArrayField(Text)` de `tags_normalizados` por modelo principal + índice GIN para búsqueda. Menos flexible para analíticas cruzadas; considerar solo si el alcance es acotado.
    - Backend (archivos a tocar): `backend/nomina/models.py` (nuevos modelos/relaciones), `serializers.py` (exponer lista de tags), `views.py`/`views_*` (endpoints CRUD/sugerencias y filtros `?tag=`/`?tags=`), `permissions.py` (quién puede crear/editar tags), migraciones.
    - Normalización/validación: almacenar `slug` en minúsculas, sin tildes/espacios; longitud máx (p. ej., 32); lista negra opcional; sanitizado de entrada.
    - Búsqueda/filtrado: soportar `?tag=ventas` y `?tags=ventas,liquidaciones` (AND/OR configurable). Añadir índice GIN o BTREE según opción elegida.
    - Frontend: componente chips con autocompletado de tags existentes, creación on-the-fly, contador de uso, filtros rápidos por etiqueta.
    - Auditoría/seguridad: registrar creación/edición de tags (usuario/fecha); visibilidad lectora para todos; escritura restringida a analistas/gerentes.
  - Riesgos/impacto colateral:
    - Cardinalidad alta de tags; necesidad de pruning/merge; governance de vocabulario; rendimiento en filtros si no se indexa adecuadamente.
  - Pruebas de validación a ejecutar:
    - Crear/editar/eliminar tags; asignación masiva; filtros simples y múltiples; case-insensitive; tildes y normalización; concurrencia; rendimiento de listados con filtros.
  - Estado: listo para implementar (feature nuevo).

- K-Users-002 — Novedades: “se omiten las primeras 4 columnas”
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Novedades (headers y guardado de registros)
  - Síntomas observados:
    - Al pedir headers para novedades, no aparecen las primeras 4 columnas del archivo (RUT, Nombre, Apellido Paterno, Apellido Materno).
    - Percepción de “pérdida de columnas” o que no se consideran al guardar.
  - Pasos para reproducir:
    1. Subir archivo de novedades con columnas: [Rut, Nombre, Apellido Paterno, Apellido Materno, Concepto A, Concepto B, ...].
    2. Ejecutar la extracción/clasificación de headers.
    3. Observar que el resultado contiene solo [Concepto A, Concepto B, ...].
  - Resultado esperado vs resultado actual:
    - Esperado: Dejar explícito que las primeras 4 columnas son de identidad del empleado y no se clasifican como conceptos; deben quedar registradas/visibles como “headers de identidad”.
    - Actual: La función retorna solo headers de conceptos (desde la columna 5), sin meta-información de que se ignoraron las 4 primeras por diseño.
  - Análisis raíz (por qué ocurre):
    - En `backend/nomina/utils/NovedadesRemuneraciones.py::obtener_headers_archivo_novedades`, se lee el Excel y se hace `filtered_headers = headers[4:]` (se excluyen las 4 primeras). Esto es intencional: las primeras 4 columnas se usan para poblar `EmpleadoCierreNovedades` y las restantes son candidatos a conceptos.
    - La omisión de meta-datos provoca confusión: el consumidor no sabe que las 4 primeras sí se usan en otra etapa.
  - Solución propuesta (sin implementar):
    - API: Cambiar el retorno a un objeto con dos listas: `{ identidad_headers: headers[:4], headers_conceptos: headers[4:] }`. Mantener compatibilidad proveyendo también `headers_conceptos` plano si algún consumidor legacy lo espera.
    - UI: Mostrar visualmente la sección “Identidad del empleado (no mapeable)” con esas 4 columnas, y otra sección “Conceptos a mapear”. Añadir copy aclaratorio.
    - Logging: Incluir en logs qué columnas se toman como identidad y cuántas se detectaron como conceptos.
  - Riesgos/impacto colateral:
    - Consumidores que asumían una lista plana; mitigar con respuesta backward-compatible o flag `?flat=true`.
  - Pruebas de validación a ejecutar:
    - Archivo con ≥5 columnas: verificar que se devuelven ambas listas y que el guardado usa las 4 primeras para empleados y las restantes para registros.
  - Estado: analizado (listo para implementar en API/UI).

- K-Users-003 — Libro de remuneraciones: “falta un ítem (concepto)”
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Libro (derivación/selección de headers de conceptos)
  - Síntomas observados:
    - Al procesar el libro, falta un concepto esperado en el set resultante (ya sea en headers clasificados o en registros guardados).
  - Pasos para reproducir:
    1. Subir libro con un concepto X visible en el Excel.
    2. Ejecutar la derivación/clasificación de headers y/o el guardado de registros.
    3. Observar que X no aparece en la lista final o en los registros para empleados.
  - Resultado esperado vs resultado actual:
    - Esperado: Solo excluir columnas de identidad (RUT, nombres, etc.) y mantener todos los demás headers como candidatos a conceptos, salvo una lista negra explícita y acotada.
    - Actual: Alguna heurística o normalización hace que el concepto X sea descartado o no coincida con el mapeo de `ConceptoRemuneracion`.
  - Análisis raíz (por qué ocurre):
    - En `backend/nomina/utils/LibroRemuneraciones.py` existen heurísticas/listas para excluir columnas no-concepto; un filtro agresivo puede descartar conceptos válidos.
    - Además, el match con `ConceptoRemuneracion` es exacto por `nombre_concepto=h, vigente=True`. Variaciones de nombre/caso/espacios hacen que `concepto` sea `None`. Aunque se guarda `RegistroConceptoEmpleado` con `nombre_concepto_original=h`, en etapas previas de “clasificación” puede desaparecer el header.
  - Solución propuesta (sin implementar):
    - Modo estricto conservador: excluir solo identidad (primeras 4) y una lista negra mínima configurable por cliente (p. ej. `['Centro de costo']`). Todo lo demás pasa como candidato.
    - Normalización de mapeo: realizar match case-insensitive y normalizado (trim, colapsar espacios, quitar tildes). Guardar además un `slug` del concepto para trazabilidad.
    - Override manual: permitir forzar inclusión/exclusión de un header desde UI, persistiendo la decisión en BD para futuras corridas.
    - Observabilidad: loggear y retornar en API `headers_excluidos` para auditoría.
  - Riesgos/impacto colateral:
    - Incluir demasiados headers ruidosos si la lista negra es mínima. Mitigar con UI para excluir y persistir la exclusión.
  - Pruebas de validación a ejecutar:
    - Libros con headers cercanos (variaciones ortográficas/espaciado); verificar que ahora se conservan y/o se mapean por normalización.
  - Estado: analizado (listo para implementar ajustes en utilidades y endpoints de headers).

- K-Users-004 — Archivos del analista: “se procesan pero no se guardan registros”
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Archivos del analista (ingresos, incidencias, finiquitos)
  - Síntomas observados:
    - Se sube un archivo, el proceso indica éxito o “procesado”, pero no aparecen filas en sus respectivas tablas o vistas.
  - Pasos para reproducir:
    1. Subir un archivo de tipo ‘ingresos’/‘incidencias’/‘finiquitos’.
    2. Esperar a que termine el procesamiento.
    3. Consultar en UI/DB por registros vinculados al `archivo_origen` y no ver resultados.
  - Resultado esperado vs resultado actual:
    - Esperado: Que se creen registros por cada fila válida del Excel, con vínculos a `cierre` y `archivo_origen`. Reportar en la respuesta cuántos se crearon y cuántos errores hubo.
    - Actual: Mensajes de “procesado” pero tablas sin nuevos registros.
  - Análisis raíz (por qué ocurre): hipótesis con base en código `backend/nomina/utils/ArchivosAnalista.py`
    - `tipo_archivo` no coincide exactamente (‘finiquitos’/‘incidencias’/‘ingresos’) → cae en `else` y lanza `ValueError`, que podría ser atrapado aguas arriba y reportado ambiguamente.
    - Validación de headers estricta: si falta un header, se lanza `ValueError` y no se insertan filas.
    - RUT/empleado: la búsqueda de empleado es por normalización de RUT; si ningún empleado del cierre coincide, igualmente se crea el registro (con `empleado=None`), pero si el modelo exige `empleado` no nulo, habría error al crear (se captura en `except` y se cuenta como error, quedando 0 insertados).
    - Observabilidad: no se persiste un resumen detallado por `archivo` (solo se loggea). Es posible confundir “procesado” con “0 filas insertadas y N errores”.
  - Solución propuesta (sin implementar):
    - Validación temprana de `tipo_archivo`: restringir a un Enum/choices en el modelo y rechazar antes de procesar, con mensaje claro.
    - Mejorar mensajes de resultado: devolver y persistir en `ArchivoAnalistaUpload.resultado_json` un resumen con `{procesados, errores[], warnings[]}` por archivo.
    - Logging estructurado: incluir `archivo_id`, `tipo_archivo`, `filas_totales`, `insertados`, `errores_count`, primeros 5 errores.
    - Tolerancia a `empleado=None`: revisar modelos `AnalistaIngreso/Incidencia/Finiquito` para permitir `empleado` opcional si el RUT no matchea, y exponer conteo de filas sin match como warning.
    - Pruebas unitarias: crear tests con archivos de ejemplo (headers válidos/ inválidos, ruts no matcheados, tipos de archivo incorrectos) y verificar inserciones y resúmenes.
  - Riesgos/impacto colateral:
    - Si se permite `empleado=None`, considerar cómo se muestran/gestionan en UI.
  - Pruebas de validación a ejecutar:
    - Tres archivos de muestra (uno por tipo) con 10 filas: validar que `insertados` > 0 y que `errores` refleje filas inválidas. Probar también `tipo_archivo` inválido y que se rechaza con mensaje claro.
  - Estado: analizado (listo para implementar en utilidades, modelos y vistas que reportan estado del archivo).


- K-Users-005 — Movimientos Mes: fechas con desfase (-1 día) y "DIAS" incorrectos
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Movimientos del mes (altas/bajas, ausentismos, vacaciones)
  - Síntomas observados:
    - En algunos archivos, las fechas cargadas aparecen corridas un día (p. ej., 2025-05-02 en vez de 2025-05-03).
    - El campo "DIAS" (o "CANTIDAD DE DIAS") resulta 0 o distinto a lo esperado.
  - Análisis raíz (por qué ocurre):
    - `backend/nomina/utils/MovimientoMes.py::convertir_fecha` solo maneja `datetime` y `str` con `parse_date`; si la celda llega como número (serial Excel) devuelve `None`.
    - Dependencias de engine/Excel: openpyxl suele entregar `datetime`, pero variaciones de formato o exportadores dejan seriales numéricos.
    - "DIAS" se toma directo del Excel; si está vacío o mal calculado en el origen, lo persistimos tal cual. En vacaciones/ausentismos suele requerirse regla de negocio (inclusive: fin - inicio + 1).
  - Solución propuesta (sin implementar):
    - Extender `convertir_fecha` para soportar seriales de Excel (int/float) con origen 1899-12-30 y retorno `date` naïve.
    - Normalizar `str` con múltiples formatos (`%d/%m/%Y`, `%Y-%m-%d`, etc.) y limpiar espacios.
    - Recalcular días cuando:
      - el campo venga vacío o no numérico, o
      - haya discrepancia clara (p. ej., fin < inicio o días negativos): `dias = (fin - inicio).days + 1` si ambas fechas existen.
    - Loggear advertencias por filas auto-correctas y contabilizar correcciones en el resultado.
  - Archivos a tocar:
    - `backend/nomina/utils/MovimientoMes.py` (funciones `convertir_fecha`, `convertir_entero`, y uso en `procesar_ausentismos`/`procesar_vacaciones`).
  - Criterios de aceptación:
    - Seriales numéricos se convierten a fechas válidas (sin desfase).
    - Días se recalculan cuando faltan o son incoherentes (inclusive), con conteo de correcciones en logs/respuesta.
    - No se introducen cambios para filas con datos ya correctos.
  - Riesgos/impacto colateral:
    - Regla de inclusión de días (inclusive vs exclusiva); acordar y documentar (por defecto, inclusive).
  - Pruebas de validación:
    - Archivo con fechas como `datetime`, como serial numérico, y como `str` en distintos formatos; casos con días vacíos y con fin < inicio.

- K-Users-006 — Novedades: la reclasificación/mapeo no se persiste entre corridas
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Novedades (clasificación de headers y mapping a conceptos)
  - Síntomas observados:
    - Las decisiones de mapeo realizadas en la UI no reaparecen al reabrir el cierre o volver a cargar el archivo; hay que re-mapear.
  - Análisis raíz:
    - No existe un modelo persistente para las decisiones de mapeo por cliente/cierre/empresa; la clasificación es efímera.
  - Solución propuesta (sin implementar):
    - Crear `NovedadHeaderMapping` con campos: `empresa`/`cliente`, `cierre` (opcional si se aplica global), `header_original`, `concepto_destino`, `normalizado`, `creado_por`, `vigente`, `version`.
    - Al clasificar, pre-cargar mapeos previos y permitir override; persistir cambios.
    - Añadir endpoints para GET/POST/PUT de mapeos; en la respuesta de "headers", devolver `{identidad_headers, headers_conceptos, mapeos_aplicados}`.
  - Archivos a tocar:
    - `backend/nomina/models.py`, `serializers.py`, `views_*`/`urls.py` (endpoints), `utils/NovedadesRemuneraciones.py` (cargar/aplicar/guardar mapping).
  - Criterios de aceptación:
    - Al reabrir un cierre o re-subir un archivo del mismo cliente, la UI precarga mapeos históricos.
    - Se puede forzar reclasificación y queda persistida.
  - Riesgos/impacto colateral:
    - Necesidad de scope (por cliente/empresa/cierre) y estrategia de versionado para cambios globales.

- K-Users-007 — Incidencias/Ausentismos: falta módulo de resolución/estado
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Flujo de analista (gestión de incidencias)
  - Síntomas observados:
    - No se puede marcar una incidencia como resuelta/descartada/en revisión; no hay filtros por estado.
  - Análisis raíz:
    - Modelos y endpoints no contemplan ciclo de vida (estado, resolved_by, resolved_at, notas de resolución).
  - Solución propuesta (sin implementar):
    - Extender modelo `AnalistaIncidencia` con `estado` (choices: abierta, en_revision, resuelta, descartada), `resolved_at`, `resolved_by`, `resolucion`.
    - Endpoints para transiciones y listados por estado; auditoría mínima.
    - UI: acciones en fila + filtros de estado y fecha.
  - Archivos a tocar:
    - `backend/nomina/models.py`, `serializers.py`, `views_*`, `permissions.py`; Frontend: tablas y formularios en `src/pages`/`src/components`.
  - Criterios de aceptación:
    - Cambios de estado auditables; listados por estado; métricas de pendientes vs resueltas.

- K-Users-008 — UI: tablas de nómina poco responsivas y con render pesado
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Frontend (React/Vite)
  - Síntomas observados:
    - Lags al renderizar listados grandes; mala experiencia en pantallas pequeñas.
  - Análisis raíz:
    - Falta de virtualización en tablas, consultas no paginadas, re-renderizados costosos, CSS no adaptativo en ciertos componentes.
  - Solución propuesta (sin implementar):
    - Implementar paginación y server-side filtering; usar virtualización (ej. react-virtualized/react-window) en tablas grandes.
    - Skeleton loaders y "lazy" para vistas pesadas; code-splitting por rutas.
    - Revisar CSS responsive (grid/flex) y breakpoints; pruebas en móviles.
  - Archivos a tocar:
    - Frontend `src/pages/*`, `src/components/*`, `src/api/*` (añadir parámetros de paginación/filtros).
  - Criterios de aceptación:
    - Tiempos de interacción percibidos < 1.5s en listados; uso estable en mobile; reducción notable de RAM/CPU en renders.

- K-Users-009 — Reclasificación de novedades no actualiza las discrepancias
  - Fecha/Entorno: 2025-09-26 · dev · branch `restauracion-nomina-31jul`
  - Área afectada: Discrepancias Libro vs Novedades
  - Síntomas observados:
    - Tras cambiar el mapeo de un header, las discrepancias siguen mostrando resultados viejos.
  - Análisis raíz:
    - Generación de discrepancias no está suscrita a cambios de mapeo; falta de invalidación o re-cálculo.
  - Solución propuesta (sin implementar):
    - Cada actualización de mapping dispara una tarea Celery "regenerar_discrepancias(cierre_id)".
    - Versionar mapping aplicado en `EmpleadoCierreNovedades`/`RegistroConceptoEmpleadoNovedades`; invalidar y recalcular.
    - UI: notificar que se está recalculando; refrescar cuando termine.
  - Archivos a tocar:
    - `backend/nomina/utils/GenerarDiscrepancias.py`, tasks en `backend/nomina/tasks.py`, endpoints de mapping.
  - Criterios de aceptación:
    - Después de reclasificar, el contador y detalle de discrepancias refleja el nuevo mapping sin intervención manual.

