# Importar todas las vistas para que estén disponibles
from .views_cierre import CierrePayrollViewSet
from .views_archivo import ArchivoSubidoViewSet, verificar_existencia_archivo
from .views_clientes import (
    clientes_asignados_payroll, 
    clientes_por_area_payroll, 
    todos_clientes_payroll,
    resumen_cliente_payroll
)# Hacer que estén disponibles cuando se importe el paquete views
__all__ = [
    'CierrePayrollViewSet',
    'ArchivoSubidoViewSet',
    'verificar_existencia_archivo',
    'clientes_asignados_payroll',
    'clientes_por_area_payroll',
    'todos_clientes_payroll',
    'resumen_cliente_payroll'
]
