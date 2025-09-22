from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import (
    CierreNomina,
    ConceptoConsolidado,
    IncidenciaCierre,
    TipoIncidencia,
)
from .views_resumen_libro import libro_resumen_v2

UMBRAL_PCT = 30.0  # Variación mínima absoluta en porcentaje


def _obtener_conceptos_por_cierre(cierre_id: int):
    """Devuelve dict {nombre_concepto: monto_total_float} para un cierre"""
    from django.db.models import Sum, Value, DecimalField
    from django.db.models.functions import Coalesce

    qs = (
        ConceptoConsolidado.objects
        .filter(nomina_consolidada__cierre_id=cierre_id)
        .values('nombre_concepto')
        .annotate(
            total=Coalesce(
                Sum('monto_total'),
                Value(0, output_field=DecimalField(max_digits=20, decimal_places=2))
            )
        )
    )
    return {r['nombre_concepto']: float(r['total']) for r in qs}


def _buscar_cierre_anterior(cierre: CierreNomina):
    return (CierreNomina.objects
            .filter(cliente=cierre.cliente, periodo__lt=cierre.periodo, estado__in=['finalizado', 'incidencias_resueltas'])
            .order_by('-periodo')
            .first())

@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def incidencias_totales_variacion(request, cierre_id: int):
    """🔎 Genera y PERSISTE incidencias de tipo suma_total SOLO para variaciones (>= ±30%).

    Diseño simplificado:
        1. Usa `libro_resumen_v2` para obtener totales actuales por concepto.
        2. Obtiene totales del cierre anterior finalizado / incidencias_resueltas.
        3. Detecta únicamente variaciones con |Δ%| >= 30 (IGNORA nuevos y eliminados).
        4. Elimina incidencias anteriores de tipo_comparacion = 'suma_total' del cierre.
        5. Inserta nuevas filas en `IncidenciaCierre` (solo VARIACION_SUMA_TOTAL).
        6. Actualiza campos de estado mínimos del cierre (`total_incidencias`, `estado_incidencias`, `estado`).

    Idempotencia básica: al ejecutar nuevamente se reemplaza el conjunto previo
    de incidencias suma_total (no afecta otros tipos).

    Request: POST (sin body necesario) | GET (modo compat: ejecuta igual)
    Response: JSON con resumen y lista de incidencias persistidas.
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)
    cierre_anterior = _buscar_cierre_anterior(cierre)

    # Obtener datos actuales reutilizando view existente (sin duplicar lógica)
    # Invocamos directamente la función y tomamos su data
    resumen_response = libro_resumen_v2(request._request if hasattr(request, '_request') else request, cierre_id)
    if resumen_response.status_code != 200:
        return resumen_response
    resumen_data = resumen_response.data

    conceptos_actuales = {c['nombre']: c['total'] for c in resumen_data.get('conceptos', [])}

    if not cierre_anterior:
        # No hay cierre anterior -> limpiar incidencias suma_total y marcar resueltas
        IncidenciaCierre.objects.filter(cierre=cierre, tipo_comparacion='suma_total').delete()
        cierre.total_incidencias = 0
        cierre.estado_incidencias = 'resueltas'
        if cierre.estado == 'datos_consolidados':
            cierre.estado = 'incidencias_resueltas'
        cierre.save(update_fields=['total_incidencias', 'estado_incidencias', 'estado'])
        return Response({
            'cierre_actual': cierre.periodo,
            'cierre_anterior': None,
            'parametros': {'umbral_pct': UMBRAL_PCT},
            'incidencias': [],
            'mensaje': 'No existe cierre anterior finalizado para comparar. Se considera sin incidencias.'
        }, status=200)

    # Construir montos del cierre anterior (consulta directa)
    conceptos_prev = _obtener_conceptos_por_cierre(cierre_anterior.id)

    claves_actual = set(conceptos_actuales.keys())
    claves_prev = set(conceptos_prev.keys())

    # Solo consideramos conceptos presentes en ambos cierres para evaluar variación
    comunes = (set(conceptos_actuales.keys()) & set(conceptos_prev.keys()))

    incidencias = []  # para respuesta
    incidencias_bulk = []  # para persistencia

    # (Se ignoran conceptos nuevos y eliminados según requerimiento actual)

    # Variaciones significativas
    import math
    for nombre in comunes:
        monto_act = conceptos_actuales.get(nombre, 0.0) or 0.0
        monto_prev = conceptos_prev.get(nombre, 0.0) or 0.0
        if math.isclose(monto_prev, 0.0):
            continue  # ya cubierto como nuevo / eliminado si corresponde
        delta_abs = monto_act - monto_prev
        delta_pct = (delta_abs / monto_prev) * 100.0 if monto_prev else 0.0
        if abs(delta_pct) >= UMBRAL_PCT:
            incidencias.append({
                'concepto': nombre,
                'monto_actual': monto_act,
                'monto_anterior': monto_prev,
                'delta_abs': delta_abs,
                'delta_pct': delta_pct,
                'tipo': 'variacion'
            })
            incidencias_bulk.append(IncidenciaCierre(
                cierre=cierre,
                tipo_incidencia=TipoIncidencia.VARIACION_SUMA_TOTAL,
                tipo_comparacion='suma_total',
                rut_empleado='-',
                descripcion=f"Variación {delta_pct:.1f}% en {nombre} (Δ ${delta_abs:,.0f})",
                concepto_afectado=nombre,
                prioridad='alta' if abs(delta_abs) > 500000 else 'media',
                impacto_monetario=abs(delta_abs),
                datos_adicionales={
                    'monto_anterior': monto_prev,
                    'monto_actual': monto_act,
                    'delta_abs': delta_abs,
                    'delta_pct': delta_pct,
                    'umbral_pct': UMBRAL_PCT,
                    'tipo_concepto': None,
                    'tipo_comparacion': 'suma_total'
                }
            ))

    # Persistencia: limpiar anteriores tipo suma_total y crear nuevas
    IncidenciaCierre.objects.filter(cierre=cierre, tipo_comparacion='suma_total').delete()
    if incidencias_bulk:
        IncidenciaCierre.objects.bulk_create(incidencias_bulk)

    total = len(incidencias_bulk)
    # Actualizar estado del cierre (mínimo viable)
    cierre.total_incidencias = total
    if total > 0:
        cierre.estado_incidencias = 'detectadas'
        if cierre.estado == 'datos_consolidados':
            cierre.estado = 'con_incidencias'
    else:
        cierre.estado_incidencias = 'resueltas'
        if cierre.estado == 'datos_consolidados':
            cierre.estado = 'incidencias_resueltas'
    cierre.save(update_fields=['total_incidencias', 'estado_incidencias', 'estado'])

    incidencias.sort(key=lambda x: abs(x['delta_abs']), reverse=True)

    return Response({
        'cierre_actual': cierre.periodo,
        'cierre_anterior': cierre_anterior.periodo,
        'parametros': {
            'umbral_pct': UMBRAL_PCT,
            'generado_en': timezone.now().isoformat(),
            'total_conceptos_actual': len(conceptos_actuales),
            'total_conceptos_anterior': len(conceptos_prev),
        },
        'estadisticas': {
            'variaciones': len([i for i in incidencias if i['tipo'] == 'variacion']),
            'total_incidencias': total
        },
        'incidencias': incidencias
    }, status=status.HTTP_200_OK)
