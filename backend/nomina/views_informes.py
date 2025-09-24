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
from .models_informe import InformeNomina
from celery import chord
from .tasks import build_informe_libro, build_informe_movimientos, unir_y_guardar_informe

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
        if cierre.estado != 'finalizado':
            return Response(
                {'error': 'El cierre debe estar finalizado para generar el informe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 1) Intentar obtener desde Redis primero
        try:
            datos_redis = InformeNomina.obtener_desde_redis(cierre.cliente_id, cierre.periodo)
        except Exception:
            datos_redis = None

        if datos_redis and isinstance(datos_redis, dict) and datos_redis.get('datos_cierre'):
            response_data = {
                'id': datos_redis.get('informe_id'),
                'cierre_id': cierre.id,
                'cliente': datos_redis.get('cliente_nombre') or (cierre.cliente.nombre if cierre.cliente else None),
                'periodo': datos_redis.get('periodo') or cierre.periodo,
                'fecha_generacion': datos_redis.get('fecha_generacion'),
                'estado_cierre': cierre.estado,
                'datos_cierre': datos_redis.get('datos_cierre'),
                'source': 'redis',
                'en_cache': True,
            }
            logger.info(f"Informe de cierre {cierre_id} obtenido desde Redis")
            return Response(response_data, status=status.HTTP_200_OK)

        # 2) Fallback a BD si no está en Redis
        try:
            informe = InformeNomina.objects.get(cierre=cierre)
        except InformeNomina.DoesNotExist:
            return Response(
                {'error': 'No existe informe para este cierre'},
                status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            'id': informe.id,
            'cierre_id': cierre.id,
            'cliente': cierre.cliente.nombre if cierre.cliente else None,
            'periodo': cierre.periodo,
            'fecha_generacion': (informe.fecha_generacion.isoformat() if getattr(informe, 'fecha_generacion', None) else None),
            'estado_cierre': cierre.estado,
            'datos_cierre': informe.datos_cierre,
            'source': 'db',
            'en_cache': False,
        }

        logger.info(f"Informe de cierre {cierre_id} obtenido desde BD")
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
        if cierre.estado != 'finalizado':
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

        # Extraer datos clave del informe (estructura simple)
        datos = informe.datos_cierre or {}

        resumen = {
            'cierre_id': cierre.id,
            'cliente': cierre.cliente.nombre if cierre.cliente else None,
            'periodo': cierre.periodo,
            'fecha_generacion': (informe.fecha_generacion.isoformat() if getattr(informe, 'fecha_generacion', None) else None),
            'metricas_clave': {
                # Mantener claves si existen en el JSON, en caso contrario 0
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_informe_cierre(request, cierre_id):
    """
    Dispara un Celery chord para generar el informe del cierre en paralelo:
    - Task A: Libro (detalle + resumen)
    - Task B: Movimientos del mes
    Luego une y guarda en InformeNomina.
    Responde 202 con el task_id del chord.
    """
    try:
        cierre = get_object_or_404(CierreNomina, id=cierre_id)

        # Validar precondición: consolidación existente
        if not cierre.nomina_consolidada.exists():
            return Response(
                {
                    'error': 'No hay datos consolidados para este cierre. Ejecute consolidación antes de generar el informe.'
                },
                status=status.HTTP_409_CONFLICT
            )

        tasks = [
            build_informe_libro.s(cierre_id),
            build_informe_movimientos.s(cierre_id),
        ]
        callback = unir_y_guardar_informe.s(cierre_id)
        result = chord(tasks)(callback)

        return Response(
            {
                'message': 'Generación de informe iniciada',
                'cierre_id': cierre_id,
                'task_id': getattr(result, 'id', None)
            },
            status=status.HTTP_202_ACCEPTED
        )
    except Exception as e:
        logger.error(f"Error al disparar generación de informe para cierre {cierre_id}: {e}")
        return Response(
            {'error': f'Error al iniciar generación: {str(e)}'},
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
                'periodo': informe.cierre.periodo,
                'fecha_generacion': (informe.fecha_generacion.isoformat() if getattr(informe, 'fecha_generacion', None) else None),
                'estado_cierre': informe.cierre.estado,
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
