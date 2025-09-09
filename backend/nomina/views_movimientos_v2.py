from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import CierreNomina, MovimientoPersonal


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movimientos_personal_resumen_v2(request, cierre_id: int):
    """🔄 Resumen simplificado de Movimientos de Personal (V2)

    Incluye solo: ingresos, finiquitos y ausentismos del periodo.
    Estructura:
    cierre: { id, cliente, periodo }
    resumen: { total_movimientos, ingreso, finiquito, ausentismo, por_tipo:{}, ausentismo_metricas:{ eventos, total_dias, promedio_dias } }
    movimientos: [ { id, tipo_movimiento, tipo_display, empleado:{ rut,nombre,cargo,centro_costo,estado,liquido_pagar }, dias_ausencia, motivo, fecha_movimiento, fecha_deteccion, detectado_por_sistema } ]
    meta: { generated_at, api_version }
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        if not cierre.nomina_consolidada.exists():
            return Response({'error': 'No hay datos consolidados para este cierre'}, status=status.HTTP_404_NOT_FOUND)

        tipos_incluidos = ['ingreso', 'finiquito', 'ausentismo']
        qs = (MovimientoPersonal.objects
              .filter(nomina_consolidada__cierre=cierre, tipo_movimiento__in=tipos_incluidos)
              .select_related('nomina_consolidada')
              .order_by('-fecha_deteccion'))

        por_tipo = {}
        total = 0
        # Construimos sets de empleados únicos por tipo en un solo recorrido para eficiencia
        empleados_por_tipo = { t: set() for t in tipos_incluidos }
        for mv in qs:
            t = mv.tipo_movimiento
            if t in empleados_por_tipo:
                rut = mv.nomina_consolidada.rut_empleado if mv.nomina_consolidada else None
                if rut:
                    empleados_por_tipo[t].add(rut)
        for tipo, display in MovimientoPersonal.TIPO_MOVIMIENTO_CHOICES:
            if tipo not in tipos_incluidos:
                continue
            c = qs.filter(tipo_movimiento=tipo).count()
            total += c
            por_tipo[tipo] = {
                'count': c,
                'display': display,
                'empleados_unicos': len(empleados_por_tipo.get(tipo, [])),
            }

        aus_qs = qs.filter(tipo_movimiento='ausentismo')
        eventos_aus = aus_qs.count()
        total_dias = 0
        # Agregaciones usando campos normalizados cuando existan
        motivos_map = {}
        subtipos_map = {}
        tipos_inasistencias_map = {}
        for mv in aus_qs:
            # Priorizar dias_en_periodo (imputable) luego dias_evento luego dias_ausencia
            dias = (mv.dias_en_periodo if mv.dias_en_periodo is not None else (mv.dias_evento if mv.dias_evento is not None else (mv.dias_ausencia or 0)))
            total_dias += dias
            raw_motivo = (mv.motivo or mv.descripcion or '').strip() or 'Sin motivo'
            # Motivos (compatibilidad frontend actual)
            m = motivos_map.get(raw_motivo) or { 'motivo': raw_motivo, 'eventos': 0, 'dias': 0 }
            m['eventos'] += 1
            m['dias'] += dias
            motivos_map[raw_motivo] = m
            # Subtipos normalizados
            subtipo = (mv.subtipo or '').strip() or 'sin_justificar'
            s_obj = subtipos_map.get(subtipo) or { 'subtipo': subtipo, 'eventos': 0, 'dias': 0 }
            s_obj['eventos'] += 1
            s_obj['dias'] += dias
            subtipos_map[subtipo] = s_obj
            # Tipo base (histórico) derivado de motivo original para no romper gráfico previo "por tipo"
            if raw_motivo == 'Vacaciones':
                tipo_base = 'Vacaciones'
            else:
                parts = raw_motivo.split(' - ', 1)
                tipo_base = parts[0].strip() if parts else raw_motivo
                if not tipo_base:
                    tipo_base = 'Sin tipo'
            t_obj = tipos_inasistencias_map.get(tipo_base) or { 'tipo': tipo_base, 'eventos': 0, 'dias': 0 }
            t_obj['eventos'] += 1
            t_obj['dias'] += dias
            tipos_inasistencias_map[tipo_base] = t_obj
        motivos_list = list(motivos_map.values())
        motivos_list.sort(key=lambda x: (x['dias'], x['eventos']), reverse=True)
        if len(motivos_list) > 12:
            top = motivos_list[:11]
            rest = motivos_list[11:]
            otros = { 'motivo': 'Otros', 'eventos': 0, 'dias': 0 }
            for r in rest:
                otros['eventos'] += r['eventos']
                otros['dias'] += r['dias']
            top.append(otros)
            motivos_list = top
        tipos_inasistencias_list = list(tipos_inasistencias_map.values())
        tipos_inasistencias_list.sort(key=lambda x: (x['eventos'], x['dias']), reverse=True)
        subtipos_list = list(subtipos_map.values())
        subtipos_list.sort(key=lambda x: (x['eventos'], x['dias']), reverse=True)
        promedio_dias = round(total_dias / eventos_aus, 1) if eventos_aus else 0.0

        movimientos_serializados = []
        for mv in qs:
            nc = mv.nomina_consolidada
            liquido = ((nc.haberes_imponibles or 0) + (nc.haberes_no_imponibles or 0)) - ((nc.dctos_legales or 0) + (nc.otros_dctos or 0) + (nc.impuestos or 0)) if nc else 0
            movimientos_serializados.append({
                'id': mv.id,
                'tipo_movimiento': mv.tipo_movimiento,
                'tipo_display': mv.get_tipo_movimiento_display(),
                'empleado': {
                    'rut': nc.rut_empleado if nc else None,
                    'nombre': nc.nombre_empleado if nc else None,
                    'cargo': nc.cargo if nc else None,
                    'centro_costo': nc.centro_costo if nc else None,
                    'estado': nc.estado_empleado if nc else None,
                    'liquido_pagar': float(liquido),
                },
                'motivo': mv.motivo,
                'dias_ausencia': mv.dias_ausencia,
                'fecha_movimiento': mv.fecha_movimiento,
                'fecha_deteccion': mv.fecha_deteccion,
                'detectado_por_sistema': mv.detectado_por_sistema,
            })

        data = {
            'cierre': { 'id': cierre.id, 'cliente': cierre.cliente.nombre, 'periodo': cierre.periodo },
            'resumen': {
                'total_movimientos': total,
                'por_tipo': por_tipo,
                'ingreso': por_tipo.get('ingreso', {}).get('count', 0),
                'finiquito': por_tipo.get('finiquito', {}).get('count', 0),
                'ausentismo': por_tipo.get('ausentismo', {}).get('count', 0),
                'ausentismo_metricas': {
                    'eventos': eventos_aus,
                    'total_dias': total_dias,
                    'promedio_dias': promedio_dias,
                    'motivos': motivos_list,            # compat legacy (por motivo crudo)
                    'por_tipo': tipos_inasistencias_list, # compat histórico derivado de motivo
                    'subtipos': subtipos_list,           # nuevo agregado normalizado
                    'base_dias': 'dias_en_periodo>dias_evento>dias_ausencia',
                }
            },
            'movimientos': movimientos_serializados,
            'meta': { 'generated_at': timezone.now().isoformat(), 'api_version': '2', 'ausentismo_motivos_count': len(motivos_list) }
        }
        return Response(data, status=status.HTTP_200_OK)
    except CierreNomina.DoesNotExist:
        return Response({'error': 'Cierre no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': 'Error interno del servidor', 'detalle': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
