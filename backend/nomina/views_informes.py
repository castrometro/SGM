"""
Views dedicadas para el sistema de informes de nómina.
Maneja la generación y consulta de informes cuando se finalizan los cierres.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .models import CierreNomina
from .models_informe import ReporteNomina

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_informe_cierre(request, cierre_id):
    """
    Obtiene el informe completo de un cierre de nómina finalizado.
    
    Args:
        cierre_id: ID del cierre de nómina
        
    Returns:
        JSON con el informe completo del cierre
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)
        
        # Verificar que el cierre esté finalizado
        if cierre.estado_actual != 'finalizado':
            return Response(
                {'error': 'El cierre debe estar finalizado para generar el informe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear el informe
        try:
            informe = InformeNomina.objects.get(cierre=cierre)
        except InformeNomina.DoesNotExist:
            # Si no existe, generarlo
            informe = InformeNomina.generar_informe_completo(cierre)
        
        # Preparar respuesta
        response_data = {
            'id': informe.id,
            'cierre_id': cierre.id,
            'cliente': cierre.cliente.nombre if cierre.cliente else None,
            'periodo': cierre.periodo.strftime('%Y-%m'),
            'fecha_generacion': informe.fecha_generacion.isoformat(),
            'estado_cierre': cierre.estado_actual,
            'datos_cierre': informe.datos_cierre,
        }
        
        logger.info(f"Informe de cierre {cierre_id} obtenido exitosamente")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al obtener informe del cierre {cierre_id}: {str(e)}")
        return Response(
            {'error': f'Error al obtener el informe: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_resumen_informe(request, cierre_id):
    """
    Obtiene un resumen simplificado del informe de cierre.
    
    Args:
        cierre_id: ID del cierre de nómina
        
    Returns:
        JSON con resumen del informe del cierre
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)
        
        # Verificar que el cierre esté finalizado
        if cierre.estado_actual != 'finalizado':
            return Response(
                {'error': 'El cierre debe estar finalizado para consultar el informe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener el informe
        try:
            informe = InformeNomina.objects.get(cierre=cierre)
        except InformeNomina.DoesNotExist:
            return Response(
                {'error': 'No existe informe para este cierre'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extraer datos clave del informe
        datos = informe.datos_cierre
        
        resumen = {
            'cierre_id': cierre.id,
            'cliente': cierre.cliente.nombre if cierre.cliente else None,
            'periodo': cierre.periodo.strftime('%Y-%m'),
            'fecha_generacion': informe.fecha_generacion.isoformat(),
            'metricas_clave': {
                'costo_empresa_total': datos.get('costo_empresa_total', 0),
                'dotacion_total': datos.get('dotacion_total', 0),
                'dotacion_activa': datos.get('dotacion_activa', 0),
                'rotacion_porcentaje': datos.get('rotacion_porcentaje', 0),
                'ausentismo_porcentaje': datos.get('ausentismo_porcentaje', 0),
                'horas_extras_total': datos.get('horas_extras_total', 0),
            },
            'movimientos': {
                'ingresos': datos.get('movimientos_ingresos', 0),
                'egresos': datos.get('movimientos_egresos', 0),
                'ausencias': datos.get('movimientos_ausencias', 0),
            }
        }
        
        logger.info(f"Resumen de informe del cierre {cierre_id} obtenido exitosamente")
        return Response(resumen, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al obtener resumen del informe del cierre {cierre_id}: {str(e)}")
        return Response(
            {'error': f'Error al obtener el resumen: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_informes_cliente(request, cliente_id):
    """
    Lista todos los informes de un cliente específico.
    
    Args:
        cliente_id: ID del cliente
        
    Returns:
        Lista de informes del cliente
    """
    try:
        informes = InformeNomina.objects.filter(
            cierre__cliente_id=cliente_id
        ).select_related('cierre').order_by('-fecha_generacion')
        
        lista_informes = []
        for informe in informes:
            lista_informes.append({
                'id': informe.id,
                'cierre_id': informe.cierre.id,
                'periodo': informe.cierre.periodo.strftime('%Y-%m'),
                'fecha_generacion': informe.fecha_generacion.isoformat(),
                'estado_cierre': informe.cierre.estado_actual,
                'costo_total': informe.datos_cierre.get('costo_empresa_total', 0),
                'dotacion_total': informe.datos_cierre.get('dotacion_total', 0),
            })
        
        return Response({
            'cliente_id': cliente_id,
            'total_informes': len(lista_informes),
            'informes': lista_informes
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al listar informes del cliente {cliente_id}: {str(e)}")
        return Response(
            {'error': f'Error al listar informes: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
