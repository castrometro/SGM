from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import (
    CuentaContable,
    AperturaCuenta,
    MovimientoContable,
    CentroCosto,
    Auxiliar,
)
from ..serializers import (
    CuentaContableSerializer,
    AperturaCuentaSerializer,
    MovimientoContableSerializer,
    CentroCostoSerializer,
    AuxiliarSerializer,
)


class CuentaContableViewSet(viewsets.ModelViewSet):
    queryset = CuentaContable.objects.all()
    serializer_class = CuentaContableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        if cliente:
            qs = qs.filter(cliente=cliente)
        return qs.order_by("codigo")


class AperturaCuentaViewSet(viewsets.ModelViewSet):
    queryset = AperturaCuenta.objects.all()
    serializer_class = AperturaCuentaSerializer
    permission_classes = [IsAuthenticated]


class MovimientoContableViewSet(viewsets.ModelViewSet):
    queryset = MovimientoContable.objects.all()
    serializer_class = MovimientoContableSerializer
    permission_classes = [IsAuthenticated]


class CentroCostoViewSet(viewsets.ModelViewSet):
    queryset = CentroCosto.objects.all()
    serializer_class = CentroCostoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.order_by("nombre")


class AuxiliarViewSet(viewsets.ModelViewSet):
    queryset = Auxiliar.objects.all()
    serializer_class = AuxiliarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by("nombre")
