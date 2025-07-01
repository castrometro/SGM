# backend/contabilidad/views/incidencias.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from django.core.cache import cache
from django.db.models import Prefetch

from ..models_incidencias import IncidenciaResumen
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
        ).select_related('upload_log', 'resuelto_por', 'creada_por')
        
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
                'estadisticas': inc.estadisticas,  # Corregir nombre del campo
                'fecha_deteccion': inc.fecha_deteccion,
                'fecha_resolucion': inc.fecha_resolucion,
                'resuelto_por': inc.resuelto_por.correo_bdo if inc.resuelto_por else None,
                'creada_por': inc.creada_por.correo_bdo if inc.creada_por else None,
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
                'usuario': h.usuario.correo_bdo if h.usuario else None,
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


class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = IncidenciaResumen.objects.all()
    serializer_class = IncidenciaResumen
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get("cierre")
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset.order_by("-fecha_creacion")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_incidencias_consolidadas_libro_mayor(request, cierre_id):
    """
    Obtiene las incidencias consolidadas para un cierre específico,
    transformando las Incidencias básicas al formato esperado por el frontend
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Obtener incidencias básicas del cierre
        from ..models_incidencias import Incidencia
        incidencias_query = Incidencia.objects.filter(cierre_id=cierre_id)
        
        if not incidencias_query.exists():
            return Response({
                'incidencias': [],
                'estadisticas': {
                    'total_incidencias': 0,
                    'por_estado': {},
                    'por_severidad': {},
                    'por_tipo': {},
                },
                'total_elementos_afectados': 0,
                'cierre_info': {
                    'id': cierre.id,
                    'periodo': cierre.periodo,
                    'cliente': cierre.cliente.nombre,
                }
            })
        
        # Agrupar incidencias por tipo y consolidar
        from collections import defaultdict
        incidencias_agrupadas = defaultdict(list)
        
        for inc in incidencias_query:
            incidencias_agrupadas[inc.tipo].append(inc)
        
        # Transformar a formato consolidado
        incidencias_consolidadas = []
        
        for tipo, incidencias_list in incidencias_agrupadas.items():
            # Determinar severidad basada en la cantidad
            cantidad_total = len(incidencias_list)
            if cantidad_total >= 50:
                severidad = 'critica'
            elif cantidad_total >= 20:
                severidad = 'alta'
            elif cantidad_total >= 5:
                severidad = 'media'
            else:
                severidad = 'baja'
            
            # Crear mensaje descriptivo
            tipo_display = dict(Incidencia.TIPO_CHOICES).get(tipo, tipo)
            
            if tipo == Incidencia.CUENTA_NO_CLASIFICADA:
                mensaje_usuario = f"Se encontraron {cantidad_total} cuentas sin clasificación"
                accion_sugerida = "Revisar y clasificar las cuentas pendientes en el sistema de clasificaciones"
            elif tipo == Incidencia.CUENTA_SIN_INGLES:
                mensaje_usuario = f"Se encontraron {cantidad_total} cuentas sin traducción al inglés"
                accion_sugerida = "Completar las traducciones faltantes en la sección de Nombres en Inglés"
            elif tipo == Incidencia.DOC_NO_RECONOCIDO:
                mensaje_usuario = f"Se encontraron {cantidad_total} documentos con tipos no reconocidos"
                accion_sugerida = "Revisar y agregar los tipos de documento faltantes"
            elif tipo == Incidencia.DOC_NULL:
                mensaje_usuario = f"Se encontraron {cantidad_total} movimientos sin tipo de documento"
                accion_sugerida = "Corregir los movimientos que no tienen tipo de documento asignado"
            else:
                mensaje_usuario = f"Se encontraron {cantidad_total} incidencias de tipo {tipo_display}"
                accion_sugerida = "Revisar y corregir las incidencias detectadas"
            
            # Recopilar elementos afectados
            elementos_afectados = []
            cuentas_afectadas = set()
            docs_afectados = set()
            
            for inc in incidencias_list:
                if inc.cuenta_codigo:
                    cuentas_afectadas.add(inc.cuenta_codigo)
                    elementos_afectados.append({
                        'tipo': 'cuenta',
                        'codigo': inc.cuenta_codigo,
                        'descripcion': inc.descripcion or ''
                    })
                if inc.tipo_doc_codigo:
                    docs_afectados.add(inc.tipo_doc_codigo)
                    elementos_afectados.append({
                        'tipo': 'documento',
                        'codigo': inc.tipo_doc_codigo,
                        'descripcion': inc.descripcion or ''
                    })
            
            # Estadísticas adicionales
            estadisticas_adicionales = {
                'cuentas_unicas_afectadas': len(cuentas_afectadas),
                'documentos_unicos_afectados': len(docs_afectados),
                'primera_deteccion': min(inc.fecha_creacion for inc in incidencias_list).isoformat(),
                'ultima_deteccion': max(inc.fecha_creacion for inc in incidencias_list).isoformat(),
            }
            
            incidencias_consolidadas.append({
                'id': f"consolidada_{tipo}_{cierre_id}",  # ID sintético
                'tipo_incidencia': tipo,
                'tipo_codigo': tipo,
                'codigo_problema': tipo,
                'cantidad_afectada': cantidad_total,
                'severidad': severidad,
                'severidad_codigo': severidad,
                'estado': 'activa',
                'estado_codigo': 'activa',
                'mensaje_usuario': mensaje_usuario,
                'accion_sugerida': accion_sugerida,
                'elementos_afectados': elementos_afectados[:10],  # Limitar para performance
                'detalle_muestra': {
                    'primeros_ejemplos': [
                        {
                            'cuenta_codigo': inc.cuenta_codigo,
                            'tipo_doc_codigo': inc.tipo_doc_codigo,
                            'descripcion': inc.descripcion
                        } for inc in incidencias_list[:5]
                    ]
                },
                'estadisticas_adicionales': estadisticas_adicionales,
                'fecha_deteccion': min(inc.fecha_creacion for inc in incidencias_list),
                'fecha_resolucion': None,
                'resuelto_por': None,
            })
        
        # Ordenar por severidad y cantidad
        severidad_order = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
        incidencias_consolidadas.sort(
            key=lambda x: (severidad_order.get(x['severidad'], 4), -x['cantidad_afectada'])
        )
        
        # Estadísticas resumen
        total_incidencias = len(incidencias_consolidadas)
        estadisticas = {
            'total_incidencias': total_incidencias,
            'por_estado': {'activa': total_incidencias},
            'por_severidad': {},
            'por_tipo': {},
        }
        
        for inc in incidencias_consolidadas:
            sev = inc['severidad']
            tipo = inc['tipo_incidencia']
            estadisticas['por_severidad'][sev] = estadisticas['por_severidad'].get(sev, 0) + 1
            estadisticas['por_tipo'][tipo] = estadisticas['por_tipo'].get(tipo, 0) + 1
        
        return Response({
            'incidencias': incidencias_consolidadas,
            'estadisticas': estadisticas,
            'total_elementos_afectados': sum(inc['cantidad_afectada'] for inc in incidencias_consolidadas),
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
def obtener_cuentas_detalle_incidencia_libro_mayor(request, cierre_id, tipo_incidencia):
    """
    Obtiene el detalle de cuentas afectadas por un tipo específico de incidencia
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Obtener incidencias del tipo específico
        from ..models_incidencias import Incidencia
        incidencias_query = Incidencia.objects.filter(
            cierre_id=cierre_id,
            tipo=tipo_incidencia
        )
        
        if not incidencias_query.exists():
            return Response({
                'cuentas': [],
                'total': 0,
                'tipo_incidencia': tipo_incidencia,
                'descripcion_tipo': dict(Incidencia.TIPO_CHOICES).get(tipo_incidencia, tipo_incidencia)
            })
        
        # Preparar lista de cuentas afectadas
        cuentas_detalle = []
        
        for inc in incidencias_query:
            cuenta_info = {
                'codigo': inc.cuenta_codigo or inc.tipo_doc_codigo or 'N/A',
                'descripcion': inc.descripcion or '',
                'fecha_deteccion': inc.fecha_creacion,
                'tiene_excepcion': False,  # Por ahora siempre False
                'detalles': {
                    'incidencia_id': inc.id,
                    'cuenta_codigo': inc.cuenta_codigo,
                    'tipo_doc_codigo': inc.tipo_doc_codigo,
                }
            }
            cuentas_detalle.append(cuenta_info)
        
        # Ordenar por código
        cuentas_detalle.sort(key=lambda x: x['codigo'])
        
        return Response({
            'cuentas': cuentas_detalle,
            'total': len(cuentas_detalle),
            'tipo_incidencia': tipo_incidencia,
            'descripcion_tipo': dict(Incidencia.TIPO_CHOICES).get(tipo_incidencia, tipo_incidencia),
            'cierre_info': {
                'id': cierre.id,
                'periodo': cierre.periodo,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo detalle de cuentas: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_incidencias_consolidadas_snapshot(request, cierre_id):
    """
    Endpoint optimizado que usa snapshots de incidencias desde UploadLog
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Obtener último UploadLog de libro mayor para este cierre
        ultimo_upload = UploadLog.objects.filter(
            cierre_id=cierre_id,
            tipo_upload='libro_mayor',
            estado='completado'
        ).order_by('-iteracion').first()
        
        if not ultimo_upload:
            # No hay procesamiento de libro mayor - fallback al método actual
            return obtener_incidencias_consolidadas_libro_mayor(request, cierre_id)
        
        # Intentar usar snapshot si existe
        if ultimo_upload.resumen and 'incidencias_snapshot' in ultimo_upload.resumen:
            snapshot = ultimo_upload.resumen['incidencias_snapshot']
            
            return Response({
                'incidencias': snapshot['incidencias_detectadas'],
                'estadisticas': snapshot['estadisticas'],
                'total_elementos_afectados': snapshot['total_elementos_afectados'],
                'iteracion_info': {
                    'numero': ultimo_upload.iteracion,
                    'fecha': snapshot['timestamp'],
                    'upload_log_id': ultimo_upload.id,
                    'comparacion_anterior': snapshot.get('comparacion_anterior')
                },
                'cierre_info': {
                    'id': cierre.id,
                    'periodo': cierre.periodo,
                    'cliente': cierre.cliente.nombre,
                },
                '_source': 'snapshot',
                '_performance': {
                    'cached': True,
                    'calculation_time': '~0ms'
                }
            })
        
        # Fallback al método actual si no hay snapshot
        return obtener_incidencias_consolidadas_libro_mayor(request, cierre_id)
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo incidencias: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_historial_incidencias_por_iteraciones(request, cierre_id):
    """
    NUEVO: Obtiene el historial completo de incidencias por iteraciones
    """
    try:
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        uploads = UploadLog.objects.filter(
            cierre_id=cierre_id,
            tipo_upload='libro_mayor',
            estado='completado'
        ).order_by('-iteracion')
        
        historial = []
        for upload in uploads:
            snapshot = upload.resumen.get('incidencias_snapshot', {}) if upload.resumen else {}
            
            historial.append({
                'iteracion': upload.iteracion,
                'fecha': upload.fecha_subida,
                'tiempo_procesamiento': upload.tiempo_procesamiento.total_seconds() if upload.tiempo_procesamiento else None,
                'usuario': upload.usuario.nombre if upload.usuario else None,
                'archivo': upload.nombre_archivo_original,
                'total_incidencias': len(snapshot.get('incidencias_detectadas', [])),
                'total_elementos_afectados': snapshot.get('total_elementos_afectados', 0),
                'comparacion': snapshot.get('comparacion_anterior', {}),
                'estadisticas': snapshot.get('estadisticas', {}),
                'upload_log_id': upload.id,
                'snapshot_disponible': bool(snapshot)
            })
        
        return Response({
            'historial': historial,
            'total_iteraciones': len(historial),
            'cierre_info': {
                'id': cierre.id,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo historial: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_incidencias_consolidadas_optimizado(request, cierre_id):
    """
    Versión optimizada que utiliza snapshots de incidencias por iteración
    
    Query params:
    - iteracion: número de iteración específica (opcional, por defecto la principal)
    - estado: filtrar por estado (activa, resuelta, obsoleta)
    - severidad: filtrar por severidad (baja, media, alta, critica)
    - tipo: filtrar por tipo de incidencia
    - usar_cache: si usar caché (default: true)
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Parámetros
        iteracion = request.GET.get('iteracion')
        usar_cache = request.GET.get('usar_cache', 'true').lower() == 'true'
        
        # Generar clave de caché
        cache_key = f"incidencias_optimizado_{cierre_id}_{iteracion or 'principal'}"
        
        # Intentar obtener del caché
        if usar_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)
        
        # Determinar qué iteración usar
        if iteracion:
            # Iteración específica
            upload_logs = UploadLog.objects.filter(
                cierre_id=cierre_id,
                iteracion=int(iteracion)
            )
        else:
            # Iteración principal (más reciente)
            upload_logs = UploadLog.objects.filter(
                cierre_id=cierre_id,
                es_iteracion_principal=True
            )
        
        if not upload_logs.exists():
            return Response({
                'error': 'No se encontraron datos para la iteración especificada',
                'iteracion_solicitada': iteracion,
                'incidencias': [],
                'estadisticas': {},
                'metadata': {
                    'iteracion_actual': None,
                    'total_iteraciones': 0,
                    'es_iteracion_principal': False
                }
            }, status=404)
        
        # Filtros adicionales
        estado = request.GET.get('estado')
        severidad = request.GET.get('severidad')
        tipo = request.GET.get('tipo')
        
        # Obtener snapshot del primer upload log
        upload_log = upload_logs.first()
        
        # Verificar si hay snapshot disponible
        if upload_log.resumen and 'incidencias_snapshot' in upload_log.resumen:
            # Usar snapshot optimizado
            snapshot = upload_log.resumen['incidencias_snapshot']
            incidencias_snapshot = snapshot.get('incidencias_detectadas', [])
            
            # Aplicar filtros al snapshot
            incidencias = []
            for inc_data in incidencias_snapshot:
                # Aplicar filtros
                if estado and inc_data.get('estado_codigo') != estado:
                    continue
                if severidad and inc_data.get('severidad_codigo') != severidad:
                    continue
                if tipo and inc_data.get('tipo_codigo') != tipo:
                    continue
                    
                incidencias.append(inc_data)
            
            # Estadísticas del snapshot
            if incidencias:
                from collections import Counter
                estadisticas = {
                    'total_incidencias': len(incidencias),
                    'por_estado': dict(Counter(inc.get('estado_codigo') for inc in incidencias)),
                    'por_severidad': dict(Counter(inc.get('severidad_codigo') for inc in incidencias)),
                    'por_tipo': dict(Counter(inc.get('tipo_codigo') for inc in incidencias)),
                    'total_elementos_afectados': sum(inc.get('cantidad_afectada', 0) for inc in incidencias),
                }
            else:
                estadisticas = {
                    'total_incidencias': 0,
                    'por_estado': {},
                    'por_severidad': {},
                    'por_tipo': {},
                    'total_elementos_afectados': 0,
                }
        else:
            # Fallback a consulta directa si no hay snapshot
            queryset = IncidenciaResumen.objects.filter(
                upload_log__in=upload_logs
            ).select_related('upload_log', 'resuelto_por', 'creada_por')
            
            # Aplicar filtros
            if estado:
                queryset = queryset.filter(estado=estado)
            if severidad:
                queryset = queryset.filter(severidad=severidad)
            if tipo:
                queryset = queryset.filter(tipo_incidencia=tipo)
            
            # Obtener incidencias de forma tradicional
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
                    'elementos_afectados': inc.elementos_afectados[:10],
                    'detalle_muestra': inc.detalle_muestra,
                    'estadisticas': inc.estadisticas,
                    'fecha_deteccion': inc.fecha_deteccion,
                    'fecha_resolucion': inc.fecha_resolucion,
                    'resuelto_por': inc.resuelto_por.correo_bdo if inc.resuelto_por else None,
                    'creada_por': inc.creada_por.correo_bdo if inc.creada_por else None,
                    'upload_log': {
                        'id': inc.upload_log.id,
                        'nombre_archivo': inc.upload_log.nombre_archivo_original,
                        'fecha_subida': inc.upload_log.fecha_subida,
                        'iteracion': inc.upload_log.iteracion,
                        'es_iteracion_principal': inc.upload_log.es_iteracion_principal,
                    }
                })
            
            # Estadísticas tradicionales
            estadisticas = {
                'total_incidencias': queryset.count(),
                'por_estado': dict(queryset.values('estado').annotate(count=Count('id')).values_list('estado', 'count')),
                'por_severidad': dict(queryset.values('severidad').annotate(count=Count('id')).values_list('severidad', 'count')),
                'por_tipo': dict(queryset.values('tipo_incidencia').annotate(count=Count('id')).values_list('tipo_incidencia', 'count')),
                'total_elementos_afectados': sum(inc.cantidad_afectada for inc in queryset),
            }
        
        # Metadata de iteración
        iteracion_actual = upload_logs.first().iteracion if upload_logs.exists() else None
        total_iteraciones = UploadLog.objects.filter(cierre_id=cierre_id).values('iteracion').distinct().count()
        
        resultado = {
            'incidencias': incidencias,
            'estadisticas': estadisticas,
            'metadata': {
                'iteracion_actual': iteracion_actual,
                'total_iteraciones': total_iteraciones,
                'es_iteracion_principal': upload_logs.filter(es_iteracion_principal=True).exists(),
                'timestamp_consulta': timezone.now().isoformat(),
                'fuente': 'snapshot_optimizado'
            },
            'cierre_info': {
                'id': cierre.id,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
            }
        }
        
        # Guardar en caché por 5 minutos
        if usar_cache:
            cache.set(cache_key, resultado, 300)
        
        return Response(resultado)
        
    except ValueError as e:
        return Response({
            'error': f'Parámetro de iteración inválido: {str(e)}'
        }, status=400)
    except Exception as e:
        return Response({
            'error': f'Error obteniendo incidencias optimizadas: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_historial_incidencias(request, cierre_id):
    """
    Obtiene el historial de incidencias por iteración para un cierre específico
    
    Query params:
    - incluir_resueltas: incluir incidencias ya resueltas (default: false)
    - limite_iteraciones: máximo número de iteraciones a retornar (default: 10)
    """
    try:
        # Validar que el cierre existe
        cierre = get_object_or_404(CierreContabilidad, id=cierre_id)
        
        # Parámetros
        incluir_resueltas = request.GET.get('incluir_resueltas', 'false').lower() == 'true'
        limite_iteraciones = int(request.GET.get('limite_iteraciones', '10'))
        
        # Obtener todas las iteraciones del cierre
        iteraciones = UploadLog.objects.filter(
            cierre_id=cierre_id
        ).values('iteracion').distinct().order_by('-iteracion')[:limite_iteraciones]
        
        if not iteraciones:
            return Response({
                'historial': [],
                'resumen': {
                    'total_iteraciones': 0,
                    'iteracion_principal': None,
                    'tendencia_incidencias': 'sin_datos'
                }
            })
        
        historial = []
        contadores_iteraciones = []
        
        for iter_data in iteraciones:
            iteracion_num = iter_data['iteracion']
            
            # Upload logs de esta iteración
            upload_logs_iteracion = UploadLog.objects.filter(
                cierre_id=cierre_id,
                iteracion=iteracion_num
            )
            
            # Consulta de incidencias
            incidencias_query = IncidenciaResumen.objects.filter(
                upload_log__in=upload_logs_iteracion
            )
            
            if not incluir_resueltas:
                incidencias_query = incidencias_query.filter(estado__in=['activa', 'pendiente'])
            
            # Estadísticas de la iteración
            total_incidencias = incidencias_query.count()
            incidencias_criticas = incidencias_query.filter(severidad__in=['alta', 'critica']).count()
            incidencias_activas = incidencias_query.filter(estado='activa').count()
            
            # Distribución por tipo
            tipos_incidencias = dict(
                incidencias_query.values('tipo_incidencia').annotate(
                    count=Count('id')
                ).values_list('tipo_incidencia', 'count')
            )
            
            # Información de la iteración
            es_principal = upload_logs_iteracion.filter(es_iteracion_principal=True).exists()
            fecha_procesamiento = upload_logs_iteracion.order_by('fecha_subida').first().fecha_subida if upload_logs_iteracion.exists() else None
            
            iteracion_info = {
                'iteracion': iteracion_num,
                'es_principal': es_principal,
                'fecha_procesamiento': fecha_procesamiento,
                'estadisticas': {
                    'total_incidencias': total_incidencias,
                    'incidencias_criticas': incidencias_criticas,
                    'incidencias_activas': incidencias_activas,
                    'por_tipo': tipos_incidencias,
                    'por_severidad': dict(
                        incidencias_query.values('severidad').annotate(
                            count=Count('id')
                        ).values_list('severidad', 'count')
                    )
                },
                'archivos_procesados': list(
                    upload_logs_iteracion.values_list('nombre_archivo_original', flat=True)
                ),
                'total_elementos_afectados': sum(
                    inc.cantidad_afectada for inc in incidencias_query
                )
            }
            
            historial.append(iteracion_info)
            contadores_iteraciones.append(total_incidencias)
        
        # Determinar tendencia
        if len(contadores_iteraciones) >= 2:
            if contadores_iteraciones[0] < contadores_iteraciones[1]:
                tendencia = 'mejorando'
            elif contadores_iteraciones[0] > contadores_iteraciones[1]:
                tendencia = 'empeorando'
            else:
                tendencia = 'estable'
        else:
            tendencia = 'sin_suficientes_datos'
        
        # Iteración principal
        iteracion_principal = None
        for iter_info in historial:
            if iter_info['es_principal']:
                iteracion_principal = iter_info['iteracion']
                break
        
        return Response({
            'historial': historial,
            'resumen': {
                'total_iteraciones': len(historial),
                'iteracion_principal': iteracion_principal,
                'tendencia_incidencias': tendencia,
                'rango_fechas': {
                    'desde': historial[-1]['fecha_procesamiento'] if historial else None,
                    'hasta': historial[0]['fecha_procesamiento'] if historial else None,
                }
            },
            'cierre_info': {
                'id': cierre.id,
                'periodo': cierre.periodo,
                'cliente': cierre.cliente.nombre,
            }
        })
        
    except ValueError as e:
        return Response({
            'error': f'Parámetros inválidos: {str(e)}'
        }, status=400)
    except Exception as e:
        return Response({
            'error': f'Error obteniendo historial de incidencias: {str(e)}'
        }, status=500)
