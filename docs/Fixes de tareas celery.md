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

