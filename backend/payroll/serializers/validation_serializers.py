# ============================================================================
#                           VALIDATION SERIALIZERS
# ============================================================================
# Serializers para validaciones de datos y consistencia

try:
    from rest_framework import serializers
    
    
    class ValidacionDatosSerializer(serializers.Serializer):
        """
        Serializer para validación de datos del cierre
        """
        cierre_id = serializers.IntegerField()
        validaciones_realizadas = serializers.ListField(child=serializers.CharField())
        
        # Resultados de validación
        empleados_sin_items = serializers.ListField(child=serializers.DictField(), default=list)
        items_sin_empleados = serializers.ListField(child=serializers.DictField(), default=list)
        montos_inconsistentes = serializers.ListField(child=serializers.DictField(), default=list)
        duplicados = serializers.ListField(child=serializers.DictField(), default=list)
        
        # Totales
        total_errores = serializers.IntegerField(default=0)
        total_advertencias = serializers.IntegerField(default=0)
        validacion_exitosa = serializers.BooleanField()
    
    
    class ComparacionArchivosSerializer(serializers.Serializer):
        """
        Serializer para comparación de archivos
        """
        archivo_origen = serializers.CharField()
        archivo_destino = serializers.CharField()
        tipo_comparacion = serializers.ChoiceField(
            choices=[
                ('excel_vs_db', 'Excel vs Base de Datos'),
                ('excel_vs_excel', 'Excel vs Excel'),
                ('pdf_vs_excel', 'PDF vs Excel')
            ]
        )
        
        # Resultados
        diferencias_encontradas = serializers.IntegerField(default=0)
        coincidencias = serializers.IntegerField(default=0)
        porcentaje_coincidencia = serializers.FloatField(default=0.0)
        
        # Detalles de diferencias
        diferencias_detalle = serializers.ListField(child=serializers.DictField(), default=list)

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class ValidacionDatosSerializer:
        pass
    
    class ComparacionArchivosSerializer:
        pass
