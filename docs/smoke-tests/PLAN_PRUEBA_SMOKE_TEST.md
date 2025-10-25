# Plan de Prueba - Smoke Test Tasks Refactorizadas

**Objetivo**: Identificar qué funciones stub se llaman realmente vs código muerto

**Método**: Ejecutar cada flujo y registrar:
- ✅ Funciones que funcionan (ya refactorizadas)
- ⚠️ Stubs que explotan con NotImplementedError (necesitan refactorización)
- ❌ Errores inesperados
- 🔇 Stubs que nunca se llaman (código muerto candidato)

**Documentación por flujo**: Para cada flujo generaremos:
1. 📖 **Diagrama de flujo**: Secuencia visual de pasos
2. 🔄 **Lógica de negocio**: Qué hace cada paso y por qué
3. 🗂️ **Modelos involucrados**: Tablas de BD que se crean/actualizan
4. 📡 **Llamadas API**: Endpoints frontend → backend
5. ⚙️ **Tasks Celery**: Tareas asíncronas que se ejecutan
6. 💾 **Estado de datos**: Transformación de datos en cada paso

---

## 📋 Checklist de Flujos a Probar

### 1. Libro de Remuneraciones ✅
**Objetivo**: Procesar archivo Excel con nómina mensual

**Pasos**:
- [x] 1.1. Subir archivo libro de remuneraciones (libro 81 con formato Previred)
- [x] 1.2. Analizar headers (automático tras subida)
- [x] 1.3. Clasificar headers (automático en chain)
- [x] 1.4. Procesar libro (botón "Procesar")
- [x] 1.5. Verificar creación de EmpleadoCierre y RegistroConceptoEmpleado

**Funciones validadas**:
```
✅ analizar_headers_libro_remuneraciones_con_logging - 0.09s
✅ clasificar_headers_libro_remuneraciones_con_logging - 0.05s
✅ actualizar_empleados_desde_libro_optimizado - 0.06s
✅ guardar_registros_nomina_optimizado - 0.15s
```

**Resultado**:
```
Estado: ✅ EXITOSO (25/10/2025)
Libro ID: 81
Empleados: 5/5 ✅
Conceptos: 65 (50 esperados + 15 campos adicionales clasificados como conceptos)
Tiempo total: ~0.35s
Stubs llamados: Ninguno
Errores: Ninguno
Notas: CARGO, CENTRO DE COSTO y AREA se clasificaron como conceptos.
       Sistema funcionando según diseño actual.
Documentación: SMOKE_TEST_FLUJO_1_RESULTADOS.md
```

**Documentación generada**: 
- [x] `FLUJO_1_COMPLETO_DESDE_SUBIDA.md` - Diagrama y lógica completa desde subida hasta procesamiento
- [x] `INSTRUCCIONES_PRUEBA_FLUJO1.md` - Guía paso a paso para prueba manual

**Estado actual**: ✅ LISTO PARA PROBAR
- Cierre 35 creado y listo
- Excel de prueba generado: `/tmp/libro_remuneraciones_smoke_test.xlsx`
- URL: http://172.17.11.18:5174/nomina/cierre/35

---

### 2. Movimientos del Mes
**Objetivo**: Procesar movimientos de personal (altas/bajas)

**Pasos**:
- [ ] 2.1. Subir archivo de movimientos
- [ ] 2.2. Procesar movimientos
- [ ] 2.3. Verificar actualización de empleados

**Funciones esperadas**:
```
✅ procesar_movimientos_mes_con_logging
⚠️ obtener_conceptos_columnas (¿existe en refactored?)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_2_MOVIMIENTOS_MES.md` - Diagrama y lógica de procesamiento de movimientos

---

### 3. Archivos de Analista y Novedades
**Objetivo**: Procesar novedades (cambios salariales, bonos, etc)

**Pasos**:
- [ ] 3.1. Subir archivo de novedades
- [ ] 3.2. Analizar headers
- [ ] 3.3. Clasificar headers
- [ ] 3.4. Procesar novedades
- [ ] 3.5. Actualizar empleados con novedades

**Funciones esperadas**:
```
✅ procesar_archivo_novedades_con_logging
✅ actualizar_empleados_desde_novedades_task_optimizado
✅ guardar_registros_novedades_task_optimizado
⚠️ procesar_archivo_analista_util (¿se usa?)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_3_NOVEDADES.md` - Diagrama y lógica de procesamiento de novedades

---

### 4. Verificación de Discrepancias
**Objetivo**: Detectar inconsistencias entre libro y sistema

**Pasos**:
- [ ] 4.1. Ir a cierre con libro procesado
- [ ] 4.2. Generar discrepancias (botón)
- [ ] 4.3. Verificar creación de registros de discrepancias

**Funciones esperadas**:
```
✅ generar_discrepancias_cierre_con_logging
⚠️ Funciones helper de comparación (si existen)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_4_DISCREPANCIAS.md` - Diagrama y lógica de detección de discrepancias

---

### 5. Consolidar Información
**Objetivo**: Consolidar datos de libro + movimientos + novedades

**Pasos**:
- [ ] 5.1. Ir a cierre con datos cargados
- [ ] 5.2. Consolidar cierre (botón)
- [ ] 5.3. Verificar consolidación en BD

**Funciones esperadas**:
```
✅ consolidar_datos_nomina_con_logging
✅ procesar_empleados_libro_paralelo
✅ procesar_conceptos_consolidados_paralelo
✅ procesar_movimientos_personal_paralelo
✅ finalizar_consolidacion_post_movimientos
⚠️ Funciones helper de consolidación
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_5_CONSOLIDACION.md` - Diagrama del Chord paralelo y lógica de consolidación

---

### 6. Dashboards en Cierre
**Objetivo**: Verificar visualización de datos en dashboards

**Pasos**:
- [ ] 6.1. Dashboard de Libro de Remuneraciones
  - [ ] Ver resumen de empleados
  - [ ] Ver resumen de conceptos
  - [ ] Ver gráficas
- [ ] 6.2. Dashboard de Movimientos
  - [ ] Ver altas/bajas
  - [ ] Ver cambios

**Funciones esperadas**:
```
⚠️ obtener_resumen_libro (si existe)
⚠️ obtener_resumen_movimientos (si existe)
⚠️ generar_graficas_dashboard (si existe)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_6_DASHBOARDS.md` - APIs de dashboards y flujo de datos

---

### 7. Generación de Incidencias
**Objetivo**: Generar reporte de incidencias/anomalías

**Pasos**:
- [ ] 7.1. Ir a cierre con datos consolidados
- [ ] 7.2. Generar incidencias (botón)
- [ ] 7.3. Verificar creación de incidencias en BD
- [ ] 7.4. Revisar reporte generado

**Funciones esperadas**:
```
✅ generar_incidencias_con_logging
⚠️ Funciones de validación de incidencias
⚠️ Funciones de generación de reporte
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_7_INCIDENCIAS.md` - Diagrama de generación y validación de incidencias

---

### 8. Corrección de Incidencias
**Objetivo**: Aplicar correcciones a incidencias detectadas

**Pasos**:
- [ ] 8.1. Ver lista de incidencias
- [ ] 8.2. Seleccionar incidencias a corregir
- [ ] 8.3. Aplicar corrección
- [ ] 8.4. Verificar actualización en BD

**Funciones esperadas**:
```
⚠️ aplicar_correccion_incidencia (stub probable)
⚠️ recalcular_datos_post_correccion (stub probable)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_8_CORRECCIONES.md` - Diagrama de aplicación de correcciones

---

### 9. Finalizar Cierre
**Objetivo**: Cerrar el periodo y generar reportes finales

**Pasos**:
- [ ] 9.1. Verificar que no hay incidencias pendientes
- [ ] 9.2. Finalizar cierre (botón)
- [ ] 9.3. Verificar estado "cerrado"
- [ ] 9.4. Verificar generación de reportes

**Funciones esperadas**:
```
⚠️ finalizar_cierre_nomina (stub probable)
⚠️ generar_reportes_finales (stub probable)
⚠️ bloquear_edicion_cierre (stub probable)
```

**Resultado**:
```
Estado: [ PENDIENTE ]
Stubs llamados: [ ]
Errores: [ ]
Notas: [ ]
```

**Documentación generada**: 
- [ ] `FLUJO_9_FINALIZACION.md` - Diagrama de cierre definitivo y generación de reportes

---

## � Documentación Generada

Cada flujo tendrá su documento `.md` con:

### Estructura de cada documento:
```markdown
# FLUJO X: [Nombre del Flujo]

## 📋 Resumen
- **Propósito**: Qué resuelve este flujo
- **Trigger**: Cómo se inicia (botón, cron, API)
- **Duración típica**: Tiempo de ejecución

## 🔄 Diagrama de Flujo
[Diagrama ASCII o descripción visual de pasos]

## 🗂️ Modelos de BD Involucrados
- **Lectura**: Modelos que se consultan
- **Escritura**: Modelos que se crean/actualizan
- **Relaciones**: Cómo se vinculan los datos

## 📡 Secuencia de Llamadas

### Frontend → Backend
1. Usuario: [Acción del usuario]
2. API Call: `POST /api/nomina/endpoint`
3. ViewSet: `NominaViewSet.action()`
4. Task dispatch: `task_name.delay()`

### Backend → Celery
1. Task principal: `task_name`
2. Subtasks paralelas: `[subtask1, subtask2, ...]`
3. Consolidación: `callback_task`

## ⚙️ Lógica de Negocio

### Paso 1: [Nombre]
**Función**: `funcion_task()`
**Qué hace**: Descripción detallada
**Por qué**: Razón de negocio
**Input**: Parámetros de entrada
**Output**: Resultado esperado
**BD Changes**: Qué se guarda

### Paso 2: [Nombre]
...

## 💾 Transformación de Datos

```
Excel/Input → Pandas DataFrame → Validación → Modelos Django → BD
```

**Ejemplo de dato en cada etapa:**
- Excel: `{rut: "12345678-9", nombre: "Juan", sueldo: 1000000}`
- DataFrame: Row con tipado y validación
- Modelo: `Empleado(rut="12345678-9", ...)`
- BD: Registro con ID, timestamps, relaciones

## 🔍 Validaciones

1. **Validación 1**: [Qué valida y por qué]
2. **Validación 2**: [Qué valida y por qué]

## ❌ Casos de Error

- **Error 1**: Causa y cómo se maneja
- **Error 2**: Causa y cómo se maneja

## ✅ Resultado Exitoso

**Estado final**:
- Modelo X en estado Y
- Z registros creados
- Usuario puede continuar a [siguiente paso]

## 📊 Métricas

- Registros procesados: X
- Tiempo promedio: Y segundos
- Tasa de error típica: Z%

## 🔗 Flujos Relacionados

- **Anterior**: [Flujo que debe ejecutarse antes]
- **Siguiente**: [Flujo que puede ejecutarse después]
- **Depende de**: [Otros flujos requeridos]
```

---

## �📊 Resumen de Resultados

### Stubs que Necesitan Refactorización (NotImplementedError)
```
[ Lista se llenará durante pruebas ]
```

### Funciones que Ya Funcionan
```
[ Lista se llenará durante pruebas ]
```

### Código Muerto Identificado (nunca llamado)
```
[ Lista se llenará durante pruebas ]
```

---

## 🔧 Estrategia de Ejecución

**Orden recomendado**:
1. ✅ **Libro de Remuneraciones** (flujo base, más usado)
2. **Consolidar Información** (usa libro)
3. **Generación de Incidencias** (usa consolidación)
4. **Verificación de Discrepancias** (complementa incidencias)
5. **Movimientos del Mes** (independiente)
6. **Archivos de Novedades** (independiente)
7. **Dashboards** (lectura, no crítico)
8. **Corrección de Incidencias** (avanzado)
9. **Finalizar Cierre** (último paso)

**Método de registro**:
- Capturar logs de Celery: `docker compose logs celery_worker -f | tee prueba_flujo_X.log`
- Capturar errores Django: `docker compose logs django -f | grep "NotImplementedError"`
- Anotar en este documento después de cada prueba

---

## 🚀 Empezar con Flujo 1

**Comando para monitoreo**:
```bash
# Terminal 1: Logs de Celery
docker compose logs celery_worker -f | grep -E "Task|Error|NotImplementedError"

# Terminal 2: Logs de Django
docker compose logs django -f | grep -E "Error|NotImplementedError"
```

**Libro ya preparado**: Libro 78 en estado "clasificado", listo para reprocesar.

---

**Fecha inicio**: 24 octubre 2025
**Estado general**: 🟡 EN PROGRESO - Smoke test iniciado
