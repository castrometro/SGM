from rest_framework import serializers
from .models import CierrePayroll, ArchivoSubido
from api.models import Cliente


class CierrePayrollSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = CierrePayroll
        fields = [
            'id', 'cliente', 'cliente_nombre', 'periodo', 'estado', 'estado_display',
            'fecha_inicio', 'fecha_termino', 'usuario_responsable'
        ]
        read_only_fields = [
            'id', 'fecha_inicio'
        ]


class ArchivoSubidoSerializer(serializers.ModelSerializer):
    tipo_archivo_display = serializers.CharField(source='get_tipo_archivo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tamaño_mb = serializers.SerializerMethodField()
    cierre_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchivoSubido
        fields = [
            'id', 'cierre', 'cierre_info', 'tipo_archivo', 'tipo_archivo_display',
            'estado', 'estado_display', 'nombre_original', 'archivo',
            'tamaño', 'tamaño_mb', 'hash_md5', 'fecha_subida',
            'fecha_procesamiento', 'registros_procesados', 'errores_detectados',
            'metadatos', 'log_errores'
        ]
        read_only_fields = [
            'id', 'hash_md5', 'tamaño', 'fecha_subida', 'fecha_procesamiento'
        ]
    
    def get_tamaño_mb(self, obj):
        if obj.tamaño:
            return round(obj.tamaño / (1024 * 1024), 2)
        return 0
    
    def get_cierre_info(self, obj):
        return {
            'id': obj.cierre.id,
            'cliente': obj.cierre.cliente.nombre,
            'periodo': obj.cierre.periodo,
            'estado': obj.cierre.estado
        }


class ArchivoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer específico para el upload de archivos.
    Incluye validaciones adicionales.
    """
    
    class Meta:
        model = ArchivoSubido
        fields = [
            'cierre', 'tipo_archivo', 'archivo', 'metadatos'
        ]
    
    def validate_archivo(self, value):
        """Validar el archivo subido"""
        # Verificar tamaño máximo (50MB)
        max_size = 50 * 1024 * 1024  # 50MB en bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f"El archivo es demasiado grande. Tamaño máximo permitido: 50MB"
            )
        
        # Verificar extensión
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = value.name.lower().split('.')[-1]
        if f".{file_extension}" not in allowed_extensions:
            raise serializers.ValidationError(
                f"Extensión de archivo no permitida. Extensiones permitidas: {allowed_extensions}"
            )
        
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        cierre = data.get('cierre')
        tipo_archivo = data.get('tipo_archivo')
        
        # Verificar que el cierre esté en un estado que permita subir archivos
        if cierre.estado in ['cerrado', 'error']:
            raise serializers.ValidationError(
                f"No se pueden subir archivos. El cierre está en estado: {cierre.get_estado_display()}"
            )
        
        # Nota: Se permite reemplazar archivos existentes del mismo tipo
        # La lógica de reemplazo se maneja en el ViewSet upload()
        
        return data
    
    def create(self, validated_data):
        # Extraer el nombre original del archivo
        archivo = validated_data['archivo']
        validated_data['nombre_original'] = archivo.name
        
        return super().create(validated_data)


class CierrePayrollCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos cierres de payroll.
    Incluye validaciones específicas para la creación.
    """
    
    class Meta:
        model = CierrePayroll
        fields = [
            'cliente', 'periodo'
        ]
    
    def validate_periodo(self, value):
        """Validar formato del periodo"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError(
                "El periodo debe tener formato YYYY-MM (ejemplo: 2024-12)"
            )
        return value
    
    def validate(self, data):
        """Validar que no exista un cierre para el mismo cliente y periodo"""
        cliente = data.get('cliente')
        periodo = data.get('periodo')
        
        if CierrePayroll.objects.filter(cliente=cliente, periodo=periodo).exists():
            raise serializers.ValidationError(
                f"Ya existe un cierre para el cliente {cliente.nombre} en el periodo {periodo}"
            )
        
        return data
    
    def create(self, validated_data):
        # Establecer valores por defecto
        validated_data['estado'] = 'pendiente'
        validated_data['usuario_responsable'] = self.context['request'].user
        
        cierre = super().create(validated_data)
        
        return cierre


class CierrePayrollListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de cierres.
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = CierrePayroll
        fields = [
            'id', 'cliente', 'cliente_nombre', 'periodo', 'estado', 'estado_display',
            'fecha_inicio'
        ]