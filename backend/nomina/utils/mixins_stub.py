# backend/nomina/utils/mixins_stub.py
"""
STUB de transición para mixins V1 de logging
Este archivo reemplaza temporalmente las funciones del sistema V1 
para evitar errores mientras migramos al V2.
"""

import logging

logger = logging.getLogger(__name__)

class UploadLogNominaMixin:
    """
    STUB: Mixin para manejar el logging de uploads en nómina
    Todas las operaciones son no-op para evitar errores durante la migración.
    """
    
    def __init__(self):
        logger.warning("⚠️ Usando UploadLogNominaMixin stub - Migrar a Activity V2")
        self.tipo_upload = None
        self.cliente = None
        self.usuario = None
        self.ip_usuario = None
    
    def crear_upload_log(self, cliente, archivo, tipo_upload=None):
        """STUB: No crea ningún log"""
        logger.debug(f"STUB: crear_upload_log - archivo: {archivo.name}")
        return None
    
    def actualizar_upload_log(self, upload_log_id, **kwargs):
        """STUB: No actualiza ningún log"""
        logger.debug(f"STUB: actualizar_upload_log - id: {upload_log_id}")
        return None
        
    def finalizar_upload_log(self, upload_log_id, estado='completado', **kwargs):
        """STUB: No finaliza ningún log"""
        logger.debug(f"STUB: finalizar_upload_log - id: {upload_log_id}")
        return None
        
    def _calcular_hash_archivo(self, archivo):
        """STUB: Retorna hash vacío"""
        return "stub_hash"
        
    def validar_archivo(self, archivo):
        """STUB: Siempre válido"""
        return True, []


class ValidacionArchivoCRUDMixin:
    """
    STUB: Mixin para validaciones CRUD
    """
    
    def __init__(self):
        logger.warning("⚠️ Usando ValidacionArchivoCRUDMixin stub - Migrar a Activity V2")
    
    def validar_estructura_excel(self, archivo):
        """STUB: Siempre válido"""
        return True, []
        
    def validar_datos_excel(self, df):
        """STUB: Siempre válido"""
        return True, []