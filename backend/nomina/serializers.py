from rest_framework import serializers
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoIngreso, MovimientoFiniquito, MovimientoAusentismo,
    LibroRemuneracionesUpload, MovimientosMesUpload,
    ArchivoAnalistaUpload, ArchivoNovedadesUpload,
    ChecklistItem
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
        fields = ['nombre_concepto', 'clasificacion', 'hashtags']

class RegistroConceptoEmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroConceptoEmpleado
        fields = '__all__'

class MovimientoIngresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoIngreso
        fields = '__all__'

class MovimientoFiniquitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoFiniquito
        fields = '__all__'

class MovimientoAusentismoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoAusentismo
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
    class Meta:
        model = ArchivoNovedadesUpload
        fields = '__all__'
