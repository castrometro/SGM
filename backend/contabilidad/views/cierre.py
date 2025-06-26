from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    CierreContabilidad,
    MovimientoContable,
    AperturaCuenta,
    AccountClassification,
)
from ..serializers import CierreContabilidadSerializer


class CierreContabilidadViewSet(viewsets.ModelViewSet):
    queryset = CierreContabilidad.objects.all()
    serializer_class = CierreContabilidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        periodo = self.request.query_params.get("periodo")

        if cliente:
            qs = qs.filter(cliente_id=cliente)
        if periodo:
            qs = qs.filter(periodo=periodo)

        return qs.order_by("-fecha_creacion")

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario actual al crear un nuevo cierre
        """
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["get"])
    def movimientos_resumen(self, request, pk=None):
        cierre = self.get_object()
        set_id = request.query_params.get("set_id")
        opcion_id = request.query_params.get("opcion_id")
        movimientos = MovimientoContable.objects.filter(cierre=cierre)
        if set_id and opcion_id:
            cuentas = AccountClassification.objects.filter(
                set_clas_id=set_id, opcion_id=opcion_id
            ).values_list("cuenta_id", flat=True)
            movimientos = movimientos.filter(cuenta_id__in=cuentas)
        totales = (
            movimientos.values("cuenta_id")
            .annotate(total_debe=Sum("debe"), total_haber=Sum("haber"))
            .order_by("cuenta_id")
        )
        aperturas = AperturaCuenta.objects.filter(cierre=cierre).values(
            "cuenta_id", "saldo_anterior"
        )
        mapa = {a["cuenta_id"]: a["saldo_anterior"] for a in aperturas}
        data = []
        for t in totales:
            saldo_final = (mapa.get(t["cuenta_id"], 0) + t["total_debe"] - t["total_haber"])
            data.append({
                "cuenta_id": t["cuenta_id"],
                "total_debe": t["total_debe"],
                "total_haber": t["total_haber"],
                "saldo_final": saldo_final,
            })
        return Response(data)
