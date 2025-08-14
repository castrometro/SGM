# 🏗️ Estrategias de Refactorización de APIs

## 📊 Análisis del Estado Actual

### 📋 Archivo Actual: `contabilidad.js`
- **Tamaño**: 1,039 líneas
- **Funciones**: ~60+ funciones exportadas
- **Problemas**: 
  - Archivo monolítico gigante
  - Difícil mantenimiento
  - Múltiples responsabilidades
  - Sin separación por dominio

### 🎯 Funcionalidades Identificadas:
1. **Gestión de Cierres** (~15 funciones)
2. **Clasificaciones** (~25 funciones)
3. **Tipos de Documento** (~8 funciones)
4. **Libro Mayor** (~10 funciones)
5. **Nombres en Inglés** (~8 funciones)
6. **Plantillas** (~3 funciones)
7. **Utilidades/Logs** (~5 funciones)

## 🚀 Patrones de Refactorización Propuestos

### 🏗️ **OPCIÓN A: Domain-Driven Design (DDD)**
```
src/api/contabilidad/
├── index.js                    # Re-exportaciones principales
├── cierres/
│   ├── index.js               # Re-exporta todo el dominio
│   ├── cicloVida.js           # crear, obtener, actualizar, finalizar
│   ├── estados.js             # gestión de estados y progreso
│   └── tareas.js              # tareas asíncronas y monitoring
├── clasificaciones/
│   ├── index.js
│   ├── sets.js                # gestión de sets y opciones
│   ├── persistentes.js        # clasificaciones permanentes
│   ├── temporales.js          # clasificaciones de upload
│   └── bulk.js                # operaciones masivas
├── documentos/
│   ├── index.js
│   ├── tipos.js               # tipos de documento
│   ├── nombresIngles.js       # traducción de nombres
│   └── plantillas.js          # descarga de plantillas
├── libroMayor/
│   ├── index.js
│   ├── upload.js              # subida y procesamiento
│   ├── incidencias.js         # gestión de incidencias
│   └── historial.js           # reprocesamiento e historial
└── shared/
    ├── monitoring.js          # logs y actividad
    └── uploads.js             # estado de uploads
```

### 🎯 **OPCIÓN B: Feature-Based (Matching Frontend)**
```
src/api/contabilidad/
├── index.js                   # Exportaciones principales
├── cierreDetalle/
│   ├── index.js
│   ├── tipoDocumento.js       # APIs del TipoDocumentoCard
│   ├── clasificaciones.js    # APIs del ClasificacionBulkCard
│   ├── nombresIngles.js       # APIs del NombresEnInglesCard
│   ├── libroMayor.js          # APIs del LibroMayorCard
│   └── estados.js             # APIs del CierreInfoBar
├── listadoCierres/
│   ├── index.js
│   └── consultas.js           # APIs para listado e historial
├── creacionCierres/
│   ├── index.js
│   └── operaciones.js         # APIs para crear cierres
└── modales/
    ├── index.js
    ├── clasificacionRegistros.js
    ├── incidenciasConsolidadas.js
    └── historialReprocesamiento.js
```

### ⚡ **OPCIÓN C: Hybrid REST + GraphQL Style**
```
src/api/contabilidad/
├── index.js
├── resources/                 # Estilo REST por recursos
│   ├── cierres.js            # CRUD de cierres
│   ├── clasificaciones.js    # CRUD de clasificaciones
│   ├── documentos.js         # CRUD de documentos
│   └── uploads.js            # CRUD de uploads
├── operations/               # Operaciones complejas
│   ├── finalizarCierre.js    # Operación compleja
│   ├── reprocesarLibro.js    # Operación compleja
│   └── migrarClasificaciones.js
└── queries/                  # Consultas específicas
    ├── estadosCierre.js      # Consultas de estado
    ├── progresoProcesos.js   # Consultas de progreso
    └── resumenContable.js    # Consultas de resumen
```

### 🧩 **OPCIÓN D: Micro-Services Style (Preparación para Futuro)**
```
src/api/
├── services/
│   ├── cierreService.js      # Servicio completo de cierres
│   ├── clasificacionService.js
│   ├── documentoService.js
│   └── monitoringService.js
├── repositories/             # Abstracción de datos
│   ├── cierreRepository.js   # Operaciones CRUD puras
│   ├── clasificacionRepository.js
│   └── documentoRepository.js
├── queries/                  # Consultas especializadas
│   ├── cierreQueries.js
│   └── reporteQueries.js
└── mutations/                # Operaciones de escritura
    ├── cierreMutations.js
    └── clasificacionMutations.js
```

## 🏆 **RECOMENDACIÓN: Opción A + B Híbrida**

### 🎯 Estrategia Recomendada:
```
src/api/contabilidad/
├── index.js                   # Re-exportaciones principales
├── cierres/                   # Dominio de cierres
│   ├── index.js
│   ├── crud.js               # crear, obtener, actualizar
│   ├── estados.js            # gestión de estados
│   ├── finalizacion.js       # proceso de finalización
│   └── monitoreo.js          # progreso y tareas
├── clasificaciones/           # Dominio de clasificaciones
│   ├── index.js
│   ├── sets.js               # gestión de sets
│   ├── cuentas.js            # clasificación de cuentas
│   ├── bulk.js               # operaciones masivas
│   └── migracion.js          # migración temporal->persistente
├── documentos/                # Dominio de documentos
│   ├── index.js
│   ├── tipos.js              # tipos de documento
│   ├── nombresIngles.js      # traducción
│   └── plantillas.js         # templates
├── libroMayor/               # Dominio libro mayor
│   ├── index.js
│   ├── procesamiento.js      # upload y procesamiento
│   ├── incidencias.js        # gestión de incidencias
│   └── historial.js          # reprocesamiento
└── shared/                   # Utilidades compartidas
    ├── index.js
    ├── monitoring.js         # logs y actividad
    ├── uploads.js            # estados de upload
    └── validaciones.js       # validaciones comunes
```

## 🛠️ Plan de Implementación

### Fase 1: Preparación
1. **Análisis detallado** de dependencias entre funciones
2. **Mapeo** de funciones por dominio
3. **Identificación** de funciones compartidas
4. **Creación** de la estructura de carpetas

### Fase 2: Migración por Dominio
1. **Cierres** → Mover funciones básicas de CRUD
2. **Clasificaciones** → Mover el conjunto más grande
3. **Documentos** → Mover tipos y nombres en inglés
4. **Libro Mayor** → Mover procesamiento e incidencias
5. **Shared** → Mover utilidades y monitoring

### Fase 3: Refactorización de Importaciones
1. **Actualizar** imports en feature folders
2. **Mantener** compatibilidad con re-exportaciones
3. **Testing** exhaustivo de todas las funcionalidades
4. **Documentación** de la nueva estructura

### Fase 4: Optimización
1. **Tree shaking** mejorado
2. **Lazy loading** de módulos pesados
3. **Caching** implementado por dominio
4. **Error handling** consistente

## ✅ Ventajas de la Refactorización

### 🎯 Mantenibilidad
- **Archivos pequeños** y enfocados
- **Responsabilidad única** por archivo
- **Fácil localización** de funciones

### ⚡ Performance
- **Tree shaking** más efectivo
- **Lazy loading** granular
- **Bundle splitting** automático

### 🧩 Escalabilidad
- **Nuevas funcionalidades** en su dominio
- **Testing** independiente por dominio
- **Refactoring** aislado

### 👥 Developer Experience
- **Imports más claros** y semánticos
- **Autocompletado** mejorado
- **Documentación** organizada

## 🚨 Consideraciones

### ⚠️ Riesgos
- **Imports rotos** durante migración
- **Dependencias circulares** potenciales
- **Overhead** de re-exportaciones

### 🛡️ Mitigaciones
- **Migración gradual** por dominio
- **Tests de regresión** exhaustivos
- **Periodo de compatibilidad** con estructura antigua
- **Rollback plan** preparado
