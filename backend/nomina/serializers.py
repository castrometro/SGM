from rest_framework import serializers
from .models import (
    CierreNomina, LibroRemuneracionesUpload, MovimientosMesUpload,
    ArchivoAnalistaUpload, ArchivoNovedadesUpload,
    ConceptoRemuneracion, Novedad,
    IncidenciaComparacion, IncidenciaNovedad, ChecklistItem
)

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'descripcion', 'estado', 'comentario']

class CierreNominaSerializer(serializers.ModelSerializer):
    checklist = ChecklistItemSerializer(many=True, read_only=True)
    class Meta:
        model = CierreNomina
        fields = ['id', 'cliente', 'periodo', 'usuario_analista', 'usuario_supervisor', 'estado','fecha_creacion', 'checklist']

class ChecklistItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['estado', 'comentario']


class ChecklistItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['descripcion']

class CierreNominaCreateSerializer(serializers.ModelSerializer):
    checklist = ChecklistItemCreateSerializer(many=True, write_only=True)
    class Meta:
        model = CierreNomina
        fields = ['cliente', 'periodo', 'usuario_supervisor', 'checklist']
        
    def validate(self, data):
        cliente = data.get('cliente')
        periodo = data.get('periodo')
        print("VALIDANDO: cliente:", cliente, "periodo:", periodo)
        existe = CierreNomina.objects.filter(cliente=cliente, periodo=periodo).exists()
        print("¿Existe cierre?", existe)
        if existe:
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

class ConceptoRemuneracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoRemuneracion
        fields = ['nombre_concepto', 'clasificacion', 'hashtags']

class NovedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Novedad
        fields = '__all__'

class IncidenciaComparacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidenciaComparacion
        fields = '__all__'

class IncidenciaNovedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidenciaNovedad
        fields = '__all__'
