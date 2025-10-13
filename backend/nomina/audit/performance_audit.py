# backend/nomina/audit/performance_audit.py
"""
Auditoría de Tiempos y Performance

Analiza tiempos de procesamiento, identifica cuellos de botella
y mide la eficiencia de los procesos de cierre.
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import statistics
from ..models_activity_v2 import ActivityEvent
from ..models import CierreNomina


class PerformanceAudit:
    """Audita performance y tiempos de procesamiento"""
    
    # Benchmarks esperados (en minutos)
    EXPECTED_BENCHMARKS = {
        'file_upload_to_classification': 15,  # Subir archivo hasta completar clasificación
        'classification_to_processing': 30,   # Clasificar hasta procesar
        'complete_archivo_section': 45,       # Completar toda la sección de archivos
        'verification_process': 20,           # Proceso de verificación
        'consolidation_process': 60,          # Proceso de consolidación
        'full_cierre_process': 240,          # Proceso completo de cierre (4 horas)
    }
    
    def analyze_processing_times(self, cierre_id):
        """
        Analiza tiempos de procesamiento para un cierre específico
        
        Mide duración de cada etapa y compara con benchmarks
        """
        events = ActivityEvent.objects.filter(
            cierre_id=cierre_id
        ).order_by('timestamp')
        
        if not events.exists():
            return {'error': 'No hay eventos para este cierre'}
        
        # Identificar hitos importantes
        milestones = {}
        
        # Inicio del cierre
        first_event = events.first()
        milestones['cierre_start'] = first_event.timestamp
        
        # Subida de archivos principales
        libro_upload = events.filter(
            seccion='libro_remuneraciones', 
            evento='file_upload'
        ).first()
        if libro_upload:
            milestones['libro_upload'] = libro_upload.timestamp
        
        # Clasificación completada
        classification_complete = events.filter(
            seccion='libro_remuneraciones',
            evento='classification_complete'
        ).first()
        if classification_complete:
            milestones['classification_complete'] = classification_complete.timestamp
        
        # Archivos del analista completados
        analista_complete = events.filter(
            seccion='archivos_analista',
            evento__in=['ausentismos_upload', 'finiquitos_upload']
        ).last()  # Último archivo subido
        if analista_complete:
            milestones['analista_complete'] = analista_complete.timestamp
        
        # Estado actualizado a archivos completos
        estado_archivos_completos = events.filter(
            seccion='cierre_general',
            evento='update_state',
            datos__new_state='archivos_completos'
        ).first()
        if estado_archivos_completos:
            milestones['archivos_completos'] = estado_archivos_completos.timestamp
        
        # Verificación completada
        verification_complete = events.filter(
            seccion='verificacion_datos',
            evento='verification_complete'
        ).first()
        if verification_complete:
            milestones['verification_complete'] = verification_complete.timestamp
        
        # Consolidación iniciada
        consolidation_start = events.filter(
            seccion='cierre_general',
            evento='consolidate_data'
        ).first()
        if consolidation_start:
            milestones['consolidation_start'] = consolidation_start.timestamp
        
        # Cierre finalizado
        cierre_finalized = events.filter(
            seccion='cierre_general',
            evento='finalize_cierre'
        ).first()
        if cierre_finalized:
            milestones['cierre_finalized'] = cierre_finalized.timestamp
        
        # Calcular duraciones
        durations = {}
        performance_issues = []
        
        # Tiempo de subida a clasificación
        if 'libro_upload' in milestones and 'classification_complete' in milestones:
            duration = (milestones['classification_complete'] - milestones['libro_upload']).total_seconds() / 60
            durations['upload_to_classification'] = duration
            
            if duration > self.EXPECTED_BENCHMARKS['file_upload_to_classification']:
                performance_issues.append({
                    'stage': 'upload_to_classification',
                    'actual_duration': duration,
                    'expected_duration': self.EXPECTED_BENCHMARKS['file_upload_to_classification'],
                    'delay_minutes': duration - self.EXPECTED_BENCHMARKS['file_upload_to_classification']
                })
        
        # Tiempo de sección completa de archivos
        if 'cierre_start' in milestones and 'archivos_completos' in milestones:
            duration = (milestones['archivos_completos'] - milestones['cierre_start']).total_seconds() / 60
            durations['complete_archivo_section'] = duration
            
            if duration > self.EXPECTED_BENCHMARKS['complete_archivo_section']:
                performance_issues.append({
                    'stage': 'complete_archivo_section',
                    'actual_duration': duration,
                    'expected_duration': self.EXPECTED_BENCHMARKS['complete_archivo_section'],
                    'delay_minutes': duration - self.EXPECTED_BENCHMARKS['complete_archivo_section']
                })
        
        # Tiempo de verificación
        if 'archivos_completos' in milestones and 'verification_complete' in milestones:
            duration = (milestones['verification_complete'] - milestones['archivos_completos']).total_seconds() / 60
            durations['verification_process'] = duration
            
            if duration > self.EXPECTED_BENCHMARKS['verification_process']:
                performance_issues.append({
                    'stage': 'verification_process',
                    'actual_duration': duration,
                    'expected_duration': self.EXPECTED_BENCHMARKS['verification_process'],
                    'delay_minutes': duration - self.EXPECTED_BENCHMARKS['verification_process']
                })
        
        # Tiempo total del cierre
        if 'cierre_start' in milestones and 'cierre_finalized' in milestones:
            duration = (milestones['cierre_finalized'] - milestones['cierre_start']).total_seconds() / 60
            durations['full_process'] = duration
            
            if duration > self.EXPECTED_BENCHMARKS['full_cierre_process']:
                performance_issues.append({
                    'stage': 'full_process',
                    'actual_duration': duration,
                    'expected_duration': self.EXPECTED_BENCHMARKS['full_cierre_process'],
                    'delay_minutes': duration - self.EXPECTED_BENCHMARKS['full_cierre_process']
                })
        
        # Calcular score de performance
        performance_score = 100
        for issue in performance_issues:
            # Penalizar según el porcentaje de retraso
            delay_percentage = (issue['delay_minutes'] / issue['expected_duration']) * 100
            penalty = min(delay_percentage / 2, 25)  # Máximo 25 puntos de penalización por etapa
            performance_score -= penalty
        
        performance_score = max(0, performance_score)
        
        # Identificar pausas largas (inactividad > 2 horas)
        long_pauses = []
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]
            
            pause_duration = (next_event.timestamp - current_event.timestamp).total_seconds() / 3600  # horas
            
            if pause_duration > 2:  # Pausa mayor a 2 horas
                long_pauses.append({
                    'start_event': {
                        'seccion': current_event.seccion,
                        'evento': current_event.evento,
                        'timestamp': current_event.timestamp.isoformat()
                    },
                    'end_event': {
                        'seccion': next_event.seccion,
                        'evento': next_event.evento,
                        'timestamp': next_event.timestamp.isoformat()
                    },
                    'pause_duration_hours': round(pause_duration, 2)
                })
        
        return {
            'cierre_id': cierre_id,
            'milestones': {k: v.isoformat() for k, v in milestones.items()},
            'durations_minutes': {k: round(v, 2) for k, v in durations.items()},
            'performance_score': round(performance_score, 2),
            'performance_issues': performance_issues,
            'long_pauses': long_pauses,
            'total_events': events.count(),
            'process_efficiency': {
                'events_per_hour': round(events.count() / (durations.get('full_process', 1) / 60), 2) if 'full_process' in durations else None,
                'avg_time_between_events': round(
                    (milestones.get('cierre_finalized', timezone.now()) - milestones['cierre_start']).total_seconds() / events.count() / 60, 2
                ) if events.count() > 0 else None
            }
        }
    
    def benchmark_comparison_report(self, cierre_ids):
        """
        Compara múltiples cierres contra benchmarks y genera reporte
        """
        results = []
        
        for cierre_id in cierre_ids:
            analysis = self.analyze_processing_times(cierre_id)
            if 'error' not in analysis:
                results.append(analysis)
        
        if not results:
            return {'error': 'No se pudieron analizar cierres'}
        
        # Estadísticas consolidadas
        all_scores = [r['performance_score'] for r in results]
        all_durations = {}
        
        # Recopilar duraciones por etapa
        for result in results:
            for stage, duration in result['durations_minutes'].items():
                if stage not in all_durations:
                    all_durations[stage] = []
                all_durations[stage].append(duration)
        
        # Calcular estadísticas por etapa
        stage_stats = {}
        for stage, durations in all_durations.items():
            stage_stats[stage] = {
                'avg_duration': round(statistics.mean(durations), 2),
                'median_duration': round(statistics.median(durations), 2),
                'min_duration': round(min(durations), 2),
                'max_duration': round(max(durations), 2),
                'std_deviation': round(statistics.stdev(durations), 2) if len(durations) > 1 else 0,
                'benchmark': self.EXPECTED_BENCHMARKS.get(stage, 'N/A'),
                'performance_vs_benchmark': round(
                    (statistics.mean(durations) / self.EXPECTED_BENCHMARKS.get(stage, statistics.mean(durations))) * 100, 2
                ) if stage in self.EXPECTED_BENCHMARKS else 100
            }
        
        # Identificar cierres problemáticos
        problematic_cierres = [r for r in results if r['performance_score'] < 70]
        top_performers = [r for r in results if r['performance_score'] > 90]
        
        return {
            'analysis_summary': {
                'total_cierres_analyzed': len(results),
                'avg_performance_score': round(statistics.mean(all_scores), 2),
                'median_performance_score': round(statistics.median(all_scores), 2),
                'problematic_cierres_count': len(problematic_cierres),
                'top_performers_count': len(top_performers)
            },
            'stage_statistics': stage_stats,
            'problematic_cierres': problematic_cierres,
            'top_performers': top_performers,
            'individual_results': results
        }
    
    def identify_bottlenecks(self, days=30):
        """
        Identifica cuellos de botella comunes en el proceso
        basado en actividad de los últimos días
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Analizar eventos que toman más tiempo del esperado
        bottlenecks = []
        
        # 1. Archivos que tardan mucho en procesarse
        slow_processing = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            evento='file_upload'
        ).values('cierre_id', 'seccion').annotate(
            upload_count=Count('id')
        )
        
        for upload in slow_processing:
            # Verificar si hay classification_complete para este cierre/sección
            classification_events = ActivityEvent.objects.filter(
                cierre_id=upload['cierre_id'],
                seccion=upload['seccion'],
                evento='classification_complete',
                timestamp__gte=cutoff_date
            )
            
            upload_events = ActivityEvent.objects.filter(
                cierre_id=upload['cierre_id'],
                seccion=upload['seccion'],
                evento='file_upload',
                timestamp__gte=cutoff_date
            ).order_by('timestamp')
            
            if upload_events.exists() and classification_events.exists():
                first_upload = upload_events.first()
                classification = classification_events.first()
                
                duration = (classification.timestamp - first_upload.timestamp).total_seconds() / 60
                expected = self.EXPECTED_BENCHMARKS.get('file_upload_to_classification', 15)
                
                if duration > expected * 1.5:  # 50% más lento que lo esperado
                    bottlenecks.append({
                        'type': 'slow_file_processing',
                        'cierre_id': upload['cierre_id'],
                        'seccion': upload['seccion'],
                        'actual_duration': round(duration, 2),
                        'expected_duration': expected,
                        'delay_factor': round(duration / expected, 2)
                    })
        
        # 2. Usuarios que consistentemente son lentos
        slow_users = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            usuario_id__isnull=False
        ).values('usuario_id').annotate(
            avg_session_length=Avg('timestamp'),  # Aproximación
            total_events=Count('id')
        ).filter(total_events__gt=50)  # Solo usuarios con actividad significativa
        
        # 3. Secciones que acumulan más errores
        error_prone_sections = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            resultado='error'
        ).values('seccion', 'evento').annotate(
            error_count=Count('id')
        ).order_by('-error_count')[:10]
        
        return {
            'analysis_period_days': days,
            'bottlenecks_found': len(bottlenecks),
            'processing_bottlenecks': bottlenecks,
            'error_prone_sections': list(error_prone_sections),
            'recommendations': self._generate_bottleneck_recommendations(bottlenecks, error_prone_sections)
        }
    
    def _generate_bottleneck_recommendations(self, bottlenecks, error_sections):
        """Genera recomendaciones basadas en cuellos de botella identificados"""
        recommendations = []
        
        # Recomendaciones por cuellos de botella de procesamiento
        slow_sections = {}
        for bottleneck in bottlenecks:
            section = bottleneck['seccion']
            if section not in slow_sections:
                slow_sections[section] = []
            slow_sections[section].append(bottleneck['delay_factor'])
        
        for section, delays in slow_sections.items():
            avg_delay = sum(delays) / len(delays)
            if avg_delay > 2:
                recommendations.append({
                    'priority': 'high',
                    'area': section,
                    'issue': 'Procesamiento consistentemente lento',
                    'recommendation': f'Revisar infraestructura de procesamiento para {section}. Considerar optimización de algoritmos de clasificación.',
                    'expected_improvement': f'Reducir tiempo de procesamiento en {round((avg_delay - 1) * 100, 1)}%'
                })
        
        # Recomendaciones por secciones con errores
        for error_section in error_sections[:3]:  # Top 3 secciones con errores
            if error_section['error_count'] > 10:
                recommendations.append({
                    'priority': 'medium',
                    'area': error_section['seccion'],
                    'issue': f'Alta frecuencia de errores en {error_section["evento"]}',
                    'recommendation': f'Implementar validaciones adicionales y mejorar documentación de usuario para {error_section["seccion"]}',
                    'expected_improvement': 'Reducir errores en 30-50%'
                })
        
        return recommendations