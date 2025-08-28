from django.apps import AppConfig


class ContabilidadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contabilidad'
    
    def ready(self):
        """
        Importar tasks cuando la app esté lista para asegurar 
        que Celery las registre correctamente.
        """
        try:
            from . import tasks
            from . import tasks_de_tipo_doc
            from . import tasks_cuentas_bulk
            from . import tasks_nombres_ingles
            from . import tasks_libro_mayor
            from . import tasks_finalizacion  # ✅ Agregar tasks de finalización
        except ImportError:
            pass
