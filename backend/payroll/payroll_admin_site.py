# ============================================================================
#                           PAYROLL ADMIN SITE
# ============================================================================
"""
Admin site dedicado para el módulo de nóminas
Accesible en: /admin-nominas/
"""

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model

User = get_user_model()

class PayrollAdminSite(AdminSite):
    """
    Sitio admin personalizado para nóminas
    """
    site_header = "SGM - Gestión de Nóminas"
    site_title = "Admin Nóminas"
    index_title = "Panel de Control - Recursos Humanos"
    
    def has_permission(self, request):
        """Control de acceso para admin de nóminas"""
        return (
            request.user.is_active and 
            request.user.is_staff and
            (request.user.is_superuser or 
             request.user.groups.filter(name='nominas').exists())
        )
    
    def index(self, request, extra_context=None):
        """Dashboard personalizado"""
        extra_context = extra_context or {}
        
        # Agregar estadísticas específicas
        try:
            from payroll.models import PayrollClosure, DiscrepancyResult, PayrollFileUpload
            
            extra_context.update({
                'total_closures': PayrollClosure.objects.count(),
                'active_closures': PayrollClosure.objects.filter(status='IN_PROGRESS').count(),
                'pending_discrepancies': DiscrepancyResult.objects.filter(is_resolved=False).count(),
                'recent_uploads': PayrollFileUpload.objects.count(),
                'quick_actions': [
                    {'title': 'Nuevo Cierre', 'url': '/admin-nominas/payroll/payrollclosure/add/'},
                    {'title': 'Ver Discrepancias', 'url': '/admin-nominas/payroll/discrepancyresult/'},
                    {'title': 'Archivos Pendientes', 'url': '/admin-nominas/payroll/payrollfileupload/?status=UPLOADED'},
                ]
            })
        except Exception as e:
            extra_context['error'] = f"Error cargando estadísticas: {e}"
        
        return super().index(request, extra_context)

# Crear instancia del admin de nóminas
payroll_admin = PayrollAdminSite(name='payroll_admin')

# Registrar modelos de nóminas
from payroll.models import (
    PayrollClosure, PayrollFileUpload, ValidationRun, 
    DiscrepancyResult, PayrollActivityLog, RedisCache,
    ComparisonResult, ValidationRule, ParsedDataStorage, 
    AuditTrail, PerformanceLog
)

from payroll.admin import (
    PayrollClosureAdmin, PayrollFileUploadAdmin, ValidationRunAdmin,
    DiscrepancyResultAdmin, PayrollActivityLogAdmin, RedisCacheAdmin,
    ComparisonResultAdmin, ValidationRuleAdmin, ParsedDataStorageAdmin,
    AuditTrailAdmin, PerformanceLogAdmin
)

# Registrar todos los modelos en el admin de nóminas
payroll_admin.register(PayrollClosure, PayrollClosureAdmin)
payroll_admin.register(PayrollFileUpload, PayrollFileUploadAdmin)
payroll_admin.register(ValidationRun, ValidationRunAdmin)
payroll_admin.register(DiscrepancyResult, DiscrepancyResultAdmin)
payroll_admin.register(PayrollActivityLog, PayrollActivityLogAdmin)
payroll_admin.register(RedisCache, RedisCacheAdmin)
payroll_admin.register(ComparisonResult, ComparisonResultAdmin)
payroll_admin.register(ValidationRule, ValidationRuleAdmin)
payroll_admin.register(ParsedDataStorage, ParsedDataStorageAdmin)
payroll_admin.register(AuditTrail, AuditTrailAdmin)
payroll_admin.register(PerformanceLog, PerformanceLogAdmin)
