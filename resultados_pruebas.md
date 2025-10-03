# Resultados Pruebas - RindeGastos

Documento que detalla los problemas detectados durante las pruebas del sistema de procesamiento de archivos RindeGastos.

## Problemas Detectados

### 1. Error en Cuenta IVA - Tipo Documento 33
**Problema:** Para el tipo de documento 33, cuenta IVA, los montos están registrándose incorrectamente al Haber cuando deberían ir al Debe.

**Estado:** ❌ Error crítico  
**Impacto:** Afecta el balance contable de las facturas con IVA  
**Prioridad:** Alta

---

### 2. Falta Integración de Monto Exento en Gastos
**Problema:** Para todos los tipos de documento, en la cuenta gastos, el campo "Monto al Debe Moneda Base" debe incluir la suma del monto exento que aparece en el Excel de entrada. Adicionalmente, el monto exento también debe registrarse en la columna "Monto 2 Detalle Libro".

**Estado:** ❌ Funcionalidad faltante  
**Impacto:** Cálculos incompletos en los gastos y falta de registro en detalle libro  
**Prioridad:** Alta  
**Nota:** Nuevo requerimiento identificado

---

### 3. Tipo de Documento No Se Transfiere al Output
**Problema:** El tipo de documento presente en el archivo de entrada no aparece en la columna correspondiente del archivo de salida.

**Estado:** ❌ Mapeo faltante  
**Impacto:** Pérdida de trazabilidad del tipo de documento  
**Prioridad:** Media

---

### 4. Folio No Se Transfiere a Número de Documento
**Problema:** El folio del archivo de entrada debe estar presente en la columna "Número de Documento" del archivo de salida, pero actualmente no se está mapeando.

**Estado:** ❌ Mapeo faltante  
**Impacto:** Pérdida de referencia del documento original  
**Prioridad:** Media

---

### 5. Validación de Guiones en Frontend
**Problema:** Se requiere agregar indicaciones en el frontend y bloqueo para que no se permita el uso de guiones en ciertos campos.

**Estado:** ❌ Validación faltante  
**Impacto:** Potencial corrupción de datos  
**Prioridad:** Media  
**Mensaje sugerido:** "Si su cuenta tiene guiones, colóquelos sin espacios adicionales"

---

## Próximos Pasos

1. **Inmediato:** Corregir el problema crítico del IVA en tipo documento 33
2. **Corto plazo:** Implementar la suma de monto exento en gastos
3. **Mediano plazo:** Completar los mapeos faltantes (tipo documento y folio)
4. **Frontend:** Agregar validaciones para manejo de guiones

---

**Fecha de reporte:** 3 de octubre de 2025  
**Responsable:** Equipo de desarrollo SGM