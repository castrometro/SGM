# PLAN DE CIERRE FASE 1 - ENDPOINTS NECESARIOS

## ✅ ENDPOINTS IMPLEMENTADOS
- POST /api/nomina/cierres/ (crear cierre)
- GET /api/nomina/cierres/ (listar cierres)
- GET /api/nomina/cierres/{id}/ (detalle cierre)
- GET /api/nomina/cierres/{id}/dashboard/ (dashboard con tarjetas)
- POST /api/nomina/cierres/{id}/consolidar/ (consolidación)
- POST /api/nomina/cierres/{id}/cerrar/ (cierre final)
- POST /api/nomina/cierres/{id}/reabrir/ (reapertura)
- POST /api/nomina/cierres/{id}/inicializar-redis/ (inicializar Redis)

## 🚧 ENDPOINTS PENDIENTES DE IMPLEMENTAR

### 1. CARGA DE ARCHIVOS
```python
# Subir libro de remuneraciones
POST /api/nomina/cierres/{id}/subir-libro/
Content-Type: multipart/form-data
{
    "archivo": File,
    "tipo_archivo": "excel|csv",
    "separador": "," # solo para CSV
}

Response: {
    "success": true,
    "archivo_id": 123,
    "empleados_detectados": 45,
    "conceptos_detectados": ["Sueldo Base", "Horas Extras", ...],
    "redis_key": "sgm:nomina:6:2025-03:libro_remuneraciones"
}
```

### 2. ANÁLISIS Y VALIDACIÓN
```python
# Analizar discrepancias
POST /api/nomina/cierres/{id}/analizar-discrepancias/
Response: {
    "discrepancias_detectadas": 3,
    "empleados_faltantes": ["12345678-9"],
    "empleados_sobrantes": ["98765432-1"],
    "diferencias_conceptos": [
        {
            "empleado": "11111111-1",
            "concepto": "Sueldo Base",
            "valor_libro": 800000,
            "valor_talana": 850000,
            "diferencia": 50000
        }
    ]
}

# Obtener datos del archivo subido
GET /api/nomina/cierres/{id}/datos-libro/
Response: {
    "empleados": [...],
    "conceptos_summary": {...},
    "estadisticas": {
        "total_empleados": 45,
        "masa_salarial": 28500000
    }
}
```

### 3. GESTIÓN DE INCIDENCIAS
```python
# Ya implementado en IncidenciaViewSet pero faltan endpoints específicos:

# Crear incidencia manual
POST /api/nomina/incidencias/
{
    "cierre": 4,
    "empleado_rut": "12345678-9",
    "concepto_afectado": "Sueldo Base",
    "tipo_incidencia": "variacion_sospechosa",
    "descripcion": "Variación del 30% respecto mes anterior"
}

# Asignar incidencia a analista/supervisor  
POST /api/nomina/incidencias/{id}/asignar/
{
    "analista_id": 2,
    "supervisor_id": 3
}

# Resolver incidencia
POST /api/nomina/incidencias/{id}/resolver/
{
    "observaciones": "Revisado con cliente, aumento por promoción"
}
```

### 4. CHECKLIST DE CONTROL
```python
# Obtener checklist del cierre
GET /api/nomina/cierres/{id}/checklist/
Response: [
    {
        "id": 1,
        "descripcion": "Validar archivo libro de remuneraciones subido",
        "estado": "completado",
        "comentario": "Archivo validado correctamente",
        "es_obligatorio": true
    },
    ...
]

# Actualizar item del checklist
PUT /api/nomina/checklist/{id}/
{
    "estado": "completado",
    "comentario": "Validación completada sin observaciones"
}
```

### 5. REPORTES Y EXPORTACIÓN
```python
# Generar reporte de cierre
GET /api/nomina/cierres/{id}/reporte/
Query params: ?formato=pdf|excel|csv

# Exportar datos consolidados
GET /api/nomina/cierres/{id}/exportar/
Response: archivo con datos consolidados del cierre
```

## 🎯 PRIORIDAD DE IMPLEMENTACIÓN

### FASE 1A (Críticos para funcionalidad básica):
1. POST /api/nomina/cierres/{id}/subir-libro/
2. POST /api/nomina/cierres/{id}/analizar-discrepancias/
3. GET /api/nomina/cierres/{id}/datos-libro/
4. GET /api/nomina/cierres/{id}/checklist/
5. PUT /api/nomina/checklist/{id}/

### FASE 1B (Para completar el flujo):
6. POST /api/nomina/incidencias/ (crear manual)
7. Endpoints específicos de incidencias (ya implementados en ViewSet)
8. Reportes básicos

### FASE 1C (Mejoras y optimizaciones):
9. Integración con Talana API
10. Exportaciones avanzadas
11. Notificaciones y alertas

## 📋 DATOS DE PRUEBA NECESARIOS

Para probar el flujo completo necesitamos:

1. **Archivo de libro de remuneraciones** (Excel/CSV)
2. **Mapeos de conceptos** para el cliente
3. **Empleados de prueba** con conceptos variados
4. **Datos del período anterior** para comparaciones
5. **Usuarios con diferentes roles** (analista, supervisor, gerente)

## 🚀 PRÓXIMOS PASOS INMEDIATOS

1. Implementar endpoint de carga de archivos
2. Crear datos de prueba para validar el flujo
3. Implementar análisis de discrepancias
4. Probar consolidación completa con datos reales
5. Validar todas las tarjetas del dashboard con información

¿Por cuál endpoint quieres empezar?
