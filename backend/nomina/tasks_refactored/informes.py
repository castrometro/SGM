"""
🎯 TASKS - INFORMES Y FINALIZACIÓN DE CIERRE

Este módulo contiene las tareas relacionadas con:
- Generación de informes (Libro de Remuneraciones, Movimientos)
- Unificación y guardado de informes
- Envío de informes a Redis
- Finalización del cierre

Migrado desde tasks.py.original
Fecha: 28 de octubre de 2025
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import (
    Count, Sum, Q, F, DecimalField, IntegerField,
    ExpressionWrapper, Value
)
from django.db.models.functions import Coalesce
import logging

logger = logging.getLogger(__name__)


def _json_safe(obj):
    """Helper para convertir Decimals/sets/dates a tipos JSON-compatibles"""
    import json
    from decimal import Decimal
    from datetime import datetime, date, time
    
    def default_handler(o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, set):
            return list(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    
    return json.loads(json.dumps(obj, default=default_handler))


@shared_task(name='nomina.build_informe_libro', bind=True)
def build_informe_libro(self, cierre_id: int) -> dict:
    """
    Construye payload del Libro de Remuneraciones desde NominaConsolidada,
    equivalente a la data que consumen las páginas (detalle + resumen).
    """
    from nomina.models import CierreNomina, NominaConsolidada, ConceptoConsolidado
    
    cierre = CierreNomina.objects.get(id=cierre_id)

    if not cierre.nomina_consolidada.exists():
        return {
            'error': 'No hay datos consolidados para este cierre',
            'detalle': None,
            'resumen': None,
        }

    # 🔥 CAMBIO: Usar ConceptoConsolidado como single source of truth (igual que dashboard)
    conceptos_qs = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=cierre)
    
    # Categorías esperadas
    CATEGORIAS = [
        'haber_imponible',
        'haber_no_imponible', 
        'descuento_legal',
        'otro_descuento',
        'impuesto',
        'aporte_patronal',
    ]

    # Resumen general (totales por categoría desde ConceptoConsolidado)
    zero_dec_2 = Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
    zero_dec_4 = Value(0, output_field=DecimalField(max_digits=20, decimal_places=4))
    
    # Total empleados únicos
    total_empleados = NominaConsolidada.objects.filter(cierre=cierre).count()
    
    # Totales por categoría (igual que dashboard)
    totales_categorias_raw = conceptos_qs.values('tipo_concepto').annotate(
        total=Coalesce(
            Sum('monto_total'),
            zero_dec_2,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    )
    totales_categorias_dict = {c: 0.0 for c in CATEGORIAS}
    for row in totales_categorias_raw:
        tipo = row.get('tipo_concepto')
        if tipo in totales_categorias_dict:
            totales_categorias_dict[tipo] = float(row['total'])

    # Desglose por concepto (por tipo_concepto)
    conceptos_base = (
        ConceptoConsolidado.objects
        .filter(nomina_consolidada__cierre=cierre)
        .values('tipo_concepto', 'nombre_concepto')
        .annotate(
            total_monto=Coalesce(Sum('monto_total'), zero_dec_2),
            total_cantidad=Coalesce(Sum('cantidad'), zero_dec_4),
        )
        .order_by('tipo_concepto', '-total_monto')
    )

    # Formato esperado por LibroRemuneraciones.jsx (libro_resumen_v2)
    # Calcular empleados por concepto (distinct nomina_consolidada con monto != 0)
    empleados_aggr = (
        ConceptoConsolidado.objects
        .filter(nomina_consolidada__cierre=cierre)
        .values('tipo_concepto', 'nombre_concepto')
        .annotate(empleados=Count('nomina_consolidada', distinct=True, filter=~Q(monto_total=0)))
    )
    emp_map = {(e['tipo_concepto'], e['nombre_concepto']): int(e['empleados'] or 0) for e in empleados_aggr}

    conceptos_serializados = []
    for tipo in ['haber_imponible', 'haber_no_imponible', 'descuento_legal', 'otro_descuento', 'impuesto', 'aporte_patronal']:
        for it in conceptos_base:
            if it['tipo_concepto'] == tipo:
                conceptos_serializados.append({
                    'nombre': it['nombre_concepto'],
                    'categoria': tipo,
                    'total': float(it['total_monto'] or 0),
                    'empleados': emp_map.get((tipo, it['nombre_concepto']), 0),
                })

    # 🔥 CAMBIO: Usar totales calculados desde ConceptoConsolidado
    totales_categorias = {
        'haber_imponible': totales_categorias_dict['haber_imponible'],
        'haber_no_imponible': totales_categorias_dict['haber_no_imponible'],
        'descuento_legal': totales_categorias_dict['descuento_legal'],
        'otro_descuento': totales_categorias_dict['otro_descuento'],
        'impuesto': totales_categorias_dict['impuesto'],
        'aporte_patronal': totales_categorias_dict['aporte_patronal'],
    }

    libro_v2 = {
        'cierre': {
            'id': cierre.id,
            'cliente': getattr(cierre.cliente, 'nombre', str(cierre.cliente)),
            'periodo': cierre.periodo,
            'total_empleados': total_empleados,
        },
        'totales_categorias': totales_categorias,
        'conceptos': conceptos_serializados,
        'meta': {
            'conceptos_count': len(conceptos_serializados),
            'generated_at': timezone.now().isoformat(),
            'api_version': '2',
        },
    }

    return libro_v2


@shared_task(name='nomina.build_informe_movimientos', bind=True)
def build_informe_movimientos(self, cierre_id: int) -> dict:
    """
    Resumen compacto de Movimientos (schema normalizado)
    Métricas:
      - Totales por categoria con empleados únicos
      - Ausentismo: eventos, días, promedio y subtipos
      - Cambios (contrato/sueldo) por subtipo
    """
    from nomina.models import CierreNomina, MovimientoPersonal
    
    cierre = CierreNomina.objects.get(id=cierre_id)

    if not cierre.nomina_consolidada.exists():
        return {'error': 'No hay datos consolidados para este cierre', 'movimientos': None}

    movimientos = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=cierre
    ).select_related('nomina_consolidada')

    por_categoria = {}
    for mv in movimientos:
        cat = mv.categoria or 'sin_categoria'
        entry = por_categoria.get(cat) or {'count': 0, 'empleados_unicos': set()}
        entry['count'] += 1
        rut = mv.nomina_consolidada.rut_empleado if mv.nomina_consolidada else None
        if rut:
            entry['empleados_unicos'].add(rut)
        por_categoria[cat] = entry
    
    por_categoria_fmt = {
        k: {'count': v['count'], 'empleados_unicos': len(v['empleados_unicos'])} 
        for k, v in por_categoria.items()
    }

    aus_qs = [mv for mv in movimientos if mv.categoria == 'ausencia']
    aus_subtipos = {}
    total_dias_aus = 0
    for mv in aus_qs:
        dias = mv.dias_en_periodo if mv.dias_en_periodo is not None else (mv.dias_evento or 0)
        total_dias_aus += dias
        st = (mv.subtipo or 'sin_justificar').strip() or 'sin_justificar'
        obj = aus_subtipos.get(st) or {'eventos': 0, 'dias': 0}
        obj['eventos'] += 1
        obj['dias'] += dias
        aus_subtipos[st] = obj
    
    aus_subtipos_list = [
        {'subtipo': k, 'eventos': v['eventos'], 'dias': v['dias']} 
        for k, v in aus_subtipos.items()
    ]
    aus_subtipos_list.sort(key=lambda x: (x['eventos'], x['dias']), reverse=True)

    cambios_map = {}
    for mv in movimientos:
        if mv.subtipo in ('cambio_contrato', 'cambio_sueldo') or mv.categoria == 'cambio_datos':
            st = mv.subtipo or 'cambio_datos'
            obj = cambios_map.get(st) or {'subtipo': st, 'eventos': 0}
            obj['eventos'] += 1
            cambios_map[st] = obj
    
    cambios_list = list(cambios_map.values())
    cambios_list.sort(key=lambda x: x['eventos'], reverse=True)

    # Serialización de movimientos como en movimientos_personal_detalle_v3
    movimientos_serializados = []
    for mv in movimientos:
        nc = mv.nomina_consolidada
        liquido = 0
        if nc:
            try:
                liquido = (
                    (nc.haberes_imponibles or 0) + (nc.haberes_no_imponibles or 0)
                ) - (
                    (nc.dctos_legales or 0) + (nc.otros_dctos or 0) + (nc.impuestos or 0)
                )
            except Exception:
                liquido = 0
        
        movimientos_serializados.append({
            'id': mv.id,
            'categoria': mv.categoria,
            'subtipo': mv.subtipo,
            'descripcion': mv.descripcion,
            'fecha_inicio': mv.fecha_inicio.isoformat() if mv.fecha_inicio else None,
            'fecha_fin': mv.fecha_fin.isoformat() if mv.fecha_fin else None,
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
            'fecha_deteccion': mv.fecha_deteccion.isoformat() if mv.fecha_deteccion else None,
            'detectado_por_sistema': mv.detectado_por_sistema,
        })

    # Formato esperado por MovimientosMes.jsx (movimientos_personal_detalle_v3)
    payload = {
        'cierre': {
            'id': cierre.id,
            'cliente': getattr(cierre.cliente, 'nombre', str(cierre.cliente)),
            'periodo': cierre.periodo,
        },
        'resumen': {
            'total_movimientos': movimientos.count(),
            'por_tipo': por_categoria_fmt,
            'ausentismo_metricas': {
                'eventos': len(aus_qs),
                'total_dias': total_dias_aus,
                'promedio_dias': round(total_dias_aus / len(aus_qs), 1) if aus_qs else 0.0,
                'subtipos': aus_subtipos_list,
            },
            'cambios_metricas': cambios_list,
        },
        'movimientos': movimientos_serializados,
        'meta': {
            'generated_at': timezone.now().isoformat(),
            'api_version': '3',
        }
    }
    return payload


@shared_task(name='nomina.unir_y_guardar_informe', bind=True)
def unir_y_guardar_informe(self, resultados: list, cierre_id: int, version: str = 'sgm-v1') -> dict:
    """
    Construye y guarda un JSON unificado que contiene exactamente lo que necesitan
    las vistas LibroRemuneraciones.jsx y MovimientosMes.jsx, más metadatos.

    Estructura final en InformeNomina.datos_cierre:
    {
      meta: {...},
      libro_resumen_v2: {...},
      movimientos_v3: {...}
    }
    """
    from nomina.models import CierreNomina
    from nomina.models_informe import InformeNomina

    cierre = CierreNomina.objects.get(id=cierre_id)
    libro, movimientos = resultados or [{}, {}]

    # Sanitizar versión (max length 10)
    raw_version = str(version) if version is not None else 'sgm-v1'
    safe_version = raw_version[:10]
    if raw_version != safe_version:
        logger.warning(f"version_calculo '{raw_version}' truncada a '{safe_version}' (max 10)")

    # Metadatos del cierre
    meta = {
        'cliente_id': getattr(cierre.cliente, 'id', None),
        'cliente_nombre': getattr(cierre.cliente, 'nombre', None),
        'periodo': cierre.periodo,  # YYYY-MM
        'generated_at': timezone.now().isoformat(),
        'version_datos': getattr(cierre, 'version_datos', None),
        'version_calculo': safe_version,
    }

    # Normalizar bloques esperados por frontend
    libro_payload = libro if isinstance(libro, dict) else {}
    movs_payload = movimientos if isinstance(movimientos, dict) else {}

    payload = {
        'meta': _json_safe(meta),
        'libro_resumen_v2': _json_safe(libro_payload),
        'movimientos_v3': _json_safe(movs_payload),
    }

    informe, _ = InformeNomina.objects.get_or_create(
        cierre=cierre,
        defaults={'datos_cierre': payload, 'version_calculo': safe_version}
    )

    inicio = timezone.now()
    informe.datos_cierre = payload
    informe.version_calculo = safe_version
    informe.fecha_generacion = inicio
    informe.tiempo_calculo = timezone.now() - inicio
    informe.save(update_fields=['datos_cierre', 'version_calculo', 'fecha_generacion', 'tiempo_calculo'])

    return {'informe_id': informe.id, 'cierre_id': cierre_id, 'saved': True}


@shared_task(name='nomina.enviar_informe_redis_task', bind=True)
def enviar_informe_redis_task(self, prev_result: dict, cierre_id: int, ttl_hours: int | None = None) -> dict:
    """
    Envía el informe del cierre a Redis usando el wrapper oficial con metadatos.
    """
    from nomina.models import CierreNomina
    from nomina.models_informe import InformeNomina

    cierre = CierreNomina.objects.get(id=cierre_id)
    informe = InformeNomina.objects.get(cierre=cierre)

    # Usar el método centralizado que construye el wrapper completo
    res = informe.enviar_a_redis(ttl_hours=ttl_hours)

    return {
        'informe_id': informe.id,
        'cierre_id': cierre_id,
        'sent_to_redis': bool(res.get('success')),
        'redis_key': res.get('clave_redis'),
        'ttl_hours': res.get('ttl_hours'),
    }


@shared_task(name='nomina.finalizar_cierre_post_informe', bind=True)
def finalizar_cierre_post_informe(self, prev_result: dict, cierre_id: int, usuario_id: int | None = None) -> dict:
    """
    Task posterior a la generación del informe: marca el cierre como 'finalizado',
    setea fecha y usuario de finalización. NO envía a Redis.

    Args:
        prev_result: resultado de la task anterior (enviar_informe_redis_task)
        cierre_id: ID del cierre a finalizar
        usuario_id: ID del usuario que inició la finalización (opcional)

    Returns:
        dict con estado de finalización y metadata básica.
    """
    from django.contrib.auth import get_user_model
    from nomina.models import CierreNomina

    cierre = CierreNomina.objects.get(id=cierre_id)

    user = None
    if usuario_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            user = None

    # Actualizar estado y metadatos
    cierre.estado = 'finalizado'
    cierre.fecha_finalizacion = timezone.now()
    if user:
        cierre.usuario_finalizacion = user
        cierre.save(update_fields=['estado', 'fecha_finalizacion', 'usuario_finalizacion'])
    else:
        cierre.save(update_fields=['estado', 'fecha_finalizacion'])

    # 🔥 NUEVO: ELIMINAR CACHE PREVIEW AL FINALIZAR
    preview_cache_deleted = 0
    try:
        from nomina.cache_redis import get_cache_system_nomina
        cache = get_cache_system_nomina()
        
        # Eliminar cache preview específico
        preview_keys = [
            f"{cierre_id}_cache_libro",
            f"{cierre_id}_cache_mov"
        ]
        
        for key in preview_keys:
            try:
                if cache.redis_client.delete(key):
                    preview_cache_deleted += 1
            except Exception:
                pass
        
        # 🔥 NUEVO: INVALIDAR CACHE PRINCIPAL CONSOLIDADOS TAMBIÉN
        try:
            cache.delete_datos_consolidados(cierre.cliente_id, cierre.periodo)
        except Exception:
            pass
        
        logger.info(f"🗑️ [Finalización] Cache preview eliminado: {preview_cache_deleted} claves para cierre {cierre_id}")
    except Exception as e:
        logger.warning(f"⚠️ [Finalización] Error eliminando cache preview: {e}")

    return {
        'success': True,
        'cierre_id': cierre_id,
        'finalizado': True,
        'informe_id': (prev_result or {}).get('informe_id'),
        'preview_cache_deleted': preview_cache_deleted
    }


@shared_task(name='nomina.calcular_kpis_cierre', bind=True)
def calcular_kpis_cierre(self, prev_result: dict, cierre_id: int) -> dict:
    """
    Calcula y guarda solo las tasas: rotación, ingreso y ausentismo (sobre dotación).
    """
    from nomina.models import CierreNomina, NominaConsolidada, MovimientoPersonal

    cierre = CierreNomina.objects.get(id=cierre_id)

    # Base dotación
    nc_qs = NominaConsolidada.objects.filter(cierre=cierre)
    dotacion_total = nc_qs.count()

    # Ingresos / Finiquitos / Ausentismos
    mov_qs = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre)
    ingresos_total = mov_qs.filter(categoria='ingreso').count()
    finiquitos_total = mov_qs.filter(categoria='finiquito').count()
    ausentismos = mov_qs.filter(categoria='ausencia')
    total_dias_ausencia = sum(
        (mv.dias_en_periodo if mv.dias_en_periodo is not None else (mv.dias_evento or 0)) 
        for mv in ausentismos
    )

    # Tasas básicas
    if dotacion_total > 0:
        tasa_rotacion = round((finiquitos_total / dotacion_total) * 100, 2)
        tasa_ingreso = round((ingresos_total / dotacion_total) * 100, 2)
        tasa_ausentismo = round((total_dias_ausencia / (dotacion_total * 30)) * 100, 2) if dotacion_total > 0 else 0.0
    else:
        tasa_rotacion = tasa_ingreso = tasa_ausentismo = 0.0

    kpis = {
        'dotacion_total': dotacion_total,
        'ingresos': ingresos_total,
        'finiquitos': finiquitos_total,
        'dias_ausencia': total_dias_ausencia,
        'tasa_rotacion': tasa_rotacion,
        'tasa_ingreso': tasa_ingreso,
        'tasa_ausentismo': tasa_ausentismo,
    }

    logger.info(f"✅ KPIs calculados para cierre {cierre_id}: {kpis}")
    return {'cierre_id': cierre_id, 'kpis': kpis}
