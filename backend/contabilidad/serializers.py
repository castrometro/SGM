from rest_framework import serializers
from .models import (
    TipoDocumento,
    CuentaContable,
    CierreContabilidad,
    LibroMayorUpload,
    AperturaCuenta,
    MovimientoContable,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
    Incidencia,
    CentroCosto,
    Auxiliar,
    AnalisisCuentaCierre,
    BulkClasificacionUpload,
    ClasificacionCuentaArchivo,
    NombresEnInglesUpload,
    TarjetaActivityLog,
)

class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'
    
    def validate(self, data):
        # Validar que no exista un tipo de documento con el mismo código para el mismo cliente
        cliente = data.get('cliente')
        codigo = data.get('codigo')
        
        if cliente and codigo:
            # En caso de actualización, excluir el registro actual
            queryset = TipoDocumento.objects.filter(cliente=cliente, codigo=codigo)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError({
                    'codigo': f'Ya existe un tipo de documento con el código "{codigo}" para este cliente.'
                })
        
        return data


class CuentaContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaContable
        fields = '__all__'


class CierreContabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CierreContabilidad
        fields = [
            'id',
            'cliente',
            'usuario',
            'periodo',
            'fecha_inicio_libro',
            'fecha_fin_libro',
            'estado',
            'fecha_creacion',
            'fecha_cierre',
            'cuentas_nuevas',
            'resumen_parsing',
            'parsing_completado',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_cierre', 'usuario']
        
class ProgresoClasificacionSerializer(serializers.Serializer):
    existen_sets = serializers.BooleanField()
    cuentas_nuevas = serializers.IntegerField()
    total_cuentas = serializers.IntegerField()
    parsing_completado = serializers.BooleanField()

class LibroMayorUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroMayorUpload
        fields = [
            'id',
            'cierre',
            'archivo',
            'fecha_subida',
            'procesado',
            'errores',
            'estado',
        ]
        read_only_fields = ['fecha_subida', 'procesado', 'errores', 'estado']



class AperturaCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AperturaCuenta
        fields = '__all__'


class MovimientoContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoContable
        fields = '__all__'


class ClasificacionSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClasificacionSet
        fields = '__all__'


class ClasificacionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClasificacionOption
        fields = '__all__'


class AccountClassificationSerializer(serializers.ModelSerializer):
    # Campos adicionales para mostrar información detallada
    cuenta_codigo = serializers.CharField(source='cuenta.codigo', read_only=True)
    cuenta_nombre = serializers.CharField(source='cuenta.nombre', read_only=True)
    set_nombre = serializers.CharField(source='set_clas.nombre', read_only=True)
    opcion_valor = serializers.CharField(source='opcion.valor', read_only=True)
    opcion_descripcion = serializers.CharField(source='opcion.descripcion', read_only=True)
    asignado_por_nombre = serializers.CharField(source='asignado_por.nombre', read_only=True)
    
    class Meta:
        model = AccountClassification
        fields = [
            'id', 'cuenta', 'set_clas', 'opcion', 'asignado_por', 'fecha',
            'cuenta_codigo', 'cuenta_nombre', 'set_nombre', 'opcion_valor', 
            'opcion_descripcion', 'asignado_por_nombre'
        ]

class AnalisisCuentaCierreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalisisCuentaCierre
        fields = '__all__'


class IncidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidencia
        fields = '__all__'


class CentroCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCosto
        fields = '__all__'


class AuxiliarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auxiliar
        fields = '__all__'

class BulkClasificacionUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkClasificacionUpload
        fields = ['id', 'cliente', 'archivo', 'fecha_subida', 'estado', 'errores', 'resumen']

class ClasificacionCuentaArchivoSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar las clasificaciones tal como vienen del archivo,
    antes del mapeo a cuentas reales
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    upload_archivo = serializers.CharField(source='upload.archivo.name', read_only=True)
    
    class Meta:
        model = ClasificacionCuentaArchivo
        fields = [
            'id', 'cliente', 'cliente_nombre', 'upload', 'upload_archivo',
            'numero_cuenta', 'clasificaciones', 'fila_excel', 'procesado',
            'errores_mapeo', 'cuenta_mapeada', 'fecha_creacion', 'fecha_procesado'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_procesado']

class NombresEnInglesUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = NombresEnInglesUpload
        fields = ['id', 'cliente', 'cierre', 'archivo', 'fecha_subida', 'estado', 'errores', 'resumen']

class TarjetaActivityLogSerializer(serializers.ModelSerializer):
    tarjeta_display = serializers.CharField(source='get_tarjeta_display', read_only=True)
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='cierre.cliente.nombre', read_only=True)
    
    class Meta:
        model = TarjetaActivityLog
        fields = ['id', 'cierre', 'tarjeta', 'tarjeta_display', 'accion', 'accion_display', 
                 'usuario', 'usuario_nombre', 'cliente_nombre', 'descripcion', 'detalles', 
                 'resultado', 'timestamp', 'ip_address']
        read_only_fields = ['timestamp']
