"""
🔄 Tareas Celery Refactorizadas - Módulo Nomina

Este paquete contiene las tareas Celery organizadas por dominio funcional.
Solo incluye las tareas que se usan activamente en las views.

IMPORTANTE:
-----------
- El archivo nomina/tasks.py ORIGINAL se mantiene intacto para views legacy
- Las views dedicadas (views_libro_remuneraciones.py, views_movimientos_mes.py, etc.) importan desde este paquete
- Ejemplo: from .tasks_refactored.libro_remuneraciones import analizar_headers_con_logging

Estructura:
-----------
- libro_remuneraciones.py: Procesamiento de libros Excel (6 tareas + 4 helpers)
- movimientos_mes.py: Procesamiento de movimientos del mes (1 tarea principal)
- archivos_analista.py: Procesamiento de archivos del analista (1 tarea, 3 tipos: finiquitos, incidencias, ingresos)
- novedades.py: Procesamiento de novedades (11 tareas: 3 principales + 6 optimizadas + 2 consolidación)
- discrepancias.py: Verificación de datos y generación de discrepancias (1 tarea principal)
- consolidacion.py: Consolidación de datos con dual logging (1 tarea principal)
- incidencias.py: Generación de incidencias con dual logging (1 tarea principal)

Autor: Sistema SGM
Fecha: 20 de octubre de 2025
Versión: 2.6.0 (Refactorizado - Added Incidencias)
"""

# ============================================================================
# LIBRO DE REMUNERACIONES (6 tareas + 4 helpers)
# ============================================================================

from .libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
    # Helper tasks (Celery las necesita registradas)
    procesar_chunk_empleados_task,
    procesar_chunk_registros_task,
    consolidar_empleados_task,
    consolidar_registros_task,
)

# ============================================================================
# MOVIMIENTOS MES (1 tarea principal)
# ============================================================================

from .movimientos_mes import (
    procesar_movimientos_mes_con_logging,
)

# ============================================================================
# ARCHIVOS ANALISTA (1 tarea principal - 3 tipos de archivo)
# ============================================================================

from .archivos_analista import (
    procesar_archivo_analista_con_logging,
)

# ============================================================================
# NOVEDADES (11 tareas: 3 análisis + 2 finales + 2 optimizadas + 4 paralelo)
# ============================================================================

from .novedades import (
    # Punto de entrada principal (no es @shared_task)
    procesar_archivo_novedades_con_logging,
    # Tareas de análisis y clasificación (chain)
    analizar_headers_archivo_novedades,
    clasificar_headers_archivo_novedades_task,
    # Tareas finales simples
    actualizar_empleados_desde_novedades_task,
    guardar_registros_novedades_task,
    # Tareas optimizadas (chord paralelo)
    actualizar_empleados_desde_novedades_task_optimizado,
    guardar_registros_novedades_task_optimizado,
    # Tareas de procesamiento paralelo en chunks
    procesar_chunk_empleados_novedades_task,
    procesar_chunk_registros_novedades_task,
    # Tareas de consolidación
    consolidar_empleados_novedades_task,
    finalizar_procesamiento_novedades_task,
)

# ============================================================================
# DISCREPANCIAS (1 tarea principal)
# ============================================================================

from .discrepancias import (
    generar_discrepancias_cierre_con_logging,
)

# ============================================================================
# CONSOLIDACIÓN (1 tarea principal)
# ============================================================================

from .consolidacion import (
    consolidar_datos_nomina_con_logging,
)

# ============================================================================
# INCIDENCIAS (1 tarea principal)
# ============================================================================

from .incidencias import (
    generar_incidencias_con_logging,
)

# ============================================================================
# EXPORTACIONES
# ============================================================================

__all__ = [
    # Libro de Remuneraciones (10 tareas: 6 principales + 4 helpers)
    'analizar_headers_libro_remuneraciones_con_logging',
    'clasificar_headers_libro_remuneraciones_con_logging',
    'actualizar_empleados_desde_libro',
    'guardar_registros_nomina',
    'actualizar_empleados_desde_libro_optimizado',
    'guardar_registros_nomina_optimizado',
    'procesar_chunk_empleados_task',
    'procesar_chunk_registros_task',
    'consolidar_empleados_task',
    'consolidar_registros_task',
    # Movimientos Mes (1 tarea principal)
    'procesar_movimientos_mes_con_logging',
    # Archivos Analista (1 tarea principal - 3 tipos)
    'procesar_archivo_analista_con_logging',
    # Novedades (11 tareas)
    'procesar_archivo_novedades_con_logging',
    'analizar_headers_archivo_novedades',
    'clasificar_headers_archivo_novedades_task',
    'actualizar_empleados_desde_novedades_task',
    'guardar_registros_novedades_task',
    'actualizar_empleados_desde_novedades_task_optimizado',
    'guardar_registros_novedades_task_optimizado',
    'procesar_chunk_empleados_novedades_task',
    'procesar_chunk_registros_novedades_task',
    'consolidar_empleados_novedades_task',
    'finalizar_procesamiento_novedades_task',
    # Discrepancias (1 tarea principal)
    'generar_discrepancias_cierre_con_logging',
    # Consolidación (1 tarea principal)
    'consolidar_datos_nomina_con_logging',
    # Incidencias (1 tarea principal)
    'generar_incidencias_con_logging',
]

# ============================================================================
# METADATA
# ============================================================================

__version__ = '2.6.0'
__author__ = 'Sistema SGM'
__status__ = 'Production'

# Estado de migración
TAREAS_MIGRADAS = {
    'libro_remuneraciones': True,   # ✅ 10 tareas (6 principales + 4 helpers)
    'movimientos_mes': True,        # ✅ 1 tarea principal
    'archivos_analista': True,      # ✅ 1 tarea principal (3 tipos: finiquitos, incidencias, ingresos)
    'novedades': True,              # ✅ 11 tareas (3 análisis + 2 finales + 2 optimizadas + 4 paralelo)
    'discrepancias': True,          # ✅ 1 tarea principal (verificación de datos)
    'consolidacion': True,          # ✅ 1 tarea principal (consolidación con dual logging)
    'incidencias': True,            # ✅ 1 tarea principal (generación de incidencias con dual logging)
    'informes': False,              # ⏳ Pendiente
}


def get_migration_status():
    """Retorna el estado de migración de cada módulo"""
    total = len(TAREAS_MIGRADAS)
    migradas = sum(1 for v in TAREAS_MIGRADAS.values() if v)
    porcentaje = (migradas / total) * 100
    
    return {
        'total_modulos': total,
        'modulos_migrados': migradas,
        'porcentaje': f'{porcentaje:.1f}%',
        'detalle': TAREAS_MIGRADAS
    }
