"""
🔄 TASKS - PROXY TO REFACTORED TASKS

Este archivo actúa como proxy/wrapper hacia tasks_refactored/
para mantener compatibilidad con imports existentes.

Fecha de transición: 24 de octubre de 2025
Estado: SMOKE TEST - Probando qué falta refactorizar
"""

# ===================================================================
# RE-EXPORTS desde tasks_refactored/
# ===================================================================

# 1. LIBRO DE REMUNERACIONES
from .tasks_refactored.libro_remuneraciones import (
    analizar_headers_libro_remuneraciones_con_logging,
    clasificar_headers_libro_remuneraciones_con_logging,
    actualizar_empleados_desde_libro_optimizado,
    guardar_registros_nomina_optimizado,
    # build_informe_libro,  # ⚠️ NO EXISTE en refactored aún
)

# Aliases para compatibilidad
analizar_headers_libro_remuneraciones = analizar_headers_libro_remuneraciones_con_logging
clasificar_headers_libro_remuneraciones_task = clasificar_headers_libro_remuneraciones_con_logging
actualizar_empleados_desde_libro = actualizar_empleados_desde_libro_optimizado
guardar_registros_nomina = guardar_registros_nomina_optimizado


# 2. CONSOLIDACIÓN
from .tasks_refactored.consolidacion import (
    consolidar_datos_nomina_task_optimizado,
    consolidar_datos_nomina_con_logging,
)

# Alias
consolidar_datos_nomina_task = consolidar_datos_nomina_con_logging


# 3. NOVEDADES
from .tasks_refactored.novedades import (
    procesar_archivo_novedades_con_logging,
    actualizar_empleados_desde_novedades_task_optimizado,
    guardar_registros_novedades_task_optimizado,
)

# Aliases
procesar_archivo_novedades = procesar_archivo_novedades_con_logging
actualizar_empleados_desde_novedades_task = actualizar_empleados_desde_novedades_task_optimizado
guardar_registros_novedades_task = guardar_registros_novedades_task_optimizado


# 4. MOVIMIENTOS
from .tasks_refactored.movimientos_mes import procesar_movimientos_mes_con_logging

# Alias
procesar_movimientos_mes = procesar_movimientos_mes_con_logging


# 5. INCIDENCIAS
from .tasks_refactored.incidencias import generar_incidencias_con_logging

# Aliases
generar_incidencias_cierre_paralelo = generar_incidencias_con_logging
generar_incidencias_cierre_task = generar_incidencias_con_logging


# 6. DISCREPANCIAS
from .tasks_refactored.discrepancias import generar_discrepancias_cierre_con_logging

# Aliases
generar_discrepancias_cierre_paralelo = generar_discrepancias_cierre_con_logging
generar_discrepancias_task = generar_discrepancias_cierre_con_logging


# 7. ARCHIVOS ANALISTA
from .tasks_refactored.archivos_analista import procesar_archivo_analista_util

# Alias
procesar_archivo_analista = procesar_archivo_analista_util


# 8. INFORMES Y FINALIZACIÓN
from .tasks_refactored.informes import (
    build_informe_libro,
    build_informe_movimientos,
    unir_y_guardar_informe,
    enviar_informe_redis_task,
    finalizar_cierre_post_informe,
    calcular_kpis_cierre,
)


# ===================================================================
# STUBS PARA FUNCIONES NO REFACTORIZADAS
# ===================================================================

def generar_incidencias_totales_simple(cierre_id):
    raise NotImplementedError("Función no refactorizada aún - ver tasks.py.original línea ~63")


def consolidar_cierre_task(cierre_id, usuario_id=None):
    raise NotImplementedError("Función no refactorizada aún - ver tasks.py.original línea ~2188")


def generar_incidencias_consolidadas_task(cierre_id):
    raise NotImplementedError("Función no refactorizada aún - ver tasks.py.original línea ~2230")


def analizar_datos_cierre_task(cierre_id, tolerancia_variacion=30.0):
    raise NotImplementedError("Función no refactorizada aún - ver tasks.py.original línea ~1907")


print("✅ tasks.py (SMOKE TEST MODE) cargado correctamente")
