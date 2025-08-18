# ============================================================================
#                           CIERRE PAYROLL VIEWS
# ============================================================================
# Views para la gestión principal del cierre de nómina
# Incluye CRUD completo y operaciones específicas del workflow

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import CierrePayroll, Empleados_Cierre, Logs_Actividad
from api.models import Cliente
# from ..utils.cierre_utils import CierreProcessor, CierreValidator
# from ..utils.excel_parser import ExcelParser
# from ..serializers.cierre_serializers import CierrePayrollSerializer


class CierrePayrollListView(LoginRequiredMixin, ListView):
    """
    Vista de lista de todos los cierres de payroll
    Con filtros, búsqueda y paginación
    """
    model = CierrePayroll
    template_name = 'payroll/cierre/list.html'
    context_object_name = 'cierres'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CierrePayroll.objects.select_related('cliente', 'usuario_responsable')
        
        # Filtros
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        periodo = self.request.GET.get('periodo')
        if periodo:
            queryset = queryset.filter(periodo__icontains=periodo)
            
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(periodo__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(observaciones__icontains=search)
            )
            
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all()
        context['estados'] = CierrePayroll.ESTADOS_CHOICES
        
        # Estadísticas rápidas
        context['stats'] = {
            'total': CierrePayroll.objects.count(),
            'pendientes': CierrePayroll.objects.filter(estado='pendiente').count(),
            'en_proceso': CierrePayroll.objects.filter(estado='procesando').count(),
            'completados': CierrePayroll.objects.filter(estado='completado').count(),
        }
        
        return context


class CierrePayrollDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detalle de un cierre específico
    Muestra toda la información y permite operaciones
    """
    model = CierrePayroll
    template_name = 'payroll/cierre/detail.html'
    context_object_name = 'cierre'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cierre = self.get_object()
        
        # Datos relacionados
        context['empleados'] = cierre.empleados_cierre.select_related('empleado')
        context['items'] = cierre.item_cierre.all()
        context['finiquitos'] = cierre.finiquitos_cierre.all()
        context['incidencias'] = cierre.incidencias_cierre.filter(estado='abierta')
        context['logs'] = cierre.logs_actividad.all()[:10]  # Últimos 10 logs
        
        # Estadísticas del cierre
        context['stats'] = {
            'total_empleados': cierre.empleados_cierre.count(),
            'total_items': cierre.item_cierre.count(),
            'incidencias_abiertas': cierre.incidencias_cierre.filter(estado='abierta').count(),
            'progreso': cierre.get_progreso_porcentaje(),
        }
        
        # Archivos
        context['archivos'] = {
            'excel_original': cierre.archivo_excel_original,
            'excel_procesado': cierre.archivo_excel_procesado,
            'pdf_comparacion': cierre.archivo_pdf_comparacion,
        }
        
        return context


class CierrePayrollCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo cierre de payroll
    """
    model = CierrePayroll
    template_name = 'payroll/cierre/create.html'
    fields = ['cliente', 'periodo', 'tipo_cierre', 'observaciones']
    success_url = reverse_lazy('payroll:cierre_list')
    
    def form_valid(self, form):
        form.instance.usuario_responsable = self.request.user
        form.instance.estado = 'pendiente'
        
        # Crear log de creación
        response = super().form_valid(form)
        
        Logs_Actividad.objects.create(
            cierre_payroll=self.object,
            usuario=self.request.user,
            accion='creacion',
            descripcion=f'Cierre creado para {self.object.cliente.nombre} - {self.object.periodo}',
            resultado='exitoso'
        )
        
        messages.success(self.request, f'Cierre creado exitosamente para {self.object.cliente.nombre}')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all()
        return context


class CierrePayrollUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un cierre existente
    """
    model = CierrePayroll
    template_name = 'payroll/cierre/edit.html'
    fields = ['cliente', 'periodo', 'tipo_cierre', 'estado', 'observaciones']
    
    def get_success_url(self):
        return reverse_lazy('payroll:cierre_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Crear log de actualización
        Logs_Actividad.objects.create(
            cierre_payroll=self.object,
            usuario=self.request.user,
            accion='actualizacion',
            descripcion=f'Cierre actualizado: {", ".join([f"{field}: {form.cleaned_data[field]}" for field in form.changed_data])}',
            resultado='exitoso'
        )
        
        messages.success(self.request, 'Cierre actualizado exitosamente')
        return super().form_valid(form)


@login_required
def procesar_cierre_view(request, pk):
    """
    Vista para iniciar el procesamiento de un cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=pk)
    
    if cierre.estado != 'pendiente':
        messages.error(request, 'Este cierre ya está siendo procesado o está completado')
        return redirect('payroll:cierre_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # Cambiar estado a procesando
            cierre.estado = 'procesando'
            cierre.fecha_inicio_procesamiento = timezone.now()
            cierre.save()
            
            # Log de inicio de procesamiento
            Logs_Actividad.objects.create(
                cierre_payroll=cierre,
                usuario=request.user,
                accion='inicio_procesamiento',
                descripcion='Iniciado procesamiento del cierre',
                resultado='exitoso'
            )
            
            # Aquí iría la lógica de procesamiento asíncrono
            # Por ejemplo, con Celery
            # process_cierre_task.delay(cierre.id)
            
            messages.success(request, 'Procesamiento iniciado exitosamente')
            
        except Exception as e:
            Logs_Actividad.objects.create(
                cierre_payroll=cierre,
                usuario=request.user,
                accion='inicio_procesamiento',
                descripcion=f'Error al iniciar procesamiento: {str(e)}',
                resultado='error'
            )
            messages.error(request, f'Error al iniciar procesamiento: {str(e)}')
    
    return redirect('payroll:cierre_detail', pk=pk)


@login_required
def upload_excel_view(request, pk):
    """
    Vista para subir archivo Excel al cierre
    """
    cierre = get_object_or_404(CierrePayroll, pk=pk)
    
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            excel_file = request.FILES['excel_file']
            
            # Validar archivo
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Por favor sube un archivo Excel válido (.xlsx o .xls)')
                return redirect('payroll:cierre_detail', pk=pk)
            
            # Guardar archivo
            cierre.archivo_excel_original = excel_file
            cierre.save()
            
            # Log de carga
            Logs_Actividad.objects.create(
                cierre_payroll=cierre,
                usuario=request.user,
                accion='carga_archivo',
                descripcion=f'Archivo Excel cargado: {excel_file.name}',
                resultado='exitoso'
            )
            
            messages.success(request, 'Archivo Excel cargado exitosamente')
            
        except Exception as e:
            Logs_Actividad.objects.create(
                cierre_payroll=cierre,
                usuario=request.user,
                accion='carga_archivo',
                descripcion=f'Error al cargar archivo: {str(e)}',
                resultado='error'
            )
            messages.error(request, f'Error al cargar archivo: {str(e)}')
    
    return redirect('payroll:cierre_detail', pk=pk)


# ============================================================================
#                           API VIEWS
# ============================================================================
# API views para integración REST

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_cierre_mensual_payroll(request, cliente_id):
    """
    API para crear un nuevo cierre mensual de payroll
    """
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        periodo = request.data.get('periodo')
        
        if not periodo:
            return Response({'error': 'Periodo es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya existe un cierre para este periodo
        cierre_existente = CierrePayroll.objects.filter(
            cliente=cliente,
            periodo=periodo
        ).first()
        
        if cierre_existente:
            return Response({
                'error': 'Ya existe un cierre para este periodo',
                'cierre_id': cierre_existente.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear el nuevo cierre
        cierre = CierrePayroll.objects.create(
            cliente=cliente,
            periodo=periodo,
            estado='pendiente',
            usuario=request.user
        )
        
        # Por ahora omitir el log hasta identificar el problema
        # Logs_Actividad.objects.create(
        #     cierre_payroll=cierre,
        #     usuario=request.user,
        #     accion='creacion_cierre',
        #     resultado='exito',
        #     detalles=f'Cierre creado para {cliente.nombre} - {periodo}'
        # )
        
        return Response({
            'id': cierre.id,
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut
            },
            'fecha_creacion': cierre.fecha_creacion.isoformat(),
            'usuario_responsable': request.user.correo_bdo
        }, status=status.HTTP_201_CREATED)
        
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_cierre_mensual_payroll(request, cliente_id, periodo):
    """
    API para obtener un cierre específico por periodo
    """
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        cierre = CierrePayroll.objects.filter(
            cliente=cliente,
            periodo=periodo
        ).first()
        
        if not cierre:
            return Response({'error': 'Cierre no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id': cierre.id,
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'fecha_creacion': cierre.fecha_creacion,
            'fecha_finalizacion': cierre.fecha_completado,
            'usuario_responsable': cierre.usuario.correo_bdo if cierre.usuario else None,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut
            }
        })
        
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cierres_cliente_payroll(request, cliente_id):
    """
    Obtiene la lista de cierres de payroll para un cliente específico
    """
    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Obtener todos los cierres del cliente ordenados por fecha de creación (más reciente primero)
        cierres = CierrePayroll.objects.filter(
            cliente=cliente
        ).order_by('-fecha_creacion')
        
        # Serializar los datos para la respuesta
        cierres_data = []
        for cierre in cierres:
            cierres_data.append({
                'id': cierre.id,
                'periodo': cierre.periodo,
                'estado': cierre.estado,
                'fecha_creacion': cierre.fecha_creacion.isoformat(),
                'fecha_finalizacion': cierre.fecha_completado.isoformat() if cierre.fecha_completado else None,
                'total_empleados': cierre.total_empleados or 0,
                'usuario_responsable': cierre.usuario.correo_bdo if cierre.usuario else None,
                'observaciones': '',  # Campo no disponible en el modelo actual
                # Agregar estadísticas básicas
                'puede_finalizar': cierre.estado in ['sin_incidencias', 'procesado'],
                'en_proceso': cierre.estado in ['procesando', 'generando_reportes']
            })
        
        return Response({
            'count': len(cierres_data),
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut
            },
            'results': cierres_data
        })
        
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
#                           VIEWSETS COMENTADOS
# ============================================================================
# ViewSets más complejos para futuras implementaciones


# class CierrePayrollViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet para API REST de CierrePayroll
#     """
#     queryset = CierrePayroll.objects.all()
#     serializer_class = CierrePayrollSerializer
#     permission_classes = [IsAuthenticated]
#     
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         
#         # Filtros via query params
#         cliente = self.request.query_params.get('cliente', None)
#         if cliente:
#             queryset = queryset.filter(cliente=cliente)
#             
#         estado = self.request.query_params.get('estado', None)
#         if estado:
#             queryset = queryset.filter(estado=estado)
#             
#         return queryset.select_related('cliente', 'usuario_responsable')
#     
#     @action(detail=True, methods=['post'])
#     def procesar(self, request, pk=None):
#         """
#         Endpoint para iniciar procesamiento de un cierre
#         """
#         cierre = self.get_object()
#         
#         if cierre.estado != 'pendiente':
#             return Response(
#                 {'error': 'El cierre no está en estado pendiente'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         
#         try:
#             cierre.estado = 'procesando'
#             cierre.fecha_inicio_procesamiento = timezone.now()
#             cierre.save()
#             
#             # Log
#             Logs_Actividad.objects.create(
#                 cierre_payroll=cierre,
#                 usuario=request.user,
#                 accion='inicio_procesamiento',
#                 descripcion='Procesamiento iniciado via API',
#                 resultado='exitoso'
#             )
#             
#             return Response({'message': 'Procesamiento iniciado'})
#             
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#     
#     @action(detail=True, methods=['get'])
#     def estadisticas(self, request, pk=None):
#         """
#         Endpoint para obtener estadísticas del cierre
#         """
#         cierre = self.get_object()
#         
#         stats = {
#             'empleados_total': cierre.empleados_cierre.count(),
#             'items_total': cierre.item_cierre.count(),
#             'incidencias_abiertas': cierre.incidencias_cierre.filter(estado='abierta').count(),
#             'progreso_porcentaje': cierre.get_progreso_porcentaje(),
#             'tiempo_procesamiento': cierre.get_tiempo_procesamiento(),
#         }
#         
#         return Response(stats)
