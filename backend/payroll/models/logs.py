from django.db import models
from django.conf import settings
from .cierre import CierrePayroll


class Logs_Comparacion(models.Model):
    """
    Registro de logs de todas las operaciones de comparación y procesamiento.
    Mantiene trazabilidad completa de las acciones realizadas en el cierre.
    """
    
    # Relación principal
    cierre_payroll = models.ForeignKey(
        CierrePayroll,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    # Información temporal
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento exacto del log"
    )
    
    # Usuario responsable
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Usuario que realizó la acción"
    )
    
    # Tipo de acción
    accion = models.CharField(
        max_length=50,
        choices=[
            ('creacion_cierre', 'Creación de Cierre'),
            ('upload_archivos', 'Upload de Archivos'),
            ('mapeo_columnas', 'Mapeo de Columnas'),
            ('comparacion_archivos', 'Comparación de Archivos'),
            ('consolidacion_datos', 'Consolidación de Datos'),
            ('analisis_variaciones', 'Análisis de Variaciones'),
            ('revision_incidencias', 'Revisión de Incidencias'),
            ('cambio_estado', 'Cambio de Estado'),
            ('aprobacion', 'Aprobación'),
            ('finalizacion', 'Finalización'),
            ('error_proceso', 'Error en Proceso'),
            ('rollback', 'Rollback de Operación')
        ],
        help_text="Tipo de acción registrada"
    )
    
    # Resultado de la operación
    resultado = models.CharField(
        max_length=20,
        choices=[
            ('exito', 'Éxito'),
            ('exito_con_alertas', 'Éxito con Alertas'),
            ('discrepancias', 'Discrepancias Encontradas'),
            ('incidencias', 'Incidencias Detectadas'),
            ('error', 'Error'),
            ('timeout', 'Timeout'),
            ('cancelado', 'Cancelado por Usuario')
        ],
        help_text="Resultado de la operación"
    )
    
    # Detalles específicos
    detalles = models.TextField(
        help_text="Información detallada de la operación (JSON)"
    )
    
    # Métricas de la operación
    duracion_segundos = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración de la operación en segundos"
    )
    registros_procesados = models.IntegerField(
        null=True,
        blank=True,
        help_text="Cantidad de registros procesados"
    )
    
    # Estados antes y después
    estado_anterior = models.CharField(
        max_length=50,
        blank=True,
        help_text="Estado del cierre antes de la operación"
    )
    estado_posterior = models.CharField(
        max_length=50,
        blank=True,
        help_text="Estado del cierre después de la operación"
    )
    
    # Información técnica
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se realizó la acción"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent del navegador"
    )
    
    # Referencia a task de Celery si aplica
    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID de la tarea de Celery asociada"
    )
    
    class Meta:
        db_table = 'payroll_logs_comparacion'
        verbose_name = 'Log de Comparación'
        verbose_name_plural = 'Logs de Comparación'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['cierre_payroll', 'timestamp']),
            models.Index(fields=['accion', 'resultado']),
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['celery_task_id']),
        ]
    
    def __str__(self):
        return f"{self.cierre_payroll} - {self.get_accion_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def log_accion(cls, cierre_payroll, usuario, accion, resultado, detalles, **kwargs):
        """
        Método de conveniencia para crear logs fácilmente.
        
        Args:
            cierre_payroll: Instancia del cierre
            usuario: Usuario que realiza la acción
            accion: Tipo de acción realizada
            resultado: Resultado de la operación
            detalles: Dict con detalles específicos
            **kwargs: Campos adicionales opcionales
        """
        import json
        
        # Convertir detalles a JSON si es un dict
        if isinstance(detalles, dict):
            detalles = json.dumps(detalles, ensure_ascii=False, indent=2)
        
        log_entry = cls.objects.create(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion=accion,
            resultado=resultado,
            detalles=detalles,
            **kwargs
        )
        
        return log_entry
    
    @classmethod
    def log_upload_archivos(cls, cierre_payroll, usuario, archivos_info, resultado='exito'):
        """Log específico para upload de archivos"""
        detalles = {
            'archivos_subidos': len(archivos_info),
            'archivos_detalle': archivos_info,
            'timestamp': cls._get_timestamp_str()
        }
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion='upload_archivos',
            resultado=resultado,
            detalles=detalles
        )
    
    @classmethod
    def log_comparacion(cls, cierre_payroll, usuario, discrepancias_count, duracion, resultado):
        """Log específico para comparación de archivos"""
        detalles = {
            'total_discrepancias': discrepancias_count,
            'duracion_proceso': f"{duracion} segundos",
            'estado_validacion': 'archivos_validados' if discrepancias_count == 0 else 'discrepancias_detectadas',
            'timestamp': cls._get_timestamp_str()
        }
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion='comparacion_archivos',
            resultado=resultado,
            detalles=detalles,
            duracion_segundos=duracion
        )
    
    @classmethod
    def log_consolidacion(cls, cierre_payroll, usuario, stats_consolidacion, duracion):
        """Log específico para consolidación de datos"""
        detalles = {
            'empleados_procesados': stats_consolidacion.get('empleados', 0),
            'items_procesados': stats_consolidacion.get('items', 0),
            'finiquitos_procesados': stats_consolidacion.get('finiquitos', 0),
            'ingresos_procesados': stats_consolidacion.get('ingresos', 0),
            'ausentismos_procesados': stats_consolidacion.get('ausentismos', 0),
            'duracion_proceso': f"{duracion} segundos",
            'timestamp': cls._get_timestamp_str()
        }
        
        total_registros = sum(stats_consolidacion.values())
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion='consolidacion_datos',
            resultado='exito',
            detalles=detalles,
            duracion_segundos=duracion,
            registros_procesados=total_registros
        )
    
    @classmethod
    def log_analisis_variaciones(cls, cierre_payroll, usuario, incidencias_count, duracion):
        """Log específico para análisis de variaciones"""
        detalles = {
            'total_incidencias_detectadas': incidencias_count,
            'algoritmo_usado': 'comparacion_porcentual',
            'tolerancia_aplicada': f"{cierre_payroll.porcentaje_tolerancia}%",
            'duracion_proceso': f"{duracion} segundos",
            'timestamp': cls._get_timestamp_str()
        }
        
        resultado = 'incidencias' if incidencias_count > 0 else 'exito'
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion='analisis_variaciones',
            resultado=resultado,
            detalles=detalles,
            duracion_segundos=duracion
        )
    
    @classmethod
    def log_cambio_estado(cls, cierre_payroll, usuario, estado_anterior, estado_nuevo, motivo=None):
        """Log específico para cambios de estado"""
        detalles = {
            'estado_anterior': estado_anterior,
            'estado_nuevo': estado_nuevo,
            'motivo': motivo or 'Progresión normal del flujo',
            'timestamp': cls._get_timestamp_str()
        }
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion='cambio_estado',
            resultado='exito',
            detalles=detalles,
            estado_anterior=estado_anterior,
            estado_posterior=estado_nuevo
        )
    
    @classmethod
    def log_error(cls, cierre_payroll, usuario, accion, error_message, stack_trace=None):
        """Log específico para errores"""
        detalles = {
            'error_message': str(error_message),
            'stack_trace': stack_trace,
            'timestamp': cls._get_timestamp_str()
        }
        
        return cls.log_accion(
            cierre_payroll=cierre_payroll,
            usuario=usuario,
            accion=accion,
            resultado='error',
            detalles=detalles
        )
    
    def get_detalles_dict(self):
        """Convierte detalles JSON a diccionario"""
        import json
        try:
            return json.loads(self.detalles) if self.detalles else {}
        except json.JSONDecodeError:
            return {'raw_data': self.detalles}
    
    def get_color_resultado(self):
        """Retorna color para el resultado en el frontend"""
        colors = {
            'exito': '#28a745',
            'exito_con_alertas': '#ffc107',
            'discrepancias': '#fd7e14',
            'incidencias': '#17a2b8',
            'error': '#dc3545',
            'timeout': '#6c757d',
            'cancelado': '#6c757d'
        }
        return colors.get(self.resultado, '#6c757d')
    
    def get_duracion_display(self):
        """Retorna duración formateada para mostrar"""
        if not self.duracion_segundos:
            return "N/A"
        
        if self.duracion_segundos < 60:
            return f"{self.duracion_segundos}s"
        
        minutos = self.duracion_segundos // 60
        segundos = self.duracion_segundos % 60
        return f"{minutos}m {segundos}s"
    
    @staticmethod
    def _get_timestamp_str():
        """Obtiene timestamp como string"""
        from django.utils import timezone
        return timezone.now().isoformat()
    
    def is_error_log(self):
        """Determina si es un log de error"""
        return self.resultado in ['error', 'timeout']
    
    def is_success_log(self):
        """Determina si es un log exitoso"""
        return self.resultado in ['exito', 'exito_con_alertas']
