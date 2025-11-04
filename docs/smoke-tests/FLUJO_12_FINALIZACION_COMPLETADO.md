# 📋 FLUJO 12: FINALIZACIÓN DEL CIERRE - DOCUMENTACIÓN TÉCNICA

**Estado**: ✅ COMPLETADO  
**Fecha Documentación**: 4 de noviembre de 2025  
**Cierre de Prueba**: #35 (EMPRESA SMOKE TEST - Octubre 2025)  
**Usuario**: admin  

---

## 📊 RESUMEN EJECUTIVO

El flujo de finalización es el último paso del proceso de cierre de nómina. Convierte un cierre en estado `incidencias_resueltas` a estado `finalizado`, generando informes consolidados (Libro de Remuneraciones y Movimientos del Mes) y guardándolos tanto en base de datos como en Redis para acceso rápido.

### Características Principales
- ✅ **Validación de pre-requisitos**: Verifica estado y datos consolidados
- ✅ **Procesamiento asíncrono**: Usa Celery chord para paralelizar generación
- ✅ **Generación de informes**: Libro y Movimientos en formato JSON
- ✅ **Cache inteligente**: Almacena en Redis con TTL de 72 horas
- ✅ **Auditoría completa**: Registra usuario y timestamp de finalización

### Flujo Observado
```
POST /api/nomina/cierres/35/finalizar/
  ↓
HTTP 202 ACCEPTED (task_id: 477a8df5-b74f-4343-834c-566e1a77e99c)
  ↓
[CELERY CHORD]
├── build_informe_libro [b0a109cd] → 0.046s
├── build_informe_movimientos [b132cfd4] → 0.032s
  ↓
└── unir_y_guardar_informe [ffb39834] → 0.037s
      ↓
    enviar_informe_redis_task [91113076] → 0.037s
      ↓
    finalizar_cierre_post_informe [477a8df5] → 0.025s
```

**Tiempo total de ejecución**: ~177ms (procesamiento completo)

---

## 🎯 ARQUITECTURA DEL FLUJO

### 1️⃣ ENDPOINT DE FINALIZACIÓN

**Archivo**: `backend/nomina/views_finalizacion.py`

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def finalizar_cierre_view(request, pk: int):
    """
    Endpoint explícito para finalizar un cierre y generar el informe con Celery chord.
    """
```

**Ruta**: `POST /api/nomina/cierres/{id}/finalizar/`

#### Validaciones Pre-Ejecución

1. **Autenticación**: Usuario debe estar autenticado
2. **Existencia del cierre**: Verifica que `CierreNomina.id` exista
3. **Estado correcto**: Debe estar en `estado='incidencias_resueltas'`
4. **Datos consolidados**: Debe tener registros en `NominaConsolidada`

#### Respuestas Posibles

| HTTP | Condición | Response |
|------|-----------|----------|
| 202 | Éxito | `{'success': True, 'task_id': '...', 'cierre_id': 35}` |
| 400 | Estado incorrecto | `{'error': 'Estado incorrecto', 'estado_actual': '...'}` |
| 404 | Cierre no existe | `{'error': 'Cierre no encontrado'}` |
| 409 | Sin datos consolidados | `{'error': 'No hay datos consolidados'}` |
| 500 | Error interno | `{'error': 'Error interno', 'message': '...'}` |

### Ejemplo de Response Exitosa
```json
{
  "success": true,
  "message": "Finalización iniciada. Generando informe y cerrando.",
  "cierre_id": 35,
  "task_id": "477a8df5-b74f-4343-834c-566e1a77e99c"
}
```

---

## ⚙️ TAREAS DE CELERY (Chord)

**Archivo**: `backend/nomina/tasks_refactored/informes.py`

### Estructura del Chord

```python
# Tareas paralelas (ejecutan simultáneamente)
tasks = [
    build_informe_libro.s(cierre.id),
    build_informe_movimientos.s(cierre.id),
]

# Tareas secuenciales (callback chain)
callback_guardar = unir_y_guardar_informe.s(cierre.id)
callback_en_redis = enviar_informe_redis_task.s(cierre.id, ttl_hours=72)
callback_final = finalizar_cierre_post_informe.s(cierre.id, usuario_id)

# Ejecución: tasks en paralelo → guardar → redis → finalizar
result = chord(tasks)(callback_guardar | callback_en_redis | callback_final)
```

---

### TASK 1: `build_informe_libro`

**Función**: Genera el payload del Libro de Remuneraciones desde `NominaConsolidada`

**Input**: `cierre_id: int`

**Output**: JSON con estructura `libro_resumen_v2`

#### Queries Ejecutadas
1. Resumen agregado de `NominaConsolidada`:
   - Total empleados
   - Suma de haberes imponibles/no imponibles
   - Suma de descuentos legales/otros
   - Suma de impuestos y aportes patronales
   - Total horas extras

2. Desglose por concepto desde `ConceptoConsolidado`:
   - Agrupación por `tipo_concepto` + `nombre_concepto`
   - Cálculo de montos totales y cantidad
   - Conteo de empleados afectados (distinct con monto != 0)

#### Estructura de Output
```json
{
  "cierre": {
    "id": 35,
    "cliente": "EMPRESA SMOKE TEST",
    "periodo": "2025-10",
    "total_empleados": 5
  },
  "totales_categorias": {
    "haber_imponible": 7500000.0,
    "haber_no_imponible": 400000.0,
    "descuento_legal": -150000.0,
    "otro_descuento": -5000.0,
    "impuesto": -375000.0,
    "aporte_patronal": -300000.0
  },
  "conceptos": [
    {
      "nombre": "SUELDO BASE",
      "categoria": "haber_imponible",
      "total": 7500000.0,
      "empleados": 5
    },
    // ... más conceptos
  ],
  "meta": {
    "conceptos_count": 8,
    "generated_at": "2025-11-04T16:04:33.008Z",
    "api_version": "2"
  }
}
```

**Tiempo observado**: 46ms (task b0a109cd)

---

### TASK 2: `build_informe_movimientos`

**Función**: Genera resumen de Movimientos del Personal desde `MovimientoPersonal`

**Input**: `cierre_id: int`

**Output**: JSON con estructura `movimientos_v3`

#### Queries Ejecutadas
1. Todos los `MovimientoPersonal` del cierre con `select_related('nomina_consolidada')`
2. Agrupación por categoría con empleados únicos
3. Análisis de ausentismo (eventos, días totales, promedio, subtipos)
4. Métricas de cambios (contrato/sueldo)

#### Estructura de Output
```json
{
  "cierre": {
    "id": 35,
    "cliente": "EMPRESA SMOKE TEST",
    "periodo": "2025-10"
  },
  "resumen": {
    "total_movimientos": 9,
    "por_tipo": {
      "cambio_datos": {"count": 6, "empleados_unicos": 3},
      "ausencia": {"count": 3, "empleados_unicos": 3}
    },
    "ausentismo_metricas": {
      "eventos": 3,
      "total_dias": 15,
      "promedio_dias": 5.0,
      "subtipos": [
        {"subtipo": "licencia_medica", "eventos": 2, "dias": 10},
        {"subtipo": "vacaciones", "eventos": 1, "dias": 5}
      ]
    },
    "cambios_metricas": [
      {"subtipo": "cambio_contrato", "eventos": 4},
      {"subtipo": "cambio_sueldo", "eventos": 2}
    ]
  },
  "movimientos": [
    {
      "id": 5215,
      "categoria": "cambio_datos",
      "subtipo": "cambio_contrato",
      "descripcion": "Cambio de contrato: de Jornada Completa a Part-Time",
      "fecha_inicio": "2021-06-01",
      "fecha_fin": "2021-06-01",
      "dias_evento": 1,
      "dias_en_periodo": 1,
      "multi_mes": false,
      "hash_evento": null,
      "hash_registro_periodo": null,
      "empleado": {
        "rut": "12345678-9",
        "nombre": "Juan Pérez",
        "cargo": "Desarrollador",
        "centro_costo": "TI",
        "estado": "ACTIVO",
        "liquido_pagar": 1450000.0
      },
      "observaciones": "De Jornada Completa a Part-Time",
      "fecha_deteccion": "2025-10-29T15:29:24.984143Z",
      "detectado_por_sistema": "consolidacion_refactored_v3"
    }
    // ... más movimientos
  ],
  "meta": {
    "generated_at": "2025-11-04T16:04:33.032Z",
    "api_version": "3"
  }
}
```

**Tiempo observado**: 32ms (task b132cfd4)

---

### TASK 3: `unir_y_guardar_informe`

**Función**: Unifica los informes y guarda en `InformeNomina`

**Input**: `resultados: list, cierre_id: int, version: str = 'sgm-v1'`

**Operaciones**:
1. Recibe resultados de las 2 tareas paralelas anteriores
2. Construye payload unificado con metadatos
3. Crea o actualiza registro en tabla `InformeNomina`
4. Calcula `tiempo_calculo` (inicio hasta save)

#### Estructura del Payload Final
```json
{
  "meta": {
    "cliente_id": 20,
    "cliente_nombre": "EMPRESA SMOKE TEST",
    "periodo": "2025-10",
    "generated_at": "2025-11-04T16:04:33.055Z",
    "version_datos": 1,
    "version_calculo": "sgm-v1"
  },
  "libro_resumen_v2": { /* output de build_informe_libro */ },
  "movimientos_v3": { /* output de build_informe_movimientos */ }
}
```

#### Modelo InformeNomina
```python
class InformeNomina(models.Model):
    cierre = models.OneToOneField(CierreNomina, ...)
    datos_cierre = models.JSONField()  # Contiene el payload completo
    version_calculo = models.CharField(max_length=10)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tiempo_calculo = models.DurationField(null=True)
```

**Output**: `{'informe_id': 39, 'cierre_id': 35, 'saved': True}`

**Tiempo observado**: 37ms (task ffb39834)

---

### TASK 4: `enviar_informe_redis_task`

**Función**: Envía el informe completo a Redis para cache rápido

**Input**: `prev_result: dict, cierre_id: int, ttl_hours: int = 72`

**Operaciones**:
1. Lee `InformeNomina` desde DB
2. Llama a `informe.enviar_a_redis(ttl_hours=72)`
3. Construye wrapper con metadatos y TTL

#### Estructura en Redis
```json
{
  "meta": {
    "cliente_id": 20,
    "periodo": "2025-10",
    "generated_at": "2025-11-04T16:04:33.096Z",
    "expiration_utc": "2025-11-07T16:04:33.096Z",
    "ttl_hours": 72
  },
  "data": {
    "libro_resumen_v2": { /* ... */ },
    "movimientos_v3": { /* ... */ }
  }
}
```

**Clave Redis**: `sgm:nomina:{cliente_id}:{periodo}:informe`  
**Ejemplo**: `sgm:nomina:20:2025-10:informe`

**TTL**: 72 horas (3 días)

**Output**: 
```json
{
  "informe_id": 39,
  "cierre_id": 35,
  "sent_to_redis": true,
  "redis_key": "sgm:nomina:20:2025-10:informe",
  "ttl_hours": 72
}
```

**Tiempo observado**: 37ms (task 91113076)

---

### TASK 5: `finalizar_cierre_post_informe`

**Función**: Marca el cierre como finalizado y registra auditoría

**Input**: `prev_result: dict, cierre_id: int, usuario_id: int`

**Operaciones**:
1. Actualiza `CierreNomina.estado = 'finalizado'`
2. Setea `CierreNomina.fecha_finalizacion = now()`
3. Asocia `CierreNomina.usuario_finalizacion = User(usuario_id)`
4. Guarda cambios

#### Campos Actualizados
```python
cierre.estado = 'finalizado'  # Estado final
cierre.fecha_finalizacion = timezone.now()
cierre.usuario_finalizacion = User.objects.get(id=usuario_id)
cierre.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
```

**Output**: 
```json
{
  "success": true,
  "cierre_id": 35,
  "finalizado": true,
  "informe_id": 39
}
```

**Tiempo observado**: 25ms (task 477a8df5)

---

## 🔍 POLLING DE ESTADO (Frontend)

Después de recibir el `task_id`, el frontend hace polling para monitorear progreso:

```javascript
// 1. Iniciar finalización
const response = await api.post(`/nomina/cierres/${cierreId}/finalizar/`);
const taskId = response.data.task_id;

// 2. Polling cada 2 segundos
const pollStatus = async () => {
  const status = await api.get(
    `/nomina/cierres/${cierreId}/task-status/${taskId}/`
  );
  
  if (status.data.state === 'SUCCESS') {
    // Finalización completada
    refreshCierreData();
  } else if (status.data.state === 'FAILURE') {
    // Error en procesamiento
    showError(status.data.result);
  } else {
    // Aún procesando (PENDING/STARTED)
    setTimeout(pollStatus, 2000);
  }
};
```

### Logs Observados del Polling

```
[04/Nov/2025 16:04:32] "OPTIONS /api/nomina/cierres/35/finalizar/" 200
[04/Nov/2025 16:04:32] "POST /api/nomina/cierres/35/finalizar/" 202
[04/Nov/2025 16:04:35] "OPTIONS /api/nomina/cierres/35/task-status/477a8df5/" 200
[04/Nov/2025 16:04:35] "GET /api/nomina/cierres/35/task-status/477a8df5/" 200
[04/Nov/2025 16:04:35] "GET /api/nomina/cierres/35/" 200
```

**Delay observado**: 3 segundos entre POST y primer GET de status (el frontend espera un momento antes de empezar a hacer polling)

---

## 📥 CONSUMO DEL INFORME (Frontend)

Una vez finalizado, el frontend accede al informe:

### Endpoint de Lectura
```
GET /api/nomina/cierres/{id}/informe/
```

### Logs Observados
```
[INFO] Informe de cierre 35 obtenido desde Redis
[04/Nov/2025 16:04:37] "GET /api/nomina/cierres/35/informe/" 200 7651
```

**Nota**: El log indica que el informe se sirvió desde **Redis** (no desde DB), demostrando que el cache está funcionando correctamente.

### Componentes Frontend que Consumen
1. **LibroRemuneraciones.jsx**: Lee `libro_resumen_v2`
2. **MovimientosMes.jsx**: Lee `movimientos_v3`

---

## 🎬 FLUJO COMPLETO CRONOLÓGICO

### Timeline de Ejecución Real (Cierre #35)

| Timestamp | Evento | Detalle |
|-----------|--------|---------|
| 16:04:32 | OPTIONS preflight | CORS check para `/finalizar/` |
| 16:04:32 | POST finalizar | Usuario presiona botón en frontend |
| 16:04:32 | HTTP 202 | Backend responde con task_id |
| 16:04:32 | Celery recibe tasks | Inicia chord con 2 tareas paralelas |
| 16:04:33 | Task libro completa | 46ms - Genera informe libro |
| 16:04:33 | Task movimientos completa | 32ms - Genera informe movimientos |
| 16:04:33 | Unir y guardar | 37ms - Crea InformeNomina #39 |
| 16:04:33 | Enviar a Redis | 37ms - Cache con TTL 72h |
| 16:04:33 | Finalizar cierre | 25ms - Estado='finalizado' |
| 16:04:35 | Primer polling | Frontend verifica estado (3s después) |
| 16:04:35 | GET cierre | Frontend recarga datos del cierre |
| 16:04:37 | GET informe | Frontend lee informe desde Redis |

**Duración total**: ~177ms (desde inicio de chord hasta finalizado)

---

## ✅ VALIDACIONES Y GARANTÍAS

### Pre-Finalización

| Validación | Ubicación | Efecto si Falla |
|-----------|-----------|-----------------|
| Usuario autenticado | `views_finalizacion.py:22` | HTTP 401 |
| Cierre existe | `views_finalizacion.py:18` | HTTP 404 |
| Estado = 'incidencias_resueltas' | `views_finalizacion.py:24` | HTTP 400 |
| Hay datos consolidados | `views_finalizacion.py:34` | HTTP 409 |

### Durante Procesamiento

| Garantía | Implementación |
|----------|----------------|
| Atomicidad | Cada task es transaccional |
| Orden de ejecución | Chord + pipe operator (`\|`) |
| Recuperación de errores | Celery retry policy |
| Auditoría | `fecha_finalizacion` + `usuario_finalizacion` |

### Post-Finalización

| Garantía | Validación |
|----------|-----------|
| Informe guardado | `InformeNomina` tiene registro |
| Cache disponible | Redis tiene la key con TTL |
| Estado correcto | `CierreNomina.estado == 'finalizado'` |
| Timestamp registrado | `fecha_finalizacion` != null |

---

## 🔄 TRANSICIONES DE ESTADO

```
incidencias_resueltas
         |
         | POST /finalizar/
         |
         ↓
    [PROCESANDO]
         |
         | Chord completa
         |
         ↓
    finalizado
```

### Estados del Cierre
- **Antes**: `estado='incidencias_resueltas'`, `fecha_finalizacion=null`
- **Durante**: Estado no cambia (sigue `incidencias_resueltas`)
- **Después**: `estado='finalizado'`, `fecha_finalizacion=timestamp`

### Estados de la Task (Celery)
- **PENDING**: Task recibida, no iniciada
- **STARTED**: Ejecutándose
- **SUCCESS**: Completada exitosamente
- **FAILURE**: Error en ejecución
- **RETRY**: Reintentando después de fallo

---

## 📊 DATOS DE EJEMPLO (Cierre #35)

### Datos de Entrada
- **Cliente**: EMPRESA SMOKE TEST (ID: 20)
- **Periodo**: 2025-10
- **Empleados**: 5
- **Estado inicial**: `incidencias_resueltas`
- **Registros consolidados**: Sí (NominaConsolidada + ConceptoConsolidado)

### Datos de Salida
- **InformeNomina ID**: 39
- **Task ID**: 477a8df5-b74f-4343-834c-566e1a77e99c
- **Estado final**: `finalizado`
- **Fecha finalización**: 2025-11-04 16:04:33 UTC
- **Usuario**: admin
- **Redis key**: `sgm:nomina:20:2025-10:informe`
- **TTL Redis**: 72 horas

### Métricas del Informe
**Libro de Remuneraciones**:
- Total empleados: 5
- Haberes imponibles: $7,500,000
- Haberes no imponibles: $400,000
- Descuentos legales: -$150,000
- Impuestos: -$375,000
- Conceptos únicos: 8

**Movimientos del Mes**:
- Total movimientos: 9
- Cambios de datos: 6 eventos, 3 empleados
- Ausentismo: 3 eventos, 15 días totales
- Promedio días ausencia: 5.0 días/evento

---

## 🐛 TROUBLESHOOTING

### Problema: "Estado incorrecto"

**Síntoma**: HTTP 400 con mensaje "El cierre debe estar en 'incidencias_resueltas'"

**Causas posibles**:
1. Cierre aún tiene incidencias pendientes
2. No se ejecutó el flujo de incidencias
3. Estado no se actualizó después de resolver incidencias

**Solución**:
```python
# Verificar estado de incidencias
from nomina.utils.reconciliacion import verificar_y_actualizar_estado_cierre
result = verificar_y_actualizar_estado_cierre(cierre_id)
print(result)
```

### Problema: "No hay datos consolidados"

**Síntoma**: HTTP 409 con mensaje sobre datos consolidados

**Causas posibles**:
1. No se ejecutó la consolidación
2. Consolidación falló silenciosamente
3. Datos eliminados por error

**Solución**:
```python
# Verificar consolidación
cierre = CierreNomina.objects.get(id=35)
print(f"Registros consolidados: {cierre.nomina_consolidada.count()}")

# Re-ejecutar si es necesario
from nomina.tasks_refactored.consolidacion import consolidar_cierre_con_logging
task = consolidar_cierre_con_logging.delay(cierre.id)
```

### Problema: Task se queda en PENDING

**Síntoma**: Polling infinito, task nunca cambia de PENDING

**Causas posibles**:
1. Workers de Celery no están corriendo
2. Redis no está disponible
3. Queue incorrecta (task enviada a queue que no existe)

**Solución**:
```bash
# Verificar workers
docker compose logs celery_worker | grep "ready"

# Verificar Redis
docker compose exec django redis-cli ping

# Ver estado de task
docker compose exec django python manage.py shell
>>> from celery.result import AsyncResult
>>> result = AsyncResult('477a8df5-b74f-4343-834c-566e1a77e99c')
>>> print(result.state, result.info)
```

### Problema: Informe no aparece en Redis

**Síntoma**: GET /informe/ devuelve datos desde DB, no desde Redis

**Causas posibles**:
1. Task `enviar_informe_redis_task` falló
2. Redis no tiene espacio
3. TTL ya expiró

**Solución**:
```bash
# Verificar clave en Redis
docker compose exec django redis-cli KEYS "sgm:nomina:20:2025-10:*"
docker compose exec django redis-cli GET "sgm:nomina:20:2025-10:informe"

# Ver TTL restante
docker compose exec django redis-cli TTL "sgm:nomina:20:2025-10:informe"

# Re-enviar manualmente
docker compose exec django python manage.py shell
>>> from nomina.models_informe import InformeNomina
>>> informe = InformeNomina.objects.get(cierre_id=35)
>>> informe.enviar_a_redis(ttl_hours=72)
```

---

## 🎓 CÓDIGO ACTIVO vs OBSOLETO

### ✅ CÓDIGO ACTIVO (EN USO)

| Archivo | Función/Clase | Uso |
|---------|---------------|-----|
| `views_finalizacion.py` | `finalizar_cierre_view()` | **Endpoint principal** |
| `tasks_refactored/informes.py` | `build_informe_libro()` | **Generación libro** |
| `tasks_refactored/informes.py` | `build_informe_movimientos()` | **Generación movimientos** |
| `tasks_refactored/informes.py` | `unir_y_guardar_informe()` | **Guardado en DB** |
| `tasks_refactored/informes.py` | `enviar_informe_redis_task()` | **Cache Redis** |
| `tasks_refactored/informes.py` | `finalizar_cierre_post_informe()` | **Cambio de estado** |
| `models_informe.py` | `InformeNomina` | **Modelo de datos** |
| `models_informe.py` | `InformeNomina.enviar_a_redis()` | **Método wrapper Redis** |

### ❌ CÓDIGO OBSOLETO (NO USAR)

| Archivo | Función/Clase | Razón de Obsolescencia |
|---------|---------------|------------------------|
| `tasks.py.original` | Tareas sin refactorizar | Reemplazadas por `tasks_refactored/` |
| `views.py` | `CierreNominaViewSet.finalizar_cierre()` | Action antiguo, reemplazado por view dedicada |
| Cualquier endpoint con `/api/cierres/{id}/finalizar_OLD/` | Endpoints deprecados | Usar `/finalizar/` sin sufijos |

---

## 📚 REFERENCIAS

### Endpoints Relacionados
- `POST /api/nomina/cierres/{id}/finalizar/` - Iniciar finalización
- `GET /api/nomina/cierres/{id}/task-status/{task_id}/` - Estado de task
- `GET /api/nomina/cierres/{id}/informe/` - Obtener informe
- `GET /api/nomina/cierres/{id}/` - Datos del cierre

### Modelos Involucrados
- `CierreNomina` - Cierre principal
- `InformeNomina` - Informe consolidado
- `NominaConsolidada` - Datos consolidados de empleados
- `ConceptoConsolidado` - Desglose de conceptos
- `MovimientoPersonal` - Movimientos del mes

### Archivos Frontend
- `src/api/nomina.js` - Cliente API
- `src/components/TarjetasCierreNomina/` - Tarjetas de cierre
- `src/pages/LibroRemuneraciones.jsx` - Vista de libro
- `src/pages/MovimientosMes.jsx` - Vista de movimientos

### Documentación Relacionada
- `FLUJO_INCIDENCIAS_ACTUAL.md` - Flujo previo de incidencias
- `PLAN_PRUEBA_SMOKE_TEST.md` - Plan maestro de pruebas
- `/docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md` - Arquitectura general

---

## 🎯 PRÓXIMOS PASOS

### Para Desarrollo
1. ✅ Flujo de finalización documentado y validado
2. ⏭️ Smoke test Flujo 12 completado
3. ⏭️ Actualizar `PLAN_PRUEBA_SMOKE_TEST.md` a 12/12 flujos

### Para QA
1. Validar finalización con diferentes tamaños de cierre
2. Probar comportamiento con Redis caído
3. Verificar TTL y expiración de cache
4. Stress test con finalizaciones concurrentes

### Para Producción
1. Monitorear tiempos de ejecución de tasks
2. Ajustar TTL de Redis según patrones de uso
3. Configurar alertas para tasks PENDING > 30s
4. Implementar retry policy para tasks críticas

---

**Documentado por**: GitHub Copilot  
**Basado en**: Logs reales de ejecución (Cierre #35)  
**Verificado**: ✅ Flujo ejecutado exitosamente
