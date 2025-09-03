# backend/nomina/utils/DetectarIncidenciasConsolidadas.py
"""
Sistema de detección de incidencias entre períodos consolidados de nómina
VERSIÓN 2.0: Sistema Dual con Celery Chord
- Comparación Individual (elemento a elemento) para conceptos seleccionados
- Comparación Suma Total (agregada) para todos los conceptos
"""

import logging
import time
from decimal import Decimal
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone
from celery import shared_task, chord
from ..models import (
    CierreNomina, 
    NominaConsolidada, 
    ConceptoConsolidado, 
    MovimientoPersonal,
    IncidenciaCierre,
    TipoIncidencia
)

logger = logging.getLogger('nomina.incidencias')

# ================================
# 🎯 CONFIGURACIÓN PABLO - CONCEPTOS A ANALIZAR
# ================================

# Conceptos que Pablo quiere analizar en DETALLE (empleado por empleado)
CONCEPTOS_ANALISIS_DETALLADO = [
    'haberes_imponibles',     # 💰 Sueldos - Cambios requieren autorización
    'haberes_no_imponibles',  # 🎁 Bonos - Decisiones de gestión  
    'otros_descuentos'        # 📋 Descuentos discrecionales
]

# Conceptos que Pablo quiere SOLO como resumen (totales)
CONCEPTOS_SOLO_RESUMEN = [
    'descuentos_legales',     # 🤖 Se calculan automáticamente por ley
    'aportes_patronales',     # 🏢 Los paga la empresa, no el empleado
    'informacion_adicional',  # 📄 No son montos
    'impuestos',              # 💸 Se calculan automáticamente
    'horas_extras'            # ⏰ Muy variables por naturaleza
]

# ================================
# 🚀 SISTEMA DUAL CON CELERY CHORD
# ================================

@shared_task
def generar_incidencias_consolidados_v2(cierre_id, clasificaciones_seleccionadas=None):
    """
    🎯 TAREA ORQUESTADORA PRINCIPAL - SISTEMA DUAL CON CONFIGURACIÓN PABLO
    
    Coordina dos tipos de comparación usando Celery Chord:
    1. Comparación Individual: elemento a elemento (SOLO conceptos de Pablo)  
    2. Comparación Suma Total: agregada (TODOS los conceptos)
    
    Args:
        cierre_id: ID del cierre actual
        clasificaciones_seleccionadas: IGNORADO - ahora usa configuración automática de Pablo
        
    Returns:
        dict: Resultado de la coordinación con estadísticas del Chord
    """
    # 🎯 USAR CONFIGURACIÓN AUTOMÁTICA DE PABLO (ignorar parámetro)
    clasificaciones_pablo = CONCEPTOS_ANALISIS_DETALLADO
    
    logger.info(f"🚀 Iniciando sistema dual para cierre {cierre_id}")
    logger.info(f"🔍 Conceptos para análisis detallado (Pablo): {clasificaciones_pablo}")
    logger.info(f"📊 Conceptos solo resumen: {CONCEPTOS_SOLO_RESUMEN}")
    
    try:
        cierre_actual = CierreNomina.objects.get(id=cierre_id)
        cierre_anterior = obtener_cierre_anterior_finalizado(cierre_actual)
        
        if not cierre_anterior:
            logger.info(f"🆕 Primer cierre del cliente {cierre_actual.cliente.nombre}")
            logger.info(f"📊 Generando análisis informativo sin comparación para {cierre_actual.periodo}")
            
            # Generar análisis informativo para el primer cierre
            return generar_analisis_primer_cierre(cierre_actual, clasificaciones_pablo)
        
        logger.info(f"📊 Comparando {cierre_actual.periodo} vs {cierre_anterior.periodo}")
        
        # 1. PREPARAR EMPLEADOS PARA COMPARACIÓN INDIVIDUAL
        empleados_consolidados = NominaConsolidada.objects.filter(
            cierre=cierre_actual
        ).select_related('cierre').prefetch_related('conceptos_consolidados')
        
        total_empleados = empleados_consolidados.count()
        logger.info(f"👥 Total empleados a procesar: {total_empleados}")
        
        if total_empleados == 0:
            logger.warning("⚠️ No hay empleados consolidados para procesar")
            return {'success': False, 'message': 'No hay empleados consolidados'}
        
        # 2. CREAR CHUNKS DINÁMICOS PARA COMPARACIÓN INDIVIDUAL
        chunks_empleados = crear_chunks_empleados_dinamicos(empleados_consolidados)
        logger.info(f"📦 Creados {len(chunks_empleados)} chunks para comparación individual")
        
        # 3. CREAR TAREAS PARALELAS
        tasks = []
        
        # TAREAS TIPO A: Comparación individual (chunks paralelos) - SOLO CONCEPTOS DE PABLO
        for i, chunk_empleados_ids in enumerate(chunks_empleados):
            tasks.append(
                procesar_chunk_comparacion_individual.s(
                    chunk_empleados_ids,
                    cierre_id,
                    cierre_anterior.id,
                    clasificaciones_pablo,  # 🎯 USAR CONFIGURACIÓN DE PABLO
                    f"individual_chunk_{i+1}"
                )
            )
        
        # TAREA TIPO B: Comparación suma total (tarea única dedicada) - TODOS LOS CONCEPTOS
        tasks.append(
            procesar_comparacion_suma_total.s(
                cierre_id,
                cierre_anterior.id,
                "suma_total_global"
            )
        )
        
        # 4. EJECUTAR CHORD
        logger.info(f"🎼 Ejecutando Chord con {len(tasks)} tareas")
        logger.info(f"   🔍 {len(chunks_empleados)} chunks individuales (solo conceptos críticos)")
        logger.info(f"   📊 1 comparación suma total (todos los conceptos)")
        
        job = chord(tasks)(consolidar_resultados_incidencias.s(cierre_id, len(chunks_empleados)))
        
        logger.info(f"✅ Chord iniciado exitosamente: {job.id}")
        
        return {
            'success': True,
            'chord_id': job.id,
            'chunks_individuales': len(chunks_empleados),
            'comparacion_suma_total': True,
            'total_tasks': len(tasks),
            'empleados_total': total_empleados,
            'clasificaciones_detalladas': clasificaciones_pablo,  # 🎯 CONCEPTOS PABLO
            'clasificaciones_solo_resumen': CONCEPTOS_SOLO_RESUMEN,
            'configuracion': 'pablo_automatica',
            'mensaje': f'Sistema Pablo: {len(chunks_empleados)} chunks individuales + suma total automática'
        }
        
    except Exception as e:
        logger.error(f"❌ Error en sistema dual: {str(e)}")
        return {'success': False, 'error': str(e)}

def obtener_cierre_anterior_finalizado(cierre_actual):
    """Obtiene el cierre anterior finalizado para comparación"""
    return CierreNomina.objects.filter(
        cliente=cierre_actual.cliente,
        periodo__lt=cierre_actual.periodo,
        estado='finalizado'
    ).order_by('-periodo').first()

# ================================
# 🔍 COMPARACIÓN INDIVIDUAL
# ================================

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
    
    logger.info(f"🔍 {chunk_id}: Iniciando comparación individual")
    logger.info(f"   👥 Empleados: {len(empleados_ids)}")
    logger.info(f"   📋 Clasificaciones: {clasificaciones_seleccionadas}")
    
    try:
        for empleado_consolidado_id in empleados_ids:
            empleado_actual = NominaConsolidada.objects.select_related('cierre').get(
                id=empleado_consolidado_id
            )
            
            # Buscar empleado equivalente en período anterior
            empleado_anterior = NominaConsolidada.objects.filter(
                cierre_id=cierre_anterior_id,
                rut_empleado=empleado_actual.rut_empleado
            ).first()
            
            if empleado_anterior:
                # FILTRAR: Solo conceptos seleccionados para análisis detallado
                conceptos_actuales = ConceptoConsolidado.objects.filter(
                    nomina_consolidada=empleado_actual,
                    tipo_concepto__in=clasificaciones_seleccionadas  # ⭐ FILTRO CLAVE
                ).select_related('nomina_consolidada')
                
                for concepto_actual in conceptos_actuales:
                    concepto_anterior = ConceptoConsolidado.objects.filter(
                        nomina_consolidada=empleado_anterior,
                        nombre_concepto=concepto_actual.nombre_concepto,
                        tipo_concepto=concepto_actual.tipo_concepto
                    ).first()
                    
                    if concepto_anterior:
                        # Calcular variación individual
                        variacion_pct = calcular_variacion_porcentual(
                            concepto_actual.monto_total, 
                            concepto_anterior.monto_total
                        )
                        
                        # Umbral diferenciado por tipo de concepto
                        umbral = obtener_umbral_individual(concepto_actual.tipo_concepto)
                        
                        if abs(variacion_pct) >= umbral:
                            incidencias_detectadas.append(
                                crear_incidencia_variacion_individual(
                                    empleado_actual, concepto_actual, concepto_anterior, variacion_pct
                                )
                            )
                    else:
                        # Concepto nuevo para este empleado
                        incidencias_detectadas.append(
                            crear_incidencia_concepto_nuevo_empleado(empleado_actual, concepto_actual)
                        )
                        
                # Buscar conceptos eliminados (estaban en anterior pero no en actual)
                conceptos_anteriores = ConceptoConsolidado.objects.filter(
                    nomina_consolidada=empleado_anterior,
                    tipo_concepto__in=clasificaciones_seleccionadas
                )
                
                for concepto_anterior in conceptos_anteriores:
                    concepto_actual = ConceptoConsolidado.objects.filter(
                        nomina_consolidada=empleado_actual,
                        nombre_concepto=concepto_anterior.nombre_concepto,
                        tipo_concepto=concepto_anterior.tipo_concepto
                    ).first()
                    
                    if not concepto_actual:
                        # Concepto eliminado para este empleado
                        incidencias_detectadas.append(
                            crear_incidencia_concepto_eliminado_empleado(empleado_anterior, concepto_anterior)
                        )
            else:
                # Empleado nuevo - crear incidencia informativa
                incidencias_detectadas.append(
                    crear_incidencia_empleado_nuevo(empleado_actual)
                )
        
        # Batch insert optimizado
        if incidencias_detectadas:
            IncidenciaCierre.objects.bulk_create(
                incidencias_detectadas, 
                batch_size=100,
                ignore_conflicts=True
            )
        
        tiempo_procesamiento = time.time() - start_time
        
        resultado = {
            'chunk_id': chunk_id,
            'tipo_comparacion': 'individual',
            'empleados_procesados': len(empleados_ids),
            'incidencias_detectadas': len(incidencias_detectadas),
            'tiempo_procesamiento': round(tiempo_procesamiento, 2),
            'throughput': round(len(empleados_ids) / tiempo_procesamiento, 2) if tiempo_procesamiento > 0 else 0,
            'clasificaciones_analizadas': clasificaciones_seleccionadas
        }
        
        logger.info(f"✅ {chunk_id}: {len(incidencias_detectadas)} incidencias individuales detectadas "
                   f"en {tiempo_procesamiento:.2f}s ({resultado['throughput']} emp/s)")
        
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
    
    Procesa comparación de sumas agregadas por concepto
    TODOS los conceptos (con y sin checkbox marcado)
    
    Args:
        cierre_actual_id: ID del cierre actual
        cierre_anterior_id: ID del cierre anterior  
        task_id: Identificador de la tarea
        
    Returns:
        dict: Estadísticas del procesamiento agregado
    """
    start_time = time.time()
    incidencias_detectadas = []
    
    logger.info(f"📊 {task_id}: Iniciando comparación suma total")
    
    try:
        # 1. OBTENER TODOS LOS CONCEPTOS ÚNICOS (SIN FILTRO)
        conceptos_actuales = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre_id=cierre_actual_id
        ).values('nombre_concepto', 'tipo_concepto').distinct()
        
        conceptos_anteriores = ConceptoConsolidado.objects.filter(
            nomina_consolidada__cierre_id=cierre_anterior_id
        ).values('nombre_concepto', 'tipo_concepto').distinct()
        
        # Crear conjunto único de conceptos (TODOS)
        conceptos_unicos = set()
        for concepto in conceptos_actuales:
            conceptos_unicos.add((concepto['nombre_concepto'], concepto['tipo_concepto']))
        for concepto in conceptos_anteriores:
            conceptos_unicos.add((concepto['nombre_concepto'], concepto['tipo_concepto']))
        
        logger.info(f"📊 Analizando {len(conceptos_unicos)} conceptos únicos para suma total")
        
        # 2. COMPARAR SUMA TOTAL POR CONCEPTO
        for nombre_concepto, tipo_concepto in conceptos_unicos:
            # Suma actual
            suma_actual = ConceptoConsolidado.objects.filter(
                nomina_consolidada__cierre_id=cierre_actual_id,
                nombre_concepto=nombre_concepto,
                tipo_concepto=tipo_concepto
            ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
            
            # Suma anterior
            suma_anterior = ConceptoConsolidado.objects.filter(
                nomina_consolidada__cierre_id=cierre_anterior_id,
                nombre_concepto=nombre_concepto,
                tipo_concepto=tipo_concepto
            ).aggregate(total=Sum('monto_total'))['total'] or Decimal('0')
            
            # Calcular variación de la suma total
            variacion_pct = calcular_variacion_porcentual(suma_actual, suma_anterior)
            
            # Umbral diferenciado para sumas totales (más sensible)
            umbral_suma = obtener_umbral_suma_total(tipo_concepto)
            
            if abs(variacion_pct) >= umbral_suma:
                incidencias_detectadas.append(
                    crear_incidencia_suma_total(
                        cierre_actual_id, nombre_concepto, tipo_concepto, 
                        suma_actual, suma_anterior, variacion_pct
                    )
                )
        
        # Detectar conceptos completamente nuevos o eliminados
        conceptos_solo_actual = set(c['nombre_concepto'] + '|' + c['tipo_concepto'] for c in conceptos_actuales) - \
                              set(c['nombre_concepto'] + '|' + c['tipo_concepto'] for c in conceptos_anteriores)
        
        conceptos_solo_anterior = set(c['nombre_concepto'] + '|' + c['tipo_concepto'] for c in conceptos_anteriores) - \
                                 set(c['nombre_concepto'] + '|' + c['tipo_concepto'] for c in conceptos_actuales)
        
        # Incidencias por conceptos nuevos
        for concepto_key in conceptos_solo_actual:
            nombre_concepto, tipo_concepto = concepto_key.split('|')
            incidencias_detectadas.append(
                crear_incidencia_concepto_nuevo_periodo(cierre_actual_id, nombre_concepto, tipo_concepto)
            )
        
        # Incidencias por conceptos eliminados
        for concepto_key in conceptos_solo_anterior:
            nombre_concepto, tipo_concepto = concepto_key.split('|')
            incidencias_detectadas.append(
                crear_incidencia_concepto_eliminado_periodo(cierre_actual_id, nombre_concepto, tipo_concepto)
            )
        
        # Batch insert
        if incidencias_detectadas:
            IncidenciaCierre.objects.bulk_create(
                incidencias_detectadas, 
                batch_size=100,
                ignore_conflicts=True
            )
        
        tiempo_procesamiento = time.time() - start_time
        
        resultado = {
            'task_id': task_id,
            'tipo_comparacion': 'suma_total',
            'conceptos_analizados': len(conceptos_unicos),
            'incidencias_detectadas': len(incidencias_detectadas),
            'conceptos_nuevos': len(conceptos_solo_actual),
            'conceptos_eliminados': len(conceptos_solo_anterior),
            'tiempo_procesamiento': round(tiempo_procesamiento, 2)
        }
        
        logger.info(f"✅ {task_id}: {len(incidencias_detectadas)} incidencias agregadas detectadas "
                   f"en {tiempo_procesamiento:.2f}s")
        logger.info(f"   📊 {len(conceptos_unicos)} conceptos analizados")
        logger.info(f"   🆕 {len(conceptos_solo_actual)} conceptos nuevos")  
        logger.info(f"   ❌ {len(conceptos_solo_anterior)} conceptos eliminados")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en comparación suma total: {str(e)}")
        return {
            'task_id': task_id,
            'error': str(e),
            'tipo_comparacion': 'suma_total',
            'conceptos_analizados': 0,
            'incidencias_detectadas': 0
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
    """Umbrales diferenciados por tipo de concepto para comparación individual"""
    umbrales = {
        'haberes_imponibles': 15.0,      # Sueldo base más estable
        'haberes_no_imponibles': 30.0,   # Bonos más variables
        'horas_extras': 50.0,            # Muy variable
        'descuentos_legales': 10.0,      # Debe ser estable
        'otros_descuentos': 25.0,        # Variable
        'aportes_patronales': 15.0,      # Relacionado con haberes
        'informacion_adicional': 40.0,   # Informativo
        'impuestos': 20.0                # Moderadamente variable
    }
    return umbrales.get(tipo_concepto, 30.0)  # 30% por defecto

def obtener_umbral_suma_total(tipo_concepto):
    """Umbrales para sumas totales (más sensibles que individuales)"""
    umbrales = {
        'haberes_imponibles': 10.0,      # Masa salarial estable
        'haberes_no_imponibles': 20.0,   # Bonos agregados
        'horas_extras': 30.0,            # Variable por temporada
        'descuentos_legales': 5.0,       # Muy estable en suma
        'otros_descuentos': 15.0,        # Algo variable
        'aportes_patronales': 10.0,      # Sigue masa salarial
        'informacion_adicional': 25.0,   # Informativo
        'impuestos': 12.0                # Moderadamente estable
    }
    return umbrales.get(tipo_concepto, 20.0)  # 20% por defecto

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
    return IncidenciaCierre(
        cierre=empleado.cierre,
        empleado_rut=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='variacion_concepto_individual',
        tipo_comparacion='individual',
        prioridad=determinar_prioridad_individual(variacion_pct),
        descripcion=f'Variación {variacion_pct:.1f}% en {concepto_actual.nombre_concepto}',
        impacto_monetario=abs(concepto_actual.monto_total - concepto_anterior.monto_total),
        datos_adicionales={
            'concepto': concepto_actual.nombre_concepto,
            'tipo_concepto': concepto_actual.tipo_concepto,
            'monto_actual': float(concepto_actual.monto_total),
            'monto_anterior': float(concepto_anterior.monto_total),
            'variacion_porcentual': round(variacion_pct, 2),
            'variacion_absoluta': float(abs(concepto_actual.monto_total - concepto_anterior.monto_total)),
            'tipo_comparacion': 'individual'
        }
    )

def crear_incidencia_concepto_nuevo_empleado(empleado, concepto):
    """Crea incidencia para concepto nuevo en empleado existente"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        empleado_rut=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='concepto_nuevo_empleado',
        tipo_comparacion='individual',
        prioridad='media',
        descripcion=f'Nuevo concepto {concepto.nombre_concepto} para empleado',
        impacto_monetario=concepto.monto_total,
        datos_adicionales={
            'concepto': concepto.nombre_concepto,
            'tipo_concepto': concepto.tipo_concepto,
            'monto_actual': float(concepto.monto_total),
            'monto_anterior': 0.0,
            'tipo_comparacion': 'individual'
        }
    )

def crear_incidencia_concepto_eliminado_empleado(empleado_anterior, concepto_anterior):
    """Crea incidencia para concepto eliminado de empleado existente"""
    return IncidenciaCierre(
        cierre_id=empleado_anterior.cierre.id + 1,  # Se asigna al cierre actual
        empleado_rut=empleado_anterior.rut_empleado,
        empleado_nombre=empleado_anterior.nombre_empleado,
        tipo_incidencia='concepto_eliminado_empleado',
        tipo_comparacion='individual',
        prioridad='media',
        descripcion=f'Concepto {concepto_anterior.nombre_concepto} eliminado del empleado',
        impacto_monetario=concepto_anterior.monto_total,
        datos_adicionales={
            'concepto': concepto_anterior.nombre_concepto,
            'tipo_concepto': concepto_anterior.tipo_concepto,
            'monto_actual': 0.0,
            'monto_anterior': float(concepto_anterior.monto_total),
            'tipo_comparacion': 'individual'
        }
    )

def crear_incidencia_empleado_nuevo(empleado):
    """Crea incidencia informativa para empleado nuevo"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        empleado_rut=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='empleado_nuevo',
        tipo_comparacion='individual',
        prioridad='baja',
        descripcion=f'Empleado nuevo sin período anterior',
        impacto_monetario=(empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0),
        datos_adicionales={
            # Mantener keys antiguas por compatibilidad, pero llenar desde nuevas categorías
            'total_haberes': float(((empleado.haberes_imponibles or 0) + (empleado.haberes_no_imponibles or 0)) or 0),
            'total_descuentos': float(((empleado.dctos_legales or 0) + (empleado.otros_dctos or 0) + (empleado.impuestos or 0)) or 0),
            'tipo_comparacion': 'individual'
        }
    )

def crear_incidencia_suma_total(cierre_id, nombre_concepto, tipo_concepto, suma_actual, suma_anterior, variacion_pct):
    """Crea incidencia para variación en suma total"""
    return IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='variacion_suma_total',
        tipo_comparacion='suma_total',
        prioridad=determinar_prioridad_suma_total(variacion_pct, abs(suma_actual - suma_anterior)),
        descripcion=f'Variación {variacion_pct:.1f}% en suma total de {nombre_concepto}',
        impacto_monetario=abs(suma_actual - suma_anterior),
        datos_adicionales={
            'concepto': nombre_concepto,
            'tipo_concepto': tipo_concepto,
            'suma_actual': float(suma_actual),
            'suma_anterior': float(suma_anterior),
            'variacion_porcentual': round(variacion_pct, 2),
            'variacion_absoluta': float(abs(suma_actual - suma_anterior)),
            'tipo_comparacion': 'suma_total'
        }
    )

def crear_incidencia_concepto_nuevo_periodo(cierre_id, nombre_concepto, tipo_concepto):
    """Crea incidencia para concepto completamente nuevo en el período"""
    return IncidenciaCierre(
        cierre_id=cierre_id,
        tipo_incidencia='concepto_nuevo_periodo',
        tipo_comparacion='suma_total',
        prioridad='media',
        descripcion=f'Concepto {nombre_concepto} aparece por primera vez',
        datos_adicionales={
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
        descripcion=f'Concepto {nombre_concepto} desaparece completamente',
        datos_adicionales={
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
        incidencias_informativas = []
        
        # 1. OBTENER EMPLEADOS CONSOLIDADOS
        empleados_consolidados = NominaConsolidada.objects.filter(
            cierre=cierre_actual
        ).prefetch_related('conceptos_consolidados')
        
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
        
        for empleado in empleados_consolidados:
            conceptos = empleado.conceptos_consolidados.filter(
                tipo_concepto__in=clasificaciones_seleccionadas
            ) if clasificaciones_seleccionadas else empleado.conceptos_consolidados.all()
            
            # Empleados sin conceptos
            if conceptos.count() == 0:
                empleados_sin_conceptos += 1
                incidencias_informativas.append(
                    crear_incidencia_informativa_sin_conceptos(empleado)
                )
            
            # Empleados con todos los conceptos en 0
            conceptos_con_monto = conceptos.filter(monto_total__gt=0)
            if conceptos.count() > 0 and conceptos_con_monto.count() == 0:
                empleados_con_montos_cero += 1
                incidencias_informativas.append(
                    crear_incidencia_informativa_montos_cero(empleado)
                )
            
            # Detectar conceptos con montos muy altos (posibles errores)
            for concepto in conceptos:
                if concepto.monto_total > 10000000:  # Más de 10M
                    conceptos_anomalos.append(concepto)
                    incidencias_informativas.append(
                        crear_incidencia_informativa_monto_alto(empleado, concepto)
                    )
        
        # 4. CREAR INCIDENCIA RESUMEN
        incidencias_informativas.append(
            crear_incidencia_resumen_primer_cierre(cierre_actual, stats, empleados_sin_conceptos, empleados_con_montos_cero)
        )
        
        # 5. GUARDAR INCIDENCIAS INFORMATIVAS
        if incidencias_informativas:
            IncidenciaCierre.objects.bulk_create(
                incidencias_informativas,
                batch_size=100,
                ignore_conflicts=True
            )
        
        # 6. 🎯 ACTUALIZAR ESTADO DEL CIERRE PRIMER ANÁLISIS
        total_incidencias = len(incidencias_informativas)
        
        # Usar función centralizada para actualizar estados
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
            'incidencias_informativas': total_incidencias,
            'empleados_sin_conceptos': empleados_sin_conceptos,
            'empleados_con_montos_cero': empleados_con_montos_cero,
            'conceptos_anomalos': len(conceptos_anomalos),
            'clasificaciones_analizadas': clasificaciones_seleccionadas,
            'estadisticas': stats,
            'estado_final': cierre_actual.estado_incidencias,
            'mensaje': f'Primer cierre analizado: {total_incidencias} incidencias informativas detectadas'
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
        empleado_rut=empleado.rut_empleado,
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
        empleado_rut=empleado.rut_empleado,
        empleado_nombre=empleado.nombre_empleado,
        tipo_incidencia='empleado_montos_cero',
        tipo_comparacion='informativo',
        prioridad='alta',
        descripcion='Empleado con todos los conceptos en monto cero',
        impacto_monetario=Decimal('0'),
        datos_adicionales={
            'tipo_analisis': 'primer_cierre',
            'problema': 'montos_cero',
            'total_conceptos': empleado.conceptos_consolidados.count()
        }
    )

def crear_incidencia_informativa_monto_alto(empleado, concepto):
    """Crea incidencia informativa para concepto con monto anómalamente alto"""
    return IncidenciaCierre(
        cierre=empleado.cierre,
        empleado_rut=empleado.rut_empleado,
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
            'estadisticas': stats,
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
