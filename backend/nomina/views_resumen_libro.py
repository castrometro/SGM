from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Value, DecimalField, Q
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import CierreNomina, ConceptoConsolidado, NominaConsolidada
from .cache_redis import get_cache_system_nomina


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def libro_resumen_v2(request, cierre_id: int):
    """📘 Resumen simplificado del Libro de Remuneraciones (V2)

    Alcance:
      - Total de empleados consolidados
      - Totales por categoría (tipo_concepto)
      - Lista de conceptos con: nombre, categoría, total, empleados (distinct)
    No incluye: líquido, headers, empleados por concepto, movimientos, incidencias.
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)

    # Si existe informe con bloque libro_resumen_v2, retornarlo (fast path)
    try:
        informe = getattr(cierre, 'informe', None)
        if informe and isinstance(informe.datos_cierre, dict):
            bloque = informe.datos_cierre.get('libro_resumen_v2')
            if isinstance(bloque, dict) and bloque.get('cierre', {}).get('id') == cierre.id:
                # 🔥 VERIFICAR SI EL INFORME ESTÁ INVALIDADO POR RECLASIFICACIÓN
                meta = bloque.get('meta', {})
                if meta.get('invalidado_por_reclasificacion'):
                    # Informe invalidado, saltar al query directo
                    pass  # Continúa al query directo de BD
                else:
                    # Agregar metadata de fuente
                    bloque['_metadata'] = {
                        'fuente': 'informe_persistente',
                        'descripcion': 'Datos históricos del informe guardado (no caduca)',
                        'fecha_informe': informe.fecha_generacion.isoformat() if hasattr(informe, 'fecha_generacion') else None
                    }
                    return Response(bloque, status=status.HTTP_200_OK)
    except Exception:
        pass

    # 1) Intentar cache temporal (TTL corto) si no hay informe guardado
    try:
        cache = get_cache_system_nomina()
        cached = cache.get_datos_consolidados(cierre.cliente_id, cierre.periodo)
        if isinstance(cached, dict):
            bloque = cached.get('libro_resumen_v2') or cached.get('libro')  # compat
            if isinstance(bloque, dict) and bloque.get('cierre', {}).get('id') == cierre.id:
                # Agregar metadata de fuente
                bloque['_metadata'] = {
                    'fuente': 'cache_redis',
                    'descripcion': 'Datos temporales en cache (TTL corto, ~5-10 min)',
                    'cached_at': cached.get('cached_at'),
                    'ttl_estimado': '5-10 minutos'
                }
                return Response(bloque, status=status.HTTP_200_OK)
    except Exception:
        pass

    # 2) Query base de conceptos consolidados para el cierre
    conceptos_qs = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre_id=cierre_id
    )

    # Categorías esperadas (aunque no todas aparezcan en los datos)
    CATEGORIAS = [
        'haber_imponible',
        'haber_no_imponible',
        'descuento_legal',
        'otro_descuento',
        'impuesto',
        'aporte_patronal',
    ]

    # Totales por categoría (rellenando faltantes con 0)
    totales_categorias_raw = conceptos_qs.values('tipo_concepto').annotate(
        total=Coalesce(
            Sum('monto_total'),
            Value(0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    )
    totales_categorias = {c: 0.0 for c in CATEGORIAS}
    for row in totales_categorias_raw:
        tipo = row.get('tipo_concepto')
        if tipo in totales_categorias:
            totales_categorias[tipo] = float(row['total'])

    # Agregación de conceptos (ordenados desc por total)
    # empleados: número de empleados con ese concepto con monto distinto de 0 (positivo o negativo)
    conceptos_agregados = conceptos_qs.values('nombre_concepto', 'tipo_concepto').annotate(
        total=Coalesce(
            Sum('monto_total'),
            Value(0, output_field=DecimalField(max_digits=20, decimal_places=2)),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        ),
        empleados=Count('nomina_consolidada_id', distinct=True, filter=~Q(monto_total=0))
    ).order_by('-total')

    conceptos_serializados = [
        {
            'nombre': c['nombre_concepto'],
            'categoria': c['tipo_concepto'],
            'total': float(c['total']),
            'empleados': c['empleados']
        }
        for c in conceptos_agregados
    ]

    total_empleados = NominaConsolidada.objects.filter(cierre_id=cierre_id).count()

    data = {
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
            'version_datos': getattr(cierre, 'version_datos', None),
            'generated_at': timezone.now().isoformat(),
            'api_version': '2'
        },
        '_metadata': {
            'fuente': 'query_directo_bd',
            'descripcion': 'Datos calculados directamente desde base de datos (sin cache)',
            'generado_en': timezone.now().isoformat(),
            'tablas_consultadas': ['ConceptoConsolidado', 'NominaConsolidada']
        }
    }

    # 3) Guardar en cache temporal si el cierre aún no está finalizado
    try:
        if cierre.estado != 'finalizado':
            cache_payload = {
                'libro_resumen_v2': data,
                'estado_cierre': cierre.estado,
                'cached_at': timezone.now().isoformat()
            }
            # TTL corto (5-10 minutos); usamos el short_ttl configurado en el sistema
            cache = cache if 'cache' in locals() else get_cache_system_nomina()
            ttl = getattr(cache, 'short_ttl', 300)
            cache.set_datos_consolidados(cierre.cliente_id, cierre.periodo, cache_payload, ttl=ttl)
    except Exception:
        pass

    return Response(data, status=status.HTTP_200_OK)
