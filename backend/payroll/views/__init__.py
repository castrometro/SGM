# ============================================================================
#                           PAYROLL VIEWS PACKAGE
# ============================================================================
# Estructura modular de views para el sistema de nómina
# Organizado por funcionalidad para facilitar mantenimiento y escalabilidad

from .cierre_views import *
from .empleados_views import *
from .items_views import *
from .finiquitos_views import *
from .ingresos_views import *
from .ausentismos_views import *
from .incidencias_views import *
from .logs_views import *
from .dashboard_views import *
from .reportes_views import *

# Views de utilidades y APIs generales
from .upload_views import *
from .validation_views import *
from .export_views import *

__all__ = [
    # Cierre Payroll Views
    'CierrePayrollListView', 'CierrePayrollDetailView', 'CierrePayrollCreateView',
    'CierrePayrollUpdateView', 'CierrePayrollDeleteView',
    
    # Empleados Views  
    'EmpleadosCierreListView', 'EmpleadosCierreDetailView', 'EmpleadosCierreCreateView',
    
    # Items Views
    'ItemCierreListView', 'ItemEmpleadoListView', 'ItemCierreCreateView',
    
    # Finiquitos Views
    'FiniquitosCierreListView', 'FiniquitosCierreDetailView',
    
    # Ingresos Views
    'IngresosCierreListView', 'IngresosCierreCreateView',
    
    # Ausentismos Views
    'AusentismosCierreListView', 'AusentismosCierreCreateView',
    
    # Incidencias Views
    'IncidenciasCierreListView', 'IncidenciasCierreDetailView',
    
    # Logs Views
    'LogsActividadListView', 'LogsActividadDetailView',
    
    # Dashboard Views
    'PayrollDashboardView', 'ResumenCierreView', 'EstadisticasView',
    
    # Reportes Views
    'ReporteNominaView', 'ReporteIncidenciasView', 'ReporteComparacionView',
    
    # Upload/Import Views
    'UploadExcelView', 'UploadPDFView', 'ImportarEmpleadosView',
    
    # Validation Views
    'ValidarDatosView', 'CompararArchivosView', 'VerificarIntegridadView',
    
    # Export Views
    'ExportarExcelView', 'ExportarPDFView', 'ExportarReporteView',
]
