"""
🔍 GENERACIÓN DE INCIDENCIAS - TASKS
====================================

Tareas Celery para generación de incidencias de nómina con dual logging.

Refactorizado desde: tasks.py (generar_incidencias_consolidados_v2_task)
Versión: 2.5.0
Fecha: 2025-10-20

Funcionalidades:
- Generación de incidencias (comparación con período anterior)
- Dual logging (TarjetaActivityLogNomina + ActivityEvent)
- Soporte para clasificaciones específicas o completas
- Detección de variaciones, ausentismos, ingresos y finiquitos

Patrones de Logging:
- generacion_incidencias_iniciada → Incidence_Detection_Start
- generacion_incidencias_completada → Incidence_Detection_Complete
- generacion_incidencias_error → Incidence_Detection_Error
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


# ==============================================================================
# FUNCIONES DE LOGGING DUAL
# ==============================================================================

def log_incidencias_start(cierre_id, usuario_id, clasificaciones_seleccionadas=None, detalles_extra=None):
    """
    Registra el INICIO de la generación de incidencias en ambos sistemas de logging.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario que inició la generación
        clasificaciones_seleccionadas: Lista de IDs de clasificaciones o None para todas
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        modo = "filtrado" if clasificaciones_seleccionadas else "dual_v2"
        clasificaciones_count = len(clasificaciones_seleccionadas) if clasificaciones_seleccionadas else None
        
        # Detalles para logging
        detalles = {
            'cierre_id': cierre_id,
            'cliente': cierre.cliente.nombre if cierre.cliente else None,
            'periodo': str(cierre.periodo),
            'modo_procesamiento': modo,
            'clasificaciones_count': clasificaciones_count,
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ TarjetaActivityLogNomina (visible en UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta='incidencias',
            accion='process_start',  # ✅ Máx 25 caracteres
            descripcion=f'Celery: Generación de incidencias iniciada (modo: {modo})',
            usuario=usuario,
            detalles=detalles,
            resultado='info'
        )
        
        # 2️⃣ ActivityEvent (sistema de eventos)
        ActivityEvent.objects.create(
            event_type='process',
            action=f'incidencias_start_cierre_{cierre_id}',
            resource_type='nomina',
            resource_id=str(cierre_id),
            user=usuario,
            cliente=cierre.cliente,
            cierre=cierre,
            details=detalles
        )
        
        logger.info(f"📋 [LOGGING] Inicio de generación de incidencias registrado: Cierre {cierre_id}, Modo: {modo}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_incidencias_start: {e}")


def log_incidencias_complete(cierre_id, usuario_id, resultado, detalles_extra=None):
    """
    Registra la FINALIZACIÓN EXITOSA de la generación de incidencias en ambos sistemas.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        resultado: Resultado de la generación (dict con estadísticas)
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
        total_incidencias = resultado.get('incidencias_generadas', 0)
        incidencias_criticas = resultado.get('incidencias_criticas', 0)
        tipos_detectados = resultado.get('tipos_detectados', [])
        
        # Detalles para logging
        detalles = {
            'cierre_id': cierre_id,
            'total_incidencias': total_incidencias,
            'incidencias_criticas': incidencias_criticas,
            'tipos_detectados': tipos_detectados,
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ TarjetaActivityLogNomina (visible en UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta='incidencias',
            accion='process_complete',  # ✅ Máx 25 caracteres
            descripcion=f'Celery: Generación completada - {total_incidencias} incidencias detectadas',
            usuario=usuario,
            detalles=detalles,
            resultado='exito'
        )
        
        # 2️⃣ ActivityEvent (sistema de eventos)
        ActivityEvent.objects.create(
            event_type='process',
            action=f'incidencias_complete_cierre_{cierre_id}',
            resource_type='nomina',
            resource_id=str(cierre_id),
            user=usuario,
            cliente=cierre.cliente,
            cierre=cierre,
            details=detalles
        )
        
        logger.info(f"✅ [LOGGING] Generación de incidencias completada: {total_incidencias} incidencias")
        
    except Exception as e:
        logger.error(f"❌ Error en log_incidencias_complete: {e}")


def log_incidencias_error(cierre_id, usuario_id, error, detalles_extra=None):
    """
    Registra un ERROR en la generación de incidencias en ambos sistemas.
    
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
        
        # 1️⃣ TarjetaActivityLogNomina (visible en UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta='incidencias',
            accion='validation_error',  # 16 chars - was 'generacion_incidencias_error' (29 chars)
            descripcion=f'Celery: Error en generación de incidencias: {str(error)[:100]}',
            usuario=usuario,
            detalles=detalles,
            resultado='error'
        )
        
        # 2️⃣ ActivityEvent (sistema de eventos)
        ActivityEvent.objects.create(
            event_type='process',
            action=f'incidencias_error_cierre_{cierre_id}',
            resource_type='nomina',
            resource_id=str(cierre_id),
            user=usuario,
            cliente=cierre.cliente,
            cierre=cierre,
            details=detalles
        )
        
        logger.error(f"❌ [LOGGING] Error en generación de incidencias: {str(error)[:100]}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_incidencias_error: {e}")


# ==============================================================================
# TAREA PRINCIPAL CON LOGGING DUAL
# ==============================================================================

@shared_task(bind=True, queue='nomina_queue', max_retries=0)
def generar_incidencias_con_logging(self, cierre_id, usuario_id=0, clasificaciones_seleccionadas=None):
    """
    🔍 WRAPPER TASK: Generar incidencias con dual logging.
    
    Esta tarea orquesta la generación de incidencias y registra todo el proceso
    en ambos sistemas de logging (TarjetaActivityLogNomina + ActivityEvent).
    
    Args:
        cierre_id: ID del cierre para generar incidencias
        usuario_id: ID del usuario que ejecuta (0 = sistema)
        clasificaciones_seleccionadas: Lista de IDs de clasificaciones o None
    
    Returns:
        dict: Resultado con estadísticas de incidencias generadas
    
    Logging Dual:
        - TarjetaActivityLogNomina (tarjeta='incidencias', visible en UI)
        - ActivityEvent (base de datos de eventos del sistema)
    """
    from nomina.models import CierreNomina
    
    tiempo_inicio = timezone.now()
    
    modo = "filtrado" if clasificaciones_seleccionadas else "dual_v2"
    logger.info(f"🔍 [INCIDENCIAS] Iniciando generación para cierre {cierre_id} - Modo: {modo}")
    
    # ✅ LOG DUAL: Inicio de generación
    log_incidencias_start(
        cierre_id=cierre_id,
        usuario_id=usuario_id,
        clasificaciones_seleccionadas=clasificaciones_seleccionadas,
        detalles_extra={
            'task_id': self.request.id,
            'worker': self.request.hostname
        }
    )
    
    try:
        # EJECUTAR GENERACIÓN DE INCIDENCIAS USANDO TAREA SIMPLIFICADA
        from nomina.utils.DetectarIncidenciasConsolidadas import generar_incidencias_consolidados_v2
        
        logger.info(f"🚀 Llamando a generar_incidencias_consolidados_v2 (versión simplificada)...")
        
        # Llamar a la función simplificada directamente (no es tarea async)
        resultado_generacion = generar_incidencias_consolidados_v2(
            cierre_id=cierre_id,
            clasificaciones_seleccionadas=clasificaciones_seleccionadas
        )
        
        # Verificar si fue exitoso
        if not resultado_generacion.get('success', False):
            raise Exception(resultado_generacion.get('error', 'Error desconocido en generación'))
        
        # RECARGAR CIERRE PARA OBTENER ESTADO ACTUALIZADO
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # RECOPILAR ESTADÍSTICAS DEL RESULTADO
        total_incidencias = resultado_generacion.get('total_incidencias', 0)
        
        # Prioridades desde el resultado
        prioridades = resultado_generacion.get('prioridades', {})
        incidencias_criticas = prioridades.get('critica', 0)
        
        # Tipos detectados desde el resultado
        tipos_detectados = resultado_generacion.get('tipos_detectados', [])
        
        resultado = {
            'success': True,
            'cierre_id': cierre_id,
            'incidencias_generadas': total_incidencias,
            'incidencias_criticas': incidencias_criticas,
            'tipos_detectados': tipos_detectados,
            'estado_final': cierre.estado,
            'modo_procesamiento': modo,
            'conceptos_analizados': resultado_generacion.get('conceptos_analizados', 0),
            'variaciones_sobre_umbral': resultado_generacion.get('variaciones_sobre_umbral', 0),
            'umbral_usado': resultado_generacion.get('umbral_usado', 30.0),
            'tiempo_ejecucion': (timezone.now() - tiempo_inicio).total_seconds(),
            'periodo_actual': resultado_generacion.get('periodo_actual'),
            'periodo_anterior': resultado_generacion.get('periodo_anterior'),
            'primer_cierre': resultado_generacion.get('primer_cierre', False)
        }
        
        # ✅ LOG DUAL: Generación completada exitosamente
        log_incidencias_complete(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            resultado=resultado,
            detalles_extra={
                'task_id': self.request.id,
                'resultado_completo': resultado_generacion
            }
        )
        
        logger.info(
            f"✅ [INCIDENCIAS] Generación completada para cierre {cierre_id}: "
            f"{total_incidencias} incidencias ({incidencias_criticas} críticas)"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ [INCIDENCIAS] Error en generación para cierre {cierre_id}: {e}", exc_info=True)
        
        # ✅ LOG DUAL: Error en generación
        log_incidencias_error(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            error=e,
            detalles_extra={
                'task_id': self.request.id,
                'tiempo_antes_error': (timezone.now() - tiempo_inicio).total_seconds()
            }
        )
        
        # Revertir estado si es necesario
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            if cierre.estado == 'generando_incidencias':
                cierre.estado = 'datos_consolidados'
                cierre.save(update_fields=['estado'])
                logger.info(f"🔄 Estado revertido a 'datos_consolidados' tras error")
        except Exception as revert_error:
            logger.error(f"❌ Error revirtiendo estado: {revert_error}")
        
        # Re-raise para que Celery marque como fallida
        raise
