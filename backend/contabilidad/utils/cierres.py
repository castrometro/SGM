from contabilidad.models import CierreContabilidad


def obtener_cierre_activo(cliente, cierre_id=None):
    """Obtiene el cierre activo para ``cliente``.

    Si se indica ``cierre_id`` se intenta devolver ese cierre, en caso de no
    existir se busca el último cierre del cliente con estado abierto.
    """
    cierre = None

    if cierre_id:
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
        except CierreContabilidad.DoesNotExist:
            pass

    if not cierre:
        cierre = (
            CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=[
                    "pendiente",
                    "procesando",
                    "clasificacion",
                    "incidencias",
                    "en_revision",
                ],
            )
            .order_by("-fecha_creacion")
            .first()
        )

    return cierre

