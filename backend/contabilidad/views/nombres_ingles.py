from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import NombreIngles
from ..serializers import NombreInglesSerializer
from ..utils.activity_logger import registrar_actividad_tarjeta
from ..utils.clientes import obtener_periodo_cierre_activo, get_client_ip


class NombreInglesViewSet(viewsets.ModelViewSet):
    queryset = NombreIngles.objects.all()
    serializer_class = NombreInglesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        if cliente:
            qs = qs.filter(cliente_id=cliente)
        return qs


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_nombres_ingles(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")
    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo requeridos"}, status=400)
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=obtener_periodo_cierre_activo(request.user.cliente_set.first()),
        tarjeta="nombres_ingles",
        accion="upload_excel",
        descripcion=f"Subido archivo nombres inglés: {archivo.name}",
        usuario=request.user,
        detalles={},
        resultado="exito",
        ip_address=get_client_ip(request),
    )
    return Response({"ok": True})
