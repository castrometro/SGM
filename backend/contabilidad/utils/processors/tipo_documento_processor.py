import hashlib
import os
from datetime import datetime, timedelta
import pandas as pd
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .base_processor import BaseProcessor
from contabilidad.models import TipoDocumento, TipoDocumentoArchivo, UploadLog
from contabilidad.utils.parsers.parser_tipo_documento import parsear_tipo_documento_excel
from contabilidad.utils.validators.tipo_documento_validator import validar_archivo_tipo_documento_excel
from contabilidad.utils.activity_logger import registrar_actividad_tarjeta


class TipoDocumentoProcessor(BaseProcessor):
    @staticmethod
    def parse_excel(cliente_id, ruta_relativa):
        return parsear_tipo_documento_excel(cliente_id, ruta_relativa)

    @staticmethod
    def procesar_upload_log(upload_log_id):
        processor = TipoDocumentoProcessor()
        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            processor.logger.error("UploadLog con id %s no encontrado", upload_log_id)
            return f"Error: UploadLog {upload_log_id} no encontrado"
        upload_log.estado = "procesando"
        upload_log.save(update_fields=["estado"])
        inicio_procesamiento = timezone.now()
        try:
            es_valido, resultado_validacion = UploadLog.validar_nombre_archivo(
                upload_log.nombre_archivo_original, "TipoDocumento", upload_log.cliente.rut
            )
            if not es_valido:
                upload_log.estado = "error"
                upload_log.errores = f"Nombre de archivo inválido: {resultado_validacion}"
                upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
                upload_log.save()
                registrar_actividad_tarjeta(
                    cliente_id=upload_log.cliente.id,
                    periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                    tarjeta="tipo_documento",
                    accion="process_excel",
                    descripcion=f"Error validación nombre archivo: {resultado_validacion}",
                    usuario=upload_log.usuario,
                    detalles={"upload_log_id": upload_log.id},
                    resultado="error",
                    ip_address=upload_log.ip_usuario,
                )
                return f"Error: {resultado_validacion}"
            ruta_relativa = upload_log.ruta_archivo
            if not ruta_relativa:
                upload_log.estado = "error"
                upload_log.errores = "No hay ruta de archivo especificada en el upload_log"
                upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
                upload_log.save()
                return "Error: No hay ruta de archivo especificada"
            ruta_completa = default_storage.path(ruta_relativa)
            if not os.path.exists(ruta_completa):
                upload_log.estado = "error"
                upload_log.errores = f"Archivo temporal no encontrado en: {ruta_relativa}"
                upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
                upload_log.save()
                registrar_actividad_tarjeta(
                    cliente_id=upload_log.cliente.id,
                    periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                    tarjeta="tipo_documento",
                    accion="process_excel",
                    descripcion="Archivo temporal no encontrado",
                    usuario=upload_log.usuario,
                    detalles={"upload_log_id": upload_log.id},
                    resultado="error",
                    ip_address=upload_log.ip_usuario,
                )
                return "Error: Archivo temporal no encontrado"
            with open(ruta_completa, "rb") as f:
                archivo_hash = hashlib.sha256(f.read()).hexdigest()
            upload_log.hash_archivo = archivo_hash
            upload_log.save(update_fields=["hash_archivo"])
            validacion = validar_archivo_tipo_documento_excel(ruta_completa)
            if not validacion["es_valido"]:
                error_msg = "Archivo inválido: " + "; ".join(validacion["errores"])
                upload_log.estado = "error"
                upload_log.errores = error_msg
                upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
                upload_log.resumen = {"validacion": validacion, "archivo_hash": archivo_hash}
                upload_log.save()
                registrar_actividad_tarjeta(
                    cliente_id=upload_log.cliente.id,
                    periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                    tarjeta="tipo_documento",
                    accion="process_excel",
                    descripcion=f"Validación archivo falló: {len(validacion['errores'])} errores",
                    usuario=upload_log.usuario,
                    detalles={"upload_log_id": upload_log.id, "errores": validacion["errores"]},
                    resultado="error",
                    ip_address=upload_log.ip_usuario,
                )
                return f"Error: {error_msg}"
            ok, msg = parsear_tipo_documento_excel(upload_log.cliente.id, ruta_relativa)
            if not ok:
                upload_log.estado = "error"
                upload_log.errores = f"Error en procesamiento: {msg}"
                upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
                upload_log.save()
                registrar_actividad_tarjeta(
                    cliente_id=upload_log.cliente.id,
                    periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                    tarjeta="tipo_documento",
                    accion="process_excel",
                    descripcion=f"Error en procesamiento: {msg}",
                    usuario=upload_log.usuario,
                    detalles={"upload_log_id": upload_log.id},
                    resultado="error",
                    ip_address=upload_log.ip_usuario,
                )
                return f"Error: {msg}"
            tipos_creados = TipoDocumento.objects.filter(cliente=upload_log.cliente).count()
            archivo_actual, created = TipoDocumentoArchivo.objects.get_or_create(
                cliente=upload_log.cliente,
                defaults={"upload_log": upload_log, "fecha_subida": timezone.now()},
            )
            if not created:
                archivo_actual.upload_log = upload_log
                archivo_actual.fecha_subida = timezone.now()
                archivo_actual.save(update_fields=["upload_log", "fecha_subida"])
            upload_log.estado = "completado"
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.resumen = {"tipos_creados": tipos_creados, "archivo_hash": archivo_hash}
            upload_log.save()
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Procesado archivo de tipos de documento: {tipos_creados} registros",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="exito",
                ip_address=upload_log.ip_usuario,
            )
            return f"Completado: {tipos_creados} tipos"
        except Exception as e:
            upload_log.estado = "error"
            upload_log.errores = str(e)
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Error inesperado en procesamiento: {e}",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id, "error": str(e)},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            processor.logger.exception("Error inesperado en procesamiento")
            return f"Error inesperado: {e}"
