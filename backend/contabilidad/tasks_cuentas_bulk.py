"""
Tasks especializadas para el procesamiento de archivos de clasificación bulk
Refactorizado para usar Celery Chains y distribuir validaciones/procesamiento

FLUJO CORRECTO DE CLASIFICACIÓN:
1. Usuario sube archivo de clasificación (códigos + sets + valores)
2. Se almacenan datos RAW en ClasificacionCuentaArchivo (NO se hace mapeo inmediato)
3. Usuario sube libro mayor -> se crean las CuentaContable
4. Se ejecuta mapeo: mapear_clasificaciones_con_cuentas() 
   - Crea ClasificacionSet y ClasificacionOption desde datos RAW
   - Mapea clasificaciones RAW con CuentaContable existentes
   - Crea AccountClassification con las FK correctas

IMPORTANTE: 
- Durante subida de clasificación NO se crean sets/opciones/mapeos
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
    ClasificacionCuentaArchivo, 
    ClasificacionSet,
    ClasificacionOption,
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
    Task 4: Procesar los datos del Excel y crear registros RAW en BD
    IMPORTANTE: Solo almacena datos RAW, NO hace mapeo con CuentaContable
    El mapeo se realizará posteriormente cuando se suba el libro mayor
    """
    logger.info(f"Procesando datos RAW de clasificación para upload_log_id: {upload_log_id}")
    
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
        # Debug: Test if ClasificacionCuentaArchivo is accessible
        try:
            test_count = ClasificacionCuentaArchivo.objects.count()
            logger.info(f"[DEBUG] Current ClasificacionCuentaArchivo count: {test_count}")
        except Exception as debug_e:
            logger.error(f"[DEBUG] Error accessing ClasificacionCuentaArchivo model: {debug_e}")
        
        ruta_completa = default_storage.path(upload_log.ruta_archivo)
        
        # Leer el Excel
        df = pd.read_excel(ruta_completa)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas")

        columna_cuentas = df.columns[0]
        sets = list(df.columns[1:])

        # Debug: Check ClasificacionCuentaArchivo model fields
        model_fields = [f.name for f in ClasificacionCuentaArchivo._meta.get_fields()]
        logger.info(f"[DEBUG] ClasificacionCuentaArchivo model fields: {model_fields}")

        # Limpiar registros anteriores del mismo upload_log
        ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log).delete()

        errores = []
        registros = 0
        filas_vacias = 0

        # Procesar cada fila - SOLO ALMACENAR DATOS RAW
        for index, row in df.iterrows():
            numero_cuenta = (
                str(row[columna_cuentas]).strip()
                if not pd.isna(row[columna_cuentas])
                else ""
            )
            if not numero_cuenta:
                filas_vacias += 1
                continue
                
            # Construir diccionario de clasificaciones (RAW, sin mapeo)
            clasif = {}
            for set_name in sets:
                valor = row[set_name]
                if not pd.isna(valor) and str(valor).strip() != "":
                    clasif[set_name] = str(valor).strip()
                    
            try:
                # Debug: Log the data being created
                logger.debug(f"Creando registro para cuenta {numero_cuenta}, clasificaciones: {clasif}")
                
                # Crear registro RAW - numero_cuenta es string, NO FK
                # Explicitly create with only the expected fields
                registro = ClasificacionCuentaArchivo(
                    cliente=upload_log.cliente,
                    upload_log=upload_log,
                    numero_cuenta=numero_cuenta,  # String, no FK
                    clasificaciones=clasif,       # JSON con set_name -> valor
                    fila_excel=index + 2,
                )
                registro.save()
                registros += 1
                logger.debug(f"Registro creado exitosamente para cuenta {numero_cuenta}")
            except Exception as e:
                error_msg = f"Fila {index+2}: {str(e)}"
                logger.error(f"Error creando registro: {error_msg}")
                errores.append(error_msg)

        # Preparar resumen
        resumen_procesamiento = {
            "total_filas": len(df),
            "filas_vacias": filas_vacias,
            "sets_encontrados": sets,
            "registros_guardados": registros,
            "errores_count": len(errores),
            "errores": errores[:10],  # Solo los primeros 10 errores
            "datos_raw": True,  # Indicador de que son datos RAW
            "mapeo_realizado": False,  # Mapeo pendiente
        }

        # Actualizar resumen existente
        if upload_log.resumen:
            upload_log.resumen.update(resumen_procesamiento)
        else:
            upload_log.resumen = resumen_procesamiento
            
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save(update_fields=['resumen', 'tiempo_procesamiento'])
        
        logger.info(f"Datos RAW procesados para upload_log {upload_log_id}: {registros} registros almacenados")
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
            resultado_predefinidos = crear_sets_predefinidos_clasificacion(upload_log.cliente.id)
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
    Task para mapear las clasificaciones RAW con las cuentas reales después de la subida del libro mayor.
    Esta función se debe llamar DESPUÉS de procesar el libro mayor cuando ya existen las CuentaContable.
    """
    logger.info(f"Iniciando mapeo de clasificaciones RAW para upload_log {upload_log_id}")

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

    # 2) Obtener RAW pendientes
    from contabilidad.models import ClasificacionCuentaArchivo, CuentaContable, AccountClassification
    registros_raw = ClasificacionCuentaArchivo.objects.filter(cliente=cliente)
    if not registros_raw.exists():
        msg = f"[mapear_clasificaciones] No hay clasificaciones RAW para cliente {cliente_id}."
        logger.info(msg)
        return {'info': msg}

    # 3) Construir diccionario de cuentas
    cuentas_dict = {c.codigo: c for c in CuentaContable.objects.filter(cliente=cliente)}
    if not cuentas_dict:
        msg = f"[mapear_clasificaciones] No hay cuentas creadas para cliente {cliente_id} (sube el libro mayor primero)."
        logger.warning(msg)
        return {'warning': msg}

    # 4) Crear sets y opciones
    resultado_sets = crear_sets_y_opciones_clasificacion_desde_raw(cliente_id)
    logger.info(f"[mapear_clasificaciones] Resultado creación sets: {resultado_sets}")

    # 5) Hacer el mapeo
    mapeos_exitosos = 0
    cuentas_no_encontradas = 0
    errores_mapeo = []

    for registro in registros_raw:
        try:
            cuenta = cuentas_dict.get(registro.numero_cuenta)
            if not cuenta:
                cuentas_no_encontradas += 1
                continue

            for set_nombre, valor in (registro.clasificaciones or {}).items():
                if not valor or not str(valor).strip():
                    continue

                from contabilidad.models import ClasificacionSet, ClasificacionOption

                clasificacion_set = ClasificacionSet.objects.filter(
                    cliente=cliente, nombre=set_nombre
                ).first()
                if not clasificacion_set:
                    logger.warning(f"Set no encontrado: {set_nombre}")
                    continue

                opcion = ClasificacionOption.objects.filter(
                    set_clas=clasificacion_set, valor=str(valor).strip()
                ).first()
                if not opcion:
                    logger.warning(f"Opción no encontrada: '{valor}' en set '{set_nombre}'")
                    continue

                # Creamos o actualizamos
                obj, created = AccountClassification.objects.update_or_create(
                    cuenta=cuenta, set_clas=clasificacion_set,
                    defaults={'opcion': opcion, 'asignado_por': None}
                )
                if created:
                    mapeos_exitosos += 1

            # registro procesado (ya no necesitamos marcar como procesado)
            pass

        except Exception as e:
            errores_mapeo.append(f"Registro {registro.id}: {e}")
            logger.error(f"[mapear_clasificaciones] Error en registro {registro.id}: {e}")

    # 6) Registrar actividad
    from contabilidad.utils.activity_logger import registrar_actividad_tarjeta
    periodo = cierre.periodo or date.today().strftime("%Y-%m")
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo,
        tarjeta="clasificacion",
        accion="mapeo_clasificaciones",
        descripcion=(
            f"Mapeo completado: {mapeos_exitosos} mapeos, "
            f"{cuentas_no_encontradas} cuentas no encontradas, "
            f"{len(errores_mapeo)} errores"
        ),
        usuario=None,
        detalles={
            "mapeos_exitosos": mapeos_exitosos,
            "cuentas_no_encontradas": cuentas_no_encontradas,
            "errores_mapeo": errores_mapeo,
            "registros_procesados": registros_raw.count(),
            "cierre_id": cierre.id,
        },
        resultado="exito" if not errores_mapeo else "parcial",
        ip_address=None,
    )

    return {
        "mapeos_exitosos": mapeos_exitosos,
        "cuentas_no_encontradas": cuentas_no_encontradas,
        "errores_mapeo": errores_mapeo,
    }

@shared_task(name='contabilidad.crear_sets_y_opciones_clasificacion_desde_raw')
def crear_sets_y_opciones_clasificacion_desde_raw(cliente_id):
    """
    Crea automáticamente ClasificacionSet y ClasificacionOption basado en 
    los datos RAW de clasificación almacenados para un cliente.
    Se ejecuta durante el mapeo, no durante la subida inicial.
    """
    logger.info(f"Creando sets y opciones desde datos RAW para cliente {cliente_id}")
    
    try:
        from .models import Cliente
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            msg = f"[crear_sets_y_opciones] Cliente con id={cliente_id} no existe. Se omite creación de sets."
            logger.error(msg)
            return {'error': msg}
        
        # Obtener todos los registros RAW del cliente
        registros_clasificacion = ClasificacionCuentaArchivo.objects.filter(
            cliente=cliente
        )
        
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
def crear_sets_predefinidos_clasificacion(cliente_id):
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
                    {'valor': 'Gross Earnings', 'descripcion': 'Gross Earnings', 'valor_en': 'Gross Earnings', 'descripcion_en': 'Gross earnings'},
                    {'valor': 'Earnings (Loss)', 'descripcion': 'Earnings (Loss)', 'valor_en': 'Earnings (Loss)', 'descripcion_en': 'Earnings (Loss)'},
                    {'valor': 'Earnings (Loss) Before Taxes', 'descripcion': 'Earnings (Loss) Before Taxes', 'valor_en': 'Earnings (Loss) Before Taxes', 'descripcion_en': 'Earnings (Loss) before taxes'},

                ]
            },
        }
        
        logger.info(f"[SETS_PREDEFINIDOS] Creando {len(sets_predefinidos)} sets predefinidos (sets únicos con opciones bilingües)...")
        
        # Crear sets y opciones
        for set_nombre, set_info in sets_predefinidos.items():
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
