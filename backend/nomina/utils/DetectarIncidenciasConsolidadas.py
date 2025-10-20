# backend/nomina/utils/DetectarIncidenciasConsolidadas.py
"""
Sistema de detección de incidencias entre períodos consolidados de nómina
VERSIÓN 2.2: Sistema Dual con Celery Chord (ajustado a requerimientos)
- Comparación Individual (ítem por empleado) para categorías seleccionadas (haber_imponible, haber_no_imponible, otro_descuento)
- Comparación Suma Total por Ítem (agregada por ítem) para TODAS las categorías

Notas:
- Individual: limitado a haber_imponible, haber_no_imponible, otro_descuento
- Suma total por ÍTEM: habilitada para TODAS las categorías
- Suma total por CATEGORÍA: deshabilitada (solo por ítem agregado)
"""

import logging
import json
import time
from decimal import Decimal
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
from celery import shared_task, chord
from ..cache_redis import get_cache_system_nomina
from ..models import (
    CierreNomina, 
    NominaConsolidada, 
    ConceptoConsolidado, 
    MovimientoPersonal,
    EmpleadoCierre,
    IncidenciaCierre,
    TipoIncidencia
)

logger = logging.getLogger('nomina.incidencias')

# ==============================
# 🔐 Helpers de serialización
# ==============================
def _serialize_decimal(value):
    """Convierte Decimals a tipos JSON-serializables.
    - Si es entero exacto -> int
    - Si tiene decimales -> float
    - Recursivo sobre dicts/listas/tuplas/sets
    """
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            try:
                return int(value)
            except Exception:
                return float(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _serialize_decimal(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        t = type(value)
        return t(_serialize_decimal(v) for v in value)
    return value


# ================================
# 🎯 CONFIGURACIÓN - GENERACIÓN DE INCIDENCIAS
# ================================

# Umbral de variación porcentual para detectar incidencias
UMBRAL_VARIACION_PORCENTUAL = 30.0

# Tipos de concepto que se EXCLUYEN del análisis (informativos, no monetarios)
CONCEPTOS_EXCLUIDOS = [
    'informacion_adicional',  # 📄 No son montos
    'informacion',            # 📄 Variante del nombre
    'informativo',            # � Otra variante
]

# 🚨 MÉTODO SIMPLIFICADO:
# Se compara la SUMA TOTAL de cada ÍTEM (nombre_concepto + tipo_concepto)
# entre el período actual y el anterior.
# Si |variación%| ≥ 30% → Se genera incidencia
# NO se analiza empleado por empleado (comparación individual eliminada)

# ================================
# 🚀 GENERACIÓN SIMPLIFICADA DE INCIDENCIAS
# ================================

@shared_task
def generar_incidencias_consolidados_v2(cierre_id, clasificaciones_seleccionadas=None):
    """
    🎯 GENERACIÓN DE INCIDENCIAS - MÉTODO SIMPLIFICADO
    
    Compara la suma total de cada ÍTEM (nombre_concepto + tipo_concepto)
    entre el período actual y el anterior.
    
    Criterio: Si |variación%| ≥ 30% → Se genera incidencia
    
    Args:
        cierre_id: ID del cierre actual
        clasificaciones_seleccionadas: Parámetro ignorado (compatibilidad)
        
    Returns:
        dict: Resultado de la generación con estadísticas
    """
    start_time = time.time()
    
    logger.info(f"🚀 Iniciando generación simplificada de incidencias para cierre {cierre_id}")
    logger.info(f"� Método: Suma total por ÍTEM (umbral: {UMBRAL_VARIACION_PORCENTUAL}%)")
    logger.info(f"❌ Conceptos excluidos: {CONCEPTOS_EXCLUIDOS}")
    
    try:
        cierre_actual = CierreNomina.objects.get(id=cierre_id)
        cierre_anterior = obtener_cierre_anterior_finalizado(cierre_actual)
        
        # CASO 1: Primer cierre del cliente (sin comparación)
        if not cierre_anterior:
            logger.info(f"🆕 Primer cierre del cliente {cierre_actual.cliente.nombre}")
            logger.info(f"📊 Generando análisis informativo sin comparación")
            
            resultado = generar_analisis_primer_cierre_simple(cierre_actual)
            
            # Actualizar estado del cierre
            actualizar_estado_cierre_incidencias(cierre_actual, total_incidencias=0)
            
            tiempo_total = time.time() - start_time
            logger.info(f"✅ Análisis primer cierre completado en {tiempo_total:.2f}s")
            
            return resultado
        
        # CASO 2: Comparación con período anterior
        logger.info(f"📊 Comparando {cierre_actual.periodo} vs {cierre_anterior.periodo}")
        
        # Validar que haya datos consolidados
        total_consolidados = cierre_actual.nomina_consolidada.count()
        if total_consolidados == 0:
            logger.warning("⚠️ No hay empleados consolidados para procesar")
            return {
                'success': False,
                'error': 'No hay datos consolidados para analizar',
                'cierre_id': cierre_id
            }
        
        logger.info(f"� Empleados consolidados: {total_consolidados}")
        
        # PROCESAR: Comparación suma total por ítem
        resultado = procesar_incidencias_suma_total_simple(
            cierre_actual=cierre_actual,
            cierre_anterior=cierre_anterior
        )
        
        # Actualizar estado del cierre
        total_incidencias = resultado.get('total_incidencias', 0)
        actualizar_estado_cierre_incidencias(cierre_actual, total_incidencias)
        
        tiempo_total = time.time() - start_time
        resultado['tiempo_procesamiento'] = f"{tiempo_total:.2f}s"
        
        logger.info(f"✅ Generación completada en {tiempo_total:.2f}s")
        logger.info(f"   � Incidencias detectadas: {total_incidencias}")
        logger.info(f"   📊 Conceptos analizados: {resultado.get('conceptos_analizados', 0)}")
        logger.info(f"   ⚠️ Variaciones >30%: {resultado.get('variaciones_sobre_umbral', 0)}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en generación de incidencias: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }

def obtener_cierre_anterior_finalizado(cierre_actual):
    """Obtiene el cierre anterior finalizado para comparación"""
    return CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado='finalizado'
    ).order_by('-periodo').first()

def obtener_totales_por_concepto_desde_cache(cliente_id: int, periodo: str):
    """
    Intenta obtener desde Redis (InformeNomina) los totales agregados por concepto
    del período indicado. Retorna dict { (nombre, categoria) -> Decimal(total) } o None si no hay cache.
    """
    try:
        cache = get_cache_system_nomina()
        informe = cache.get_informe_nomina(cliente_id, periodo)
        if not informe:
            try:
                logger.info(f"🔎 [CACHE] MISS InformeNomina para cliente={cliente_id}, periodo={periodo}")
            except Exception:
                pass
            return None
        bloque = None
        # El informe puede estar anidado directo o bajo 'datos_cierre'
        if isinstance(informe, dict):
            bloque = informe.get('libro_resumen_v2') or (
                informe.get('datos_cierre', {}).get('libro_resumen_v2') if isinstance(informe.get('datos_cierre'), dict) else None
            )
        if not isinstance(bloque, dict):
            try:
                logger.info(f"🔎 [CACHE] InformeNomina encontrado pero sin bloque libro_resumen_v2 para cliente={cliente_id}, periodo={periodo}")
            except Exception:
                pass
            return None
        conceptos = bloque.get('conceptos') or []
        mapa = {}
        for c in conceptos:
            try:
                nombre = c.get('nombre')
                categoria = c.get('categoria')
                total = c.get('total') or 0
                if nombre and categoria is not None:
                    mapa[(nombre, categoria)] = Decimal(str(total))
            except Exception:
                continue
        try:
            logger.info(f"✅ [CACHE] HIT InformeNomina para cliente={cliente_id}, periodo={periodo} (conceptos={len(conceptos)})")
        except Exception:
            pass
        return mapa
    except Exception:
        return None

# ================================
# 🎯 PROCESAMIENTO SIMPLIFICADO
# ================================

def procesar_incidencias_suma_total_simple(cierre_actual, cierre_anterior):
    """
    📊 PROCESAMIENTO SIMPLIFICADO DE INCIDENCIAS
    
    Compara la suma total de cada ÍTEM entre dos períodos.
    Genera incidencia si |variación%| ≥ 30%
    
    Args:
        cierre_actual: CierreNomina del período actual
        cierre_anterior: CierreNomina del período anterior
        
    Returns:
        dict: Estadísticas del procesamiento
    """
    incidencias_creadas = []
    conceptos_analizados = 0
    variaciones_sobre_umbral = 0
    conceptos_excluidos_count = 0
    
    # Obtener versión del cierre para trazabilidad
    cierre_version = cierre_actual.version_datos or 1
    
    # Obtener todos los conceptos únicos de ambos períodos
    conceptos_actuales = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual
    ).values('nombre_concepto', 'tipo_concepto').distinct()
    
    conceptos_anteriores = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_anterior
    ).values('nombre_concepto', 'tipo_concepto').distinct()
    
    # Unir todos los conceptos únicos
    conceptos_unicos = set()
    for c in conceptos_actuales:
        conceptos_unicos.add((c['nombre_concepto'], c['tipo_concepto']))
    for c in conceptos_anteriores:
        conceptos_unicos.add((c['nombre_concepto'], c['tipo_concepto']))
    
    logger.info(f"📊 Analizando {len(conceptos_unicos)} ítems únicos (umbral: {UMBRAL_VARIACION_PORCENTUAL}%)")
    
    # Procesar cada concepto único
    for nombre_concepto, tipo_concepto in conceptos_unicos:
        # EXCLUIR conceptos informativos
        if tipo_concepto in CONCEPTOS_EXCLUIDOS:
            conceptos_excluidos_count += 1
            continue
        
        # Calcular suma total en período actual
        suma_actual = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre=cierre_actual,
            nombre_concepto=nombre_concepto,
            tipo_concepto=tipo_concepto
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # Calcular suma total en período anterior
        suma_anterior = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre=cierre_anterior,
            nombre_concepto=nombre_concepto,
            tipo_concepto=tipo_concepto
        ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
        
        # Calcular variación porcentual
        variacion_pct = calcular_variacion_porcentual(suma_actual, suma_anterior)
        conceptos_analizados += 1
        
        # Verificar si supera el umbral
        if abs(variacion_pct) >= UMBRAL_VARIACION_PORCENTUAL:
            variaciones_sobre_umbral += 1
            
            # Crear incidencia
            incidencia = crear_incidencia_suma_total(
                cierre_id=cierre_actual.id,
                nombre_concepto=nombre_concepto,
                tipo_concepto=tipo_concepto,
                suma_actual=suma_actual,
                suma_anterior=suma_anterior,
                variacion_pct=variacion_pct
            )
            
            incidencias_creadas.append(incidencia)
    
    # Guardar todas las incidencias en batch
    if incidencias_creadas:
        IncidenciaCierre.objects.bulk_create(incidencias_creadas, ignore_conflicts=True)
        logger.info(f"✅ Creadas {len(incidencias_creadas)} incidencias en base de datos")
    
    # Estadísticas de incidencias por prioridad
    incidencias_criticas = sum(1 for inc in incidencias_creadas if inc.prioridad == 'critica')
    incidencias_alta = sum(1 for inc in incidencias_creadas if inc.prioridad == 'alta')
    incidencias_media = sum(1 for inc in incidencias_creadas if inc.prioridad == 'media')
    incidencias_baja = sum(1 for inc in incidencias_creadas if inc.prioridad == 'baja')
    
    # Tipos de incidencias detectadas
    tipos_detectados = list(set(inc.tipo_incidencia for inc in incidencias_creadas))
    
    return {
        'success': True,
        'cierre_id': cierre_actual.id,
        'total_incidencias': len(incidencias_creadas),
        'conceptos_analizados': conceptos_analizados,
        'conceptos_excluidos': conceptos_excluidos_count,
        'variaciones_sobre_umbral': variaciones_sobre_umbral,
        'umbral_usado': UMBRAL_VARIACION_PORCENTUAL,
        'prioridades': {
            'critica': incidencias_criticas,
            'alta': incidencias_alta,
            'media': incidencias_media,
            'baja': incidencias_baja
        },
        'tipos_detectados': tipos_detectados,
        'periodo_actual': cierre_actual.periodo,
        'periodo_anterior': cierre_anterior.periodo
    }

def generar_analisis_primer_cierre_simple(cierre_actual):
    """
    📊 ANÁLISIS INFORMATIVO PARA PRIMER CIERRE
    
    Genera estadísticas descriptivas cuando no hay período anterior para comparar
    
    Args:
        cierre_actual: CierreNomina del primer período
        
    Returns:
        dict: Estadísticas del primer cierre
    """
    total_empleados = cierre_actual.nomina_consolidada.count()
    
    # Obtener estadísticas de conceptos
    conceptos = ConceptoConsolidado.objects.filter(
        nomina_consolidada__cierre=cierre_actual
    ).values('tipo_concepto').annotate(
        total_monto=Sum('monto_total'),
        cantidad=Count('id')
    )
    
    estadisticas_conceptos = {}
    for c in conceptos:
        if c['tipo_concepto'] not in CONCEPTOS_EXCLUIDOS:
            estadisticas_conceptos[c['tipo_concepto']] = {
                'total': float(c['total_monto'] or 0),
                'cantidad': c['cantidad']
            }
    
    logger.info(f"📊 Primer cierre: {total_empleados} empleados, {len(estadisticas_conceptos)} tipos de conceptos")
    
    return {
        'success': True,
        'cierre_id': cierre_actual.id,
        'primer_cierre': True,
        'total_empleados': total_empleados,
        'estadisticas_conceptos': estadisticas_conceptos,
        'total_incidencias': 0,
        'mensaje': 'Primer cierre del cliente - Sin comparación'
    }

def calcular_variacion_porcentual(valor_actual, valor_anterior):
    """Calcula variación porcentual entre dos valores"""
    if valor_anterior == 0:
        return 100.0 if valor_actual > 0 else 0.0
    
    return ((valor_actual - valor_anterior) / valor_anterior) * 100

def actualizar_estado_cierre_incidencias(cierre, total_incidencias):
    """Actualiza el estado del cierre según las incidencias detectadas"""
    if total_incidencias > 0:
        cierre.estado = 'con_incidencias'
        logger.info(f"📌 Estado actualizado a 'con_incidencias' ({total_incidencias} detectadas)")
    else:
        cierre.estado = 'incidencias_resueltas'
        logger.info(f"✅ Estado actualizado a 'incidencias_resueltas' (0 incidencias)")
    
    cierre.save(update_fields=['estado'])
    return cierre

# ================================
# 🔍 COMPARACIÓN INDIVIDUAL (DEPRECATED - Comentado para referencia)
# ================================
# Las siguientes funciones están comentadas porque ya NO se usa comparación individual
# Solo se mantienen para referencia histórica

@shared_task
def procesar_chunk_comparacion_individual(empleados_ids, cierre_actual_id, cierre_anterior_id, 
                                        clasificaciones_seleccionadas, chunk_id):
    """
    🔍 COMPARACIÓN ELEMENTO A ELEMENTO
    
    Procesa un chunk de empleados comparando conceptos individuales
    SOLO para clasificaciones con checkbox marcado
    
    Args:
        empleados_ids: Lista de IDs de empleados a procesar
        cierre_actual_id: ID del cierre actual
        cierre_anterior_id: ID del cierre anterior
        clasificaciones_seleccionadas: Tipos de conceptos para analizar
        chunk_id: Identificador del chunk para logging
        
    Returns:
        dict: Estadísticas del procesamiento del chunk
    """
    start_time = time.time()
    incidencias_detectadas = []
    eventos_informativos = []  # p.ej., ingresos de empleados nuevos
    # Métricas de diagnóstico
    empleados_con_match = 0
    empleados_sin_match = 0
    conceptos_comparados = 0
    comparaciones_superan_umbral = 0
    DEBUG_MAX_SAMPLES = 10
    debug_samples = []
    
    logger.info(f"🔍 {chunk_id}: Iniciando comparación individual")
    logger.info(f"   👥 Empleados: {len(empleados_ids)}")
    logger.info(f"   📋 Clasificaciones: {clasificaciones_seleccionadas}")
    
    try:
        # Obtener versión de datos del cierre (vN) y cache de empleados para referencias
        try:
            cierre_version = CierreNomina.objects.values_list('version_datos', flat=True).get(id=cierre_actual_id) or 1
        except Exception:
            cierre_version = 1
        cache_empleado_libro = {}

        def _empleado_libro_id(rut: str):
            if not rut:
                return None
            rid = cache_empleado_libro.get(rut)
            if rid is not None:
                return rid
            rid = EmpleadoCierre.objects.filter(cierre_id=cierre_actual_id, rut=rut).values_list('id', flat=True).first()
            cache_empleado_libro[rut] = rid
            return rid

        def _preparar_incidencia(inc: IncidenciaCierre, rut: str):
            """Completa firma, versiones y referencia empleado_libro antes de agregar al batch."""
            try:
                # Firma
                clave, h = inc.generar_firma()
                inc.firma_clave = inc.firma_clave or clave
                inc.firma_hash = inc.firma_hash or h
                # Versiones
                if not inc.version_detectada_primera:
                    inc.version_detectada_primera = cierre_version
                inc.version_detectada_ultima = cierre_version
                # Referencia empleado
                if rut and not inc.empleado_libro_id:
                    inc.empleado_libro_id = _empleado_libro_id(rut)
            except Exception:
                pass
            return inc
        for empleado_consolidado_id in empleados_ids:
            empleado_actual = NominaConsolidada.objects.select_related('cierre').get(
                id=empleado_consolidado_id
            )
            
            # Buscar empleado equivalente en período anterior
            empleado_anterior = NominaConsolidada.objects.filter(
                cierre_id=cierre_anterior_id,
                rut_empleado=empleado_actual.rut_empleado
            ).first()
            
            # Para nuestra lógica: si no hay empleado anterior, trataremos todos los conceptos como vs 0
            empleados_con_match += 1 if empleado_anterior else 0
            empleados_sin_match += 1 if not empleado_anterior else 0

            # === NUEVAS INCIDENCIAS DE PRESENCIA/ALTA/BAJA ===
            # 1) Empleado aparece en cierre actual, pero en el cierre anterior tiene finiquito → finiquito_no_aplicado
            try:
                if empleado_anterior:
                    tuvo_finiquito = MovimientoPersonal.objects.filter(
                        nomina_consolidada=empleado_anterior,
                        categoria='finiquito'
                    ).exists()
                    if tuvo_finiquito:
                        incidencias_detectadas.append(
                            _preparar_incidencia(IncidenciaCierre(
                                cierre_id=cierre_actual_id,
                                rut_empleado=empleado_actual.rut_empleado,
                                empleado_nombre=empleado_actual.nombre_empleado,
                                tipo_incidencia='finiquito_no_aplicado',
                                tipo_comparacion='individual',
                                prioridad='alta',
                                concepto_afectado='Estado del empleado',
                                descripcion=f"Empleado con finiquito en {empleado_anterior.cierre.periodo} aparece en el cierre actual",
                                impacto_monetario=Decimal('0'),
                                datos_adicionales={
                                    'alcance': 'empleado',
                                    'categoria_concepto': 'movimiento_personal',
                                    'tipo_comparacion': 'individual',
                                    'periodo_finiquito': empleado_anterior.cierre.periodo,
                                    'rut': empleado_actual.rut_empleado,
                                    'empleado': empleado_actual.nombre_empleado,
                                }
                            ), empleado_actual.rut_empleado)
                        )
            except Exception:
                # No bloquear el resto por este chequeo
                pass

            # 2) Empleado NO existe en cierre anterior: verificar que tenga registro de ingreso en actual o anterior → si no, ingreso_no_informado
            try:
                if not empleado_anterior:
                    ingreso_actual = MovimientoPersonal.objects.filter(
                        nomina_consolidada=empleado_actual,
                        categoria='ingreso'
                    ).exists()
                    ingreso_en_anterior = MovimientoPersonal.objects.filter(
                        nomina_consolidada__cierre_id=cierre_anterior_id,
                        nomina_consolidada__rut_empleado=empleado_actual.rut_empleado,
                        categoria='ingreso'
                    ).exists()
                    if not ingreso_actual and not ingreso_en_anterior:
                        incidencias_detectadas.append(
                            _preparar_incidencia(IncidenciaCierre(
                                cierre_id=cierre_actual_id,
                                rut_empleado=empleado_actual.rut_empleado,
                                empleado_nombre=empleado_actual.nombre_empleado,
                                tipo_incidencia='ingreso_no_informado',
                                tipo_comparacion='individual',
                                prioridad='alta',
                                concepto_afectado='Estado del empleado',
                                descripcion='Empleado presente sin registro de ingreso informado',
                                impacto_monetario=Decimal('0'),
                                datos_adicionales={
                                    'alcance': 'empleado',
                                    'categoria_concepto': 'movimiento_personal',
                                    'tipo_comparacion': 'individual',
                                    'periodo_actual': empleado_actual.cierre.periodo,
                                    'rut': empleado_actual.rut_empleado,
                                    'empleado': empleado_actual.nombre_empleado,
                                }
                            ), empleado_actual.rut_empleado)
                        )
            except Exception:
                pass

            # Cargar conceptos actuales y anteriores, solo de las clasificaciones seleccionadas
            conceptos_actuales_qs = ConceptoConsolidado.objects.filter(
                nomina_consolidada=empleado_actual,
                tipo_concepto__in=clasificaciones_seleccionadas
            ).values('nombre_concepto', 'tipo_concepto', 'monto_total')

            anteriores_qs = ConceptoConsolidado.objects.filter(
                nomina_consolidada=empleado_anterior
            ).values('nombre_concepto', 'tipo_concepto', 'monto_total') if empleado_anterior else []

            mapa_actual = { (c['nombre_concepto'], c['tipo_concepto']): c['monto_total'] for c in conceptos_actuales_qs }
            mapa_anterior = { (c['nombre_concepto'], c['tipo_concepto']): c['monto_total'] for c in anteriores_qs if c['tipo_concepto'] in clasificaciones_seleccionadas }

            # Si el empleado es NUEVO (no existía en el cierre anterior), queremos:
            # - NO crear incidencias de variación individual (vs 0)
            # - Crear registros informativos por concepto para mostrarlos en el front como "Ingreso"
            if not empleado_anterior:
                try:
                    for (nombre_concepto, tipo_concepto), monto_act in mapa_actual.items():
                        eventos_informativos.append(
                            _preparar_incidencia(IncidenciaCierre(
                                cierre_id=cierre_actual_id,
                                rut_empleado=empleado_actual.rut_empleado,
                                empleado_nombre=empleado_actual.nombre_empleado,
                                tipo_incidencia='ingreso_empleado',  # informativo
                                tipo_comparacion='individual',  # se mostrará en detalle pero será filtrado en KPIs/front
                                estado='resuelta_analista',  # No requiere aprobación
                                prioridad='baja',
                                concepto_afectado=nombre_concepto,
                                descripcion=f'Ingreso del empleado (nuevo en período) para {nombre_concepto}',
                                impacto_monetario=Decimal(monto_act or 0),
                                datos_adicionales={
                                    'alcance': 'empleado',
                                    'categoria_concepto': tipo_concepto,
                                    'concepto': nombre_concepto,
                                    'tipo_concepto': tipo_concepto,
                                    'monto_actual': float(monto_act or 0),
                                    'monto_anterior': 0.0,
                                    'variacion_porcentual': 100.0 if (monto_act or 0) > 0 else 0.0,
                                    'tipo_comparacion': 'individual',
                                    'informativo': True
                                }
                            ), empleado_actual.rut_empleado)
                        )
                except Exception:
                    pass

            # Unión de conceptos
            todas_claves = set(mapa_actual.keys()) | set(mapa_anterior.keys())

            if not todas_claves and len(debug_samples) < DEBUG_MAX_SAMPLES:
                # Muestreo cuando no hay claves que comparar para este empleado
                try:
                    logger.debug(
                        f"🔎 {chunk_id}: Sin claves a comparar para empleado {empleado_actual.rut_empleado}. "
                        f"Actual={list(mapa_actual.keys())[:5]} Anterior={list(mapa_anterior.keys())[:5]}"
                    )
                except Exception:
                    pass

            for (nombre_concepto, tipo_concepto) in todas_claves:
                # Si el empleado es nuevo, saltar la creación de incidencias de variación
                if not empleado_anterior:
                    continue
                monto_act = mapa_actual.get((nombre_concepto, tipo_concepto), Decimal('0'))
                monto_ant = mapa_anterior.get((nombre_concepto, tipo_concepto), Decimal('0'))

                variacion_pct = calcular_variacion_porcentual(monto_act, monto_ant)
                try:
                    variacion_pct_f = float(variacion_pct)
                except Exception:
                    variacion_pct_f = 0.0
                umbral = obtener_umbral_individual(tipo_concepto)
                conceptos_comparados += 1

                if abs(variacion_pct_f) >= umbral:
                    comparaciones_superan_umbral += 1
                    # Crear una incidencia sintética con valores actuales/anterior
                    # Creamos objetos ligeros para usar el factory existente
                    class _Obj:
                        pass
                    obj_actual = _Obj(); obj_anterior = _Obj()
                    obj_actual.nombre_concepto = nombre_concepto
                    obj_actual.tipo_concepto = tipo_concepto
                    obj_actual.monto_total = Decimal(monto_act)
                    obj_anterior.nombre_concepto = nombre_concepto
                    obj_anterior.tipo_concepto = tipo_concepto
                    obj_anterior.monto_total = Decimal(monto_ant)

                    incidencias_detectadas.append(
                        _preparar_incidencia(IncidenciaCierre(
                            cierre_id=cierre_actual_id,
                            rut_empleado=empleado_actual.rut_empleado,
                            empleado_nombre=empleado_actual.nombre_empleado,
                            tipo_incidencia='variacion_concepto_individual',
                            tipo_comparacion='individual',
                            prioridad=determinar_prioridad_individual(variacion_pct_f),
                            concepto_afectado=nombre_concepto,
                            descripcion=f'Variación {variacion_pct_f:.1f}% en {nombre_concepto}',
                            impacto_monetario=abs(Decimal(monto_act) - Decimal(monto_ant)),
                            datos_adicionales={
                                'alcance': 'empleado',
                                'categoria_concepto': tipo_concepto,
                                'concepto': nombre_concepto,
                                'tipo_concepto': tipo_concepto,
                                'monto_actual': float(monto_act),
                                'monto_anterior': float(monto_ant),
                                'variacion_porcentual': round(variacion_pct_f, 2),
                                'variacion_absoluta': float(abs(Decimal(monto_act) - Decimal(monto_ant))),
                                'tipo_comparacion': 'individual'
                            }
                        ), empleado_actual.rut_empleado)
                    )

                if len(debug_samples) < DEBUG_MAX_SAMPLES:
                    try:
                        debug_samples.append({
                            'empleado': empleado_actual.rut_empleado,
                            'concepto': nombre_concepto,
                            'tipo_concepto': tipo_concepto,
                            'monto_actual': float(monto_act),
                            'monto_anterior': float(monto_ant),
                            'variacion_pct': round(float(variacion_pct), 4) if monto_ant != 0 or monto_act != 0 else 0.0,
                            'umbral_usado': umbral,
                            'dispara_incidencia': abs(variacion_pct_f) >= umbral
                        })
                    except Exception:
                        pass
        
        # Batch insert optimizado
        if incidencias_detectadas or eventos_informativos:
            IncidenciaCierre.objects.bulk_create(
                incidencias_detectadas + eventos_informativos,
                batch_size=100,
                ignore_conflicts=True
            )
        
        tiempo_procesamiento = time.time() - start_time
        
        # Logs de diagnóstico
        if debug_samples:
            try:
                logger.debug(
                    f"🔎 {chunk_id}: Muestras de comparaciones (máx {DEBUG_MAX_SAMPLES}):\n"
                    + json.dumps(debug_samples, ensure_ascii=False, indent=2, default=str)
                )
            except Exception:
                logger.debug(f"🔎 {chunk_id}: Muestras de comparaciones no serializables")

        resultado = {
            'chunk_id': chunk_id,
            'tipo_comparacion': 'individual',
            'empleados_procesados': len(empleados_ids),
            'incidencias_detectadas': len(incidencias_detectadas),
            'tiempo_procesamiento': round(tiempo_procesamiento, 2),
            'throughput': round(len(empleados_ids) / tiempo_procesamiento, 2) if tiempo_procesamiento > 0 else 0,
            'clasificaciones_analizadas': clasificaciones_seleccionadas,
            'diag': {
                'empleados_con_match': empleados_con_match,
                'empleados_sin_match': empleados_sin_match,
                'conceptos_comparados': conceptos_comparados,
                'comparaciones_superan_umbral': comparaciones_superan_umbral,
                'umbral_individual': obtener_umbral_individual('cualquiera')
            }
        }
        
        logger.info(
            f"✅ {chunk_id}: {len(incidencias_detectadas)} incs individuales | "
            f"empleados match: {empleados_con_match}, sin_match: {empleados_sin_match}, "
            f"comparaciones: {conceptos_comparados}, sobre_umbral: {comparaciones_superan_umbral} | "
            f"t={tiempo_procesamiento:.2f}s ({resultado['throughput']} emp/s), umbral={resultado['diag']['umbral_individual']}%"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en {chunk_id}: {str(e)}")
        return {
            'chunk_id': chunk_id,
            'error': str(e),
            'tipo_comparacion': 'individual',
            'empleados_procesados': 0,
            'incidencias_detectadas': 0
        }

# ================================
# 📊 COMPARACIÓN SUMA TOTAL  
# ================================

@shared_task  
def procesar_comparacion_suma_total(cierre_actual_id, cierre_anterior_id, task_id):
    """
    📊 COMPARACIÓN SUMA TOTAL
    
    Compara las sumas totales por concepto entre dos cierres. Solo genera
    incidencias por variación porcentual que supere el umbral. No se generan
    incidencias por "concepto nuevo" o "concepto eliminado" a este nivel.
    """
    start_time = time.time()
    incidencias_detectadas = []
    conceptos_analizados = 0
    categorias_analizadas = 0
    variaciones_sobre_umbral = 0
    variaciones_categoria_sobre_umbral = 0
    DEBUG_TOP_N = 10
    variaciones_detalle = []

    logger.info(f"📊 {task_id}: Iniciando comparación suma total por ÍTEM (TODAS las categorías)")

    try:
        try:
            cierre_version = CierreNomina.objects.values_list('version_datos', flat=True).get(id=cierre_actual_id) or 1
        except Exception:
            cierre_version = 1
        # 1) Comparación por concepto (ítem específico agregado sobre empleados) — ACTIVADO (todas las categorías)
        conceptos_unicos = set()
        if GENERAR_INCIDENCIAS_SUMA_TOTAL_POR_CONCEPTO:
            # Alcance ampliado: considerar todos los tipo_concepto presentes
            conceptos_actuales = ConceptoConsolidado.objects.filter(
                nomina_consolidada__cierre_id=cierre_actual_id,
            ).values('nombre_concepto', 'tipo_concepto').distinct()
            # Intentar obtener conjunto y totales del periodo anterior desde Redis (InformeNomina)
            cierre_actual = CierreNomina.objects.get(id=cierre_actual_id)
            cierre_anterior = CierreNomina.objects.get(id=cierre_anterior_id)
            mapa_prev_cache = obtener_totales_por_concepto_desde_cache(cierre_anterior.cliente_id, cierre_anterior.periodo)
            prev_period_cache_used = mapa_prev_cache is not None
            if prev_period_cache_used:
                try:
                    logger.info(f"🧠 [CACHE] Usando totales del periodo anterior desde cache para {cierre_anterior.periodo}")
                except Exception:
                    pass
            if mapa_prev_cache is None:
                conceptos_anteriores = ConceptoConsolidado.objects.filter(
                    nomina_consolidada__cierre_id=cierre_anterior_id,
                ).values('nombre_concepto', 'tipo_concepto').distinct()
            else:
                conceptos_anteriores = (
                    {'nombre_concepto': n, 'tipo_concepto': t} for (n, t) in mapa_prev_cache.keys()
                )

            for c in conceptos_actuales:
                conceptos_unicos.add((c['nombre_concepto'], c['tipo_concepto']))
            for c in conceptos_anteriores:
                conceptos_unicos.add((c['nombre_concepto'], c['tipo_concepto']))

            logger.info(
                f"📊 Analizando {len(conceptos_unicos)} ítems únicos (umbral={obtener_umbral_suma_total('cualquiera')}%)"
            )

            for nombre_concepto, tipo_concepto in conceptos_unicos:
                # No generar incidencias agregadas por ítem para categorías con análisis individual
                if tipo_concepto in CONCEPTOS_ANALISIS_DETALLADO:
                    continue
                suma_actual = ConceptoConsolidado.objects.filter(
                    nomina_consolidada__cierre_id=cierre_actual_id,
                    nombre_concepto=nombre_concepto,
                    tipo_concepto=tipo_concepto
                ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
                # Anterior: preferir cache del InformeNomina del período anterior
                if mapa_prev_cache is not None:
                    suma_anterior = mapa_prev_cache.get((nombre_concepto, tipo_concepto), Decimal('0'))
                else:
                    suma_anterior = ConceptoConsolidado.objects.filter(
                        nomina_consolidada__cierre_id=cierre_anterior_id,
                        nombre_concepto=nombre_concepto,
                        tipo_concepto=tipo_concepto
                    ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')

                variacion_pct = calcular_variacion_porcentual(suma_actual, suma_anterior)
                umbral_suma = obtener_umbral_suma_total(tipo_concepto)
                conceptos_analizados += 1

                if abs(variacion_pct) >= umbral_suma:
                    variaciones_sobre_umbral += 1
                    inc_tmp = crear_incidencia_suma_total(
                            cierre_actual_id,
                            nombre_concepto,
                            tipo_concepto,
                            suma_actual,
                            suma_anterior,
                            variacion_pct,
                        )
                    # Completar firma/version antes de batch
                    clave, h = inc_tmp.generar_firma()
                    inc_tmp.firma_clave = inc_tmp.firma_clave or clave
                    inc_tmp.firma_hash = inc_tmp.firma_hash or h
                    if not inc_tmp.version_detectada_primera:
                        inc_tmp.version_detectada_primera = cierre_version
                    inc_tmp.version_detectada_ultima = cierre_version
                    incidencias_detectadas.append(inc_tmp)

                # Mantener detalle para top-N debug
                try:
                    variaciones_detalle.append({
                        'concepto': nombre_concepto,
                        'tipo_concepto': tipo_concepto,
                        'suma_actual': float(suma_actual),
                        'suma_anterior': float(suma_anterior),
                        'variacion_pct': round(float(variacion_pct), 4),
                        'umbral_usado': umbral_suma,
                        'dispara_incidencia': abs(variacion_pct) >= umbral_suma,
                    })
                except Exception:
                    pass

        # 2) Comparación por CATEGORÍA (total categoría) — DESACTIVADA por requerimiento
        if GENERAR_INCIDENCIAS_SUMA_TOTAL_POR_CATEGORIA:
            CATEGORIAS = [
                'haber_imponible',
                'haber_no_imponible',
                'descuento_legal',
                'otro_descuento',
                'impuesto',
                'aporte_patronal',
            ]
            cat_tot_act = {}
            cat_tot_ant = {}
            for categoria in CATEGORIAS:
                suma_cat_actual = ConceptoConsolidado.objects.filter(
                    nomina_consolidada__cierre_id=cierre_actual_id,
                    tipo_concepto=categoria,
                ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')

                suma_cat_anterior = ConceptoConsolidado.objects.filter(
                    nomina_consolidada__cierre_id=cierre_anterior_id,
                    tipo_concepto=categoria,
                ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')

                cat_tot_act[categoria] = suma_cat_actual
                cat_tot_ant[categoria] = suma_cat_anterior

                variacion_pct_cat = calcular_variacion_porcentual(suma_cat_actual, suma_cat_anterior)
                umbral_cat = obtener_umbral_suma_total(categoria)
                categorias_analizadas += 1

                if abs(variacion_pct_cat) >= umbral_cat:
                    variaciones_categoria_sobre_umbral += 1
                    incidencias_detectadas.append(
                        crear_incidencia_suma_total_categoria(
                            cierre_actual_id,
                            categoria,
                            suma_cat_actual,
                            suma_cat_anterior,
                            variacion_pct_cat,
                        )
                    )

            # Variación del TOTAL (Total Líquido = Haberes - Descuentos - Impuestos)
            hab_imp_act = cat_tot_act.get('haber_imponible', Decimal('0'))
            hab_no_imp_act = cat_tot_act.get('haber_no_imponible', Decimal('0'))
            dcto_legal_act = cat_tot_act.get('descuento_legal', Decimal('0'))
            otro_dcto_act = cat_tot_act.get('otro_descuento', Decimal('0'))
            impuesto_act = cat_tot_act.get('impuesto', Decimal('0'))

            hab_imp_ant = cat_tot_ant.get('haber_imponible', Decimal('0'))
            hab_no_imp_ant = cat_tot_ant.get('haber_no_imponible', Decimal('0'))
            dcto_legal_ant = cat_tot_ant.get('descuento_legal', Decimal('0'))
            otro_dcto_ant = cat_tot_ant.get('otro_descuento', Decimal('0'))
            impuesto_ant = cat_tot_ant.get('impuesto', Decimal('0'))

            total_liquido_act = (hab_imp_act + hab_no_imp_act) - (dcto_legal_act + otro_dcto_act + impuesto_act)
            total_liquido_ant = (hab_imp_ant + hab_no_imp_ant) - (dcto_legal_ant + otro_dcto_ant + impuesto_ant)

            variacion_pct_total = calcular_variacion_porcentual(total_liquido_act, total_liquido_ant)
            umbral_total = obtener_umbral_suma_total('total_liquido')
            if abs(variacion_pct_total) >= umbral_total:
                variaciones_categoria_sobre_umbral += 1
                incidencias_detectadas.append(
                    crear_incidencia_suma_total_categoria(
                        cierre_actual_id,
                        'total_liquido',
                        total_liquido_act,
                        total_liquido_ant,
                        variacion_pct_total,
                    )
                )

        # 3) No se consideran conceptos nuevos/eliminados a este nivel
        conceptos_solo_actual = set()
        conceptos_solo_anterior = set()

        if incidencias_detectadas:
            IncidenciaCierre.objects.bulk_create(
                incidencias_detectadas, batch_size=100, ignore_conflicts=True
            )

        tiempo_procesamiento = time.time() - start_time

        # Top-N variaciones por |variacion_pct| (ítems agregados)
        if variaciones_detalle:
            try:
                top_variaciones = sorted(
                    variaciones_detalle,
                    key=lambda x: abs(x.get('variacion_pct', 0)),
                    reverse=True,
                )[:DEBUG_TOP_N]
                logger.debug(
                    "🔎 Top variaciones (suma total):\n"
                    + json.dumps(top_variaciones, ensure_ascii=False, indent=2, default=str)
                )
            except Exception:
                logger.debug("🔎 Top variaciones (suma total): no serializables")

        resultado = {
            'task_id': task_id,
            'tipo_comparacion': 'suma_total',
            'conceptos_analizados': conceptos_analizados,
            'incidencias_detectadas': len(incidencias_detectadas),
            'conceptos_nuevos': len(conceptos_solo_actual),
            'conceptos_eliminados': len(conceptos_solo_anterior),
            'tiempo_procesamiento': round(tiempo_procesamiento, 2),
            'prev_period_cache_used': prev_period_cache_used,
            'diag': {
                'comparaciones_realizadas': conceptos_analizados,
                'variaciones_sobre_umbral': variaciones_sobre_umbral,
                'categorias_analizadas': categorias_analizadas,
                'variaciones_categoria_sobre_umbral': variaciones_categoria_sobre_umbral,
                'umbral_suma_total': obtener_umbral_suma_total('cualquiera'),
            },
        }

        logger.info(
            f"✅ {task_id}: {len(incidencias_detectadas)} incs suma_total_por_item | "
            f"comparaciones: {conceptos_analizados}, sobre_umbral: {variaciones_sobre_umbral}, "
            f"categorias_eval: {categorias_analizadas if GENERAR_INCIDENCIAS_SUMA_TOTAL_POR_CATEGORIA else 0}, "
            f"cat_sobre_umbral: {variaciones_categoria_sobre_umbral if GENERAR_INCIDENCIAS_SUMA_TOTAL_POR_CATEGORIA else 0}, "
            f"nuevos: {len(conceptos_solo_actual)}, eliminados: {len(conceptos_solo_anterior)} | "
            f"t={tiempo_procesamiento:.2f}s, umbral={resultado['diag']['umbral_suma_total']}%"
        )
        if GENERAR_INCIDENCIAS_SUMA_TOTAL_POR_CONCEPTO:
            logger.info(f"   📊 {len(conceptos_unicos)} ítems únicos analizados (todas las categorías)")
            try:
                logger.info(f"   🧠 Cache periodo anterior utilizado: {prev_period_cache_used}")
            except Exception:
                pass

        return resultado

    except Exception as e:
        logger.error(f"❌ Error en comparación suma total: {str(e)}")
        return {
            'task_id': task_id,
            'error': str(e),
            'tipo_comparacion': 'suma_total',
            'conceptos_analizados': 0,
            'incidencias_detectadas': 0,
        }

# ================================
# 🎯 CONSOLIDACIÓN FINAL
# ================================

@shared_task
def consolidar_resultados_incidencias(resultados_tasks, cierre_id, chunks_individuales):
    """
    🎯 CONSOLIDACIÓN FINAL DE RESULTADOS
    
    Procesa los resultados de todas las tareas del Chord y actualiza el estado del cierre
    
    Args:
        resultados_tasks: Lista de resultados de las tareas paralelas
        cierre_id: ID del cierre a actualizar
        chunks_individuales: Número de chunks individuales procesados
        
    Returns:
        dict: Estadísticas consolidadas finales
    """
    logger.info(f"🎯 Consolidando resultados para cierre {cierre_id}")
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Inicializar contadores
        total_incidencias_individuales = 0
        total_incidencias_suma = 0
        tasks_exitosas = 0
        tasks_con_error = 0
        tiempo_total_individual = 0
        tiempo_suma_total = 0
        empleados_procesados_total = 0
        
        # Procesar resultados de cada tarea
        for resultado in resultados_tasks:
            if isinstance(resultado, dict):
                if 'error' in resultado:
                    tasks_con_error += 1
                    logger.error(f"❌ Tarea con error: {resultado.get('chunk_id', 'unknown')} - {resultado['error']}")
                else:
                    tasks_exitosas += 1
                    
                    if resultado.get('tipo_comparacion') == 'individual':
                        total_incidencias_individuales += resultado.get('incidencias_detectadas', 0)
                        tiempo_total_individual += resultado.get('tiempo_procesamiento', 0)
                        empleados_procesados_total += resultado.get('empleados_procesados', 0)
                    elif resultado.get('tipo_comparacion') == 'suma_total':
                        total_incidencias_suma += resultado.get('incidencias_detectadas', 0)
                        tiempo_suma_total = resultado.get('tiempo_procesamiento', 0)
        
        total_incidencias = total_incidencias_individuales + total_incidencias_suma
        
        # 🎯 ACTUALIZAR ESTADOS DEL CIERRE SEGÚN INCIDENCIAS DETECTADAS
        if tasks_con_error > 0:
            # Si hubo errores en el procesamiento, mantener estado de error
            logger.warning(f"⚠️ Procesamiento completado con {tasks_con_error} errores")
            cierre.estado_incidencias = 'pendiente'
            cierre.save()
            # No cambiar el estado principal si hay errores
        else:
            # Usar función centralizada para actualizar estados
            actualizar_estado_cierre_por_incidencias(cierre, total_incidencias, es_primer_cierre=False)
            
            # Logging detallado por tipo de incidencia
            if total_incidencias > 0:
                if total_incidencias_individuales > 0:
                    logger.info(f"   � {total_incidencias_individuales} incidencias individuales (empleado por empleado)")
                if total_incidencias_suma > 0:
                    logger.info(f"   📊 {total_incidencias_suma} incidencias agregadas (sumas totales)")
        
        # Calcular estadísticas de performance
        throughput_individual = empleados_procesados_total / tiempo_total_individual if tiempo_total_individual > 0 else 0
        tiempo_total_sistema = max(tiempo_total_individual, tiempo_suma_total)
        
        # Ejecutar reconciliación simplificada (suma_total)
        try:
            from .reconciliacion import reconciliar_cierre_suma_total
            resumen_recon = reconciliar_cierre_suma_total(cierre_id)
            logger.info(f"🔄 Reconciliación suma_total v{resumen_recon['version']}: {resumen_recon}")
        except Exception as e:
            logger.error(f"❌ Error en reconciliación suma_total: {e}")

        # Log final detallado
        logger.info(f"🎯 ===== CONSOLIDACIÓN COMPLETADA =====")
        logger.info(f"   🔍 Incidencias individuales: {total_incidencias_individuales}")
        logger.info(f"   📊 Incidencias suma total: {total_incidencias_suma}")
        logger.info(f"   📈 Total incidencias: {total_incidencias}")
        logger.info(f"   ✅ Tareas exitosas: {tasks_exitosas}")
        logger.info(f"   ❌ Tareas con error: {tasks_con_error}") 
        logger.info(f"   👥 Empleados procesados: {empleados_procesados_total}")
        logger.info(f"   ⏱️ Tiempo individual: {tiempo_total_individual:.2f}s")
        logger.info(f"   ⏱️ Tiempo suma total: {tiempo_suma_total:.2f}s")
        logger.info(f"   🚀 Throughput: {throughput_individual:.2f} emp/s")
        logger.info(f"   🎯 Estado final: {cierre.estado_incidencias}")
        logger.info(f"=====================================")
        
        return {
            'success': True,
            'incidencias_individuales': total_incidencias_individuales,
            'incidencias_suma_total': total_incidencias_suma,
            'total_incidencias': total_incidencias,
            'tasks_exitosas': tasks_exitosas,
            'tasks_con_error': tasks_con_error,
            'chunks_procesados': chunks_individuales,
            'empleados_procesados': empleados_procesados_total,
            'tiempo_individual': round(tiempo_total_individual, 2),
            'tiempo_suma_total': round(tiempo_suma_total, 2),
            'tiempo_total_sistema': round(tiempo_total_sistema, 2),
            'throughput': round(throughput_individual, 2),
            'estado_final': cierre.estado_incidencias,
            'performance_summary': {
                'chunks_paralelos': chunks_individuales,
                'suma_total_paralela': True,
                'empleados_por_segundo': round(throughput_individual, 2),
                'eficiencia': 'optima' if tasks_con_error == 0 else 'con_errores'
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error consolidando resultados: {str(e)}")
        return {'success': False, 'error': str(e)}

# ================================
# 🛠️ FUNCIONES AUXILIARES
# ================================

# ================================
# 🛠️ FUNCIONES AUXILIARES
# ================================

def actualizar_estado_cierre_por_incidencias(cierre, total_incidencias, es_primer_cierre=False):
    """
    🎯 FUNCIÓN CENTRALIZADA PARA ACTUALIZAR ESTADOS DEL CIERRE
    
    Maneja la lógica de transición de estados basada en incidencias detectadas
    
    Args:
        cierre: Instancia del CierreNomina
        total_incidencias: Número total de incidencias detectadas
        es_primer_cierre: Si es True, aplica lógica específica para primer cierre
    """
    cierre.total_incidencias = total_incidencias
    cierre.fecha_ultima_revision = timezone.now()
    
    if total_incidencias > 0:
        # 🔍 HAY INCIDENCIAS DETECTADAS
        tipo_analisis = "informativas" if es_primer_cierre else "comparativas"
        logger.info(f"🔍 {total_incidencias} incidencias {tipo_analisis} detectadas")
        
        cierre.estado_incidencias = 'detectadas'
        cierre.estado = 'con_incidencias'
        
        accion = "primer cierre" if es_primer_cierre else "análisis comparativo"
        logger.info(f"🎯 Estado actualizado: {accion} → con_incidencias")
        
    else:
        # ✅ NO HAY INCIDENCIAS DETECTADAS
        tipo_analisis = "Primer cierre limpio" if es_primer_cierre else "Análisis comparativo limpio"
        logger.info(f"✅ {tipo_analisis} - Sin incidencias detectadas")
        
        cierre.estado_incidencias = 'resueltas'  # Sin incidencias = resueltas automáticamente
        
        # Determinar siguiente estado basado en el estado actual
        if cierre.estado == 'datos_consolidados':
            cierre.estado = 'incidencias_resueltas'
            logger.info("🎯 Estado actualizado: datos_consolidados → incidencias_resueltas")
        elif cierre.estado in ['con_incidencias', 'con_discrepancias']:
            cierre.estado = 'incidencias_resueltas'
            logger.info(f"🎯 Estado actualizado: {cierre.estado} → incidencias_resueltas")
        # Para otros estados, mantener el estado actual
    
    # Log del estado final
    logger.info(f"📊 Estado del cierre actualizado:")
    logger.info(f"   🎯 Estado principal: {cierre.estado}")
    logger.info(f"   🔍 Estado incidencias: {cierre.estado_incidencias}")
    logger.info(f"   📈 Total incidencias: {cierre.total_incidencias}")
    
    cierre.save()
    return cierre

def calcular_variacion_porcentual(valor_actual, valor_anterior):
    """Calcula variación porcentual entre dos valores"""
    if valor_anterior == 0:
        return 100.0 if valor_actual > 0 else 0.0
    
    return ((valor_actual - valor_anterior) / valor_anterior) * 100

def obtener_umbral_individual(tipo_concepto):
    """Umbral fijo para comparación individual (solicitud: 30%)."""
    return 30.0

def obtener_umbral_suma_total(tipo_concepto):
    """Umbral fijo para sumas totales (solicitud: 30%)."""
    return 30.0

def crear_chunks_empleados_dinamicos(empleados_consolidados):
    """Crea chunks dinámicos optimizados para comparación"""
    total_empleados = empleados_consolidados.count()
    
    if total_empleados <= 50:
        chunk_size = max(10, total_empleados // 3)
    elif total_empleados <= 200:
        chunk_size = 25
    elif total_empleados <= 500:
        chunk_size = 50
    else:
        chunk_size = 75
    
    empleados_ids = list(empleados_consolidados.values_list('id', flat=True))
    
    return [
        empleados_ids[i:i + chunk_size] 
        for i in range(0, len(empleados_ids), chunk_size)
    ]

# ================================
# 🔍 CREACIÓN DE INCIDENCIAS
# ================================

def crear_incidencia_variacion_individual(empleado, concepto_actual, concepto_anterior, variacion_pct):
    """Crea incidencia para variación individual por empleado"""
    obj = IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='variacion_concepto_individual',
        tipo_comparacion='individual',
        prioridad=determinar_prioridad_individual(variacion_pct),
        concepto_afectado=concepto_actual.nombre_concepto,
        descripcion=f'Variación {variacion_pct:.1f}% en {concepto_actual.nombre_concepto}',
        impacto_monetario=abs(concepto_actual.monto_total - concepto_anterior.monto_total),
        datos_adicionales={
            'alcance': 'empleado',
            'categoria_concepto': concepto_actual.tipo_concepto,
            'concepto': concepto_actual.nombre_concepto,
            'tipo_concepto': concepto_actual.tipo_concepto,
            'monto_actual': float(concepto_actual.monto_total),
            'monto_anterior': float(concepto_anterior.monto_total),
            'variacion_porcentual': round(variacion_pct, 2),
            'variacion_absoluta': float(abs(concepto_actual.monto_total - concepto_anterior.monto_total)),
            'tipo_comparacion': 'individual'
        }
    )
    clave, h = obj.generar_firma()
    obj.firma_clave = clave
    obj.firma_hash = h
    return obj

def crear_incidencia_concepto_nuevo_empleado(empleado, concepto):
    """Crea incidencia para concepto nuevo en empleado existente"""
    obj = IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='concepto_nuevo_empleado',
        tipo_comparacion='individual',
        prioridad='media',
        concepto_afectado=concepto.nombre_concepto,
        descripcion=f'Nuevo concepto {concepto.nombre_concepto} para empleado',
        impacto_monetario=concepto.monto_total,
        datos_adicionales={
            'alcance': 'empleado',
            'categoria_concepto': concepto.tipo_concepto,
            'concepto': concepto.nombre_concepto,
            'tipo_concepto': concepto.tipo_concepto,
            'monto_actual': float(concepto.monto_total),
            'monto_anterior': 0.0,
            'tipo_comparacion': 'individual'
        }
    )
    clave, h = obj.generar_firma()
    obj.firma_clave = clave
    obj.firma_hash = h
    return obj

def crear_incidencia_concepto_eliminado_empleado(empleado_anterior, concepto_anterior, cierre_actual_id=None):
    """Crea incidencia para concepto eliminado de empleado existente
    Nota: cierre_actual_id debe ser el cierre en curso; si no se entrega, se usa el del empleado_anterior (fallback)
    """
    obj = IncidenciaCierre(
        cierre_id=cierre_actual_id or empleado_anterior.cierre.id,
        rut_empleado=empleado_anterior.rut_empleado,
        empleado_nombre=empleado_anterior.nombre_empleado,
        tipo_incidencia='concepto_eliminado_empleado',
        tipo_comparacion='individual',
        prioridad='media',
        concepto_afectado=concepto_anterior.nombre_concepto,
        descripcion=f'Concepto {concepto_anterior.nombre_concepto} eliminado del empleado',
        impacto_monetario=concepto_anterior.monto_total,
        datos_adicionales={
            'alcance': 'empleado',
            'categoria_concepto': concepto_anterior.tipo_concepto,
            'concepto': concepto_anterior.nombre_concepto,
            'tipo_concepto': concepto_anterior.tipo_concepto,
            'monto_actual': 0.0,
            'monto_anterior': float(concepto_anterior.monto_total),
            'tipo_comparacion': 'individual'
        }
    )
    clave, h = obj.generar_firma()
    obj.firma_clave = clave
    obj.firma_hash = h
    return obj

def crear_incidencia_empleado_nuevo(empleado):
    """Crea incidencia informativa para empleado nuevo"""
    # Informativa: no genera firma
    return IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='empleado_nuevo',
        tipo_comparacion='individual',
        estado='resuelta_analista',  # Informativa: no requiere aprobación
        prioridad='baja',
        concepto_afectado='Estado del empleado',
        descripcion=f'Empleado nuevo sin período anterior',
        impacto_monetario=(empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0),
        datos_adicionales={
            'alcance': 'empleado',
            'categoria_concepto': 'movimiento_personal',
            'informativo': True,
            # Mantener keys antiguas por compatibilidad, pero llenar desde nuevas categorías
            'total_haberes': float(((empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0)) or 0),
            'total_descuentos': float(((empleado.dctos_legales or 0) + (empleado.otros_dctos or 0) + (empleado.impuestos or 0)) or 0),
            'tipo_comparacion': 'individual'
        }
    )

def crear_incidencia_suma_total(cierre_id, nombre_concepto, tipo_concepto, suma_actual, suma_anterior, variacion_pct):
    """
    Crea incidencia para variación en suma total (modelo simplificado sin firma).
    Compatible con IncidenciaCierre simplificado.
    """
    variacion_pct_float = float(variacion_pct)
    variacion_abs_float = float(abs(suma_actual - suma_anterior))
    
    # Truncar tipo_concepto si es muy largo (máx 30 caracteres)
    clasificacion_truncada = tipo_concepto[:30] if tipo_concepto and len(tipo_concepto) > 30 else tipo_concepto
    
    return IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='variacion_suma_total',
        tipo_comparacion='suma_total',
        clasificacion_concepto=clasificacion_truncada,
        prioridad=determinar_prioridad_suma_total(variacion_pct_float, variacion_abs_float),
        concepto_afectado=nombre_concepto,
        descripcion=f'Variación {variacion_pct_float:.1f}% en suma total de {nombre_concepto}',
        impacto_monetario=abs(suma_actual - suma_anterior),
        datos_adicionales={
            'alcance': 'item',
            'categoria_concepto': tipo_concepto,
            'concepto': nombre_concepto,
            'tipo_concepto': tipo_concepto,
            'suma_actual': float(suma_actual),
            'suma_anterior': float(suma_anterior),
            'variacion_porcentual': round(variacion_pct_float, 2),
            'variacion_absoluta': variacion_abs_float,
            'tipo_comparacion': 'suma_total',
            'monto_actual': float(suma_actual),
            'monto_anterior': float(suma_anterior),
            'delta_abs': variacion_abs_float,
            'delta_pct': variacion_pct_float
        }
    )

def crear_incidencia_suma_total_categoria(cierre_id, categoria, suma_actual, suma_anterior, variacion_pct):
    """Crea incidencia para variación en suma total por CATEGORÍA (e.g., total haberes imponibles)."""
    variacion_pct_float = float(variacion_pct)
    variacion_abs_float = float(abs(suma_actual - suma_anterior))
    etiquetas = {
        'haber_imponible': 'Haberes Imponibles',
        'haber_no_imponible': 'Haberes No Imponibles',
        'descuento_legal': 'Descuentos Legales',
        'otro_descuento': 'Otros Descuentos',
        'impuesto': 'Impuestos',
        'aporte_patronal': 'Aportes Patronales',
    'total_liquido': 'Total Líquido',
    }
    nombre_legible = etiquetas.get(categoria, categoria)
    obj = IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='variacion_suma_total_categoria',
        tipo_comparacion='suma_total',
        prioridad=determinar_prioridad_suma_total(variacion_pct_float, variacion_abs_float),
        concepto_afectado=f'Total {nombre_legible}',
        descripcion=f'Variación {variacion_pct_float:.1f}% en total de {nombre_legible}',
        impacto_monetario=abs(suma_actual - suma_anterior),
        datos_adicionales={
            'alcance': 'categoria',
            'categoria_concepto': categoria,
            'categoria': categoria,
            'concepto': f'Total {nombre_legible}',
            'tipo_concepto': categoria,
            'suma_actual': float(suma_actual),
            'suma_anterior': float(suma_anterior),
            'variacion_porcentual': round(variacion_pct_float, 2),
            'variacion_absoluta': variacion_abs_float,
            'tipo_comparacion': 'suma_total'
        }
    )
    clave, h = obj.generar_firma()
    obj.firma_clave = clave
    obj.firma_hash = h
    return obj

def crear_incidencia_concepto_nuevo_periodo(cierre_id, nombre_concepto, tipo_concepto):
    """Crea incidencia para concepto completamente nuevo en el período"""
    return IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='concepto_nuevo_periodo',
        tipo_comparacion='suma_total',
        prioridad='media',
        concepto_afectado=nombre_concepto,
        descripcion=f'Concepto {nombre_concepto} aparece por primera vez',
        datos_adicionales={
            'alcance': 'item',
            'categoria_concepto': tipo_concepto,
            'concepto': nombre_concepto,
            'tipo_concepto': tipo_concepto,
            'tipo_comparacion': 'suma_total'
        }
    )

def crear_incidencia_concepto_eliminado_periodo(cierre_id, nombre_concepto, tipo_concepto):
    """Crea incidencia para concepto completamente eliminado del período"""
    return IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='concepto_eliminado_periodo',
        tipo_comparacion='suma_total',
        prioridad='alta',  # Eliminación completa es más crítica
        concepto_afectado=nombre_concepto,
        descripcion=f'Concepto {nombre_concepto} desaparece completamente',
        datos_adicionales={
            'alcance': 'item',
            'categoria_concepto': tipo_concepto,
            'concepto': nombre_concepto,
            'tipo_concepto': tipo_concepto,
            'tipo_comparacion': 'suma_total'
        }
    )

def determinar_prioridad_individual(variacion_pct):
    """Determina prioridad para incidencias individuales"""
    abs_variacion = abs(variacion_pct)
    if abs_variacion >= 75:
        return 'critica'
    elif abs_variacion >= 50:
        return 'alta'
    elif abs_variacion >= 30:
        return 'media'
    else:
        return 'baja'

def determinar_prioridad_suma_total(variacion_pct, impacto_monetario):
    """Determina prioridad para incidencias de suma total"""
    abs_variacion = abs(variacion_pct)
    
    # Considerar tanto variación porcentual como impacto monetario
    if abs_variacion >= 50 or impacto_monetario >= 10000000:  # 10M
        return 'critica'
    elif abs_variacion >= 30 or impacto_monetario >= 5000000:  # 5M
        return 'alta'
    elif abs_variacion >= 15 or impacto_monetario >= 1000000:  # 1M
        return 'media'
    else:
        return 'baja'

# ================================
# 🔧 FUNCIONES DE COMPATIBILIDAD
# ================================

def generar_analisis_primer_cierre(cierre_actual, clasificaciones_seleccionadas):
    """
    🆕 ANÁLISIS INFORMATIVO PARA PRIMER CIERRE
    
    Cuando no hay período anterior, genera incidencias informativas:
    - Estadísticas generales del cierre
    - Empleados sin conceptos
    - Conceptos con montos anómalos
    - Resumen por clasificación seleccionada
    
    Args:
        cierre_actual: Instancia del cierre a analizar
        clasificaciones_seleccionadas: Tipos de conceptos seleccionados
        
    Returns:
        dict: Resultado del análisis informativo
    """
    logger.info(f"🆕 Iniciando análisis informativo para primer cierre {cierre_actual.id}")

    try:
        # Política final: Primer cierre NO genera incidencias (ninguna, ni informativas ni resumen).
        
        # 1. OBTENER EMPLEADOS CONSOLIDADOS
        # Igual que arriba, usar 'conceptos' como related_name válido
        empleados_consolidados = NominaConsolidada.objects.filter(
            cierre=cierre_actual
        ).prefetch_related('conceptos')
        
        total_empleados = empleados_consolidados.count()
        
        if total_empleados == 0:
            return {
                'success': False,
                'message': 'No hay empleados consolidados en este cierre'
            }
        
        logger.info(f"👥 Analizando {total_empleados} empleados del primer cierre")
        
        # 2. ESTADÍSTICAS GENERALES
        stats = calcular_estadisticas_primer_cierre(empleados_consolidados, clasificaciones_seleccionadas)
        
        # 3. DETECTAR ANOMALÍAS INFORMATIVAS
        empleados_sin_conceptos = 0
        empleados_con_montos_cero = 0
        conceptos_anomalos = []
        
        # (Eliminado) Generación de incidencias por empleado para primer cierre.
        
        # 4. NO crear ninguna incidencia. Mantener total_incidencias=0
        total_incidencias = 0
        # Actualizar estado como "sin incidencias" directamente
        actualizar_estado_cierre_por_incidencias(cierre_actual, total_incidencias, es_primer_cierre=True)
        
        logger.info(f"✅ Análisis primer cierre completado:")
        logger.info(f"   📊 {total_empleados} empleados analizados")
        logger.info(f"   🔍 {len(clasificaciones_seleccionadas)} tipos de conceptos revisados")
        logger.info(f"   ⚠️ {total_incidencias} incidencias informativas creadas")
        logger.info(f"   🚫 {empleados_sin_conceptos} empleados sin conceptos")
        logger.info(f"   💰 {empleados_con_montos_cero} empleados con montos en cero")
        logger.info(f"   🔥 {len(conceptos_anomalos)} conceptos con montos anómalos")
        
        return {
            'success': True,
            'tipo_analisis': 'primer_cierre',
            'total_empleados': total_empleados,
            'total_incidencias': total_incidencias,
            'incidencias_informativas': 0,
            'empleados_sin_conceptos': empleados_sin_conceptos,
            'empleados_con_montos_cero': empleados_con_montos_cero,
            'conceptos_anomalos': len(conceptos_anomalos),
            'clasificaciones_analizadas': clasificaciones_seleccionadas,
            'estadisticas': stats,
            'estado_final': cierre_actual.estado_incidencias,
            'mensaje': 'Primer cierre analizado: sin generación de incidencias (política primer cierre)'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis primer cierre: {str(e)}")
        return {'success': False, 'error': str(e)}

def calcular_estadisticas_primer_cierre(empleados_consolidados, clasificaciones_seleccionadas):
    """Calcula estadísticas generales del primer cierre"""
    from django.db.models import Sum, Avg, Count
    
    stats = {
        'total_empleados': empleados_consolidados.count(),
        'total_haberes': 0,
        'total_descuentos': 0,
        'promedio_liquido': 0,
        'conceptos_por_clasificacion': {}
    }

    # Calcular totales usando las nuevas categorías
    totales = empleados_consolidados.aggregate(
        total_haberes_imponibles=Sum('haberes_imponibles'),
        total_haberes_no_imponibles=Sum('haberes_no_imponibles'),
        total_dctos_legales=Sum('dctos_legales'),
        total_otros_dctos=Sum('otros_dctos'),
        total_impuestos=Sum('impuestos')
    )

    # Mapear a formato histórico
    total_haberes = (totales.get('total_haberes_imponibles') or 0) + (totales.get('total_haberes_no_imponibles') or 0)
    total_descuentos = (totales.get('total_dctos_legales') or 0) + (totales.get('total_otros_dctos') or 0) + (totales.get('total_impuestos') or 0)

    stats['total_haberes'] = total_haberes
    stats['total_descuentos'] = total_descuentos
    # promedio liquido aproximado
    stats['promedio_liquido'] = (total_haberes - total_descuentos) / empleados_consolidados.count() if empleados_consolidados.count() > 0 else 0
    
    # Estadísticas por clasificación seleccionada
    for clasificacion in clasificaciones_seleccionadas:
        conceptos_clasificacion = ConceptoConsolidado.objects.filter(
            nomina_consolidada__in=empleados_consolidados,
            tipo_concepto=clasificacion
        ).aggregate(
            total_monto=Sum('monto_total'),
            cantidad_conceptos=Count('id'),
            empleados_con_concepto=Count('nomina_consolidada', distinct=True)
        )
        
        stats['conceptos_por_clasificacion'][clasificacion] = conceptos_clasificacion
    
    return stats

def crear_incidencia_informativa_sin_conceptos(empleado):
    """Crea incidencia informativa para empleado sin conceptos"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='empleado_sin_conceptos',
        tipo_comparacion='informativo',
        prioridad='media',
        descripcion='Empleado sin conceptos de nómina registrados',
        impacto_monetario=Decimal('0'),
        datos_adicionales={
            'tipo_analisis': 'primer_cierre',
            'problema': 'sin_conceptos',
            'total_haberes': float(empleado.total_haberes or 0),
            'total_descuentos': float(empleado.total_descuentos or 0)
        }
    )

def crear_incidencia_informativa_montos_cero(empleado):
    """Crea incidencia informativa para empleado con todos los conceptos en cero"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='empleado_montos_cero',
        tipo_comparacion='informativo',
        prioridad='alta',
        descripcion='Empleado con todos los conceptos en monto cero',
        impacto_monetario=Decimal('0'),
        datos_adicionales={
            'tipo_analisis': 'primer_cierre',
            'problema': 'montos_cero',
            'total_conceptos': empleado.conceptos.count()
        }
    )

def crear_incidencia_informativa_monto_alto(empleado, concepto):
    """Crea incidencia informativa para concepto con monto anómalamente alto"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        rut_empleado=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='concepto_monto_anomalo',
        tipo_comparacion='informativo',
        prioridad='alta',
        descripcion=f'Monto anómalamente alto en {concepto.nombre_concepto}: ${concepto.monto_total:,.0f}',
        impacto_monetario=concepto.monto_total,
        datos_adicionales={
            'tipo_analisis': 'primer_cierre',
            'problema': 'monto_anomalo',
            'concepto': concepto.nombre_concepto,
            'tipo_concepto': concepto.tipo_concepto,
            'monto': float(concepto.monto_total)
        }
    )

def crear_incidencia_resumen_primer_cierre(cierre, stats, empleados_sin_conceptos, empleados_con_montos_cero):
    """Crea incidencia resumen del análisis del primer cierre"""
    stats_serializables = _serialize_decimal(stats)
    return IncidenciaCierre(
        cierre=cierre,
        tipo_incidencia='resumen_primer_cierre',
        tipo_comparacion='informativo',
        prioridad='baja',
        descripcion=f'Resumen del primer cierre: {stats["total_empleados"]} empleados analizados',
        impacto_monetario=stats.get('total_haberes', 0) or Decimal('0'),
        datos_adicionales={
            'tipo_analisis': 'primer_cierre',
            'resumen': True,
            'estadisticas': stats_serializables,
            'empleados_sin_conceptos': empleados_sin_conceptos,
            'empleados_con_montos_cero': empleados_con_montos_cero,
            'total_haberes': float(stats.get('total_haberes', 0) or 0),
            'total_descuentos': float(stats.get('total_descuentos', 0) or 0),
            'promedio_liquido': float(stats.get('promedio_liquido', 0) or 0)
        }
    )

def detectar_incidencias_consolidadas_simple(cierre_actual):
    """
    🔧 FUNCIÓN DE COMPATIBILIDAD CON CONFIGURACIÓN PABLO
    
    Mantiene compatibilidad con el sistema anterior pero usa configuración automática.
    Esta función redirige al sistema dual con la configuración fija de Pablo.
    """
    logger.info(f"🔧 Función legacy llamada para {cierre_actual} - Usando configuración Pablo")
    
    # 🎯 USAR CONFIGURACIÓN AUTOMÁTICA DE PABLO (sin parámetros)
    resultado = generar_incidencias_consolidados_v2.apply(
        args=[cierre_actual.id]  # Sin pasar clasificaciones - usa configuración automática
    )
    
    return {
        'success': resultado.successful(),
        'resultado_sistema_dual': resultado.result if resultado else None,
        'configuracion_usada': 'pablo_automatica',
        'conceptos_detallados': CONCEPTOS_ANALISIS_DETALLADO,
        'conceptos_resumen': CONCEPTOS_SOLO_RESUMEN,
        'message': 'Migrado a sistema dual con configuración automática de Pablo'
    }
