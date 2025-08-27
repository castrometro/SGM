# backend/payroll/tasks/__init__.py
# Exportar tasks principales para el sistema de payroll

from .libro_remuneraciones import (
    procesar_libro_remuneraciones,
    extraer_headers_task,
    extraer_empleados_task,
    extraer_valores_task
)

__all__ = [
    'procesar_libro_remuneraciones',
    'extraer_headers_task',
    'extraer_empleados_task',
    'extraer_valores_task'
]