# backend/contabilidad/views/helpers.py
import logging
from datetime import date

from django.http import HttpRequest
from api.models import Cliente
from contabilidad.models import CierreContabilidad, CuentaContable, AccountClassification, ClasificacionSet

logger = logging.getLogger(__name__)


def obtener_periodo_actividad_para_cliente(cliente: Cliente) -> str:
    """
    Helper function para obtener el período correcto para registrar actividades de tarjeta.
    Busca el cierre activo del cliente, si no encuentra usa la fecha actual.
    """
    try:
        cierre_para_actividad = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
        
        if cierre_para_actividad:
            return cierre_para_actividad.periodo
        else:
            return date.today().strftime("%Y-%m")
    except Exception:
        return date.today().strftime("%Y-%m")


def get_client_ip(request: HttpRequest) -> str:
    """
    Helper function para obtener la IP del cliente desde el request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def verificar_y_marcar_completo(cuenta_id: int) -> None:
    """
    Verifica si todas las cuentas del cliente están clasificadas y marca el cierre como completo.
    """
    try:
        cuenta = CuentaContable.objects.get(id=cuenta_id)
        cierre = (
            CierreContabilidad.objects.filter(cliente=cuenta.cliente)
            .order_by("-fecha_creacion")
            .first()
        )
        set_principal = ClasificacionSet.objects.filter(cliente=cuenta.cliente).first()
        if not (cierre and set_principal):
            return
        cuentas = CuentaContable.objects.filter(cliente=cuenta.cliente)
        clasificadas = AccountClassification.objects.filter(
            cuenta__in=cuentas, set_clas=set_principal
        ).values_list("cuenta_id", flat=True)
        if cuentas.exclude(id__in=clasificadas).count() == 0:
            cierre.estado = "completo"
            cierre.save(update_fields=["estado"])
    except Exception as e:
        logger.exception("Error al verificar cierre completo: %s", e)
