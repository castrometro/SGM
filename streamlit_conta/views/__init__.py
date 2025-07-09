"""Views for the accounting dashboard."""

from . import dashboard_general
from . import movimientos  
from . import estado_situacion_financiera

__all__ = [
    'dashboard_general',
    'movimientos', 
    'estado_situacion_financiera'
]
