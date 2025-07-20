# 📋 Documentación Completa de Base de Datos - Módulo Nómina

## 🎯 Introducción

Este documento presenta la arquitectura completa de la base de datos del módulo de nómina del SGM (Sistema de Gestión de Microempresas). El módulo maneja el procesamiento de nóminas con un enfoque de consolidación de múltiples fuentes de datos y manejo colaborativo de incidencias.

## 🏗️ Arquitectura General

La base de datos está estructurada en **6 niveles principales**:

1. **🔄 Gestión de Cierres** - Control del proceso de cierre mensual
2. **📄 Archivos y Cargas** - Gestión de archivos subidos y su procesamiento  
3. **👥 Empleados y Conceptos** - Datos de empleados y conceptos de remuneración
4. **📊 Movimientos de Personal** - Altas, bajas, ausencias y variaciones
5. **🚨 Incidencias y Discrepancias** - Sistema colaborativo de resolución
6. **💼 Consolidación Final** - Datos procesados y listos para reportes

---

## 1️⃣ GESTIÓN DE CIERRES

### 🔄 CierreNomina
**Propósito**: Entidad central que controla el proceso completo del cierre mensual de nómina.

**Atributos Principales**:
- `cliente`: Referencia al cliente (empresa)
- `periodo`: Mes/año del cierre (YYYY-MM)
- `estado`: Estado del proceso de cierre
- `estado_consolidacion`: Control de consolidación de datos
- `estado_incidencias`: Control del manejo de incidencias
- `clasificaciones_archivos`: JSON con mapeo de archivos
- `configuracion_tolerancias`: JSON con tolerancias para análisis

**Estados del Cierre**:
- `pendiente` → `cargando_archivos` → `archivos_completos` → `clasificaciones_completas` → `consolidado` → `completado`

**Métodos Importantes**:
- `actualizar_estado_automatico()`: Actualiza estado según archivos procesados
- `puede_generar_incidencias()`: Verifica si está listo para análisis
- `_verificar_archivos_listos()`: Valida que archivos obligatorios estén procesados

### ✅ ChecklistItem  
**Propósito**: Elementos de verificación manual del cierre.

**Atributos**:
- `cierre`: Referencia al cierre
- `descripcion`: Descripción del item a verificar
- `estado`: `pendiente` | `completado` | `no_realizado`
- `comentario`: Observaciones del analista

---

## 2️⃣ ARCHIVOS Y CARGAS

### 📊 LibroRemuneracionesUpload
**Propósito**: Archivo principal con datos de remuneraciones del período.

**Atributos**:
- `archivo`: Archivo Excel/CSV subido
- `estado`: Control del procesamiento
- `header_json`: Headers detectados en el archivo
- `upload_log`: Referencia al log del upload

**Estados**: `pendiente` → `analizando_hdrs` → `hdrs_analizados` → `clasif_en_proceso` → `clasif_pendiente` → `clasificado`

### 🔄 MovimientosMesUpload
**Propósito**: Archivo con movimientos de personal (altas, bajas, ausencias).

**Atributos**:
- `archivo`: Archivo con movimientos
- `estado`: Estado de procesamiento
- `resultados_procesamiento`: JSON con resultados del análisis

**Estados**: `pendiente` → `en_proceso` → `procesado` | `con_error` | `con_errores_parciales`

### 👔 ArchivoAnalistaUpload
**Propósito**: Archivos específicos subidos por analistas (ingresos, finiquitos, incidencias).

**Atributos**:
- `tipo_archivo`: `ingresos` | `finiquitos` | `incidencias`
- `archivo`: Archivo subido
- `analista`: Usuario que subió el archivo
- `estado`: Control de procesamiento

### 📝 ArchivoNovedadesUpload
**Propósito**: Archivo opcional con novedades/variaciones del período.

**Atributos**:
- `archivo`: Archivo de novedades
- `header_json`: Headers detectados
- `estado`: Similar a libro de remuneraciones

### 📋 UploadLogNomina (implícito)
**Propósito**: Log de todos los uploads realizados (referenciado en otros modelos).

---

## 3️⃣ EMPLEADOS Y CONCEPTOS

### 👥 EmpleadoCierre
**Propósito**: Empleado específico de un cierre con datos básicos.

**Atributos**:
- `cierre`: Referencia al cierre
- `rut`: RUT del empleado
- `nombre`, `apellido_paterno`, `apellido_materno`: Datos personales
- `rut_empresa`: RUT de la empresa empleadora
- `dias_trabajados`: Días trabajados en el período

**Restricciones**: Único por cierre y RUT.

### 👤 EmpleadoCierreNovedades
**Propósito**: Empleado específico para procesamiento de novedades (separado del principal).

**Atributos**: Similar a EmpleadoCierre pero sin días trabajados.

### 💰 ConceptoRemuneracion
**Propósito**: Conceptos de remuneración clasificados por cliente.

**Atributos**:
- `cliente`: Cliente propietario
- `nombre_concepto`: Nombre del concepto
- `clasificacion`: Tipo de concepto (haber, descuento, etc.)
- `hashtags`: JSON con etiquetas de clasificación
- `usuario_clasifica`: Quien clasificó el concepto
- `vigente`: Si está activo

**Clasificaciones Disponibles**:
- Haberes imponibles/no imponibles
- Descuentos legales/otros
- Aportes patronales
- Solo informativos

### 💵 RegistroConceptoEmpleado
**Propósito**: Registros individuales de conceptos por empleado del libro de remuneraciones.

**Atributos**:
- `empleado`: Referencia al empleado
- `concepto`: Concepto clasificado (puede ser null)
- `nombre_concepto_original`: Nombre tal como aparece en archivo
- `monto`: Valor del concepto (string, puede contener texto)

**Propiedades Calculadas**:
- `monto_numerico`: Convierte monto a número
- `es_numerico`: Verifica si es convertible

### 🔗 ConceptoRemuneracionNovedades
**Propósito**: Mapeo entre headers de novedades y conceptos del libro principal.

**Atributos**:
- `nombre_concepto_novedades`: Header en archivo de novedades
- `concepto_libro`: Mapeo al concepto principal
- `usuario_mapea`: Usuario que creó el mapeo
- `activo`: Estado del mapeo

### 📊 RegistroConceptoEmpleadoNovedades
**Propósito**: Registros de conceptos para empleados desde archivo de novedades.

**Atributos**: Similar a RegistroConceptoEmpleado pero con referencia a novedades.

---

## 4️⃣ MOVIMIENTOS DE PERSONAL

### ⬆️ MovimientoAltaBaja
**Propósito**: Registros de ingresos y retiros de empleados.

**Atributos**:
- Datos completos del empleado
- `fecha_ingreso`, `fecha_retiro`: Fechas del movimiento
- `alta_o_baja`: Tipo de movimiento
- `motivo`: Razón del movimiento
- `sueldo_base`: Sueldo base del empleado

### 🏥 MovimientoAusentismo
**Propósito**: Registros de ausencias (licencias médicas, permisos, etc.).

**Atributos**:
- `fecha_inicio_ausencia`, `fecha_fin_ausencia`: Período de ausencia
- `dias`: Cantidad de días
- `tipo`: Tipo de ausentismo
- `motivo`, `observaciones`: Detalles adicionales

### 🏖️ MovimientoVacaciones
**Propósito**: Registros específicos de vacaciones.

**Atributos**:
- `fecha_inicio`, `fecha_fin_vacaciones`, `fecha_retorno`: Fechas del período
- `cantidad_dias`: Días de vacaciones

### 💸 MovimientoVariacionSueldo
**Propósito**: Cambios en el sueldo base de empleados.

**Atributos**:
- `sueldo_base_anterior`, `sueldo_base_actual`: Valores antes/después
- `porcentaje_reajuste`: Porcentaje de cambio
- `variacion_pesos`: Diferencia en pesos

### 📋 MovimientoVariacionContrato
**Propósito**: Cambios en tipo de contrato de empleados.

**Atributos**:
- `tipo_contrato_anterior`, `tipo_contrato_actual`: Tipos antes/después

### 👔 AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso
**Propósito**: Datos específicos subidos por analistas para validación.

**Atributos Comunes**:
- `archivo_origen`: Referencia al archivo que los generó
- `rut`, `nombre`: Datos del empleado
- Campos específicos según el tipo de movimiento

---

## 5️⃣ INCIDENCIAS Y DISCREPANCIAS

### 🚨 IncidenciaCierre
**Propósito**: Incidencias detectadas que requieren resolución colaborativa entre analista y supervisor.

**Atributos Principales**:
- `tipo_incidencia`: Tipo de problema detectado
- `descripcion`: Descripción detallada
- `valor_libro`, `valor_novedades`, `valor_movimientos`, `valor_analista`: Valores de cada fuente
- `estado`: Estado de resolución
- `prioridad`: Nivel de importancia
- `impacto_monetario`: Impacto económico calculado
- `asignado_a`: Usuario responsable de resolver

**Tipos de Incidencias**:
- `variacion_concepto`: Variaciones >30% en conceptos
- `concepto_nuevo`: Conceptos que aparecen por primera vez
- `concepto_perdido`: Conceptos que desaparecen
- `empleado_deberia_ingresar`: Empleados esperados pero no presentes
- `empleado_no_deberia_estar`: Empleados presentes pero no esperados
- `ausentismo_continuo`: Ausencias prolongadas

**Estados de Resolución**:
- `pendiente` → `resuelta_analista` → `aprobada_supervisor` | `rechazada_supervisor`

### 💬 ResolucionIncidencia
**Propósito**: Historial de conversaciones y resoluciones de incidencias.

**Atributos**:
- `tipo_resolucion`: Tipo de acción tomada
- `comentario`: Explicación/justificación
- `adjunto`: Archivo de soporte
- `valor_corregido`: Valor corregido si aplica
- `usuarios_mencionados`: Usuarios mencionados en la resolución

### 🔍 DiscrepanciaCierre
**Propósito**: Sistema informativo de verificación de datos (no requiere resolución obligatoria).

**Atributos**:
- `tipo_discrepancia`: Tipo de diferencia encontrada
- Valores comparados entre fuentes
- Solo registra diferencias para conocimiento

**Tipos de Discrepancias**:
- Diferencias Libro vs Novedades
- Diferencias MovimientosMes vs Analista
- Datos faltantes o inconsistentes

---

## 6️⃣ ANÁLISIS Y CONSOLIDACIÓN

### 📊 AnalisisDatosCierre
**Propósito**: Análisis estadístico comparativo con el período anterior.

**Atributos**:
- Contadores actuales vs anteriores (empleados, ingresos, finiquitos, ausentismos)
- `ausentismos_por_tipo_actual`, `ausentismos_por_tipo_anterior`: JSON con estadísticas
- `tolerancia_variacion_salarial`: Configuración de tolerancias
- `estado`: Estado del análisis

**Métodos**:
- `calcular_variaciones()`: Calcula variaciones porcentuales
- `_calcular_variacion_porcentual()`: Cálculo individual

### 📈 IncidenciaVariacionSalarial
**Propósito**: Incidencias específicas de cambios salariales significativos.

**Atributos**:
- Datos salariales comparativos
- `porcentaje_variacion`: Porcentaje de cambio
- `tipo_variacion`: `aumento` | `disminucion`
- Sistema completo de justificación y aprobación

**Flujo de Resolución**:
1. Detección automática
2. Asignación a analista
3. Justificación del analista
4. Revisión del supervisor
5. Aprobación/rechazo final

---

## 7️⃣ CONSOLIDACIÓN FINAL

### 💼 NominaConsolidada
**Propósito**: **REGISTRO FINAL** - Un empleado por cierre con toda su información consolidada y totales finales.

**Atributos Principales**:
- `rut_empleado`, `nombre_empleado`: Identificación
- `cargo`, `centro_costo`: Ubicación organizacional
- `estado_empleado`: Estado del empleado en este período
- `total_haberes`, `total_descuentos`, `liquido_pagar`: **TOTALES FINALES**
- `dias_trabajados`, `dias_ausencia`: Información de asistencia
- `fuente_datos`: JSON con fuentes usadas para consolidar

**Estados de Empleado**:
- `activo`: Empleado normal
- `nueva_incorporacion`: Ingreso nuevo
- `finiquito`: Empleado retirado
- `ausente_total`: Sin asistencia en el período
- `ausente_parcial`: Ausencias parciales

### 💰 ConceptoConsolidado
**Propósito**: Conceptos individuales por empleado con clasificación y totales finales.

**Atributos**:
- `codigo_concepto`, `nombre_concepto`: Identificación
- `tipo_concepto`: Clasificación final del concepto
- `monto_total`: **MONTO FINAL CONSOLIDADO**
- `cantidad`: Cantidad/horas si aplica
- `fuente_archivo`: Archivo origen del dato

**Tipos de Concepto**:
- `haber_imponible`, `haber_no_imponible`
- `descuento_legal`, `otro_descuento`
- `aporte_patronal`, `informativo`

### 🔄 MovimientoPersonal
**Propósito**: Resumen de movimientos detectados automáticamente por empleado.

**Atributos**:
- `tipo_movimiento`: Tipo de cambio detectado
- `motivo`: Razón del movimiento
- `dias_ausencia`: Días si es ausencia
- `fecha_movimiento`: Fecha del cambio
- `detectado_por_sistema`: Sistema que lo detectó

---

## 🔗 RELACIONES PRINCIPALES

### Flujo de Datos:
```
CierreNomina
├── Archivos Upload (4 tipos)
│   ├── LibroRemuneracionesUpload → EmpleadoCierre + RegistroConceptoEmpleado
│   ├── MovimientosMesUpload → MovimientoAltaBaja/Ausentismo/Vacaciones/etc.
│   ├── ArchivoAnalistaUpload → AnalistaFiniquito/Incidencia/Ingreso
│   └── ArchivoNovedadesUpload → EmpleadoCierreNovedades + RegistroConceptoEmpleadoNovedades
│
├── Análisis y Detección
│   ├── AnalisisDatosCierre → IncidenciaVariacionSalarial
│   ├── DiscrepanciaCierre (verificaciones)
│   └── IncidenciaCierre → ResolucionIncidencia
│
└── Consolidación Final
    ├── NominaConsolidada (RESULTADO FINAL)
    ├── ConceptoConsolidado (por empleado)
    └── MovimientoPersonal (cambios detectados)
```

### Integraciones:
- **Cliente**: Todas las entidades se relacionan con el cliente
- **User**: Usuarios involucrados en clasificación y resolución
- **UploadLogNomina**: Trazabilidad de archivos

---

## 📋 CASOS DE USO PRINCIPALES

1. **Subida y Procesamiento de Archivos**
   - Upload → Análisis de headers → Clasificación → Procesamiento → Consolidación

2. **Detección de Incidencias**
   - Comparación automática → Generación de incidencias → Asignación → Resolución colaborativa

3. **Verificación de Datos**
   - Generación de discrepancias informativas → Revisión por analista

4. **Consolidación Final**
   - Datos de múltiples fuentes → NominaConsolidada → Reportes y liquidaciones

5. **Análisis Comparativo**
   - Comparación con período anterior → Detección de variaciones → Gestión de cambios significativos

---

## 🎯 CONCLUSIÓN

La base de datos del módulo nómina implementa un **sistema completo de consolidación de datos** que:

- ✅ **Procesa múltiples fuentes** (libro, movimientos, analista, novedades)
- ✅ **Detecta automáticamente** inconsistencias e incidencias
- ✅ **Facilita resolución colaborativa** entre analistas y supervisores  
- ✅ **Consolida datos finales** listos para reportes
- ✅ **Mantiene trazabilidad completa** del proceso
- ✅ **Permite análisis estadísticos** comparativos

El diseño permite manejar la complejidad inherente del procesamiento de nóminas manteniendo la integridad de datos y facilitando la detección temprana de problemas.
