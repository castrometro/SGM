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

def detectar_incidencias_consolidadas_simple(cierre_actual):
    """
    🎯 DETECCIÓN SIMPLIFICADA DE INCIDENCIAS
    
    Enfoque directo en 2 pasos:
    1. Comparar nóminas de empleados comunes (variaciones de conceptos/montos)
    2. Revisar empleados únicos (verificar documentación de ingresos/finiquitos)
    
    Args:
        cierre_actual: CierreNomina - Cierre actual consolidado
        
    Returns:
        dict: Resultado de la detección con estadísticas
    """
    logger.info(f"🎯 Iniciando detección simplificada para {cierre_actual}")
    
    # 1. OBTENER CIERRE ANTERIOR
    cierre_anterior = CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado='finalizado'
    ).order_by('-periodo').first()
    
    if not cierre_anterior:
        logger.info(f"⚠️ No hay período anterior finalizado para {cierre_actual}")
        return {
            'success': True,
            'total_incidencias': 0,
            'incidencias_variaciones': 0,
            'incidencias_faltantes': 0,
            'mensaje': 'Sin período anterior para comparar'
        }
    
    logger.info(f"📊 Comparando {cierre_actual.periodo} vs {cierre_anterior.periodo}")
    
    # 2. OBTENER NÓMINAS DE AMBOS PERÍODOS
    nominas_actual = NominaConsolidada.objects.filter(cierre=cierre_actual)
    nominas_anterior = NominaConsolidada.objects.filter(cierre=cierre_anterior)
    
    # Crear mapas por RUT para comparación eficiente
    ruts_actual = set(nominas_actual.values_list('rut_empleado', flat=True))
    ruts_anterior = set(nominas_anterior.values_list('rut_empleado', flat=True))
    
    logger.info(f"📋 Empleados actual: {len(ruts_actual)}, anterior: {len(ruts_anterior)}")
    
    # 3. PASO 1: COMPARAR EMPLEADOS COMUNES (variaciones)
    ruts_comunes = ruts_actual & ruts_anterior
    logger.info(f"👥 Empleados comunes: {len(ruts_comunes)}")
    
    incidencias_variaciones = _comparar_nominas_empleados_comunes(
        cierre_actual, cierre_anterior, ruts_comunes
    )
    
    # 4. PASO 2: ANALIZAR EMPLEADOS ÚNICOS (diferencias)
    ruts_solo_anterior = ruts_anterior - ruts_actual  # Posibles finiquitos
    ruts_solo_actual = ruts_actual - ruts_anterior    # Posibles ingresos
    
    logger.info(f"📤 Solo en anterior: {len(ruts_solo_anterior)}, Solo en actual: {len(ruts_solo_actual)}")
    
    incidencias_faltantes = _analizar_empleados_unicos(
        cierre_actual, cierre_anterior, ruts_solo_anterior, ruts_solo_actual
    )
    
    # 5. CONSOLIDAR RESULTADOS
    total_incidencias = len(incidencias_variaciones) + len(incidencias_faltantes)
    
    # Actualizar estado del cierre
    if total_incidencias > 0:
        cierre_actual.estado = 'con_incidencias'
        cierre_actual.estado_incidencias = 'pendientes'
    else:
        cierre_actual.estado = 'incidencias_resueltas'
        cierre_actual.estado_incidencias = 'sin_incidencias'
    
    cierre_actual.total_incidencias = total_incidencias
    cierre_actual.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
    
    logger.info(f"✅ Detección completada: {len(incidencias_variaciones)} variaciones, {len(incidencias_faltantes)} faltantes")
    
    return {
        'success': True,
        'total_incidencias': total_incidencias,
        'incidencias_variaciones': len(incidencias_variaciones),
        'incidencias_faltantes': len(incidencias_faltantes),
        'ruts_comunes': len(ruts_comunes),
        'ruts_solo_anterior': len(ruts_solo_anterior),
        'ruts_solo_actual': len(ruts_solo_actual)
    }


def _comparar_nominas_empleados_comunes(cierre_actual, cierre_anterior, ruts_comunes):
    """
    Compara conceptos y montos entre empleados que existen en ambos meses
    """
    logger.info(f"🔍 Comparando {len(ruts_comunes)} empleados comunes")
    incidencias = []
    
    tolerancia_porcentaje = Decimal('30.0')  # 30% de tolerancia
    
    for rut in ruts_comunes:
        # Obtener nóminas de ambos períodos
        try:
            nomina_actual = NominaConsolidada.objects.get(cierre=cierre_actual, rut_empleado=rut)
            nomina_anterior = NominaConsolidada.objects.get(cierre=cierre_anterior, rut_empleado=rut)
        except NominaConsolidada.DoesNotExist:
            continue
        
        # Comparar conceptos consolidados
        conceptos_actual = {c.nombre_concepto: c.monto_total 
                           for c in ConceptoConsolidado.objects.filter(nomina_consolidada=nomina_actual)
                           if c.es_numerico and c.monto_total}
        
        conceptos_anterior = {c.nombre_concepto: c.monto_total 
                             for c in ConceptoConsolidado.objects.filter(nomina_consolidada=nomina_anterior)
                             if c.es_numerico and c.monto_total}
        
        # Comparar cada concepto
        todos_conceptos = set(conceptos_actual.keys()) | set(conceptos_anterior.keys())
        
        for concepto in todos_conceptos:
            monto_actual = conceptos_actual.get(concepto, Decimal('0'))
            monto_anterior = conceptos_anterior.get(concepto, Decimal('0'))
            
            # Solo comparar si hay valores significativos
            if abs(monto_anterior) < Decimal('1000'):  # Menos de $1,000 se ignora
                continue
            
            # Calcular variación
            if monto_anterior != 0:
                variacion = abs((monto_actual - monto_anterior) / monto_anterior) * 100
                
                if variacion > tolerancia_porcentaje:
                    # Crear incidencia
                    incidencia = IncidenciaCierre.objects.create(
                        cierre=cierre_actual,
                        tipo_incidencia=TipoIncidencia.VARIACION_CONCEPTO,
                        rut_empleado=rut,
                        descripcion=f"Variación {variacion:.1f}% en {concepto}: ${monto_anterior:,.0f} → ${monto_actual:,.0f}",
                        concepto_afectado=concepto,
                        valor_libro=str(monto_actual),  # Valor actual
                        valor_novedades=str(monto_anterior),  # Valor anterior
                        prioridad='media',
                        estado='pendiente',
                        impacto_monetario=abs(monto_actual - monto_anterior)
                    )
                    incidencias.append(incidencia)
    
    logger.info(f"📊 {len(incidencias)} incidencias de variación detectadas")
    return incidencias


def _analizar_empleados_unicos(cierre_actual, cierre_anterior, ruts_solo_anterior, ruts_solo_actual):
    """
    Analiza empleados que están solo en un período y verifica documentación
    """
    from ..models import AnalistaIngreso, AnalistaFiniquito
    
    logger.info(f"🔍 Analizando empleados únicos: {len(ruts_solo_anterior)} + {len(ruts_solo_actual)}")
    incidencias = []
    
    # 1. EMPLEADOS SOLO EN ANTERIOR (verificar finiquitos)
    for rut in ruts_solo_anterior:
        # Obtener información del empleado
        try:
            nomina_anterior = NominaConsolidada.objects.get(cierre=cierre_anterior, rut_empleado=rut)
        except NominaConsolidada.DoesNotExist:
            continue
        
        # Verificar si tiene finiquito documentado en el período anterior
        tiene_finiquito = AnalistaFiniquito.objects.filter(
            cierre=cierre_anterior,
            rut=rut
        ).exists()
        
        if not tiene_finiquito:
            # No tiene finiquito documentado - crear incidencia
            incidencia = IncidenciaCierre.objects.create(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,
                rut_empleado=rut,
                descripcion=f"Empleado {nomina_anterior.nombre_empleado} no está en nómina actual pero no tiene finiquito documentado en período anterior",
                concepto_afectado='finiquito_faltante',
                valor_libro='ausente',
                valor_novedades='presente_sin_finiquito',
                prioridad='alta',
                estado='pendiente'
            )
            incidencias.append(incidencia)
    
    # 2. EMPLEADOS SOLO EN ACTUAL (verificar ingresos)
    for rut in ruts_solo_actual:
        # Obtener información del empleado
        try:
            nomina_actual = NominaConsolidada.objects.get(cierre=cierre_actual, rut_empleado=rut)
        except NominaConsolidada.DoesNotExist:
            continue
        
        # Verificar si tiene ingreso documentado en el período actual
        tiene_ingreso = AnalistaIngreso.objects.filter(
            cierre=cierre_actual,
            rut=rut
        ).exists()
        
        if not tiene_ingreso:
            # No tiene ingreso documentado - crear incidencia
            incidencia = IncidenciaCierre.objects.create(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.EMPLEADO_DEBERIA_INGRESAR,
                rut_empleado=rut,
                descripcion=f"Empleado {nomina_actual.nombre_empleado} está en nómina actual pero no tiene ingreso documentado",
                concepto_afectado='ingreso_faltante',
                valor_libro='presente_sin_ingreso',
                valor_novedades='ausente',
                prioridad='alta',
                estado='pendiente'
            )
            incidencias.append(incidencia)
    
    logger.info(f"📊 {len(incidencias)} incidencias de documentación faltante detectadas")
    return incidencias


def detectar_incidencias_consolidadas(cierre_actual):
    """
    🔍 DETECCIÓN DE INCIDENCIAS: Compara el cierre actual consolidado vs el período anterior
    
    Implementa las 4 reglas principales:
    1. Variaciones de valor header-empleado superior a ±30%
    2. Ausentismos del mes anterior que deberían continuar
    3. Personas que ingresaron el mes anterior y no están presentes
    4. Personas que finiquitaron el mes anterior y siguen presentes
    """
    # Verificar que el cierre esté en un estado válido para detectar incidencias
    estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas']
    if cierre_actual.estado not in estados_validos:
        raise ValueError(f"El cierre debe estar en estado válido para detectar incidencias. Estado actual: {cierre_actual.estado}, Estados válidos: {estados_validos}")
    
    # Obtener período anterior FINALIZADO del mismo cliente (comparación directa)
    periodo_anterior = CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado='finalizado'
    ).order_by('-periodo').first()
    
    if not periodo_anterior:
        logger.info(f"⚠️ No hay período anterior FINALIZADO para {cierre_actual}. Marcando como 'sin_incidencias'")
        
        # Actualizar estado del cierre cuando no hay período anterior finalizado
        cierre_actual.estado_incidencias = 'sin_incidencias'
        cierre_actual.estado = 'incidencias_resueltas'
        cierre_actual.total_incidencias = 0
        cierre_actual.save(update_fields=['estado_incidencias', 'total_incidencias', 'estado'])
        
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
    
    # 7. Detectar finiquitos que no deberían estar presentes
    incidencias.extend(_detectar_finiquitos_presentes(cierre_actual, periodo_anterior))
    
    logger.info(f"Detectadas {len(incidencias)} incidencias entre períodos")
    return incidencias


def _detectar_variaciones_conceptos(cierre_actual, periodo_anterior, umbral=30.0):
    """
    Detecta variaciones >30% en conceptos entre períodos
    Mejorado para usar modelos de consolidación correctamente
    """
    incidencias = []
    
    # Obtener conceptos consolidados de ambos períodos
    conceptos_actual = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual,
        es_numerico=True,
        monto_total__isnull=False
    ).select_related('nomina_consolidada')
    
    conceptos_anterior = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        es_numerico=True,
        monto_total__isnull=False
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
                
                # Filtrar montos muy pequeños que pueden causar variaciones irrelevantes
                if abs(monto_anterior) < 1000 and abs(monto_actual) < 1000:
                    continue  # Saltar conceptos con montos menores a $1,000
                
                if monto_anterior != 0:  # Evitar división por cero
                    variacion_pct = ((monto_actual - monto_anterior) / abs(monto_anterior)) * 100
                    
                    if abs(variacion_pct) > umbral:
                        # Determinar prioridad según la magnitud de la variación
                        if abs(variacion_pct) > 100:
                            prioridad = 'alta'
                        elif abs(variacion_pct) > 50:
                            prioridad = 'media'
                        else:
                            prioridad = 'baja'
                        
                        # Calcular diferencia absoluta
                        diferencia_absoluta = abs(monto_actual - monto_anterior)
                        
                        incidencias.append(IncidenciaCierre(
                            cierre=cierre_actual,
                            tipo_incidencia=TipoIncidencia.VARIACION_CONCEPTO,
                            rut_empleado=concepto_actual.nomina_consolidada.rut_empleado,
                            descripcion=f"⏰ TEMPORAL: Variación {variacion_pct:+.1f}% en {concepto_actual.nombre_concepto} para {concepto_actual.nomina_consolidada.nombre_empleado} (${monto_actual:,.0f} vs ${monto_anterior:,.0f} en {periodo_anterior.periodo})",
                            concepto_afectado=concepto_actual.nombre_concepto,
                            valor_libro=str(monto_actual),  # Período actual
                            valor_novedades=str(monto_anterior),  # Período anterior
                            prioridad=prioridad,
                            impacto_monetario=Decimal(str(diferencia_absoluta))
                        ))
                elif monto_anterior == 0 and monto_actual != 0:
                    # Concepto que pasó de 0 a tener valor
                    incidencias.append(IncidenciaCierre(
                        cierre=cierre_actual,
                        tipo_incidencia=TipoIncidencia.VARIACION_CONCEPTO,
                        rut_empleado=concepto_actual.nomina_consolidada.rut_empleado,
                        descripcion=f"⏰ TEMPORAL: {concepto_actual.nombre_concepto} para {concepto_actual.nomina_consolidada.nombre_empleado} pasó de $0 a ${monto_actual:,.0f} (nuevo valor en período actual)",
                        concepto_afectado=concepto_actual.nombre_concepto,
                        valor_libro=str(monto_actual),
                        valor_novedades="0",
                        prioridad='media',
                        impacto_monetario=Decimal(str(abs(monto_actual)))
                    ))
                    
            except (ValueError, TypeError, AttributeError) as e:
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
            descripcion=f"⏰ TEMPORAL: Concepto nuevo '{nombre_concepto}' detectado en {empleados_afectados} empleados (no existía en {periodo_anterior.periodo})",
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
            descripcion=f"⏰ TEMPORAL: Concepto '{nombre_concepto}' desapareció (existía en {periodo_anterior.periodo} para {empleados_anteriores} empleados)",
            concepto_afectado=nombre_concepto,
            prioridad='alta',  # Pérdida de conceptos es más crítica
        ))
    
    return incidencias


def _detectar_empleados_deberian_ingresar(cierre_actual, periodo_anterior):
    """
    Detecta empleados que tuvieron incorporaciones en el período anterior
    pero no aparecen en el período actual - usando modelos de consolidación
    """
    incidencias = []
    
    # 1. EMPLEADOS QUE INGRESARON EN PERÍODO ANTERIOR
    ingresos_anterior = {}
    
    # A. Buscar en MovimientoPersonal por ingresos
    movimientos_ingreso = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        tipo_movimiento='ingreso'
    ).select_related('nomina_consolidada')
    
    for movimiento in movimientos_ingreso:
        rut = movimiento.nomina_consolidada.rut_empleado
        ingresos_anterior[rut] = {
            'nombre': movimiento.nomina_consolidada.nombre_empleado,
            'fecha_ingreso': movimiento.fecha_movimiento,
            'observaciones': movimiento.observaciones,
            'fuente': 'movimiento_personal'
        }
    
    # B. Buscar empleados marcados como "nueva_incorporacion" en estado consolidado
    nuevas_incorporaciones = NominaConsolidada.objects.filter(
        cierre=periodo_anterior,
        estado_empleado='nueva_incorporacion'
    )
    
    for empleado in nuevas_incorporaciones:
        rut = empleado.rut_empleado
        if rut not in ingresos_anterior:  # Evitar duplicados
            ingresos_anterior[rut] = {
                'nombre': empleado.nombre_empleado,
                'fecha_ingreso': None,
                'observaciones': f"Estado: {empleado.estado_empleado}",
                'fuente': 'estado_consolidado'
            }
    
    # 2. EMPLEADOS PRESENTES EN PERÍODO ACTUAL
    empleados_actuales = set(NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).values_list('rut_empleado', flat=True))
    
    # 3. DETECTAR INGRESOS PERDIDOS
    for rut_empleado, datos_ingreso in ingresos_anterior.items():
        if rut_empleado not in empleados_actuales:
            # Verificar si tiene finiquito documentado en el período anterior o actual
            tiene_finiquito_anterior = MovimientoPersonal.objects.filter(
                nomina_consolidada__cierre=periodo_anterior,
                nomina_consolidada__rut_empleado=rut_empleado,
                tipo_movimiento='finiquito'
            ).exists()
            
            # También verificar si estaba marcado como finiquito en estado consolidado
            if not tiene_finiquito_anterior:
                empleado_anterior = NominaConsolidada.objects.filter(
                    cierre=periodo_anterior,
                    rut_empleado=rut_empleado,
                    estado_empleado='finiquito'
                ).exists()
                tiene_finiquito_anterior = empleado_anterior
            
            # Determinar prioridad según si tiene finiquito o no
            if tiene_finiquito_anterior:
                # Tiene finiquito documentado - prioridad baja
                prioridad = 'baja'
                descripcion = f"⏰ TEMPORAL: {datos_ingreso['nombre']} ingresó en {periodo_anterior.periodo} pero tiene finiquito documentado. Verificar coherencia temporal."
            else:
                # No tiene finiquito - empleado que ingresó debería estar presente
                prioridad = 'alta'
                fecha_info = f" el {datos_ingreso['fecha_ingreso']}" if datos_ingreso['fecha_ingreso'] else ""
                descripcion = f"⏰ TEMPORAL: {datos_ingreso['nombre']} ingresó en {periodo_anterior.periodo}{fecha_info} pero no aparece en nómina actual (sin finiquito documentado)"
            
            incidencias.append(IncidenciaCierre(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.EMPLEADO_DEBERIA_INGRESAR,
                rut_empleado=rut_empleado,
                descripcion=descripcion,
                prioridad=prioridad,
            ))
    
    return incidencias


def _detectar_empleados_no_deberian_estar(cierre_actual, periodo_anterior):
    """
    Detecta empleados que aparecen en el período actual sin estar en el anterior
    y sin incorporación documentada - usando modelos de consolidación
    """
    incidencias = []
    
    # 1. EMPLEADOS EN PERÍODO ACTUAL
    empleados_actuales = NominaConsolidada.objects.filter(
        cierre=cierre_actual
    ).select_related()
    
    # 2. EMPLEADOS QUE ESTABAN EN PERÍODO ANTERIOR
    empleados_anteriores = set(NominaConsolidada.objects.filter(
        cierre=periodo_anterior
    ).values_list('rut_empleado', flat=True))
    
    # 3. ANALIZAR EMPLEADOS NUEVOS
    for empleado_actual in empleados_actuales:
        if empleado_actual.rut_empleado not in empleados_anteriores:
            # Empleado nuevo - verificar si tiene incorporación documentada
            
            # A. Verificar si tiene movimiento de ingreso documentado
            tiene_incorporacion_movimiento = MovimientoPersonal.objects.filter(
                nomina_consolidada=empleado_actual,
                tipo_movimiento='ingreso'
            ).exists()
            
            # B. Verificar si está marcado como nueva incorporación en estado
            es_nueva_incorporacion = empleado_actual.estado_empleado == 'nueva_incorporacion'
            
            # C. Verificar si tiene documentación en archivos analista
            # Buscar en ingresos del analista para este cierre
            from ..models import AnalistaIngreso
            tiene_ingreso_analista = AnalistaIngreso.objects.filter(
                cierre=cierre_actual,
                rut=empleado_actual.rut_empleado
            ).exists()
            
            # Determinar si la incorporación está bien documentada
            incorporacion_documentada = (
                tiene_incorporacion_movimiento or 
                es_nueva_incorporacion or 
                tiene_ingreso_analista
            )
            
            if not incorporacion_documentada:
                # Empleado sin documentación de ingreso
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,
                    rut_empleado=empleado_actual.rut_empleado,
                    descripcion=f"⏰ TEMPORAL: {empleado_actual.nombre_empleado} aparece en nómina sin documentación de ingreso (no estaba en {periodo_anterior.periodo} y sin registro de incorporación)",
                    prioridad='alta',
                ))
            else:
                # Empleado con documentación pero verificar coherencia
                documentacion_info = []
                if tiene_incorporacion_movimiento:
                    documentacion_info.append("movimiento de ingreso")
                if es_nueva_incorporacion:
                    documentacion_info.append("marcado como nueva incorporación")
                if tiene_ingreso_analista:
                    documentacion_info.append("archivo del analista")
                
                # Crear incidencia informativa de baja prioridad
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,
                    rut_empleado=empleado_actual.rut_empleado,
                    descripcion=f"⏰ TEMPORAL: {empleado_actual.nombre_empleado} es empleado nuevo (no estaba en {periodo_anterior.periodo}). Documentación: {', '.join(documentacion_info)}. Verificar coherencia.",
                    prioridad='baja',
                ))
    
    return incidencias


def _detectar_ausentismos_continuos(cierre_actual, periodo_anterior):
    """
    Detecta empleados con ausentismos en período anterior que cambiaron de estado
    Usa los modelos de consolidación para mejor precisión en la detección
    """
    incidencias = []
    
    # 1. EMPLEADOS CON AUSENTISMOS EN PERÍODO ANTERIOR
    # Buscar tanto en MovimientoPersonal como en estado_empleado de NominaConsolidada
    empleados_ausentes_anterior = {}
    
    # A. Ausentismos registrados como movimientos
    ausentismos_movimientos = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        tipo_movimiento='ausentismo'
    ).select_related('nomina_consolidada')
    
    for movimiento in ausentismos_movimientos:
        rut = movimiento.nomina_consolidada.rut_empleado
        empleados_ausentes_anterior[rut] = {
            'nombre': movimiento.nomina_consolidada.nombre_empleado,
            'motivo': movimiento.motivo,
            'dias_ausencia': movimiento.dias_ausencia,
            'fuente': 'movimiento_personal'
        }
    
    # B. Empleados marcados como ausentes en estado consolidado
    empleados_ausentes_estado = NominaConsolidada.objects.filter(
        cierre=periodo_anterior,
        estado_empleado__in=['ausente_total', 'ausente_parcial']
    )
    
    for empleado in empleados_ausentes_estado:
        rut = empleado.rut_empleado
        if rut not in empleados_ausentes_anterior:  # Evitar duplicados
            empleados_ausentes_anterior[rut] = {
                'nombre': empleado.nombre_empleado,
                'motivo': f"Estado: {empleado.estado_empleado}",
                'dias_ausencia': empleado.dias_ausencia,
                'fuente': 'estado_consolidado'
            }
    
    # 2. EMPLEADOS EN PERÍODO ACTUAL
    empleados_actuales = {}
    nominas_actuales = NominaConsolidada.objects.filter(
        cierre=cierre_actual
    )
    
    for nomina in nominas_actuales:
        empleados_actuales[nomina.rut_empleado] = {
            'nombre': nomina.nombre_empleado,
            'estado': nomina.estado_empleado,
            'dias_ausencia': nomina.dias_ausencia,
            'presente': True
        }
    
    # Empleados con ausentismos actuales
    ausentismos_actuales = set()
    
    # A. Por movimientos
    movimientos_actuales = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=cierre_actual,
        tipo_movimiento='ausentismo'
    ).values_list('nomina_consolidada__rut_empleado', flat=True)
    ausentismos_actuales.update(movimientos_actuales)
    
    # B. Por estado consolidado
    estados_ausentes = NominaConsolidada.objects.filter(
        cierre=cierre_actual,
        estado_empleado__in=['ausente_total', 'ausente_parcial']
    ).values_list('rut_empleado', flat=True)
    ausentismos_actuales.update(estados_ausentes)
    
    # 3. ANÁLISIS DE CONTINUIDAD DE AUSENTISMOS
    for rut_empleado, datos_anterior in empleados_ausentes_anterior.items():
        
        # Caso 1: Estaba ausente, ahora está presente y activo (reintegro no documentado)
        if rut_empleado in empleados_actuales:
            empleado_actual = empleados_actuales[rut_empleado]
            
            if (rut_empleado not in ausentismos_actuales and 
                empleado_actual['estado'] == 'activo'):
                
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.AUSENTISMO_CONTINUO,
                    rut_empleado=rut_empleado,
                    descripcion=f"⏰ TEMPORAL: {datos_anterior['nombre']} tenía ausentismo en {periodo_anterior.periodo} ({datos_anterior['motivo']}) y ahora está presente/activo. ¿Se reintegró correctamente?",
                    prioridad='media',
                ))
        
        # Caso 2: Estaba ausente, sigue ausente (verificar continuidad lógica)
        elif rut_empleado in ausentismos_actuales:
            empleado_actual = empleados_actuales[rut_empleado]
            
            # Verificar si la ausencia tiene lógica de continuidad
            motivo_anterior = datos_anterior['motivo'].lower()
            estado_actual = empleado_actual['estado']
            
            # Si era una ausencia temporal y sigue ausente mucho tiempo
            if ('parcial' in motivo_anterior or 'temporal' in motivo_anterior) and estado_actual == 'ausente_total':
                incidencias.append(IncidenciaCierre(
                    cierre=cierre_actual,
                    tipo_incidencia=TipoIncidencia.AUSENTISMO_CONTINUO,
                    rut_empleado=rut_empleado,
                    descripcion=f"⏰ TEMPORAL: {datos_anterior['nombre']} tenía ausentismo parcial/temporal en {periodo_anterior.periodo} pero ahora aparece como ausencia total. Verificar evolución.",
                    prioridad='media',
                ))
        
        # Caso 3: Estaba ausente, ahora no aparece en nómina (continuidad esperada pero verificar)
        elif rut_empleado not in empleados_actuales:
            # Verificar si tiene finiquito documentado
            tiene_finiquito = MovimientoPersonal.objects.filter(
                nomina_consolidada__cierre=cierre_actual,
                nomina_consolidada__rut_empleado=rut_empleado,
                tipo_movimiento='finiquito'
            ).exists()
            
            if not tiene_finiquito:
                # También buscar en período actual por si está en consolidación
                tiene_finiquito = MovimientoPersonal.objects.filter(
                    nomina_consolidada__cierre=periodo_anterior,
                    nomina_consolidada__rut_empleado=rut_empleado,
                    tipo_movimiento='finiquito'
                ).exists()
            
            prioridad = 'baja' if tiene_finiquito else 'media'
            finiquito_info = " (tiene finiquito documentado)" if tiene_finiquito else " (sin finiquito documentado)"
            
            incidencias.append(IncidenciaCierre(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.AUSENTISMO_CONTINUO,
                rut_empleado=rut_empleado,
                descripcion=f"⏰ TEMPORAL: {datos_anterior['nombre']} ausente desde {periodo_anterior.periodo} no aparece en nómina actual{finiquito_info}. Verificar estado.",
                prioridad=prioridad,
            ))
    
    return incidencias


def _detectar_finiquitos_presentes(cierre_actual, periodo_anterior):
    """
    Detecta empleados que finiquitaron en el período anterior
    pero aparecen en el período actual - usando modelos de consolidación
    """
    incidencias = []
    
    # 1. EMPLEADOS QUE FINIQUITARON EN PERÍODO ANTERIOR
    finiquitos_anterior = {}
    
    # A. Buscar en MovimientoPersonal por finiquitos
    movimientos_finiquito = MovimientoPersonal.objects.filter(
        nomina_consolidada__cierre=periodo_anterior,
        tipo_movimiento='finiquito'
    ).select_related('nomina_consolidada')
    
    for movimiento in movimientos_finiquito:
        rut = movimiento.nomina_consolidada.rut_empleado
        finiquitos_anterior[rut] = {
            'nombre': movimiento.nomina_consolidada.nombre_empleado,
            'fecha_finiquito': movimiento.fecha_movimiento,
            'motivo': movimiento.motivo,
            'observaciones': movimiento.observaciones,
            'fuente': 'movimiento_personal'
        }
    
    # B. Buscar empleados marcados como "finiquito" en estado consolidado
    empleados_finiquitados = NominaConsolidada.objects.filter(
        cierre=periodo_anterior,
        estado_empleado='finiquito'
    )
    
    for empleado in empleados_finiquitados:
        rut = empleado.rut_empleado
        if rut not in finiquitos_anterior:  # Evitar duplicados
            finiquitos_anterior[rut] = {
                'nombre': empleado.nombre_empleado,
                'fecha_finiquito': None,
                'motivo': f"Estado: {empleado.estado_empleado}",
                'observaciones': '',
                'fuente': 'estado_consolidado'
            }
    
    # C. Buscar también en archivos del analista (finiquitos documentados)
    from ..models import AnalistaFiniquito
    finiquitos_analista = AnalistaFiniquito.objects.filter(
        cierre=periodo_anterior
    )
    
    for finiquito in finiquitos_analista:
        rut = finiquito.rut
        if rut not in finiquitos_anterior:  # Evitar duplicados
            finiquitos_anterior[rut] = {
                'nombre': f"{finiquito.nombres} {finiquito.apellidos}",
                'fecha_finiquito': finiquito.fecha_finiquito,
                'motivo': finiquito.tipo_finiquito,
                'observaciones': finiquito.observaciones or '',
                'fuente': 'archivo_analista'
            }
    
    # 2. EMPLEADOS PRESENTES EN PERÍODO ACTUAL
    empleados_actuales = {}
    nominas_actuales = NominaConsolidada.objects.filter(
        cierre=cierre_actual
    )
    
    for nomina in nominas_actuales:
        empleados_actuales[nomina.rut_empleado] = {
            'nombre': nomina.nombre_empleado,
            'estado': nomina.estado_empleado,
            'presente': True
        }
    
    # 3. DETECTAR FINIQUITOS QUE APARECEN EN NÓMINA ACTUAL
    for rut_empleado, datos_finiquito in finiquitos_anterior.items():
        if rut_empleado in empleados_actuales:
            empleado_actual = empleados_actuales[rut_empleado]
            
            # Verificar si tiene reingreso documentado
            tiene_reingreso = MovimientoPersonal.objects.filter(
                nomina_consolidada__cierre=cierre_actual,
                nomina_consolidada__rut_empleado=rut_empleado,
                tipo_movimiento='ingreso'
            ).exists()
            
            # También verificar en archivos del analista si hay reingreso
            from ..models import AnalistaIngreso
            tiene_reingreso_analista = AnalistaIngreso.objects.filter(
                cierre=cierre_actual,
                rut=rut_empleado
            ).exists()
            
            reingreso_documentado = tiene_reingreso or tiene_reingreso_analista
            
            if reingreso_documentado:
                # Tiene reingreso documentado - incidencia informativa
                prioridad = 'baja'
                descripcion = f"⏰ TEMPORAL: {datos_finiquito['nombre']} finiquitó en {periodo_anterior.periodo} pero tiene reingreso documentado en período actual. Verificar coherencia temporal."
            else:
                # No tiene reingreso documentado - inconsistencia
                prioridad = 'alta'
                fecha_info = f" el {datos_finiquito['fecha_finiquito']}" if datos_finiquito['fecha_finiquito'] else ""
                descripcion = f"⏰ TEMPORAL: {datos_finiquito['nombre']} finiquitó en {periodo_anterior.periodo}{fecha_info} pero aparece en nómina actual sin reingreso documentado. Motivo anterior: {datos_finiquito['motivo']}"
            
            incidencias.append(IncidenciaCierre(
                cierre=cierre_actual,
                tipo_incidencia=TipoIncidencia.EMPLEADO_NO_DEBERIA_ESTAR,  # Usar el tipo existente más apropiado
                rut_empleado=rut_empleado,
                descripcion=descripcion,
                prioridad=prioridad,
            ))
    
    return incidencias


def generar_incidencias_consolidadas_task(cierre_id):
    """
    🎯 TAREA SIMPLIFICADA: Generar incidencias de un cierre consolidado
    
    Usa la nueva función simplificada que compara directamente las nóminas
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Verificar que el cierre esté en un estado válido para detectar incidencias
        estados_validos = ['datos_consolidados', 'con_incidencias', 'incidencias_resueltas']
        if cierre.estado not in estados_validos:
            raise ValueError(f"El cierre debe estar en estado válido para detectar incidencias. Estado actual: {cierre.estado}, Estados válidos: {estados_validos}")
        
        # Limpiar incidencias anteriores del cierre (sistema legacy o ejecutuciones previas)
        from ..models import IncidenciaCierre
        incidencias_existentes = IncidenciaCierre.objects.filter(cierre=cierre)
        incidencias_borradas = incidencias_existentes.count()
        if incidencias_borradas > 0:
            logger.info(f"🗑️ Limpiando {incidencias_borradas} incidencias anteriores del cierre {cierre_id}")
        
        incidencias_existentes.delete()
        logger.info(f"✅ Limpiadas {incidencias_borradas} incidencias anteriores del cierre {cierre_id}")
        
        # 🎯 USAR LA NUEVA FUNCIÓN SIMPLIFICADA
        resultado = detectar_incidencias_consolidadas_simple(cierre)
        
        if not resultado['success']:
            raise Exception(f"Error en detección simplificada: {resultado.get('error', 'Error desconocido')}")
        
        total_incidencias = resultado['total_incidencias']
        
        # Debug información
        logger.info(f"✅ Detección simplificada completada para cierre {cierre_id}:")
        logger.info(f"   📊 Total incidencias: {total_incidencias}")
        logger.info(f"   🔄 Variaciones: {resultado['incidencias_variaciones']}")
        logger.info(f"   📄 Documentación faltante: {resultado['incidencias_faltantes']}")
        logger.info(f"   � Empleados comunes: {resultado.get('ruts_comunes', 0)}")
        logger.info(f"   📤 Solo anterior: {resultado.get('ruts_solo_anterior', 0)}")
        logger.info(f"   � Solo actual: {resultado.get('ruts_solo_actual', 0)}")
        
        # Obtener incidencias creadas para información adicional
        from ..models import IncidenciaCierre
        incidencias_creadas = IncidenciaCierre.objects.filter(cierre=cierre)
        
        # Preparar respuesta según resultado
        resultado_final = {
            'success': True,
            'total_incidencias': total_incidencias,
            'estado_cierre': cierre.estado,
            'estado_incidencias': cierre.estado_incidencias,
            'incidencias_variaciones': resultado['incidencias_variaciones'],
            'incidencias_faltantes': resultado['incidencias_faltantes'],
            'empleados_comunes': resultado.get('ruts_comunes', 0),
            'empleados_solo_anterior': resultado.get('ruts_solo_anterior', 0),
            'empleados_solo_actual': resultado.get('ruts_solo_actual', 0)
        }
        
        if total_incidencias > 0:
            # Mostrar tipos de incidencias generadas
            tipos_incidencias = list(incidencias_creadas.values_list('tipo_incidencia', flat=True).distinct())
            resultado_final['tipos_detectados'] = tipos_incidencias
            resultado_final['mensaje'] = f"🔍 {total_incidencias} incidencias detectadas que requieren revisión"
            resultado_final['siguiente_accion'] = "Resolver incidencias en sistema colaborativo"
            
            # Mostrar muestra de incidencias
            logger.info("📋 Muestra de incidencias generadas:")
            for i, inc in enumerate(incidencias_creadas[:3]):
                logger.info(f"  {i+1}. {inc.tipo_incidencia}: {inc.descripcion[:100]}...")
        else:
            resultado_final['tipos_detectados'] = []
            resultado_final['mensaje'] = "✅ No se detectaron incidencias. Cierre listo para finalizar"
            resultado_final['siguiente_accion'] = "Generar informes y finalizar cierre"
            resultado_final['puede_finalizar'] = True
            logger.info("✅ No se detectaron incidencias - comparación exitosa con período anterior")
        
        return resultado_final
        
    except Exception as e:
        logger.error(f"❌ Error generando incidencias para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
