# 🔄 Documentación: Flujo de Resubida de Archivos - Sistema de Nómina

## 📋 Resumen del Problema y Solución

### ⚠️ **Problema Identificado**

Cuando un usuario utilizaba la funcionalidad de "Resubir archivo" en el sistema de Cierre de Nómina, se identificó que:

1. **Los datos derivados NO se eliminaban** cuando se eliminaba el archivo original
2. **Al subir un nuevo archivo**, los datos se actualizaban pero podían quedar inconsistencias
3. **Falta de trazabilidad** sobre qué datos se eliminaron durante la resubida

### ✅ **Solución Implementada**

Se implementaron métodos `perform_destroy` personalizados en todos los ViewSets de archivos para garantizar la eliminación completa de datos relacionados y el logging apropiado.

---

## 📁 Tipos de Archivos y Datos Relacionados

### 1. **Libro de Remuneraciones** (`LibroRemuneracionesUpload`)

**Datos que crea al procesarse:**
- `EmpleadoCierre` - Empleados del cierre
- `RegistroConceptoEmpleado` - Conceptos/montos por empleado
- Headers clasificados y conceptos de remuneración

**Datos eliminados al usar "Resubir":**
```python
# 1. Todos los registros de conceptos de empleados
for empleado in cierre.empleados.all():
    empleado.registroconceptoempleado_set.all().delete()

# 2. Todos los empleados del cierre
cierre.empleados.all().delete()

# 3. Reset del estado del cierre
cierre.estado = 'pendiente'
cierre.estado_incidencias = 'analisis_pendiente'
```

### 2. **Movimientos del Mes** (`MovimientosMesUpload`)

**Datos que crea al procesarse:**
- `MovimientoAltaBaja`
- `MovimientoAusentismo` 
- `MovimientoVacaciones`
- `MovimientoVariacionSueldo`
- `MovimientoVariacionContrato`

**Datos eliminados al usar "Resubir":**
```python
# Eliminar todos los movimientos del cierre
cierre.movimientoaltabaja_set.all().delete()
cierre.movimientoausentismo_set.all().delete()
cierre.movimientovacaciones_set.all().delete()
cierre.movimientovariacionsueldo_set.all().delete()
cierre.movimientovariacioncontrato_set.all().delete()
```

### 3. **Archivos del Analista** (`ArchivoAnalistaUpload`)

**Tipos y datos que crean:**

#### Finiquitos:
- `AnalistaFiniquito` - Datos de finiquitos por empleado

#### Incidencias:
- `AnalistaIncidencia` - Datos de ausentismos/incidencias

#### Ingresos:
- `AnalistaIngreso` - Datos de nuevos ingresos

**Datos eliminados al usar "Resubir":**
```python
# Los modelos tienen CASCADE automático desde archivo_origen
# Se eliminan automáticamente al eliminar ArchivoAnalistaUpload
```

### 4. **Archivos de Novedades** (`ArchivoNovedadesUpload`)

**Datos que crea al procesarse:**
- `EmpleadoCierreNovedades` - Empleados específicos para novedades
- `RegistroConceptoEmpleadoNovedades` - Conceptos/montos de novedades

**Datos eliminados al usar "Resubir":**
```python
# Eliminar empleados de novedades (CASCADE elimina registros)
cierre.empleados_novedades.all().delete()
```

---

## 🔧 Implementación Técnica

### Métodos `perform_destroy` Agregados

**Ubicación:** `/backend/nomina/views.py`

```python
# LibroRemuneracionesUploadViewSet
def perform_destroy(self, instance):
    # Logging + eliminación completa de datos relacionados
    
# MovimientosMesUploadViewSet  
def perform_destroy(self, instance):
    # Logging + eliminación de movimientos
    
# ArchivoAnalistaUploadViewSet
def perform_destroy(self, instance):
    # Logging + eliminación automática por CASCADE
    
# ArchivoNovedadesUploadViewSet
def perform_destroy(self, instance):
    # Logging + eliminación de empleados de novedades
```

### Características de la Implementación

1. **✅ Transacciones Atómicas:** Todos los deletes se ejecutan en una transacción
2. **✅ Logging Completo:** Se registra la actividad antes de eliminar
3. **✅ Conteo de Registros:** Se cuenta cuántos registros se eliminan
4. **✅ Reset de Estado:** El cierre vuelve a estado 'pendiente'

---

## 📊 Flujo de "Resubida"

### Antes de la Implementación:
```
Usuario → Eliminar Archivo → ❌ Datos quedan huérfanos
Usuario → Subir Nuevo → ⚠️ Actualiza pero inconsistencias
```

### Después de la Implementación:
```
Usuario → Eliminar Archivo → ✅ Elimina TODOS los datos relacionados
                           → ✅ Registra actividad en logs
                           → ✅ Reset estado del cierre
Usuario → Subir Nuevo → ✅ Procesa limpiamente desde cero
```

---

## 🚨 Consideraciones Importantes

### ⚠️ **Datos que se CONSERVAN** (por diseño):

1. **Clasificaciones de Conceptos** (`ConceptoRemuneracion`)
   - Se mantienen a nivel de cliente, no de cierre específico
   - Son reutilizables entre diferentes cierres

2. **Logs de Actividad** (`TarjetaActivityLogNomina`)
   - Historial completo de acciones del usuario
   - Incluye registro de eliminaciones

3. **Upload Logs** (`UploadLogNomina`)
   - Historial de subidas de archivos
   - Trazabilidad completa

### ✅ **Datos que se ELIMINAN**:

1. **Todos los datos derivados específicos del archivo**
2. **Empleados y sus registros asociados** (para libro)
3. **Movimientos del mes** (para movimientos)
4. **Datos del analista** (para archivos analista)
5. **Empleados de novedades** (para novedades)

---

## 🧪 Testing y Validación

### Para verificar que funciona correctamente:

1. **Subir un archivo** y verificar que se crean datos
2. **Usar "Resubir archivo"** y verificar que:
   - Se eliminan TODOS los datos relacionados
   - Se registra la actividad en logs
   - El estado del cierre vuelve a 'pendiente'
3. **Subir nuevo archivo** y verificar que:
   - Se procesan los datos limpiamente
   - No hay duplicados ni inconsistencias

### Consultas SQL para verificar limpieza:

```sql
-- Verificar empleados del cierre
SELECT COUNT(*) FROM nomina_empleadocierre WHERE cierre_id = {cierre_id};

-- Verificar registros de conceptos
SELECT COUNT(*) FROM nomina_registroconceptoempleado 
WHERE empleado_id IN (
    SELECT id FROM nomina_empleadocierre WHERE cierre_id = {cierre_id}
);

-- Verificar movimientos
SELECT COUNT(*) FROM nomina_movimientoaltabaja WHERE cierre_id = {cierre_id};
-- (repetir para otros tipos de movimientos)
```

---

## 📝 Notas para el Equipo

1. **Esta implementación es DESTRUCTIVA** - una vez que se elimina un archivo, todos sus datos se pierden permanentemente
2. **El logging es completo** - toda actividad queda registrada para auditoría
3. **Las clasificaciones se conservan** - el trabajo de clasificar conceptos no se pierde
4. **Es seguro usar "Resubir"** - el sistema garantiza consistencia de datos

Esta solución asegura que el flujo de resubida sea robusto, consistente y completamente trazable.
