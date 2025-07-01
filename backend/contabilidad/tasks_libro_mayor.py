# tasks_libro_mayor.py

import os
import re
import hashlib
import datetime
from decimal import Decimal

from django.utils import timezone
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import transaction
from celery import shared_task, chain
from celery.utils.log import get_task_logger
from openpyxl import load_workbook
from django.contrib.auth import get_user_model

from .models import (
    UploadLog,
    LibroMayorArchivo,
    CuentaContable,
    AperturaCuenta,
    MovimientoContable,
    TipoDocumento,
    NombreIngles,
    ClasificacionCuentaArchivo,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
    Incidencia,
    ExcepcionValidacion,
)

logger = get_task_logger(__name__)


def crear_chain_libro_mayor(upload_log_id, user_correo_bdo):
    """
    Crea un chain de tasks para procesar el libro mayor.
    Usamos .s() para el primer task y .si() para los demás para mantener
    los mismos argumentos en cada task del chain.
    """
    return chain(
        validar_nombre_archivo_libro_mayor.s(upload_log_id, user_correo_bdo),
        verificar_archivo_libro_mayor.si(upload_log_id, user_correo_bdo),
        validar_contenido_libro_mayor.si(upload_log_id, user_correo_bdo),
        procesar_libro_mayor_raw.si(upload_log_id, user_correo_bdo),
        generar_incidencias_libro_mayor.si(upload_log_id, user_correo_bdo),
        finalizar_procesamiento_libro_mayor.si(upload_log_id, user_correo_bdo),
    )
# ─── Utilidades ───────────────────────────────────────────────────────────────

def _parse_fecha(value):
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return timezone.now().date()


def _clean_header(h):
    if not isinstance(h, str):
        return ""
    hh = h.strip().upper()
    for a, b in [("Á","A"),("É","E"),("Í","I"),("Ó","O"),("Ú","U"),("Ñ","N")]:
        hh = hh.replace(a, b)
    return re.sub(r"[^A-Z0-9]", "", hh)


# ─── Tasks 1–3: Validaciones previas ──────────────────────────────────────────

@shared_task
def validar_nombre_archivo_libro_mayor(upload_log_id, user_correo_bdo):
    try:
        upload = UploadLog.objects.get(pk=upload_log_id)
        nombre = upload.nombre_archivo_original
        rut = upload.cliente.rut or str(upload.cliente.id)
        rut_clean = rut.replace(".", "").replace("-", "")
        pattern = rf"^{rut_clean}_(LibroMayor|Mayor)_(\d{{6}})\.xlsx?$"
        match = re.match(pattern, nombre, flags=re.IGNORECASE)
        if not match:
            msg = f"Nombre inválido: {nombre}"
            upload.estado  = "error"
            upload.errores = msg
            upload.save()
            raise ValueError(msg)
        periodo = match.group(2)
        resumen = upload.resumen or {}
        resumen["validacion_nombre"] = {"periodo": periodo}
        upload.resumen = resumen
        upload.estado = "procesando"
        upload.save(update_fields=["resumen","estado"])
        return upload_log_id
    except UploadLog.DoesNotExist:
        logger.error(f"UploadLog con id {upload_log_id} no encontrado")
        raise
    except Exception as e:
        logger.error(f"Error validando nombre archivo libro mayor {upload_log_id}: {e}")
        try:
            upload = UploadLog.objects.get(pk=upload_log_id)
            upload.estado = "error"
            upload.errores = f"Error validando nombre: {str(e)}"
            upload.save()
        except:
            pass
        raise


@shared_task
def verificar_archivo_libro_mayor(upload_log_id, user_correo_bdo):
    upload = UploadLog.objects.get(pk=upload_log_id)
    ruta_rel = upload.ruta_archivo
    if not ruta_rel:
        raise ValueError("Ruta de archivo no definida")
    full = default_storage.path(ruta_rel)
    if not os.path.exists(full):
        raise FileNotFoundError(full)
    with open(full, "rb") as f:
        data = f.read()
    upload.hash_archivo = hashlib.sha256(data).hexdigest()
    resumen = upload.resumen or {}
    resumen["verificacion_archivo"] = {"bytes": len(data)}
    upload.resumen = resumen
    upload.save(update_fields=["hash_archivo","resumen"])
    return upload_log_id


@shared_task
def validar_contenido_libro_mayor(upload_log_id, user_correo_bdo):
    upload = UploadLog.objects.get(pk=upload_log_id)
    full = default_storage.path(upload.ruta_archivo)
    wb = load_workbook(full, read_only=True, data_only=True)
    ws = wb.active
    headers = next(ws.iter_rows(min_row=9, max_row=9, values_only=True))
    cleaned = [_clean_header(h) for h in headers]
    required = {"CUENTA","FECHA","DEBE","HABER","DESCRIPCION"}
    if not required.issubset(cleaned):
        faltan = required - set(cleaned)
        msg = f"Headers faltantes: {faltan}"
        upload.estado  = "error"
        upload.errores = msg
        upload.save()
        raise ValueError(msg)
    # chequear datos en fila 11
    sample = list(ws.iter_rows(min_row=11, max_row=11, values_only=True))[0]
    if all(cell is None for cell in sample):
        msg = "Sin datos en fila 11"
        upload.estado  = "error"
        upload.errores = msg
        upload.save()
        raise ValueError(msg)
    resumen = upload.resumen or {}
    resumen["validacion_contenido"] = {"ok": True}
    upload.resumen = resumen
    upload.save(update_fields=["resumen"])
    return upload_log_id


# ─── Task 4: Procesar aperturas y movimientos ─────────────────────────────────

@shared_task
def procesar_libro_mayor_raw(upload_log_id, user_correo_bdo):
    upload = UploadLog.objects.get(pk=upload_log_id)
    inicio = timezone.now()
    full = default_storage.path(upload.ruta_archivo)
    wb = load_workbook(full, read_only=True, data_only=True)
    ws = wb.active

    # -- índices de columnas --
    headers = next(ws.iter_rows(min_row=9, max_row=9, values_only=True))
    idx = {_clean_header(h): i for i,h in enumerate(headers) if isinstance(h, str)}
    C, F, D, H, DS = idx["CUENTA"], idx["FECHA"], idx["DEBE"], idx["HABER"], idx["DESCRIPCION"]
    S = idx.get("SALDO")  # Column for SALDO
    TD = idx.get("TIPODOC") or idx.get("TIPODOC.")
    
    # Columnas adicionales que pueden estar presentes
    ND = idx.get("NUMERODOCUMENTO") or idx.get("NUMDOCUMENTO") or idx.get("NUMDOC") or idx.get("NUMERODOC")
    TP = idx.get("TIPO")
    NC = idx.get("NUMEROCOMPROBANTE") or idx.get("NUMCOMPROBANTE") or idx.get("COMPROBANTE") or idx.get("NCOMPROBANTE")
    NI = idx.get("NUMEROINTERNO") or idx.get("NUMINTERNO") or idx.get("INTERNO") or idx.get("NINTERNO")
    CC = idx.get("CENTROCOSTO") or idx.get("CENTRO_COSTO") or idx.get("CCOSTO") or idx.get("CENTRODECOSTO")
    AUX = idx.get("AUXILIAR")
    DG = idx.get("DETALLEGASTO") or idx.get("DETALLE_GASTO") or idx.get("GASTO") or idx.get("DETDEGASTOINSTFINANCIERO")
    
    logger.info(f"Columnas detectadas: {list(idx.keys())}")
    logger.info(f"Columnas adicionales encontradas: ND={ND}, TP={TP}, NC={NC}, NI={NI}, CC={CC}, AUX={AUX}, DG={DG}")

    cliente = upload.cliente
    cliente_id = cliente.id
    cierre = upload.cierre

    # 1. CARGA INICIAL - Una sola vez al inicio
    nombres_ingles_map = {
        ni.cuenta_codigo: ni.nombre_ingles
        for ni in NombreIngles.objects.filter(cliente=cliente)
    }
    clasif_raw_map = {
        c.numero_cuenta: c
        for c in ClasificacionCuentaArchivo.objects.filter(cliente=cliente)
    }
    processed_accounts = {}
    aperturas = []
    movimientos = []
    stats = {"cuentas_nuevas": 0, "aperturas": 0, "movimientos": 0}
    
    logger.info(f"Cargados {len(nombres_ingles_map)} nombres en inglés para cliente {cliente_id}")
    logger.info(f"Cargados {len(clasif_raw_map)} registros de clasificación RAW para cliente {cliente_id}")

    # -- helper para tipos de documento (con caché) --
    def get_tipo_doc(code):
        code = code.strip()
        key = f"tipodoc:{cliente_id}:{code}"
        td_id = cache.get(key)
        if td_id is None:
            td = TipoDocumento.objects.filter(cliente=cliente, codigo=code).first()
            td_id = td.id if td else None
            cache.set(key, td_id, timeout=3600)
        return TipoDocumento.objects.filter(pk=td_id).first() if td_id else None

    # 2. FUNCIONES AUXILIARES
    def procesar_saldo_anterior(row, cierre, code, aperturas, stats):
        """Procesa un saldo anterior y lo añade a la lista de aperturas"""
        try:
            saldo = Decimal(row[S] if S and row[S] else (row[D] or 0))
            cuenta_obj = processed_accounts[code]
            apertura = AperturaCuenta(
                cierre=cierre,
                cuenta=cuenta_obj,
                saldo_anterior=saldo
            )
            aperturas.append(apertura)
            stats["aperturas"] += 1
            logger.debug(f"Saldo anterior procesado para cuenta {code}: {saldo}")
        except Exception as e:
            logger.error(f"Error procesando saldo anterior para cuenta {code}: {e}")

    def procesar_movimiento(row, cierre, cuenta_obj, get_tipo_doc, movimientos, stats, indices_cols):
        """Procesa un movimiento contable y lo añade a la lista de movimientos"""
        try:
            # Desempaquetar índices de columnas
            ND, TP, NC, NI, CC, AUX, DG, DS, TD, D, H, F = indices_cols
            
            # Campos básicos
            codigo_td = (str(row[TD]).strip()[:10] if (TD is not None and row[TD]) else "")
            
            # Capturar TODOS los datos disponibles del Excel
            mov = MovimientoContable(
                cierre=cierre,
                cuenta=cuenta_obj,
                fecha=_parse_fecha(row[F]),
                debe=Decimal(row[D] or 0),
                haber=Decimal(row[H] or 0),
                descripcion=str(row[DS] or "")[:500] if (DS is not None and row[DS]) else "",
                tipo_doc_codigo=codigo_td,
                # Campos adicionales si están disponibles
                numero_documento=str(row[ND])[:50] if (ND is not None and row[ND]) else "",
                tipo=str(row[TP])[:50] if (TP is not None and row[TP]) else "",
                numero_comprobante=str(row[NC])[:50] if (NC is not None and row[NC]) else "",
                numero_interno=str(row[NI])[:50] if (NI is not None and row[NI]) else "",
                detalle_gasto=str(row[DG]) if (DG is not None and row[DG]) else "",
            )
            
            # Asociar tipo_documento si existe
            if codigo_td:
                td_obj = get_tipo_doc(codigo_td)
                if td_obj:
                    mov.tipo_documento = td_obj
            
            # TODO: Manejar centro_costo y auxiliar si hay columnas disponibles
            # Estas requieren lookup a otras tablas, se puede implementar después
            if CC is not None and row[CC]:
                logger.debug(f"Centro de costo detectado pero no procesado: {row[CC]}")
            if AUX is not None and row[AUX]:
                logger.debug(f"Auxiliar detectado pero no procesado: {row[AUX]}")
            
            # Debug para verificar que se están guardando los campos
            if ND is not None and row[ND]:
                logger.debug(f"Guardando número documento: {row[ND]}")
            if NC is not None and row[NC]:
                logger.debug(f"Guardando número comprobante: {row[NC]}")
            if NI is not None and row[NI]:
                logger.debug(f"Guardando número interno: {row[NI]}")
            if DG is not None and row[DG]:
                logger.debug(f"Guardando detalle gasto: {row[DG]}")
            
            movimientos.append(mov)
            stats["movimientos"] += 1
        except Exception as e:
            logger.error(f"Error procesando movimiento: {e}")
            # Crear movimiento con campos mínimos para no perder el registro
            try:
                mov_minimo = MovimientoContable(
                    cierre=cierre,
                    cuenta=cuenta_obj,
                    fecha=_parse_fecha(row[F]),
                    debe=Decimal(row[D] or 0),
                    haber=Decimal(row[H] or 0),
                    descripcion="Error procesando campos adicionales",
                    flag_incompleto=True
                )
                movimientos.append(mov_minimo)
                stats["movimientos"] += 1
            except Exception as e2:
                logger.error(f"Error creando movimiento mínimo: {e2}")

    # 3. BUCLE PRINCIPAL
    current_code = None
    
    with transaction.atomic():
        for row in ws.iter_rows(min_row=11, values_only=True):
            cell = row[C]
            
            # SALDO ANTERIOR → nuevo bloque de cuenta
            if isinstance(cell, str) and cell.startswith("SALDO ANTERIOR"):
                # Extrae code y nombre real de la cuenta
                # Formato: "SALDO ANTERIOR DE LA CUENTA: 5-04-004-002-0002  Comisiones y gastos bancarios"
                texto_completo = cell.split(":", 1)[1].strip()  # "5-04-004-002-0002  Comisiones y gastos bancarios"
                
                # Separar código y nombre
                partes = texto_completo.split(" ", 1)  # ["5-04-004-002-0002", "Comisiones y gastos bancarios"]
                code = partes[0].strip()
                nombre_real = partes[1].strip() if len(partes) > 1 else f"Cuenta {code}"
                
                current_code = code
                
                # Si code no está en processed_accounts
                if code not in processed_accounts:
                    # get_or_create la CuentaContable CON EL NOMBRE REAL
                    cuenta, created = CuentaContable.objects.get_or_create(
                        cliente=cliente,
                        codigo=code[:50],
                        defaults={"nombre": nombre_real[:50]}  # Usar el nombre real del Excel
                    )
                    # Si la cuenta ya existía pero no tenía nombre, actualizarlo
                    if not created and (not cuenta.nombre or cuenta.nombre.startswith("Cuenta ")):
                        cuenta.nombre = nombre_real[:50]
                        cuenta.save(update_fields=["nombre"])
                        logger.debug(f"Actualizado nombre de cuenta existente {cuenta.codigo}: {nombre_real}")
                    
                    # Incrementar stats["cuentas_nuevas"] si es nueva
                    if created:
                        stats["cuentas_nuevas"] += 1
                        logger.debug(f"Cuenta nueva creada: {code} - {nombre_real}")
                    
                    # Aplicar nombre en inglés UNA SOLA VEZ usando nombres_ingles_map
                    ing = nombres_ingles_map.get(cuenta.codigo)
                    if ing and not cuenta.nombre_en:
                        cuenta.nombre_en = ing
                        cuenta.save(update_fields=["nombre_en"])
                        logger.debug(f"Aplicado nombre en inglés a cuenta {cuenta.codigo}: {ing}")
                    
                    # Aplicar clasificación UNA SOLA VEZ usando clasif_raw_map
                    raw = clasif_raw_map.get(cuenta.codigo)
                    if raw:
                        logger.debug(f"Aplicando clasificaciones para cuenta {cuenta.codigo}")
                        for set_name, valor in (raw.clasificaciones or {}).items():
                            set_obj, _ = ClasificacionSet.objects.get_or_create(
                                cliente=cliente, 
                                nombre=set_name
                            )
                            opt_obj, _ = ClasificacionOption.objects.get_or_create(
                                set_clas=set_obj, 
                                valor=str(valor)
                            )
                            AccountClassification.objects.update_or_create(
                                cuenta=cuenta,
                                set_clas=set_obj,
                                defaults={"opcion": opt_obj}
                            )
                    
                    # Guardar la cuenta en processed_accounts
                    processed_accounts[code] = cuenta
                
                # Llamar a procesar_saldo_anterior para añadir la apertura
                procesar_saldo_anterior(row, cierre, code, aperturas, stats)
                continue
            
            # Si current_code definido y row[F] no es None
            if current_code and row[F] is not None:
                # Recuperar cuenta_obj = processed_accounts[current_code]
                cuenta_obj = processed_accounts[current_code]
                # Llamar a procesar_movimiento para añadir el movimiento
                indices_cols = (ND, TP, NC, NI, CC, AUX, DG, DS, TD, D, H, F)
                procesar_movimiento(row, cierre, cuenta_obj, get_tipo_doc, movimientos, stats, indices_cols)
                continue
            
            # Ignorar el resto de filas

        # 4. BULK-CREATE Y RESUMEN
        # Al final, bulk-create de aperturas y movimientos
        if aperturas:
            AperturaCuenta.objects.bulk_create(aperturas, batch_size=500)
        if movimientos:
            MovimientoContable.objects.bulk_create(movimientos, batch_size=500)

    # Guardar stats en upload.resumen
    resumen = upload.resumen or {}
    resumen["procesamiento"] = stats
    upload.resumen = resumen
    upload.tiempo_procesamiento = timezone.now() - inicio
    upload.save(update_fields=["resumen", "tiempo_procesamiento"])

    logger.info(f"Procesamiento completado: {stats}")
    return upload_log_id

# ─── Task 5: Generar incidencias ───────────────────────────────────────────────

@shared_task
def generar_incidencias_libro_mayor(upload_log_id, user_correo_bdo):
    User = get_user_model()
    try:
        creador = User.objects.get(correo_bdo=user_correo_bdo)
    except User.DoesNotExist:
        creador = None

    upload_log = UploadLog.objects.get(id=upload_log_id)
    cierre = upload_log.cierre

    # Mapear clasificaciones ANTES de generar incidencias
    try:
        from .tasks_cuentas_bulk import mapear_clasificaciones_con_cuentas
        
        # Verificar si hay registros RAW de clasificaciones para el cliente
        registros_raw_count = ClasificacionCuentaArchivo.objects.filter(
            cliente=upload_log.cliente
        ).count()
        logger.info(f"Registros RAW de clasificaciones disponibles: {registros_raw_count} para cliente {upload_log.cliente.id}")
        
        logger.info(f"Iniciando mapeo de clasificaciones para upload_log {upload_log_id}")
        resultado_mapeo = mapear_clasificaciones_con_cuentas(upload_log_id)
        logger.info(f"Mapeo de clasificaciones completado: {resultado_mapeo}")
        
        # Verificar si hay clasificaciones disponibles después del mapeo
        total_clasificaciones = AccountClassification.objects.filter(
            cuenta__cliente=upload_log.cliente
        ).count()
        logger.info(f"Total de clasificaciones después del mapeo: {total_clasificaciones}")
        
    except ImportError as e:
        logger.warning(f"No se pudo importar mapear_clasificaciones_con_cuentas: {e}")
    except Exception as e:
        logger.error(f"Error en mapeo de clasificaciones: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    # Cargar excepciones activas para optimizar consultas
    excepciones_tipo_doc_null = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='movimientos_tipodoc_nulo',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_tipo_doc_no_reconocido = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='tipos_doc_no_reconocidos',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_sin_nombre_ingles = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_nombre_ingles',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    excepciones_sin_clasificacion = set(
        ExcepcionValidacion.objects.filter(
            cliente=upload_log.cliente,
            tipo_excepcion='cuentas_sin_clasificacion',
            activa=True
        ).values_list('codigo_cuenta', flat=True)
    )
    
    logger.info(f"Excepciones cargadas - Tipo doc null: {len(excepciones_tipo_doc_null)}, "
               f"Tipo doc no reconocido: {len(excepciones_tipo_doc_no_reconocido)}, "
               f"Sin nombre inglés: {len(excepciones_sin_nombre_ingles)}, "
               f"Sin clasificación: {len(excepciones_sin_clasificacion)}")

    Incidencia.objects.filter(cierre=cierre).delete()
    creadas = existentes = 0

    # — Cuentas sin clasificación —
    # Verificar si hay clasificaciones configuradas para este cliente
    hay_clasificaciones_raw = ClasificacionCuentaArchivo.objects.filter(
        cliente=upload_log.cliente
    ).exists()
    
    hay_sets_clasificacion = ClasificacionSet.objects.filter(
        cliente=upload_log.cliente
    ).exists()
    
    logger.info(f"¿Hay clasificaciones RAW para cliente? {hay_clasificaciones_raw}")
    logger.info(f"¿Hay sets de clasificación para cliente? {hay_sets_clasificacion}")
    
    # Solo generar incidencias de clasificación si hay clasificaciones configuradas Y archivos RAW
    if hay_clasificaciones_raw and hay_sets_clasificacion:
        # Obtener IDs de cuentas clasificadas para este cliente
        cuentas_clasificadas_ids = AccountClassification.objects.filter(
            cuenta__cliente=upload_log.cliente
        ).values_list('cuenta_id', flat=True)
        
        logger.info(f"Cuentas clasificadas encontradas: {len(cuentas_clasificadas_ids)} para cliente {upload_log.cliente.id}")
        
        sin_clas = CuentaContable.objects.filter(
            movimientocontable__cierre=cierre
        ).distinct().exclude(
            id__in=cuentas_clasificadas_ids
        ).exclude(
            codigo__in=excepciones_sin_clasificacion  # Excluir cuentas marcadas como "No aplica"
        )
        
        total_cuentas_en_movimientos = CuentaContable.objects.filter(
            movimientocontable__cierre=cierre
        ).distinct().count()
        
        logger.info(f"Total cuentas en movimientos: {total_cuentas_en_movimientos}")
        logger.info(f"Cuentas sin clasificación: {sin_clas.count()}")
        
        for c in sin_clas:
            obj, new = Incidencia.objects.get_or_create(
                cierre=cierre,
                tipo=Incidencia.CUENTA_NO_CLASIFICADA,
                cuenta_codigo=c.codigo,
                defaults={'descripcion': f"Cuenta {c.codigo} sin clasificación", 'creada_por': creador}
            )
            if new:
                creadas += 1
            else:
                existentes += 1
    elif hay_sets_clasificacion and not hay_clasificaciones_raw:
        logger.info(f"Cliente {upload_log.cliente.id} tiene sets de clasificación pero no hay archivo RAW reciente.")
        logger.info(f"Para aplicar clasificaciones, suba primero un archivo de clasificaciones correspondiente a las cuentas del libro mayor actual.")
    else:
        logger.info(f"No hay clasificaciones configuradas para cliente {upload_log.cliente.id}, omitiendo incidencias de clasificación")

    # — Cuentas sin nombre inglés (bilingüe) —
    if upload_log.cliente.bilingue:
        # Cargar nombres en inglés disponibles para este cliente
        nombres_ingles_disponibles = set(
            NombreIngles.objects.filter(cliente=upload_log.cliente)
            .values_list('cuenta_codigo', flat=True)
        )
        
        # Obtener cuentas que aparecen en movimientos pero no tienen nombre_en
        cuentas_sin_nombre_en = CuentaContable.objects.filter(
            movimientocontable__cierre=cierre,
            nombre_en__isnull=True
        ).distinct()
        
        for c in cuentas_sin_nombre_en:
            # Solo crear incidencia si NO existe un nombre en inglés disponible 
            # Y la cuenta no está marcada como excepción
            if c.codigo not in nombres_ingles_disponibles and c.codigo not in excepciones_sin_nombre_ingles:
                obj, new = Incidencia.objects.get_or_create(
                    cierre=cierre,
                    tipo=Incidencia.CUENTA_SIN_INGLES,
                    cuenta_codigo=c.codigo,
                    defaults={'descripcion': f"Cuenta {c.codigo} sin nombre en inglés", 'creada_por': creador}
                )
                if new:
                    creadas += 1
                else:
                    existentes += 1
            else:
                # Si existe nombre en inglés pero no está aplicado, intentar aplicarlo
                try:
                    nombre_ing = NombreIngles.objects.filter(
                        cliente=upload_log.cliente,
                        cuenta_codigo=c.codigo
                    ).first()
                    if nombre_ing:
                        c.nombre_en = nombre_ing.nombre_ingles
                        c.save(update_fields=['nombre_en'])
                        logger.info(f"Aplicado nombre en inglés a cuenta {c.codigo}: {nombre_ing.nombre_ingles}")
                except Exception as e:
                    logger.error(f"Error aplicando nombre en inglés a cuenta {c.codigo}: {e}")

    # — Movimientos —
    movimientos = MovimientoContable.objects.filter(cierre=cierre).select_related('cuenta')
    for mov in movimientos:
        # Verificar si la cuenta tiene excepción para tipo de documento nulo
        if not mov.tipo_doc_codigo:
            if mov.cuenta.codigo not in excepciones_tipo_doc_null:
                obj, new = Incidencia.objects.get_or_create(
                    cierre=cierre,
                    tipo=Incidencia.DOC_NULL,
                    cuenta_codigo=mov.cuenta.codigo,
                    defaults={'descripcion': f"Mov {mov.id} sin código de documento", 'creada_por': creador}
                )
                if new:
                    creadas += 1
                else:
                    existentes += 1
            continue

        # Verificar si la cuenta tiene excepción para tipos de documento no reconocidos
        if not mov.tipo_documento:
            if mov.cuenta.codigo not in excepciones_tipo_doc_no_reconocido:
                obj, new = Incidencia.objects.get_or_create(
                    cierre=cierre,
                    tipo=Incidencia.DOC_NO_RECONOCIDO,
                    tipo_doc_codigo=mov.tipo_doc_codigo,
                    defaults={'descripcion': f"Mov {mov.id}: tipo '{mov.tipo_doc_codigo}' no reconocido", 'creada_por': creador}
                )
                if new:
                    creadas += 1
                else:
                    existentes += 1

    # Guardar resumen…
    resumen = upload_log.resumen or {}
    resumen['incidencias'] = {
        'creadas': creadas,
        'existentes': existentes,
        'total_bd': Incidencia.objects.filter(cierre=cierre).count()
    }
    upload_log.resumen = resumen
    upload_log.save(update_fields=['resumen'])

    return upload_log_id

# ─── Task 6: Finalizar y limpiar ───────────────────────────────────────────────

@shared_task
def finalizar_procesamiento_libro_mayor(upload_log_id, user_correo_bdo):
    upload = UploadLog.objects.get(pk=upload_log_id)
    cierre = upload.cierre

    # NUEVO: Auto-incrementar iteración para libro mayor
    if upload.tipo_upload == 'libro_mayor' and upload.cierre:
        iteraciones_anteriores = UploadLog.objects.filter(
            cierre=upload.cierre,
            tipo_upload='libro_mayor',
            estado='completado'
        ).exclude(id=upload.id).count()
        
        upload.iteracion = iteraciones_anteriores + 1
        logger.info(f"Upload {upload.id} asignado iteración {upload.iteracion}")

    # marcar completado
    upload.estado = "completado"
    upload.save(update_fields=["estado", "iteracion"])

    # Crear el registro de LibroMayorArchivo para que el frontend pueda encontrarlo
    try:
        crear_registro_libro_mayor_archivo(upload_log_id)
        logger.info(f"Registro LibroMayorArchivo creado para upload_log {upload_log_id}")
    except Exception as e:
        logger.error(f"Error creando registro LibroMayorArchivo: {e}")

    # NUEVO: Crear snapshot de incidencias consolidadas
    try:
        crear_snapshot_incidencias_consolidadas(upload_log_id)
        logger.info(f"Snapshot de incidencias creado para upload_log {upload_log_id}")
    except Exception as e:
        logger.error(f"Error creando snapshot de incidencias: {e}")

    # post-procesos asíncronos - clasificaciones ya se procesaron en generar_incidencias
    # (se movió el mapeo de clasificaciones para que ocurra antes de generar incidencias)

    # Aplicar nombres en inglés pendientes
    try:
        aplicar_nombres_ingles_pendientes(upload_log_id)
        logger.info(f"Aplicados nombres en inglés pendientes para upload_log {upload_log_id}")
    except Exception as e:
        logger.error(f"Error aplicando nombres en inglés: {e}")

    # limpiar archivo temp
    try:
        path = default_storage.path(upload.ruta_archivo)
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"No se eliminó temp: {e}")

    stats_proc = upload.resumen.get("procesamiento", {})
    stats_inc  = upload.resumen.get("incidencias", {})
    msg = (
        f"Movimientos: {stats_proc.get('movimientos',0)}, "
        f"Aperturas: {stats_proc.get('aperturas',0)}, "
        f"Incidencias: {stats_inc.get('creadas',0)}"
    )
    return msg


def aplicar_nombres_ingles_pendientes(upload_log_id):
    """
    Aplica nombres en inglés pendientes a las cuentas que no los tienen
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        cliente = upload_log.cliente
        
        # Obtener mapeo de nombres en inglés
        nombres_ingles_map = {
            ni.cuenta_codigo: ni.nombre_ingles
            for ni in NombreIngles.objects.filter(cliente=cliente)
        }
        
        # Aplicar a cuentas que no tienen nombre en inglés
        cuentas_sin_nombre = CuentaContable.objects.filter(
            cliente=cliente,
            nombre_en__isnull=True,
            codigo__in=nombres_ingles_map.keys()
        )
        
        aplicados = 0
        for cuenta in cuentas_sin_nombre:
            if cuenta.codigo in nombres_ingles_map:
                cuenta.nombre_en = nombres_ingles_map[cuenta.codigo]
                cuenta.save(update_fields=['nombre_en'])
                aplicados += 1
        
        logger.info(f"Aplicados {aplicados} nombres en inglés pendientes para cliente {cliente.id}")
        
    except Exception as e:
        logger.error(f"Error en aplicar_nombres_ingles_pendientes: {e}")

@shared_task
def mapear_clasificaciones_desde_sets_existentes(cliente_id, cierre_id=None):
    """
    Intenta mapear cuentas a clasificaciones usando sets y opciones existentes
    cuando no hay archivos RAW disponibles. Útil para casos donde se tienen
    sets configurados pero se necesita aplicar a un nuevo conjunto de cuentas.
    """
    try:
        from .models import Cliente, CierreContabilidad, CuentaContable
        
        cliente = Cliente.objects.get(id=cliente_id)
        logger.info(f"Iniciando mapeo desde sets existentes para cliente {cliente_id}")
        
        # Buscar cierre
        if cierre_id:
            cierre = CierreContabilidad.objects.filter(id=cierre_id, cliente=cliente).first()
        else:
            cierre = CierreContabilidad.objects.filter(
                cliente=cliente, 
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        
        if not cierre:
            return {'error': f'No hay cierre activo para cliente {cliente_id}'}
        
        # Obtener sets de clasificación
        sets_clasificacion = ClasificacionSet.objects.filter(cliente=cliente)
        if not sets_clasificacion.exists():
            return {'error': f'No hay sets de clasificación para cliente {cliente_id}'}
        
        # Obtener cuentas del cierre actual
        cuentas = CuentaContable.objects.filter(
            movimientocontable__cierre=cierre
        ).distinct()
        
        logger.info(f"Encontradas {cuentas.count()} cuentas en el cierre {cierre.id}")
        logger.info(f"Encontrados {sets_clasificacion.count()} sets de clasificación")
        
        # Aquí podrías implementar lógica de mapeo inteligente
        # Por ejemplo, mapear por patrones de códigos de cuenta, nombres, etc.
        # Por ahora, solo retornamos información para que el usuario tome decisiones
        
        return {
            'info': f'Análisis completado para cliente {cliente_id}',
            'total_cuentas': cuentas.count(),
            'total_sets': sets_clasificacion.count(),
            'sets_disponibles': list(sets_clasificacion.values_list('nombre', flat=True)),
            'mensaje': 'Para aplicar clasificaciones, suba un archivo de clasificaciones que mapee las cuentas actuales con los sets existentes.'
        }
        
    except Exception as e:
        logger.error(f"Error en mapeo desde sets existentes: {e}")
        return {'error': str(e)}


def crear_registro_libro_mayor_archivo(upload_log_id):
    """
    Crea el registro LibroMayorArchivo necesario para que el frontend
    pueda mostrar el estado correcto del libro mayor
    """
    from django.core.files.base import ContentFile
    
    upload_log = UploadLog.objects.get(id=upload_log_id)
    
    # Extraer el período del nombre del archivo
    rut_limpio = upload_log.cliente.rut.replace(".", "").replace("-", "") if upload_log.cliente.rut else str(upload_log.cliente.id)
    nombre_sin_ext = re.sub(r"\.(xlsx|xls)$", "", upload_log.nombre_archivo_original, flags=re.IGNORECASE)
    patron_periodo = rf"^{rut_limpio}_(LibroMayor|Mayor)_(\d{{6}})$"
    match = re.match(patron_periodo, nombre_sin_ext)
    periodo = match.group(2) if match else "000000"
    
    # Leer el archivo original para guardarlo en LibroMayorArchivo
    ruta_completa = default_storage.path(upload_log.ruta_archivo)
    if os.path.exists(ruta_completa):
        with open(ruta_completa, "rb") as f:
            contenido = f.read()
        
        nombre_final = f"libro_mayor_{upload_log.cliente.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        archivo_obj, created = LibroMayorArchivo.objects.get_or_create(
            cliente=upload_log.cliente,
            cierre=upload_log.cierre,
            defaults={
                "archivo": ContentFile(contenido, name=nombre_final),
                "estado": "completado",
                "procesado": True,
                "upload_log": upload_log,
                "periodo": periodo,
                "errores": "",
            },
        )
        
        if not created:
            # Si ya existe, actualizar el estado
            archivo_obj.estado = "completado"
            archivo_obj.procesado = True
            archivo_obj.upload_log = upload_log
            archivo_obj.errores = ""
            archivo_obj.save(update_fields=["estado", "procesado", "upload_log", "errores"])
        
        logger.info(f"LibroMayorArchivo {'creado' if created else 'actualizado'} para upload_log {upload_log_id}")
    else:
        logger.warning(f"Archivo temporal no encontrado para upload_log {upload_log_id}")

# ─── NUEVO: Snapshot de Incidencias ──────────────────────────────────────────

def crear_snapshot_incidencias_consolidadas(upload_log_id):
    """
    Crea un snapshot de las incidencias consolidadas y lo guarda en el resumen del UploadLog
    """
    import json
    from collections import defaultdict
    from django.utils import timezone
    
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)
        
        if not upload_log.cierre:
            logger.warning(f"UploadLog {upload_log_id} no tiene cierre asociado")
            return
        
        # Obtener incidencias del cierre
        incidencias_query = Incidencia.objects.filter(cierre_id=upload_log.cierre.id)
        
        if not incidencias_query.exists():
            # No hay incidencias - crear snapshot vacío
            snapshot = {
                'iteracion': upload_log.iteracion,
                'timestamp': timezone.now().isoformat(),
                'incidencias_detectadas': [],
                'estadisticas': {
                    'total_incidencias': 0,
                    'por_tipo': {}
                },
                'total_elementos_afectados': 0,
                'comparacion_anterior': None,
                'sin_incidencias': True,  # Flag para indicar que no hay incidencias
                'mensaje_sin_incidencias': 'Procesamiento completado sin incidencias detectadas'
            }
        else:
            # Agrupar incidencias por tipo (igual que en views/incidencias.py)
            incidencias_agrupadas = defaultdict(list)
            
            for inc in incidencias_query:
                incidencias_agrupadas[inc.tipo].append(inc)
            
            # Transformar a formato consolidado
            incidencias_consolidadas = []
            
            for tipo, incidencias_list in incidencias_agrupadas.items():
                cantidad_total = len(incidencias_list)
                
                # Determinar severidad
                if cantidad_total >= 50:
                    severidad = 'critica'
                elif cantidad_total >= 20:
                    severidad = 'alta'
                elif cantidad_total >= 5:
                    severidad = 'media'
                else:
                    severidad = 'baja'
                
                # Crear mensaje descriptivo
                tipo_display = dict(Incidencia.TIPO_CHOICES).get(tipo, tipo)
                
                if tipo == Incidencia.CUENTA_NO_CLASIFICADA:
                    mensaje_usuario = f"Se encontraron {cantidad_total} cuentas sin clasificación"
                    accion_sugerida = "Revisar y clasificar las cuentas pendientes en el sistema de clasificaciones"
                elif tipo == Incidencia.CUENTA_SIN_INGLES:
                    mensaje_usuario = f"Se encontraron {cantidad_total} cuentas sin traducción al inglés"
                    accion_sugerida = "Completar las traducciones faltantes en la sección de Nombres en Inglés"
                elif tipo == Incidencia.DOC_NO_RECONOCIDO:
                    mensaje_usuario = f"Se encontraron {cantidad_total} documentos con tipos no reconocidos"
                    accion_sugerida = "Revisar y agregar los tipos de documento faltantes"
                elif tipo == Incidencia.DOC_NULL:
                    mensaje_usuario = f"Se encontraron {cantidad_total} movimientos sin tipo de documento"
                    accion_sugerida = "Corregir los movimientos que no tienen tipo de documento asignado"
                else:
                    mensaje_usuario = f"Se encontraron {cantidad_total} incidencias de tipo {tipo_display}"
                    accion_sugerida = "Revisar y corregir las incidencias detectadas"
                
                # Recopilar elementos afectados (todos para el modal)
                elementos_afectados = []
                for inc in incidencias_list:  # Incluir TODOS los elementos
                    if inc.cuenta_codigo:
                        elementos_afectados.append({
                            'tipo': 'cuenta',
                            'codigo': inc.cuenta_codigo,
                            'descripcion': inc.descripcion or ''
                        })
                    if inc.tipo_doc_codigo:
                        elementos_afectados.append({
                            'tipo': 'documento',
                            'codigo': inc.tipo_doc_codigo,
                            'descripcion': inc.descripcion or ''
                        })
                
                incidencias_consolidadas.append({
                    'id': f"consolidada_{tipo}_{upload_log.cierre.id}",
                    'tipo_incidencia': tipo,
                    'tipo_codigo': tipo,
                    'codigo_problema': tipo,
                    'cantidad_afectada': cantidad_total,
                    'severidad': severidad,
                    'severidad_codigo': severidad,
                    'estado': 'activa',
                    'estado_codigo': 'activa',
                    'mensaje_usuario': mensaje_usuario,
                    'accion_sugerida': accion_sugerida,
                    'elementos_afectados': elementos_afectados,
                    'detalle_muestra': {
                        'primeros_ejemplos': [
                            {
                                'cuenta_codigo': inc.cuenta_codigo,
                                'tipo_doc_codigo': inc.tipo_doc_codigo,
                                'descripcion': inc.descripcion
                            } for inc in incidencias_list[:5]
                        ]
                    },
                    'fecha_deteccion': min(inc.fecha_creacion for inc in incidencias_list).isoformat(),
                    'fecha_resolucion': None,
                    'resuelto_por': None,
                })
            
            # Ordenar por severidad y cantidad
            severidad_order = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
            incidencias_consolidadas.sort(
                key=lambda x: (severidad_order.get(x['severidad'], 4), -x['cantidad_afectada'])
            )
            
            # Estadísticas
            estadisticas = {
                'total_incidencias': len(incidencias_consolidadas),
                'por_tipo': {}
            }
            
            for inc in incidencias_consolidadas:
                tipo = inc['tipo_incidencia']
                estadisticas['por_tipo'][tipo] = estadisticas['por_tipo'].get(tipo, 0) + 1
            
            # Comparar con iteración anterior si existe
            comparacion_anterior = comparar_con_iteracion_anterior(upload_log, incidencias_consolidadas)
            
            snapshot = {
                'iteracion': upload_log.iteracion,
                'timestamp': timezone.now().isoformat(),
                'incidencias_detectadas': incidencias_consolidadas,
                'estadisticas': estadisticas,
                'total_elementos_afectados': sum(inc['cantidad_afectada'] for inc in incidencias_consolidadas),
                'comparacion_anterior': comparacion_anterior,
                'sin_incidencias': False,  # Flag para indicar que SÍ hay incidencias
                'mensaje_sin_incidencias': None
            }
        
        # Guardar snapshot en el resumen del UploadLog
        if not upload_log.resumen:
            upload_log.resumen = {}
        
        upload_log.resumen['incidencias_snapshot'] = snapshot
        upload_log.save(update_fields=['resumen'])
        
        logger.info(f"Snapshot de incidencias creado para iteración {upload_log.iteracion} "
                   f"con {len(snapshot['incidencias_detectadas'])} tipos de incidencias")
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error creando snapshot de incidencias para upload_log {upload_log_id}: {e}")
        raise


def comparar_con_iteracion_anterior(upload_log_actual, incidencias_actuales):
    """
    Compara las incidencias actuales con la iteración anterior
    """
    try:
        if upload_log_actual.iteracion <= 1:
            return {'es_primera_iteracion': True}
        
        upload_anterior = UploadLog.objects.filter(
            cierre=upload_log_actual.cierre,
            tipo_upload='libro_mayor',
            iteracion=upload_log_actual.iteracion - 1,
            estado='completado'
        ).first()
        
        if not upload_anterior or not upload_anterior.resumen:
            return {'anterior_no_encontrada': True}
        
        snapshot_anterior = upload_anterior.resumen.get('incidencias_snapshot')
        if not snapshot_anterior:
            return {'snapshot_anterior_no_encontrado': True}
        
        incidencias_anteriores = snapshot_anterior.get('incidencias_detectadas', [])
        
        # Comparación simple por tipo
        tipos_anteriores = {inc['tipo_codigo']: inc['cantidad_afectada'] for inc in incidencias_anteriores}
        tipos_actuales = {inc['tipo_codigo']: inc['cantidad_afectada'] for inc in incidencias_actuales}
        
        cambios = {
            'resueltas': [],
            'nuevas': [],
            'empeoradas': [],
            'mejoradas': []
        }
        
        # Tipos que mejoraron o empeoraron
        for tipo, cantidad_actual in tipos_actuales.items():
            cantidad_anterior = tipos_anteriores.get(tipo, 0)
            
            if cantidad_anterior > cantidad_actual:
                cambios['mejoradas'].append({
                    'tipo': tipo,
                    'anterior': cantidad_anterior,
                    'actual': cantidad_actual,
                    'diferencia': cantidad_anterior - cantidad_actual
                })
            elif cantidad_anterior < cantidad_actual:
                cambios['empeoradas'].append({
                    'tipo': tipo,
                    'anterior': cantidad_anterior,
                    'actual': cantidad_actual,
                    'diferencia': cantidad_actual - cantidad_anterior
                })
        
        # Tipos que aparecieron por primera vez
        for tipo, cantidad_actual in tipos_actuales.items():
            if tipo not in tipos_anteriores:
                cambios['nuevas'].append({
                    'tipo': tipo,
                    'cantidad': cantidad_actual
                })
        
        # Tipos que desaparecieron completamente
        for tipo, cantidad_anterior in tipos_anteriores.items():
            if tipo not in tipos_actuales:
                cambios['resueltas'].append({
                    'tipo': tipo,
                    'cantidad_resuelta': cantidad_anterior
                })
        
        return cambios
        
    except Exception as e:
        logger.error(f"Error comparando con iteración anterior: {e}")
        return {'error_comparacion': str(e)}
