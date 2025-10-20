# backend/nomina/tasks_refactored/discrepancias.py
"""
Módulo de Discrepancias - Sistema de Verificación de Datos
Versión: 1.0.0

Este módulo contiene la tarea para generar y registrar discrepancias
en la verificación de datos de un cierre de nómina.

Objetivo:
- Detectar diferencias entre los datos consolidados
- Registrar discrepancias encontradas
- Actualizar estado del cierre según resultado (0 discrepancias o X discrepancias)
- Logging dual: TarjetaActivityLogNomina + ActivityEvent
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ===== 🔧 HELPER FUNCTIONS =====

def get_sistema_user():
    """Obtiene o crea el usuario 'sistema' para operaciones automáticas"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        usuario_sistema = User.objects.get(username='sistema')
    except User.DoesNotExist:
        logger.warning("Usuario 'sistema' no encontrado, usando primer superusuario")
        usuario_sistema = User.objects.filter(is_superuser=True).first()
        if not usuario_sistema:
            raise ValueError("No hay usuario sistema ni superusuarios disponibles")
    
    return usuario_sistema


# ===== 🎨 MAPEO DE ACCIONES A ACCION_CHOICES =====

ACCION_MAP = {
    # Generación de discrepancias
    'verificacion_iniciada': 'process_start',
    'verificacion_completada_sin_discrepancias': 'process_complete',
    'verificacion_completada_con_discrepancias': 'validation_error',
    'verificacion_error': 'validation_error',
    
    # Estados del proceso
    'archivos_verificados': 'validation_error',
    'estado_actualizado': 'state_change',
}


def get_tarjeta_accion(accion_descriptiva):
    """
    Convierte una acción descriptiva a una acción válida de ACCION_CHOICES.
    """
    if accion_descriptiva in ACCION_MAP:
        return ACCION_MAP[accion_descriptiva]
    
    # Fallback basado en sufijos
    if 'iniciado' in accion_descriptiva or 'iniciada' in accion_descriptiva:
        return 'process_start'
    elif 'completado' in accion_descriptiva or 'completada' in accion_descriptiva:
        return 'process_complete'
    elif 'error' in accion_descriptiva:
        return 'validation_error'
    else:
        return 'process_start'


# ===== 📊 FUNCIONES DE LOGGING DUAL =====

def log_discrepancias_start(cierre_id, accion, descripcion, usuario_id=None, detalles_extra=None):
    """
    Registra el inicio del proceso de verificación de discrepancias
    
    Args:
        cierre_id: ID del CierreNomina
        accion: Acción descriptiva
        descripcion: Descripción legible del proceso
        usuario_id: ID del usuario que inició la operación
        detalles_extra: Detalles adicionales opcionales
    """
    from ..models import CierreNomina, ActivityEvent
    from ..models_logging import registrar_actividad_tarjeta_nomina
    
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
        
        # Obtener usuario con fallback
        if usuario_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                logger.warning(f"Usuario ID {usuario_id} no encontrado, usando sistema")
                usuario = get_sistema_user()
        else:
            usuario = get_sistema_user()
        
        # Preparar detalles base
        detalles = {
            'cierre_id': cierre_id,
            'cliente_id': cliente.id,
            'cliente_nombre': cliente.nombre,
            'periodo': cierre.periodo,
            'estado_inicial': cierre.estado,
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ Logging en TarjetaActivityLogNomina (usuario-visible con acción del CHOICES)
        accion_tarjeta = get_tarjeta_accion(accion)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta='revision',  # Tarjeta de revisión/verificación
            accion=accion_tarjeta,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles,
            resultado='info'
        )
        
        # 2️⃣ Logging en ActivityEvent (audit trail con acción descriptiva completa)
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='verification',
            action=accion,
            resource_type='discrepancias',
            resource_id=str(cierre_id),
            details=detalles
        )
        
        logger.info(f"✅ Log dual iniciado: verificación discrepancias cierre {cierre_id} - {accion}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_discrepancias_start para cierre {cierre_id}: {e}")


def log_discrepancias_complete(cierre_id, accion, descripcion, usuario_id=None, resultado='exito', detalles_extra=None):
    """
    Registra la finalización del proceso de verificación de discrepancias
    
    Args:
        cierre_id: ID del CierreNomina
        accion: Acción descriptiva
        descripcion: Descripción legible del resultado
        usuario_id: ID del usuario
        resultado: 'exito', 'warning', o 'error'
        detalles_extra: Detalles adicionales
    """
    from ..models import CierreNomina, ActivityEvent
    from ..models_logging import registrar_actividad_tarjeta_nomina
    
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
        
        # Obtener usuario con fallback
        if usuario_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                usuario = get_sistema_user()
        else:
            usuario = get_sistema_user()
        
        # Preparar detalles
        detalles = {
            'cierre_id': cierre_id,
            'estado_final': cierre.estado,
            'timestamp_completado': timezone.now().isoformat(),
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ TarjetaActivityLogNomina (acción del CHOICES)
        accion_tarjeta = get_tarjeta_accion(accion)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta='revision',
            accion=accion_tarjeta,
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles,
            resultado=resultado
        )
        
        # 2️⃣ ActivityEvent (acción descriptiva completa)
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='verification',
            action=accion,
            resource_type='discrepancias',
            resource_id=str(cierre_id),
            details=detalles
        )
        
        logger.info(f"✅ Log dual completado: verificación discrepancias cierre {cierre_id} - {accion} - {resultado}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_discrepancias_complete para cierre {cierre_id}: {e}")


# ===== 🔍 HELPER: VERIFICACIÓN DE ARCHIVOS =====

def _verificar_archivos_listos_para_discrepancias(cierre):
    """
    Verifica que los archivos necesarios estén procesados para generar discrepancias
    
    Args:
        cierre: Instancia de CierreNomina
        
    Returns:
        bool: True si todos los archivos están listos
    """
    from ..models import LibroRemuneracionesUpload, MovimientosMesUpload
    
    # Verificar libro de remuneraciones procesado
    libro = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
    if not libro or libro.estado not in ['clasificado', 'procesado']:
        logger.warning(f"Libro de remuneraciones no procesado para cierre {cierre.id}")
        return False
    
    # Verificar movimientos del mes procesados
    movimientos = MovimientosMesUpload.objects.filter(cierre=cierre).first()
    if not movimientos or movimientos.estado != 'procesado':
        logger.warning(f"Movimientos del mes no procesados para cierre {cierre.id}")
        return False
    
    # Verificar al menos un archivo del analista procesado
    archivos_analista = cierre.archivos_analista.filter(estado='procesado')
    if archivos_analista.count() == 0:
        logger.warning(f"No hay archivos del analista procesados para cierre {cierre.id}")
        return False
    
    # Archivo de novedades es opcional - si existe debe estar procesado
    archivo_novedades = cierre.archivos_novedades.first()
    if archivo_novedades and archivo_novedades.estado not in ['clasificado', 'procesado']:
        logger.warning(f"Archivo de novedades no procesado para cierre {cierre.id}")
        return False
    
    return True


# ===== 🎯 TAREA PRINCIPAL =====

@shared_task(bind=True, queue='nomina_queue')
def generar_discrepancias_cierre_con_logging(self, cierre_id, usuario_id=None):
    """
    🔍 Genera discrepancias en la verificación de datos de un cierre
    
    Detecta diferencias entre:
    - Libro de Remuneraciones
    - Movimientos del Mes
    - Archivos del Analista
    - Novedades (opcional)
    
    Args:
        cierre_id: ID del CierreNomina
        usuario_id: ID del usuario que inició el proceso (opcional)
        
    Returns:
        dict: {
            'cierre_id': int,
            'total_discrepancias': int,
            'discrepancias_por_tipo': dict,
            'estado_final': str,
            'timestamp': str
        }
    """
    from ..utils.GenerarDiscrepancias import generar_todas_discrepancias
    from ..models import CierreNomina
    
    logger.info(f"🔍 Iniciando generación de discrepancias para cierre {cierre_id}")
    
    # ✅ Logging de inicio
    log_discrepancias_start(
        cierre_id=cierre_id,
        accion='verificacion_iniciada',
        descripcion='Iniciando verificación de datos y generación de discrepancias',
        usuario_id=usuario_id,
        detalles_extra={'task_id': self.request.id}
    )
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Cambiar estado a verificacion_datos al iniciar
        cierre.estado = 'verificacion_datos'
        cierre.save(update_fields=['estado'])
        
        # Verificar que el cierre tenga los archivos necesarios procesados
        if not _verificar_archivos_listos_para_discrepancias(cierre):
            raise ValueError("No todos los archivos están procesados para generar discrepancias")
        
        # Eliminar discrepancias anteriores si existen
        cantidad_eliminada = cierre.discrepancias.all().count()
        cierre.discrepancias.all().delete()
        
        logger.info(f"📋 Discrepancias anteriores eliminadas: {cantidad_eliminada}")
        
        # Generar nuevas discrepancias
        resultado = generar_todas_discrepancias(cierre)
        
        total_discrepancias = resultado.get('total_discrepancias', 0)
        
        # Actualizar estado del cierre según resultado
        if total_discrepancias == 0:
            # Sin discrepancias - datos verificados ✅
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.puede_consolidar = True
            accion_log = 'verificacion_completada_sin_discrepancias'
            descripcion_log = f'Verificación completada: 0 discrepancias encontradas. Cierre listo para consolidación.'
            resultado_log = 'exito'
        else:
            # Con discrepancias - requiere corrección ⚠️
            cierre.estado = 'con_discrepancias'
            cierre.puede_consolidar = False
            accion_log = 'verificacion_completada_con_discrepancias'
            descripcion_log = f'Verificación completada: {total_discrepancias} discrepancias encontradas. Requiere corrección.'
            resultado_log = 'warning'
        
        cierre.save(update_fields=['estado', 'puede_consolidar'])
        
        # ✅ Logging de finalización exitosa
        log_discrepancias_complete(
            cierre_id=cierre_id,
            accion=accion_log,
            descripcion=descripcion_log,
            usuario_id=usuario_id,
            resultado=resultado_log,
            detalles_extra={
                'total_discrepancias': total_discrepancias,
                'discrepancias_por_tipo': resultado.get('discrepancias_por_tipo', {}),
                'estado_final': cierre.estado,
                'puede_consolidar': cierre.puede_consolidar,
                'discrepancias_eliminadas': cantidad_eliminada,
            }
        )
        
        logger.info(f"✅ Discrepancias generadas exitosamente para cierre {cierre_id}: {total_discrepancias} discrepancias")
        
        return {
            'cierre_id': cierre_id,
            'total_discrepancias': total_discrepancias,
            'discrepancias_por_tipo': resultado.get('discrepancias_por_tipo', {}),
            'estado_final': cierre.estado,
            'puede_consolidar': cierre.puede_consolidar,
            'timestamp': timezone.now().isoformat(),
            'usuario_id': usuario_id,
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando discrepancias para cierre {cierre_id}: {e}")
        
        # Intentar volver al estado anterior
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'archivos_completos'
            cierre.save(update_fields=['estado'])
            
            # ✅ Logging de error
            log_discrepancias_complete(
                cierre_id=cierre_id,
                accion='verificacion_error',
                descripcion=f'Error en verificación de discrepancias: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={
                    'error': str(e),
                    'tipo_error': type(e).__name__,
                }
            )
        except Exception as ex:
            logger.error(f"❌ Error adicional al revertir estado: {ex}")
        
        raise
