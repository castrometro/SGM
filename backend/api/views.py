# api/views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework_simplejwt.views import TokenObtainPairView


from .permissions import IsGerenteOrSelfOrReadOnly

from .models import Cliente, Contrato, Usuario, Industria, Area, Servicio, ServicioCliente, AsignacionClienteUsuario

from .serializers import (
    ClienteSerializer, ContratoSerializer,
    UsuarioSerializer, IndustriaSerializer,
    AreaSerializer, ServicioSerializer, ServicioClienteSerializer,
    AsignacionClienteUsuarioSerializer, CustomTokenObtainPairSerializer,
    ServicioClienteMiniSerializer, AnalistaPerformanceSerializer,
    AnalistaDetalladoSerializer, DashboardDataSerializer, 
    EstadisticasAnalistaSerializer, ClienteSimpleSerializer
)
from .permissions import (
    IsAuthenticatedAndActive, IsGerente, IsSupervisor, IsAnalista,
    ClienteAccess, ContratoAccess
)
from django.db.models import Count, Q, Avg, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ping(request):
    return Response({"pong": True, "usuario": str(request.user)})


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticatedAndActive & (IsGerente | IsSupervisor)]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="me")
    def me(self, request):
        """Devuelve los datos del usuario autenticado."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticatedAndActive, ClienteAccess]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.tipo_usuario == 'analista':
            asignados = AsignacionClienteUsuario.objects.filter(
                usuario=self.request.user
            ).values_list('cliente_id', flat=True)
            return qs.filter(pk__in=asignados)
        return qs
    
    @action(detail=False, methods=["get"], url_path="asignados")
    def asignados(self, request):
        asignados = AsignacionClienteUsuario.objects.filter(usuario=request.user)
        ids = asignados.values_list("cliente_id", flat=True)
        clientes = Cliente.objects.filter(id__in=ids)
        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="servicios", permission_classes=[IsAuthenticated])
    def servicios(self, request, pk=None):
        cliente = self.get_object()
        contratos = Contrato.objects.filter(cliente=cliente)
        serializer = ContratoSerializer(contratos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='servicios-area', permission_classes=[IsAuthenticated])
    def servicios_area(self, request, pk=None):
        cliente = self.get_object()
        user_area_ids = request.user.areas.values_list("id", flat=True)

        # Obtener los IDs de servicios de esas áreas
        servicio_ids = Servicio.objects.filter(area_id__in=user_area_ids).values_list("id", flat=True)

        # Obtener los servicios contratados del cliente que pertenezcan a esas áreas
        servicios = ServicioCliente.objects.filter(
            cliente=cliente,
            servicio_id__in=servicio_ids
        ).select_related('servicio', 'servicio__area')

        serializer = ServicioClienteMiniSerializer(servicios, many=True)
        return Response(serializer.data)

        

class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticatedAndActive, ContratoAccess]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.tipo_usuario == 'analista':
            asignados = AsignacionClienteUsuario.objects.filter(
                usuario=self.request.user
            ).values_list('cliente_id', flat=True)
            return qs.filter(cliente_id__in=asignados)
        return qs

class IndustriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Industria.objects.all()
    serializer_class = IndustriaSerializer
    permission_classes = [IsAuthenticatedAndActive]

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticatedAndActive & IsGerente]

class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [IsAuthenticatedAndActive]

class ServicioClienteViewSet(viewsets.ModelViewSet):
    queryset = ServicioCliente.objects.all()
    serializer_class = ServicioClienteSerializer
    permission_classes = [IsAuthenticatedAndActive]

class AsignacionClienteUsuarioViewSet(viewsets.ModelViewSet):
    queryset = AsignacionClienteUsuario.objects.select_related('cliente','usuario')
    serializer_class = AsignacionClienteUsuarioSerializer
    permission_classes = [IsAuthenticated, IsGerenteOrSelfOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        # superusuario ve todo
        if user.is_superuser:
            return qs
        # gerente ve sólo las asignaciones de usuarios de sus mismas áreas
        if user.tipo_usuario == 'gerente':
            return qs.filter(usuario__areas__in=user.areas.all()).distinct()
        # supervisor ve sólo sus propias asignaciones
        if user.tipo_usuario == 'supervisor':
            return qs.filter(usuario=user)
        # analista ve sólo sus propias asignaciones, read-only
        return qs.filter(usuario=user)
        
    def perform_create(self, serializer):
        """Validar que el cliente no esté ya asignado a otro analista en las mismas áreas"""
        cliente = serializer.validated_data['cliente']
        usuario_asignado = serializer.validated_data['usuario']
        
        # Obtener las áreas del usuario que se está asignando
        areas_usuario = list(usuario_asignado.areas.all())
        
        # Verificar si ya existe algún analista asignado al cliente en las mismas áreas
        asignaciones_existentes = AsignacionClienteUsuario.objects.filter(
            cliente=cliente,
            usuario__areas__in=areas_usuario
        ).exclude(usuario=usuario_asignado).select_related('usuario').prefetch_related('usuario__areas')
        
        # Verificar conflictos por área
        for asignacion in asignaciones_existentes:
            areas_conflicto = set(areas_usuario) & set(asignacion.usuario.areas.all())
            if areas_conflicto:
                areas_nombres = ', '.join([area.nombre for area in areas_conflicto])
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'cliente': f'Este cliente ya está asignado a {asignacion.usuario.nombre} {asignacion.usuario.apellido} en el área: {areas_nombres}'
                })
        
        serializer.save()


class AnalistaPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AnalistaPerformanceSerializer
    permission_classes = [IsAuthenticatedAndActive & IsGerente]

    def get_queryset(self):
        gerente = self.request.user
        areas = gerente.areas.all()
        return (
            Usuario.objects.filter(tipo_usuario='analista', areas__in=areas)
            .distinct()
            .annotate(
                clientes_asignados=Count('asignaciones', distinct=True),
                cierres_contabilidad=Count(
                    'cierrecontabilidad',
                    filter=Q(cierrecontabilidad__area__in=areas),
                    distinct=True,
                ),
                cierres_nomina=Count('cierres_analista', distinct=True),
            )
        )


class DashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """Dashboard ejecutivo con KPIs y métricas"""
    permission_classes = [IsAuthenticatedAndActive & IsGerente]
    
    def list(self, request):
        periodo = request.query_params.get('periodo', 'current_month')
        
        # Calcular fechas según el período
        now = timezone.now()
        if periodo == 'current_month':
            start_date = now.replace(day=1)
            end_date = now
        elif periodo == 'last_month':
            first_day_current = now.replace(day=1)
            start_date = (first_day_current - timedelta(days=1)).replace(day=1)
            end_date = first_day_current - timedelta(days=1)
        elif periodo == 'quarter':
            quarter_start = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start, day=1)
            end_date = now
        else:  # year
            start_date = now.replace(month=1, day=1)
            end_date = now
        
        gerente = request.user
        areas = gerente.areas.all()
        
        # Verificar qué áreas maneja el gerente para adaptar los KPIs
        tiene_contabilidad = areas.filter(nombre='Contabilidad').exists()
        tiene_nomina = areas.filter(nombre='Nomina').exists()
        
        # KPIs principales
        total_analistas = Usuario.objects.filter(
            tipo_usuario='analista', 
            areas__in=areas
        ).distinct().count()
        
        clientes_activos = Cliente.objects.filter(
            asignaciones__usuario__areas__in=areas
        ).distinct().count()
        
        # Importar modelos de cierres
        from contabilidad.models import CierreContabilidad
        from nomina.models import CierreNomina
        
        # Cierres por área específica
        cierres_contabilidad = 0
        cierres_nomina = 0
        
        if tiene_contabilidad:
            cierres_contabilidad = CierreContabilidad.objects.filter(
                area__in=areas.filter(nombre='Contabilidad'),
                fecha_creacion__range=[start_date, end_date],
                estado__in=['aprobado', 'completo']
            ).count()
        
        if tiene_nomina:
            cierres_nomina = CierreNomina.objects.filter(
                fecha_creacion__range=[start_date, end_date],
                estado='completado'
            ).count()
        
        total_cierres = cierres_contabilidad + cierres_nomina
        
        # Performance de analistas
        analistas_queryset = Usuario.objects.filter(
            tipo_usuario='analista', 
            areas__in=areas
        ).distinct().annotate(
            clientes_asignados=Count('asignaciones', distinct=True),
            cierres_completados=Count('cierrecontabilidad', 
                filter=Q(cierrecontabilidad__estado__in=['aprobado', 'completo']),
                distinct=True
            ) + Count('cierres_analista',
                filter=Q(cierres_analista__estado='completado'),
                distinct=True
            ),
            cierres_contabilidad=Count('cierrecontabilidad',
                filter=Q(cierrecontabilidad__area__in=areas),
                distinct=True
            ),
            cierres_nomina=Count('cierres_analista', distinct=True)
        ).annotate(
            eficiencia=F('cierres_completados') * 100.0 / (F('clientes_asignados') + 1),
            carga_trabajo=F('clientes_asignados') * 10.0  # Simplificado
        ).prefetch_related('areas')
        
        # Convertir a lista de diccionarios serializables
        analistas_performance = []
        for analista in analistas_queryset[:10]:
            analistas_performance.append({
                'id': analista.id,
                'nombre': analista.nombre,
                'apellido': analista.apellido,
                'correo_bdo': analista.correo_bdo,
                'clientes_asignados': analista.clientes_asignados,
                'cierres_completados': analista.cierres_completados,
                'cierres_contabilidad': analista.cierres_contabilidad,
                'cierres_nomina': analista.cierres_nomina,
                'eficiencia': round(float(analista.eficiencia or 0), 1),
                'carga_trabajo': round(float(analista.carga_trabajo or 0), 1),
                'areas': [{'id': area.id, 'nombre': area.nombre} for area in analista.areas.all()]
            })
        
        # Estados de cierres específicos por área
        cierres_por_estado = {}
        
        if tiene_contabilidad:
            estados_contabilidad = CierreContabilidad.objects.filter(
                area__in=areas.filter(nombre='Contabilidad'),
                fecha_creacion__range=[start_date, end_date]
            ).values('estado').annotate(count=Count('id'))
            
            for item in estados_contabilidad:
                cierres_por_estado[f"{item['estado']}_contabilidad"] = item['count']
        
        if tiene_nomina:
            estados_nomina = CierreNomina.objects.filter(
                fecha_creacion__range=[start_date, end_date]
            ).values('estado').annotate(count=Count('id'))
            
            for item in estados_nomina:
                cierres_por_estado[f"{item['estado']}_nomina"] = item['count']
        
        # Clientes por industria
        clientes_por_industria_raw = Cliente.objects.filter(
            asignaciones__usuario__areas__in=areas
        ).values('industria__nombre').annotate(
            count=Count('id', distinct=True)
        ).order_by('-count')[:5]
        
        # Convertir a formato serializable y manejar valores nulos
        clientes_por_industria = []
        for item in clientes_por_industria_raw:
            clientes_por_industria.append({
                'nombre': item['industria__nombre'] or 'Sin Industria',
                'count': item['count']
            })
        
        # Ingresos por servicio (simplificado)
        ingresos_por_servicio = []
        for area in areas:
            servicios = ServicioCliente.objects.filter(
                servicio__area=area
            ).aggregate(
                total=Sum('valor'),
                clientes=Count('cliente', distinct=True)
            )
            if servicios['total']:
                ingresos_por_servicio.append({
                    'area': area.nombre,
                    'total_ingresos': float(servicios['total']),
                    'clientes': servicios['clientes']
                })
        
        # Tendencia de cierres (últimos 6 meses) - simplificado
        tendencia_cierres = []
        for i in range(6):
            days_back = 30 * i
            month_end = now - timedelta(days=days_back)
            month_start = now - timedelta(days=days_back + 30)
            
            month_cierres = CierreContabilidad.objects.filter(
                area__in=areas,
                fecha_creacion__range=[month_start, month_end]
            ).count() + CierreNomina.objects.filter(
                fecha_creacion__range=[month_start, month_end]
            ).count()
            
            tendencia_cierres.append({
                'periodo': month_end.strftime('%m/%y'),
                'total': month_cierres
            })
        
        tendencia_cierres.reverse()
        
        # Alertas de cierres retrasados específicos por área
        fecha_limite = now - timedelta(days=30)
        cierres_retrasados = 0
        
        if tiene_contabilidad:
            cierres_retrasados += CierreContabilidad.objects.filter(
                area__in=areas.filter(nombre='Contabilidad'),
                fecha_creacion__lt=fecha_limite,
                estado__in=['pendiente', 'procesando', 'clasificacion']
            ).count()
        
        if tiene_nomina:
            cierres_retrasados += CierreNomina.objects.filter(
                fecha_creacion__lt=fecha_limite,
                estado__in=['pendiente', 'en_proceso', 'datos_consolidados']
            ).count()
        
        # Calcular eficiencia promedio solo de analistas con clientes asignados
        analistas_con_datos = [a for a in analistas_performance if a['clientes_asignados'] > 0]
        if analistas_con_datos:
            eficiencia_promedio = sum(a['eficiencia'] for a in analistas_con_datos) / len(analistas_con_datos)
        else:
            eficiencia_promedio = 0
        
        data = {
            'areas_gerente': {
                'tiene_contabilidad': tiene_contabilidad,
                'tiene_nomina': tiene_nomina,
                'areas': [{'id': area.id, 'nombre': area.nombre} for area in areas]
            },
            'kpis': {
                'total_analistas': total_analistas,
                'clientes_activos': clientes_activos,
                'cierres_completados': total_cierres,
                'cierres_contabilidad': cierres_contabilidad if tiene_contabilidad else None,
                'cierres_nomina': cierres_nomina if tiene_nomina else None,
                'eficiencia_promedio': round(eficiencia_promedio, 1)
            },
            'analistas_performance': analistas_performance,
            'cierres_por_estado': cierres_por_estado,
            'clientes_por_industria': clientes_por_industria,
            'ingresos_por_servicio': ingresos_por_servicio,
            'tendencia_cierres': tendencia_cierres,
            'alerta_cierres_retrasados': {
                'count': cierres_retrasados
            }
        }
        
        return Response(data)


class AnalistasDetalladoViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista detallada de analistas para gestión"""
    serializer_class = AnalistaDetalladoSerializer
    permission_classes = [IsAuthenticatedAndActive & IsGerente]
    
    def get_queryset(self):
        gerente = self.request.user
        areas = gerente.areas.all()
        
        return Usuario.objects.filter(
            tipo_usuario='analista', 
            areas__in=areas
        ).distinct().annotate(
            clientes_asignados=Count('asignaciones', distinct=True),
            cierres_completados=Count('cierrecontabilidad', 
                filter=Q(cierrecontabilidad__estado__in=['aprobado', 'completo']),
                distinct=True
            ) + Count('cierres_analista',
                filter=Q(cierres_analista__estado='completado'),
                distinct=True
            ),
            cierres_contabilidad=Count('cierrecontabilidad',
                filter=Q(cierrecontabilidad__area__in=areas),
                distinct=True
            ),
            cierres_nomina=Count('cierres_analista', distinct=True)
        ).annotate(
            eficiencia=F('cierres_completados') * 100.0 / (F('clientes_asignados') + 1),
            carga_trabajo=F('clientes_asignados') * 10.0
        ).prefetch_related('areas')
    
    @action(detail=True, methods=['get'], url_path='estadisticas')
    def estadisticas(self, request, pk=None):
        """Estadísticas detalladas de un analista específico"""
        analista = self.get_object()
        
        from contabilidad.models import CierreContabilidad
        from nomina.models import CierreNomina
        
        # Cierres por estado
        cierres_contabilidad = CierreContabilidad.objects.filter(
            usuario=analista
        ).values('estado').annotate(count=Count('id'))
        
        cierres_nomina = CierreNomina.objects.filter(
            usuario_analista=analista
        ).values('estado').annotate(count=Count('id'))
        
        cierres_por_estado = {}
        for item in cierres_contabilidad:
            cierres_por_estado[item['estado']] = item['count']
        for item in cierres_nomina:
            cierres_por_estado[item['estado']] = cierres_por_estado.get(item['estado'], 0) + item['count']
        
        # Clientes asignados
        clientes = Cliente.objects.filter(asignaciones__usuario=analista)
        
        # Métricas de performance
        total_cierres = sum(cierres_por_estado.values())
        completados = cierres_por_estado.get('completo', 0) + cierres_por_estado.get('completado', 0) + cierres_por_estado.get('aprobado', 0)
        eficiencia = (completados / total_cierres * 100) if total_cierres > 0 else 0
        
        # Tiempo promedio (simplificado)
        tiempo_promedio = 15.5  # Placeholder
        
        data = {
            'cierres_completados': completados,
            'eficiencia': round(eficiencia, 1),
            'tiempo_promedio_dias': tiempo_promedio,
            'cierres_por_estado': cierres_por_estado,
            'clientes': clientes
        }
        
        serializer = EstadisticasAnalistaSerializer(data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def clientes_disponibles(request, analista_id):
    """Obtener clientes que no tienen analista asignado en las áreas del gerente"""
    try:
        analista = Usuario.objects.get(id=analista_id, tipo_usuario='analista')
        gerente = request.user
        areas_gerente = gerente.areas.all()
        areas_analista = analista.areas.all()
        
        # Obtener IDs de áreas comunes entre gerente y analista
        areas_gerente_ids = list(areas_gerente.values_list('id', flat=True))
        areas_analista_ids = list(areas_analista.values_list('id', flat=True))
        areas_comunes_ids = list(set(areas_gerente_ids) & set(areas_analista_ids))
        
        if not areas_comunes_ids:
            # No hay áreas en común, no hay clientes disponibles
            return Response([])
        
        # Clientes que tienen servicios contratados en las áreas comunes
        from .models import ServicioCliente, Servicio
        clientes_con_servicios_area = Cliente.objects.filter(
            servicios_contratados__servicio__area_id__in=areas_comunes_ids
        ).distinct()
        
        # 1. Excluir clientes que YA ESTÁN asignados a este analista
        clientes_ya_asignados_a_analista = AsignacionClienteUsuario.objects.filter(
            usuario=analista
        ).values_list('cliente_id', flat=True)
        
        # 2. Excluir clientes que ya tienen analista asignado en alguna de las áreas comunes (pero de otros analistas)
        clientes_ocupados_en_areas = []
        for cliente in clientes_con_servicios_area.exclude(id__in=clientes_ya_asignados_a_analista):
            asignaciones_existentes = AsignacionClienteUsuario.objects.filter(
                cliente=cliente,
                usuario__areas__id__in=areas_comunes_ids
            ).exclude(usuario=analista).prefetch_related('usuario__areas')
            
            if asignaciones_existentes.exists():
                # Verificar si hay conflicto de áreas
                for asignacion in asignaciones_existentes:
                    areas_asignado_ids = list(asignacion.usuario.areas.values_list('id', flat=True))
                    if set(areas_comunes_ids) & set(areas_asignado_ids):
                        clientes_ocupados_en_areas.append(cliente.id)
                        break
        
        # Obtener lista final de clientes disponibles
        clientes_excluidos = list(clientes_ya_asignados_a_analista) + clientes_ocupados_en_areas
        disponibles = clientes_con_servicios_area.exclude(id__in=clientes_excluidos)
        
        serializer = ClienteSimpleSerializer(disponibles, many=True)
        return Response(serializer.data)
        
    except Usuario.DoesNotExist:
        return Response({'error': 'Analista no encontrado'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def clientes_asignados(request, analista_id):
    """Obtener clientes asignados a un analista específico"""
    try:
        analista = Usuario.objects.get(id=analista_id, tipo_usuario='analista')
        
        asignaciones = AsignacionClienteUsuario.objects.filter(
            usuario=analista
        ).select_related('cliente')
        
        clientes = [asig.cliente for asig in asignaciones]
        
        serializer = ClienteSimpleSerializer(clientes, many=True)
        return Response(serializer.data)
        
    except Usuario.DoesNotExist:
        return Response({'error': 'Analista no encontrado'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def remover_asignacion(request, analista_id, cliente_id):
    """Remover asignación cliente-analista"""
    try:
        asignacion = AsignacionClienteUsuario.objects.get(
            usuario_id=analista_id,
            cliente_id=cliente_id
        )
        asignacion.delete()
        return Response({'success': True})
        
    except AsignacionClienteUsuario.DoesNotExist:
        return Response({'error': 'Asignación no encontrada'}, status=404)
