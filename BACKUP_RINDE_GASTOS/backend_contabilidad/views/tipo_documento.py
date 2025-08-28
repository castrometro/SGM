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
from ..utils.activity_logger import registrar_actividad_tarjeta
from .helpers import obtener_periodo_actividad_para_cliente


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

    def perform_create(self, serializer):
        """Registrar actividad al crear tipo documento manualmente"""
        instance = serializer.save()
        
        # Registrar actividad
        try:
            cliente = Cliente.objects.get(id=instance.cliente_id)
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            
            registrar_actividad_tarjeta(
                cliente_id=instance.cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_create",
                descripcion=f"Creó tipo documento manual: {instance.codigo} - {instance.descripcion}",
                usuario=self.request.user,
                detalles={
                    "tipo_documento_id": instance.id,
                    "codigo": instance.codigo,
                    "descripcion": instance.descripcion,
                    "accion_origen": "crud_manual",
                },
                resultado="exito",
                ip_address=get_client_ip(self.request),
            )
        except Exception as e:
            # No fallar la creación si hay error en el logging
            pass

    def perform_update(self, serializer):
        """Registrar actividad al actualizar tipo documento"""
        instance = serializer.save()
        
        # Registrar actividad
        try:
            cliente = Cliente.objects.get(id=instance.cliente_id)
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            
            registrar_actividad_tarjeta(
                cliente_id=instance.cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_edit",
                descripcion=f"Editó tipo documento: {instance.codigo} - {instance.descripcion}",
                usuario=self.request.user,
                detalles={
                    "tipo_documento_id": instance.id,
                    "codigo": instance.codigo,
                    "descripcion": instance.descripcion,
                    "accion_origen": "crud_manual",
                },
                resultado="exito",
                ip_address=get_client_ip(self.request),
            )
        except Exception as e:
            # No fallar la actualización si hay error en el logging
            pass

    def perform_destroy(self, instance):
        """Registrar actividad al eliminar tipo documento"""
        # Capturar datos antes de eliminar
        cliente_id = instance.cliente_id
        codigo = instance.codigo
        descripcion = instance.descripcion
        tipo_documento_id = instance.id
        
        # Eliminar el registro
        instance.delete()
        
        # Registrar actividad
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_delete",
                descripcion=f"Eliminó tipo documento: {codigo} - {descripcion}",
                usuario=self.request.user,
                detalles={
                    "tipo_documento_id": tipo_documento_id,
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "accion_origen": "crud_manual",
                },
                resultado="exito",
                ip_address=get_client_ip(self.request),
            )
        except Exception as e:
            # Ya se eliminó, no se puede deshacer
            pass


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
