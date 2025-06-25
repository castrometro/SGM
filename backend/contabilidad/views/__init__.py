from .libro_mayor import (
    LibroMayorUploadViewSet,
    cargar_libro_mayor,
    reprocesar_movimientos_incompletos,
    movimientos_incompletos,
)
from .tipo_documento import TipoDocumentoViewSet, cargar_tipo_documento
from .nombres_ingles import NombreInglesViewSet, cargar_nombres_ingles, NombresEnInglesView, NombresEnInglesUploadViewSet
from .clasificacion import (
    ClasificacionCuentaArchivoViewSet, 
    cargar_clasificacion_bulk,
    ClasificacionViewSet,
    ClasificacionSetViewSet,
    ClasificacionOptionViewSet,
    AccountClassificationViewSet,
)
from .cuentas import (
    CuentaContableViewSet,
    AperturaCuentaViewSet,
    MovimientoContableViewSet,
    CentroCostoViewSet,
    AuxiliarViewSet,
)
from .cierre import CierreContabilidadViewSet
from .actividad import TarjetaActivityLogViewSet
from .incidencias import (
    obtener_incidencias_consolidadas,
    dashboard_incidencias,
    marcar_incidencia_resuelta,
    historial_reprocesamiento,
    resumen_tipos_incidencia,
    estadisticas_globales_incidencias,
    IncidenciaViewSet,
)
from .analisis import AnalisisCuentaCierreViewSet

# Helper functions
from .helpers import (
    obtener_periodo_actividad_para_cliente,
    get_client_ip,
    verificar_y_marcar_completo,
)

# Cliente views
from .cliente import (
    resumen_cliente, 
    detalle_cliente, 
    historial_uploads_cliente, 
    estado_tipo_documento,
    estado_clasificaciones,
    tipos_documento_cliente,
    registrar_vista_tipos_documento,
    # Nuevas funciones agregadas
    eliminar_tipos_documento,
    eliminar_nombres_ingles,
    eliminar_todos_nombres_ingles_upload,
    estado_nombres_ingles,
    nombres_ingles_cliente,
    registrar_vista_nombres_ingles,
    registrar_vista_clasificaciones,
    cuentas_pendientes_set,
)

# Utilidades
from .utilidades import (
    test_celery,
    limpiar_archivos_temporales,
    estado_upload_log,
)

__all__ = [
    "LibroMayorUploadViewSet",
    "cargar_libro_mayor",
    "reprocesar_movimientos_incompletos",
    "movimientos_incompletos",
    "TipoDocumentoViewSet",
    "cargar_tipo_documento",
    "NombreInglesViewSet",
    "cargar_nombres_ingles",
    "NombresEnInglesView",
    "NombresEnInglesUploadViewSet",
    "ClasificacionCuentaArchivoViewSet",
    "cargar_clasificacion_bulk",
    "ClasificacionViewSet",
    "ClasificacionSetViewSet",
    "ClasificacionOptionViewSet",
    "AccountClassificationViewSet",
    "CuentaContableViewSet",
    "AperturaCuentaViewSet",
    "MovimientoContableViewSet",
    "CentroCostoViewSet",
    "AuxiliarViewSet",
    "CierreContabilidadViewSet",
    "TarjetaActivityLogViewSet",
    "AnalisisCuentaCierreViewSet",
    "IncidenciaViewSet",
    # Incidencias consolidadas
    "obtener_incidencias_consolidadas",
    "dashboard_incidencias", 
    "marcar_incidencia_resuelta",
    "historial_reprocesamiento",
    "resumen_tipos_incidencia",
    "estadisticas_globales_incidencias",
    # Cliente views
    "resumen_cliente",
    "detalle_cliente",
    "historial_uploads_cliente",
    "estado_tipo_documento",
    "estado_clasificaciones",
    "tipos_documento_cliente",
    "registrar_vista_tipos_documento",
    # Nuevas funciones
    "eliminar_tipos_documento",
    "eliminar_nombres_ingles", 
    "eliminar_todos_nombres_ingles_upload",
    "estado_nombres_ingles",
    "nombres_ingles_cliente",
    "registrar_vista_nombres_ingles",
    "registrar_vista_clasificaciones",
    "cuentas_pendientes_set",
    # Utilidades
    "test_celery",
    "limpiar_archivos_temporales", 
    "estado_upload_log",
    # Helper functions
    "obtener_periodo_actividad_para_cliente",
    "get_client_ip",
    "verificar_y_marcar_completo",
]
