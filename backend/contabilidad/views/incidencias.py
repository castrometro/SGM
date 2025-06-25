# backend/contabilidad/views/incidencias.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ..models_incidencias import IncidenciaResumen, HistorialReprocesamiento, LogResolucionIncidencia
from ..models import CierreContabilidad, UploadLog
from api.models import Cliente


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_incidencias_consolidadas(request, cierre_id):
    """
    Obtiene las incidencias consolidadas para un cierre específico
    
    Query params:
    - estado: filtrar por estado (activa, resuelta, obsoleta)
    - severidad: filtrar por severidad (baja, media, alta, critica)
    - tipo: filtrar por tipo de incidencia
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Filtros
        estado = request.GET.get('estado')
        severidad = request.GET.get('severidad')
        tipo = request.GET.get('tipo')
        
        # Base queryset
        queryset = IncidenciaResumen.objects.filter(
            upload_log__cierre_id=cierre_id
        ).select_related('upload_log', 'resuelto_por')
        
        # Aplicar filtros
        if estado:
            queryset = queryset.filter(estado=estado)
        if severidad:
            queryset = queryset.filter(severidad=severidad)
        if tipo:
            queryset = queryset.filter(tipo_incidencia=tipo)
        
        # Obtener incidencias
        incidencias = []
        for inc in queryset.order_by('-severidad', '-fecha_deteccion'):
            incidencias.append({
                'id': inc.id,
                'tipo_incidencia': inc.get_tipo_incidencia_display(),
                'tipo_codigo': inc.tipo_incidencia,
                'codigo_problema': inc.codigo_problema,
                'cantidad_afectada': inc.cantidad_afectada,
                'severidad': inc.get_severidad_display(),
                'severidad_codigo': inc.severidad,
                'estado': inc.get_estado_display(),
                'estado_codigo': inc.estado,
                'mensaje_usuario': inc.mensaje_usuario,
                'accion_sugerida': inc.accion_sugerida,
                'elementos_afectados': inc.elementos_afectados[:10],  # Limitar para performance
                'detalle_muestra': inc.detalle_muestra,
                'estadisticas': inc.estadisticas_adicionales,
                'fecha_deteccion': inc.fecha_deteccion,
                'fecha_resolucion': inc.fecha_resolucion,
                'resuelto_por': inc.resuelto_por.username if inc.resuelto_por else None,
                'upload_log': {
                    'id': inc.upload_log.id,
                    'nombre_archivo': inc.upload_log.nombre_archivo_original,
                    'fecha_subida': inc.upload_log.fecha_subida,
                }
            })
        
        # Estadísticas resumen
        estadisticas = {
            'total_incidencias': queryset.count(),
            'por_estado': dict(queryset.values('estado').annotate(count=Count('id')).values_list('estado', 'count')),
            'por_severidad': dict(queryset.values('severidad').annotate(count=Count('id')).values_list('severidad', 'count')),
            'por_tipo': dict(queryset.values('tipo_incidencia').annotate(count=Count('id')).values_list('tipo_incidencia', 'count')),
        }
        
        return Response({
            'incidencias': incidencias,
            'estadisticas': estadisticas,
            'total_elementos_afectados': sum(inc.cantidad_afectada for inc in queryset),
            'cierre_info': {
                'id': cierre.id,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo incidencias: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_incidencias(request, cliente_id):
    """
    Dashboard ejecutivo de incidencias para un cliente
    """
    try:
        # Validar que el cliente existe
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Obtener últimos 3 cierres del cliente
        cierres_recientes = CierreContabilidad.objects.filter(
            cliente_id=cliente_id
        ).order_by('-periodo')[:3]
        
        if not cierres_recientes:
            return Response({
                'mensaje': 'No hay cierres disponibles para este cliente',
                'dashboard': {
                    'resumen_general': {
                        'total_incidencias': 0,
                        'incidencias_activas': 0,
                        'incidencias_resueltas': 0,
                        'porcentaje_resolucion': 100,
                    }
                }
            })
        
        # Obtener incidencias de los cierres recientes
        incidencias_query = IncidenciaResumen.objects.filter(
            upload_log__cierre__in=cierres_recientes
        )
        
        # Métricas generales
        total_incidencias = incidencias_query.count()
        incidencias_activas = incidencias_query.filter(estado='activa').count()
        incidencias_resueltas = incidencias_query.filter(estado='resuelta').count()
        
        # Distribución por severidad
        severidad_stats = dict(
            incidencias_query.values('severidad').annotate(
                count=Count('id')
            ).values_list('severidad', 'count')
        )
        
        # Top 5 tipos de problemas más frecuentes
        tipos_frecuentes = list(
            incidencias_query.filter(estado='activa').values(
                'tipo_incidencia'
            ).annotate(
                count=Count('id'),
                total_afectados=Sum('cantidad_afectada')
            ).order_by('-count')[:5]
        )
        
        # Incidencias críticas que requieren atención inmediata
        incidencias_criticas = []
        for inc in incidencias_query.filter(
            estado='activa', 
            severidad__in=['alta', 'critica']
        ).order_by('-severidad', '-cantidad_afectada')[:5]:
            incidencias_criticas.append({
                'id': inc.id,
                'tipo': inc.get_tipo_incidencia_display(),
                'codigo_problema': inc.codigo_problema,
                'cantidad_afectada': inc.cantidad_afectada,
                'severidad': inc.get_severidad_display(),
                'mensaje': inc.mensaje_usuario,
                'accion_sugerida': inc.accion_sugerida,
                'impacto_monetario': inc.estadisticas_adicionales.get('monto_total_afectado', 0),
                'cierre_periodo': inc.upload_log.cierre.periodo if inc.upload_log.cierre else None,
            })
        
        # Tendencia de resolución (últimos 3 cierres)
        tendencia = []
        for cierre in cierres_recientes:
            incidencias_cierre = IncidenciaResumen.objects.filter(
                upload_log__cierre=cierre
            )
            tendencia.append({
                'periodo': cierre.periodo,
                'total': incidencias_cierre.count(),
                'activas': incidencias_cierre.filter(estado='activa').count(),
                'resueltas': incidencias_cierre.filter(estado='resuelta').count(),
                'porcentaje_resolucion': (
                    (incidencias_cierre.filter(estado='resuelta').count() / incidencias_cierre.count() * 100)
                    if incidencias_cierre.count() > 0 else 100
                )
            })
        
        return Response({
            'dashboard': {
                'resumen_general': {
                    'total_incidencias': total_incidencias,
                    'incidencias_activas': incidencias_activas,
                    'incidencias_resueltas': incidencias_resueltas,
                    'porcentaje_resolucion': (
                        (incidencias_resueltas / total_incidencias * 100) 
                        if total_incidencias > 0 else 100
                    ),
                },
                'distribucion_severidad': severidad_stats,
                'tipos_frecuentes': tipos_frecuentes,
                'incidencias_criticas': incidencias_criticas,
                'tendencia_cierres': tendencia,
                'cierres_analizados': [
                    {
                        'id': c.id, 
                        'periodo': c.periodo,
                        'fecha_cierre': c.fecha_cierre
                    } for c in cierres_recientes
                ],
            },
            'cliente_info': {
                'id': cliente.id,
                'nombre': cliente.nombre,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error generando dashboard: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_incidencia_resuelta(request, incidencia_id):
    """
    Marca una incidencia como resuelta y registra el log correspondiente
    """
    try:
        incidencia = get_object_or_404(IncidenciaResumen, id=incidencia_id)
        
        # Validar que no esté ya resuelta
        if incidencia.estado == 'resuelta':
            return Response({
                'mensaje': 'La incidencia ya está marcada como resuelta'
            })
        
        # Marcar como resuelta
        incidencia.marcar_como_resuelta(usuario=request.user)
        
        # Crear log de resolución
        accion = request.data.get('accion_realizada', 'reprocesamiento')
        observaciones = request.data.get('observaciones', '')
        upload_log_relacionado_id = request.data.get('upload_log_relacionado_id')
        
        log_resolucion = LogResolucionIncidencia.objects.create(
            incidencia_resumen=incidencia,
            usuario=request.user,
            accion_realizada=accion,
            elementos_resueltos=incidencia.elementos_afectados,
            cantidad_resuelta=incidencia.cantidad_afectada,
            upload_log_relacionado_id=upload_log_relacionado_id,
            observaciones=observaciones,
            datos_adicionales={
                'fecha_resolucion_manual': timezone.now().isoformat(),
                'metodo_resolucion': 'manual',
                'usuario_resolucion': request.user.username,
            }
        )
        
        return Response({
            'mensaje': 'Incidencia marcada como resuelta exitosamente',
            'incidencia_id': incidencia.id,
            'log_resolucion_id': log_resolucion.id,
            'fecha_resolucion': incidencia.fecha_resolucion,
        })
        
    except Exception as e:
        return Response({
            'error': f'Error marcando incidencia como resuelta: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_reprocesamiento(request, upload_log_id):
    """
    Obtiene el historial de reprocesamiento para un upload_log específico
    """
    try:
        # Validar que el upload_log existe
        upload_log = get_object_or_404(UploadLog, id=upload_log_id)
        
        historial = HistorialReprocesamiento.objects.filter(
            upload_log_id=upload_log_id
        ).order_by('-iteracion')
        
        historial_data = []
        for h in historial:
            historial_data.append({
                'id': h.id,
                'iteracion': h.iteracion,
                'trigger': h.get_trigger_reprocesamiento_display(),
                'trigger_codigo': h.trigger_reprocesamiento,
                'usuario': h.usuario.username if h.usuario else None,
                'fecha_inicio': h.fecha_inicio,
                'tiempo_procesamiento': h.tiempo_procesamiento.total_seconds(),
                'incidencias_previas': h.incidencias_previas_count,
                'incidencias_nuevas': h.incidencias_nuevas_count,
                'incidencias_resueltas': h.incidencias_resueltas_count,
                'movimientos_corregidos': h.movimientos_corregidos,
                'movimientos_total': h.movimientos_total,
                'efectividad': h.calcular_efectividad(),
                'mejoras': h.obtener_mejoras(),
                'notas': h.notas,
            })
        
        return Response({
            'historial': historial_data,
            'total_iteraciones': len(historial_data),
            'upload_log_info': {
                'id': upload_log.id,
                'nombre_archivo': upload_log.nombre_archivo_original,
                'cliente': upload_log.cliente.nombre,
                'fecha_subida': upload_log.fecha_subida,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo historial: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen_tipos_incidencia(request):
    """
    Obtiene un resumen de todos los tipos de incidencia disponibles con sus descripciones
    """
    try:
        tipos_info = []
        for codigo, descripcion in IncidenciaResumen.TIPOS_INCIDENCIA:
            # Contar incidencias activas de este tipo
            count_activas = IncidenciaResumen.objects.filter(
                tipo_incidencia=codigo,
                estado='activa'
            ).count()
            
            tipos_info.append({
                'codigo': codigo,
                'descripcion': descripcion,
                'incidencias_activas': count_activas,
            })
        
        severidades_info = []
        for codigo, descripcion in IncidenciaResumen.SEVERIDAD_CHOICES:
            count = IncidenciaResumen.objects.filter(
                severidad=codigo,
                estado='activa'
            ).count()
            
            severidades_info.append({
                'codigo': codigo,
                'descripcion': descripcion,
                'incidencias_activas': count,
            })
        
        return Response({
            'tipos_incidencia': tipos_info,
            'severidades': severidades_info,
            'estados': [
                {'codigo': codigo, 'descripcion': desc}
                for codigo, desc in IncidenciaResumen.ESTADOS
            ]
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo tipos de incidencia: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_globales_incidencias(request):
    """
    Obtiene estadísticas globales de incidencias del sistema
    """
    try:
        # Estadísticas generales
        total_incidencias = IncidenciaResumen.objects.count()
        activas = IncidenciaResumen.objects.filter(estado='activa').count()
        resueltas = IncidenciaResumen.objects.filter(estado='resuelta').count()
        
        # Distribución por tipo
        tipos_distribution = dict(
            IncidenciaResumen.objects.values('tipo_incidencia').annotate(
                count=Count('id')
            ).values_list('tipo_incidencia', 'count')
        )
        
        # Clientes con más incidencias activas
        clientes_mas_incidencias = list(
            IncidenciaResumen.objects.filter(estado='activa')
            .values('upload_log__cliente__nombre')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        return Response({
            'resumen': {
                'total_incidencias': total_incidencias,
                'incidencias_activas': activas,
                'incidencias_resueltas': resueltas,
                'porcentaje_resolucion': (resueltas / total_incidencias * 100) if total_incidencias > 0 else 100,
            },
            'distribucion_tipos': tipos_distribution,
            'clientes_mas_incidencias': clientes_mas_incidencias,
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo estadísticas globales: {str(e)}'
        }, status=500)
