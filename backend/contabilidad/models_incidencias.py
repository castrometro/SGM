# backend/contabilidad/models_incidencias.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import json

from .models import UploadLog, CierreContabilidad


class IncidenciaResumen(models.Model):
    """
    Modelo consolidado para agrupar incidencias por tipo y reducir ruido en BD
    """
    TIPOS_INCIDENCIA = [
        ('cuentas_sin_clasificacion', 'Cuentas sin clasificación'),
        ('cuentas_sin_nombre_ingles', 'Cuentas sin nombre en inglés'),
        ('tipos_doc_no_reconocidos', 'Códigos tipo documento no reconocidos'),
        ('movimientos_tipodoc_nulo', 'Movimientos con TIPODOC vacío'),
        ('cuentas_nuevas_detectadas', 'Cuentas nuevas detectadas'),
        ('errores_formato_fecha', 'Errores de formato en fechas'),
        ('errores_formato_monto', 'Errores de formato en montos'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    ESTADOS = [
        ('activa', 'Activa'),
        ('resuelta', 'Resuelta'),
        ('obsoleta', 'Obsoleta'),
    ]
    
    # Relaciones
    upload_log = models.ForeignKey(
        UploadLog, 
        on_delete=models.CASCADE,
        related_name='incidencias_resumen'
    )
    
    # Información del problema
    tipo_incidencia = models.CharField(max_length=50, choices=TIPOS_INCIDENCIA)
    codigo_problema = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Código específico del problema (ej: 'FAC', '1101', etc.)"
    )
    
    # Métricas consolidadas
    cantidad_afectada = models.IntegerField(
        help_text="Número total de elementos afectados"
    )
    elementos_afectados = models.JSONField(
        help_text="Lista de códigos/IDs afectados (cuentas, movimientos, etc.)"
    )
    detalle_muestra = models.JSONField(
        help_text="Primeros 5-10 ejemplos para debugging"
    )
    
    # Metadatos de resolución
    severidad = models.CharField(max_length=10, choices=SEVERIDAD_CHOICES)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activa')
    mensaje_usuario = models.TextField(
        help_text="Mensaje descriptivo para mostrar al usuario"
    )
    accion_sugerida = models.TextField(
        help_text="Acción específica recomendada para resolver"
    )
    
    # Estadísticas adicionales
    estadisticas_adicionales = models.JSONField(
        default=dict,
        help_text="Métricas adicionales (montos, fechas, etc.)"
    )
    
    # Fechas de seguimiento
    fecha_deteccion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['upload_log', 'tipo_incidencia']),
            models.Index(fields=['upload_log', 'estado']),
            models.Index(fields=['severidad', 'estado']),
            models.Index(fields=['fecha_deteccion']),
        ]
        unique_together = ['upload_log', 'tipo_incidencia', 'codigo_problema']
    
    def __str__(self):
        return f"{self.get_tipo_incidencia_display()} - {self.cantidad_afectada} afectados"
    
    def marcar_como_resuelta(self, usuario=None):
        """Marca la incidencia como resuelta"""
        self.estado = 'resuelta'
        self.fecha_resolucion = timezone.now()
        self.resuelto_por = usuario
        self.save(update_fields=['estado', 'fecha_resolucion', 'resuelto_por'])
    
    def obtener_resumen_ejecutivo(self):
        """Retorna un resumen ejecutivo para dashboards"""
        return {
            'tipo': self.get_tipo_incidencia_display(),
            'severidad': self.get_severidad_display(),
            'cantidad': self.cantidad_afectada,
            'codigo': self.codigo_problema,
            'accion': self.accion_sugerida,
            'impacto_monetario': self.estadisticas_adicionales.get('monto_total_afectado', 0),
            'elementos_criticos': len([e for e in self.elementos_afectados[:5]]),
        }


class HistorialReprocesamiento(models.Model):
    """
    Historial de reprocessamientos del libro mayor con tracking de incidencias
    """
    TRIGGERS = [
        ('user_manual', 'Reprocesamiento manual por usuario'),
        ('auto_after_upload', 'Automático después de subir tarjeta'),
        ('scheduled', 'Procesamiento programado'),
        ('api_trigger', 'Disparado por API externa'),
    ]
    
    # Relaciones
    upload_log = models.ForeignKey(
        UploadLog,
        on_delete=models.CASCADE,
        related_name='historial_reprocesamiento'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Información de la iteración
    iteracion = models.PositiveIntegerField(
        help_text="Número de iteración de reprocesamiento"
    )
    
    # Snapshots de estado
    incidencias_previas = models.JSONField(
        default=list,
        help_text="Snapshot de incidencias antes del reprocesamiento"
    )
    incidencias_previas_count = models.PositiveIntegerField(default=0)
    
    incidencias_nuevas = models.JSONField(
        default=list,
        help_text="Snapshot de incidencias después del reprocesamiento"
    )
    incidencias_nuevas_count = models.PositiveIntegerField(default=0)
    
    incidencias_resueltas = models.JSONField(
        default=list,
        help_text="Lista de incidencias que se resolvieron en esta iteración"
    )
    incidencias_resueltas_count = models.PositiveIntegerField(default=0)
    
    # Métricas de movimientos
    movimientos_corregidos = models.PositiveIntegerField(default=0)
    movimientos_total = models.PositiveIntegerField(default=0)
    
    # Metadatos del procesamiento
    tiempo_procesamiento = models.DurationField()
    trigger_reprocesamiento = models.CharField(max_length=20, choices=TRIGGERS)
    notas = models.TextField(blank=True)
    
    # Fechas
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['upload_log', 'iteracion']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['trigger_reprocesamiento']),
        ]
        unique_together = ['upload_log', 'iteracion']
    
    def __str__(self):
        return f"Iteración {self.iteracion} - {self.upload_log} - {self.incidencias_resueltas_count} resueltas"
    
    def calcular_efectividad(self):
        """Calcula la efectividad del reprocesamiento"""
        if self.incidencias_previas_count == 0:
            return 100.0
        return (self.incidencias_resueltas_count / self.incidencias_previas_count) * 100
    
    def obtener_mejoras(self):
        """Retorna métricas de mejora"""
        return {
            'incidencias_reducidas': self.incidencias_previas_count - self.incidencias_nuevas_count,
            'porcentaje_resolucion': self.calcular_efectividad(),
            'movimientos_corregidos_pct': (
                (self.movimientos_corregidos / self.movimientos_total) * 100 
                if self.movimientos_total > 0 else 0
            ),
            'tiempo_procesamiento_segundos': self.tiempo_procesamiento.total_seconds(),
        }


class LogResolucionIncidencia(models.Model):
    """
    Log detallado de acciones tomadas para resolver incidencias
    """
    TIPOS_ACCION = [
        ('subida_tarjeta', 'Subida de tarjeta relacionada'),
        ('creacion_manual', 'Creación manual de datos'),
        ('correccion_archivo', 'Corrección en archivo fuente'),
        ('configuracion_sistema', 'Cambio en configuración'),
        ('reprocesamiento', 'Reprocesamiento automático'),
    ]
    
    # Relaciones
    incidencia_resumen = models.ForeignKey(
        IncidenciaResumen,
        on_delete=models.CASCADE,
        related_name='logs_resolucion'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Información de la acción
    accion_realizada = models.CharField(max_length=50, choices=TIPOS_ACCION)
    elementos_resueltos = models.JSONField(
        default=list,
        help_text="Lista específica de elementos que se resolvieron"
    )
    cantidad_resuelta = models.PositiveIntegerField(default=0)
    
    # Referencias a otras entidades
    upload_log_relacionado = models.ForeignKey(
        UploadLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="UploadLog de tarjeta relacionada que ayudó a resolver"
    )
    
    # Metadatos
    observaciones = models.TextField(blank=True)
    datos_adicionales = models.JSONField(
        default=dict,
        help_text="Información adicional específica de la acción"
    )
    
    # Fechas
    fecha_accion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['incidencia_resumen', 'fecha_accion']),
            models.Index(fields=['accion_realizada']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"{self.get_accion_realizada_display()} - {self.cantidad_resuelta} elementos"
