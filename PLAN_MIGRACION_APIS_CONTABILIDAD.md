# 🚀 Plan de Migración Progresiva - APIs de Contabilidad

## 📊 Estado Actual (Fase 1 - COMPLETADA ✅)

### ✅ Dominios Migrados:
1. **`cierres/`** - Gestión completa del ciclo de vida de cierres
   - `crud.js` - Operaciones CRUD básicas (7 funciones)
   - `estados.js` - Progreso y monitoreo (6 funciones)
   - `finalizacion.js` - Lógica de cierre definitivo (4 funciones)

2. **`shared/`** - Utilidades compartidas
   - `constants.js` - Constantes del dominio
   - `logging.js` - Sistema de logging unificado
   - `index.js` - Re-exportaciones centralizadas

### 📋 Funciones Migradas del `contabilidad.js` original:
```javascript
// Migradas a cierres/crud.js
- obtenerCierresCliente ✅
- obtenerCierrePorId ✅
- obtenerCierreMensual ✅
- crearCierreMensual ✅
- actualizarEstadoCierre ✅
- obtenerResumenContable ✅

// Migradas a cierres/estados.js
- obtenerProgresoClasificacionTodosLosSets ✅
- obtenerProgresoClasificacionPorSet ✅
- obtenerCuentasPendientes ✅
- obtenerEstadoFinalizacion ✅

// Migradas a cierres/finalizacion.js
- finalizarCierre ✅ (con mejoras)

// Migradas a shared/logging.js
- registrarActividadTarjeta ✅
- registrarVistaClasificaciones ✅
- registrarVistaSetsClasificacion ✅
- registrarVistaTiposDocumento ✅
```

## 🎯 Próximos Pasos - Migración Progresiva

### Fase 2: Dominio `clasificaciones/` 📈
**Prioridad: ALTA** - ~25 funciones (~25% del archivo original)

#### Estructura Propuesta:
```
src/api/contabilidad/clasificaciones/
├── index.js              # Re-exportaciones del dominio
├── sets.js               # Gestión de sets de clasificación
├── persistentes.js       # Clasificaciones permanentes
├── temporales.js         # Clasificaciones de upload
├── bulk.js               # Operaciones masivas
└── incidencias.js        # Gestión de incidencias
```

#### Funciones a Migrar:
```javascript
// Sets de clasificación (sets.js)
- obtenerSetsClasificacion
- crearSetClasificacion
- actualizarSetClasificacion
- eliminarSetClasificacion
- obtenerOpcionesClasificacion

// Clasificaciones persistentes (persistentes.js)
- obtenerClasificacionesCliente
- crearClasificacion
- actualizarClasificacion
- eliminarClasificacion
- obtenerDetalleClasificacion

// Clasificaciones temporales (temporales.js)
- obtenerClasificacionesPorUpload
- eliminarClasificacionesPorUpload

// Operaciones masivas (bulk.js)
- subirClasificacionesBulk
- crearClasificacionBulk
- actualizarClasificacionBulk
- eliminarClasificacionBulk
- procesarClasificacionBulk

// Incidencias (incidencias.js)
- obtenerIncidenciasClasificacion
- reclasificarCuentas
```

### Fase 3: Dominio `documentos/` 📄
**Prioridad: MEDIA** - ~8 funciones

#### Estructura Propuesta:
```
src/api/contabilidad/documentos/
├── index.js              # Re-exportaciones del dominio
├── tipos.js              # Gestión de tipos de documento
├── plantillas.js         # Descarga de plantillas
└── crud.js               # Operaciones CRUD
```

### Fase 4: Dominio `libroMayor/` 📚
**Prioridad: MEDIA** - ~10 funciones

#### Estructura Propuesta:
```
src/api/contabilidad/libroMayor/
├── index.js              # Re-exportaciones del dominio
├── upload.js             # Subida y procesamiento
├── incidencias.js        # Gestión de incidencias
├── historial.js          # Reprocesamiento e historial
└── movimientos.js        # Consulta de movimientos
```

### Fase 5: Dominio `nombresIngles/` 🌐
**Prioridad: BAJA** - ~8 funciones

#### Estructura Propuesta:
```
src/api/contabilidad/nombresIngles/
├── index.js              # Re-exportaciones del dominio
├── crud.js               # Operaciones CRUD
└── upload.js             # Gestión de uploads
```

## 🔧 Estrategia de Migración

### 1. **Compatibilidad Total**
- El archivo `contabilidad/index.js` mantiene todas las exportaciones legacy
- Los imports existentes siguen funcionando sin cambios
- Migración transparente para el frontend

### 2. **Migración Gradual por Dominio**
- Cada fase migra un dominio completo
- Se mantienen tests de compatibilidad
- Se actualizan imports progresivamente

### 3. **Mejoras Incrementales**
- Logging unificado con shared/logging
- Gestión de errores mejorada
- Validaciones de negocio incluidas
- Documentación JSDoc completa

## 📋 Checklist de Migración

### ✅ Fase 1 - Completada
- [x] Crear estructura de directorios
- [x] Migrar dominio `cierres/`
- [x] Implementar shared utilities
- [x] Crear `contabilidad/index.js` con compatibilidad
- [x] Documentar estrategia

### 🔄 Fase 2 - En Planificación
- [ ] Analizar funciones de clasificaciones
- [ ] Crear `clasificaciones/sets.js`
- [ ] Crear `clasificaciones/persistentes.js`
- [ ] Crear `clasificaciones/temporales.js`
- [ ] Crear `clasificaciones/bulk.js`
- [ ] Crear `clasificaciones/incidencias.js`
- [ ] Actualizar `contabilidad/index.js`

### ⏳ Fase 3-5 - Pendientes
- [ ] Migrar `documentos/`
- [ ] Migrar `libroMayor/`
- [ ] Migrar `nombresIngles/`
- [ ] Remover archivo legacy
- [ ] Actualizar todas las importaciones frontend

## 🎯 Beneficios Esperados

1. **Mantenibilidad**: Cada dominio es independiente y enfocado
2. **Escalabilidad**: Fácil agregar nuevas funcionalidades por dominio
3. **Testing**: Tests más específicos y focalizados
4. **Performance**: Imports más granulares y tree-shaking
5. **Documentación**: Cada dominio autodocumentado
6. **Colaboración**: Equipos pueden trabajar en paralelo por dominio

## 📈 Métricas de Progreso

- **Funciones migradas**: 17/60+ (~28%)
- **Dominios completados**: 1/5 (20%)
- **Líneas refactorizadas**: ~200/1,039 (~19%)
- **Cobertura de tests**: Por implementar
- **Compatibilidad**: 100% mantenida

---

**Próximo paso**: Comenzar Fase 2 con migración de `clasificaciones/`
