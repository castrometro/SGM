# contabilidad/permissions.py
from rest_framework import permissions
from api.models import (Cliente, AsignacionClienteUsuario, Area)

class PuedeCrearCierreContabilidad(permissions.BasePermission):
    """
    Permite crear cierres de contabilidad SOLO a usuarios:
      - Que pertenecen al área 'Contabilidad'
      - Que están asignados al cliente correspondiente
    """

    def has_permission(self, request, view):
        # Solo chequea en creación
        if view.action != 'create':
            return True

        user = request.user

        # ¿El usuario está activo?
        if not user.is_active:
            return False

        # ¿El usuario pertenece al área Contabilidad?
        if not user.areas.filter(nombre__iexact='Contabilidad').exists():
            return False

        # El cliente debe estar en el body (por ID)
        cliente_id = request.data.get('cliente')
        if not cliente_id:
            return False

        # ¿El usuario está asignado a este cliente?
        if not AsignacionClienteUsuario.objects.filter(usuario=user, cliente_id=cliente_id).exists():
            return False

        return True



class SoloContabilidadAsignadoOGerente(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_active:
            return False
        if not user.areas.filter(nombre__iexact='Contabilidad').exists():
            return False
        return True  # Sigue evaluando has_object_permission()

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Gerente ve todo
        if user.tipo_usuario.lower() == 'gerente':
            return True

        # Si el objeto tiene cliente, validamos asignación
        cliente = getattr(obj, 'cliente', None)
        if not cliente:
            return False

        return AsignacionClienteUsuario.objects.filter(usuario=user, cliente=cliente).exists()
