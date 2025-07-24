# Modelo ResolucionIncidencia SIMPLIFICADO
# Reemplazar la versión actual en models.py

def resolucion_upload_to(instance, filename):
    now = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"resoluciones/{instance.incidencia.cierre.cliente.id}/{instance.incidencia.cierre.periodo}/{now}_{filename}"


class ResolucionIncidencia(models.Model):
    """
    Modelo simplificado para el historial de resoluciones de incidencias.
    
    Flujo de estados:
    1. Analista crea 'justificacion'
    2. Supervisor puede crear 'consulta' (pregunta) o tomar decisión
    3. Si supervisor crea 'rechazo', analista puede responder con nueva 'justificacion'
    4. Si supervisor crea 'aprobacion', la incidencia se cierra
    """
    
    # Campos esenciales
    incidencia = models.ForeignKey(
        IncidenciaCierre, 
        on_delete=models.CASCADE, 
        related_name='resoluciones'
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField(help_text="Contenido del mensaje")
    adjunto = models.FileField(
        upload_to=resolucion_upload_to, 
        null=True, 
        blank=True,
        help_text="Archivo adjunto opcional"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Estado único y claro
    tipo_resolucion = models.CharField(
        max_length=20, 
        choices=[
            ('justificacion', 'Justificación del Analista'),
            ('consulta', 'Consulta del Supervisor'), 
            ('rechazo', 'Rechazo del Supervisor'),
            ('aprobacion', 'Aprobación del Supervisor'),
        ],
        help_text="Tipo de resolución que determina el estado de la conversación"
    )
    
    class Meta:
        ordering = ['fecha_creacion']  # Orden cronológico
        verbose_name = "Resolución de Incidencia"
        verbose_name_plural = "Resoluciones de Incidencias"
    
    def __str__(self):
        return f"{self.get_tipo_resolucion_display()} - {self.usuario.first_name} {self.usuario.last_name}"
    
    def es_mensaje_supervisor(self):
        """Determina si el mensaje fue creado por un supervisor"""
        return self.usuario.is_staff or self.usuario.is_superuser
    
    def es_decision_final(self):
        """Determina si esta resolución es una decisión final"""
        return self.tipo_resolucion in ['aprobacion', 'rechazo']
    
    def cierra_incidencia(self):
        """Determina si esta resolución cierra la incidencia"""
        return self.tipo_resolucion == 'aprobacion'
