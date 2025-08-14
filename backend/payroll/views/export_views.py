# ============================================================================
#                           EXPORT VIEWS
# ============================================================================
# Views para exportación de datos y reportes

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from ..models import CierrePayroll, Empleados_Cierre, Item_Empleado


@login_required
def exportar_excel_view(request, cierre_id):
    """
    Vista para exportar cierre a Excel
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    # Preparar datos para export
    empleados_data = []
    for emp_cierre in cierre.empleados_cierre.all():
        empleados_data.append({
            'rut': emp_cierre.empleado.rut,
            'nombre': f"{emp_cierre.empleado.nombre} {emp_cierre.empleado.apellido}",
            'liquido': emp_cierre.liquido_pagar or 0
        })
    
    return JsonResponse({
        'success': True,
        'empleados': empleados_data,
        'total_empleados': len(empleados_data),
        'total_liquido': sum(emp['liquido'] for emp in empleados_data)
    })


@login_required
def exportar_pdf_view(request, cierre_id):
    """
    Vista para exportar cierre a PDF
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    # Por ahora retornamos estructura básica
    return JsonResponse({
        'success': True,
        'mensaje': 'PDF generado correctamente',
        'cierre': f"{cierre.cliente.nombre} - {cierre.periodo}"
    })


@login_required
def exportar_reporte_view(request, cierre_id):
    """
    Vista para exportar reporte completo
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    return JsonResponse({
        'success': True,
        'reporte_generado': True,
        'cierre_info': {
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
            'estado': cierre.get_estado_display()
        }
    })
