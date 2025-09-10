from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import CierreNomina, MovimientoPersonal


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movimientos_personal_detalle_v3(request, cierre_id: int):
    """🧩 Movimientos de Personal Detalle (V3)

    Objetivo: entregar listado completo de movimientos (todos los tipos) con los
    campos normalizados y agregaciones claves para la vista MovimientosMes.

    Diferencias vs V2:
    - Incluye TODOS los tipos (ingreso, finiquito, ausentismo, reincorporacion, cambio_contrato, cambio_sueldo, cambio_datos)
    - Devuelve campos normalizados: categoria, subtipo, fecha_inicio, fecha_fin, dias_evento, dias_en_periodo, multi_mes, hashes
    - Ausentismo: métricas basadas en dias_en_periodo (fallback dias_evento)
    - Agrega agregación de subtipos para ausencias y para cambios (contrato / sueldo)
    - Mantiene compatibilidad: resumen.por_tipo ahora por categoria
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        if not cierre.nomina_consolidada.exists():
            return Response({'error': 'No hay datos consolidados para este cierre'}, status=status.HTTP_404_NOT_FOUND)

        qs = (MovimientoPersonal.objects
              .filter(nomina_consolidada__cierre=cierre)
              .select_related('nomina_consolidada')
              .order_by('-fecha_deteccion'))

        # === Resumen por categoría ===
        por_tipo = {}
        empleados_por_cat = {}
        for mv in qs:
            cat = mv.categoria or 'sin_categoria'
            rut = mv.nomina_consolidada.rut_empleado if mv.nomina_consolidada else None
            empleados_por_cat.setdefault(cat, set())
            if rut:
                empleados_por_cat[cat].add(rut)
            item = por_tipo.get(cat) or {'count': 0, 'display': cat.title(), 'empleados_unicos': 0}
            item['count'] += 1
            por_tipo[cat] = item
        for cat, data in por_tipo.items():
            data['empleados_unicos'] = len(empleados_por_cat.get(cat, []))
        total_movs = sum(v['count'] for v in por_tipo.values())

        # === Agregaciones específicas ===
        # Ausentismo (categoria ausencia)
        aus_qs = [mv for mv in qs if mv.categoria == 'ausencia']
        eventos_aus = len(aus_qs)
        total_dias_aus = 0
        subtipos_aus_map = {}
        for mv in aus_qs:
            dias = mv.dias_en_periodo if mv.dias_en_periodo is not None else (mv.dias_evento or 0)
            total_dias_aus += dias
            subtipo = (mv.subtipo or '').strip() or 'sin_justificar'
            s = subtipos_aus_map.get(subtipo) or {'subtipo': subtipo, 'eventos': 0, 'dias': 0}
            s['eventos'] += 1
            s['dias'] += dias
            subtipos_aus_map[subtipo] = s
        subtipos_aus_list = list(subtipos_aus_map.values())
        subtipos_aus_list.sort(key=lambda x: (x['eventos'], x['dias']), reverse=True)
        promedio_dias_aus = round(total_dias_aus / eventos_aus, 1) if eventos_aus else 0.0

        # Cambios (contrato / sueldo) — agrupar por subtipo
        cambios_qs = [mv for mv in qs if mv.subtipo in ('cambio_contrato', 'cambio_sueldo') or mv.categoria == 'cambio_datos']
        cambios_map = {}
        for mv in cambios_qs:
            st = mv.subtipo or 'cambio_datos'
            obj = cambios_map.get(st) or {'subtipo': st, 'eventos': 0}
            obj['eventos'] += 1
            cambios_map[st] = obj
        cambios_list = list(cambios_map.values())
        cambios_list.sort(key=lambda x: x['eventos'], reverse=True)

        # Serialización movimientos
        movimientos_serializados = []
        for mv in qs:
            nc = mv.nomina_consolidada
            liquido = 0
            if nc:
                try:
                    liquido = ((nc.haberes_imponibles or 0) + (nc.haberes_no_imponibles or 0)) - ((nc.dctos_legales or 0) + (nc.otros_dctos or 0) + (nc.impuestos or 0))
                except Exception:
                    liquido = 0
            movimientos_serializados.append({
                'id': mv.id,
                'categoria': mv.categoria,
                'subtipo': mv.subtipo,
                'descripcion': mv.descripcion,
                'fecha_inicio': mv.fecha_inicio,
                'fecha_fin': mv.fecha_fin,
                'dias_evento': mv.dias_evento,
                'dias_en_periodo': mv.dias_en_periodo,
                'multi_mes': mv.multi_mes,
                'hash_evento': mv.hash_evento,
                'hash_registro_periodo': mv.hash_registro_periodo,
                'empleado': {
                    'rut': nc.rut_empleado if nc else None,
                    'nombre': nc.nombre_empleado if nc else None,
                    'cargo': nc.cargo if nc else None,
                    'centro_costo': nc.centro_costo if nc else None,
                    'estado': nc.estado_empleado if nc else None,
                    'liquido_pagar': float(liquido),
                },
                'observaciones': mv.observaciones,
                'fecha_deteccion': mv.fecha_deteccion,
                'detectado_por_sistema': mv.detectado_por_sistema,
            })

        data = {
            'cierre': {'id': cierre.id, 'cliente': cierre.cliente.nombre, 'periodo': cierre.periodo},
            'resumen': {
                'total_movimientos': total_movs,
                'por_tipo': por_tipo,
                'ausentismo_metricas': {
                    'eventos': eventos_aus,
                    'total_dias': total_dias_aus,
                    'promedio_dias': promedio_dias_aus,
                    'subtipos': subtipos_aus_list,
                    'base_dias': 'dias_en_periodo>dias_evento'
                },
                'cambios_metricas': cambios_list,
            },
            'movimientos': movimientos_serializados,
            'meta': {
                'generated_at': timezone.now().isoformat(),
                'api_version': '3'
            }
        }
        return Response(data, status=status.HTTP_200_OK)
    except CierreNomina.DoesNotExist:
        return Response({'error': 'Cierre no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': 'Error interno del servidor', 'detalle': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
