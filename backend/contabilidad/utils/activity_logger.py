# backend/contabilidad/utils/activity_logger.py
from ..models import TarjetaActivityLog, CierreContabilidad
from django.contrib.auth import get_user_model

Usuario = get_user_model()

def registrar_actividad_tarjeta(
    cliente_id,
    periodo,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado='exito',
    ip_address=None
):
    """
    Registra una actividad en una tarjeta específica
    
    Args:
        cliente_id: ID del cliente
        periodo: Periodo del cierre (ej: "2025-06")
        tarjeta: Tipo de tarjeta ('tipo_documento', 'libro_mayor', etc.)
        accion: Acción realizada ('manual_create', 'upload_excel', etc.)
        descripcion: Descripción legible de la acción
        usuario: Usuario que realizó la acción (opcional)
        detalles: Dict con información adicional (opcional)
        resultado: 'exito', 'error', 'warning'
        ip_address: IP del usuario (opcional)
    
    Returns:
        TarjetaActivityLog: El log creado
    """
    try:
        # Buscar o crear el cierre
        cierre, _ = CierreContabilidad.objects.get_or_create(
            cliente_id=cliente_id,
            periodo=periodo,
            defaults={
                'usuario': usuario,
                'estado': 'pendiente'
            }
        )
        
        # Crear el log
        log_entry = TarjetaActivityLog.objects.create(
            cierre=cierre,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles or {},
            resultado=resultado,
            ip_address=ip_address
        )
        
        return log_entry
        
    except Exception as e:
        # En caso de error, no fallar la operación principal
        print(f"Error registrando actividad: {e}")
        return None

def obtener_logs_tarjeta(cliente_id, periodo, tarjeta=None):
    """
    Obtiene los logs de actividad para un cierre específico
    
    Args:
        cliente_id: ID del cliente
        periodo: Periodo del cierre
        tarjeta: Filtrar por tarjeta específica (opcional)
    
    Returns:
        QuerySet: Logs de actividad ordenados por timestamp
    """
    try:
        cierre = CierreContabilidad.objects.get(
            cliente_id=cliente_id,
            periodo=periodo
        )
        
        logs = TarjetaActivityLog.objects.filter(cierre=cierre)
        
        if tarjeta:
            logs = logs.filter(tarjeta=tarjeta)
            
        return logs.select_related('usuario').order_by('-timestamp')
        
    except CierreContabilidad.DoesNotExist:
        return TarjetaActivityLog.objects.none()
