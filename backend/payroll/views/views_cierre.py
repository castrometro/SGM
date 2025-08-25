from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime

from ..models import CierrePayroll
from ..serializers import CierrePayrollSerializer


class CierrePayrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los cierres de payroll.
    Incluye funcionalidades específicas para el flujo de cierre.
    """
    queryset = CierrePayroll.objects.all()
    serializer_class = CierrePayrollSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cliente si se proporciona
        cliente_id = self.request.query_params.get('cliente', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtrar por periodo si se proporciona
        periodo = self.request.query_params.get('periodo', None)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        
        # Filtrar por estado si se proporciona
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def iniciar_cierre(self, request, pk=None):
        """Inicia el proceso de cierre cambiando el estado a 'pendiente'"""
        cierre = self.get_object()
        
        if cierre.estado != 'pendiente':
            return Response(
                {'error': 'El cierre ya ha sido iniciado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cierre.estado = 'pendiente'
        cierre.usuario_responsable = request.user
        cierre.save()
        
        return Response(CierrePayrollSerializer(cierre).data)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambia el estado del cierre con validaciones"""
        cierre = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Se requiere especificar el nuevo estado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el estado sea válido
        estados_validos = [choice[0] for choice in CierrePayroll.ESTADOS_CHOICES]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado no válido. Estados permitidos: {estados_validos}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cierre.estado = nuevo_estado
        
        if nuevo_estado == 'cerrado':
            cierre.fecha_termino = datetime.now()
        
        cierre.save()
        
        return Response(CierrePayrollSerializer(cierre).data)
    
    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Obtiene un resumen completo del cierre"""
        cierre = self.get_object()
        
        from ..models import ArchivoSubido
        archivos = ArchivoSubido.objects.filter(cierre=cierre)
        
        resumen = {
            'cierre': CierrePayrollSerializer(cierre).data,
            'estadisticas': {
                'total_archivos': archivos.count(),
                'archivos_procesados': archivos.filter(estado='procesado').count(),
            }
        }
        
        return Response(resumen)
