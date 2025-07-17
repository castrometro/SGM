# Sistema de Logging de Actividad en Contabilidad

## Resumen del Sistema

El sistema de contabilidad utiliza un sistema centralizado de logging que registra todas las actividades de los usuarios en la base de datos a través del modelo `TarjetaActivityLog`. Este sistema permite auditoría completa y trazabilidad de todas las operaciones realizadas en el sistema.

## Arquitectura del Sistema

### 1. Modelo Principal: `TarjetaActivityLog`

**Ubicación**: `/backend/contabilidad/models.py` (líneas 716-785)

**Campos principales**:
- `cierre`: ForeignKey a `CierreContabilidad` (asociación obligatoria)
- `tarjeta`: CharField con las opciones de tarjetas del sistema
- `accion`: CharField con el tipo de acción realizada
- `descripcion`: TextField con descripción legible
- `usuario`: ForeignKey a Usuario (puede ser null para procesos automáticos)
- `detalles`: JSONField con información adicional
- `resultado`: CharField ('exito', 'error', 'warning')
- `timestamp`: DateTimeField automático
- `ip_address`: CharField para auditoría

### 2. Función Central: `registrar_actividad_tarjeta`

**Ubicación**: `/backend/contabilidad/utils/activity_logger.py`

**Función principal**:
```python
def registrar_actividad_tarjeta(
    cliente_id,
    periodo,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado='exito',
    ip_address=None
):
```

**Características**:
- ✅ **Seguridad**: No crea cierres automáticamente si no existen
- ✅ **Tolerancia a fallos**: No falla operaciones principales por errores de logging
- ✅ **Flexibilidad**: Acepta procesos automáticos (usuario=None) y manuales
- ✅ **Auditoría**: Registra IP, detalles JSON y timestamps automáticos

## Tipos de Tarjetas (TARJETA_CHOICES)

### Tarjetas del Sistema
```python
TARJETA_CHOICES = [
    ("tipo_documento", "Tarjeta: Tipo de Documento"),
    ("libro_mayor", "Tarjeta: Libro Mayor"),
    ("clasificacion", "Tarjeta: Clasificaciones"),
    ("nombres_ingles", "Tarjeta: Nombres en Inglés"),
    ("incidencias", "Tarjeta: Incidencias"),
    ("revision", "Tarjeta: Revisión"),
    ("movimientos_cuenta", "Tarjeta: Movimientos por Cuenta"),
    ("movimientos_resumen", "Tarjeta: Resumen de Movimientos"),
    ("reportes", "Tarjeta: Reportes"),
]
```

### Mapeo por Funcionalidad

1. **tipo_documento**: Gestión de tipos de documentos contables
2. **libro_mayor**: Carga y procesamiento de libros mayor
3. **clasificacion**: Gestión de clasificaciones contables
4. **nombres_ingles**: Gestión de nombres en inglés
5. **incidencias**: Gestión de incidencias y resoluciones
6. **revision**: Procesos de revisión y aprobación
7. **movimientos_cuenta**: Consulta de movimientos por cuenta específica
8. **movimientos_resumen**: Consulta de resumen de movimientos
9. **reportes**: Generación y consulta de reportes

## Tipos de Acciones (ACCION_CHOICES)

### Acciones Manuales
```python
- "manual_create": Creación manual de registros
- "manual_edit": Edición manual de registros  
- "manual_delete": Eliminación manual de registros
- "bulk_delete": Eliminación masiva de registros
```

### Acciones de Visualización
```python
- "view_data": Visualización de datos/consultas
- "view_list": Visualización de listas
```

### Acciones de Procesamiento
```python
- "upload_excel": Subida de archivos Excel
- "process_start": Inicio de procesamiento
- "process_complete": Procesamiento completado
- "validation_error": Error de validación
```

### Acciones de Gestión
```python
- "set_create": Creación de conjuntos/sets
- "set_edit": Edición de conjuntos/sets
- "set_delete": Eliminación de conjuntos/sets
- "option_create": Creación de opciones
- "option_edit": Edición de opciones
- "option_delete": Eliminación de opciones
- "individual_create": Creación individual
- "individual_edit": Edición individual
- "individual_delete": Eliminación individual
- "delete_all": Eliminación total
```

## Puntos de Registro en el Sistema

### 1. Vistas CRUD (`ViewSets`)

**Archivos principales**:
- `/backend/contabilidad/views/tipo_documento.py`
- `/backend/contabilidad/views/clasificacion.py`
- `/backend/contabilidad/views/nombres_ingles.py`

**Implementación**:
```python
def perform_create(self, serializer):
    instance = serializer.save()
    
    registrar_actividad_tarjeta(
        cliente_id=instance.cliente_id,
        periodo=obtener_periodo_actividad_para_cliente(cliente),
        tarjeta="tipo_documento",
        accion="manual_create",
        descripcion=f"Creó tipo documento: {instance.codigo}",
        usuario=self.request.user,
        detalles={
            "tipo_documento_id": instance.id,
            "codigo": instance.codigo,
        },
        resultado="exito",
        ip_address=get_client_ip(self.request),
    )
```

### 2. Consultas de Visualización

**Archivo**: `/backend/contabilidad/views/cierre.py`

**Ejemplo - Resumen de Movimientos**:
```python
def movimientos_resumen(self, request, pk=None):
    # ... lógica de consulta ...
    
    self.log_activity(
        cliente_id=cierre.cliente.id,
        periodo=cierre.periodo,
        tarjeta="movimientos_resumen",
        accion="view_data",
        descripcion=f"Consulta resumen movimientos - {len(data)} cuentas",
        usuario=request.user,
        detalles={
            "cierre_id": cierre.id,
            "filtros": {...},
            "cuentas_mostradas": len(data),
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )
```

### 3. Tareas Asíncronas (Celery)

**Archivos**:
- `/backend/contabilidad/tasks.py`
- `/backend/contabilidad/tasks_de_tipo_doc.py`
- `/backend/contabilidad/tasks_cuentas_bulk.py`

**Ejemplo - Procesamiento de Excel**:
```python
def procesar_libro_mayor(upload_log_id):
    # ... lógica de procesamiento ...
    
    registrar_actividad_tarjeta(
        cliente_id=upload_log.cliente.id,
        periodo=upload_log.cierre.periodo,
        tarjeta="libro_mayor",
        accion="process_complete",
        descripcion=f"Procesado archivo: {movimientos_creados} movimientos",
        usuario=None,  # Proceso automático
        detalles={
            "upload_log_id": upload_log.id,
            "movimientos_creados": movimientos_creados,
        },
        resultado="exito",
        ip_address=None,
    )
```

### 4. Subida de Archivos

**Archivo**: `/backend/contabilidad/views/clasificacion.py`

**Ejemplo**:
```python
def upload_excel(request):
    # ... lógica de subida ...
    
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo_actividad,
        tarjeta="clasificacion",
        accion="upload_excel",
        descripcion=f"Subido archivo: {archivo.name}",
        usuario=request.user,
        detalles={
            "nombre_archivo": archivo.name,
            "tamaño_bytes": archivo.size,
            "upload_log_id": upload_log.id,
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )
```

## Mixin para Logging Automático

**Ubicación**: `/backend/contabilidad/utils/mixins.py`

**Uso**:
```python
class ActivityLogMixin:
    def log_activity(self, **kwargs):
        registrar_actividad_tarjeta(**kwargs)
```

**Implementación en ViewSets**:
```python
class CierreContabilidadViewSet(ActivityLogMixin, viewsets.ModelViewSet):
    def movimientos_resumen(self, request, pk=None):
        # ... lógica ...
        self.log_activity(
            cliente_id=cierre.cliente.id,
            periodo=cierre.periodo,
            tarjeta="movimientos_resumen",
            # ... más parámetros
        )
```

## Manejo de Errores

### Principios de Diseño

1. **No fallar operaciones principales**: Los errores de logging no deben afectar la funcionalidad
2. **Logging silencioso**: Se capturan excepciones pero no se propagan
3. **Logging de fallbacks**: Se usan datos por defecto cuando faltan parámetros

### Ejemplo de Manejo de Errores

```python
try:
    registrar_actividad_tarjeta(
        cliente_id=instance.cliente_id,
        periodo=periodo_actividad,
        tarjeta="tipo_documento",
        accion="manual_create",
        descripcion=f"Creó tipo documento: {instance.codigo}",
        usuario=self.request.user,
        # ... más parámetros
    )
except Exception as e:
    # No fallar la creación si hay error en el logging
    logger.error(f"Error en logging: {e}")
```

## Consulta de Logs

### Endpoint Principal

**URL**: `/contabilidad/gerente/logs-actividad/`
**Vista**: `obtener_logs_actividad` en `/backend/contabilidad/views/gerente.py`

### Filtros Disponibles

```python
filtros = {
    'cliente_id': 'ID del cliente',
    'usuario_id': 'ID del usuario',
    'tarjeta': 'Tipo de tarjeta',
    'accion': 'Tipo de acción',
    'cierre': 'Estado del cierre',
    'periodo': 'Período específico (ej: 2025-07)',
    'fecha_desde': 'Fecha desde',
    'fecha_hasta': 'Fecha hasta',
}
```

### Respuesta del Endpoint

```json
{
    "results": [
        {
            "id": 1,
            "cliente_id": 123,
            "cliente_nombre": "Cliente ABC",
            "usuario_nombre": "Juan Pérez",
            "usuario_email": "juan@empresa.com",
            "tarjeta": "tipo_documento",
            "accion": "manual_create",
            "descripcion": "Creó tipo documento: FC001",
            "resultado": "exito",
            "timestamp": "2025-07-17T10:30:00Z",
            "ip_address": "192.168.1.100",
            "detalles": {
                "tipo_documento_id": 456,
                "codigo": "FC001"
            },
            "estado_cierre": "clasificacion",
            "periodo_cierre": "2025-07"
        }
    ],
    "count": 1,
    "total_pages": 1,
    "current_page": 1,
    "has_next": false,
    "has_previous": false
}
```

## Estadísticas y Métricas

### Endpoint de Estadísticas

**URL**: `/contabilidad/gerente/estadisticas-actividad/`
**Vista**: `obtener_estadisticas_actividad`

### Métricas Disponibles

```python
estadisticas = {
    'resumen': {
        'total_actividades': 1250,
        'usuarios_activos': 12,
        'clientes_trabajados': 45,
        'periodo': 'semana'
    },
    'actividades_por_dia': [...],
    'top_usuarios': [...],
    'actividades_por_tarjeta': [...],
    'actividades_por_accion': [...]
}
```

## Mejores Prácticas

### 1. Descripción Clara

```python
# ✅ Buena práctica
descripcion="Creó tipo documento manual: FC001 - Factura Comercial"

# ❌ Mala práctica  
descripcion="Creó registro"
```

### 2. Detalles Estructurados

```python
# ✅ Buena práctica
detalles={
    "tipo_documento_id": instance.id,
    "codigo": instance.codigo,
    "descripcion": instance.descripcion,
    "accion_origen": "crud_manual",
}

# ❌ Mala práctica
detalles={"data": "algún dato"}
```

### 3. Manejo de Usuarios

```python
# ✅ Para acciones manuales
usuario=self.request.user

# ✅ Para procesos automáticos
usuario=None
```

### 4. Resultado Apropiado

```python
# ✅ Uso correcto
resultado="exito"     # Operación exitosa
resultado="error"     # Error en la operación
resultado="warning"   # Completado con advertencias
```

## Casos de Uso Comunes

### 1. Tracking de Subida de Archivos

```python
# Al subir archivo
registrar_actividad_tarjeta(
    tarjeta="clasificacion",
    accion="upload_excel",
    descripcion=f"Subido archivo: {archivo.name}",
    # ...
)

# Al completar procesamiento
registrar_actividad_tarjeta(
    tarjeta="clasificacion", 
    accion="process_complete",
    descripcion=f"Procesado archivo: {registros_creados} registros",
    # ...
)
```

### 2. Tracking de Operaciones CRUD

```python
# Crear
registrar_actividad_tarjeta(
    accion="manual_create",
    descripcion=f"Creó {tipo}: {identificador}",
    # ...
)

# Editar
registrar_actividad_tarjeta(
    accion="manual_edit",
    descripcion=f"Editó {tipo}: {identificador}",
    # ...
)

# Eliminar
registrar_actividad_tarjeta(
    accion="manual_delete",
    descripcion=f"Eliminó {tipo}: {identificador}",
    # ...
)
```

### 3. Tracking de Consultas

```python
registrar_actividad_tarjeta(
    accion="view_data",
    descripcion=f"Consultó resumen de movimientos - {total_registros} registros",
    detalles={
        "filtros_aplicados": filtros,
        "registros_mostrados": total_registros,
    },
    # ...
)
```

## Conclusión

El sistema de logging de actividad en contabilidad es robusto y completo, proporcionando:

- **Auditoría completa**: Registro de todas las acciones del usuario
- **Trazabilidad**: Seguimiento de procesos automáticos y manuales
- **Flexibilidad**: Adaptable a diferentes tipos de operaciones
- **Tolerancia a fallos**: No afecta operaciones principales
- **Análisis**: Estadísticas y métricas para gestión

Este sistema permite a los gerentes tener visibilidad completa de la actividad del sistema y realizar auditorías detalladas cuando sea necesario.
