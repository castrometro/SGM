# backend/nomina/utils/activity_logger.py
from ..models import TarjetaActivityLogNomina, CierreNomina
from django.contrib.auth import get_user_model

Usuario = get_user_model()

def registrar_actividad_tarjeta_nomina(
    cierre_id,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado='exito',
    ip_address=None,
    archivo_relacionado=None,
    empleado_rut="",
    concepto_afectado=""
):
    """
    Registra una actividad en una tarjeta específica de nómina
    
    Args:
        cierre_id: ID del cierre de nómina
        tarjeta: Tipo de tarjeta ('libro_remuneraciones', 'movimientos_mes', etc.)
        accion: Acción realizada ('upload_excel', 'mapear_headers', etc.)
        descripcion: Descripción legible de la acción
        usuario: Usuario que realizó la acción (opcional)
        detalles: Dict con información adicional (opcional)
        resultado: 'exito', 'error', 'warning'
        ip_address: IP del usuario (opcional)
        archivo_relacionado: Referencia a UploadLogNomina (opcional)
        empleado_rut: RUT del empleado afectado (opcional)
        concepto_afectado: Concepto de remuneración afectado (opcional)
    
    Returns:
        TarjetaActivityLogNomina: El log creado
    """
    try:
        # Obtener el cierre
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Crear el log
        log_entry = TarjetaActivityLogNomina.objects.create(
            cierre=cierre,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles or {},
            resultado=resultado,
            ip_address=ip_address,
            archivo_relacionado=archivo_relacionado,
            empleado_rut=empleado_rut,
            concepto_afectado=concepto_afectado
        )
        
        return log_entry
        
    except Exception as e:
        # En caso de error, no fallar la operación principal
        print(f"Error registrando actividad de nómina: {e}")
        return None


def obtener_logs_cierre_nomina(cierre_id, tarjeta=None):
    """
    Obtiene los logs de actividad para un cierre específico de nómina
    
    Args:
        cierre_id: ID del cierre de nómina
        tarjeta: Filtrar por tarjeta específica (opcional)
    
    Returns:
        QuerySet: Logs de actividad ordenados por timestamp
    """
    try:
        logs = TarjetaActivityLogNomina.objects.filter(cierre_id=cierre_id)
        
        if tarjeta:
            logs = logs.filter(tarjeta=tarjeta)
            
        return logs.select_related('usuario', 'archivo_relacionado').order_by('-timestamp')
        
    except Exception as e:
        print(f"Error obteniendo logs de nómina: {e}")
        return TarjetaActivityLogNomina.objects.none()


def obtener_resumen_actividad_nomina(cierre_id):
    """
    Obtiene un resumen de actividad por tarjeta para un cierre
    
    Args:
        cierre_id: ID del cierre de nómina
        
    Returns:
        dict: Resumen de actividades por tarjeta
    """
    try:
        logs = TarjetaActivityLogNomina.objects.filter(cierre_id=cierre_id)
        
        resumen = {}
        for tarjeta_code, tarjeta_name in TarjetaActivityLogNomina.TARJETA_CHOICES:
            tarjeta_logs = logs.filter(tarjeta=tarjeta_code)
            resumen[tarjeta_code] = {
                'nombre': tarjeta_name,
                'total_actividades': tarjeta_logs.count(),
                'ultima_actividad': tarjeta_logs.first().timestamp if tarjeta_logs.exists() else None,
                'errores': tarjeta_logs.filter(resultado='error').count(),
                'warnings': tarjeta_logs.filter(resultado='warning').count(),
            }
            
        return resumen
        
    except Exception as e:
        print(f"Error generando resumen de actividad: {e}")
        return {}
