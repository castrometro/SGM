# backend/nomina/audit/user_behavior.py
"""
Auditoría de Comportamiento de Usuarios

Analiza patrones de uso, detecta anomalías y comportamientos sospechosos
en el manejo de cierres de nómina.
"""

from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from ..models_activity_v2 import ActivityEvent
from ..models import CierreNomina

User = get_user_model()


class UserBehaviorAudit:
    """Audita comportamientos de usuario en cierres"""
    
    def analyze_user_activity_patterns(self, user_id, days=30):
        """
        Analiza patrones de actividad de un usuario específico
        
        Detecta:
        - Horarios de trabajo inusuales
        - Velocidad de procesamiento anómala
        - Patrones de errores
        - Omisión de pasos importantes
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        events = ActivityEvent.objects.filter(
            usuario_id=user_id,
            timestamp__gte=cutoff_date
        ).order_by('timestamp')
        
        if not events.exists():
            return {'error': 'No hay actividad del usuario en el período especificado'}
        
        # 1. Análisis de horarios
        work_hours = []
        weekend_work = []
        
        for event in events:
            hour = event.timestamp.hour
            day_of_week = event.timestamp.weekday()  # 0=Monday, 6=Sunday
            
            work_hours.append(hour)
            
            if day_of_week >= 5:  # Sábado o Domingo
                weekend_work.append(event)
        
        # Horarios más comunes
        from collections import Counter
        hour_distribution = Counter(work_hours)
        
        # 2. Análisis de velocidad de procesamiento
        processing_speeds = []
        file_uploads = events.filter(evento__in=['file_upload', 'file_select'])
        
        for i in range(len(file_uploads) - 1):
            current_upload = file_uploads[i]
            next_upload = file_uploads[i + 1]
            
            # Tiempo entre selección y subida
            time_diff = (next_upload.timestamp - current_upload.timestamp).total_seconds()
            if time_diff < 300:  # Menos de 5 minutos entre uploads
                processing_speeds.append(time_diff)
        
        # 3. Análisis de errores
        error_events = events.filter(resultado='error')
        error_rate = (error_events.count() / events.count()) * 100 if events.count() > 0 else 0
        
        # Tipos de errores más comunes
        error_patterns = error_events.values('seccion', 'evento').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 4. Análisis de sesiones
        sessions = events.values('session_id').distinct().count()
        avg_events_per_session = events.count() / sessions if sessions > 0 else 0
        
        # 5. Detección de anomalías
        anomalies = []
        
        # Trabajo fuera de horario laboral (antes 7am o después 7pm)
        off_hours_work = [h for h in work_hours if h < 7 or h > 19]
        if len(off_hours_work) > len(work_hours) * 0.3:  # Más del 30% fuera de horario
            anomalies.append({
                'type': 'off_hours_work',
                'severity': 'medium',
                'description': f'Trabajo fuera de horario laboral: {len(off_hours_work)} eventos'
            })
        
        # Procesamiento extremadamente rápido (posible bot/script)
        if processing_speeds and min(processing_speeds) < 10:  # Menos de 10 segundos
            anomalies.append({
                'type': 'very_fast_processing',
                'severity': 'high',
                'description': f'Procesamiento muy rápido detectado: {min(processing_speeds):.1f}s'
            })
        
        # Alta tasa de errores
        if error_rate > 15:  # Más del 15% de errores
            anomalies.append({
                'type': 'high_error_rate',
                'severity': 'medium',
                'description': f'Alta tasa de errores: {error_rate:.1f}%'
            })
        
        # Trabajo intensivo en fines de semana
        if len(weekend_work) > events.count() * 0.2:  # Más del 20% en fines de semana
            anomalies.append({
                'type': 'excessive_weekend_work',
                'severity': 'low',
                'description': f'Trabajo excesivo en fines de semana: {len(weekend_work)} eventos'
            })
        
        return {
            'user_id': user_id,
            'analysis_period_days': days,
            'total_events': events.count(),
            'total_sessions': sessions,
            'work_patterns': {
                'most_active_hours': dict(hour_distribution.most_common(5)),
                'weekend_work_events': len(weekend_work),
                'avg_events_per_session': round(avg_events_per_session, 2)
            },
            'performance_metrics': {
                'error_rate_percentage': round(error_rate, 2),
                'common_error_patterns': list(error_patterns),
                'avg_processing_speed_seconds': round(sum(processing_speeds) / len(processing_speeds), 2) if processing_speeds else None
            },
            'anomalies': anomalies,
            'risk_score': len([a for a in anomalies if a['severity'] == 'high']) * 3 +
                          len([a for a in anomalies if a['severity'] == 'medium']) * 2 +
                          len([a for a in anomalies if a['severity'] == 'low']) * 1
        }
    
    def detect_suspicious_activities(self, days=7):
        """
        Detecta actividades sospechosas en todos los usuarios
        
        Busca:
        - Múltiples usuarios desde la misma IP
        - Patrones de actividad idénticos
        - Actividad fuera de horarios normales
        - Velocidad de procesamiento inhumana
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        suspicious_activities = []
        
        # 1. Múltiples usuarios desde la misma IP
        ip_analysis = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            ip_address__isnull=False
        ).values('ip_address').annotate(
            user_count=Count('usuario_id', distinct=True),
            event_count=Count('id')
        ).filter(user_count__gt=3)  # Más de 3 usuarios desde la misma IP
        
        for ip_data in ip_analysis:
            users_from_ip = ActivityEvent.objects.filter(
                ip_address=ip_data['ip_address'],
                timestamp__gte=cutoff_date
            ).values_list('usuario_id', flat=True).distinct()
            
            suspicious_activities.append({
                'type': 'multiple_users_same_ip',
                'severity': 'medium',
                'details': {
                    'ip_address': ip_data['ip_address'],
                    'user_count': ip_data['user_count'],
                    'user_ids': list(users_from_ip),
                    'event_count': ip_data['event_count']
                }
            })
        
        # 2. Actividad nocturna masiva (2am - 5am)
        night_activity = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            timestamp__hour__gte=2,
            timestamp__hour__lt=5
        ).values('usuario_id').annotate(
            night_events=Count('id')
        ).filter(night_events__gt=20)  # Más de 20 eventos nocturnos
        
        for night_user in night_activity:
            suspicious_activities.append({
                'type': 'excessive_night_activity',
                'severity': 'medium',
                'details': {
                    'user_id': night_user['usuario_id'],
                    'night_events': night_user['night_events']
                }
            })
        
        # 3. Procesamiento extremadamente rápido (posibles bots)
        rapid_processing = ActivityEvent.objects.filter(
            timestamp__gte=cutoff_date,
            evento__in=['file_upload', 'classification_complete']
        ).values('usuario_id', 'session_id').annotate(
            event_count=Count('id')
        ).filter(event_count__gt=10)  # Más de 10 procesamientos por sesión
        
        for rapid_user in rapid_processing:
            # Verificar si los eventos fueron muy rápidos
            session_events = ActivityEvent.objects.filter(
                usuario_id=rapid_user['usuario_id'],
                session_id=rapid_user['session_id'],
                timestamp__gte=cutoff_date
            ).order_by('timestamp')
            
            if session_events.count() > 1:
                first_event = session_events.first()
                last_event = session_events.last()
                session_duration = (last_event.timestamp - first_event.timestamp).total_seconds()
                
                # Si procesó más de 10 archivos en menos de 5 minutos
                if session_duration < 300 and session_events.count() > 10:
                    suspicious_activities.append({
                        'type': 'robot_like_processing',
                        'severity': 'high',
                        'details': {
                            'user_id': rapid_user['usuario_id'],
                            'session_id': rapid_user['session_id'],
                            'events_in_session': session_events.count(),
                            'session_duration_seconds': session_duration,
                            'events_per_minute': round((session_events.count() / session_duration) * 60, 2)
                        }
                    })
        
        return {
            'analysis_period_days': days,
            'suspicious_activities': suspicious_activities,
            'total_suspicious_events': len(suspicious_activities),
            'high_risk_count': len([a for a in suspicious_activities if a['severity'] == 'high']),
            'medium_risk_count': len([a for a in suspicious_activities if a['severity'] == 'medium'])
        }
    
    def generate_user_compliance_report(self, user_id, cierre_ids):
        """
        Genera reporte de cumplimiento para un usuario específico
        en cierres determinados
        """
        events = ActivityEvent.objects.filter(
            usuario_id=user_id,
            cierre_id__in=cierre_ids
        )
        
        # Verificar cumplimiento de procedimientos obligatorios
        required_actions = [
            'file_upload',
            'classification_complete', 
            'verification_complete'
        ]
        
        compliance_score = 0
        compliance_details = {}
        
        for cierre_id in cierre_ids:
            cierre_events = events.filter(cierre_id=cierre_id)
            cierre_compliance = {}
            
            for action in required_actions:
                performed = cierre_events.filter(evento=action).exists()
                cierre_compliance[action] = performed
                if performed:
                    compliance_score += 1
            
            compliance_details[cierre_id] = cierre_compliance
        
        max_possible_score = len(cierre_ids) * len(required_actions)
        compliance_percentage = (compliance_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        return {
            'user_id': user_id,
            'cierres_analyzed': cierre_ids,
            'compliance_percentage': round(compliance_percentage, 2),
            'compliance_details': compliance_details,
            'missing_procedures': [
                action for action in required_actions
                if not events.filter(evento=action).exists()
            ]
        }