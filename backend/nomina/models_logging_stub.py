# backend/nomina/models_logging_stub.py
"""
STUB de transición para models_logging V1
Este archivo reemplaza temporalmente las funciones del sistema V1 
para evitar errores mientras migramos al V2.
"""

import logging

logger = logging.getLogger(__name__)


class StubInstance:
    """Instancia stub que simula un objeto de modelo"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = None  # Simular que no tiene ID
    
    def save(self):
        logger.debug("STUB: save() no-op")
        pass


class StubManager:
    """Manager stub que simula Django ORM"""
    
    def create(self, **kwargs):
        logger.debug(f"STUB: UploadLogNomina/TarjetaActivityLogNomina.create(**kwargs)")
        return StubInstance(**kwargs)
    
    def get(self, **kwargs):
        logger.debug("STUB: get() - returning None")
        return None
    
    def filter(self, **kwargs):
        logger.debug("STUB: filter() - returning empty list")
        return []


# Stub models que no hacen nada
class UploadLogNomina:
    """STUB: Modelo para logging de uploads"""
    objects = StubManager()


class TarjetaActivityLogNomina:
    """STUB: Modelo para logging de actividades"""
    objects = StubManager()


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