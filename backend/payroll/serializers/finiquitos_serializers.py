# ============================================================================
#                           FINIQUITOS SERIALIZERS
# ============================================================================

try:
    from rest_framework import serializers
    from ..models import Finiquitos_Cierre
    
    class FiniquitosCierreSerializer(serializers.ModelSerializer):
        empleado_nombre = serializers.SerializerMethodField()
        
        class Meta:
            model = Finiquitos_Cierre
            fields = '__all__'
        
        def get_empleado_nombre(self, obj):
            return f"{obj.empleado.first_name} {obj.empleado.last_name}".strip() or obj.empleado.username
    
    class FiniquitosCierreDetailSerializer(FiniquitosCierreSerializer):
        pass

except ImportError:
    class FiniquitosCierreSerializer:
        pass
    
    class FiniquitosCierreDetailSerializer:
        pass
