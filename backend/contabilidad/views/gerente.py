# backend/contabilidad/views/gerente.py

from django.db.models import Count, Q, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.contrib.sessions.models import Session
import logging

from api.models import Cliente, Usuario, AsignacionClienteUsuario
from ..models import TarjetaActivityLog, CierreContabilidad
from ..cache_redis import get_cache_system

logger = logging.getLogger(__name__)

# ==================== LOGS Y ACTIVIDAD ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_logs_actividad(request):
    """
    Obtiene logs de actividad con filtros para gerentes usando sistema híbrido
    - Redis para logs recientes (últimos 7 días)
    - PostgreSQL para búsquedas históricas
    """
    # Verificar que el usuario sea gerente
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Obtener filtros
    cliente_id = request.GET.get('cliente_id')
    usuario_id = request.GET.get('usuario_id')
    tarjeta = request.GET.get('tarjeta')
    accion = request.GET.get('accion')
    cierre = request.GET.get('cierre')  # Nuevo filtro por estado de cierre
    periodo = request.GET.get('periodo')  # Nuevo filtro por período de cierre
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    force_redis = request.GET.get('force_redis', 'false').lower() == 'true'  # Nuevo parámetro
    
    # Determinar estrategia de consulta
    use_redis = force_redis or should_use_redis_cache(fecha_desde, fecha_hasta)
    
    if use_redis and (force_redis or not (usuario_id or tarjeta or accion or cierre)):
        # Usar Redis para consultas simples y recientes
        try:
            logs_data = get_logs_from_redis(
                cliente_id=cliente_id,
                periodo=periodo,
                page=page,
                page_size=page_size,
                force_all=force_redis  # Pasar el parámetro para obtener todos los logs
            )
            if logs_data['results'] or force_redis:  # Si Redis tiene datos o se fuerza su uso
                return Response(logs_data)
        except Exception as e:
            logger.warning(f"Error con Redis, usando PostgreSQL: {e}")
            if force_redis:  # Si se fuerza Redis, devolver error
                return Response({'error': 'Error accediendo a Redis'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Usar PostgreSQL para búsquedas complejas o históricas
    logs_data = get_logs_from_postgres(
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        tarjeta=tarjeta,
        accion=accion,
        cierre=cierre,
        periodo=periodo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        page_size=page_size
    )
    
    return Response(logs_data)


def should_use_redis_cache(fecha_desde, fecha_hasta):
    """Determina si usar Redis o PostgreSQL según los filtros de fecha"""
    # Si no hay filtros de fecha, usar Redis (logs recientes)
    if not fecha_desde and not fecha_hasta:
        return True
    
    # Si hay filtros de fecha, verificar si están en el rango de Redis (7 días)
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            if fecha_desde_dt < datetime.now() - timedelta(days=7):
                return False
        except ValueError:
            pass
    
    return True


def get_logs_from_redis(cliente_id=None, periodo=None, page=1, page_size=20, force_all=False):
    """Obtiene logs desde Redis con paginación"""
    from ..utils.activity_logger import ActivityLogStorage
    
    try:
        # Determinar el límite según si se fuerza obtener todos los logs
        if force_all:
            # Obtener todos los logs disponibles en Redis
            logs = ActivityLogStorage.get_recent_logs(
                cliente_id=cliente_id,
                periodo=periodo,
                limit=None  # Sin límite para obtener todos los logs
            )
        else:
            # Obtener más logs para filtrado y paginación
            logs = ActivityLogStorage.get_recent_logs(
                cliente_id=cliente_id,
                periodo=periodo,
                limit=page_size * 10  # Buffer para paginación
            )
        
        # Paginación simple
        total_count = len(logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = logs[start_idx:end_idx]
        
        return {
            'results': paginated_logs,
            'count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size,
            'current_page': page,
            'has_next': end_idx < total_count,
            'has_previous': page > 1,
            'source': 'redis'  # Para debugging
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo logs desde Redis: {e}")
        return {'results': [], 'count': 0, 'total_pages': 0, 'current_page': 1, 'has_next': False, 'has_previous': False}


def get_logs_from_postgres(cliente_id=None, usuario_id=None, tarjeta=None,
                          accion=None, cierre=None, periodo=None,
                          fecha_desde=None, fecha_hasta=None,
                          page=1, page_size=20):
    """Obtiene logs desde PostgreSQL (método mejorado)"""
    # Construir query
    logs = TarjetaActivityLog.objects.select_related(
        'cierre', 'cierre__cliente', 'usuario'
    ).all()
    
    # Aplicar filtros
    if cliente_id:
        logs = logs.filter(cierre__cliente_id=cliente_id)
    
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    
    if tarjeta:
        logs = logs.filter(tarjeta=tarjeta)
    
    if accion:
        logs = logs.filter(accion=accion)
    
    if cierre:  # Nuevo filtro por estado de cierre
        logs = logs.filter(cierre__estado=cierre)
    
    if periodo:  # Nuevo filtro por período de cierre
        logs = logs.filter(cierre__periodo=periodo)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            logs = logs.filter(timestamp__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    # Ordenar por fecha más reciente
    logs = logs.order_by('-timestamp')
    
    # Paginar
    paginator = Paginator(logs, page_size)
    page_obj = paginator.get_page(page)
    
    # Serializar resultados
    results = []
    for log in page_obj.object_list:
        results.append({
            'id': log.id,
            'cliente_id': log.cierre.cliente.id if log.cierre and log.cierre.cliente else None,
            'cliente_nombre': log.cierre.cliente.nombre if log.cierre and log.cierre.cliente else 'N/A',
            'usuario_nombre': f"{log.usuario.nombre} {log.usuario.apellido}" if log.usuario else 'Sistema',
            'usuario_email': log.usuario.correo_bdo if log.usuario else 'N/A',
            'tarjeta': log.tarjeta,
            'accion': log.accion,
            'descripcion': log.descripcion,
            'resultado': log.resultado,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,  # Asegurar formato ISO
            'fecha_creacion': log.timestamp.isoformat() if log.timestamp else None,  # Mantener compatibilidad
            'ip_address': log.ip_address,
            'detalles': log.detalles,
            'estado_cierre': log.cierre.estado if log.cierre else None,  # Nuevo campo
            'periodo_cierre': log.cierre.periodo if log.cierre else None,  # Nuevo campo
        })
    
    return {
        'results': results,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'source': 'postgres'  # Para debugging
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estadisticas_actividad(request):
    """
    Obtiene estadísticas de actividad para el dashboard
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    periodo = request.GET.get('periodo', 'semana')
    
    # Calcular fechas según el período
    now = timezone.now()
    if periodo == 'semana':
        fecha_inicio = now - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = now - timedelta(days=30)
    elif periodo == 'trimestre':
        fecha_inicio = now - timedelta(days=90)
    else:
        fecha_inicio = now - timedelta(days=7)
    
    # Obtener logs del período
    logs = TarjetaActivityLog.objects.filter(
        timestamp__gte=fecha_inicio
    ).select_related('usuario', 'cierre__cliente')
    
    # Estadísticas generales
    total_actividades = logs.count()
    usuarios_activos = logs.values('usuario').distinct().count()
    clientes_trabajados = logs.values('cierre__cliente').distinct().count()
    
    # Actividades por día
    actividades_por_dia = []
    for i in range(7):
        fecha = (now - timedelta(days=i)).date()
        count = logs.filter(timestamp__date=fecha).count()
        actividades_por_dia.append({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Top usuarios por actividad
    top_usuarios = logs.values(
        'usuario__nombre', 'usuario__apellido', 'usuario__correo_bdo'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Actividades por tarjeta
    actividades_por_tarjeta = logs.values('tarjeta').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Actividades por acción
    actividades_por_accion = logs.values('accion').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return Response({
        'resumen': {
            'total_actividades': total_actividades,
            'usuarios_activos': usuarios_activos,
            'clientes_trabajados': clientes_trabajados,
            'periodo': periodo
        },
        'actividades_por_dia': list(reversed(actividades_por_dia)),
        'top_usuarios': list(top_usuarios),
        'actividades_por_tarjeta': list(actividades_por_tarjeta),
        'actividades_por_accion': list(actividades_por_accion)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_usuarios_actividad(request):
    """
    Obtiene lista de usuarios para filtros
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Obtener usuarios que tienen actividad
    usuarios = Usuario.objects.filter(
        tarjetaactivitylog__isnull=False
    ).distinct().values(
        'id', 'nombre', 'apellido', 'correo_bdo', 'tipo_usuario'
    )
    
    return Response(list(usuarios))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_periodos_disponibles(request):
    """
    Obtiene períodos de cierre disponibles para filtros
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Obtener períodos únicos con conteo de actividad
    periodos = TarjetaActivityLog.objects.select_related(
        'cierre'
    ).values(
        'cierre__periodo', 'cierre__cliente__nombre'
    ).annotate(
        count=Count('id')
    ).filter(
        cierre__periodo__isnull=False
    ).order_by('-cierre__periodo')
    
    # Agrupar por período
    periodos_agrupados = {}
    for item in periodos:
        periodo = item['cierre__periodo']
        cliente = item['cierre__cliente__nombre']
        count = item['count']
        
        if periodo not in periodos_agrupados:
            periodos_agrupados[periodo] = {
                'periodo': periodo,
                'clientes': [],
                'total_actividades': 0
            }
        
        periodos_agrupados[periodo]['clientes'].append({
            'nombre': cliente,
            'actividades': count
        })
        periodos_agrupados[periodo]['total_actividades'] += count
    
    # Convertir a lista y ordenar
    resultado = list(periodos_agrupados.values())
    resultado.sort(key=lambda x: x['periodo'], reverse=True)
    
    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estadisticas_redis_logs(request):
    """
    Obtiene estadísticas del sistema Redis para logs
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from ..utils.activity_logger import ActivityLogStorage
        
        stats = ActivityLogStorage.get_redis_stats()
        
        # Agregar información adicional
        stats['endpoint_info'] = {
            'description': 'Estadísticas del sistema híbrido de logs',
            'redis_ttl_days': 7,
            'max_logs_per_client': 1000,
            'strategy': 'Redis para logs recientes, PostgreSQL para históricos'
        }
        
        return Response(stats)
        
    except Exception as e:
        return Response({
            'error': 'Error obteniendo estadísticas Redis',
            'details': str(e),
            'redis_available': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ESTADOS DE CIERRES ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estados_cierres(request):
    """
    Obtiene el estado de todos los cierres para monitoreo
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Obtener filtros
    cliente_id = request.GET.get('cliente_id')
    estado = request.GET.get('estado')
    usuario_id = request.GET.get('usuario_id')
    periodo = request.GET.get('periodo')
    
    # FILTRAR CIERRES POR ÁREAS DEL GERENTE
    # El gerente solo puede ver cierres de sus áreas asignadas
    areas_gerente = request.user.areas.all()
    if not areas_gerente.exists():
        return Response([], status=status.HTTP_200_OK)
    
    cierres = CierreContabilidad.objects.select_related(
        'cliente', 'usuario', 'area'
    ).filter(
        area__in=areas_gerente  # Solo cierres de las áreas del gerente
    )
    
    # Aplicar filtros adicionales solo si se especifican
    if cliente_id:
        cierres = cierres.filter(cliente_id=cliente_id)
    
    if estado:
        cierres = cierres.filter(estado=estado)
    
    if usuario_id:
        cierres = cierres.filter(usuario_id=usuario_id)
    
    if periodo:
        cierres = cierres.filter(periodo=periodo)
    
    # Ordenar por fecha de creación más reciente
    cierres = cierres.order_by('-fecha_creacion')
    
    # Serializar resultados
    results = []
    for cierre in cierres:
        # Calcular tiempo en estado actual
        tiempo_en_estado = None
        if cierre.fecha_creacion:
            tiempo_en_estado = (timezone.now() - cierre.fecha_creacion).days
        
        # Obtener última actividad
        ultima_actividad = TarjetaActivityLog.objects.filter(
            cierre=cierre
        ).order_by('-timestamp').first()
        
        results.append({
            'id': cierre.id,
            'cliente_nombre': cierre.cliente.nombre,
            'cliente_id': cierre.cliente.id,
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'area_nombre': cierre.area.nombre if cierre.area else 'Sin área',
            'area_id': cierre.area.id if cierre.area else None,
            'usuario_nombre': f"{cierre.usuario.nombre} {cierre.usuario.apellido}" if cierre.usuario else 'Sin asignar',
            'usuario_email': cierre.usuario.correo_bdo if cierre.usuario else None,
            'fecha_creacion': cierre.fecha_creacion.isoformat() if cierre.fecha_creacion else None,
            'fecha_cierre': cierre.fecha_cierre.isoformat() if cierre.fecha_cierre else None,
            'fecha_finalizacion': cierre.fecha_finalizacion.isoformat() if cierre.fecha_finalizacion else None,
            'reportes_generados': cierre.reportes_generados,
            'tiempo_en_estado_dias': tiempo_en_estado,
            'ultima_actividad': ultima_actividad.timestamp.isoformat() if ultima_actividad else None,
            'cuentas_nuevas': cierre.cuentas_nuevas,
            'parsing_completado': cierre.parsing_completado
        })
    
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_cierres(request):
    """
    Endpoint de debugging para ver qué cierres existen en la BD
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Información básica de todos los cierres
    cierres = CierreContabilidad.objects.select_related('cliente', 'usuario', 'area').all()
    
    # Información sobre las áreas del gerente
    areas_gerente = request.user.areas.all()
    areas_gerente_ids = list(areas_gerente.values_list('id', flat=True))
    areas_gerente_nombres = list(areas_gerente.values_list('nombre', flat=True))
    
    # Cierres filtrados por área del gerente
    cierres_del_gerente = cierres.filter(area__in=areas_gerente)
    
    debug_info = {
        'gerente_info': {
            'id': request.user.id,
            'nombre': f"{request.user.nombre} {request.user.apellido}",
            'areas_asignadas': areas_gerente_nombres,
            'areas_ids': areas_gerente_ids
        },
        'total_cierres_sistema': cierres.count(),
        'total_cierres_del_gerente': cierres_del_gerente.count(),
        'estados_disponibles': list(cierres.values_list('estado', flat=True).distinct()),
        'periodos_disponibles': list(cierres.values_list('periodo', flat=True).distinct()),
        'areas_en_cierres': list(cierres.exclude(area__isnull=True).values_list('area__nombre', flat=True).distinct()),
        'cierres_sample': []
    }
    
    # Mostrar los primeros 10 cierres del gerente como muestra
    for cierre in cierres_del_gerente[:10]:
        debug_info['cierres_sample'].append({
            'id': cierre.id,
            'cliente': cierre.cliente.nombre if cierre.cliente else 'Sin cliente',
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'area': cierre.area.nombre if cierre.area else 'Sin área',
            'usuario': f"{cierre.usuario.nombre} {cierre.usuario.apellido}" if cierre.usuario else 'Sin usuario',
            'fecha_creacion': cierre.fecha_creacion.isoformat() if cierre.fecha_creacion else None
        })
    
    return Response(debug_info)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_metricas_cierres(request):
    """
    Obtiene métricas generales de cierres
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    # Cierres por estado
    cierres_por_estado = CierreContabilidad.objects.values('estado').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Tiempo promedio por estado (últimos 30 cierres completados)
    cierres_completados = CierreContabilidad.objects.filter(
        estado__in=['completo', 'finalizado'],
        fecha_finalizacion__isnull=False
    ).order_by('-fecha_finalizacion')[:30]
    
    tiempo_promedio = None
    if cierres_completados:
        tiempos = []
        for cierre in cierres_completados:
            if cierre.fecha_creacion and cierre.fecha_finalizacion:
                tiempo = (cierre.fecha_finalizacion - cierre.fecha_creacion).days
                tiempos.append(tiempo)
        
        if tiempos:
            tiempo_promedio = sum(tiempos) / len(tiempos)
    
    # Cierres por analista (últimos 30 días)
    fecha_limite = timezone.now() - timedelta(days=30)
    cierres_por_analista = CierreContabilidad.objects.filter(
        fecha_creacion__gte=fecha_limite
    ).values(
        'usuario__nombre', 'usuario__apellido', 'usuario__correo_bdo'
    ).annotate(
        count=Count('id'),
        completados=Count('id', filter=Q(estado__in=['completo', 'finalizado']))
    ).order_by('-count')
    
    # Cierres estancados (más de 7 días en el mismo estado)
    fecha_estancado = timezone.now() - timedelta(days=7)
    cierres_estancados = CierreContabilidad.objects.filter(
        fecha_creacion__lte=fecha_estancado,
        estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias']
    ).count()
    
    return Response({
        'cierres_por_estado': list(cierres_por_estado),
        'tiempo_promedio_dias': tiempo_promedio,
        'cierres_por_analista': list(cierres_por_analista),
        'cierres_estancados': cierres_estancados,
        'total_cierres_activos': CierreContabilidad.objects.exclude(
            estado__in=['completo', 'finalizado']
        ).count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_historial_cierre(request, cierre_id):
    """
    Obtiene el historial completo de actividad de un cierre específico
    Para que el gerente pueda ver quién ha trabajado y qué ha hecho
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Obtener información del cierre
        cierre = CierreContabilidad.objects.select_related('cliente', 'usuario').get(id=cierre_id)
        
        # Obtener todo el historial de actividad
        historial = TarjetaActivityLog.objects.filter(
            cierre=cierre
        ).select_related('usuario').order_by('timestamp')
        
        # Estadísticas del cierre
        total_actividades = historial.count()
        usuarios_involucrados = historial.values('usuario').distinct().count()
        
        # Calcular tiempo total trabajado (días entre primera y última actividad)
        tiempo_total_trabajado = None
        if historial.exists():
            primera_actividad = historial.first().timestamp
            ultima_actividad = historial.last().timestamp
            if primera_actividad and ultima_actividad:
                tiempo_total_trabajado = (ultima_actividad - primera_actividad).days
        
        # Actividades por usuario
        actividades_por_usuario = historial.values(
            'usuario__nombre', 'usuario__apellido', 'usuario__correo_bdo'
        ).annotate(
            total_actividades=Count('id'),
            primera_actividad=Min('timestamp'),
            ultima_actividad=Max('timestamp')
        ).order_by('-total_actividades')
        
        # Actividades por tarjeta/etapa
        actividades_por_tarjeta = historial.values('tarjeta').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Timeline detallado
        timeline = []
        for log in historial:
            timeline.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                'usuario_nombre': f"{log.usuario.nombre} {log.usuario.apellido}" if log.usuario else 'Sistema',
                'usuario_email': log.usuario.correo_bdo if log.usuario else 'N/A',
                'tarjeta': log.tarjeta,
                'accion': log.accion,
                'descripcion': log.descripcion,
                'resultado': log.resultado,
                'ip_address': log.ip_address,
                'detalles': log.detalles
            })
        
        # Información del cierre
        cierre_info = {
            'id': cierre.id,
            'cliente_nombre': cierre.cliente.nombre,
            'periodo': cierre.periodo,
            'estado_actual': cierre.estado,
            'usuario_asignado': f"{cierre.usuario.nombre} {cierre.usuario.apellido}" if cierre.usuario else 'Sin asignar',
            'fecha_creacion': cierre.fecha_creacion.isoformat() if cierre.fecha_creacion else None,
            'fecha_cierre': cierre.fecha_cierre.isoformat() if cierre.fecha_cierre else None,
            'fecha_finalizacion': cierre.fecha_finalizacion.isoformat() if cierre.fecha_finalizacion else None,
            'reportes_generados': cierre.reportes_generados,
            'cuentas_nuevas': cierre.cuentas_nuevas,
            'parsing_completado': cierre.parsing_completado
        }
        
        return Response({
            'cierre': cierre_info,
            'estadisticas': {
                'total_actividades': total_actividades,
                'usuarios_involucrados': usuarios_involucrados,
                'tiempo_total_trabajado_dias': tiempo_total_trabajado,
                'actividades_por_usuario': list(actividades_por_usuario),
                'actividades_por_tarjeta': list(actividades_por_tarjeta)
            },
            'timeline': timeline
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response({
            'error': 'Cierre no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error obteniendo historial del cierre: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_dashboard_cierres(request):
    """
    Vista dashboard para el gerente enfocada en estados y progreso de cierres
    Solo muestra cierres de las áreas asignadas al gerente
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        now = timezone.now()
        
        # FILTRAR POR ÁREAS DEL GERENTE
        areas_gerente = request.user.areas.all()
        if not areas_gerente.exists():
            return Response({
                'error': 'El gerente no tiene áreas asignadas',
                'alertas': {'cierres_problematicos': [], 'total_con_problemas': 0},
                'resumen': {'total_cierres': 0, 'cierres_activos': 0, 'cierres_completados': 0, 'completados_este_mes': 0, 'porcentaje_completados': 0},
                'estados': [],
                'antiguedad': {'nuevos': 0, 'normales': 0, 'atrasados': 0, 'criticos': 0},
                'actividad_semanal': [],
                'timestamp': now.isoformat()
            })
        
        # 🚨 CIERRES QUE REQUIEREN ATENCIÓN
        # Cierres estancados (más de 7 días sin actividad)
        hace_7_dias = now - timedelta(days=7)
        cierres_con_problemas = []
        
        # Obtener cierres que NO están terminados Y son del área del gerente
        estados_terminados = ['completo', 'finalizado', 'cerrado', 'terminado']
        cierres_activos = CierreContabilidad.objects.exclude(
            estado__in=estados_terminados
        ).filter(
            area__in=areas_gerente  # Solo cierres de las áreas del gerente
        ).select_related('cliente', 'usuario', 'area')
        
        for cierre in cierres_activos:
            ultima_actividad = TarjetaActivityLog.objects.filter(
                cierre=cierre
            ).order_by('-timestamp').first()
            
            # Si no hay actividad o la última es muy antigua
            if not ultima_actividad or ultima_actividad.timestamp < hace_7_dias:
                dias_sin_actividad = 0
                if ultima_actividad:
                    dias_sin_actividad = (now - ultima_actividad.timestamp).days
                else:
                    dias_sin_actividad = (now - cierre.fecha_creacion).days if cierre.fecha_creacion else 0
                
                cierres_con_problemas.append({
                    'cierre_id': cierre.id,
                    'cliente_nombre': cierre.cliente.nombre,
                    'periodo': cierre.periodo,
                    'estado': cierre.estado,
                    'responsable': f"{cierre.usuario.nombre} {cierre.usuario.apellido}" if cierre.usuario else 'Sin asignar',
                    'dias_sin_actividad': dias_sin_actividad,
                    'ultima_actividad': ultima_actividad.timestamp.isoformat() if ultima_actividad else None,
                    'prioridad': 'Alta' if dias_sin_actividad > 14 else 'Media' if dias_sin_actividad > 7 else 'Baja'
                })
        
        # 📊 RESUMEN POR ESTADO
        # Estados de cierres con conteos - Solo del área del gerente
        estados_cierres = CierreContabilidad.objects.filter(
            area__in=areas_gerente
        ).values('estado').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # 📈 PROGRESO GENERAL
        total_cierres = CierreContabilidad.objects.filter(area__in=areas_gerente).count()
        
        # Definir qué estados consideramos "terminados"
        estados_terminados = ['completo', 'finalizado', 'cerrado', 'terminado']
        cierres_completados = CierreContabilidad.objects.filter(
            area__in=areas_gerente,
            estado__in=estados_terminados
        ).count()
        cierres_activos_count = total_cierres - cierres_completados
        
        # Cierres completados este mes
        cierres_completados_mes = CierreContabilidad.objects.filter(
            area__in=areas_gerente,
            estado__in=estados_terminados,
            fecha_finalizacion__gte=now.replace(day=1)  # Primer día del mes
        ).count()
        
        # 🕒 CIERRES POR ANTIGÜEDAD
        cierres_por_antiguedad = {
            'nuevos': 0,      # 0-3 días
            'normales': 0,    # 4-7 días  
            'atrasados': 0,   # 8-14 días
            'criticos': 0     # +14 días
        }
        
        for cierre in cierres_activos:
            if cierre.fecha_creacion:
                dias = (now - cierre.fecha_creacion).days
                if dias <= 3:
                    cierres_por_antiguedad['nuevos'] += 1
                elif dias <= 7:
                    cierres_por_antiguedad['normales'] += 1
                elif dias <= 14:
                    cierres_por_antiguedad['atrasados'] += 1
                else:
                    cierres_por_antiguedad['criticos'] += 1
        
        # � ACTIVIDAD DE LA SEMANA
        actividad_semanal = []
        for i in range(7):
            fecha = (now - timedelta(days=i)).date()
            actividad_dia = TarjetaActivityLog.objects.filter(
                timestamp__date=fecha,
                cierre__area__in=areas_gerente  # Solo actividad de cierres del área
            ).count()
            actividad_semanal.append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'dia': fecha.strftime('%A'),
                'actividad': actividad_dia
            })
        
        return Response({
            'alertas': {
                'cierres_problematicos': cierres_con_problemas,
                'total_con_problemas': len(cierres_con_problemas)
            },
            'resumen': {
                'total_cierres': total_cierres,
                'cierres_activos': cierres_activos_count,
                'cierres_completados': cierres_completados,
                'completados_este_mes': cierres_completados_mes,
                'porcentaje_completados': round((cierres_completados / total_cierres * 100), 1) if total_cierres > 0 else 0
            },
            'estados': list(estados_cierres),
            'antiguedad': cierres_por_antiguedad,
            'actividad_semanal': list(reversed(actividad_semanal)),
            'timestamp': now.isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo dashboard de cierres: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== CACHE REDIS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estado_cache(request):
    """
    Obtiene estadísticas del cache Redis
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cache_system = get_cache_system()
        stats = cache_system.get_cache_stats()
        
        return Response({
            'stats': stats,
            'health': cache_system.health_check()
        })
    
    except Exception as e:
        return Response({
            'error': f'Error obteniendo estado del cache: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_cierres_en_cache(request):
    """
    Obtiene qué cierres están disponibles en cache vs BD
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cache_system = get_cache_system()
        
        # Obtener todos los cierres de BD
        cierres_bd = CierreContabilidad.objects.select_related('cliente').all()
        
        results = []
        for cierre in cierres_bd:
            # Verificar si está en cache
            en_cache_esf = cache_system.get_estado_financiero(
                cierre.cliente.id, cierre.periodo, 'esf'
            ) is not None
            
            en_cache_eri = cache_system.get_estado_financiero(
                cierre.cliente.id, cierre.periodo, 'eri'
            ) is not None
            
            en_cache_kpis = cache_system.get_kpis(
                cierre.cliente.id, cierre.periodo
            ) is not None
            
            results.append({
                'cierre_id': cierre.id,
                'cliente_nombre': cierre.cliente.nombre,
                'periodo': cierre.periodo,
                'estado': cierre.estado,
                'en_cache': {
                    'esf': en_cache_esf,
                    'eri': en_cache_eri,
                    'kpis': en_cache_kpis,
                    'completo': en_cache_esf and en_cache_eri
                },
                'fecha_finalizacion': cierre.fecha_finalizacion
            })
        
        return Response(results)
    
    except Exception as e:
        return Response({
            'error': f'Error obteniendo cierres en cache: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cargar_cierre_a_cache(request):
    """
    Fuerza la carga de un cierre específico al cache
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    cliente_id = request.data.get('cliente_id')
    periodo = request.data.get('periodo')
    
    if not cliente_id or not periodo:
        return Response({
            'error': 'cliente_id y periodo son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Buscar el cierre
        cierre = CierreContabilidad.objects.select_related('cliente').get(
            cliente_id=cliente_id,
            periodo=periodo
        )
        
        # Aquí puedes implementar la lógica para regenerar los datos en cache
        # Por ahora retornamos un mensaje de éxito
        
        return Response({
            'success': True,
            'message': f'Cierre {cierre.cliente.nombre} - {periodo} marcado para recarga en cache'
        })
    
    except CierreContabilidad.DoesNotExist:
        return Response({
            'error': 'Cierre no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': f'Error cargando cierre: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def limpiar_cache(request):
    """
    Limpia el cache Redis de manera selectiva
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    cliente_id = request.data.get('cliente_id')
    periodo = request.data.get('periodo')
    
    try:
        cache_system = get_cache_system()
        
        if cliente_id and periodo:
            # Limpiar un cierre específico
            deleted = cache_system.invalidate_cliente_periodo(cliente_id, periodo)
            return Response({
                'success': True,
                'message': f'Cache limpiado para cliente {cliente_id}, período {periodo}',
                'claves_eliminadas': deleted
            })
        elif cliente_id:
            # Limpiar todo el cliente
            deleted = cache_system.invalidate_cliente_all(cliente_id)
            return Response({
                'success': True,
                'message': f'Cache limpiado para cliente {cliente_id}',
                'claves_eliminadas': deleted
            })
        else:
            return Response({
                'error': 'Se requiere al menos cliente_id'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': f'Error limpiando cache: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GESTIÓN DE USUARIOS ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gestionar_usuarios(request):
    """
    GET: Lista todos los usuarios del sistema
    POST: Crea un nuevo usuario
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Obtener las áreas del gerente
        areas_gerente = request.user.areas.all()
        
        # Filtrar usuarios por las áreas del gerente
        usuarios = Usuario.objects.filter(
            areas__in=areas_gerente
        ).distinct().order_by('-fecha_registro')
        
        data = []
        
        for usuario in usuarios:
            # Obtener solo las áreas del usuario que coincidan con las del gerente
            areas_usuario = usuario.areas.filter(id__in=areas_gerente.values_list('id', flat=True))
            areas_nombres = ', '.join([area.nombre for area in areas_usuario])
            
            data.append({
                'id': usuario.id,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'email': usuario.correo_bdo,  # Enviar como email para compatibilidad frontend
                'tipo_usuario': usuario.tipo_usuario,
                'area': areas_nombres,
                'cargo_bdo': usuario.cargo_bdo,
                'activo': usuario.is_active,
                'ultimo_acceso': usuario.last_login,
                'fecha_creacion': usuario.fecha_registro,
            })
        
        return Response(data)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar que el email no exista ya
            correo_bdo = data.get('correo_bdo')
            if Usuario.objects.filter(correo_bdo=correo_bdo).exists():
                return Response({
                    'error': f'Ya existe un usuario con el email: {correo_bdo}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear usuario básico
            usuario = Usuario.objects.create_user(
                correo_bdo=correo_bdo,
                password=data.get('password'),  # Usar create_user para manejar la contraseña correctamente
                nombre=data.get('nombre'),
                apellido=data.get('apellido'),
                tipo_usuario=data.get('tipo_usuario', 'analista'),
                cargo_bdo=data.get('cargo_bdo', ''),
                is_active=data.get('is_active', True)
            )
            
            # Asignar área solo si está dentro de las áreas del gerente
            area_nombre = data.get('area')
            if area_nombre:
                areas_gerente = request.user.areas.all()
                area_permitida = areas_gerente.filter(nombre=area_nombre).first()
                
                if area_permitida:
                    usuario.areas.add(area_permitida)
                else:
                    return Response({
                        'error': f'No tienes permisos para asignar el área: {area_nombre}'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                'id': usuario.id,
                'message': 'Usuario creado exitosamente'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error creando usuario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_usuario(request, user_id):
    """
    Actualiza datos de un usuario específico
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verificar que el usuario a editar pertenezca a las áreas del gerente
        areas_gerente = request.user.areas.all()
        usuario = Usuario.objects.filter(
            id=user_id,
            areas__in=areas_gerente
        ).distinct().first()
        
        if not usuario:
            return Response({
                'error': 'Usuario no encontrado o no tienes permisos para editarlo'
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        
        usuario.nombre = data.get('nombre', usuario.nombre)
        usuario.apellido = data.get('apellido', usuario.apellido)
        usuario.correo_bdo = data.get('correo_bdo', usuario.correo_bdo)
        usuario.tipo_usuario = data.get('tipo_usuario', usuario.tipo_usuario)
        usuario.cargo_bdo = data.get('cargo_bdo', usuario.cargo_bdo)
        usuario.is_active = data.get('is_active', usuario.is_active)
        
        # Manejar área - solo permitir áreas del gerente
        area_nombre = data.get('area')
        if area_nombre:
            area_permitida = areas_gerente.filter(nombre=area_nombre).first()
            if area_permitida:
                # Limpiar áreas existentes que pertenezcan al gerente y agregar la nueva
                usuario.areas.remove(*areas_gerente)
                usuario.areas.add(area_permitida)
            else:
                return Response({
                    'error': f'No tienes permisos para asignar el área: {area_nombre}'
                }, status=status.HTTP_403_FORBIDDEN)
        
        usuario.save()
        
        return Response({
            'message': 'Usuario actualizado exitosamente'
        })
        
    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error actualizando usuario: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_usuario(request, user_id):
    """
    Elimina un usuario específico (solo gerentes pueden eliminar usuarios de sus áreas)
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verificar que el usuario a eliminar pertenezca a las áreas del gerente
        areas_gerente = request.user.areas.all()
        usuario = Usuario.objects.filter(
            id=user_id,
            areas__in=areas_gerente
        ).distinct().first()
        
        if not usuario:
            return Response({
                'error': 'Usuario no encontrado o no tienes permisos para eliminarlo'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # No permitir que un gerente se elimine a sí mismo
        if usuario.id == request.user.id:
            return Response({
                'error': 'No puedes eliminarte a ti mismo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar información del usuario antes de eliminarlo
        usuario_nombre = f"{usuario.nombre} {usuario.apellido}"
        
        # Eliminar usuario
        usuario.delete()
        
        return Response({
            'message': f'Usuario {usuario_nombre} eliminado exitosamente'
        })
        
    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error eliminando usuario: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gestionar_clientes(request):
    """
    GET: Lista todos los clientes del área de contabilidad
    POST: Crea un nuevo cliente con área de contabilidad
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Filtrar solo clientes del área de contabilidad
        from api.models import Area
        try:
            area_contabilidad = Area.objects.get(nombre='Contabilidad')
        except Area.DoesNotExist:
            return Response({'error': 'Área de Contabilidad no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener clientes que tienen área directa de contabilidad o servicios en contabilidad
        clientes_directos = Cliente.objects.filter(areas=area_contabilidad)
        clientes_servicios = Cliente.objects.filter(
            servicios_contratados__servicio__area=area_contabilidad
        ).exclude(id__in=clientes_directos.values_list('id', flat=True))
        
        # Combinar ambos querysets
        clientes = clientes_directos.union(clientes_servicios).order_by('-fecha_registro')
        
        data = []
        for cliente in clientes:
            # Obtener áreas efectivas
            areas_efectivas = cliente.get_areas_efectivas()
            
            data.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'rut': cliente.rut,
                'bilingue': cliente.bilingue,
                'industria': cliente.industria.nombre if cliente.industria else '',
                'industria_nombre': cliente.industria.nombre if cliente.industria else '',
                'fecha_registro': cliente.fecha_registro,
                'areas_efectivas': [{'nombre': area.nombre} for area in areas_efectivas]
            })
        
        return Response(data)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validar que el RUT no exista ya
            rut = data.get('rut')
            if Cliente.objects.filter(rut=rut).exists():
                return Response({
                    'error': f'Ya existe un cliente con el RUT: {rut}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Buscar industria si se proporciona
            industria = None
            industria_nombre = data.get('industria')
            if industria_nombre:
                from api.models import Industria
                industria = Industria.objects.filter(nombre=industria_nombre).first()
            
            cliente = Cliente.objects.create(
                nombre=data.get('nombre'),
                rut=rut,
                bilingue=data.get('bilingue', False),
                industria=industria
            )
            
            # Asignar áreas directas
            areas_nombres = data.get('areas', ['Contabilidad'])
            if areas_nombres:
                from api.models import Area
                areas_obj = Area.objects.filter(nombre__in=areas_nombres)
                cliente.areas.set(areas_obj)
            
            return Response({
                'id': cliente.id,
                'message': 'Cliente creado exitosamente',
                'areas_asignadas': areas_nombres
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error creando cliente: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_cliente(request, cliente_id):
    """
    Actualiza datos de un cliente específico incluyendo áreas directas
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        data = request.data
        
        # Validar RUT único si se está cambiando
        nuevo_rut = data.get('rut')
        if nuevo_rut and nuevo_rut != cliente.rut:
            if Cliente.objects.filter(rut=nuevo_rut).exists():
                return Response({
                    'error': f'Ya existe un cliente con el RUT: {nuevo_rut}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar campos disponibles en el modelo
        cliente.nombre = data.get('nombre', cliente.nombre)
        cliente.rut = data.get('rut', cliente.rut)
        cliente.bilingue = data.get('bilingue', cliente.bilingue)
        
        # Manejar industria
        industria_nombre = data.get('industria')
        if industria_nombre:
            from api.models import Industria
            industria = Industria.objects.filter(nombre=industria_nombre).first()
            cliente.industria = industria
        elif industria_nombre == '':  # Si se envía string vacío, remover industria
            cliente.industria = None
        
        # Actualizar áreas directas
        areas_nombres = data.get('areas')
        if areas_nombres is not None:
            from api.models import Area
            if areas_nombres:
                areas_obj = Area.objects.filter(nombre__in=areas_nombres)
                cliente.areas.set(areas_obj)
            else:
                cliente.areas.clear()
        
        cliente.save()
        
        return Response({
            'message': 'Cliente actualizado exitosamente',
            'areas_asignadas': areas_nombres or []
        })
        
    except Cliente.DoesNotExist:
        return Response({
            'error': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error actualizando cliente: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_cliente(request, cliente_id):
    """
    Elimina un cliente específico
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Verificar si el cliente tiene asignaciones activas
        asignaciones_activas = AsignacionClienteUsuario.objects.filter(cliente=cliente).count()
        if asignaciones_activas > 0:
            return Response({
                'error': f'No se puede eliminar el cliente {cliente.nombre} porque tiene asignaciones activas. Primero desasigna el cliente de todos los usuarios.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el cliente tiene cierres activos
        from ..models import CierreContabilidad
        cierres_activos = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias']
        ).count()
        
        if cierres_activos > 0:
            return Response({
                'error': f'No se puede eliminar el cliente {cliente.nombre} porque tiene cierres contables activos. Espera a que terminen los procesos en curso.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar información del cliente antes de eliminarlo
        cliente_nombre = cliente.nombre
        
        # Eliminar cliente
        cliente.delete()
        
        return Response({
            'message': f'Cliente {cliente_nombre} eliminado exitosamente'
        })
        
    except Cliente.DoesNotExist:
        return Response({
            'error': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error eliminando cliente: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_areas(request):
    """
    Obtiene lista de áreas disponibles para el gerente
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Obtener solo las áreas del gerente autenticado
        areas_gerente = request.user.areas.all().values_list('nombre', flat=True)
        return Response(list(areas_gerente))
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo áreas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_metricas_sistema(request):
    """
    Obtiene métricas generales del sistema
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Métricas básicas
        usuarios_totales = Usuario.objects.count()
        clientes_activos = Cliente.objects.count()  # Todos los clientes, no hay campo 'activo' en el modelo
        
        # Actividad hoy
        hoy = timezone.now().date()
        actividad_hoy = TarjetaActivityLog.objects.filter(
            timestamp__date=hoy
        ).count()
        
        # Registros en base de datos (estimación)
        registros_db = (
            Usuario.objects.count() +
            Cliente.objects.count() +
            CierreContabilidad.objects.count() +
            TarjetaActivityLog.objects.count()
        )
        
        # Estados de servicios (simulado)
        servicios = {
            'django': 'activo',
            'redis': 'activo',
            'postgresql': 'activo',
            'nginx': 'activo'
        }
        
        # Recursos del sistema (simulado)
        recursos = {
            'CPU': 45,
            'Memoria': 67,
            'Disco': 32,
            'Red': 23
        }
        
        return Response({
            'usuarios_totales': usuarios_totales,
            'clientes_activos': clientes_activos,
            'registros_db': registros_db,
            'actividad_hoy': actividad_hoy,
            'servicios': servicios,
            'recursos': recursos
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo métricas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_metricas_cache(request):
    """
    Obtiene métricas detalladas del cache Redis
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cache_system = get_cache_system()
        
        # Simular métricas de rendimiento
        metricas = {
            'hit_rate': 87.5,
            'ops_por_segundo': 1250,
            'clientes_conectados': 12,
            'comandos_procesados': 45280,
            'memoria_fragmentacion': 1.15,
            'tiempo_respuesta_promedio': 0.8
        }
        
        return Response(metricas)
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo métricas de cache: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def forzar_recalculo_cierre(request, cierre_id):
    """
    Fuerza el recálculo de un cierre específico
    """
    if request.user.tipo_usuario != 'gerente':
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
        
        # Resetear estado del cierre
        cierre.estado = 'pendiente'
        cierre.fecha_fin = None
        cierre.logs_error = []
        cierre.progreso_porcentaje = 0
        cierre.progreso_detalle = 'Recálculo iniciado por gerente'
        cierre.save()
        
        # Aquí se podría disparar una tarea asíncrona para recalcular
        # Por ahora solo actualizamos el estado
        
        return Response({
            'message': 'Recálculo del cierre iniciado',
            'cierre_id': cierre_id
        })
        
    except CierreContabilidad.DoesNotExist:
        return Response({
            'error': 'Cierre no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error forzando recálculo: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== USUARIOS CONECTADOS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_usuarios_conectados(request):
    """
    Obtiene la lista de usuarios conectados basado en actividad reciente.
    Opción B - Basado en actividad reciente de los logs (últimos 10 minutos).
    """
    try:
        from api.models import Area
        
        # Debug: Mostrar todas las áreas disponibles
        todas_areas = Area.objects.all().values_list('nombre', flat=True)
        print(f"[DEBUG] Áreas disponibles en el sistema: {list(todas_areas)}")
        
        now = timezone.now()
        
        # MÉTODO 1: Sesiones de Django (para admin)
        active_sessions = Session.objects.filter(expire_date__gte=now)
        session_user_ids = []
        for session in active_sessions:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            if user_id:
                session_user_ids.append(int(user_id))
        
        print(f"[DEBUG] Usuarios en sesiones Django: {session_user_ids}")
        
        # MÉTODO 2: Actividad reciente (últimos 10 minutos) - para frontend React
        hace_10_minutos = now - timedelta(minutes=10)
        usuarios_activos_recientes = TarjetaActivityLog.objects.filter(
            timestamp__gte=hace_10_minutos
        ).values_list('usuario_id', flat=True).distinct()
        
        print(f"[DEBUG] Usuarios con actividad reciente (últimos 10 min): {list(usuarios_activos_recientes)}")
        
        # Combinar ambos métodos
        connected_user_ids = list(set(session_user_ids + list(usuarios_activos_recientes)))
        print(f"[DEBUG] User IDs conectados (combinado): {connected_user_ids}")
        
        # Obtener información de todos los usuarios conectados
        usuarios_conectados = Usuario.objects.filter(
            id__in=connected_user_ids,
            is_active=True
        ).distinct().values(
            'id', 'nombre', 'apellido', 'correo_bdo', 'tipo_usuario'
        )
        
        print(f"[DEBUG] Usuarios conectados encontrados: {list(usuarios_conectados)}")
        
        # Obtener última actividad de cada usuario conectado
        usuarios_con_actividad = []
        for usuario in usuarios_conectados:
            # Buscar la actividad más reciente de este usuario
            ultima_actividad = TarjetaActivityLog.objects.filter(
                usuario_id=usuario['id']
            ).order_by('-timestamp').first()
            
            # Determinar el tipo de conexión
            tipo_conexion = "Sesión Web"  # Default
            if usuario['id'] in session_user_ids:
                tipo_conexion = "Django Admin"
            if usuario['id'] in usuarios_activos_recientes:
                if usuario['id'] in session_user_ids:
                    tipo_conexion = "Web + Admin"
                else:
                    tipo_conexion = "Plataforma React"
            
            usuario_info = {
                'id': usuario['id'],
                'nombre': f"{usuario['nombre']} {usuario['apellido']}",
                'email': usuario['correo_bdo'],
                'rol': usuario['tipo_usuario'],
                'ultima_actividad': ultima_actividad.timestamp.isoformat() if ultima_actividad else None,
                'cliente_actual': None,
                'tipo_conexion': tipo_conexion,
                'minutos_desde_actividad': None
            }
            
            # Calcular minutos desde última actividad
            if ultima_actividad:
                delta = now - ultima_actividad.timestamp
                usuario_info['minutos_desde_actividad'] = int(delta.total_seconds() / 60)
                
                # Obtener cliente actual - TarjetaActivityLog tiene campo 'cierre', no 'cliente_id'
                try:
                    cliente = ultima_actividad.cierre.cliente if ultima_actividad.cierre else None
                    usuario_info['cliente_actual'] = cliente.nombre if cliente else None
                except Exception as e:
                    print(f"[ERROR] Error obteniendo cliente del cierre: {e}")
                    pass
            
            usuarios_con_actividad.append(usuario_info)
        
        print(f"[DEBUG] Respuesta final: {usuarios_con_actividad}")
        
        return Response({
            'success': True,
            'usuarios_conectados': usuarios_con_actividad,
            'total_conectados': len(usuarios_con_actividad),
            'timestamp': now.isoformat(),
            'debug': {
                'total_sessions': active_sessions.count(),
                'session_user_ids': session_user_ids,
                'recent_activity_users': list(usuarios_activos_recientes),
                'connected_user_ids': connected_user_ids,
                'filtered_users': len(usuarios_con_actividad)
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo usuarios conectados: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Error obteniendo usuarios conectados: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
