"""
Serializers para Nueva Arquitectura de Nómina SGM
================================================

Serializers para modelos rediseñados centrados en CierreNomina:
- CierreNomina: Modelo principal con integración Redis
- EmpleadoNomina/EmpleadoConcepto: Lista empleados y conceptos
- Ausentismos, Incidencias: Datos adicionales del cierre
- KPINomina: Métricas pre-calculadas para dashboards
- Sistema de ofuscación y optimizaciones

Autor: Sistema SGM - Módulo Nómina  
Fecha: 20 de julio de 2025
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from api.models import Cliente
from .models import (
    # Modelos principales
    CierreNomina,
    EmpleadoNomina, 
    EmpleadoConcepto,
    Ausentismo,
    Incidencia,
    InteraccionIncidencia,
    
    # Optimizaciones y KPIs
    KPINomina,
    EmpleadoOfuscado,
    IndiceEmpleadoBusqueda,
    ComparacionMensual,
    CacheConsultas,
    
    # Mapeos y utilidades
    MapeoConcepto,
    MapeoNovedades,
    LogArchivo,
)

User = get_user_model()

# ========== SERIALIZERS PRINCIPALES ==========

class CierreNominaListSerializer(serializers.ModelSerializer):
    """Serializer para lista de cierres (datos mínimos)"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    analista_nombre = serializers.CharField(
        source='analista_responsable.get_full_name', 
        read_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    # Contadores rápidos
    total_empleados = serializers.IntegerField(
        source='total_empleados_activos',
        read_only=True
    )
    
    class Meta:
        model = CierreNomina
        fields = [
            'id', 'periodo', 'estado', 'estado_display',
            'cliente', 'cliente_nombre',
            'analista_responsable', 'analista_nombre',
            'fecha_creacion', 'fecha_consolidacion', 'fecha_cierre',
            'total_empleados', 'total_finiquitos', 'total_ingresos',
            'discrepancias_detectadas'
        ]

class CierreNominaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de cierre"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    analista_nombre = serializers.CharField(
        source='analista_responsable.get_full_name', 
        read_only=True
    )
    usuario_cierre_nombre = serializers.CharField(
        source='usuario_cierre.get_full_name', 
        read_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    # Contadores de empleados
    empleados_count = serializers.SerializerMethodField()
    incidencias_count = serializers.SerializerMethodField()
    kpis_disponibles = serializers.SerializerMethodField()
    
    class Meta:
        model = CierreNomina
        fields = [
            'id', 'periodo', 'estado', 'estado_display', 'version',
            
            # Relaciones
            'cliente', 'cliente_nombre',
            'analista_responsable', 'analista_nombre',
            'usuario_cierre', 'usuario_cierre_nombre',
            
            # Fechas del ciclo de vida
            'fecha_creacion', 'fecha_consolidacion', 'fecha_cierre',
            
            # Metadatos
            'total_empleados_activos', 'total_finiquitos', 'total_ingresos',
            'discrepancias_detectadas', 'cache_key_redis',
            'archivos_procesados',
            
            # Control de reaperturas
            'fecha_reapertura', 'motivo_reapertura',
            
            # Observaciones
            'observaciones',
            
            # Campos calculados
            'empleados_count', 'incidencias_count', 'kpis_disponibles'
        ]
        
    def get_empleados_count(self, obj):
        return obj.empleados_nomina.count()
    
    def get_incidencias_count(self, obj):
        return obj.incidencias.count()
    
    def get_kpis_disponibles(self, obj):
        return obj.kpis_calculados.count()

class CierreNominaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevos cierres"""
    
    class Meta:
        model = CierreNomina
        fields = [
            'id', 'cliente', 'periodo', 'analista_responsable', 'observaciones'
        ]
    
    def validate(self, data):
        cliente = data.get('cliente')
        periodo = data.get('periodo')
        
        # Validar que no exista otro cierre para el mismo cliente/período
        if CierreNomina.objects.filter(cliente=cliente, periodo=periodo).exists():
            raise serializers.ValidationError({
                'periodo': f'Ya existe un cierre para {cliente.nombre} en el período {periodo}'
            })
        
        # Validar formato del período (YYYY-MM)
        try:
            year, month = periodo.split('-')
            if len(year) != 4 or len(month) != 2:
                raise ValueError
            int(year)
            month_int = int(month)
            if not 1 <= month_int <= 12:
                raise ValueError
        except (ValueError, AttributeError):
            raise serializers.ValidationError({
                'periodo': 'El período debe tener formato YYYY-MM (ej: 2025-07)'
            })
        
        return data
    
    def create(self, validated_data):
        # Ahora que el ORM funciona, usar creación normal
        cierre = CierreNomina.objects.create(**validated_data)
        
        # Inicializar en Redis si es necesario (comentado por ahora)
        # cierre.inicializar_en_redis()
        
        return cierre

# ========== EMPLEADOS Y CONCEPTOS ==========

class EmpleadoConceptoSerializer(serializers.ModelSerializer):
    """Serializer para conceptos de empleados"""
    
    concepto_clasificacion = serializers.SerializerMethodField()
    
    class Meta:
        model = EmpleadoConcepto
        fields = [
            'id', 'concepto', 'valor', 'valor_numerico',
            'fecha_consolidacion', 'concepto_clasificacion'
        ]
    
    def get_concepto_clasificacion(self, obj):
        return obj.get_clasificacion()

class EmpleadoNominaListSerializer(serializers.ModelSerializer):
    """Serializer para lista de empleados (datos mínimos)"""
    
    tipo_empleado_display = serializers.CharField(source='get_tipo_empleado_display', read_only=True)
    conceptos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmpleadoNomina
        fields = [
            'id', 'rut_empleado', 'nombre_empleado', 
            'tipo_empleado', 'tipo_empleado_display',
            'fecha_ingreso', 'fecha_finiquito', 'motivo_finiquito',
            'fecha_consolidacion', 'conceptos_count'
        ]
    
    def get_conceptos_count(self, obj):
        return obj.conceptos.count()

class EmpleadoNominaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de empleado"""
    
    conceptos = EmpleadoConceptoSerializer(many=True, read_only=True)
    tipo_empleado_display = serializers.CharField(source='get_tipo_empleado_display', read_only=True)
    cierre_periodo = serializers.CharField(source='cierre.periodo', read_only=True)
    cierre_cliente = serializers.CharField(source='cierre.cliente.nombre', read_only=True)
    
    # Estadísticas calculadas
    resumen_conceptos = serializers.SerializerMethodField()
    
    class Meta:
        model = EmpleadoNomina
        fields = [
            'id', 'rut_empleado', 'nombre_empleado',
            'tipo_empleado', 'tipo_empleado_display',
            'fecha_ingreso', 'fecha_finiquito', 'motivo_finiquito',
            'fecha_consolidacion', 'cierre_periodo', 'cierre_cliente',
            'conceptos', 'resumen_conceptos'
        ]
    
    def get_resumen_conceptos(self, obj):
        """Resumen agrupado por clasificación"""
        try:
            resumen = {}
            
            # Mapear conceptos a clasificaciones
            mapeos = MapeoConcepto.objects.filter(
                cliente=obj.cierre.cliente,
                activo=True
            ).select_related()
            
            conceptos_clasificados = {}
            for mapeo in mapeos:
                conceptos_clasificados[mapeo.concepto_original] = mapeo.clasificacion
            
            # Agrupar por clasificación
            for concepto_obj in obj.conceptos.all():
                clasificacion = conceptos_clasificados.get(concepto_obj.concepto, 'sin_clasificar')
                
                if clasificacion not in resumen:
                    resumen[clasificacion] = {
                        'total': 0,
                        'conceptos': []
                    }
                
                resumen[clasificacion]['total'] += float(concepto_obj.valor_numerico)
                resumen[clasificacion]['conceptos'].append({
                    'concepto': concepto_obj.concepto,
                    'valor': concepto_obj.valor,
                    'valor_numerico': float(concepto_obj.valor_numerico)
                })
            
            return resumen
        except Exception as e:
            return {'error': str(e)}

# ========== AUSENTISMOS ==========

class AusentismoSerializer(serializers.ModelSerializer):
    """Serializer para ausentismos"""
    
    cierre_periodo = serializers.CharField(source='cierre.periodo', read_only=True)
    dias_calculados = serializers.SerializerMethodField()
    
    class Meta:
        model = Ausentismo
        fields = [
            'id', 'rut_empleado', 'nombre_empleado', 'tipo_ausentismo',
            'fecha_inicio', 'fecha_fin', 'dias_ausentismo', 'dias_calculados',
            'observaciones', 'fecha_consolidacion', 'cierre_periodo'
        ]
    
    def get_dias_calculados(self, obj):
        """Calcular días entre fechas automáticamente"""
        if obj.fecha_inicio and obj.fecha_fin:
            return (obj.fecha_fin - obj.fecha_inicio).days + 1
        return obj.dias_ausentismo

# ========== INCIDENCIAS ==========

class InteraccionIncidenciaSerializer(serializers.ModelSerializer):
    """Serializer para interacciones de incidencias"""
    
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    tipo_interaccion_display = serializers.CharField(source='get_tipo_interaccion_display', read_only=True)
    
    class Meta:
        model = InteraccionIncidencia
        fields = [
            'id', 'usuario', 'usuario_nombre', 'fecha_interaccion',
            'mensaje', 'tipo_interaccion', 'tipo_interaccion_display'
        ]

class IncidenciaListSerializer(serializers.ModelSerializer):
    """Serializer para lista de incidencias"""
    
    tipo_incidencia_display = serializers.CharField(source='get_tipo_incidencia_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    analista_nombre = serializers.CharField(source='analista_asignado.get_full_name', read_only=True)
    supervisor_nombre = serializers.CharField(source='supervisor_asignado.get_full_name', read_only=True)
    cierre_periodo = serializers.CharField(source='cierre.periodo', read_only=True)
    
    class Meta:
        model = Incidencia
        fields = [
            'id', 'empleado_rut', 'empleado_nombre', 'concepto_afectado',
            'valor_periodo_actual', 'valor_periodo_anterior',
            'diferencia_absoluta', 'diferencia_porcentual',
            'tipo_incidencia', 'tipo_incidencia_display',
            'estado', 'estado_display',
            'fecha_deteccion', 'fecha_resolucion',
            'analista_asignado', 'analista_nombre',
            'supervisor_asignado', 'supervisor_nombre',
            'cierre_periodo'
        ]

class IncidenciaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de incidencia"""
    
    interacciones = InteraccionIncidenciaSerializer(many=True, read_only=True)
    tipo_incidencia_display = serializers.CharField(source='get_tipo_incidencia_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    analista_nombre = serializers.CharField(source='analista_asignado.get_full_name', read_only=True)
    supervisor_nombre = serializers.CharField(source='supervisor_asignado.get_full_name', read_only=True)
    usuario_resolucion_nombre = serializers.CharField(source='usuario_resolucion.get_full_name', read_only=True)
    
    class Meta:
        model = Incidencia
        fields = [
            'id', 'empleado_rut', 'empleado_nombre', 'concepto_afectado',
            'valor_periodo_actual', 'valor_periodo_anterior',
            'diferencia_absoluta', 'diferencia_porcentual',
            'tipo_incidencia', 'tipo_incidencia_display',
            'estado', 'estado_display',
            'fecha_deteccion', 'fecha_resolucion',
            'analista_asignado', 'analista_nombre',
            'supervisor_asignado', 'supervisor_nombre',
            'usuario_resolucion', 'usuario_resolucion_nombre',
            'observaciones_resolucion', 'interacciones'
        ]

# ========== KPIS Y OPTIMIZACIONES ==========

class KPINominaSerializer(serializers.ModelSerializer):
    """Serializer para KPIs de nómina"""
    
    tipo_kpi_display = serializers.CharField(source='get_tipo_kpi_display', read_only=True)
    cierre_periodo = serializers.CharField(source='cierre.periodo', read_only=True)
    cliente_nombre = serializers.CharField(source='cierre.cliente.nombre', read_only=True)
    tiene_comparacion = serializers.SerializerMethodField()
    
    class Meta:
        model = KPINomina
        fields = [
            'id', 'tipo_kpi', 'tipo_kpi_display', 'valor_numerico',
            'valor_comparativo_anterior', 'variacion_porcentual',
            'metadatos_kpi', 'fecha_calculo', 'hash_verificacion',
            'cierre_periodo', 'cliente_nombre', 'tiene_comparacion'
        ]
    
    def get_tiene_comparacion(self, obj):
        return obj.valor_comparativo_anterior is not None

# ========== MAPEOS Y CONFIGURACIÓN ==========

class MapeoConceptoSerializer(serializers.ModelSerializer):
    """Serializer para mapeos de conceptos"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    clasificacion_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MapeoConcepto
        fields = [
            'id', 'cliente', 'cliente_nombre', 'concepto_original',
            'concepto_normalizado', 'clasificacion', 'clasificacion_display',
            'activo', 'usuario_actualiza', 'fecha_actualizacion'
        ]
    
    def get_clasificacion_display(self, obj):
        # Buscar en CLASIFICACION_CHOICES
        from .models import CLASIFICACION_CHOICES
        for choice_value, choice_display in CLASIFICACION_CHOICES:
            if choice_value == obj.clasificacion:
                return choice_display
        return obj.clasificacion

# ========== LOGS Y AUDITORÍA ==========

class LogArchivoSerializer(serializers.ModelSerializer):
    """Serializer para logs de archivos"""
    
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    
    class Meta:
        model = LogArchivo
        fields = [
            'id', 'cliente', 'cliente_nombre', 'periodo', 'tipo_archivo',
            'nombre_archivo', 'usuario', 'usuario_nombre', 'fecha_subida',
            'procesado_exitoso', 'errores', 'resumen_procesamiento'
        ]
