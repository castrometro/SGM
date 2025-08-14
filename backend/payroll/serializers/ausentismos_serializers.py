# ============================================================================
#                         AUSENTISMOS SERIALIZERS
# ============================================================================

try:
    from rest_framework import serializers
    from ..models import Ausentismos_Cierre
    
    class AusentismosCierreSerializer(serializers.ModelSerializer):
        class Meta:
            model = Ausentismos_Cierre
            fields = '__all__'
    
    class AusentismosCierreCreateSerializer(AusentismosCierreSerializer):
        pass

except ImportError:
    class AusentismosCierreSerializer:
        pass
    
    class AusentismosCierreCreateSerializer:
        pass
