# Data package for SGM Contabilidad Dashboard
"""Helper functions to access sample accounting data."""

from .loader_contabilidad import cargar_datos_redis

__all__ = [
    "cargar_datos_redis",
]
