# nomina/permissions.py
from rest_framework import permissions
from api.models import AsignacionClienteUsuario


class SupervisorPuedeVerCierresNominaAnalistas(permissions.BasePermission):
    """
    Permite a supervisores ver cierres de nómina de clientes asignados a sus analistas supervisados
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_active:
            return False
        
        # Gerentes tienen acceso completo
        if user.tipo_usuario.lower() == 'gerente':
            return True
            
        # Solo usuarios de nómina pueden acceder  
        if not user.areas.filter(nombre__iexact='Nomina').exists():
            return False
        
        # Supervisores y analistas de nómina tienen acceso
        if user.tipo_usuario in ['supervisor', 'analista', 'senior']:
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Gerentes ven todo
        if user.tipo_usuario.lower() == 'gerente':
            return True
        
        # Supervisores solo ven cierres de clientes asignados a sus analistas supervisados
        if user.tipo_usuario.lower() == 'supervisor':
            cliente = getattr(obj, 'cliente', None)
            if not cliente:
                return False
            
            # Obtener analistas supervisados por este supervisor
            analistas_supervisados = user.get_analistas_supervisados()
            
            # Verificar si alguno de los analistas supervisados tiene asignado este cliente
            return AsignacionClienteUsuario.objects.filter(
                usuario__in=analistas_supervisados,
                cliente=cliente
            ).exists()
        
        return False


class AnalistaNominaAccess(permissions.BasePermission):
    """
    Permite acceso a analistas de nómina solo a sus clientes asignados
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_active:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Gerentes ven todo
        if user.tipo_usuario.lower() == 'gerente':
            return True
        
        # Supervisores ven cierres de sus analistas supervisados
        if user.tipo_usuario.lower() == 'supervisor':
            cliente = getattr(obj, 'cliente', None)
            if not cliente:
                return False
            
            analistas_supervisados = user.get_analistas_supervisados()
            return AsignacionClienteUsuario.objects.filter(
                usuario__in=analistas_supervisados,
                cliente=cliente
            ).exists()
        
        # Analistas solo ven sus clientes asignados
        if user.tipo_usuario in ['analista', 'senior']:
            cliente = getattr(obj, 'cliente', None)
            if not cliente:
                return False
            
            return AsignacionClienteUsuario.objects.filter(
                usuario=user,
                cliente=cliente
            ).exists()
        
        return False
