# backend/contabilidad/tasks.py


import datetime
import hashlib
import logging
import os
import re
import time
import json
import redis
from datetime import date
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from celery import shared_task, group, chord
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from contabilidad.models import (
    AccountClassification,
    # ClasificacionCuentaArchivo,  # OBSOLETO - ELIMINADO EN REDISEÑO
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    CentroCosto,
    Auxiliar,
    LibroMayorArchivo, 
    MovimientoContable,
    AperturaCuenta,
    Incidencia,
    NombresEnInglesUpload,
    TipoDocumento,
    UploadLog,
    ExcepcionValidacion,
    CierreContabilidad,
    ReporteFinanciero,
)
# ✨ NUEVO: Importar modelo de incidencias consolidadas
from contabilidad.models_incidencias import IncidenciaResumen
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


#=======PROCESSORS========



@shared_task
def procesar_libro_mayor(upload_log_id):
    """Procesa archivo de Libro Mayor usando UploadLog"""
    import hashlib
    import os
    import re
    from openpyxl import load_workbook
    import datetime

    logger.info("Iniciando procesamiento de libro mayor para upload_log %s", upload_log_id)

    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
    except UploadLog.DoesNotExist:
        logger.error("UploadLog con id %s no encontrado", upload_log_id)
        return f"Error: UploadLog {upload_log_id} no encontrado"

    upload_log.estado = "procesando"
    upload_log.save(update_fields=["estado"])
    inicio = timezone.now()

    archivo_obj = None

    try:
        es_valido, msg_valid = UploadLog.validar_nombre_archivo(
            upload_log.nombre_archivo_original,
            "LibroMayor",
            upload_log.cliente.rut,
        )

        if not es_valido:
            upload_log.estado = "error"
            upload_log.errores = f"Nombre de archivo inválido: {msg_valid}"
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            return f"Error: {msg_valid}"

        # Usar la ruta que se guardó en el upload_log
        ruta_relativa = upload_log.ruta_archivo
        if not ruta_relativa:
            upload_log.estado = "error"
            upload_log.errores = "No hay ruta de archivo especificada en el upload_log"
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

        # Verificar que el upload_log tenga un cierre asignado
        if not upload_log.cierre:
            upload_log.estado = "error"
            upload_log.errores = "LibroMayorUpload has no cierre."
            upload_log.tiempo_procesamiento = timezone.now() - inicio
            upload_log.save()
            return "Error: LibroMayorUpload has no cierre."

        # Extraer período del nombre del archivo
        import re
        rut_limpio = upload_log.cliente.rut.replace(".", "").replace("-", "") if upload_log.cliente.rut else str(upload_log.cliente.id)
        nombre_sin_ext = re.sub(r"\.(xlsx|xls)$", "", upload_log.nombre_archivo_original, flags=re.IGNORECASE)
        patron_periodo = rf"^{rut_limpio}_(LibroMayor|Mayor)_(\d{{6}})$"
        match = re.match(patron_periodo, nombre_sin_ext)
        periodo = match.group(2) if match else "000000"

        nombre_final = f"libro_mayor_{upload_log.cliente.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        archivo_obj, created = LibroMayorArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            cierre=upload_log.cierre,  # ✅ Agregado campo cierre
            defaults={
                "archivo": ContentFile(contenido, name=nombre_final),
                "estado": "procesando",
                "procesado": False,
                "upload_log": upload_log,
                "periodo": periodo,
            },
        )
        if not created:
            if archivo_obj.archivo:
                try:
                    archivo_obj.archivo.delete()
                except Exception:
                    pass
            archivo_obj.archivo.save(nombre_final, ContentFile(contenido))
            archivo_obj.estado = "procesando"
            archivo_obj.procesado = False
            archivo_obj.upload_log = upload_log
            archivo_obj.periodo = periodo
            archivo_obj.save()

        # Cargar excepciones de validación para este cliente
        excepciones_por_cuenta = {}
        for exc in ExcepcionValidacion.objects.filter(cliente=upload_log.cliente):
            key = f"{exc.codigo_cuenta}_{exc.tipo_excepcion}"
            excepciones_por_cuenta[key] = exc
        
        logger.info(f"Cargadas {len(excepciones_por_cuenta)} excepciones de validación para cliente {upload_log.cliente.id}")

        # Cargar datos auxiliares generados por otras tarjetas para
        # complementar el libro mayor (tipos de documento, nombres en
        # inglés y clasificaciones)
        tipos_doc_map = {
            td.codigo: td
            for td in TipoDocumento.objects.filter(cliente=upload_log.cliente)
        }

        nombres_ingles_map = {
            c.codigo: (c.nombre_en or "")
            for c in CuentaContable.objects.filter(cliente=upload_log.cliente).exclude(nombre_en__isnull=True)
        }

        # Obtener clasificaciones existentes desde AccountClassification (fuente única de verdad)
        clasificaciones_por_cuenta = {}
        for ac in AccountClassification.objects.filter(cliente=upload_log.cliente).select_related('set_clas', 'opcion', 'cuenta'):
            codigo_cuenta = ac.codigo_cuenta_display  # Usa el property que maneja tanto FK como código temporal
            if codigo_cuenta not in clasificaciones_por_cuenta:
                clasificaciones_por_cuenta[codigo_cuenta] = {}
            clasificaciones_por_cuenta[codigo_cuenta][ac.set_clas.nombre] = ac.opcion.valor

        wb = load_workbook(ruta_completa, read_only=True, data_only=True)
        ws = wb.active

        def clean(h):
            h = h.strip().upper()
            for a, b in [("Á","A"),("É","E"),("Í","I"),("Ó","O"),("Ú","U"),("Ñ","N")]:
                h = h.replace(a, b)
            return re.sub(r"[^A-Z0-9]", "", h)

        raw = next(ws.iter_rows(min_row=9, max_row=9, values_only=True))
        idx = {clean(h): i for i, h in enumerate(raw) if isinstance(h, str)}

        C = idx["CUENTA"]
        F = idx["FECHA"]
        NC = idx.get("NCOMPROBANTE")
        T = idx.get("TIPO")
        NI = idx.get("NINTERNO")
        CC = idx.get("CENTRODECOSTO")
        AX = idx.get("AUXILIAR")
        # La cabecera original suele venir como "TIPODOC." con punto al final.
        # Al normalizarla se convierte en "TIPODOC", pero dejamos el alias por
        # claridad.
        TD = idx.get("TIPODOC") or idx.get("TIPODOC.")
        ND = idx.get("NUMERODOC")
        DG = idx.get("DETDEGASTOINSTFINANCIERO")
        D = idx["DEBE"]
        H = idx["HABER"]
        S = idx["SALDO"]
        DS = idx["DESCRIPCION"]

        errores = []
        current_code = None
        fechas_mov = []
        movimientos_creados = 0
        incidencias_creadas = 0

        for row_idx, row in enumerate(ws.iter_rows(min_row=11, values_only=True), start=11):
            cell = row[C]

            if isinstance(cell, str) and cell.startswith("SALDO ANTERIOR"):
                try:
                    resto = cell.split(":", 1)[1].strip()
                    code, name = resto.split(" ", 1)
                    saldo_ant = row[S] or 0
                    cuenta_obj, _ = CuentaContable.objects.get_or_create(
                        cliente=upload_log.cliente,
                        codigo=code,
                        defaults={"nombre": name},
                    )
                    AperturaCuenta.objects.update_or_create(
                        cierre=upload_log.cierre,
                        cuenta=cuenta_obj,
                        defaults={"saldo_anterior": saldo_ant},
                    )
                    current_code = code
                except Exception as e:
                    errores.append(f"F{row_idx} Apertura: {e}")
                continue

            if current_code and row[F] is not None: #====es decir, esta fila es un movimiento=====#
                raw_fecha = row[F]
                try:
                    if isinstance(raw_fecha, str):
                        s = raw_fecha.strip().strip('"').strip("'")
                        fecha = datetime.datetime.strptime(s, "%d/%m/%Y").date()
                    elif isinstance(raw_fecha, datetime.datetime):
                        fecha = raw_fecha.date()
                    elif isinstance(raw_fecha, datetime.date):
                        fecha = raw_fecha
                    else:
                        raise ValueError(f"Formato de fecha no soportado: {raw_fecha!r}")
                    fechas_mov.append(fecha)
                except Exception as e:
                    errores.append(f"F{row_idx} Fecha: {e}")
                    continue

                cuenta_obj, _ = CuentaContable.objects.get_or_create(
                    cliente=upload_log.cliente,
                    codigo=current_code,
                )

                # Completar nombre en inglés desde registros previos
                if not cuenta_obj.nombre_en:
                    nombre_ing = nombres_ingles_map.get(cuenta_obj.codigo)
                    if nombre_ing:
                        cuenta_obj.nombre_en = nombre_ing
                        cuenta_obj.save(update_fields=["nombre_en"])

                # Aplicar clasificaciones registradas anteriormente
                clasif_info = clasificaciones_por_cuenta.get(cuenta_obj.codigo)
                if clasif_info:
                    for set_nombre, opcion_valor in clasif_info.items():
                        set_obj, _ = ClasificacionSet.objects.get_or_create(
                            cliente=upload_log.cliente, nombre=set_nombre
                        )
                        opcion_obj, _ = ClasificacionOption.objects.get_or_create(
                            set_clas=set_obj, valor=str(opcion_valor).strip()
                        )
                        AccountClassification.objects.update_or_create(
                            cuenta=cuenta_obj,
                            set_clas=set_obj,
                            defaults={"opcion": opcion_obj, "asignado_por": None},
                        )

                centro_obj = None
                if CC and row[CC]:
                    centro_obj, _ = CentroCosto.objects.get_or_create(
                        cliente=upload_log.cliente,
                        nombre=str(row[CC]).strip(),
                    )

                aux_obj = None
                if AX and row[AX]:
                    aux_obj, _ = Auxiliar.objects.get_or_create(
                        rut_auxiliar=str(row[AX]).strip(),
                        defaults={"nombre": "", "fecha_creacion": timezone.now()},
                    )

                td_obj = None
                mov_incompleto = False
                if TD is not None:
                    codigo_td = str(row[TD] or "").strip()
                    # Verificar si esta cuenta tiene excepción para tipo de documento
                    tiene_excepcion_tipodoc = f"{current_code}_tipos_doc_no_reconocidos" in excepciones_por_cuenta or \
                                            f"{current_code}_movimientos_tipodoc_nulo" in excepciones_por_cuenta
                    
                    if codigo_td:
                        td_obj = tipos_doc_map.get(codigo_td)
                        if td_obj is None and not tiene_excepcion_tipodoc:
                            Incidencia.objects.create(
                                cierre=upload_log.cierre,
                                tipo="negocio",
                                descripcion=(
                                    f"Movimiento {row_idx-10}, cuenta {current_code}: "
                                    f"Tipo de documento '{codigo_td}' no encontrado"
                                ),
                            )
                            incidencias_creadas += 1
                            mov_incompleto = True
                    else:
                        if not tiene_excepcion_tipodoc:
                            Incidencia.objects.create(
                                cierre=upload_log.cierre,
                                tipo="negocio",
                                descripcion=(
                                    f"Movimiento {row_idx-10}, cuenta {current_code}: "
                                    "Tipo de documento vacío"
                                ),
                            )
                            incidencias_creadas += 1
                            mov_incompleto = True
                
                mov = MovimientoContable.objects.create(
                    cierre=upload_log.cierre,
                    cuenta=cuenta_obj,
                    fecha=fecha,
                    tipo_documento=td_obj,
                    tipo_doc_codigo=codigo_td,
                    numero_documento=str(row[ND] or ""),
                    tipo=str(row[T] or ""),
                    numero_comprobante=str(row[NC] or ""),
                    numero_interno=str(row[NI] or ""),
                    centro_costo=centro_obj,
                    auxiliar=aux_obj,
                    detalle_gasto=str(row[DG] or ""),
                    debe=row[D] or 0,
                    haber=row[H] or 0,
                    descripcion=str(row[DS] or ""),
                    flag_incompleto=mov_incompleto,
                )

                # Verificar excepciones para nombres en inglés y clasificaciones
                tiene_excepcion_nombre = f"{current_code}_cuentas_sin_nombre_ingles" in excepciones_por_cuenta
                tiene_excepcion_clasificacion = f"{current_code}_cuentas_sin_clasificacion" in excepciones_por_cuenta

                if not cuenta_obj.nombre_en and not tiene_excepcion_nombre:
                    Incidencia.objects.create(
                        cierre=upload_log.cierre,
                        tipo="negocio",
                        descripcion=(
                            f"Movimiento {row_idx-10}, cuenta {current_code}: "
                            "No tiene nombre en inglés"
                        ),
                    )
                    incidencias_creadas += 1
                    mov.flag_incompleto = True

                if not AccountClassification.objects.filter(cuenta=cuenta_obj).exists() and not tiene_excepcion_clasificacion:
                    Incidencia.objects.create(
                        cierre=upload_log.cierre,
                        tipo="negocio",
                        descripcion=(
                            f"Movimiento {row_idx-10}, cuenta {current_code}: "
                            "Cuenta sin clasificación asignada"
                        ),
                    )
                    incidencias_creadas += 1
                    mov.flag_incompleto = True

                if mov.flag_incompleto:
                    mov.save(update_fields=["flag_incompleto"])
                movimientos_creados += 1

        fecha_inicio = min(fechas_mov) if fechas_mov else None
        fecha_fin = max(fechas_mov) if fechas_mov else None

        archivo_obj.estado = "completado" if not errores else "error"
        archivo_obj.procesado = True
        archivo_obj.errores = "\n".join(errores) if errores else ""
        archivo_obj.save()

        upload_log.estado = "completado" if not errores else "error"
        upload_log.errores = "\n".join(errores) if errores else ""
        upload_log.resumen = {
            "movimientos_creados": movimientos_creados,
            "incidencias_creadas": incidencias_creadas,
            "archivo_hash": archivo_hash,
        }
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save()

        # ✨ NUEVO: Generar incidencias consolidadas por sub-tipo
        try:
            logger.info(f"Generando incidencias consolidadas para upload_log {upload_log.id}")
            
            # Definir mensajes y acciones predefinidas por tipo de incidencia
            _MENSAJES = {
                "movimientos_tipodoc_nulo": "Se encontraron movimientos sin tipo de documento asignado (campo vacío)",
                "tipos_doc_no_reconocidos": "Se encontraron códigos de tipo de documento que no están registrados en el sistema",
                "cuentas_sin_clasificacion": "Se detectaron cuentas contables sin clasificación asignada",
                "cuentas_sin_nombre_ingles": "Se encontraron cuentas sin nombre en inglés configurado",
                "cuentas_nuevas_detectadas": "Se detectaron nuevas cuentas contables en el libro mayor",
            }
            
            _ACCIONES = {
                "movimientos_tipodoc_nulo": "Revisar el archivo fuente y completar los tipos de documento faltantes",
                "tipos_doc_no_reconocidos": "Cargar archivo de tipos de documento actualizado con los códigos faltantes",
                "cuentas_sin_clasificacion": "Cargar archivo de clasificaciones o asignar clasificaciones manualmente", 
                "cuentas_sin_nombre_ingles": "Cargar archivo de nombres en inglés actualizado",
                "cuentas_nuevas_detectadas": "Revisar nuevas cuentas y configurar nombres en inglés y clasificaciones",
            }
            
            # Analizar incidencias del upload_log actual y generar conteos por tipo
            from django.db.models import Q
            import re
            
            raw_counts = {}
            elementos_detallados = {}
            
            # 1. Contar movimientos con tipo de documento vacío y extraer elementos afectados
            incidencias_tipodoc_vacio = Incidencia.objects.filter(
                cierre=upload_log.cierre,
                descripcion__icontains="Tipo de documento vacío"
            )
            if incidencias_tipodoc_vacio.exists():
                count = incidencias_tipodoc_vacio.count()
                raw_counts["movimientos_tipodoc_nulo"] = count
                # Extraer cuentas afectadas de las descripciones
                # Formato: "Movimiento X, cuenta CODIGO: Tipo de documento vacío"
                cuentas_afectadas = []
                for inc in incidencias_tipodoc_vacio[:50]:  # Limitar a primeras 50 para rendimiento
                    match = re.search(r'cuenta\s+([\d\-]+):', inc.descripcion, flags=re.IGNORECASE)
                    if match:
                        codigo_cuenta = match.group(1)
                        if codigo_cuenta not in cuentas_afectadas:
                            cuentas_afectadas.append(codigo_cuenta)
                    else:
                        # Debug: Ver el formato real de la descripción
                        logger.debug(f"Descripción no coincide con regex: {inc.descripcion}")
                elementos_detallados["movimientos_tipodoc_nulo"] = cuentas_afectadas
            
            # 2. Contar incidencias de tipos de documento no encontrados
            incidencias_tipodoc_no_reconocido = Incidencia.objects.filter(
                cierre=upload_log.cierre,
                descripcion__icontains="no encontrado"
            ).exclude(
                descripcion__icontains="vacío"
            )
            if incidencias_tipodoc_no_reconocido.exists():
                count = incidencias_tipodoc_no_reconocido.count()
                raw_counts["tipos_doc_no_reconocidos"] = count
                # Extraer códigos de tipo de documento no reconocidos
                codigos_no_reconocidos = []
                for inc in incidencias_tipodoc_no_reconocido[:50]:
                    match = re.search(r"'([^']+)' no encontrado", inc.descripcion)
                    if match:
                        codigo_td = match.group(1)
                        if codigo_td not in codigos_no_reconocidos:
                            codigos_no_reconocidos.append(codigo_td)
                    else:
                        # Debug: Ver el formato real de la descripción
                        logger.debug(f"Descripción TD no reconocido no coincide: {inc.descripcion}")
                elementos_detallados["tipos_doc_no_reconocidos"] = codigos_no_reconocidos
            
            # 3. Contar cuentas sin clasificación
            incidencias_sin_clasif = Incidencia.objects.filter(
                cierre=upload_log.cierre,
                descripcion__icontains="sin clasificación"
            )
            if incidencias_sin_clasif.exists():
                count = incidencias_sin_clasif.count()
                raw_counts["cuentas_sin_clasificacion"] = count
                # Extraer cuentas sin clasificación
                cuentas_sin_clasif = []
                for inc in incidencias_sin_clasif[:50]:
                    match = re.search(r'cuenta\s+([\d\-]+):', inc.descripcion, flags=re.IGNORECASE)
                    if match:
                        codigo_cuenta = match.group(1)
                        if codigo_cuenta not in cuentas_sin_clasif:
                            cuentas_sin_clasif.append(codigo_cuenta)
                    else:
                        # Debug: Ver el formato real de la descripción
                        logger.debug(f"Descripción sin clasificación no coincide: {inc.descripcion}")
                elementos_detallados["cuentas_sin_clasificacion"] = cuentas_sin_clasif
            
            # 4. Contar cuentas sin nombre en inglés
            incidencias_sin_nombre = Incidencia.objects.filter(
                cierre=upload_log.cierre,
                descripcion__icontains="nombre en inglés"
            )
            if incidencias_sin_nombre.exists():
                count = incidencias_sin_nombre.count()
                raw_counts["cuentas_sin_nombre_ingles"] = count
                # Extraer cuentas sin nombre en inglés
                cuentas_sin_nombre = []
                for inc in incidencias_sin_nombre[:50]:
                    match = re.search(r'cuenta\s+([\d\-]+):', inc.descripcion, flags=re.IGNORECASE)
                    if match:
                        codigo_cuenta = match.group(1)
                        if codigo_cuenta not in cuentas_sin_nombre:
                            cuentas_sin_nombre.append(codigo_cuenta)
                    else:
                        # Debug: Ver el formato real de la descripción
                        logger.debug(f"Descripción sin nombre inglés no coincide: {inc.descripcion}")
                elementos_detallados["cuentas_sin_nombre_ingles"] = cuentas_sin_nombre
            
            # 5. Contar cuentas nuevas detectadas (usando las cuentas creadas durante el procesamiento)
            cuentas_nuevas = upload_log.resumen.get("cuentas_nuevas", 0)
            if cuentas_nuevas > 0:
                raw_counts["cuentas_nuevas_detectadas"] = cuentas_nuevas
                # Para cuentas nuevas, como no tenemos timestamp de creación,
                # obtenemos una muestra de las últimas cuentas del cliente
                cuentas_recientes = list(
                    CuentaContable.objects.filter(
                        cliente=upload_log.cliente
                    ).order_by('-id')[:50].values_list('codigo', flat=True)
                )
                elementos_detallados["cuentas_nuevas_detectadas"] = cuentas_recientes
            
            # Crear registros individuales de IncidenciaResumen por cada sub-tipo
            incidencias_consolidadas_creadas = 0
            for sub_tipo, count in raw_counts.items():
                # Determinar severidad basada en cantidad
                if count > 100:
                    severidad = "critica"
                elif count > 50:
                    severidad = "alta"
                elif count > 10:
                    severidad = "media"
                else:
                    severidad = "baja"
                
                # Obtener elementos afectados para este sub-tipo
                elementos_afectados = elementos_detallados.get(sub_tipo, [])
                
                # Debug: log de elementos extraídos
                logger.info(f"Sub-tipo {sub_tipo}: {count} incidencias, {len(elementos_afectados)} elementos extraídos: {elementos_afectados[:5]}")
                
                # Crear registro consolidado para este sub-tipo
                IncidenciaResumen.objects.create(
                    upload_log=upload_log,
                    tipo_incidencia=sub_tipo,
                    cantidad_afectada=count,
                    estado="activa",
                    severidad=severidad,
                    mensaje_usuario=_MENSAJES.get(sub_tipo, f"Incidencia detectada: {sub_tipo}"),
                    accion_sugerida=_ACCIONES.get(sub_tipo, "Revisar y corregir manualmente"),
                    codigo_problema=f"{sub_tipo.upper()}_{upload_log.id}",
                    elementos_afectados=elementos_afectados,
                    detalle_muestra={
                        "upload_log_id": upload_log.id,
                        "cantidad": count,
                        "tipo": sub_tipo,
                        "elementos_muestra": elementos_afectados[:10],  # Solo primeros 10 para la muestra
                        "total_elementos": len(elementos_afectados)
                    }
                )
                incidencias_consolidadas_creadas += 1
            
            # Actualizar resumen con información consolidada
            upload_log.resumen.update({
                "incidencias_consolidadas_creadas": incidencias_consolidadas_creadas,
                "tipos_incidencia_detectados": list(raw_counts.keys()),
                "conteos_por_tipo": raw_counts,
                "sistema_consolidado": True
            })
            upload_log.save(update_fields=['resumen'])
            
            logger.info(f"Creadas {incidencias_consolidadas_creadas} incidencias consolidadas por sub-tipo")
            
        except Exception as e:
            logger.error(f"Error generando incidencias consolidadas: {e}")
            # No fallar el procesamiento por esto
            pass

        try:
            os.remove(ruta_completa)
        except OSError:
            pass

        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
            tarjeta="libro_mayor",
            accion="process_excel",
            descripcion=f"Procesado archivo de libro mayor: {movimientos_creados} movimientos",
            usuario=None,
            detalles={
                "upload_log_id": upload_log.id,
                "movimientos_creados": movimientos_creados,
                "incidencias_creadas": incidencias_creadas,
            },
            resultado="exito" if not errores else "warning",
            ip_address=None,
        )

        # FK-only: Ya no hay clasificaciones temporales por código, se omite mapeo
        try:
            logger.info("FK-only activo: se omite mapeo de clasificaciones temporales a FK")
        except Exception:
            pass

        return f"Completado: {movimientos_creados} movimientos"

    except Exception as e:
        if archivo_obj:
            archivo_obj.estado = "error"
            archivo_obj.errores = str(e)
            archivo_obj.save()

        upload_log.estado = "error"
        upload_log.errores = str(e)
        upload_log.tiempo_procesamiento = timezone.now() - inicio
        upload_log.save()

        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=upload_log.cierre.periodo if upload_log.cierre else date.today().strftime("%Y-%m"),
            tarjeta="libro_mayor",
            accion="process_excel",
            descripcion=f"Error al procesar libro mayor: {str(e)}",
            usuario=None,
            detalles={"upload_log_id": upload_log.id},
            resultado="error",
            ip_address=None,
        )

        return f"Error: {str(e)}"




#=======CLEANING TASKS=======
from celery import shared_task
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

# ===== TAREAS DE REPORTES FINANCIEROS =====

@shared_task
def generar_estado_situacion_financiera(cierre_id, usuario_id=None):
    """
    Genera el Estado de Situación Financiera para un cierre específico.
    
    Args:
        cierre_id (int): ID del cierre para el cual generar el reporte
        usuario_id (int): ID del usuario que solicita el reporte (opcional)
    
    Returns:
        dict: Resultado de la generación del reporte
    """
    from decimal import Decimal
    from django.contrib.auth.models import User
    import json
    
    logger.info(f"🏛️ Iniciando generación de Estado de Situación Financiera para cierre {cierre_id}")
    
    inicio = timezone.now()
    usuario = None
    
    try:
        # Validar que el cierre existe
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id)
        except CierreContabilidad.DoesNotExist:
            error_msg = f"Cierre con ID {cierre_id} no encontrado"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Obtener usuario si se proporciona
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                logger.warning(f"Usuario con ID {usuario_id} no encontrado, continuando sin usuario")
        
        # Verificar si ya existe un reporte para este cierre
        reporte_existente = ReporteFinanciero.objects.filter(
            cierre=cierre,
            tipo_reporte='esf'
        ).first()
        
        if reporte_existente:
            logger.info(f"Ya existe un reporte ESF para el cierre {cierre_id}, actualizando...")
            reporte = reporte_existente
            # IMPORTANTE: Actualizar el usuario generador cuando se regenera
            if usuario:
                reporte.usuario_generador = usuario
        else:
            # Crear nuevo reporte
            reporte = ReporteFinanciero.objects.create(
                cierre=cierre,
                tipo_reporte='esf',
                usuario_generador=usuario,
                estado='generando'
            )
        
        # Actualizar estado a generando
        reporte.estado = 'generando'
        reporte.fecha_generacion = inicio
        reporte.save(update_fields=['estado', 'fecha_generacion', 'usuario_generador'])
        
        # Obtener todas las cuentas con movimientos en el cierre
        movimientos = MovimientoContable.objects.filter(cierre=cierre).select_related('cuenta')
        
        # Obtener saldos de apertura
        saldos_apertura = AperturaCuenta.objects.filter(cierre=cierre).select_related('cuenta')
        
        # Construir diccionario de cuentas únicas
        cuentas_data = {}
        
        # Procesar saldos de apertura
        for apertura in saldos_apertura:
            cuenta_codigo = apertura.cuenta.codigo
            if cuenta_codigo not in cuentas_data:
                cuentas_data[cuenta_codigo] = {
                    'codigo': apertura.cuenta.codigo,
                    'nombre': apertura.cuenta.nombre,
                    'saldo_anterior': float(apertura.saldo_anterior or 0),
                    'debe': 0.0,
                    'haber': 0.0,
                    'saldo_final': float(apertura.saldo_anterior or 0)
                }
            else:
                cuentas_data[cuenta_codigo]['saldo_anterior'] = float(apertura.saldo_anterior or 0)
                cuentas_data[cuenta_codigo]['saldo_final'] = float(apertura.saldo_anterior or 0)
        
        # Procesar movimientos
        for movimiento in movimientos:
            cuenta_codigo = movimiento.cuenta.codigo
            if cuenta_codigo not in cuentas_data:
                cuentas_data[cuenta_codigo] = {
                    'codigo': movimiento.cuenta.codigo,
                    'nombre': movimiento.cuenta.nombre,
                    'saldo_anterior': 0.0,
                    'debe': 0.0,
                    'haber': 0.0,
                    'saldo_final': 0.0
                }
            
            # Acumular debe y haber
            cuentas_data[cuenta_codigo]['debe'] += float(movimiento.debe or 0)
            cuentas_data[cuenta_codigo]['haber'] += float(movimiento.haber or 0)
        
        # Calcular saldos finales
        for cuenta_codigo, data in cuentas_data.items():
            data['saldo_final'] = data['saldo_anterior'] + data['debe'] - data['haber']
        
        # Obtener clasificaciones para estructurar el reporte
        # Buscar el set de clasificación "Estado de Situación Financiera" o similar
        try:
            set_esf = ClasificacionSet.objects.filter(
                nombre__icontains='situación financiera'
            ).first()
            
            if not set_esf:
                # Si no existe, buscar el primer set disponible
                set_esf = ClasificacionSet.objects.first()
                
            if not set_esf:
                raise ValueError("No se encontró ningún set de clasificación disponible")
                
        except Exception as e:
            logger.error(f"Error al obtener set de clasificación: {e}")
            set_esf = None
        
        # Estructura del Estado de Situación Financiera
        estructura_esf = {
            'activos': {
                'corrientes': {},
                'no_corrientes': {},
                'total': 0.0
            },
            'pasivos': {
                'corrientes': {},
                'no_corrientes': {},
                'total': 0.0
            },
            'patrimonio': {
                'capital': {},
                'resultados': {},
                'total': 0.0
            },
            'total_pasivos_patrimonio': 0.0
        }
        
        # Clasificar cuentas según su código (lógica básica)
        for cuenta_codigo, data in cuentas_data.items():
            saldo = data['saldo_final']
            
            # Lógica básica de clasificación por código de cuenta
            if cuenta_codigo.startswith('1'):  # Activos
                if cuenta_codigo.startswith('11'):  # Activos corrientes
                    estructura_esf['activos']['corrientes'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                else:  # Activos no corrientes
                    estructura_esf['activos']['no_corrientes'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                estructura_esf['activos']['total'] += saldo
                
            elif cuenta_codigo.startswith('2'):  # Pasivos
                if cuenta_codigo.startswith('21'):  # Pasivos corrientes
                    estructura_esf['pasivos']['corrientes'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                else:  # Pasivos no corrientes
                    estructura_esf['pasivos']['no_corrientes'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                estructura_esf['pasivos']['total'] += saldo
                
            elif cuenta_codigo.startswith('3'):  # Patrimonio
                if 'capital' in data['nombre'].lower():
                    estructura_esf['patrimonio']['capital'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                else:
                    estructura_esf['patrimonio']['resultados'][cuenta_codigo] = {
                        'nombre': data['nombre'],
                        'saldo': saldo
                    }
                estructura_esf['patrimonio']['total'] += saldo
        
        # Calcular total pasivos + patrimonio
        estructura_esf['total_pasivos_patrimonio'] = (
            estructura_esf['pasivos']['total'] + 
            estructura_esf['patrimonio']['total']
        )
        
        # Metadatos del reporte
        metadatos = {
            'cierre_id': cierre.id,
            'cliente': cierre.cliente.nombre,
            'periodo': cierre.periodo,
            'fecha_generacion': inicio.isoformat(),
            'usuario': usuario.correo_bdo if usuario else 'Sistema',
            'total_cuentas': len(cuentas_data),
            'set_clasificacion_usado': set_esf.nombre if set_esf else 'N/A'
        }
        
        # Preparar datos completos del reporte
        datos_reporte = {
            'metadatos': metadatos,
            'estructura': estructura_esf,
            'detalle_cuentas': cuentas_data
        }
        
        # Guardar el reporte
        reporte.datos_reporte = datos_reporte
        reporte.estado = 'completado'
        reporte.save(update_fields=['datos_reporte', 'estado'])
        
        logger.info(f"✅ Estado de Situación Financiera generado exitosamente para cierre {cierre_id}")
        
        return {
            'success': True,
            'reporte_id': reporte.id,
            'total_cuentas': len(cuentas_data),
            'total_activos': estructura_esf['activos']['total'],
            'total_pasivos_patrimonio': estructura_esf['total_pasivos_patrimonio']
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando Estado de Situación Financiera: {str(e)}")
        
        # Actualizar estado del reporte si existe
        if 'reporte' in locals():
            reporte.estado = 'error'
            reporte.error_mensaje = str(e)
            reporte.save(update_fields=['estado', 'error_mensaje'])
        
        return {
            'error': str(e),
            'cierre_id': cierre_id
        }

@shared_task
def enviar_reporte_a_cache(reporte_id):
    """
    Envía un reporte financiero al caché Redis
    
    Args:
        reporte_id: ID del reporte financiero a enviar al caché
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        from contabilidad.cache_redis import get_cache_system
        
        logger.info(f"Iniciando envío al caché del reporte ID: {reporte_id}")
        
        # Obtener el reporte
        try:
            reporte = ReporteFinanciero.objects.select_related(
                'cierre', 'cierre__cliente'
            ).get(id=reporte_id)
        except ReporteFinanciero.DoesNotExist:
            error_msg = f"Reporte con ID {reporte_id} no encontrado"
            logger.error(error_msg)
            return {'error': error_msg, 'reporte_id': reporte_id}
        
        # Validar que el reporte esté completado
        if reporte.estado != 'completado':
            error_msg = f"Reporte {reporte_id} no está completado. Estado actual: {reporte.estado}"
            logger.error(error_msg)
            return {'error': error_msg, 'reporte_id': reporte_id}
        
        # Validar que tenga datos
        if not reporte.datos_reporte:
            error_msg = f"Reporte {reporte_id} no tiene datos para enviar al caché"
            logger.error(error_msg)
            return {'error': error_msg, 'reporte_id': reporte_id}
        
        # Obtener sistema de caché
        cache_system = get_cache_system()
        
        # Mapear tipo de reporte a clave de caché
        tipo_cache_map = {
            'esf': 'esf',  # Estado de Situación Financiera
            'eri': 'eri',  # Estado de Resultado Integral
            'ecp': 'ecp'   # Estado de Cambios en el Patrimonio
        }
        
        tipo_cache = tipo_cache_map.get(reporte.tipo_reporte)
        if not tipo_cache:
            error_msg = f"Tipo de reporte no soportado para caché: {reporte.tipo_reporte}"
            logger.error(error_msg)
            return {'error': error_msg, 'reporte_id': reporte_id}
        
        # Preparar datos para el caché
        # Obtener información del usuario de forma segura
        usuario_info = None
        if reporte.usuario_generador:
            try:
                # El modelo Usuario usa correo_bdo como USERNAME_FIELD
                if hasattr(reporte.usuario_generador, 'correo_bdo'):
                    usuario_info = reporte.usuario_generador.correo_bdo
                elif hasattr(reporte.usuario_generador, 'nombre'):
                    usuario_info = f"{reporte.usuario_generador.nombre} {getattr(reporte.usuario_generador, 'apellido', '')}"
                else:
                    usuario_info = str(reporte.usuario_generador)
            except Exception as e:
                logger.warning(f"Error obteniendo información del usuario: {e}")
                usuario_info = "Usuario desconocido"
        
        datos_cache = {
            **reporte.datos_reporte,
            '_reporte_metadata': {
                'reporte_id': reporte.id,
                'fecha_generacion': reporte.fecha_generacion.isoformat(),
                'usuario_generador': usuario_info,
                'tipo_reporte': reporte.tipo_reporte,
                'enviado_cache_at': timezone.now().isoformat()
            }
        }
        
        # Enviar al caché con TTL extendido (4 horas para reportes)
        resultado = cache_system.set_estado_financiero(
            cliente_id=reporte.cierre.cliente.id,
            periodo=reporte.cierre.periodo,
            tipo_estado=tipo_cache,
            datos=datos_cache,
            ttl=14400  # 4 horas
        )
        
        if resultado:
            logger.info(
                f"Reporte {reporte_id} ({reporte.get_tipo_reporte_display()}) "
                f"enviado exitosamente al caché. Cliente: {reporte.cierre.cliente.nombre}, "
                f"Período: {reporte.cierre.periodo}"
            )
            
            return {
                'success': True,
                'reporte_id': reporte_id,
                'tipo_reporte': reporte.tipo_reporte,
                'cliente': reporte.cierre.cliente.nombre,
                'periodo': reporte.cierre.periodo,
                'mensaje': 'Reporte enviado al caché exitosamente'
            }
        else:
            error_msg = f"Error enviando reporte {reporte_id} al caché"
            logger.error(error_msg)
            return {'error': error_msg, 'reporte_id': reporte_id}
            
    except Exception as e:
        error_msg = f"Error inesperado enviando reporte {reporte_id} al caché: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg, 'reporte_id': reporte_id}


@shared_task
def enviar_multiples_reportes_a_cache(reporte_ids):
    """
    Envía múltiples reportes financieros al caché Redis
    
    Args:
        reporte_ids: Lista de IDs de reportes financieros
        
    Returns:
        dict: Resultado consolidado de la operación
    """
    resultados = {
        'exitosos': [],
        'errores': [],
        'total_procesados': len(reporte_ids),
        'total_exitosos': 0,
        'total_errores': 0
    }
    
    logger.info(f"Iniciando envío masivo al caché de {len(reporte_ids)} reportes")
    
    for reporte_id in reporte_ids:
        try:
            resultado = enviar_reporte_a_cache(reporte_id)
            
            if resultado.get('success'):
                resultados['exitosos'].append(resultado)
                resultados['total_exitosos'] += 1
            else:
                resultados['errores'].append(resultado)
                resultados['total_errores'] += 1
                
        except Exception as e:
            error_resultado = {
                'error': f"Error procesando reporte {reporte_id}: {str(e)}",
                'reporte_id': reporte_id
            }
            resultados['errores'].append(error_resultado)
            resultados['total_errores'] += 1
    
    logger.info(
        f"Envío masivo completado. Exitosos: {resultados['total_exitosos']}, "
        f"Errores: {resultados['total_errores']}"
    )
    
    return resultados


# =====================================================
# FUNCIONES AUXILIARES PARA CAPTURA MASIVA DE GASTOS
# =====================================================

def get_redis_client_db1():
    """
    Obtiene cliente Redis para db1 usando la configuración de Django
    Con soporte UTF-8 completo
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )

def get_redis_client_db1_binary():
    """
    Obtiene cliente Redis para db1 para datos binarios (sin decode_responses)
    Con soporte UTF-8 para metadatos
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=False,
            encoding='utf-8'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=False,
            encoding='utf-8'
        )

def serialize_excel_data(data):
    """
    Serializa datos de Excel para que sean compatibles con JSON/Redis
    """
    if isinstance(data, list):
        return [serialize_excel_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_excel_data(value) for key, value in data.items()}
    elif isinstance(data, (datetime.datetime, datetime.date)):
        return data.isoformat()
    elif isinstance(data, (int, float, str, bool)) or data is None:
        # Asegurar que las strings mantengan encoding UTF-8
        return data
    else:
        return data

def contar_centros_costos(fila, headers, mapeo_cc=None):
    """
    Cuenta la cantidad de centros de costos en una fila de gastos
    """
    if mapeo_cc is None:
        mapeo_cc = {}
    
    count = 0
    # Buscar columnas que contengan información de centros de costos
    for header in headers:
        if header and ('pyc' in header.lower() or 'ps/eb' in header.lower() or 'co' in header.lower()):
            valor = fila.get(header)
            if valor and str(valor).strip():
                count += 1
    
    return count

# =====================================================
# TAREAS DE CAPTURA MASIVA DE GASTOS
# =====================================================

@shared_task(bind=True)
def procesar_captura_masiva_gastos_task(self, archivo_content, archivo_nombre, usuario_id, mapeo_cc=None):
    """
    Tarea principal que recibe el archivo Excel y dispara el procesamiento con Chord
    """
    logger.info(f"🧾 Iniciando captura masiva de gastos para archivo: {archivo_nombre}")
    
    # Si no hay mapeo, usar diccionario vacío
    if mapeo_cc is None:
        mapeo_cc = {}
    
    try:
        # Configurar Redis db1 para resultados temporales - usar configuración de Django
        redis_client = get_redis_client_db1()
        
        # Cargar el archivo Excel desde el contenido
        wb = load_workbook(BytesIO(archivo_content))
        ws = wb.active
        
        # Obtener headers de la primera fila
        headers = []
        for cell in ws[1]:
            headers.append(cell.value)
        
        logger.info(f"📋 Headers encontrados: {headers}")
        
        # Procesar filas desde la fila 2 (saltar header)
        filas_data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if any(row):  # Solo procesar filas que no estén completamente vacías
                fila_dict = dict(zip(headers, row))
                # Serializar datos para evitar problemas con datetime
                fila_dict = serialize_excel_data(fila_dict)
                filas_data.append(fila_dict)
        
        logger.info(f"📊 Total filas a procesar: {len(filas_data)}")
        
        # Agrupar por "Tipo Doc" (columna 2) + cantidad de Centros de Costos (PyC, PS/EB, CO)
        tipo_doc_column = headers[1] if len(headers) > 1 else None
        if not tipo_doc_column:
            raise ValueError("No se encontró la columna de Tipo Doc (columna 2)")
        
        grupos_por_tipo_cc = {}
        for i, fila in enumerate(filas_data):
            tipo_doc = fila.get(tipo_doc_column, 'Sin Tipo')
            cc_count = contar_centros_costos(fila, headers, mapeo_cc)
            
            # Crear clave de grupo: "TipoDoc con XCC"
            clave_grupo = f"{tipo_doc} con {cc_count}CC"
            
            if clave_grupo not in grupos_por_tipo_cc:
                grupos_por_tipo_cc[clave_grupo] = []
            grupos_por_tipo_cc[clave_grupo].append(fila)
        
        logger.info(f"🗂️ Grupos creados por Tipo Doc + CC: {list(grupos_por_tipo_cc.keys())}")
        
        # Generar task_id único para coordinar resultados
        task_id = self.request.id
        
        # Almacenar metadatos en Redis con TTL de 5 minutos - incluir usuario_id en la clave
        metadata = {
            'task_id': task_id,
            'archivo_nombre': archivo_nombre,
            'usuario_id': usuario_id,
            'total_filas': len(filas_data),
            'grupos': list(grupos_por_tipo_cc.keys()),
            'headers': headers,
            'mapeo_cc': mapeo_cc,
            'inicio': timezone.now().isoformat(),
            'estado': 'procesando'
        }
        redis_client.setex(
            f"captura_gastos_meta:{usuario_id}:{task_id}", 
            300, 
            json.dumps(metadata, ensure_ascii=False)
        )
        
        # Procesar cada grupo y crear Excel con pestañas
        logger.info(f"🔧 DEBUG: Llamando a consolidar_resultados_gastos_directo con {len(grupos_por_tipo_cc)} grupos")
        resultado = consolidar_resultados_gastos_directo(grupos_por_tipo_cc, headers, mapeo_cc, task_id, usuario_id)
        logger.info(f"🔧 DEBUG: consolidar_resultados_gastos_directo retornó: {resultado}")
        
        # Actualizar metadatos con resultado
        metadata.update({
            'estado': 'completado',
            'total_filas_procesadas': resultado['total_filas_procesadas'],
            'fin': timezone.now().isoformat(),
            'archivo_resultado': f'{archivo_nombre.rsplit(".", 1)[0]}_procesado.xlsx',
            'archivo_excel_disponible': True
        })
        
        redis_client.setex(
            f"captura_gastos_meta:{usuario_id}:{task_id}", 
            300, 
            json.dumps(metadata, ensure_ascii=False)
        )
        
        logger.info(f"✅ Captura masiva de gastos completada. Archivo: {metadata['archivo_resultado']}")
        
        return {
            'status': 'SUCCESS',
            'task_id': task_id,
            'archivo_resultado': metadata['archivo_resultado'],
            'filas_procesadas': resultado['total_filas_procesadas'],
            'errores': 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando captura masiva de gastos: {str(e)}")
        
        # Actualizar metadatos con error
        try:
            redis_client = get_redis_client_db1()
            metadata = {
                'task_id': self.request.id,
                'estado': 'error',
                'error': str(e),
                'fin': timezone.now().isoformat()
            }
            redis_client.setex(
                f"captura_gastos_meta:{usuario_id}:{self.request.id}", 
                300, 
                json.dumps(metadata, ensure_ascii=False)
            )
        except:
            pass
        
        raise

def consolidar_resultados_gastos_directo(grupos_por_tipo_cc, headers, mapeo_cc, task_id, usuario_id):
    """
    Consolida los resultados de todos los grupos y genera el Excel final directamente
    """
    logger.info(f"🔄 Consolidando resultados para task_id: {task_id}, usuario: {usuario_id}")
    
    try:
        # Mapeo estático de tipos de documento chilenos comunes
        tipos_doc_map = {
            "33": "Factura Electrónica",
            "34": "Factura Exenta Electrónica", 
            "39": "Boleta Electrónica",
            "41": "Boleta Exenta Electrónica",
            "43": "Liquidación Factura Electrónica",
            "46": "Factura de Compra Electrónica",
            "52": "Guía de Despacho Electrónica",
            "56": "Nota de Débito Electrónica",
            "61": "Nota de Crédito Electrónica",
            "110": "Factura de Exportación Electrónica",
            "111": "Nota de Débito de Exportación Electrónica",
            "112": "Nota de Crédito de Exportación Electrónica"
        }
        logger.info(f"📋 Usando mapeo estático de {len(tipos_doc_map)} tipos de documento chilenos")
        
        # Crear un nuevo workbook con pestañas por tipo de documento
        wb = Workbook()
        wb.remove(wb.active)  # Remover hoja por defecto
        
        total_filas_procesadas = 0
        
        # Procesar cada grupo y crear pestañas
        for clave_grupo, filas_data in grupos_por_tipo_cc.items():
            
            # Crear hoja para este grupo - convertir a string y limpiar para Excel
            nombre_hoja = str(clave_grupo)[:31]  # Excel limita a 31 caracteres
            # Reemplazar caracteres no válidos para nombres de hoja en Excel
            nombre_hoja = nombre_hoja.replace(":", "-").replace("/", "-").replace("\\", "-")
            ws = wb.create_sheet(title=nombre_hoja)
            
            # Headers de salida según especificaciones contables
            headers_salida = get_headers_salida_contabilidad()
            
            # Escribir headers de salida
            for col, header in enumerate(headers_salida, 1):
                ws.cell(row=1, column=col, value=header)
            
            # Escribir datos transformados
            row_idx = 2  # Comenzar después del header
            
            for fila in filas_data:
                # Extraer tipo de documento y cantidad de CC del nombre del grupo (ej: "33 con 2CC" -> "33", 2)
                partes_grupo = clave_grupo.split(' ')
                tipo_doc = partes_grupo[0]
                cc_count = int(partes_grupo[2].replace('CC', '')) if len(partes_grupo) >= 3 else 1
                
                # Aplicar reglas de transformación según tipo de documento y cantidad de CC
                # Esto puede retornar múltiples filas (ej: para tipo 33 retorna 3 filas: Proveedores, Gastos, IVA)
                filas_transformadas = aplicar_reglas_tipo_documento(fila, headers, tipo_doc, cc_count, mapeo_cc, tipos_doc_map)
                
                # Escribir cada fila transformada
                for fila_transformada in filas_transformadas:
                    for col_idx, header in enumerate(headers_salida, 1):
                        valor = fila_transformada.get(header, "")
                        ws.cell(row=row_idx, column=col_idx, value=valor)
                    row_idx += 1
            
            # Calcular total de filas de salida para este grupo
            filas_salida_grupo = 0
            for fila in filas_data:
                partes_grupo = clave_grupo.split(' ')
                tipo_doc = partes_grupo[0]
                cc_count = int(partes_grupo[2].replace('CC', '')) if len(partes_grupo) >= 3 else 1
                filas_transformadas = aplicar_reglas_tipo_documento(fila, headers, tipo_doc, cc_count, mapeo_cc, tipos_doc_map)
                filas_salida_grupo += len(filas_transformadas)
            
            total_filas_procesadas += filas_salida_grupo
            logger.info(f"📊 Hoja '{clave_grupo}' creada con {len(filas_data)} filas de entrada → {filas_salida_grupo} filas de salida")
        
        # Convertir workbook a bytes
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_content = excel_buffer.getvalue()
        
        # Almacenar el archivo Excel en Redis con TTL de 5 minutos - incluir usuario_id en la clave
        redis_client_binary = get_redis_client_db1_binary()
        redis_client_binary.setex(
            f"captura_gastos_archivo:{usuario_id}:{task_id}", 
            300, 
            excel_content
        )
        
        logger.info(f"✅ Consolidación completada para task_id: {task_id}")
        
        return {
            'task_id': task_id,
            'estado': 'completado',
            'total_filas_procesadas': total_filas_procesadas,
            'total_grupos': len(grupos_por_tipo_cc),
            'archivo_excel_disponible': True
        }
        
    except Exception as e:
        logger.error(f"❌ Error consolidando resultados: {str(e)}")
        raise

def get_headers_salida_contabilidad():
    """
    Headers de salida para el archivo Excel procesado según especificaciones contables
    """
    return [
        'Fecha',
        'Tipo Doc',
        'Número Doc',
        'RUT',
        'Razón Social',
        'Cuenta',
        'Nombre Cuenta',
        'Debe',
        'Haber',
        'Centro Costo',
        'Proyecto',
        'Glosa',
        'Referencia'
    ]

def aplicar_reglas_tipo_documento(fila, headers, tipo_doc, cc_count, mapeo_cc, tipos_doc_map):
    """
    Aplica las reglas de transformación según el tipo de documento
    Retorna una lista de filas transformadas
    """
    filas_resultado = []
    
    try:
        # Headers de entrada esperados
        fecha_idx = next((i for i, h in enumerate(headers) if h and 'fecha' in h.lower() and 'docto' in h.lower()), 6)
        folio_idx = next((i for i, h in enumerate(headers) if h and 'folio' in h.lower()), 5)
        rut_idx = next((i for i, h in enumerate(headers) if h and 'rut' in h.lower()), 3)
        razon_idx = next((i for i, h in enumerate(headers) if h and 'razon' in h.lower() or 'social' in h.lower()), 4)
        
        # Montos
        monto_neto_idx = next((i for i, h in enumerate(headers) if h and 'neto' in h.lower()), 8)
        monto_iva_idx = next((i for i, h in enumerate(headers) if h and 'iva' in h.lower() and 'recuperable' in h.lower()), 9)
        monto_total_idx = next((i for i, h in enumerate(headers) if h and 'total' in h.lower()), 11)
        
        # Obtener valores de la fila
        fecha = fila.get(headers[fecha_idx]) if fecha_idx < len(headers) else ""
        folio = fila.get(headers[folio_idx]) if folio_idx < len(headers) else ""
        rut = fila.get(headers[rut_idx]) if rut_idx < len(headers) else ""
        razon_social = fila.get(headers[razon_idx]) if razon_idx < len(headers) else ""
        
        monto_neto = float(fila.get(headers[monto_neto_idx], 0) or 0)
        monto_iva = float(fila.get(headers[monto_iva_idx], 0) or 0)
        monto_total = float(fila.get(headers[monto_total_idx], 0) or 0)
        
        # Descripción del tipo de documento
        tipo_doc_desc = tipos_doc_map.get(str(tipo_doc), f"Tipo {tipo_doc}")
        
        # Reglas según tipo de documento
        if tipo_doc == "33":  # Factura Electrónica
            # 1. Fila de Proveedores (HABER)
            filas_resultado.append({
                'Fecha': fecha,
                'Tipo Doc': tipo_doc,
                'Número Doc': folio,
                'RUT': rut,
                'Razón Social': razon_social,
                'Cuenta': '2111001',  # Cuenta de proveedores
                'Nombre Cuenta': 'Proveedores Nacionales',
                'Debe': '',
                'Haber': monto_total,
                'Centro Costo': '',
                'Proyecto': '',
                'Glosa': f'{tipo_doc_desc} - {razon_social}',
                'Referencia': folio
            })
            
            # 2. Fila de Gastos (DEBE)
            filas_resultado.append({
                'Fecha': fecha,
                'Tipo Doc': tipo_doc,
                'Número Doc': folio,
                'RUT': rut,
                'Razón Social': razon_social,
                'Cuenta': '5111001',  # Cuenta de gastos generales
                'Nombre Cuenta': 'Gastos Generales',
                'Debe': monto_neto,
                'Haber': '',
                'Centro Costo': get_centro_costo_principal(fila, headers, mapeo_cc),
                'Proyecto': '',
                'Glosa': f'{tipo_doc_desc} - {razon_social}',
                'Referencia': folio
            })
            
            # 3. Fila de IVA (DEBE)
            if monto_iva > 0:
                filas_resultado.append({
                    'Fecha': fecha,
                    'Tipo Doc': tipo_doc,
                    'Número Doc': folio,
                    'RUT': rut,
                    'Razón Social': razon_social,
                    'Cuenta': '1141001',  # IVA Crédito Fiscal
                    'Nombre Cuenta': 'IVA Crédito Fiscal',
                    'Debe': monto_iva,
                    'Haber': '',
                    'Centro Costo': '',
                    'Proyecto': '',
                    'Glosa': f'IVA {tipo_doc_desc} - {razon_social}',
                    'Referencia': folio
                })
        
        elif tipo_doc == "39":  # Boleta Electrónica
            # Para boletas, solo una fila de gasto (no hay IVA recuperable)
            filas_resultado.append({
                'Fecha': fecha,
                'Tipo Doc': tipo_doc,
                'Número Doc': folio,
                'RUT': rut,
                'Razón Social': razon_social,
                'Cuenta': '5111002',  # Gastos menores
                'Nombre Cuenta': 'Gastos Menores',
                'Debe': monto_total,
                'Haber': '',
                'Centro Costo': get_centro_costo_principal(fila, headers, mapeo_cc),
                'Proyecto': '',
                'Glosa': f'{tipo_doc_desc} - {razon_social}',
                'Referencia': folio
            })
        
        else:
            # Para otros tipos de documento, usar regla genérica
            filas_resultado.append({
                'Fecha': fecha,
                'Tipo Doc': tipo_doc,
                'Número Doc': folio,
                'RUT': rut,
                'Razón Social': razon_social,
                'Cuenta': '5111003',  # Gastos varios
                'Nombre Cuenta': 'Gastos Varios',
                'Debe': monto_total,
                'Haber': '',
                'Centro Costo': get_centro_costo_principal(fila, headers, mapeo_cc),
                'Proyecto': '',
                'Glosa': f'{tipo_doc_desc} - {razon_social}',
                'Referencia': folio
            })
    
    except Exception as e:
        logger.error(f"Error aplicando reglas para tipo {tipo_doc}: {str(e)}")
        # En caso de error, crear una fila básica
        filas_resultado.append({
            'Fecha': '',
            'Tipo Doc': tipo_doc,
            'Número Doc': '',
            'RUT': '',
            'Razón Social': '',
            'Cuenta': '5111099',
            'Nombre Cuenta': 'Gastos Sin Clasificar',
            'Debe': '',
            'Haber': '',
            'Centro Costo': '',
            'Proyecto': '',
            'Glosa': f'Error procesando: {str(e)}',
            'Referencia': ''
        })
    
    return filas_resultado

def get_centro_costo_principal(fila, headers, mapeo_cc):
    """
    Obtiene el centro de costo principal de una fila
    """
    # Buscar columnas de centros de costo conocidas
    cc_columns = ['PyC', 'EB', 'CO']
    
    for cc_col in cc_columns:
        if cc_col in headers:
            valor = fila.get(cc_col)
            if valor and str(valor).strip():
                # Aplicar mapeo si existe
                cc_mapeado = mapeo_cc.get(str(valor), str(valor))
                return cc_mapeado
    
    return ''

def procesar_filas_gastos_simple(filas_data, headers, mapeo_cc):
    """
    Versión simplificada del procesamiento de gastos
    """
    resumen = {
        'total_procesadas': len(filas_data),
        'con_centros_costo': 0,
        'sin_centros_costo': 0
    }
    
    for fila in filas_data:
        cc_count = contar_centros_costos(fila, headers, mapeo_cc)
        if cc_count > 0:
            resumen['con_centros_costo'] += 1
        else:
            resumen['sin_centros_costo'] += 1
    
    return {'resumen': resumen}

def crear_excel_resultado_gastos(filas_data, headers, resultado):
    """
    Crea un archivo Excel con los resultados del procesamiento
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Gastos Procesados"
    
    # Agregar headers
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Agregar datos
    for row_idx, fila in enumerate(filas_data, 2):
        for col_idx, header in enumerate(headers, 1):
            valor = fila.get(header)
            ws.cell(row=row_idx, column=col_idx, value=valor)
    
    # Agregar columna de estado
    estado_col = len(headers) + 1
    ws.cell(row=1, column=estado_col, value="Estado Procesamiento")
    
    for row_idx in range(2, len(filas_data) + 2):
        ws.cell(row=row_idx, column=estado_col, value="Procesado")
    
    return wb


# =====================================================
# FUNCIONES PARA CAPTURA MASIVA DE GASTOS
# =====================================================

def get_redis_client_db1():
    """
    Obtiene cliente Redis para db1 usando la configuración de Django
    Con soporte UTF-8 completo
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )

def get_redis_client_db1_binary():
    """
    Obtiene cliente Redis para db1 para datos binarios (sin decode_responses)
    Con soporte UTF-8 para metadatos
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=False,
            encoding='utf-8'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=False,
            encoding='utf-8'
        )

def serialize_excel_data(data):
    """
    Serializa datos de Excel para evitar problemas con datetime y otros tipos
    """
    if isinstance(data, dict):
        return {k: serialize_excel_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_excel_data(item) for item in data]
    elif hasattr(data, 'isoformat'):  # datetime objects
        return data.isoformat()
    elif isinstance(data, (str, int, float, bool)) or data is None:
        # Asegurar que las strings mantengan encoding UTF-8
        return data
    else:
        return data

def contar_centros_costos(fila, headers, mapeo_cc):
    """
    Cuenta cuántos centros de costos tiene una fila de gastos
    """
    centros_count = 0
    
    # Buscar columnas que contengan información de centros de costos
    cc_columns = []
    for header in headers:
        if header and ('centro' in str(header).lower() or 'cc' in str(header).lower() or 
                      'pyc' in str(header).lower() or 'ps' in str(header).lower() or 
                      'eb' in str(header).lower() or 'co' in str(header).lower()):
            cc_columns.append(header)
    
    # Contar valores no vacíos en columnas de centros de costos
    for cc_col in cc_columns:
        valor = fila.get(cc_col)
        if valor and str(valor).strip():
            centros_count += 1
    
    return min(centros_count, 3)  # Máximo 3 centros de costos

@shared_task(bind=True)
def procesar_captura_masiva_gastos_task(self, archivo_content, archivo_nombre, usuario_id, mapeo_cc=None):
    """
    Tarea principal que recibe el archivo Excel y procesa captura masiva de gastos
    """
    logger.info(f"🧾 Iniciando captura masiva de gastos para archivo: {archivo_nombre}")
    
    # Si no hay mapeo, usar diccionario vacío
    if mapeo_cc is None:
        mapeo_cc = {}
    
    try:
        # Configurar Redis db1 para resultados temporales
        redis_client = get_redis_client_db1()
        redis_client_binary = get_redis_client_db1_binary()
        
        # Metadatos iniciales de la tarea
        task_metadata = {
            'task_id': self.request.id,
            'usuario_id': usuario_id,
            'archivo_nombre': archivo_nombre,
            'estado': 'procesando',
            'timestamp_inicio': datetime.datetime.now().isoformat(),
            'progreso': 0,
            'total_filas': 0,
            'filas_procesadas': 0,
            'errores': []
        }
        
        # Guardar metadatos iniciales
        redis_client.set(
            f"captura_gastos_meta:{usuario_id}:{self.request.id}",
            json.dumps(task_metadata),
            ex=86400  # 24 horas
        )
        
        # Cargar el archivo Excel desde el contenido
        wb = load_workbook(BytesIO(archivo_content))
        ws = wb.active
        
        # Obtener headers de la primera fila
        headers = []
        for cell in ws[1]:
            headers.append(cell.value)
        
        logger.info(f"📋 Headers encontrados: {headers}")
        
        # Procesar filas desde la fila 2 (saltar header)
        filas_data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if any(row):  # Solo procesar filas que no estén completamente vacías
                fila_dict = dict(zip(headers, row))
                # Serializar datos para evitar problemas con datetime
                fila_dict = serialize_excel_data(fila_dict)
                filas_data.append(fila_dict)
        
        logger.info(f"📊 Total filas a procesar: {len(filas_data)}")
        
        # Actualizar metadatos con total de filas
        task_metadata['total_filas'] = len(filas_data)
        task_metadata['progreso'] = 10
        redis_client.set(
            f"captura_gastos_meta:{usuario_id}:{self.request.id}",
            json.dumps(task_metadata),
            ex=86400
        )
        
        # Procesar filas y generar archivo de resultado
        filas_procesadas = []
        errores = []
        
        for i, fila in enumerate(filas_data):
            try:
                # Aquí iría la lógica de procesamiento específica de gastos
                # Por ahora, simplemente agregamos la fila con un indicador de procesada
                fila_procesada = fila.copy()
                fila_procesada['__ESTADO__'] = 'Procesada'
                fila_procesada['__FECHA_PROCESO__'] = datetime.datetime.now().isoformat()
                filas_procesadas.append(fila_procesada)
                
                # Actualizar progreso cada 10 filas
                if i % 10 == 0:
                    progreso = 10 + int((i / len(filas_data)) * 80)  # De 10% a 90%
                    task_metadata['progreso'] = progreso
                    task_metadata['filas_procesadas'] = i + 1
                    redis_client.set(
                        f"captura_gastos_meta:{usuario_id}:{self.request.id}",
                        json.dumps(task_metadata),
                        ex=86400
                    )
                
            except Exception as e:
                error_msg = f"Error en fila {i+2}: {str(e)}"
                errores.append(error_msg)
                logger.error(error_msg)
        
        # Crear archivo Excel de resultado
        wb_resultado = Workbook()
        ws_resultado = wb_resultado.active
        ws_resultado.title = "Gastos Procesados"
        
        # Agregar headers (originales + nuevas columnas)
        headers_resultado = headers + ['__ESTADO__', '__FECHA_PROCESO__']
        ws_resultado.append(headers_resultado)
        
        # Agregar filas procesadas
        for fila in filas_procesadas:
            fila_valores = [fila.get(header, '') for header in headers_resultado]
            ws_resultado.append(fila_valores)
        
        # Guardar archivo en Redis
        archivo_buffer = BytesIO()
        wb_resultado.save(archivo_buffer)
        archivo_bytes = archivo_buffer.getvalue()
        
        # Nombre del archivo resultado
        nombre_base = archivo_nombre.rsplit('.', 1)[0] if '.' in archivo_nombre else archivo_nombre
        archivo_resultado_nombre = f"{nombre_base}_procesado.xlsx"
        
        # Guardar archivo en Redis
        redis_client_binary.set(
            f"captura_gastos_archivo:{usuario_id}:{self.request.id}",
            archivo_bytes,
            ex=86400  # 24 horas
        )
        
        # Actualizar metadatos finales
        task_metadata.update({
            'estado': 'completado',
            'timestamp_fin': datetime.datetime.now().isoformat(),
            'progreso': 100,
            'filas_procesadas': len(filas_procesadas),
            'total_errores': len(errores),
            'errores': errores[:10],  # Solo primeros 10 errores
            'archivo_resultado': archivo_resultado_nombre,
            'archivo_excel_disponible': True
        })
        
        redis_client.set(
            f"captura_gastos_meta:{usuario_id}:{self.request.id}",
            json.dumps(task_metadata),
            ex=86400
        )
        
        logger.info(f"✅ Captura masiva de gastos completada. Archivo: {archivo_resultado_nombre}")
        
        return {
            'status': 'SUCCESS',
            'task_id': self.request.id,
            'archivo_resultado': archivo_resultado_nombre,
            'filas_procesadas': len(filas_procesadas),
            'errores': len(errores)
        }
        
    except Exception as e:
        error_msg = f"Error en captura masiva de gastos: {str(e)}"
        logger.error(error_msg)
        
        # Actualizar metadatos con error
        task_metadata.update({
            'estado': 'error',
            'timestamp_fin': datetime.datetime.now().isoformat(),
            'error': error_msg
        })
        
        redis_client.set(
            f"captura_gastos_meta:{usuario_id}:{self.request.id}",
            json.dumps(task_metadata),
            ex=86400
        )
        
        raise

