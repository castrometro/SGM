# backend/nomina/utils/DetectarIncidenciasConsolidadas.py
"""
Sistema de detección de incidencias entre períodos consolidados de nómina
"""

import logging
from decimal import Decimal
from django.db.models import Q
from ..models import (
    CierreNomina, 
    NominaConsolidada, 
    ConceptoConsolidado, 
    MovimientoPersonal,
    IncidenciaCierre,
    TipoIncidencia
)

logger = logging.getLogger(__name__)

def detectar_incidencias_consolidadas(cierre_actual):
    """
    Detecta incidencias comparando el cierre actual consolidado vs el período anterior
    """
    if not cierre_actual.estado_consolidacion == 'consolidado':
        raise ValueError("El cierre debe estar consolidado para detectar incidencias")
    
    # Obtener período anterior del mismo cliente
    periodo_anterior = CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado_consolidacion='consolidado'
    ).order_by('-periodo').first()
    
    if not periodo_anterior:
        logger.info(f"No hay período anterior consolidado para {cierre_actual}. No se detectan incidencias.")
        return []
    
    logger.info(f"Comparando {cierre_actual.periodo} vs {periodo_anterior.periodo}")
    
    incidencias = []
    
    # 1. Detectar variaciones de conceptos (>30%)
    incidencias.extend(_detectar_variaciones_conceptos(cierre_actual, periodo_anterior))
    
    # 2. Detectar conceptos nuevos
    incidencias.extend(_detectar_conceptos_nuevos(cierre_actual, periodo_anterior))
    
    # 3. Detectar conceptos perdidos
    incidencias.extend(_detectar_conceptos_perdidos(cierre_actual, periodo_anterior))
    
    # 4. Detectar empleados que deberían ingresar
    incidencias.extend(_detectar_empleados_deberian_ingresar(cierre_actual, periodo_anterior))
    
    # 5. Detectar empleados que no deberían estar
    incidencias.extend(_detectar_empleados_no_deberian_estar(cierre_actual, periodo_anterior))
    
    # 6. Detectar ausentismos continuos
    incidencias.extend(_detectar_ausentismos_continuos(cierre_actual, periodo_anterior))
    
    logger.info(f"Detectadas {len(incidencias)} incidencias entre períodos")
    return incidencias


def _detectar_variaciones_conceptos(cierre_actual, periodo_anterior, umbral=30.0):
    """
    Detecta variaciones >30% en conceptos entre períodos
    """
    incidencias = []
    
    # Obtener conceptos consolidados de ambos períodos
    conceptos_actual = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual,
        es_numerico=True
    ).select_related('nomina_consolidada')
    
    conceptos_anterior = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        es_numerico=True
    ).select_related('nomina_consolidada')
    
    # Crear mapas por empleado+concepto
    mapa_actual = {}
    for concepto in conceptos_actual:
        key = f"{concepto.nomina_consolidada.rut_empleado}_{concepto.nombre_concepto}"
        mapa_actual[key] = concepto
    
    mapa_anterior = {}
    for concepto in conceptos_anterior:
        key = f"{concepto.nomina_consolidada.rut_empleado}_{concepto.nombre_concepto}"
        mapa_anterior[key] = concepto
    
    # Comparar conceptos que existen en ambos períodos
    for key, concepto_actual in mapa_actual.items():
        if key in mapa_anterior:
            concepto_anterior = mapa_anterior[key]
            
            try:
                monto_actual = float(concepto_actual.monto_total)
                monto_anterior = float(concepto_anterior.monto_total)
                
                if monto_anterior != 0:  # Evitar división por cero
                    variacion_pct = ((monto_actual - monto_anterior) / abs(monto_anterior)) * 100
                    
                    if abs(variacion_pct) > umbral:
                        incidencias.append(IncidenciaCierre(
                            cierre=cierre_actual,
                            tipo_incidencia=TipoIncidencia.VARIACION_CONCEPTO,
                            rut_empleado=concepto_actual.nomina_consolidada.rut_empleado,
                            descripcion=f"Variación {variacion_pct:.1f}% en {concepto_actual.nombre_concepto} para {concepto_actual.nomina_consolidada.nombre_empleado}",
                            concepto_afectado=concepto_actual.nombre_concepto,
                            valor_libro=str(monto_actual),  # Período actual
                            valor_novedades=str(monto_anterior),  # Período anterior
                            prioridad='alta' if abs(variacion_pct) > 50 else 'media',
                            impacto_monetario=Decimal(str(abs(monto_actual - monto_anterior)))
                        ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error calculando variación para {key}: {e}")
                continue
    
    return incidencias


def _detectar_conceptos_nuevos(cierre_actual, periodo_anterior):
    """
    Detecta conceptos que aparecen por primera vez en el período actual
    """
    incidencias = []
    
    # Conceptos únicos por período
    conceptos_actual = set(ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual
    ).values_list('nombre_concepto', flat=True).distinct())
    
    conceptos_anterior = set(ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=periodo_anterior
    ).values_list('nombre_concepto', flat=True).distinct())
    
    # Conceptos nuevos = están en actual pero no en anterior
    conceptos_nuevos = conceptos_actual - conceptos_anterior
    
    for nombre_concepto in conceptos_nuevos:
        # Contar empleados afectados
        empleados_afectados = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre=cierre_actual,
            nombre_concepto=nombre_concepto
        ).count()
        
        incidencias.append(IncidenciaCierre(
            cierre=cierre_actual,
            tipo_incidencia=TipoIncidencia.CONCEPTO_NUEVO,
            rut_empleado='MULTIPLE',  # Afecta múltiples empleados
            descripcion=f"Concepto nuevo '{nombre_concepto}' detectado en {empleados_afectados} empleados",
            concepto_afectado=nombre_concepto,
            prioridad='media',
        ))
    
    return incidencias


def _detectar_conceptos_perdidos(cierre_actual, periodo_anterior):
    """
    Detecta conceptos que desaparecen completamente del período actual
    """
    incidencias = []
    
    # Conceptos únicos por período
    conceptos_actual = set(ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual
    ).values_list('nombre_concepto', flat=True).distinct())
    
    conceptos_anterior = set(ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=periodo_anterior
    ).values_list('nombre_concepto', flat=True).distinct())
    
    # Conceptos perdidos = estaban en anterior pero no en actual
    conceptos_perdidos = conceptos_anterior - conceptos_actual
    
    for nombre_concepto in conceptos_perdidos:
        # Contar empleados que lo tenían antes
        empleados_anteriores = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre=periodo_anterior,
            nombre_concepto=nombre_concepto
        ).count()
        
        incidencias.append(IncidenciaCierre(
            cierre=cierre_actual,
            tipo_incidencia=TipoIncidencia.CONCEPTO_PERDIDO,
            rut_empleado='MULTIPLE',  # Afectaba múltiples empleados
            descripcion=f"Concepto '{nombre_concepto}' desapareció (antes en {empleados_anteriores} empleados)",
            concepto_afectado=nombre_concepto,
            prioridad='alta',  # Pérdida de conceptos es más crítica
        ))
    
    return incidencias


def _detectar_empleados_deberian_ingresar(cierre_actual, periodo_anterior):
    """
    Detecta empleados que tuvieron incorporaciones en el período anterior
    pero no aparecen en el período actual
    """
    incidencias = []
    
    # Empleados que ingresaron en período anterior
    incorporaciones_anterior = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        tipo_movimiento='ingreso'
    ).values_list('nomina_consolidada__rut_empleado', flat=True)
    
    # Empleados presentes en período actual
    empleados_actuales = set(NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).values_list('rut_empleado', flat=True))
    
    for rut_empleado in incorporaciones_anterior:
        if rut_empleado not in empleados_actuales:
            # Este empleado ingresó el mes anterior pero no está presente ahora
            movimiento = MovimientoPersonal.objects.filter(
                nomina_consolidada__cierre=periodo_anterior,
                nomina_consolidada__rut_empleado=rut_empleado,
                tipo_movimiento='ingreso'
            ).select_related('nomina_consolidada').first()
            
            if movimiento:
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.EMPLEADO_DEBERIA_INGRESAR,
                    rut_empleado=rut_empleado,
                    descripcion=f"Empleado {movimiento.nomina_consolidada.nombre_empleado} ingresó en {periodo_anterior.periodo} pero no aparece en nómina actual",
                    prioridad='alta',
                ))
    
    return incidencias


def _detectar_empleados_no_deberian_estar(cierre_actual, periodo_anterior):
    """
    Detecta empleados que aparecen en el período actual sin incorporación previa
    """
    incidencias = []
    
    # Empleados en período actual
    empleados_actuales = NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).select_related()
    
    # Empleados que estaban en período anterior
    empleados_anteriores = set(NominaConsolidada.objects.filter(
        cierre=periodo_anterior
    ).values_list('rut_empleado', flat=True))
    
    for empleado_actual in empleados_actuales:
        if empleado_actual.rut_empleado not in empleados_anteriores:
            # Empleado nuevo - verificar si tiene incorporación documentada en movimientos
            tiene_incorporacion = MovimientoPersonal.objects.filter(
                nomina_consolidada=empleado_actual,
                tipo_movimiento='ingreso'
            ).exists()
            
            if not tiene_incorporacion:
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,
                    rut_empleado=empleado_actual.rut_empleado,
                    descripcion=f"Empleado {empleado_actual.nombre_empleado} aparece sin incorporación documentada",
                    prioridad='alta',
                ))
    
    return incidencias


def _detectar_ausentismos_continuos(cierre_actual, periodo_anterior):
    """
    Detecta empleados con ausentismos en período anterior que cambiaron de estado
    """
    incidencias = []
    
    # Empleados ausentes en período anterior
    ausentismos_anteriores = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        tipo_movimiento='ausentismo'
    ).select_related('nomina_consolidada')
    
    # Empleados presentes en período actual  
    empleados_actuales = set(NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).values_list('rut_empleado', flat=True))
    
    # Empleados con ausentismos en período actual
    ausentismos_actuales = set(MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=cierre_actual,
        tipo_movimiento='ausentismo'
    ).values_list('nomina_consolidada__rut_empleado', flat=True))
    
    for ausentismo_anterior in ausentismos_anteriores:
        rut_empleado = ausentismo_anterior.nomina_consolidada.rut_empleado
        
        # Caso 1: Estaba ausente, ahora está presente (posible reintegro)
        if rut_empleado in empleados_actuales and rut_empleado not in ausentismos_actuales:
            incidencias.append(IncidenciaCierre(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.AUSENTISMO_CONTINUO,
                rut_empleado=rut_empleado,
                descripcion=f"Empleado {ausentismo_anterior.nomina_consolidada.nombre_empleado} tenía ausentismo y ahora está presente (¿se reintegró?)",
                prioridad='media',
            ))
        
        # Caso 2: Estaba ausente, ahora no aparece en nómina (continuidad esperada pero verificar)
        elif rut_empleado not in empleados_actuales:
            incidencias.append(IncidenciaCierre(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.AUSENTISMO_CONTINUO,
                rut_empleado=rut_empleado,
                descripcion=f"Empleado {ausentismo_anterior.nomina_consolidada.nombre_empleado} continúa ausente (verificar estado)",
                prioridad='baja',  # Continuidad es esperada
            ))
    
    return incidencias


def generar_incidencias_consolidadas_task(cierre_id):
    """
    Tarea para generar incidencias de un cierre consolidado
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar que esté consolidado
        if not cierre.puede_generar_incidencias():
            raise ValueError(f"Cierre {cierre_id} no está listo para generar incidencias")
        
        # Detectar incidencias
        incidencias_detectadas = detectar_incidencias_consolidadas(cierre)
        
        # Guardar incidencias en la base de datos
        incidencias_guardadas = []
        for incidencia in incidencias_detectadas:
            incidencia.save()
            incidencias_guardadas.append(incidencia)
        
        # Actualizar estado del cierre
        cierre.estado_incidencias = 'incidencias_generadas' if incidencias_guardadas else 'sin_incidencias'
        cierre.total_incidencias = len(incidencias_guardadas)
        cierre.save(update_fields=['estado_incidencias', 'total_incidencias'])
        
        logger.info(f"Generadas {len(incidencias_guardadas)} incidencias para cierre {cierre_id}")
        return {
            'success': True,
            'total_incidencias': len(incidencias_guardadas),
            'tipos_detectados': list(set(inc.tipo_incidencia for inc in incidencias_guardadas))
        }
        
    except Exception as e:
        logger.error(f"Error generando incidencias para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
