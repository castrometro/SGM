from .activity_logger import registrar_actividad_tarjeta
from ..models import CierreContabilidad, UploadLog


class UploadLogMixin:
    """Helper para crear registros UploadLog a partir de un archivo."""

    tipo_upload = None

    def crear_upload_log(self, cliente, archivo):
        return UploadLog.objects.create(
            cliente=cliente,
            tipo_upload=self.tipo_upload,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
        )


class CierreLookupMixin:
    """Mixin para obtener y cachear un cierre contable"""

    cierre_cache = None

    def get_cierre(self, cierre_id):
        if self.cierre_cache and self.cierre_cache.id == cierre_id:
            return self.cierre_cache
        self.cierre_cache = CierreContabilidad.objects.get(id=cierre_id)
        return self.cierre_cache


class ActivityLoggerMixin:
    def log_activity(self, **kwargs):
        registrar_actividad_tarjeta(**kwargs)
