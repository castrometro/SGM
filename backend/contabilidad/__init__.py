# Configuración de la app de contabilidad
default_app_config = 'contabilidad.apps.ContabilidadConfig'

# Asegurar que las tareas de Celery se registren
try:
    from . import tasks_finalizacion
except ImportError:
    pass