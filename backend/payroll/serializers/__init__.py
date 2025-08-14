# ============================================================================
#                           PAYROLL SERIALIZERS PACKAGE
# ============================================================================
# Estructura modular de serializers para APIs REST del sistema de nómina
# Organizado por funcionalidad para facilitar mantenimiento y escalabilidad

from .cierre_serializers import *
from .empleados_serializers import *
from .items_serializers import *
from .finiquitos_serializers import *
from .ingresos_serializers import *
from .ausentismos_serializers import *
from .incidencias_serializers import *
from .logs_serializers import *

# Serializers de utilidades y APIs generales
from .dashboard_serializers import *
from .upload_serializers import *
from .validation_serializers import *

__all__ = [
    # Cierre Payroll Serializers
    'CierrePayrollSerializer', 'CierrePayrollDetailSerializer', 'CierrePayrollCreateSerializer',
    'CierrePayrollListSerializer', 'CierrePayrollStatsSerializer',
    
    # Empleados Serializers  
    'EmpleadosCierreSerializer', 'EmpleadosCierreDetailSerializer', 'EmpleadosCierreCreateSerializer',
    'EmpleadosCierreListSerializer', 'EmpleadosCierreStatsSerializer',
    
    # Items Serializers
    'ItemCierreSerializer', 'ItemEmpleadoSerializer', 'ItemCierreCreateSerializer',
    'ItemEmpleadoDetailSerializer', 'ItemCierreStatsSerializer',
    
    # Finiquitos Serializers
    'FiniquitosCierreSerializer', 'FiniquitosCierreDetailSerializer',
    
    # Ingresos Serializers
    'IngresosCierreSerializer', 'IngresosCierreCreateSerializer',
    
    # Ausentismos Serializers
    'AusentismosCierreSerializer', 'AusentismosCierreCreateSerializer',
    
    # Incidencias Serializers
    'IncidenciasCierreSerializer', 'IncidenciasCierreDetailSerializer',
    
    # Logs Serializers
    'LogsActividadSerializer', 'LogsActividadDetailSerializer',
    
    # Dashboard Serializers
    'DashboardStatsSerializer', 'ResumenCierreSerializer', 'EstadisticasSerializer',
    
    # Upload Serializers
    'UploadExcelSerializer', 'UploadPDFSerializer', 'ImportarEmpleadosSerializer',
    
    # Validation Serializers
    'ValidacionDatosSerializer', 'ComparacionArchivosSerializer',
]
