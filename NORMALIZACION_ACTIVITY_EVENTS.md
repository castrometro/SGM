# 📋 Normalización de Activity Events - Sistema SGM

## 🎯 Objetivo

Estandarizar el registro de eventos de actividad para el ciclo de vida completo de un **Cierre de Nómina**, permitiendo queries eficientes y un timeline consistente.

---

## 🏗️ Estructura Normalizada

### Campo `cierre` (ForeignKey)
- **Propósito**: Relación directa con `CierreNomina` para queries eficientes
- **Tipo**: `ForeignKey(CierreNomina, null=True, blank=True, db_index=True)`
- **Ventaja**: Permite `ActivityEvent.objects.filter(cierre=cierre_id)` sin JSON queries

### Campos Estándar
```python
ActivityEvent.log(
    user=request.user,           # Usuario que ejecuta la acción
    cliente=cliente,              # Cliente asociado
    cierre=cierre,                # ✨ NORMALIZADO - Cierre de nómina
    event_type='upload',          # Tipo de evento
    action='archivo_subido',      # Acción específica
    resource_type='libro_rem',    # Tipo de recurso
    resource_id=str(libro.id),    # ID del recurso específico
    details={...},                # Detalles adicionales en JSON
    request=request               # Para IP y user agent
)
```

---

## 📊 Taxonomía de Event Types

| `event_type` | Descripción | Ejemplos de `action` |
|-------------|-------------|----------------------|
| `create` | Creación de recursos | `cierre_creado`, `empleado_creado` |
| `upload` | Subida de archivos | `upload_iniciado`, `archivo_validado` |
| `process` | Procesamiento async | `procesamiento_iniciado`, `procesamiento_completado` |
| `delete` | Eliminación | `archivo_eliminado`, `cierre_eliminado` |
| `update` | Actualizaciones | `estado_actualizado`, `datos_modificados` |
| `generate` | Generación de reportes | `discrepancias_generadas`, `incidencias_generadas` |
| `resolve` | Resolución de issues | `incidencia_resuelta`, `discrepancia_corregida` |
| `finalize` | Cierre de procesos | `cierre_finalizado`, `consolidacion_completada` |
| `error` | Errores | `validacion_fallida`, `procesamiento_error` |
| `view` | Consultas | `reporte_visto`, `timeline_consultado` |

---

## 🔄 Ciclo de Vida del Cierre - 15 Acciones Clave

### 1. **Creación del Cierre**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='create',
    action='cierre_creado',
    resource_type='cierre_nomina',
    resource_id=str(cierre.id),
    details={
        'periodo': str(cierre.periodo),
        'mes': cierre.periodo.month,
        'anio': cierre.periodo.year
    },
    request=request
)
```

### 2. **Subir Libro de Remuneraciones**
```python
# Inicio
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='upload_iniciado',
    resource_type='libro_remuneraciones',
    resource_id=str(cierre.id),
    details={
        'archivo_nombre': archivo.name,
        'archivo_size': archivo.size
    },
    request=request
)

# Validado
ActivityEvent.log(..., action='archivo_validado', resource_id=str(libro.id))

# Error
ActivityEvent.log(..., event_type='error', action='validacion_fallida')
```

### 3. **Libro Procesado**
```python
# En tarea Celery
ActivityEvent.log(
    user=sistema_user,
    cliente=cliente,
    cierre=cierre,
    event_type='process',
    action='procesamiento_completado',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'headers_detectados': len(headers),
        'registros_procesados': total_registros,
        'duracion_segundos': duracion
    }
)
```

### 4. **Libro Eliminado**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='delete',
    action='archivo_eliminado',
    resource_type='libro_remuneraciones',
    resource_id=str(libro.id),
    details={
        'archivo_nombre': libro.archivo.name,
        'estado_anterior': libro.estado,
        'motivo': 'resubida'
    },
    request=request
)
```

### 5. **Movimientos del Mes Subido**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='archivo_validado',
    resource_type='movimientos_mes',
    resource_id=str(movimiento.id),
    details={
        'archivo_nombre': archivo.name,
        'accion_db': 'creado' | 'actualizado'
    },
    request=request
)
```

### 6. **Eliminar Movimientos del Mes**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='delete',
    action='archivo_eliminado',
    resource_type='movimientos_mes',
    resource_id=str(movimiento.id),
    details={
        'archivo_nombre': movimiento.archivo.name,
        'movimientos_eliminados': {
            'altas_bajas': count_ab,
            'ausentismos': count_aus,
            'vacaciones': count_vac
        }
    },
    request=request
)
```

### 7. **Subir Archivo Finiquitos**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='archivo_validado',
    resource_type='finiquitos',
    resource_id=str(archivo.id),
    details={
        'archivo_nombre': archivo.nombre,
        'tipo_documento': 'finiquitos'
    },
    request=request
)
```

### 8. **Eliminar Archivo Finiquitos**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='delete',
    action='archivo_eliminado',
    resource_type='finiquitos',
    resource_id=str(archivo.id),
    details={
        'archivo_nombre': archivo.nombre,
        'registros_eliminados': count
    },
    request=request
)
```

### 9. **Subir/Eliminar Ausentismos/Incidencias**
```python
# Subir
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='archivo_validado',
    resource_type='ausentismos' | 'incidencias_externas',
    resource_id=str(archivo.id),
    details={
        'archivo_nombre': archivo.nombre,
        'tipo_documento': archivo.tipo_documento
    },
    request=request
)

# Eliminar
ActivityEvent.log(..., event_type='delete', action='archivo_eliminado')
```

### 10. **Subir/Eliminar Archivo Ingresos**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='archivo_validado',
    resource_type='ingresos',
    resource_id=str(archivo.id),
    details={
        'archivo_nombre': archivo.nombre,
        'registros_procesados': count
    },
    request=request
)
```

### 11. **Subir/Eliminar/Procesar Archivo Novedades**
```python
# Subir
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='upload',
    action='upload_iniciado',
    resource_type='novedades',
    resource_id=str(archivo.id),
    details={
        'archivo_nombre': archivo.nombre
    },
    request=request
)

# Procesamiento completado
ActivityEvent.log(
    user=sistema_user,
    cliente=cliente,
    cierre=cierre,
    event_type='process',
    action='clasificacion_completada',
    resource_type='novedades',
    resource_id=str(archivo.id),
    details={
        'headers_clasificados': len(headers),
        'columnas_creacion': columnas_creacion,
        'columnas_movimiento': columnas_movimiento
    }
)

# Consolidación final
ActivityEvent.log(
    user=sistema_user,
    cliente=cliente,
    cierre=cierre,
    event_type='process',
    action='consolidacion_completada',
    resource_type='novedades',
    resource_id=str(archivo.id),
    details={
        'empleados_actualizados': count_updated,
        'empleados_creados': count_created
    }
)
```

### 12. **Discrepancias Generadas**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='generate',
    action='discrepancias_generadas',
    resource_type='discrepancias',
    resource_id='',  # No hay recurso individual
    details={
        'total_discrepancias': total,
        'tipos': {
            'rut_duplicado': count_dup,
            'sueldo_cero': count_zero,
            'formato_invalido': count_inv
        }
    },
    request=request
)
```

### 13. **Incidencias Generadas**
```python
ActivityEvent.log(
    user=sistema_user,
    cliente=cliente,
    cierre=cierre,
    event_type='generate',
    action='incidencias_generadas',
    resource_type='incidencias',
    resource_id='',
    details={
        'total_incidencias': total,
        'empleados_afectados': count_emp,
        'conceptos_afectados': conceptos,
        'monto_total_diferencias': monto
    }
)
```

### 14. **Incidencias Resueltas**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='resolve',
    action='incidencia_resuelta',
    resource_type='incidencias',
    resource_id=str(incidencia.id),
    details={
        'incidencia_tipo': incidencia.tipo,
        'resolucion': incidencia.resolucion,
        'justificacion': incidencia.justificacion
    },
    request=request
)
```

### 15. **Cierre Finalizado**
```python
ActivityEvent.log(
    user=request.user,
    cliente=cliente,
    cierre=cierre,
    event_type='finalize',
    action='cierre_finalizado',
    resource_type='cierre_nomina',
    resource_id=str(cierre.id),
    details={
        'periodo': str(cierre.periodo),
        'total_empleados': count_emp,
        'total_registros': count_reg,
        'incidencias_pendientes': count_pending,
        'estado_final': cierre.estado
    },
    request=request
)
```

---

## 📈 Queries Optimizadas

### Timeline completo de un cierre
```python
eventos = ActivityEvent.objects.filter(
    cierre=cierre_id
).select_related('user', 'cliente').order_by('timestamp')
```

### Eventos de un tipo específico
```python
uploads = ActivityEvent.objects.filter(
    cierre=cierre_id,
    event_type='upload'
)
```

### Errores en el cierre
```python
errores = ActivityEvent.objects.filter(
    cierre=cierre_id,
    event_type='error'
)
```

### Actividad por usuario
```python
actividad_usuario = ActivityEvent.objects.filter(
    cierre=cierre_id,
    user=user
).order_by('-timestamp')
```

### Resumen de actividades
```python
resumen = ActivityEvent.objects.filter(
    cierre=cierre_id
).values('event_type').annotate(
    count=Count('id')
).order_by('-count')
```

---

## ✅ Ventajas de la Normalización

1. **Queries eficientes**: `filter(cierre=X)` en lugar de `filter(details__contains={'cierre_id': X})`
2. **Índices DB**: PostgreSQL puede indexar ForeignKey, no JSON
3. **Integridad referencial**: CASCADE automático al eliminar cierre
4. **Consistencia**: Todos los eventos usan la misma estructura
5. **Escalabilidad**: Agregar nuevos eventos es trivial
6. **Timeline preciso**: Ordenar por `timestamp` con filtro `cierre`

---

## 🔧 Próximos Pasos

- [ ] Actualizar todas las llamadas a `ActivityEvent.log()` para incluir `cierre=cierre`
- [ ] Crear endpoint API: `GET /api/nomina/cierres/{id}/timeline/`
- [ ] Implementar componente React `CierreTimeline` con estos eventos
- [ ] Agregar filtros por `event_type` en el frontend
- [ ] Crear vista de "Actividad Reciente" en dashboard

---

## 📝 Ejemplo de Respuesta API

```json
{
  "cierre_id": 123,
  "periodo": "2025-10",
  "eventos": [
    {
      "id": 1,
      "timestamp": "2025-10-17T10:30:00Z",
      "user": "juan.perez",
      "event_type": "create",
      "action": "cierre_creado",
      "resource_type": "cierre_nomina",
      "details": {"periodo": "2025-10"}
    },
    {
      "id": 2,
      "timestamp": "2025-10-17T10:35:00Z",
      "user": "maria.lopez",
      "event_type": "upload",
      "action": "upload_iniciado",
      "resource_type": "libro_remuneraciones",
      "details": {"archivo_nombre": "libro_octubre_2025.xlsx"}
    }
  ],
  "resumen": {
    "total_eventos": 15,
    "eventos_por_tipo": {
      "upload": 5,
      "process": 4,
      "generate": 2,
      "finalize": 1
    },
    "usuarios_activos": ["juan.perez", "maria.lopez", "sistema"]
  }
}
```

---

**Migración**: `0251_add_cierre_to_activity_event.py` ✅ Aplicada
