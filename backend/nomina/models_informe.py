# backend/nomina/models_informe.py

from django.db import models
from django.utils import timezone
from decimal import Decimal
from .models import CierreNomina, NominaConsolidada, ConceptoConsolidado, MovimientoPersonal
from django.db.models import Sum, Count, Avg, Max, Min, Q
import json
import calendar
from datetime import datetime, date, timedelta


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
        """📊 KPIs específicos del cierre de nómina según requerimientos"""
        nominas = NominaConsolidada.objects.filter(cierre=self.cierre)
        conceptos = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=self.cierre)
        movimientos = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=self.cierre)
        
        # OBTENER DATOS DEL CIERRE ANTERIOR PARA COMPARACIONES
        periodo_anterior = self._calcular_periodo_anterior()
        cierre_anterior = None
        if periodo_anterior:
            try:
                cierre_anterior = CierreNomina.objects.get(
                    cliente=self.cierre.cliente,
                    periodo=periodo_anterior,
                    estado='finalizado'
                )
            except CierreNomina.DoesNotExist:
                pass
        
        # MÉTRICAS BÁSICAS DE CONTEO
        contratos_mes = nominas.count()
        ingresos_mes_actual = movimientos.filter(tipo_movimiento='ingreso').count()
        finiquitos_mes_actual = movimientos.filter(tipo_movimiento='finiquito').count()
        
        # CÁLCULO DE DOTACIÓN SEGÚN FÓRMULA ESPECÍFICA
        # dotación: dotación mes anterior + ingresos mes actual - finiquitos mes anterior
        dotacion_mes_anterior = 0
        finiquitos_mes_anterior = 0
        if cierre_anterior:
            nominas_anterior = NominaConsolidada.objects.filter(cierre=cierre_anterior)
            movimientos_anterior = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre_anterior)
            dotacion_mes_anterior = nominas_anterior.count()
            finiquitos_mes_anterior = movimientos_anterior.filter(tipo_movimiento='finiquito').count()
        
        dotacion_calculada = dotacion_mes_anterior + ingresos_mes_actual - finiquitos_mes_anterior
        
        # ROTACIÓN SEGÚN FÓRMULA ESPECÍFICA
        # rotación: (finiquitos del periodo/((dotacion al inicio + dotacion al final del periodo)/2))*100
        dotacion_inicio = dotacion_mes_anterior
        dotacion_final = dotacion_calculada
        promedio_dotacion = (dotacion_inicio + dotacion_final) / 2 if (dotacion_inicio + dotacion_final) > 0 else 1
        rotacion_porcentaje = (finiquitos_mes_actual / promedio_dotacion) * 100
        
        # COSTO EMPRESA (total haberes + aportes patronales)
        total_haberes = conceptos.filter(
            tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        aportes_patronales = conceptos.filter(
            tipo_concepto='aporte_patronal'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        costo_empresa = total_haberes + aportes_patronales
        
        # DESGLOSE DE HABERES
        haberes_imponibles = conceptos.filter(
            tipo_concepto='haber_imponible'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        haberes_no_imponibles = conceptos.filter(
            tipo_concepto='haber_no_imponible'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # DESGLOSE DE DESCUENTOS
        descuentos_legales = conceptos.filter(
            tipo_concepto='descuento_legal'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        otros_descuentos = conceptos.filter(
            tipo_concepto='descuento_voluntario'
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # HORAS EXTRAS SEPARADAS (50% y 100%)
        horas_50 = conceptos.filter(
            nombre_concepto__iregex=r'(hora.*50|50.*hora)',
            tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
        ).aggregate(
            cantidad=Sum('cantidad'),
            monto=Sum('monto_total')
        )
        
        horas_100 = conceptos.filter(
            nombre_concepto__iregex=r'(hora.*100|100.*hora)',
            tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
        ).aggregate(
            cantidad=Sum('cantidad'),
            monto=Sum('monto_total')
        )
        
        # AUSENTISMOS Y DÍAS LABORALES
        total_ausentismos = movimientos.filter(tipo_movimiento='ausentismo').count()
        
        # Calcular días laborales del mes y tasa de ausentismo detallada
        año, mes = map(int, str(self.cierre.periodo).split('-'))
        dias_laborales_mes = self._calcular_dias_laborales_chile(año, mes)
        
        # Calcular días de ausencia totales
        total_dias_ausencias = 0
        ausentismos_justificados = 0
        ausentismos_injustificados = 0
        
        for movimiento in movimientos.filter(tipo_movimiento='ausentismo'):
            # Si existe campo de días, usarlo; sino asumir 1 día
            dias_ausencia = getattr(movimiento, 'dias_ausencia', 1)
            total_dias_ausencias += dias_ausencia
            
            # Clasificar justificados vs injustificados si hay campo disponible
            if hasattr(movimiento, 'justificado'):
                if movimiento.justificado:
                    ausentismos_justificados += dias_ausencia
                else:
                    ausentismos_injustificados += dias_ausencia
            else:
                # Si no hay clasificación, asumir como justificado por defecto
                ausentismos_justificados += dias_ausencia
        
        # Calcular tasa de ausentismo
        total_dias_laborales_posibles = contratos_mes * dias_laborales_mes
        tasa_ausentismo = (total_dias_ausencias / total_dias_laborales_posibles) * 100 if total_dias_laborales_posibles > 0 else 0
        dias_trabajados_efectivos = total_dias_laborales_posibles - total_dias_ausencias
        
        # REMUNERACIÓN PROMEDIO
        remuneracion_total = total_haberes
        trabajadores_mes = contratos_mes if contratos_mes > 0 else 1
        remuneracion_promedio = remuneracion_total / trabajadores_mes
        
        # VARIACIÓN DE REMUNERACIONES VS MES ANTERIOR
        variacion_remuneraciones = 0
        if cierre_anterior:
            conceptos_anterior = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=cierre_anterior)
            remuneraciones_anterior = conceptos_anterior.filter(
                tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
            ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
            
            if remuneraciones_anterior > 0:
                variacion_remuneraciones = ((remuneracion_total - remuneraciones_anterior) / remuneraciones_anterior) * 100
        
        # TASAS ESPECÍFICAS
        tasa_ingreso = (ingresos_mes_actual / promedio_dotacion) * 100 if promedio_dotacion > 0 else 0
        tasa_finiquitos = (finiquitos_mes_actual / promedio_dotacion) * 100 if promedio_dotacion > 0 else 0
        
        # ANÁLISIS AFP/ISAPRE/FONASA
        afp_detalle = conceptos.filter(
            tipo_concepto='descuento_legal',
            nombre_concepto__iregex=r'afp'
        ).aggregate(
            total=Sum('monto_total'),
            empleados=Count('nomina_consolidada', distinct=True)
        )
        
        isapre_detalle = conceptos.filter(
            tipo_concepto='descuento_legal',
            nombre_concepto__iregex=r'isapre'
        ).aggregate(
            total=Sum('monto_total'),
            empleados=Count('nomina_consolidada', distinct=True)
        )
        
        fonasa_detalle = conceptos.filter(
            tipo_concepto='descuento_legal',
            nombre_concepto__iregex=r'(fonasa|salud.*7)'
        ).aggregate(
            total=Sum('monto_total'),
            empleados=Count('nomina_consolidada', distinct=True)
        )
        
        # PROPORCIÓN DE AFILIADOS
        total_afiliados_salud = (isapre_detalle['empleados'] or 0) + (fonasa_detalle['empleados'] or 0)
        proporcion_isapre = (isapre_detalle['empleados'] / total_afiliados_salud * 100) if total_afiliados_salud > 0 else 0
        proporcion_fonasa = (fonasa_detalle['empleados'] / total_afiliados_salud * 100) if total_afiliados_salud > 0 else 0
        
        # LISTA DETALLADA DE EMPLEADOS
        lista_empleados = self._generar_lista_empleados(nominas, conceptos, movimientos, dias_laborales_mes)
        
        return {
            'metadatos': {
                'periodo': str(self.cierre.periodo),
                'cliente': self.cierre.cliente.nombre,
                'fecha_calculo': timezone.now().isoformat(),
                'estado_cierre': self.cierre.estado,
                'periodo_anterior': periodo_anterior,
                'tiene_comparacion': cierre_anterior is not None
            },
            'metricas_principales': {
                # KPIs según especificación exacta
                'costo_empresa_total': float(costo_empresa),
                'contratos_del_mes': contratos_mes,
                'finiquitos_del_mes': finiquitos_mes_actual,
                'dotacion_calculada': dotacion_calculada,
                'rotacion_porcentaje': round(rotacion_porcentaje, 2),
                'total_ausentismos': total_ausentismos,
                'total_haberes': float(total_haberes),
                'total_haberes_imponibles': float(haberes_imponibles),
                'total_haberes_no_imponibles': float(haberes_no_imponibles),
                'total_descuentos_legales': float(descuentos_legales),
                'total_otros_descuentos': float(otros_descuentos),
                'total_aportes_patronales': float(aportes_patronales),
                'variacion_remuneraciones_porcentaje': round(variacion_remuneraciones, 2),
                'remuneracion_promedio_mes': float(remuneracion_promedio),
                'tasa_ingreso_porcentaje': round(tasa_ingreso, 2),
                'tasa_finiquitos_porcentaje': round(tasa_finiquitos, 2)
            },
            'ausentismo_detallado': {
                'total_ausentismos_empleados': total_ausentismos,
                'total_dias_ausencias': total_dias_ausencias,
                'dias_ausencias_justificadas': ausentismos_justificados,
                'dias_ausencias_injustificadas': ausentismos_injustificados,
                'dias_laborales_mes': dias_laborales_mes,
                'total_dias_laborales_posibles': total_dias_laborales_posibles,
                'dias_trabajados_efectivos': dias_trabajados_efectivos,
                'tasa_ausentismo_porcentaje': round(tasa_ausentismo, 2),
                'tasa_ausentismo_justificado': round((ausentismos_justificados / total_dias_laborales_posibles) * 100, 2) if total_dias_laborales_posibles > 0 else 0,
                'tasa_ausentismo_injustificado': round((ausentismos_injustificados / total_dias_laborales_posibles) * 100, 2) if total_dias_laborales_posibles > 0 else 0
            },
            'horas_extras': {
                'horas_50_porcentaje': {
                    'cantidad': float(horas_50['cantidad'] or 0),
                    'monto_total': float(horas_50['monto'] or 0)
                },
                'horas_100_porcentaje': {
                    'cantidad': float(horas_100['cantidad'] or 0),
                    'monto_total': float(horas_100['monto'] or 0)
                }
            },
            'dotacion_detalle': {
                'dotacion_mes_anterior': dotacion_mes_anterior,
                'ingresos_mes_actual': ingresos_mes_actual,
                'finiquitos_mes_anterior': finiquitos_mes_anterior,
                'dotacion_inicio_periodo': dotacion_inicio,
                'dotacion_final_periodo': dotacion_final,
                'promedio_dotacion_periodo': round(promedio_dotacion, 2)
            },
            'afiliaciones_previsionales': {
                'afp': {
                    'empleados': afp_detalle['empleados'] or 0,
                    'monto_total': float(afp_detalle['total'] or 0)
                },
                'isapre': {
                    'empleados': isapre_detalle['empleados'] or 0,
                    'monto_total': float(isapre_detalle['total'] or 0),
                    'proporcion_porcentaje': round(proporcion_isapre, 2)
                },
                'fonasa': {
                    'empleados': fonasa_detalle['empleados'] or 0,
                    'monto_total': float(fonasa_detalle['total'] or 0),
                    'proporcion_porcentaje': round(proporcion_fonasa, 2)
                }
            },
            'empleados': lista_empleados
        }
    
    def _calcular_periodo_anterior(self):
        """Calcula el período anterior al cierre actual"""
        from datetime import datetime
        try:
            # Parsear el período actual (formato YYYY-MM)
            año, mes = map(int, str(self.cierre.periodo).split('-'))
            
            # Calcular mes anterior
            if mes == 1:
                año_anterior = año - 1
                mes_anterior = 12
            else:
                año_anterior = año
                mes_anterior = mes - 1
            
            return f"{año_anterior}-{mes_anterior:02d}"
        except:
            return None
    
    def _generar_lista_empleados(self, nominas, conceptos, movimientos, dias_laborales_mes):
        """Genera lista detallada de empleados con sus métricas individuales"""
        lista_empleados = []
        
        for nomina in nominas:
            # Obtener conceptos del empleado
            conceptos_empleado = conceptos.filter(nomina_consolidada=nomina)
            movimientos_empleado = movimientos.filter(nomina_consolidada=nomina)
            
            # Calcular totales del empleado
            total_haberes_emp = conceptos_empleado.filter(
                tipo_concepto__in=['haber_imponible', 'haber_no_imponible']
            ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
            
            total_descuentos_emp = conceptos_empleado.filter(
                tipo_concepto__in=['descuento_legal', 'descuento_voluntario']
            ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
            
            liquido_pagar = total_haberes_emp - total_descuentos_emp
            
            # Analizar ausentismos del empleado
            ausentismos_empleado = movimientos_empleado.filter(tipo_movimiento='ausentismo')
            total_dias_ausencias_emp = 0
            ausencias_justificadas_emp = 0
            ausencias_injustificadas_emp = 0
            
            for ausencia in ausentismos_empleado:
                dias_ausencia = getattr(ausencia, 'dias_ausencia', 1)
                total_dias_ausencias_emp += dias_ausencia
                
                if hasattr(ausencia, 'justificado') and ausencia.justificado:
                    ausencias_justificadas_emp += dias_ausencia
                else:
                    ausencias_injustificadas_emp += dias_ausencia
            
            # Calcular días trabajados
            dias_trabajados_emp = dias_laborales_mes - total_dias_ausencias_emp
            
            # Identificar AFP/Isapre/Fonasa
            afp_empleado = conceptos_empleado.filter(
                tipo_concepto='descuento_legal',
                nombre_concepto__iregex=r'afp'
            ).first()
            
            salud_empleado = conceptos_empleado.filter(
                tipo_concepto='descuento_legal',
                nombre_concepto__iregex=r'(isapre|fonasa|salud)'
            ).first()
            
            # Identificar horas extras
            horas_extras_emp = conceptos_empleado.filter(
                nombre_concepto__iregex=r'hora'
            ).aggregate(
                total_horas=Sum('cantidad'),
                total_monto=Sum('monto_total')
            )
            
            # Identificar estado del empleado (ingreso, finiquito, activo)
            estado_periodo = 'activo'
            if movimientos_empleado.filter(tipo_movimiento='ingreso').exists():
                estado_periodo = 'ingreso'
            elif movimientos_empleado.filter(tipo_movimiento='finiquito').exists():
                estado_periodo = 'finiquito'
            
            # Identificar si tiene novedades
            tiene_novedades = conceptos_empleado.filter(
                nombre_concepto__icontains='novedad'
            ).exists()
            
            empleado_data = {
                'rut_empleado': nomina.rut_empleado,
                'nombre_completo': f"{nomina.nombre_empleado} {getattr(nomina, 'apellido_paterno', '')} {getattr(nomina, 'apellido_materno', '')}".strip(),
                'estado_empleado': nomina.estado_empleado,
                'estado_periodo': estado_periodo,
                'cargo': getattr(nomina, 'cargo', ''),
                'centro_costo': getattr(nomina, 'centro_costo', ''),
                'remuneracion': {
                    'total_haberes': float(total_haberes_emp),
                    'total_descuentos': float(total_descuentos_emp),
                    'liquido_pagar': float(liquido_pagar)
                },
                'ausentismo': {
                    'total_dias_ausencias': total_dias_ausencias_emp,
                    'dias_justificados': ausencias_justificadas_emp,
                    'dias_injustificados': ausencias_injustificadas_emp,
                    'dias_trabajados': max(0, dias_trabajados_emp),
                    'tasa_ausentismo': round((total_dias_ausencias_emp / dias_laborales_mes) * 100, 2) if dias_laborales_mes > 0 else 0
                },
                'horas_extras': {
                    'total_horas': float(horas_extras_emp['total_horas'] or 0),
                    'total_monto': float(horas_extras_emp['total_monto'] or 0)
                },
                'afiliaciones': {
                    'afp': afp_empleado.nombre_concepto if afp_empleado else None,
                    'salud': salud_empleado.nombre_concepto if salud_empleado else None,
                    'tipo_salud': 'isapre' if salud_empleado and 'isapre' in salud_empleado.nombre_concepto.lower() else 'fonasa'
                },
                'indicadores': {
                    'tiene_novedades': tiene_novedades,
                    'cantidad_conceptos': conceptos_empleado.count(),
                    'es_nuevo_ingreso': estado_periodo == 'ingreso',
                    'es_finiquito': estado_periodo == 'finiquito',
                    'tiene_horas_extras': horas_extras_emp['total_horas'] > 0 if horas_extras_emp['total_horas'] else False
                }
            }
            
            lista_empleados.append(empleado_data)
        
        # Ordenar por apellido/nombre
        lista_empleados.sort(key=lambda x: x['nombre_completo'])
        
        return {
            'total_empleados': len(lista_empleados),
            'resumen_estados': {
                'activos': len([e for e in lista_empleados if e['estado_periodo'] == 'activo']),
                'ingresos': len([e for e in lista_empleados if e['estado_periodo'] == 'ingreso']),
                'finiquitos': len([e for e in lista_empleados if e['estado_periodo'] == 'finiquito']),
                'con_ausencias': len([e for e in lista_empleados if e['ausentismo']['total_dias_ausencias'] > 0]),
                'con_horas_extras': len([e for e in lista_empleados if e['indicadores']['tiene_horas_extras']]),
                'con_novedades': len([e for e in lista_empleados if e['indicadores']['tiene_novedades']])
            },
            'detalle': lista_empleados
        }
    
    def get_kpi_principal(self, nombre_kpi):
        """🎯 Obtener un KPI específico"""
        return self.datos_cierre.get('metricas_principales', {}).get(nombre_kpi, 0)
    
    @property
    def costo_empresa_total(self):
        return self.get_kpi_principal('costo_empresa_total')
    
    @property
    def contratos_del_mes(self):
        return self.get_kpi_principal('contratos_del_mes')
    
    @property
    def rotacion_porcentaje(self):
        return self.get_kpi_principal('rotacion_porcentaje')
    
    @property
    def dotacion_calculada(self):
        return self.get_kpi_principal('dotacion_calculada')
    
    @property
    def remuneracion_promedio(self):
        return self.get_kpi_principal('remuneracion_promedio_mes')
    
    def calcular_tasa_ausentismo_dias(self, dias_laborales_mes=None):
        """
        Calcula la tasa de ausentismo basada en días no trabajados
        Fórmula: (días no trabajados/total de días laborales del mes)*100
        """
        # Calcular días laborales del mes si no se proporciona
        if dias_laborales_mes is None:
            año, mes = map(int, str(self.cierre.periodo).split('-'))
            dias_laborales_mes = self._calcular_dias_laborales_chile(año, mes)
        
        # Obtener datos de ausentismo detallado
        nominas = NominaConsolidada.objects.filter(cierre=self.cierre)
        movimientos = MovimientoPersonal.objects.filter(
            nomina_consolidada__cierre=self.cierre,
            tipo_movimiento='ausentismo'
        )
        
        # Calcular días no trabajados totales
        total_dias_ausencias = 0
        for movimiento in movimientos:
            # Si el movimiento tiene días específicos, usarlos
            if hasattr(movimiento, 'dias_ausencia') and movimiento.dias_ausencia:
                total_dias_ausencias += movimiento.dias_ausencia
            else:
                # Asumir 1 día por movimiento de ausentismo
                total_dias_ausencias += 1
        
        # Calcular total de días laborales posibles
        contratos = self.get_kpi_principal('contratos_del_mes')
        total_dias_laborales_posibles = contratos * dias_laborales_mes
        
        # Calcular tasa de ausentismo
        tasa_ausentismo = (total_dias_ausencias / total_dias_laborales_posibles) * 100 if total_dias_laborales_posibles > 0 else 0
        
        return {
            'tasa_ausentismo_porcentaje': round(tasa_ausentismo, 2),
            'dias_laborales_mes': dias_laborales_mes,
            'total_dias_ausencias': total_dias_ausencias,
            'total_dias_laborales_posibles': total_dias_laborales_posibles,
            'dias_trabajados_efectivos': total_dias_laborales_posibles - total_dias_ausencias
        }
    
    def _calcular_dias_laborales_chile(self, año, mes):
        """
        Calcula los días laborales de un mes en Chile
        Excluye fines de semana y feriados principales
        """
        # Feriados fijos principales en Chile
        feriados_fijos = {
            (1, 1): "Año Nuevo",
            (5, 1): "Día del Trabajador", 
            (5, 21): "Día de las Glorias Navales",
            (6, 29): "San Pedro y San Pablo",
            (7, 16): "Día de la Virgen del Carmen",
            (8, 15): "Asunción de la Virgen",
            (9, 18): "Independencia Nacional",
            (9, 19): "Día de las Glorias del Ejército",
            (10, 12): "Descubrimiento de América",
            (11, 1): "Día de Todos los Santos",
            (12, 8): "Inmaculada Concepción",
            (12, 25): "Navidad"
        }
        
        # Calcular Viernes Santo (variable según año)
        viernes_santo = self._calcular_viernes_santo(año)
        
        # Obtener el rango de días del mes
        primer_dia = date(año, mes, 1)
        ultimo_dia = date(año, mes, calendar.monthrange(año, mes)[1])
        
        dias_laborales = 0
        current_date = primer_dia
        
        while current_date <= ultimo_dia:
            # Verificar si es día laborable (Lunes=0 a Viernes=4)
            if current_date.weekday() < 5:  # Lunes a Viernes
                # Verificar si no es feriado
                if (current_date.month, current_date.day) not in feriados_fijos:
                    # Verificar si no es Viernes Santo
                    if current_date != viernes_santo:
                        dias_laborales += 1
            
            current_date += timedelta(days=1)
        
        return dias_laborales
    
    def _calcular_viernes_santo(self, año):
        """Calcula la fecha del Viernes Santo para un año dado"""
        # Algoritmo para calcular Pascua (Domingo de Resurrección)
        a = año % 19
        b = año // 100
        c = año % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        
        # Domingo de Pascua
        domingo_pascua = date(año, n, p + 1)
        
        # Viernes Santo es 2 días antes
        viernes_santo = domingo_pascua - timedelta(days=2)
        
        return viernes_santo
    
    def obtener_resumen_ejecutivo(self):
        """Retorna un resumen ejecutivo con los KPIs más importantes"""
        return {
            'costo_empresa': f"${self.costo_empresa_total:,.0f}",
            'contratos': self.contratos_del_mes,
            'rotacion': f"{self.rotacion_porcentaje}%",
            'variacion_remuneraciones': f"{self.get_kpi_principal('variacion_remuneraciones_porcentaje')}%",
            'tasa_ingreso': f"{self.get_kpi_principal('tasa_ingreso_porcentaje')}%",
            'tasa_finiquitos': f"{self.get_kpi_principal('tasa_finiquitos_porcentaje')}%",
            'remuneracion_promedio': f"${self.remuneracion_promedio:,.0f}",
            'periodo': self.datos_cierre['metadatos']['periodo'],
            'cliente': self.datos_cierre['metadatos']['cliente']
        }
    
    def obtener_comparacion_mes_anterior(self):
        """Retorna las métricas comparativas con el mes anterior si están disponibles"""
        if not self.datos_cierre['metadatos'].get('tiene_comparacion', False):
            return None
        
        return {
            'variacion_remuneraciones': self.get_kpi_principal('variacion_remuneraciones_porcentaje'),
            'periodo_anterior': self.datos_cierre['metadatos'].get('periodo_anterior'),
            'dotacion_anterior': self.datos_cierre.get('dotacion_detalle', {}).get('dotacion_mes_anterior', 0),
            'dotacion_actual': self.dotacion_calculada,
        }
    def obtener_empleados_por_criterio(self, criterio):
        """
        Filtra empleados según diferentes criterios
        
        Criterios disponibles:
        - 'con_ausencias': Empleados con días de ausencia
        - 'sin_ausencias': Empleados sin ausencias
        - 'ingresos': Nuevos ingresos del período
        - 'finiquitos': Empleados finiquitados
        - 'con_horas_extras': Empleados con horas extras
        - 'con_novedades': Empleados con novedades
        - 'alta_remuneracion': 20% mejor pagados
        - 'isapre': Afiliados a Isapre
        - 'fonasa': Afiliados a Fonasa
        """
        empleados_data = self.datos_cierre.get('empleados', {})
        empleados = empleados_data.get('detalle', [])
        
        if not empleados:
            return []
        
        if criterio == 'con_ausencias':
            return [e for e in empleados if e['ausentismo']['total_dias_ausencias'] > 0]
        
        elif criterio == 'sin_ausencias':
            return [e for e in empleados if e['ausentismo']['total_dias_ausencias'] == 0]
        
        elif criterio == 'ingresos':
            return [e for e in empleados if e['estado_periodo'] == 'ingreso']
        
        elif criterio == 'finiquitos':
            return [e for e in empleados if e['estado_periodo'] == 'finiquito']
        
        elif criterio == 'con_horas_extras':
            return [e for e in empleados if e['indicadores']['tiene_horas_extras']]
        
        elif criterio == 'con_novedades':
            return [e for e in empleados if e['indicadores']['tiene_novedades']]
        
        elif criterio == 'alta_remuneracion':
            # Ordenar por remuneración total y tomar el 20% superior
            empleados_ordenados = sorted(empleados, key=lambda x: x['remuneracion']['total_haberes'], reverse=True)
            top_20_percent = max(1, len(empleados_ordenados) // 5)
            return empleados_ordenados[:top_20_percent]
        
        elif criterio == 'isapre':
            return [e for e in empleados if e['afiliaciones']['tipo_salud'] == 'isapre']
        
        elif criterio == 'fonasa':
            return [e for e in empleados if e['afiliaciones']['tipo_salud'] == 'fonasa']
        
        else:
            return empleados
    
    def obtener_estadisticas_empleados(self):
        """Obtiene estadísticas avanzadas de la lista de empleados"""
        empleados_data = self.datos_cierre.get('empleados', {})
        empleados = empleados_data.get('detalle', [])
        
        if not empleados:
            return {}
        
        remuneraciones = [e['remuneracion']['total_haberes'] for e in empleados]
        ausencias = [e['ausentismo']['total_dias_ausencias'] for e in empleados]
        
        # Estadísticas de remuneración
        remuneracion_max = max(remuneraciones)
        remuneracion_min = min(remuneraciones)
        remuneracion_promedio = sum(remuneraciones) / len(remuneraciones)
        remuneracion_mediana = sorted(remuneraciones)[len(remuneraciones) // 2]
        
        # Estadísticas de ausentismo
        empleados_con_ausencias = [e for e in empleados if e['ausentismo']['total_dias_ausencias'] > 0]
        promedio_ausencias = sum(ausencias) / len(ausencias) if ausencias else 0
        
        # Distribución por rango salarial
        rangos_salariales = {
            'menos_500k': len([r for r in remuneraciones if r < 500000]),
            '500k_1M': len([r for r in remuneraciones if 500000 <= r < 1000000]),
            '1M_1.5M': len([r for r in remuneraciones if 1000000 <= r < 1500000]),
            '1.5M_2M': len([r for r in remuneraciones if 1500000 <= r < 2000000]),
            'mas_2M': len([r for r in remuneraciones if r >= 2000000])
        }
        
        return {
            'remuneracion': {
                'promedio': round(remuneracion_promedio, 2),
                'mediana': round(remuneracion_mediana, 2),
                'maximo': remuneracion_max,
                'minimo': remuneracion_min,
                'rango': remuneracion_max - remuneracion_min,
                'rangos_salariales': rangos_salariales
            },
            'ausentismo': {
                'empleados_con_ausencias': len(empleados_con_ausencias),
                'empleados_sin_ausencias': len(empleados) - len(empleados_con_ausencias),
                'promedio_dias_ausencias': round(promedio_ausencias, 2),
                'total_dias_perdidos': sum(ausencias)
            },
            'distribucion': {
                'por_centro_costo': self._agrupar_por_campo(empleados, 'centro_costo'),
                'por_cargo': self._agrupar_por_campo(empleados, 'cargo'),
                'por_tipo_salud': self._agrupar_por_campo(empleados, 'afiliaciones.tipo_salud')
            }
        }
    
    def _agrupar_por_campo(self, empleados, campo):
        """Agrupa empleados por un campo específico"""
        grupos = {}
        
        for empleado in empleados:
            # Manejar campos anidados como 'afiliaciones.tipo_salud'
            if '.' in campo:
                campos = campo.split('.')
                valor = empleado
                for c in campos:
                    valor = valor.get(c, 'No especificado')
                    if valor is None:
                        valor = 'No especificado'
                        break
            else:
                valor = empleado.get(campo, 'No especificado')
            
            if valor not in grupos:
                grupos[valor] = 0
            grupos[valor] += 1
        
        return grupos
    
    def calcular_dias_trabajados_por_empleado(self):
        """
        Calcula estadísticas de días trabajados basado en la fórmula:
        días trabajados = días laborales del mes - días ausentes
        """
        ausentismo_data = self.datos_cierre.get('ausentismo_detallado', {})
        contratos = self.get_kpi_principal('contratos_del_mes')
        
        if contratos == 0:
            return {}
        
        dias_laborales_mes = ausentismo_data.get('dias_laborales_mes', 22)
        total_dias_ausencias = ausentismo_data.get('total_dias_ausencias', 0)
        total_ausentismos_empleados = ausentismo_data.get('total_ausentismos_empleados', 0)
        
        # Cálculos estadísticos
        promedio_ausencias_por_empleado_ausente = total_dias_ausencias / total_ausentismos_empleados if total_ausentismos_empleados > 0 else 0
        empleados_sin_ausencias = contratos - total_ausentismos_empleados
        
        # Días trabajados estadísticos
        dias_trabajados_empleados_sin_ausencias = empleados_sin_ausencias * dias_laborales_mes
        dias_trabajados_empleados_con_ausencias = (total_ausentismos_empleados * dias_laborales_mes) - total_dias_ausencias
        total_dias_trabajados = dias_trabajados_empleados_sin_ausencias + dias_trabajados_empleados_con_ausencias
        
        promedio_dias_trabajados_por_empleado = total_dias_trabajados / contratos if contratos > 0 else 0
        
        return {
            'promedio_dias_trabajados_por_empleado': round(promedio_dias_trabajados_por_empleado, 2),
            'empleados_sin_ausencias': empleados_sin_ausencias,
            'empleados_con_ausencias': total_ausentismos_empleados,
            'promedio_ausencias_por_empleado_ausente': round(promedio_ausencias_por_empleado_ausente, 2),
            'total_dias_trabajados_efectivos': total_dias_trabajados,
            'eficiencia_tiempo_trabajo': round((total_dias_trabajados / ausentismo_data.get('total_dias_laborales_posibles', 1)) * 100, 2)
        }
    
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
                
                # KPIs principales para acceso rápido (actualizados)
                'kpis_principales': {
                    'costo_empresa_total': self.get_kpi_principal('costo_empresa_total'),
                    'contratos_del_mes': self.get_kpi_principal('contratos_del_mes'),
                    'finiquitos_del_mes': self.get_kpi_principal('finiquitos_del_mes'),
                    'dotacion_calculada': self.get_kpi_principal('dotacion_calculada'),
                    'rotacion_porcentaje': self.get_kpi_principal('rotacion_porcentaje'),
                    'total_ausentismos': self.get_kpi_principal('total_ausentismos'),
                    'total_haberes': self.get_kpi_principal('total_haberes'),
                    'total_descuentos_legales': self.get_kpi_principal('total_descuentos_legales'),
                    'total_aportes_patronales': self.get_kpi_principal('total_aportes_patronales'),
                    'variacion_remuneraciones_porcentaje': self.get_kpi_principal('variacion_remuneraciones_porcentaje'),
                    'remuneracion_promedio_mes': self.get_kpi_principal('remuneracion_promedio_mes'),
                    'tasa_ingreso_porcentaje': self.get_kpi_principal('tasa_ingreso_porcentaje'),
                    'tasa_finiquitos_porcentaje': self.get_kpi_principal('tasa_finiquitos_porcentaje')
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
