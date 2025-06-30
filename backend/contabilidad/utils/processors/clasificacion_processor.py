from django.utils import timezone
from .base_processor import BaseProcessor
from contabilidad.models import (
    UploadLog,
    ClasificacionCuentaArchivo,
    CuentaContable,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
)
from contabilidad.utils.validators.clasificacion_validator import validar_archivo_clasificacion_excel
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pandas as pd
import os
import hashlib
from datetime import date


class ClasificacionProcessor(BaseProcessor):
    @staticmethod
    def map_clasificaciones(upload_log_id):
        processor = ClasificacionProcessor()
        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            processor.logger.error("UploadLog %s no encontrado", upload_log_id)
            return
        registros_raw = ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log, procesado=False)
        errores = []
        clasificaciones_aplicadas = 0
        cuentas_no_encontradas = 0
        for registro in registros_raw:
            try:
                cuenta = CuentaContable.objects.get(codigo=registro.numero_cuenta, cliente=upload_log.cliente)
                for set_name, valor in registro.clasificaciones.items():
                    if not valor or str(valor).strip() == "":
                        continue
                    set_obj, _ = ClasificacionSet.objects.get_or_create(cliente=upload_log.cliente, nombre=set_name)
                    opcion_obj, _ = ClasificacionOption.objects.get_or_create(set_clas=set_obj, valor=str(valor).strip())
                    AccountClassification.objects.update_or_create(
                        cuenta=cuenta, set_clas=set_obj, defaults={"opcion": opcion_obj}
                    )
                    clasificaciones_aplicadas += 1
                registro.procesado = True
                registro.cuenta_mapeada = cuenta
                registro.fecha_procesado = timezone.now()
                registro.errores_mapeo = ""
                registro.save()
            except CuentaContable.DoesNotExist:
                msg = f"Cuenta no encontrada: {registro.numero_cuenta}"
                errores.append(msg)
                registro.errores_mapeo = msg
                registro.save()
                cuentas_no_encontradas += 1
            except Exception as e:
                msg = f"Error procesando {registro.numero_cuenta}: {e}"
                errores.append(msg)
                registro.errores_mapeo = msg
                registro.save()
        resumen_actual = upload_log.resumen or {}
        resumen_actual.update({
            "mapeo_procesado": True,
            "clasificaciones_aplicadas": clasificaciones_aplicadas,
            "cuentas_no_encontradas": cuentas_no_encontradas,
            "errores_mapeo_count": len(errores),
            "errores_mapeo": errores[:10],
        })
        upload_log.resumen = resumen_actual
        upload_log.save(update_fields=["resumen"])
        processor.logger.info(
            "Mapeo completado: %s clasificaciones aplicadas, %s cuentas no encontradas",
            clasificaciones_aplicadas,
            cuentas_no_encontradas,
        )

    @staticmethod
    def process_upload_log(upload_log_id):
        from contabilidad.models import ClasificacionArchivo
        processor = ClasificacionProcessor()
        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            processor.logger.error("UploadLog %s no encontrado", upload_log_id)
            return f"Error: UploadLog {upload_log_id} no encontrado"
        upload_log.estado = "procesando"
        upload_log.save(update_fields=["estado"])
        inicio = timezone.now()
        ruta_relativa = upload_log.ruta_archivo
        if not ruta_relativa:
            upload_log.estado = "error"
            upload_log.errores = "No hay ruta de archivo especificada"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            return "Error: No hay ruta de archivo especificada"
        ruta_completa = default_storage.path(ruta_relativa)
        if not os.path.exists(ruta_completa):
            upload_log.estado = "error"
            upload_log.errores = f"Archivo temporal no encontrado en: {ruta_relativa}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            return "Error: Archivo temporal no encontrado"
        with open(ruta_completa, "rb") as f:
            contenido = f.read()
            archivo_hash = hashlib.sha256(contenido).hexdigest()
        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])
        validacion = validar_archivo_clasificacion_excel(ruta_completa, upload_log.cliente.id)
        if not validacion['es_valido']:
            upload_log.estado = "error"
            upload_log.errores = "Archivo inválido"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.resumen = {"validacion": validacion, "archivo_hash": archivo_hash}
            upload_log.save()
            return "Error: Archivo inválido"
        df = pd.read_excel(ruta_completa)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas")
        columna_cuentas = df.columns[0]
        sets = list(df.columns[1:])
        ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log).delete()
        registros = 0
        for index, row in df.iterrows():
            numero_cuenta = str(row[columna_cuentas]).strip() if not pd.isna(row[columna_cuentas]) else ""
            if not numero_cuenta:
                continue
            clasif = {}
            for set_name in sets:
                valor = row[set_name]
                if not pd.isna(valor) and str(valor).strip() != "":
                    clasif[set_name] = str(valor).strip()
            ClasificacionCuentaArchivo.objects.create(
                cliente=upload_log.cliente,
                upload_log=upload_log,
                numero_cuenta=numero_cuenta,
                clasificaciones=clasif,
                fila_excel=index + 2,
            )
            registros += 1
        nombre_final = f"clasificacion_cliente_{upload_log.cliente.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        archivo_content = ContentFile(contenido, name=nombre_final)
        archivo_existente, created = ClasificacionArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            defaults={"upload_log": upload_log, "archivo": archivo_content},
        )
        if not created:
            if archivo_existente.archivo:
                archivo_existente.archivo.delete()
            archivo_existente.archivo.save(nombre_final, ContentFile(contenido))
            archivo_existente.upload_log = upload_log
            archivo_existente.fecha_subida = timezone.now()
            archivo_existente.save()
        upload_log.estado = "completado"
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.resumen = {
            "total_filas": len(df),
            "registros_guardados": registros,
            "archivo_hash": archivo_hash,
            "validacion": validacion,
        }
        upload_log.save()
        try:
            os.remove(ruta_completa)
        except OSError:
            pass
        return f"Completado: {registros} registros"

    @staticmethod
    def create_sets_options(upload_log_id):
        processor = ClasificacionProcessor()
        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            processor.logger.error("UploadLog %s no encontrado", upload_log_id)
            return f"Error: UploadLog {upload_log_id} no encontrado"
        registros = ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log)
        if not registros.exists():
            processor.logger.warning("No hay registros de clasificación para upload_log %s", upload_log_id)
            return "Sin registros de clasificación para procesar"
        cliente = upload_log.cliente
        sets_creados = 0
        opciones_creadas = 0
        todos_los_sets = {}
        for registro in registros:
            for set_nombre, valor in (registro.clasificaciones or {}).items():
                if valor and str(valor).strip():
                    todos_los_sets.setdefault(set_nombre, set()).add(str(valor).strip())
        for set_nombre, valores in todos_los_sets.items():
            clasificacion_set, set_created = ClasificacionSet.objects.get_or_create(
                cliente=cliente,
                nombre=set_nombre,
                defaults={
                    "descripcion": f"Set de clasificación generado automáticamente desde archivo: {upload_log.nombre_archivo_original}",
                    "idioma": "es",
                },
            )
            if set_created:
                sets_creados += 1
            for valor in valores:
                _, opcion_created = ClasificacionOption.objects.get_or_create(
                    set_clas=clasificacion_set,
                    valor=valor,
                    defaults={"descripcion": f"Opción generada automáticamente: {valor}", "parent": None},
                )
                if opcion_created:
                    opciones_creadas += 1
        if upload_log.resumen:
            upload_log.resumen.update({
                "sets_creados": sets_creados,
                "opciones_creadas": opciones_creadas,
                "total_sets_procesados": len(todos_los_sets),
            })
        else:
            upload_log.resumen = {
                "sets_creados": sets_creados,
                "opciones_creadas": opciones_creadas,
                "total_sets_procesados": len(todos_los_sets),
            }
        upload_log.save(update_fields=["resumen"])
        processor.logger.info(
            "Completado: Creados %s sets y %s opciones para cliente %s",
            sets_creados,
            opciones_creadas,
            cliente.nombre,
        )
        return f"Completado: {sets_creados} sets y {opciones_creadas} opciones creadas"
