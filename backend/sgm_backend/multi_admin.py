# ============================================================================
#                           MULTI-ADMIN SITES SETUP
# ============================================================================
"""
Sistema profesional con múltiples sitios admin independientes:

1. Admin Principal (/admin/) - Super administradores
2. Admin Nóminas (/admin-nominas/) - Equipo RRHH  
3. Admin Contabilidad (/admin-contabilidad/) - Equipo Finanzas
4. Admin Tareas (/admin-tareas/) - Project Managers
"""

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render

User = get_user_model()

# ============================================================================
#                           ADMIN SITES PERSONALIZADOS
# ============================================================================

class PayrollAdminSite(AdminSite):
    """
    Sitio admin dedicado para el equipo de Nóminas
    """
    site_header = "SGM - Gestión de Nóminas"
    site_title = "Admin Nóminas"
    index_title = "Panel de Control - Recursos Humanos"
    
    # Personalización avanzada
    site_url = "/nominas-dashboard/"  # Link personalizado
    enable_nav_sidebar = True
    
    def has_permission(self, request):
        """Solo usuarios del grupo 'nominas' pueden acceder"""
        return (
            request.user.is_active and 
            request.user.is_staff and
            (request.user.is_superuser or 
             request.user.groups.filter(name='nominas').exists())
        )
    
    def index(self, request, extra_context=None):
        """Dashboard personalizado para nóminas"""
        extra_context = extra_context or {}
        
        # Estadísticas específicas de nóminas
        from payroll.models import PayrollClosure, DiscrepancyResult
        
        extra_context.update({
            'total_closures': PayrollClosure.objects.count(),
            'active_closures': PayrollClosure.objects.filter(status='IN_PROGRESS').count(),
            'total_discrepancies': DiscrepancyResult.objects.filter(is_resolved=False).count(),
            'custom_actions': [
                {'name': 'Generar Reporte Mensual', 'url': '/admin-nominas/reports/monthly/'},
                {'name': 'Validar Archivos Pendientes', 'url': '/admin-nominas/validate/'},
                {'name': 'Exportar Discrepancias', 'url': '/admin-nominas/export/discrepancies/'},
            ]
        })
        
        return super().index(request, extra_context)


class AccountingAdminSite(AdminSite):
    """
    Sitio admin dedicado para el equipo de Contabilidad
    """
    site_header = "SGM - Gestión Contable"
    site_title = "Admin Contabilidad"
    index_title = "Panel de Control - Finanzas"
    
    def has_permission(self, request):
        """Solo usuarios del grupo 'contabilidad' pueden acceder"""
        return (
            request.user.is_active and 
            request.user.is_staff and
            (request.user.is_superuser or 
             request.user.groups.filter(name='contabilidad').exists())
        )


class TaskManagerAdminSite(AdminSite):
    """
    Sitio admin dedicado para Project Managers
    """
    site_header = "SGM - Gestión de Tareas"
    site_title = "Admin Tareas" 
    index_title = "Panel de Control - Project Management"
    
    def has_permission(self, request):
        """Solo usuarios del grupo 'task_managers' pueden acceder"""
        return (
            request.user.is_active and 
            request.user.is_staff and
            (request.user.is_superuser or 
             request.user.groups.filter(name='task_managers').exists())
        )


class SuperAdminSite(AdminSite):
    """
    Sitio admin principal para super administradores
    """
    site_header = "SGM - Administración Central"
    site_title = "Super Admin"
    index_title = "Panel de Control - Sistema Completo"
    
    def has_permission(self, request):
        """Solo superusuarios pueden acceder"""
        return request.user.is_active and request.user.is_superuser
    
    def index(self, request, extra_context=None):
        """Dashboard global del sistema"""
        extra_context = extra_context or {}
        
        # Estadísticas globales
        extra_context.update({
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'system_modules': [
                {'name': 'Nóminas', 'url': '/admin-nominas/', 'status': 'active'},
                {'name': 'Contabilidad', 'url': '/admin-contabilidad/', 'status': 'active'},
                {'name': 'Tareas', 'url': '/admin-tareas/', 'status': 'active'},
            ]
        })
        
        return super().index(request, extra_context)


# ============================================================================
#                           INSTANCIAS DE LOS SITIOS
# ============================================================================

# Crear instancias de cada sitio admin
payroll_admin_site = PayrollAdminSite(name='payroll_admin')
accounting_admin_site = AccountingAdminSite(name='accounting_admin')
task_admin_site = TaskManagerAdminSite(name='task_admin')
super_admin_site = SuperAdminSite(name='super_admin')

# ============================================================================
#                           REGISTRO DE MODELOS
# ============================================================================

# Registrar modelos en el sitio de nóminas
from payroll.models import (
    PayrollClosure, PayrollFileUpload, ValidationRun, 
    DiscrepancyResult, PayrollActivityLog, RedisCache
)
from payroll.admin import (
    PayrollClosureAdmin, PayrollFileUploadAdmin, ValidationRunAdmin,
    DiscrepancyResultAdmin, PayrollActivityLogAdmin, RedisCacheAdmin
)

payroll_admin_site.register(PayrollClosure, PayrollClosureAdmin)
payroll_admin_site.register(PayrollFileUpload, PayrollFileUploadAdmin)
payroll_admin_site.register(ValidationRun, ValidationRunAdmin)
payroll_admin_site.register(DiscrepancyResult, DiscrepancyResultAdmin)
payroll_admin_site.register(PayrollActivityLog, PayrollActivityLogAdmin)
payroll_admin_site.register(RedisCache, RedisCacheAdmin)

# Registrar modelos de contabilidad (ejemplo)
try:
    from contabilidad.models import RegistroContable
    from contabilidad.admin import RegistroContableAdmin
    accounting_admin_site.register(RegistroContable, RegistroContableAdmin)
except ImportError:
    pass

# Registrar modelos de task manager
try:
    from task_manager.models import Task, TaskNotification
    from task_manager.admin import TaskAdmin, TaskNotificationAdmin
    task_admin_site.register(Task, TaskAdmin)
    task_admin_site.register(TaskNotification, TaskNotificationAdmin)
except ImportError:
    pass

# Registrar TODOS los modelos en super admin
from django.contrib.auth.models import Group
from api.models import Usuario, Cliente

super_admin_site.register(Usuario)
super_admin_site.register(Cliente)
super_admin_site.register(Group)
super_admin_site.register(PayrollClosure, PayrollClosureAdmin)
# ... y todos los demás modelos
