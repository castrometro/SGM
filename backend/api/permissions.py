# api/permissions.py
from rest_framework import permissions
from .models import AsignacionClienteUsuario
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsGerenteOrSelfOrReadOnly(BasePermission):
    """
    - GETs permitidos para:
      * superuser sobre todo
      * gerente sobre usuarios de sus áreas
      * supervisor/analista sobre sus propias asignaciones
    - POST/PUT/PATCH/D ELETE sólo para:
      * superuser sobre todo
      * gerente para reasignar dentro de su área
      * supervisor/analista sólo modifican sus propias asignaciones (o quizá sólo superuser/gerente)
    """
    def has_permission(self, request, view):
        # autenticación ya garantizada por IsAuthenticated
        if request.method in SAFE_METHODS:
            return True
        # sólo gerente o superuser pueden crear/editar
        return request.user.is_superuser or request.user.tipo_usuario == 'gerente'

    def has_object_permission(self, request, view, obj):
        # lectura
        if request.method in SAFE_METHODS:
            return True
        # escritura: superuser siempre, gerente si el usuario asignado está en su área
        if request.user.is_superuser:
            return True
        if request.user.tipo_usuario == 'gerente':
            return obj.usuario.areas.filter(pk__in=request.user.areas.values_list('pk',flat=True)).exists()
        return False


class IsAuthenticatedAndActive(permissions.IsAuthenticated):
    """
    Sólo usuarios autenticados y activos pueden acceder.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_active


class IsGerente(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.tipo_usuario == 'gerente'

class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.tipo_usuario == 'supervisor'

class IsAnalista(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.tipo_usuario == 'analista'

class ClienteAccess(permissions.BasePermission):
    """
    - Gerente: puede ver sólo los clientes de sus áreas.
    - Analista, Senior, Supervisor: sólo clientes asignados (como analista).
    """
    def has_permission(self, request, view):
        return True  # Autenticación y actividad ya verificadas

    def has_object_permission(self, request, view, cliente):
        user = request.user

        if user.tipo_usuario in ['Analista', 'Senior', 'Supervisor']:
            # Solo clientes asignados a ese usuario
            return AsignacionClienteUsuario.objects.filter(
                cliente=cliente, usuario=user
            ).exists()

        elif user.tipo_usuario == 'Gerente':
            # Puede ver clientes de sus áreas (ajusta según modelo)
            # Por ejemplo, si cliente.industria es el área:
            return cliente.industria in user.areas.all()
            # O, si Cliente tiene FK area:
            # return cliente.area in user.areas.all()

        # Superuser o permisos especiales
        return True


class ContratoAccess(permissions.BasePermission):
    """
    Mismo patrón que ClienteAccess para los contratos.
    """
    def has_object_permission(self, request, view, contrato):
        if request.user.tipo_usuario == 'analista':
            return AsignacionClienteUsuario.objects.filter(
                cliente=contrato.cliente, usuario=request.user
            ).exists()
        return True
