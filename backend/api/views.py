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
)
from .permissions import (
    IsAuthenticatedAndActive, IsGerente, IsSupervisor, IsAnalista,
    ClienteAccess, ContratoAccess
)
from django.db.models import Count, Q

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
