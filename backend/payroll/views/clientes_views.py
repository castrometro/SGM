# ============================================================================
#                           CLIENTES PAYROLL VIEWS
# ============================================================================
# Views específicas para obtener clientes con información de estado de cierre payroll

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api.models import Cliente, Usuario, AsignacionClienteUsuario
from ..models import CierrePayroll


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clientes_asignados_payroll(request):
    """
    Obtiene clientes asignados al usuario actual con información de estado de cierre payroll
    
    GET /api/payroll/clientes/asignados/
    
    Respuesta:
    [
        {
            "id": 1,
            "nombre": "Cliente ABC",
            "rut": "12345678-9",
            "ultimo_cierre_payroll": {
                "periodo": "2025-01",
                "estado": "completado",
                "fecha": "2025-01-15"
            }
        }
    ]
    """
    try:
        # Obtener usuario actual
        usuario = Usuario.objects.get(correo_bdo=request.user.correo_bdo)
        
        # Obtener clientes asignados al usuario
        asignaciones = AsignacionClienteUsuario.objects.filter(
            usuario=usuario
        ).select_related('cliente')
        
        clientes_data = []
        for asignacion in asignaciones:
            cliente = asignacion.cliente
            
            # Obtener el último cierre de payroll del cliente
            ultimo_cierre = CierrePayroll.objects.filter(
                cliente=cliente
            ).order_by('-fecha_creacion').first()
            
            # Formatear información del cierre
            if ultimo_cierre:
                cierre_info = {
                    'periodo': ultimo_cierre.periodo,
                    'estado': ultimo_cierre.estado,
                    'fecha': ultimo_cierre.fecha_creacion.strftime('%Y-%m-%d')
                }
            else:
                cierre_info = {
                    'periodo': None,
                    'estado': 'sin_cierres',
                    'fecha': None
                }
            
            clientes_data.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut,
                'bilingue': cliente.bilingue,
                'industria_nombre': cliente.industria.nombre if cliente.industria else None,
                'ultimo_cierre_payroll': cierre_info
            })
        
        return Response(clientes_data)
        
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clientes_por_area_payroll(request):
    """
    Obtiene clientes del área del usuario actual con información de estado de cierre payroll
    
    GET /api/payroll/clientes/por-area/
    
    Respuesta similar a clientes_asignados_payroll pero para todos los clientes del área
    """
    try:
        # Obtener usuario actual
        usuario = Usuario.objects.get(correo_bdo=request.user.correo_bdo)
        areas_usuario = usuario.areas.all()
        
        if not areas_usuario.exists():
            return Response([])
        
        areas_usuario_ids = list(areas_usuario.values_list('id', flat=True))
        
        # Obtener clientes que tienen áreas directas en común
        clientes_directos = Cliente.objects.filter(
            areas__id__in=areas_usuario_ids
        ).distinct()
        
        # Obtener clientes que tienen servicios en las áreas del usuario
        clientes_servicios = Cliente.objects.filter(
            servicios_contratados__servicio__area_id__in=areas_usuario_ids
        ).exclude(id__in=clientes_directos.values_list('id', flat=True))
        
        # Combinar ambos querysets
        todos_clientes = clientes_directos.union(clientes_servicios)
        
        clientes_data = []
        for cliente in todos_clientes:
            # Obtener el último cierre de payroll del cliente
            ultimo_cierre = CierrePayroll.objects.filter(
                cliente=cliente
            ).order_by('-fecha_creacion').first()
            
            # Formatear información del cierre
            if ultimo_cierre:
                cierre_info = {
                    'periodo': ultimo_cierre.periodo,
                    'estado': ultimo_cierre.estado,
                    'fecha': ultimo_cierre.fecha_creacion.strftime('%Y-%m-%d')
                }
            else:
                cierre_info = {
                    'periodo': None,
                    'estado': 'sin_cierres',
                    'fecha': None
                }
            
            # Obtener áreas efectivas
            areas_efectivas = cliente.get_areas_efectivas()
            
            clientes_data.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut,
                'bilingue': cliente.bilingue,
                'areas_efectivas': [{'nombre': area.nombre} for area in areas_efectivas],
                'areas': [{'nombre': area.nombre} for area in cliente.areas.all()],
                'industria_nombre': cliente.industria.nombre if cliente.industria else None,
                'ultimo_cierre_payroll': cierre_info
            })
        
        return Response(clientes_data)
        
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
