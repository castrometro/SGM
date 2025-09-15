# Reconciliación de Incidencias de Nómina (alcance acotado)

Fecha: 2025-09-15
Estado: Propuesta Acordada

## Objetivo

Mantener coherencia de incidencias entre versiones de datos (v1, v2, v3, …) generadas por recargas de Talana, preservando historial y decisiones previas, con un modelo simple acotado a:
- No hay renombres de ítems.
- Puede aparecer un ítem nuevo.
- Puede cambiar el mapeo ítem → concepto.

## Definiciones

- Versión de datos (version_datos): entero que aumenta con cada recarga del cierre (v1 inicial, luego v2, v3…)
- Incidencia: anomalía detectada ya sea:
  - Por ítem total (suma mensual) vs mes anterior (umbral 30%).
  - Por empleado por ítem (cuando corresponda).
- Incidencias informativas: no impactan KPIs de finalización.

## Firma estable de incidencia

Para reconciliar entre versiones, se usa una firma estable basada en el ítem y el tipo de comparación:

- Por ítem total: `por_item_total|<item_normalizado>|-`
- Por empleado por ítem: `por_empleado_item|<item_normalizado>|<rut>`

Normalización de `<item_normalizado>`:
- trim, a minúsculas, colapso de espacios múltiples, eliminación de acentos y caracteres no alfanuméricos salvo espacios.

Campos en el modelo `IncidenciaCierre`:
- `firma_clave: CharField` — la cadena anterior.
- `firma_hash: CharField` — hash sha1 de `firma_clave` (para índices cortos).
- `version_detectada_primera: IntegerField` — primera versión donde apareció.
- `version_detectada_ultima: IntegerField` — última versión donde fue recalculada o detectada.

Índices recomendados:
- Compuesto `(cierre_id, firma_hash)` para reconciliar eficientemente dentro del cierre.
- Índice sobre `firma_clave` para búsquedas y auditoría.

## Estados y decisiones

- abierta → justificada (analista) → aprobada (supervisor) | rechazada (supervisor)
- Mensajes y adjuntos se guardan como historial.
- Decisiones y mensajes no se borran en recargas; se añade una “nota del sistema” cuando cambian valores por una nueva versión.

## Reglas de reconciliación vN → vN+1

Dado un mismo cierre con versiones crecientes v1, v2, v3… se aplican estas reglas por `firma`:

1. Coincidencia por firma (existe en vN y vN+1)
   - Upsert en el mismo registro: se actualizan montos, deltas y `version_detectada_ultima = vN+1`.
   - Se preservan estado y decisiones; se agrega nota del sistema: "Recalculada con vN+1" con los valores anteriores y nuevos.

2. Incidencia que desaparece (existe en vN y no existe en vN+1)
   - Mantener el registro (no eliminar) y cambiar su estado a `resolucion_supervisor_pendiente`.
   - Actualizar campos de detalle para reflejar la nueva situación, mostrando variación/monto actualizado (por ejemplo delta=0 o por debajo del umbral).
   - Agregar nota del sistema: "Incidencia no presente en vN+1; requiere confirmación del supervisor".
   - El supervisor debe dar el OK final para cerrar.

3. Incidencia nueva (existe en vN+1 y no existía en vN)
   - Crear registro nuevo con `version_detectada_primera = version_detectada_ultima = vN+1`.
   - Estado inicial `abierta`.

Notas:
- Este proceso se repite para v2→v3, v3→v4, … sin límite (v6, v7, etc.).
- Si un ítem cambia su mapeo a concepto, la firma se mantiene (no hay renombres), por lo que cae en el caso 1.

## KPIs y UI

- KPIs del header y resumen por ítem:
  - Nuevas (vN+1 sin presencia en vN)
  - Vigentes (coinciden por firma y siguen sobre umbral)
  - En revisión por recarga (caso 2: `resolucion_supervisor_pendiente`)
  - Totales
- Modal de incidencia:
  - Encabezado compacto con resumen colapsable.
  - Chat neutral (mensajes) y acciones separadas (aprobar/rechazar) por rol.
  - Notas del sistema visibles cuando hay cambios por recarga.

## Contrato de métodos (backend)

- `IncidenciaCierre.generar_firma(tipo, item, rut=None) -> (firma_clave, firma_hash)`
  - Normaliza `item` y forma la clave; calcula sha1.
- `IncidenciaCierre.actualizar_firma_y_versiones(version)`
  - Setea `version_detectada_primera` cuando no exista y actualiza `version_detectada_ultima = version`.
- Servicio `reconciliar_cierre(cierre_id, nueva_version)`
  - Entrada: `cierre_id`, `nueva_version` (int)
  - Efecto: aplica reglas 1–3 y retorna un resumen: `{nuevas, vigentes_actualizadas, supervisor_pendiente}`.

## Permisos y validaciones

- Recomendación: exigir que todas las incidencias estén resueltas (aprobadas o rechazadas) antes de permitir recarga. Si no, pedir una confirmación explícita.
- Sólo supervisor puede aprobar/rechazar; analista puede justificar y solicitar recarga.

## Auditoría

- `version_detectada_primera` y `version_detectada_ultima` permiten rastrear la vida de la incidencia a través de recargas múltiples (v2…vN).
- Notas del sistema documentan recalculados y desapariciones.

## Futuras mejoras (opcionales)

- Cierre automático configurable para desapariciones si el equipo decide simplificar (hoy queda en `resolucion_supervisor_pendiente`).
- Métricas por centro de costo/cargo para escalar revisión humana sin drill-down masivo.
