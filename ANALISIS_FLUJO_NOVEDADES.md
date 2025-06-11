# Análisis del Flujo por Fases - Sistema de Novedades

## Estado Actual: IMPLEMENTADO ✅

El sistema de novedades **YA IMITA EXACTAMENTE** el proceso del libro de remuneraciones con un flujo por fases completo.

## Flujo Implementado

### 1. SUBIDA DE ARCHIVO
**Endpoint:** `POST /api/nomina/archivo-novedades/subir/{cierre_id}/`
**Frontend:** `ArchivosAnalistaCard.jsx` - Botón "Subir Archivo de Novedades"
**Estado inicial:** `pendiente`

```javascript
// src/api/nomina.js
export const subirArchivoNovedades = (cierreId, formData) => {
    return api.post(`/nomina/archivo-novedades/subir/${cierreId}/`, formData);
};
```

### 2. ANÁLISIS AUTOMÁTICO DE HEADERS
**Task:** `analizar_headers_archivo_novedades()`
**Estados:** `pendiente` → `analizando_hdrs` → `hdrs_analizados`

```python
# backend/nomina/tasks.py
@shared_task
def analizar_headers_archivo_novedades(archivo_id):
    # Lee el archivo Excel
    # Extrae headers de la primera fila
    # Guarda en header_json
    # Cambia estado a 'hdrs_analizados'
```

### 3. CLASIFICACIÓN AUTOMÁTICA
**Task:** `clasificar_headers_archivo_novedades_task()`
**Estados:** `hdrs_analizados` → `clasif_en_proceso` → `clasif_pendiente`/`clasificado`

```python
# Clasifica automáticamente headers usando mapeos existentes
# Si todos los headers tienen mapeo → 'clasificado'
# Si algunos faltan → 'clasif_pendiente'
```

### 4. CLASIFICACIÓN MANUAL (si es necesaria)
**Endpoint:** `POST /api/nomina/archivo-novedades/{id}/clasificar_headers/`
**Frontend:** `ModalClasificacionNovedades.jsx`
**Estado:** `clasif_pendiente` → `clasificado`

```javascript
// Modal para mapear headers de novedades con conceptos del libro
export const clasificarHeadersNovedades = (archivoId, mapeos) => {
    return api.post(`/nomina/archivo-novedades/${archivoId}/clasificar_headers/`, {
        mapeos: mapeos
    });
};
```

### 5. PROCESAMIENTO FINAL
**Endpoint:** `POST /api/nomina/archivo-novedades/{id}/procesar_final/`
**Tasks:** `actualizar_empleados_desde_novedades_task()` + `guardar_registros_novedades_task()`
**Estado:** `clasificado` → `procesado`

## Estados del Sistema

```python
# backend/nomina/models.py - ArchivoNovedadesUpload
ESTADOS_ARCHIVO = [
    ('pendiente', 'Pendiente'),
    ('analizando_hdrs', 'Analizando Headers'),
    ('hdrs_analizados', 'Headers Analizados'),
    ('clasif_en_proceso', 'Clasificación en Proceso'),
    ('clasif_pendiente', 'Clasificación Pendiente'),
    ('clasificado', 'Clasificado'),
    ('procesado', 'Procesado'),
    ('con_error', 'Con Error'),
]
```

## Componentes Frontend

### Tarjeta Principal
**Archivo:** `src/components/TarjetasCierreNomina/ArchivosAnalistaCard.jsx`
- Muestra estado actual del archivo
- Botón de subida
- Acciones según el estado

### Modal de Clasificación
**Archivo:** `src/components/ModalClasificacionNovedades.jsx`
- Interfaz para mapear headers pendientes
- Dropdown con conceptos del libro de remuneraciones
- Guarda mapeos en `ConceptoRemuneracionNovedades`

## Diferencias con Libro de Remuneraciones

| Aspecto | Libro Remuneraciones | Novedades |
|---------|---------------------|-----------|
| **Clasificación** | Por categorías (Haberes, Descuentos, etc.) | Mapeo a conceptos existentes |
| **Modelo de mapeo** | `ConceptoRemuneracion` | `ConceptoRemuneracionNovedades` |
| **Procesamiento final** | Actualiza empleados + registros | Actualiza empleados + registros |
| **Estados** | 8 estados | 8 estados (idénticos) |

## Endpoints Disponibles

1. `GET /api/nomina/archivo-novedades/estado/{cierre_id}/` - Estado del archivo
2. `POST /api/nomina/archivo-novedades/subir/{cierre_id}/` - Subir archivo
3. `GET /api/nomina/archivo-novedades/{id}/headers/` - Obtener headers para clasificar
4. `POST /api/nomina/archivo-novedades/{id}/clasificar_headers/` - Clasificar headers
5. `POST /api/nomina/archivo-novedades/{id}/procesar_final/` - Procesamiento final
6. `POST /api/nomina/archivo-novedades/{id}/reprocesar/` - Reprocesar desde inicio

## Flujo Completo Visualizado

```
SUBIDA → ANÁLISIS → CLASIFICACIÓN AUTO → CLASIFICACIÓN MANUAL → PROCESAMIENTO
  ↓         ↓             ↓                    ↓                     ↓
pendiente → analizando → clasif_en_proceso → clasif_pendiente → procesado
            ↓             ↓                    ↓
        hdrs_analizados   clasificado ←───────┘
```

## Conclusión

**EL FLUJO YA ESTÁ IMPLEMENTADO COMPLETAMENTE** 🎉

El sistema de novedades imita fielmente el proceso del libro de remuneraciones:
- ✅ Subida por fases
- ✅ Extracción automática de headers  
- ✅ Clasificación automática + manual
- ✅ Procesamiento final
- ✅ Estados detallados
- ✅ Interfaz de usuario completa

No se requieren cambios adicionales - el flujo funciona exactamente como el libro de remuneraciones.
