from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Value, DecimalField, Q
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import CierreNomina, ConceptoConsolidado, NominaConsolidada


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

    # Query base de conceptos consolidados para el cierre
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
        }
    }

    return Response(data, status=status.HTTP_200_OK)
