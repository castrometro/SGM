# backend/api/views_gerente.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q, F, Max
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    Cliente, Usuario, AsignacionClienteUsuario, Area, Servicio, 
    ServicioCliente, Contrato
)
from .serializers import ClienteSerializer, UsuarioSerializer
from .permissions import IsGerente, IsAuthenticatedAndActive
from contabilidad.models import CierreContabilidad
from nomina.models import CierreNomina


# ========== GESTIÓN DE CLIENTES ==========

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def obtener_clientes_gerente(request):
    """
    Obtiene todos los clientes con información detallada para el gerente
    """
    gerente = request.user
    areas_gerente = gerente.areas.all()
    
    # Obtener clientes que tienen servicios en las áreas del gerente
    clientes = Cliente.objects.filter(
        servicios_contratados__servicio__area__in=areas_gerente
    ).distinct().prefetch_related(
        'asignaciones__usuario__areas',
        'servicios_contratados__servicio__area'
    )
    
    clientes_data = []
    for cliente in clientes:
        # Obtener áreas activas del cliente
        areas_activas = list(cliente.servicios_contratados.filter(
            servicio__area__in=areas_gerente
        ).values_list('servicio__area__nombre', flat=True).distinct())
        
        # Obtener analistas asignados
        asignaciones = cliente.asignaciones.select_related('usuario').prefetch_related('usuario__areas')
        analistas_asignados = []
        for asignacion in asignaciones:
            for area in asignacion.usuario.areas.filter(id__in=areas_gerente.values_list('id', flat=True)):
                analistas_asignados.append({
                    'id': asignacion.id,
                    'analista_id': asignacion.usuario.id,
                    'analista_nombre': f"{asignacion.usuario.nombre} {asignacion.usuario.apellido}",
                    'area': area.nombre,
                    'fecha_asignacion': asignacion.fecha_asignacion.strftime('%Y-%m-%d')
                })
        
        # Determinar estado de cierres (lógica simplificada)
        ultimo_cierre_contabilidad = CierreContabilidad.objects.filter(
            cliente=cliente
        ).order_by('-periodo').first()
        
        ultimo_cierre_nomina = CierreNomina.objects.filter(
            cliente=cliente
        ).order_by('-periodo').first()
        
        estado_cierres = 'al_dia'  # Por defecto
        ultimo_cierre = None
        
        if ultimo_cierre_contabilidad:
            ultimo_cierre = ultimo_cierre_contabilidad.periodo
            if ultimo_cierre_contabilidad.estado in ['atrasado', 'pendiente']:
                estado_cierres = 'atrasado'
        
        clientes_data.append({
            'id': cliente.id,
            'nombre': cliente.nombre,
            'rut': cliente.rut,
            'areas_activas': areas_activas,
            'analistas_asignados': analistas_asignados,
            'estado_cierres': estado_cierres,
            'ultimo_cierre': ultimo_cierre
        })
    
    return Response(clientes_data)


@api_view(['POST'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def reasignar_cliente(request):
    """
    Reasigna un cliente a un nuevo analista en un área específica
    """
    cliente_id = request.data.get('cliente_id')
    nuevo_analista_id = request.data.get('nuevo_analista_id')
    area_nombre = request.data.get('area')
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        nuevo_analista = Usuario.objects.get(id=nuevo_analista_id, tipo_usuario='analista')
        area = Area.objects.get(nombre=area_nombre)
        
        # Verificar que el gerente tenga acceso al área
        if area not in request.user.areas.all():
            return Response(
                {'error': 'No tienes permisos en esta área'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que el analista tenga esa área
        if area not in nuevo_analista.areas.all():
            return Response(
                {'error': 'El analista no pertenece a esta área'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Eliminar asignaciones existentes en esa área
        AsignacionClienteUsuario.objects.filter(
            cliente=cliente,
            usuario__areas=area
        ).delete()
        
        # Crear nueva asignación
        AsignacionClienteUsuario.objects.create(
            cliente=cliente,
            usuario=nuevo_analista
        )
        
        return Response({'success': True, 'message': 'Cliente reasignado exitosamente'})
        
    except (Cliente.DoesNotExist, Usuario.DoesNotExist, Area.DoesNotExist) as e:
        return Response(
            {'error': 'Recurso no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def perfil_completo_cliente(request, cliente_id):
    """
    Obtiene el perfil completo de un cliente con todas las métricas
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Verificar acceso del gerente
        areas_gerente = request.user.areas.all()
        if not cliente.servicios_contratados.filter(servicio__area__in=areas_gerente).exists():
            return Response(
                {'error': 'No tienes acceso a este cliente'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Información básica
        perfil = {
            'id': cliente.id,
            'nombre': cliente.nombre,
            'rut': cliente.rut,
            'industria': cliente.industria.nombre if cliente.industria else None,
            'fecha_inicio': None,  # Se puede obtener del primer contrato
        }
        
        # Servicios contratados
        servicios = cliente.servicios_contratados.filter(
            servicio__area__in=areas_gerente
        ).select_related('servicio__area')
        
        perfil['servicios_contratados'] = [
            {
                'id': sc.id,
                'servicio_nombre': sc.servicio.nombre,
                'area': sc.servicio.area.nombre,
                'fecha_inicio': sc.fecha_inicio,
                'valor_mensual': float(sc.valor_mensual) if sc.valor_mensual else 0
            } for sc in servicios
        ]
        
        # Analistas asignados
        asignaciones = cliente.asignaciones.select_related('usuario').prefetch_related('usuario__areas')
        perfil['analistas_asignados'] = [
            {
                'id': asig.id,
                'analista_id': asig.usuario.id,
                'analista_nombre': f"{asig.usuario.nombre} {asig.usuario.apellido}",
                'area': ', '.join([area.nombre for area in asig.usuario.areas.filter(id__in=areas_gerente.values_list('id', flat=True))]),
                'fecha_asignacion': asig.fecha_asignacion.strftime('%Y-%m-%d')
            } for asig in asignaciones
        ]
        
        # Métricas de rendimiento (simuladas por ahora)
        perfil.update({
            'total_cierres': 24,
            'cierres_tiempo': 22,
            'tiempo_promedio_cierre': 5,
            'sla_cumplimiento': 92,
            'satisfaccion_score': 8.5,
            'valor_mensual_total': sum([s['valor_mensual'] for s in perfil['servicios_contratados']]),
            'rentabilidad': 'Alta',
            'riesgo_nivel': 'Bajo'
        })
        
        return Response(perfil)
        
    except Cliente.DoesNotExist:
        return Response(
            {'error': 'Cliente no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ========== MÉTRICAS Y KPIs ==========

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def metricas_avanzadas(request):
    """
    Obtiene métricas avanzadas para el dashboard del gerente
    """
    gerente = request.user
    areas_gerente = gerente.areas.all()
    
    # Filtros
    area_filtro = request.GET.get('area')
    periodo_filtro = request.GET.get('periodo', 'month')
    
    # Fecha base para filtros
    if periodo_filtro == 'week':
        fecha_inicio = timezone.now() - timedelta(days=7)
    elif periodo_filtro == 'month':
        fecha_inicio = timezone.now() - timedelta(days=30)
    elif periodo_filtro == 'quarter':
        fecha_inicio = timezone.now() - timedelta(days=90)
    else:
        fecha_inicio = timezone.now() - timedelta(days=30)
    
    # Clientes en las áreas del gerente
    clientes_query = Cliente.objects.filter(
        servicios_contratados__servicio__area__in=areas_gerente
    ).distinct()
    
    if area_filtro:
        area_obj = Area.objects.filter(nombre=area_filtro, id__in=areas_gerente).first()
        if area_obj:
            clientes_query = clientes_query.filter(
                servicios_contratados__servicio__area=area_obj
            )
    
    # Analistas en las áreas del gerente
    analistas = Usuario.objects.filter(
        tipo_usuario='analista',
        areas__in=areas_gerente
    ).distinct()
    
    # Métricas básicas
    total_clientes = clientes_query.count()
    total_analistas = analistas.count()
    
    # Clientes asignados vs sin asignar
    clientes_asignados = clientes_query.filter(asignaciones__isnull=False).distinct().count()
    clientes_sin_asignar = total_clientes - clientes_asignados
    
    # Cierres recientes
    cierres_contabilidad = CierreContabilidad.objects.filter(
        cliente__in=clientes_query,
        fecha_creacion__gte=fecha_inicio
    ).count()
    
    cierres_nomina = CierreNomina.objects.filter(
        cliente__in=clientes_query,
        fecha_creacion__gte=fecha_inicio
    ).count()
    
    # KPIs calculados
    promedio_clientes_por_analista = round(total_clientes / total_analistas, 1) if total_analistas > 0 else 0
    porcentaje_asignacion = round((clientes_asignados / total_clientes) * 100, 1) if total_clientes > 0 else 0
    
    # Tendencias (datos simulados por ahora)
    tendencia_cierres = [
        {'periodo': '2024-01', 'cierres': 45},
        {'periodo': '2024-02', 'cierres': 52},
        {'periodo': '2024-03', 'cierres': 48},
        {'periodo': '2024-04', 'cierres': 55},
        {'periodo': '2024-05', 'cierres': 62},
        {'periodo': '2024-06', 'cierres': 58},
    ]
    
    distribucion_areas = []
    for area in areas_gerente:
        clientes_area = clientes_query.filter(
            servicios_contratados__servicio__area=area
        ).distinct().count()
        distribucion_areas.append({
            'area': area.nombre,
            'clientes': clientes_area,
            'porcentaje': round((clientes_area / total_clientes) * 100, 1) if total_clientes > 0 else 0
        })
    
    return Response({
        'resumen': {
            'total_clientes': total_clientes,
            'total_analistas': total_analistas,
            'clientes_asignados': clientes_asignados,
            'clientes_sin_asignar': clientes_sin_asignar,
            'cierres_periodo': cierres_contabilidad + cierres_nomina,
            'promedio_clientes_analista': promedio_clientes_por_analista,
            'porcentaje_asignacion': porcentaje_asignacion
        },
        'tendencias': {
            'cierres_mensuales': tendencia_cierres,
            'distribucion_areas': distribucion_areas
        },
        'kpis': {
            'eficiencia_equipo': 85,  # Simulado
            'tiempo_promedio_cierre': 5.2,  # Simulado
            'satisfaccion_promedio': 8.3,  # Simulado
            'sla_cumplimiento': 92  # Simulado
        }
    })


# ========== ANÁLISIS DE PORTAFOLIO ==========

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def analisis_portafolio(request):
    """
    Análisis completo del portafolio de clientes
    """
    gerente = request.user
    areas_gerente = gerente.areas.all()
    vista_tipo = request.GET.get('vista', 'valor')  # valor, crecimiento, riesgo
    
    clientes = Cliente.objects.filter(
        servicios_contratados__servicio__area__in=areas_gerente
    ).distinct()
    
    total_clientes = clientes.count()
    
    # Calcular valor total del portafolio (basado en servicios contratados)
    valor_total_portafolio = 0
    for cliente in clientes:
        servicios_cliente = cliente.servicios_contratados.filter(
            servicio__area__in=areas_gerente
        )
        for servicio in servicios_cliente:
            if servicio.valor_mensual:
                valor_total_portafolio += float(servicio.valor_mensual)
    
    # Matriz de segmentación (5x5 grid con datos más realistas)
    matriz_segmentacion = [
        {
            'nombre': 'Premium Estable',
            'clientes_count': 8,
            'valor': 750000,
            'rentabilidad': 35,
            'riesgo': 2,
            'crecimiento': 12
        },
        {
            'nombre': 'Premium Crecimiento',
            'clientes_count': 4,
            'valor': 850000,
            'rentabilidad': 28,
            'riesgo': 4,
            'crecimiento': 25
        },
        {
            'nombre': 'Alto Valor',
            'clientes_count': 12,
            'valor': 450000,
            'rentabilidad': 32,
            'riesgo': 3,
            'crecimiento': 8
        },
        {
            'nombre': 'Medio Estable',
            'clientes_count': 18,
            'valor': 180000,
            'rentabilidad': 22,
            'riesgo': 4,
            'crecimiento': 5
        },
        {
            'nombre': 'Medio Volátil',
            'clientes_count': 10,
            'valor': 220000,
            'rentabilidad': 18,
            'riesgo': 7,
            'crecimiento': 15
        },
        {
            'nombre': 'Básico Plus',
            'clientes_count': 15,
            'valor': 95000,
            'rentabilidad': 25,
            'riesgo': 5,
            'crecimiento': 3
        },
        {
            'nombre': 'Básico Standard',
            'clientes_count': 22,
            'valor': 65000,
            'rentabilidad': 20,
            'riesgo': 6,
            'crecimiento': 2
        },
        {
            'nombre': 'Entrada',
            'clientes_count': 8,
            'valor': 35000,
            'rentabilidad': 15,
            'riesgo': 8,
            'crecimiento': -2
        }
    ]
    
    # Top clientes por diferentes categorías (datos más realistas)
    top_clientes_valor = [
        {'id': 1, 'nombre': 'Corporación Financiera ABC', 'valor_mensual': 950000, 'industria': 'Finanzas'},
        {'id': 2, 'nombre': 'Tech Solutions SpA', 'valor_mensual': 780000, 'industria': 'Tecnología'},
        {'id': 3, 'nombre': 'Retail Group Chile', 'valor_mensual': 650000, 'industria': 'Retail'},
        {'id': 4, 'nombre': 'Constructora Del Sur', 'valor_mensual': 520000, 'industria': 'Construcción'},
        {'id': 5, 'nombre': 'Servicios Logísticos Pro', 'valor_mensual': 480000, 'industria': 'Logística'}
    ]
    
    top_clientes_crecimiento = [
        {'id': 6, 'nombre': 'StartUp AI Vision', 'crecimiento_anual': 85, 'industria': 'Tecnología'},
        {'id': 7, 'nombre': 'EcoEnergy Solutions', 'crecimiento_anual': 62, 'industria': 'Energía'},
        {'id': 8, 'nombre': 'HealthTech Innovate', 'crecimiento_anual': 45, 'industria': 'Salud'},
        {'id': 9, 'nombre': 'Digital Marketing Plus', 'crecimiento_anual': 38, 'industria': 'Marketing'},
        {'id': 10, 'nombre': 'AgriTech Futuro', 'crecimiento_anual': 32, 'industria': 'Agricultura'}
    ]
    
    top_clientes_rentabilidad = [
        {'id': 11, 'nombre': 'Consultora Premium', 'rentabilidad': 42, 'industria': 'Consultoría'},
        {'id': 12, 'nombre': 'Software House Elite', 'rentabilidad': 38, 'industria': 'Tecnología'},
        {'id': 13, 'nombre': 'Firma Legal Asociados', 'rentabilidad': 35, 'industria': 'Legal'},
        {'id': 14, 'nombre': 'Inversiones Global', 'rentabilidad': 33, 'industria': 'Finanzas'},
        {'id': 15, 'nombre': 'Arquitectura & Diseño', 'rentabilidad': 30, 'industria': 'Diseño'}
    ]
    
    clientes_alto_riesgo = [
        {'id': 16, 'nombre': 'Comercial en Crisis', 'score_riesgo': 8.5, 'industria': 'Comercio'},
        {'id': 17, 'nombre': 'Manufactura Obsoleta', 'score_riesgo': 8.1, 'industria': 'Manufactura'},
        {'id': 18, 'nombre': 'Transporte Antiguo', 'score_riesgo': 7.8, 'industria': 'Transporte'},
        {'id': 19, 'nombre': 'Retail Tradicional', 'score_riesgo': 7.5, 'industria': 'Retail'},
        {'id': 20, 'nombre': 'Servicios Básicos Ltda', 'score_riesgo': 7.2, 'industria': 'Servicios'}
    ]
    
    return Response({
        'valor_total_portafolio': int(valor_total_portafolio),
        'total_clientes_activos': total_clientes,
        'crecimiento_clientes': 8.5,  # Porcentaje vs mes anterior
        'rentabilidad_promedio': 24.8,
        'riesgo_promedio': 5.2,
        'matriz_segmentacion': matriz_segmentacion,
        'top_clientes_valor': top_clientes_valor,
        'top_clientes_crecimiento': top_clientes_crecimiento,
        'top_clientes_rentabilidad': top_clientes_rentabilidad,
        'clientes_alto_riesgo': clientes_alto_riesgo,
        'concentracion_industria': [
            {'industria': 'Tecnología', 'porcentaje': 28.5},
            {'industria': 'Finanzas', 'porcentaje': 22.1},
            {'industria': 'Retail', 'porcentaje': 18.3},
            {'industria': 'Manufactura', 'porcentaje': 12.7},
            {'industria': 'Servicios', 'porcentaje': 10.8},
            {'industria': 'Otros', 'porcentaje': 7.6}
        ],
        'concentracion_tamano': [
            {'segmento': 'Grande (>$500K)', 'porcentaje': 35.2},
            {'segmento': 'Mediano ($100K-$500K)', 'porcentaje': 42.8},
            {'segmento': 'Pequeño (<$100K)', 'porcentaje': 22.0}
        ],
        'concentracion_area': [
            {'area': area.nombre, 'porcentaje': round(100 / len(areas_gerente), 1)}
            for area in areas_gerente
        ]
    })


# ========== SISTEMA DE ALERTAS ==========

@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def obtener_alertas(request):
    """
    Obtiene las alertas del sistema para el gerente
    """
    # Por ahora simulamos las alertas, en el futuro se pueden implementar en BD
    alertas = [
        {
            'id': 1,
            'tipo': 'cierre_atrasado',
            'prioridad': 'alta',
            'titulo': 'Cierre de Marzo atrasado',
            'mensaje': 'Cliente ABC Corp tiene su cierre de marzo pendiente hace 5 días',
            'fecha': timezone.now() - timedelta(hours=2),
            'leida': False,
            'cliente_id': 1,
            'analista_id': 2
        },
        {
            'id': 2,
            'tipo': 'sobrecarga_analista',
            'prioridad': 'media',
            'titulo': 'Analista con sobrecarga',
            'mensaje': 'Juan Pérez tiene 15 clientes asignados (límite recomendado: 12)',
            'fecha': timezone.now() - timedelta(hours=5),
            'leida': False,
            'analista_id': 2
        },
        {
            'id': 3,
            'tipo': 'nuevo_cliente',
            'prioridad': 'baja',
            'titulo': 'Nuevo cliente sin asignar',
            'mensaje': 'Cliente XYZ Ltda requiere asignación de analista',
            'fecha': timezone.now() - timedelta(hours=8),
            'leida': True,
            'cliente_id': 3
        }
    ]
    
    # Filtros
    prioridad = request.GET.get('prioridad')
    tipo = request.GET.get('tipo')
    solo_no_leidas = request.GET.get('no_leidas') == 'true'
    
    alertas_filtradas = alertas
    
    if prioridad:
        alertas_filtradas = [a for a in alertas_filtradas if a['prioridad'] == prioridad]
    
    if tipo:
        alertas_filtradas = [a for a in alertas_filtradas if a['tipo'] == tipo]
    
    if solo_no_leidas:
        alertas_filtradas = [a for a in alertas_filtradas if not a['leida']]
    
    # Convertir fechas a string
    for alerta in alertas_filtradas:
        alerta['fecha'] = alerta['fecha'].strftime('%Y-%m-%d %H:%M:%S')
    
    return Response({
        'alertas': alertas_filtradas,
        'resumen': {
            'total': len(alertas),
            'no_leidas': len([a for a in alertas if not a['leida']]),
            'alta_prioridad': len([a for a in alertas if a['prioridad'] == 'alta']),
            'por_tipo': {
                'cierre_atrasado': len([a for a in alertas if a['tipo'] == 'cierre_atrasado']),
                'sobrecarga_analista': len([a for a in alertas if a['tipo'] == 'sobrecarga_analista']),
                'nuevo_cliente': len([a for a in alertas if a['tipo'] == 'nuevo_cliente'])
            }
        }
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def marcar_alerta_leida(request, alerta_id):
    """
    Marca una alerta como leída
    """
    # Por ahora solo retornamos success, en el futuro actualizaríamos la BD
    return Response({'success': True, 'message': f'Alerta {alerta_id} marcada como leída'})


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def obtener_configuracion_alertas(request):
    """
    Obtiene la configuración actual de alertas para el gerente
    """
    # Por ahora retornamos una configuración por defecto
    # En el futuro se puede guardar en la BD asociada al usuario
    configuracion_default = {
        'cierre_atrasado_dias': 3,
        'sobrecarga_clientes': 12,
        'sla_critico': 85,
        'notificaciones_email': True,
        'notificaciones_push': True,
        'alertas_activas': {
            'cierre_atrasado': True,
            'sobrecarga_analista': True,
            'nuevo_cliente': True,
            'sla_critico': True,
            'error_sistema': False
        }
    }
    
    return Response(configuracion_default)


@api_view(['POST'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def configurar_alertas(request):
    """
    Guarda la configuración de alertas del gerente
    """
    configuracion = request.data
    
    # Validar configuración
    if 'cierre_atrasado_dias' in configuracion:
        if not isinstance(configuracion['cierre_atrasado_dias'], int) or configuracion['cierre_atrasado_dias'] < 1:
            return Response(
                {'error': 'Los días de atraso deben ser un número entero mayor a 0'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if 'sobrecarga_clientes' in configuracion:
        if not isinstance(configuracion['sobrecarga_clientes'], int) or configuracion['sobrecarga_clientes'] < 1:
            return Response(
                {'error': 'El límite de clientes debe ser un número entero mayor a 0'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # En el futuro, aquí se guardaría en la BD
    # Por ahora solo confirmamos que se recibió
    
    return Response({
        'success': True, 
        'message': 'Configuración de alertas actualizada',
        'configuracion': configuracion
    })


# ========== REPORTES ==========

@api_view(['POST'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def generar_reporte(request):
    """
    Genera un reporte según los parámetros especificados
    """
    tipo_reporte = request.data.get('tipo')
    parametros = request.data.get('parametros', {})
    
    # Simulamos la generación del reporte
    reporte_id = f"RPT-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    
    reporte_info = {
        'id': reporte_id,
        'tipo': tipo_reporte,
        'estado': 'generando',
        'fecha_creacion': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'parametros': parametros,
        'url_descarga': None
    }
    
    # En una implementación real, aquí se iniciaría una tarea async
    # Por ahora simulamos que el reporte se genera inmediatamente
    reporte_info.update({
        'estado': 'completado',
        'url_descarga': f'/api/gerente/reportes/{reporte_id}/descargar/'
    })
    
    return Response(reporte_info)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def historial_reportes(request):
    """
    Obtiene el historial de reportes generados
    """
    limite = int(request.GET.get('limite', 20))
    
    # Simulamos un historial de reportes
    reportes = [
        {
            'id': 'RPT-202406151430',
            'tipo': 'rendimiento_equipo',
            'fecha_creacion': '2024-06-15 14:30:00',
            'estado': 'completado',
            'tamaño': '2.5 MB'
        },
        {
            'id': 'RPT-202406141200',
            'tipo': 'analisis_portafolio',
            'fecha_creacion': '2024-06-14 12:00:00',
            'estado': 'completado',
            'tamaño': '3.8 MB'
        },
        {
            'id': 'RPT-202406131015',
            'tipo': 'kpis_mensuales',
            'fecha_creacion': '2024-06-13 10:15:00',
            'estado': 'completado',
            'tamaño': '1.2 MB'
        }
    ]
    
    return Response(reportes[:limite])


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive & IsGerente])
def descargar_reporte(request, reporte_id):
    """
    Descarga un reporte específico
    """
    # En una implementación real, buscaríamos el reporte en la base de datos
    # y devolveríamos el archivo correspondiente
    
    # Por ahora, simulamos un archivo Excel
    import openpyxl
    from django.http import HttpResponse
    import io
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte"
    
    # Headers de ejemplo
    ws.append(['Campo 1', 'Campo 2', 'Campo 3'])
    ws.append(['Dato 1', 'Dato 2', 'Dato 3'])
    ws.append(['Información simulada', 'Para el reporte', reporte_id])
    
    # Guardar el workbook en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_{reporte_id}.xlsx"'
    
    return response
