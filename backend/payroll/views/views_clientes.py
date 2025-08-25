# views/views_clientes.py
# Views específicas para obtener clientes con información de payroll

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Prefetch

from api.models import Cliente, AsignacionClienteUsuario, Area
from api.serializers import ClienteSimpleSerializer
from api.permissions import IsAuthenticatedAndActive


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def clientes_asignados_payroll(request):
    """
    Obtiene clientes asignados al usuario actual con información de estado de cierre payroll
    Para analistas: solo clientes asignados
    """
    usuario = request.user
    
    try:
        if usuario.tipo_usuario == 'analista':
            # Para analistas: solo clientes asignados directamente
            asignaciones = AsignacionClienteUsuario.objects.filter(
                usuario=usuario
            ).select_related('cliente')
            
            clientes = [asig.cliente for asig in asignaciones]
            
        elif usuario.tipo_usuario in ['gerente', 'supervisor']:
            # Para gerentes/supervisores: clientes de sus áreas
            areas_usuario = usuario.areas.all()
            
            clientes = Cliente.objects.filter(
                Q(area__in=areas_usuario) | 
                Q(asignaciones__usuario=usuario)
            ).distinct()
            
        else:
            # Admin puede ver todos los clientes
            clientes = Cliente.objects.all()
        
        # Serializar los clientes
        serializer = ClienteSimpleSerializer(clientes, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Error obteniendo clientes: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def clientes_por_area_payroll(request):
    """
    Obtiene clientes del área del usuario actual con información de estado de cierre payroll
    Para gerentes/supervisores: clientes de sus áreas
    """
    usuario = request.user
    
    try:
        if usuario.tipo_usuario in ['gerente', 'supervisor']:
            # Obtener áreas del usuario
            areas_usuario = usuario.areas.all()
            
            if not areas_usuario:
                return Response({'clientes': []})
            
            # Obtener clientes de esas áreas
            clientes = Cliente.objects.filter(
                area__in=areas_usuario
            ).distinct().select_related('area')
            
        elif usuario.tipo_usuario == 'analista':
            # Los analistas solo ven sus clientes asignados
            asignaciones = AsignacionClienteUsuario.objects.filter(
                usuario=usuario
            ).select_related('cliente__area')
            
            clientes = [asig.cliente for asig in asignaciones]
            
        else:
            # Admin puede ver todos los clientes
            clientes = Cliente.objects.all().select_related('area')
        
        # Serializar los clientes
        serializer = ClienteSimpleSerializer(clientes, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Error obteniendo clientes por área: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def todos_clientes_payroll(request):
    """
    Obtiene todos los clientes con información de estado de cierre payroll
    Solo para administradores y usuarios con permisos especiales
    """
    usuario = request.user
    
    if usuario.tipo_usuario not in ['admin', 'gerente']:
        return Response(
            {'error': 'No tienes permisos para ver todos los clientes'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        clientes = Cliente.objects.all().select_related('area')
        
        # Serializar los clientes
        serializer = ClienteSimpleSerializer(clientes, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': f'Error obteniendo todos los clientes: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def resumen_cliente_payroll(request, cliente_id):
    """
    Obtiene el resumen de payroll de un cliente específico
    Incluye información de empleados, último cierre, estado actual, etc.
    """
    try:
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar permisos del usuario para ver este cliente
        usuario = request.user
        if usuario.tipo_usuario == 'analista':
            # Analistas solo pueden ver clientes asignados
            if not AsignacionClienteUsuario.objects.filter(
                usuario=usuario, cliente=cliente
            ).exists():
                return Response(
                    {'error': 'No tienes permisos para ver este cliente'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Importar modelos de payroll
        from ..models import CierrePayroll
        
        # Obtener información de cierres de payroll
        cierres = CierrePayroll.objects.filter(
            cliente=cliente
        ).order_by('-fecha_inicio')
        
        ultimo_cierre = cierres.first() if cierres.exists() else None
        
        # Preparar resumen
        resumen = {
            'cliente_id': cliente.id,
            'cliente_nombre': cliente.nombre,
            'cliente_rut': cliente.rut,
            'total_cierres': cierres.count(),
            'ultimo_cierre': {
                'id': ultimo_cierre.id if ultimo_cierre else None,
                'periodo': ultimo_cierre.periodo if ultimo_cierre else None,
                'estado': ultimo_cierre.estado if ultimo_cierre else 'sin_cierres',
                'fecha_inicio': ultimo_cierre.fecha_inicio if ultimo_cierre else None,
                'fecha_termino': ultimo_cierre.fecha_termino if ultimo_cierre else None,
            } if ultimo_cierre else None,
            'estado_cliente': ultimo_cierre.estado if ultimo_cierre else 'sin_cierres',
            # Información adicional que podríamos agregar en el futuro
            'total_empleados': 0,  # TODO: Implementar cuando tengamos modelo de empleados
            'archivos_subidos': 0,  # TODO: Calcular desde ArchivoSubido
        }
        
        return Response(resumen)
        
    except Exception as e:
        return Response(
            {'error': f'Error obteniendo resumen del cliente: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
