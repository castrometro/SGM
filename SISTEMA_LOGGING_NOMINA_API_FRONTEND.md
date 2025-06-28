# API de Logging para Frontend - Nómina

## 📋 Endpoints Disponibles

### 🔄 **UploadLogNomina**

#### Listar Upload Logs
```
GET /api/nomina/upload-logs/
```

**Filtros disponibles:**
- `cierre_id`: ID del cierre
- `tipo_upload`: Tipo de archivo (`libro_remuneraciones`, `movimientos_mes`, etc.)
- `estado`: Estado del upload (`subido`, `procesando`, `completado`, `error`)
- `usuario_id`: ID del usuario
- `fecha_desde`: Fecha desde (ISO format)
- `fecha_hasta`: Fecha hasta (ISO format)

**Ejemplo:**
```
GET /api/nomina/upload-logs/?cierre_id=123&estado=completado
```

#### Obtener Upload Log específico
```
GET /api/nomina/upload-logs/{id}/
```

#### Estadísticas de Uploads
```
GET /api/nomina/upload-logs/estadisticas/
```

**Filtros opcionales:**
- `cierre_id`: Filtrar por cierre específico

**Respuesta:**
```json
{
  "total_uploads": 25,
  "por_tipo": {
    "libro_remuneraciones": 8,
    "movimientos_mes": 12,
    "novedades": 5
  },
  "por_estado": {
    "completado": 20,
    "error": 3,
    "procesando": 2
  },
  "tamaño_total_mb": 456.78,
  "tiempo_promedio_procesamiento": "2m 34s",
  "uploads_recientes": [...]
}
```

---

### 📝 **TarjetaActivityLogNomina**

#### Listar Activity Logs
```
GET /api/nomina/activity-logs/
```

**Filtros disponibles:**
- `cierre_id`: ID del cierre
- `tarjeta`: Tipo de tarjeta (`libro_remuneraciones`, `movimientos_mes`, etc.)
- `accion`: Acción realizada (`upload_excel`, `mapear_headers`, etc.)
- `usuario_id`: ID del usuario
- `resultado`: Resultado (`exito`, `error`, `warning`)
- `empleado_rut`: RUT del empleado afectado
- `concepto_afectado`: Concepto de remuneración afectado
- `fecha_desde`: Fecha desde (ISO format)
- `fecha_hasta`: Fecha hasta (ISO format)

**Ejemplo:**
```
GET /api/nomina/activity-logs/?cierre_id=123&tarjeta=novedades&resultado=exito
```

#### Resumen de Actividad por Tarjeta
```
GET /api/nomina/activity-logs/resumen_actividad/?cierre_id=123
```

**Respuesta:**
```json
[
  {
    "tarjeta": "libro_remuneraciones",
    "tarjeta_display": "Tarjeta 1: Libro de Remuneraciones",
    "total_actividades": 15,
    "ultima_actividad": "2025-06-27T10:30:00Z",
    "acciones_principales": {
      "upload_excel": 3,
      "analizar_headers": 5,
      "procesar_final": 2
    },
    "resultados_resumen": {
      "exito": 12,
      "warning": 2,
      "error": 1
    },
    "usuarios_activos": ["Juan Pérez", "Ana López"]
  },
  ...
]
```

---

### 📁 **MovimientosAnalistaUpload**

#### Listar Archivos del Analista
```
GET /api/nomina/movimientos-analista-uploads/
```

**Filtros disponibles:**
- `cierre_id`: ID del cierre
- `tipo_archivo`: Tipo de archivo (`ingresos`, `egresos`, etc.)
- `procesado`: Si está procesado (true/false)

---

### 🔧 **Endpoints Especiales**

#### Registrar Actividad desde Frontend
```
POST /api/nomina/logging/registrar-actividad/
```

**Body:**
```json
{
  "cierre_id": 123,
  "tarjeta": "modal_mapeo_novedades",
  "accion": "mapear_headers",
  "descripcion": "Usuario mapeó header 'SUELDO_BASE' a concepto 'Sueldo Base'",
  "detalles": {
    "header": "SUELDO_BASE",
    "concepto_id": 456,
    "concepto_nombre": "Sueldo Base"
  },
  "resultado": "exito",
  "empleado_rut": "12345678-9",
  "concepto_afectado": "Sueldo Base"
}
```

#### Obtener Todos los Logs de un Cierre
```
GET /api/nomina/logging/cierre/{cierre_id}/
```

**Respuesta:**
```json
{
  "cierre_id": 123,
  "cliente": "Empresa ABC",
  "periodo": "2025-06",
  "upload_logs": [...],
  "activity_logs": [...],
  "total_uploads": 8,
  "total_activities": 45
}
```

---

## 📊 **Casos de Uso Frontend**

### 1. **Dashboard de Actividad de Cierre**
```javascript
// Obtener resumen completo de un cierre
const response = await fetch(`/api/nomina/logging/cierre/${cierreId}/`);
const cierreData = await response.json();

// Mostrar estadísticas
console.log(`Total uploads: ${cierreData.total_uploads}`);
console.log(`Total actividades: ${cierreData.total_activities}`);
```

### 2. **Tarjeta con Histórico de Uploads**
```javascript
// Obtener uploads específicos de una tarjeta
const response = await fetch(
  `/api/nomina/upload-logs/?cierre_id=${cierreId}&tipo_upload=libro_remuneraciones`
);
const uploads = await response.json();

// Mostrar estado del último upload
const ultimoUpload = uploads.results[0];
console.log(`Estado: ${ultimoUpload.estado_display}`);
```

### 3. **Modal con Logging de Acciones**
```javascript
// Registrar cuando el usuario abre un modal
await fetch('/api/nomina/logging/registrar-actividad/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cierre_id: cierreId,
    tarjeta: "modal_mapeo_novedades",
    accion: "view_modal",
    descripcion: "Usuario abrió modal de mapeo de novedades",
    resultado: "exito"
  })
});

// Registrar cuando el usuario mapea un header
await fetch('/api/nomina/logging/registrar-actividad/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    cierre_id: cierreId,
    tarjeta: "modal_mapeo_novedades",
    accion: "mapear_headers",
    descripcion: `Header '${header}' mapeado a concepto '${concepto}'`,
    detalles: {
      header: header,
      concepto_id: conceptoId,
      concepto_nombre: concepto
    },
    resultado: "exito"
  })
});
```

### 4. **Vista de Auditoría**
```javascript
// Obtener actividades de un usuario específico
const response = await fetch(
  `/api/nomina/activity-logs/?usuario_id=${usuarioId}&fecha_desde=2025-06-01`
);
const actividades = await response.json();

// Filtrar por errores
const errores = actividades.results.filter(a => a.resultado === 'error');
```

### 5. **Estadísticas en Tiempo Real**
```javascript
// Obtener estadísticas de uploads
const response = await fetch(
  `/api/nomina/upload-logs/estadisticas/?cierre_id=${cierreId}`
);
const stats = await response.json();

// Mostrar gráficos
console.log('Uploads por tipo:', stats.por_tipo);
console.log('Estados:', stats.por_estado);
```

---

## 🎯 **Integración Recomendada**

### **Componente React de Ejemplo**
```jsx
import { useState, useEffect } from 'react';

export const CierreActivityDashboard = ({ cierreId }) => {
  const [logs, setLogs] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Cargar datos del cierre
    fetch(`/api/nomina/logging/cierre/${cierreId}/`)
      .then(res => res.json())
      .then(setLogs);

    // Cargar estadísticas
    fetch(`/api/nomina/upload-logs/estadisticas/?cierre_id=${cierreId}`)
      .then(res => res.json())
      .then(setStats);
  }, [cierreId]);

  const registrarActividad = async (tarjeta, accion, descripcion, detalles = {}) => {
    await fetch('/api/nomina/logging/registrar-actividad/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cierre_id: cierreId,
        tarjeta,
        accion,
        descripcion,
        detalles,
        resultado: 'exito'
      })
    });
  };

  return (
    <div className="cierre-dashboard">
      <h2>Actividad del Cierre</h2>
      
      {stats && (
        <div className="stats">
          <div>Total Uploads: {stats.total_uploads}</div>
          <div>Tiempo Promedio: {stats.tiempo_promedio_procesamiento}</div>
        </div>
      )}
      
      {logs && (
        <div className="activities">
          <h3>Actividades Recientes</h3>
          {logs.activity_logs.slice(0, 10).map(log => (
            <div key={log.id} className="activity-item">
              <span>{log.tarjeta_display}</span>
              <span>{log.accion_display}</span>
              <span>{log.tiempo_transcurrido}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```
