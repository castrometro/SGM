# backend/nomina/views_activity_v2.py
"""
Vistas para el sistema de Activity Logging V2
Reemplaza las vistas antiguas del sistema V1
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
import logging

from .models import ActivityEvent, CierreNomina
from api.models import Cliente

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_activities(request):
    """
    Listar eventos de actividad con filtros
    
    GET /api/nomina/activity-log/
    Query params:
    - cliente_id: Filtrar por cliente
    - event_type: Filtrar por tipo (nomina, contabilidad, etc.)
    - resource_type: Filtrar por recurso
    - days: Últimos N días (default: 7)
    - limit: Límite de resultados (default: 100, max: 1000)
    """
    queryset = ActivityEvent.objects.select_related('user', 'cliente')
    
    # Filtrar por cliente si no es superuser
    if not request.user.is_superuser:
        # Obtener clientes asignados a través de AsignacionClienteUsuario
        clientes_ids = request.user.asignaciones.values_list('cliente_id', flat=True)
        queryset = queryset.filter(cliente_id__in=clientes_ids)
    
    # Aplicar filtros
    cliente_id = request.GET.get('cliente_id')
    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    
    event_type = request.GET.get('event_type')
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    resource_type = request.GET.get('resource_type')
    if resource_type:
        queryset = queryset.filter(resource_type=resource_type)
    
    session_id = request.GET.get('session_id')
    if session_id:
        queryset = queryset.filter(session_id=session_id)
    
    # Filtrar por días
    days = int(request.GET.get('days', 7))
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(timestamp__gte=cutoff_date)
    
    # Límite
    limit = min(int(request.GET.get('limit', 100)), 1000)
    events = queryset.order_by('-timestamp')[:limit]
    
    # Serializar
    data = [{
        'id': event.id,
        'timestamp': event.timestamp.isoformat(),
        'user_email': getattr(event.user, 'email', str(event.user)),
        'cliente_nombre': event.cliente.nombre,
        'event_type': event.event_type,
        'action': event.action,
        'resource_type': event.resource_type,
        'resource_id': event.resource_id,
        'details': event.details,
    } for event in events]
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_activity(request):
    """
    Registrar actividad manualmente desde el frontend
    
    POST /api/nomina/activity-log/log/
    Body:
    {
        "cliente_id": 1,
        "cierre_id": 30,           // ✅ NUEVO: ID del cierre
        "event_type": "nomina",
        "action": "modal_opened",
        "resource_type": "ingresos",
        "resource_id": "123",
        "details": {},
        "session_id": ""
    }
    """
    try:
        cliente_id = request.data.get('cliente_id')
        if not cliente_id:
            return Response(
                {'error': 'cliente_id requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Verificar acceso
        if not request.user.is_superuser:
            # Verificar que el usuario tiene asignado este cliente
            tiene_acceso = request.user.asignaciones.filter(cliente_id=cliente_id).exists()
            if not tiene_acceso:
                return Response(
                    {'error': 'Sin acceso a este cliente'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # ✅ Obtener cierre_id del request
        cierre_id = request.data.get('cierre_id', '')
        resource_id = request.data.get('resource_id', '')
        
        # ✅ Si tenemos cierre_id, usarlo como resource_id con tipo 'cierre'
        if cierre_id:
            resource_type = 'cierre'
            resource_id = str(cierre_id)
        else:
            resource_type = request.data.get('resource_type', 'general')
        
        event = ActivityEvent.log(
            user=request.user,
            cliente=cliente,
            event_type=request.data.get('event_type', 'manual'),
            action=request.data.get('action', 'manual_log'),
            resource_type=resource_type,           # ✅ Usar 'cierre' si tenemos cierre_id
            resource_id=resource_id,               # ✅ Usar cierre_id como resource_id
            details=request.data.get('details', {}),
            session_id=request.data.get('session_id', ''),
            request=request
        )
        
        return Response({
            'success': True,
            'event_id': event.id,
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cierre_activities(request, cierre_id):
    """
    Obtener actividad de un cierre específico
    
    GET /api/nomina/activity-log/cierre/{cierre_id}/
    
    Retorna todas las actividades relacionadas con este cierre.
    """
    cierre = get_object_or_404(CierreNomina, id=cierre_id)
    
    # Verificar acceso
    if not request.user.is_superuser:
        # Verificar que el usuario tiene asignado este cliente
        tiene_acceso = request.user.asignaciones.filter(cliente_id=cierre.cliente_id).exists()
        if not tiene_acceso:
            return Response(
                {'error': 'Sin acceso'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # ✅ Buscar por resource_type='cierre' Y resource_id=cierre_id
    events = ActivityEvent.objects.filter(
        resource_type='cierre',
        resource_id=str(cierre_id),
        cliente=cierre.cliente
    ).select_related('user').order_by('-timestamp')[:200]  # ✅ Aumentado límite a 200
    
    data = [{
        'id': e.id,
        'timestamp': e.timestamp.isoformat(),
        'user_email': getattr(e.user, 'email', str(e.user)),
        'action': e.action,
        'details': e.details,
    } for e in events]
    
    return Response({
        'cierre_id': cierre_id,
        'count': len(data),
        'events': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_stats(request):
    """
    Estadísticas de actividad
    
    GET /api/nomina/activity-log/stats/
    """
    queryset = ActivityEvent.objects.all()
    
    if not request.user.is_superuser:
        queryset = queryset.filter(cliente__in=request.user.clientes.all())
    
    days = int(request.GET.get('days', 7))
    cutoff = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(timestamp__gte=cutoff)
    
    # Contar por tipo
    event_counts = {}
    for et in queryset.values_list('event_type', flat=True).distinct():
        event_counts[et] = queryset.filter(event_type=et).count()
    
    return Response({
        'total': queryset.count(),
        'by_type': event_counts,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cierre_timeline(request, cierre_id):
    """
    Obtener timeline completo de todas las actividades de un cierre
    
    GET /api/nomina/cierre/{cierre_id}/timeline/
    
    Retorna un historial completo con todos los eventos que ocurrieron
    en el cierre: uploads, eliminaciones, procesamientos, errores, etc.
    
    Response:
    {
        "cierre_id": 30,
        "periodo": "2025-10",
        "cliente": "Cliente XYZ",
        "total_eventos": 47,
        "timeline": [
            {
                "timestamp": "2025-10-17T10:30:00Z",
                "seccion": "libro_remuneraciones",
                "evento": "upload_iniciado",
                "usuario": "Juan Pérez",
                "resultado": "ok",
                "datos": {...}
            },
            ...
        ],
        "resumen": {
            "uploads_exitosos": 5,
            "uploads_fallidos": 1,
            "eliminaciones": 2,
            "procesamiento_exitoso": 4,
            "errores": 1,
            "primera_actividad": "2025-10-17T10:00:00Z",
            "ultima_actividad": "2025-10-17T14:20:00Z"
        }
    }
    """
    from .models import ActivityEvent  # ✅ Importar desde models principal
    from django.db.models import Count, Q, Min, Max
    
    # Obtener cierre
    cierre = get_object_or_404(CierreNomina, id=cierre_id)
    
    # Verificar acceso
    if not request.user.is_superuser:
        tiene_acceso = request.user.asignaciones.filter(cliente_id=cierre.cliente_id).exists()
        if not tiene_acceso:
            return Response(
                {'error': 'Sin acceso a este cierre'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Obtener todos los eventos del cierre
    eventos = ActivityEvent.objects.filter(
        cierre_id=cierre_id
    ).select_related('usuario').order_by('timestamp')
    
    # Construir timeline
    timeline = []
    for e in eventos:
        timeline.append({
            'id': e.id,
            'timestamp': e.timestamp.isoformat(),
            'seccion': e.seccion,
            'evento': e.evento,
            'modulo': e.modulo,
            'usuario': e.usuario.get_full_name() if e.usuario_id else 'Sistema',
            'usuario_email': e.usuario.correo_bdo if e.usuario_id else None,
            'resultado': e.resultado,
            'datos': e.datos,
            'session_id': e.session_id,
        })
    
    # Generar resumen estadístico
    stats = eventos.aggregate(
        primera_actividad=Min('timestamp'),
        ultima_actividad=Max('timestamp'),
    )
    
    resumen = {
        'total_eventos': eventos.count(),
        'uploads_exitosos': eventos.filter(
            Q(evento__icontains='upload') | Q(evento__icontains='completado'),
            resultado='ok'
        ).count(),
        'uploads_fallidos': eventos.filter(
            Q(evento__icontains='upload') | Q(evento__icontains='validacion'),
            resultado='error'
        ).count(),
        'eliminaciones': eventos.filter(evento__icontains='eliminado').count(),
        'procesamiento_exitoso': eventos.filter(
            Q(evento__icontains='procesamiento') | Q(evento__icontains='analisis') | Q(evento__icontains='clasificacion'),
            resultado='ok'
        ).count(),
        'errores': eventos.filter(resultado='error').count(),
        'primera_actividad': stats['primera_actividad'].isoformat() if stats['primera_actividad'] else None,
        'ultima_actividad': stats['ultima_actividad'].isoformat() if stats['ultima_actividad'] else None,
    }
    
    # Agrupar por sección
    por_seccion = {}
    for seccion in eventos.values_list('seccion', flat=True).distinct():
        por_seccion[seccion] = eventos.filter(seccion=seccion).count()
    
    return Response({
        'cierre_id': cierre_id,
        'periodo': str(cierre.periodo),
        'cliente': cierre.cliente.razon_social,
        'cliente_id': cierre.cliente.id,
        'total_eventos': eventos.count(),
        'timeline': timeline,
        'resumen': resumen,
        'por_seccion': por_seccion,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exportar_cierre_log_txt(request, cierre_id):
    """
    Exportar historial del cierre como archivo de texto plano
    
    GET /api/nomina/cierre/{cierre_id}/log/export/txt/
    """
    from .models import ActivityEvent  # ✅ Importar desde models principal
    from django.http import HttpResponse
    
    # Obtener cierre
    cierre = get_object_or_404(CierreNomina, id=cierre_id)
    
    # Verificar acceso
    if not request.user.is_superuser:
        tiene_acceso = request.user.asignaciones.filter(cliente_id=cierre.cliente_id).exists()
        if not tiene_acceso:
            return Response(
                {'error': 'Sin acceso a este cierre'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Obtener eventos
    eventos = ActivityEvent.objects.filter(
        cierre_id=cierre_id
    ).select_related('usuario').order_by('timestamp')
    
    # Generar contenido de texto
    lines = []
    lines.append("=" * 80)
    lines.append(f"LOG DE ACTIVIDAD - CIERRE #{cierre_id}")
    lines.append(f"Cliente: {cierre.cliente.razon_social}")
    lines.append(f"Período: {cierre.periodo}")
    lines.append(f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    for evento in eventos:
        usuario = evento.usuario.get_full_name() if evento.usuario_id else 'Sistema'
        timestamp = evento.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        resultado_icon = "✅" if evento.resultado == 'ok' else "❌" if evento.resultado == 'error' else "⏱️"
        
        lines.append(f"{timestamp} - {usuario}")
        lines.append(f"  {resultado_icon} {evento.seccion}: {evento.evento}")
        
        if evento.datos:
            lines.append(f"  Datos: {evento.datos}")
        
        lines.append("")
    
    lines.append("=" * 80)
    lines.append(f"RESUMEN")
    lines.append(f"Total de eventos: {eventos.count()}")
    lines.append(f"Eventos exitosos: {eventos.filter(resultado='ok').count()}")
    lines.append(f"Eventos con error: {eventos.filter(resultado='error').count()}")
    lines.append("=" * 80)
    
    # Generar respuesta
    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="cierre_{cierre_id}_log.txt"'
    
    return response
