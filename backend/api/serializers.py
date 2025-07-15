#backend/api/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Usuario, Industria, Area,
    Servicio, ServicioCliente,
    Cliente, Contrato, AsignacionClienteUsuario
)

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'nombre']
        read_only_fields = ['nombre']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = Usuario.USERNAME_FIELD
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Actualizar last_login manualmente
        from django.utils import timezone
        self.user.last_login = timezone.now()
        self.user.save(update_fields=['last_login'])
        
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    areas = AreaSerializer(many=True, read_only=True)  # <--- Aquí va el cambio
    supervisor = serializers.PrimaryKeyRelatedField(read_only=True)
    supervisor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo',
            'tipo_usuario', 'is_active', 'fecha_registro', 'cargo_bdo', 'areas',
            'supervisor', 'supervisor_nombre'
        ]
        read_only_fields = ['id', 'fecha_registro']

    def get_supervisor_nombre(self, obj):
        if obj.supervisor:
            return f"{obj.supervisor.nombre} {obj.supervisor.apellido}"
        return None


class IndustriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Industria
        fields = ['id_industria', 'nombre']
        read_only_fields = ['id_industria']




class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'area']
        read_only_fields = ['id']


class ServicioClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioCliente
        fields = ['id', 'servicio', 'cliente', 'valor', 'moneda']
        read_only_fields = ['id']


class ServicioClienteMiniSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source="servicio.nombre", read_only=True)
    area_nombre = serializers.CharField(source="servicio.area.nombre", read_only=True)

    class Meta:
        model = ServicioCliente
        fields = ['id', 'servicio_nombre', 'area_nombre', 'valor', 'moneda']


class ClienteSerializer(serializers.ModelSerializer):
    industria_nombre = serializers.SerializerMethodField()
    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre', 'rut',
            'fecha_registro', 'industria_nombre','bilingue'
        ]
        read_only_fields = ['id', 'fecha_registro']

    def get_industria_nombre(self, obj):
        return obj.industria.nombre if obj.industria else None


class ContratoSerializer(serializers.ModelSerializer):
    servicios_contratados = ServicioClienteMiniSerializer(many=True)
    class Meta:
        model = Contrato
        fields = [
            'id', 'servicios_contratados',
            'fecha_inicio', 'fecha_vencimiento', 'activo'
        ]
        read_only_fields = ['id', 'fecha_inicio']


class AsignacionClienteUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionClienteUsuario
        fields = [
            'id', 'cliente', 'usuario', 'fecha_asignacion'
        ]
        read_only_fields = ['id', 'fecha_asignacion']


class AnalistaPerformanceSerializer(serializers.ModelSerializer):
    clientes_asignados = serializers.IntegerField(read_only=True)
    cierres_contabilidad = serializers.IntegerField(read_only=True)
    cierres_nomina = serializers.IntegerField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo', 'cargo_bdo',
            'clientes_asignados', 'cierres_contabilidad', 'cierres_nomina'
        ]
        read_only_fields = fields


class AnalistaDetalladoSerializer(serializers.ModelSerializer):
    clientes_asignados = serializers.IntegerField(read_only=True)
    cierres_completados = serializers.IntegerField(read_only=True)
    cierres_contabilidad = serializers.IntegerField(read_only=True)
    cierres_nomina = serializers.IntegerField(read_only=True)
    eficiencia = serializers.FloatField(read_only=True)
    carga_trabajo = serializers.FloatField(read_only=True)
    areas = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo', 'cargo_bdo', 'fecha_registro',
            'clientes_asignados', 'cierres_completados', 'cierres_contabilidad', 
            'cierres_nomina', 'eficiencia', 'carga_trabajo', 'areas'
        ]
        read_only_fields = fields


class DashboardKpisSerializer(serializers.Serializer):
    total_analistas = serializers.IntegerField()
    clientes_activos = serializers.IntegerField()
    cierres_completados = serializers.IntegerField()
    eficiencia_promedio = serializers.FloatField()


class DashboardDataSerializer(serializers.Serializer):
    kpis = DashboardKpisSerializer()
    analistas_performance = AnalistaDetalladoSerializer(many=True)
    cierres_por_estado = serializers.DictField()
    clientes_por_industria = serializers.ListField()
    ingresos_por_servicio = serializers.ListField()
    tendencia_cierres = serializers.ListField()
    alerta_cierres_retrasados = serializers.DictField()


class ClienteSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'rut', 'industria']
        read_only_fields = fields


class EstadisticasAnalistaSerializer(serializers.Serializer):
    cierres_completados = serializers.IntegerField()
    eficiencia = serializers.FloatField()
    tiempo_promedio_dias = serializers.FloatField()
    cierres_por_estado = serializers.DictField()
    clientes = ClienteSimpleSerializer(many=True)


class UsuarioSupervisorSerializer(serializers.ModelSerializer):
    """Serializer para usuarios con tipo supervisor, incluyendo analistas supervisados"""
    areas = AreaSerializer(many=True, read_only=True)
    analistas_supervisados = serializers.SerializerMethodField()
    total_analistas = serializers.SerializerMethodField()
    total_clientes_supervisados = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo', 'cargo_bdo', 'areas',
            'analistas_supervisados', 'total_analistas', 'total_clientes_supervisados'
        ]
        read_only_fields = fields

    def get_analistas_supervisados(self, obj):
        analistas = obj.get_analistas_supervisados()
        return UsuarioAnalistaSerializer(analistas, many=True).data

    def get_total_analistas(self, obj):
        return obj.get_analistas_supervisados().count()

    def get_total_clientes_supervisados(self, obj):
        return len(obj.get_clientes_de_analistas_supervisados())


class UsuarioAnalistaSerializer(serializers.ModelSerializer):
    """Serializer simplificado para analistas supervisados"""
    areas = AreaSerializer(many=True, read_only=True)
    clientes_asignados = serializers.SerializerMethodField()
    total_clientes = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo', 'cargo_bdo', 'areas',
            'clientes_asignados', 'total_clientes'
        ]
        read_only_fields = fields

    def get_clientes_asignados(self, obj):
        asignaciones = obj.asignaciones.all()
        return ClienteSimpleSerializer([asig.cliente for asig in asignaciones], many=True).data

    def get_total_clientes(self, obj):
        return obj.asignaciones.count()


