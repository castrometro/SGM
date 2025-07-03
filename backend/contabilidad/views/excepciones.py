from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from api.models import Cliente
from ..models import CierreContabilidad, ExcepcionValidacion, CuentaContable, ClasificacionSet, ExcepcionClasificacionSet


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_cuenta_no_aplica(request):
    """
    Marca una cuenta como "No aplica" para un tipo específico de validación.
    
    Body esperado:
    {
        "cierre_id": 123,
        "codigo_cuenta": "1-01-001-001-0001",
        "tipo_excepcion": "DOC_NULL" | "CUENTA_NO_CLAS",  // Tipo de incidencia
        "motivo": "Cuenta de efectivo no requiere tipo de documento",
        "set_clasificacion_id": 123  // Solo requerido para CUENTA_NO_CLAS
    }
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        cierre_id = data.get('cierre_id')
        codigo_cuenta = data.get('codigo_cuenta')
        tipo_incidencia = data.get('tipo_excepcion', '')
        motivo = data.get('motivo', '')
        set_clasificacion_id = data.get('set_clasificacion_id')
        
        if not all([cierre_id, codigo_cuenta, tipo_incidencia]):
            return Response({
                'error': 'Faltan campos requeridos: cierre_id, codigo_cuenta, tipo_excepcion'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el cierre
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
        except CierreContabilidad.DoesNotExist:
            return Response({
                'error': f'Cierre {cierre_id} no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener información de la cuenta para el nombre
        nombre_cuenta = ''
        try:
            cuenta = CuentaContable.objects.get(
                cliente=cierre.cliente,
                codigo=codigo_cuenta
            )
            nombre_cuenta = cuenta.nombre
        except CuentaContable.DoesNotExist:
            # Si no existe la cuenta, usar el código como nombre
            nombre_cuenta = f'Cuenta {codigo_cuenta}'
        
        # CASO ESPECIAL: CUENTA_NO_CLAS requiere ExcepcionClasificacionSet
        if tipo_incidencia in ['CUENTA_NO_CLAS', 'CUENTA_NO_CLASIFICADA']:
            if not set_clasificacion_id:
                return Response({
                    'error': 'set_clasificacion_id es requerido para excepciones de clasificación'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                set_clasificacion = ClasificacionSet.objects.get(
                    id=set_clasificacion_id, 
                    cliente=cierre.cliente
                )
            except ClasificacionSet.DoesNotExist:
                return Response({
                    'error': f'Set de clasificación {set_clasificacion_id} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Crear o actualizar ExcepcionClasificacionSet
            excepcion, created = ExcepcionClasificacionSet.objects.get_or_create(
                cliente=cierre.cliente,
                set_clasificacion=set_clasificacion,
                cuenta_codigo=codigo_cuenta,
                defaults={
                    'motivo': motivo,
                    'usuario_creador': request.user,
                    'activa': True
                }
            )
            
            if not created:
                # Si ya existe, actualizar
                excepcion.motivo = motivo
                excepcion.activa = True
                excepcion.save()
            
            return Response({
                'success': True,
                'excepcion_id': excepcion.id,
                'mensaje': f'Cuenta {codigo_cuenta} marcada como "No aplica" para clasificación en set "{set_clasificacion.nombre}"',
                'created': created,
                'tipo': 'ExcepcionClasificacionSet',
                'details': {
                    'codigo_cuenta': codigo_cuenta,
                    'nombre_cuenta': nombre_cuenta,
                    'set_clasificacion': set_clasificacion.nombre,
                    'motivo': motivo,
                    'fecha_creacion': excepcion.fecha_creacion.isoformat(),
                    'usuario_creador': request.user.correo_bdo if request.user else None
                }
            })
        
        # CASOS NORMALES: ExcepcionValidacion
        else:
            # Mapear tipo de incidencia a tipo de excepción
            mapeo_tipos = {
                'DOC_NULL': 'movimientos_tipodoc_nulo',
                'DOC_NO_REC': 'tipos_doc_no_reconocidos', 
                'CUENTA_INGLES': 'cuentas_sin_nombre_ingles',
            }
            
            tipo_excepcion = mapeo_tipos.get(tipo_incidencia)
            if not tipo_excepcion:
                return Response({
                    'error': f'Tipo de incidencia no válido: {tipo_incidencia}',
                    'tipos_validos': list(mapeo_tipos.keys()) + ['CUENTA_NO_CLAS', 'CUENTA_NO_CLASIFICADA']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear o actualizar la excepción
            excepcion, created = ExcepcionValidacion.objects.get_or_create(
                cliente=cierre.cliente,
                tipo_excepcion=tipo_excepcion,
                codigo_cuenta=codigo_cuenta,
                defaults={
                    'nombre_cuenta': nombre_cuenta,
                    'motivo': motivo,
                    'usuario_creador': request.user,
                    'activa': True
                }
            )
            
            if not created:
                # Si ya existe, actualizar
                excepcion.motivo = motivo
                excepcion.activa = True
                excepcion.save()
            
            return Response({
                'success': True,
                'excepcion_id': excepcion.id,
                'mensaje': f'Cuenta {codigo_cuenta} marcada como "No aplica" para {excepcion.get_tipo_excepcion_display()}',
                'created': created,
                'tipo': 'ExcepcionValidacion',
                'details': {
                    'codigo_cuenta': codigo_cuenta,
                    'nombre_cuenta': nombre_cuenta,
                    'tipo_excepcion': excepcion.get_tipo_excepcion_display(),
                    'motivo': motivo,
                    'fecha_creacion': excepcion.fecha_creacion.isoformat(),
                    'usuario_creador': request.user.correo_bdo if request.user else None
                }
            })
        
    except json.JSONDecodeError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON inválido en marcar_cuenta_no_aplica: {e}")
        return Response({
            'error': 'JSON inválido en el body de la petición'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error en marcar_cuenta_no_aplica: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        logger.error(f"Request data: {getattr(request, 'data', 'No data')}")
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_excepciones_cuenta(request, cierre_id, codigo_cuenta):
    """
    Lista las excepciones activas para una cuenta específica
    """
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        excepciones = ExcepcionValidacion.objects.filter(
            cliente=cierre.cliente,
            codigo_cuenta=codigo_cuenta,
            activa=True
        ).select_related('usuario_creador')
        
        data = []
        for exc in excepciones:
            data.append({
                'id': exc.id,
                'tipo_excepcion': exc.tipo_excepcion,
                'tipo_display': exc.get_tipo_excepcion_display(),
                'motivo': exc.motivo,
                'fecha_creacion': exc.fecha_creacion.isoformat(),
                'usuario_creador': exc.usuario_creador.username if exc.usuario_creador else None
            })
        
        return Response({
            'codigo_cuenta': codigo_cuenta,
            'cliente': cierre.cliente.nombre,
            'excepciones': data
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response({
            'error': f'Cierre {cierre_id} no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_excepcion(request, excepcion_id):
    """
    Elimina (desactiva) una excepción específica
    """
    try:
        excepcion = ExcepcionValidacion.objects.get(id=excepcion_id)
        excepcion.activa = False
        excepcion.save()
        
        return Response({
            'success': True,
            'mensaje': f'Excepción eliminada para cuenta {excepcion.codigo_cuenta}'
        })
        
    except ExcepcionValidacion.DoesNotExist:
        return Response({
            'error': f'Excepción {excepcion_id} no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error interno: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
