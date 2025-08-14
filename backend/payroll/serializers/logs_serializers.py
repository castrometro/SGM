# ============================================================================
#                           LOGS ACTIVIDAD SERIALIZERS
# ============================================================================
# Serializers para la gestión de logs de actividad

try:
    from rest_framework import serializers
    from django.contrib.auth import get_user_model
    from ..models import Logs_Actividad, CierrePayroll
    
    User = get_user_model()
    
    
    class LogsActividadListSerializer(serializers.ModelSerializer):
        """
        Serializer para lista de logs (vista resumida)
        """
        usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
        cierre_info = serializers.SerializerMethodField()
        accion_display = serializers.CharField(source='get_accion_display', read_only=True)
        resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
        duracion_display = serializers.SerializerMethodField()
        timestamp_formatted = serializers.SerializerMethodField()
        
        class Meta:
            model = Logs_Actividad
            fields = [
                'id', 'timestamp', 'timestamp_formatted', 'usuario_nombre',
                'cierre_info', 'accion', 'accion_display', 'resultado',
                'resultado_display', 'descripcion', 'duracion_display'
            ]
        
        def get_cierre_info(self, obj):
            if obj.cierre_payroll:
                return {
                    'id': obj.cierre_payroll.id,
                    'cliente': obj.cierre_payroll.cliente.nombre,
                    'periodo': obj.cierre_payroll.periodo,
                }
            return None
        
        def get_duracion_display(self, obj):
            if hasattr(obj, 'get_duracion_display'):
                return obj.get_duracion_display()
            return None
        
        def get_timestamp_formatted(self, obj):
            return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    
    class LogsActividadDetailSerializer(serializers.ModelSerializer):
        """
        Serializer detallado para log específico
        """
        usuario_info = serializers.SerializerMethodField()
        cierre_info = serializers.SerializerMethodField()
        accion_display = serializers.CharField(source='get_accion_display', read_only=True)
        resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
        duracion_info = serializers.SerializerMethodField()
        color_resultado = serializers.SerializerMethodField()
        timestamp_formatted = serializers.SerializerMethodField()
        
        class Meta:
            model = Logs_Actividad
            fields = [
                'id', 'timestamp', 'timestamp_formatted', 'usuario_info',
                'cierre_info', 'accion', 'accion_display', 'resultado',
                'resultado_display', 'descripcion', 'detalles',
                'duracion_info', 'color_resultado'
            ]
        
        def get_usuario_info(self, obj):
            return {
                'id': obj.usuario.id,
                'username': obj.usuario.username,
                'nombre_completo': f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or obj.usuario.username,
                'email': obj.usuario.email,
            }
        
        def get_cierre_info(self, obj):
            if obj.cierre_payroll:
                return {
                    'id': obj.cierre_payroll.id,
                    'cliente': {
                        'id': obj.cierre_payroll.cliente.id,
                        'nombre': obj.cierre_payroll.cliente.nombre,
                        'rut': obj.cierre_payroll.cliente.rut,
                    },
                    'periodo': obj.cierre_payroll.periodo,
                    'estado': obj.cierre_payroll.estado,
                    'estado_display': obj.cierre_payroll.get_estado_display(),
                }
            return None
        
        def get_duracion_info(self, obj):
            if hasattr(obj, 'get_duracion_display'):
                return {
                    'display': obj.get_duracion_display(),
                    'seconds': None,  # Aquí se podría calcular si tuviera campo de duración
                }
            return None
        
        def get_color_resultado(self, obj):
            if hasattr(obj, 'get_color_resultado'):
                return obj.get_color_resultado()
            
            # Colores por defecto según resultado
            colors = {
                'exitoso': '#28a745',
                'error': '#dc3545',
                'advertencia': '#ffc107',
                'informacion': '#17a2b8',
            }
            return colors.get(obj.resultado, '#6c757d')
        
        def get_timestamp_formatted(self, obj):
            return {
                'datetime': obj.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'date': obj.timestamp.strftime('%Y-%m-%d'),
                'time': obj.timestamp.strftime('%H:%M:%S'),
                'relative': self.get_relative_time(obj.timestamp),
            }
        
        def get_relative_time(self, timestamp):
            from django.utils import timezone
            now = timezone.now()
            diff = now - timestamp
            
            if diff.days > 0:
                return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"hace {hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "hace unos segundos"
    
    
    class LogsActividadCreateSerializer(serializers.ModelSerializer):
        """
        Serializer para crear logs (uso interno principalmente)
        """
        class Meta:
            model = Logs_Actividad
            fields = [
                'cierre_payroll', 'accion', 'descripcion', 'resultado', 'detalles'
            ]
        
        def validate_descripcion(self, value):
            if len(value) < 10:
                raise serializers.ValidationError(
                    "La descripción debe tener al menos 10 caracteres"
                )
            return value
        
        def create(self, validated_data):
            # Asignar usuario del request si está disponible
            if 'request' in self.context:
                validated_data['usuario'] = self.context['request'].user
            
            return super().create(validated_data)
    
    
    class LogsActividadStatsSerializer(serializers.ModelSerializer):
        """
        Serializer para estadísticas de logs
        """
        usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
        cierre_cliente = serializers.CharField(source='cierre_payroll.cliente.nombre', read_only=True)
        accion_display = serializers.CharField(source='get_accion_display', read_only=True)
        resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
        timestamp_date = serializers.SerializerMethodField()
        
        class Meta:
            model = Logs_Actividad
            fields = [
                'id', 'timestamp', 'timestamp_date', 'usuario_nombre',
                'cierre_cliente', 'accion', 'accion_display',
                'resultado', 'resultado_display'
            ]
        
        def get_timestamp_date(self, obj):
            return obj.timestamp.strftime('%Y-%m-%d')
    
    
    class LogsTimelineSerializer(serializers.ModelSerializer):
        """
        Serializer optimizado para timeline de logs
        """
        usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
        accion_display = serializers.CharField(source='get_accion_display', read_only=True)
        resultado_display = serializers.CharField(source='get_resultado_display', read_only=True)
        color = serializers.SerializerMethodField()
        descripcion_corta = serializers.SerializerMethodField()
        
        class Meta:
            model = Logs_Actividad
            fields = [
                'id', 'timestamp', 'usuario_nombre', 'accion_display',
                'resultado_display', 'color', 'descripcion_corta'
            ]
        
        def get_color(self, obj):
            colors = {
                'exitoso': '#28a745',
                'error': '#dc3545',
                'advertencia': '#ffc107',
                'informacion': '#17a2b8',
            }
            return colors.get(obj.resultado, '#6c757d')
        
        def get_descripcion_corta(self, obj):
            if len(obj.descripcion) > 50:
                return obj.descripcion[:47] + '...'
            return obj.descripcion
    
    
    # Serializer principal (alias para compatibilidad)
    LogsActividadSerializer = LogsActividadDetailSerializer

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class LogsActividadSerializer:
        pass
    
    class LogsActividadDetailSerializer:
        pass
    
    class LogsActividadListSerializer:
        pass
    
    class LogsActividadCreateSerializer:
        pass
    
    class LogsActividadStatsSerializer:
        pass
    
    class LogsTimelineSerializer:
        pass
