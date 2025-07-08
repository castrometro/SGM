# Flujo de Incidencias Implementado

## Resumen del Flujo

Se ha implementado el flujo completo para el manejo de incidencias en el sistema de contabilidad:

1. **Procesar libro** → Generar incidencias
2. **Generar incidencias en modal** → Usuario puede verlas
3. **Marcar como "No aplica"** → Solo frontend, cambio local pendiente
4. **Editar tarjetas** → Cambios reales en clasificaciones (independiente)
5. **Reprocesar libro** → Sincroniza excepciones → Reprocesa → Actualiza modal

## Componentes Implementados

### Frontend

#### `ModalIncidenciasConsolidadas.jsx`

**Nuevas funcionalidades agregadas:**

1. **Estado de excepciones locales**:
   - `excepcionesLocales[]` - Array que mantiene los cambios pendientes
   - Cada excepción local tiene: `{codigoCuenta, tipoIncidencia, setId, motivo, accion}`

2. **Marcar "No aplica" (solo frontend)**:
   - `handleMarcarNoAplica()` - Actualiza UI inmediatamente + agrega a excepciones locales
   - No llama al backend hasta reprocesar
   - Muestra indicador visual "Cambio local"

3. **Eliminar "No aplica" (local o servidor)**:
   - `handleEliminarExcepcion()` - Distingue entre excepciones locales vs servidor
   - Si es local: la quita de la lista
   - Si es del servidor: la marca para eliminación

4. **Sincronización y reprocesamiento**:
   - `sincronizarExcepcionesLocales()` - Sube todas las excepciones pendientes al backend
   - `handleReprocesar()` - Flujo completo: sincronizar → reprocesar → actualizar modal
   - Indicador visual de cambios pendientes en el header

5. **Botones del header**:
   - **Actualizar**: Recarga incidencias sin perder cambios locales
   - **Reprocesar**: Sincroniza excepciones + reprocesa + actualiza modal

### Backend

#### `views/incidencias.py`

**Endpoints mejorados:**

1. **`obtener_incidencias_consolidadas_libro_mayor`**:
   - Incluye información de excepciones actuales en `elementos_afectados`
   - Campo `tiene_excepcion` refleja estado real del servidor
   - Soporte para excepciones específicas por set de clasificación

2. **`obtener_incidencias_consolidadas_optimizado`**:
   - Versión con caché y snapshots
   - Filtros por estado, severidad, tipo
   - Metadata de iteraciones

#### `views/excepciones.py`

**Endpoints funcionando:**

1. **`marcar_cuenta_no_aplica`**:
   - Crea excepciones para DOC_NULL, CUENTA_NO_CLAS, etc.
   - Soporte para clasificaciones específicas por set

2. **`eliminar_excepcion_clasificacion`**:
   - Elimina excepciones específicas de clasificación por set
   - Maneja tanto ExcepcionValidacion como ExcepcionClasificacionSet

### API Frontend

#### `src/api/contabilidad.js`

**Métodos implementados:**

1. **`marcarCuentaNoAplica(cierreId, codigoCuenta, tipoExcepcion, motivo, setId)`**
   - Endpoint: `/contabilidad/libro-mayor/marcar-no-aplica/`

2. **`eliminarExcepcionNoAplica(cierreId, codigoCuenta, tipoExcepcion, setId)`**
   - Para clasificaciones: `/contabilidad/libro-mayor/excepciones/clasificacion/eliminar/`
   - Para otras: endpoint tradicional de excepciones

3. **`reprocesarConExcepciones(cierreId)`**
   - Endpoint: `/contabilidad/libro-mayor/reprocesar-con-excepciones/`

## Flujo de Usuario Final

### 1. Procesar Libro Mayor
- Usuario sube archivo → Sistema procesa → Genera incidencias
- Sistema muestra el botón "Ver Incidencias" si hay problemas detectados

### 2. Ver Incidencias en Modal
- Modal muestra incidencias agrupadas por tipo
- Cada cuenta muestra estado actual de excepciones desde el servidor
- Usuario puede expandir cada grupo para ver detalles

### 3. Marcar "No Aplica" (Solo Frontend)
```javascript
// Solo actualiza interfaz + agrega a excepciones locales
handleMarcarNoAplica(codigoCuenta, tipoIncidencia, setId)
```
- ✅ Cambio inmediato en la UI
- ✅ Indicador "Cambio local" 
- ✅ Contador de "X cambios pendientes" en header
- ❌ NO llama al backend aún

### 4. Deshacer "No Aplica"
```javascript
// Distingue entre local vs servidor
handleEliminarExcepcion(codigoCuenta, tipoIncidencia, setId)
```
- Si es cambio local: lo quita inmediatamente
- Si es del servidor: lo marca para eliminación

### 5. Reprocesar (Sincronización Total)
```javascript
// Flujo completo
handleReprocesar()
```

**Pasos internos:**
1. **Sincronizar excepciones locales** → Backend
   - Crea nuevas excepciones
   - Elimina excepciones marcadas
   - Limpia lista de cambios locales

2. **Reprocesar libro mayor** → Backend
   - Crea nueva iteración
   - Aplica excepciones al procesamiento
   - Genera nuevas incidencias

3. **Actualizar modal** → Frontend
   - Recarga incidencias desde servidor
   - Limpia detalles expandidos
   - Muestra estado actualizado

## Tipos de Incidencia Soportados

### ✅ Con "No Aplica"
- **DOC_NULL**: Movimientos sin tipo de documento
- **CUENTA_NO_CLAS**: Cuentas sin clasificación (específico por set)
- **CUENTA_NO_CLASIFICADA**: Cuentas sin clasificación (general)

### ❌ Sin "No Aplica" (requieren acción)
- **CUENTA_INGLES**: Requiere agregar traducción al inglés
- **DOC_NO_REC**: Requiere configurar tipo de documento

## Estados de las Excepciones

1. **Server**: Excepción ya existe en el servidor
2. **Local Pending**: Marcada "No aplica" pero no sincronizada
3. **Delete Pending**: Marcada para eliminación pero no sincronizada
4. **Synced**: Sincronizada después del reprocesamiento

## Indicadores Visuales

- 🟠 **Cambio local**: Cuenta con excepción local pendiente
- 🟢 **No aplica**: Cuenta con excepción sincronizada
- 📊 **X cambios pendientes**: Contador en header
- 🔄 **Reprocesando...**: Estado de carga durante reprocesamiento

## Archivos Modificados

```
Frontend:
✅ /src/components/TarjetasCierreContabilidad/ModalIncidenciasConsolidadas.jsx
✅ /src/api/contabilidad.js

Backend:
✅ /backend/contabilidad/views/incidencias.py
✅ /backend/contabilidad/views/excepciones.py
✅ /backend/contabilidad/views/reprocesamiento.py
```

## Próximos Pasos (Opcionales)

1. **Testing**: Pruebas unitarias para los endpoints y componentes
2. **Performance**: Optimización de consultas para cierres con muchas incidencias
3. **UX**: Animaciones para transiciones entre estados
4. **Logging**: Logs detallados del proceso de reprocesamiento
5. **Validaciones**: Validaciones adicionales para casos edge

---

**Estado**: ✅ **IMPLEMENTADO Y FUNCIONAL**

El flujo está completo y cumple con los requerimientos especificados:
- Marcar "No aplica" es local hasta reprocesar ✅
- Usuario puede deshacer cambios antes de reprocesar ✅  
- Reprocesar sincroniza excepciones y actualiza modal ✅
- Modal refleja siempre el estado actual ✅
