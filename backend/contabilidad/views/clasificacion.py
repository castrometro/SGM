from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import ClasificacionCuentaArchivo
from ..serializers import ClasificacionCuentaArchivoSerializer


class ClasificacionCuentaArchivoViewSet(viewsets.ModelViewSet):
    queryset = ClasificacionCuentaArchivo.objects.all()
    serializer_class = ClasificacionCuentaArchivoSerializer
    permission_classes = [IsAuthenticated]


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cargar_clasificacion_bulk(request):
    return Response({"detail": "not implemented"})
