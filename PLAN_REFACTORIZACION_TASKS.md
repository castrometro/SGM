# 🔥 Plan de Refactorización: nomina/tasks.py

**Fecha**: 17 de octubre de 2025  
**Problema**: Archivo monolítico de 5,279 líneas con 59 tareas Celery caóticas  
**Objetivo**: Organizar tareas por dominio funcional con estructura clara

---

## 📊 Estado Actual (Análisis)

### **Números que Asustan**:
- **5,279 líneas** en un solo archivo
- **59 tareas Celery** (`@shared_task`)
- **~100+ funciones** totales
- **Múltiples versiones** de la misma funcionalidad:
  - `consolidar_datos_nomina_task()`
  - `consolidar_datos_nomina_task_optimizado()`
  - `consolidar_datos_nomina_task_secuencial()`
  - `consolidar_datos_nomina_task_paralelo()` (¿existe?)
- **Código muerto**: v1, v2, _old, _legacy sin documentar
- **Sin organización**: Todo mezclado sin separación por dominio

### **Tareas Identificadas por Categoría**:

#### 📖 **Libro de Remuneraciones** (≈15 tareas):
- `analizar_headers_libro_remuneraciones()`
- `analizar_headers_libro_remuneraciones_con_logging()` ⚠️ DUPLICADO
- `clasificar_headers_libro_remuneraciones_task()`
- `clasificar_headers_libro_remuneraciones_con_logging()` ⚠️ DUPLICADO
- `actualizar_empleados_desde_libro()`
- `guardar_registros_nomina()`
- `procesar_chunk_empleados_*()` (múltiples versiones)
- `procesar_chunk_registros_*()` (múltiples versiones)

#### 📅 **Movimientos del Mes** (≈3 tareas):
- `procesar_movimientos_mes()`
- `procesar_movimientos_personal_paralelo()`

#### 📋 **Archivos Analista** (≈2 tareas):
- `procesar_archivo_analista()`

#### 🆕 **Novedades** (≈12 tareas):
- `analizar_headers_archivo_novedades()`
- `clasificar_headers_archivo_novedades_task()`
- `actualizar_empleados_desde_novedades_task()`
- `actualizar_empleados_desde_novedades_task_optimizado()` ⚠️ DUPLICADO
- `guardar_registros_novedades_task()`
- `guardar_registros_novedades_task_optimizado()` ⚠️ DUPLICADO
- `procesar_chunk_*_novedades_*()` (múltiples)

#### 🔄 **Consolidación** (≈10 tareas):
- `consolidar_cierre_task()`
- `consolidar_datos_nomina_task()`
- `consolidar_datos_nomina_task_optimizado()` ⚠️ DUPLICADO
- `consolidar_datos_nomina_task_secuencial()` ⚠️ DUPLICADO
- `procesar_empleados_libro_paralelo()`
- `procesar_conceptos_consolidados_paralelo()`
- `finalizar_consolidacion_post_movimientos()`
- `consolidar_resultados_finales()`

#### ⚠️ **Incidencias** (≈15 tareas):
- `generar_incidencias_totales_simple()`
- `generar_incidencias_cierre_task()`
- `generar_incidencias_consolidados_v2_task()` ⚠️ v2
- `generar_incidencias_consolidadas_task()`
- `generar_incidencias_cierre_paralelo()`
- `procesar_chunk_comparacion_individual_task()`
- `procesar_comparacion_suma_total_task()`
- `consolidar_resultados_incidencias_task()`

#### 📉 **Discrepancias** (≈5 tareas):
- `analizar_datos_cierre_task()`
- `generar_discrepancias_cierre_task()`
- `generar_discrepancias_cierre_paralelo()`

---

## 🎯 Estrategia de Refactorización

### **Fase 1: Mapeo y Documentación** (2 horas)
**Objetivo**: Entender qué tareas se usan actualmente

#### Acciones:
1. **Identificar tareas activas**:
   ```bash
   # Buscar qué tareas se llaman desde views
   grep -r "\.delay\|\.apply_async\|chain\|chord\|group" backend/nomina/views*.py
   ```

2. **Marcar código muerto**:
   - Tareas sin referencias: DEPRECATED
   - Versiones antiguas: OBSOLETE
   - Experimentos: EXPERIMENTAL

3. **Crear matriz de dependencias**:
   - ¿Qué tarea llama a qué?
   - ¿Qué utils usa cada tarea?

### **Fase 2: Arquitectura Nueva** (Diseño)

#### **Estructura Propuesta**:

```
backend/nomina/
├── tasks/
│   ├── __init__.py              # Exporta todas las tareas para Celery
│   │
│   ├── libro_remuneraciones.py  # 📖 LIBRO DE REMUNERACIONES
│   │   ├── analizar_headers()
│   │   ├── clasificar_headers()
│   │   ├── procesar_empleados()
│   │   ├── procesar_registros()
│   │   └── procesar_chunk_empleados()  # Worker paralelo
│   │
│   ├── movimientos_mes.py       # 📅 MOVIMIENTOS DEL MES
│   │   ├── procesar_movimientos()
│   │   └── procesar_movimientos_paralelo()
│   │
│   ├── archivos_analista.py     # 📋 ARCHIVOS ANALISTA
│   │   └── procesar_archivo()
│   │
│   ├── novedades.py             # 🆕 NOVEDADES
│   │   ├── analizar_headers()
│   │   ├── clasificar_headers()
│   │   ├── procesar_empleados()
│   │   └── procesar_registros()
│   │
│   ├── consolidacion.py         # 🔄 CONSOLIDACIÓN
│   │   ├── consolidar_cierre()
│   │   ├── consolidar_empleados()
│   │   ├── consolidar_conceptos()
│   │   └── finalizar_consolidacion()
│   │
│   ├── incidencias.py           # ⚠️ INCIDENCIAS
│   │   ├── generar_incidencias_simple()
│   │   ├── generar_incidencias_avanzado()
│   │   └── consolidar_incidencias()
│   │
│   ├── discrepancias.py         # 📉 DISCREPANCIAS
│   │   ├── analizar_datos_cierre()
│   │   └── generar_discrepancias()
│   │
│   └── _deprecated.py           # 🗑️ CÓDIGO OBSOLETO (temporal)
│       └── [todas las versiones antiguas]
│
└── tasks.py                     # ⚠️ MANTENER VACÍO CON IMPORT
    # from .tasks import *  # Para retrocompatibilidad
```

#### **Ventajas**:
- ✅ **Modular**: Cada archivo < 500 líneas
- ✅ **Claro**: Nombre del archivo = dominio funcional
- ✅ **Mantenible**: Fácil encontrar dónde está cada tarea
- ✅ **Testeable**: Tests unitarios por módulo
- ✅ **Escalable**: Agregar nuevas tareas sin contaminar

---

## 📋 Plan de Migración (Paso a Paso)

### **Paso 1: Crear Estructura de Directorios**

```bash
mkdir -p backend/nomina/tasks
touch backend/nomina/tasks/__init__.py
```

### **Paso 2: Extraer Tareas por Dominio** (Orden de prioridad)

#### **2.1 Libro de Remuneraciones** (PRIMERO - crítico)

```python
# backend/nomina/tasks/libro_remuneraciones.py

from celery import shared_task, chain
from ..models import LibroRemuneracionesUpload, ActivityEvent
from ..utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
)
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, queue='nomina_queue')
def analizar_headers(self, libro_id):
    """
    Analiza headers del libro de remuneraciones.
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
    
    Returns:
        dict: {libro_id, headers, archivo_path}
    
    Raises:
        Exception: Si falla el análisis
    """
    logger.info(f"[LIBRO] Analizando headers libro {libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.select_related(
            'cierre', 'cierre__cliente'
        ).get(id=libro_id)
        
        cierre = libro.cierre
        
        # Logging V2
        ActivityEvent.log(
            user=sistema_user(),
            cliente=cierre.cliente,
            cierre=cierre,
            event_type='process',
            action='analisis_headers_iniciado',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={'task_id': self.request.id}
        )
        
        # Procesar
        resultado = obtener_headers_libro_remuneraciones(
            str(libro.archivo.path)
        )
        
        # Logging éxito
        ActivityEvent.log(
            user=sistema_user(),
            cliente=cierre.cliente,
            cierre=cierre,
            event_type='process',
            action='analisis_headers_exitoso',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'columnas': len(resultado['headers']),
                'task_id': self.request.id
            }
        )
        
        return {
            'libro_id': libro_id,
            'headers': resultado['headers'],
            'archivo_path': str(libro.archivo.path)
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] Error analizando headers: {e}")
        
        # Logging error
        ActivityEvent.log(
            user=sistema_user(),
            cliente=cierre.cliente,
            cierre=cierre,
            event_type='process',
            action='analisis_headers_error',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={'error': str(e)}
        )
        
        raise


@shared_task(bind=True, queue='nomina_queue')
def clasificar_headers(self, resultado_anterior):
    """
    Clasifica headers del libro usando IA.
    
    Args:
        resultado_anterior: Output de analizar_headers()
    
    Returns:
        dict: {libro_id, clasificaciones}
    """
    # Similar pattern...
    pass


def sistema_user():
    """Helper: Usuario sistema para Celery tasks"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_staff=True).first()
```

#### **2.2 Consolidación** (SEGUNDO - core business)

```python
# backend/nomina/tasks/consolidacion.py

@shared_task(bind=True, queue='nomina_queue')
def consolidar_cierre(self, cierre_id, modo='optimizado'):
    """
    Tarea principal de consolidación.
    
    Args:
        cierre_id: ID del CierreNomina
        modo: 'secuencial' | 'optimizado' | 'paralelo'
    """
    logger.info(f"[CONSOLIDACION] Iniciando modo={modo} cierre={cierre_id}")
    
    if modo == 'paralelo':
        return _consolidar_paralelo(cierre_id)
    elif modo == 'secuencial':
        return _consolidar_secuencial(cierre_id)
    else:
        return _consolidar_optimizado(cierre_id)


def _consolidar_optimizado(cierre_id):
    """Implementación optimizada (default)"""
    # Código limpio sin versiones antiguas
    pass


def _consolidar_paralelo(cierre_id):
    """Implementación paralela con chord"""
    # Para cierres grandes (>10K registros)
    pass


def _consolidar_secuencial(cierre_id):
    """Implementación secuencial (fallback)"""
    # Para debugging o cierres pequeños
    pass
```

#### **2.3 Incidencias** (TERCERO)

```python
# backend/nomina/tasks/incidencias.py

@shared_task(bind=True, queue='nomina_queue')
def generar_incidencias(self, cierre_id, tipo='simple'):
    """
    Genera incidencias para un cierre.
    
    Args:
        cierre_id: ID del CierreNomina
        tipo: 'simple' (umbral 30%) | 'avanzado' (comparación individual)
    """
    if tipo == 'simple':
        return _generar_simple(cierre_id)
    else:
        return _generar_avanzado(cierre_id)


def _generar_simple(cierre_id):
    """Umbral fijo 30% - rápido"""
    pass


def _generar_avanzado(cierre_id):
    """Comparación individual por empleado - preciso"""
    pass
```

### **Paso 3: Actualizar `tasks/__init__.py`**

```python
# backend/nomina/tasks/__init__.py

"""
Celery tasks para el módulo de nómina.

Estructura:
- libro_remuneraciones: Procesamiento de libros de remuneraciones
- movimientos_mes: Movimientos del mes
- consolidacion: Consolidación de datos
- incidencias: Generación de incidencias
- discrepancias: Análisis de discrepancias
"""

# Libro de Remuneraciones
from .libro_remuneraciones import (
    analizar_headers,
    clasificar_headers,
    procesar_empleados,
    procesar_registros,
)

# Movimientos del Mes
from .movimientos_mes import (
    procesar_movimientos,
)

# Consolidación
from .consolidacion import (
    consolidar_cierre,
    consolidar_empleados,
    consolidar_conceptos,
)

# Incidencias
from .incidencias import (
    generar_incidencias,
)

# Discrepancias
from .discrepancias import (
    generar_discrepancias,
)

__all__ = [
    # Libro
    'analizar_headers',
    'clasificar_headers',
    'procesar_empleados',
    'procesar_registros',
    # Movimientos
    'procesar_movimientos',
    # Consolidación
    'consolidar_cierre',
    'consolidar_empleados',
    'consolidar_conceptos',
    # Incidencias
    'generar_incidencias',
    # Discrepancias
    'generar_discrepancias',
]
```

### **Paso 4: Retrocompatibilidad en `tasks.py`**

```python
# backend/nomina/tasks.py

"""
⚠️ DEPRECATED: Este archivo se mantiene solo para retrocompatibilidad.
Nuevas tareas deben agregarse en nomina/tasks/

Las importaciones se hacen desde nomina.tasks.* directamente.
"""

# Importar todo desde el paquete tasks/
from .tasks import *  # noqa: F401, F403

# Este import permite que código legacy siga funcionando:
# from nomina.tasks import analizar_headers  # ✅ Funciona

# Advertencia en logs
import logging
logger = logging.getLogger(__name__)
logger.warning(
    "⚠️ Importando desde nomina.tasks (deprecated). "
    "Usa 'from nomina.tasks.libro_remuneraciones import analizar_headers' en su lugar."
)
```

### **Paso 5: Actualizar Views**

```python
# ANTES
from .tasks import analizar_headers_libro_remuneraciones_con_logging

# DESPUÉS
from .tasks.libro_remuneraciones import analizar_headers

# O si prefieres mantener compatibilidad:
from .tasks import analizar_headers  # Funciona por el __init__.py
```

---

## 🧪 Testing de la Migración

### **Verificar que Celery detecta las tareas**:

```bash
# Listar todas las tareas registradas
docker compose exec celery_worker celery -A sgm_backend inspect registered

# Debe aparecer:
# - nomina.tasks.libro_remuneraciones.analizar_headers
# - nomina.tasks.consolidacion.consolidar_cierre
# etc.
```

### **Test de importación**:

```python
# backend/test_imports_tasks.py

def test_imports_nuevos():
    """Verificar que los imports nuevos funcionan"""
    from nomina.tasks.libro_remuneraciones import analizar_headers
    from nomina.tasks.consolidacion import consolidar_cierre
    assert callable(analizar_headers)
    assert callable(consolidar_cierre)
    

def test_imports_legacy():
    """Verificar retrocompatibilidad"""
    from nomina.tasks import analizar_headers
    assert callable(analizar_headers)
```

---

## 📝 Convenciones de Código

### **Naming**:
- Tareas: `verbo_sustantivo()` → `analizar_headers()`, `consolidar_cierre()`
- No sufijos: `_task`, `_con_logging`, `_optimizado` (elegir UNA versión)
- Helpers privados: `_helper_name()` → `_consolidar_paralelo()`

### **Docstrings**:
```python
@shared_task(bind=True, queue='nomina_queue')
def analizar_headers(self, libro_id):
    """
    Breve descripción de una línea.
    
    Args:
        libro_id: Descripción del parámetro
    
    Returns:
        dict: Estructura del resultado
    
    Raises:
        Exception: Cuándo falla
    
    Example:
        >>> result = analizar_headers.delay(123)
        >>> result.get()
        {'libro_id': 123, 'headers': [...]}
    """
```

### **Logging consistente**:
```python
logger.info(f"[{DOMINIO}] Mensaje claro")
logger.error(f"[{DOMINIO}] Error: {e}", exc_info=True)

# Ejemplos:
# [LIBRO] Analizando headers libro 123
# [CONSOLIDACION] Iniciando modo=paralelo cierre=30
# [INCIDENCIAS] Generadas 5 incidencias para cierre 30
```

### **ActivityEvent siempre**:
```python
# Inicio de tarea
ActivityEvent.log(
    user=sistema_user(),
    cliente=cierre.cliente,
    cierre=cierre,
    event_type='process',
    action='operacion_iniciada',
    resource_type='tipo_recurso',
    resource_id=str(recurso_id),
    details={'task_id': self.request.id}
)

# Éxito
ActivityEvent.log(..., action='operacion_exitosa', details={'resultado': stats})

# Error
ActivityEvent.log(..., action='operacion_error', details={'error': str(e)})
```

---

## 🗑️ Código a Eliminar (Deprecation Plan)

### **Marcar como deprecated**:
```python
# backend/nomina/tasks/_deprecated.py

import warnings

@shared_task
def analizar_headers_libro_remuneraciones_con_logging(libro_id, upload_log_id):
    """
    ⚠️ DEPRECATED: Usar nomina.tasks.libro_remuneraciones.analizar_headers
    
    Esta tarea se eliminará en la versión 2.0.0
    """
    warnings.warn(
        "analizar_headers_libro_remuneraciones_con_logging está deprecated. "
        "Usa nomina.tasks.libro_remuneraciones.analizar_headers",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Redirigir a la nueva tarea
    from .libro_remuneraciones import analizar_headers
    return analizar_headers.delay(libro_id)
```

### **Timeline de eliminación**:
1. **Semana 1-2**: Migrar todas las llamadas en views
2. **Semana 3-4**: Marcar tareas antiguas como deprecated
3. **Mes 2**: Eliminar tareas deprecated si no hay uso

---

## 📊 Comparación Antes/Después

| Métrica | ANTES | DESPUÉS |
|---------|-------|---------|
| **Archivo principal** | 5,279 líneas | ~50 líneas (imports) |
| **Tareas totales** | 59 tareas | ~25 tareas (limpiado) |
| **Versiones duplicadas** | 3-4 por funcionalidad | 1 por funcionalidad |
| **Archivos** | 1 monolito | 7 módulos especializados |
| **Mantenibilidad** | ❌ Imposible | ✅ Alta |
| **Testeable** | ❌ Difícil | ✅ Fácil (por módulo) |
| **Onboarding** | 2 días | 2 horas |

---

## 🚀 Prioridades de Implementación

### **Prioridad 1 (CRÍTICO)**: Libro de Remuneraciones
- **Razón**: Es el flujo principal del sistema
- **Impacto**: Alto - se usa en cada cierre
- **Esfuerzo**: 3-4 horas
- **Archivos afectados**: 
  - `views_libro_remuneraciones.py`
  - Tests de libro

### **Prioridad 2 (IMPORTANTE)**: Consolidación
- **Razón**: Core business logic
- **Impacto**: Alto - afecta reportes
- **Esfuerzo**: 4-5 horas
- **Decisión clave**: ¿Qué modo es el default? (optimizado vs paralelo)

### **Prioridad 3 (MEDIO)**: Incidencias
- **Razón**: Feature complejo con múltiples versiones
- **Impacto**: Medio - solo para revisión
- **Esfuerzo**: 3-4 horas

### **Prioridad 4 (BAJO)**: Movimientos, Analista, Novedades
- **Razón**: Menos usados
- **Impacto**: Bajo
- **Esfuerzo**: 2 horas c/u

---

## ✅ Checklist de Refactorización

### **Planificación**:
- [ ] Mapear todas las tareas activas (grep en views)
- [ ] Identificar dependencias entre tareas
- [ ] Decidir qué versiones mantener (optimizado vs secuencial vs paralelo)
- [ ] Documentar código muerto

### **Implementación**:
- [ ] Crear estructura `nomina/tasks/`
- [ ] Migrar libro_remuneraciones.py (PRIMERO)
- [ ] Actualizar views para usar nuevos imports
- [ ] Verificar Celery detecta las tareas
- [ ] Tests de imports

### **Limpieza**:
- [ ] Mover código obsoleto a `_deprecated.py`
- [ ] Marcar tareas antiguas con warnings
- [ ] Eliminar versiones duplicadas
- [ ] Reducir `tasks.py` a solo imports

### **Validación**:
- [ ] Subir libro → Verificar task ejecuta
- [ ] Consolidar cierre → Verificar task ejecuta
- [ ] Generar incidencias → Verificar task ejecuta
- [ ] Revisar logs de Celery (sin errores)
- [ ] ActivityEvent registra eventos correctamente

---

## 🎯 Resultado Final Esperado

```bash
backend/nomina/tasks/
├── __init__.py                    # 50 líneas (exports)
├── libro_remuneraciones.py        # 400 líneas
├── movimientos_mes.py             # 150 líneas
├── archivos_analista.py           # 100 líneas
├── novedades.py                   # 300 líneas
├── consolidacion.py               # 500 líneas
├── incidencias.py                 # 300 líneas
├── discrepancias.py               # 200 líneas
└── _deprecated.py                 # 500 líneas (temporal)

Total: ~2,500 líneas (vs 5,279 original)
Reducción: 52% de código
```

**Beneficios**:
- ✅ Código limpio y organizado
- ✅ Fácil de mantener
- ✅ Fácil de testear
- ✅ Fácil de entender para nuevos devs
- ✅ Sin versiones duplicadas
- ✅ Logging consistente
- ✅ ActivityEvent integrado

---

## ⏱️ Estimación de Tiempo

| Fase | Tiempo | Descripción |
|------|--------|-------------|
| **Mapeo** | 2h | Analizar código actual |
| **Libro** | 4h | Migrar libro_remuneraciones.py |
| **Consolidación** | 5h | Migrar consolidacion.py |
| **Incidencias** | 4h | Migrar incidencias.py |
| **Resto** | 4h | Movimientos, analista, novedades |
| **Testing** | 3h | Verificar todo funciona |
| **Limpieza** | 2h | Deprecated y documentación |
| **TOTAL** | **24h** | ~3 días de trabajo |

---

## 🤔 Decisiones Pendientes

1. **¿Qué versión de consolidación es la "buena"?**
   - `optimizado` → Default
   - `paralelo` → Para cierres grandes
   - `secuencial` → Deprecated

2. **¿Eliminamos código muerto inmediatamente?**
   - Opción A: Mover a `_deprecated.py` con warnings
   - Opción B: Eliminar directamente (agresivo)
   - **Recomendación**: Opción A (más seguro)

3. **¿Cómo manejamos las versiones "con_logging"?**
   - **Solución**: TODAS las tareas nuevas tienen logging integrado
   - Eliminar sufijo `_con_logging`

4. **¿Tasks con sufijo `_task`?**
   - **Solución**: Eliminar sufijo (redundante)
   - `clasificar_headers_task()` → `clasificar_headers()`

---

## 🎯 ¿Empezamos?

**Propongo**:
1. **AHORA**: Mapear tareas activas (2h)
2. **HOY**: Migrar `libro_remuneraciones.py` (4h)
3. **MAÑANA**: Resto de módulos (8h)

**¿Confirmas el plan?** 🚀
