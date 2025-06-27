from datetime import date

from ..models import CierreContabilidad


def obtener_periodo_cierre_activo(cliente) -> str:
    """Devuelve el período del cierre activo o la fecha actual en YYYY-MM."""
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
    return cierre.periodo if cierre else date.today().strftime("%Y-%m")


def get_client_ip(request) -> str:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")
