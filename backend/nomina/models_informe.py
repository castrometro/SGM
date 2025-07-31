# backend/nomina/models_informe.py

from django.db import models
from django.utils import timezone
from decimal import Decimal
from .models import CierreNomina, NominaConsolidada, ConceptoConsolidado, MovimientoPersonal
from django.db.models import Sum, Count, Avg, Max, Min, Q
import json


class InformeNomina(models.Model):
    """
    📊 INFORME COMPREHENSIVO DE CIERRE DE NÓMINA
    
    Se genera automáticamente al finalizar un cierre de nómina.
    Contiene métricas de RRHH similares a los informes ESF/ER/ERI del módulo contabilidad
    pero enfocado en indicadores laborales y de gestión de personal.
    """
    
    # Relación con el cierre
    cierre = models.OneToOneField(
        CierreNomina, 
        on_delete=models.CASCADE, 
        related_name='informe'
    )
    
    # Datos del cierre - estructura simple
    datos_cierre = models.JSONField(
        help_text="Datos consolidados del cierre de nómina"
    )
    
    # Metadatos
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    version_calculo = models.CharField(max_length=10, default="1.0")
    tiempo_calculo = models.DurationField(null=True, blank=True)
    
    class Meta:
        db_table = 'nomina_informe_cierre'
        verbose_name = 'Informe de Nómina'
        verbose_name_plural = 'Informes de Nómina'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Informe {self.cierre.cliente.nombre} - {self.cierre.periodo}"
    
    @classmethod
    def generar_informe_completo(cls, cierre):
        """
        🎯 FUNCIÓN PRINCIPAL: Genera el informe completo para un cierre
        """
        inicio = timezone.now()
        
        # Obtener o crear el informe
        informe, created = cls.objects.get_or_create(
            cierre=cierre,
            defaults={
                'datos_cierre': {}
            }
        )
        
        # Calcular los datos del cierre
        informe.datos_cierre = informe._calcular_datos_cierre()
        
        # Guardar tiempo de cálculo
        informe.tiempo_calculo = timezone.now() - inicio
        informe.save()
        
        return informe
    
    def _calcular_datos_cierre(self):
        """📊 Datos básicos del cierre de nómina"""
        nominas = NominaConsolidada.objects.filter(cierre=self.cierre)
        conceptos = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=self.cierre)
        movimientos = MovimientoPersonal.objects.filter(cierre=self.cierre)
        
        # MÉTRICAS BÁSICAS
        dotacion_total = nominas.count()
        dotacion_activa = nominas.filter(estado_empleado='activo').count()
        
        # COSTO EMPRESA (haberes + aportes patronales)
        costo_empresa = conceptos.filter(
            tipo_concepto__in=['haber_imponible', 'haber_no_imponible', 'aporte_patronal']
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # ROTACIÓN
        ingresos = movimientos.filter(tipo_movimiento='ingreso').count()
        egresos = movimientos.filter(tipo_movimiento='finiquito').count()
        rotacion_porcentaje = (egresos / dotacion_total * 100) if dotacion_total > 0 else 0
        
        # AUSENTISMO
        empleados_con_ausencias = movimientos.filter(tipo_movimiento='ausentismo').values('rut_empleado').distinct().count()
        ausentismo_porcentaje = (empleados_con_ausencias / dotacion_total * 100) if dotacion_total > 0 else 0
        
        # HORAS EXTRAS
        horas_extras_total = conceptos.filter(
            nombre_concepto__icontains='hora'
        ).aggregate(total_cantidad=Sum('cantidad'))['total_cantidad'] or Decimal('0')
        
        # DESCUENTOS LEGALES (AFP/Isapre)
        descuentos_legales = conceptos.filter(
            tipo_concepto='descuento_legal'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # ANÁLISIS AFP/ISAPRE ESPECÍFICO
        afp_isapre_detalle = conceptos.filter(
            tipo_concepto='descuento_legal',
            nombre_concepto__iregex=r'(afp|isapre|fonasa|salud)'
        ).values('nombre_concepto').annotate(
            total=Sum('monto_total'),
            empleados=Count('nomina_consolidada', distinct=True)
        ).order_by('-empleados')
        
        return {
            'metadatos': {
                'periodo': str(self.cierre.periodo),
                'cliente': self.cierre.cliente.nombre,
                'fecha_calculo': timezone.now().isoformat(),
                'estado_cierre': self.cierre.estado
            },
            'metricas_basicas': {
                'costo_empresa_total': float(costo_empresa),
                'dotacion_total': dotacion_total,
                'dotacion_activa': dotacion_activa,
                'rotacion_porcentaje': round(rotacion_porcentaje, 2),
                'ausentismo_porcentaje': round(ausentismo_porcentaje, 2),
                'descuentos_legales_total': float(descuentos_legales),
                'horas_extras_total': float(horas_extras_total)
            },
            'movimientos': {
                'empleados_nuevos': ingresos,
                'empleados_finiquitados': egresos,
                'empleados_con_ausencias': empleados_con_ausencias
            },
            'afp_isapre': [
                {
                    'concepto': item['nombre_concepto'],
                    'monto_total': float(item['total']),
                    'empleados': item['empleados']
                }
                for item in afp_isapre_detalle
            ]
        }
    
    def get_kpi_principal(self, nombre_kpi):
        """🎯 Obtener un KPI específico"""
        return self.datos_cierre.get('metricas_basicas', {}).get(nombre_kpi, 0)
    
    @property
    def costo_empresa_total(self):
        return self.get_kpi_principal('costo_empresa_total')
    
    @property
    def dotacion_total(self):
        return self.get_kpi_principal('dotacion_total')
    
    @property
    def rotacion_porcentaje(self):
        return self.get_kpi_principal('rotacion_porcentaje')
