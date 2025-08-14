# ============================================================================
#                           INGRESOS SERIALIZERS
# ============================================================================

try:
    from rest_framework import serializers
    from ..models import Ingresos_Cierre
    
    class IngresosCierreSerializer(serializers.ModelSerializer):
        class Meta:
            model = Ingresos_Cierre
            fields = '__all__'
    
    class IngresosCierreCreateSerializer(IngresosCierreSerializer):
        pass

except ImportError:
    class IngresosCierreSerializer:
        pass
    
    class IngresosCierreCreateSerializer:
        pass
