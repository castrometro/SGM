# backend/payroll/tasks/__init__.py
# Exportar tasks principales para el sistema de payroll

from .libro_remuneraciones import (
    procesar_libro_remuneraciones,
    extraer_headers_task,
    extraer_empleados_task,
    extraer_valores_task
)

from .movimientos_mes import (
    procesar_movimientos_mes,
    validar_archivo_movimientos,
    procesar_altas_bajas,
    procesar_ausentismo,
    finalizar_procesamiento_movimientos
)

from .archivos_analista import (
    procesar_finiquitos_analista,
    procesar_ausentismos_analista,
    procesar_ingresos_analista
)

__all__ = [
    # Libro de remuneraciones
    'procesar_libro_remuneraciones',
    'extraer_headers_task',
    'extraer_empleados_task',
    'extraer_valores_task',
    
    # Movimientos del mes
    'procesar_movimientos_mes',
    'validar_archivo_movimientos',
    'procesar_altas_bajas',
    'procesar_ausentismo',
    'finalizar_procesamiento_movimientos',
    
    # Archivos del analista
    'procesar_finiquitos_analista',
    'procesar_ausentismos_analista',
    'procesar_ingresos_analista'
]