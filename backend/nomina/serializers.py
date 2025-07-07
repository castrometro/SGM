from rest_framework import serializers
from .models import (
    CierreNomina, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
    MovimientoVariacionSueldo, MovimientoVariacionContrato,
    LibroRemuneracionesUpload, MovimientosMesUpload,
    ArchivoAnalistaUpload, ArchivoNovedadesUpload,
    ChecklistItem, AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso,
    # Nuevos modelos para novedades
    EmpleadoCierreNovedades, ConceptoRemuneracionNovedades, RegistroConceptoEmpleadoNovedades,
    # Modelos para el sistema de incidencias
    IncidenciaCierre, ResolucionIncidencia
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
        fields = ['id', 'nombre_concepto', 'clasificacion', 'hashtags', 'usuario_clasifica']

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
    analista_nombre = serializers.CharField(source='analista.correo_bdo', read_only=True)
    
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


# Serializers para modelos de Novedades

class EmpleadoCierreNovedadesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpleadoCierreNovedades
        fields = ['id', 'rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'cierre']
        read_only_fields = ['cierre']


class ConceptoRemuneracionNovedadesSerializer(serializers.ModelSerializer):
    usuario_mapea_nombre = serializers.CharField(source='usuario_mapea.correo_bdo', read_only=True)
    concepto_libro_nombre = serializers.CharField(source='concepto_libro.nombre_concepto', read_only=True)
    clasificacion = serializers.CharField(read_only=True)  # Viene del concepto del libro
    hashtags = serializers.JSONField(read_only=True)  # Viene del concepto del libro
    
    concepto_libro = serializers.PrimaryKeyRelatedField(
        queryset=ConceptoRemuneracion.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = ConceptoRemuneracionNovedades
        fields = [
            'id', 'nombre_concepto_novedades', 'concepto_libro', 'concepto_libro_nombre',
            'clasificacion', 'hashtags', 'activo', 'cliente', 'usuario_mapea',
            'usuario_mapea_nombre', 'fecha_mapeo'
        ]
        read_only_fields = ['cliente', 'usuario_mapea', 'fecha_mapeo', 'clasificacion', 'hashtags']


class RegistroConceptoEmpleadoNovedadesSerializer(serializers.ModelSerializer):
    empleado_rut = serializers.CharField(source='empleado.rut', read_only=True)
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)
    concepto_nombre = serializers.CharField(source='concepto.nombre_concepto', read_only=True)
    concepto_clasificacion = serializers.CharField(source='concepto.clasificacion', read_only=True)
    
    class Meta:
        model = RegistroConceptoEmpleadoNovedades
        fields = [
            'id', 'nombre_concepto_original', 'monto', 'fecha_registro',
            'empleado', 'empleado_rut', 'empleado_nombre',
            'concepto', 'concepto_nombre', 'concepto_clasificacion'
        ]
        read_only_fields = ['empleado', 'concepto', 'fecha_registro']


# ===== SERIALIZERS PARA SISTEMA DE INCIDENCIAS =====

class ResolucionIncidenciaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    usuario_correo = serializers.CharField(source='usuario.correo_bdo', read_only=True)
    usuarios_mencionados_nombres = serializers.SerializerMethodField()
    
    class Meta:
        model = ResolucionIncidencia
        fields = [
            'id', 'tipo_resolucion', 'comentario', 'adjunto',
            'fecha_resolucion', 'estado_anterior', 'estado_nuevo',
            'valor_corregido', 'campo_corregido', 'usuario',
            'usuario_nombre', 'usuario_correo', 'usuarios_mencionados',
            'usuarios_mencionados_nombres'
        ]
        read_only_fields = ['usuario', 'fecha_resolucion', 'estado_anterior', 'estado_nuevo']
    
    def get_usuarios_mencionados_nombres(self, obj):
        return [user.get_full_name() or user.correo_bdo for user in obj.usuarios_mencionados.all()]

class IncidenciaCierreSerializer(serializers.ModelSerializer):
    empleado_libro_nombre = serializers.SerializerMethodField()
    empleado_novedades_nombre = serializers.SerializerMethodField()
    tipo_incidencia_display = serializers.CharField(source='get_tipo_incidencia_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    resoluciones = ResolucionIncidenciaSerializer(many=True, read_only=True)
    asignado_a_nombre = serializers.CharField(source='asignado_a.get_full_name', read_only=True)
    tiempo_sin_resolver = serializers.SerializerMethodField()
    
    class Meta:
        model = IncidenciaCierre
        fields = [
            'id', 'tipo_incidencia', 'tipo_incidencia_display', 'rut_empleado',
            'descripcion', 'valor_libro', 'valor_novedades', 'valor_movimientos',
            'valor_analista', 'concepto_afectado', 'fecha_detectada',
            'estado', 'estado_display', 'prioridad', 'prioridad_display',
            'impacto_monetario', 'asignado_a', 'asignado_a_nombre',
            'fecha_primera_resolucion', 'fecha_ultima_accion',
            'empleado_libro', 'empleado_novedades', 'empleado_libro_nombre',
            'empleado_novedades_nombre', 'resoluciones', 'tiempo_sin_resolver'
        ]
        read_only_fields = [
            'fecha_detectada', 'fecha_primera_resolucion', 'fecha_ultima_accion',
            'tiempo_sin_resolver'
        ]
    
    def get_empleado_libro_nombre(self, obj):
        if obj.empleado_libro:
            return f"{obj.empleado_libro.nombre} {obj.empleado_libro.apellido_paterno}"
        return None
    
    def get_empleado_novedades_nombre(self, obj):
        if obj.empleado_novedades:
            return f"{obj.empleado_novedades.nombre} {obj.empleado_novedades.apellido_paterno}"
        return None
    
    def get_tiempo_sin_resolver(self, obj):
        if obj.estado == 'pendiente':
            from django.utils import timezone
            diff = timezone.now() - obj.fecha_detectada
            return diff.days
        return None

class CrearResolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResolucionIncidencia
        fields = [
            'tipo_resolucion', 'comentario', 'adjunto',
            'valor_corregido', 'campo_corregido', 'usuarios_mencionados'
        ]
    
    def validate(self, data):
        # Validaciones específicas según tipo de resolución
        tipo = data.get('tipo_resolucion')
        
        if tipo == 'correccion' and not data.get('valor_corregido'):
            raise serializers.ValidationError({
                'valor_corregido': 'El valor corregido es requerido para correcciones.'
            })
        
        if not data.get('comentario', '').strip():
            raise serializers.ValidationError({
                'comentario': 'El comentario es requerido.'
            })
        
        return data

class ResumenIncidenciasSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    por_prioridad = serializers.DictField()
    por_estado = serializers.DictField()
    impacto_monetario_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Estadísticas adicionales
    pendientes_criticas = serializers.IntegerField(required=False)
    tiempo_promedio_resolucion = serializers.FloatField(required=False)
    porcentaje_resueltas = serializers.FloatField(required=False)
