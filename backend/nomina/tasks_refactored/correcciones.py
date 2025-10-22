"""
🧹 Corrección de Libro de Remuneraciones - Logging refactorizado
===============================================================

Funciones auxiliares para registrar el inicio y fin del flujo de corrección
del Libro de Remuneraciones usando DUAL LOGGING:

- Log de Usuario (TarjetaActivityLogNomina) visible en la UI
- Log Técnico (ActivityEvent) para auditoría

Se integran desde la vista sincronizada `corregir_libro_view` para mantener
la semántica actual (borrado inmediato y luego subida del nuevo archivo).

Nota: No se mueven los borrados a Celery para evitar condiciones de carrera
con la subida inmediata realizada por el frontend.
"""

import logging
from django.utils import timezone


logger = logging.getLogger(__name__)


def _get_user(user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        return User.objects.get(id=user_id) if user_id else None
    except Exception:
        return None


def log_correccion_start(
    cierre_id: int,
    usuario_id: int | None,
    archivo_nombre: str,
    version_anterior: int,
    version_nueva: int,
    ip_address: str | None = None,
):
    """Registrar INICIO de la corrección (validación OK + preparación de cleanup)."""
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina

    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = _get_user(usuario_id)

        detalles = {
            "cierre_id": cierre_id,
            "cliente": getattr(cierre.cliente, "nombre", None),
            "periodo": str(getattr(cierre, "periodo", "")),
            "archivo_nombre": archivo_nombre,
            "version_anterior": version_anterior,
            "version_nueva": version_nueva,
            "timestamp": timezone.now().isoformat(),
        }

        # 1) Log de usuario (UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="libro_remuneraciones",
            accion="process_start",  # acción válida en ACCION_CHOICES
            descripcion=f"Corrección iniciada v{version_anterior} → v{version_nueva} (validación OK)",
            usuario=usuario,
            detalles=detalles,
            resultado="exito",
            ip_address=ip_address,
        )

        # 2) Log técnico (ActivityEvent)
        ActivityEvent.objects.create(
            event_type="process",
            action=f"correccion_start_cierre_{cierre_id}",
            resource_type="libro_remuneraciones",
            resource_id=str(cierre_id),
            user=usuario,
            cliente=cierre.cliente,
            cierre=cierre,
            details=detalles,
        )

        logger.info(
            "[Correcciones] Inicio registrado: cierre=%s archivo=%s v%d→v%d",
            cierre_id,
            archivo_nombre,
            version_anterior,
            version_nueva,
        )
    except Exception as e:
        logger.error("Error en log_correccion_start: %s", e)


def log_correccion_cleanup_complete(
    cierre_id: int,
    usuario_id: int | None,
    eliminados: int,
    eliminados_archivo: int,
    upload_log_id: int | None,
    archivo_nombre: str,
    version_nueva: int,
    ip_address: str | None = None,
):
    """Registrar FIN de la fase de cleanup (previos eliminados)."""
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina

    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = _get_user(usuario_id)

        detalles = {
            "cierre_id": cierre_id,
            "archivo_correccion_nombre": archivo_nombre,
            "libros_previos_eliminados": eliminados,
            "archivos_fisicos_eliminados": eliminados_archivo,
            "upload_log_id": upload_log_id,
            "version_datos": version_nueva,
            "timestamp": timezone.now().isoformat(),
        }

        # 1) Log de usuario (UI) - usamos una acción existente del CHOICES
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="libro_remuneraciones",
            accion="delete_all",
            descripcion=f"Corrección v{version_nueva}: uploads previos eliminados (validación OK)",
            usuario=usuario,
            detalles=detalles,
            resultado="exito",
            ip_address=ip_address,
        )

        # 2) Log técnico (ActivityEvent)
        ActivityEvent.objects.create(
            event_type="process",
            action=f"correccion_cleanup_complete_cierre_{cierre_id}",
            resource_type="libro_remuneraciones",
            resource_id=str(cierre_id),
            user=usuario,
            cliente=cierre.cliente,
            cierre=cierre,
            details=detalles,
        )

        logger.info(
            "[Correcciones] Cleanup registrado: cierre=%s eliminados=%d archivos=%d upload_log=%s",
            cierre_id,
            eliminados,
            eliminados_archivo,
            str(upload_log_id),
        )
    except Exception as e:
        logger.error("Error en log_correccion_cleanup_complete: %s", e)
