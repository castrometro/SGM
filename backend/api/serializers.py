
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

class UsuarioSerializer(serializers.ModelSerializer):
    areas = AreaSerializer(many=True, read_only=True)  # <--- Aquí va el cambio

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo_bdo',
            'tipo_usuario', 'is_active', 'fecha_registro', 'cargo_bdo', 'areas',
        ]
        read_only_fields = ['id', 'fecha_registro']


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


