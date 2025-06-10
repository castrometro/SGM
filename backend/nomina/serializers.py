from rest_framework import serializers
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
    MovimientoVariacionSueldo, MovimientoVariacionContrato,
    LibroRemuneracionesUpload, MovimientosMesUpload,
    ArchivoAnalistaUpload, ArchivoNovedadesUpload,
    ChecklistItem, AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso
)

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'descripcion', 'estado', 'comentario']

class ChecklistItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['estado', 'comentario']

class ChecklistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['descripcion']

class CierreNominaSerializer(serializers.ModelSerializer):
    checklist = ChecklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = CierreNomina
        fields = [
            'id', 'cliente', 'periodo', 'usuario_analista',
            'estado', 'fecha_creacion', 'checklist'
        ]

class CierreNominaCreateSerializer(serializers.ModelSerializer):
    checklist = ChecklistItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = CierreNomina
        fields = ['cliente', 'periodo', 'checklist']

    def validate(self, data):
        cliente = data.get('cliente')
        periodo = data.get('periodo')
        if CierreNomina.objects.filter(cliente=cliente, periodo=periodo).exists():
            raise serializers.ValidationError("Ya existe un cierre para este cliente en ese periodo.")
        return data

    def create(self, validated_data):
        checklist_data = validated_data.pop('checklist', [])
        cierre = CierreNomina.objects.create(**validated_data)
        for item in checklist_data:
            ChecklistItem.objects.create(
                cierre=cierre,
                descripcion=item['descripcion'],
                estado='pendiente'
            )
        return cierre

class EmpleadoCierreSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpleadoCierre
        fields = '__all__'

class ConceptoRemuneracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoRemuneracion
        fields = ['nombre_concepto', 'clasificacion', 'hashtags', 'usuario_clasifica']

class RegistroConceptoEmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroConceptoEmpleado
        fields = '__all__'

# Nuevos serializers para los modelos de Movimientos_Mes

class MovimientoAltaBajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoAltaBaja
        fields = '__all__'

class MovimientoAusentismoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoAusentismo
        fields = '__all__'

class MovimientoVacacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoVacaciones
        fields = '__all__'

class MovimientoVariacionSueldoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoVariacionSueldo
        fields = '__all__'

class MovimientoVariacionContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoVariacionContrato
        fields = '__all__'

class LibroRemuneracionesUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroRemuneracionesUpload
        fields = '__all__'

class MovimientosMesUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientosMesUpload
        fields = '__all__'

class ArchivoAnalistaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivoAnalistaUpload
        fields = '__all__'

class ArchivoNovedadesUploadSerializer(serializers.ModelSerializer):
    analista_nombre = serializers.CharField(source='analista.username', read_only=True)
    
    class Meta:
        model = ArchivoNovedadesUpload
        fields = ['id', 'archivo', 'fecha_subida', 'estado', 'analista', 'analista_nombre']
        read_only_fields = ['fecha_subida', 'estado', 'analista']


# Nuevos serializers para los modelos del Analista

class AnalistaFiniquitoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)
    archivo_origen_id = serializers.IntegerField(source='archivo_origen.id', read_only=True)
    
    class Meta:
        model = AnalistaFiniquito
        fields = [
            'id', 'rut', 'nombre', 'fecha_retiro', 'motivo',
            'cierre', 'empleado', 'empleado_nombre', 'archivo_origen', 'archivo_origen_id'
        ]
        read_only_fields = ['cierre', 'empleado', 'archivo_origen']


class AnalistaIncidenciaSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)
    archivo_origen_id = serializers.IntegerField(source='archivo_origen.id', read_only=True)
    
    class Meta:
        model = AnalistaIncidencia
        fields = [
            'id', 'rut', 'nombre', 'fecha_inicio_ausencia', 'fecha_fin_ausencia', 
            'dias', 'tipo_ausentismo', 'cierre', 'empleado', 'empleado_nombre', 
            'archivo_origen', 'archivo_origen_id'
        ]
        read_only_fields = ['cierre', 'empleado', 'archivo_origen']


class AnalistaIngresoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)
    archivo_origen_id = serializers.IntegerField(source='archivo_origen.id', read_only=True)
    
    class Meta:
        model = AnalistaIngreso
        fields = [
            'id', 'rut', 'nombre', 'fecha_ingreso', 'cierre', 
            'empleado', 'empleado_nombre', 'archivo_origen', 'archivo_origen_id'
        ]
        read_only_fields = ['cierre', 'empleado', 'archivo_origen']
