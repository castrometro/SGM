from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Cliente
from ..models import TipoDocumento, CierreContabilidad, UploadLog
from ..serializers import TipoDocumentoSerializer
from ..tasks_de_tipo_doc import iniciar_procesamiento_tipo_documento_chain
from ..utils.mixins import UploadLogMixin
from ..utils.clientes import get_client_ip
from ..utils.uploads import guardar_temporal


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
    
    # 1. VALIDACIONES BÁSICAS SÍNCRONAS
    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)
    
    # 2. VERIFICAR CLIENTE EXISTE (crítico para continuar)
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    # 3. CREAR UPLOAD_LOG BÁSICO Y GUARDAR ARCHIVO
    mixin = UploadLogMixin()
    mixin.tipo_upload = "tipo_documento"
    upload_log = mixin.crear_upload_log(cliente, archivo)
    upload_log.usuario = request.user
    upload_log.ip_usuario = get_client_ip(request)
    upload_log.save()
    
    # Guardar archivo temporal inmediatamente
    nombre_temporal = f"tipo_doc_cliente_{cliente_id}_{upload_log.id}.xlsx"
    ruta = guardar_temporal(nombre_temporal, archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    
    # 4. 🔗 INICIAR CELERY CHAIN
    # El chain manejará: validación datos existentes, nombre archivo, procesamiento, limpieza
    iniciar_procesamiento_tipo_documento_chain.delay(
        upload_log.id,
        archivo.name,  # Para validación de nombre
        nombre_temporal  # Nombre temporal ya guardado
    )
    
    return Response({
        "mensaje": "Archivo recibido y procesamiento iniciado",
        "upload_log_id": upload_log.id,
        "estado": "procesando",
        "info": "El procesamiento se realizará de manera asíncrona"
    })
