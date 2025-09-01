# nomina/signals.py

import os
import logging
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from .models import LibroRemuneracionesUpload, MovimientosMesUpload

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=LibroRemuneracionesUpload)
def eliminar_archivo_libro_remuneraciones(sender, instance, **kwargs):
    """
    Eliminar archivo físico cuando se borra LibroRemuneracionesUpload
    desde cualquier lugar (Admin, API, shell, etc.)
    """
    if instance.archivo:
        try:
            if os.path.isfile(instance.archivo.path):
                archivo_path = instance.archivo.path
                os.remove(archivo_path)
                logger.info(f"[SIGNAL] Archivo eliminado: {archivo_path}")
            else:
                logger.warning(f"[SIGNAL] Archivo no existe en disco: {instance.archivo.path}")
        except Exception as e:
            logger.error(f"[SIGNAL] Error eliminando archivo de libro: {e}")


@receiver(pre_save, sender=LibroRemuneracionesUpload)
def eliminar_archivo_anterior_libro_remuneraciones(sender, instance, **kwargs):
    """
    Eliminar archivo anterior cuando se actualiza LibroRemuneracionesUpload
    desde cualquier lugar (Admin, API, shell, etc.)
    """
    if instance.pk:  # Solo si es actualización (no creación)
        try:
            old_instance = LibroRemuneracionesUpload.objects.get(pk=instance.pk)
            
            # Si hay archivo anterior y es diferente al nuevo
            if (old_instance.archivo and 
                instance.archivo and 
                old_instance.archivo.name != instance.archivo.name):
                
                if os.path.isfile(old_instance.archivo.path):
                    archivo_path = old_instance.archivo.path
                    os.remove(archivo_path)
                    logger.info(f"[SIGNAL] Archivo anterior eliminado: {archivo_path}")
                    
        except LibroRemuneracionesUpload.DoesNotExist:
            # El registro no existe (creación), no hacer nada
            pass
        except Exception as e:
            logger.error(f"[SIGNAL] Error eliminando archivo anterior: {e}")


@receiver(pre_delete, sender=MovimientosMesUpload)
def eliminar_archivo_movimientos_mes(sender, instance, **kwargs):
    """
    Eliminar archivo físico cuando se borra MovimientosMesUpload
    """
    if instance.archivo:
        try:
            if os.path.isfile(instance.archivo.path):
                archivo_path = instance.archivo.path
                os.remove(archivo_path)
                logger.info(f"[SIGNAL] Archivo de movimientos eliminado: {archivo_path}")
        except Exception as e:
            logger.error(f"[SIGNAL] Error eliminando archivo de movimientos: {e}")


@receiver(pre_save, sender=MovimientosMesUpload)
def eliminar_archivo_anterior_movimientos_mes(sender, instance, **kwargs):
    """
    Eliminar archivo anterior cuando se actualiza MovimientosMesUpload
    """
    if instance.pk:  # Solo si es actualización
        try:
            old_instance = MovimientosMesUpload.objects.get(pk=instance.pk)
            
            if (old_instance.archivo and 
                instance.archivo and 
                old_instance.archivo.name != instance.archivo.name):
                
                if os.path.isfile(old_instance.archivo.path):
                    archivo_path = old_instance.archivo.path
                    os.remove(archivo_path)
                    logger.info(f"[SIGNAL] Archivo anterior de movimientos eliminado: {archivo_path}")
                    
        except MovimientosMesUpload.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"[SIGNAL] Error eliminando archivo anterior de movimientos: {e}")
