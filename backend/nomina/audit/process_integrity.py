# backend/nomina/audit/process_integrity.py
"""
Auditoría de Integridad del Proceso de Cierre

Verifica que todos los pasos obligatorios se hayan completado
en el orden correcto y sin saltos de flujo.
"""

from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from ..models_activity_v2 import ActivityEvent
from ..models import CierreNomina


class ProcessIntegrityAudit:
    """Audita la integridad del flujo de cierre"""
    
    # Flujo esperado para un cierre completo
    EXPECTED_FLOW = [
        ('cierre_general', 'create_cierre'),
        ('libro_remuneraciones', 'file_upload'),
        ('libro_remuneraciones', 'classification_complete'),
        ('movimientos_mes', 'file_upload'),
        ('archivos_analista', 'ingresos_upload'),
        ('archivos_analista', 'finiquitos_upload'),
        ('archivos_analista', 'ausentismos_upload'),
        ('cierre_general', 'update_state'),  # A archivos_completos
        ('verificacion_datos', 'verification_complete'),
        ('cierre_general', 'consolidate_data'),
        ('incidencias', 'resolve_all'),
        ('cierre_general', 'finalize_cierre'),
    ]
    
    def audit_cierre_flow(self, cierre_id):
        """
        Audita si un cierre siguió el flujo esperado
        
        Returns:
            dict con resultado de auditoría
        """
        events = ActivityEvent.objects.filter(
            cierre_id=cierre_id,
            modulo='nomina'
        ).order_by('timestamp')
        
        # Mapear eventos actuales
        actual_flow = [(e.seccion, e.evento) for e in events]
        
        # Detectar pasos faltantes
        missing_steps = []
        for expected_step in self.EXPECTED_FLOW:
            if expected_step not in actual_flow:
                missing_steps.append(expected_step)
        
        # Detectar pasos fuera de orden
        out_of_order = []
        last_expected_idx = -1
        
        for actual_step in actual_flow:
            if actual_step in self.EXPECTED_FLOW:
                current_idx = self.EXPECTED_FLOW.index(actual_step)
                if current_idx < last_expected_idx:
                    out_of_order.append({
                        'step': actual_step,
                        'expected_position': current_idx,
                        'actual_position': len(out_of_order)
                    })
                last_expected_idx = max(last_expected_idx, current_idx)
        
        # Detectar pasos repetidos innecesariamente
        repeated_steps = []
        step_counts = {}
        for step in actual_flow:
            step_counts[step] = step_counts.get(step, 0) + 1
        
        for step, count in step_counts.items():
            if count > 1 and step not in [
                ('cierre_general', 'update_state'),  # Puede repetirse
                ('archivos_analista', 'file_reupload')  # Resubidas permitidas
            ]:
                repeated_steps.append({'step': step, 'count': count})
        
        # Calcular score de integridad
        total_expected = len(self.EXPECTED_FLOW)
        completed_steps = total_expected - len(missing_steps)
        integrity_score = (completed_steps / total_expected) * 100
        
        # Penalizar por problemas de orden
        if out_of_order:
            integrity_score -= len(out_of_order) * 5
        
        return {
            'cierre_id': cierre_id,
            'integrity_score': max(0, integrity_score),
            'missing_steps': missing_steps,
            'out_of_order_steps': out_of_order,
            'repeated_steps': repeated_steps,
            'total_events': len(actual_flow),
            'completion_percentage': (completed_steps / total_expected) * 100
        }
    
    def audit_multiple_cierres(self, cierre_ids):
        """Audita múltiples cierres y genera reporte consolidado"""
        results = []
        
        for cierre_id in cierre_ids:
            result = self.audit_cierre_flow(cierre_id)
            results.append(result)
        
        # Estadísticas consolidadas
        avg_score = sum(r['integrity_score'] for r in results) / len(results)
        problematic_cierres = [r for r in results if r['integrity_score'] < 80]
        
        return {
            'total_cierres_audited': len(results),
            'average_integrity_score': avg_score,
            'problematic_cierres': problematic_cierres,
            'individual_results': results
        }


# Ejemplo de uso:
def generate_monthly_integrity_report():
    """Genera reporte mensual de integridad"""
    # Obtener cierres del último mes
    last_month = timezone.now() - timedelta(days=30)
    cierres = CierreNomina.objects.filter(
        fecha_creacion__gte=last_month
    ).values_list('id', flat=True)
    
    auditor = ProcessIntegrityAudit()
    report = auditor.audit_multiple_cierres(list(cierres))
    
    return report