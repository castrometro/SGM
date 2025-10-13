# backend/nomina/urls_activity_v2.py
"""
URLs para Activity Logging V2 - Sistema Simplificado
"""

from django.urls import path
from .views_activity_v2 import (
    log_single_activity,
    log_batch_activities, 
    get_activity_stats,
    get_activity_log,
    cleanup_old_activities,
)

urlpatterns = [
    # Logging endpoints
    path('activity/', log_single_activity, name='log_activity'),
    path('activity/batch/', log_batch_activities, name='log_batch_activities'),
    
    # Query endpoints
    path('activity/stats/<int:cierre_id>/', get_activity_stats, name='activity_stats'),
    path('activity/log/<int:cierre_id>/', get_activity_log, name='activity_log'),
    
    # Admin endpoints  
    path('activity/cleanup/', cleanup_old_activities, name='cleanup_activities'),
]