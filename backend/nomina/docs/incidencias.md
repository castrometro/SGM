# Sistema de Incidencias: ¿Qué se compara y cómo?

Este documento describe, de forma concreta, qué compara el backend para levantar incidencias de nómina y cómo se aplican los criterios. La implementación se basa en el "Sistema Dual" definido en `backend/nomina/utils/DetectarIncidenciasConsolidadas.py`.

## Definiciones (para esta conversación)

- Concepto de remuneraciones: categoría como "haber imponible", "haber no imponible", "otros descuentos".
- Ítem de remuneraciones: un elemento específico dentro de un concepto, por ejemplo "bono x".

## Resumen ejecutivo

- Dos tipos de comparaciones:
  - Comparación individual por empleado y por ítem (solo para conceptos: haber_imponible, haber_no_imponible, otro_descuento).
  - Comparación de suma total por ítem (agregada sobre todos los empleados), para TODAS las categorías.
- No se generan incidencias por sumas de categoría (total categoría) ni por total líquido en esta versión.
- Umbral fijo: 30% para ambos tipos (individual e ítem agregado).
- Dependencia temporal: se compara el cierre actual contra el cierre previo finalizado; si no existe, se ejecuta un análisis informativo de primer cierre.

## Fuentes de datos principales

- `NominaConsolidada`: consolidado por empleado y período (cierre).
- `ConceptoConsolidado`: conceptos y montos por empleado.
- `CierreNomina`: controla estado del cierre y de incidencias.
- `IncidenciaCierre`: registro de cada incidencia generada.

## Comparación 1: Individual por empleado (por ítem)

- Alcance: Solo en conceptos `haber_imponible`, `haber_no_imponible`, `otro_descuento` (alias antiguos se normalizan, p.ej., `haberes_imponibles` → `haber_imponible`).
- Qué se compara:
  - Para cada empleado actual, se busca el mismo rut en el cierre anterior.
  - Se arma la unión de claves `(nombre_concepto, tipo_concepto)` de ambos períodos dentro de las categorías objetivo.
  - Para cada ítem, se comparan montos: `monto_actual` vs `monto_anterior`.
- Fórmula de variación porcentual:
  - Si `monto_anterior == 0`: variación = 100% si `monto_actual > 0`, si no 0%.
  - Si no: `(monto_actual - monto_anterior) / monto_anterior * 100`.
- Umbral y disparo de incidencia:
  - Umbral fijo: 30%.
  - Se crea incidencia si `abs(variación) >= 30`.
- Tipo y contenido de la incidencia creada:
  - `tipo_incidencia`: `variacion_concepto_individual`.
  - `tipo_comparacion`: `individual`.
  - `datos_adicionales` incluye: concepto, tipo_concepto, monto_actual, monto_anterior, variacion_porcentual, variacion_absoluta, tipo_comparacion.
  - Prioridad según magnitud de variación: >=75% crítica, >=50% alta, >=30% media, else baja.

Notas adicionales (individual):
- Si no existe el empleado en el período anterior, la comparación se hace contra 0.
- Hay factories auxiliares para incidencias de concepto nuevo/eliminado y empleado nuevo, usadas en otros flujos/compatibilidad.

## Comparación 2: Suma total por ítem (agregada sobre empleados)

- Alcance:
  - Por ítem específico (nombre_concepto) agregado sobre todos los empleados.
  - Aplica a todas las categorías EXCEPTO aquellas con análisis individual (haber_imponible, haber_no_imponible, otro_descuento).
  - Para las categorías con análisis individual, el front muestra el total agrupado (no genera incidencia agregada) y despliega el detalle de incidencias por empleado.
- Qué se compara (ítem agregado):
  - Para cada par `(nombre_concepto, tipo_concepto)` presente en cualquiera de los dos períodos, se calcula la suma total del ítem en el cierre actual y en el anterior.
  - Se calcula la variación porcentual entre ambas sumas.
- Fórmula de variación porcentual: igual a la comparación individual (mismo manejo de cero).
- Umbral y disparo de incidencia:
  - Umbral fijo: 30%.
  - Se crea incidencia si `abs(variación) >= 30`.
- Tipo y contenido de la incidencia creada:
  - Por ítem agregado: `tipo_incidencia = variacion_suma_total`, `tipo_comparacion = suma_total`.
  - `datos_adicionales` incluye: categoría/concepto, tipo_concepto, suma_actual, suma_anterior, variacion_porcentual, variacion_absoluta, tipo_comparacion.
  - Prioridad considera variación y el impacto monetario (umbral de 1M, 5M, 10M para media, alta, crítica respectivamente, o 15/30/50% en variación).

No considerado en suma total:
- No se generan incidencias por sumas de categoría (ni total líquido) en esta versión.
- No se generan incidencias por “concepto nuevo” o “concepto eliminado” a este nivel agregado.

## Primer cierre (sin período previo)

- Si no existe cierre previo finalizado del cliente:
  - No hay comparación; se genera un análisis informativo.
  - Incidencias informativas posibles: `empleado_sin_conceptos`, `empleado_montos_cero`, `concepto_monto_anomalo` (> $10.000.000), y un `resumen_primer_cierre` con estadísticas.
  - `tipo_comparacion = informativo`.
  - El cierre actualiza `estado_incidencias` y `estado` con lógica específica de primer análisis.

## Estados y efectos sobre el Cierre

- Tras consolidar resultados, se actualiza: `cierre.total_incidencias`, `cierre.estado_incidencias`, y eventualmente `cierre.estado`.
- Con incidencias: `estado_incidencias = detectadas` y `estado = con_incidencias`.
- Sin incidencias: `estado_incidencias = resueltas` y el estado principal avanza a `incidencias_resueltas` si corresponde.

## Endpoints relacionados (referencia rápida)

- POST `incidencias/generar/<cierre_id>`: dispara el chord del sistema dual.
- DELETE `incidencias/limpiar/<cierre_id>`: borra incidencias y resetea estado de incidencias.
- GET `cierres-incidencias/<id>/estado_incidencias`: estado y conteos.
- GET `incidencias/preview|resumen|analisis-completo/<cierre_id>`: vistas auxiliares para UI.
- POST `incidencias/finalizar/<cierre_id>`: corre generación de informe y finaliza.

## Anexos: funciones clave

- Orquestación: `generar_incidencias_consolidados_v2` (Celery chord).
- Individual: `procesar_chunk_comparacion_individual`.
- Agregado: `procesar_comparacion_suma_total`.
- Cálculo y umbrales: `calcular_variacion_porcentual`, `obtener_umbral_individual`, `obtener_umbral_suma_total`.
- Prioridades: `determinar_prioridad_individual`, `determinar_prioridad_suma_total`.
- Estados del cierre: `actualizar_estado_cierre_por_incidencias`.

---

Última actualización: 2025-09-13.
