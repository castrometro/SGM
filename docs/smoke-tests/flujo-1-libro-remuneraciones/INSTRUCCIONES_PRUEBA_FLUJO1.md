# 🧪 INSTRUCCIONES DE PRUEBA - Flujo 1: Libro de Remuneraciones

**Fecha**: 24 octubre 2025  
**Cierre de prueba**: ID 35 (Periodo 2025-10)  
**Cliente**: EMPRESA SMOKE TEST (ID: 20)

---

## 📋 Datos de Prueba

- **Excel**: `/tmp/libro_remuneraciones_smoke_test.xlsx`
- **Contenido**:
  - 5 empleados
  - 10 conceptos de nómina
  - Columnas: RUT, NOMBRE COMPLETO, CARGO, CENTRO DE COSTO, AREA + conceptos

---

## 🚀 PASO A PASO - Prueba Manual en Frontend

### PASO 1: Abrir el Cierre

1. Navega a: **http://172.17.11.18:5174/nomina/cierre/35**

2. Verás la página de "Cierre Detalle Nómina" con:
   - Info del cierre (periodo 2025-10)
   - Cliente: EMPRESA SMOKE TEST
   - Sección "Archivos Talana" (donde está el libro de remuneraciones)

---

### PASO 2: Subir Archivo Excel

1. **Localizar sección**: Busca la tarjeta "Libro de Remuneraciones"

2. **Click en botón**: "Seleccionar archivo" o área de drop zone

3. **Seleccionar archivo**: 
   - Ruta: `/tmp/libro_remuneraciones_smoke_test.xlsx`
   - Nombre: `libro_remuneraciones_smoke_test.xlsx`
   - Tamaño: ~5.6 KB

4. **Esperar subida**: Verás un spinner "Subiendo..."

5. **Verificar respuesta**:
   ```
   ✅ Archivo subido exitosamente
   Estado: "Analizando headers..."
   ```

**⏱️ Tiempo esperado**: 2-3 segundos

**🎯 Lo que pasa en backend**:
- Se crea `LibroRemuneracionesUpload` (ID ~79)
- Se crea `UploadLogNomina` para auditoría
- Se inicia Celery task `analizar_headers_libro_remuneraciones_con_logging`

---

### PASO 3: Análisis Automático de Headers

1. **Polling automático**: El frontend consulta cada 2 segundos

2. **Esperar mensaje**: "Headers analizados"

3. **Verificar estado**: 
   - Estado del libro cambia de `pendiente` → `analizado`
   - Se abre modal automáticamente con headers

**⏱️ Tiempo esperado**: 3-5 segundos

**🎯 Lo que pasa en backend**:
- Celery lee el Excel con pandas
- Extrae columnas: ['RUT', 'NOMBRE COMPLETO', 'CARGO', 'SUELDO BASE', ...]
- Clasifica automáticamente:
  - `empleado`: RUT, NOMBRE COMPLETO, CARGO, CENTRO DE COSTO, AREA
  - `concepto`: SUELDO BASE, BONO PRODUCTIVIDAD, COLACION, etc.
- Guarda en `header_json` del libro

---

### PASO 4: Clasificación Manual de Headers

1. **Modal abierto**: "Clasificar Headers"

2. **Revisar clasificación automática**:
   - Verde (alta confianza): Columnas de empleado detectadas automáticamente
   - Amarillo (baja confianza): Conceptos que debes revisar

3. **Tabla de headers**:
   ```
   | Columna Excel      | Tipo     | Confianza |
   |--------------------|----------|-----------|
   | RUT                | empleado | 90%       |
   | NOMBRE COMPLETO    | empleado | 90%       |
   | CARGO              | empleado | 90%       |
   | CENTRO DE COSTO    | empleado | 90%       |
   | AREA               | empleado | 90%       |
   | SUELDO BASE        | concepto | 50%       |
   | BONO PRODUCTIVIDAD | concepto | 50%       |
   | COLACION           | concepto | 50%       |
   | MOVILIZACION       | concepto | 50%       |
   | GRATIFICACION      | concepto | 50%       |
   | AFP                | concepto | 50%       |
   | SALUD              | concepto | 50%       |
   | IMPUESTO           | concepto | 50%       |
   | ANTICIPO           | concepto | 50%       |
   | LIQUIDO A PAGAR    | concepto | 50%       |
   ```

4. **Modificar si es necesario**:
   - Si alguna clasificación está mal, cambiarla en el dropdown
   - Opciones: "Dato de Empleado", "Concepto de Nómina", "Ignorar"

5. **Click "Guardar Clasificación"**

6. **Verificar confirmación**:
   ```
   ✅ Clasificación guardada
   Estado: "Listo para procesar"
   ```

**⏱️ Tiempo esperado**: 1-2 minutos (manual)

**🎯 Lo que pasa en backend**:
- Se guarda `header_json` con clasificación manual
- Estado cambia: `analizado` → `clasificado`
- Se habilita botón "Procesar Libro"

---

### PASO 5: Procesar Libro Completo

1. **Verificar estado**: Botón "Procesar Libro" debe estar habilitado

2. **Click "Procesar Libro"**

3. **Ver confirmación**: Modal o notificación
   ```
   🚀 Procesamiento iniciado
   Task ID: abc-123-def-456
   ```

4. **Ver progreso**: 
   - Estado cambia a "Procesando..."
   - Spinner activo
   - Polling automático cada 2 segundos

5. **Esperar finalización**:
   - Primera fase: "Creando empleados..." (~15 segundos)
   - Segunda fase: "Guardando conceptos..." (~25 segundos)

6. **Verificar completado**:
   ```
   ✅ Libro procesado exitosamente
   Estado: "Procesado"
   ```

**⏱️ Tiempo esperado**: 35-45 segundos

**🎯 Lo que pasa en backend**:

**FASE 1 - Crear Empleados (Chord paralelo)**:
- Divide 5 empleados en chunks
- Crea/actualiza `EmpleadoCierre` (5 registros)
- Procesa en paralelo con Celery workers

**FASE 2 - Crear Conceptos (Chord paralelo)**:
- Por cada empleado, crea registros de conceptos
- Crea `RegistroConceptoEmpleado` (50 registros = 5 empleados × 10 conceptos)
- Procesa en paralelo con Celery workers

**Estado final**: `procesando` → `procesado`

---

## 🔍 Verificación en Base de Datos

Después de completar, verifica en BD:

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import LibroRemuneracionesUpload, EmpleadoCierre, RegistroConceptoEmpleado

# Verificar libro
libro = LibroRemuneracionesUpload.objects.filter(cierre_id=35).first()
print(f"📚 Libro ID: {libro.id}")
print(f"   Estado: {libro.estado}")
print(f"   Headers: {len(libro.header_json)} columnas")

# Verificar empleados
empleados = EmpleadoCierre.objects.filter(cierre_id=35)
print(f"\n👥 Empleados creados: {empleados.count()}")
for emp in empleados[:3]:
    print(f"   - {emp.rut}: {emp.nombre_completo} ({emp.cargo})")

# Verificar conceptos
conceptos = RegistroConceptoEmpleado.objects.filter(empleado__cierre_id=35)
print(f"\n💰 Conceptos creados: {conceptos.count()}")
print(f"   Esperado: {empleados.count()} empleados × 10 conceptos = {empleados.count() * 10}")

# Verificar algunos conceptos
for concepto in conceptos[:5]:
    print(f"   - {concepto.empleado.rut}: {concepto.concepto} = ${concepto.valor:,.0f}")

EOF
```

**Resultado esperado**:
```
📚 Libro ID: 79
   Estado: procesado
   Headers: 15 columnas

👥 Empleados creados: 5
   - 11111111-1: JUAN PEREZ GONZALEZ (ANALISTA)
   - 22222222-2: MARIA LOPEZ SILVA (ANALISTA)
   - 33333333-3: PEDRO RODRIGUEZ MARTINEZ (SENIOR)

💰 Conceptos creados: 50
   Esperado: 5 empleados × 10 conceptos = 50
   - 11111111-1: SUELDO BASE = $1,500,000
   - 11111111-1: BONO PRODUCTIVIDAD = $150,000
   - 11111111-1: COLACION = $50,000
   - 11111111-1: MOVILIZACION = $30,000
   - 11111111-1: GRATIFICACION = $100,000
```

---

## 📊 Monitoreo de Logs en Tiempo Real

### Terminal 1: Logs de Celery
```bash
docker compose logs celery_worker -f | grep -E "libro|empleado|concepto|Task.*succeeded|FAILED"
```

### Terminal 2: Logs de Django
```bash
docker compose logs django -f | grep -E "libro|Procesamiento|iniciado"
```

---

## ✅ Checklist de Validación

### PASO 1: Subida
- [ ] Archivo se sube sin errores
- [ ] Se crea registro `LibroRemuneracionesUpload`
- [ ] Se crea registro `UploadLogNomina`
- [ ] Estado inicial: `pendiente`

### PASO 2: Análisis
- [ ] Task Celery se ejecuta automáticamente
- [ ] Headers se extraen correctamente (15 columnas)
- [ ] Clasificación automática funciona
- [ ] Estado cambia a `analizado`
- [ ] Modal se abre automáticamente

### PASO 3: Clasificación
- [ ] Modal muestra todos los headers
- [ ] Se pueden modificar clasificaciones
- [ ] Al guardar, estado cambia a `clasificado`
- [ ] `header_json` se actualiza con clasificación manual
- [ ] Botón "Procesar" se habilita

### PASO 4: Procesamiento
- [ ] Botón "Procesar" inicia el proceso
- [ ] Task Celery Chain se crea correctamente
- [ ] FASE 1: Se crean 5 `EmpleadoCierre`
- [ ] FASE 2: Se crean 50 `RegistroConceptoEmpleado`
- [ ] Estado final: `procesado`
- [ ] No hay errores en logs

---

## ❌ Posibles Errores y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "Archivo demasiado grande" | Excel > 10MB | Reducir tamaño o aumentar límite |
| "No se encontró columna RUT" | Clasificación incorrecta | Reclasificar headers manualmente |
| "Error al procesar chunk" | Worker sobrecargado | Reiniciar celery workers |
| "Task timeout" | Archivo muy grande | Aumentar timeout o reducir chunk size |
| Modal no se abre | Estado no cambió a `analizado` | Verificar logs de Celery task |

---

## 🎯 Funciones que se Están Probando

### ✅ Funciones Refactorizadas (deberían funcionar)
- `analizar_headers_libro_remuneraciones_con_logging`
- `clasificar_headers_libro_remuneraciones_con_logging`
- `actualizar_empleados_desde_libro_optimizado`
- `procesar_chunk_empleados_task`
- `consolidar_empleados_task`
- `guardar_registros_nomina_optimizado`
- `procesar_chunk_registros_task`
- `consolidar_registros_task`

### ⚠️ Stubs Potenciales (podrían fallar)
- `build_informe_libro` (si se llama)
- Funciones de validación no refactorizadas

---

## 📝 Registro de Resultados

**Al completar la prueba, documenta:**

```markdown
### Resultado PASO 1: Subida
- ✅/❌ Estado: 
- Tiempo: 
- Libro ID: 
- Observaciones:

### Resultado PASO 2: Análisis
- ✅/❌ Estado:
- Tiempo:
- Headers encontrados:
- Observaciones:

### Resultado PASO 3: Clasificación
- ✅/❌ Estado:
- Tiempo:
- Headers empleado:
- Headers concepto:
- Observaciones:

### Resultado PASO 4: Procesamiento
- ✅/❌ Estado:
- Tiempo total:
- Empleados creados:
- Conceptos creados:
- Errores encontrados:
- Stubs llamados:
- Observaciones:
```

---

## 🚀 ¡Listo para Probar!

**URL**: http://172.17.11.18:5174/nomina/cierre/35

**Archivo**: `/tmp/libro_remuneraciones_smoke_test.xlsx`

**Sigue los pasos y documenta los resultados en `PLAN_PRUEBA_SMOKE_TEST.md`**

---

**Creado**: 24 octubre 2025  
**Para**: Smoke Test de tasks refactorizadas
