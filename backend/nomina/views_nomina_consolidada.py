from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, F, DecimalField, IntegerField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import CierreNomina, NominaConsolidada


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_resumen_nomina_consolidada(request, cierre_id: int):
    """
    Resumen agregado de la tabla NominaConsolidada para un cierre dado.

    Retorna totales por categorías (haberes, descuentos, impuestos, aportes),
    conteo de empleados y métricas derivadas (líquido total, horas extras, etc.).
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)

    qs = NominaConsolidada.objects.filter(cierre_id=cierre_id)

    # Expresión para líquido a pagar por empleado
    liquido_expr = ExpressionWrapper(
        F("haberes_imponibles")
        + F("haberes_no_imponibles")
        - F("dctos_legales")
        - F("otros_dctos")
        - F("impuestos"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )

    # Agregaciones principales
    zero_dec_2 = Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
    zero_dec_4 = Value(0, output_field=DecimalField(max_digits=20, decimal_places=4))
    zero_int = Value(0, output_field=IntegerField())

    agg = qs.aggregate(
        total_empleados=Count("id"),
        total_haberes_imponibles=Coalesce(Sum("haberes_imponibles"), zero_dec_2),
        total_haberes_no_imponibles=Coalesce(Sum("haberes_no_imponibles"), zero_dec_2),
        total_dctos_legales=Coalesce(Sum("dctos_legales"), zero_dec_2),
        total_otros_dctos=Coalesce(Sum("otros_dctos"), zero_dec_2),
        total_impuestos=Coalesce(Sum("impuestos"), zero_dec_2),
        total_aportes_patronales=Coalesce(Sum("aportes_patronales"), zero_dec_2),
        horas_extras_cantidad_total=Coalesce(Sum("horas_extras_cantidad"), zero_dec_4),
        dias_trabajados_total=Coalesce(Sum("dias_trabajados"), zero_int),
        dias_ausencia_total=Coalesce(Sum("dias_ausencia"), zero_int),
        liquido_total=Coalesce(Sum(liquido_expr), zero_dec_2),
    )

    # Traer resumen del período anterior si existe para comparación
    resumen_anterior = None
    periodo_anterior = None
    try:
        cierre_anterior = (
            CierreNomina.objects
            .filter(
                cliente=cierre.cliente,
                periodo__lt=cierre.periodo,
                estado__in=["datos_consolidados", "finalizado"],
            )
            .order_by("-periodo")
            .first()
        )
        if cierre_anterior:
            periodo_anterior = cierre_anterior.periodo
            qs_prev = NominaConsolidada.objects.filter(cierre_id=cierre_anterior.id)
            resumen_anterior = qs_prev.aggregate(
                total_empleados=Count("id"),
                total_haberes_imponibles=Coalesce(Sum("haberes_imponibles"), zero_dec_2),
                total_haberes_no_imponibles=Coalesce(Sum("haberes_no_imponibles"), zero_dec_2),
                total_dctos_legales=Coalesce(Sum("dctos_legales"), zero_dec_2),
                total_otros_dctos=Coalesce(Sum("otros_dctos"), zero_dec_2),
                total_impuestos=Coalesce(Sum("impuestos"), zero_dec_2),
                total_aportes_patronales=Coalesce(Sum("aportes_patronales"), zero_dec_2),
                horas_extras_cantidad_total=Coalesce(Sum("horas_extras_cantidad"), zero_dec_4),
                dias_trabajados_total=Coalesce(Sum("dias_trabajados"), zero_int),
                dias_ausencia_total=Coalesce(Sum("dias_ausencia"), zero_int),
                liquido_total=Coalesce(Sum(liquido_expr), zero_dec_2),
            )
    except Exception:
        resumen_anterior = None

    # Conteos por estado de empleado
    por_estado = {
        item["estado_empleado"]: item["c"]
        for item in qs.values("estado_empleado").annotate(c=Count("id"))
    }

    data = {
        "cierre": {
            "id": cierre.id,
            "cliente_id": cierre.cliente.id,
            "cliente": getattr(cierre.cliente, "nombre", str(cierre.cliente)),
            "periodo": cierre.periodo,
            "estado_consolidacion": cierre.estado_consolidacion,
        },
        "resumen": agg,
    "periodo_anterior": periodo_anterior,
    "resumen_anterior": resumen_anterior,
        "por_estado": por_estado,
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def obtener_detalle_nomina_consolidada(request, cierre_id: int):
    """
    Detalle de Nómina Consolidada para un cierre:
    - Lista de empleados consolidados con totales por categoría y líquido
    - Headers únicos y valores por empleado
    - Conceptos consolidados por empleado
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)

    if not cierre.nomina_consolidada.exists():
        return Response({
            'error': 'No hay datos consolidados para este cierre',
            'mensaje': 'Debe ejecutar la consolidación antes de ver la nómina consolidada'
        }, status=status.HTTP_404_NOT_FOUND)

    # Importes diferidos para evitar ciclos
    from .models import HeaderValorEmpleado, ConceptoConsolidado

    empleados_qs = NominaConsolidada.objects.filter(cierre=cierre).order_by('nombre_empleado')

    # Headers únicos del cierre
    headers_unicos = (
        HeaderValorEmpleado.objects
        .filter(nomina_consolidada__cierre=cierre)
        .values_list('nombre_header', flat=True)
        .distinct()
        .order_by('nombre_header')
    )

    data = {
        'cierre': {
            'id': cierre.id,
            'cliente': getattr(cierre.cliente, 'nombre', str(cierre.cliente)),
            'periodo': cierre.periodo,
            'estado': cierre.estado,
            'fecha_consolidacion': cierre.fecha_consolidacion,
        },
        'headers': list(headers_unicos),
        'empleados': []
    }

    for emp in empleados_qs:
        # Valores por header
        hvs = HeaderValorEmpleado.objects.filter(nomina_consolidada=emp).order_by('nombre_header')
        valores_headers = {hv.nombre_header: hv.valor_original for hv in hvs}

        # Conceptos consolidados
        conceptos_qs = ConceptoConsolidado.objects.filter(nomina_consolidada=emp).order_by('nombre_concepto')

        empleado_data = {
            'id': emp.id,
            'rut_empleado': emp.rut_empleado,
            'nombre_empleado': emp.nombre_empleado,
            'cargo': emp.cargo,
            'centro_costo': emp.centro_costo,
            'estado_empleado': emp.estado_empleado,
            'total_haberes': str((emp.haberes_imponibles or 0) + (emp.haberes_no_imponibles or 0)),
            'total_descuentos': str((emp.dctos_legales or 0) + (emp.otros_dctos or 0) + (emp.impuestos or 0)),
            'liquido_pagar': str(((emp.haberes_imponibles or 0) + (emp.haberes_no_imponibles or 0)) - ((emp.dctos_legales or 0) + (emp.otros_dctos or 0) + (emp.impuestos or 0))),
            'dias_trabajados': emp.dias_trabajados,
            'dias_ausencia': emp.dias_ausencia,
            'valores_headers': valores_headers,
            'conceptos': [
                {
                    'nombre': c.nombre_concepto,
                    'clasificacion': c.tipo_concepto,
                    'monto_total': str(c.monto_total),
                    'cantidad': c.cantidad,
                    'origen_datos': c.fuente_archivo,
                }
                for c in conceptos_qs
            ]
        }

        data['empleados'].append(empleado_data)

    return Response(data, status=status.HTTP_200_OK)
