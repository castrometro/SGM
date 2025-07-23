# backend/nomina/utils/AnalisisCompletoIncidencias.py
"""
Análisis completo de comparación temporal entre períodos
Muestra TODAS las comparaciones, no solo las que generan incidencias
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

def generar_analisis_completo_temporal(cierre_actual):
    """
    🔍 ANÁLISIS COMPLETO: Muestra todas las comparaciones vs período anterior
    
    Implementa las 4 reglas con TODA la información:
    1. Todas las variaciones de valor header-empleado (incluso <30%)
    2. Todos los ausentismos del mes anterior (continúan o no)
    3. Todas las personas que ingresaron el mes anterior (están o no)
    4. Todas las personas que finiquitaron el mes anterior (siguen o no)
    """
    if cierre_actual.estado != 'datos_consolidados':
        raise ValueError(f"El cierre debe estar en estado 'datos_consolidados' para análisis completo")
    
    # 1. Verificar si hay período anterior FINALIZADO para comparar
    periodo_anterior = CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado='finalizado'
    ).order_by('-periodo').first()
    
    if not periodo_anterior:
        # Buscar cualquier período anterior para mostrar información útil en el error
        periodo_cualquiera = CierreNomina.objects.filter(
            cliente=cierre_actual.cliente,
            periodo__lt=cierre_actual.periodo
        ).order_by('-periodo').first()
        
        if periodo_cualquiera:
            mensaje = f"No hay período anterior FINALIZADO para comparación directa. Se encontró el período {periodo_cualquiera.periodo} pero está en estado '{periodo_cualquiera.estado}'. Para realizar el análisis temporal, el período anterior debe estar finalizado."
            return {
                'tiene_periodo_anterior': False,
                'mensaje': mensaje,
                'periodo_anterior_encontrado': str(periodo_cualquiera.periodo),
                'estado_periodo_anterior': periodo_cualquiera.estado,
                'cliente': cierre_actual.cliente.nombre,
                'periodo_actual': str(cierre_actual.periodo)
            }
        else:
            return {
                'tiene_periodo_anterior': False,
                'mensaje': f"No existe ningún período anterior para el cliente {cierre_actual.cliente.nombre}. Este es el primer cierre registrado.",
                'cliente': cierre_actual.cliente.nombre,
                'periodo_actual': str(cierre_actual.periodo)
            }
    
    logger.info(f"🔍 Generando análisis completo: {cierre_actual.periodo} vs {periodo_anterior.periodo}")
    
    analisis = {
        'tiene_periodo_anterior': True,
        'periodo_actual': str(cierre_actual.periodo),
        'periodo_anterior': str(periodo_anterior.periodo),
        'cliente': cierre_actual.cliente.nombre if cierre_actual.cliente else 'N/A',
        
        # REGLA 1: Variaciones de conceptos (todas, no solo >30%)
        'variaciones_conceptos': _analizar_todas_variaciones_conceptos(cierre_actual, periodo_anterior),
        
        # REGLA 2: Ausentismos continuos
        'ausentismos_continuos': _analizar_ausentismos_continuos(cierre_actual, periodo_anterior),
        
        # REGLA 3: Ingresos del mes anterior
        'ingresos_mes_anterior': _analizar_ingresos_mes_anterior(cierre_actual, periodo_anterior),
        
        # REGLA 4: Finiquitos del mes anterior
        'finiquitos_mes_anterior': _analizar_finiquitos_mes_anterior(cierre_actual, periodo_anterior),
        
        # Resumen estadíSTICO
        'resumen': {}
    }
    
    # Calcular resumen
    analisis['resumen'] = _calcular_resumen_analisis(analisis)
    
    return analisis


def _analizar_todas_variaciones_conceptos(cierre_actual, periodo_anterior, umbral_incidencia=30.0):
    """
    REGLA 1: Analiza TODAS las variaciones de conceptos, no solo las >30%
    """
    resultado = {
        'total_comparaciones': 0,
        'con_variacion': 0,
        'incidencias_detectadas': 0,  # >30%
        'variaciones_menores': 0,     # <30%
        'sin_cambios': 0,
        'detalle': []
    }
    
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
    
    # Comparar todos los conceptos que existen en ambos períodos
    for key, concepto_actual in mapa_actual.items():
        if key in mapa_anterior:
            concepto_anterior = mapa_anterior[key]
            resultado['total_comparaciones'] += 1
            
            try:
                monto_actual = float(concepto_actual.monto_total)
                monto_anterior = float(concepto_anterior.monto_total)
                
                if monto_anterior != 0:  # Evitar división por cero
                    variacion_pct = ((monto_actual - monto_anterior) / abs(monto_anterior)) * 100
                    diferencia_absoluta = abs(monto_actual - monto_anterior)
                    
                    # Clasificar variación
                    es_incidencia = abs(variacion_pct) > umbral_incidencia
                    tiene_variacion = abs(variacion_pct) > 0.01  # Más de 0.01%
                    
                    if tiene_variacion:
                        resultado['con_variacion'] += 1
                        if es_incidencia:
                            resultado['incidencias_detectadas'] += 1
                            estado = 'INCIDENCIA'
                            criticidad = 'ALTA' if abs(variacion_pct) > 50 else 'MEDIA'
                        else:
                            resultado['variaciones_menores'] += 1
                            estado = 'VARIACIÓN MENOR'
                            criticidad = 'BAJA'
                    else:
                        resultado['sin_cambios'] += 1
                        estado = 'SIN CAMBIOS'
                        criticidad = 'OK'
                    
                    # Agregar al detalle
                    resultado['detalle'].append({
                        'rut_empleado': concepto_actual.nomina_consolidada.rut_empleado,
                        'nombre_empleado': concepto_actual.nomina_consolidada.nombre_empleado,
                        'concepto': concepto_actual.nombre_concepto,
                        'monto_actual': monto_actual,
                        'monto_anterior': monto_anterior,
                        'variacion_pct': round(variacion_pct, 2),
                        'diferencia_absoluta': round(diferencia_absoluta, 2),
                        'estado': estado,
                        'criticidad': criticidad,
                        'es_incidencia': es_incidencia
                    })
                    
                else:
                    # Caso especial: monto anterior era 0
                    if monto_actual != 0:
                        resultado['con_variacion'] += 1
                        resultado['incidencias_detectadas'] += 1
                        
                        resultado['detalle'].append({
                            'rut_empleado': concepto_actual.nomina_consolidada.rut_empleado,
			    'nombre_empleado': concepto_actual.nomina_consolidada.nombre_empleado,
                            'concepto': concepto_actual.nombre_concepto,
                            'monto_actual': monto_actual,
                            'monto_anterior': 0,
                            'variacion_pct': 999.99,  # Infinito
                            'diferencia_absoluta': monto_actual,
                            'estado': 'CONCEPTO NUEVO',
                            'criticidad': 'ALTA',
                            'es_incidencia': True
                        })
                    else:
                        resultado['sin_cambios'] += 1
                        
            except (ValueError, TypeError) as e:
                logger.warning(f"Error calculando variación para {key}: {e}")
                continue
    
    # Ordenar detalle por variación descendente
    resultado['detalle'] = sorted(resultado['detalle'], 
                                key=lambda x: abs(x['variacion_pct']), 
                                reverse=True)
    
    return resultado


def _analizar_ausentismos_continuos(cierre_actual, periodo_anterior):
    """
    REGLA 2: Analiza todos los ausentismos del mes anterior
    """
    resultado = {
        'total_ausentismos_anteriores': 0,
        'deberian_continuar': 0,
        'continuaron': 0,
        'no_continuaron': 0,
        'incidencias_detectadas': 0,
        'detalle': []
    }
    
    # Por ahora simulamos - en producción se consultarían MovimientoPersonal
    # o las tablas correspondientes de ausentismos
    
    # TODO: Implementar lógica real basada en MovimientoPersonal o tablas de ausentismos
    resultado['mensaje'] = "⚠️ Análisis de ausentismos pendiente de implementación completa"
    
    return resultado


def _analizar_ingresos_mes_anterior(cierre_actual, periodo_anterior):
    """
    REGLA 3: Analiza ingresos del mes anterior que deberían estar presentes
    """
    resultado = {
        'total_ingresos_anteriores': 0,
        'deberian_estar_presentes': 0,
        'estan_presentes': 0,
        'no_estan_presentes': 0,
        'incidencias_detectadas': 0,
        'detalle': []
    }
    
    # Obtener empleados que aparecen en cada período
    empleados_actual = set(NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).values_list('rut_empleado', flat=True))
    
    empleados_anterior = set(NominaConsolidada.objects.filter(
        cierre=periodo_anterior
    ).values_list('rut_empleado', flat=True))
    
    # Los que ingresaron el mes anterior = están en anterior pero no en el anterior al anterior
    try:
        periodo_anterior_anterior = CierreNomina.objects.filter(
            cliente=cierre_actual.cliente,
            periodo__lt=periodo_anterior.periodo,
            estado='datos_consolidados'
        ).order_by('-periodo').first()
        
        if periodo_anterior_anterior:
            empleados_anterior_anterior = set(NominaConsolidada.objects.filter(
                cierre=periodo_anterior_anterior
            ).values_list('rut_empleado', flat=True))
            
            # Ingresos del mes anterior
            ingresos_mes_anterior = empleados_anterior - empleados_anterior_anterior
        else:
            # Si no hay período anterior al anterior, todos los del mes anterior son "ingresos"
            ingresos_mes_anterior = empleados_anterior
            
    except Exception as e:
        logger.warning(f"Error calculando ingresos mes anterior: {e}")
        ingresos_mes_anterior = set()
    
    resultado['total_ingresos_anteriores'] = len(ingresos_mes_anterior)
    
    # Analizar cada ingreso del mes anterior
    for rut in ingresos_mes_anterior:
        esta_presente = rut in empleados_actual
        
        if esta_presente:
            resultado['estan_presentes'] += 1
            estado = 'PRESENTE'
            criticidad = 'OK'
            es_incidencia = False
        else:
            resultado['no_estan_presentes'] += 1
            resultado['incidencias_detectadas'] += 1
            estado = 'INCIDENCIA - NO PRESENTE'
            criticidad = 'ALTA'
            es_incidencia = True
        
        # Obtener datos del empleado
        try:
            empleado_anterior = NominaConsolidada.objects.filter(
                cierre=periodo_anterior, 
                rut_empleado=rut
            ).first()
            
            nombre_empleado = empleado_anterior.nombre_empleado if empleado_anterior else 'N/A'
        except:
            nombre_empleado = 'N/A'
        
        resultado['detalle'].append({
            'rut_empleado': rut,
            'nombre_empleado': nombre_empleado,
            'ingreso_detectado_en': str(periodo_anterior.periodo),
            'esta_presente_mes_actual': esta_presente,
            'estado': estado,
            'criticidad': criticidad,
            'es_incidencia': es_incidencia
        })
    
    return resultado


def _analizar_finiquitos_mes_anterior(cierre_actual, periodo_anterior):
    """
    REGLA 4: Analiza finiquitos del mes anterior que no deberían estar presentes
    """
    resultado = {
        'total_finiquitos_anteriores': 0,
        'no_deberian_estar': 0,
        'aun_presentes': 0,
        'correctamente_ausentes': 0,
        'incidencias_detectadas': 0,
        'detalle': []
    }
    
    # Obtener empleados que aparecen en cada período
    empleados_actual = set(NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).values_list('rut_empleado', flat=True))
    
    empleados_anterior = set(NominaConsolidada.objects.filter(
        cierre=periodo_anterior
    ).values_list('rut_empleado', flat=True))
    
    # Los que finiquitaron el mes anterior = estaban en anterior al anterior pero no en anterior
    try:
        periodo_anterior_anterior = CierreNomina.objects.filter(
            cliente=cierre_actual.cliente,
            periodo__lt=periodo_anterior.periodo,
            estado='datos_consolidados'
        ).order_by('-periodo').first()
        
        if periodo_anterior_anterior:
            empleados_anterior_anterior = set(NominaConsolidada.objects.filter(
                cierre=periodo_anterior_anterior
            ).values_list('rut_empleado', flat=True))
            
            # Finiquitos del mes anterior
            finiquitos_mes_anterior = empleados_anterior_anterior - empleados_anterior
        else:
            # Si no hay período anterior al anterior, no podemos determinar finiquitos
            finiquitos_mes_anterior = set()
            
    except Exception as e:
        logger.warning(f"Error calculando finiquitos mes anterior: {e}")
        finiquitos_mes_anterior = set()
    
    resultado['total_finiquitos_anteriores'] = len(finiquitos_mes_anterior)
    
    # Analizar cada finiquito del mes anterior
    for rut in finiquitos_mes_anterior:
        aun_presente = rut in empleados_actual
        
        if aun_presente:
            resultado['aun_presentes'] += 1
            resultado['incidencias_detectadas'] += 1
            estado = 'INCIDENCIA - AÚN PRESENTE'
            criticidad = 'ALTA'
            es_incidencia = True
        else:
            resultado['correctamente_ausentes'] += 1
            estado = 'CORRECTAMENTE AUSENTE'
            criticidad = 'OK'
            es_incidencia = False
        
        # Obtener datos del empleado del período anterior al anterior
        try:
            periodo_anterior_anterior = CierreNomina.objects.filter(
                cliente=cierre_actual.cliente,
                periodo__lt=periodo_anterior.periodo,
                estado='datos_consolidados'
            ).order_by('-periodo').first()
            
            if periodo_anterior_anterior:
                empleado_anterior_anterior = NominaConsolidada.objects.filter(
                    cierre=periodo_anterior_anterior, 
                    rut_empleado=rut
                ).first()
                
                nombre_empleado = empleado_anterior_anterior.nombre_empleado if empleado_anterior_anterior else 'N/A'
            else:
                nombre_empleado = 'N/A'
        except:
            nombre_empleado = 'N/A'
        
        resultado['detalle'].append({
            'rut_empleado': rut,
            'nombre_empleado': nombre_empleado,
            'finiquito_detectado_en': str(periodo_anterior.periodo),
            'aun_presente_mes_actual': aun_presente,
            'estado': estado,
            'criticidad': criticidad,
            'es_incidencia': es_incidencia
        })
    
    return resultado


def _calcular_resumen_analisis(analisis):
    """
    Calcula un resumen estadístico del análisis completo
    """
    resumen = {
        'total_comparaciones': 0,
        'total_incidencias': 0,
        'total_validaciones_ok': 0,
        'porcentaje_cumplimiento': 0,
        'reglas_analizadas': 4
    }
    
    # Sumar estadísticas de cada regla
    reglas = ['variaciones_conceptos', 'ausentismos_continuos', 'ingresos_mes_anterior', 'finiquitos_mes_anterior']
    
    for regla in reglas:
        if regla in analisis:
            data = analisis[regla]
            
            # Diferentes estructuras según la regla
            if regla == 'variaciones_conceptos':
                resumen['total_comparaciones'] += data.get('total_comparaciones', 0)
                resumen['total_incidencias'] += data.get('incidencias_detectadas', 0)
                resumen['total_validaciones_ok'] += data.get('sin_cambios', 0) + data.get('variaciones_menores', 0)
            else:
                # Para ingresos y finiquitos
                total_casos = data.get('total_ingresos_anteriores', 0) + data.get('total_finiquitos_anteriores', 0)
                incidencias = data.get('incidencias_detectadas', 0)
                ok_casos = total_casos - incidencias
                
                resumen['total_comparaciones'] += total_casos
                resumen['total_incidencias'] += incidencias
                resumen['total_validaciones_ok'] += ok_casos
    
    # Calcular porcentaje de cumplimiento
    if resumen['total_comparaciones'] > 0:
        resumen['porcentaje_cumplimiento'] = round(
            (resumen['total_validaciones_ok'] / resumen['total_comparaciones']) * 100, 1
        )
    
    return resumen
