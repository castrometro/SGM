"""
Tareas Celery para procesamiento de Movimientos del Mes
Extraído de tasks.py para mejor organización y mantenibilidad

Este módulo contiene la tarea principal para procesar archivos Excel
de movimientos del mes (altas, bajas, ausentismos, vacaciones, variaciones).

Implementa el patrón de logging dual:
- TarjetaActivityLogNomina: Eventos visibles para el usuario (process_start, process_complete)
- ActivityEvent: Audit trail técnico detallado

IMPORTANTE: Siempre pasar usuario_id a través de las tareas para logging correcto.
"""

import logging
from celery import shared_task

from ..models import MovimientosMesUpload
from ..utils.MovimientoMes import procesar_archivo_movimientos_mes_util

logger = logging.getLogger(__name__)

# Helper para obtener usuario del sistema como fallback
def _get_sistema_user():
    """Obtiene el primer usuario staff como usuario del sistema"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_staff=True).first() or User.objects.first()


@shared_task(bind=True, queue='nomina_queue')
def procesar_movimientos_mes_con_logging(self, movimiento_id, usuario_id=None):
    """
    Procesa un archivo de movimientos del mes con logging completo dual.
    
    Esta tarea procesa el archivo Excel de movimientos y genera:
    - Movimientos de Altas/Bajas
    - Movimientos de Ausentismo  
    - Movimientos de Vacaciones
    - Movimientos de Variación de Sueldo
    - Movimientos de Variación de Contrato
    
    Args:
        movimiento_id (int): ID del MovimientosMesUpload a procesar
        usuario_id (int, optional): ID del usuario que inició el procesamiento
        
    Returns:
        dict: Resultados del procesamiento con contadores por tipo de movimiento
        
    Implementa Logging Dual:
        - TarjetaActivityLogNomina: process_start, process_complete (user-facing)
        - ActivityEvent: procesamiento_celery_iniciado, procesamiento_completado, procesamiento_error (audit)
    """
    from ..models_logging import registrar_actividad_tarjeta_nomina
    from ..models import ActivityEvent
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Obtener usuario real o usar sistema_user como fallback
    if usuario_id:
        try:
            usuario = User.objects.get(id=usuario_id)
            logger.info(f"Procesando movimientos mes con usuario: {usuario.correo_bdo} (ID: {usuario_id})")
        except User.DoesNotExist:
            logger.warning(f"Usuario {usuario_id} no encontrado, usando sistema_user")
            usuario = _get_sistema_user()
    else:
        logger.warning(f"No se proporcionó usuario_id, usando sistema_user")
        usuario = _get_sistema_user()
    
    logger.info(f"[MOVIMIENTOS MES] Iniciando procesamiento de archivo id={movimiento_id}, usuario={usuario.correo_bdo}")
    
    try:
        # Obtener referencias
        movimiento = MovimientosMesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=movimiento_id)
        cierre = movimiento.cierre
        cliente = cierre.cliente
        
        # ============================================================
        # DUAL LOGGING: Procesamiento iniciado
        # ============================================================
        
        # 1. ActivityEvent - Audit trail técnico
        ActivityEvent.log(
            user=usuario,  # ✅ Usuario real
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_celery_iniciado',
            resource_type='movimientos_mes',
            resource_id=str(movimiento_id),
            details={
                'movimiento_id': movimiento_id,
                'archivo_nombre': movimiento.archivo.name if movimiento.archivo else "N/A",
                'celery_task_id': self.request.id,
                'usuario_id': usuario_id,
                'usuario_correo': usuario.correo_bdo
            }
        )
        
        # 2. TarjetaActivityLogNomina - User-facing event
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="movimientos_mes",
            accion="process_start",
            descripcion="Iniciando procesamiento de archivo de movimientos del mes",
            usuario=usuario,  # ✅ Usuario real
            resultado='info',
            detalles={
                "movimiento_id": movimiento_id,
                "archivo_nombre": movimiento.archivo.name if movimiento.archivo else "N/A",
                "periodo": str(cierre.periodo)
            }
        )
        
        # ============================================================
        # PROCESAMIENTO: Cambiar estado y ejecutar
        # ============================================================
        
        movimiento.estado = 'en_proceso'
        movimiento.save(update_fields=['estado'])
        
        logger.info(f"[MOVIMIENTOS MES] Ejecutando procesamiento de archivo: {movimiento.archivo.name}")
        
        # Procesar archivo Excel con utility function
        resultados = procesar_archivo_movimientos_mes_util(movimiento)
        
        logger.info(f"[MOVIMIENTOS MES] Procesamiento completado. Resultados: {resultados}")
        
        # ============================================================
        # DETERMINAR ESTADO FINAL
        # ============================================================
        
        movimiento.resultados_procesamiento = resultados
        
        if resultados.get('errores'):
            # Verificar si hay algún registro exitoso
            registros_exitosos = sum(v for k, v in resultados.items() if k != 'errores' and isinstance(v, int))
            
            if registros_exitosos > 0:
                estado_final = 'con_errores_parciales'
                resultado_actividad = 'warning'
                logger.warning(f"[MOVIMIENTOS MES] Procesamiento con errores parciales: {len(resultados['errores'])} errores, {registros_exitosos} registros exitosos")
            else:
                estado_final = 'con_error'
                resultado_actividad = 'error'
                logger.error(f"[MOVIMIENTOS MES] Procesamiento con error total: {len(resultados['errores'])} errores")
        else:
            estado_final = 'procesado'  # ✅ Usar "procesado" (no "completado")
            resultado_actividad = 'exito'
            logger.info(f"[MOVIMIENTOS MES] Procesamiento exitoso sin errores")
        
        movimiento.estado = estado_final
        movimiento.save(update_fields=['estado', 'resultados_procesamiento'])
        
        # ============================================================
        # DUAL LOGGING: Procesamiento completado
        # ============================================================
        
        registros_totales = sum(v for k, v in resultados.items() if k != 'errores' and isinstance(v, int))
        errores_count = len(resultados.get('errores', []))
        
        # 1. ActivityEvent - Audit trail técnico
        ActivityEvent.log(
            user=usuario,  # ✅ Usuario real
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_completado',
            resource_type='movimientos_mes',
            resource_id=str(movimiento_id),
            details={
                'movimiento_id': movimiento_id,
                'estado_final': estado_final,
                'resultados': resultados,
                'registros_totales': registros_totales,
                'errores_count': errores_count,
                'celery_task_id': self.request.id,
                'usuario_id': usuario_id,
                'usuario_correo': usuario.correo_bdo
            }
        )
        
        # 2. TarjetaActivityLogNomina - User-facing event
        descripcion = f"Procesamiento completado con estado: {estado_final}"
        if errores_count > 0:
            descripcion += f". Errores: {errores_count}"
        
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="movimientos_mes",
            accion="process_complete",
            descripcion=descripcion,
            usuario=usuario,  # ✅ Usuario real
            resultado=resultado_actividad,
            detalles={
                "movimiento_id": movimiento_id,
                "estado_final": estado_final,  # ✅ "procesado" no "completado"
                "resultados": resultados,
                "registros_totales": registros_totales,
                "errores_count": errores_count
            }
        )
        
        logger.info(f"[MOVIMIENTOS MES] ✅ Procesamiento finalizado exitosamente. Estado: {estado_final}")
        
        return resultados
        
    except Exception as e:
        error_msg = f"Error procesando movimientos mes id={movimiento_id}: {str(e)}"
        logger.error(f"[MOVIMIENTOS MES] ❌ {error_msg}", exc_info=True)
        
        # ============================================================
        # MANEJO DE ERROR: Actualizar estados y logging
        # ============================================================
        
        try:
            movimiento = MovimientosMesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=movimiento_id)
            cierre = movimiento.cierre
            cliente = cierre.cliente
            
            # Actualizar estado del movimiento
            movimiento.estado = 'con_error'
            movimiento.resultados_procesamiento = {'errores': [str(e)]}
            movimiento.save(update_fields=['estado', 'resultados_procesamiento'])
            
            # ============================================================
            # DUAL LOGGING: Error en procesamiento
            # ============================================================
            
            # 1. ActivityEvent - Audit trail técnico
            ActivityEvent.log(
                user=usuario,  # ✅ Usuario real
                cliente=cliente,
                cierre=cierre,
                event_type='error',
                action='procesamiento_error',
                resource_type='movimientos_mes',
                resource_id=str(movimiento_id),
                details={
                    'movimiento_id': movimiento_id,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'celery_task_id': self.request.id,
                    'usuario_id': usuario_id,
                    'usuario_correo': usuario.correo_bdo
                }
            )
            
            # 2. TarjetaActivityLogNomina - User-facing event
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta="movimientos_mes",
                accion="process_complete",
                descripcion=f"Error en procesamiento: {str(e)}",
                usuario=usuario,  # ✅ Usuario real
                resultado="error",
                detalles={
                    "movimiento_id": movimiento_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
        except Exception as log_error:
            logger.error(f"[MOVIMIENTOS MES] Error adicional al intentar registrar error: {log_error}", exc_info=True)
        
        # Re-lanzar excepción para que Celery la maneje
        raise
