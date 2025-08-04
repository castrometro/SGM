# task_manager/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskExecutionViewSet, TaskNotificationViewSet, TaskTemplateViewSet

router = DefaultRouter()
router.register(r'tasks', TaskExecutionViewSet, basename='tasks')
router.register(r'notifications', TaskNotificationViewSet, basename='notifications')
router.register(r'templates', TaskTemplateViewSet, basename='templates')

urlpatterns = [
    path('api/task-manager/', include(router.urls)),
]
