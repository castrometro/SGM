import logging
from celery import shared_task
from contabilidad.utils.processors.base_processor import BaseProcessor
from contabilidad.utils.processors.nombres_ingles_processor import NombresInglesProcessor
from contabilidad.utils.processors.tipo_documento_processor import TipoDocumentoProcessor
from contabilidad.utils.processors.clasificacion_processor import ClasificacionProcessor
from contabilidad.utils.processors.libro_mayor_processor import LibroMayorProcessor
from contabilidad.utils.validators.excel_validator import limpiar_archivos_temporales

logger = logging.getLogger(__name__)


@shared_task
def tarea_de_prueba(nombre):
    logger.info("👋 ¡Hola %s desde Celery!", nombre)
    return f"Completado por {nombre}"


@shared_task
def parsear_tipo_documento(cliente_id, ruta_relativa):
    ok, msg = TipoDocumentoProcessor.parse_excel(cliente_id, ruta_relativa)
    logger.info(msg)
    return msg


@shared_task
def procesar_nombres_ingles(cliente_id, path_archivo):
    return NombresInglesProcessor.procesar_archivo(cliente_id, path_archivo)


@shared_task
def procesar_mapeo_clasificaciones(upload_log_id):
    ClasificacionProcessor.map_clasificaciones(upload_log_id)


@shared_task
def procesar_nombres_ingles_upload(upload_id):
    NombresInglesProcessor.procesar_upload(upload_id)


@shared_task
def procesar_nombres_ingles_con_upload_log(upload_log_id):
    return NombresInglesProcessor.procesar_con_upload_log(upload_log_id)


@shared_task
def procesar_tipo_documento_con_upload_log(upload_log_id):
    return TipoDocumentoProcessor.procesar_upload_log(upload_log_id)


@shared_task
def procesar_clasificacion_con_upload_log(upload_log_id):
    return ClasificacionProcessor.process_upload_log(upload_log_id)


@shared_task
def crear_sets_y_opciones_clasificacion(upload_log_id):
    return ClasificacionProcessor.create_sets_options(upload_log_id)


@shared_task
def procesar_libro_mayor(upload_log_id):
    return LibroMayorProcessor.procesar(upload_log_id)


@shared_task
def limpiar_archivos_temporales_antiguos_task():
    eliminados = limpiar_archivos_temporales()
    logger.info("🧹 Limpieza automática: %s archivos temporales eliminados", eliminados)
    return f"Eliminados {eliminados} archivos temporales"
