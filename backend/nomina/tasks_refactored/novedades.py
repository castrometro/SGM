# backend/nomina/tasks_refactored/novedades.py
"""
🚀 Módulo Refactorizado: Tareas de Procesamiento de Novedades
==============================================================

Extraído del monolítico tasks.py para mejorar mantenibilidad.

📊 WORKFLOW COMPLETO:
1. procesar_archivo_novedades → Punto de entrada, inicia chain
2. analizar_headers_archivo_novedades → Extrae headers del Excel
3. clasificar_headers_archivo_novedades_task → Clasifica headers automáticamente
4. (Usuario decide si procesar)
5. actualizar_empleados_desde_novedades_task/optimizado → Actualiza datos de empleados
6. guardar_registros_novedades_task/optimizado → Guarda registros

🔧 MODO OPTIMIZADO (archivos grandes >50 filas):
- Usa Celery Chord para procesamiento paralelo en chunks
- procesar_chunk_empleados_novedades_task → Procesa chunk de empleados
- procesar_chunk_registros_novedades_task → Procesa chunk de registros
- consolidar_empleados_novedades_task → Consolida resultados de empleados
- finalizar_procesamiento_novedades_task → Consolida y finaliza

✅ FEATURES:
- Dual logging (TarjetaActivityLogNomina + ActivityEvent)
- Propagación de usuario_id
- Procesamiento paralelo para archivos grandes
- Manejo robusto de errores

Autor: Sistema refactorizado
Versión: 1.0.0
Fecha: 18 de octubre de 2025
"""

import logging
from celery import shared_task, chain, chord
from django.utils import timezone

from ..models import ArchivoNovedadesUpload, ActivityEvent
from ..models_logging import registrar_actividad_tarjeta_nomina
from ..utils.NovedadesRemuneraciones import (
    obtener_headers_archivo_novedades,
    clasificar_headers_archivo_novedades,
    actualizar_empleados_desde_novedades,
    guardar_registros_novedades,
)
from ..utils.NovedadesOptimizado import (
    dividir_dataframe_novedades,
    obtener_archivo_novedades_path,
    procesar_chunk_empleados_novedades_util,
    procesar_chunk_registros_novedades_util,
    consolidar_stats_novedades,
    validar_chunk_data,
)

logger = logging.getLogger(__name__)


# ===== 🧮 FUNCIONES HELPER =====

def get_sistema_user():
    """Obtiene el primer usuario staff como usuario del sistema"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_staff=True).first() or User.objects.first()


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


# ===== 📤 FUNCIONES DE LOGGING DUAL =====

# ===== 🎨 MAPEO DE ACCIONES DESCRIPTIVAS A ACCION_CHOICES =====
# Mapeo de nuestras acciones descriptivas a las acciones válidas de TarjetaActivityLogNomina
ACCION_MAP = {
    # Análisis de headers
    'analisis_headers_iniciado': 'header_analysis',
    'analisis_headers_exitoso': 'header_analysis',
    'analisis_headers_error': 'validation_error',
    
    # Clasificación
    'clasificacion_headers_iniciada': 'classification_start',
    'clasificacion_headers_exitosa': 'classification_complete',
    'clasificacion_headers_error': 'validation_error',
    
    # Actualización de empleados
    'actualizacion_empleados_iniciada': 'process_start',
    'actualizacion_empleados_exitosa': 'process_complete',
    'actualizacion_empleados_error': 'validation_error',
    
    # Guardado de registros
    'guardado_registros_iniciado': 'process_start',
    'guardado_registros_exitoso': 'process_complete',
    'guardado_registros_error': 'validation_error',
    
    # Procesamiento inicial
    'upload_archivo_iniciado': 'upload_excel',
    'procesamiento_inicial_error': 'validation_error',
    
    # Procesamiento paralelo
    'procesamiento_paralelo_completo': 'process_complete',
    'procesamiento_paralelo_error': 'validation_error',
    
    # Operaciones optimizadas
    'actualizacion_empleados_optimizada_iniciada': 'process_start',
    'actualizacion_empleados_optimizada_exitosa': 'process_complete',
    'actualizacion_empleados_optimizada_error': 'validation_error',
    'guardado_registros_optimizado_iniciado': 'process_start',
    'guardado_registros_optimizado_exitoso': 'process_complete',
    'guardado_registros_optimizado_error': 'validation_error',
}


def get_tarjeta_accion(accion_descriptiva):
    """
    Convierte una acción descriptiva a una acción válida de ACCION_CHOICES.
    Si no hay mapeo, usa 'process_start' o 'process_complete' según el sufijo.
    """
    if accion_descriptiva in ACCION_MAP:
        return ACCION_MAP[accion_descriptiva]
    
    # Fallback basado en sufijos
    if 'iniciado' in accion_descriptiva or 'iniciada' in accion_descriptiva:
        return 'process_start'
    elif 'exitoso' in accion_descriptiva or 'exitosa' in accion_descriptiva:
        return 'process_complete'
    elif 'error' in accion_descriptiva:
        return 'validation_error'
    else:
        return 'process_start'


# ===== 📊 FUNCIONES DE LOGGING DUAL =====

def log_process_start_novedades(archivo_id, accion, descripcion, usuario_id=None, detalles_extra=None):
    """
    Registra el inicio de una fase del procesamiento de novedades en ambos sistemas de logging
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        accion: Acción descriptiva (ej: 'analisis_headers_iniciado', 'clasificacion_headers_iniciada')
        descripcion: Descripción legible del proceso
        usuario_id: ID del usuario que inició la operación
        detalles_extra: Detalles adicionales opcionales
    """
    try:
        archivo = ArchivoNovedadesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=archivo_id)
        cierre = archivo.cierre
        cliente = cierre.cliente
        
        # Obtener usuario con fallback inteligente
        if usuario_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                logger.warning(f"Usuario ID {usuario_id} no encontrado, usando sistema")
                usuario = get_sistema_user()
        else:
            usuario = get_sistema_user()
        
        # Preparar detalles base
        detalles = {
            'archivo_id': archivo_id,
            'archivo_nombre': archivo.archivo.name if archivo.archivo else 'N/A',
            'estado_inicial': archivo.estado,
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ Logging en TarjetaActivityLogNomina (usuario-visible con acción del CHOICES)
        accion_tarjeta = get_tarjeta_accion(accion)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta='novedades',
            accion=accion_tarjeta,  # ✅ Usar acción válida del CHOICES
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles,
            resultado='info'
        )
        
        # 2️⃣ Logging en ActivityEvent (audit trail con acción descriptiva completa)
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action=accion,  # ✅ Usar acción descriptiva personalizada
            resource_type='archivo_novedades',
            resource_id=str(archivo_id),
            details=detalles
        )
        
        logger.info(f"✅ Log dual iniciado: novedades {archivo_id} - {accion}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_process_start_novedades para archivo {archivo_id}: {e}")


def log_process_complete_novedades(archivo_id, accion, descripcion, usuario_id=None, resultado='exito', detalles_extra=None):
    """
    Registra la finalización de una fase del procesamiento de novedades
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        accion: Acción descriptiva (ej: 'analisis_headers_exitoso', 'clasificacion_headers_exitosa')
        descripcion: Descripción legible del resultado
        usuario_id: ID del usuario
        resultado: 'exito', 'warning', o 'error'
        detalles_extra: Detalles adicionales
    """
    try:
        archivo = ArchivoNovedadesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=archivo_id)
        cierre = archivo.cierre
        cliente = cierre.cliente
        
        # Obtener usuario con fallback
        if usuario_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                usuario = get_sistema_user()
        else:
            usuario = get_sistema_user()
        
        # Preparar detalles
        detalles = {
            'archivo_id': archivo_id,
            'estado_final': archivo.estado,
            'timestamp_completado': timezone.now().isoformat(),
        }
        if detalles_extra:
            detalles.update(detalles_extra)
        
        # 1️⃣ TarjetaActivityLogNomina (acción del CHOICES)
        accion_tarjeta = get_tarjeta_accion(accion)
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta='novedades',
            accion=accion_tarjeta,  # ✅ Usar acción válida del CHOICES
            descripcion=descripcion,
            usuario=usuario,
            detalles=detalles,
            resultado=resultado
        )
        
        # 2️⃣ ActivityEvent (acción descriptiva completa)
        ActivityEvent.log(
            user=usuario,
            cliente=cliente,
            cierre=cierre,
            event_type='process',
            action=accion,  # ✅ Usar acción descriptiva personalizada
            resource_type='archivo_novedades',
            resource_id=str(archivo_id),
            details=detalles
        )
        
        logger.info(f"✅ Log dual completado: novedades {archivo_id} - {accion} - {resultado}")
        
    except Exception as e:
        logger.error(f"❌ Error en log_process_complete_novedades para archivo {archivo_id}: {e}")


# ===== 🎯 TAREAS PRINCIPALES =====

def procesar_archivo_novedades_con_logging(archivo_id, usuario_id=None):
    """
    Procesa un archivo de novedades - solo hasta clasificación inicial
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        usuario_id: ID del usuario que inició el procesamiento
        
    Returns:
        dict: Estado del procesamiento
    """
    logger.info(f"📤 Iniciando procesamiento novedades id={archivo_id}, usuario_id={usuario_id}")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # ✅ Logging dual de inicio con acción descriptiva
        log_process_start_novedades(
            archivo_id=archivo_id,
            accion='upload_archivo_iniciado',
            descripcion='Archivo de novedades recibido, iniciando análisis y clasificación',
            usuario_id=usuario_id,
            detalles_extra={'workflow': 'chain_analisis_clasificacion'}
        )
        
        # ✅ Ejecutar chain: análisis → clasificación
        workflow = chain(
            analizar_headers_archivo_novedades.s(archivo_id, usuario_id),
            clasificar_headers_archivo_novedades_task.s(usuario_id)
        )
        
        # Ejecutar cadena
        workflow.apply_async()
        
        logger.info(f"🚀 Chain análisis+clasificación iniciado para novedades id={archivo_id}")
        return {"archivo_id": archivo_id, "estado": "cadena_iniciada"}
        
    except Exception as e:
        # Marcar archivo como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = 'con_error'
            archivo.save()
            
            # Log de error
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='procesamiento_inicial_error',
                descripcion=f'Error en procesamiento inicial: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={'error': str(e)}
            )
        except Exception as ex:
            logger.error(f"❌ Error guardando estado error para novedades id={archivo_id}: {ex}")
        
        logger.error(f"❌ Error iniciando procesamiento novedades id={archivo_id}: {e}")
        raise


@shared_task(bind=True, queue='nomina_queue')
def analizar_headers_archivo_novedades(self, archivo_id, usuario_id=None):
    """
    Analiza headers de un archivo de novedades
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        usuario_id: ID del usuario
        
    Returns:
        dict: {"archivo_id": int, "headers": list, "usuario_id": int}
    """
    logger.info(f"🔍 Analizando headers novedades id={archivo_id}")
    
    # ✅ Logging de inicio con acción descriptiva
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='analisis_headers_iniciado',
        descripcion='Iniciando análisis de headers del archivo Excel',
        usuario_id=usuario_id
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        archivo.estado = "analizando_hdrs"
        archivo.save()

        # Extraer headers del Excel
        headers = obtener_headers_archivo_novedades(archivo.archivo.path)
        
        # Guardar headers en el modelo
        archivo.header_json = headers
        archivo.estado = "hdrs_analizados"
        archivo.save()
        
        # ✅ Logging de completado con acción descriptiva
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='analisis_headers_exitoso',
            descripcion=f'Headers analizados exitosamente: {len(headers)} columnas detectadas',
            usuario_id=usuario_id,
            resultado='exito',
            detalles_extra={'headers_detectados': len(headers)}
        )
        
        logger.info(f"✅ Headers analizados: novedades id={archivo_id}, {len(headers)} headers")
        
        # Retornar con usuario_id para siguiente tarea
        return {
            "archivo_id": archivo_id,
            "headers": headers,
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        archivo.estado = "con_error"
        archivo.save()
        
        # Log de error con acción descriptiva
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='analisis_headers_error',
            descripcion=f'Error al analizar headers: {str(e)}',
            usuario_id=usuario_id,
            resultado='error',
            detalles_extra={'error': str(e)}
        )
        
        logger.error(f"❌ Error analizando headers novedades id={archivo_id}: {e}")
        raise


@shared_task(bind=True, queue='nomina_queue')
def clasificar_headers_archivo_novedades_task(self, result, usuario_id=None):
    """
    Clasifica headers de un archivo de novedades
    
    Args:
        result: Resultado de la tarea anterior (dict con archivo_id, headers)
        usuario_id: ID del usuario (viene del result o parámetro)
        
    Returns:
        dict: Estadísticas de clasificación
    """
    archivo_id = result["archivo_id"]
    # Propagar usuario_id
    if not usuario_id:
        usuario_id = result.get("usuario_id")
    
    logger.info(f"🏷️ Clasificando headers novedades id={archivo_id}")
    
    # ✅ Logging de inicio con acción descriptiva
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='clasificacion_headers_iniciada',
        descripcion='Iniciando clasificación automática de headers',
        usuario_id=usuario_id
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.select_related('cierre', 'cierre__cliente').get(id=archivo_id)
        cierre = archivo.cierre
        cliente = cierre.cliente

        # Marcar en proceso
        archivo.estado = "clasif_en_proceso"
        archivo.save()

        # Obtener headers
        headers = (
            archivo.header_json
            if isinstance(archivo.header_json, list)
            else result["headers"]
        )

        # Clasificar headers automáticamente
        headers_clasificados, headers_sin_clasificar = clasificar_headers_archivo_novedades(headers, cliente)

        # Guardar resultado en JSON
        archivo.header_json = {
            "headers_clasificados": headers_clasificados,
            "headers_sin_clasificar": headers_sin_clasificar,
        }

        # Determinar estado final
        if headers_sin_clasificar:
            archivo.estado = "clasif_pendiente"
            resultado_log = 'warning'
            descripcion_log = f'Clasificación completada con {len(headers_sin_clasificar)} headers pendientes de mapeo manual'
        else:
            archivo.estado = "clasificado"
            resultado_log = 'exito'
            descripcion_log = f'Clasificación completada: {len(headers_clasificados)} de {len(headers)} columnas identificadas'
            logger.info(f"✅ Novedades {archivo_id}: Todos los headers clasificados automáticamente")

        archivo.save()
        
        # ✅ Logging de completado con acción descriptiva
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='clasificacion_headers_exitosa',
            descripcion=descripcion_log,
            usuario_id=usuario_id,
            resultado=resultado_log,
            detalles_extra={
                'headers_total': len(headers),
                'headers_clasificados': len(headers_clasificados),
                'headers_sin_clasificar': len(headers_sin_clasificar),
                'estado_final': archivo.estado
            }
        )
        
        logger.info(
            f"✅ Novedades {archivo_id}: {len(headers_clasificados)} clasificados, "
            f"{len(headers_sin_clasificar)} sin clasificar"
        )
        
        return {
            "archivo_id": archivo_id,
            "headers_clasificados": len(headers_clasificados),
            "headers_sin_clasificar": len(headers_sin_clasificar),
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error clasificando headers novedades id={archivo_id}: {e}")
        
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
            
            # Log de error con acción descriptiva
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='clasificacion_headers_error',
                descripcion=f'Error en clasificación de headers: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={'error': str(e)}
            )
        except Exception as ex:
            logger.error(f"❌ Error guardando estado error novedades id={archivo_id}: {ex}")
        
        raise


# ===== 👥 TAREAS DE PROCESAMIENTO FINAL =====

@shared_task(bind=True, queue='nomina_queue')
def actualizar_empleados_desde_novedades_task(self, result, usuario_id=None):
    """
    Task para actualizar empleados desde archivo de novedades
    
    Args:
        result: Resultado anterior (dict con archivo_id)
        usuario_id: ID del usuario
        
    Returns:
        dict: Estadísticas de actualización
    """
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    if not usuario_id:
        usuario_id = result.get("usuario_id") if isinstance(result, dict) else None
    
    logger.info(f"👥 Actualizando empleados desde novedades id={archivo_id}")
    
    # ✅ Logging de inicio con acción descriptiva
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='actualizacion_empleados_iniciada',
        descripcion='Iniciando actualización de datos de empleados desde novedades',
        usuario_id=usuario_id
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        count = actualizar_empleados_desde_novedades(archivo)
        
        # ✅ Logging de completado con acción descriptiva
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='actualizacion_empleados_exitosa',
            descripcion=f'Actualización de empleados completada: {count} empleados actualizados',
            usuario_id=usuario_id,
            resultado='exito',
            detalles_extra={'empleados_actualizados': count}
        )
        
        logger.info(f"✅ Actualizados {count} empleados desde novedades {archivo_id}")
        
        return {
            "archivo_id": archivo_id,
            "empleados_actualizados": count,
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        # Log de error
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='actualizacion_empleados_error',
            descripcion=f'Error al actualizar empleados: {str(e)}',
            usuario_id=usuario_id,
            resultado='error',
            detalles_extra={'error': str(e)}
        )
        
        logger.error(f"❌ Error actualizando empleados novedades id={archivo_id}: {e}")
        raise


@shared_task(bind=True, queue='nomina_queue')
def guardar_registros_novedades_task(self, result, usuario_id=None):
    """
    Task para guardar registros de novedades
    
    Args:
        result: Resultado anterior
        usuario_id: ID del usuario
        
    Returns:
        dict: Estadísticas de guardado
    """
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    if not usuario_id:
        usuario_id = result.get("usuario_id") if isinstance(result, dict) else None
    
    logger.info(f"💾 Guardando registros novedades id={archivo_id}")
    
    # ✅ Logging de inicio con acción descriptiva
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='guardado_registros_iniciado',
        descripcion='Iniciando guardado de registros de novedades en la base de datos',
        usuario_id=usuario_id
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        count = guardar_registros_novedades(archivo)
        
        # ✅ Actualizar estado final
        archivo.estado = "procesado"
        archivo.save()
        
        # ✅ Logging de completado con acción descriptiva
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='guardado_registros_exitoso',
            descripcion=f'Procesamiento completado: {count} registros guardados exitosamente',
            usuario_id=usuario_id,
            resultado='exito',
            detalles_extra={
                'registros_guardados': count,
                'estado_final': 'procesado'
            }
        )
        
        logger.info(f"✅ Guardados {count} registros novedades {archivo_id}")
        
        return {
            "archivo_id": archivo_id,
            "registros_guardados": count,
            "estado": "procesado",
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        # Marcar como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
            
            # Log de error
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='guardado_registros_error',
                descripcion=f'Error al guardar registros: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={'error': str(e)}
            )
        except:
            pass
        
        logger.error(f"❌ Error guardando registros novedades id={archivo_id}: {e}")
        raise


# ===== 🚀 TAREAS OPTIMIZADAS CON CELERY CHORD =====

@shared_task(bind=True, queue='nomina_queue')
def procesar_chunk_empleados_novedades_task(self, archivo_id, chunk_data):
    """
    👥 Task para procesar un chunk específico de empleados de novedades en paralelo
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        dict: Estadísticas del procesamiento del chunk
    """
    logger.info(f"🔄 Procesando chunk empleados novedades {chunk_data.get('chunk_id')}")
    
    # Validar datos del chunk
    if not validar_chunk_data(chunk_data):
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'empleados_actualizados': 0,
            'errores': ['Datos del chunk inválidos'],
            'archivo_id': archivo_id,
            'success': False
        }
    
    try:
        resultado = procesar_chunk_empleados_novedades_util(archivo_id, chunk_data)
        logger.info(f"✅ Chunk empleados novedades {chunk_data.get('chunk_id')} completado")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en chunk empleados novedades {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'empleados_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': 0,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


@shared_task(bind=True, queue='nomina_queue')
def procesar_chunk_registros_novedades_task(self, archivo_id, chunk_data):
    """
    📝 Task para procesar un chunk específico de registros de novedades en paralelo
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        dict: Estadísticas del procesamiento del chunk
    """
    logger.info(f"💾 Procesando chunk registros novedades {chunk_data.get('chunk_id')}")
    
    # Validar datos
    if not validar_chunk_data(chunk_data):
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'registros_creados': 0,
            'registros_actualizados': 0,
            'errores': ['Datos del chunk inválidos'],
            'archivo_id': archivo_id,
            'success': False
        }
    
    try:
        resultado = procesar_chunk_registros_novedades_util(archivo_id, chunk_data)
        logger.info(f"✅ Chunk registros novedades {chunk_data.get('chunk_id')} completado")
        return resultado
        
    except Exception as e:
        error_msg = f"Error en chunk registros novedades {chunk_data.get('chunk_id')}: {str(e)}"
        logger.error(error_msg)
        return {
            'chunk_id': chunk_data.get('chunk_id', 0),
            'registros_creados': 0,
            'registros_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': 0,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


@shared_task(bind=True, queue='nomina_queue')
def consolidar_empleados_novedades_task(self, resultados_chunks):
    """
    📊 Consolida los resultados de múltiples chunks de empleados de novedades
    
    Args:
        resultados_chunks: Lista de resultados de chunks de empleados
        
    Returns:
        dict: Estadísticas consolidadas
    """
    logger.info(f"📊 Consolidando {len(resultados_chunks)} chunks de empleados novedades")
    
    try:
        consolidado = consolidar_stats_novedades(resultados_chunks, 'empleados')
        
        # Obtener archivo_id
        archivo_id = resultados_chunks[0].get('archivo_id') if resultados_chunks else None
        
        # Agregar info para siguiente fase
        consolidado.update({
            'fase': 'empleados_completada',
            'archivo_id': archivo_id,
            'listo_para_registros': True
        })
        
        logger.info(f"✅ Consolidación empleados completada: {consolidado.get('empleados_actualizados', 0)} empleados")
        
        return consolidado
        
    except Exception as e:
        logger.error(f"❌ Error consolidando empleados novedades: {e}")
        return {
            'fase': 'empleados_error',
            'archivo_id': resultados_chunks[0].get('archivo_id') if resultados_chunks else None,
            'errores': [str(e)],
            'success': False
        }


@shared_task(bind=True, queue='nomina_queue')
def finalizar_procesamiento_novedades_task(self, resultados_chunks, usuario_id=None):
    """
    🎯 Finaliza el procesamiento de novedades y actualiza el estado del archivo
    
    Args:
        resultados_chunks: Lista de resultados de chunks de registros
        usuario_id: ID del usuario
        
    Returns:
        dict: Resultado final del procesamiento
    """
    logger.info(f"🎯 Finalizando procesamiento novedades con {len(resultados_chunks)} chunks")
    
    try:
        # Consolidar estadísticas de registros
        consolidado = consolidar_stats_novedades(resultados_chunks, 'registros')
        archivo_id = consolidado.get('archivo_id') or (resultados_chunks[0].get('archivo_id') if resultados_chunks else None)
        
        if not archivo_id:
            raise ValueError("No se pudo obtener archivo_id de los resultados")
        
        # Obtener archivo
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Determinar estado final basado en errores
        errores_totales = consolidado.get('errores_totales', 0)
        registros_creados = consolidado.get('registros_creados', 0)
        registros_actualizados = consolidado.get('registros_actualizados', 0)
        
        if errores_totales > 0 and (registros_creados > 0 or registros_actualizados > 0):
            estado_final = "con_errores_parciales"
            resultado_log = "warning"
        elif errores_totales > 0:
            estado_final = "con_error"
            resultado_log = "error"
        else:
            estado_final = "procesado"
            resultado_log = "exito"
        
        # Actualizar estado
        archivo.estado = estado_final
        archivo.save()
        
        # ✅ Logging dual de finalización
        log_process_complete_novedades(
            archivo_id=archivo_id,
            accion='procesamiento_paralelo_completo',
            descripcion=f'Procesamiento paralelo completado: {registros_creados} registros creados, {registros_actualizados} actualizados',
            usuario_id=usuario_id,
            resultado=resultado_log,
            detalles_extra={
                'registros_creados': registros_creados,
                'registros_actualizados': registros_actualizados,
                'errores_totales': errores_totales,
                'estado_final': estado_final,
                'modo': 'chord_paralelo'
            }
        )
        
        resultado_final = {
            'archivo_id': archivo_id,
            'estado_final': estado_final,
            'estadisticas_consolidadas': consolidado,
            'timestamp_finalizacion': timezone.now().isoformat(),
            'success': True
        }
        
        logger.info(f"🎯 Novedades finalizado - Estado: {estado_final}, Registros: {registros_creados}+{registros_actualizados}")
        
        return resultado_final
        
    except Exception as e:
        logger.error(f"❌ Error finalizando novedades: {e}")
        
        # Marcar como error
        try:
            if 'archivo_id' in locals():
                archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
                archivo.estado = "con_error"
                archivo.save()
                
                # Log de error
                log_process_complete_novedades(
                    archivo_id=archivo_id,
                    accion='procesamiento_paralelo_error',
                    descripcion=f'Error en procesamiento paralelo: {str(e)}',
                    usuario_id=usuario_id,
                    resultado='error',
                    detalles_extra={'error': str(e)}
                )
        except:
            pass
        
        return {
            'archivo_id': archivo_id if 'archivo_id' in locals() else None,
            'estado_final': 'con_error',
            'errores': [str(e)],
            'success': False
        }


# ===== 🚀 TAREAS OPTIMIZADAS (VERSIONES OPTIMIZADAS) =====

@shared_task(bind=True, queue='nomina_queue')
def actualizar_empleados_desde_novedades_task_optimizado(self, result, usuario_id=None):
    """
    🚀 Versión optimizada que usa Celery Chord para procesar empleados en chunks paralelos
    
    Args:
        result: Resultado de la task anterior (contiene archivo_id)
        usuario_id: ID del usuario
        
    Returns:
        dict: Información del procesamiento o referencia al chord
    """
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    if not usuario_id:
        usuario_id = result.get("usuario_id") if isinstance(result, dict) else None
    
    logger.info(f"🚀 Iniciando actualización optimizada empleados novedades {archivo_id}")
    
    # ✅ Logging de inicio
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='actualizacion_empleados_optimizada_iniciada',
        descripcion='Iniciando actualización optimizada de empleados con chord paralelo',
        usuario_id=usuario_id,
        detalles_extra={'modo': 'chord_paralelo'}
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Obtener ruta del archivo
        ruta_archivo = obtener_archivo_novedades_path(archivo_id)
        if not ruta_archivo:
            raise ValueError(f"No se pudo obtener ruta del archivo {archivo_id}")
        
        # Leer archivo para calcular chunk size
        import pandas as pd
        df = pd.read_excel(ruta_archivo, engine="openpyxl")
        total_filas = len(df)
        
        # Calcular chunk size dinámico
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"📊 Total filas novedades: {total_filas}, Chunk size: {chunk_size}")
        
        # Para archivos pequeños, procesamiento directo
        if total_filas <= 50:
            logger.info(f"📝 Archivo pequeño ({total_filas} filas), procesamiento directo")
            count = actualizar_empleados_desde_novedades(archivo)
            
            # Log de completado
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='actualizacion_empleados_optimizada_exitosa',
                descripcion=f'Actualización directa completada: {count} empleados actualizados ({total_filas} filas)',
                usuario_id=usuario_id,
                resultado='exito',
                detalles_extra={
                    'empleados_actualizados': count,
                    'modo': 'directo',
                    'filas': total_filas
                }
            )
            
            return {
                "archivo_id": archivo_id,
                "empleados_actualizados": count,
                "modo": "directo",
                "timestamp": timezone.now().isoformat(),
                "usuario_id": usuario_id
            }
        
        # Dividir en chunks para procesamiento paralelo
        chunks = dividir_dataframe_novedades(ruta_archivo, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se crearon chunks para archivo {archivo_id}")
            raise ValueError("No se pudieron crear chunks")
        
        logger.info(f"📦 Creados {len(chunks)} chunks para procesamiento paralelo")
        
        # Crear tasks paralelas usando chord
        tasks_paralelas = [
            procesar_chunk_empleados_novedades_task.s(archivo_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord: tasks paralelas | callback
        callback = consolidar_empleados_novedades_task.s()
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"🚀 Chord empleados iniciado: {len(chunks)} chunks en paralelo")
        
        return {
            "archivo_id": archivo_id,
            "chord_id": str(resultado_chord),
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord_empleados",
            "timestamp": timezone.now().isoformat(),
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error en empleados optimizado archivo {archivo_id}: {e}")
        
        # Marcar como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
            
            # Log de error
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='actualizacion_empleados_optimizada_error',
                descripcion=f'Error en actualización optimizada: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={'error': str(e)}
            )
        except:
            pass
        
        raise


@shared_task(bind=True, queue='nomina_queue')
def guardar_registros_novedades_task_optimizado(self, result, usuario_id=None):
    """
    🚀 Versión optimizada que usa Celery Chord para guardar registros en chunks paralelos
    
    Args:
        result: Resultado de la task anterior
        usuario_id: ID del usuario
        
    Returns:
        dict: Información del procesamiento o referencia al chord
    """
    archivo_id = result.get("archivo_id") if isinstance(result, dict) else result
    if not usuario_id:
        usuario_id = result.get("usuario_id") if isinstance(result, dict) else None
    
    logger.info(f"🚀 Iniciando guardado optimizado registros novedades {archivo_id}")
    
    # ✅ Logging de inicio
    log_process_start_novedades(
        archivo_id=archivo_id,
        accion='guardado_registros_optimizado_iniciado',
        descripcion='Iniciando guardado optimizado de registros con chord paralelo',
        usuario_id=usuario_id,
        detalles_extra={'modo': 'chord_paralelo'}
    )
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        
        # Verificar estado
        if archivo.estado not in ['clasificado', 'empleados_actualizados']:
            logger.warning(f"⚠️ Archivo en estado {archivo.estado}, continuando")
        
        # Obtener ruta
        ruta_archivo = obtener_archivo_novedades_path(archivo_id)
        if not ruta_archivo:
            raise ValueError(f"No se pudo obtener ruta del archivo {archivo_id}")
        
        # Leer archivo
        import pandas as pd
        df = pd.read_excel(ruta_archivo, engine="openpyxl")
        total_filas = len(df)
        
        # Calcular chunk size
        chunk_size = calcular_chunk_size_dinamico(total_filas)
        
        logger.info(f"💾 Guardado en chunks: {total_filas} filas, chunk size: {chunk_size}")
        
        # Archivos pequeños: procesamiento directo
        if total_filas <= 50:
            logger.info(f"📝 Archivo pequeño ({total_filas} filas), guardado directo")
            count = guardar_registros_novedades(archivo)
            
            # Actualizar estado final
            archivo.estado = "procesado"
            archivo.save()
            
            # Log de completado
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='guardado_registros_optimizado_exitoso',
                descripcion=f'Guardado directo completado: {count} registros guardados ({total_filas} filas)',
                usuario_id=usuario_id,
                resultado='exito',
                detalles_extra={
                    'registros_guardados': count,
                    'estado_final': 'procesado',
                    'modo': 'directo',
                    'filas': total_filas
                }
            )
            
            return {
                "archivo_id": archivo_id,
                "registros_guardados": count,
                "estado_final": "procesado",
                "modo": "directo",
                "timestamp": timezone.now().isoformat(),
                "usuario_id": usuario_id
            }
        
        # Dividir en chunks
        chunks = dividir_dataframe_novedades(ruta_archivo, chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️ No se crearon chunks para registros archivo {archivo_id}")
            raise ValueError("No se pudieron crear chunks para registros")
        
        logger.info(f"📦 Creados {len(chunks)} chunks para guardado paralelo")
        
        # Crear tasks paralelas para registros
        tasks_paralelas = [
            procesar_chunk_registros_novedades_task.s(archivo_id, chunk_data) 
            for chunk_data in chunks
        ]
        
        # Ejecutar chord para registros - pasar usuario_id al callback
        callback = finalizar_procesamiento_novedades_task.s(usuario_id=usuario_id)
        resultado_chord = chord(tasks_paralelas)(callback)
        
        logger.info(f"🚀 Chord registros iniciado: {len(chunks)} chunks en paralelo")
        
        return {
            "archivo_id": archivo_id,
            "chord_id": str(resultado_chord),
            "chunks_totales": len(chunks),
            "modo": "optimizado_chord_registros",
            "timestamp": timezone.now().isoformat(),
            "usuario_id": usuario_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error en registros optimizado archivo {archivo_id}: {e}")
        
        # Marcar como error
        try:
            archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
            archivo.estado = "con_error"
            archivo.save()
            
            # Log de error
            log_process_complete_novedades(
                archivo_id=archivo_id,
                accion='guardado_registros_optimizado_error',
                descripcion=f'Error en guardado optimizado: {str(e)}',
                usuario_id=usuario_id,
                resultado='error',
                detalles_extra={'error': str(e)}
            )
        except:
            pass
        
        raise
