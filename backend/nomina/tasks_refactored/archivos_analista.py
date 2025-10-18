"""
Tareas Celery para procesamiento de Archivos del Analista
Extraído de tasks.py para mejor organización y mantenibilidad

Este módulo contiene la tarea para procesar archivos Excel subidos por analistas:
- Finiquitos: Procesa terminaciones de contratos
- Incidencias: Procesa ausentismos y eventos especiales
- Ingresos: Procesa nuevas incorporaciones

Implementa el patrón de logging dual:
- TarjetaActivityLogNomina: Eventos visibles para el usuario (process_start, process_complete)
- ActivityEvent: Audit trail técnico detallado

IMPORTANTE: El tipo de archivo se registra en todos los logs para diferenciación.
"""

import logging
from celery import shared_task

from ..models import ArchivoAnalistaUpload
from ..utils.ArchivosAnalista import procesar_archivo_analista_util

logger = logging.getLogger(__name__)

# Helper para obtener usuario del sistema como fallback
def _get_sistema_user():
    """Obtiene el primer usuario staff como usuario del sistema"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_staff=True).first() or User.objects.first()


# Mapeo de tipos de archivo para logs más claros
TIPO_ARCHIVO_DISPLAY = {
    'finiquitos': 'Finiquitos',
    'incidencias': 'Incidencias/Ausentismos',
    'ingresos': 'Nuevos Ingresos'
}


@shared_task(bind=True, queue='nomina_queue')
def procesar_archivo_analista_con_logging(self, archivo_id, usuario_id=None):
    """
    Procesa un archivo subido por el analista con logging completo dual.
    
    El archivo puede ser de 3 tipos:
    - finiquitos: Procesa terminaciones de contratos
    - incidencias: Procesa ausentismos y eventos especiales  
    - ingresos: Procesa nuevas incorporaciones
    
    Args:
        archivo_id (int): ID del ArchivoAnalistaUpload a procesar
        usuario_id (int, optional): ID del usuario (analista) que subió el archivo
        
    Returns:
        dict: Resultados del procesamiento con contadores
        
    Implementa Logging Dual:
        - TarjetaActivityLogNomina: process_start, process_complete (user-facing)
        - ActivityEvent: procesamiento_celery_iniciado, procesamiento_completado, procesamiento_error (audit)
        
    IMPORTANTE: Todos los logs incluyen el tipo de archivo para diferenciación.
    """
    from ..models_logging import registrar_actividad_tarjeta_nomina
    from ..models import ActivityEvent
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Obtener usuario real o usar sistema_user como fallback
    if usuario_id:
        try:
            usuario = User.objects.get(id=usuario_id)
            logger.info(f"Procesando archivo analista con usuario: {usuario.correo_bdo} (ID: {usuario_id})")
        except User.DoesNotExist:
            logger.warning(f"Usuario {usuario_id} no encontrado, usando sistema_user")
            usuario = _get_sistema_user()
    else:
        # Si no se proporciona usuario, usar el analista asignado al archivo
        try:
            archivo_temp = ArchivoAnalistaUpload.objects.select_related('analista').get(id=archivo_id)
            if archivo_temp.analista:
                usuario = archivo_temp.analista
                logger.info(f"Usando analista del archivo: {usuario.correo_bdo}")
            else:
                logger.warning(f"Archivo sin analista asignado, usando sistema_user")
                usuario = _get_sistema_user()
        except Exception as e:
            logger.warning(f"Error obteniendo analista del archivo: {e}, usando sistema_user")
            usuario = _get_sistema_user()
    
    try:
        # Obtener referencias
        archivo = ArchivoAnalistaUpload.objects.select_related(
            'cierre', 'cierre__cliente', 'analista'
        ).get(id=archivo_id)
        
        cierre = archivo.cierre
        cliente = cierre.cliente
        tipo_archivo = archivo.tipo_archivo or 'desconocido'
        tipo_display = TIPO_ARCHIVO_DISPLAY.get(tipo_archivo.lower(), tipo_archivo.title())
        
        logger.info(
            f"[ARCHIVO ANALISTA] Iniciando procesamiento de archivo id={archivo_id}, "
            f"tipo={tipo_display}, usuario={usuario.correo_bdo}"
        )
        
        # ============================================================
        # DUAL LOGGING: Procesamiento iniciado
        # ============================================================
        
        # 1. ActivityEvent - Audit trail técnico
        # ✅ resource_type incluye el tipo específico de archivo para diferenciación
        resource_type_especifico = f'archivo_analista_{tipo_archivo}'  # ej: 'archivo_analista_finiquitos'
        
        ActivityEvent.log(
            user=usuario,  # ✅ Usuario real
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_celery_iniciado',
            resource_type=resource_type_especifico,  # ✅ 'archivo_analista_finiquitos' / 'archivo_analista_incidencias' / 'archivo_analista_ingresos'
            resource_id=str(archivo_id),
            details={
                'archivo_id': archivo_id,
                'tipo_archivo': tipo_archivo,  # ✅ Diferenciación de tipo
                'tipo_display': tipo_display,
                'archivo_nombre': archivo.archivo.name if archivo.archivo else "N/A",
                'celery_task_id': self.request.id,
                'usuario_id': usuario.id,
                'usuario_correo': usuario.correo_bdo,
                'analista_id': archivo.analista.id if archivo.analista else None,
                'analista_correo': archivo.analista.correo_bdo if archivo.analista else None
            }
        )
        
        # 2. TarjetaActivityLogNomina - User-facing event
        # ✅ tarjeta incluye el tipo específico de archivo (abreviado para DB limit de 25 chars)
        tarjeta_especifica = f'analista_{tipo_archivo}'  # ej: 'analista_finiquitos' (20 chars)
        
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta=tarjeta_especifica,  # ✅ 'analista_finiquitos' / 'analista_incidencias' / 'analista_ingresos'
            accion="process_start",
            descripcion=f"Iniciando procesamiento de archivo: {tipo_display}",  # ✅ Tipo en descripción
            usuario=usuario,  # ✅ Usuario real
            resultado='info',
            detalles={
                "archivo_id": archivo_id,
                "tipo_archivo": tipo_archivo,  # ✅ Diferenciación de tipo
                "tipo_display": tipo_display,
                "archivo_nombre": archivo.archivo.name if archivo.archivo else "N/A",
                "periodo": str(cierre.periodo)
            }
        )
        
        # ============================================================
        # PROCESAMIENTO: Cambiar estado y ejecutar
        # ============================================================
        
        archivo.estado = 'en_proceso'
        archivo.save(update_fields=['estado'])
        
        logger.info(
            f"[ARCHIVO ANALISTA] Ejecutando procesamiento de {tipo_display}: {archivo.archivo.name}"
        )
        
        # Procesar archivo según tipo (finiquitos/incidencias/ingresos)
        resultados = procesar_archivo_analista_util(archivo)
        
        logger.info(
            f"[ARCHIVO ANALISTA] Procesamiento de {tipo_display} completado. "
            f"Resultados: {resultados}"
        )
        
        # ============================================================
        # DETERMINAR ESTADO FINAL
        # ============================================================
        
        procesados = resultados.get('procesados', 0)
        errores = resultados.get('errores', [])
        errores_count = len(errores) if isinstance(errores, list) else 0
        
        if errores_count > 0:
            if procesados > 0:
                estado_final = 'procesado'  # Parcialmente exitoso
                resultado_actividad = 'warning'
                logger.warning(
                    f"[ARCHIVO ANALISTA] {tipo_display} procesado con {errores_count} errores, "
                    f"{procesados} registros exitosos"
                )
            else:
                estado_final = 'con_error'  # Totalmente fallido
                resultado_actividad = 'error'
                logger.error(
                    f"[ARCHIVO ANALISTA] {tipo_display} falló completamente: "
                    f"{errores_count} errores, 0 registros exitosos"
                )
        else:
            estado_final = 'procesado'  # ✅ Usar "procesado" (no "completado")
            resultado_actividad = 'exito'
            logger.info(
                f"[ARCHIVO ANALISTA] {tipo_display} procesado exitosamente sin errores: "
                f"{procesados} registros"
            )
        
        archivo.estado = estado_final
        archivo.save(update_fields=['estado'])
        
        # ============================================================
        # DUAL LOGGING: Procesamiento completado
        # ============================================================
        
        # 1. ActivityEvent - Audit trail técnico
        ActivityEvent.log(
            user=usuario,  # ✅ Usuario real
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='procesamiento_completado',
            resource_type=resource_type_especifico,  # ✅ 'archivo_analista_finiquitos' / 'archivo_analista_incidencias' / 'archivo_analista_ingresos'
            resource_id=str(archivo_id),
            details={
                'archivo_id': archivo_id,
                'tipo_archivo': tipo_archivo,  # ✅ Diferenciación de tipo
                'tipo_display': tipo_display,
                'estado_final': estado_final,
                'resultados': resultados,
                'procesados': procesados,
                'errores_count': errores_count,
                'celery_task_id': self.request.id,
                'usuario_id': usuario.id,
                'usuario_correo': usuario.correo_bdo
            }
        )
        
        # 2. TarjetaActivityLogNomina - User-facing event
        descripcion = f"Procesamiento de {tipo_display} completado: {estado_final}"
        if errores_count > 0:
            descripcion += f" ({errores_count} errores)"
        
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta=tarjeta_especifica,  # ✅ 'analista_finiquitos' / 'analista_incidencias' / 'analista_ingresos'
            accion="process_complete",
            descripcion=descripcion,  # ✅ Tipo en descripción
            usuario=usuario,  # ✅ Usuario real
            resultado=resultado_actividad,
            detalles={
                "archivo_id": archivo_id,
                "tipo_archivo": tipo_archivo,  # ✅ Diferenciación de tipo
                "tipo_display": tipo_display,
                "estado_final": estado_final,
                "procesados": procesados,
                "errores_count": errores_count
            }
        )
        
        logger.info(
            f"[ARCHIVO ANALISTA] ✅ Procesamiento de {tipo_display} finalizado exitosamente. "
            f"Estado: {estado_final}"
        )
        
        return resultados
        
    except Exception as e:
        error_msg = f"Error procesando archivo analista id={archivo_id}: {str(e)}"
        logger.error(f"[ARCHIVO ANALISTA] ❌ {error_msg}", exc_info=True)
        
        # ============================================================
        # MANEJO DE ERROR: Actualizar estados y logging
        # ============================================================
        
        try:
            archivo = ArchivoAnalistaUpload.objects.select_related(
                'cierre', 'cierre__cliente'
            ).get(id=archivo_id)
            
            cierre = archivo.cierre
            cliente = cierre.cliente
            tipo_archivo = archivo.tipo_archivo or 'desconocido'
            tipo_display = TIPO_ARCHIVO_DISPLAY.get(tipo_archivo.lower(), tipo_archivo.title())
            resource_type_especifico = f'archivo_analista_{tipo_archivo}'  # ✅ Para logging de error
            tarjeta_especifica = f'analista_{tipo_archivo}'  # ✅ Para logging de error (abreviado)
            
            # Actualizar estado del archivo
            archivo.estado = 'con_error'
            archivo.save(update_fields=['estado'])
            
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
                resource_type=resource_type_especifico,  # ✅ 'archivo_analista_finiquitos' / 'archivo_analista_incidencias' / 'archivo_analista_ingresos'
                resource_id=str(archivo_id),
                details={
                    'archivo_id': archivo_id,
                    'tipo_archivo': tipo_archivo,  # ✅ Diferenciación de tipo
                    'tipo_display': tipo_display,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'celery_task_id': self.request.id,
                    'usuario_id': usuario.id,
                    'usuario_correo': usuario.correo_bdo
                }
            )
            
            # 2. TarjetaActivityLogNomina - User-facing event
            registrar_actividad_tarjeta_nomina(
                cierre_id=cierre.id,
                tarjeta=tarjeta_especifica,  # ✅ 'analista_finiquitos' / 'analista_incidencias' / 'analista_ingresos'
                accion="process_complete",
                descripcion=f"Error en procesamiento de {tipo_display}: {str(e)}",  # ✅ Tipo en descripción
                usuario=usuario,  # ✅ Usuario real
                resultado="error",
                detalles={
                    "archivo_id": archivo_id,
                    "tipo_archivo": tipo_archivo,  # ✅ Diferenciación de tipo
                    "tipo_display": tipo_display,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
        except Exception as log_error:
            logger.error(
                f"[ARCHIVO ANALISTA] Error adicional al intentar registrar error: {log_error}",
                exc_info=True
            )
        
        # Re-lanzar excepción para que Celery la maneje
        raise
