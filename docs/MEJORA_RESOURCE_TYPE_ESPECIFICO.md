# 🔧 Mejora: resource_type Específico por Tipo de Archivo

## 📋 Problema Identificado

Los logs de ActivityEvent usaban `resource_type='archivo_analista'` genérico para los 3 tipos de archivo, haciendo difícil identificar rápidamente qué tipo de archivo se procesó.

**Ejemplo anterior:**
```python
# ❌ Todos los archivos tenían el mismo resource_type
ActivityEvent: resource_type='archivo_analista'  # ¿finiquitos? ¿incidencias? ¿ingresos?
```

## ✅ Solución Implementada

Ahora `resource_type` incluye el tipo específico de archivo:

```python
# ✅ resource_type diferenciado por tipo
resource_type_especifico = f'archivo_analista_{tipo_archivo}'

# Ejemplos:
# - 'archivo_analista_finiquitos'
# - 'archivo_analista_incidencias'  
# - 'archivo_analista_ingresos'
```

## 🎯 Beneficios

### 1. Filtrado Rápido en Queries

**Antes:**
```python
# ❌ Necesitaba filtrar Y revisar details
events = ActivityEvent.objects.filter(resource_type='archivo_analista')
# Luego revisar details['tipo_archivo'] uno por uno
```

**Ahora:**
```python
# ✅ Filtrado directo por tipo específico
finiquitos = ActivityEvent.objects.filter(resource_type='archivo_analista_finiquitos')
incidencias = ActivityEvent.objects.filter(resource_type='archivo_analista_incidencias')
ingresos = ActivityEvent.objects.filter(resource_type='archivo_analista_ingresos')
```

### 2. Logs Más Claros

**Ejemplo de log mejorado:**
```
[INFO] ActivityEvent created: 
  resource_type='archivo_analista_finiquitos'    # ✅ Tipo visible inmediatamente
  action='procesamiento_celery_iniciado'
  user='ana.lopez@sgm.cl'
```

### 3. Métricas y Dashboards

Ahora es fácil crear métricas por tipo:
```python
# Contar procesamiento por tipo
from django.db.models import Count

metrics = ActivityEvent.objects.filter(
    resource_type__startswith='archivo_analista_',
    action='procesamiento_completado'
).values('resource_type').annotate(
    count=Count('id')
)

# Resultado:
# [
#   {'resource_type': 'archivo_analista_finiquitos', 'count': 45},
#   {'resource_type': 'archivo_analista_incidencias', 'count': 128},
#   {'resource_type': 'archivo_analista_ingresos', 'count': 23}
# ]
```

## 📊 Cambios Realizados

### Archivo Modificado
- `backend/nomina/tasks_refactored/archivos_analista.py`

### Cambios Específicos

**1. Procesamiento Iniciado (línea ~108)**
```python
# Calcular resource_type específico
resource_type_especifico = f'archivo_analista_{tipo_archivo}'

ActivityEvent.log(
    resource_type=resource_type_especifico,  # ✅ Específico
    # ...
)
```

**2. Procesamiento Completado (línea ~213)**
```python
ActivityEvent.log(
    action='procesamiento_completado',
    resource_type=resource_type_especifico,  # ✅ Específico
    # ...
)
```

**3. Procesamiento Error (línea ~280)**
```python
# En bloque de excepción, calcular resource_type
tipo_archivo = archivo.tipo_archivo or 'desconocido'
resource_type_especifico = f'archivo_analista_{tipo_archivo}'

ActivityEvent.log(
    action='procesamiento_error',
    resource_type=resource_type_especifico,  # ✅ Específico
    # ...
)
```

## 🔍 Ejemplos de Uso

### Query 1: Todos los finiquitos del último mes
```python
from datetime import datetime, timedelta
from nomina.models import ActivityEvent

un_mes_atras = datetime.now() - timedelta(days=30)

finiquitos = ActivityEvent.objects.filter(
    resource_type='archivo_analista_finiquitos',
    timestamp__gte=un_mes_atras
).select_related('user', 'cliente')

for evt in finiquitos:
    print(f"{evt.timestamp}: {evt.user.correo_bdo} - {evt.action}")
```

### Query 2: Errores por tipo de archivo
```python
from django.db.models import Count

errores_por_tipo = ActivityEvent.objects.filter(
    resource_type__startswith='archivo_analista_',
    event_type='error'
).values('resource_type').annotate(
    total_errores=Count('id')
).order_by('-total_errores')

print("Errores por tipo de archivo:")
for item in errores_por_tipo:
    tipo = item['resource_type'].replace('archivo_analista_', '')
    print(f"  {tipo.title()}: {item['total_errores']} errores")
```

### Query 3: Tiempo promedio de procesamiento por tipo
```python
from django.db.models import Avg, F
from django.db.models.functions import Extract

# Asumir que guardamos duration en details
tiempos = ActivityEvent.objects.filter(
    resource_type__startswith='archivo_analista_',
    action='procesamiento_completado',
    details__has_key='duration'
).values('resource_type').annotate(
    avg_duration=Avg(F('details__duration'))
)

for item in tiempos:
    tipo = item['resource_type'].replace('archivo_analista_', '')
    print(f"{tipo.title()}: {item['avg_duration']:.2f}s promedio")
```

## 📈 Compatibilidad

### Retrocompatibilidad
- ✅ Los logs antiguos con `resource_type='archivo_analista'` siguen siendo válidos
- ✅ Los nuevos logs usan el formato específico
- ✅ Queries pueden filtrar ambos:
  ```python
  # Todos los archivos analista (antiguos y nuevos)
  todos = ActivityEvent.objects.filter(
      resource_type__startswith='archivo_analista'
  )
  ```

### TarjetaActivityLogNomina
- ℹ️ `TarjetaActivityLogNomina` sigue usando `tarjeta='archivos_analista'` genérico
- ℹ️ La diferenciación está en `detalles['tipo_archivo']` y `detalles['tipo_display']`
- ✅ Esto está correcto porque es para UI de usuario

## ✅ Validación

| Aspecto | Estado |
|---------|--------|
| resource_type específico en logs iniciados | ✅ |
| resource_type específico en logs completados | ✅ |
| resource_type específico en logs de error | ✅ |
| Celery worker reiniciado | ✅ |
| Sin errores de sintaxis | ✅ |

## 🎓 Patrón Aplicable a Otros Módulos

Este patrón se puede aplicar a cualquier módulo que procese múltiples tipos:

```python
# Patrón general:
tipo = recurso.tipo or 'desconocido'
resource_type_especifico = f'{resource_type_base}_{tipo}'

ActivityEvent.log(
    resource_type=resource_type_especifico,  # ✅ Específico
    # ...
)
```

**Candidatos para aplicar:**
- ✅ Archivos Analista (ya aplicado)
- ⏳ Otros módulos con subtipos (si existen)

---

**Mejora aplicada:** 18 de octubre de 2025  
**Versión:** SGM v2.2.0  
**Impacto:** Mejora en observabilidad y análisis de logs
