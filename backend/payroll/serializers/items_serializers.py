# ============================================================================
#                           ITEMS SERIALIZERS
# ============================================================================
# Serializers para la gestión de items de nómina (haberes y descuentos)

try:
    from rest_framework import serializers
    from ..models import Item_Cierre, Item_Empleado, CierrePayroll, Empleados_Cierre
    
    
    class ItemCierreListSerializer(serializers.ModelSerializer):
        """
        Serializer para lista de items del cierre
        """
        tipo_display = serializers.CharField(source='get_tipo_item_display', read_only=True)
        total_empleados = serializers.SerializerMethodField()
        monto_total = serializers.SerializerMethodField()
        
        class Meta:
            model = Item_Cierre
            fields = [
                'id', 'codigo_item', 'nombre_item', 'tipo_item', 'tipo_display',
                'es_imponible', 'es_variable', 'orden_calculo',
                'total_empleados', 'monto_total'
            ]
        
        def get_total_empleados(self, obj):
            return obj.item_empleado.count()
        
        def get_monto_total(self, obj):
            from django.db.models import Sum
            total = obj.item_empleado.aggregate(total=Sum('monto'))['total']
            return float(total) if total else 0.0
    
    
    class ItemCierreDetailSerializer(serializers.ModelSerializer):
        """
        Serializer detallado para item del cierre
        """
        tipo_display = serializers.CharField(source='get_tipo_item_display', read_only=True)
        estadisticas = serializers.SerializerMethodField()
        empleados_con_item = serializers.SerializerMethodField()
        
        class Meta:
            model = Item_Cierre
            fields = [
                'id', 'codigo_item', 'nombre_item', 'tipo_item', 'tipo_display',
                'es_imponible', 'es_variable', 'orden_calculo',
                'estadisticas', 'empleados_con_item'
            ]
        
        def get_estadisticas(self, obj):
            from django.db.models import Sum, Avg, Count, Min, Max
            
            items_empleado = obj.item_empleado.all()
            
            if not items_empleado.exists():
                return {
                    'total_empleados': 0,
                    'monto_total': 0.0,
                    'monto_promedio': 0.0,
                    'monto_minimo': 0.0,
                    'monto_maximo': 0.0,
                }
            
            stats = items_empleado.aggregate(
                total_empleados=Count('id'),
                monto_total=Sum('monto'),
                monto_promedio=Avg('monto'),
                monto_minimo=Min('monto'),
                monto_maximo=Max('monto')
            )
            
            return {
                'total_empleados': stats['total_empleados'] or 0,
                'monto_total': float(stats['monto_total'] or 0),
                'monto_promedio': float(stats['monto_promedio'] or 0),
                'monto_minimo': float(stats['monto_minimo'] or 0),
                'monto_maximo': float(stats['monto_maximo'] or 0),
                'monto_total_formateado': f"${(stats['monto_total'] or 0):,.0f}",
                'monto_promedio_formateado': f"${(stats['monto_promedio'] or 0):,.0f}",
            }
        
        def get_empleados_con_item(self, obj):
            items_empleado = obj.item_empleado.select_related(
                'empleado_cierre__empleado'
            ).all()[:10]  # Limitar a 10 para performance
            
            return [
                {
                    'empleado_id': item.empleado_cierre.empleado.id,
                    'empleado_nombre': f"{item.empleado_cierre.empleado.first_name} {item.empleado_cierre.empleado.last_name}".strip() or item.empleado_cierre.empleado.username,
                    'monto': float(item.monto) if item.monto else 0.0,
                    'monto_formateado': f"${item.monto:,.0f}" if item.monto else "$0",
                }
                for item in items_empleado
            ]
    
    
    class ItemCierreCreateSerializer(serializers.ModelSerializer):
        """
        Serializer para crear items en el cierre
        """
        class Meta:
            model = Item_Cierre
            fields = [
                'codigo_item', 'nombre_item', 'tipo_item',
                'es_imponible', 'es_variable', 'orden_calculo'
            ]
        
        def validate_codigo_item(self, value):
            # Verificar que no exista otro item con el mismo código en el cierre
            cierre = self.context.get('cierre')
            if cierre:
                existing = Item_Cierre.objects.filter(
                    cierre_payroll=cierre,
                    codigo_item=value
                ).exists()
                
                if existing:
                    raise serializers.ValidationError(
                        f"Ya existe un item con código '{value}' en este cierre"
                    )
            
            return value.upper()  # Normalizar a mayúsculas
        
        def validate_orden_calculo(self, value):
            if value < 1 or value > 999:
                raise serializers.ValidationError(
                    "El orden de cálculo debe estar entre 1 y 999"
                )
            return value
        
        def create(self, validated_data):
            # Asignar cierre del contexto
            validated_data['cierre_payroll'] = self.context['cierre']
            return super().create(validated_data)
    
    
    class ItemEmpleadoSerializer(serializers.ModelSerializer):
        """
        Serializer para items de empleado
        """
        item_cierre = ItemCierreListSerializer(read_only=True)
        empleado_nombre = serializers.SerializerMethodField()
        monto_formateado = serializers.SerializerMethodField()
        
        class Meta:
            model = Item_Empleado
            fields = [
                'id', 'item_cierre', 'empleado_cierre', 'monto',
                'monto_formateado', 'empleado_nombre'
            ]
        
        def get_empleado_nombre(self, obj):
            return f"{obj.empleado_cierre.empleado.first_name} {obj.empleado_cierre.empleado.last_name}".strip() or obj.empleado_cierre.empleado.username
        
        def get_monto_formateado(self, obj):
            if obj.monto:
                return f"${obj.monto:,.0f}"
            return "$0"
    
    
    class ItemEmpleadoDetailSerializer(serializers.ModelSerializer):
        """
        Serializer detallado para item de empleado
        """
        item_cierre = ItemCierreDetailSerializer(read_only=True)
        empleado_info = serializers.SerializerMethodField()
        monto_formateado = serializers.SerializerMethodField()
        
        class Meta:
            model = Item_Empleado
            fields = [
                'id', 'item_cierre', 'empleado_cierre', 'monto',
                'monto_formateado', 'empleado_info'
            ]
        
        def get_empleado_info(self, obj):
            empleado = obj.empleado_cierre.empleado
            return {
                'id': empleado.id,
                'username': empleado.username,
                'nombre_completo': f"{empleado.first_name} {empleado.last_name}".strip() or empleado.username,
                'email': empleado.email,
            }
        
        def get_monto_formateado(self, obj):
            if obj.monto:
                return f"${obj.monto:,.0f}"
            return "$0"
    
    
    class ItemEmpleadoCreateSerializer(serializers.ModelSerializer):
        """
        Serializer para crear items de empleado
        """
        class Meta:
            model = Item_Empleado
            fields = ['item_cierre', 'empleado_cierre', 'monto']
        
        def validate_monto(self, value):
            if value < 0:
                raise serializers.ValidationError("El monto no puede ser negativo")
            return value
        
        def validate(self, data):
            # Verificar que el item y empleado pertenezcan al mismo cierre
            item_cierre = data.get('item_cierre')
            empleado_cierre = data.get('empleado_cierre')
            
            if item_cierre and empleado_cierre:
                if item_cierre.cierre_payroll != empleado_cierre.cierre_payroll:
                    raise serializers.ValidationError(
                        "El item y el empleado deben pertenecer al mismo cierre"
                    )
                
                # Verificar que no exista ya este item para este empleado
                existing = Item_Empleado.objects.filter(
                    item_cierre=item_cierre,
                    empleado_cierre=empleado_cierre
                ).exists()
                
                if existing:
                    raise serializers.ValidationError(
                        f"El empleado ya tiene asignado el item '{item_cierre.nombre_item}'"
                    )
            
            return data
    
    
    class ItemCierreStatsSerializer(serializers.ModelSerializer):
        """
        Serializer para estadísticas de items
        """
        tipo_display = serializers.CharField(source='get_tipo_item_display', read_only=True)
        total_empleados = serializers.SerializerMethodField()
        monto_total = serializers.SerializerMethodField()
        monto_promedio = serializers.SerializerMethodField()
        porcentaje_cobertura = serializers.SerializerMethodField()
        
        class Meta:
            model = Item_Cierre
            fields = [
                'id', 'codigo_item', 'nombre_item', 'tipo_item', 'tipo_display',
                'es_imponible', 'es_variable', 'total_empleados', 'monto_total',
                'monto_promedio', 'porcentaje_cobertura'
            ]
        
        def get_total_empleados(self, obj):
            return obj.item_empleado.count()
        
        def get_monto_total(self, obj):
            from django.db.models import Sum
            total = obj.item_empleado.aggregate(total=Sum('monto'))['total']
            return float(total) if total else 0.0
        
        def get_monto_promedio(self, obj):
            from django.db.models import Avg
            promedio = obj.item_empleado.aggregate(promedio=Avg('monto'))['promedio']
            return float(promedio) if promedio else 0.0
        
        def get_porcentaje_cobertura(self, obj):
            total_empleados_cierre = obj.cierre_payroll.empleados_cierre.count()
            empleados_con_item = obj.item_empleado.count()
            
            if total_empleados_cierre > 0:
                return round((empleados_con_item / total_empleados_cierre) * 100, 2)
            return 0.0
    
    
    # Serializers principales (alias para compatibilidad)
    ItemCierreSerializer = ItemCierreDetailSerializer

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class ItemCierreSerializer:
        pass
    
    class ItemCierreDetailSerializer:
        pass
    
    class ItemCierreCreateSerializer:
        pass
    
    class ItemCierreListSerializer:
        pass
    
    class ItemEmpleadoSerializer:
        pass
    
    class ItemEmpleadoDetailSerializer:
        pass
    
    class ItemEmpleadoCreateSerializer:
        pass
    
    class ItemCierreStatsSerializer:
        pass
