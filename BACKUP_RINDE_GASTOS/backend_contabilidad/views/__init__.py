from .libro_mayor import (
    LibroMayorArchivoViewSet,  # ✅ Nuevo ViewSet
    cargar_libro_mayor,
)
from .tipo_documento import TipoDocumentoViewSet, cargar_tipo_documento
from .nombres_ingles import NombreInglesViewSet, cargar_nombres_ingles, NombresEnInglesView, NombresEnInglesUploadViewSet
from .clasificacion import (
    # ClasificacionCuentaArchivoViewSet,  # OBSOLETO - ELIMINADO EN REDISEÑO
    cargar_clasificacion_bulk,
    ClasificacionViewSet,
    ClasificacionSetViewSet,
    ClasificacionOptionViewSet,
    AccountClassificationViewSet,
    obtener_clasificaciones_persistentes_detalladas,  # CORRECTO - Incluye temporales
    crear_registro_clasificacion_completo,  # Nueva función para registros completos
    actualizar_registro_clasificacion_completo,  # Nueva función para editar registros completos
    eliminar_registro_clasificacion_completo,  # Nueva función para eliminar registros completos
)
from .clasificacion_persistente import (
    # obtener_clasificaciones_persistentes_detalladas,  # MOVIDO A clasificacion.py
    registrar_vista_clasificaciones_persistentes,
    clasificacion_masiva_persistente,
    obtener_estadisticas_clasificaciones_persistentes,
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
    "LibroMayorArchivoViewSet",  # Corregido el nombre
    "cargar_libro_mayor",
    "TipoDocumentoViewSet",
    "cargar_tipo_documento",
    "NombreInglesViewSet",
    "cargar_nombres_ingles",
    "NombresEnInglesView",
    "NombresEnInglesUploadViewSet",
    # "ClasificacionCuentaArchivoViewSet",  # OBSOLETO - ELIMINADO EN REDISEÑO
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
    # Nuevas funciones para clasificaciones persistentes
    "obtener_clasificaciones_persistentes_detalladas",
    "registrar_vista_clasificaciones_persistentes", 
    "clasificacion_masiva_persistente",
    "obtener_estadisticas_clasificaciones_persistentes",
    "crear_registro_clasificacion_completo",
    "actualizar_registro_clasificacion_completo",
    "eliminar_registro_clasificacion_completo",
    # Utilidades
    "test_celery",
    "limpiar_archivos_temporales", 
    "estado_upload_log",
    # Helper functions
    "obtener_periodo_actividad_para_cliente",
    "get_client_ip",
    "verificar_y_marcar_completo",
]
