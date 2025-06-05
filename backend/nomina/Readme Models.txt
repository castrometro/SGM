# 📘 README — Modelo de Cierre de Nómina

## 🎯 Propósito

Este modelo define cómo se estructura y almacena la información del proceso mensual de cierre de nómina de un cliente. Su objetivo es que todos los datos del libro de remuneraciones (archivo Excel) queden accesibles, trazables y comparables desde la base de datos sin volver a procesar el archivo.

---

## 🧩 Componentes del Modelo

### 1. `CierreNomina`

Representa un proceso mensual de remuneración para un cliente.

* Identifica cliente y periodo (`cliente + periodo` es único).
* Guarda estado del proceso (pendiente, consolidado, validado, etc.).

### 2. `EmpleadoCierre`

Es un snapshot del trabajador en ese mes:

* RUT, nombre, apellidos.
* RUT de la empresa, días trabajados (extraídos del libro).

### 3. `RegistroConceptoEmpleado`

Cada concepto aplicado a un empleado:

* El nombre tal como vino en el libro.
* Su valor.
* Una posible referencia al concepto clasificado (`ConceptoRemuneracion`).

Permite consultas del tipo:

```sql
SELECT * FROM registroconceptoempleado WHERE concepto.clasificacion = 'haber';
```

### 4. `ConceptoRemuneracion`

Diccionario de conceptos definidos por el analista para cada cliente:

* Se clasifican como haber, descuento o informativo.
* Admiten hashtags múltiples.

### 5. `MovimientoIngreso`, `MovimientoFiniquito`, `MovimientoAusentismo`

Movimientos extraídos desde Talana, estandarizados por hoja:

* Asociados al cierre y opcionalmente al empleado si está emparejado.
* Sirven como base para comparar contra archivos del analista.

---

## 🔁 Flujo Esperado

1. El analista sube el libro de remuneraciones (Excel).
2. El sistema lee una vez el archivo y crea:

   * Un `EmpleadoCierre` por trabajador.
   * Un `RegistroConceptoEmpleado` por concepto aplicado.
3. Los conceptos sin clasificar se muestran al analista.
4. El analista clasifica conceptos (como haber/descuento/etc.).
5. Se actualiza automáticamente el vínculo de conceptos a sus clasificaciones.
6. Todo queda trazable y listo para comparar con las novedades y Talana.

---

## ✅ Beneficios

* 📌 Lectura única del Excel.
* 🔍 Consultas SQL y ORM posibles para cualquier dato.
* 📊 Reportes e insights por concepto, empleado, cierre, cliente.
* 🔄 Base sólida para validaciones automáticas y generación de incidencias.
* 💡 Preparado para extender a dashboards, IA o reportería regulatoria.

---

## 🚧 Futuro

* Incorporar `IncidenciaNovedad` para diferencias entre libro y novedades.
* Agregar histórico por concepto y comparaciones multi-periodo.
* Implementar versionado de libros y movimientos.
