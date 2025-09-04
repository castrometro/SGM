import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgm_backend.settings')

app = Celery('sgm_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración de colas y routing
app.conf.update(
    # Asegurar que la cola por defecto sea 'default' (no 'celery')
    task_default_queue='default',

    task_routes={
        # Tareas de nómina (cubrir nombres con y sin ".tasks.")
        'nomina.tasks.*': {'queue': 'nomina_queue'},
        'nomina.utils.*': {'queue': 'nomina_queue'},
        'nomina.*': {'queue': 'nomina_queue'},
        
        # Tareas de contabilidad (cubrir nombres con y sin ".tasks.")
        'contabilidad.tasks.*': {'queue': 'contabilidad_queue'},
        'contabilidad.utils.*': {'queue': 'contabilidad_queue'},
        'contabilidad.*': {'queue': 'contabilidad_queue'},
        
        # Tareas generales
        'api.tasks.*': {'queue': 'default'},
        'api.*': {'queue': 'default'},
        # Catch-all para cualquier otra tarea
        '*': {'queue': 'default'},
    },
    
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Configuración de resultados
    result_expires=3600,  # 1 hora
    task_track_started=True,
    task_send_sent_event=True,
    
    # Configuración de workers
    worker_prefetch_multiplier=1,  # Para mejor distribución
    task_acks_late=True,
    worker_disable_rate_limits=False,
)

app.autodiscover_tasks()
