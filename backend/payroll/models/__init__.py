# Importar todos los modelos para que Django los reconozca
from .models_cierre import CierrePayroll
from .models_fase_1 import ArchivoSubido

# Hacer que estén disponibles cuando se importe el paquete models
__all__ = [
    'CierrePayroll',
    'ArchivoSubido'
]
