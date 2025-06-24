# backend/contabilidad/tasks.py
import hashlib
import logging
import os
import re
import time
from datetime import date

import pandas as pd
from celery import shared_task
from contabilidad.models import (
    AccountClassification,
    ClasificacionCuentaArchivo,
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    LibroMayorUpload,
    MovimientoContable,
    NombreIngles,
    NombreInglesArchivo,
    NombresEnInglesUpload,
    TipoDocumento,
    UploadLog,
)
from contabilidad.utils.parser_libro_mayor import parsear_libro_mayor
from contabilidad.utils.parser_nombre_ingles import procesar_archivo_nombres_ingles
from contabilidad.utils.parser_tipo_documento import parsear_tipo_documento_excel
from contabilidad.utils.activity_logger import registrar_actividad_tarjeta
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def tarea_de_prueba(nombre):
    logger.info("👋 ¡Hola %s desde Celery!", nombre)
    time.sleep(999)
    logger.info("✅ Tarea completada.")
    return f"Completado por {nombre}"  # esto sale en succeeded


@shared_task
def parsear_tipo_documento(cliente_id, ruta_relativa):
    ok, msg = parsear_tipo_documento_excel(cliente_id, ruta_relativa)
    if ok:
        logger.info("✅ %s", msg)
    else:
        logger.error("❌ %s", msg)
    return msg


@shared_task
def procesar_libro_mayor(libro_mayor_id):
    logger.info(
        f"Iniciando procesamiento de libro mayor para upload_id: {libro_mayor_id}"
    )

    try:
        libro = LibroMayorUpload.objects.get(id=libro_mayor_id)
    except LibroMayorUpload.DoesNotExist:
        logger.error(f"Libro mayor con id {libro_mayor_id} no encontrado")
        return

    cierre = libro.cierre
    cliente = cierre.cliente
    ruta = libro.archivo.path

    # 1. Al iniciar: Procesando
    libro.estado = "procesando"
    libro.save()
    cierre.estado = "procesando"
    cierre.save(update_fields=["estado"])

    try:
        logger.info(f"Procesando libro mayor para cliente {cliente.nombre}")

        # Verificar prerequisitos
        tipos_documento = TipoDocumento.objects.filter(cliente=cliente)
        clasificaciones_disponibles = AccountClassification.objects.filter(
            cuenta__cliente=cliente
        ).exists()

        logger.info(
            f"Prerequisitos - Tipos de documento: {tipos_documento.count()}, "
            f"Clasificaciones: {'Sí' if clasificaciones_disponibles else 'No'}"
        )

        # Procesar archivo con toda la información disponible
        errores, fecha_inicio, fecha_fin, resumen = parsear_libro_mayor_completo(
            ruta, libro, tipos_documento, clasificaciones_disponibles
        )

        libro.estado = "completado" if not errores else "error"
        libro.errores = "\n".join(errores) if errores else ""
        libro.save()

        # Actualiza fechas en el cierre
        if fecha_inicio:
            cierre.fecha_inicio_libro = fecha_inicio
        if fecha_fin:
            cierre.fecha_fin_libro = fecha_fin

        cierre.cuentas_nuevas = resumen.get("cuentas_nuevas", 0)
        cierre.resumen_parsing = resumen
        cierre.parsing_completado = True

        # 2. Estado final basado en resultados
        if errores:
            cierre.estado = "error"
            logger.error(f"Procesamiento completado con errores: {len(errores)}")
        else:
            cierre.estado = "completo"
            logger.info(
                f"Procesamiento completado exitosamente. "
                f"Movimientos procesados: {resumen.get('movimientos_procesados', 0)}"
            )

        cierre.save(
            update_fields=[
                "fecha_inicio_libro",
                "fecha_fin_libro",
                "cuentas_nuevas",
                "resumen_parsing",
                "parsing_completado",
                "estado",
            ]
        )

    except Exception as e:
        logger.exception("Error en procesamiento de libro mayor")
        libro.estado = "error"
        libro.errores = str(e)
        libro.save()
        cierre.estado = "error"
        cierre.save(update_fields=["estado"])


@shared_task
def procesar_nombres_ingles(cliente_id, path_archivo):
    actualizados = procesar_archivo_nombres_ingles(cliente_id, path_archivo)
    # Borra archivo temporal
    try:
        os.remove(path_archivo)
    except Exception:
        pass
    return actualizados


@shared_task
def procesar_mapeo_clasificaciones(upload_log_id):
    """Mapea los registros RAW a las cuentas reales usando UploadLog"""
    logger.info(
        f"Iniciando mapeo de clasificaciones para upload_log_id: {upload_log_id}"
    )

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return

    registros_raw = ClasificacionCuentaArchivo.objects.filter(
        upload_log=upload_log, procesado=False
    )

    errores = []
    clasificaciones_aplicadas = 0
    cuentas_no_encontradas = 0

    for registro in registros_raw:
        try:
            # Buscar la cuenta real
            cuenta = CuentaContable.objects.get(
                codigo=registro.numero_cuenta, cliente=upload_log.cliente
            )

            # Aplicar cada clasificación del registro
            for set_name, valor in registro.clasificaciones.items():
                if not valor or str(valor).strip() == "":
                    continue

                # Obtener o crear set y opción
                set_obj, created_set = ClasificacionSet.objects.get_or_create(
                    cliente=upload_log.cliente, nombre=set_name
                )
                if created_set:
                    logger.info(f"Creado nuevo set: {set_name}")

                opcion_obj, created_opcion = ClasificacionOption.objects.get_or_create(
                    set_clas=set_obj, valor=str(valor).strip()
                )
                if created_opcion:
                    logger.info(f"Creada nueva opción: {valor} para set {set_name}")

                # Aplicar clasificación
                clasificacion, created = AccountClassification.objects.update_or_create(
                    cuenta=cuenta, set_clas=set_obj, defaults={"opcion": opcion_obj}
                )
                if created:
                    clasificaciones_aplicadas += 1

            # Marcar como procesado y guardar referencia a la cuenta
            registro.procesado = True
            registro.cuenta_mapeada = cuenta
            registro.fecha_procesado = timezone.now()
            registro.errores_mapeo = ""
            registro.save()

        except CuentaContable.DoesNotExist:
            error_msg = f"Cuenta no encontrada: {registro.numero_cuenta}"
            errores.append(error_msg)
            registro.errores_mapeo = error_msg
            registro.save()
            cuentas_no_encontradas += 1

        except Exception as e:
            error_msg = f"Error procesando {registro.numero_cuenta}: {str(e)}"
            errores.append(error_msg)
            registro.errores_mapeo = error_msg
            registro.save()

    # Actualizar resumen del upload
    resumen_actual = upload_log.resumen or {}
    resumen_actual.update(
        {
            "mapeo_procesado": True,
            "clasificaciones_aplicadas": clasificaciones_aplicadas,
            "cuentas_no_encontradas": cuentas_no_encontradas,
            "errores_mapeo_count": len(errores),
            "errores_mapeo": errores[:10],
        }
    )

    upload_log.resumen = resumen_actual
    upload_log.save(update_fields=["resumen"])

    logger.info(
        f"Mapeo completado: {clasificaciones_aplicadas} clasificaciones aplicadas, {cuentas_no_encontradas} cuentas no encontradas"
    )


@shared_task
def procesar_nombres_ingles_upload(upload_id):
    """
    Procesa archivo Excel de nombres en inglés usando el nuevo modelo de upload
    """
    logger.info(
        f"Iniciando procesamiento de nombres en inglés para upload_id: {upload_id}"
    )

    try:
        upload = NombresEnInglesUpload.objects.get(id=upload_id)
    except NombresEnInglesUpload.DoesNotExist:
        logger.error(f"Upload de nombres en inglés con id {upload_id} no encontrado")
        return

    upload.estado = "procesando"
    upload.save(update_fields=["estado"])

    try:
        archivo_path = upload.archivo.path
        logger.info(f"Procesando archivo: {archivo_path}")

        df = pd.read_excel(archivo_path)
        logger.info(f"Archivo Excel leído con {len(df)} filas")

        # Validar columnas (debe tener al menos código y nombre en inglés)
        if len(df.columns) < 2:
            raise ValueError(
                "El archivo debe tener al menos 2 columnas: código de cuenta y nombre en inglés"
            )

        # Tomar las primeras dos columnas: código y nombre en inglés
        columna_codigo = df.columns[0]
        columna_nombre_en = df.columns[1]

        logger.info(
            f"Columnas detectadas - Código: '{columna_codigo}', Nombre en inglés: '{columna_nombre_en}'"
        )

        errores = []
        cuentas_actualizadas = 0
        cuentas_no_encontradas = 0

        for index, row in df.iterrows():
            codigo = str(row[columna_codigo]).strip()
            nombre_en = str(row[columna_nombre_en]).strip()

            if not codigo or pd.isna(row[columna_codigo]):
                continue

            if (
                not nombre_en
                or pd.isna(row[columna_nombre_en])
                or nombre_en.lower() == "nan"
            ):
                continue

            try:
                cuenta = CuentaContable.objects.get(
                    codigo=codigo, cliente=upload.cliente
                )
                cuenta.nombre_en = nombre_en
                cuenta.save(update_fields=["nombre_en"])
                cuentas_actualizadas += 1
                logger.debug(f"Actualizada cuenta {codigo}: {nombre_en}")

            except CuentaContable.DoesNotExist:
                errores.append(f"Cuenta no encontrada: {codigo}")
                cuentas_no_encontradas += 1
                continue
            except Exception as e:
                errores.append(f"Error al actualizar cuenta {codigo}: {str(e)}")
                continue

        resumen = {
            "total_filas": len(df),
            "cuentas_actualizadas": cuentas_actualizadas,
            "cuentas_no_encontradas": cuentas_no_encontradas,
            "errores_count": len(errores),
            "errores": errores[:10],  # Solo primeros 10 errores
        }

        upload.estado = "completado"
        upload.resumen = resumen
        upload.errores = ""  # Limpiar errores previos
        upload.save(update_fields=["estado", "resumen", "errores"])

        logger.info(
            f"Procesamiento completado: {cuentas_actualizadas} cuentas actualizadas, {len(errores)} errores"
        )

    except Exception as e:
        logger.exception("Error en procesamiento de nombres en inglés")
        upload.estado = "error"
        upload.errores = str(e)
        upload.resumen = {"error": str(e)}
        upload.save(update_fields=["estado", "errores", "resumen"])


@shared_task
def procesar_nombres_ingles_con_upload_log(upload_log_id):
    """Procesa archivo de nombres en inglés usando UploadLog"""
    logger.info(
        "Iniciando procesamiento de nombres en inglés para upload_log %s",
        upload_log_id,
    )

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error("UploadLog con id %s no encontrado", upload_log_id)
        return f"Error: UploadLog {upload_log_id} no encontrado"

    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    inicio = timezone.now()

    try:
        ruta_relativa = (
            f"temp/nombres_ingles_cliente_{upload_log.cliente.id}_{upload_log.id}.xlsx"
        )
        ruta_completa = default_storage.path(ruta_relativa)

        # Calcular hash del archivo para registrarlo en el UploadLog
        with open(ruta_completa, "rb") as f:
            archivo_hash = hashlib.sha256(f.read()).hexdigest()

        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])

        df = pd.read_excel(ruta_completa, skiprows=1, header=None)
        if len(df.columns) < 2:
            raise ValueError(
                "El archivo debe tener al menos 2 columnas: código y nombre en inglés"
            )

        df.columns = ["cuenta_codigo", "nombre_ingles"] + [
            f"col_{i}" for i in range(2, len(df.columns))
        ]

        df = df.dropna(subset=["cuenta_codigo", "nombre_ingles"])
        df["cuenta_codigo"] = df["cuenta_codigo"].astype(str).str.strip()
        df["nombre_ingles"] = df["nombre_ingles"].astype(str).str.strip()
        df = df[
            (df["cuenta_codigo"] != "")
            & (df["cuenta_codigo"] != "nan")
            & (df["nombre_ingles"] != "")
            & (df["nombre_ingles"] != "nan")
        ]

        eliminados = NombreIngles.objects.filter(cliente=upload_log.cliente).count()
        NombreIngles.objects.filter(cliente=upload_log.cliente).delete()

        # Eliminar duplicados manteniendo el último registro de cada código
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
                errores.append(f"Fila {idx + 3}: {str(e)}")

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
        logger.exception("Error en procesamiento de nombres en ingles")
        return f"Error: {str(e)}"


def parsear_libro_mayor_completo(
    ruta_archivo, libro_upload, tipos_documento, usar_clasificaciones
):
    """
    Versión mejorada de parsear_libro_mayor que integra tipos de documento y clasificaciones
    """
    logger.info(f"Iniciando parseo completo del libro mayor: {ruta_archivo}")

    try:
        df = pd.read_excel(ruta_archivo)
        logger.info(f"Archivo Excel leído con {len(df)} filas")

        errores = []
        cierre = libro_upload.cierre
        cliente = cierre.cliente

        # Obtener mapeo de tipos de documento
        tipos_doc_map = {}
        if tipos_documento.exists():
            for tipo_doc in tipos_documento:
                tipos_doc_map[tipo_doc.codigo] = tipo_doc
            logger.info(f"Tipos de documento disponibles: {len(tipos_doc_map)}")

        # Obtener clasificaciones existentes
        clasificaciones_map = {}
        if usar_clasificaciones:
            clasificaciones = AccountClassification.objects.filter(
                cuenta__cliente=cliente
            ).select_related("cuenta", "set_clas", "opcion")
            for clasificacion in clasificaciones:
                codigo_cuenta = clasificacion.cuenta.codigo
                if codigo_cuenta not in clasificaciones_map:
                    clasificaciones_map[codigo_cuenta] = {}
                clasificaciones_map[codigo_cuenta][
                    clasificacion.set_clas.nombre
                ] = clasificacion.opcion.valor
            logger.info(
                f"Clasificaciones disponibles para {len(clasificaciones_map)} cuentas"
            )

        # Procesar movimientos
        movimientos_procesados = 0
        cuentas_nuevas = 0
        incidencias_generadas = 0
        fecha_inicio = None
        fecha_fin = None

        for index, row in df.iterrows():
            try:
                # Extraer datos básicos del movimiento
                codigo_cuenta = str(row.get("Codigo_Cuenta", "")).strip()
                fecha_mov = pd.to_datetime(row.get("Fecha", ""), errors="coerce")
                monto = pd.to_numeric(row.get("Monto", 0), errors="coerce")
                tipo_documento_codigo = str(row.get("Tipo_Documento", "")).strip()

                if not codigo_cuenta or pd.isna(fecha_mov) or pd.isna(monto):
                    errores.append(f"Fila {index + 2}: Datos incompletos")
                    continue

                # Actualizar rango de fechas
                if fecha_inicio is None or fecha_mov < fecha_inicio:
                    fecha_inicio = fecha_mov
                if fecha_fin is None or fecha_mov > fecha_fin:
                    fecha_fin = fecha_mov

                # Obtener o crear cuenta contable
                cuenta, created = CuentaContable.objects.get_or_create(
                    cliente=cliente,
                    codigo=codigo_cuenta,
                    defaults={"nombre": f"Cuenta {codigo_cuenta}"},
                )
                if created:
                    cuentas_nuevas += 1
                    logger.info(f"Nueva cuenta creada: {codigo_cuenta}")

                # Crear movimiento contable
                movimiento = MovimientoContable.objects.create(
                    cierre=cierre,
                    cuenta=cuenta,
                    fecha=fecha_mov,
                    debe=monto if monto > 0 else 0,
                    haber=abs(monto) if monto < 0 else 0,
                    descripcion=str(row.get("Descripcion", "")),
                    referencia=str(row.get("Referencia", "")),
                )

                # Aplicar tipo de documento si existe
                if tipo_documento_codigo and tipo_documento_codigo in tipos_doc_map:
                    tipo_doc = tipos_doc_map[tipo_documento_codigo]
                    # Aquí puedes agregar lógica específica según el tipo de documento
                    logger.debug(f"Tipo de documento aplicado: {tipo_doc.nombre}")

                # Aplicar clasificaciones si existen
                if codigo_cuenta in clasificaciones_map:
                    clasificaciones_cuenta = clasificaciones_map[codigo_cuenta]
                    logger.debug(
                        f"Clasificaciones aplicadas para {codigo_cuenta}: {clasificaciones_cuenta}"
                    )

                movimientos_procesados += 1

            except Exception as e:
                error_msg = f"Fila {index + 2}: Error al procesar - {str(e)}"
                errores.append(error_msg)
                logger.error(error_msg)
                continue

        # Generar incidencias si hay problemas
        if errores:
            from .models import Incidencia

            Incidencia.objects.create(
                cierre=cierre,
                tipo="error_procesamiento",
                descripcion=f"Errores en procesamiento del libro mayor: {len(errores)} errores encontrados",
                detalle={"errores": errores[:10]},  # Solo primeros 10
            )
            incidencias_generadas += 1

        resumen = {
            "movimientos_procesados": movimientos_procesados,
            "cuentas_nuevas": cuentas_nuevas,
            "incidencias_generadas": incidencias_generadas,
            "tipos_documento_aplicados": len(tipos_doc_map),
            "cuentas_con_clasificacion": len(clasificaciones_map),
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "total_filas_procesadas": len(df),
        }

        logger.info(f"Parseo completado: {resumen}")
        return errores, fecha_inicio, fecha_fin, resumen

    except Exception as e:
        logger.exception("Error en parseo completo del libro mayor")
        return [f"Error crítico en procesamiento: {str(e)}"], None, None, {}


@shared_task
def limpiar_archivos_temporales_antiguos_task():
    """
    Tarea Celery para limpiar archivos temporales antiguos (>24h)
    """
    from contabilidad.views import limpiar_archivos_temporales_antiguos

    archivos_eliminados = limpiar_archivos_temporales_antiguos()
    logger.info(
        f"🧹 Limpieza automática: {archivos_eliminados} archivos temporales eliminados"
    )
    return f"Eliminados {archivos_eliminados} archivos temporales"


@shared_task
def parsear_nombres_ingles(cliente_id, ruta_relativa):
    """
    Parsea archivo Excel de nombres en inglés y los guarda en la base de datos
    """
    import os

    import pandas as pd
    from api.models import Cliente
    from django.core.files.storage import default_storage

    logger.info(
        f"Iniciando procesamiento de nombres en inglés para cliente {cliente_id}"
    )

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        logger.error(f"Cliente con id {cliente_id} no encontrado")
        return "Error: Cliente no encontrado"

    try:
        # Obtener ruta completa del archivo
        ruta_completa = default_storage.path(ruta_relativa)
        logger.info(f"Procesando archivo: {ruta_completa}")

        # Leer archivo Excel con estructura fija:
        # Columna 1 (índice 0): código de cuenta
        # Columna 2 (índice 1): nombre en inglés
        # Los datos comienzan desde la fila 2 (skiprows=1)
        df = pd.read_excel(ruta_completa, skiprows=1, header=None)
        logger.info(
            f"Archivo Excel leído con {len(df)} filas de datos y {len(df.columns)} columnas"
        )

        # Validar que tenga al menos 2 columnas
        if len(df.columns) < 2:
            logger.error(
                "El archivo debe tener al menos 2 columnas: código de cuenta y nombre en inglés"
            )
            return "Error: El archivo debe tener al menos 2 columnas"

        # Asignar nombres estándar a las columnas
        df.columns = ["cuenta_codigo", "nombre_ingles"] + [
            f"col_{i}" for i in range(2, len(df.columns))
        ]
        logger.info(
            f"Usando columna 0 como código de cuenta y columna 1 como nombre en inglés"
        )

        # Filtrar filas válidas (sin NaN en campos requeridos)
        df_procesado = df.dropna(subset=["cuenta_codigo", "nombre_ingles"])

        # Limpiar datos
        df_procesado["cuenta_codigo"] = (
            df_procesado["cuenta_codigo"].astype(str).str.strip()
        )
        df_procesado["nombre_ingles"] = (
            df_procesado["nombre_ingles"].astype(str).str.strip()
        )

        # Filtrar filas vacías después de limpiar
        df_procesado = df_procesado[
            (df_procesado["cuenta_codigo"] != "")
            & (df_procesado["cuenta_codigo"] != "nan")
            & (df_procesado["nombre_ingles"] != "")
            & (df_procesado["nombre_ingles"] != "nan")
        ]

        logger.info(f"Filas válidas después del procesamiento: {len(df_procesado)}")

        # Eliminar nombres en inglés existentes para este cliente antes de insertar nuevos
        nombres_eliminados = NombreIngles.objects.filter(cliente=cliente).count()
        NombreIngles.objects.filter(cliente=cliente).delete()
        logger.info(f"Eliminados {nombres_eliminados} nombres en inglés existentes")

        # Insertar nuevos registros
        nombres_creados = []
        errores = []

        for idx, row in df_procesado.iterrows():
            try:
                nombre_ingles = NombreIngles.objects.create(
                    cliente=cliente,
                    cuenta_codigo=row["cuenta_codigo"],
                    nombre_ingles=row["nombre_ingles"],
                )
                nombres_creados.append(nombre_ingles)

            except Exception as e:
                # Sumar 3 porque: idx empieza en 0 + 1 fila de header saltada + 1 para base-1 = fila real en Excel
                error_msg = f"Error en fila {idx + 3}: {str(e)}"
                errores.append(error_msg)
                logger.warning(error_msg)

        # Guardar archivo procesado en el modelo NombreInglesArchivo
        try:
            # Eliminar archivo anterior si existe
            archivo_anterior = NombreInglesArchivo.objects.filter(
                cliente=cliente
            ).first()
            if archivo_anterior:
                if archivo_anterior.archivo and os.path.exists(
                    archivo_anterior.archivo.path
                ):
                    os.remove(archivo_anterior.archivo.path)
                archivo_anterior.delete()

            # Crear nuevo registro de archivo
            with open(ruta_completa, "rb") as f:
                from django.core.files.base import ContentFile

                contenido = f.read()
                archivo_final = ContentFile(
                    contenido, name=f"nombres_ingles_{cliente.id}.xlsx"
                )

                NombreInglesArchivo.objects.create(
                    cliente=cliente, archivo=archivo_final
                )

        except Exception as e:
            logger.warning(f"Error al guardar archivo procesado: {str(e)}")

        # Limpiar archivo temporal
        try:
            if os.path.exists(ruta_completa):
                os.remove(ruta_completa)
                logger.info("Archivo temporal eliminado")
        except OSError as e:
            logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

        # Registrar actividad exitosa
        from datetime import date

        from .utils.activity_logger import registrar_actividad_tarjeta

        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="nombres_ingles",
            accion="process_excel",
            descripcion=f"Procesado archivo: {len(nombres_creados)} nombres en inglés creados",
            usuario=None,  # Tarea automática
            detalles={
                "total_creados": len(nombres_creados),
                "total_errores": len(errores),
                "nombres_eliminados_anteriores": nombres_eliminados,
                "errores": errores[:10] if errores else [],  # Solo primeros 10 errores
            },
            resultado="exito",
            ip_address=None,
        )

        mensaje_final = f"✅ Procesamiento completado: {len(nombres_creados)} nombres en inglés creados"
        if errores:
            mensaje_final += f", {len(errores)} errores encontrados"

        logger.info(mensaje_final)
        return mensaje_final

    except Exception as e:
        error_msg = f"❌ Error al procesar nombres en inglés: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Registrar error
        from datetime import date

        from .utils.activity_logger import registrar_actividad_tarjeta

        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="nombres_ingles",
            accion="process_excel",
            descripcion=f"Error al procesar archivo de nombres en inglés: {str(e)}",
            usuario=None,  # Tarea automática
            detalles={"error": str(e), "archivo": ruta_relativa},
            resultado="error",
            ip_address=None,
        )

        return error_msg


@shared_task
def procesar_tipo_documento_con_upload_log(upload_log_id):
    """
    Nuevo task que procesa tipo documento usando el sistema UploadLog unificado
    """
    import hashlib
    import os
    from datetime import datetime, timedelta

    from api.models import Cliente
    from contabilidad.models import TipoDocumento, TipoDocumentoArchivo, UploadLog
    from contabilidad.utils.parser_tipo_documento import parsear_tipo_documento_excel
    from django.utils import timezone

    logger.info(
        f"Iniciando procesamiento de tipo documento para upload_log_id: {upload_log_id}"
    )

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return f"Error: UploadLog {upload_log_id} no encontrado"

    # Marcar como procesando
    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    inicio_procesamiento = timezone.now()

    try:
        # 1. VALIDAR NOMBRE DE ARCHIVO
        logger.info(
            f"Validando nombre de archivo: {upload_log.nombre_archivo_original}"
        )
        es_valido, resultado_validacion = UploadLog.validar_nombre_archivo(
            upload_log.nombre_archivo_original, "TipoDocumento", upload_log.cliente.rut
        )

        if not es_valido:
            upload_log.estado = "error"
            upload_log.errores = f"Nombre de archivo inválido: {resultado_validacion}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(f"Validación de nombre falló: {resultado_validacion}")
            
            # Registrar actividad de error usando información del upload_log
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Error validación nombre archivo: {resultado_validacion}",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return f"Error: {resultado_validacion}"

        logger.info(f"Nombre de archivo válido: {resultado_validacion}")

        # 2. VERIFICAR QUE NO EXISTAN DATOS PREVIOS
        tipos_existentes = TipoDocumento.objects.filter(
            cliente=upload_log.cliente
        ).count()
        if tipos_existentes > 0:
            upload_log.estado = "error"
            upload_log.errores = (
                f"Ya existen {tipos_existentes} tipos de documento para este cliente"
            )
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.resumen = {
                "tipos_existentes": tipos_existentes,
                "accion_requerida": "Eliminar tipos existentes antes de procesar",
            }
            upload_log.save()
            logger.error(f"Cliente ya tiene {tipos_existentes} tipos de documento")
            
            # Registrar actividad de error usando información del upload_log
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Error: Cliente ya tiene {tipos_existentes} tipos de documento",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id, "tipos_existentes": tipos_existentes},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return f"Error: Cliente ya tiene tipos de documento existentes"

        # 3. BUSCAR ARCHIVO TEMPORAL (debe haber sido subido previamente)
        # Construir la ruta basada en el upload_log_id (como se guarda en la vista)
        ruta_relativa = (
            f"temp/tipo_doc_cliente_{upload_log.cliente.id}_{upload_log.id}.xlsx"
        )
        ruta_completa = default_storage.path(ruta_relativa)

        if not os.path.exists(ruta_completa):
            upload_log.estado = "error"
            upload_log.errores = f"Archivo temporal no encontrado en: {ruta_relativa}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(f"Archivo temporal no encontrado: {ruta_completa}")
            
            # Registrar actividad de error usando información del upload_log
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion="Archivo temporal no encontrado",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return "Error: Archivo temporal no encontrado"

        # 4. CALCULAR HASH DEL ARCHIVO
        with open(ruta_completa, "rb") as f:
            archivo_hash = hashlib.sha256(f.read()).hexdigest()

        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])

        # 5. PROCESAR ARCHIVO CON PARSER EXISTENTE
        logger.info(f"Procesando archivo con parser existente: {ruta_completa}")
        ok, msg = parsear_tipo_documento_excel(upload_log.cliente.id, ruta_relativa)

        if not ok:
            upload_log.estado = "error"
            upload_log.errores = f"Error en procesamiento: {msg}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
            upload_log.save()
            logger.error(f"Error en parser: {msg}")
            
            # Registrar actividad de error usando información del upload_log
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="process_excel",
                descripcion=f"Error en procesamiento: {msg}",
                usuario=upload_log.usuario,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=upload_log.ip_usuario,
            )
            return f"Error: {msg}"

        # 6. CONTAR TIPOS PROCESADOS
        tipos_creados = TipoDocumento.objects.filter(cliente=upload_log.cliente).count()

        # 7. ACTUALIZAR/CREAR ARCHIVO ACTUAL
        archivo_actual, created = TipoDocumentoArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            defaults={"upload_log": upload_log, "fecha_subida": timezone.now()},
        )

        if not created:
            # Actualizar archivo existente
            archivo_actual.upload_log = upload_log
            archivo_actual.fecha_subida = timezone.now()
            archivo_actual.save()

        # El parser existente ya maneja el guardado del archivo
        # No necesitamos mover manualmente el archivo

        # 8. MARCAR COMO COMPLETADO
        upload_log.estado = "completado"
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.resumen = {
            "tipos_documento_creados": tipos_creados,
            "archivo_hash": archivo_hash,
            "procesamiento_exitoso": True,
            "mensaje_parser": msg,
        }
        upload_log.save()

        # 9. LIMPIAR ARCHIVO TEMPORAL
        try:
            if os.path.exists(ruta_completa):
                os.remove(ruta_completa)
                logger.info("Archivo temporal eliminado")
        except OSError as e:
            logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

        # 10. REGISTRAR ACTIVIDAD EXITOSA usando información del upload_log
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="process_excel",
            descripcion=f"Procesado archivo de tipo documento: {tipos_creados} tipos creados",
            usuario=upload_log.usuario,
            detalles={
                "upload_log_id": upload_log.id,
                "tipos_creados": tipos_creados,
                "archivo_hash": archivo_hash,
            },
            resultado="exito",
            ip_address=upload_log.ip_usuario,
        )

        logger.info(
            f"✅ Procesamiento completado: {tipos_creados} tipos de documento creados"
        )
        return f"Completado: {tipos_creados} tipos de documento procesados"

    except Exception as e:
        # Error inesperado
        upload_log.estado = "error"
        upload_log.errores = f"Error inesperado: {str(e)}"
        upload_log.tiempo_procesamiento = timezone.now() - inicio_procesamiento
        upload_log.save()
        logger.exception(f"Error inesperado en procesamiento: {str(e)}")
        
        # Registrar actividad de error usando información del upload_log
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="process_excel",
            descripcion=f"Error inesperado en procesamiento: {str(e)}",
            usuario=upload_log.usuario,
            detalles={"upload_log_id": upload_log.id, "error": str(e)},
            resultado="error",
            ip_address=upload_log.ip_usuario,
        )
        
        return f"Error inesperado: {str(e)}"


@shared_task
def procesar_clasificacion_con_upload_log(upload_log_id):
    """Procesa archivo de clasificaciones utilizando el sistema UploadLog"""
    import hashlib
    import os
    from datetime import date

    import pandas as pd
    from django.core.files.base import ContentFile
    from django.utils import timezone

    from .models import ClasificacionArchivo, ClasificacionCuentaArchivo, UploadLog
    from .utils.activity_logger import registrar_actividad_tarjeta

    logger.info(
        f"Iniciando procesamiento de clasificacion para upload_log_id: {upload_log_id}"
    )

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return f"Error: UploadLog {upload_log_id} no encontrado"

    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    inicio = timezone.now()

    try:
        es_valido, msg_valid = UploadLog.validar_nombre_archivo(
            upload_log.nombre_archivo_original, "Clasificacion", upload_log.cliente.rut
        )

        if not es_valido:
            upload_log.estado = "error"
            upload_log.errores = f"Nombre de archivo inválido: {msg_valid}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            logger.error(f"Validación de nombre falló: {msg_valid}")
            
            # Usar el período del cierre asociado o el actual como fallback
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="process_excel",
                descripcion=f"Error validación nombre archivo: {msg_valid}",
                usuario=None,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=None,
            )
            return f"Error: {msg_valid}"

        ruta_relativa = (
            f"temp/clasificacion_cliente_{upload_log.cliente.id}_{upload_log.id}.xlsx"
        )
        ruta_completa = default_storage.path(ruta_relativa)

        if not os.path.exists(ruta_completa):
            upload_log.estado = "error"
            upload_log.errores = f"Archivo temporal no encontrado en: {ruta_relativa}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            logger.error(f"Archivo temporal no encontrado: {ruta_completa}")
            
            # Usar el período del cierre asociado o el actual como fallback
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="process_excel",
                descripcion="Archivo temporal no encontrado",
                usuario=None,
                detalles={"upload_log_id": upload_log.id},
                resultado="error",
                ip_address=None,
            )
            return "Error: Archivo temporal no encontrado"

        with open(ruta_completa, "rb") as f:
            contenido = f.read()
            archivo_hash = hashlib.sha256(contenido).hexdigest()

        upload_log.hash_archivo = archivo_hash
        upload_log.save(update_fields=["hash_archivo"])

        # VALIDACIÓN EXHAUSTIVA DEL ARCHIVO
        logger.info(f"Iniciando validación del archivo Excel para upload_log {upload_log.id}")
        validacion = validar_archivo_clasificacion_excel(ruta_completa, upload_log.cliente.id)
        
        if not validacion['es_valido']:
            error_msg = "Archivo inválido: " + "; ".join(validacion['errores'])
            upload_log.estado = "error"
            upload_log.errores = error_msg
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.resumen = {
                'validacion': validacion,
                'archivo_hash': archivo_hash
            }
            upload_log.save()
            
            logger.error(f"Validación falló para upload_log {upload_log.id}: {error_msg}")
            
            # Usar el período del cierre asociado o el actual como fallback
            periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=upload_log.cliente.id,
                periodo=periodo_actividad,
                tarjeta="clasificacion",
                accion="process_excel",
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
            return f"Error: {error_msg}"
        
        # Log de advertencias si las hay
        if validacion['advertencias']:
            logger.warning(f"Advertencias en archivo upload_log {upload_log.id}: {'; '.join(validacion['advertencias'])}")

        nombre_final = f"clasificacion_cliente_{upload_log.cliente.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        archivo_content = ContentFile(contenido, name=nombre_final)
        # Guardar archivo procesado directamente en ClasificacionArchivo

        df = pd.read_excel(ruta_completa)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas")

        columna_cuentas = df.columns[0]
        sets = list(df.columns[1:])

        ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log).delete()

        errores = []
        registros = 0
        filas_vacias = 0

        for index, row in df.iterrows():
            numero_cuenta = (
                str(row[columna_cuentas]).strip()
                if not pd.isna(row[columna_cuentas])
                else ""
            )
            if not numero_cuenta:
                filas_vacias += 1
                continue
            clasif = {}
            for set_name in sets:
                valor = row[set_name]
                if not pd.isna(valor) and str(valor).strip() != "":
                    clasif[set_name] = str(valor).strip()
            try:
                ClasificacionCuentaArchivo.objects.create(
                    cliente=upload_log.cliente,
                    upload_log=upload_log,
                    numero_cuenta=numero_cuenta,
                    clasificaciones=clasif,
                    fila_excel=index + 2,
                )
                registros += 1
            except Exception as e:
                errores.append(f"Fila {index+2}: {str(e)}")

        resumen = {
            "total_filas": len(df),
            "filas_vacias": filas_vacias,
            "sets_encontrados": sets,
            "registros_guardados": registros,
            "errores_count": len(errores),
            "errores": errores[:10],
            "validacion": {
                "errores": validacion['errores'],
                "advertencias": validacion['advertencias'], 
                "estadisticas": validacion['estadisticas']
            }
        }

        archivo_existente, created = ClasificacionArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            defaults={
                "upload_log": upload_log,
                "archivo": ContentFile(contenido, name=nombre_final),
            },
        )
        if not created:
            if archivo_existente.archivo:
                try:
                    archivo_existente.archivo.delete()
                except Exception:
                    pass
            archivo_existente.archivo.save(nombre_final, ContentFile(contenido))
            archivo_existente.upload_log = upload_log
            archivo_existente.fecha_subida = timezone.now()
            archivo_existente.save()

        upload_log.estado = "completado"
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.resumen = resumen | {"archivo_hash": archivo_hash}
        upload_log.save()

        try:
            os.remove(ruta_completa)
        except OSError:
            pass

        # Usar el período del cierre asociado o el actual como fallback
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")

        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="process_excel",
            descripcion=f"Procesado archivo de clasificacion: {registros} registros",
            usuario=None,
            detalles={"upload_log_id": upload_log.id, "errores": len(errores)},
            resultado="exito",
            ip_address=None,
        )

        # Crear sets y opciones de clasificación automáticamente
        logger.info(f"Iniciando creación automática de sets y opciones para upload_log {upload_log.id}")
        crear_sets_y_opciones_clasificacion.delay(upload_log.id)

        return f"Completado: {registros} registros"

    except Exception as e:
        upload_log.estado = "error"
        upload_log.errores = str(e)
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save()
        
        # Usar el período del cierre asociado o el actual como fallback
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="process_excel",
            descripcion=f"Error al procesar archivo de clasificacion: {str(e)}",
            usuario=None,
            detalles={"upload_log_id": upload_log.id},
            resultado="error",
            ip_address=None,
        )
        logger.exception("Error en procesamiento de clasificacion")
        return f"Error: {str(e)}"


@shared_task
def crear_sets_y_opciones_clasificacion(upload_log_id):
    """
    Crea automáticamente ClasificacionSet y ClasificacionOption basado en 
    los datos de clasificación encontrados en el archivo subido
    """
    from .utils.activity_logger import registrar_actividad_tarjeta
    
    logger.info(f"Iniciando creación de sets y opciones para upload_log_id: {upload_log_id}")
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        return f"Error: UploadLog {upload_log_id} no encontrado"
    
    try:
        # Obtener todos los registros de clasificación de este upload
        registros_clasificacion = ClasificacionCuentaArchivo.objects.filter(
            upload_log=upload_log
        )
        
        if not registros_clasificacion.exists():
            logger.warning(f"No hay registros de clasificación para upload_log {upload_log_id}")
            return "Sin registros de clasificación para procesar"
        
        cliente = upload_log.cliente
        sets_creados = 0
        opciones_creadas = 0
        
        # Extraer todos los sets y valores únicos
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
                    'descripcion': f'Set de clasificación generado automáticamente desde archivo: {upload_log.nombre_archivo_original}',
                    'idioma': 'es'  # Default a español, se puede ajustar según necesidades
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
                        'parent': None  # Por ahora creamos opciones planas, se puede mejorar para detectar jerarquías
                    }
                )
                
                if opcion_created:
                    opciones_creadas += 1
        
        # Actualizar el resumen del upload_log
        if upload_log.resumen:
            upload_log.resumen.update({
                'sets_creados': sets_creados,
                'opciones_creadas': opciones_creadas,
                'total_sets_procesados': len(todos_los_sets)
            })
        else:
            upload_log.resumen = {
                'sets_creados': sets_creados,
                'opciones_creadas': opciones_creadas,
                'total_sets_procesados': len(todos_los_sets)
            }
        
        upload_log.save(update_fields=['resumen'])
        
        # Usar el período del cierre asociado o el actual como fallback
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="create_sets_options",
            descripcion=f"Creados {sets_creados} sets y {opciones_creadas} opciones de clasificación",
            usuario=None,
            detalles={
                "upload_log_id": upload_log.id,
                "sets_creados": sets_creados,
                "opciones_creadas": opciones_creadas,
                "sets_names": list(todos_los_sets.keys())
            },
            resultado="exito",
            ip_address=None,
        )
        
        logger.info(f"Completado: Creados {sets_creados} sets y {opciones_creadas} opciones para cliente {cliente.nombre}")
        return f"Completado: {sets_creados} sets y {opciones_creadas} opciones creadas"
        
    except Exception as e:
        logger.exception(f"Error creando sets y opciones para upload_log {upload_log_id}: {str(e)}")
        
        # Usar el período del cierre asociado o el actual como fallback
        periodo_actividad = upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m")
        
        # Registrar error en actividad
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="create_sets_options",
            descripcion=f"Error creando sets y opciones: {str(e)}",
            usuario=None,
            detalles={"upload_log_id": upload_log.id, "error": str(e)},
            resultado="error",
            ip_address=None,
        )
        
        return f"Error: {str(e)}"


def validar_archivo_clasificacion_excel(ruta_archivo, cliente_id):
    """
    Valida exhaustivamente un archivo Excel de clasificaciones antes de procesarlo.
    
    Formato esperado:
    - Fila 1: Headers (Columna A: códigos de cuenta, Columnas B+: nombres de sets)
    - Columna A: Códigos de cuenta
    - Columnas B+: Valores de clasificación para cada set
    
    Returns:
        dict: {
            'es_valido': bool,
            'errores': list[str],
            'advertencias': list[str],
            'estadisticas': dict
        }
    """
    import re
    import pandas as pd
    from django.db import models
    
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
        
        # No validamos existencia ya que las cuentas vienen del libro mayor que se sube después
        
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
