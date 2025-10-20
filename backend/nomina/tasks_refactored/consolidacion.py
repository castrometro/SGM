"""
🔄 CONSOLIDACIÓN DE DATOS - TASKS
==================================

Tareas Celery para consolidación de datos de nómina con dual logging.

Refactorizado desde: tasks.py
Versión: 2.5.0
Fecha: 2025-10-20

Funcionalidades:
- Consolidación de datos (Libro + Movimientos + Analista)
- Dual logging (TarjetaActivityLogNomina + ActivityEvent)
- Soporte para modo optimizado y secuencial
- Procesamiento paralelo con Celery Chord

Patrones de Logging:
- consolidacion_iniciada → Process_Start (inicio visible en UI)
- consolidacion_completada → Data_Integration_Complete (éxito)
- consolidacion_error → Data_Integration_Error (error)
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


# ==============================================================================
# FUNCIONES DE LOGGING DUAL
# ==============================================================================

def log_consolidacion_start(cierre_id, usuario_id, modo, detalles_extra=None):
    """
    Registra el INICIO de la consolidación en ambos sistemas de logging.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario que inició la consolidación
        modo: Modo de consolidación ('optimizado' o 'secuencial')
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Preparar detalles
        detalles = {
            'cierre_id': cierre_id,
            'periodo': cierre.periodo,
            'cliente_id': cierre.cliente_id,
            'estado_inicial': cierre.estado,
            'modo_consolidacion': modo,
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_iniciada",
            descripcion=f"Iniciando consolidación de datos de nómina (modo: {modo})",
            usuario=usuario,
            detalles=detalles,
            resultado="info"
        )
        
        # 2. LOG EN ACTIVITY EVENT (base de datos de eventos)
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.PROCESS_START,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.info(f"✅ Dual logging iniciado: consolidación cierre {cierre_id} - {modo}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_start: {e}")


def log_consolidacion_complete(cierre_id, usuario_id, resultado, detalles_extra=None):
    """
    Registra la FINALIZACIÓN EXITOSA de la consolidación en ambos sistemas.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        resultado: Resultado de la consolidación (dict con estadísticas)
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Estadísticas del resultado
        total_consolidados = resultado.get('empleados_consolidados', 0)
        total_headers = resultado.get('headers_consolidados', 0)
        total_movimientos = resultado.get('movimientos_consolidados', 0)
        
        # Preparar detalles
        detalles = {
            'cierre_id': cierre_id,
            'periodo': cierre.periodo,
            'estado_final': cierre.estado,
            'empleados_consolidados': total_consolidados,
            'headers_consolidados': total_headers,
            'movimientos_consolidados': total_movimientos,
            'duracion_segundos': resultado.get('duracion_segundos', 0),
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_completada",
            descripcion=(
                f"Consolidación completada exitosamente: "
                f"{total_consolidados} empleados, {total_headers} conceptos, "
                f"{total_movimientos} movimientos"
            ),
            usuario=usuario,
            detalles=detalles,
            resultado="exito"
        )
        
        # 2. LOG EN ACTIVITY EVENT
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.DATA_INTEGRATION_COMPLETE,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.info(f"✅ Dual logging completado: consolidación cierre {cierre_id} exitosa")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_complete: {e}")


def log_consolidacion_error(cierre_id, usuario_id, error, detalles_extra=None):
    """
    Registra un ERROR durante la consolidación en ambos sistemas.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        error: Mensaje de error o excepción
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Preparar detalles del error
        detalles = {
            'cierre_id': cierre_id,
            'error': str(error),
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_error",
            descripcion=f"Error en consolidación: {str(error)[:200]}",
            usuario=usuario,
            detalles=detalles,
            resultado="error"
        )
        
        # 2. LOG EN ACTIVITY EVENT
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.DATA_INTEGRATION_ERROR,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.error(f"✅ Dual logging error: consolidación cierre {cierre_id} - {error}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_error: {e}")


# ==============================================================================
# TAREA PRINCIPAL CON DUAL LOGGING
# ==============================================================================

@shared_task(bind=True, queue='nomina_queue')
def consolidar_datos_nomina_con_logging(self, cierre_id, usuario_id=None, modo='optimizado'):
    """
    🔄 TAREA PRINCIPAL: CONSOLIDACIÓN DE DATOS CON DUAL LOGGING
    
    Wrapper que ejecuta la consolidación (optimizada o secuencial) con logging dual.
    
    Args:
        cierre_id: ID del cierre a consolidar
        usuario_id: ID del usuario que inició la consolidación
        modo: 'optimizado' (Celery Chord) o 'secuencial' (procesamiento lineal)
    
    Returns:
        dict: Resultado de la consolidación con estadísticas
    
    Logging Dual:
        - TarjetaActivityLogNomina (tarjeta='consolidacion', visible en UI)
        - ActivityEvent (base de datos de eventos del sistema)
    """
    from nomina.models import CierreNomina
    
    tiempo_inicio = timezone.now()
    
    logger.info(f"🔄 [CONSOLIDACIÓN] Iniciando para cierre {cierre_id} - Modo: {modo}")
    
    # ✅ LOG DUAL: Inicio de consolidación
    log_consolidacion_start(
        cierre_id=cierre_id,
        usuario_id=usuario_id,
        modo=modo,
        detalles_extra={
            'task_id': self.request.id,
            'worker': self.request.hostname
        }
    )
    
    try:
        # EJECUTAR CONSOLIDACIÓN SEGÚN MODO
        if modo == 'optimizado':
            logger.info("🚀 Usando consolidación OPTIMIZADA con Celery Chord")
            from nomina.tasks import consolidar_datos_nomina_task_optimizado
            resultado = consolidar_datos_nomina_task_optimizado(cierre_id)
        else:
            logger.info("⏳ Usando consolidación SECUENCIAL")
            from nomina.tasks import consolidar_datos_nomina_task_secuencial
            resultado = consolidar_datos_nomina_task_secuencial(cierre_id)
        
        # Calcular duración
        tiempo_fin = timezone.now()
        duracion = (tiempo_fin - tiempo_inicio).total_seconds()
        
        # Agregar duración al resultado
        if isinstance(resultado, dict):
            resultado['duracion_segundos'] = duracion
        else:
            resultado = {
                'success': True,
                'duracion_segundos': duracion
            }
        
        # Obtener estadísticas de la consolidación
        cierre = CierreNomina.objects.get(id=cierre_id)
        resultado['empleados_consolidados'] = cierre.nomina_consolidada.count()
        
        # Contar headers consolidados
        from nomina.models import HeaderValorEmpleado
        resultado['headers_consolidados'] = HeaderValorEmpleado.objects.filter(
            nomina_consolidada__cierre=cierre
        ).count()
        
        # Contar movimientos consolidados
        from nomina.models import MovimientoPersonal
        resultado['movimientos_consolidados'] = MovimientoPersonal.objects.filter(
            nomina_consolidada__cierre=cierre
        ).count()
        
        # 🔄 ACTUALIZAR ESTADO DEL CIERRE
        # Si el cierre NO estaba en 'con_incidencias', cambiar a 'datos_consolidados'
        estado_anterior = cierre.estado
        if estado_anterior != 'con_incidencias':
            cierre.estado = 'datos_consolidados'
            cierre.save(update_fields=['estado'])
            resultado['estado_final'] = 'datos_consolidados'
            logger.info(f"✅ Estado actualizado: {estado_anterior} → datos_consolidados")
        else:
            resultado['estado_final'] = estado_anterior
            logger.info(f"ℹ️ Estado preservado: {estado_anterior} (con incidencias)")
        
        # ✅ LOG DUAL: Consolidación completada exitosamente
        log_consolidacion_complete(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            resultado=resultado,
            detalles_extra={
                'task_id': self.request.id,
                'modo': modo
            }
        )
        
        logger.info(
            f"✅ [CONSOLIDACIÓN] Completada para cierre {cierre_id}: "
            f"{resultado.get('empleados_consolidados', 0)} empleados, "
            f"{resultado.get('headers_consolidados', 0)} conceptos, "
            f"{resultado.get('movimientos_consolidados', 0)} movimientos "
            f"en {duracion:.2f}s"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ [CONSOLIDACIÓN] Error para cierre {cierre_id}: {e}")
        
        # ❌ LOG DUAL: Error en consolidación
        log_consolidacion_error(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            error=str(e),
            detalles_extra={
                'task_id': self.request.id,
                'modo': modo,
                'tipo_error': type(e).__name__
            }
        )
        
        # Revertir estado del cierre
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado_consolidacion = 'error'
            cierre.save(update_fields=['estado_consolidacion'])
        except Exception as revert_error:
            logger.error(f"❌ Error revirtiendo estado: {revert_error}")
        
        # Re-lanzar la excepción para que Celery la registre
        raise
