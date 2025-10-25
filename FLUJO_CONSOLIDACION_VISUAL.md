# 🔄 FLUJO DE CONSOLIDACIÓN DE DATOS - SISTEMA SGM NÓMINA

**Versión**: 3.0.0 Refactorizado  
**Fecha**: 24 de octubre 2025  
**Módulo**: `backend/nomina/tasks_refactored/consolidacion.py`

---

## 📊 DIAGRAMA DE FLUJO COMPLETO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         🖥️  FRONTEND (React)                            │
│                   VerificacionControl.jsx                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Usuario presiona "Consolidar Datos"
                                    ↓
              ┌─────────────────────────────────────────┐
              │  API Call: consolidarDatosTalana()      │
              │  POST /nomina/consolidacion/{id}/       │
              │       consolidar/                       │
              │  Payload: { modo: 'optimizado' }       │
              └─────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      🐍 BACKEND - Django REST API                        │
│                   views_consolidacion.py                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                     ✅ VALIDACIONES │
                                    ├──→ 1. Cierre existe?
                                    ├──→ 2. Estado válido? (verificado_sin_discrepancias,
                                    │                        datos_consolidados,
                                    │                        con_incidencias)
                                    ├──→ 3. Archivo Libro procesado?
                                    └──→ 4. Archivo Movimientos procesado?
                                    │
                                    ↓
              ┌─────────────────────────────────────────┐
              │  🚀 LANZAR TAREA CELERY                 │
              │  consolidar_datos_nomina_con_logging    │
              │    .delay(                              │
              │      cierre_id=123,                     │
              │      usuario_id=456,                    │
              │      modo='optimizado'                  │
              │    )                                    │
              └─────────────────────────────────────────┘
                                    │
                                    ↓
              ┌─────────────────────────────────────────┐
              │  📝 REGISTRAR ACTIVIDAD UI              │
              │  registrar_actividad_tarjeta_nomina(    │
              │    tarjeta="consolidacion",             │
              │    accion="consolidar_datos_inicio"     │
              │  )                                      │
              └─────────────────────────────────────────┘
                                    │
                                    ↓
              ┌─────────────────────────────────────────┐
              │  ↩️  RETORNAR A FRONTEND                │
              │  Response: {                            │
              │    "task_id": "abc-123-xyz",            │
              │    "cierre_id": 123                     │
              │  }                                      │
              │  Status: 202 ACCEPTED                   │
              └─────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    🔄 CELERY WORKER - Async Task                         │
│           tasks_refactored/consolidacion.py                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    │  @shared_task(bind=True, queue='nomina_queue')                │
    │  consolidar_datos_nomina_con_logging(self, cierre_id, ...)    │
    └───────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
              ┌─────────────────────────────────────────┐
              │  📊 DUAL LOGGING: INICIO                │
              │  ├─→ log_consolidacion_start()          │
              │  │   ├─→ TarjetaActivityLogNomina       │
              │  │   │   (tarjeta="consolidacion",      │
              │  │   │    accion="consolidacion_        │
              │  │   │            iniciada")             │
              │  │   └─→ ActivityEvent                  │
              │  │       (action=PROCESS_START)         │
              │  └─→ Logger: "🔄 Iniciando..."          │
              └─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │  ¿Modo = 'optimizado'?        │
                    └───────────────┬───────────────┘
                           SÍ │            │ NO
                              ↓            ↓
                    ┌──────────────┐  ┌──────────────────┐
                    │ OPTIMIZADO   │  │   SECUENCIAL     │
                    │ (Paralelo)   │  │   (Lineal)       │
                    └──────────────┘  └──────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    🚀 MODO OPTIMIZADO (Celery Chain)                     │
│             consolidar_datos_nomina_task_optimizado()                   │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  📋 VERIFICAR PRERREQUISITOS                │
        │  ├─→ Obtener CierreNomina                   │
        │  ├─→ Verificar estado                       │
        │  ├─→ Marcar: estado_consolidacion =         │
        │  │            'consolidando'                 │
        │  ├─→ Verificar LibroRemuneraciones          │
        │  └─→ Verificar MovimientosMes               │
        └─────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  🗑️  LIMPIAR CONSOLIDACIÓN ANTERIOR        │
        │  ├─→ Eliminar MovimientoPersonal            │
        │  ├─→ Eliminar NominaConsolidada             │
        │  └─→ Logger: "✅ X registros eliminados"   │
        └─────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  🧮 CALCULAR CHUNK SIZE DINÁMICO            │
        │  empleados_count = 150                      │
        │  chunk_size = calcular_chunk_size_dinamico( │
        │                 empleados_count              │
        │               ) = 50                         │
        └─────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  🔗 CREAR CELERY CHAIN                      │
        │  chain(                                     │
        │    procesar_empleados_libro_paralelo,       │
        │    procesar_movimientos_personal_paralelo,  │
        │    finalizar_consolidacion_post_movimientos │
        │  ).apply_async()                            │
        └─────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ↓                                   │
┌───────────────────────────────────┐          │
│  STEP 1: PROCESAR EMPLEADOS       │          │
│  procesar_empleados_libro_paralelo│          │
└───────────────────────────────────┘          │
            │                                   │
            ↓                                   │
    FOR i in range(0, total_empleados,         │
                   chunk_size):                │
        batch = empleados[i:i+chunk_size]      │
                                                │
        ┌─────────────────────────────┐        │
        │  📦 PROCESAR BATCH           │        │
        │  (50 empleados)             │        │
        │  ├─→ Crear NominaConsolidada│        │
        │  │   bulk_create()          │        │
        │  │                           │        │
        │  ├─→ Para cada empleado:    │        │
        │  │   │                       │        │
        │  │   ├─→ Normalizar RUT     │        │
        │  │   │   "12.345.678-9"     │        │
        │  │   │   → "123456789"      │        │
        │  │   │                       │        │
        │  │   └─→ Crear Headers:     │        │
        │  │       FOR concepto in    │        │
        │  │         empleado.conceptos:│       │
        │  │         │                 │        │
        │  │         ├─→ Validar si   │        │
        │  │         │   es numérico  │        │
        │  │         │   (Decimal)    │        │
        │  │         │                 │        │
        │  │         └─→ HeaderValor  │        │
        │  │             Empleado(    │        │
        │  │               nomina,    │        │
        │  │               nombre_    │        │
        │  │                 header,  │        │
        │  │               valor,     │        │
        │  │               es_numerico│        │
        │  │             )            │        │
        │  │                           │        │
        │  └─→ bulk_create(headers)   │        │
        │      cada 500 registros     │        │
        └─────────────────────────────┘        │
                                                │
    Logger: "📊 Progreso: 50/150 empleados"    │
    Logger: "📊 Progreso: 100/150 empleados"   │
    Logger: "📊 Progreso: 150/150 empleados"   │
                                                │
    ✅ RESULTADO:                               │
    {                                           │
      'success': True,                          │
      'empleados_consolidados': 150,            │
      'headers_consolidados': 12000             │
    }                                           │
            │                                   │
            ↓                                   │
┌───────────────────────────────────┐          │
│  STEP 2: PROCESAR MOVIMIENTOS     │          │
│  procesar_movimientos_personal_   │          │
│  paralelo                         │          │
└───────────────────────────────────┘          │
            │                                   │
            ↓                                   │
    ┌──────────────────────────────┐           │
    │  🔍 BUSCAR MOVIMIENTOS       │           │
    │  ├─→ MovimientoAltaBaja      │           │
    │  ├─→ MovimientoAusentismo    │           │
    │  ├─→ MovimientoVacaciones    │           │
    │  ├─→ MovimientoVariacion     │           │
    │  │      Sueldo               │           │
    │  └─→ MovimientoVariacion     │           │
    │       Contrato               │           │
    └──────────────────────────────┘           │
            │                                   │
            ↓                                   │
    FOR cada tipo de movimiento:               │
                                                │
        ┌────────────────────────────┐         │
        │  🔄 PROCESAR MOVIMIENTO    │         │
        │  ├─→ Buscar empleado por   │         │
        │  │   RUT normalizado       │         │
        │  │                          │         │
        │  ├─→ Actualizar estado_    │         │
        │  │   empleado si aplica    │         │
        │  │   (finiquito, ausente,  │         │
        │  │    nueva_incorporacion) │         │
        │  │                          │         │
        │  ├─→ Calcular:             │         │
        │  │   - fecha_inicio        │         │
        │  │   - fecha_fin           │         │
        │  │   - dias_evento         │         │
        │  │   - dias_en_periodo     │         │
        │  │   - multi_mes (flag)    │         │
        │  │                          │         │
        │  ├─→ Generar hash único:   │         │
        │  │   SHA1(rut:categoria:   │         │
        │  │        subtipo:fechas)  │         │
        │  │                          │         │
        │  └─→ Crear MovimientoPers  │         │
        │      onal(...)             │         │
        └────────────────────────────┘         │
                                                │
    bulk_create() cada 100 movimientos         │
                                                │
    Logger: "✅ 10 altas/bajas procesados"     │
    Logger: "✅ 25 ausentismos procesados"     │
    Logger: "✅ 15 vacaciones procesadas"      │
                                                │
    ✅ RESULTADO:                               │
    {                                           │
      'success': True,                          │
      'movimientos_creados': 80                 │
    }                                           │
            │                                   │
            ↓                                   │
┌───────────────────────────────────┐          │
│  STEP 3: FINALIZAR CONSOLIDACIÓN  │          │
│  finalizar_consolidacion_post_    │          │
│  movimientos                      │          │
└───────────────────────────────────┘          │
            │                                   │
            ↓                                   │
    ┌──────────────────────────────┐           │
    │  💰 PROCESAR CONCEPTOS       │           │
    │  procesar_conceptos_         │           │
    │  consolidados_paralelo       │           │
    └──────────────────────────────┘           │
            │                                   │
            ↓                                   │
    FOR nomina in NominaConsolidada:           │
                                                │
        ┌────────────────────────────┐         │
        │  📊 AGRUPAR CONCEPTOS      │         │
        │  ├─→ Obtener headers con   │         │
        │  │   concepto_remuneracion │         │
        │  │                          │         │
        │  ├─→ Agrupar por:          │         │
        │  │   - nombre_concepto     │         │
        │  │   - clasificacion       │         │
        │  │                          │         │
        │  ├─→ Calcular totales por  │         │
        │  │   categoría:            │         │
        │  │   • haberes_imponibles  │         │
        │  │   • haberes_no_impon... │         │
        │  │   • dctos_legales       │         │
        │  │   • otros_dctos         │         │
        │  │   • impuestos           │         │
        │  │   • horas_extras        │         │
        │  │   • aportes_patronales  │         │
        │  │                          │         │
        │  ├─→ Crear ConceptoCons... │         │
        │  │   para cada concepto    │         │
        │  │   agrupado              │         │
        │  │                          │         │
        │  └─→ Actualizar campos de  │         │
        │      totales en nomina     │         │
        └────────────────────────────┘         │
                                                │
    bulk_create(conceptos) cada 200            │
                                                │
    ✅ RESULTADO:                               │
    {                                           │
      'success': True,                          │
      'conceptos_consolidados': 600             │
    }                                           │
            │                                   │
            ↓                                   │
    ┌──────────────────────────────┐           │
    │  🎯 ACTUALIZAR ESTADO FINAL  │           │
    │  ├─→ Si estado != 'con_      │           │
    │  │   incidencias':           │           │
    │  │   cierre.estado =         │           │
    │  │     'datos_consolidados'  │           │
    │  │                            │           │
    │  ├─→ cierre.estado_          │           │
    │  │   consolidacion =         │           │
    │  │     'consolidado'         │           │
    │  │                            │           │
    │  └─→ cierre.fecha_           │           │
    │      consolidacion = now()   │           │
    └──────────────────────────────┘           │
            │                                   │
            ↓                                   │
    ┌──────────────────────────────┐           │
    │  🧩 ¿Estado = 'con_          │           │
    │     incidencias'?            │           │
    └──────────────────────────────┘           │
            │                                   │
            ├──→ SÍ: Disparar                  │
            │    generar_incidencias_          │
            │    con_logging.delay()           │
            │    (tasks_refactored)            │
            │                                   │
            └──→ NO: Continuar                 │
                                                │
    ✅ RESULTADO FINAL:                         │
    {                                           │
      'success': True,                          │
      'cierre_id': 123,                         │
      'conceptos_consolidados': 600,            │
      'nuevo_estado': 'datos_consolidados'      │
    }                                           │
            │                                   │
            └───────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  📊 DUAL LOGGING: ÉXITO                     │
        │  ├─→ log_consolidacion_complete()           │
        │  │   ├─→ TarjetaActivityLogNomina           │
        │  │   │   (accion="consolidacion_completada",│
        │  │   │    resultado="exito",                │
        │  │   │    detalles={estadísticas})          │
        │  │   └─→ ActivityEvent                      │
        │  │       (action=DATA_INTEGRATION_COMPLETE) │
        │  └─→ Logger: "✅ Consolidación completada"  │
        └─────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │  ↩️  RETORNAR RESULTADO                     │
        │  {                                          │
        │    'success': True,                         │
        │    'empleados_consolidados': 150,           │
        │    'headers_consolidados': 12000,           │
        │    'movimientos_consolidados': 80,          │
        │    'conceptos_consolidados': 600,           │
        │    'duracion_segundos': 45.3,               │
        │    'estado_final': 'datos_consolidados'     │
        │  }                                          │
        └─────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    🖥️  FRONTEND - Polling & UI Update                   │
└─────────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │  ⏱️  POLLING CADA 3 SEGUNDOS              │
        │  GET /nomina/task-status/{task_id}/       │
        └───────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │  estado = 'PENDING'?              │
            └─────────────────┬─────────────────┘
                    SÍ │             │ NO
                       │             ↓
                       │    ┌────────────────────┐
                       │    │  estado = 'SUCCESS'│
                       │    └────────────────────┘
                       │             │
                       │             ↓
                       │    ┌────────────────────┐
                       │    │  🎉 MOSTRAR ÉXITO  │
                       │    │  - Toast success   │
                       │    │  - Actualizar UI   │
                       │    │  - Refrescar datos │
                       │    └────────────────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │  🔄 Continuar polling │
            │  Mostrar spinner     │
            └──────────────────────┘

```

---

## 🔑 CONCEPTOS CLAVE

### **1. Normalización de RUT**
```python
normalizar_rut("12.345.678-9")  →  "123456789"
normalizar_rut("12345678-9")    →  "123456789"
normalizar_rut("12.345.678-K")  →  "12345678K"
```

### **2. Chunk Size Dinámico**
```python
≤ 50 empleados   → chunk_size = 25
≤ 200 empleados  → chunk_size = 50  ✅ Ejemplo: 150 empleados
≤ 500 empleados  → chunk_size = 100
≤ 1000 empleados → chunk_size = 150
> 1000 empleados → chunk_size = 200
```

### **3. Dual Logging**
```python
# Log 1: UI Visible (TarjetaActivityLogNomina)
registrar_actividad_tarjeta_nomina(
    tarjeta="consolidacion",
    accion="consolidacion_iniciada",
    descripcion="Iniciando consolidación..."
)

# Log 2: Sistema (ActivityEvent)
ActivityEvent.log(
    action=PROCESS_START,
    resource_type='cierre_nomina',
    resource_id=str(cierre_id)
)
```

### **4. Estados del Cierre**
```
verificado_sin_discrepancias  →  [CONSOLIDAR]  →  datos_consolidados
                                                        ↓
                                                   (flujo continúa)
                                                        ↓
                                                 analisis_financiero
```

### **5. Modelos Generados**

#### **NominaConsolidada** (1 por empleado)
```python
{
  'rut_empleado': '123456789',
  'nombre_empleado': 'Juan Pérez González',
  'estado_empleado': 'activo',  # activo, finiquito, ausente_total, etc.
  'haberes_imponibles': Decimal('1500000'),
  'haberes_no_imponibles': Decimal('50000'),
  'dctos_legales': Decimal('200000'),
  'liquido': Decimal('1350000')
}
```

#### **HeaderValorEmpleado** (N por empleado)
```python
{
  'nombre_header': 'SUELDO BASE',
  'valor_original': '$1.200.000',
  'valor_numerico': Decimal('1200000'),
  'es_numerico': True,
  'concepto_remuneracion': ConceptoRemuneracion(...)
}
```

#### **MovimientoPersonal** (0-N por empleado)
```python
{
  'categoria': 'ausencia',
  'subtipo': 'vacaciones',
  'fecha_inicio': date(2025, 10, 15),
  'fecha_fin': date(2025, 10, 19),
  'dias_evento': 5,
  'dias_en_periodo': 5,
  'multi_mes': False
}
```

#### **ConceptoConsolidado** (N por empleado)
```python
{
  'nombre_concepto': 'SUELDO BASE',
  'tipo_concepto': 'haber_imponible',
  'monto_total': Decimal('1200000'),
  'cantidad': 1
}
```

---

## ⚡ OPTIMIZACIONES IMPLEMENTADAS

### **1. Bulk Operations**
- ✅ `NominaConsolidada.objects.bulk_create(nominas_batch)`
- ✅ `HeaderValorEmpleado.objects.bulk_create(headers_batch)` cada 500
- ✅ `MovimientoPersonal.objects.bulk_create(movimientos_batch)` cada 100
- ✅ `ConceptoConsolidado.objects.bulk_create(conceptos_batch)` cada 200

### **2. Celery Chain**
- ✅ Procesamiento secuencial con tasks paralelas internas
- ✅ Empleados → Movimientos → Conceptos (dependencias respetadas)
- ✅ Callback automático al finalizar cada step

### **3. Prefetch & Select Related**
```python
nominas = NominaConsolidada.objects.filter(cierre=cierre).prefetch_related(
    'header_valores__concepto_remuneracion'
)
```

### **4. Transaccionalidad**
- ✅ Limpieza completa antes de consolidar
- ✅ Rollback automático en caso de error
- ✅ Estado del cierre revertido si falla

---

## 📈 MÉTRICAS DE EJEMPLO

**Empresa Mediana (150 empleados)**:
```
⏱️  Tiempo total: ~45 segundos
📊 Empleados consolidados: 150
📋 Headers creados: 12,000 (80 conceptos × 150 empleados)
🔄 Movimientos detectados: 80
💰 Conceptos consolidados: 600
🎯 Chunk size usado: 50
```

**Empresa Grande (500 empleados)**:
```
⏱️  Tiempo total: ~2.5 minutos
📊 Empleados consolidados: 500
📋 Headers creados: 40,000
🔄 Movimientos detectados: 250
💰 Conceptos consolidados: 2,000
🎯 Chunk size usado: 100
```

---

## 🚨 MANEJO DE ERRORES

### **Error en Empleados**
```python
try:
    # Procesar empleado
except Exception as e:
    logger.error(f"❌ Error procesando empleado {empleado.rut}: {e}")
    continue  # Saltar y continuar con el siguiente
```

### **Error Global**
```python
try:
    # Consolidación completa
except Exception as e:
    # 1. Log error (dual logging)
    log_consolidacion_error(cierre_id, usuario_id, str(e))
    
    # 2. Revertir estado
    cierre.estado = 'verificado_sin_discrepancias'
    cierre.estado_consolidacion = 'error'
    cierre.save()
    
    # 3. Re-lanzar excepción
    raise
```

---

## 🔍 DEBUGGING

### **Ver Logs en Tiempo Real**
```bash
# Logs de Django
docker compose logs -f django

# Logs de Celery Worker
docker compose logs -f celery_worker

# Filtrar por consolidación
docker compose logs celery_worker | grep "CONSOLIDACIÓN"
```

### **Verificar Estado en DB**
```python
# En Django shell
cierre = CierreNomina.objects.get(id=123)
print(f"Estado: {cierre.estado}")
print(f"Estado consolidación: {cierre.estado_consolidacion}")
print(f"Empleados: {cierre.nomina_consolidada.count()}")
print(f"Movimientos: {MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).count()}")
```

---

## ✅ CHECKLIST DE ÉXITO

Después de una consolidación exitosa:

- [x] `cierre.estado = 'datos_consolidados'`
- [x] `cierre.estado_consolidacion = 'consolidado'`
- [x] `cierre.fecha_consolidacion` tiene timestamp
- [x] `NominaConsolidada` tiene N registros (1 por empleado)
- [x] `HeaderValorEmpleado` tiene N×80 registros aprox
- [x] `MovimientoPersonal` tiene M registros (según movimientos detectados)
- [x] `ConceptoConsolidado` tiene agrupaciones por concepto
- [x] Logs en `TarjetaActivityLogNomina` con acción "consolidacion_completada"
- [x] Logs en `ActivityEvent` con action "Data_Integration_Complete"

---

**🎯 Este flujo garantiza:**
1. ✅ Procesamiento eficiente y escalable
2. ✅ Trazabilidad completa (dual logging)
3. ✅ Manejo robusto de errores
4. ✅ UI responsiva con feedback en tiempo real
5. ✅ Integridad de datos garantizada
