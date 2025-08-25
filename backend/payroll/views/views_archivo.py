from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import datetime

from ..models import ArchivoSubido
from ..serializers import ArchivoSubidoSerializer, ArchivoUploadSerializer


class ArchivoSubidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los archivos subidos.
    Incluye funcionalidades de upload y procesamiento.
    """
    queryset = ArchivoSubido.objects.all()
    serializer_class = ArchivoSubidoSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cierre si se proporciona
        cierre_id = self.request.query_params.get('cierre', None)
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Endpoint específico para subir archivos"""
        serializer = ArchivoUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            # Verificar que no exista ya un archivo del mismo tipo para este cierre
            cierre = serializer.validated_data['cierre']
            tipo_archivo = serializer.validated_data['tipo_archivo']
            
            if ArchivoSubido.objects.filter(cierre=cierre, tipo_archivo=tipo_archivo).exists():
                return Response(
                    {'error': f'Ya existe un archivo de tipo {tipo_archivo} para este cierre'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            archivo = serializer.save()
            
            # Cambiar estado del cierre si es necesario
            if cierre.estado == 'pendiente':
                cierre.estado = 'archivos_subidos'
                cierre.save()
            
            return Response(ArchivoSubidoSerializer(archivo).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """Inicia el procesamiento de un archivo"""
        archivo = self.get_object()
        
        if archivo.estado != 'subido':
            return Response(
                {'error': 'El archivo no está en estado para ser procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo.estado = 'procesando'
        archivo.fecha_procesamiento = datetime.now()
        archivo.save()
        
        # Aquí se llamaría a la tarea de Celery para procesar el archivo
        # from ..tasks import procesar_archivo_task
        # procesar_archivo_task.delay(archivo.id)
        
        return Response(ArchivoSubidoSerializer(archivo).data)
    
    @action(detail=True, methods=['get'])
    def verificar_integridad(self, request, pk=None):
        """Verifica la integridad del archivo mediante hash"""
        archivo = self.get_object()
        
        # Recalcular hash
        hash_actual = archivo.calcular_hash()
        
        es_integro = hash_actual == archivo.hash_md5
        
        return Response({
            'archivo_id': archivo.id,
            'hash_original': archivo.hash_md5,
            'hash_actual': hash_actual,
            'es_integro': es_integro
        })
