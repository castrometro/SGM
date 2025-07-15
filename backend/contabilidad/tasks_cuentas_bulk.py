"""
Tasks especializadas para el procesamiento de archivos de clasificación bulk
Refactorizado para usar Celery Chains y distribuir validaciones/procesamiento

FLUJO NUEVO DE CLASIFICACIÓN (REDISEÑADO):
1. Usuario sube archivo de clasificación (códigos + sets + valores)
2. Se procesan y almacenan directamente en AccountClassification
   - Con FK a cuenta si existe, o código temporal si no existe
   - Se crean ClasificacionSet y ClasificacionOption según necesidad
3. Usuario sube libro mayor -> se crean las CuentaContable
4. Se ejecuta migración automática: migrar_clasificaciones_temporales_a_fk()
   - Convierte clasificaciones temporales (por código) a FK reales
   - Elimina duplicados manteniendo la versión con FK

IMPORTANTE: 
- AccountClassification es la única fuente de verdad
- Modelo ClasificacionCuentaArchivo fue eliminado
- El mapeo ocurre DESPUÉS cuando existen las cuentas del libro mayor
"""

import hashlib
import logging
import os
from datetime import date

import pandas as pd
from celery import chain, shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import (
    ClasificacionArchivo, 
    # ClasificacionCuentaArchivo,  # OBSOLETO - ELIMINADO EN REDISEÑO
    ClasificacionSet,
    ClasificacionOption,
    CuentaContable,
    AccountClassification,
    UploadLog
)
from .utils.activity_logger import registrar_actividad_tarjeta

logger = logging.getLogger(__name__)


@shared_task(name='contabilidad.validar_nombre_archivo_clasificacion_task')
def validar_nombre_archivo_clasificacion_task(upload_log_id):
    """
    Task 1: Validar que el nombre del archivo cumpla con las convenciones
    """
    logger.info(f"Validando nombre de archivo para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    # Actualizar estado
    upload_log.estado = "validando_nombre"
    upload_log.save(update_fields=["estado"])
    
    try:
        es_valido, msg_valid = UploadLog.validar_nombre_archivo(
            upload_log.nombre_archivo_original, "Clasificacion", upload_log.cliente.rut
        )

        if not es_valido:
            upload_log.estado = "error"
            upload_log.errores = f"Nombre de archivo inválido: {msg_valid}"
            upload_log.save()
            
            # Registrar actividad de error
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="validate_filename",
                descripcion=f"Error validación nombre archivo: {msg_valid}",
                usuario=None,
                detalles={"upload_log_id": upload_log.id, "error": msg_valid},
                resultado="error",
                ip_address=None,
            )
            
            raise Exception(f"Nombre de archivo inválido: {msg_valid}")
        
        logger.info(f"Nombre de archivo válido para upload_log {upload_log_id}")
        return upload_log_id
        
    except Exception as e:
        if upload_log.estado != "error":  # Solo actualizar si no se actualizó antes
            upload_log.estado = "error"
            upload_log.errores = f"Error validando nombre archivo: {str(e)}"
            upload_log.save()
        raise


@shared_task(name='contabilidad.verificar_archivo_temporal_clasificacion_task')
def verificar_archivo_temporal_clasificacion_task(upload_log_id):
    """
    Task 2: Verificar que el archivo temporal existe y calcular hash
    """
    logger.info(f"Verificando archivo temporal para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    # Actualizar estado
    upload_log.estado = "verificando_archivo"
    upload_log.save(update_fields=["estado"])
    
    try:
        # Verificar ruta del archivo
        ruta_relativa = upload_log.ruta_archivo
        if not ruta_relativa:
            upload_log.estado = "error"
            upload_log.errores = "No hay ruta de archivo especificada en el upload_log"
            upload_log.save()
            raise Exception("No hay ruta de archivo especificada")

        ruta_completa = default_storage.path(ruta_relativa)

        if not os.path.exists(ruta_completa):
            upload_log.estado = "error"
            upload_log.errores = f"Archivo temporal no encontrado en: {ruta_relativa}"
            upload_log.save()
            
            # Registrar actividad de error
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="verify_file",
                descripcion="Archivo temporal no encontrado",
                usuario=None,
                detalles={"upload_log_id": upload_log.id, "ruta": ruta_relativa},
                resultado="error",
                ip_address=None,
            )
            
            raise Exception("Archivo temporal no encontrado")

        # Calcular hash del archivo
        with open(ruta_completa, "rb") as f:
            contenido = f.read()
            archivo_hash = hashlib.sha256(contenido).hexdigest()

        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])
        
        logger.info(f"Archivo temporal verificado para upload_log {upload_log_id}, hash: {archivo_hash[:8]}...")
        return upload_log_id
        
    except Exception as e:
        if upload_log.estado != "error":  # Solo actualizar si no se actualizó antes
            upload_log.estado = "error"
            upload_log.errores = f"Error verificando archivo: {str(e)}"
            upload_log.save()
        raise


@shared_task(name='contabilidad.validar_contenido_clasificacion_excel_task')
def validar_contenido_clasificacion_excel_task(upload_log_id):
    """
    Task 3: Validar exhaustivamente el contenido del archivo Excel
    """
    logger.info(f"Validando contenido Excel para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    # Actualizar estado
    upload_log.estado = "validando_contenido"
    upload_log.save(update_fields=["estado"])
    
    try:
        ruta_completa = default_storage.path(upload_log.ruta_archivo)
        
        # Usar la función de validación existente
        validacion = validar_archivo_clasificacion_excel(ruta_completa, upload_log.cliente.id)
        
        if not validacion['es_valido']:
            error_msg = "Archivo inválido: " + "; ".join(validacion['errores'])
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.resumen = {
                'validacion': validacion,
                'archivo_hash': upload_log.hash_archivo
            }
            upload_log.save()
            
            # Registrar actividad de error
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="validate_content",
                descripcion=f"Validación de archivo falló: {len(validacion['errores'])} errores",
                usuario=None,
                detalles={
                    "upload_log_id": upload_log.id,
                    "errores": validacion['errores'],
                    "advertencias": validacion['advertencias'],
                    "estadisticas": validacion['estadisticas']
                },
                resultado="error",
                ip_address=None,
            )
            
            raise Exception(error_msg)
        
        # Guardar validación exitosa en resumen
        if upload_log.resumen:
            upload_log.resumen.update({'validacion': validacion})
        else:
            upload_log.resumen = {'validacion': validacion}
        upload_log.save(update_fields=['resumen'])
        
        # Log de advertencias si las hay
        if validacion['advertencias']:
            logger.warning(f"Advertencias en archivo upload_log {upload_log.id}: {'; '.join(validacion['advertencias'])}")
        
        logger.info(f"Contenido Excel válido para upload_log {upload_log_id}")
        return upload_log_id
        
    except Exception as e:
        if upload_log.estado != "error":  # Solo actualizar si no se actualizó antes
            upload_log.estado = "error"
            upload_log.errores = f"Error validando contenido: {str(e)}"
            upload_log.save()
        raise


@shared_task(name='contabilidad.procesar_datos_clasificacion_task')
def procesar_datos_clasificacion_task(upload_log_id):
    """
    REDISEÑADO: Procesa Excel y crea directamente AccountClassification.
    No usa modelo intermedio - es la fuente única de verdad.
    Soporta tanto clasificaciones con FK (cuentas existentes) como temporales (por código).
    """
    logger.info(f"Procesando clasificación Excel directamente para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    # Actualizar estado
    upload_log.estado = "procesando_datos"
    upload_log.save(update_fields=["estado"])
    
    inicio = timezone.now()
    
    try:
        ruta_completa = default_storage.path(upload_log.ruta_archivo)
        
        # Leer el Excel
        df = pd.read_excel(ruta_completa)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas")

        columna_cuentas = df.columns[0]
        sets = list(df.columns[1:])

        # Eliminar clasificaciones anteriores del mismo upload_log
        AccountClassification.objects.filter(upload_log=upload_log).delete()
        logger.info(f"Eliminadas clasificaciones anteriores del upload_log {upload_log.id}")

        errores = []
        clasificaciones_creadas = 0
        clasificaciones_actualizadas = 0
        sets_creados = 0
        opciones_creadas = 0
        filas_vacias = 0

        # Procesar cada fila - CREAR DIRECTAMENTE AccountClassification
        for index, row in df.iterrows():
            numero_cuenta = (
                str(row[columna_cuentas]).strip()
                if not pd.isna(row[columna_cuentas])
                else ""
            )
            if not numero_cuenta:
                filas_vacias += 1
                continue
                
            # Verificar si la cuenta existe (para FK) o usar código temporal
            cuenta_obj = None
            try:
                cuenta_obj = CuentaContable.objects.get(
                    cliente=upload_log.cliente, 
                    codigo=numero_cuenta
                )
            except CuentaContable.DoesNotExist:
                # La cuenta no existe aún, se creará clasificación temporal
                pass
                
            # Procesar cada clasificación de la fila
            for set_name in sets:
                valor = row[set_name]
                if pd.isna(valor) or str(valor).strip() == "":
                    continue  # Saltar clasificaciones vacías
                    
                valor_limpio = str(valor).strip()
                
                try:
                    # Buscar o crear el set
                    set_clas, set_creado = ClasificacionSet.objects.get_or_create(
                        cliente=upload_log.cliente,
                        nombre=set_name,
                        defaults={
                            'descripcion': f'Set creado automáticamente desde Excel: {set_name}',
                            'idioma': 'es'
                        }
                    )
                    
                    if set_creado:
                        sets_creados += 1
                        logger.debug(f"Set creado: {set_name}")
                    
                    # Buscar o crear la opción
                    opcion, opcion_creada = ClasificacionOption.objects.get_or_create(
                        set_clas=set_clas,
                        valor=valor_limpio,
                        defaults={
                            'descripcion': f'Opción creada automáticamente: {valor_limpio}'
                        }
                    )
                    
                    if opcion_creada:
                        opciones_creadas += 1
                        logger.debug(f"Opción creada: {valor_limpio} en set {set_name}")
                    
                    # Crear o actualizar AccountClassification
                    if cuenta_obj:
                        # Usar FK a cuenta existente
                        clasificacion_existente = AccountClassification.objects.filter(
                            cuenta=cuenta_obj,
                            set_clas=set_clas
                        ).first()
                        
                        if clasificacion_existente:
                            # Actualizar existente
                            clasificacion_existente.opcion = opcion
                            clasificacion_existente.upload_log = upload_log
                            clasificacion_existente.origen = 'actualizacion'
                            clasificacion_existente.save()
                            clasificaciones_actualizadas += 1
                        else:
                            # Crear nueva con FK
                            AccountClassification.objects.create(
                                cuenta=cuenta_obj,
                                cliente=upload_log.cliente,
                                set_clas=set_clas,
                                opcion=opcion,
                                upload_log=upload_log,
                                origen='excel',
                                cuenta_codigo=numero_cuenta  # Mantener código para compatibilidad con modal
                            )
                            clasificaciones_creadas += 1
                    else:
                        # Crear clasificación temporal (por código)
                        clasificacion_existente = AccountClassification.objects.filter(
                            cliente=upload_log.cliente,
                            cuenta_codigo=numero_cuenta,
                            set_clas=set_clas
                        ).first()
                        
                        if clasificacion_existente:
                            # Actualizar temporal existente
                            clasificacion_existente.opcion = opcion
                            clasificacion_existente.upload_log = upload_log
                            clasificacion_existente.origen = 'actualizacion'
                            clasificacion_existente.save()
                            clasificaciones_actualizadas += 1
                        else:
                            # Crear nueva temporal
                            AccountClassification.objects.create(
                                cuenta_codigo=numero_cuenta,
                                cliente=upload_log.cliente,
                                set_clas=set_clas,
                                opcion=opcion,
                                upload_log=upload_log,
                                origen='excel'
                            )
                            clasificaciones_creadas += 1
                            
                except Exception as e:
                    error_msg = f"Fila {index+2}, Set '{set_name}': {str(e)}"
                    logger.error(f"Error procesando clasificación: {error_msg}")
                    errores.append(error_msg)

        # Preparar resumen
        resumen_procesamiento = {
            "total_filas": len(df),
            "filas_vacias": filas_vacias,
            "sets_encontrados": sets,
            "sets_creados": sets_creados,
            "opciones_creadas": opciones_creadas,
            "clasificaciones_creadas": clasificaciones_creadas,
            "clasificaciones_actualizadas": clasificaciones_actualizadas,
            "errores_count": len(errores),
            "errores": errores[:10],  # Solo los primeros 10 errores
            "procesamiento_directo": True,  # Indicador del nuevo flujo
        }

        # Actualizar resumen existente
        if upload_log.resumen:
            upload_log.resumen.update(resumen_procesamiento)
        else:
            upload_log.resumen = resumen_procesamiento
            
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save(update_fields=['resumen', 'tiempo_procesamiento'])
        
        logger.info(f"Clasificaciones procesadas para upload_log {upload_log_id}: {clasificaciones_creadas} creadas, {clasificaciones_actualizadas} actualizadas")
        return upload_log_id
        
    except Exception as e:
        upload_log.estado = "error"
        upload_log.errores = f"Error procesando datos: {str(e)}"
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save()
        raise




@shared_task(name='contabilidad.guardar_archivo_clasificacion_task')
def guardar_archivo_clasificacion_task(upload_log_id):
    """
    Task 5: Guardar el archivo procesado en ClasificacionArchivo
    """
    logger.info(f"Guardando archivo de clasificación para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    # Actualizar estado
    upload_log.estado = "guardando_archivo"
    upload_log.save(update_fields=["estado"])
    
    try:
        ruta_completa = default_storage.path(upload_log.ruta_archivo)
        
        # Leer contenido del archivo
        with open(ruta_completa, "rb") as f:
            contenido = f.read()

        # Generar nombre final
        nombre_final = f"clasificacion_cliente_{upload_log.cliente.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Crear o actualizar ClasificacionArchivo
        archivo_existente, created = ClasificacionArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            defaults={
                "upload_log": upload_log,
                "archivo": ContentFile(contenido, name=nombre_final),
            },
        )
        
        if not created:
            # Actualizar archivo existente
            if archivo_existente.archivo:
                try:
                    archivo_existente.archivo.delete()
                except Exception:
                    pass
            archivo_existente.archivo.save(nombre_final, ContentFile(contenido))
            archivo_existente.upload_log = upload_log
            archivo_existente.fecha_subida = timezone.now()
            archivo_existente.save()
        
        logger.info(f"Archivo de clasificación guardado para upload_log {upload_log_id}")
        return upload_log_id
        
    except Exception as e:
        upload_log.estado = "error"
        upload_log.errores = f"Error guardando archivo: {str(e)}"
        upload_log.save()
        raise


@shared_task(name='contabilidad.finalizar_procesamiento_clasificacion_task')
def finalizar_procesamiento_clasificacion_task(upload_log_id):
    """
    Task 6: Finalizar el procesamiento, limpiar archivos temporales y disparar post-procesamiento
    """
    logger.info(f"Finalizando procesamiento de clasificación para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise Exception(f"UploadLog {upload_log_id} no encontrado")

    try:
        # Actualizar estado final
        upload_log.estado = "completado"
        upload_log.save(update_fields=["estado"])
        
        # Limpiar archivo temporal
        if upload_log.ruta_archivo:
            ruta_completa = default_storage.path(upload_log.ruta_archivo)
            try:
                if os.path.exists(ruta_completa):
                    os.remove(ruta_completa)
                    logger.info(f"Archivo temporal eliminado: {ruta_completa}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo temporal {ruta_completa}: {e}")

        # Crear automáticamente sets y opciones desde los datos RAW
        logger.info(f"Creando sets y opciones automáticamente para cliente {upload_log.cliente.id}")
        try:
            resultado_sets = crear_sets_y_opciones_clasificacion_desde_raw(upload_log.cliente.id)
            logger.info(f"Resultado creación sets desde RAW: {resultado_sets}")
        except Exception as e:
            logger.error(f"Error creando sets desde RAW automáticamente: {str(e)}")
            # No interrumpir el procesamiento por este error
        
        # Crear también sets predefinidos con opciones bilingües estándar
        logger.info(f"Creando sets predefinidos para cliente {upload_log.cliente.id}")
        try:
            resumen = upload_log.resumen or {}
            sets_archivo = [s.lower().strip() for s in resumen.get('sets_encontrados', [])]
            omit_sets = []
            if any(s in ['esr', 'estado de resultado'] for s in sets_archivo):
                omit_sets.append('Estado de Resultados')
            if any(s in ['eri', 'estado de resultado integral'] for s in sets_archivo):
                omit_sets.append('Estado de Resultados Integral')

            resultado_predefinidos = crear_sets_predefinidos_clasificacion(
                upload_log.cliente.id, omit_sets=omit_sets
            )
            logger.info(f"Resultado creación sets predefinidos: {resultado_predefinidos}")
        except Exception as e:
            logger.error(f"Error creando sets predefinidos: {str(e)}")
            # No interrumpir el procesamiento por este error

        # Registrar actividad exitosa
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        resumen = upload_log.resumen or {}
        registros_guardados = resumen.get('registros_guardados', 0)
        errores_count = resumen.get('errores_count', 0)
        
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="process_excel",
            descripcion=f"Almacenados datos RAW de clasificación: {registros_guardados} registros y sets generados",
            usuario=None,
            detalles={
                "upload_log_id": upload_log.id, 
                "errores": errores_count,
                "sets_creados": True,
                "nota": "Datos RAW almacenados y sets/opciones creados automáticamente"
            },
            resultado="exito",
            ip_address=None,
        )

        logger.info(f"Datos RAW de clasificación almacenados para upload_log {upload_log_id} - Sets y opciones creados")
        return f"Completado: {registros_guardados} registros RAW almacenados y sets/opciones creados"
        
    except Exception as e:
        upload_log.estado = "error"
        upload_log.errores = f"Error finalizando procesamiento: {str(e)}"
        upload_log.save()
        
        # Registrar actividad de error
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="process_excel",
            descripcion=f"Error finalizando procesamiento: {str(e)}",
            usuario=None,
            detalles={"upload_log_id": upload_log.id},
            resultado="error",
            ip_address=None,
        )
        raise


@shared_task(name='contabilidad.iniciar_procesamiento_clasificacion_chain')
def iniciar_procesamiento_clasificacion_chain(upload_log_id):
    """
    Task principal que inicia el chain de procesamiento de clasificación
    """
    logger.info(f"Iniciando chain de procesamiento de clasificación para upload_log_id: {upload_log_id}")
    
    # Crear el chain de tasks
    processing_chain = chain(
        validar_nombre_archivo_clasificacion_task.s(upload_log_id),
        verificar_archivo_temporal_clasificacion_task.s(),
        validar_contenido_clasificacion_excel_task.s(),
        procesar_datos_clasificacion_task.s(),
        guardar_archivo_clasificacion_task.s(),
        finalizar_procesamiento_clasificacion_task.s(),
    )
    
    # Ejecutar el chain
    result = processing_chain.apply_async()
    
    logger.info(f"Chain de clasificación iniciado con ID: {result.id} para upload_log {upload_log_id}")
    return result.id


# ==== FUNCIONES AUXILIARES (movidas desde tasks.py) ====


@shared_task(name='contabilidad.mapear_clasificaciones_con_cuentas')
def mapear_clasificaciones_con_cuentas(upload_log_id, cierre_id=None):
    """
    REDISEÑADO: Migra clasificaciones temporales (por código) a FK definitivas
    después de la subida del libro mayor cuando ya existen las CuentaContable.
    """
    logger.info(f"Iniciando migración de clasificaciones temporales a FK para upload_log {upload_log_id}")

    try:
        # Obtener el upload_log y extraer el cliente
        upload_log = UploadLog.objects.get(id=upload_log_id)
        cliente = upload_log.cliente
        cliente_id = cliente.id
    except UploadLog.DoesNotExist:
        msg = f"[mapear_clasificaciones] UploadLog con id={upload_log_id} no encontrado."
        logger.error(msg)
        return {'error': msg}
    except Exception as e:
        msg = f"[mapear_clasificaciones] Error obteniendo UploadLog {upload_log_id}: {str(e)}"
        logger.error(msg)
        return {'error': msg}

    # 1) Buscar cierre
    from contabilidad.models import CierreContabilidad
    cierre = None
    if cierre_id:
        cierre = CierreContabilidad.objects.filter(id=cierre_id, cliente=cliente).first()
    else:
        cierre = (
            CierreContabilidad.objects
            .filter(cliente=cliente, estado__in=[
                'pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision'
            ])
            .order_by('-fecha_creacion')
            .first()
        )

    if not cierre:
        msg = f"[mapear_clasificaciones] No hay cierre activo para cliente {cliente_id}."
        logger.warning(msg)
        return {'warning': msg}

    # 2) Obtener clasificaciones temporales pendientes (sin FK a cuenta)
    clasificaciones_temporales = AccountClassification.objects.filter(
        cliente=cliente,
        cuenta__isnull=True,  # Solo las temporales
        cuenta_codigo__isnull=False  # Que tengan código
    ).exclude(cuenta_codigo='')
    
    if not clasificaciones_temporales.exists():
        msg = f"[mapear_clasificaciones] No hay clasificaciones temporales para cliente {cliente_id}."
        logger.info(msg)
        return {'info': msg}

    # 3) Construir diccionario de cuentas
    cuentas_dict = {c.codigo: c for c in CuentaContable.objects.filter(cliente=cliente)}
    if not cuentas_dict:
        msg = f"[mapear_clasificaciones] No hay cuentas creadas para cliente {cliente_id} (sube el libro mayor primero)."
        logger.warning(msg)
        return {'warning': msg}

    # 4) Hacer la migración de temporales a FK
    migraciones_exitosas = 0
    cuentas_no_encontradas = 0
    errores_mapeo = []

    for clasificacion_temporal in clasificaciones_temporales:
        try:
            cuenta = cuentas_dict.get(clasificacion_temporal.cuenta_codigo)
            if not cuenta:
                cuentas_no_encontradas += 1
                logger.debug(f"Cuenta no encontrada: {clasificacion_temporal.cuenta_codigo}")
                continue

            # Verificar si ya existe una clasificación definitiva para esta cuenta y set
            clasificacion_definitiva = AccountClassification.objects.filter(
                cuenta=cuenta,
                set_clas=clasificacion_temporal.set_clas
            ).first()
            
            if clasificacion_definitiva:
                # Ya existe definitiva, eliminar la temporal
                clasificacion_temporal.delete()
                logger.debug(f"Eliminada clasificación temporal duplicada: {cuenta.codigo} -> {clasificacion_temporal.set_clas.nombre}")
            else:
                # Migrar temporal a definitiva
                clasificacion_temporal.cuenta = cuenta
                clasificacion_temporal.cliente = cuenta.cliente
                # CORREGIDO: MANTENER cuenta_codigo para compatibilidad con modal CRUD
                # clasificacion_temporal.cuenta_codigo = ''  # NO limpiar código temporal
                clasificacion_temporal.origen = 'migracion_fk'
                clasificacion_temporal.save()
                
                migraciones_exitosas += 1
                logger.debug(f"Migración exitosa: {cuenta.codigo} -> {clasificacion_temporal.set_clas.nombre} -> {clasificacion_temporal.opcion.valor}")

        except Exception as e:
            errores_mapeo.append(f"Clasificación temporal {clasificacion_temporal.id}: {e}")
            logger.error(f"[mapear_clasificaciones] Error migrando clasificación {clasificacion_temporal.id}: {e}")

    # 5) Registrar actividad
    from contabilidad.utils.activity_logger import registrar_actividad_tarjeta
    from datetime import date
    periodo = cierre.periodo or date.today().strftime("%Y-%m")
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo,
        tarjeta="clasificacion",
        accion="migracion_clasificaciones_fk",
        descripcion=(
            f"Migración completada: {migraciones_exitosas} migradas, "
            f"{cuentas_no_encontradas} cuentas no encontradas, "
            f"{len(errores_mapeo)} errores"
        ),
        usuario=None,
        detalles={
            "migraciones_exitosas": migraciones_exitosas,
            "cuentas_no_encontradas": cuentas_no_encontradas,
            "errores_mapeo": errores_mapeo,
            "clasificaciones_procesadas": clasificaciones_temporales.count(),
            "cierre_id": cierre.id,
        },
        resultado="exito" if not errores_mapeo else "parcial",
        ip_address=None,
    )

    return {
        "migraciones_exitosas": migraciones_exitosas,
        "cuentas_no_encontradas": cuentas_no_encontradas,
        "errores_mapeo": errores_mapeo,
    }

@shared_task(name='contabilidad.crear_sets_y_opciones_clasificacion_desde_raw')
def crear_sets_y_opciones_clasificacion_desde_raw(cliente_id):
    """
    REDISEÑADO: Esta función ya no es necesaria porque los sets y opciones
    se crean automáticamente durante el procesamiento directo del Excel
    en procesar_datos_clasificacion_task.
    """
    logger.info(f"Función obsoleta: crear_sets_y_opciones_clasificacion_desde_raw para cliente {cliente_id}")
    logger.info("Los sets y opciones se crean automáticamente durante el procesamiento del Excel")
    
    try:
        from .models import Cliente
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener estadísticas actuales para el reporte
        from contabilidad.models import ClasificacionSet, ClasificacionOption, AccountClassification
        
        sets_count = ClasificacionSet.objects.filter(cliente=cliente).count()
        opciones_count = ClasificacionOption.objects.filter(set_clas__cliente=cliente).count()
        clasificaciones_count = AccountClassification.objects.filter(cliente=cliente).count()
        
        return {
            'info': 'Sets y opciones ya creados automáticamente durante procesamiento',
            'sets_existentes': sets_count,
            'opciones_existentes': opciones_count,
            'clasificaciones_existentes': clasificaciones_count,
            'proceso_automatico': True
        }
        
    except Cliente.DoesNotExist:
        msg = f"Cliente con id={cliente_id} no existe."
        logger.error(msg)
        return {'error': msg}
        
        if not registros_clasificacion.exists():
            logger.warning(f"No hay registros RAW para cliente {cliente_id}")
            return "Sin registros RAW para procesar"
        
        sets_creados = 0
        opciones_creadas = 0
        
        # Extraer todos los sets y valores únicos de todos los registros RAW
        todos_los_sets = {}
        
        for registro in registros_clasificacion:
            clasificaciones = registro.clasificaciones or {}
            for set_nombre, valor in clasificaciones.items():
                if valor and str(valor).strip():
                    if set_nombre not in todos_los_sets:
                        todos_los_sets[set_nombre] = set()
                    todos_los_sets[set_nombre].add(str(valor).strip())
        
        # Crear o actualizar ClasificacionSet y sus opciones
        for set_nombre, valores in todos_los_sets.items():
            # Crear o obtener el ClasificacionSet
            clasificacion_set, set_created = ClasificacionSet.objects.get_or_create(
                cliente=cliente,
                nombre=set_nombre,
                defaults={
                    'descripcion': f'Set de clasificación generado automáticamente desde datos RAW',
                    'idioma': 'es'
                }
            )
            
            if set_created:
                sets_creados += 1
                logger.info(f"Creado nuevo ClasificacionSet: {set_nombre}")
            
            # Crear las opciones para este set
            for valor in valores:
                opcion, opcion_created = ClasificacionOption.objects.get_or_create(
                    set_clas=clasificacion_set,
                    valor=valor,
                    defaults={
                        'descripcion': f'Opción generada automáticamente: {valor}',
                        'parent': None
                    }
                )
                
                if opcion_created:
                    opciones_creadas += 1
        
        resultado = f"Creados {sets_creados} sets y {opciones_creadas} opciones para cliente {cliente.nombre}"
        logger.info(resultado)
        return resultado
        
    except Exception as e:
        logger.exception(f"Error creando sets desde RAW para cliente {cliente_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(name='contabilidad.crear_sets_y_opciones_clasificacion')
def crear_sets_y_opciones_clasificacion(upload_log_id):
    """
    DEPRECATED: Esta función se mantiene por compatibilidad pero ya no se usa automáticamente.
    Use 'crear_sets_y_opciones_clasificacion_desde_raw' y 'mapear_clasificaciones_con_cuentas' en su lugar.
    
    Crea automáticamente ClasificacionSet y ClasificacionOption basado en 
    los datos de clasificación encontrados en un upload específico.
    """
    logger.warning(f"Usando función DEPRECATED crear_sets_y_opciones_clasificacion para upload_log {upload_log_id}")
    logger.info(f"Se recomienda usar mapear_clasificaciones_con_cuentas después de subir el libro mayor")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return f"Error: UploadLog {upload_log_id} no encontrado"
    
    # Delegar a la nueva función
    return crear_sets_y_opciones_clasificacion_desde_raw(upload_log.cliente.id)


def validar_archivo_clasificacion_excel(ruta_archivo, cliente_id):
    """
    Valida exhaustivamente un archivo Excel de clasificaciones antes de procesarlo.
    Función auxiliar movida desde tasks.py
    """
    import re
    import pandas as pd
    
    errores = []
    advertencias = []
    estadisticas = {}
    
    try:
        # 1. VALIDACIONES BÁSICAS DEL ARCHIVO
        if not os.path.exists(ruta_archivo):
            errores.append("El archivo no existe en la ruta especificada")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        
        # Verificar que el archivo no esté vacío
        if os.path.getsize(ruta_archivo) == 0:
            errores.append("El archivo está vacío (0 bytes)")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        
        # 2. LEER Y VALIDAR ESTRUCTURA DEL EXCEL
        try:
            df = pd.read_excel(ruta_archivo)
        except Exception as e:
            errores.append(f"Error leyendo el archivo Excel: {str(e)}")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        
        # Verificar que tenga al menos una fila de datos (además del header)
        if len(df) == 0:
            errores.append("El archivo no contiene filas de datos (solo headers o completamente vacío)")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        
        # Verificar que tenga al menos 2 columnas (códigos + al menos un set)
        if len(df.columns) < 2:
            errores.append("El archivo debe tener al menos 2 columnas: códigos de cuenta y al menos un set de clasificación")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        
        # 3. VALIDAR ESTRUCTURA DE COLUMNAS
        columna_cuentas = df.columns[0]
        sets_columnas = list(df.columns[1:])
        
        # Verificar que las columnas de sets tengan nombres válidos
        for i, set_nombre in enumerate(sets_columnas, 2):
            if pd.isna(set_nombre) or str(set_nombre).strip() == '':
                errores.append(f"La columna {chr(65+i)} (columna {i+1}) no tiene nombre de set válido")
            elif len(str(set_nombre).strip()) > 100:  # Límite del modelo ClasificacionSet
                errores.append(f"Nombre de set demasiado largo en columna {chr(65+i)}: '{str(set_nombre)[:50]}...' (máximo 100 caracteres)")
        
        # 4. VALIDAR CÓDIGOS DE CUENTA
        cuentas_validas = 0
        cuentas_vacias = 0
        cuentas_formato_invalido = []
        cuentas_duplicadas = []
        
        # Patrón para códigos de cuenta: solo números y guiones
        patron_cuenta = r'^[\d\-]+$'  # Solo dígitos y guiones
        
        cuentas_vistas = set()
        
        for index, cuenta in df[columna_cuentas].items():
            fila_excel = index + 2  # +1 por 0-indexing, +1 por header
            
            # Verificar si está vacía - siempre omitir filas vacías
            if pd.isna(cuenta) or str(cuenta).strip() == '':
                cuentas_vacias += 1
                continue
            
            cuenta_str = str(cuenta).strip()
            
            # Verificar formato: solo números y guiones
            if not re.match(patron_cuenta, cuenta_str):
                cuentas_formato_invalido.append(f"Fila {fila_excel}: '{cuenta_str}'")
                continue
            
            # Solo verificar duplicados en el archivo
            if cuenta_str in cuentas_vistas:
                cuentas_duplicadas.append(f"Fila {fila_excel}: '{cuenta_str}'")
            else:
                cuentas_vistas.add(cuenta_str)
            
            cuentas_validas += 1
        
        # 5. VALIDAR CLASIFICACIONES
        filas_sin_clasificaciones = []
        clasificaciones_vacias_por_set = {set_name: 0 for set_name in sets_columnas}
        valores_muy_largos = []
        
        for index, row in df.iterrows():
            fila_excel = index + 2
            cuenta = row[columna_cuentas]
            
            # Solo validar si la cuenta no está vacía
            if pd.isna(cuenta) or str(cuenta).strip() == '':
                continue
            
            tiene_alguna_clasificacion = False
            
            for set_nombre in sets_columnas:
                valor = row[set_nombre]
                
                if pd.isna(valor) or str(valor).strip() == '':
                    clasificaciones_vacias_por_set[set_nombre] += 1
                else:
                    tiene_alguna_clasificacion = True
                    # Verificar longitud del valor
                    if len(str(valor).strip()) > 100:  # Límite del modelo ClasificacionOption
                        valores_muy_largos.append(f"Fila {fila_excel}, Set '{set_nombre}': '{str(valor)[:50]}...'")
            
            if not tiene_alguna_clasificacion:
                filas_sin_clasificaciones.append(f"Fila {fila_excel}: '{str(cuenta).strip()}'")
        
        # 6. GENERAR ERRORES Y ADVERTENCIAS
        
        # Errores críticos
        if cuentas_formato_invalido:
            errores.append(f"Códigos de cuenta con caracteres inválidos ({len(cuentas_formato_invalido)}): {', '.join(cuentas_formato_invalido[:3])}")
            if len(cuentas_formato_invalido) > 3:
                errores.append(f"... y {len(cuentas_formato_invalido) - 3} más")
            errores.append("Los códigos de cuenta solo pueden contener números y guiones (-)")
        
        if cuentas_duplicadas:
            errores.append(f"Códigos de cuenta duplicados ({len(cuentas_duplicadas)}): {', '.join(cuentas_duplicadas[:3])}")
            if len(cuentas_duplicadas) > 3:
                errores.append(f"... y {len(cuentas_duplicadas) - 3} más")
        
        if valores_muy_largos:
            errores.append(f"Valores de clasificación demasiado largos (máximo 100 caracteres): {', '.join(valores_muy_largos[:3])}")
        
        # Advertencias
        if cuentas_vacias > 0:
            advertencias.append(f"Se encontraron {cuentas_vacias} filas con códigos de cuenta vacíos (serán omitidas)")
        
        if filas_sin_clasificaciones:
            advertencias.append(f"Cuentas sin ninguna clasificación ({len(filas_sin_clasificaciones)}): {', '.join(filas_sin_clasificaciones[:3])}")
            if len(filas_sin_clasificaciones) > 3:
                advertencias.append(f"... y {len(filas_sin_clasificaciones) - 3} más")
        
        # Advertencias por set vacío
        for set_nombre, vacias in clasificaciones_vacias_por_set.items():
            if vacias > 0:
                porcentaje = (vacias / len(df)) * 100
                if porcentaje > 50:  # Si más del 50% están vacías
                    advertencias.append(f"Set '{set_nombre}': {vacias} cuentas sin clasificación ({porcentaje:.1f}%)")
        
        # 7. ESTADÍSTICAS
        estadisticas = {
            'total_filas': len(df),
            'total_sets': len(sets_columnas),
            'sets_nombres': sets_columnas,
            'cuentas_validas': cuentas_validas,
            'cuentas_vacias': cuentas_vacias,
            'cuentas_formato_invalido': len(cuentas_formato_invalido),
            'cuentas_duplicadas': len(cuentas_duplicadas),
            'filas_sin_clasificaciones': len(filas_sin_clasificaciones),
            'clasificaciones_vacias_por_set': clasificaciones_vacias_por_set
        }
        
        # 8. DETERMINAR SI ES VÁLIDO
        es_valido = len(errores) == 0 and cuentas_validas > 0
        
        return {
            'es_valido': es_valido,
            'errores': errores,
            'advertencias': advertencias,
            'estadisticas': estadisticas
        }
        
    except Exception as e:
        errores.append(f"Error inesperado validando archivo: {str(e)}")
        return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}


@shared_task(name='contabilidad.crear_sets_predefinidos_clasificacion')
def crear_sets_predefinidos_clasificacion(cliente_id, omit_sets=None):
    """
    Crea sets de clasificación predefinidos con opciones bilingües estándar
    para clasificación contable. Incluye sets como Tipo de Cuenta, Categoría IFRS, etc.
    
    IMPORTANTE: Los sets son únicos, las opciones contienen tanto valor_es como valor_en
    """
    logger.info(f"[SETS_PREDEFINIDOS] Iniciando creación para cliente {cliente_id}")
    
    try:
        from .models import Cliente, ClasificacionSet, ClasificacionOption
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            logger.info(f"[SETS_PREDEFINIDOS] Cliente encontrado: {cliente.nombre} (Bilingüe: {cliente.bilingue})")
        except Cliente.DoesNotExist:
            msg = f"[crear_sets_predefinidos] Cliente con id={cliente_id} no existe."
            logger.error(msg)
            return {'error': msg}
        
        if omit_sets is None:
            omit_sets = []

        sets_creados = 0
        opciones_creadas = 0
        sets_actualizados = 0
        opciones_actualizadas = 0
        
        # Definir sets predefinidos con opciones bilingües
        sets_predefinidos = {
            'Estado Situacion Financiera': {
                'descripcion': 'Clasificación para informe ESF',
                'opciones': [
                    {'valor': 'Activo Corriente', 'descripcion': 'Cuentas de activo corriente', 'valor_en': 'Current Assets', 'descripcion_en': 'Current assets accounts'},
                    {'valor': 'Pasivo Corriente', 'descripcion': 'Cuentas de pasivo corriente', 'valor_en': 'Current Liabilities', 'descripcion_en': 'Current liabilities accounts'},
                    {'valor': 'Activo No Corriente', 'descripcion': 'Cuentas de activo no corriente', 'valor_en': 'Non-Current Assets', 'descripcion_en': 'Non-current assets accounts'},
                    {'valor': 'Pasivo No Corriente', 'descripcion': 'Cuentas de pasivo no corriente', 'valor_en': 'Non-Current Liabilities', 'descripcion_en': 'Non-current liabilities accounts'},
                    {'valor': 'Patrimonio', 'descripcion': 'Cuentas de patrimonio', 'valor_en': 'Patrimony', 'descripcion_en': 'Patrimony accounts'},
                ]
            },
            'Estado de Resultados Integral': {
                'descripcion': 'Clasificación para informe ERI',
                'opciones': [
                    {'valor': 'Ganancias Brutas', 'descripcion': 'Ganancias Brutas', 'valor_en': 'Gross Earnings', 'descripcion_en': 'Gross earnings'},
                    {'valor': 'Ganancia (perdida)', 'descripcion': 'Ganancia (pérdida)', 'valor_en': 'Earnings (Loss)', 'descripcion_en': 'Earnings (Loss)'},
                    {'valor': 'Ganancia (perdida) antes de Impuestos', 'descripcion': 'Ganancia (pérdida) antes de Impuestos', 'valor_en': 'Earnings (Loss) Before Taxes', 'descripcion_en': 'Earnings (Loss) before taxes'},
                ]
            },

            'Estado de Cambio Patrimonial': {
                'descripcion': 'Clasificación para informe ECP',
                'opciones': [
                    {'valor': 'Capital', 'descripcion': 'Capital', 'valor_en': 'Capital', 'descripcion_en': 'Capital'},
                    {'valor': 'Otras Reservas', 'descripcion': 'Otras Reservas', 'valor_en': 'Other Reserves', 'descripcion_en': 'Other reserves'},
                    {'valor': 'Resultados Acumulados', 'descripcion': 'Resultados Acumulados', 'valor_en': 'Accumulated Earnings', 'descripcion_en': 'Accumulated earnings'},   
                ]
            },



        }
        
        logger.info(f"[SETS_PREDEFINIDOS] Creando {len(sets_predefinidos)} sets predefinidos (sets únicos con opciones bilingües)...")
        
        # Crear sets y opciones
        for set_nombre, set_info in sets_predefinidos.items():
            if set_nombre in omit_sets:
                logger.info(f"[SETS_PREDEFINIDOS] Omitiendo set existente en archivo: {set_nombre}")
                continue
            logger.debug(f"[SETS_PREDEFINIDOS] Procesando set: {set_nombre}")
            
            # Crear o actualizar el ClasificacionSet único (no duplicamos por idioma)
            clasificacion_set, set_created = ClasificacionSet.objects.get_or_create(
                cliente=cliente,
                nombre=set_nombre,
                defaults={
                    'descripcion': set_info['descripcion'],
                    'idioma': 'es'  # Set base en español, opciones son bilingües
                }
            )
            
            if set_created:
                sets_creados += 1
                logger.info(f"[SETS_PREDEFINIDOS] ✓ Creado ClasificacionSet: {set_nombre}")
            else:
                sets_actualizados += 1
                logger.debug(f"[SETS_PREDEFINIDOS] - Ya existía ClasificacionSet: {set_nombre}")
            
            # Crear opciones bilingües para el set
            opciones_set_creadas = 0
            opciones_set_actualizadas = 0
            
            for opcion_info in set_info['opciones']:
                # Preparar datos de la opción (siempre incluye ambos idiomas si están disponibles)
                opcion_defaults = {
                    'descripcion': opcion_info['descripcion'],
                    'parent': None
                }
                
                # Agregar campos en inglés si existen y el cliente es bilingüe
                if cliente.bilingue and 'valor_en' in opcion_info:
                    opcion_defaults['valor_en'] = opcion_info['valor_en']
                    opcion_defaults['descripcion_en'] = opcion_info['descripcion_en']
                
                # Crear o actualizar la opción
                opcion, opcion_created = ClasificacionOption.objects.update_or_create(
                    set_clas=clasificacion_set,
                    valor=opcion_info['valor'],  # Clave única: set + valor en español
                    defaults=opcion_defaults
                )
                
                if opcion_created:
                    opciones_creadas += 1
                    opciones_set_creadas += 1
                    accion = "creada"
                else:
                    opciones_actualizadas += 1
                    opciones_set_actualizadas += 1
                    accion = "actualizada"
                
                # Log detallado de la opción
                if cliente.bilingue and 'valor_en' in opcion_info:
                    logger.debug(f"[SETS_PREDEFINIDOS]   - Opción {accion}: '{opcion_info['valor']}' / '{opcion_info['valor_en']}'")
                else:
                    logger.debug(f"[SETS_PREDEFINIDOS]   - Opción {accion}: '{opcion_info['valor']}'")
            
            logger.debug(f"[SETS_PREDEFINIDOS] Set {set_nombre}: {opciones_set_creadas} opciones creadas, {opciones_set_actualizadas} actualizadas")
        
        # Resumen final
        total_sets = sets_creados + sets_actualizados
        total_opciones = opciones_creadas + opciones_actualizadas
        bilingue_msg = " (opciones bilingües ES/EN)" if cliente.bilingue else " (solo español)"
        
        resultado = f"Sets predefinidos procesados para cliente {cliente.nombre}{bilingue_msg}: {sets_creados} sets nuevos, {sets_actualizados} sets existentes, {opciones_creadas} opciones nuevas, {opciones_actualizadas} opciones actualizadas"
        logger.info(f"[SETS_PREDEFINIDOS] ✅ {resultado}")
        
        return {
            'exito': True,
            'sets_creados': sets_creados,
            'sets_actualizados': sets_actualizados,
            'opciones_creadas': opciones_creadas,
            'opciones_actualizadas': opciones_actualizadas,
            'total_sets': total_sets,
            'total_opciones': total_opciones,
            'cliente_bilingue': cliente.bilingue,
            'mensaje': resultado
        }
        
    except Exception as e:
        error_msg = f"Error creando sets predefinidos para cliente {cliente_id}: {str(e)}"
        logger.exception(f"[SETS_PREDEFINIDOS] ❌ {error_msg}")
        return {'error': error_msg}

@shared_task(name='contabilidad.reinstalar_sets_predefinidos_clasificacion')
def reinstalar_sets_predefinidos_clasificacion(cliente_id, limpiar_existentes=False):
    """
    Reinstala o recupera los sets predefinidos de clasificación para un cliente.
    Útil para recuperar sets perdidos o actualizarlos.
    
    Args:
        cliente_id: ID del cliente
        limpiar_existentes: Si True, elimina sets existentes antes de crear nuevos
        
    NOTA: Solo maneja sets únicos, no duplicados por idioma.
    """
    logger.info(f"[REINSTALAR_SETS] Iniciando para cliente {cliente_id}, limpiar_existentes={limpiar_existentes}")
    
    try:
        from .models import Cliente, ClasificacionSet, ClasificacionOption
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            logger.info(f"[REINSTALAR_SETS] Cliente: {cliente.nombre} (Bilingüe: {cliente.bilingue})")
        except Cliente.DoesNotExist:
            msg = f"[reinstalar_sets] Cliente con id={cliente_id} no existe."
            logger.error(msg)
            return {'error': msg}
        
        sets_eliminados = 0
        
        # Si se solicita limpiar, eliminar sets existentes que coincidan con nombres predefinidos
        if limpiar_existentes:
            nombres_predefinidos = [
                'Tipo de Cuenta', 'Clasificacion Balance', 'Categoria IFRS', 'AGRUPACION CLIENTE'
            ]
            
            # NOTA: Ya no buscamos versiones (EN) porque ahora solo hay sets únicos
            sets_a_eliminar = ClasificacionSet.objects.filter(
                cliente=cliente,
                nombre__in=nombres_predefinidos
            )
            
            logger.info(f"[REINSTALAR_SETS] Eliminando {sets_a_eliminar.count()} sets existentes...")
            sets_eliminados_result = sets_a_eliminar.delete()
            sets_eliminados = sets_eliminados_result[0]
            
            logger.info(f"[REINSTALAR_SETS] ✓ Eliminados {sets_eliminados} sets existentes")
        
        # Crear los sets predefinidos
        logger.info(f"[REINSTALAR_SETS] Creando sets predefinidos...")
        resultado = crear_sets_predefinidos_clasificacion(cliente_id)
        
        if 'error' in resultado:
            logger.error(f"[REINSTALAR_SETS] ❌ Error: {resultado['error']}")
            return resultado
        
        mensaje_final = f"Reinstalación completada para {cliente.nombre}: {resultado.get('sets_creados', 0)} sets nuevos, {resultado.get('opciones_creadas', 0)} opciones nuevas"
        if limpiar_existentes:
            mensaje_final += f" (eliminados {sets_eliminados} sets anteriores)"
        
        logger.info(f"[REINSTALAR_SETS] ✅ {mensaje_final}")
        return {
            'exito': True,
            'mensaje': mensaje_final,
            'sets_creados': resultado.get('sets_creados', 0),
            'sets_actualizados': resultado.get('sets_actualizados', 0),
            'opciones_creadas': resultado.get('opciones_creadas', 0),
            'opciones_actualizadas': resultado.get('opciones_actualizadas', 0),
            'sets_eliminados': sets_eliminados,
            'cliente_bilingue': cliente.bilingue
        }
        
    except Exception as e:
        error_msg = f"Error reinstalando sets predefinidos para cliente {cliente_id}: {str(e)}"
        logger.exception(f"[REINSTALAR_SETS] ❌ {error_msg}")
        return {'error': error_msg}

# ==== FUNCIONES DE UTILIDAD PARA GESTIÓN MANUAL ====

def recuperar_sets_clasificacion_cliente(cliente_id, incluir_predefinidos=True, limpiar_existentes=False):
    """
    Función de utilidad para recuperar/reinstalar sets de clasificación para un cliente.
    Puede ser llamada desde Django admin, shell, o endpoints.
    
    Args:
        cliente_id: ID del cliente
        incluir_predefinidos: Si incluir sets predefinidos estándar
        limpiar_existentes: Si eliminar sets existentes antes de crear nuevos
    
    Returns:
        dict con resultado de la operación
    """
    try:
        from .models import Cliente
        
        cliente = Cliente.objects.get(id=cliente_id)
        logger.info(f"Recuperando sets de clasificación para cliente {cliente.nombre} (ID: {cliente_id})")
        
        resultados = {}
        
        # 1. Crear sets desde datos RAW si existen
        try:
            resultado_raw = crear_sets_y_opciones_clasificacion_desde_raw(cliente_id)
            resultados['desde_raw'] = resultado_raw
            logger.info(f"Sets desde RAW: {resultado_raw}")
        except Exception as e:
            resultados['desde_raw'] = {'error': str(e)}
            logger.error(f"Error creando sets desde RAW: {e}")
        
        # 2. Crear sets predefinidos si se solicita
        if incluir_predefinidos:
            try:
                if limpiar_existentes:
                    resultado_predefinidos = reinstalar_sets_predefinidos_clasificacion(cliente_id, limpiar_existentes=True)
                else:
                    resultado_predefinidos = crear_sets_predefinidos_clasificacion(cliente_id)
                resultados['predefinidos'] = resultado_predefinidos
                logger.info(f"Sets predefinidos: {resultado_predefinidos}")
            except Exception as e:
                resultados['predefinidos'] = {'error': str(e)}
                logger.error(f"Error creando sets predefinidos: {e}")
        
        # 3. Resumen final
        total_sets = 0
        total_opciones = 0
        
        if 'desde_raw' in resultados and isinstance(resultados['desde_raw'], str):
            # Parsear resultado tipo string del RAW
            pass
        
        if 'predefinidos' in resultados and 'sets_creados' in resultados['predefinidos']:
            total_sets += resultados['predefinidos']['sets_creados']
            total_opciones += resultados['predefinidos']['opciones_creadas']
        
        mensaje_final = f"Recuperación completada para {cliente.nombre}: {total_sets} sets, {total_opciones} opciones"
        
        return {
            'exito': True,
            'cliente': {'id': cliente.id, 'nombre': cliente.nombre, 'bilingue': cliente.bilingue},
            'mensaje': mensaje_final,
            'detalles': resultados,
            'totales': {'sets': total_sets, 'opciones': total_opciones}
        }
        
    except Cliente.DoesNotExist:
        return {'error': f"Cliente con ID {cliente_id} no encontrado"}
    except Exception as e:
        logger.exception(f"Error recuperando sets para cliente {cliente_id}")
        return {'error': str(e)}
