from rest_framework import viewsets, mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from celery import chain
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from api.models import Cliente
from django.contrib.auth import get_user_model
import logging

from .utils.LibroRemuneraciones import clasificar_headers_libro_remuneraciones

User = get_user_model()


from .models import (
    CierreNomina, 
    LibroRemuneracionesUpload, 
    MovimientosMesUpload, 
    ArchivoAnalistaUpload, 
    ArchivoNovedadesUpload, 
    ChecklistItem,
    ConceptoRemuneracion

)
from .serializers import (
    CierreNominaSerializer, 
    LibroRemuneracionesUploadSerializer, 
    MovimientosMesUploadSerializer,
    ArchivoAnalistaUploadSerializer, 
    ArchivoNovedadesUploadSerializer, 
    CierreNominaCreateSerializer, 
    ChecklistItemUpdateSerializer, 
    ChecklistItemCreateSerializer,
    ConceptoRemuneracionSerializer
)



from .tasks import (
    analizar_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones_task
)

logger = logging.getLogger(__name__)



class CierreNominaViewSet(viewsets.ModelViewSet):
    queryset = CierreNomina.objects.all()
    serializer_class = CierreNominaSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        periodo = self.request.query_params.get('periodo')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CierreNominaCreateSerializer
        return CierreNominaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cierre = serializer.save(usuario_analista=request.user)
        read_serializer = CierreNominaSerializer(cierre, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='resumen/(?P<cliente_id>[^/.]+)')
    def resumen_cliente(self, request, cliente_id=None):
        # Trae el último cierre de nómina por fecha para este cliente
        cierre = (
            CierreNomina.objects
            .filter(cliente_id=cliente_id)
            .order_by('-periodo')
            .first()
        )
        if cierre:
            return Response({
                "ultimo_cierre": cierre.periodo,
                "estado_ultimo_cierre": cierre.estado,
            })
        else:
            return Response({
                "ultimo_cierre": None,
                "estado_cierre_actual": None,
            })
        

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroRemuneracionesUpload.objects.all()
    serializer_class = LibroRemuneracionesUploadSerializer
    def perform_create(self, serializer):
        instance = serializer.save()
        chain(
            analizar_headers_libro_remuneraciones.s(instance.id),
            clasificar_headers_libro_remuneraciones_task.s()
        )()



    @action(detail=False, methods=['get'], url_path='estado/(?P<cierre_id>[^/.]+)')
    def estado(self, request, cierre_id=None):
        libro = self.get_queryset().filter(cierre_id=cierre_id).order_by('-fecha_subida').first()
        if libro:
            return Response({
                "estado": libro.estado,
                "archivo_nombre": libro.archivo.name.split("/")[-1],
                "archivo_url": request.build_absolute_uri(libro.archivo.url),
                "header_json": libro.header_json,  # o donde guardes los pendientes
                "fecha_subida": libro.fecha_subida,
                "cliente_id": libro.cierre.cliente.id,
                "cliente_nombre": libro.cierre.cliente.nombre,
            })
        else:
            return Response({
                "estado": "no_subido",
                "archivo_nombre": "",
                "archivo_url": "",
                "header_json": [],
                "fecha_subida": None,
                "cliente_id": None,
                "cliente_nombre": "",
            })

@api_view(['GET'])
def conceptos_remuneracion_por_cliente(request):
    cliente_id = request.query_params.get('cliente_id')
    if not cliente_id:
        return Response({"error": "Se requiere cliente_id"}, status=400)

    conceptos = ConceptoRemuneracion.objects.filter(cliente_id=cliente_id, vigente=True)
    serializer = ConceptoRemuneracionSerializer(conceptos, many=True)
    return Response(serializer.data)




class ConceptoRemuneracionBatchView(APIView):
    def post(self, request):
        data = request.data
        cliente_id = data.get("cliente_id")
        cierre_id = data.get("cierre_id")
        conceptos = data.get("conceptos", {})

        if not cliente_id or not isinstance(conceptos, dict):
            return Response({"error": "Datos incompletos"}, status=400)

        cliente = Cliente.objects.filter(id=cliente_id).first()
        if not cliente:
            return Response({"error": "Cliente no encontrado"}, status=404)

        usuario = request.user

        for nombre, info in conceptos.items():
            clasificacion = info.get("clasificacion")
            hashtags = info.get("hashtags", [])

            if not clasificacion:
                continue  # Ignora si falta clasificación

            obj, _ = ConceptoRemuneracion.objects.update_or_create(
                cliente=cliente,
                nombre_concepto=nombre,
                defaults={
                    "clasificacion": clasificacion,
                    "hashtags": hashtags,
                    "usuario_clasifica": usuario,
                    "vigente": True
                }
            )

        # Si se especificó un cierre, actualiza el JSON de headers
        if cierre_id:
            try:
                libro = (
                    LibroRemuneracionesUpload.objects
                    .filter(cierre_id=cierre_id)
                    .order_by('-fecha_subida')
                    .first()
                )
                if libro:
                    if isinstance(libro.header_json, dict):
                        headers = (
                            libro.header_json.get("headers_clasificados", [])
                            + libro.header_json.get("headers_sin_clasificar", [])
                        )
                    else:
                        headers = libro.header_json or []
                    headers_c, headers_s = clasificar_headers_libro_remuneraciones(headers, cliente)
                    libro.header_json = {
                        "headers_clasificados": headers_c,
                        "headers_sin_clasificar": headers_s,
                    }
                    libro.estado = 'clasif_pendiente' if headers_s else 'clasificado'
                    libro.save()
            except Exception as e:
                logger.error(f"Error actualizando libro tras clasificacion: {e}")

        return Response({"status": "ok", "actualizados": len(conceptos)}, status=status.HTTP_200_OK)


@api_view(['GET'])
def obtener_hashtags_disponibles(request, cliente_id):
    conceptos = ConceptoRemuneracion.objects.filter(cliente_id=cliente_id)
    hashtags = set()
    for c in conceptos:
        hashtags.update(c.hashtags or [])
    return Response(sorted(list(hashtags)))


@api_view(['DELETE'])
def eliminar_concepto_remuneracion(request, cliente_id, nombre_concepto):
    try:
        concepto = ConceptoRemuneracion.objects.get(
            cliente_id=cliente_id,
            nombre_concepto=nombre_concepto
        )
    except ConceptoRemuneracion.DoesNotExist:
        return Response(
            {"error": "No encontrado"},
            status=status.HTTP_404_NOT_FOUND
        )

    concepto.vigente = False
    concepto.save()
    return Response({"status": "ok"})

class MovimientosMesUploadViewSet(viewsets.ModelViewSet):
    queryset = MovimientosMesUpload.objects.all()
    serializer_class = MovimientosMesUploadSerializer

class ArchivoAnalistaUploadViewSet(viewsets.ModelViewSet):
    queryset = ArchivoAnalistaUpload.objects.all()
    serializer_class = ArchivoAnalistaUploadSerializer

class ArchivoNovedadesUploadViewSet(viewsets.ModelViewSet):
    queryset = ArchivoNovedadesUpload.objects.all()
    serializer_class = ArchivoNovedadesUploadSerializer

class ChecklistItemViewSet(mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemUpdateSerializer