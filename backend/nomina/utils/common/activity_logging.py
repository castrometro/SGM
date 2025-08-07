# nomina/utils/activity_logging.py

from ..models_logging import registrar_actividad_tarjeta_nomina
from .clientes import get_client_ip
import logging

logger = logging.getLogger(__name__)


class NominaActivityLogger:
    """
    Helper class para logging de actividades en tarjetas de nómina
    Proporciona métodos convenientes para registrar actividades comunes
    """
    
    def __init__(self, cierre_id, tarjeta, usuario=None, request=None):
        self.cierre_id = cierre_id
        self.tarjeta = tarjeta
        self.usuario = usuario
        self.ip_address = get_client_ip(request) if request else None
    
    def _log_activity(self, accion, descripcion, detalles=None, resultado="exito", upload_log=None):
        """Método interno para registrar actividad"""
        try:
            return registrar_actividad_tarjeta_nomina(
                cierre_id=self.cierre_id,
                tarjeta=self.tarjeta,
                accion=accion,
                descripcion=descripcion,
                usuario=self.usuario,
                detalles=detalles or {},
                resultado=resultado,
                ip_address=self.ip_address,
                upload_log=upload_log
            )
        except Exception as e:
            logger.error(f"Error registrando actividad {accion}: {e}")
            return None
    
    # === ACTIVIDADES DE ARCHIVO ===
    
    def log_file_select(self, archivo_nombre, archivo_size=None):
        """Registra selección de archivo"""
        return self._log_activity(
            "file_select",
            f"Archivo seleccionado: {archivo_nombre}",
            {
                "archivo_nombre": archivo_nombre,
                "archivo_size": archivo_size
            }
        )
    
    def log_file_validate(self, archivo_nombre, resultado_validacion, errores=None):
        """Registra validación de archivo"""
        return self._log_activity(
            "file_validate",
            f"Validación de archivo: {'exitosa' if not errores else 'fallida'}",
            {
                "archivo_nombre": archivo_nombre,
                "validacion_exitosa": not errores,
                "errores": errores or []
            },
            resultado="exito" if not errores else "error"
        )
    
    def log_download_template(self, template_type):
        """Registra descarga de plantilla"""
        return self._log_activity(
            "download_template",
            f"Plantilla descargada: {template_type}",
            {"template_type": template_type}
        )
    
    # === ACTIVIDADES DE MODAL ===
    
    def log_modal_open(self, modal_type, context=None):
        """Registra apertura de modal"""
        return self._log_activity(
            "modal_open",
            f"Modal abierto: {modal_type}",
            {
                "modal_type": modal_type,
                "context": context or {}
            }
        )
    
    def log_modal_close(self, modal_type, action_taken=None):
        """Registra cierre de modal"""
        return self._log_activity(
            "modal_close",
            f"Modal cerrado: {modal_type}",
            {
                "modal_type": modal_type,
                "action_taken": action_taken
            }
        )
    
    # === ACTIVIDADES DE CLASIFICACIÓN ===
    
    def log_view_classification(self, headers_count=None, classified_count=None):
        """Registra visualización de clasificación"""
        return self._log_activity(
            "view_classification",
            "Visualización de clasificación de headers",
            {
                "headers_count": headers_count,
                "classified_count": classified_count,
                "unclassified_count": (headers_count - classified_count) if headers_count and classified_count else None
            }
        )
    
    def log_concept_map(self, header_name, concepto_id, concepto_nombre):
        """Registra mapeo de concepto"""
        return self._log_activity(
            "concept_map",
            f"Header '{header_name}' mapeado a concepto '{concepto_nombre}'",
            {
                "header_name": header_name,
                "concepto_id": concepto_id,
                "concepto_nombre": concepto_nombre
            }
        )
    
    def log_concept_unmap(self, header_name):
        """Registra desmapeo de concepto"""
        return self._log_activity(
            "concept_unmap",
            f"Header '{header_name}' desmapeado",
            {"header_name": header_name}
        )
    
    def log_save_classification(self, saved_count, total_count):
        """Registra guardado de clasificación"""
        return self._log_activity(
            "save_classification",
            f"Clasificación guardada: {saved_count} de {total_count} headers",
            {
                "saved_count": saved_count,
                "total_count": total_count,
                "completion_percentage": (saved_count / total_count * 100) if total_count > 0 else 0
            }
        )
    
    # === ACTIVIDADES DE ESTADO ===
    
    def log_state_change(self, old_state, new_state, trigger=None):
        """Registra cambio de estado"""
        return self._log_activity(
            "state_change",
            f"Estado cambió de '{old_state}' a '{new_state}'",
            {
                "old_state": old_state,
                "new_state": new_state,
                "trigger": trigger
            }
        )
    
    def log_polling_start(self, interval_seconds):
        """Registra inicio de polling"""
        return self._log_activity(
            "polling_start",
            f"Polling iniciado con intervalo de {interval_seconds} segundos",
            {"interval_seconds": interval_seconds}
        )
    
    def log_polling_stop(self, reason=None):
        """Registra detención de polling"""
        return self._log_activity(
            "polling_stop",
            f"Polling detenido{': ' + reason if reason else ''}",
            {"reason": reason}
        )
    
    # === ACTIVIDADES DE SESIÓN ===
    
    def log_session_start(self):
        """Registra inicio de sesión de trabajo"""
        return self._log_activity(
            "session_start",
            f"Sesión de trabajo iniciada en tarjeta {self.tarjeta}",
            {"tarjeta": self.tarjeta}
        )
    
    def log_session_end(self, duration_seconds=None):
        """Registra fin de sesión de trabajo"""
        return self._log_activity(
            "session_end",
            f"Sesión de trabajo finalizada en tarjeta {self.tarjeta}",
            {
                "tarjeta": self.tarjeta,
                "duration_seconds": duration_seconds
            }
        )
    
    # === ACTIVIDADES DE PROGRESO ===
    
    def log_progress_update(self, progress_percentage, step_description):
        """Registra actualización de progreso"""
        return self._log_activity(
            "progress_update",
            f"Progreso actualizado: {progress_percentage}% - {step_description}",
            {
                "progress_percentage": progress_percentage,
                "step_description": step_description
            }
        )
    
    def log_error_recovery(self, error_type, recovery_action):
        """Registra recuperación de error"""
        return self._log_activity(
            "error_recovery",
            f"Recuperación de error {error_type}: {recovery_action}",
            {
                "error_type": error_type,
                "recovery_action": recovery_action
            }
        )


# === FUNCIONES DE CONVENIENCIA ===

def create_activity_logger(cierre_id, tarjeta, usuario=None, request=None):
    """Factory function para crear un ActivityLogger"""
    return NominaActivityLogger(cierre_id, tarjeta, usuario, request)


def log_quick_activity(cierre_id, tarjeta, accion, descripcion, usuario=None, request=None, **kwargs):
    """Función rápida para registrar una actividad simple"""
    logger_instance = create_activity_logger(cierre_id, tarjeta, usuario, request)
    return logger_instance._log_activity(accion, descripcion, kwargs.get('detalles'), kwargs.get('resultado', 'exito'))
