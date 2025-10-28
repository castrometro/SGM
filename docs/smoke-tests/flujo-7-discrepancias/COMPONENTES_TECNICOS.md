# Flujo 7: Discrepancias - Componentes Técnicos

> **Referencia Rápida de Arquitectura**  
> Documento técnico detallando todos los componentes, endpoints y flujos del sistema de verificación de discrepancias.

---

## 📋 Índice

1. [Backend - Tasks Celery](#backend---tasks-celery)
2. [Backend - ViewSets](#backend---viewsets)
3. [Backend - API Endpoints](#backend---api-endpoints)
4. [Backend - Modelos](#backend---modelos)
5. [Backend - Utils](#backend---utils)
6. [Backend - Serializers](#backend---serializers)
7. [Frontend - Componentes React](#frontend---componentes-react)
8. [Frontend - API Client](#frontend---api-client)
9. [Flujo Técnico Completo](#flujo-técnico-completo)
10. [Logging Dual](#logging-dual)
11. [Resumen de Archivos](#resumen-de-archivos)

---

## 🔧 Backend - Tasks Celery

### 📍 Archivo: `backend/nomina/tasks_refactored/discrepancias.py`

### ✅ Tarea Principal

**`generar_discrepancias_cierre_con_logging()`**
- **Parámetros**: `(self, cierre_id, usuario_id=None)`
- **Queue**: `nomina_queue`
- **Función**: Genera y registra discrepancias en verificación
- **Returns**: 
  ```python
  {
    'cierre_id': int,
    'total_discrepancias': int,
    'estado_final': str,
    'discrepancias_por_tipo': dict,
    'empleados_afectados': list
  }
  ```

### 📦 Funciones Auxiliares

| Función | Propósito |
|---------|-----------|
| `get_sistema_user()` | Obtiene usuario sistema |
| `get_tarjeta_accion()` | Mapea acciones a ACCION_CHOICES |
| `log_discrepancias_start()` | Logging dual inicio |
| `log_discrepancias_complete()` | Logging dual finalización |
| `_verificar_archivos_listos_para_discrepancias()` | Valida archivos necesarios |

---

## 🎯 Backend - ViewSets

### 📍 Archivo: `backend/nomina/views_discrepancias.py`

### ✅ ViewSet Principal: `DiscrepanciaCierreViewSet`

**Configuración Base:**
- **Base Class**: `viewsets.ModelViewSet`
- **Modelo**: `DiscrepanciaCierre`
- **Serializer**: `DiscrepanciaCierreSerializer`
- **Permission**: `IsAuthenticated`

### 📋 Métodos Estándar (CRUD)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `list()` | `GET /discrepancias/` | Listar todas |
| `retrieve()` | `GET /discrepancias/{id}/` | Detalle de una |
| `create()` | `POST /discrepancias/` | Crear nueva |
| `update()` | `PUT /discrepancias/{id}/` | Actualizar |
| `destroy()` | `DELETE /discrepancias/{id}/` | Eliminar |
| `get_queryset()` | - | Filtros avanzados |

### 🎯 Custom Actions

#### 1. `generar_discrepancias()`
- **Endpoint**: `POST /discrepancias/generar/{cierre_id}/`
- **Función**: Ejecuta verificación con logging dual
- **Respuesta**: Task ID y datos del cierre

#### 2. `resumen_discrepancias()`
- **Endpoint**: `GET /discrepancias/resumen/{cierre_id}/`
- **Función**: Resumen estadístico detallado
- **Respuesta**: Totales, tipos, empleados afectados

#### 3. `estado_discrepancias()`
- **Endpoint**: `GET /discrepancias/estado/{cierre_id}/`
- **Función**: Estado actual con contadores
- **Respuesta**: Estado del cierre, total de discrepancias

### 🔍 Filtros Disponibles (Query Parameters)

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `cierre` | Integer | Filtrar por cierre | `?cierre=35` |
| `tipo` | String | Filtrar por tipo | `?tipo=diff_concepto_monto` |
| `rut` | String | Buscar por RUT (parcial) | `?rut=12345678` |
| `grupo` | String | Agrupar resultados | `?grupo=libro_vs_novedades` |

**Grupos válidos:**
- `libro_vs_novedades`
- `movimientos_vs_analista`

### ✅ ViewSet Secundario

**`CierreNominaDiscrepanciasViewSet`**
- Gestión de discrepancias desde el cierre
- Hereda funcionalidades del principal

---

## 📡 Backend - API Endpoints

### 📍 Base URL: `/api/nomina/`

### 🔹 1. Generar Discrepancias (Acción Principal)

**Endpoint**: `POST /discrepancias/generar/{cierre_id}/`

**Request:**
```http
POST /api/nomina/discrepancias/generar/35/
Authorization: Bearer {token}
Content-Type: application/json
```

**Response 202 (Accepted):**
```json
{
  "message": "Verificación de datos iniciada",
  "task_id": "abc-123-def-456",
  "cierre_id": 35,
  "usuario_ejecutor": "analista.nomina@bdo.cl"
}
```

### 🔹 2. Estado de Discrepancias

**Endpoint**: `GET /discrepancias/estado/{cierre_id}/`

**Response 200:**
```json
{
  "cierre_id": 35,
  "estado_cierre": "con_discrepancias",
  "tiene_discrepancias": true,
  "total_discrepancias": 25,
  "discrepancias_por_grupo": {
    "libro_vs_novedades": 16,
    "movimientos_vs_analista": 9
  },
  "empleados_afectados": 9,
  "fecha_ultima_verificacion": "2025-10-28T10:30:00Z"
}
```

### 🔹 3. Resumen Detallado

**Endpoint**: `GET /discrepancias/resumen/{cierre_id}/`

**Response 200:**
```json
{
  "total_discrepancias": 25,
  "discrepancias_por_tipo": {
    "diff_concepto_monto": 16,
    "ingreso_no_reportado": 3,
    "ausencia_no_reportada": 2,
    "empleado_solo_novedades": 2,
    "finiquito_no_reportado": 2
  },
  "empleados_afectados": ["12345678-9", "98765432-1", ...],
  "timestamp": "2025-10-28T10:30:00Z"
}
```

### 🔹 4. Listar Discrepancias (con Filtros)

**Endpoint**: `GET /discrepancias/?cierre=35&tipo=diff_sueldo_base&limit=10`

**Response 200:**
```json
{
  "count": 3,
  "next": "http://api/discrepancias/?cierre=35&page=2",
  "previous": null,
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
    }
  ]
}
```

### 🔹 5. Detalle de Discrepancia

**Endpoint**: `GET /discrepancias/{id}/`

**Response 200:**
```json
{
  "id": 1,
  "cierre": 35,
  "tipo_discrepancia": "diff_concepto_monto",
  "empleado_libro": {
    "id": 123,
    "rut": "12345678-9",
    "nombre": "Juan Pérez"
  },
  "empleado_novedades": {
    "id": 456,
    "rut": "12345678-9",
    "nombre": "Juan Pérez"
  },
  "rut_empleado": "12345678-9",
  "descripcion": "Diferencia en monto del concepto 'Bono Producción'",
  "valor_libro": "150000",
  "valor_novedades": "180000",
  "valor_movimientos": null,
  "valor_analista": null,
  "concepto_afectado": "Bono Producción",
  "fecha_detectada": "2025-10-28T10:30:00Z",
  "historial_verificacion": null
}
```

### 🔹 6. Task Status (Polling)

**Endpoint**: `GET /task-status/{task_id}/`

**Response 200 (In Progress):**
```json
{
  "task_id": "abc-123",
  "status": "PENDING",
  "progress": 50
}
```

**Response 200 (Success):**
```json
{
  "task_id": "abc-123",
  "status": "SUCCESS",
  "result": {
    "cierre_id": 35,
    "total_discrepancias": 25,
    "estado_final": "con_discrepancias",
    "discrepancias_por_tipo": {...},
    "empleados_afectados": [...]
  }
}
```

**Response 200 (Error):**
```json
{
  "task_id": "abc-123",
  "status": "FAILURE",
  "error": "Error message details"
}
```

---

## 🗄️ Backend - Modelos

### 📍 Archivo: `backend/nomina/models.py`

### ✅ Modelo Principal: `DiscrepanciaCierre`

**Campos:**

| Campo | Tipo | Descripción | Null |
|-------|------|-------------|------|
| `cierre` | ForeignKey | Referencia a CierreNomina | No |
| `tipo_discrepancia` | CharField | Tipo de discrepancia (choices) | No |
| `empleado_libro` | ForeignKey | Empleado en libro remuneraciones | Sí |
| `empleado_novedades` | ForeignKey | Empleado en novedades | Sí |
| `rut_empleado` | CharField(20) | RUT del empleado afectado | No |
| `descripcion` | TextField | Descripción detallada | No |
| `valor_libro` | CharField(100) | Valor en libro | Sí |
| `valor_novedades` | CharField(100) | Valor en novedades | Sí |
| `valor_movimientos` | CharField(100) | Valor en movimientos | Sí |
| `valor_analista` | CharField(100) | Valor en archivos analista | Sí |
| `concepto_afectado` | CharField(100) | Concepto en discrepancia | Sí |
| `fecha_detectada` | DateTimeField | Fecha de detección | Auto |
| `historial_verificacion` | ForeignKey | Referencia a historial | Sí |

### 📋 Tipos de Discrepancias (CHOICES)

**Categoría: Empleados**
- `empleado_solo_libro` - Empleado solo en Libro de Remuneraciones
- `empleado_solo_novedades` - Empleado solo en Novedades

**Categoría: Datos Personales**
- `diff_datos_personales` - Diferencia en datos personales
- `diff_sueldo_base` - Diferencia en sueldo base

**Categoría: Conceptos**
- `diff_concepto_monto` - Diferencia en monto de concepto
- `concepto_solo_libro` - Concepto solo en Libro
- `concepto_solo_novedades` - Concepto solo en Novedades

**Categoría: Movimientos vs Analista**
- `ingreso_no_reportado` - Ingreso no reportado en movimientos
- `archivo_ingreso_sin_movimiento` - Archivo de ingreso sin movimiento correspondiente
- `finiquito_no_reportado` - Finiquito no reportado en movimientos
- `archivo_finiquito_sin_movimiento` - Archivo de finiquito sin movimiento correspondiente
- `ausencia_no_reportada` - Ausencia no reportada en movimientos

**Categoría: Fechas**
- `diff_fecha_ingreso` - Diferencia en fecha de ingreso
- `diff_fecha_finiquito` - Diferencia en fecha de finiquito

### ⚠️ Modelo Opcional: `HistorialVerificacionCierre`

> **Nota**: Este modelo existe pero **NO está siendo usado actualmente** por el sistema.

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cierre` | ForeignKey | Referencia a CierreNomina |
| `numero_intento` | PositiveIntegerField | Número de intento de verificación |
| `usuario_ejecutor` | ForeignKey | Usuario que ejecutó |
| `fecha_ejecucion` | DateTimeField | Fecha de inicio |
| `fecha_finalizacion` | DateTimeField | Fecha de finalización |
| `tiempo_ejecucion` | PositiveIntegerField | Tiempo en segundos |
| `total_discrepancias_encontradas` | PositiveIntegerField | Total |
| `discrepancias_libro_vs_novedades` | PositiveIntegerField | Subtotal |
| `discrepancias_movimientos_vs_analista` | PositiveIntegerField | Subtotal |
| `estado_verificacion` | CharField | Estado (choices) |
| `task_id` | CharField | ID de tarea Celery |
| `observaciones` | TextField | Notas adicionales |
| `archivos_analizados` | JSONField | Detalle de archivos |

**Estados de Verificación (CHOICES):**
- `en_proceso` - Verificación en proceso
- `completada` - Verificación completada exitosamente
- `completada_con_discrepancias` - Completada con discrepancias detectadas
- `fallida` - Verificación fallida por error

---

## 🔧 Backend - Utils

### 📍 Archivo: `backend/nomina/utils/GenerarDiscrepancias.py`

### 📦 Función Principal

**`generar_todas_discrepancias(cierre)`**

**Propósito**: Ejecuta todas las comparaciones y detecta discrepancias

**Proceso:**
1. Llama a `comparar_libro_vs_novedades(cierre)`
2. Llama a `comparar_movimientos_vs_analista(cierre)`
3. Consolida resultados

**Returns:**
```python
{
  'total_discrepancias': int,
  'discrepancias_por_tipo': {
    'diff_concepto_monto': int,
    'ingreso_no_reportado': int,
    ...
  },
  'discrepancias_libro_vs_novedades': int,
  'discrepancias_movimientos_vs_analista': int
}
```

### 📦 Funciones de Comparación

#### 1. `comparar_libro_vs_novedades(cierre)`

**Detecta:**
- ✅ Empleados que están solo en Libro
- ✅ Empleados que están solo en Novedades
- ✅ Diferencias en datos personales (nombre, apellidos)
- ✅ Diferencias en sueldo base
- ✅ Diferencias en montos de conceptos

**Lógica:**
```python
# 1. Obtener empleados de ambas fuentes
empleados_libro = EmpleadoCierre.objects.filter(cierre=cierre)
empleados_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre)

# 2. Comparar conjuntos
ruts_libro = set(empleados_libro.values_list('rut', flat=True))
ruts_novedades = set(empleados_novedades.values_list('rut', flat=True))

# 3. Detectar diferencias
solo_libro = ruts_libro - ruts_novedades
solo_novedades = ruts_novedades - ruts_libro

# 4. Para empleados comunes, comparar conceptos
for rut in ruts_libro & ruts_novedades:
    # Comparar conceptos y montos
    ...
```

#### 2. `comparar_movimientos_vs_analista(cierre)`

**Detecta:**
- ✅ Ingresos en archivos analista sin movimiento correspondiente
- ✅ Finiquitos en archivos analista sin movimiento correspondiente
- ✅ Ausencias en archivos analista sin movimiento correspondiente
- ✅ Movimientos sin archivo analista correspondiente
- ✅ Diferencias en fechas

**Lógica:**
```python
# 1. Obtener movimientos del mes
movimientos = MovimientoMes.objects.filter(cierre=cierre)

# 2. Obtener archivos de analista
ingresos = ArchivoIngresoAnalista.objects.filter(cierre=cierre)
finiquitos = ArchivoFiniquitoAnalista.objects.filter(cierre=cierre)
ausencias = ArchivoAusenciaAnalista.objects.filter(cierre=cierre)

# 3. Comparar cada tipo
for ingreso in ingresos:
    mov = movimientos.filter(
        rut=ingreso.rut,
        tipo_movimiento='ingreso'
    ).first()
    
    if not mov:
        # Crear discrepancia: ingreso_no_reportado
        ...
```

#### 3. `obtener_resumen_discrepancias(cierre)`

**Propósito**: Genera estadísticas y resúmenes de discrepancias existentes

**Returns:**
```python
{
  'total': int,
  'por_tipo': dict,
  'por_grupo': dict,
  'empleados_afectados': list,
  'conceptos_afectados': list
}
```

---

## 📊 Backend - Serializers

### 📍 Archivo: `backend/nomina/serializers.py`

### ✅ `DiscrepanciaCierreSerializer`

**Propósito**: Serializar modelo DiscrepanciaCierre para API

**Campos Principales:**
```python
class DiscrepanciaCierreSerializer(serializers.ModelSerializer):
    empleado_libro_data = EmpleadoCierreSerializer(
        source='empleado_libro', 
        read_only=True
    )
    empleado_novedades_data = EmpleadoCierreNovedadesSerializer(
        source='empleado_novedades', 
        read_only=True
    )
    
    class Meta:
        model = DiscrepanciaCierre
        fields = '__all__'
```

### ✅ `ResumenDiscrepanciasSerializer`

**Propósito**: Serializar resúmenes estadísticos

**Estructura:**
```python
class ResumenDiscrepanciasSerializer(serializers.Serializer):
    total_discrepancias = serializers.IntegerField()
    discrepancias_por_tipo = serializers.DictField()
    discrepancias_por_grupo = serializers.DictField()
    empleados_afectados = serializers.ListField()
    conceptos_afectados = serializers.ListField()
    fecha_ultima_verificacion = serializers.DateTimeField()
```

---

## ⚛️ Frontend - Componentes React

### 📍 Directorio: `src/components/TarjetasCierreNomina/`

### ✅ Componente Principal: `VerificadorDatosSection.jsx`

**Props:**
```javascript
{
  cierre: Object,                    // Objeto cierre completo
  disabled: Boolean,                 // Si está bloqueado
  onCierreActualizado: Function,     // Callback actualización
  onEstadoChange: Function,          // Callback cambio estado
  deberiaDetenerPolling: Boolean,    // Control polling
  expandido: Boolean,                // Estado acordeón
  onToggleExpansion: Function        // Toggle acordeón
}
```

**Funcionalidades:**
- 🎨 Acordeón expandible/colapsable
- 🔒 Lock visual cuando `disabled`
- 🎨 Color coding por estado:
  - 🟢 Verde: Sin discrepancias
  - 🔴 Rojo: Con discrepancias
  - 🟡 Amarillo: Verificando
  - ⚫ Gris: Pendiente
- 📊 Contador de discrepancias en header
- 🔄 Polling automático durante verificación
- ⏳ Loader animado durante proceso

**Estados Manejados:**
```javascript
const [estadoDiscrepancias, setEstadoDiscrepancias] = useState(null);

// Estructura de estadoDiscrepancias:
{
  total_discrepancias: number,
  requiere_correccion: boolean,
  verificacion_completada: boolean,
  empleados_afectados: number,
  discrepancias_por_tipo: {...}
}
```

### 📦 Subcomponente 1: `VerificadorDatos/VerificacionControl.jsx`

**Propósito**: Controla el inicio de verificación y polling de estado

**Funcionalidades:**
- 🔘 Botón "Verificar Datos"
- 🔄 Polling automático de task status
- 📊 Indicadores de progreso
- ⚠️ Manejo de estados (verificando, completado, error)
- 🔔 Notificaciones de resultado

**Estados:**
```javascript
const [verificando, setVerificando] = useState(false);
const [taskId, setTaskId] = useState(null);
const [progreso, setProgreso] = useState(0);
const [error, setError] = useState(null);
```

**Proceso:**
```javascript
// 1. Usuario click "Verificar"
const handleVerificar = async () => {
  const response = await generarDiscrepancias(cierre.id);
  setTaskId(response.task_id);
  setVerificando(true);
  iniciarPolling(response.task_id);
};

// 2. Polling cada 2 segundos
const iniciarPolling = (taskId) => {
  const interval = setInterval(async () => {
    const status = await getTaskStatus(taskId);
    
    if (status.status === 'SUCCESS') {
      clearInterval(interval);
      setVerificando(false);
      onEstadoDiscrepanciasChange(status.result);
    } else if (status.status === 'FAILURE') {
      clearInterval(interval);
      setError(status.error);
    }
  }, 2000);
};
```

### 📦 Subcomponente 2: `VerificadorDatos/DiscrepanciasViewer.jsx`

**Propósito**: Visualizar las discrepancias detectadas

**Props:**
```javascript
{
  cierreId: number,
  estadoDiscrepancias: object,
  visible: boolean
}
```

**Funcionalidades:**
- 📋 Lista paginada de discrepancias
- 🔍 Filtros por tipo y grupo
- 🔎 Búsqueda por RUT
- 📊 Vista detallada de cada discrepancia
- 📈 Resumen estadístico
- 🎨 Color coding por tipo de discrepancia

**Estructura de Vista:**
```
┌─────────────────────────────────────┐
│  Resumen: 25 discrepancias          │
│  ├─ Libro vs Novedades: 16          │
│  └─ Movimientos vs Analista: 9      │
├─────────────────────────────────────┤
│  Filtros: [Tipo▼] [Grupo▼] [RUT🔍] │
├─────────────────────────────────────┤
│  📋 Lista de Discrepancias          │
│  ┌───────────────────────────────┐  │
│  │ 🔴 Diferencia Sueldo Base     │  │
│  │ RUT: 12345678-9               │  │
│  │ Libro: $1,500,000             │  │
│  │ Novedades: $1,600,000         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 🟠 Ingreso No Reportado       │  │
│  │ RUT: 98765432-1               │  │
│  │ ...                           │  │
└─────────────────────────────────────┘
```

---

## 🔌 Frontend - API Client

### 📍 Archivo: `src/api/nominaApi.js`

### 📦 Funciones API

#### 1. `generarDiscrepancias(cierreId)`

```javascript
export const generarDiscrepancias = async (cierreId) => {
  const response = await api.post(
    `/nomina/discrepancias/generar/${cierreId}/`
  );
  return response.data;
};
```

**Returns:**
```javascript
{
  task_id: string,
  cierre_id: number,
  usuario_ejecutor: string
}
```

#### 2. `getEstadoDiscrepancias(cierreId)`

```javascript
export const getEstadoDiscrepancias = async (cierreId) => {
  const response = await api.get(
    `/nomina/discrepancias/estado/${cierreId}/`
  );
  return response.data;
};
```

**Returns:**
```javascript
{
  total_discrepancias: number,
  empleados_afectados: number,
  tiene_discrepancias: boolean,
  discrepancias_por_grupo: {...}
}
```

#### 3. `getResumenDiscrepancias(cierreId)`

```javascript
export const getResumenDiscrepancias = async (cierreId) => {
  const response = await api.get(
    `/nomina/discrepancias/resumen/${cierreId}/`
  );
  return response.data;
};
```

**Returns:**
```javascript
{
  discrepancias_por_tipo: {...},
  estadisticas: {...}
}
```

#### 4. `listarDiscrepancias(cierreId, filtros = {})`

```javascript
export const listarDiscrepancias = async (cierreId, filtros = {}) => {
  const params = new URLSearchParams({
    cierre: cierreId,
    ...filtros
  });
  
  const response = await api.get(
    `/nomina/discrepancias/?${params.toString()}`
  );
  return response.data;
};
```

**Parámetros de filtros:**
```javascript
{
  tipo: string,           // 'diff_concepto_monto', etc.
  grupo: string,          // 'libro_vs_novedades', etc.
  rut: string,            // Búsqueda parcial
  limit: number,          // Paginación
  offset: number          // Paginación
}
```

#### 5. `getTaskStatus(taskId)`

```javascript
export const getTaskStatus = async (taskId) => {
  const response = await api.get(`/task-status/${taskId}/`);
  return response.data;
};
```

**Returns:**
```javascript
{
  task_id: string,
  status: 'PENDING' | 'SUCCESS' | 'FAILURE',
  result: object,         // Cuando SUCCESS
  error: string,          // Cuando FAILURE
  progress: number        // 0-100
}
```

---

## 🔄 Flujo Técnico Completo

### Secuencia de Ejecución

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 1: Usuario Inicia Verificación                   │
│  ─────────────────────────────────────────────         │
│                                                         │
│  Frontend: VerificadorDatosSection                     │
│       ↓                                                 │
│  Usuario click "Verificar Datos"                       │
│       ↓                                                 │
│  VerificacionControl.handleVerificar()                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 2: Llamada a API                                 │
│  ─────────────────────────                             │
│                                                         │
│  POST /api/nomina/discrepancias/generar/{cierre_id}/   │
│  Authorization: Bearer {token}                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 3: Backend ViewSet                               │
│  ──────────────────────                                │
│                                                         │
│  DiscrepanciaCierreViewSet.generar_discrepancias()     │
│       ↓                                                 │
│  1. Valida estado del cierre                           │
│  2. Valida archivos necesarios                         │
│  3. Dispara task Celery                                │
│       ↓                                                 │
│  Returns: {task_id, cierre_id, usuario}                │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 4: Celery Task (Background)                      │
│  ────────────────────────────────                      │
│                                                         │
│  generar_discrepancias_cierre_con_logging.delay()      │
│       ↓                                                 │
│  1. Log inicio (dual logging)                          │
│  2. Cambia estado: 'verificacion_datos'                │
│  3. Ejecuta: generar_todas_discrepancias(cierre)       │
│       ↓                                                 │
│       ├─ comparar_libro_vs_novedades()                 │
│       │   ├─ Detecta empleados faltantes               │
│       │   ├─ Compara datos personales                  │
│       │   ├─ Compara sueldos base                      │
│       │   └─ Compara montos conceptos                  │
│       │                                                 │
│       └─ comparar_movimientos_vs_analista()            │
│           ├─ Verifica ingresos                         │
│           ├─ Verifica finiquitos                       │
│           └─ Detecta ausencias                         │
│       ↓                                                 │
│  4. Actualiza estado cierre según resultado:           │
│     • 0 discrepancias → 'verificado_sin_discrepancias' │
│     • >0 discrepancias → 'con_discrepancias'           │
│  5. Log finalización (dual logging)                    │
│       ↓                                                 │
│  Returns: {total, tipos, empleados, ...}               │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 5: Frontend Polling                              │
│  ────────────────────────                              │
│                                                         │
│  GET /api/task-status/{task_id}/                       │
│  Cada 2 segundos hasta completar                       │
│       ↓                                                 │
│  Actualiza UI con progreso                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  PASO 6: Cuando Completa                               │
│  ──────────────────────                                │
│                                                         │
│  1. GET /api/discrepancias/estado/{cierre_id}/         │
│     → Obtiene totales y estado                         │
│                                                         │
│  2. GET /api/discrepancias/?cierre={id}                │
│     → Obtiene lista de discrepancias                   │
│                                                         │
│  3. DiscrepanciasViewer muestra resultados             │
│     ├─ Resumen estadístico                             │
│     ├─ Lista paginada                                  │
│     └─ Detalles de cada discrepancia                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Tiempos Estimados

| Fase | Tiempo Estimado |
|------|-----------------|
| Validación inicial | < 1 segundo |
| Comparación Libro vs Novedades | 0.5 - 1.5 segundos |
| Comparación Movimientos vs Analista | 0.3 - 0.8 segundos |
| Logging y actualización estado | < 0.5 segundos |
| **TOTAL** | **< 2 segundos** |

---

## 📝 Logging Dual

El sistema utiliza **dos sistemas de logging paralelos** para máxima trazabilidad:

### ✅ Sistema 1: TarjetaActivityLogNomina

**Tabla**: `nomina_tarjetaactivitylognomina`

**Campos Clave:**
- `cierre_id` - Referencia al cierre
- `tarjeta` - Valor fijo: `'revision'`
- `accion` - Tipo de acción (process_start, process_complete, etc.)
- `usuario` - Usuario ejecutor
- `timestamp` - Fecha/hora

**Función de Registro:**
```python
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta='revision',
    accion='process_start',  # o 'process_complete', 'validation_error'
    usuario_id=usuario.id,
    detalles={...}
)
```

**Eventos Registrados:**
1. `process_start` - Inicio de verificación
2. `validation_error` - Error en validación
3. `process_complete` - Finalización exitosa

### ✅ Sistema 2: ActivityEvent

**Tabla**: `nomina_activityevent`

**Campos Clave:**
- `cierre_id` - Referencia al cierre
- `event_type` - Valor fijo: `'verification'`
- `action` - Acción específica
- `user` - Usuario ejecutor
- `timestamp` - Fecha/hora
- `metadata` - Datos adicionales (JSON)

**Función de Registro:**
```python
ActivityEvent.log(
    cierre_id=cierre.id,
    event_type='verification',
    action='verificacion_iniciada',  # o 'verificacion_completada_*'
    user_id=usuario.id,
    metadata={
        'total_discrepancias': int,
        'empleados_afectados': int,
        ...
    }
)
```

**Eventos Registrados:**
1. `verificacion_iniciada` - Inicio
2. `verificacion_completada_sin_discrepancias` - Sin discrepancias
3. `verificacion_completada_con_discrepancias` - Con discrepancias
4. `verificacion_fallida` - Error

### Comparación de Sistemas

| Característica | TarjetaActivityLogNomina | ActivityEvent |
|----------------|--------------------------|---------------|
| **Propósito** | Auditoría de tarjetas UI | Eventos generales |
| **Alcance** | Nómina específico | Sistema completo |
| **Granularidad** | Por tarjeta | Por tipo de evento |
| **Metadata** | Limitado | JSON flexible |
| **Consultas** | Por tarjeta + cierre | Por event_type + cierre |

---

## 📦 Resumen de Archivos

### Backend

| Archivo | Propósito | Componentes Principales |
|---------|-----------|------------------------|
| `backend/nomina/tasks_refactored/discrepancias.py` | Tasks Celery | `generar_discrepancias_cierre_con_logging()` |
| `backend/nomina/views_discrepancias.py` | ViewSets | `DiscrepanciaCierreViewSet` |
| `backend/nomina/utils/GenerarDiscrepancias.py` | Lógica de comparación | `generar_todas_discrepancias()` |
| `backend/nomina/models.py` | Modelos de datos | `DiscrepanciaCierre`, `HistorialVerificacionCierre` |
| `backend/nomina/serializers.py` | Serializers | `DiscrepanciaCierreSerializer` |
| `backend/nomina/urls.py` | Routing | `router.register()` |

### Frontend

| Archivo | Propósito | Componente |
|---------|-----------|------------|
| `src/components/TarjetasCierreNomina/VerificadorDatosSection.jsx` | Contenedor principal | `VerificadorDatosSection` |
| `src/components/TarjetasCierreNomina/VerificadorDatos/VerificacionControl.jsx` | Control de verificación | `VerificacionControl` |
| `src/components/TarjetasCierreNomina/VerificadorDatos/DiscrepanciasViewer.jsx` | Visualización | `DiscrepanciasViewer` |
| `src/api/nominaApi.js` | Cliente API | Funciones API |

---

## 🎯 Puntos Clave

### ✅ Funcionalidades Implementadas

1. **Comparación Libro vs Novedades**
   - Detección de empleados faltantes
   - Validación de datos personales
   - Verificación de sueldos base
   - Comparación de conceptos y montos

2. **Comparación Movimientos vs Archivos Analista**
   - Verificación de ingresos
   - Verificación de finiquitos
   - Detección de ausencias no reportadas

3. **Sistema de Logging Dual**
   - TarjetaActivityLogNomina
   - ActivityEvent
   - Trazabilidad completa

4. **API REST Completa**
   - CRUD de discrepancias
   - Endpoints especializados
   - Filtros y paginación

5. **Frontend Reactivo**
   - Polling automático
   - UI responsive
   - Visualización clara

### ⚠️ Funcionalidades NO Implementadas

1. **HistorialVerificacionCierre**
   - Modelo existe pero no se usa
   - No hay creación de registros
   - Impacto: **BAJO** (logs cubren auditoría)

2. **Cálculo de Tiempo de Ejecución**
   - No se registra explícitamente
   - Puede inferirse de logs
   - Impacto: **MUY BAJO**

---

## 📊 Métricas del Sistema

### Validación Flujo 7

- ✅ **7/9 verificaciones** pasadas (77%)
- ✅ **7/7 verificaciones core** (100%)
- ⚠️ **2 funcionalidades opcionales** no implementadas
- ✅ **25 discrepancias** detectadas correctamente
- ✅ **9 empleados** afectados identificados
- ✅ **Performance**: < 2 segundos

### Tipos de Discrepancias Detectadas

| Tipo | Cantidad | Porcentaje |
|------|----------|------------|
| `diff_concepto_monto` | 16 | 64% |
| `ingreso_no_reportado` | 3 | 12% |
| `ausencia_no_reportada` | 2 | 8% |
| `empleado_solo_novedades` | 2 | 8% |
| `finiquito_no_reportado` | 2 | 8% |

---

## 🔗 Referencias

- **README.md**: Arquitectura general del flujo
- **INSTRUCCIONES_PRUEBA.md**: Guía de testing
- **RESULTADOS.md**: Resultados de validación
- **PLAN_PRUEBA_SMOKE_TEST.md**: Plan maestro (Flujo 7 completado)

---

**Fecha de Creación**: 28 de octubre de 2025  
**Estado**: ✅ Documentación Completa  
**Versión**: 1.0
