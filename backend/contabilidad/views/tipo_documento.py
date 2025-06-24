from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import TipoDocumento, CierreContabilidad, UploadLog
from ..serializers import TipoDocumentoSerializer
from ..tasks import procesar_tipo_documento_con_upload_log
from ..utils.uploads import validar_nombre_archivo, guardar_temporal
from ..utils.mixins import UploadLogMixin
from ..utils.clientes import get_client_ip
from ..utils.activity_logger import registrar_actividad_tarjeta


class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer
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
def cargar_tipo_documento(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")
    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)
    cliente = TipoDocumento.objects.model.cliente.field.related_model.objects.get(id=cliente_id)
    es_valido, _ = validar_nombre_archivo(archivo.name, "tipo_documento", cliente)
    if not es_valido:
        return Response({"error": "Nombre de archivo inválido"}, status=400)
    upload_log = UploadLogMixin().crear_upload_log(cliente, archivo)
    ruta = guardar_temporal(f"tipo_documento_{upload_log.id}.xlsx", archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    procesar_tipo_documento_con_upload_log.delay(upload_log.id)
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=getattr(CierreContabilidad.objects.filter(cliente=cliente).order_by('-fecha_creacion').first(), 'periodo', None) or "",
        tarjeta="tipo_documento",
        accion="upload_excel",
        descripcion=f"Subido archivo de tipos de documento: {archivo.name}",
        usuario=request.user,
        detalles={"upload_log_id": upload_log.id},
        resultado="exito",
        ip_address=get_client_ip(request),
    )
    return Response({"upload_log_id": upload_log.id})
