"""
Vista personalizada para el dashboard del admin de payroll.
Proporciona estadísticas y datos para la interfaz de administración moderna.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    PayrollClosure, PayrollFileUpload, ValidationRun, 
    DiscrepancyResult, ComparisonResult
)


@staff_member_required
def dashboard_stats(request):
    """
    API endpoint para obtener estadísticas del dashboard en tiempo real.
    """
    # Obtener fecha actual y rango de tiempo
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    
    # Estadísticas de cierres de nómina
    total_closures = PayrollClosure.objects.count()
    active_closures = PayrollClosure.objects.filter(status='OPEN').count()
    closed_closures = PayrollClosure.objects.filter(status='CLOSED').count()
    
    # Estadísticas de archivos
    total_files = PayrollFileUpload.objects.count()
    files_last_30_days = PayrollFileUpload.objects.filter(
        created_at__gte=last_30_days
    ).count()
    pending_files = PayrollFileUpload.objects.filter(
        status='PENDING'
    ).count()
    
    # Estadísticas de validaciones
    total_validations = ValidationRun.objects.count()
    recent_validations = ValidationRun.objects.filter(
        created_at__gte=last_30_days
    ).count()
    failed_validations = ValidationRun.objects.filter(
        status='FAILED'
    ).count()
    
    # Estadísticas de discrepancias
    total_discrepancies = DiscrepancyResult.objects.count()
    pending_discrepancies = DiscrepancyResult.objects.filter(
        status='PENDING'
    ).count()
    resolved_discrepancies = DiscrepancyResult.objects.filter(
        status='RESOLVED'
    ).count()
    
    # Estadísticas de cálculos (usar ComparisonResult como alternativa)
    total_calculations = ComparisonResult.objects.count()
    successful_calculations = ComparisonResult.objects.filter(
        status='COMPLETED'
    ).count()
    
    # Preparar datos de respuesta
    stats = {
        'payroll': {
            'total_closures': total_closures,
            'active_closures': active_closures,
            'closed_closures': closed_closures,
            'completion_rate': round(
                (closed_closures / total_closures * 100) if total_closures > 0 else 0, 1
            )
        },
        'files': {
            'total_files': total_files,
            'recent_files': files_last_30_days,
            'pending_files': pending_files,
            'processing_rate': round(
                ((total_files - pending_files) / total_files * 100) if total_files > 0 else 0, 1
            )
        },
        'validations': {
            'total_validations': total_validations,
            'recent_validations': recent_validations,
            'failed_validations': failed_validations,
            'success_rate': round(
                ((total_validations - failed_validations) / total_validations * 100) 
                if total_validations > 0 else 0, 1
            )
        },
        'discrepancies': {
            'total_discrepancies': total_discrepancies,
            'pending_discrepancies': pending_discrepancies,
            'resolved_discrepancies': resolved_discrepancies,
            'resolution_rate': round(
                (resolved_discrepancies / total_discrepancies * 100) 
                if total_discrepancies > 0 else 0, 1
            )
        },
        'calculations': {
            'total_calculations': total_calculations,
            'successful_calculations': successful_calculations,
            'success_rate': round(
                (successful_calculations / total_calculations * 100) 
                if total_calculations > 0 else 0, 1
            )
        },
        'system': {
            'last_updated': now.isoformat(),
            'active_users': request.user.is_authenticated,
            'system_status': 'operational'
        }
    }
    
    return JsonResponse(stats)


def custom_admin_index(request, extra_context=None):
    """
    Vista personalizada para el índice del admin.
    Reemplaza la vista por defecto con estadísticas del dashboard.
    """
    context = {
        'title': 'Dashboard SGM - Administración de Nóminas',
        'site_title': 'SGM Admin',
        'site_header': 'Sistema de Gestión de Nóminas',
        'user': request.user,
    }
    
    # Agregar contexto adicional si se proporciona
    if extra_context:
        context.update(extra_context)
    
    return render(request, 'admin/index.html', context)
