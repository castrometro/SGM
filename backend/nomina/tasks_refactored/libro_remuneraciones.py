"""
📖 Tareas Celery: Libro de Remuneraciones

Procesamiento completo del libro de remuneraciones Excel:
1. analizar_headers_con_logging: Extrae columnas del Excel
2. clasificar_headers_con_logging: Compara columnas con ConceptoRemuneracion vigentes
3. actualizar_empleados: Actualiza/crea registros de empleados
4. guardar_registros: Guarda registros de nómina por empleado
5. actualizar_empleados_optimizado: Versión paralela con Chord
6. guardar_registros_optimizado: Versión paralela con Chord

Autor: Sistema SGM
Fecha: 18 de octubre de 2025
"""

import logging
import pandas as pd
from celery import shared_task, chord
from django.contrib.auth import get_user_model
from django.utils import timezone

# Models
from ..models import (
    LibroRemuneracionesUpload,
    ActivityEvent,
)
from ..models_logging_stub import UploadLogNomina
from ..models_logging import registrar_actividad_tarjeta_nomina  # ← Para logs de usuario

# Utils
from ..utils.LibroRemuneraciones import (
    obtener_headers_libro_remuneraciones,
    clasificar_headers_libro_remuneraciones,
    actualizar_empleados_desde_libro_util,
    guardar_registros_nomina_util,
)
from ..utils.LibroRemuneracionesOptimizado import (
    dividir_dataframe_empleados,
    consolidar_stats_empleados,
    consolidar_stats_registros,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_sistema_user():
    """Helper: Obtener usuario del sistema para tasks sin request.user"""
    return User.objects.filter(is_staff=True).first() or User.objects.first()


def _calcular_chunk_size_dinamico(empleados_count):
    """
    Calcula chunk size óptimo basado en cantidad de empleados.
    
    Args:
        empleados_count: Total de empleados
        
    Returns:
        int: Chunk size óptimo
    """
    if empleados_count <= 50:
        return empleados_count  # Sin paralelización
    elif empleados_count <= 200:
        return 50
    elif empleados_count <= 500:
        return 100
    elif empleados_count <= 1000:
        return 150
    else:
        return 200


# ============================================================================
# TAREA 1: Analizar Headers
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def analizar_headers_libro_remuneraciones_con_logging(self, libro_id, upload_log_id, usuario_id=None):
    """
    Analiza headers del Excel y los guarda en LibroRemuneracionesUpload.header_json
    
    Args:
        libro_id: ID del LibroRemuneracionesUpload
        upload_log_id: ID del UploadLogNomina (puede ser None)
        usuario_id: ID del usuario que subió el archivo (opcional, usa SISTEMA si es None)
        
    Returns:
        dict: {"libro_id", "upload_log_id", "headers"}
        
    Raises:
        Exception: Si el archivo no existe o no se pueden leer los headers
        
    ActivityEvents:
        - analisis_headers_iniciado (inicio)
        - analisis_headers_exitoso (éxito)
        - analisis_headers_error (error)
    """
    logger.info(f"[LIBRO] Analizando headers libro_id={libro_id}")
    
    # Obtener datos del libro y cierre
    try:
        libro = LibroRemuneracionesUpload.objects.select_related(
            'cierre', 'cierre__cliente'
        ).get(id=libro_id)
        cierre = libro.cierre
        cliente = cierre.cliente
        # Obtener usuario real si se pasó, sino usar SISTEMA
        if usuario_id:
            from api.models import Usuario
            usuario = Usuario.objects.get(id=usuario_id)
        else:
            usuario = _get_sistema_user()
    except Exception as e:
        logger.error(f"[LIBRO] No se pudo obtener libro {libro_id}: {e}")
        raise
    
    try:
        # ✅ LOGGING V2: Inicio
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='analisis_headers_iniciado',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
                'archivo': libro.archivo.name.split('/')[-1] if libro.archivo else 'sin_archivo',
            }
        )
        
        # Actualizar estado del libro
        libro.estado = "analizando_hdrs"
        libro.save(update_fields=['estado'])
        
        # Actualizar UploadLog si existe
        upload_log = None
        if upload_log_id:
            try:
                upload_log = UploadLogNomina.objects.get(id=upload_log_id)
                upload_log.estado = "analizando_hdrs"
                upload_log.save()
            except Exception as e:
                logger.debug(f"[LIBRO] UploadLog no disponible: {e}")
        
        # Procesar headers del Excel
        headers = obtener_headers_libro_remuneraciones(libro.archivo.path)
        
        # Guardar headers en el libro
        libro.header_json = headers
        libro.estado = "hdrs_analizados"
        libro.save(update_fields=['header_json', 'estado'])
        
        # Actualizar UploadLog con headers
        if upload_log:
            upload_log.estado = "hdrs_analizados"
            upload_log.headers_detectados = headers
            upload_log.save()
        
        # ✅ LOGGING V2: Éxito
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='analisis_headers_exitoso',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
                'headers_detectados': len(headers),
                'archivo': libro.archivo.name.split('/')[-1] if libro.archivo else 'sin_archivo',
            }
        )
        
        logger.info(f"[LIBRO] ✅ Headers analizados: {len(headers)} columnas")
        
        return {
            "libro_id": libro_id,
            "upload_log_id": upload_log_id,
            "usuario_id": usuario_id,  # ← NUEVO: Pasar usuario_id a la siguiente tarea
            "headers": headers
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error analizando headers: {e}", exc_info=True)
        
        # ✅ LOGGING V2: Error
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='error',
            action='analisis_headers_error',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
                'error': str(e),
            }
        )
        
        # Marcar errores
        libro.estado = "con_error"
        libro.save(update_fields=['estado'])
        
        if upload_log_id:
            try:
                upload_log = UploadLogNomina.objects.get(id=upload_log_id)
                upload_log.marcar_como_error(f"Error analizando headers: {str(e)}")
            except:
                pass
        
        raise


# ============================================================================
# TAREA 2: Clasificar Headers
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def clasificar_headers_libro_remuneraciones_con_logging(self, result):
    """
    Clasifica headers comparándolos con ConceptoRemuneracion vigentes del cliente.
    
    Recibe headers del Excel y los compara con los conceptos de nómina
    registrados en la base de datos para el cliente específico.
    
    Clasificación por match exacto (case-insensitive):
    - Si header coincide con un ConceptoRemuneracion vigente → clasificado
    - Si no coincide → sin clasificar (requiere mapeo manual)
    
    Args:
        result: Resultado de analizar_headers (dict con libro_id, headers, usuario_id)
        
    Returns:
        dict: {"libro_id", "headers_clasificados", "headers_sin_clasificar", "estado_final"}
        
    Raises:
        Exception: Si falla la clasificación
        
    ActivityEvents:
        - clasificacion_headers_iniciada (inicio)
        - clasificacion_headers_exitosa (éxito)
        - clasificacion_headers_error (error)
    """
    libro_id = result["libro_id"]
    upload_log_id = result["upload_log_id"]
    usuario_id = result.get("usuario_id")  # ← NUEVO: Obtener usuario_id
    
    logger.info(f"[LIBRO] Clasificando headers libro_id={libro_id}")
    
    # Obtener datos del libro
    try:
        libro = LibroRemuneracionesUpload.objects.select_related(
            'cierre', 'cierre__cliente'
        ).get(id=libro_id)
        cierre = libro.cierre
        cliente = cierre.cliente
        # Obtener usuario real si se pasó, sino usar SISTEMA
        if usuario_id:
            from api.models import Usuario
            usuario = Usuario.objects.get(id=usuario_id)
        else:
            usuario = _get_sistema_user()
    except Exception as e:
        logger.error(f"[LIBRO] No se pudo obtener libro {libro_id}: {e}")
        raise
    
    try:
        # ✅ LOGGING V2: Inicio
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='clasificacion_headers_iniciada',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
            }
        )
        
        # Actualizar estados
        libro.estado = "clasif_en_proceso"
        libro.save(update_fields=['estado'])
        
        upload_log = None
        if upload_log_id:
            try:
                upload_log = UploadLogNomina.objects.get(id=upload_log_id)
                upload_log.estado = "clasif_en_proceso"
                upload_log.save()
            except Exception as e:
                logger.debug(f"[LIBRO] UploadLog no disponible: {e}")
        
        # Obtener headers (de libro o resultado anterior)
        if isinstance(libro.header_json, list):
            headers = libro.header_json
        else:
            headers = result["headers"]
        
        # Clasificar headers con IA
        headers_clasificados, headers_sin_clasificar = (
            clasificar_headers_libro_remuneraciones(headers, cliente)
        )
        
        # Guardar clasificación en el libro
        libro.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }
        
        # Determinar estado final
        if headers_sin_clasificar:
            libro.estado = "clasif_pendiente"
        else:
            libro.estado = "clasificado"
        
        libro.save(update_fields=['header_json', 'estado'])
        
        # Actualizar UploadLog
        if upload_log:
            upload_log.estado = libro.estado
            upload_log.resumen = {
                "libro_id": libro_id,
                "headers_total": len(headers),
                "headers_clasificados": len(headers_clasificados),
                "headers_sin_clasificar": len(headers_sin_clasificar),
                "clasificados": headers_clasificados,
                "sin_clasificar": headers_sin_clasificar
            }
            upload_log.save()
        
        # ✅ LOGGING V2: Éxito
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action='clasificacion_headers_exitosa',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
                'headers_total': len(headers),
                'headers_clasificados': len(headers_clasificados),
                'headers_sin_clasificar': len(headers_sin_clasificar),
                'estado_final': libro.estado,
            }
        )
        
        logger.info(
            f"[LIBRO] ✅ Clasificación: {len(headers_clasificados)} clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        
        # ✅ LOGGING USUARIO: Clasificación completada (para historial UI)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta="libro_remuneraciones",
            accion="classification_complete",
            descripcion=f"Clasificación completada: {len(headers_clasificados)} de {len(headers)} columnas identificadas",
            usuario=usuario,  # ← CORREGIDO: Usar usuario real en lugar de SISTEMA
            detalles={
                'headers_total': len(headers),
                'headers_clasificados': len(headers_clasificados),
                'headers_sin_clasificar': len(headers_sin_clasificar),
                'estado': libro.estado,
                'hora': timezone.now().strftime('%H:%M:%S')
            },
            resultado="exito"
        )
        logger.info(f"✅ TarjetaActivityLog registrado: classification_complete para libro {libro_id} (usuario_id={usuario_id})")
        
        return {
            "libro_id": libro_id,
            "upload_log_id": upload_log_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
            "estado_final": libro.estado
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error clasificando headers: {e}", exc_info=True)
        
        # ✅ LOGGING V2: Error
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='error',
            action='clasificacion_headers_error',
            resource_type='libro_remuneraciones',
            resource_id=str(libro_id),
            details={
                'task_id': self.request.id,
                'error': str(e),
            }
        )
        
        # Marcar errores
        libro.estado = "con_error"
        libro.save(update_fields=['estado'])
        
        if upload_log_id:
            try:
                upload_log = UploadLogNomina.objects.get(id=upload_log_id)
                upload_log.marcar_como_error(f"Error clasificando headers: {str(e)}")
            except:
                pass
        
        raise


# ============================================================================
# TAREA 3: Actualizar Empleados (Secuencial)
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def actualizar_empleados_desde_libro(self, result):
    """
    Actualiza/crea registros de EmpleadoCierre desde el libro.
    
    Versión secuencial (sin paralelización). Lee el Excel y por cada fila
    crea o actualiza el empleado en la base de datos.
    
    Args:
        result: Resultado anterior (dict con libro_id o solo libro_id)
        
    Returns:
        dict: {"libro_id", "empleados_actualizados"}
        
    Raises:
        Exception: Si falla la actualización
    """
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    
    logger.info(f"[LIBRO] Actualizando empleados libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        count = actualizar_empleados_desde_libro_util(libro)
        
        logger.info(f"[LIBRO] ✅ {count} empleados actualizados")
        
        return {
            "libro_id": libro_id,
            "empleados_actualizados": count
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error actualizando empleados: {e}", exc_info=True)
        raise


# ============================================================================
# TAREA 4: Guardar Registros Nómina (Secuencial)
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def guardar_registros_nomina(self, result):
    """
    Guarda registros de nómina por empleado desde el libro.
    
    Versión secuencial. Lee el Excel y por cada fila crea registros
    de RegistroNomina con todos los conceptos del empleado.
    
    Args:
        result: Resultado anterior (dict con libro_id o solo libro_id)
        
    Returns:
        dict: {"libro_id", "registros_actualizados", "estado"}
        
    Raises:
        Exception: Si falla el guardado
    """
    libro_id = result.get("libro_id") if isinstance(result, dict) else result
    
    logger.info(f"[LIBRO] Guardando registros nómina libro_id={libro_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        count = guardar_registros_nomina_util(libro)
        
        # Actualizar estado a procesado
        libro.estado = "procesado"
        libro.save(update_fields=['estado'])
        
        logger.info(f"[LIBRO] ✅ {count} registros guardados - Estado: procesado")
        
        return {
            "libro_id": libro_id,
            "registros_actualizados": count,
            "estado": "procesado"
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error guardando registros: {e}", exc_info=True)
        
        # Marcar como error
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            libro.estado = "con_error"
            libro.save(update_fields=['estado'])
        except:
            pass
        
        raise


# ============================================================================
# TAREA 5: Actualizar Empleados (Optimizado con Chord)
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def actualizar_empleados_desde_libro_optimizado(self, result, usuario_id=None, usar_chord=True):
    """
    Actualiza empleados en paralelo usando Celery Chord.
    
    Divide el Excel en chunks y procesa cada chunk en paralelo.
    Más rápido para libros grandes (>200 empleados).
    
    Args:
        result: Resultado anterior (dict con libro_id) o libro_id directo
        usuario_id: ID del usuario que inició el procesamiento
        usar_chord: Si False, usa versión secuencial
        
    Returns:
        dict: {"libro_id", "usuario_id", "chord_id", "chunks_totales", "modo"} o 
              {"libro_id", "usuario_id", "empleados_actualizados"} si secuencial
              
    Raises:
        Exception: Si falla la paralelización (hace fallback a secuencial)
    """
    # Extraer libro_id dependiendo del formato de result
    if isinstance(result, dict):
        libro_id = result.get("libro_id")
        # Si viene de upload/clasificación, puede tener usuario_id
        if not usuario_id and "usuario_id" in result:
            usuario_id = result["usuario_id"]
    else:
        libro_id = result
    
    logger.info(f"[LIBRO] Actualizando empleados (optimizado) libro_id={libro_id}, usuario_id={usuario_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        # Fallback a secuencial si no usar chord
        if not usar_chord:
            logger.info(f"[LIBRO] Usando método secuencial")
            count = actualizar_empleados_desde_libro_util(libro)
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "empleados_actualizados": count
            }
        
        # Calcular chunk size dinámico
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        chunk_size = _calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"[LIBRO] Total: {total_filas} filas, Chunk size: {chunk_size}")
        
        # Dividir en chunks
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        
        if not chunks:
            logger.warning(f"[LIBRO] No hay chunks válidos")
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "empleados_actualizados": 0
            }
        
        # Crear tasks paralelas (importación dinámica para evitar circular imports)
        from . import procesar_chunk_empleados_task, consolidar_empleados_task
        
        tasks_paralelas = [
            procesar_chunk_empleados_task.s(libro_id, chunk_data)
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback
        callback = consolidar_empleados_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"[LIBRO] 🚀 Chord iniciado: {len(chunks)} chunks en paralelo")
        
        return {
            "libro_id": libro_id,
            "usuario_id": usuario_id,  # ← Propagar usuario_id
            "chord_id": resultado_chord.id if hasattr(resultado_chord, 'id') else None,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord"
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error en optimizado, fallback a secuencial: {e}")
        
        # Fallback a secuencial
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            count = actualizar_empleados_desde_libro_util(libro)
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "empleados_actualizados": count,
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"[LIBRO] ❌ Error en fallback: {fallback_error}")
            raise


# ============================================================================
# TAREA 6: Guardar Registros (Optimizado con Chord)
# ============================================================================

@shared_task(bind=True, queue='nomina_queue')
def guardar_registros_nomina_optimizado(self, result, usar_chord=True):
    """
    Guarda registros de nómina en paralelo usando Celery Chord.
    
    Divide el Excel en chunks y procesa cada chunk en paralelo.
    Más rápido para libros grandes (>200 empleados).
    
    Args:
        result: Resultado anterior (dict con libro_id, usuario_id)
        usar_chord: Si False, usa versión secuencial
        
    Returns:
        dict: {"libro_id", "usuario_id", "chord_id", "chunks_totales", "modo"} o
              {"libro_id", "usuario_id", "registros_actualizados", "estado"} si secuencial
              
    Raises:
        Exception: Si falla la paralelización (hace fallback a secuencial)
    """
    # Extraer libro_id y usuario_id del resultado anterior
    if isinstance(result, dict):
        libro_id = result.get("libro_id")
        usuario_id = result.get("usuario_id")
    else:
        libro_id = result
        usuario_id = None
    
    logger.info(f"[LIBRO] Guardando registros (optimizado) libro_id={libro_id}, usuario_id={usuario_id}")
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        
        # Fallback a secuencial si no usar chord
        if not usar_chord:
            logger.info(f"[LIBRO] Usando método secuencial")
            count = guardar_registros_nomina_util(libro)
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "registros_actualizados": count,
                "estado": "procesado"
            }
        
        # Calcular chunk size dinámico
        df = pd.read_excel(libro.archivo.path, engine="openpyxl")
        total_filas = len(df)
        chunk_size = _calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"[LIBRO] Total: {total_filas} filas, Chunk size: {chunk_size}")
        
        # Dividir en chunks
        chunks = dividir_dataframe_empleados(libro.archivo.path, chunk_size)
        
        if not chunks:
            logger.warning(f"[LIBRO] No hay chunks válidos")
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "registros_actualizados": 0,
                "estado": "procesado"
            }
        
        # Crear tasks paralelas (importación dinámica)
        from . import procesar_chunk_registros_task, consolidar_registros_task
        
        # ✅ IMPORTANTE: Pasar usuario_id en el contexto del chunk
        # Los workers individuales no lo necesitan, pero el callback sí
        tasks_paralelas = [
            procesar_chunk_registros_task.s(libro_id, chunk_data)
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback que recibe usuario_id
        # NOTA: El callback consolidar_registros_task recibirá los resultados de los chunks
        # Necesitamos pasar usuario_id de alguna forma al callback
        callback = consolidar_registros_task.s(usuario_id=usuario_id)
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"[LIBRO] 🚀 Chord de registros iniciado: {len(chunks)} chunks con usuario_id={usuario_id}")
        
        return {
            "libro_id": libro_id,
            "usuario_id": usuario_id,  # ← Propagar usuario_id
            "chord_id": resultado_chord.id if hasattr(resultado_chord, 'id') else None,
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord",
            "estado": "procesando"  # Se actualizará en callback
        }
        
    except Exception as e:
        logger.error(f"[LIBRO] ❌ Error en optimizado, fallback a secuencial: {e}")
        
        # Fallback a secuencial
        try:
            libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
            count = guardar_registros_nomina_util(libro)
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id,
                "usuario_id": usuario_id,  # ← Propagar usuario_id
                "registros_actualizados": count,
                "estado": "procesado",
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"[LIBRO] ❌ Error en fallback: {fallback_error}")
            raise
            libro.save(update_fields=['estado'])
            return {
                "libro_id": libro_id,
                "registros_actualizados": count,
                "estado": "procesado",
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"[LIBRO] ❌ Error en fallback: {fallback_error}")
            raise


# ============================================================================
# HELPER TASKS (Chord Workers - No exportadas directamente)
# ============================================================================

@shared_task(queue='nomina_queue')
def procesar_chunk_empleados_task(libro_id, chunk_data):
    """Worker: Procesa un chunk de empleados (usado por chord)"""
    from ..utils.LibroRemuneracionesOptimizado import procesar_chunk_empleados_util
    
    try:
        libro = LibroRemuneracionesUpload.objects.get(id=libro_id)
        stats = procesar_chunk_empleados_util(libro, chunk_data)
        return stats
    except Exception as e:
        logger.error(f"[LIBRO] Error en chunk empleados: {e}")
        return {"empleados_procesados": 0, "error": str(e)}


@shared_task(queue='nomina_queue')
def procesar_chunk_registros_task(libro_id, chunk_data):
    """Worker: Procesa un chunk de registros (usado por chord)"""
    from ..utils.LibroRemuneracionesOptimizado import procesar_chunk_registros_util
    
    try:
        stats = procesar_chunk_registros_util(libro_id, chunk_data)  # ← CORREGIDO: pasar libro_id directamente
        # ✅ Agregar libro_id a los stats para que el callback lo tenga
        stats['libro_id'] = libro_id
        return stats
    except Exception as e:
        logger.error(f"[LIBRO] Error en chunk registros: {e}")
        return {"registros_procesados": 0, "libro_id": libro_id, "error": str(e)}


@shared_task(queue='nomina_queue')
def consolidar_empleados_task(resultados_chunks):
    """Callback: Consolida resultados de todos los chunks de empleados"""
    stats = consolidar_stats_empleados(resultados_chunks)
    logger.info(f"[LIBRO] ✅ Consolidación empleados: {stats}")
    return stats


@shared_task(queue='nomina_queue')
def consolidar_registros_task(resultados_chunks, usuario_id=None):
    """
    Callback: Consolida resultados de todos los chunks de registros.
    
    Esta tarea se ejecuta AL FINAL del chord, cuando todos los chunks
    de registros han sido procesados. Actualiza el estado del libro
    y registra el evento en el historial del usuario.
    
    Args:
        resultados_chunks: Lista de resultados de procesar_chunk_registros_task
        usuario_id: ID del usuario que inició el procesamiento (opcional)
    """
    stats = consolidar_stats_registros(resultados_chunks)
    logger.info(f"[LIBRO] ✅ Consolidación registros: {stats}")
    
    # Obtener libro_id del primer chunk result (todos tienen el mismo libro_id)
    # Los resultados vienen en formato: {'registros_procesados': X, 'libro_id': Y}
    libro_id = None
    total_registros = stats.get('total_registros_procesados', 0)
    
    # Buscar libro_id en los resultados
    for resultado in resultados_chunks:
        if isinstance(resultado, dict) and 'libro_id' in resultado:
            libro_id = resultado['libro_id']
            break
    
    # Si no encontramos libro_id en resultados, intentar desde stats
    if not libro_id and 'libro_id' in stats:
        libro_id = stats['libro_id']
    
    # Actualizar estado del libro y registrar log de usuario
    if libro_id:
        try:
            libro = LibroRemuneracionesUpload.objects.select_related(
                'cierre', 'cierre__cliente'
            ).get(id=libro_id)
            
            # Marcar libro como procesado (frontend espera "procesado", no "completado")
            libro.estado = "procesado"
            libro.save(update_fields=['estado'])
            logger.info(f"[LIBRO] Estado actualizado a 'procesado' para libro {libro_id}")
            
            # Obtener stats de empleados (deberían estar en el cierre)
            total_empleados = libro.cierre.empleados.count()
            
            # Obtener usuario: si se pasó usuario_id, usarlo; sino usar sistema
            if usuario_id:
                from api.models import Usuario
                try:
                    usuario = Usuario.objects.get(id=usuario_id)
                    logger.info(f"[LIBRO] Usando usuario real: {usuario.nombre} {usuario.apellido} (ID: {usuario_id})")
                except Usuario.DoesNotExist:
                    logger.warning(f"[LIBRO] Usuario ID {usuario_id} no encontrado, usando SISTEMA")
                    usuario = _get_sistema_user()
            else:
                logger.info(f"[LIBRO] No se recibió usuario_id, usando SISTEMA")
                usuario = _get_sistema_user()
            
            # ✅ LOGGING USUARIO: Procesamiento completado (para historial UI)
            registrar_actividad_tarjeta_nomina(
                cierre_id=libro.cierre.id,
                tarjeta="libro_remuneraciones",
                accion="process_complete",
                descripcion=f"Procesamiento completado: {total_empleados} empleados, {total_registros} registros",
                usuario=usuario,  # ← Ahora usa el usuario real
                detalles={
                    'empleados_procesados': total_empleados,
                    'registros_guardados': total_registros,
                    'estado_final': 'procesado',  # ← Actualizado para reflejar el estado real
                    'hora': timezone.now().strftime('%H:%M:%S')
                },
                resultado="exito"
            )
            logger.info(f"✅ TarjetaActivityLog registrado: process_complete para libro {libro_id} (usuario_id={usuario_id})")
            
        except LibroRemuneracionesUpload.DoesNotExist:
            logger.error(f"[LIBRO] No se encontró libro {libro_id} para actualizar estado")
        except Exception as e:
            logger.error(f"[LIBRO] Error actualizando estado/log para libro {libro_id}: {e}")
    
    return stats
