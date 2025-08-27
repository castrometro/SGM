# Importar todos los modelos para que Django los reconozca
from .models_cierre import CierrePayroll
from .models_fase_1 import ArchivoSubido
from .models_staging import (
    ListaEmpleados_stg,
    ItemsRemuneraciones_stg,
    ValorItemEmpleado_stg,
    limpiar_staging_por_archivo,
    obtener_resumen_staging,
)

# Hacer que estén disponibles cuando se importe el paquete models
__all__ = [
    'CierrePayroll',
    'ArchivoSubido',
    'EmpleadoStaging',
    'ItemRemuneracionStaging',
    'ValorItemEmpleadoStaging',
    'limpiar_staging_por_archivo',
    'obtener_resumen_staging'
]
