from decimal import Decimal
from django.db.models import Sum

def aggregate_by_tipo(nomina_consolidada):
    """
    Agrupa y suma montos de ConceptoConsolidado por su campo 'tipo_concepto'.
    Retorna un dict con keys = tipo_concepto y valores Decimal acumulados.
    """
    resultados = {}
    # Usar el related_name 'conceptos' definido en el modelo ConceptoConsolidado
    qs = nomina_consolidada.conceptos.values('tipo_concepto').annotate(total=Sum('monto_total'))
    for row in qs:
        tipo = row.get('tipo_concepto') or 'sin_tipo'
        total = row.get('total') or Decimal('0')
        resultados[tipo] = Decimal(total)

    return resultados
