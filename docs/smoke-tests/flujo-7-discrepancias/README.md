# Flujo 7: Verificación de Discrepancias

## 📋 Resumen Ejecutivo

**Propósito**: Detectar diferencias entre los datos consolidados de diferentes fuentes (Libro de Remuneraciones, Movimientos, Archivos Analista, Novedades) para garantizar la consistencia de los datos antes de finalizar el cierre.

**Trigger**: Usuario hace clic en botón "Verificar Datos" o "Generar Discrepancias" en el cierre

**Arquitectura**: Sistema independiente con task refactorizada + logging dual

**Importancia**: ⚠️ **CRÍTICO** - Este flujo valida que todos los datos sean consistentes antes de procesar la nómina final

---

## 🎯 Objetivo del Flujo

El sistema de verificación de discrepancias compara automáticamente:

1. **Libro de Remuneraciones vs Novedades**:
   - Empleados que solo existen en uno de los dos
   - Diferencias en datos personales (nombre, apellido)
   - Diferencias en sueldo base
   - Diferencias en montos de conceptos
   - Conceptos que solo existen en una fuente

2. **Movimientos del Mes vs Archivos Analista**:
   - Ingresos registrados en movimientos vs archivo de ingresos
   - Finiquitos registrados en movimientos vs archivo de finiquitos
   - Inconsistencias en fechas o datos

---

## 🏗️ Arquitectura del Sistema

### Modelos Involucrados

```python
# Modelo principal
DiscrepanciaCierre:
  - cierre: ForeignKey(CierreNomina)
  - tipo_discrepancia: CharField (choices de TipoDiscrepancia)
  - rut_empleado: CharField
  - descripcion: TextField
  - valor_libro, valor_novedades: CharField (valores en conflicto)
  - valor_movimientos, valor_analista: CharField (valores en conflicto)
  - concepto_afectado: CharField (opcional)
  - fecha_detectada: DateTimeField
  - historial_verificacion: FK a HistorialVerificacionCierre

# Historial de ejecuciones
HistorialVerificacionCierre:
  - cierre: ForeignKey(CierreNomina)
  - numero_intento: PositiveIntegerField (1, 2, 3...)
  - usuario_ejecutor: ForeignKey(User)
  - fecha_ejecucion, fecha_finalizacion: DateTimeField
  - total_discrepancias_encontradas: PositiveIntegerField
  - discrepancias_libro_vs_novedades: PositiveIntegerField
  - discrepancias_movimientos_vs_analista: PositiveIntegerField
  - estado_verificacion: CharField (iniciado/completado/error)
  - task_id: CharField (ID de Celery)
```

### Tipos de Discrepancias

```python
TipoDiscrepancia.choices = [
    # Libro vs Novedades
    ('empleado_solo_libro', 'Empleado solo en Libro'),
    ('empleado_solo_novedades', 'Empleado solo en Novedades'),
    ('diff_datos_personales', 'Diferencia en Datos Personales'),
    ('diff_sueldo_base', 'Diferencia en Sueldo Base'),
    ('diff_concepto_monto', 'Diferencia en Monto de Concepto'),
    ('concepto_solo_libro', 'Concepto solo en Libro'),
    ('concepto_solo_novedades', 'Concepto solo en Novedades'),
    
    # Movimientos vs Analista
    ('ingreso_sin_archivo', 'Ingreso en Movimientos sin Archivo'),
    ('archivo_ingreso_sin_movimiento', 'Archivo Ingreso sin Movimiento'),
    ('finiquito_sin_archivo', 'Finiquito en Movimientos sin Archivo'),
    ('archivo_finiquito_sin_movimiento', 'Archivo Finiquito sin Movimiento'),
    ('diff_fecha_ingreso', 'Diferencia en Fecha de Ingreso'),
    ('diff_fecha_finiquito', 'Diferencia en Fecha de Finiquito'),
]
```

---

## 🔄 Flujo de Ejecución

### Secuencia Completa

```
1. Usuario → Frontend
   └─ Clic en botón "Verificar Datos" o "Generar Discrepancias"

2. Frontend → Backend API
   └─ POST /nomina/discrepancias/generar/{cierre_id}/
   
3. ViewSet: DiscrepanciaCierreViewSet.generar_discrepancias()
   ├─ Valida que el cierre existe
   ├─ Verifica estado del cierre (debe estar en estado adecuado)
   ├─ Obtiene usuario ejecutor
   └─ Dispara tarea Celery: generar_discrepancias_cierre_con_logging.delay()

4. Task Celery: generar_discrepancias_cierre_con_logging
   ├─ 📊 Log inicio (TarjetaActivityLogNomina + ActivityEvent)
   ├─ Cambia estado cierre a 'verificacion_datos'
   ├─ Valida que existan archivos necesarios
   ├─ Ejecuta: generar_todas_discrepancias(cierre)
   │   ├─ Limpia discrepancias previas del intento actual
   │   ├─ Compara Libro vs Novedades (si existe archivo novedades)
   │   │   ├─ Detecta empleados faltantes en cada fuente
   │   │   ├─ Compara datos personales (nombre, apellido)
   │   │   ├─ Compara sueldos base
   │   │   └─ Compara montos de conceptos
   │   └─ Compara Movimientos vs Archivos Analista
   │       ├─ Verifica ingresos
   │       ├─ Verifica finiquitos
   │       └─ Detecta inconsistencias en fechas
   ├─ Cuenta total de discrepancias
   ├─ Actualiza estado del cierre:
   │   ├─ Si 0 discrepancias → 'verificado_sin_discrepancias'
   │   └─ Si >0 discrepancias → 'discrepancias_detectadas'
   ├─ Crea/actualiza HistorialVerificacionCierre
   └─ 📊 Log finalización (resultado, total discrepancias, tiempo)

5. Frontend recibe task_id
   └─ Hace polling a /task-status/{task_id}/ para ver progreso

6. Cuando tarea completa
   └─ Frontend muestra resultado:
       ├─ Si 0 discrepancias: ✅ "Datos verificados correctamente"
       └─ Si >0 discrepancias: ⚠️ "Se detectaron X discrepancias"
```

---

## 📡 Endpoints API

### 1. Generar Discrepancias
```http
POST /nomina/discrepancias/generar/{cierre_id}/
Authorization: Bearer {token}

Response 202 (Accepted):
{
  "message": "Verificación de datos iniciada",
  "task_id": "abc-123-def-456",
  "cierre_id": 35,
  "usuario_ejecutor": "analista.nomina@bdo.cl"
}
```

### 2. Obtener Estado de Discrepancias
```http
GET /nomina/discrepancias/estado/{cierre_id}/
Authorization: Bearer {token}

Response 200:
{
  "cierre_id": 35,
  "estado_cierre": "discrepancias_detectadas",
  "tiene_discrepancias": true,
  "total_discrepancias": 12,
  "discrepancias_por_grupo": {
    "libro_vs_novedades": 8,
    "movimientos_vs_analista": 4
  },
  "empleados_afectados": 5,
  "fecha_ultima_verificacion": "2025-10-28T10:30:00Z"
}
```

### 3. Obtener Resumen Detallado
```http
GET /nomina/discrepancias/resumen/{cierre_id}/
Authorization: Bearer {token}

Response 200:
{
  "total_discrepancias": 12,
  "discrepancias_por_tipo": {
    "empleado_solo_libro": 2,
    "diff_sueldo_base": 3,
    "diff_concepto_monto": 5,
    "ingreso_sin_archivo": 2
  },
  "empleados_afectados": ["12345678-9", "98765432-1", ...],
  ...
}
```

### 4. Listar Discrepancias (con filtros)
```http
GET /nomina/discrepancias/?cierre=35&tipo=diff_sueldo_base
Authorization: Bearer {token}

Response 200:
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "tipo_discrepancia": "diff_sueldo_base",
      "rut_empleado": "12345678-9",
      "descripcion": "Diferencia en Sueldo Base",
      "valor_libro": "1500000",
      "valor_novedades": "1600000",
      "concepto_afectado": "Sueldo Base",
      "fecha_detectada": "2025-10-28T10:30:00Z"
    },
    ...
  ]
}
```

---

## ⚙️ Lógica de Negocio Detallada

### Estados Permitidos para Generar Discrepancias

```python
estados_permitidos = [
    'archivos_completos',      # Todos los archivos subidos
    'verificacion_datos',      # Ya en proceso de verificación
    'con_discrepancias',       # Re-verificar después de correcciones
    'datos_consolidados',      # Datos consolidados, verificar antes de avanzar
    'discrepancias_detectadas' # Re-verificar si se hicieron cambios
]
```

### Algoritmo de Comparación

#### 1. Libro vs Novedades (si existe archivo de novedades)

```python
# Paso 1: Detectar empleados faltantes
empleados_libro = EmpleadoCierre.objects.filter(cierre=cierre)
empleados_novedades = EmpleadoCierreNovedades.objects.filter(archivo__cierre=cierre)

# Empleados solo en Libro
for emp in empleados_libro:
    if not existe_en_novedades(emp.rut):
        crear_discrepancia(tipo='empleado_solo_libro', rut=emp.rut)

# Empleados solo en Novedades
for emp in empleados_novedades:
    if not existe_en_libro(emp.rut):
        crear_discrepancia(tipo='empleado_solo_novedades', rut=emp.rut)

# Paso 2: Comparar datos personales
for rut in empleados_comunes:
    emp_libro = get_empleado_libro(rut)
    emp_novedades = get_empleado_novedades(rut)
    
    if emp_libro.nombre != emp_novedades.nombre:
        crear_discrepancia(
            tipo='diff_datos_personales',
            rut=rut,
            valor_libro=emp_libro.nombre,
            valor_novedades=emp_novedades.nombre
        )

# Paso 3: Comparar sueldos base
for rut in empleados_comunes:
    sueldo_libro = get_sueldo_base_libro(rut)
    sueldo_novedades = get_sueldo_base_novedades(rut)
    
    if sueldo_libro != sueldo_novedades:
        crear_discrepancia(
            tipo='diff_sueldo_base',
            rut=rut,
            valor_libro=str(sueldo_libro),
            valor_novedades=str(sueldo_novedades)
        )

# Paso 4: Comparar conceptos y montos
for rut in empleados_comunes:
    conceptos_libro = get_conceptos_libro(rut)
    conceptos_novedades = get_conceptos_novedades(rut)
    
    for concepto in todos_los_conceptos:
        monto_libro = conceptos_libro.get(concepto, 0)
        monto_novedades = conceptos_novedades.get(concepto, 0)
        
        if monto_libro != monto_novedades:
            crear_discrepancia(
                tipo='diff_concepto_monto',
                rut=rut,
                concepto_afectado=concepto,
                valor_libro=str(monto_libro),
                valor_novedades=str(monto_novedades)
            )
```

#### 2. Movimientos vs Archivos Analista

```python
# Comparar Ingresos
movimientos_ingreso = MovimientoMes.objects.filter(
    cierre=cierre,
    tipo_movimiento='ingreso'
)
archivos_ingreso = AnalistaIngreso.objects.filter(
    archivo_origen__cierre=cierre
)

for mov in movimientos_ingreso:
    if not existe_archivo_ingreso(mov.rut):
        crear_discrepancia(
            tipo='ingreso_sin_archivo',
            rut=mov.rut,
            valor_movimientos=mov.fecha_movimiento
        )

for archivo in archivos_ingreso:
    if not existe_movimiento_ingreso(archivo.rut):
        crear_discrepancia(
            tipo='archivo_ingreso_sin_movimiento',
            rut=archivo.rut,
            valor_analista=archivo.fecha_ingreso
        )

# Comparar Finiquitos (similar)
# ... lógica análoga para finiquitos ...
```

### Actualización de Estado del Cierre

```python
if total_discrepancias == 0:
    cierre.estado = 'verificado_sin_discrepancias'
    resultado_mensaje = '✅ Sin discrepancias detectadas'
else:
    cierre.estado = 'discrepancias_detectadas'
    resultado_mensaje = f'⚠️ {total_discrepancias} discrepancias detectadas'

cierre.save()
```

---

## 📊 Sistema de Logging Dual

### 1. TarjetaActivityLogNomina

```python
# Inicio
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta='revision',  # Tarjeta de revisión/verificación
    accion='process_start',
    descripcion='Iniciando verificación de datos y generación de discrepancias',
    usuario=usuario,
    detalles={
        'cierre_id': cierre_id,
        'cliente_nombre': cliente.nombre,
        'periodo': cierre.periodo,
        'estado_inicial': cierre.estado
    },
    resultado='info'
)

# Finalización
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta='revision',
    accion='process_complete' if total == 0 else 'validation_error',
    descripcion=f'Verificación completada: {total} discrepancias',
    usuario=usuario,
    detalles={
        'total_discrepancias': total,
        'libro_vs_novedades': count_libro_novedades,
        'movimientos_vs_analista': count_movimientos_analista,
        'estado_final': cierre.estado,
        'tiempo_ejecucion': f'{duracion}s'
    },
    resultado='exito' if total == 0 else 'advertencia'
)
```

### 2. ActivityEvent

```python
# Inicio
ActivityEvent.log(
    user=usuario,
    cliente=cliente,
    cierre=cierre,
    event_type='verification',
    action='verificacion_iniciada',
    resource_type='discrepancias',
    resource_id=str(cierre_id),
    details={
        'cierre_id': cierre_id,
        'estado_inicial': cierre.estado,
        'task_id': task_id
    }
)

# Finalización
ActivityEvent.log(
    user=usuario,
    cliente=cliente,
    cierre=cierre,
    event_type='verification',
    action='verificacion_completada_sin_discrepancias' if total == 0 
           else 'verificacion_completada_con_discrepancias',
    resource_type='discrepancias',
    resource_id=str(cierre_id),
    details={
        'total_discrepancias': total,
        'discrepancias_por_tipo': resumen_tipos,
        'estado_final': cierre.estado,
        'tiempo_ejecucion': duracion
    }
)
```

---

## ✅ Criterios de Éxito

### Verificaciones Esperadas

1. ✅ **Tarea se ejecuta sin errores**
   - Task completa con estado SUCCESS
   - No excepciones en logs

2. ✅ **Logging dual funciona**
   - Mínimo 2 eventos en TarjetaActivityLogNomina
   - Mínimo 2 eventos en ActivityEvent
   - Usuario ejecutor registrado correctamente

3. ✅ **Discrepancias se detectan correctamente**
   - Total de discrepancias >= 0
   - Tipos de discrepancias correctos
   - Valores en conflicto registrados

4. ✅ **Estado del cierre se actualiza**
   - Si 0 discrepancias: estado = 'verificado_sin_discrepancias'
   - Si >0 discrepancias: estado = 'discrepancias_detectadas'

5. ✅ **HistorialVerificacionCierre se crea**
   - Registro con numero_intento correcto
   - Usuario ejecutor registrado
   - Total de discrepancias guardado
   - Tiempo de ejecución calculado

6. ✅ **Discrepancias se pueden consultar**
   - GET /discrepancias/ con filtros funciona
   - Resumen estadístico correcto
   - Estado de discrepancias accesible

---

## 🎯 Escenarios de Prueba

### Escenario 1: Cierre Sin Discrepancias (Ideal)
- Todos los datos coinciden entre fuentes
- Resultado: 0 discrepancias
- Estado final: 'verificado_sin_discrepancias'

### Escenario 2: Discrepancias en Sueldos
- Diferencias en montos de sueldos base
- Resultado: N discrepancias tipo 'diff_sueldo_base'
- Estado final: 'discrepancias_detectadas'

### Escenario 3: Empleados Faltantes
- Empleados en Libro pero no en Novedades
- Resultado: N discrepancias tipo 'empleado_solo_libro'
- Estado final: 'discrepancias_detectadas'

### Escenario 4: Sin Archivo de Novedades
- Solo compara Movimientos vs Archivos Analista
- Resultado: Discrepancias solo de ese grupo
- Estado final: depende del resultado

---

## 📂 Archivos del Sistema

```
backend/nomina/
├── views_discrepancias.py           # ViewSet principal
├── tasks_refactored/
│   └── discrepancias.py             # Task con logging
├── utils/
│   └── GenerarDiscrepancias.py      # Lógica de comparación
├── models.py                         # DiscrepanciaCierre, HistorialVerificacionCierre
└── serializers.py                    # Serializers para API
```

---

## 🔍 Notas Importantes

1. **Es sistema informativo**: Las discrepancias solo se registran, no bloquean el flujo
2. **Puede ejecutarse múltiples veces**: Cada ejecución se guarda en el historial
3. **Limpia discrepancias previas**: Antes de generar nuevas, limpia las del intento actual
4. **No modifica datos**: Solo lee y compara, no corrige automáticamente

---

**Estado**: 🟡 PENDIENTE DE VALIDACIÓN  
**Prioridad**: Alta  
**Complejidad**: Media-Alta  
**Dependencias**: Flujos 1-6 completados
