# backend/contabilidad/views/analisis.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import AnalisisCuentaCierre
from ..serializers import AnalisisCuentaCierreSerializer


class AnalisisCuentaCierreViewSet(viewsets.ModelViewSet):
    queryset = AnalisisCuentaCierre.objects.all()
    serializer_class = AnalisisCuentaCierreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get("cierre")
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.order_by("-fecha_creacion")
