# Propuesta de Modelo para Informes de Nómina
# backend/nomina/models.py (agregar al archivo existente)

from django.db import models
from django.contrib.auth.models import User
import json

class InformeNomina(models.Model):
    """
    Modelo para almacenar informes generados al finalizar cierres de nómina.
    Similar a los informes contables pero enfocado en métricas de RRHH.
    """
    
    # Relación con el cierre
    cierre = models.OneToOneField(
        'CierreNomina', 
        on_delete=models.CASCADE,
        related_name='informe_final'
    )
    
    # Metadatos del informe
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    usuario_generador = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que finalizó el cierre"
    )
    
    # Datos del informe (JSONFields organizados)
    resumen_ejecutivo = models.JSONField(
        help_text="KPIs principales y métricas clave para gerencia"
    )
    
    detalle_empleados = models.JSONField(
        help_text="Lista completa de empleados con sus datos consolidados"
    )
    
    analisis_conceptos = models.JSONField(
        help_text="Análisis detallado por tipo de concepto (haberes, descuentos, etc.)"
    )
    
    metricas_rrhh = models.JSONField(
        help_text="KPIs específicos de RRHH (rotación, dotación, ausentismo)"
    )
    
    comparativo_anterior = models.JSONField(
        null=True, blank=True,
        help_text="Comparación con el período anterior (si existe)"
    )
    
    # Campos de control
    version_informe = models.CharField(
        max_length=10, 
        default="1.0",
        help_text="Versión del formato del informe"
    )
    
    tiempo_generacion = models.FloatField(
        null=True, blank=True,
        help_text="Tiempo en segundos que tomó generar el informe"
    )
    
    class Meta:
        db_table = 'nomina_informe'
        verbose_name = "Informe de Nómina"
        verbose_name_plural = "Informes de Nómina"
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Informe {self.cierre.cliente.nombre} - {self.cierre.periodo}"
    
    @property
    def total_empleados(self):
        """Número total de empleados en el informe"""
        return len(self.detalle_empleados.get('empleados', []))
    
    @property
    def costo_total_empresa(self):
        """Costo total para la empresa"""
        resumen = self.resumen_ejecutivo.get('costos', {})
        return resumen.get('costo_total_empresa', 0)
    
    def obtener_kpi(self, categoria, kpi):
        """Método helper para obtener un KPI específico"""
        data_map = {
            'ejecutivo': self.resumen_ejecutivo,
            'rrhh': self.metricas_rrhh,
            'conceptos': self.analisis_conceptos,
            'comparativo': self.comparativo_anterior or {}
        }
        return data_map.get(categoria, {}).get(kpi)


# Estructura JSON ejemplo para resumen_ejecutivo:
EJEMPLO_RESUMEN_EJECUTIVO = {
    "costos": {
        "total_haberes": 50000000,
        "total_aportes_patronales": 8500000,
        "costo_total_empresa": 58500000,
        "costo_promedio_empleado": 450000
    },
    "empleados": {
        "total_empleados": 130,
        "empleados_activos": 128,
        "empleados_licencia": 2,
        "nuevos_ingresos": 5,
        "finiquitos": 3
    },
    "distribucion": {
        "haberes_imponibles": 42000000,
        "haberes_no_imponibles": 8000000,
        "descuentos_legales": 12000000,
        "otros_descuentos": 500000
    }
}

# Estructura JSON ejemplo para metricas_rrhh:
EJEMPLO_METRICAS_RRHH = {
    "dotacion": {
        "dotacion_inicial": 128,
        "ingresos": 5,
        "finiquitos": 3,
        "dotacion_final": 130
    },
    "rotacion": {
        "tasa_rotacion_mensual": 2.34,  # %
        "rotacion_anualizada": 28.08    # %
    },
    "ausentismo": {
        "total_licencias_medicas": 45,
        "total_dias_ausentismo": 180,
        "tasa_ausentismo": 4.2  # %
    },
    "horas_extras": {
        "total_horas_50": 120,
        "total_horas_100": 80,
        "costo_horas_extras": 2500000,
        "porcentaje_del_total": 4.3
    },
    "previsiones": {
        "afp_cuprum": 45,
        "afp_habitat": 38,
        "afp_provida": 32,
        "afp_modelo": 15,
        "fonasa": 89,
        "isapre": 41
    }
}
