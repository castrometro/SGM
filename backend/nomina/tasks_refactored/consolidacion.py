"""
🔄 CONSOLIDACIÓN DE DATOS - TASKS
==================================

Tareas Celery para consolidación de datos de nómina con dual logging.

Refactorizado desde: tasks.py
Versión: 3.0.0 (COMPLETO - Sin dependencias de tasks.py)
Fecha: 2025-10-24

Funcionalidades:
- Consolidación de datos (Libro + Movimientos + Analista)
- Dual logging (TarjetaActivityLogNomina + ActivityEvent)
- Soporte para modo optimizado y secuencial
- Procesamiento paralelo con Celery Chord
- Todas las funciones auxiliares incluidas

Patrones de Logging:
- consolidacion_iniciada → Process_Start (inicio visible en UI)
- consolidacion_completada → Data_Integration_Complete (éxito)
- consolidacion_error → Data_Integration_Error (error)
"""

import logging
import re
from celery import shared_task, chord, chain
from django.utils import timezone
from django.db import transaction
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


# ==============================================================================
# FUNCIONES AUXILIARES (INDEPENDIENTES)
# ==============================================================================

def normalizar_rut(rut):
    """
    Normaliza RUT para comparaciones removiendo puntos, guiones y espacios
    """
    if not rut:
        return ""
    
    # Convertir a string y limpiar
    rut_limpio = str(rut).strip()
    
    # Remover puntos, guiones, espacios
    rut_limpio = re.sub(r'[.\-\s]', '', rut_limpio)
    
    # Convertir a mayúsculas (por si el dígito verificador es 'k')
    rut_limpio = rut_limpio.upper()
    
    return rut_limpio


def calcular_chunk_size_dinamico(empleados_count):
    """
    🧮 Calcula el tamaño de chunk óptimo basado en el número de empleados
    
    Args:
        empleados_count: Número total de empleados a procesar
        
    Returns:
        int: Tamaño de chunk optimizado
    """
    if empleados_count <= 50:
        return 25  # Chunks pequeños para pocos empleados
    elif empleados_count <= 200:
        return 50  # Chunks medianos para empresas pequeñas-medianas
    elif empleados_count <= 500:
        return 100  # Chunks grandes para empresas medianas
    elif empleados_count <= 1000:
        return 150  # Chunks muy grandes para empresas grandes
    else:
        return 200  # Chunks extremos para corporaciones


# ==============================================================================
# FUNCIONES DE LOGGING DUAL
# ==============================================================================

def log_consolidacion_start(cierre_id, usuario_id, modo, detalles_extra=None):
    """
    Registra el INICIO de la consolidación en ambos sistemas de logging.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario que inició la consolidación
        modo: Modo de consolidación ('optimizado' o 'secuencial')
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Preparar detalles
        detalles = {
            'cierre_id': cierre_id,
            'periodo': cierre.periodo,
            'cliente_id': cierre.cliente_id,
            'estado_inicial': cierre.estado,
            'modo_consolidacion': modo,
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_iniciada",
            descripcion=f"Iniciando consolidación de datos de nómina (modo: {modo})",
            usuario=usuario,
            detalles=detalles,
            resultado="info"
        )
        
        # 2. LOG EN ACTIVITY EVENT (base de datos de eventos)
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.PROCESS_START,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.info(f"✅ Dual logging iniciado: consolidación cierre {cierre_id} - {modo}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_start: {e}")


def log_consolidacion_complete(cierre_id, usuario_id, resultado, detalles_extra=None):
    """
    Registra la FINALIZACIÓN EXITOSA de la consolidación en ambos sistemas.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        resultado: Resultado de la consolidación (dict con estadísticas)
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Estadísticas del resultado
        total_consolidados = resultado.get('empleados_consolidados', 0)
        total_headers = resultado.get('headers_consolidados', 0)
        total_movimientos = resultado.get('movimientos_consolidados', 0)
        
        # Preparar detalles
        detalles = {
            'cierre_id': cierre_id,
            'periodo': cierre.periodo,
            'estado_final': cierre.estado,
            'empleados_consolidados': total_consolidados,
            'headers_consolidados': total_headers,
            'movimientos_consolidados': total_movimientos,
            'duracion_segundos': resultado.get('duracion_segundos', 0),
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_completada",
            descripcion=(
                f"Consolidación completada exitosamente: "
                f"{total_consolidados} empleados, {total_headers} conceptos, "
                f"{total_movimientos} movimientos"
            ),
            usuario=usuario,
            detalles=detalles,
            resultado="exito"
        )
        
        # 2. LOG EN ACTIVITY EVENT
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.DATA_INTEGRATION_COMPLETE,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.info(f"✅ Dual logging completado: consolidación cierre {cierre_id} exitosa")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_complete: {e}")


def log_consolidacion_error(cierre_id, usuario_id, error, detalles_extra=None):
    """
    Registra un ERROR durante la consolidación en ambos sistemas.
    
    Args:
        cierre_id: ID del cierre
        usuario_id: ID del usuario
        error: Mensaje de error o excepción
        detalles_extra: Detalles adicionales opcionales
    """
    from nomina.models import CierreNomina, ActivityEvent
    from nomina.models_logging import registrar_actividad_tarjeta_nomina
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        usuario = User.objects.get(id=usuario_id) if usuario_id else None
        
        # Preparar detalles del error
        detalles = {
            'cierre_id': cierre_id,
            'error': str(error),
            'timestamp': timezone.now().isoformat()
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1. LOG EN TARJETA (UI visible)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta="consolidacion",
            accion="consolidacion_error",
            descripcion=f"Error en consolidación: {str(error)[:200]}",
            usuario=usuario,
            detalles=detalles,
            resultado="error"
        )
        
        # 2. LOG EN ACTIVITY EVENT
        if usuario:
            ActivityEvent.log(
                user=usuario,
                action=ActivityEvent.ActionChoices.DATA_INTEGRATION_ERROR,
                resource_type='cierre_nomina',
                resource_id=str(cierre_id),
                details=detalles
            )
        
        logger.error(f"✅ Dual logging error: consolidación cierre {cierre_id} - {error}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_consolidacion_error: {e}")


# ==============================================================================
# TAREA PRINCIPAL CON DUAL LOGGING
# ==============================================================================

@shared_task(bind=True, queue='nomina_queue')
def consolidar_datos_nomina_con_logging(self, cierre_id, usuario_id=None, modo='optimizado'):
    """
    🔄 TAREA PRINCIPAL: CONSOLIDACIÓN DE DATOS CON DUAL LOGGING
    
    Wrapper que ejecuta la consolidación (optimizada o secuencial) con logging dual.
    
    Args:
        cierre_id: ID del cierre a consolidar
        usuario_id: ID del usuario que inició la consolidación
        modo: 'optimizado' (Celery Chord) o 'secuencial' (procesamiento lineal)
    
    Returns:
        dict: Resultado de la consolidación con estadísticas
    
    Logging Dual:
        - TarjetaActivityLogNomina (tarjeta='consolidacion', visible en UI)
        - ActivityEvent (base de datos de eventos del sistema)
    """
    from nomina.models import CierreNomina
    
    tiempo_inicio = timezone.now()
    
    logger.info(f"🔄 [CONSOLIDACIÓN] Iniciando para cierre {cierre_id} - Modo: {modo}")
    
    # ✅ LOG DUAL: Inicio de consolidación
    log_consolidacion_start(
        cierre_id=cierre_id,
        usuario_id=usuario_id,
        modo=modo,
        detalles_extra={
            'task_id': self.request.id,
            'worker': self.request.hostname
        }
    )
    
    try:
        # EJECUTAR CONSOLIDACIÓN SEGÚN MODO
        if modo == 'optimizado':
            logger.info("🚀 Usando consolidación OPTIMIZADA con Celery Chord")
            resultado = consolidar_datos_nomina_task_optimizado(cierre_id)
        else:
            logger.info("⏳ Usando consolidación SECUENCIAL")
            resultado = consolidar_datos_nomina_task_secuencial(cierre_id)
        
        # Calcular duración
        tiempo_fin = timezone.now()
        duracion = (tiempo_fin - tiempo_inicio).total_seconds()
        
        # Agregar duración al resultado
        if isinstance(resultado, dict):
            resultado['duracion_segundos'] = duracion
        else:
            resultado = {
                'success': True,
                'duracion_segundos': duracion
            }
        
        # Obtener estadísticas de la consolidación
        cierre = CierreNomina.objects.get(id=cierre_id)
        resultado['empleados_consolidados'] = cierre.nomina_consolidada.count()
        
        # Contar headers consolidados
        from nomina.models import HeaderValorEmpleado
        resultado['headers_consolidados'] = HeaderValorEmpleado.objects.filter(
            nomina_consolidada__cierre=cierre
        ).count()
        
        # Contar movimientos consolidados
        from nomina.models import MovimientoPersonal
        resultado['movimientos_consolidados'] = MovimientoPersonal.objects.filter(
            nomina_consolidada__cierre=cierre
        ).count()
        
        # 🔄 ACTUALIZAR ESTADO DEL CIERRE
        # Si el cierre NO estaba en 'con_incidencias', cambiar a 'datos_consolidados'
        estado_anterior = cierre.estado
        if estado_anterior != 'con_incidencias':
            cierre.estado = 'datos_consolidados'
            cierre.save(update_fields=['estado'])
            resultado['estado_final'] = 'datos_consolidados'
            logger.info(f"✅ Estado actualizado: {estado_anterior} → datos_consolidados")
        else:
            resultado['estado_final'] = estado_anterior
            logger.info(f"ℹ️ Estado preservado: {estado_anterior} (con incidencias)")
        
        # ✅ LOG DUAL: Consolidación completada exitosamente
        log_consolidacion_complete(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            resultado=resultado,
            detalles_extra={
                'task_id': self.request.id,
                'modo': modo
            }
        )
        
        logger.info(
            f"✅ [CONSOLIDACIÓN] Completada para cierre {cierre_id}: "
            f"{resultado.get('empleados_consolidados', 0)} empleados, "
            f"{resultado.get('headers_consolidados', 0)} conceptos, "
            f"{resultado.get('movimientos_consolidados', 0)} movimientos "
            f"en {duracion:.2f}s"
        )

        # 🚀 DISPARO AUTOMÁTICO DE INCIDENCIAS (REFACTORIZADO)
        # Ejecutar generación automática de incidencias post-consolidación
        # (solo si el cierre está en estado que requiere incidencias)
        if resultado.get('estado_final') == 'con_incidencias':
            try:
                from nomina.tasks_refactored.incidencias import generar_incidencias_con_logging
                generar_incidencias_con_logging.delay(cierre_id, usuario_id or 0)
                logger.info(
                    f"🔁 [CONSOLIDACIÓN] Disparada generación automática de incidencias (tasks_refactored) para cierre {cierre_id}"
                )
            except Exception as e_auto:
                logger.error(
                    f"⚠️ [CONSOLIDACIÓN] No se pudo disparar incidencias automáticas (tasks_refactored) para cierre {cierre_id}: {e_auto}"
                )
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ [CONSOLIDACIÓN] Error para cierre {cierre_id}: {e}")
        
        # ❌ LOG DUAL: Error en consolidación
        log_consolidacion_error(
            cierre_id=cierre_id,
            usuario_id=usuario_id,
            error=str(e),
            detalles_extra={
                'task_id': self.request.id,
                'modo': modo,
                'tipo_error': type(e).__name__
            }
        )
        
        # Revertir estado del cierre
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado_consolidacion = 'error'
            cierre.save(update_fields=['estado_consolidacion'])
        except Exception as revert_error:
            logger.error(f"❌ Error revirtiendo estado: {revert_error}")
        
        # Re-lanzar la excepción para que Celery la registre
        raise


# ==============================================================================
# TASKS DE CONSOLIDACIÓN OPTIMIZADA (PARALELA CON CELERY CHORD)
# ==============================================================================

@shared_task
def consolidar_datos_nomina_task_optimizado(cierre_id):
    """
    🚀 TAREA OPTIMIZADA: CONSOLIDACIÓN DE DATOS DE NÓMINA CON CELERY CHORD
    
    Utiliza paralelización para optimizar el proceso de consolidación:
    1. Ejecuta tareas en paralelo usando chord
    2. Consolida resultados al final
    3. Reduce significativamente el tiempo de procesamiento
    """
    logger.info(f"🚀 Iniciando consolidación OPTIMIZADA de datos para cierre {cierre_id}")
    
    try:
        # 1. VERIFICAR PRERREQUISITOS
        from nomina.models import CierreNomina, NominaConsolidada, HeaderValorEmpleado, MovimientoPersonal
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        logger.info(f"📋 Cierre obtenido: {cierre} - Estado: {cierre.estado}")
        
        # Verificar estado (alineado con vista: permitir también 'con_incidencias')
        if cierre.estado not in ['verificado_sin_discrepancias', 'datos_consolidados', 'con_incidencias']:
            raise ValueError(
                "El cierre debe estar en 'verificado_sin_discrepancias', 'datos_consolidados' o 'con_incidencias', "
                f"actual: {cierre.estado}"
            )
        
        # Marcar consolidación en progreso sin cambiar el estado visible del cierre
        cierre.estado_consolidacion = 'consolidando'
        cierre.save(update_fields=['estado_consolidacion'])
        
        # 2. VERIFICAR ARCHIVOS PROCESADOS
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        if not movimientos:
            raise ValueError("No hay archivo de movimientos procesado")
            
        logger.info(f"📚 Libro: {libro.archivo.name}")
        logger.info(f"🔄 Movimientos: {movimientos.archivo.name}")
        
        # 3. LIMPIAR CACHE REDIS ANTES DE CONSOLIDAR
        # BUG FIX: Evitar que dashboards muestren datos antiguos de cache después de re-consolidar
        try:
            from nomina.cache_redis import get_cache_system_nomina
            cache_system = get_cache_system_nomina()
            cache_cleared = cache_system.clear_cierre_cache(
                cliente_id=cierre.cliente_id,
                periodo=str(cierre.periodo)
            )
            if cache_cleared:
                logger.info(f"🗑️ Cache Redis limpiado para cierre {cierre.id} antes de consolidar")
            else:
                logger.warning(f"⚠️ No se pudo limpiar completamente el cache Redis para cierre {cierre.id}")
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando cache Redis antes de consolidar: {e}")
        
        # 4. LIMPIAR CONSOLIDACIÓN ANTERIOR EN BD (SI EXISTE)
        consolidaciones_eliminadas = cierre.nomina_consolidada.count()
        if consolidaciones_eliminadas > 0:
            logger.info(f"🗑️ Eliminando {consolidaciones_eliminadas} registros de consolidación anterior en BD...")
            movimientos_eliminados = MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).count()
            MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).delete()
            
            cierre.nomina_consolidada.all().delete()
            logger.info(f"✅ {consolidaciones_eliminadas} registros de consolidación anterior eliminados exitosamente")
            logger.info(f"✅ {movimientos_eliminados} movimientos de personal anteriores eliminados exitosamente")
        else:
            logger.info("ℹ️ No hay consolidación anterior que eliminar")
        
        # 5. CÁLCULO DINÁMICO DE CHUNKS
        from nomina.models import EmpleadoCierre
        empleados_count = EmpleadoCierre.objects.filter(cierre=cierre).count()
        chunk_size = calcular_chunk_size_dinamico(empleados_count)
        logger.info(f"📊 Procesando {empleados_count} empleados con chunk size dinámico: {chunk_size}")
        
        # 6. INICIAR ORQUESTACIÓN: EMPLEADOS → MOVIMIENTOS → CONCEPTOS
        logger.info("🎯 Iniciando orquestación: empleados → movimientos → conceptos")

        flujo = chain(
            # Empleados del libro (usa su propio procesamiento batch interno)
            procesar_empleados_libro_paralelo.s(cierre_id, chunk_size),
            # Movimientos deben correr después de que existan las nóminas consolidadas
            procesar_movimientos_personal_paralelo.si(cierre_id),
            # Finalización: conceptos y cambio de estado
            finalizar_consolidacion_post_movimientos.si(cierre_id)
        )

        resultado_flujo = flujo.apply_async()

        logger.info(f"🔗 Cadena de consolidación iniciada para cierre {cierre_id}")

        return {
            'success': True,
            'cierre_id': cierre_id,
            'chain_id': getattr(resultado_flujo, 'id', None),
            'modo': 'optimizado_empleados_paralelo_movs_secuencial',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error en consolidación optimizada para cierre {cierre_id}: {e}")
        
        # Revertir estado en caso de error
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.save(update_fields=['estado'])
        except:
            pass
            
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'modo': 'optimizado_paralelo'
        }


@shared_task
def procesar_empleados_libro_paralelo(cierre_id, chunk_size=50):
    """
    📚 TAREA PARALELA: Procesar empleados del libro de remuneraciones
    
    Args:
        cierre_id: ID del cierre a procesar
        chunk_size: Tamaño dinámico de chunks para optimizar el procesamiento
    """
    logger.info(f"📚 [PARALELO] Procesando empleados del libro para cierre {cierre_id} (chunk_size: {chunk_size})")
    
    try:
        from nomina.models import CierreNomina, NominaConsolidada, HeaderValorEmpleado
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        
        empleados_consolidados = 0
        headers_consolidados = 0
        
        # Procesar empleados del libro en lotes para optimizar
        empleados = cierre.empleados.all()
        total_empleados = empleados.count()
        logger.info(f"👥 Procesando {total_empleados} empleados en lotes (chunk_size: {chunk_size})")
        
        # Procesar en lotes usando el chunk_size dinámico
        for i in range(0, total_empleados, chunk_size):
            batch_empleados = empleados[i:i + chunk_size]
            
            # Crear registros de nómina consolidada en lote
            nominas_batch = []
            headers_batch = []
            
            for empleado in batch_empleados:
                # Crear registro de nómina consolidada
                nomina_consolidada = NominaConsolidada(
                    cierre=cierre,
                    rut_empleado=normalizar_rut(empleado.rut),
                    nombre_empleado=f"{empleado.nombre} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                    estado_empleado='activo',
                    dias_trabajados=empleado.dias_trabajados,
                    fecha_consolidacion=timezone.now(),
                    fuente_datos={
                        'libro_id': libro.id,
                        'consolidacion_version': '3.0_optimizada_refactored',
                        'procesamiento': 'paralelo'
                    }
                )
                nominas_batch.append(nomina_consolidada)
            
            # Bulk create nóminas con manejo de duplicados
            NominaConsolidada.objects.bulk_create(nominas_batch, ignore_conflicts=True)
            empleados_consolidados += len(nominas_batch)
            
            # Procesar headers para este lote
            for j, empleado in enumerate(batch_empleados):
                try:
                    # Obtener o crear la nómina consolidada (manejo de duplicados)
                    nomina_consolidada, created = NominaConsolidada.objects.get_or_create(
                        cierre=cierre, 
                        rut_empleado=normalizar_rut(empleado.rut),
                        defaults={
                            'nombre_empleado': f"{empleado.nombre} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                            'estado_empleado': 'activo',
                            'dias_trabajados': empleado.dias_trabajados,
                            'fecha_consolidacion': timezone.now(),
                            'fuente_datos': {
                                'libro_id': libro.id,
                                'consolidacion_version': '3.0_optimizada_refactored',
                                'procesamiento': 'paralelo'
                            }
                        }
                    )
                
                    # Crear HeaderValorEmpleado para cada concepto
                    conceptos_empleado = empleado.registroconceptoempleado_set.all()
                    
                    for concepto in conceptos_empleado:
                        # Determinar si es numérico
                        valor_numerico = None
                        es_numerico = False
                        
                        if concepto.monto:
                            try:
                                valor_limpio = str(concepto.monto).replace('$', '').replace(',', '').strip()
                                if valor_limpio and (valor_limpio.replace('-', '').replace('.', '').isdigit()):
                                    valor_numerico = Decimal(valor_limpio)
                                    es_numerico = True
                            except (ValueError, InvalidOperation, AttributeError):
                                pass
                        
                        # Crear registro HeaderValorEmpleado
                        header = HeaderValorEmpleado(
                            nomina_consolidada=nomina_consolidada,
                            nombre_header=concepto.nombre_concepto_original,
                            concepto_remuneracion=concepto.concepto,
                            valor_original=concepto.monto or '',
                            valor_numerico=valor_numerico,
                            es_numerico=es_numerico,
                            fuente_archivo='libro_remuneraciones',
                            fecha_consolidacion=timezone.now()
                        )
                        headers_batch.append(header)
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando empleado {empleado.rut}: {e}")
                    continue
            
            # Bulk create headers cada cierto número para evitar memoria excesiva
            if len(headers_batch) >= 500:
                HeaderValorEmpleado.objects.bulk_create(headers_batch)
                headers_consolidados += len(headers_batch)
                headers_batch = []
                
            logger.info(f"📊 Progreso: {empleados_consolidados}/{total_empleados} empleados procesados")
        
        # Insertar headers restantes
        if headers_batch:
            HeaderValorEmpleado.objects.bulk_create(headers_batch)
            headers_consolidados += len(headers_batch)
        
        logger.info(f"✅ [PARALELO] Empleados procesados: {empleados_consolidados}, Headers: {headers_consolidados}")
        
        return {
            'success': True,
            'task': 'procesar_empleados_libro',
            'empleados_consolidados': empleados_consolidados,
            'headers_consolidados': headers_consolidados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando empleados para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_empleados_libro',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_movimientos_personal_paralelo(cierre_id):
    """
    🔄 TAREA PARALELA: Procesar movimientos de personal
    """
    logger.info(f"🔄 [PARALELO] Procesando movimientos de personal para cierre {cierre_id}")
    
    try:
        from nomina.models import (
            CierreNomina, NominaConsolidada, MovimientoPersonal,
            MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
            MovimientoVariacionSueldo, MovimientoVariacionContrato
        )
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        movimientos_creados = 0
        
        # Verificar si hay archivo de movimientos procesado
        movimientos_archivo = cierre.movimientos_mes.filter(estado='procesado').first()
        if not movimientos_archivo:
            logger.warning(f"⚠️ [PARALELO] No hay archivo de movimientos procesado para cierre {cierre_id}")
            return {
                'success': True,
                'task': 'procesar_movimientos_personal',
                'movimientos_creados': 0,
                'cierre_id': cierre_id,
                'info': 'No hay archivo de movimientos procesado'
            }
        
        logger.info(f"📁 [PARALELO] Archivo de movimientos encontrado: {movimientos_archivo.archivo.name}")
        
        # Crear lista para bulk_create y contadores
        movimientos_batch = []
        contador_altas_bajas = 0
        contador_ausentismos = 0
        contador_vacaciones = 0
        contador_variaciones_sueldo = 0
        contador_variaciones_contrato = 0
        
        # 1. Procesar ALTAS y BAJAS
        altas_bajas = MovimientoAltaBaja.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {altas_bajas.count()} registros de altas/bajas en BD")
        
        for movimiento in altas_bajas:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=normalizar_rut(movimiento.rut)
                )
                
                # Actualizar estado del empleado
                if movimiento.alta_o_baja == 'ALTA':
                    nomina_consolidada.estado_empleado = 'nueva_incorporacion'
                elif movimiento.alta_o_baja == 'BAJA':
                    nomina_consolidada.estado_empleado = 'finiquito'
                
                nomina_consolidada.save(update_fields=['estado_empleado'])
                
                # Crear MovimientoPersonal
                fecha_evt = movimiento.fecha_ingreso if movimiento.alta_o_baja == 'ALTA' else movimiento.fecha_retiro
                categoria = 'ingreso' if movimiento.alta_o_baja == 'ALTA' else 'finiquito'
                _desc = (movimiento.motivo or '')
                if _desc and len(_desc) > 300:
                    _desc = _desc[:300]
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    categoria=(categoria[:20] if categoria else None),
                    subtipo=None,
                    descripcion=_desc,
                    fecha_inicio=fecha_evt,
                    fecha_fin=fecha_evt,
                    dias_evento=1,
                    dias_en_periodo=1,
                    multi_mes=False,
                    observaciones=f"Tipo contrato: {movimiento.tipo_contrato}, Sueldo base: ${movimiento.sueldo_base:,.0f}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_refactored_v3'
                )
                movimientos_batch.append(mov_personal)
                contador_altas_bajas += 1
                
            except NominaConsolidada.DoesNotExist:
                # Crear empleado si no existe (caso de finiquitos)
                if movimiento.alta_o_baja == 'BAJA':
                    nomina_consolidada = NominaConsolidada.objects.create(
                        cierre=cierre,
                        rut_empleado=normalizar_rut(movimiento.rut),
                        nombre_empleado=movimiento.nombres_apellidos,
                        estado_empleado='finiquito',
                        fecha_consolidacion=timezone.now(),
                        fuente_datos={'movimiento_finiquito': True}
                    )
                    
                    _desc2 = (movimiento.motivo or '')
                    if _desc2 and len(_desc2) > 300:
                        _desc2 = _desc2[:300]
                    mov_personal = MovimientoPersonal(
                        nomina_consolidada=nomina_consolidada,
                        categoria='finiquito',
                        subtipo=None,
                        descripcion=_desc2,
                        fecha_inicio=movimiento.fecha_retiro,
                        fecha_fin=movimiento.fecha_retiro,
                        dias_evento=1,
                        dias_en_periodo=1,
                        multi_mes=False,
                        fecha_deteccion=timezone.now(),
                        detectado_por_sistema='consolidacion_refactored_v3'
                    )
                    movimientos_batch.append(mov_personal)
                    contador_altas_bajas += 1
        
        logger.info(f"✅ [PARALELO] {contador_altas_bajas} movimientos de altas/bajas procesados")
        
        # 2. Procesar AUSENTISMOS
        ausentismos = MovimientoAusentismo.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {ausentismos.count()} registros de ausentismo en BD")
        
        for ausentismo in ausentismos:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=normalizar_rut(ausentismo.rut)
                )
                
                # Actualizar estado si es ausencia total
                if ausentismo.dias >= 30:
                    nomina_consolidada.estado_empleado = 'ausente_total'
                else:
                    nomina_consolidada.estado_empleado = 'ausente_parcial'
                nomina_consolidada.save(update_fields=['estado_empleado'])
                
                # Crear MovimientoPersonal
                descripcion = f"{ausentismo.tipo} - {ausentismo.motivo}".strip(' -')
                subtipo = ausentismo.tipo.lower().replace(' ', '_') if ausentismo.tipo else 'sin_justificar'
                if subtipo and len(subtipo) > 40:
                    subtipo = subtipo[:40]
                fecha_inicio = ausentismo.fecha_inicio_ausencia
                fecha_fin = ausentismo.fecha_fin_ausencia
                dias_evento = (fecha_fin - fecha_inicio).days + 1 if fecha_inicio and fecha_fin else ausentismo.dias
                
                # Clipping al periodo
                try:
                    year, month = map(int, cierre.periodo.split('-'))
                    from datetime import date
                    import calendar
                    start_periodo = date(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    end_periodo = date(year, month, last_day)
                    clip_start = fecha_inicio if fecha_inicio > start_periodo else start_periodo
                    clip_end = fecha_fin if fecha_fin < end_periodo else end_periodo
                    dias_en_periodo = (clip_end - clip_start).days + 1 if clip_end >= clip_start else 0
                    multi_mes_flag = (fecha_inicio < start_periodo) or (fecha_fin > end_periodo)
                except Exception:
                    dias_en_periodo = ausentismo.dias
                    multi_mes_flag = False
                
                from hashlib import sha1
                base_hash = f"{nomina_consolidada.rut_empleado}:ausencia:{subtipo}:{fecha_inicio}:{fecha_fin}".lower()
                hash_evento = sha1(base_hash.encode('utf-8')).hexdigest()
                hash_registro_periodo = sha1(f"{hash_evento}:{cierre.periodo}".encode('utf-8')).hexdigest()
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    categoria='ausencia',
                    subtipo=subtipo or 'sin_justificar',
                    descripcion=descripcion,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    dias_evento=dias_evento,
                    dias_en_periodo=dias_en_periodo,
                    multi_mes=multi_mes_flag,
                    hash_evento=hash_evento,
                    hash_registro_periodo=hash_registro_periodo,
                    observaciones=f"Desde: {ausentismo.fecha_inicio_ausencia} hasta: {ausentismo.fecha_fin_ausencia}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_refactored_v3'
                )
                movimientos_batch.append(mov_personal)
                contador_ausentismos += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {ausentismo.rut} en ausentismo")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_ausentismos} movimientos de ausentismo procesados")
        
        # 3. Procesar VACACIONES
        vacaciones = MovimientoVacaciones.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {vacaciones.count()} registros de vacaciones en BD")
        
        for vacacion in vacaciones:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=normalizar_rut(vacacion.rut)
                )
                
                # Crear MovimientoPersonal
                fecha_inicio = vacacion.fecha_inicio
                fecha_fin = vacacion.fecha_fin_vacaciones
                dias_evento = (fecha_fin - fecha_inicio).days + 1 if fecha_inicio and fecha_fin else vacacion.cantidad_dias
                
                # Clipping al periodo
                try:
                    year, month = map(int, cierre.periodo.split('-'))
                    from datetime import date
                    import calendar
                    start_periodo = date(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    end_periodo = date(year, month, last_day)
                    clip_start = fecha_inicio if fecha_inicio > start_periodo else start_periodo
                    clip_end = fecha_fin if fecha_fin < end_periodo else end_periodo
                    dias_en_periodo = (clip_end - clip_start).days + 1 if clip_end >= clip_start else 0
                    multi_mes_flag = (fecha_inicio < start_periodo) or (fecha_fin > end_periodo)
                except Exception:
                    dias_en_periodo = vacacion.cantidad_dias
                    multi_mes_flag = False
                
                from hashlib import sha1
                base_hash = f"{nomina_consolidada.rut_empleado}:ausencia:vacaciones:{fecha_inicio}:{fecha_fin}".lower()
                hash_evento = sha1(base_hash.encode('utf-8')).hexdigest()
                hash_registro_periodo = sha1(f"{hash_evento}:{cierre.periodo}".encode('utf-8')).hexdigest()
                
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    categoria='ausencia',
                    subtipo='vacaciones',
                    descripcion='Vacaciones',
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    dias_evento=dias_evento,
                    dias_en_periodo=dias_en_periodo,
                    multi_mes=multi_mes_flag,
                    hash_evento=hash_evento,
                    hash_registro_periodo=hash_registro_periodo,
                    observaciones=f"Vacaciones desde: {vacacion.fecha_inicio} hasta: {vacacion.fecha_fin_vacaciones}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_refactored_v3'
                )
                movimientos_batch.append(mov_personal)
                contador_vacaciones += 1
                
            except NominaConsolidada.DoesNotExist:
                rut_normalizado = normalizar_rut(vacacion.rut)
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {vacacion.rut} → {rut_normalizado} en vacaciones")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_vacaciones} movimientos de vacaciones procesados")
        
        # 4. Procesar VARIACIONES DE SUELDO
        variaciones_sueldo = MovimientoVariacionSueldo.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {variaciones_sueldo.count()} registros de variaciones de sueldo en BD")
        
        for variacion in variaciones_sueldo:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=normalizar_rut(variacion.rut)
                )
                
                motivo_text = f"Cambio de sueldo: de ${variacion.sueldo_base_anterior:,.0f} a ${variacion.sueldo_base_actual:,.0f}"
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    categoria='cambio_datos',
                    subtipo='cambio_sueldo',
                    descripcion=motivo_text,
                    fecha_inicio=getattr(variacion, 'fecha_cambio', getattr(variacion, 'fecha_ingreso', timezone.now())),
                    fecha_fin=getattr(variacion, 'fecha_cambio', getattr(variacion, 'fecha_ingreso', timezone.now())),
                    dias_evento=1,
                    dias_en_periodo=1,
                    multi_mes=False,
                    observaciones=f"De ${variacion.sueldo_base_anterior:,.0f} a ${variacion.sueldo_base_actual:,.0f}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_refactored_v3'
                )
                movimientos_batch.append(mov_personal)
                contador_variaciones_sueldo += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación sueldo")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_variaciones_sueldo} movimientos de variación de sueldo procesados")
        
        # 5. Procesar VARIACIONES DE CONTRATO
        variaciones_contrato = MovimientoVariacionContrato.objects.filter(cierre=cierre)
        logger.info(f"📊 [PARALELO] Encontrados {variaciones_contrato.count()} registros de variaciones de contrato en BD")
        
        for variacion in variaciones_contrato:
            try:
                nomina_consolidada = NominaConsolidada.objects.get(
                    cierre=cierre, 
                    rut_empleado=normalizar_rut(variacion.rut)
                )
                
                motivo_text = f"Cambio de contrato: de {variacion.tipo_contrato_anterior} a {variacion.tipo_contrato_actual}"
                mov_personal = MovimientoPersonal(
                    nomina_consolidada=nomina_consolidada,
                    categoria='cambio_datos',
                    subtipo='cambio_contrato',
                    descripcion=motivo_text,
                    fecha_inicio=getattr(variacion, 'fecha_cambio', getattr(variacion, 'fecha_ingreso', timezone.now())),
                    fecha_fin=getattr(variacion, 'fecha_cambio', getattr(variacion, 'fecha_ingreso', timezone.now())),
                    dias_evento=1,
                    dias_en_periodo=1,
                    multi_mes=False,
                    observaciones=f"De {variacion.tipo_contrato_anterior} a {variacion.tipo_contrato_actual}",
                    fecha_deteccion=timezone.now(),
                    detectado_por_sistema='consolidacion_refactored_v3'
                )
                movimientos_batch.append(mov_personal)
                contador_variaciones_contrato += 1
                
            except NominaConsolidada.DoesNotExist:
                logger.warning(f"⚠️ No se encontró empleado consolidado para RUT {variacion.rut} en variación contrato")
                continue
        
        logger.info(f"✅ [PARALELO] {contador_variaciones_contrato} movimientos de variación de contrato procesados")
        
        # Bulk create movimientos en lotes
        if movimientos_batch:
            batch_size = 100
            for i in range(0, len(movimientos_batch), batch_size):
                batch = movimientos_batch[i:i + batch_size]
                MovimientoPersonal.objects.bulk_create(batch)
                movimientos_creados += len(batch)
        
        # Resumen detallado
        total_tipos = contador_altas_bajas + contador_ausentismos + contador_vacaciones + contador_variaciones_sueldo + contador_variaciones_contrato
        logger.info(f"📋 [PARALELO] RESUMEN DETALLADO DE MOVIMIENTOS:")
        logger.info(f"    ⬆️ Altas/Bajas: {contador_altas_bajas}")
        logger.info(f"    🏥 Ausentismos: {contador_ausentismos}")
        logger.info(f"    🏖️ Vacaciones: {contador_vacaciones}")
        logger.info(f"    💰 Variaciones Sueldo: {contador_variaciones_sueldo}")
        logger.info(f"    📑 Variaciones Contrato: {contador_variaciones_contrato}")
        logger.info(f"    📊 TOTAL TIPOS: {total_tipos}")
        logger.info(f"    ✅ TOTAL CREADOS: {movimientos_creados}")
        
        return {
            'success': True,
            'task': 'procesar_movimientos_personal',
            'movimientos_creados': movimientos_creados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando movimientos para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_movimientos_personal',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def procesar_conceptos_consolidados_paralelo(cierre_id):
    """
    💰 TAREA PARALELA: Procesar conceptos consolidados y calcular totales
    """
    logger.info(f"💰 [PARALELO] Procesando conceptos consolidados para cierre {cierre_id}")
    
    try:
        from nomina.models import CierreNomina, NominaConsolidada, HeaderValorEmpleado, ConceptoConsolidado
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        conceptos_consolidados = 0
        
        # Obtener todas las nóminas consolidadas
        nominas = NominaConsolidada.objects.filter(cierre=cierre).prefetch_related(
            'header_valores__concepto_remuneracion'
        )
        
        conceptos_batch = []
        
        logger.info(f"📊 Procesando conceptos para {nominas.count()} empleados")
        
        for nomina_consolidada in nominas:
            # Obtener todos los headers para este empleado
            headers_empleado = nomina_consolidada.header_valores.filter(
                es_numerico=True,
                concepto_remuneracion__isnull=False
            )
            
            # Totales por nuevas categorías
            total_haberes_imponibles = Decimal('0')
            total_haberes_no_imponibles = Decimal('0')
            total_dctos_legales = Decimal('0')
            total_otros_dctos = Decimal('0')
            total_impuestos = Decimal('0')
            total_horas_extras = Decimal('0')
            total_aportes_patronales = Decimal('0')
            
            # Agrupar por concepto y sumar
            conceptos_agrupados = {}
            
            for header in headers_empleado:
                concepto_nombre = header.concepto_remuneracion.nombre_concepto
                clasificacion = header.concepto_remuneracion.clasificacion
                
                if concepto_nombre not in conceptos_agrupados:
                    conceptos_agrupados[concepto_nombre] = {
                        'clasificacion': clasificacion,
                        'monto_total': Decimal('0'),
                        'cantidad': 0,
                        'concepto_obj': header.concepto_remuneracion
                    }
                
                conceptos_agrupados[concepto_nombre]['monto_total'] += header.valor_numerico
                conceptos_agrupados[concepto_nombre]['cantidad'] += 1
                
                # Sumar a la categoría correspondiente según clasificación proporcionada por analista
                if clasificacion == 'haberes_imponibles':
                    total_haberes_imponibles += header.valor_numerico
                elif clasificacion == 'haberes_no_imponibles':
                    total_haberes_no_imponibles += header.valor_numerico
                elif clasificacion == 'horas_extras':
                    try:
                        total_horas_extras += Decimal(header.valor_numerico) if header.valor_numerico is not None else Decimal('0')
                    except Exception:
                        total_horas_extras += Decimal('0')
                elif clasificacion == 'descuentos_legales':
                    total_dctos_legales += header.valor_numerico
                elif clasificacion == 'otros_descuentos':
                    total_otros_dctos += header.valor_numerico
                elif clasificacion == 'impuestos':
                    total_impuestos += header.valor_numerico
                elif clasificacion == 'aportes_patronales':
                    total_aportes_patronales += header.valor_numerico
            
            # Crear ConceptoConsolidado para cada concepto agrupado
            for concepto_nombre, datos in conceptos_agrupados.items():
                # Mapear clasificación a tipo_concepto
                clasificacion_mapping = {
                    'haberes_imponibles': 'haber_imponible',
                    'haberes_no_imponibles': 'haber_no_imponible',
                    'descuentos_legales': 'descuento_legal',
                    'otros_descuentos': 'otro_descuento',
                    'aportes_patronales': 'aporte_patronal',
                    'impuestos': 'impuesto'
                }
                
                tipo_concepto = clasificacion_mapping.get(datos['clasificacion'], 'informativo')
                codigo_concepto = str(datos['concepto_obj'].id) if datos['concepto_obj'] else None
                
                concepto_consolidado = ConceptoConsolidado(
                    nomina_consolidada=nomina_consolidada,
                    codigo_concepto=codigo_concepto,
                    nombre_concepto=concepto_nombre,
                    tipo_concepto=tipo_concepto,
                    monto_total=datos['monto_total'],
                    cantidad=datos['cantidad'],
                    es_numerico=True,
                    fuente_archivo='libro_remuneraciones'
                )
                conceptos_batch.append(concepto_consolidado)
            
            # Actualizar nuevos campos por categoría en la nómina consolidada
            nomina_consolidada.haberes_imponibles = total_haberes_imponibles
            nomina_consolidada.haberes_no_imponibles = total_haberes_no_imponibles
            nomina_consolidada.dctos_legales = total_dctos_legales
            nomina_consolidada.otros_dctos = total_otros_dctos
            nomina_consolidada.impuestos = total_impuestos
            nomina_consolidada.horas_extras_cantidad = total_horas_extras
            nomina_consolidada.aportes_patronales = total_aportes_patronales
            nomina_consolidada.save(update_fields=['haberes_imponibles', 'haberes_no_imponibles', 'dctos_legales', 'otros_dctos', 'impuestos', 'horas_extras_cantidad', 'aportes_patronales'])
        
        # Bulk create conceptos
        if conceptos_batch:
            batch_size = 200
            for i in range(0, len(conceptos_batch), batch_size):
                batch = conceptos_batch[i:i + batch_size]
                ConceptoConsolidado.objects.bulk_create(batch)
                conceptos_consolidados += len(batch)
        
        logger.info(f"✅ [PARALELO] Conceptos consolidados procesados: {conceptos_consolidados}")
        
        return {
            'success': True,
            'task': 'procesar_conceptos_consolidados',
            'conceptos_consolidados': conceptos_consolidados,
            'cierre_id': cierre_id
        }
        
    except Exception as e:
        logger.error(f"❌ [PARALELO] Error procesando conceptos para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'task': 'procesar_conceptos_consolidados',
            'error': str(e),
            'cierre_id': cierre_id
        }


@shared_task
def finalizar_consolidacion_post_movimientos(cierre_id):
    """
    🎯 TAREA FINAL: Ejecuta el procesamiento de conceptos y cierra la consolidación
    """
    logger.info(f"🎯 [FINAL] Ejecutando conceptos y finalizando consolidación para cierre {cierre_id}")

    try:
        from nomina.models import CierreNomina

        # Procesar conceptos
        resultado_conceptos = procesar_conceptos_consolidados_paralelo(cierre_id)
        conceptos_consolidados = 0
        if resultado_conceptos.get('success', False):
            conceptos_consolidados = resultado_conceptos.get('conceptos_consolidados', 0)
            logger.info(f"✅ [FINAL] Conceptos consolidados: {conceptos_consolidados}")
        else:
            logger.error(f"❌ [FINAL] Error procesando conceptos: {resultado_conceptos.get('error', 'Error desconocido')}")

        # Poner estado final del cierre (preservar 'con_incidencias' si corresponde)
        cierre = CierreNomina.objects.get(id=cierre_id)
        estado_anterior = cierre.estado
        if estado_anterior != 'con_incidencias':
            cierre.estado = 'datos_consolidados'
            campos_estado = ['estado']
        else:
            campos_estado = []
        
        try:
            cierre.estado_consolidacion = 'consolidado'
            update_fields = campos_estado + ['fecha_consolidacion', 'estado_consolidacion']
        except Exception:
            update_fields = campos_estado + ['fecha_consolidacion']
        
        cierre.fecha_consolidacion = timezone.now()
        cierre.save(update_fields=update_fields)

        # Si preservamos 'con_incidencias', disparar generación de incidencias usando tarea REFACTORIZADA
        if estado_anterior == 'con_incidencias':
            try:
                from nomina.tasks_refactored.incidencias import generar_incidencias_con_logging
                generar_incidencias_con_logging.delay(cierre_id, usuario_id=0)
                logger.info(
                    f"🧩 [FINAL] Cierre {cierre_id} en 'con_incidencias': incidencias (tasks_refactored) disparadas automáticamente"
                )
            except Exception as ex:
                logger.error(
                    f"⚠️ [FINAL] No se pudo disparar incidencias (tasks_refactored) automáticamente para cierre {cierre_id}: {ex}"
                )

        return {
            'success': True,
            'cierre_id': cierre_id,
            'conceptos_consolidados': conceptos_consolidados,
            'nuevo_estado': cierre.estado
        }
    except Exception as e:
        logger.error(f"❌ [FINAL] Error finalizando consolidación para cierre {cierre_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id
        }


# ==============================================================================
# TASK DE CONSOLIDACIÓN SECUENCIAL (ALTERNATIVA)
# ==============================================================================

@shared_task
def consolidar_datos_nomina_task_secuencial(cierre_id):
    """
    ⏳ TAREA SECUENCIAL: CONSOLIDACIÓN DE DATOS DE NÓMINA
    
    Versión secuencial (no paralela) para compatibilidad.
    Procesa empleados, movimientos y conceptos de forma lineal.
    """
    logger.info(f"⏳ Iniciando consolidación SECUENCIAL de datos para cierre {cierre_id}")
    
    try:
        from nomina.models import (
            CierreNomina, NominaConsolidada, HeaderValorEmpleado, MovimientoPersonal,
            MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
            MovimientoVariacionSueldo, MovimientoVariacionContrato, ConceptoConsolidado
        )
        
        cierre = CierreNomina.objects.get(id=cierre_id)
        logger.info(f"📋 Cierre obtenido: {cierre} - Estado: {cierre.estado}")
        
        # Verificar estado
        if cierre.estado not in ['verificado_sin_discrepancias', 'datos_consolidados', 'con_incidencias']:
            raise ValueError(f"El cierre debe estar en estado válido, actual: {cierre.estado}")
        
        # Marcar consolidación en progreso
        cierre.estado_consolidacion = 'consolidando'
        cierre.save(update_fields=['estado_consolidacion'])
        
        # Obtener archivos procesados
        libro = cierre.libros_remuneraciones.filter(estado='procesado').first()
        movimientos = cierre.movimientos_mes.filter(estado='procesado').first()
        
        if not libro:
            raise ValueError("No hay libro de remuneraciones procesado")
        if not movimientos:
            raise ValueError("No hay archivo de movimientos procesado")
            
        logger.info(f"📚 Libro: {libro.archivo.name}")
        logger.info(f"🔄 Movimientos: {movimientos.archivo.name}")
        
        # Limpiar cache Redis antes de consolidar (igual que versión optimizada)
        try:
            from nomina.cache_redis import get_cache_system_nomina
            cache_system = get_cache_system_nomina()
            cache_cleared = cache_system.clear_cierre_cache(
                cliente_id=cierre.cliente_id,
                periodo=str(cierre.periodo)
            )
            if cache_cleared:
                logger.info(f"🗑️ Cache Redis limpiado para cierre {cierre.id} antes de consolidar (modo secuencial)")
            else:
                logger.warning(f"⚠️ No se pudo limpiar completamente el cache Redis para cierre {cierre.id}")
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando cache Redis antes de consolidar: {e}")
        
        # Limpiar consolidación anterior en BD
        consolidaciones_eliminadas = cierre.nomina_consolidada.count()
        if consolidaciones_eliminadas > 0:
            logger.info(f"🗑️ Eliminando {consolidaciones_eliminadas} registros de consolidación anterior en BD...")
            MovimientoPersonal.objects.filter(nomina_consolidada__cierre=cierre).delete()
            cierre.nomina_consolidada.all().delete()
        
        # Procesar empleados del libro
        empleados_consolidados = 0
        headers_consolidados = 0
        
        empleados = cierre.empleados.all()
        logger.info(f"👥 Procesando {empleados.count()} empleados")
        
        for empleado in empleados:
            # Crear registro de nómina consolidada
            nomina_consolidada = NominaConsolidada.objects.create(
                cierre=cierre,
                rut_empleado=normalizar_rut(empleado.rut),
                nombre_empleado=f"{empleado.nombre} {empleado.apellido_paterno} {empleado.apellido_materno}".strip(),
                estado_empleado='activo',
                dias_trabajados=empleado.dias_trabajados,
                fecha_consolidacion=timezone.now(),
                fuente_datos={
                    'libro_id': libro.id,
                    'movimientos_id': movimientos.id,
                    'consolidacion_version': '3.0_secuencial_refactored'
                }
            )
            
            # Crear HeaderValorEmpleado para cada concepto
            conceptos_empleado = empleado.registroconceptoempleado_set.all()
            
            for concepto in conceptos_empleado:
                # Determinar si es numérico
                valor_numerico = None
                es_numerico = False
                
                if concepto.monto:
                    try:
                        valor_limpio = str(concepto.monto).replace('$', '').replace(',', '').strip()
                        if valor_limpio and (valor_limpio.replace('-', '').replace('.', '').isdigit()):
                            valor_numerico = Decimal(valor_limpio)
                            es_numerico = True
                    except (ValueError, InvalidOperation, AttributeError):
                        pass
                
                # Crear registro HeaderValorEmpleado
                HeaderValorEmpleado.objects.create(
                    nomina_consolidada=nomina_consolidada,
                    nombre_header=concepto.nombre_concepto_original,
                    concepto_remuneracion=concepto.concepto,
                    valor_original=concepto.monto or '',
                    valor_numerico=valor_numerico,
                    es_numerico=es_numerico,
                    fuente_archivo='libro_remuneraciones',
                    fecha_consolidacion=timezone.now()
                )
                headers_consolidados += 1
            
            empleados_consolidados += 1
            
            if empleados_consolidados % 100 == 0:
                logger.info(f"📊 Progreso: {empleados_consolidados} empleados consolidados")
        
        logger.info(f"✅ Empleados consolidados: {empleados_consolidados}")
        logger.info(f"✅ Headers consolidados: {headers_consolidados}")
        
        # Procesar movimientos (llamar a la función paralela que es reutilizable)
        resultado_movimientos = procesar_movimientos_personal_paralelo(cierre_id)
        movimientos_creados = resultado_movimientos.get('movimientos_creados', 0)
        
        # Procesar conceptos
        resultado_conceptos = procesar_conceptos_consolidados_paralelo(cierre_id)
        conceptos_consolidados = resultado_conceptos.get('conceptos_consolidados', 0)
        
        # Actualizar estado del cierre
        estado_anterior = cierre.estado
        if estado_anterior != 'con_incidencias':
            cierre.estado = 'datos_consolidados'
        
        cierre.estado_consolidacion = 'consolidado'
        cierre.fecha_consolidacion = timezone.now()
        cierre.save()
        
        logger.info(f"✅ Consolidación SECUENCIAL completada:")
        logger.info(f"   📊 {empleados_consolidados} empleados")
        logger.info(f"   📋 {headers_consolidados} headers")
        logger.info(f"   🔄 {movimientos_creados} movimientos")
        logger.info(f"   💰 {conceptos_consolidados} conceptos")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'modo': 'secuencial',
            'empleados_consolidados': empleados_consolidados,
            'headers_consolidados': headers_consolidados,
            'movimientos_creados': movimientos_creados,
            'conceptos_consolidados': conceptos_consolidados,
            'nuevo_estado': cierre.estado
        }
        
    except Exception as e:
        logger.error(f"❌ Error en consolidación secuencial para cierre {cierre_id}: {e}")
        
        # Revertir estado en caso de error
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
            cierre.estado = 'verificado_sin_discrepancias'
            cierre.estado_consolidacion = 'error'
            cierre.save()
        except:
            pass
            
        return {
            'success': False,
            'error': str(e),
            'cierre_id': cierre_id,
            'modo': 'secuencial'
        }
