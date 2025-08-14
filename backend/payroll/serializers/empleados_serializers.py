# ============================================================================
#                           EMPLEADOS CIERRE SERIALIZERS
# ============================================================================
# Serializers para la gestión de empleados en cierres de nómina

try:
    from rest_framework import serializers
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    from ..models import Empleados_Cierre, CierrePayroll, Item_Empleado
    
    
    class EmpleadoSimpleSerializer(serializers.ModelSerializer):
        """Serializer simple para empleado (Usuario)"""
        nombre_completo = serializers.SerializerMethodField()
        
        class Meta:
            model = User
            fields = ['id', 'username', 'first_name', 'last_name', 'nombre_completo', 'email']
        
        def get_nombre_completo(self, obj):
            return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    
    class EmpleadosCierreListSerializer(serializers.ModelSerializer):
        """
        Serializer para lista de empleados en cierre (vista resumida)
        """
        empleado = EmpleadoSimpleSerializer(read_only=True)
        estado_display = serializers.CharField(source='get_estado_procesamiento_display', read_only=True)
        liquido_formateado = serializers.SerializerMethodField()
        total_items = serializers.SerializerMethodField()
        
        class Meta:
            model = Empleados_Cierre
            fields = [
                'id', 'empleado', 'dias_trabajados', 'horas_extras',
                'liquido_pagar', 'liquido_formateado', 'estado_procesamiento',
                'estado_display', 'fecha_procesamiento', 'total_items'
            ]
        
        def get_liquido_formateado(self, obj):
            if obj.liquido_pagar:
                return f"${obj.liquido_pagar:,.0f}"
            return "$0"
        
        def get_total_items(self, obj):
            return obj.item_empleado.count()
    
    
    class EmpleadosCierreDetailSerializer(serializers.ModelSerializer):
        """
        Serializer detallado para empleado en cierre
        """
        empleado = EmpleadoSimpleSerializer(read_only=True)
        estado_display = serializers.CharField(source='get_estado_procesamiento_display', read_only=True)
        
        # Items del empleado
        items_detalle = serializers.SerializerMethodField()
        resumen_items = serializers.SerializerMethodField()
        
        class Meta:
            model = Empleados_Cierre
            fields = [
                'id', 'empleado', 'cierre_payroll', 'dias_trabajados', 'horas_extras',
                'liquido_pagar', 'estado_procesamiento', 'estado_display',
                'fecha_procesamiento', 'observaciones', 'observaciones_procesamiento',
                'items_detalle', 'resumen_items'
            ]
        
        def get_items_detalle(self, obj):
            items = obj.item_empleado.select_related('item_cierre').all()
            return [
                {
                    'id': item.id,
                    'codigo_item': item.item_cierre.codigo_item,
                    'nombre_item': item.item_cierre.nombre_item,
                    'tipo_item': item.item_cierre.tipo_item,
                    'monto': float(item.monto) if item.monto else 0.0,
                    'monto_formateado': f"${item.monto:,.0f}" if item.monto else "$0",
                    'es_imponible': item.item_cierre.es_imponible,
                    'es_variable': item.item_cierre.es_variable,
                }
                for item in items
            ]
        
        def get_resumen_items(self, obj):
            items = obj.item_empleado.select_related('item_cierre').all()
            
            haberes = items.filter(item_cierre__tipo_item='haberes')
            descuentos = items.filter(item_cierre__tipo_item='descuentos')
            
            total_haberes = sum(item.monto for item in haberes if item.monto)
            total_descuentos = sum(item.monto for item in descuentos if item.monto)
            
            return {
                'total_haberes': float(total_haberes),
                'total_descuentos': float(total_descuentos),
                'liquido_calculado': float(total_haberes - total_descuentos),
                'cantidad_haberes': haberes.count(),
                'cantidad_descuentos': descuentos.count(),
                'total_items': items.count(),
                'haberes_formateado': f"${total_haberes:,.0f}",
                'descuentos_formateado': f"${total_descuentos:,.0f}",
                'liquido_formateado': f"${(total_haberes - total_descuentos):,.0f}",
            }
    
    
    class EmpleadosCierreCreateSerializer(serializers.ModelSerializer):
        """
        Serializer para crear empleados en cierre
        """
        class Meta:
            model = Empleados_Cierre
            fields = ['empleado', 'dias_trabajados', 'horas_extras', 'observaciones']
        
        def validate_dias_trabajados(self, value):
            if value < 0 or value > 31:
                raise serializers.ValidationError("Los días trabajados deben estar entre 0 y 31")
            return value
        
        def validate_horas_extras(self, value):
            if value < 0:
                raise serializers.ValidationError("Las horas extras no pueden ser negativas")
            return value
        
        def validate(self, data):
            # Verificar que el empleado no esté ya en el cierre
            cierre = self.context.get('cierre')
            empleado = data.get('empleado')
            
            if cierre and empleado:
                existing = Empleados_Cierre.objects.filter(
                    cierre_payroll=cierre,
                    empleado=empleado
                ).exists()
                
                if existing:
                    raise serializers.ValidationError(
                        f"El empleado {empleado.username} ya está en este cierre"
                    )
            
            return data
        
        def create(self, validated_data):
            # Asignar cierre del contexto
            validated_data['cierre_payroll'] = self.context['cierre']
            validated_data['estado_procesamiento'] = 'pendiente'
            
            return super().create(validated_data)
    
    
    class EmpleadosCierreUpdateSerializer(serializers.ModelSerializer):
        """
        Serializer para actualizar empleados en cierre
        """
        class Meta:
            model = Empleados_Cierre
            fields = [
                'dias_trabajados', 'horas_extras', 'liquido_pagar',
                'estado_procesamiento', 'observaciones', 'observaciones_procesamiento'
            ]
        
        def validate_estado_procesamiento(self, value):
            """Validar transiciones de estado"""
            if self.instance:
                current_state = self.instance.estado_procesamiento
                
                valid_transitions = {
                    'pendiente': ['procesando', 'procesado'],
                    'procesando': ['procesado', 'error'],
                    'procesado': ['procesando'],  # Re-procesar
                    'error': ['pendiente', 'procesando']
                }
                
                if value not in valid_transitions.get(current_state, []):
                    raise serializers.ValidationError(
                        f"No se puede cambiar el estado de '{current_state}' a '{value}'"
                    )
            
            return value
    
    
    class EmpleadosCierreStatsSerializer(serializers.ModelSerializer):
        """
        Serializer para estadísticas de empleados
        """
        empleado_nombre = serializers.CharField(source='empleado.username', read_only=True)
        empleado_completo = serializers.SerializerMethodField()
        total_items = serializers.SerializerMethodField()
        total_haberes = serializers.SerializerMethodField()
        total_descuentos = serializers.SerializerMethodField()
        
        class Meta:
            model = Empleados_Cierre
            fields = [
                'id', 'empleado_nombre', 'empleado_completo', 'dias_trabajados',
                'horas_extras', 'liquido_pagar', 'estado_procesamiento',
                'total_items', 'total_haberes', 'total_descuentos'
            ]
        
        def get_empleado_completo(self, obj):
            return f"{obj.empleado.first_name} {obj.empleado.last_name}".strip() or obj.empleado.username
        
        def get_total_items(self, obj):
            return obj.item_empleado.count()
        
        def get_total_haberes(self, obj):
            from django.db.models import Sum
            total = obj.item_empleado.filter(
                item_cierre__tipo_item='haberes'
            ).aggregate(total=Sum('monto'))['total']
            return float(total) if total else 0.0
        
        def get_total_descuentos(self, obj):
            from django.db.models import Sum
            total = obj.item_empleado.filter(
                item_cierre__tipo_item='descuentos'
            ).aggregate(total=Sum('monto'))['total']
            return float(total) if total else 0.0
    
    
    # Serializer principal (alias para compatibilidad)
    EmpleadosCierreSerializer = EmpleadosCierreDetailSerializer

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class EmpleadosCierreSerializer:
        pass
    
    class EmpleadosCierreDetailSerializer:
        pass
    
    class EmpleadosCierreCreateSerializer:
        pass
    
    class EmpleadosCierreListSerializer:
        pass
    
    class EmpleadosCierreStatsSerializer:
        pass
