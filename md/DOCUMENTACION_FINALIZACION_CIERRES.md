# Sistema de Finalización de Cierres Contables

## Descripción General

Este sistema permite finalizar cierres contables que están en estado "sin_incidencias", ejecutando una serie de procesos automatizados que incluyen validaciones finales, cálculos contables, consolidación de datos y generación de reportes.

## Arquitectura

### Backend

- **Models**: `CierreContabilidad` con métodos para finalización
- **Tasks**: `tasks_finalizacion.py` con tareas de Celery
- **Views**: `views/finalizacion.py` con endpoints REST
- **URLs**: `urls_finalizacion.py` con rutas específicas

### Frontend

- **Componente React**: Maneja el botón de finalización y progreso
- **Polling**: Actualización en tiempo real del progreso
- **UX**: Modal de confirmación y seguimiento visual

## Flujo de Trabajo

### 1. Estado Inicial
```
Cierre en estado: "sin_incidencias"
→ Todas las incidencias resueltas
→ Archivos subidos y procesados
→ Botón "Finalizar Cierre" disponible
```

### 2. Inicio de Finalización
```
POST /api/contabilidad/cierres/{id}/finalizar/
→ Cambio de estado a "generando_reportes"
→ Disparo de tarea Celery
→ Retorno de task_id para seguimiento
```

### 3. Procesamiento (Tarea Celery)
```
Step 1: Validaciones Finales
  ├── Integridad de datos
  ├── Balance contable
  ├── Clasificaciones completas
  └── Nombres en inglés (si aplica)

Step 2: Cálculos Contables
  ├── Saldos finales
  ├── Balance de comprobación
  ├── Ratios financieros
  └── Movimientos por clasificación

Step 3: Consolidación Dashboard
  ├── Datos por área
  ├── Métricas de gestión
  ├── KPIs financieros
  └── Datos para gráficos

Step 4: Generación de Reportes
  ├── Balance General (PDF)
  ├── Estado de Resultados (PDF)
  ├── Reporte de Clasificaciones (Excel)
  ├── Reporte Bilingüe (Excel)
  └── Dashboard Ejecutivo (PDF)

Step 5: Finalización
  └── Estado cambia a "finalizado"
```

### 4. Estado Final
```
Cierre en estado: "finalizado"
→ fecha_finalizacion registrada
→ reportes_generados = True
→ Reportes disponibles para descarga
```

## Endpoints API

### 1. Finalizar Cierre
```http
POST /api/contabilidad/cierres/{cierre_id}/finalizar/
```

**Request Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Response (200):**
```json
{
  "success": true,
  "mensaje": "Finalización iniciada exitosamente",
  "task_id": "uuid-de-la-tarea",
  "cierre": {
    "id": 123,
    "estado": "generando_reportes",
    "periodo": "2025-06",
    "cliente": "Empresa ABC"
  },
  "estimacion_tiempo": "Aproximadamente 2-5 minutos"
}
```

**Response (400) - No puede finalizar:**
```json
{
  "success": false,
  "error": "El cierre debe estar en estado 'sin_incidencias'",
  "estado_actual": "incidencias_abiertas"
}
```

### 2. Estado de Finalización
```http
GET /api/contabilidad/cierres/{cierre_id}/estado-finalizacion/
```

**Response:**
```json
{
  "cierre": {
    "id": 123,
    "estado": "generando_reportes",
    "periodo": "2025-06",
    "cliente": "Empresa ABC",
    "puede_finalizar": false,
    "motivo_no_finalizar": "El cierre está siendo finalizado",
    "fecha_finalizacion": null,
    "reportes_generados": false,
    "fecha_sin_incidencias": "2025-07-01T10:30:00Z"
  },
  "tarea_activa": {
    "task_id": "uuid",
    "estado": "RUNNING",
    "descripcion": "Procesando finalización..."
  }
}
```

### 3. Progreso de Tarea
```http
GET /api/contabilidad/tareas/{task_id}/progreso/
```

**Response:**
```json
{
  "task_id": "uuid",
  "estado": "PROGRESS",
  "progreso": {
    "paso_actual": 2,
    "total_pasos": 5,
    "descripcion": "Ejecutando cálculos contables...",
    "porcentaje": 40
  }
}
```

### 4. Lista de Cierres Finalizables
```http
GET /api/contabilidad/cierres-finalizables/
```

**Response:**
```json
{
  "cierres": [
    {
      "id": 123,
      "periodo": "2025-06",
      "cliente": "Empresa ABC",
      "estado": "sin_incidencias",
      "fecha_sin_incidencias": "2025-07-01T10:30:00Z",
      "puede_finalizar": true,
      "dias_sin_incidencias": 2
    }
  ],
  "total": 1
}
```

## Integración Frontend

### Instalación del Componente

```jsx
import FinalizarCierreComponent from './components/FinalizarCierreComponent';

// En tu componente de cierre
<FinalizarCierreComponent 
  cierre={cierreData}
  onCierreActualizado={handleCierreUpdate}
/>
```

### Estados del Componente

1. **Botón Disponible**: Estado "sin_incidencias"
2. **Confirmación**: Modal de confirmación antes de iniciar
3. **En Progreso**: Modal con barra de progreso y detalles
4. **Completado**: Mensaje de éxito y enlaces a reportes
5. **Error**: Alert con mensaje de error

### Polling Automático

El componente hace polling cada 2 segundos para:
- Verificar el progreso de la tarea
- Actualizar la barra de progreso
- Detectar finalización o errores
- Actualizar el estado del cierre

## Configuración Celery

### Tareas Registradas

```python
# En settings.py o celery.py
CELERY_ROUTES = {
    'contabilidad.finalizar_cierre_y_generar_reportes': {'queue': 'finalizacion'},
    'contabilidad.ejecutar_validaciones_finales': {'queue': 'validaciones'},
    'contabilidad.ejecutar_calculos_contables': {'queue': 'calculos'},
    'contabilidad.consolidar_datos_dashboard': {'queue': 'consolidacion'},
    'contabilidad.generar_reportes_finales': {'queue': 'reportes'},
}
```

### Monitoreo

```bash
# Ver tareas activas
celery -A sgm inspect active

# Ver tareas programadas
celery -A sgm inspect scheduled

# Ver estadísticas
celery -A sgm inspect stats
```

## Logs y Debugging

### Logs de la Aplicación

```python
import logging
logger = logging.getLogger('contabilidad.finalizacion')

# En settings.py
LOGGING = {
    'loggers': {
        'contabilidad.finalizacion': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Seguimiento en Base de Datos

```python
# Los logs se almacenan en TarjetaActivityLog
TarjetaActivityLog.objects.filter(
    tarjeta='revision',
    accion='process_complete'
).order_by('-timestamp')
```

## Casos de Error Comunes

### 1. Cierre No Puede Finalizar
```
Error: "Hay 3 incidencias pendientes por resolver"
Solución: Resolver todas las incidencias antes de finalizar
```

### 2. Tarea Celery Falla
```
Error: Timeout o excepción en la tarea
Solución: El estado se revierte automáticamente a "sin_incidencias"
```

### 3. Permisos Insuficientes
```
Error: "No tienes permisos para finalizar este cierre"
Solución: Verificar que el usuario pertenece al cliente del cierre
```

## Extensiones Futuras

### 1. Notificaciones
- Email automático al finalizar
- Notificaciones push en tiempo real
- Integración con Slack/Teams

### 2. Reportes Personalizados
- Templates configurables
- Formatos adicionales (Word, CSV)
- Envío automático por email

### 3. Métricas y Analytics
- Tiempo promedio de finalización
- Estadísticas de errores
- Dashboard de monitoreo

### 4. Integración con Sistemas Externos
- ERP del cliente
- Sistemas de BI
- APIs de terceros

## Ejemplo de Uso

```python
# Backend - Finalizar un cierre
cierre = CierreContabilidad.objects.get(id=123)
puede, mensaje = cierre.puede_finalizar()

if puede:
    task_id = cierre.iniciar_finalizacion(usuario=request.user)
    print(f"Finalización iniciada: {task_id}")
else:
    print(f"No se puede finalizar: {mensaje}")
```

```javascript
// Frontend - Iniciar finalización
const finalizarCierre = async (cierreId) => {
  const response = await fetch(`/api/contabilidad/cierres/${cierreId}/finalizar/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Iniciar polling del progreso
    pollTaskProgress(data.task_id);
  }
};
```
