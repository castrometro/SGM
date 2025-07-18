# api/views_bypass.py
# Vistas que bypassean la lógica de servicios contratados

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Cliente, Usuario, AsignacionClienteUsuario, Area
from .serializers import ClienteSimpleSerializer
from .permissions import IsAuthenticatedAndActive, IsGerente


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def clientes_disponibles_bypass(request, analista_id):
    """
    Obtener clientes disponibles usando el campo areas directo (bypass de servicios)
    """
    try:
        analista = Usuario.objects.get(id=analista_id, tipo_usuario='analista')
        gerente = request.user
        
        # Obtener áreas comunes entre gerente y analista
        areas_gerente = gerente.areas.all()
        areas_analista = analista.areas.all()
        
        areas_gerente_ids = list(areas_gerente.values_list('id', flat=True))
        areas_analista_ids = list(areas_analista.values_list('id', flat=True))
        areas_comunes_ids = list(set(areas_gerente_ids) & set(areas_analista_ids))
        
        if not areas_comunes_ids:
            return Response([])
        
        # Obtener clientes ya asignados a este analista
        clientes_ya_asignados = AsignacionClienteUsuario.objects.filter(
            usuario=analista
        ).values_list('cliente_id', flat=True)
        
        # Obtener clientes con áreas directas en común
        clientes_con_areas_directas = Cliente.objects.filter(
            areas__id__in=areas_comunes_ids
        ).distinct()
        
        # Obtener clientes que tienen servicios en las áreas comunes
        clientes_con_servicios = Cliente.objects.filter(
            servicios_contratados__servicio__area_id__in=areas_comunes_ids
        ).distinct()
        
        # Combinar ambos conjuntos usando listas de IDs
        ids_directos = set(clientes_con_areas_directas.values_list('id', flat=True))
        ids_servicios = set(clientes_con_servicios.values_list('id', flat=True))
        todos_ids = ids_directos | ids_servicios
        
        # Filtrar clientes ocupados
        clientes_ocupados = []
        for cliente_id in todos_ids:
            if cliente_id in clientes_ya_asignados:
                continue
                
            # Verificar si está asignado a otro analista en las mismas áreas
            asignaciones_existentes = AsignacionClienteUsuario.objects.filter(
                cliente_id=cliente_id,
                usuario__areas__id__in=areas_comunes_ids
            ).exclude(usuario=analista)
            
            if asignaciones_existentes.exists():
                clientes_ocupados.append(cliente_id)
        
        # Obtener IDs de clientes disponibles
        clientes_excluidos = list(clientes_ya_asignados) + clientes_ocupados
        ids_disponibles = todos_ids - set(clientes_excluidos)
        
        # Obtener objetos cliente finales
        disponibles = Cliente.objects.filter(id__in=ids_disponibles)
        
        serializer = ClienteSimpleSerializer(disponibles, many=True)
        return Response(serializer.data)
        
    except Usuario.DoesNotExist:
        return Response({'error': 'Analista no encontrado'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def asignar_areas_cliente(request, cliente_id):
    """
    Asignar áreas directamente a un cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        areas_ids = request.data.get('areas', [])
        
        if not areas_ids:
            return Response({'error': 'Debe proporcionar al menos un área'}, status=400)
        
        # Verificar que el gerente tiene permisos sobre estas áreas
        gerente = request.user
        areas_gerente_ids = list(gerente.areas.values_list('id', flat=True))
        
        if not all(area_id in areas_gerente_ids for area_id in areas_ids):
            return Response({'error': 'No tiene permisos para asignar algunas de estas áreas'}, status=403)
        
        # Asignar las áreas al cliente
        areas = Area.objects.filter(id__in=areas_ids)
        cliente.areas.set(areas)
        
        return Response({
            'success': True,
            'mensaje': f'Áreas asignadas al cliente {cliente.nombre}',
            'areas_asignadas': [area.nombre for area in areas]
        })
        
    except Cliente.DoesNotExist:
        return Response({'error': 'Cliente no encontrado'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def clientes_sin_areas(request):
    """
    Obtener clientes que no tienen áreas asignadas directamente
    """
    clientes_sin_areas = Cliente.objects.filter(areas__isnull=True)
    
    # Si es gerente, filtrar por sus áreas usando servicios contratados
    if request.user.tipo_usuario == 'gerente':
        areas_gerente_ids = list(request.user.areas.values_list('id', flat=True))
        clientes_sin_areas = clientes_sin_areas.filter(
            servicios_contratados__servicio__area_id__in=areas_gerente_ids
        ).distinct()
    
    serializer = ClienteSimpleSerializer(clientes_sin_areas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def clientes_area(request):
    """
    Obtener todos los clientes del área del usuario actual
    """
    try:
        usuario = request.user
        areas_usuario = usuario.areas.all()
        
        if not areas_usuario.exists():
            return Response([])
        
        areas_ids = list(areas_usuario.values_list('id', flat=True))
        
        # Obtener clientes que tienen áreas directas del usuario
        clientes_areas_directas = Cliente.objects.filter(
            areas__id__in=areas_ids
        ).distinct()
        
        # Obtener clientes que tienen servicios en las áreas del usuario
        clientes_areas_servicios = Cliente.objects.filter(
            servicios_contratados__servicio__area_id__in=areas_ids
        ).distinct()
        
        # Combinar ambos querysets
        clientes_combinados = clientes_areas_directas.union(clientes_areas_servicios)
        
        serializer = ClienteSimpleSerializer(clientes_combinados, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def analistas_area(request):
    """
    Obtener todos los analistas del área del usuario actual
    """
    try:
        usuario = request.user
        areas_usuario = usuario.areas.all()
        
        if not areas_usuario.exists():
            return Response([])
        
        areas_ids = list(areas_usuario.values_list('id', flat=True))
        
        # Obtener analistas que tienen áreas en común con el usuario
        analistas = Usuario.objects.filter(
            tipo_usuario='analista',
            is_active=True,
            areas__id__in=areas_ids
        ).distinct()
        
        data = []
        for analista in analistas:
            data.append({
                'id': analista.id,
                'nombre': analista.nombre,
                'apellido': analista.apellido,
                'correo_bdo': analista.correo_bdo,
                'areas': [area.nombre for area in analista.areas.all()]
            })
        
        return Response(data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def clientes_por_area(request, area_id):
    """
    Obtener clientes de un área específica
    """
    try:
        # Verificar que el usuario tenga permisos para esta área
        usuario = request.user
        if not usuario.areas.filter(id=area_id).exists():
            return Response({'error': 'No tiene permisos para esta área'}, status=403)
        
        # Obtener clientes que tienen áreas directas
        clientes_areas_directas = Cliente.objects.filter(areas__id=area_id)
        
        # Obtener clientes que tienen servicios en esta área
        clientes_areas_servicios = Cliente.objects.filter(
            servicios_contratados__servicio__area_id=area_id
        )
        
        # Combinar ambos querysets
        clientes_combinados = clientes_areas_directas.union(clientes_areas_servicios).distinct()
        
        serializer = ClienteSimpleSerializer(clientes_combinados, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def migrar_clientes_a_areas_directas(request):
    """
    Migrar clientes existentes de servicios contratados a áreas directas
    """
    gerente = request.user
    areas_gerente_ids = list(gerente.areas.values_list('id', flat=True))
    
    # Obtener clientes que tienen servicios en las áreas del gerente pero no tienen áreas directas
    clientes_para_migrar = Cliente.objects.filter(
        servicios_contratados__servicio__area_id__in=areas_gerente_ids,
        areas__isnull=True
    ).distinct()
    
    migrados = 0
    
    for cliente in clientes_para_migrar:
        # Obtener áreas de los servicios contratados del cliente
        areas_servicios = Area.objects.filter(
            servicios__precios_cliente__cliente=cliente,
            id__in=areas_gerente_ids
        ).distinct()
        
        if areas_servicios.exists():
            cliente.areas.set(areas_servicios)
            migrados += 1
    
    return Response({
        'success': True,
        'mensaje': f'Se migraron {migrados} clientes a áreas directas',
        'clientes_migrados': migrados
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def obtener_clientes_por_area(request):
    """
    Obtener clientes del área del usuario actual (áreas directas + servicios)
    """
    usuario = request.user
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
    
    # Serializar los datos
    clientes_data = []
    for cliente in todos_clientes:
        areas_efectivas = cliente.get_areas_efectivas()
        clientes_data.append({
            'id': cliente.id,
            'nombre': cliente.nombre,
            'rut': cliente.rut,
            'bilingue': cliente.bilingue,
            'areas_efectivas': [{'nombre': area.nombre} for area in areas_efectivas],
            'areas': [{'nombre': area.nombre} for area in cliente.areas.all()],
            'industria_nombre': cliente.industria.nombre if cliente.industria else None
        })
    
    return Response(clientes_data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def obtener_analistas_por_area(request):
    """
    Obtener analistas que comparten áreas con el usuario actual
    """
    usuario = request.user
    areas_usuario = usuario.areas.all()
    
    if not areas_usuario.exists():
        return Response([])
    
    # Obtener analistas que tienen al menos un área en común
    analistas = Usuario.objects.filter(
        tipo_usuario='analista',
        is_active=True,
        areas__in=areas_usuario
    ).distinct().prefetch_related('areas')
    
    analistas_data = []
    for analista in analistas:
        areas_comunes = analista.areas.filter(id__in=areas_usuario.values_list('id', flat=True))
        analistas_data.append({
            'id': analista.id,
            'nombre': analista.nombre,
            'apellido': analista.apellido,
            'correo_bdo': analista.correo_bdo,
            'areas': [{'nombre': area.nombre} for area in areas_comunes],
            'total_areas': areas_comunes.count()
        })
    
    return Response(analistas_data)
