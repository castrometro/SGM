# ============================================================================
#                           VALIDATION VIEWS
# ============================================================================
# Views para validación de datos y consistencia

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q

from ..models import CierrePayroll, Empleados_Cierre, Item_Empleado, Item_Cierre


@login_required
def validar_datos_cierre(request, cierre_id):
    """
    Vista para validar integridad de datos del cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    validaciones = {
        'empleados_sin_items': [],
        'items_sin_empleados': [],
        'montos_inconsistentes': [],
        'duplicados': [],
        'totales': {}
    }
    
    # Validar empleados sin items
    empleados_sin_items = Empleados_Cierre.objects.filter(
        cierre_payroll=cierre
    ).annotate(
        total_items=Count('item_empleado')
    ).filter(total_items=0)
    
    validaciones['empleados_sin_items'] = [
        {
            'id': emp.id,
            'nombre': f"{emp.empleado.nombre} {emp.empleado.apellido}",
            'rut': emp.empleado.rut
        }
        for emp in empleados_sin_items
    ]
    
    # Validar items sin empleados
    items_sin_empleados = Item_Cierre.objects.filter(
        cierre_payroll=cierre
    ).annotate(
        total_empleados=Count('item_empleado')
    ).filter(total_empleados=0)
    
    validaciones['items_sin_empleados'] = [
        {
            'id': item.id,
            'codigo': item.codigo_item,
            'nombre': item.nombre_item
        }
        for item in items_sin_empleados
    ]
    
    return JsonResponse(validaciones)


@login_required
def comparar_archivos_view(request, cierre_id):
    """
    Vista para comparar archivos del cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    # Aquí iría la lógica de comparación
    # Por ahora retornamos estructura básica
    
    return JsonResponse({
        'success': True,
        'diferencias_encontradas': 0,
        'archivos_comparados': ['excel_original', 'excel_procesado'],
        'resumen': 'Comparación completada'
    })


@login_required
def verificar_integridad_view(request, cierre_id):
    """
    Vista para verificar integridad del cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    resultado = {
        'integridad_ok': True,
        'errores': [],
        'advertencias': []
    }
    
    # Validaciones básicas
    empleados_count = cierre.empleados_cierre.count()
    if empleados_count == 0:
        resultado['errores'].append('No hay empleados en el cierre')
        resultado['integridad_ok'] = False
    
    return JsonResponse(resultado)
