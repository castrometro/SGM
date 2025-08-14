# ============================================================================
#                         INCIDENCIAS SERIALIZERS
# ============================================================================

try:
    from rest_framework import serializers
    from ..models import Incidencias_Cierre
    
    class IncidenciasCierreSerializer(serializers.ModelSerializer):
        class Meta:
            model = Incidencias_Cierre
            fields = '__all__'
    
    class IncidenciasCierreCreateSerializer(IncidenciasCierreSerializer):
        pass

except ImportError:
    class IncidenciasCierreSerializer:
        pass
    
    class IncidenciasCierreCreateSerializer:
        pass
