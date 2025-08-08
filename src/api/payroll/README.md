# Payroll API - Sistema Modular de Nómina

Esta es la versión mejorada y modular de la API de nómina, diseñada para ser más escalable, mantenible y organizada.

## Estructura de Módulos

### 📂 `config.js`
Configuración base del sistema, incluyendo:
- Endpoints principales
- Estados de cierres e incidencias
- Tipos de archivos
- Tolerancias por defecto

### 📂 `closures.js`
Gestión de cierres de nómina:
- ✅ Operaciones CRUD de cierres
- ✅ Gestión de estados
- ✅ Consolidación de datos
- ✅ Finalización de cierres

### 📂 `incidents.js`
Sistema de incidencias:
- ✅ Generación y gestión de incidencias
- ✅ Cambio de estados
- ✅ Asignación de usuarios
- ✅ Aprobación/rechazo
- ✅ Resúmenes y estadísticas

### 📂 `analysis.js`
Análisis de datos y variaciones:
- ✅ Análisis automático de datos
- ✅ Detección de variaciones salariales
- ✅ Comparaciones temporales
- ✅ Análisis de patrones
- ✅ Reportes de análisis

### 📂 `files.js`
Gestión de archivos:
- ✅ Upload de archivos (libro, movimientos, novedades)
- ✅ Plantillas de descarga
- ✅ Procesamiento de archivos
- ✅ Estados de upload
- ✅ Gestión de headers y mapeo

### 📂 `discrepancies.js`
Sistema de discrepancias:
- ✅ Detección automática de discrepancias
- ✅ Resolución de discrepancias
- ✅ Comparación entre sistemas
- ✅ Validación de consistencia
- ✅ Configuración de tolerancias

### 📂 `resolutions.js`
Gestión de resoluciones:
- ✅ Creación y seguimiento de resoluciones
- ✅ Historial y cronología
- ✅ Sistema de turnos
- ✅ Comentarios y comunicación
- ✅ Plantillas de resolución

### 📂 `reports.js`
Generación de reportes:
- ✅ Reportes básicos y comparativos
- ✅ Reportes de cumplimiento
- ✅ Reportes financieros
- ✅ Reportes personalizados
- ✅ Exportación múltiple (Excel, PDF, CSV)
- ✅ Dashboards y KPIs

### 📂 `concepts.js`
Conceptos y clasificaciones:
- ✅ Gestión de conceptos de remuneración
- ✅ Clasificaciones automáticas
- ✅ Configuración por cliente
- ✅ Validación de consistencia
- ✅ Importación/exportación

## Uso

### Importación Individual
```javascript
// Importar módulos específicos
import { closures, incidents, analysis } from '@/api/payroll';

// Usar funciones específicas
const closure = await closures.getMonthlyClosure(clientId, period);
const incidents = await incidents.getClosureIncidents(closureId);
```

### Importación Completa
```javascript
// Importar toda la API
import payroll from '@/api/payroll';

// Usar módulos
const closure = await payroll.closures.getMonthlyClosure(clientId, period);
const incidents = await payroll.incidents.getClosureIncidents(closureId);
```

### Importación por Módulo
```javascript
// Importar módulos individuales
import * as closures from '@/api/payroll/closures';
import * as incidents from '@/api/payroll/incidents';

// Usar directamente
const closure = await closures.getMonthlyClosure(clientId, period);
```

## Mejoras sobre la API Original

### ✅ Completadas
1. **Modularización**: Separación lógica por funcionalidad
2. **Nombres Descriptivos**: Funciones con nombres más claros
3. **Documentación**: JSDoc completo en todas las funciones
4. **Consistencia**: Parámetros y respuestas estandarizadas
5. **Configuración Centralizada**: Estados y endpoints en un solo lugar
6. **Logging Mejorado**: Logs estructurados y informativos

### 🔄 Mejoras Implementadas
- Funciones con nombres más descriptivos en inglés
- Parámetros más consistentes
- Mejor manejo de errores
- Configuración centralizada de endpoints
- Documentación completa
- Separación de responsabilidades

## Consideraciones de Migración

### Compatibilidad con Backend
- Los endpoints están configurados para `/payroll/` pero pueden necesitar ajustes según el backend real
- Algunos endpoints pueden no existir aún en el backend y requerirán implementación
- La estructura de respuestas puede necesitar adaptación

### Funciones Pendientes
Algunas funcionalidades de la API original no se implementaron si:
1. No se tenía claridad sobre su funcionamiento exacto
2. Dependían de estructura de backend específica
3. Eran muy específicas a la implementación anterior

### Próximos Pasos
1. Validar endpoints con el backend real
2. Ajustar estructura de respuestas según API real
3. Implementar funciones pendientes
4. Pruebas de integración
5. Migración gradual desde la API anterior

## Notas Técnicas

- **Configuración**: Centralizada en `config.js`
- **Tipos**: TypeScript-ready (JSDoc permite inferencia de tipos)
- **Errores**: Manejo consistente de errores
- **Logging**: Sistema de logs estructurado
- **Formatos**: Soporte para múltiples formatos de exportación

## Estados del Sistema

### Estados de Cierres
- `pending`: Pendiente
- `in_progress`: En progreso
- `review`: En revisión
- `completed`: Completado
- `rejected`: Rechazado

### Estados de Incidencias
- `pending`: Pendiente
- `in_progress`: En progreso
- `resolved`: Resuelta
- `approved`: Aprobada
- `rejected`: Rechazada

### Tipos de Archivos
- `payroll_book`: Libro de remuneraciones
- `monthly_movements`: Movimientos mensuales
- `analyst_files`: Archivos del analista
- `novelties`: Novedades
- `settlements`: Finiquitos
- `incidents`: Incidencias
- `entries`: Ingresos
