# 🎯 CONSOLIDACIÓN DE DATOS - DIAGRAMA SIMPLIFICADO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  👤 USUARIO PRESIONA "CONSOLIDAR DATOS"                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  📡 FRONTEND LLAMA API                                                  │
│  POST /api/nomina/consolidacion/123/consolidar/                        │
│  Body: { "modo": "optimizado" }                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  🐍 BACKEND VALIDA Y LANZA TAREA CELERY                                │
│  ✅ Cierre existe?                                                      │
│  ✅ Estado correcto?                                                    │
│  ✅ Archivos procesados?                                                │
│  🚀 consolidar_datos_nomina_con_logging.delay(...)                     │
│  ↩️  Retorna: { "task_id": "abc-123", "cierre_id": 123 }               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  🔄 CELERY WORKER EJECUTA TAREA                                         │
│  📊 Log inicio (TarjetaActivityLog + ActivityEvent)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │   ¿Modo optimizado?           │
                    └───────────────┬───────────────┘
                           SÍ │            │ NO
                              │            │
                    ┌─────────┴────┐  ┌───┴──────────┐
                    │  PARALELO    │  │  SECUENCIAL  │
                    │  (Celery     │  │  (Uno por    │
                    │   Chain)     │  │   uno)       │
                    └─────────┬────┘  └───┬──────────┘
                              │            │
                              └─────┬──────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  📋 STEP 1: PROCESAR EMPLEADOS                                          │
│  ┌────────────────────────────────────────┐                            │
│  │ FOR batch in empleados (chunks de 50): │                            │
│  │   • Crear NominaConsolidada            │                            │
│  │   • Normalizar RUT: 12.345.678-9       │                            │
│  │                  → 123456789            │                            │
│  │   • Crear HeaderValorEmpleado          │                            │
│  │     (todos los conceptos Excel)        │                            │
│  │   • bulk_create() cada 500             │                            │
│  └────────────────────────────────────────┘                            │
│  ✅ Resultado: 150 empleados, 12,000 headers                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  🔄 STEP 2: PROCESAR MOVIMIENTOS                                        │
│  ┌────────────────────────────────────────┐                            │
│  │ Buscar en 5 tipos de movimientos:      │                            │
│  │   1. ⬆️  Altas/Bajas                   │                            │
│  │   2. 🏥 Ausentismos                    │                            │
│  │   3. 🏖️  Vacaciones                    │                            │
│  │   4. 💰 Variaciones Sueldo             │                            │
│  │   5. 📑 Variaciones Contrato           │                            │
│  │                                         │                            │
│  │ FOR cada movimiento:                   │                            │
│  │   • Buscar empleado por RUT            │                            │
│  │   • Actualizar estado_empleado         │                            │
│  │   • Calcular días en periodo           │                            │
│  │   • Generar hash único                 │                            │
│  │   • Crear MovimientoPersonal           │                            │
│  │   • bulk_create() cada 100             │                            │
│  └────────────────────────────────────────┘                            │
│  ✅ Resultado: 80 movimientos detectados                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  💰 STEP 3: PROCESAR CONCEPTOS Y FINALIZAR                              │
│  ┌────────────────────────────────────────┐                            │
│  │ FOR nomina in empleados:               │                            │
│  │   • Agrupar headers por concepto       │                            │
│  │   • Calcular totales:                  │                            │
│  │     - haberes_imponibles               │                            │
│  │     - haberes_no_imponibles            │                            │
│  │     - descuentos_legales               │                            │
│  │     - otros_descuentos                 │                            │
│  │     - impuestos                        │                            │
│  │     - horas_extras                     │                            │
│  │   • Crear ConceptoConsolidado          │                            │
│  │   • Actualizar totales en nomina       │                            │
│  │   • bulk_create() cada 200             │                            │
│  └────────────────────────────────────────┘                            │
│  ✅ Resultado: 600 conceptos consolidados                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  🎯 ACTUALIZAR ESTADO DEL CIERRE                                        │
│  • cierre.estado = 'datos_consolidados'                                │
│  • cierre.estado_consolidacion = 'consolidado'                         │
│  • cierre.fecha_consolidacion = now()                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 LOG ÉXITO (DUAL LOGGING)                                            │
│  • TarjetaActivityLogNomina (visible en UI)                            │
│  • ActivityEvent (base de datos sistema)                               │
│  • Logger: "✅ Consolidación completada"                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  ↩️  RETORNAR RESULTADO                                                 │
│  {                                                                      │
│    "success": true,                                                    │
│    "empleados_consolidados": 150,                                      │
│    "headers_consolidados": 12000,                                      │
│    "movimientos_consolidados": 80,                                     │
│    "conceptos_consolidados": 600,                                      │
│    "duracion_segundos": 45.3,                                          │
│    "estado_final": "datos_consolidados"                                │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  🖥️  FRONTEND: POLLING & ACTUALIZACIÓN UI                              │
│  ┌────────────────────────────────────────┐                            │
│  │ WHILE task_status == 'PENDING':        │                            │
│  │   • Mostrar spinner                    │                            │
│  │   • Polling cada 3 segundos            │                            │
│  │   • GET /task-status/{task_id}/        │                            │
│  └────────────────────────────────────────┘                            │
│                                                                         │
│  ┌────────────────────────────────────────┐                            │
│  │ IF task_status == 'SUCCESS':           │                            │
│  │   🎉 Mostrar toast de éxito            │                            │
│  │   🔄 Refrescar datos del cierre        │                            │
│  │   ✅ Actualizar UI                     │                            │
│  └────────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 DATOS GENERADOS

### **Por cada consolidación**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📦 NominaConsolidada (1 por empleado)                                  │
│  ├─→ rut_empleado: "123456789"          (normalizado)                  │
│  ├─→ nombre_empleado: "Juan Pérez"                                     │
│  ├─→ estado_empleado: "activo"                                         │
│  ├─→ haberes_imponibles: 1,500,000                                     │
│  ├─→ haberes_no_imponibles: 50,000                                     │
│  ├─→ dctos_legales: 200,000                                            │
│  └─→ liquido: 1,350,000                                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  📋 HeaderValorEmpleado (80-100 por empleado)                           │
│  ├─→ nombre_header: "SUELDO BASE"                                      │
│  ├─→ valor_original: "$1.200.000"                                      │
│  ├─→ valor_numerico: 1200000           (parseado)                      │
│  ├─→ es_numerico: true                                                 │
│  └─→ concepto_remuneracion: ConceptoRemuneracion(...)                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  🔄 MovimientoPersonal (variable por empleado)                          │
│  ├─→ categoria: "ausencia"                                             │
│  ├─→ subtipo: "vacaciones"                                             │
│  ├─→ fecha_inicio: 2025-10-15                                          │
│  ├─→ fecha_fin: 2025-10-19                                             │
│  ├─→ dias_evento: 5                                                    │
│  ├─→ dias_en_periodo: 5                                                │
│  ├─→ multi_mes: false                                                  │
│  └─→ hash_evento: "sha1..."               (único)                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  💰 ConceptoConsolidado (20-30 por empleado)                            │
│  ├─→ nombre_concepto: "SUELDO BASE"                                    │
│  ├─→ tipo_concepto: "haber_imponible"                                  │
│  ├─→ monto_total: 1,200,000                                            │
│  └─→ cantidad: 1                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ OPTIMIZACIONES

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🧮 CHUNKS DINÁMICOS                                                    │
│  ├─→ ≤ 50 empleados   → chunks de 25                                   │
│  ├─→ ≤ 200 empleados  → chunks de 50   ✅ (para 150 empleados)         │
│  ├─→ ≤ 500 empleados  → chunks de 100                                  │
│  ├─→ ≤ 1000 empleados → chunks de 150                                  │
│  └─→ > 1000 empleados → chunks de 200                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  📦 BULK OPERATIONS                                                     │
│  ├─→ NominaConsolidada: bulk_create(batch)                             │
│  ├─→ HeaderValorEmpleado: bulk_create() cada 500                       │
│  ├─→ MovimientoPersonal: bulk_create() cada 100                        │
│  └─→ ConceptoConsolidado: bulk_create() cada 200                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  🔗 CELERY CHAIN (Procesamiento en Secuencia)                          │
│  ├─→ Step 1: procesar_empleados_libro_paralelo                         │
│  ├─→ Step 2: procesar_movimientos_personal_paralelo                    │
│  └─→ Step 3: finalizar_consolidacion_post_movimientos                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📈 MÉTRICAS

```
┌───────────────────────────────────────┬─────────────────────────────────┐
│  EMPRESA MEDIANA (150 empleados)     │  EMPRESA GRANDE (500 empleados) │
├───────────────────────────────────────┼─────────────────────────────────┤
│  ⏱️  Tiempo: ~45 segundos             │  ⏱️  Tiempo: ~2.5 minutos       │
│  📊 Empleados: 150                    │  📊 Empleados: 500              │
│  📋 Headers: 12,000                   │  📋 Headers: 40,000             │
│  🔄 Movimientos: 80                   │  🔄 Movimientos: 250            │
│  💰 Conceptos: 600                    │  💰 Conceptos: 2,000            │
│  🎯 Chunk size: 50                    │  🎯 Chunk size: 100             │
└───────────────────────────────────────┴─────────────────────────────────┘
```

---

## 🎯 RESUMEN

✅ **Sistema COMPLETAMENTE refactorizado**  
✅ **Sin dependencias de tasks.py**  
✅ **19 funciones/tasks incluidas**  
✅ **Dual logging implementado**  
✅ **Optimizado con bulk operations**  
✅ **Chunks dinámicos según tamaño empresa**  
✅ **Procesamiento paralelo con Celery Chain**  
✅ **Manejo robusto de errores**  
✅ **Listo para producción** 🚀
