# backend/payroll/signals.py
# Signals para trigger automático de procesamiento

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models.models_fase_1 import ArchivoSubido
from .tasks.libro_remuneraciones import procesar_libro_remuneraciones

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ArchivoSubido)
def trigger_procesamiento_automatico(sender, instance, created, **kwargs):
    """
    Signal que dispara automáticamente el procesamiento cuando:
    1. Se crea un nuevo archivo (created=True) 
    2. Solo para archivos de tipo libro_remuneraciones
    3. Solo si está en estado 'subido' y estado_procesamiento 'pendiente'
    """
    
    # Solo disparar para archivos de tipo libro_remuneraciones
    if instance.tipo_archivo != 'libro_remuneraciones':
        return
    
    # Solo disparar para archivos nuevos en estado correcto
    if created and instance.estado == 'subido' and instance.estado_procesamiento == 'pendiente':
        
        logger.info(f"🔔 Signal: Disparando procesamiento para archivo NUEVO {instance.id}")
        
        try:
            # Disparar tarea Celery de forma asíncrona
            result = procesar_libro_remuneraciones.delay(instance.id)
            
            logger.info(f"✅ Signal: Task disparada con ID {result.id} para archivo {instance.id}")
            
        except Exception as e:
            logger.error(f"❌ Signal: Error disparando task para archivo {instance.id}: {str(e)}")
            
            # Marcar archivo como error
            instance.estado = 'error'
            instance.estado_procesamiento = 'error'
            instance.save(update_fields=['estado', 'estado_procesamiento'])
