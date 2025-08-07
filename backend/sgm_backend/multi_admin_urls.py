# ============================================================================
#                           MULTI-ADMIN URLS CONFIGURATION
# ============================================================================
"""
Configuración de URLs para múltiples sitios admin:

URLs disponibles:
- /admin/              → Super Admin (solo superusuarios)
- /admin-nominas/      → Admin Nóminas (equipo RRHH)
- /admin-contabilidad/ → Admin Contabilidad (equipo Finanzas)  
- /admin-tareas/       → Admin Tareas (Project Managers)
"""

from django.urls import path, include
from django.contrib import admin
from sgm_backend.multi_admin import (
    payroll_admin_site,
    accounting_admin_site, 
    task_admin_site,
    super_admin_site
)

# ============================================================================
#                           URL PATTERNS PRINCIPALES
# ============================================================================

urlpatterns = [
    # Super Admin - Acceso completo al sistema
    path('admin/', super_admin_site.urls),
    
    # Admin Nóminas - Solo modelos de payroll
    path('admin-nominas/', payroll_admin_site.urls),
    
    # Admin Contabilidad - Solo modelos contables
    path('admin-contabilidad/', accounting_admin_site.urls),
    
    # Admin Tareas - Solo modelos de task manager
    path('admin-tareas/', task_admin_site.urls),
    
    # APIs REST
    path('api/', include('api.urls')),
    path('api/payroll/', include('payroll.urls')),
    path('api/contabilidad/', include('contabilidad.urls')),
    path('api/tasks/', include('task_manager.urls')),
]

# ============================================================================
#                           URLS ADICIONALES PARA CADA ADMIN
# ============================================================================

# URLs personalizadas para admin de nóminas
payroll_patterns = [
    path('reports/monthly/', 'payroll.views.monthly_report', name='payroll_monthly_report'),
    path('validate/', 'payroll.views.validate_files', name='payroll_validate'),
    path('export/discrepancies/', 'payroll.views.export_discrepancies', name='payroll_export'),
]

# URLs personalizadas para admin contable
accounting_patterns = [
    path('reports/balance/', 'contabilidad.views.balance_report', name='accounting_balance'),
    path('reconcile/', 'contabilidad.views.reconcile', name='accounting_reconcile'),
]

# URLs personalizadas para admin de tareas
task_patterns = [
    path('dashboard/', 'task_manager.views.dashboard', name='task_dashboard'),
    path('bulk-assign/', 'task_manager.views.bulk_assign', name='task_bulk_assign'),
]

# ============================================================================
#                           MIDDLEWARE DE SEGURIDAD
# ============================================================================

class AdminAccessMiddleware:
    """
    Middleware para controlar acceso a diferentes admin sites
    basado en grupos de usuarios
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar acceso antes de procesar la vista
        if request.path.startswith('/admin'):
            if not self.check_admin_access(request):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("No tienes permisos para acceder a esta sección")
        
        response = self.get_response(request)
        return response
    
    def check_admin_access(self, request):
        """Verificar permisos específicos por admin site"""
        user = request.user
        
        if not user.is_authenticated:
            return False
            
        # Super admin - solo superusuarios
        if request.path.startswith('/admin/'):
            return user.is_superuser
            
        # Admin nóminas - grupo 'nominas' o superuser
        if request.path.startswith('/admin-nominas/'):
            return user.is_superuser or user.groups.filter(name='nominas').exists()
            
        # Admin contabilidad - grupo 'contabilidad' o superuser  
        if request.path.startswith('/admin-contabilidad/'):
            return user.is_superuser or user.groups.filter(name='contabilidad').exists()
            
        # Admin tareas - grupo 'task_managers' o superuser
        if request.path.startswith('/admin-tareas/'):
            return user.is_superuser or user.groups.filter(name='task_managers').exists()
            
        return True

# ============================================================================
#                           CONFIGURACIÓN DE TEMPLATES
# ============================================================================

# Templates personalizados por admin site
ADMIN_TEMPLATES = {
    'payroll_admin': {
        'base_template': 'admin/payroll/base_site.html',
        'index_template': 'admin/payroll/index.html',
        'login_template': 'admin/payroll/login.html',
    },
    'accounting_admin': {
        'base_template': 'admin/accounting/base_site.html', 
        'index_template': 'admin/accounting/index.html',
        'login_template': 'admin/accounting/login.html',
    },
    'task_admin': {
        'base_template': 'admin/tasks/base_site.html',
        'index_template': 'admin/tasks/index.html', 
        'login_template': 'admin/tasks/login.html',
    },
    'super_admin': {
        'base_template': 'admin/super/base_site.html',
        'index_template': 'admin/super/index.html',
        'login_template': 'admin/super/login.html',
    }
}

# ============================================================================
#                           EJEMPLOS DE VISTAS PERSONALIZADAS
# ============================================================================

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse

@staff_member_required
def payroll_dashboard_api(request):
    """API endpoint para dashboard de nóminas"""
    from payroll.models import PayrollClosure, DiscrepancyResult
    
    data = {
        'active_closures': PayrollClosure.objects.filter(status='IN_PROGRESS').count(),
        'pending_discrepancies': DiscrepancyResult.objects.filter(is_resolved=False).count(),
        'recent_uploads': PayrollFileUpload.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
    }
    
    return JsonResponse(data)

@staff_member_required  
def accounting_reports(request):
    """Vista personalizada para reportes contables"""
    context = {
        'title': 'Reportes Contables',
        'available_reports': [
            {'name': 'Balance General', 'url': '/admin-contabilidad/reports/balance/'},
            {'name': 'Estado de Resultados', 'url': '/admin-contabilidad/reports/income/'},
            {'name': 'Flujo de Caja', 'url': '/admin-contabilidad/reports/cashflow/'},
        ]
    }
    return render(request, 'admin/accounting/reports.html', context)

# ============================================================================
#                           CONFIGURACIÓN DE PERMISOS AVANZADOS
# ============================================================================

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def setup_admin_permissions():
    """
    Configurar permisos específicos para cada admin site
    """
    
    # Permisos para admin de nóminas
    payroll_perms = [
        'view_payrollclosure',
        'add_payrollclosure', 
        'change_payrollclosure',
        'view_payrollfileupload',
        'add_payrollfileupload',
        'view_discrepancyresult',
        'change_discrepancyresult',
    ]
    
    # Permisos para admin contable
    accounting_perms = [
        'view_registrocontable',
        'add_registrocontable',
        'change_registrocontable',
        'delete_registrocontable',
    ]
    
    # Permisos para admin de tareas
    task_perms = [
        'view_task',
        'add_task',
        'change_task',
        'delete_task',
        'view_tasknotification',
    ]
    
    return {
        'nominas': payroll_perms,
        'contabilidad': accounting_perms, 
        'task_managers': task_perms,
    }
