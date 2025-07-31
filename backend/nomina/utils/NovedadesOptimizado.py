"""
🚀 UTILIDADES OPTIMIZADAS PARA NOVEDADES CON CELERY CHORD

Implementa procesamiento paralelo por chunks para archivos de novedades,
siguiendo el patrón exitoso de LibroRemuneraciones.

Funciones principales:
- dividir_dataframe_novedades: Divide el archivo en chunks para procesamiento paralelo
- procesar_chunk_empleados_novedades_util: Procesa empleados de un chunk específico
- procesar_chunk_registros_novedades_util: Procesa registros de un chunk específico
- consolidar_stats_novedades: Consolida estadísticas de múltiples chunks
"""

import pandas as pd
import logging
from django.utils import timezone
from django.db import transaction
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def dividir_dataframe_novedades(ruta_archivo, chunk_size):
    """
    📊 Divide el archivo de novedades en chunks para procesamiento paralelo
    
    Args:
        ruta_archivo: Ruta al archivo Excel de novedades
        chunk_size: Tamaño de cada chunk
        
    Returns:
        List[Dict]: Lista de chunks con metadatos
    """
    try:
        logger.info(f"📂 Dividiendo archivo novedades en chunks: {ruta_archivo}")
        
        # Leer el archivo completo
        df = pd.read_excel(ruta_archivo, engine="openpyxl")
        total_filas = len(df)
        
        if total_filas == 0:
            logger.warning("⚠️ Archivo vacío, no se pueden crear chunks")
            return []
        
        logger.info(f"📊 Total filas: {total_filas}, Chunk size: {chunk_size}")
        
        chunks = []
        for i in range(0, total_filas, chunk_size):
            chunk_end = min(i + chunk_size, total_filas)
            chunk_df = df.iloc[i:chunk_end]
            
            chunk_data = {
                'chunk_id': len(chunks),
                'inicio_fila': i,
                'fin_fila': chunk_end,
                'total_filas': chunk_end - i,
                'datos': chunk_df.to_dict('records'),  # Convertir a dict para serialización
                'headers': list(df.columns),
                'timestamp_creacion': timezone.now().isoformat()
            }
            
            chunks.append(chunk_data)
            logger.info(f"✅ Chunk {len(chunks)} creado: filas {i}-{chunk_end} ({chunk_end - i} registros)")
        
        logger.info(f"🎯 División completada: {len(chunks)} chunks creados")
        return chunks
        
    except Exception as e:
        logger.error(f"❌ Error dividiendo archivo novedades: {e}")
        return []


def procesar_chunk_empleados_novedades_util(archivo_id, chunk_data):
    """
    👥 Procesa un chunk específico de empleados de novedades
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento
    """
    from ..models import ArchivoNovedadesUpload, EmpleadoCierre
    
    chunk_id = chunk_data.get('chunk_id', 0)
    inicio_tiempo = timezone.now()
    
    logger.info(f"👥 Procesando chunk empleados {chunk_id}: {chunk_data.get('total_filas', 0)} registros")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        cierre = archivo.cierre
        
        empleados_actualizados = 0
        errores = []
        
        # Procesar cada registro del chunk
        for i, row_data in enumerate(chunk_data.get('datos', [])):
            try:
                # Obtener RUT del empleado
                rut = str(row_data.get("Rut del Trabajador", "")).strip()
                if not rut or rut == 'nan':
                    continue
                
                # Buscar el empleado en el cierre
                try:
                    empleado = EmpleadoCierre.objects.get(cierre=cierre, rut=rut)
                except EmpleadoCierre.DoesNotExist:
                    logger.warning(f"⚠️ Empleado con RUT {rut} no encontrado en cierre")
                    continue
                
                # Actualizar datos del empleado con información de novedades
                actualizado = False
                
                # Actualizar nombre si está disponible
                if 'Nombre' in row_data and row_data['Nombre']:
                    nuevo_nombre = str(row_data['Nombre']).strip()
                    if nuevo_nombre != empleado.nombre:
                        empleado.nombre = nuevo_nombre
                        actualizado = True
                
                # Actualizar apellidos si están disponibles
                if 'Apellido Paterno' in row_data and row_data['Apellido Paterno']:
                    nuevo_apellido = str(row_data['Apellido Paterno']).strip()
                    if nuevo_apellido != empleado.apellido_paterno:
                        empleado.apellido_paterno = nuevo_apellido
                        actualizado = True
                
                if 'Apellido Materno' in row_data and row_data['Apellido Materno']:
                    nuevo_apellido_m = str(row_data['Apellido Materno']).strip()
                    if nuevo_apellido_m != empleado.apellido_materno:
                        empleado.apellido_materno = nuevo_apellido_m
                        actualizado = True
                
                # Actualizar sueldo base si está disponible
                if 'Sueldo Base' in row_data and row_data['Sueldo Base']:
                    try:
                        nuevo_sueldo = Decimal(str(row_data['Sueldo Base']).replace('$', '').replace(',', ''))
                        if empleado.sueldo_base != nuevo_sueldo:
                            empleado.sueldo_base = nuevo_sueldo
                            actualizado = True
                    except (ValueError, InvalidOperation):
                        logger.warning(f"⚠️ Sueldo base inválido para RUT {rut}: {row_data['Sueldo Base']}")
                
                # Guardar cambios si hubo actualizaciones
                if actualizado:
                    empleado.save()
                    empleados_actualizados += 1
                    
            except Exception as e:
                error_msg = f"Error procesando fila {i} del chunk {chunk_id}: {str(e)}"
                logger.error(error_msg)
                errores.append(error_msg)
        
        tiempo_procesamiento = (timezone.now() - inicio_tiempo).total_seconds()
        
        resultado = {
            'chunk_id': chunk_id,
            'empleados_actualizados': empleados_actualizados,
            'errores': errores,
            'tiempo_procesamiento': tiempo_procesamiento,
            'registros_procesados': chunk_data.get('total_filas', 0),
            'archivo_id': archivo_id,
            'success': True
        }
        
        logger.info(f"✅ Chunk empleados {chunk_id} completado: {empleados_actualizados} empleados actualizados en {tiempo_procesamiento:.2f}s")
        return resultado
        
    except Exception as e:
        tiempo_procesamiento = (timezone.now() - inicio_tiempo).total_seconds()
        error_msg = f"Error crítico en chunk empleados {chunk_id}: {str(e)}"
        logger.error(error_msg)
        
        return {
            'chunk_id': chunk_id,
            'empleados_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': tiempo_procesamiento,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


def procesar_chunk_registros_novedades_util(archivo_id, chunk_data):
    """
    📝 Procesa un chunk específico de registros de novedades
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        chunk_data: Datos del chunk a procesar
        
    Returns:
        Dict: Estadísticas del procesamiento
    """
    from ..models import ArchivoNovedadesUpload, EmpleadoCierre, ConceptoRemuneracion, RegistroConceptoEmpleado
    
    chunk_id = chunk_data.get('chunk_id', 0)
    inicio_tiempo = timezone.now()
    
    logger.info(f"📝 Procesando chunk registros {chunk_id}: {chunk_data.get('total_filas', 0)} registros")
    
    try:
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        cierre = archivo.cierre
        cliente = cierre.cliente
        
        # Obtener headers clasificados
        headers_clasificados = archivo.header_json.get('headers_clasificados', {})
        
        registros_creados = 0
        registros_actualizados = 0
        errores = []
        
        # Usar transacción para el chunk completo
        with transaction.atomic():
            # Procesar cada registro del chunk
            for i, row_data in enumerate(chunk_data.get('datos', [])):
                try:
                    # Obtener RUT del empleado
                    rut = str(row_data.get("Rut del Trabajador", "")).strip()
                    if not rut or rut == 'nan':
                        continue
                    
                    # Buscar el empleado
                    try:
                        empleado = EmpleadoCierre.objects.get(cierre=cierre, rut=rut)
                    except EmpleadoCierre.DoesNotExist:
                        continue
                    
                    # Procesar cada header clasificado
                    for header_original, concepto_nombre in headers_clasificados.items():
                        if header_original in row_data:
                            valor = row_data[header_original]
                            
                            # Saltar valores vacíos
                            if pd.isna(valor) or str(valor).strip() == '':
                                continue
                            
                            try:
                                # Buscar el concepto de remuneración
                                concepto = ConceptoRemuneracion.objects.filter(
                                    cliente=cliente,
                                    nombre_concepto=concepto_nombre,
                                    vigente=True
                                ).first()
                                
                                # Crear o actualizar registro
                                registro, created = RegistroConceptoEmpleado.objects.update_or_create(
                                    empleado=empleado,
                                    nombre_concepto_original=header_original,
                                    defaults={
                                        "monto": str(valor),
                                        "concepto": concepto,
                                        "fuente_archivo": "novedades"
                                    }
                                )
                                
                                if created:
                                    registros_creados += 1
                                else:
                                    registros_actualizados += 1
                                    
                            except Exception as e:
                                error_msg = f"Error creando registro para {header_original}: {str(e)}"
                                errores.append(error_msg)
                                
                except Exception as e:
                    error_msg = f"Error procesando fila {i} del chunk {chunk_id}: {str(e)}"
                    logger.error(error_msg)
                    errores.append(error_msg)
        
        tiempo_procesamiento = (timezone.now() - inicio_tiempo).total_seconds()
        
        resultado = {
            'chunk_id': chunk_id,
            'registros_creados': registros_creados,
            'registros_actualizados': registros_actualizados,
            'errores': errores,
            'tiempo_procesamiento': tiempo_procesamiento,
            'registros_procesados': chunk_data.get('total_filas', 0),
            'archivo_id': archivo_id,
            'success': True
        }
        
        logger.info(f"✅ Chunk registros {chunk_id} completado: {registros_creados} creados, {registros_actualizados} actualizados en {tiempo_procesamiento:.2f}s")
        return resultado
        
    except Exception as e:
        tiempo_procesamiento = (timezone.now() - inicio_tiempo).total_seconds()
        error_msg = f"Error crítico en chunk registros {chunk_id}: {str(e)}"
        logger.error(error_msg)
        
        return {
            'chunk_id': chunk_id,
            'registros_creados': 0,
            'registros_actualizados': 0,
            'errores': [error_msg],
            'tiempo_procesamiento': tiempo_procesamiento,
            'registros_procesados': 0,
            'archivo_id': archivo_id,
            'success': False
        }


def consolidar_stats_novedades(resultados_chunks, tipo_procesamiento):
    """
    📊 Consolida estadísticas de múltiples chunks de procesamiento
    
    Args:
        resultados_chunks: Lista de resultados de chunks
        tipo_procesamiento: 'empleados' o 'registros'
        
    Returns:
        Dict: Estadísticas consolidadas
    """
    logger.info(f"📊 Consolidando estadísticas de {len(resultados_chunks)} chunks ({tipo_procesamiento})")
    
    # Inicializar contadores
    total_procesados = 0
    total_errores = []
    tiempo_total = 0
    chunks_exitosos = 0
    chunks_con_errores = 0
    
    # Contadores específicos por tipo
    if tipo_procesamiento == 'empleados':
        empleados_actualizados = 0
        for resultado in resultados_chunks:
            empleados_actualizados += resultado.get('empleados_actualizados', 0)
            total_procesados += resultado.get('registros_procesados', 0)
            total_errores.extend(resultado.get('errores', []))
            tiempo_total = max(tiempo_total, resultado.get('tiempo_procesamiento', 0))
            
            if resultado.get('success', False):
                chunks_exitosos += 1
            else:
                chunks_con_errores += 1
        
        stats_especificas = {
            'empleados_actualizados': empleados_actualizados
        }
        
    elif tipo_procesamiento == 'registros':
        registros_creados = 0
        registros_actualizados = 0
        for resultado in resultados_chunks:
            registros_creados += resultado.get('registros_creados', 0)
            registros_actualizados += resultado.get('registros_actualizados', 0)
            total_procesados += resultado.get('registros_procesados', 0)
            total_errores.extend(resultado.get('errores', []))
            tiempo_total = max(tiempo_total, resultado.get('tiempo_procesamiento', 0))
            
            if resultado.get('success', False):
                chunks_exitosos += 1
            else:
                chunks_con_errores += 1
        
        stats_especificas = {
            'registros_creados': registros_creados,
            'registros_actualizados': registros_actualizados
        }
    
    else:
        stats_especificas = {}
    
    # Calcular throughput
    throughput = total_procesados / tiempo_total if tiempo_total > 0 else 0
    
    consolidado = {
        'tipo_procesamiento': tipo_procesamiento,
        'chunks_totales': len(resultados_chunks),
        'chunks_exitosos': chunks_exitosos,
        'chunks_con_errores': chunks_con_errores,
        'registros_procesados': total_procesados,
        'errores_totales': len(total_errores),
        'errores': total_errores[:10],  # Solo primeros 10 errores para evitar overflow
        'tiempo_total_segundos': tiempo_total,
        'throughput_registros_por_segundo': round(throughput, 2),
        'timestamp_consolidacion': timezone.now().isoformat(),
        **stats_especificas
    }
    
    logger.info(f"✅ Consolidación {tipo_procesamiento} completada:")
    logger.info(f"  - Chunks exitosos: {chunks_exitosos}/{len(resultados_chunks)}")
    logger.info(f"  - Registros procesados: {total_procesados}")
    logger.info(f"  - Tiempo total: {tiempo_total:.2f}s")
    logger.info(f"  - Throughput: {throughput:.2f} registros/segundo")
    
    if stats_especificas:
        for key, value in stats_especificas.items():
            logger.info(f"  - {key}: {value}")
    
    return consolidado


def obtener_archivo_novedades_path(archivo_id):
    """
    📂 Obtiene la ruta del archivo de novedades
    
    Args:
        archivo_id: ID del ArchivoNovedadesUpload
        
    Returns:
        str: Ruta del archivo
    """
    try:
        from ..models import ArchivoNovedadesUpload
        archivo = ArchivoNovedadesUpload.objects.get(id=archivo_id)
        return archivo.archivo.path
    except Exception as e:
        logger.error(f"❌ Error obteniendo ruta archivo {archivo_id}: {e}")
        return None


def validar_chunk_data(chunk_data):
    """
    ✅ Valida la estructura de datos del chunk
    
    Args:
        chunk_data: Datos del chunk a validar
        
    Returns:
        bool: True si es válido
    """
    required_fields = ['chunk_id', 'datos', 'total_filas']
    
    for field in required_fields:
        if field not in chunk_data:
            logger.error(f"❌ Campo requerido faltante en chunk: {field}")
            return False
    
    if not isinstance(chunk_data['datos'], list):
        logger.error(f"❌ Campo 'datos' debe ser una lista")
        return False
    
    if len(chunk_data['datos']) != chunk_data['total_filas']:
        logger.warning(f"⚠️ Inconsistencia en tamaño de chunk: esperado {chunk_data['total_filas']}, obtenido {len(chunk_data['datos'])}")
    
    return True
