# ============================================================================
#                           EMPLEADOS CIERRE VIEWS
# ============================================================================
# Views para la gestión de empleados en el cierre de nómina

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Sum, Count
from django.urls import reverse_lazy
from django.utils import timezone

from ..models import Empleados_Cierre, CierrePayroll, Item_Empleado
from api.models import Usuario  # Cambiado de Empleado a Usuario


class EmpleadosCierreListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de empleados en un cierre específico
    """
    model = Empleados_Cierre
    template_name = 'payroll/empleados/list.html'
    context_object_name = 'empleados_cierre'
    paginate_by = 50
    
    def get_queryset(self):
        cierre_id = self.kwargs.get('cierre_id')
        queryset = Empleados_Cierre.objects.filter(
            cierre_payroll_id=cierre_id
        ).select_related('empleado', 'cierre_payroll')
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado_procesamiento=estado)
            
        departamento = self.request.GET.get('departamento')
        if departamento:
            queryset = queryset.filter(empleado__departamento__icontains=departamento)
            
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(empleado__rut__icontains=search) |
                Q(empleado__nombre__icontains=search) |
                Q(empleado__apellido__icontains=search)
            )
            
        return queryset.order_by('empleado__apellido', 'empleado__nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cierre_id = self.kwargs.get('cierre_id')
        context['cierre'] = get_object_or_404(CierrePayroll, pk=cierre_id)
        
        # Estadísticas
        empleados_cierre = Empleados_Cierre.objects.filter(cierre_payroll_id=cierre_id)
        context['stats'] = {
            'total': empleados_cierre.count(),
            'procesados': empleados_cierre.filter(estado_procesamiento='procesado').count(),
            'pendientes': empleados_cierre.filter(estado_procesamiento='pendiente').count(),
            'con_errores': empleados_cierre.filter(estado_procesamiento='error').count(),
            'total_liquido': empleados_cierre.aggregate(Sum('liquido_pagar'))['liquido_pagar__sum'] or 0,
        }
        
        return context


class EmpleadosCierreDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detalle de un empleado específico en el cierre
    """
    model = Empleados_Cierre
    template_name = 'payroll/empleados/detail.html'
    context_object_name = 'empleado_cierre'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empleado_cierre = self.get_object()
        
        # Items del empleado
        context['items'] = Item_Empleado.objects.filter(
            empleado_cierre=empleado_cierre
        ).select_related('item_cierre')
        
        # Separar haberes y descuentos
        context['haberes'] = context['items'].filter(item_cierre__tipo_item='haberes')
        context['descuentos'] = context['items'].filter(item_cierre__tipo_item='descuentos')
        
        # Totales
        context['total_haberes'] = context['haberes'].aggregate(Sum('monto'))['monto__sum'] or 0
        context['total_descuentos'] = context['descuentos'].aggregate(Sum('monto'))['monto__sum'] or 0
        context['liquido_calculado'] = context['total_haberes'] - context['total_descuentos']
        
        return context


class EmpleadosCierreCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para agregar empleados a un cierre
    """
    model = Empleados_Cierre
    template_name = 'payroll/empleados/create.html'
    fields = ['empleado', 'dias_trabajados', 'horas_extras', 'observaciones']
    
    def dispatch(self, request, *args, **kwargs):
        self.cierre = get_object_or_404(CierrePayroll, pk=kwargs['cierre_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.cierre_payroll = self.cierre
        form.instance.estado_procesamiento = 'pendiente'
        
        messages.success(self.request, f'Empleado {form.instance.empleado} agregado al cierre')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('payroll:empleados_list', kwargs={'cierre_id': self.cierre.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cierre'] = self.cierre
        
        # Empleados disponibles (que no estén ya en el cierre)
        empleados_en_cierre = Empleados_Cierre.objects.filter(
            cierre_payroll=self.cierre
        ).values_list('empleado_id', flat=True)
        
        context['empleados_disponibles'] = Usuario.objects.exclude(
            id__in=empleados_en_cierre
        )
        
        return context


@login_required
def calcular_liquido_empleado(request, pk):
    """
    Vista AJAX para calcular el líquido a pagar de un empleado
    """
    empleado_cierre = get_object_or_404(Empleados_Cierre, pk=pk)
    
    try:
        # Obtener todos los items del empleado
        items = Item_Empleado.objects.filter(empleado_cierre=empleado_cierre)
        
        total_haberes = items.filter(
            item_cierre__tipo_item='haberes'
        ).aggregate(Sum('monto'))['monto__sum'] or 0
        
        total_descuentos = items.filter(
            item_cierre__tipo_item='descuentos'
        ).aggregate(Sum('monto'))['monto__sum'] or 0
        
        liquido = total_haberes - total_descuentos
        
        # Actualizar el empleado_cierre
        empleado_cierre.liquido_pagar = liquido
        empleado_cierre.save()
        
        return JsonResponse({
            'success': True,
            'total_haberes': float(total_haberes),
            'total_descuentos': float(total_descuentos),
            'liquido_pagar': float(liquido)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def procesar_empleado_individual(request, pk):
    """
    Vista para procesar un empleado individual
    """
    empleado_cierre = get_object_or_404(Empleados_Cierre, pk=pk)
    
    if request.method == 'POST':
        try:
            # Lógica de procesamiento individual
            empleado_cierre.estado_procesamiento = 'procesando'
            empleado_cierre.save()
            
            # Calcular líquido
            calcular_liquido_empleado(request, pk)
            
            # Validaciones adicionales aquí
            # ...
            
            empleado_cierre.estado_procesamiento = 'procesado'
            empleado_cierre.fecha_procesamiento = timezone.now()
            empleado_cierre.save()
            
            messages.success(request, f'Empleado {empleado_cierre.empleado} procesado exitosamente')
            
        except Exception as e:
            empleado_cierre.estado_procesamiento = 'error'
            empleado_cierre.observaciones_procesamiento = str(e)
            empleado_cierre.save()
            
            messages.error(request, f'Error al procesar empleado: {str(e)}')
    
    return redirect('payroll:empleado_detail', pk=pk)


@login_required
def exportar_empleados_excel(request, cierre_id):
    """
    Vista para exportar lista de empleados a Excel
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    empleados = Empleados_Cierre.objects.filter(
        cierre_payroll=cierre
    ).select_related('empleado')
    
    # Aquí iría la lógica de exportación con openpyxl o similar
    # Por ahora retornamos un JSON
    
    data = []
    for emp_cierre in empleados:
        data.append({
            'rut': emp_cierre.empleado.rut,
            'nombre': f"{emp_cierre.empleado.nombre} {emp_cierre.empleado.apellido}",
            'dias_trabajados': emp_cierre.dias_trabajados,
            'horas_extras': emp_cierre.horas_extras,
            'liquido_pagar': float(emp_cierre.liquido_pagar or 0),
            'estado': emp_cierre.estado_procesamiento,
        })
    
    return JsonResponse({
        'empleados': data,
        'total': len(data),
        'cierre': {
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
        }
    })


@login_required
def resumen_empleados_por_departamento(request, cierre_id):
    """
    Vista para obtener resumen de empleados agrupados por departamento
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    # Agrupar por departamento
    from django.db.models import Case, When, Value, CharField
    
    resumen = Empleados_Cierre.objects.filter(
        cierre_payroll=cierre
    ).values(
        'empleado__departamento'
    ).annotate(
        total_empleados=Count('id'),
        total_liquido=Sum('liquido_pagar'),
        procesados=Count(Case(
            When(estado_procesamiento='procesado', then=Value(1)),
            output_field=CharField()
        )),
        pendientes=Count(Case(
            When(estado_procesamiento='pendiente', then=Value(1)),
            output_field=CharField()
        ))
    )
    
    return JsonResponse({
        'resumen': list(resumen),
        'cierre_info': {
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
        }
    })


# ============================================================================
#                           VISTAS MASIVAS
# ============================================================================

@login_required
def procesar_empleados_masivo(request, cierre_id):
    """
    Vista para procesar múltiples empleados de forma masiva
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    if request.method == 'POST':
        empleados_ids = request.POST.getlist('empleados_ids')
        
        if not empleados_ids:
            messages.error(request, 'Debe seleccionar al menos un empleado')
            return redirect('payroll:empleados_list', cierre_id=cierre_id)
        
        try:
            empleados_procesados = 0
            empleados_con_error = 0
            
            for emp_id in empleados_ids:
                try:
                    empleado_cierre = Empleados_Cierre.objects.get(
                        id=emp_id, 
                        cierre_payroll=cierre
                    )
                    
                    # Procesar empleado individual
                    empleado_cierre.estado_procesamiento = 'procesado'
                    empleado_cierre.fecha_procesamiento = timezone.now()
                    empleado_cierre.save()
                    
                    empleados_procesados += 1
                    
                except Exception as e:
                    empleados_con_error += 1
            
            messages.success(
                request, 
                f'Procesamiento masivo completado: {empleados_procesados} exitosos, {empleados_con_error} con errores'
            )
            
        except Exception as e:
            messages.error(request, f'Error en procesamiento masivo: {str(e)}')
    
    return redirect('payroll:empleados_list', cierre_id=cierre_id)
