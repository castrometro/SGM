# ============================================================================
#                           ITEMS VIEWS
# ============================================================================
# Views para la gestión de items de nómina (haberes y descuentos)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Sum, Count, Avg
from django.urls import reverse_lazy
from django.utils import timezone

from ..models import Item_Cierre, Item_Empleado, CierrePayroll, Empleados_Cierre


class ItemCierreListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de items del cierre
    """
    model = Item_Cierre
    template_name = 'payroll/items/list.html'
    context_object_name = 'items'
    paginate_by = 30
    
    def get_queryset(self):
        cierre_id = self.kwargs.get('cierre_id')
        queryset = Item_Cierre.objects.filter(
            cierre_payroll_id=cierre_id
        ).select_related('cierre_payroll')
        
        # Filtros
        tipo_item = self.request.GET.get('tipo')
        if tipo_item:
            queryset = queryset.filter(tipo_item=tipo_item)
            
        es_imponible = self.request.GET.get('imponible')
        if es_imponible:
            queryset = queryset.filter(es_imponible=es_imponible == 'true')
            
        es_variable = self.request.GET.get('variable')
        if es_variable:
            queryset = queryset.filter(es_variable=es_variable == 'true')
            
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(codigo_item__icontains=search) |
                Q(nombre_item__icontains=search)
            )
            
        return queryset.order_by('tipo_item', 'codigo_item')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cierre_id = self.kwargs.get('cierre_id')
        context['cierre'] = get_object_or_404(CierrePayroll, pk=cierre_id)
        
        # Estadísticas
        items = Item_Cierre.objects.filter(cierre_payroll_id=cierre_id)
        context['stats'] = {
            'total_items': items.count(),
            'haberes': items.filter(tipo_item='haberes').count(),
            'descuentos': items.filter(tipo_item='descuentos').count(),
            'imponibles': items.filter(es_imponible=True).count(),
            'variables': items.filter(es_variable=True).count(),
        }
        
        return context


class ItemEmpleadoListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de items por empleado
    """
    model = Item_Empleado
    template_name = 'payroll/items/empleado_items.html'
    context_object_name = 'items_empleado'
    paginate_by = 50
    
    def get_queryset(self):
        empleado_cierre_id = self.kwargs.get('empleado_cierre_id')
        return Item_Empleado.objects.filter(
            empleado_cierre_id=empleado_cierre_id
        ).select_related('item_cierre', 'empleado_cierre__empleado')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empleado_cierre_id = self.kwargs.get('empleado_cierre_id')
        context['empleado_cierre'] = get_object_or_404(Empleados_Cierre, pk=empleado_cierre_id)
        
        # Totales
        items = self.get_queryset()
        haberes = items.filter(item_cierre__tipo_item='haberes')
        descuentos = items.filter(item_cierre__tipo_item='descuentos')
        
        context['totales'] = {
            'haberes': haberes.aggregate(Sum('monto'))['monto__sum'] or 0,
            'descuentos': descuentos.aggregate(Sum('monto'))['monto__sum'] or 0,
        }
        context['totales']['liquido'] = context['totales']['haberes'] - context['totales']['descuentos']
        
        # Separar por tipo
        context['haberes'] = haberes
        context['descuentos'] = descuentos
        
        return context


class ItemCierreCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo item en el cierre
    """
    model = Item_Cierre
    template_name = 'payroll/items/create.html'
    fields = [
        'codigo_item', 'nombre_item', 'tipo_item', 
        'es_imponible', 'es_variable', 'orden_calculo'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        self.cierre = get_object_or_404(CierrePayroll, pk=kwargs['cierre_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.cierre_payroll = self.cierre
        
        messages.success(self.request, f'Item {form.instance.nombre_item} creado exitosamente')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('payroll:items_list', kwargs={'cierre_id': self.cierre.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cierre'] = self.cierre
        return context


@login_required
def aplicar_item_masivo(request, cierre_id):
    """
    Vista para aplicar un item a múltiples empleados
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        monto = request.POST.get('monto')
        empleados_ids = request.POST.getlist('empleados_ids')
        
        if not all([item_id, monto, empleados_ids]):
            messages.error(request, 'Debe completar todos los campos')
            return redirect('payroll:items_list', cierre_id=cierre_id)
        
        try:
            item = Item_Cierre.objects.get(id=item_id, cierre_payroll=cierre)
            monto = float(monto)
            
            items_creados = 0
            
            for emp_id in empleados_ids:
                try:
                    empleado_cierre = Empleados_Cierre.objects.get(
                        id=emp_id, 
                        cierre_payroll=cierre
                    )
                    
                    # Crear o actualizar item_empleado
                    item_empleado, created = Item_Empleado.objects.get_or_create(
                        empleado_cierre=empleado_cierre,
                        item_cierre=item,
                        defaults={'monto': monto}
                    )
                    
                    if not created:
                        item_empleado.monto = monto
                        item_empleado.save()
                    
                    items_creados += 1
                    
                except Exception as e:
                    continue
            
            messages.success(
                request, 
                f'Item {item.nombre_item} aplicado a {items_creados} empleados'
            )
            
        except Exception as e:
            messages.error(request, f'Error al aplicar item masivo: {str(e)}')
    
    return redirect('payroll:items_list', cierre_id=cierre_id)


@login_required
def calcular_item_variable(request, item_id):
    """
    Vista AJAX para calcular montos de items variables
    """
    item = get_object_or_404(Item_Cierre, pk=item_id)
    
    if not item.es_variable:
        return JsonResponse({
            'success': False,
            'error': 'Este item no es variable'
        })
    
    try:
        # Lógica de cálculo según el tipo de item variable
        # Por ejemplo, horas extras, comisiones, etc.
        
        items_empleado = Item_Empleado.objects.filter(item_cierre=item)
        total_calculado = 0
        empleados_afectados = 0
        
        for item_emp in items_empleado:
            # Aquí iría la lógica específica de cálculo
            # Por ahora, ejemplo simple
            if item.codigo_item == 'HE001':  # Horas extras
                # Calcular basado en horas extras del empleado
                monto_calculado = item_emp.empleado_cierre.horas_extras * 5000  # Ejemplo
                item_emp.monto = monto_calculado
                item_emp.save()
                
                total_calculado += monto_calculado
                empleados_afectados += 1
        
        return JsonResponse({
            'success': True,
            'total_calculado': float(total_calculado),
            'empleados_afectados': empleados_afectados,
            'item_nombre': item.nombre_item
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def resumen_items_por_tipo(request, cierre_id):
    """
    Vista para obtener resumen de items agrupados por tipo
    """
    cierre = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    # Resumen de items por tipo
    resumen_items = Item_Cierre.objects.filter(
        cierre_payroll=cierre
    ).values('tipo_item').annotate(
        total_items=Count('id'),
        items_imponibles=Count('id', filter=Q(es_imponible=True)),
        items_variables=Count('id', filter=Q(es_variable=True))
    )
    
    # Resumen de montos por tipo
    resumen_montos = Item_Empleado.objects.filter(
        empleado_cierre__cierre_payroll=cierre
    ).values('item_cierre__tipo_item').annotate(
        total_monto=Sum('monto'),
        promedio_monto=Avg('monto'),
        empleados_con_item=Count('empleado_cierre', distinct=True)
    )
    
    return JsonResponse({
        'resumen_items': list(resumen_items),
        'resumen_montos': list(resumen_montos),
        'cierre_info': {
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
        }
    })


@login_required
def validar_items_empleado(request, empleado_cierre_id):
    """
    Vista para validar los items de un empleado específico
    """
    empleado_cierre = get_object_or_404(Empleados_Cierre, pk=empleado_cierre_id)
    
    try:
        items = Item_Empleado.objects.filter(empleado_cierre=empleado_cierre)
        
        validaciones = {
            'items_sin_monto': [],
            'items_negativos': [],
            'items_duplicados': [],
            'total_haberes': 0,
            'total_descuentos': 0,
            'liquido_calculado': 0,
        }
        
        # Validaciones
        for item in items:
            if not item.monto or item.monto == 0:
                validaciones['items_sin_monto'].append(item.item_cierre.nombre_item)
            
            if item.monto and item.monto < 0:
                validaciones['items_negativos'].append(item.item_cierre.nombre_item)
            
            # Sumar totales
            if item.item_cierre.tipo_item == 'haberes':
                validaciones['total_haberes'] += item.monto or 0
            else:
                validaciones['total_descuentos'] += item.monto or 0
        
        validaciones['liquido_calculado'] = validaciones['total_haberes'] - validaciones['total_descuentos']
        
        # Verificar duplicados
        codigos_items = items.values_list('item_cierre__codigo_item', flat=True)
        duplicados = [codigo for codigo in set(codigos_items) if list(codigos_items).count(codigo) > 1]
        
        for codigo in duplicados:
            item_duplicado = Item_Cierre.objects.get(codigo_item=codigo, cierre_payroll=empleado_cierre.cierre_payroll)
            validaciones['items_duplicados'].append(item_duplicado.nombre_item)
        
        # Determinar si hay errores
        tiene_errores = any([
            validaciones['items_sin_monto'],
            validaciones['items_negativos'],
            validaciones['items_duplicados']
        ])
        
        return JsonResponse({
            'success': True,
            'validaciones': validaciones,
            'tiene_errores': tiene_errores,
            'empleado': {
                'nombre': f"{empleado_cierre.empleado.nombre} {empleado_cierre.empleado.apellido}",
                'rut': empleado_cierre.empleado.rut
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def copiar_items_desde_cierre(request, cierre_id):
    """
    Vista para copiar items desde otro cierre
    """
    cierre_destino = get_object_or_404(CierrePayroll, pk=cierre_id)
    
    if request.method == 'POST':
        cierre_origen_id = request.POST.get('cierre_origen_id')
        
        if not cierre_origen_id:
            messages.error(request, 'Debe seleccionar un cierre origen')
            return redirect('payroll:items_list', cierre_id=cierre_id)
        
        try:
            cierre_origen = CierrePayroll.objects.get(id=cierre_origen_id)
            items_origen = Item_Cierre.objects.filter(cierre_payroll=cierre_origen)
            
            items_copiados = 0
            
            for item in items_origen:
                # Crear nuevo item en el cierre destino
                Item_Cierre.objects.get_or_create(
                    cierre_payroll=cierre_destino,
                    codigo_item=item.codigo_item,
                    defaults={
                        'nombre_item': item.nombre_item,
                        'tipo_item': item.tipo_item,
                        'es_imponible': item.es_imponible,
                        'es_variable': item.es_variable,
                        'orden_calculo': item.orden_calculo,
                    }
                )
                items_copiados += 1
            
            messages.success(
                request, 
                f'{items_copiados} items copiados desde {cierre_origen.cliente.nombre} - {cierre_origen.periodo}'
            )
            
        except Exception as e:
            messages.error(request, f'Error al copiar items: {str(e)}')
    
    return redirect('payroll:items_list', cierre_id=cierre_id)
