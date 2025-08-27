# backend/payroll/signals.py
# Signals para trigger automático de procesamiento

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models.models_fase_1 import ArchivoSubido
from .tasks.libro_remuneraciones import procesar_libro_remuneraciones
from .tasks.movimientos_mes import procesar_movimientos_mes
from .tasks.archivos_analista import (
    procesar_finiquitos_analista,
    procesar_ausentismos_analista,
    procesar_ingresos_analista
)
from .tasks.novedades_analista import (
    procesar_novedades_analista
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ArchivoSubido)
def trigger_procesamiento_automatico(sender, instance, created, **kwargs):
    """
    Signal que dispara automáticamente el procesamiento cuando:
    1. Se crea un nuevo archivo (created=True) 
    2. Para archivos de tipos soportados
    3. Solo si está en estado 'subido' y estado_procesamiento 'pendiente'
    """
    
    # Solo disparar para archivos nuevos en estado correcto
    if not (created and instance.estado == 'subido' and instance.estado_procesamiento == 'pendiente'):
        return
    
    logger.info(f"🔔 Signal: Disparando procesamiento para archivo NUEVO {instance.id} tipo {instance.tipo_archivo}")
    
    try:
        # Determinar qué tarea disparar según el tipo de archivo
        if instance.tipo_archivo == 'libro_remuneraciones':
            result = procesar_libro_remuneraciones.delay(instance.id)
            
        elif instance.tipo_archivo == 'movimientos_mes':
            result = procesar_movimientos_mes.delay(instance.id)
            
        # Archivos del analista
        elif instance.tipo_archivo == 'finiquitos':
            result = procesar_finiquitos_analista.delay(instance.id)
            
        elif instance.tipo_archivo == 'ausentismos':
            result = procesar_ausentismos_analista.delay(instance.id)
            
        elif instance.tipo_archivo == 'ingresos':
            result = procesar_ingresos_analista.delay(instance.id)
            
        elif instance.tipo_archivo == 'novedades':
            result = procesar_novedades_analista.delay(instance.id)
            
        else:
            logger.info(f"⚠️ Signal: Tipo de archivo '{instance.tipo_archivo}' no tiene procesamiento automático configurado")
            return
        
        logger.info(f"✅ Signal: Task disparada con ID {result.id} para archivo {instance.id}")
        
    except Exception as e:
        logger.error(f"❌ Signal: Error disparando task para archivo {instance.id}: {str(e)}")
        
        # Marcar archivo como error
        instance.estado = 'error'
        instance.estado_procesamiento = 'error'
        instance.save(update_fields=['estado', 'estado_procesamiento'])
