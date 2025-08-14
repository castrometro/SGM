# ============================================================================
#                           CIERRE PAYROLL SERIALIZERS
# ============================================================================
# Serializers para la gestión de cierres de nómina
# Incluye diferentes niveles de detalle según el uso

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import CierrePayroll, Empleados_Cierre, Logs_Actividad
from api.models import Cliente

User = get_user_model()


class ClienteSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para cliente en cierres"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'rut']


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para usuario"""
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'nombre_completo']
    
    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class CierrePayrollListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de cierres (vista resumida)
    """
    cliente = ClienteSimpleSerializer(read_only=True)
    usuario_responsable = UsuarioSimpleSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    progreso_porcentaje = serializers.SerializerMethodField()
    total_empleados = serializers.SerializerMethodField()
    
    class Meta:
        model = CierrePayroll
        fields = [
            'id', 'cliente', 'periodo', 'tipo_cierre', 'estado', 'estado_display',
            'fecha_creacion', 'fecha_inicio_procesamiento', 'fecha_fin_procesamiento',
            'usuario_responsable', 'progreso_porcentaje', 'total_empleados'
        ]
    
    def get_progreso_porcentaje(self, obj):
        try:
            return obj.get_progreso_porcentaje()
        except:
            return 0
    
    def get_total_empleados(self, obj):
        return obj.empleados_cierre.count()


class CierrePayrollDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un cierre específico
    """
    cliente = ClienteSimpleSerializer(read_only=True)
    usuario_responsable = UsuarioSimpleSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_cierre_display = serializers.CharField(source='get_tipo_cierre_display', read_only=True)
    
    # Estadísticas
    estadisticas = serializers.SerializerMethodField()
    
    # Archivos
    archivos = serializers.SerializerMethodField()
    
    # Tiempo de procesamiento
    tiempo_procesamiento = serializers.SerializerMethodField()
    
    class Meta:
        model = CierrePayroll
        fields = [
            'id', 'cliente', 'periodo', 'tipo_cierre', 'tipo_cierre_display',
            'estado', 'estado_display', 'fecha_creacion', 'fecha_inicio_procesamiento',
            'fecha_fin_procesamiento', 'usuario_responsable', 'observaciones',
            'estadisticas', 'archivos', 'tiempo_procesamiento'
        ]
    
    def get_estadisticas(self, obj):
        empleados = obj.empleados_cierre.all()
        
        return {
            'empleados': {
                'total': empleados.count(),
                'procesados': empleados.filter(estado_procesamiento='procesado').count(),
                'pendientes': empleados.filter(estado_procesamiento='pendiente').count(),
                'con_errores': empleados.filter(estado_procesamiento='error').count(),
            },
            'items': {
                'total': obj.item_cierre.count(),
                'haberes': obj.item_cierre.filter(tipo_item='haberes').count(),
                'descuentos': obj.item_cierre.filter(tipo_item='descuentos').count(),
            },
            'incidencias': {
                'total': obj.incidencias_cierre.count(),
                'abiertas': obj.incidencias_cierre.filter(estado='abierta').count(),
                'criticas': obj.incidencias_cierre.filter(prioridad='critica').count(),
            },
            'progreso_porcentaje': obj.get_progreso_porcentaje() if hasattr(obj, 'get_progreso_porcentaje') else 0,
        }
    
    def get_archivos(self, obj):
        return {
            'excel_original': {
                'nombre': obj.archivo_excel_original.name if obj.archivo_excel_original else None,
                'url': obj.archivo_excel_original.url if obj.archivo_excel_original else None,
                'size': obj.archivo_excel_original.size if obj.archivo_excel_original else None,
            },
            'excel_procesado': {
                'nombre': obj.archivo_excel_procesado.name if obj.archivo_excel_procesado else None,
                'url': obj.archivo_excel_procesado.url if obj.archivo_excel_procesado else None,
                'size': obj.archivo_excel_procesado.size if obj.archivo_excel_procesado else None,
            },
            'pdf_comparacion': {
                'nombre': obj.archivo_pdf_comparacion.name if obj.archivo_pdf_comparacion else None,
                'url': obj.archivo_pdf_comparacion.url if obj.archivo_pdf_comparacion else None,
                'size': obj.archivo_pdf_comparacion.size if obj.archivo_pdf_comparacion else None,
            }
        }
    
    def get_tiempo_procesamiento(self, obj):
        if hasattr(obj, 'get_tiempo_procesamiento'):
            return obj.get_tiempo_procesamiento()
        
        if obj.fecha_inicio_procesamiento and obj.fecha_fin_procesamiento:
            delta = obj.fecha_fin_procesamiento - obj.fecha_inicio_procesamiento
            return {
                'total_seconds': delta.total_seconds(),
                'horas': delta.total_seconds() / 3600,
                'formatted': str(delta)
            }
        return None


class CierrePayrollCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos cierres
    """
    class Meta:
        model = CierrePayroll
        fields = ['cliente', 'periodo', 'tipo_cierre', 'observaciones']
    
    def validate_periodo(self, value):
        """Validar formato del periodo"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError(
                "El periodo debe tener formato YYYY-MM (ejemplo: 2025-08)"
            )
        return value
    
    def validate(self, data):
        """Validaciones generales"""
        # Verificar que no exista un cierre para el mismo cliente y periodo
        cliente = data.get('cliente')
        periodo = data.get('periodo')
        
        if cliente and periodo:
            existing = CierrePayroll.objects.filter(
                cliente=cliente,
                periodo=periodo
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    f"Ya existe un cierre para {cliente.nombre} en el periodo {periodo}"
                )
        
        return data
    
    def create(self, validated_data):
        # Asignar usuario responsable del request
        validated_data['usuario_responsable'] = self.context['request'].user
        validated_data['estado'] = 'pendiente'
        
        cierre = super().create(validated_data)
        
        # Crear log de creación
        Logs_Actividad.objects.create(
            cierre_payroll=cierre,
            usuario=self.context['request'].user,
            accion='creacion',
            descripcion=f'Cierre creado para {cierre.cliente.nombre} - {cierre.periodo}',
            resultado='exitoso'
        )
        
        return cierre


class CierrePayrollUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar cierres existentes
    """
    class Meta:
        model = CierrePayroll
        fields = ['periodo', 'tipo_cierre', 'estado', 'observaciones']
    
    def validate_estado(self, value):
        """Validar transiciones de estado válidas"""
        if self.instance:
            current_state = self.instance.estado
            
            # Definir transiciones válidas
            valid_transitions = {
                'pendiente': ['procesando', 'cancelado'],
                'procesando': ['completado', 'error', 'pausado'],
                'pausado': ['procesando', 'cancelado'],
                'completado': [],  # No se puede cambiar desde completado
                'error': ['pendiente', 'procesando'],
                'cancelado': ['pendiente']
            }
            
            if value not in valid_transitions.get(current_state, []):
                raise serializers.ValidationError(
                    f"No se puede cambiar el estado de '{current_state}' a '{value}'"
                )
        
        return value
    
    def update(self, instance, validated_data):
        # Capturar cambios para log
        cambios = []
        for field, new_value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != new_value:
                cambios.append(f"{field}: {old_value} → {new_value}")
        
        cierre = super().update(instance, validated_data)
        
        # Crear log de actualización si hay cambios
        if cambios and 'request' in self.context:
            Logs_Actividad.objects.create(
                cierre_payroll=cierre,
                usuario=self.context['request'].user,
                accion='actualizacion',
                descripcion=f'Cierre actualizado: {", ".join(cambios)}',
                resultado='exitoso'
            )
        
        return cierre


class CierrePayrollStatsSerializer(serializers.ModelSerializer):
    """
    Serializer para estadísticas de cierres
    """
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    total_empleados = serializers.SerializerMethodField()
    total_liquido = serializers.SerializerMethodField()
    incidencias_criticas = serializers.SerializerMethodField()
    tiempo_procesamiento_horas = serializers.SerializerMethodField()
    
    class Meta:
        model = CierrePayroll
        fields = [
            'id', 'cliente_nombre', 'periodo', 'estado',
            'fecha_creacion', 'total_empleados', 'total_liquido',
            'incidencias_criticas', 'tiempo_procesamiento_horas'
        ]
    
    def get_total_empleados(self, obj):
        return obj.empleados_cierre.count()
    
    def get_total_liquido(self, obj):
        from django.db.models import Sum
        total = obj.empleados_cierre.aggregate(
            total=Sum('liquido_pagar')
        )['total']
        return float(total) if total else 0.0
    
    def get_incidencias_criticas(self, obj):
        return obj.incidencias_cierre.filter(
            prioridad='critica',
            estado='abierta'
        ).count()
    
    def get_tiempo_procesamiento_horas(self, obj):
        if obj.fecha_inicio_procesamiento and obj.fecha_fin_procesamiento:
            delta = obj.fecha_fin_procesamiento - obj.fecha_inicio_procesamiento
            return round(delta.total_seconds() / 3600, 2)
        return None


# Serializer principal (alias para compatibilidad)
CierrePayrollSerializer = CierrePayrollDetailSerializer
