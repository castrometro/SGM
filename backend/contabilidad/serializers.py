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
)

class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'


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
    class Meta:
        model = AccountClassification
        fields = '__all__'

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
