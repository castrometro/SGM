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
    IncidenciaCierre, ResolucionIncidencia,
    # Modelos para análisis de datos
    AnalisisDatosCierre, IncidenciaVariacionSalarial,
    # Modelos para sistema de discrepancias
    DiscrepanciaCierre, TipoDiscrepancia
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
    tipo_resolucion_display = serializers.CharField(source='get_tipo_resolucion_display', read_only=True)
    
    class Meta:
        model = ResolucionIncidencia
        fields = [
            'id', 'tipo_resolucion', 'comentario', 'adjunto',
            'fecha_resolucion', 'usuario', 'usuario_nombre', 'usuario_correo', 'tipo_resolucion_display'
        ]
        read_only_fields = ['usuario', 'fecha_resolucion']

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
            'incidencia', 'tipo_resolucion', 'comentario', 'adjunto'
        ]
    
    def validate(self, data):
        # Validaciones específicas según tipo de resolución
        tipo = data.get('tipo_resolucion')
        
        # No necesitamos validación específica para correcciones en la nueva arquitectura
        # Solo validamos que el comentario no esté vacío
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


# ======== SERIALIZERS PARA ANÁLISIS DE DATOS ========

class AnalisisDatosCierreSerializer(serializers.ModelSerializer):
    variaciones = serializers.SerializerMethodField()
    # Campos con nombres compatibles con el frontend
    empleados_actual = serializers.IntegerField(source='cantidad_empleados_actual', read_only=True)
    empleados_anterior = serializers.IntegerField(source='cantidad_empleados_anterior', read_only=True)
    ingresos_actual = serializers.IntegerField(source='cantidad_ingresos_actual', read_only=True)
    ingresos_anterior = serializers.IntegerField(source='cantidad_ingresos_anterior', read_only=True)
    finiquitos_actual = serializers.IntegerField(source='cantidad_finiquitos_actual', read_only=True)
    finiquitos_anterior = serializers.IntegerField(source='cantidad_finiquitos_anterior', read_only=True)
    ausentismos_actual = serializers.IntegerField(source='cantidad_ausentismos_actual', read_only=True)
    ausentismos_anterior = serializers.IntegerField(source='cantidad_ausentismos_anterior', read_only=True)
    tolerancia_variacion = serializers.DecimalField(source='tolerancia_variacion_salarial', max_digits=5, decimal_places=2, read_only=True)
    periodo_actual = serializers.CharField(source='cierre.periodo', read_only=True)
    periodo_anterior = serializers.SerializerMethodField()
    incidencias_generadas = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalisisDatosCierre
        fields = [
            'id', 'cierre', 'empleados_actual', 'empleados_anterior',
            'ingresos_actual', 'ingresos_anterior', 'finiquitos_actual', 'finiquitos_anterior',
            'ausentismos_actual', 'ausentismos_anterior', 'tolerancia_variacion',
            'periodo_actual', 'periodo_anterior', 'incidencias_generadas',
            'estado', 'fecha_analisis', 'fecha_completado', 'analista', 'notas', 'variaciones'
        ]
    
    def get_variaciones(self, obj):
        """Calcula las variaciones porcentuales"""
        return obj.calcular_variaciones()
    
    def get_periodo_anterior(self, obj):
        """Calcula el periodo anterior basado en el periodo actual"""
        try:
            from datetime import datetime
            periodo_actual = datetime.strptime(obj.cierre.periodo, '%Y-%m')
            if periodo_actual.month == 1:
                periodo_anterior = periodo_actual.replace(year=periodo_actual.year - 1, month=12)
            else:
                periodo_anterior = periodo_actual.replace(month=periodo_actual.month - 1)
            return periodo_anterior.strftime('%Y-%m')
        except:
            return None
    
    def get_incidencias_generadas(self, obj):
        """Cuenta las incidencias de variación salarial generadas"""
        return obj.incidencias_variacion.count()

class IncidenciaVariacionSalarialSerializer(serializers.ModelSerializer):
    analista_asignado_nombre = serializers.SerializerMethodField()
    supervisor_revisor_nombre = serializers.SerializerMethodField()
    diferencia_salarial = serializers.SerializerMethodField()
    
    class Meta:
        model = IncidenciaVariacionSalarial
        fields = [
            'id', 'analisis', 'cierre', 'rut_empleado', 'nombre_empleado',
            'sueldo_base_actual', 'sueldo_base_anterior', 'porcentaje_variacion',
            'tipo_variacion', 'estado', 'analista_asignado', 'supervisor_revisor',
            'justificacion_analista', 'fecha_justificacion', 'comentario_supervisor',
            'fecha_resolucion_supervisor', 'fecha_deteccion', 'fecha_ultima_accion',
            'analista_asignado_nombre', 'supervisor_revisor_nombre', 'diferencia_salarial'
        ]
    
    def get_analista_asignado_nombre(self, obj):
        return obj.analista_asignado.get_full_name() if obj.analista_asignado else None
    
    def get_supervisor_revisor_nombre(self, obj):
        return obj.supervisor_revisor.get_full_name() if obj.supervisor_revisor else None
    
    def get_diferencia_salarial(self, obj):
        return obj.sueldo_base_actual - obj.sueldo_base_anterior


# ===== SERIALIZERS PARA SISTEMA DE DISCREPANCIAS =====

class DiscrepanciaCierreSerializer(serializers.ModelSerializer):
    """Serializer para las discrepancias de verificación de datos"""
    tipo_discrepancia_display = serializers.CharField(source='get_tipo_discrepancia_display', read_only=True)
    empleado_libro_nombre = serializers.SerializerMethodField()
    empleado_novedades_nombre = serializers.SerializerMethodField()
    grupo_discrepancia = serializers.SerializerMethodField()
    
    class Meta:
        model = DiscrepanciaCierre
        fields = [
            'id', 'cierre', 'tipo_discrepancia', 'tipo_discrepancia_display',
            'empleado_libro', 'empleado_novedades', 'rut_empleado',
            'descripcion', 'valor_libro', 'valor_novedades', 
            'valor_movimientos', 'valor_analista', 'concepto_afectado',
            'empleado_libro_nombre', 'empleado_novedades_nombre',
            'grupo_discrepancia'
        ]
    
    def get_empleado_libro_nombre(self, obj):
        """Obtiene el nombre completo del empleado del libro"""
        if obj.empleado_libro:
            return f"{obj.empleado_libro.nombre} {obj.empleado_libro.apellido_paterno} {obj.empleado_libro.apellido_materno}".strip()
        return None
    
    def get_empleado_novedades_nombre(self, obj):
        """Obtiene el nombre completo del empleado de novedades"""
        if obj.empleado_novedades:
            return f"{obj.empleado_novedades.nombre} {obj.empleado_novedades.apellido_paterno} {obj.empleado_novedades.apellido_materno}".strip()
        return None
    
    def get_grupo_discrepancia(self, obj):
        """Determina el grupo de la discrepancia"""
        libro_vs_novedades = [
            'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
            'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
        ]
        
        if obj.tipo_discrepancia in libro_vs_novedades:
            return 'libro_vs_novedades'
        else:
            return 'movimientos_vs_analista'


class ResumenDiscrepanciasSerializer(serializers.Serializer):
    """Serializer para el resumen estadístico de discrepancias"""
    total_discrepancias = serializers.IntegerField()
    discrepancias_por_tipo = serializers.DictField()
    discrepancias_por_grupo = serializers.DictField()
    empleados_afectados = serializers.IntegerField()
    conceptos_afectados = serializers.ListField(child=serializers.CharField(), required=False)
    fecha_ultimo_analisis = serializers.DateTimeField(required=False)
    
    # Totales por grupo
    total_libro_vs_novedades = serializers.IntegerField()
    total_movimientos_vs_analista = serializers.IntegerField()
    
    # Top discrepancias por tipo
    top_tipos_discrepancia = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class DiscrepanciaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear discrepancias (usado internamente por los algoritmos)"""
    class Meta:
        model = DiscrepanciaCierre
        fields = [
            'cierre', 'tipo_discrepancia', 'empleado_libro', 'empleado_novedades',
            'rut_empleado', 'descripcion', 'valor_libro', 'valor_novedades',
            'valor_movimientos', 'valor_analista', 'concepto_afectado'
        ]
