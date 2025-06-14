# Implementación Completa: Nuevo Flujo de Clasificación de Cuentas

## Resumen de Cambios

Se implementó exitosamente el nuevo flujo de clasificación de cuentas que funciona de manera similar al de tipo de documento: primero se guardan los registros raw del archivo Excel y después se procesan/mapean a las cuentas reales.

## Cambios Realizados

### 1. Backend - Modelos

**Archivo: `/backend/contabilidad/models.py`**
- ✅ **Agregado modelo `ClasificacionCuentaArchivo`**: Almacena los datos raw del Excel antes del mapeo
- ✅ **Campos incluidos**:
  - `numero_cuenta`: Código tal como viene en el archivo
  - `clasificaciones`: JSONField con los sets y valores
  - `procesado`: Boolean para tracking del estado
  - `errores_mapeo`: Texto para errores durante el mapeo
  - `cuenta_mapeada`: FK a la cuenta real una vez procesado
  - `fila_excel`: Para tracking de errores

### 2. Backend - Serializers

**Archivo: `/backend/contabilidad/serializers.py`**
- ✅ **Agregado `ClasificacionCuentaArchivoSerializer`**
- ✅ **Campos adicionales**:
  - `cliente_nombre`: Nombre del cliente (read-only)
  - `upload_archivo`: Nombre del archivo (read-only)

### 3. Backend - Tareas Celery

**Archivo: `/backend/contabilidad/tasks.py`**
- ✅ **Modificada `procesar_bulk_clasificacion()`**: Ahora guarda datos raw en lugar de aplicar directamente
- ✅ **Agregada `procesar_mapeo_clasificaciones()`**: Nueva tarea para mapear registros raw a cuentas reales
- ✅ **Funcionalidades**:
  - Limpia registros previos del mismo upload
  - Guarda todos los registros con sus clasificaciones en JSON
  - Maneja errores por fila
  - Actualiza estadísticas en el resumen

### 4. Backend - Views y URLs

**Archivo: `/backend/contabilidad/views.py`**
- ✅ **Agregado `ClasificacionCuentaArchivoViewSet`**
- ✅ **Endpoints nuevos**:
  - `GET /contabilidad/clasificacion-archivo/` - Listar registros raw
  - `POST /contabilidad/clasificacion-archivo/procesar_mapeo/` - Disparar mapeo
  - `GET /contabilidad/clasificacion-archivo/estadisticas/` - Estadísticas por upload

**Archivo: `/backend/contabilidad/urls.py`**
- ✅ **Agregada ruta para el nuevo ViewSet**

### 5. Backend - Admin

**Archivo: `/backend/contabilidad/admin.py`**
- ✅ **Agregado `ClasificacionCuentaArchivoAdmin`**
- ✅ **Configuración**:
  - Lista filtrable por procesado, cliente, estado
  - Solo lectura (no permite agregar manualmente)
  - Select_related optimizado

### 6. Frontend - API

**Archivo: `/src/api/contabilidad.js`**
- ✅ **Agregadas funciones**:
  - `obtenerClasificacionesArchivo(uploadId)`
  - `procesarMapeoClasificaciones(uploadId)`
  - `obtenerClasificacionesArchivoCliente(clienteId, procesado)`
  - `obtenerEstadisticasClasificacionArchivo(uploadId)`

### 7. Frontend - Componentes

**Archivo: `/src/components/TarjetasCierreContabilidad/ClasificacionBulkCard.jsx`**
- ✅ **Modificaciones**:
  - Carga automática de registros raw después de subir archivo
  - Botón para procesar mapeo cuando hay registros pendientes
  - Información de estadísticas del mapeo
  - Integración con modal de detalles

**Archivo: `/src/components/ModalClasificacionRegistrosRaw.jsx` (NUEVO)**
- ✅ **Funcionalidades**:
  - Vista detallada de todos los registros raw
  - Estadísticas en tiempo real (total, procesados, pendientes, errores)
  - Filtros por estado (todos, procesados, pendientes, errores)
  - Botón para procesar mapeo desde el modal
  - Tabla completa con información de errores
  - Actualización automática después del procesamiento

## Flujo de Trabajo Implementado

### Fase 1: Subida de Archivo
1. Usuario sube archivo Excel
2. Celery procesa y guarda registros raw en `ClasificacionCuentaArchivo`
3. Estado del upload: `completado`
4. Se muestran estadísticas de registros guardados

### Fase 2: Revisión de Datos (NUEVO)
1. Usuario puede ver todos los registros raw antes del mapeo
2. Modal muestra datos tal como vienen del Excel
3. Estadísticas de lo que se va a procesar

### Fase 3: Procesamiento/Mapeo
1. Usuario hace clic en "Procesar mapeo a cuentas"
2. Celery ejecuta `procesar_mapeo_clasificaciones()`
3. Se buscan las cuentas reales por código
4. Se crean los sets y opciones si no existen
5. Se aplican las clasificaciones a las cuentas
6. Se marcan registros como procesados

### Fase 4: Resultados
1. Estadísticas finales del mapeo
2. Lista de cuentas no encontradas
3. Errores específicos por registro
4. Estado final: mapeo completado

## Estados del Sistema

- **`pendiente`**: No hay archivo subido
- **`procesando`**: Celery está procesando el archivo
- **`completado`**: Registros raw guardados, listo para mapeo
- **`error`**: Error en el procesamiento

## Ventajas del Nuevo Flujo

1. **Transparencia**: Usuario ve exactamente qué datos se van a procesar
2. **Validación**: Puede revisar los datos antes del mapeo
3. **Rastreabilidad**: Cada registro mantiene su fila de Excel original
4. **Recuperación**: Posibilidad de reprocesar registros con errores
5. **Consistencia**: Mismo patrón que tipo de documento
6. **Flexibilidad**: Sets y opciones se crean dinámicamente

## Próximos Pasos

- [ ] Crear migración de base de datos: `python manage.py makemigrations contabilidad`
- [ ] Aplicar migración: `python manage.py migrate`
- [ ] Probar el flujo completo end-to-end
- [ ] Agregar tests unitarios para las nuevas funcionalidades
- [ ] Documentar el nuevo flujo para usuarios finales

## Archivos Modificados

### Backend
- `backend/contabilidad/models.py` - Nuevo modelo
- `backend/contabilidad/serializers.py` - Nuevo serializer
- `backend/contabilidad/views.py` - Nuevo ViewSet
- `backend/contabilidad/urls.py` - Nueva ruta
- `backend/contabilidad/admin.py` - Nuevo admin
- `backend/contabilidad/tasks.py` - Tareas modificadas y nueva

### Frontend
- `src/api/contabilidad.js` - Nuevas funciones API
- `src/components/TarjetasCierreContabilidad/ClasificacionBulkCard.jsx` - Integración del nuevo flujo
- `src/components/ModalClasificacionRegistrosRaw.jsx` - **NUEVO ARCHIVO**

## Compatibilidad

✅ **Los cambios son completamente retrocompatibles**:
- Los uploads existentes siguen funcionando
- El modelo anterior `BulkClasificacionUpload` se mantiene
- La API existente no se rompe
- Se agregaron nuevas funcionalidades sin eliminar las anteriores

El sistema ahora ofrece un flujo mucho más robusto y transparente para la clasificación masiva de cuentas contables.
