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
        movimientos = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=self.cierre)
        
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
        empleados_con_ausencias = movimientos.filter(tipo_movimiento='ausentismo').values('nomina_consolidada__rut_empleado').distinct().count()
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
    
    def enviar_a_redis(self, ttl_hours: int = 24) -> dict:
        """
        🚀 Envía el informe completo a Redis DB 2
        
        Args:
            ttl_hours: Tiempo de vida en Redis en horas (default: 24h)
            
        Returns:
            dict: Resultado de la operación
        """
        from .cache_redis import get_cache_system_nomina
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Obtener sistema de cache
            cache_system = get_cache_system_nomina()
            
            # Preparar datos para Redis
            datos_redis = {
                'informe_id': self.id,
                'cliente_id': self.cierre.cliente.id,
                'cliente_nombre': self.cierre.cliente.nombre,
                'periodo': self.cierre.periodo,
                'estado_cierre': self.cierre.estado,
                'fecha_generacion': self.fecha_generacion.isoformat(),
                'fecha_finalizacion': self.cierre.fecha_finalizacion.isoformat() if self.cierre.fecha_finalizacion else None,
                'usuario_finalizacion': self.cierre.usuario_finalizacion.correo_bdo if self.cierre.usuario_finalizacion else None,
                'version_calculo': self.version_calculo,
                'tiempo_calculo_segundos': self.tiempo_calculo.total_seconds() if self.tiempo_calculo else None,
                
                # Datos del cierre completos
                'datos_cierre': self.datos_cierre,
                
                # KPIs principales para acceso rápido
                'kpis_principales': {
                    'dotacion_total': self.get_kpi_principal('dotacion_total'),
                    'costo_empresa_total': self.get_kpi_principal('costo_empresa_total'),
                    'rotacion_porcentaje': self.get_kpi_principal('rotacion_porcentaje'),
                    'ausentismo_porcentaje': self.get_kpi_principal('ausentismo_porcentaje'),
                    'promedio_sueldo_base': self.get_kpi_principal('promedio_sueldo_base'),
                    'total_horas_extras': self.get_kpi_principal('total_horas_extras'),
                    'empleados_activos': self.get_kpi_principal('empleados_activos'),
                    'nuevos_ingresos': self.get_kpi_principal('nuevos_ingresos'),
                    'salidas_periodo': self.get_kpi_principal('salidas_periodo'),
                    'total_vacaciones': self.get_kpi_principal('total_vacaciones'),
                    'promedio_dias_trabajados': self.get_kpi_principal('promedio_dias_trabajados')
                }
            }
            
            # Convertir TTL a segundos
            ttl_seconds = ttl_hours * 3600
            
            # Enviar a Redis
            success = cache_system.set_informe_nomina(
                cliente_id=self.cierre.cliente.id,
                periodo=self.cierre.periodo,
                informe_data=datos_redis,
                ttl=ttl_seconds
            )
            
            if success:
                logger.info(f"✅ Informe enviado a Redis: {self.cierre.cliente.nombre} - {self.cierre.periodo}")
                return {
                    'success': True,
                    'mensaje': 'Informe enviado exitosamente a Redis',
                    'clave_redis': f"sgm:nomina:{self.cierre.cliente.id}:{self.cierre.periodo}:informe",
                    'ttl_hours': ttl_hours,
                    'size_kb': len(str(datos_redis)) / 1024
                }
            else:
                return {
                    'success': False,
                    'error': 'Error al enviar informe a Redis'
                }
                
        except Exception as e:
            logger.error(f"❌ Error enviando informe a Redis: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def obtener_desde_redis(cls, cliente_id: int, periodo: str) -> dict:
        """
        📥 Obtiene un informe desde Redis
        
        Args:
            cliente_id: ID del cliente
            periodo: Período del cierre
            
        Returns:
            dict: Datos del informe o None si no existe
        """
        from .cache_redis import get_cache_system_nomina
        
        try:
            cache_system = get_cache_system_nomina()
            return cache_system.get_informe_nomina(cliente_id, periodo)
        except Exception as e:
            return None
