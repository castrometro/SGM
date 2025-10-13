# backend/nomina/models_activity_v2.py
"""
Sistema de Activity Logging V2 - Simplificado y Unificado

Principios:
- Un solo modelo para todas las actividades
- Campos mínimos pero suficientes
- Sin redundancia con otros sistemas
- Enfoque en patrones de uso, no micro-detalles
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class ActivityEvent(models.Model):
    """
    Evento de actividad unificado para el sistema SGM
    
    Captura SOLO información relevante para:
    - Analytics de UX
    - Debugging de problemas
    - Auditoría básica
    """
    
    # === IDENTIFICACIÓN ===
    cierre_id = models.PositiveIntegerField(db_index=True)
    modulo = models.CharField(max_length=20, choices=[
        ('nomina', 'Nómina'),
        ('contabilidad', 'Contabilidad'),
    ], db_index=True)
    
    # === CONTEXTO ===
    seccion = models.CharField(max_length=50, db_index=True)  # 'libro_remuneraciones', 'archivos_analista', etc.
    evento = models.CharField(max_length=50, db_index=True)   # 'file_upload', 'modal_open', 'state_change', etc.
    
    # === META-INFORMACIÓN ===
    usuario_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)  # Para agrupar sesiones
    
    # === DATOS FLEXIBLES ===
    datos = models.JSONField(default=dict, blank=True)  # Información específica del evento
    resultado = models.CharField(max_length=10, choices=[
        ('ok', 'Exitoso'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ], default='ok', db_index=True)
    
    # === METADATA ===
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'nomina_activity_event'
        indexes = [
            models.Index(fields=['cierre_id', 'modulo', 'timestamp']),
            models.Index(fields=['seccion', 'evento', 'timestamp']),
            models.Index(fields=['usuario_id', 'timestamp']),
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['timestamp']),  # Para limpieza automática
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.modulo}:{self.seccion}:{self.evento} - {self.timestamp.strftime('%H:%M:%S')}"

    @classmethod
    def log(cls, **kwargs):
        """
        Método estático para logging simplificado
        
        Uso:
            ActivityEvent.log(
                cierre_id=123,
                modulo='nomina',
                seccion='libro_remuneraciones',
                evento='file_upload',
                datos={'filename': 'libro.xlsx', 'size': 1024},
                usuario_id=user.id,
                session_id=request.session.session_key
            )
        """
        try:
            return cls.objects.create(**kwargs)
        except Exception as e:
            # Logging nunca debe fallar la operación principal
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error en activity logging: {e}")
            return None

    @classmethod
    def cleanup_old_events(cls, days_to_keep=30):
        """Limpia eventos antiguos para mantener la DB limpia"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        deleted_count, _ = cls.objects.filter(timestamp__lt=cutoff_date).delete()
        return deleted_count


# === FUNCIONES DE CONVENIENCIA ===

def log_activity(cierre_id, modulo, seccion, evento, **kwargs):
    """
    Función global simplificada para logging
    
    Args:
        cierre_id: ID del cierre
        modulo: 'nomina' o 'contabilidad'  
        seccion: Sección específica ('libro_remuneraciones', etc.)
        evento: Tipo de evento ('file_upload', 'modal_open', etc.)
        **kwargs: Datos adicionales (datos, usuario_id, session_id, etc.)
    
    Returns:
        ActivityEvent instance o None si falla
    """
    return ActivityEvent.log(
        cierre_id=cierre_id,
        modulo=modulo,
        seccion=seccion,
        evento=evento,
        **kwargs
    )


def log_user_activity(request, cierre_id, modulo, seccion, evento, datos=None):
    """
    Función específica para actividades de usuario con request
    Extrae automáticamente info del request
    """
    return log_activity(
        cierre_id=cierre_id,
        modulo=modulo,
        seccion=seccion,
        evento=evento,
        datos=datos or {},
        usuario_id=request.user.id if request.user.is_authenticated else None,
        session_id=request.session.session_key if hasattr(request, 'session') else None,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def _get_client_ip(request):
    """Extrae IP del cliente de forma segura"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip