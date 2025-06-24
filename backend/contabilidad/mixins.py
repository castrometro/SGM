from .utils.activity_logger import registrar_actividad_tarjeta


class ActivityLogMixin:
    """Mixin para registrar acciones de creación, actualización y eliminación."""

    def _log_action(
        self,
        *,
        cliente_id,
        periodo,
        tarjeta,
        accion,
        descripcion,
        detalles=None,
        resultado="exito",
    ):
        """Llama a ``registrar_actividad_tarjeta`` usando la request actual."""
        return registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo,
            tarjeta=tarjeta,
            accion=accion,
            descripcion=descripcion,
            usuario=getattr(self.request, "user", None),
            detalles=detalles,
            resultado=resultado,
            ip_address=self.request.META.get("REMOTE_ADDR") if hasattr(self, "request") else None,
        )

    def log_create(self, **kwargs):
        kwargs.setdefault("accion", "manual_create")
        return self._log_action(**kwargs)

    def log_update(self, **kwargs):
        kwargs.setdefault("accion", "manual_edit")
        return self._log_action(**kwargs)

    def log_delete(self, **kwargs):
        kwargs.setdefault("accion", "manual_delete")
        return self._log_action(**kwargs)
