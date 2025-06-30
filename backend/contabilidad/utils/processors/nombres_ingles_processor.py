import hashlib
import os
import pandas as pd
from django.utils import timezone
from django.core.files.storage import default_storage
from .base_processor import BaseProcessor
from contabilidad.models import (
    CuentaContable,
    NombreIngles,
    NombreInglesArchivo,
    NombresEnInglesUpload,
    UploadLog,
)
from contabilidad.utils.validators.nombres_ingles_validator import validar_archivo_nombres_ingles_excel


class NombresInglesProcessor(BaseProcessor):
    @staticmethod
    def procesar_archivo(cliente_id, path_archivo):
        from contabilidad.utils.parsers.parser_nombre_ingles import procesar_archivo_nombres_ingles
        return procesar_archivo_nombres_ingles(cliente_id, path_archivo)

    @staticmethod
    def procesar_upload(upload_id):
        processor = NombresInglesProcessor()
        try:
            upload = NombresEnInglesUpload.objects.get(id=upload_id)
        except NombresEnInglesUpload.DoesNotExist:
            processor.logger.error("Upload de nombres en inglés con id %s no encontrado", upload_id)
            return
        upload.estado = "procesando"
        upload.save(update_fields=["estado"])
        try:
            archivo_path = upload.archivo.path
            df = pd.read_excel(archivo_path)
            if len(df.columns) < 2:
                raise ValueError("El archivo debe tener al menos 2 columnas: código de cuenta y nombre en inglés")
            columna_codigo = df.columns[0]
            columna_nombre_en = df.columns[1]
            errores = []
            cuentas_actualizadas = 0
            cuentas_no_encontradas = 0
            for _, row in df.iterrows():
                codigo = str(row[columna_codigo]).strip()
                nombre_en = str(row[columna_nombre_en]).strip()
                if not codigo or pd.isna(row[columna_codigo]):
                    continue
                if not nombre_en or pd.isna(row[columna_nombre_en]) or nombre_en.lower() == "nan":
                    continue
                try:
                    cuenta = CuentaContable.objects.get(codigo=codigo, cliente=upload.cliente)
                    cuenta.nombre_en = nombre_en
                    cuenta.save(update_fields=["nombre_en"])
                    cuentas_actualizadas += 1
                except CuentaContable.DoesNotExist:
                    errores.append(f"Cuenta no encontrada: {codigo}")
                    cuentas_no_encontradas += 1
                except Exception as e:
                    errores.append(f"Error al actualizar cuenta {codigo}: {e}")
            resumen = {
                "total_filas": len(df),
                "cuentas_actualizadas": cuentas_actualizadas,
                "cuentas_no_encontradas": cuentas_no_encontradas,
                "errores_count": len(errores),
                "errores": errores[:10],
            }
            upload.estado = "completado"
            upload.resumen = resumen
            upload.errores = ""
            upload.save(update_fields=["estado", "resumen", "errores"])
        except Exception as e:
            processor.logger.exception("Error en procesamiento de nombres en inglés")
            upload.estado = "error"
            upload.errores = str(e)
            upload.resumen = {"error": str(e)}
            upload.save(update_fields=["estado", "errores", "resumen"])

    @staticmethod
    def procesar_con_upload_log(upload_log_id):
        processor = NombresInglesProcessor()
        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            processor.logger.error("UploadLog con id %s no encontrado", upload_log_id)
            return f"Error: UploadLog {upload_log_id} no encontrado"
        upload_log.estado = "procesando"
        upload_log.save(update_fields=["estado"])
        inicio = timezone.now()
        try:
            ruta_relativa = upload_log.ruta_archivo
            if not ruta_relativa:
                upload_log.estado = "error"
                upload_log.errores = "No hay ruta de archivo especificada en el upload_log"
                upload_log.tiempo_procesamiento = timezone.now() - inicio
                upload_log.save()
                return "Error: No hay ruta de archivo especificada"
            ruta_completa = default_storage.path(ruta_relativa)
            with open(ruta_completa, "rb") as f:
                archivo_hash = hashlib.sha256(f.read()).hexdigest()
            upload_log.hash_archivo = archivo_hash
            upload_log.save(update_fields=["hash_archivo"])
            validacion = validar_archivo_nombres_ingles_excel(ruta_completa)
            if not validacion["es_valido"]:
                error_msg = "Archivo inválido: " + "; ".join(validacion["errores"])
                upload_log.estado = "error"
                upload_log.errores = error_msg
                upload_log.tiempo_procesamiento = timezone.now() - inicio
                upload_log.resumen = {"validacion": validacion, "archivo_hash": archivo_hash}
                upload_log.save()
                return f"Error: {error_msg}"
            df = pd.read_excel(ruta_completa, skiprows=1, header=None)
            if len(df.columns) < 2:
                raise ValueError("El archivo debe tener al menos 2 columnas: código y nombre en inglés")
            df.columns = ["cuenta_codigo", "nombre_ingles"] + [f"col_{i}" for i in range(2, len(df.columns))]
            df = df.dropna(subset=["cuenta_codigo", "nombre_ingles"])
            df["cuenta_codigo"] = df["cuenta_codigo"].astype(str).str.strip()
            df["nombre_ingles"] = df["nombre_ingles"].astype(str).str.strip()
            df = df[(df["cuenta_codigo"] != "") & (df["cuenta_codigo"] != "nan") & (df["nombre_ingles"] != "") & (df["nombre_ingles"] != "nan")]
            eliminados = NombreIngles.objects.filter(cliente=upload_log.cliente).count()
            NombreIngles.objects.filter(cliente=upload_log.cliente).delete()
            df = df.drop_duplicates(subset=["cuenta_codigo"], keep="last")
            creados = 0
            errores = []
            for idx, row in df.iterrows():
                try:
                    NombreIngles.objects.update_or_create(
                        cliente=upload_log.cliente,
                        cuenta_codigo=row["cuenta_codigo"],
                        defaults={"nombre_ingles": row["nombre_ingles"]},
                    )
                    creados += 1
                except Exception as e:
                    errores.append(f"Fila {idx + 3}: {e}")
            resumen = {
                "total_filas": len(df),
                "nombres_creados": creados,
                "nombres_eliminados_previos": eliminados,
                "errores_count": len(errores),
                "archivo_hash": archivo_hash,
            }
            upload_log.estado = "completado"
            upload_log.resumen = resumen
            upload_log.errores = "" if not errores else "\n".join(errores[:10])
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            try:
                if os.path.exists(ruta_completa):
                    os.remove(ruta_completa)
            except OSError:
                pass
            return f"Completado: {creados} nombres"
        except Exception as e:
            upload_log.estado = "error"
            upload_log.errores = str(e)
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            processor.logger.exception("Error en procesamiento de nombres en ingles")
            return f"Error: {e}"
