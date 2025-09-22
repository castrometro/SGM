"""
🎯 PROPUESTA: MODELO SIMPLIFICADO DE INCIDENCIAS
Solo para comparación de totales por concepto (sin empleados individuales)

Este modelo reemplazaría al actual IncidenciaCierre para el nuevo sistema
enfocado únicamente en variaciones de totales por ítem entre períodos.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

User = get_user_model()

class TipoIncidenciaSimplificado(models.TextChoices):
    """Tipos de incidencia simplificados - solo totales por concepto"""
    # Únicamente variaciones de conceptos (agregados)
    VARIACION_TOTAL_CONCEPTO = 'variacion_total_concepto', 'Variación en Total de Concepto (≥30%)'
    CONCEPTO_NUEVO_PERIODO = 'concepto_nuevo_periodo', 'Concepto Nuevo en Período'
    CONCEPTO_ELIMINADO_PERIODO = 'concepto_eliminado_periodo', 'Concepto Eliminado del Período'

class EstadoIncidenciaSimplificado(models.TextChoices):
    """Estados de resolución simplificados"""
    PENDIENTE = 'pendiente', 'Pendiente de Análisis'
    JUSTIFICADA = 'justificada', 'Justificada por Analista'
    APROBADA = 'aprobada', 'Aprobada por Supervisor'
    RECHAZADA = 'rechazada', 'Rechazada por Supervisor'

class PrioridadIncidencia(models.TextChoices):
    """Prioridad basada en impacto monetario y porcentaje de variación"""
    BAJA = 'baja', 'Baja'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'
    CRITICA = 'critica', 'Crítica'

class IncidenciaCierreSimplificada(models.Model):
    """
    🎯 MODELO SIMPLIFICADO DE INCIDENCIAS - SOLO TOTALES POR CONCEPTO
    
    Enfoque: Comparación período actual vs anterior únicamente a nivel de totales
    por concepto (suma de todos los empleados por cada concepto).
    
    Sin empleados individuales, sin RUTs, sin comparaciones elemento a elemento.
    """
    
    # === RELACIÓN BÁSICA ===
    cierre = models.ForeignKey('CierreNomina', on_delete=models.CASCADE, related_name='incidencias_simplificadas')
    
    # === TIPO Y CLASIFICACIÓN ===
    tipo_incidencia = models.CharField(
        max_length=40, 
        choices=TipoIncidenciaSimplificado.choices,
        help_text="Tipo de incidencia detectada"
    )
    
    # === CONCEPTO AFECTADO ===
    concepto_afectado = models.CharField(
        max_length=200, 
        db_index=True,
        help_text="Nombre del concepto que presenta la incidencia"
    )
    
    clasificacion_concepto = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        help_text="Clasificación del concepto (haberes_imponibles, descuentos_legales, etc.)"
    )
    
    # === DATOS DE VARIACIÓN ===
    monto_actual = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Total del concepto en el período actual"
    )
    
    monto_anterior = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Total del concepto en el período anterior"
    )
    
    delta_absoluto = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Diferencia absoluta (actual - anterior)"
    )
    
    delta_porcentual = models.DecimalField(
        max_digits=8, 
        decimal_places=4,
        help_text="Variación porcentual ((actual - anterior) / anterior * 100)"
    )
    
    empleados_afectados = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad de empleados que tienen este concepto en el período actual"
    )
    
    # === METADATOS DE DETECCIÓN ===
    descripcion = models.TextField(
        help_text="Descripción automática de la incidencia"
    )
    
    fecha_detectada = models.DateTimeField(
        auto_now_add=True,
        help_text="Cuándo fue detectada la incidencia"
    )
    
    umbral_utilizado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00,
        help_text="Umbral de variación porcentual utilizado para detectar la incidencia"
    )
    
    # === RESOLUCIÓN COLABORATIVA ===
    estado = models.CharField(
        max_length=20, 
        choices=EstadoIncidenciaSimplificado.choices, 
        default='pendiente'
    )
    
    prioridad = models.CharField(
        max_length=10, 
        choices=PrioridadIncidencia.choices, 
        default='media'
    )
    
    # === USUARIOS Y FECHAS DE RESOLUCIÓN ===
    analista_asignado = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='incidencias_asignadas_simplificadas'
    )
    
    justificacion_analista = models.TextField(
        blank=True,
        help_text="Justificación proporcionada por el analista"
    )
    
    fecha_justificacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Cuándo el analista justificó la incidencia"
    )
    
    supervisor_revisor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='incidencias_supervisadas_simplificadas'
    )
    
    comentario_supervisor = models.TextField(
        blank=True,
        help_text="Comentario del supervisor (aprobación/rechazo)"
    )
    
    fecha_resolucion_final = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Cuándo el supervisor resolvió definitivamente la incidencia"
    )
    
    # === METADATOS ADICIONALES ===
    datos_contexto = models.JSONField(
        default=dict,
        help_text="Datos adicionales de contexto (desglose por empleados, etc.)"
    )
    
    # === VERSIONADO Y TRAZABILIDAD ===
    version_datos_cierre = models.PositiveIntegerField(
        default=1,
        help_text="Versión de los datos del cierre cuando se detectó"
    )
    
    hash_deteccion = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Hash único para evitar duplicados en re-detecciones"
    )
    
    class Meta:
        db_table = 'nomina_incidencia_simplificada'
        
        constraints = [
            # Evitar duplicados por concepto en el mismo cierre
            models.UniqueConstraint(
                fields=['cierre', 'concepto_afectado', 'tipo_incidencia'],
                name='unique_incidencia_por_concepto_cierre'
            ),
        ]
        
        indexes = [
            models.Index(fields=['cierre', 'estado']),
            models.Index(fields=['cierre', 'tipo_incidencia']),
            models.Index(fields=['estado', 'prioridad']),
            models.Index(fields=['concepto_afectado']),
            models.Index(fields=['fecha_detectada']),
            models.Index(fields=['analista_asignado', 'estado']),
            models.Index(fields=['supervisor_revisor', 'estado']),
            models.Index(fields=['hash_deteccion']),
        ]
        
        ordering = ['-fecha_detectada', '-delta_absoluto']
    
    def __str__(self):
        signo = '+' if self.delta_absoluto >= 0 else ''
        return f"{self.concepto_afectado}: {signo}{self.delta_porcentual:.1f}% (${self.delta_absoluto:,.0f})"
    
    def save(self, *args, **kwargs):
        """Auto-cálculo de campos derivados antes de guardar"""
        
        # Calcular prioridad automáticamente
        if not self.prioridad or self.prioridad == 'media':
            self.prioridad = self.calcular_prioridad_automatica()
        
        # Generar descripción automática si no existe
        if not self.descripcion:
            self.descripcion = self.generar_descripcion_automatica()
        
        # Generar hash de detección para evitar duplicados
        if not self.hash_deteccion:
            self.hash_deteccion = self.generar_hash_deteccion()
        
        super().save(*args, **kwargs)
    
    def calcular_prioridad_automatica(self):
        """Calcula prioridad basada en impacto monetario y porcentaje"""
        impacto_abs = abs(self.delta_absoluto)
        variacion_abs = abs(self.delta_porcentual)
        
        # Criterios de prioridad
        if impacto_abs >= 1000000 or variacion_abs >= 100:  # $1M+ o 100%+
            return 'critica'
        elif impacto_abs >= 500000 or variacion_abs >= 75:   # $500K+ o 75%+
            return 'alta'
        elif impacto_abs >= 100000 or variacion_abs >= 50:   # $100K+ o 50%+
            return 'media'
        else:
            return 'baja'
    
    def generar_descripcion_automatica(self):
        """Genera descripción legible de la incidencia"""
        if self.tipo_incidencia == TipoIncidenciaSimplificado.VARIACION_TOTAL_CONCEPTO:
            direccion = "aumento" if self.delta_absoluto > 0 else "disminución"
            return (f"Variación del {self.delta_porcentual:.1f}% en {self.concepto_afectado} "
                   f"({direccion} de ${abs(self.delta_absoluto):,.0f})")
        elif self.tipo_incidencia == TipoIncidenciaSimplificado.CONCEPTO_NUEVO_PERIODO:
            return f"Concepto nuevo '{self.concepto_afectado}' con total ${self.monto_actual:,.0f}"
        elif self.tipo_incidencia == TipoIncidenciaSimplificado.CONCEPTO_ELIMINADO_PERIODO:
            return f"Concepto '{self.concepto_afectado}' eliminado (antes ${self.monto_anterior:,.0f})"
        return f"Incidencia en {self.concepto_afectado}"
    
    def generar_hash_deteccion(self):
        """Genera hash único para esta detección específica"""
        import hashlib
        
        contenido = f"{self.cierre.id}|{self.concepto_afectado}|{self.tipo_incidencia}|{self.monto_actual}|{self.monto_anterior}"
        return hashlib.sha256(contenido.encode()).hexdigest()[:32]
    
    def puede_justificar(self, usuario):
        """Verifica si un usuario puede justificar esta incidencia"""
        return (
            self.estado == 'pendiente' and
            (not self.analista_asignado or self.analista_asignado == usuario) and
            hasattr(usuario, 'tipo_usuario') and usuario.tipo_usuario in ['analista', 'gerente']
        )
    
    def puede_aprobar_rechazar(self, usuario):
        """Verifica si un usuario puede aprobar/rechazar esta incidencia"""
        return (
            self.estado == 'justificada' and
            hasattr(usuario, 'tipo_usuario') and usuario.tipo_usuario in ['supervisor', 'gerente']
        )
    
    def justificar(self, usuario, justificacion):
        """Marca la incidencia como justificada por el analista"""
        if not self.puede_justificar(usuario):
            raise ValueError("Usuario no puede justificar esta incidencia")
        
        self.estado = 'justificada'
        self.analista_asignado = usuario
        self.justificacion_analista = justificacion
        self.fecha_justificacion = timezone.now()
        self.save(update_fields=['estado', 'analista_asignado', 'justificacion_analista', 'fecha_justificacion'])
    
    def aprobar(self, supervisor, comentario=""):
        """Aprueba la incidencia"""
        if not self.puede_aprobar_rechazar(supervisor):
            raise ValueError("Usuario no puede aprobar esta incidencia")
        
        self.estado = 'aprobada'
        self.supervisor_revisor = supervisor
        self.comentario_supervisor = comentario
        self.fecha_resolucion_final = timezone.now()
        self.save(update_fields=['estado', 'supervisor_revisor', 'comentario_supervisor', 'fecha_resolucion_final'])
    
    def rechazar(self, supervisor, comentario):
        """Rechaza la incidencia (vuelve a pendiente)"""
        if not self.puede_aprobar_rechazar(supervisor):
            raise ValueError("Usuario no puede rechazar esta incidencia")
        
        self.estado = 'rechazada'
        self.supervisor_revisor = supervisor
        self.comentario_supervisor = comentario
        self.fecha_resolucion_final = timezone.now()
        self.save(update_fields=['estado', 'supervisor_revisor', 'comentario_supervisor', 'fecha_resolucion_final'])
    
    @property
    def impacto_monetario(self):
        """Alias para compatibilidad - retorna valor absoluto del delta"""
        return abs(self.delta_absoluto)
    
    @property
    def es_variacion_positiva(self):
        """True si es un aumento, False si es disminución"""
        return self.delta_absoluto > 0
    
    @property
    def es_incidencia_critica(self):
        """True si la incidencia es de prioridad crítica"""
        return self.prioridad == 'critica'


# =====================================
# VENTAJAS DEL MODELO SIMPLIFICADO:
# =====================================

"""
🎯 BENEFICIOS DE LA SIMPLIFICACIÓN:

1. **CLARIDAD CONCEPTUAL**:
   - Solo maneja totales por concepto
   - Sin complejidad de empleados individuales
   - Enfoque único: variaciones período vs período

2. **PERFORMANCE MEJORADA**:
   - Menos registros (1 por concepto vs N por empleado)
   - Consultas más rápidas
   - Índices más eficientes

3. **FLUJO DE TRABAJO SIMPLIFICADO**:
   - Un solo tipo de análisis (totales)
   - Proceso de resolución más directo
   - Menos tipos de incidencia para manejar

4. **MANTENIMIENTO REDUCIDO**:
   - Menos código para mantener
   - Menos casos edge
   - Migración más sencilla

5. **COMPATIBILIDAD CON REQUERIMIENTO ACTUAL**:
   - Se alinea perfectamente con la exclusión de informacion_adicional
   - Soporta el umbral del 30%
   - Mantiene la funcionalidad de justificación/aprobación

6. **ESCALABILIDAD**:
   - Puede manejar miles de conceptos eficientemente
   - Reporting agregado más rápido
   - Menos carga en la BD

🔄 MIGRACIÓN SUGERIDA:
1. Crear nueva tabla con este modelo
2. Migrar datos existentes (solo suma_total)
3. Actualizar views para usar el nuevo modelo
4. Deprecar modelo anterior gradualmente
"""