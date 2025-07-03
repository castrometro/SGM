"""
URLs para finalización de cierres contables.
"""

from django.urls import path
from .views import finalizacion

urlpatterns = [
    # Finalización de cierres
    path('cierres/<int:cierre_id>/finalizar/', 
         finalizacion.finalizar_cierre, 
         name='finalizar_cierre'),
    
    path('cierres/<int:cierre_id>/estado-finalizacion/', 
         finalizacion.estado_finalizacion, 
         name='estado_finalizacion'),
    
    path('cierres/<int:cierre_id>/actualizar-estado/', 
         finalizacion.actualizar_estado_cierre, 
         name='actualizar_estado_cierre'),
    
    path('cierres-finalizables/', 
         finalizacion.cierres_finalizables, 
         name='cierres_finalizables'),
    
    # Monitoreo de tareas
    path('tareas/<str:task_id>/progreso/', 
         finalizacion.progreso_tarea, 
         name='progreso_tarea'),
]
