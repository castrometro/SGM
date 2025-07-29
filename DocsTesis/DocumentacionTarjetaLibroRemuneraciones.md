# 📋 DOCUMENTACIÓN COMPLETA: Tarjeta Libro de Remuneraciones

## 🔗 1. CUANDO SE SUBE EL LIBRO - ENDPOINT Y FLUJO

### **Frontend (API Call):**
```javascript
// Archivo: /src/api/nomina.js - línea 300
export const subirLibroRemuneraciones = async (cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cierre", cierreId);
  formData.append("archivo", archivo);
  
  const res = await api.post("/nomina/libros-remuneraciones/", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return res.data;
};
```

### **Backend - Endpoint:**
- **URL:** `POST /nomina/libros-remuneraciones/`
- **ViewSet:** `LibroRemuneracionesUploadViewSet` (línea 28 en `views_libro_remuneraciones.py`)
- **Método:** `perform_create()` (línea 34)

## 🔄 2. PROCESO COMPLETO AL SUBIR ARCHIVO:

### **Paso 1: Validación y Creación de Logs**
```python
# En perform_create():
# 1. Validar archivo
validator = ValidacionArchivoCRUDMixin()
validator.validar_archivo(archivo)

# 2. Crear UploadLog para tracking
upload_log = log_mixin.crear_upload_log(cliente, archivo)

# 3. Guardar archivo temporal
nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
ruta = guardar_temporal(nombre_temporal, archivo)
```

### **Paso 2: Crear/Actualizar Registro**
```python
# Crear o actualizar LibroRemuneracionesUpload
libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()

if libro_existente:
    # Actualizar existente
    libro_existente.estado = 'pendiente'
    libro_existente.header_json = []
else:
    # Crear nuevo
    instance = serializer.save(cierre=cierre, estado='pendiente')
```

### **Paso 3: Iniciar Procesamiento Asíncrono**
```python
# Iniciar chain de Celery (línea 135)
chain(
    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, upload_log.id),
    clasificar_headers_libro_remuneraciones_con_logging.s(),
).apply_async()
```

## ⚙️ 3. TASKS DE CELERY - QUÉ HACEN:

### **Task 1: `analizar_headers_libro_remuneraciones_con_logging`**
```python
# Archivo: backend/nomina/tasks.py - línea 681
# ¿Qué hace?
1. Cambia estado a "analizando_hdrs"
2. Llama a obtener_headers_libro_remuneraciones(libro.archivo.path)
3. Extrae headers del Excel (columnas)
4. Guarda headers en libro.header_json
5. Cambia estado a "hdrs_analizados"
```

### **Task 2: `clasificar_headers_libro_remuneraciones_con_logging`**
```python
# Archivo: backend/nomina/tasks.py - línea 735
# ¿Qué hace?
1. Cambia estado a "clasif_en_proceso"
2. Llama a clasificar_headers_libro_remuneraciones(headers, cliente)
3. Compara headers con conceptos ya clasificados del cliente
4. Separa en: headers_clasificados y headers_sin_clasificar
5. Si hay sin clasificar: estado = "clasif_pendiente"
6. Si todos clasificados: estado = "clasificado"
```

## 📊 4. ¿QUÉ SON LOS HEADERS?

Los **headers** son las **columnas del Excel** que contienen conceptos de remuneración:

```javascript
// Ejemplo de headers extraídos:
[
  "SUELDO BASE",
  "HORAS EXTRAS 50%", 
  "MOVILIZACION",
  "FONASA",
  "AFP",
  "GRATIFICACION"
]
```

**Estados de Headers:**
- **headers_clasificados:** Ya tienen categoría asignada (ej: "SUELDO BASE" → "haberes_imponibles")
- **headers_sin_clasificar:** Necesitan clasificación manual

## 🎯 5. MODAL DE CLASIFICACIONES - PARA QUÉ SIRVE:

### **Propósito:**
Permite **clasificar manualmente** los conceptos de remuneración en categorías fiscales/contables.

### **Ubicación:** `/src/components/ModalClasificacionHeaders.jsx`

### **Categorías Disponibles:**
```javascript
const categorias = [
  "haberes_imponibles",     // 💰 Sueldos, gratificaciones
  "haberes_no_imponibles",  // 🎁 Movilización, colación
  "horas_extras",           // ⏰ Horas extras
  "descuentos_legales",     // ⚖️ AFP, Fonasa, impuestos
  "otros_descuentos",       // 📋 Préstamos, descuentos varios
  "aportes_patronales",     // 🏢 Mutual, seguro cesantía
  "informacion_adicional",  // 📝 Datos informativos
  "impuestos"              // 🏛️ Impuesto único, otros
];
```

### **Funcionalidades:**
1. **Clasificación individual:** Un concepto a la vez
2. **Clasificación múltiple:** Varios conceptos con la misma categoría
3. **Hashtags:** Etiquetas adicionales para organización
4. **Vista por categorías:** Organizar por tipo de concepto

## 🔧 6. BOTÓN "PROCESAR" - QUÉ HACE:

### **Frontend Call:**
```javascript
// Archivo: /src/api/nomina.js
export const procesarLibroRemuneraciones = async (libroId) => {
  const res = await api.post(`/nomina/libros-remuneraciones/${libroId}/procesar/`);
  return res.data;
};
```

### **Backend - Endpoint:**
- **URL:** `POST /nomina/libros-remuneraciones/{id}/procesar/`
- **Método:** `procesar()` en ViewSet

### **¿Qué hace el procesamiento?**
```python
# El botón "Procesar" ejecuta:
1. Validar que todos los headers estén clasificados
2. Leer y procesar todas las filas del Excel
3. Crear registros de NominaConsolidada para cada empleado
4. Aplicar las clasificaciones a cada concepto
5. Cambiar estado a "procesado"
```

## 📈 7. FLUJO DE ESTADOS COMPLETO:

```
no_subido → 
pendiente (archivo subido) →
analizando_hdrs (extrayendo columnas) →
hdrs_analizados (columnas extraídas) →
clasif_en_proceso (clasificando conceptos) →
clasif_pendiente (necesita clasificación manual) →
clasificado (todos los conceptos clasificados) →
procesando (generando registros) →
procesado (datos listos para usar)
```

## 🗃️ 8. ENTIDADES/MODELOS INVOLUCRADOS:

1. **LibroRemuneracionesUpload:** Registro principal del archivo
2. **UploadLogNomina:** Log de seguimiento del procesamiento
3. **CierreNomina:** Cierre al que pertenece
4. **NominaConsolidada:** Datos procesados finales (después de "Procesar")
5. **ConceptoRemuneracion:** Clasificaciones de conceptos por cliente

## 🔍 9. PUNTOS CRÍTICOS PARA DEBUGGING:

1. **Subida:** Validación de archivo y creación de logs
2. **Análisis:** Extracción correcta de headers del Excel
3. **Clasificación:** Comparación con conceptos existentes
4. **Modal:** Guardado de clasificaciones manuales
5. **Procesamiento:** Generación de registros consolidados

## 📝 10. LOGGING Y TRACKING:

- **UploadLogNomina** rastrea cada paso del proceso
- Estados se actualizan en tiempo real
- Errores se capturan y almacenan
- Frontend hace polling para mostrar progreso

## 🔄 11. PUNTOS DE TRANSICIÓN Y CONDICIONES DE ESTADO DEL CIERRE

### **📍 PUNTO 1: VerificadorDatosSection - Transición Automática**
**Ubicación:** `/src/components/TarjetasCierreNomina/VerificadorDatosSection.jsx` (líneas 54-85)

**Condición de Transición:**
```javascript
if (estado && estado.total_discrepancias === 0 && estado.verificacion_completada) {
  await actualizarEstadoSinDiscrepancias();
}
```

**¿Qué hace?**
- **Automáticamente** actualiza el estado del cierre cuando no hay discrepancias
- Llama a `actualizarEstadoCierreNomina(cierre.id)`
- Es un punto **crítico** porque puede cambiar el estado sin intervención del usuario

**🚨 Posibles Bugs:**
- Múltiples llamadas simultáneas (protegido por `actualizandoEstado`)
- Falla en la verificación de 0 discrepancias
- No hay rollback si algo falla después

### **📍 PUNTO 2: Estados de Bloqueo - Condiciones de Acceso**
**Ubicación:** `/src/components/TarjetasCierreNomina/CierreProgresoNomina.jsx` (líneas 31-39)

**Estados Posteriores a Consolidación:**
```javascript
const estadosPosteriores = [
  'datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'validacion_final', 'finalizado'
];
```

**Impacto:**
- **ArchivosAnalistaSection:** Se bloquea cuando `esEstadoPosteriorAConsolidacion()` es true
- **VerificadorDatosSection:** Se bloquea cuando está posterior a consolidación
- **ArchivosTalanaSection:** Solo se bloquea cuando está `finalizado`

**🚨 Posibles Bugs:**
- Estados intermedios no contemplados
- Inconsistencia entre lo que muestra el UI y el estado real
- Transiciones que saltan estados

### **📍 PUNTO 3: Finalización del Cierre - Transición Manual**
**Ubicación:** `/src/components/TarjetasCierreNomina/IncidenciasEncontradas/BotonFinalizarCierre.jsx` (líneas 10-12)

**Condiciones para Finalizar:**
```javascript
const puedeFinalizarse = cierre?.estado === 'incidencias_resueltas' && 
                        (cierre?.estado_incidencias === 'resueltas' || 
                         cierre?.estado_incidencias === 'pendiente');
```

**Proceso de Finalización:**
1. Verifica condiciones
2. Llama a `finalizarCierre(cierre.id)`
3. Cambia estado a `finalizado`
4. Genera informes

**🚨 Posibles Bugs:**
- Doble verificación de estados (`estado` vs `estado_incidencias`)
- Inconsistencias entre estas dos propiedades
- Falla en generación de informes pero estado ya cambió

### **📍 PUNTO 4: API Backend - Actualización de Estado**
**Ubicación:** `/src/api/nomina.js` (línea 43)

**Endpoint:**
```javascript
export const actualizarEstadoCierreNomina = async (cierreId) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/actualizar-estado/`);
  return res.data;
};
```

**¿Quién lo llama?**
1. **CierreInfoBar** - Actualización manual
2. **VerificadorDatosSection** - Automática cuando 0 discrepancias
3. **CierreStateDebugger** - Para debugging

**🚨 Posibles Bugs:**
- El backend decide el próximo estado sin contexto del frontend
- No hay validación de que el cambio sea válido
- Puede fallar silenciosamente

## 🎯 **Flujo Completo de Estados**

```
inicial → 
archivos_talana_subidos → 
archivos_analista_procesados → 
datos_consolidados (AUTOMÁTICO via VerificadorDatos) → 
con_incidencias → 
incidencias_resueltas → 
validacion_final → 
finalizado (MANUAL via BotonFinalizar)
```

## ⚠️ **Puntos Críticos Donde Pueden Ocurrir Bugs**

### **1. Transición Automática sin Discrepancias**
- **Problema:** El sistema decide automáticamente cambiar de estado
- **Riesgo:** Si hay un error en el cálculo de discrepancias, puede avanzar incorrectamente
- **Ubicación:** `VerificadorDatosSection.jsx:54-68`

### **2. Inconsistencia entre `estado` y `estado_incidencias`**
- **Problema:** Dos campos que deberían estar sincronizados
- **Riesgo:** El botón finalizar puede estar disponible cuando no debería
- **Ubicación:** `BotonFinalizarCierre.jsx:10-12`

### **3. Estados de Bloqueo Inconsistentes**
- **Problema:** Diferentes secciones se bloquean en momentos diferentes
- **Riesgo:** El usuario puede ver opciones disponibles que realmente están bloqueadas
- **Ubicación:** `CierreProgresoNomina.jsx:297-303`

### **4. Falta de Rollback en Transiciones**
- **Problema:** Si algo falla después de cambiar el estado, no hay manera de volver
- **Riesgo:** Cierres "colgados" en estados intermedios
- **Ubicación:** Todas las llamadas a `actualizarEstadoCierreNomina`

## 💡 **Recomendaciones para Identificar Bugs**

1. **Monitorear las llamadas automáticas** en `VerificadorDatosSection`
2. **Verificar sincronización** entre `estado` y `estado_incidencias`
3. **Revisar transiciones** que saltan estados esperados
4. **Validar que los bloqueos** se apliquen consistentemente

---

**Fecha de creación:** 29 de julio de 2025  
**Autor:** Documentación del sistema SGM  
**Versión:** 1.0
