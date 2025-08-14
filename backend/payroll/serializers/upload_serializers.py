# ============================================================================
#                           UPLOAD SERIALIZERS
# ============================================================================
# Serializers para carga de archivos y validaciones

try:
    from rest_framework import serializers
    from django.core.files.uploadedfile import UploadedFile
    
    
    class UploadExcelSerializer(serializers.Serializer):
        """
        Serializer para carga de archivos Excel
        """
        excel_file = serializers.FileField()
        cierre_id = serializers.IntegerField()
        
        def validate_excel_file(self, value):
            """Validar archivo Excel"""
            if not value.name.endswith(('.xlsx', '.xls')):
                raise serializers.ValidationError(
                    "El archivo debe ser un Excel válido (.xlsx o .xls)"
                )
            
            # Validar tamaño (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El archivo no puede ser mayor a 10MB"
                )
            
            return value
        
        def validate_cierre_id(self, value):
            """Validar que el cierre existe"""
            from ..models import CierrePayroll
            
            try:
                cierre = CierrePayroll.objects.get(id=value)
                if cierre.estado == 'completado':
                    raise serializers.ValidationError(
                        "No se pueden cargar archivos a un cierre completado"
                    )
                return value
            except CierrePayroll.DoesNotExist:
                raise serializers.ValidationError("El cierre especificado no existe")
    
    
    class UploadPDFSerializer(serializers.Serializer):
        """
        Serializer para carga de archivos PDF
        """
        pdf_file = serializers.FileField()
        cierre_id = serializers.IntegerField()
        tipo_pdf = serializers.ChoiceField(
            choices=[
                ('comparacion', 'Comparación'),
                ('reporte', 'Reporte'),
                ('liquidacion', 'Liquidación')
            ],
            default='comparacion'
        )
        
        def validate_pdf_file(self, value):
            """Validar archivo PDF"""
            if not value.name.endswith('.pdf'):
                raise serializers.ValidationError(
                    "El archivo debe ser un PDF válido"
                )
            
            # Validar tamaño (max 20MB)
            if value.size > 20 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El archivo no puede ser mayor a 20MB"
                )
            
            return value
    
    
    class ImportarEmpleadosSerializer(serializers.Serializer):
        """
        Serializer para importación masiva de empleados
        """
        excel_empleados = serializers.FileField()
        crear_usuarios = serializers.BooleanField(default=True)
        actualizar_existentes = serializers.BooleanField(default=False)
        
        def validate_excel_empleados(self, value):
            """Validar archivo de empleados"""
            if not value.name.endswith(('.xlsx', '.xls')):
                raise serializers.ValidationError(
                    "El archivo debe ser un Excel válido (.xlsx o .xls)"
                )
            
            # Validar tamaño (max 5MB para empleados)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El archivo no puede ser mayor a 5MB"
                )
            
            return value
    
    
    class ValidacionArchivoSerializer(serializers.Serializer):
        """
        Serializer para validación previa de archivos
        """
        archivo = serializers.FileField()
        tipo_validacion = serializers.ChoiceField(
            choices=[
                ('excel_payroll', 'Excel Payroll'),
                ('excel_empleados', 'Excel Empleados'),
                ('pdf_comparacion', 'PDF Comparación')
            ]
        )
        
        def validate_archivo(self, value):
            """Validaciones básicas del archivo"""
            tipo_validacion = self.initial_data.get('tipo_validacion')
            
            if tipo_validacion in ['excel_payroll', 'excel_empleados']:
                if not value.name.endswith(('.xlsx', '.xls')):
                    raise serializers.ValidationError(
                        "Debe ser un archivo Excel (.xlsx o .xls)"
                    )
            elif tipo_validacion == 'pdf_comparacion':
                if not value.name.endswith('.pdf'):
                    raise serializers.ValidationError(
                        "Debe ser un archivo PDF"
                    )
            
            return value
    
    
    class ResultadoUploadSerializer(serializers.Serializer):
        """
        Serializer para respuesta de upload
        """
        success = serializers.BooleanField()
        message = serializers.CharField()
        archivo_id = serializers.IntegerField(required=False)
        archivo_url = serializers.URLField(required=False)
        
        # Estadísticas del procesamiento
        empleados_procesados = serializers.IntegerField(default=0)
        items_procesados = serializers.IntegerField(default=0)
        errores = serializers.ListField(child=serializers.CharField(), default=list)
        advertencias = serializers.ListField(child=serializers.CharField(), default=list)
        
        # Tiempo de procesamiento
        tiempo_procesamiento = serializers.FloatField(required=False)
    
    
    class ResultadoValidacionSerializer(serializers.Serializer):
        """
        Serializer para respuesta de validación
        """
        formato_valido = serializers.BooleanField()
        errores = serializers.ListField(child=serializers.CharField(), default=list)
        advertencias = serializers.ListField(child=serializers.CharField(), default=list)
        
        # Información del archivo
        hojas_encontradas = serializers.ListField(child=serializers.CharField(), default=list)
        hojas_requeridas = serializers.ListField(child=serializers.CharField(), default=list)
        
        # Estadísticas preliminares
        total_filas = serializers.IntegerField(default=0)
        columnas_detectadas = serializers.ListField(child=serializers.CharField(), default=list)
        
        # Recomendaciones
        recomendaciones = serializers.ListField(child=serializers.CharField(), default=list)

except ImportError:
    # Si REST framework no está disponible, crear clases dummy
    class UploadExcelSerializer:
        pass
    
    class UploadPDFSerializer:
        pass
    
    class ImportarEmpleadosSerializer:
        pass
    
    class ValidacionArchivoSerializer:
        pass
    
    class ResultadoUploadSerializer:
        pass
    
    class ResultadoValidacionSerializer:
        pass
