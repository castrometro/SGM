# task_manager/serializers.py
from rest_framework import serializers
from .models import TaskExecution, TaskNotification, TaskTemplate

class TaskNotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones de tareas"""
    
    class Meta:
        model = TaskNotification
        fields = ['id', 'type', 'title', 'message', 'details', 'created_at', 'read']
        read_only_fields = ['id', 'created_at']


class TaskExecutionSerializer(serializers.ModelSerializer):
    """Serializer completo para ejecuciones de tareas"""
    
    notifications = TaskNotificationSerializer(many=True, read_only=True)
    duration_seconds = serializers.ReadOnlyField()
    is_finished = serializers.ReadOnlyField()
    is_running = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskExecution
        fields = [
            'id', 'task_id', 'task_name', 'task_module', 'description',
            'status', 'progress_percentage', 'current_step', 'total_steps',
            'created_at', 'started_at', 'completed_at', 'updated_at',
            'user', 'user_name', 'context_data', 'result_data',
            'error_message', 'error_traceback', 'timeout_seconds',
            'retry_count', 'max_retries', 'worker_name', 'queue_name',
            'duration_seconds', 'is_finished', 'is_running', 'is_successful',
            'notifications'
        ]
        read_only_fields = [
            'id', 'created_at', 'started_at', 'completed_at', 'updated_at',
            'duration_seconds', 'is_finished', 'is_running', 'is_successful'
        ]


class TaskExecutionSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para listas de tareas"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    duration_seconds = serializers.ReadOnlyField()
    is_finished = serializers.ReadOnlyField()
    unread_notifications = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskExecution
        fields = [
            'id', 'task_id', 'task_name', 'task_module', 'description',
            'status', 'progress_percentage', 'current_step',
            'created_at', 'user_name', 'duration_seconds', 'is_finished',
            'unread_notifications'
        ]
    
    def get_unread_notifications(self, obj):
        return obj.notifications.filter(read=False).count()


class TaskTemplateSerializer(serializers.ModelSerializer):
    """Serializer para templates de tareas"""
    
    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'name', 'module', 'description', 'default_timeout',
            'default_max_retries', 'estimated_duration_seconds',
            'typical_steps', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskStatusResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de estado de tareas (combinando local + Flower)"""
    
    task_id = serializers.CharField()
    exists_locally = serializers.BooleanField()
    exists_in_flower = serializers.BooleanField()
    
    # Datos locales
    id = serializers.UUIDField(required=False)
    task_name = serializers.CharField(required=False)
    module = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)
    progress_percentage = serializers.IntegerField(required=False)
    current_step = serializers.CharField(required=False, allow_blank=True)
    total_steps = serializers.IntegerField(required=False)
    user = serializers.CharField(required=False, allow_null=True)
    context_data = serializers.DictField(required=False)
    created_at = serializers.CharField(required=False)
    started_at = serializers.CharField(required=False, allow_null=True)
    completed_at = serializers.CharField(required=False, allow_null=True)
    duration_seconds = serializers.FloatField(required=False)
    is_finished = serializers.BooleanField(required=False)
    is_running = serializers.BooleanField(required=False)
    is_successful = serializers.BooleanField(required=False)
    result_data = serializers.DictField(required=False)
    error_message = serializers.CharField(required=False, allow_blank=True)
    worker_name = serializers.CharField(required=False, allow_blank=True)
    queue_name = serializers.CharField(required=False, allow_blank=True)
    
    # Datos de Flower
    flower_state = serializers.CharField(required=False)
    flower_result = serializers.CharField(required=False, allow_null=True)
    flower_traceback = serializers.CharField(required=False, allow_null=True)
    flower_worker = serializers.CharField(required=False, allow_null=True)
    flower_timestamp = serializers.FloatField(required=False, allow_null=True)
    flower_runtime = serializers.FloatField(required=False, allow_null=True)
    
    # Estado unificado
    unified_status = serializers.CharField()
    user_friendly_message = serializers.CharField()


class WorkerStatusSerializer(serializers.Serializer):
    """Serializer para estado de workers"""
    
    name = serializers.CharField()
    status = serializers.CharField()
    active_tasks = serializers.IntegerField()
    total_tasks = serializers.DictField()
    queues = serializers.ListField(child=serializers.CharField())
    uptime = serializers.IntegerField()


class TaskProgressUpdateSerializer(serializers.Serializer):
    """Serializer para actualizaciones de progreso"""
    
    percentage = serializers.IntegerField(min_value=0, max_value=100, required=False)
    step_description = serializers.CharField(max_length=500, required=False)
    step_number = serializers.IntegerField(min_value=1, required=False)
    total_steps = serializers.IntegerField(min_value=1, required=False)


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevas tareas trackeadas"""
    
    class Meta:
        model = TaskExecution
        fields = [
            'task_id', 'task_name', 'task_module', 'description',
            'context_data', 'timeout_seconds', 'max_retries', 'total_steps'
        ]
    
    def create(self, validated_data):
        # Asignar usuario actual si está autenticado
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        return super().create(validated_data)
