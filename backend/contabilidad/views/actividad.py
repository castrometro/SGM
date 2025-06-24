from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import TarjetaActivityLog
from ..serializers import TarjetaActivityLogSerializer


class TarjetaActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TarjetaActivityLog.objects.all()
    serializer_class = TarjetaActivityLogSerializer
    permission_classes = [IsAuthenticated]
