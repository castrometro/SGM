# backend/nomina/models_logging_stub.py
"""
STUB de transición para models_logging V1
Este archivo reemplaza temporalmente las funciones del sistema V1 
para evitar errores mientras migramos al V2.
"""

import logging
from django.db import models

logger = logging.getLogger(__name__)

# Stub models que no hacen nada
class UploadLogNomina:
    """STUB: Modelo para logging de uploads"""
    
    @classmethod
    def objects(cls):
        class StubManager:
            def create(cls, **kwargs):
                logger.debug("STUB: UploadLogNomina.create()")
                return None
            def get(cls, **kwargs):
                logger.debug("STUB: UploadLogNomina.get()")
                return None
            def filter(cls, **kwargs):
                logger.debug("STUB: UploadLogNomina.filter()")
                return []
        return StubManager()


class TarjetaActivityLogNomina:
    """STUB: Modelo para logging de actividades"""
    
    @classmethod  
    def objects(cls):
        class StubManager:
            def create(cls, **kwargs):
                logger.debug("STUB: TarjetaActivityLogNomina.create()")
                return None
            def get(cls, **kwargs):
                logger.debug("STUB: TarjetaActivityLogNomina.get()")
                return None
            def filter(cls, **kwargs):
                logger.debug("STUB: TarjetaActivityLogNomina.filter()")
                return []
        return StubManager()


# Stub functions
def registrar_actividad_tarjeta_nomina(*args, **kwargs):
    """STUB: Función de registro de actividad"""
    logger.debug("STUB: registrar_actividad_tarjeta_nomina()")
    return None


def obtener_logs_actividad(*args, **kwargs):
    """STUB: Función para obtener logs"""
    logger.debug("STUB: obtener_logs_actividad()")
    return []


def limpiar_logs_antiguos(*args, **kwargs):
    """STUB: Función para limpiar logs"""
    logger.debug("STUB: limpiar_logs_antiguos()")
    return None