#backend/contabilidad/tasks.py
from celery import shared_task
from contabilidad.utils.parser_tipo_documento import parsear_tipo_documento_excel
from contabilidad.utils.parser_libro_mayor import parsear_libro_mayor
from contabilidad.utils.parser_nombre_ingles import procesar_archivo_nombres_ingles
from contabilidad.models import LibroMayorUpload, BulkClasificacionUpload, CuentaContable, AccountClassification, ClasificacionSet, ClasificacionOption, TipoDocumento, MovimientoContable, NombresEnInglesUpload, ClasificacionCuentaArchivo, NombreIngles, NombreInglesArchivo
from django.utils import timezone
from django.core.files.storage import default_storage
import time
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)


@shared_task
def tarea_de_prueba(nombre):
    logger.info("👋 ¡Hola %s desde Celery!", nombre)
    time.sleep(999)
    logger.info("✅ Tarea completada.")
    return f"Completado por {nombre}" #esto sale en succeeded


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
    logger.info(f"Iniciando procesamiento de libro mayor para upload_id: {libro_mayor_id}")
    
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
        clasificaciones_bulk = BulkClasificacionUpload.objects.filter(
            cliente=cliente, 
            estado='completado'
        ).first()
        
        logger.info(f"Prerequisitos - Tipos de documento: {tipos_documento.count()}, "
                   f"Clasificaciones bulk: {'Sí' if clasificaciones_bulk else 'No'}")

        # Procesar archivo con toda la información disponible
        errores, fecha_inicio, fecha_fin, resumen = parsear_libro_mayor_completo(
            ruta, libro, tipos_documento, clasificaciones_bulk
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
            logger.info(f"Procesamiento completado exitosamente. "
                       f"Movimientos procesados: {resumen.get('movimientos_procesados', 0)}")
        
        cierre.save(update_fields=[
            'fecha_inicio_libro', 
            'fecha_fin_libro',
            'cuentas_nuevas', 
            'resumen_parsing',
            'parsing_completado',
            'estado'
        ])
        
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
def procesar_bulk_clasificacion(upload_id):
    """
    Procesa archivo Excel de clasificación bulk y guarda los datos RAW en ClasificacionCuentaArchivo
    (similar al flujo de tipo_documento)
    """
    logger.info(f"Iniciando procesamiento de clasificación bulk para upload_id: {upload_id}")
    
    try:
        upload = BulkClasificacionUpload.objects.get(id=upload_id)
    except BulkClasificacionUpload.DoesNotExist:
        logger.error(f"Upload con id {upload_id} no encontrado")
        return
    
    upload.estado = 'procesando'
    upload.save(update_fields=['estado'])
    
    try:
        # Obtener archivo local
        local_path = default_storage.path(upload.archivo.name)
        logger.info(f"Procesando archivo: {local_path}")
        
        df = pd.read_excel(local_path)
        logger.info(f"Archivo Excel leído con {len(df)} filas y {len(df.columns)} columnas")
        logger.info(f"Columnas encontradas: {list(df.columns)}")
        
        # Validar que tenga al menos 2 columnas (una para cuentas, una para sets)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas: una para números de cuenta y al menos una para clasificación")
        
        # La primera columna siempre son números de cuenta, el resto son sets
        columna_cuentas = df.columns[0]
        sets = list(df.columns[1:])  # Todas las columnas excepto la primera
        
        logger.info(f"Columna de cuentas: '{columna_cuentas}'")
        logger.info(f"Sets de clasificación encontrados: {sets}")
        
        errores = []
        registros_guardados = 0
        
        # Limpiar registros previos de este upload
        ClasificacionCuentaArchivo.objects.filter(upload=upload).delete()
        
        # Mostrar una muestra de los datos para debug
        logger.info(f"Muestra de datos (primeras 3 filas):")
        for i in range(min(3, len(df))):
            logger.info(f"  Fila {i+2}: {dict(df.iloc[i])}")
        
        filas_procesadas = 0
        filas_vacias = 0
        
        for index, row in df.iterrows():
            filas_procesadas += 1
            numero_cuenta = str(row[columna_cuentas]).strip() if not pd.isna(row[columna_cuentas]) else ""
            
            if not numero_cuenta:
                filas_vacias += 1
                logger.debug(f"Fila {index + 2}: Número de cuenta vacío")
                continue
                
            # Construir el diccionario de clasificaciones para esta cuenta
            clasificaciones_dict = {}
            for set_name in sets:
                valor = row[set_name]
                if not pd.isna(valor) and str(valor).strip() != '':
                    clasificaciones_dict[set_name] = str(valor).strip()
            
            # Guardar SIEMPRE el registro, incluso sin clasificaciones (como tipo documento)
            try:
                ClasificacionCuentaArchivo.objects.create(
                    cliente=upload.cliente,
                    upload=upload,
                    numero_cuenta=numero_cuenta,
                    clasificaciones=clasificaciones_dict,
                    fila_excel=index + 2  # +2 porque Excel empieza en 1 y además header
                )
                registros_guardados += 1
                logger.debug(f"Guardado registro: {numero_cuenta} con {len(clasificaciones_dict)} clasificaciones")
            except Exception as e:
                error_msg = f"Fila {index + 2}: Error al guardar {numero_cuenta} - {str(e)}"
                errores.append(error_msg)
                logger.error(error_msg)

        resumen = {
            'total_filas': len(df),
            'filas_procesadas': filas_procesadas,
            'filas_vacias': filas_vacias,
            'sets_encontrados': sets,
            'registros_guardados': registros_guardados,
            'errores_count': len(errores),
            'errores': errores[:10]  # Solo primeros 10 errores para no sobrecargar
        }
        
        upload.estado = 'completado'
        upload.resumen = resumen
        upload.errores = ''  # Limpiar errores previos
        upload.save(update_fields=['estado', 'resumen', 'errores'])
        
        logger.info(f"Procesamiento completado: {registros_guardados} registros guardados en archivo")
        
    except Exception as e:
        logger.exception("Error en bulk clasificacion")
        upload.estado = 'error'
        upload.errores = str(e)
        upload.resumen = {'error': str(e)}
        upload.save(update_fields=['estado', 'errores', 'resumen'])

@shared_task
def procesar_mapeo_clasificaciones(upload_id):
    """
    Procesa el mapeo de los registros raw en ClasificacionCuentaArchivo a las cuentas reales
    """
    logger.info(f"Iniciando mapeo de clasificaciones para upload_id: {upload_id}")
    
    try:
        upload = BulkClasificacionUpload.objects.get(id=upload_id)
    except BulkClasificacionUpload.DoesNotExist:
        logger.error(f"Upload con id {upload_id} no encontrado")
        return
    
    # Obtener todos los registros raw no procesados de este upload
    registros_raw = ClasificacionCuentaArchivo.objects.filter(
        upload=upload, 
        procesado=False
    )
    
    errores = []
    clasificaciones_aplicadas = 0
    cuentas_no_encontradas = 0
    
    for registro in registros_raw:
        try:
            # Buscar la cuenta real
            cuenta = CuentaContable.objects.get(
                codigo=registro.numero_cuenta,
                cliente=upload.cliente
            )
            
            # Aplicar cada clasificación del registro
            for set_name, valor in registro.clasificaciones.items():
                if not valor or str(valor).strip() == '':
                    continue
                    
                # Obtener o crear set y opción
                set_obj, created_set = ClasificacionSet.objects.get_or_create(
                    cliente=upload.cliente,
                    nombre=set_name
                )
                if created_set:
                    logger.info(f"Creado nuevo set: {set_name}")
                
                opcion_obj, created_opcion = ClasificacionOption.objects.get_or_create(
                    set_clas=set_obj,
                    valor=str(valor).strip()
                )
                if created_opcion:
                    logger.info(f"Creada nueva opción: {valor} para set {set_name}")
                
                # Aplicar clasificación
                clasificacion, created = AccountClassification.objects.update_or_create(
                    cuenta=cuenta,
                    set_clas=set_obj,
                    defaults={'opcion': opcion_obj}
                )
                if created:
                    clasificaciones_aplicadas += 1
            
            # Marcar como procesado y guardar referencia a la cuenta
            registro.procesado = True
            registro.cuenta_mapeada = cuenta
            registro.fecha_procesado = timezone.now()
            registro.errores_mapeo = ''
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
    resumen_actual = upload.resumen or {}
    resumen_actual.update({
        'mapeo_procesado': True,
        'clasificaciones_aplicadas': clasificaciones_aplicadas,
        'cuentas_no_encontradas': cuentas_no_encontradas,
        'errores_mapeo_count': len(errores),
        'errores_mapeo': errores[:10]
    })
    
    upload.resumen = resumen_actual
    upload.save(update_fields=['resumen'])
    
    logger.info(f"Mapeo completado: {clasificaciones_aplicadas} clasificaciones aplicadas, {cuentas_no_encontradas} cuentas no encontradas")


@shared_task
def procesar_nombres_ingles_upload(upload_id):
    """
    Procesa archivo Excel de nombres en inglés usando el nuevo modelo de upload
    """
    logger.info(f"Iniciando procesamiento de nombres en inglés para upload_id: {upload_id}")
    
    try:
        upload = NombresEnInglesUpload.objects.get(id=upload_id)
    except NombresEnInglesUpload.DoesNotExist:
        logger.error(f"Upload de nombres en inglés con id {upload_id} no encontrado")
        return
    
    upload.estado = 'procesando'
    upload.save(update_fields=['estado'])
    
    try:
        archivo_path = upload.archivo.path
        logger.info(f"Procesando archivo: {archivo_path}")
        
        df = pd.read_excel(archivo_path)
        logger.info(f"Archivo Excel leído con {len(df)} filas")
        
        # Validar columnas (debe tener al menos código y nombre en inglés)
        if len(df.columns) < 2:
            raise ValueError("El archivo debe tener al menos 2 columnas: código de cuenta y nombre en inglés")
        
        # Tomar las primeras dos columnas: código y nombre en inglés
        columna_codigo = df.columns[0]
        columna_nombre_en = df.columns[1]
        
        logger.info(f"Columnas detectadas - Código: '{columna_codigo}', Nombre en inglés: '{columna_nombre_en}'")
        
        errores = []
        cuentas_actualizadas = 0
        cuentas_no_encontradas = 0
        
        for index, row in df.iterrows():
            codigo = str(row[columna_codigo]).strip()
            nombre_en = str(row[columna_nombre_en]).strip()
            
            if not codigo or pd.isna(row[columna_codigo]):
                continue
                
            if not nombre_en or pd.isna(row[columna_nombre_en]) or nombre_en.lower() == 'nan':
                continue
                
            try:
                cuenta = CuentaContable.objects.get(codigo=codigo, cliente=upload.cliente)
                cuenta.nombre_en = nombre_en
                cuenta.save(update_fields=['nombre_en'])
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
            'total_filas': len(df),
            'cuentas_actualizadas': cuentas_actualizadas,
            'cuentas_no_encontradas': cuentas_no_encontradas,
            'errores_count': len(errores),
            'errores': errores[:10]  # Solo primeros 10 errores
        }
        
        upload.estado = 'completado'
        upload.resumen = resumen
        upload.errores = ''  # Limpiar errores previos
        upload.save(update_fields=['estado', 'resumen', 'errores'])
        
        logger.info(f"Procesamiento completado: {cuentas_actualizadas} cuentas actualizadas, {len(errores)} errores")
        
    except Exception as e:
        logger.exception("Error en procesamiento de nombres en inglés")
        upload.estado = 'error'
        upload.errores = str(e)
        upload.resumen = {'error': str(e)}
        upload.save(update_fields=['estado', 'errores', 'resumen'])


def parsear_libro_mayor_completo(ruta_archivo, libro_upload, tipos_documento, clasificaciones_bulk):
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
        if clasificaciones_bulk:
            clasificaciones = AccountClassification.objects.filter(
                cuenta__cliente=cliente
            ).select_related('cuenta', 'set_clas', 'opcion')
            for clasificacion in clasificaciones:
                codigo_cuenta = clasificacion.cuenta.codigo
                if codigo_cuenta not in clasificaciones_map:
                    clasificaciones_map[codigo_cuenta] = {}
                clasificaciones_map[codigo_cuenta][clasificacion.set_clas.nombre] = clasificacion.opcion.valor
            logger.info(f"Clasificaciones disponibles para {len(clasificaciones_map)} cuentas")
        
        # Procesar movimientos
        movimientos_procesados = 0
        cuentas_nuevas = 0
        incidencias_generadas = 0
        fecha_inicio = None
        fecha_fin = None
        
        for index, row in df.iterrows():
            try:
                # Extraer datos básicos del movimiento
                codigo_cuenta = str(row.get('Codigo_Cuenta', '')).strip()
                fecha_mov = pd.to_datetime(row.get('Fecha', ''), errors='coerce')
                monto = pd.to_numeric(row.get('Monto', 0), errors='coerce')
                tipo_documento_codigo = str(row.get('Tipo_Documento', '')).strip()
                
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
                    defaults={'nombre': f'Cuenta {codigo_cuenta}'}
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
                    descripcion=str(row.get('Descripcion', '')),
                    referencia=str(row.get('Referencia', ''))
                )
                
                # Aplicar tipo de documento si existe
                if tipo_documento_codigo and tipo_documento_codigo in tipos_doc_map:
                    tipo_doc = tipos_doc_map[tipo_documento_codigo]
                    # Aquí puedes agregar lógica específica según el tipo de documento
                    logger.debug(f"Tipo de documento aplicado: {tipo_doc.nombre}")
                
                # Aplicar clasificaciones si existen
                if codigo_cuenta in clasificaciones_map:
                    clasificaciones_cuenta = clasificaciones_map[codigo_cuenta]
                    logger.debug(f"Clasificaciones aplicadas para {codigo_cuenta}: {clasificaciones_cuenta}")
                
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
                tipo='error_procesamiento',
                descripcion=f"Errores en procesamiento del libro mayor: {len(errores)} errores encontrados",
                detalle={'errores': errores[:10]}  # Solo primeros 10
            )
            incidencias_generadas += 1
        
        resumen = {
            'movimientos_procesados': movimientos_procesados,
            'cuentas_nuevas': cuentas_nuevas,
            'incidencias_generadas': incidencias_generadas,
            'tipos_documento_aplicados': len(tipos_doc_map),
            'cuentas_con_clasificacion': len(clasificaciones_map),
            'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
            'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
            'total_filas_procesadas': len(df)
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
    logger.info(f"🧹 Limpieza automática: {archivos_eliminados} archivos temporales eliminados")
    return f"Eliminados {archivos_eliminados} archivos temporales"


@shared_task
def parsear_nombres_ingles(cliente_id, ruta_relativa):
    """
    Parsea archivo Excel de nombres en inglés y los guarda en la base de datos
    """
    from django.core.files.storage import default_storage
    from api.models import Cliente
    import pandas as pd
    import os
    
    logger.info(f"Iniciando procesamiento de nombres en inglés para cliente {cliente_id}")
    
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
        logger.info(f"Archivo Excel leído con {len(df)} filas de datos y {len(df.columns)} columnas")
        
        # Validar que tenga al menos 2 columnas
        if len(df.columns) < 2:
            logger.error("El archivo debe tener al menos 2 columnas: código de cuenta y nombre en inglés")
            return "Error: El archivo debe tener al menos 2 columnas"
        
        # Asignar nombres estándar a las columnas
        df.columns = ['cuenta_codigo', 'nombre_ingles'] + [f'col_{i}' for i in range(2, len(df.columns))]
        logger.info(f"Usando columna 0 como código de cuenta y columna 1 como nombre en inglés")
        
        # Filtrar filas válidas (sin NaN en campos requeridos)
        df_procesado = df.dropna(subset=['cuenta_codigo', 'nombre_ingles'])
        
        # Limpiar datos
        df_procesado['cuenta_codigo'] = df_procesado['cuenta_codigo'].astype(str).str.strip()
        df_procesado['nombre_ingles'] = df_procesado['nombre_ingles'].astype(str).str.strip()
        
        # Filtrar filas vacías después de limpiar
        df_procesado = df_procesado[
            (df_procesado['cuenta_codigo'] != '') & 
            (df_procesado['cuenta_codigo'] != 'nan') &
            (df_procesado['nombre_ingles'] != '') & 
            (df_procesado['nombre_ingles'] != 'nan')
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
                    cuenta_codigo=row['cuenta_codigo'],
                    nombre_ingles=row['nombre_ingles']
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
            archivo_anterior = NombreInglesArchivo.objects.filter(cliente=cliente).first()
            if archivo_anterior:
                if archivo_anterior.archivo and os.path.exists(archivo_anterior.archivo.path):
                    os.remove(archivo_anterior.archivo.path)
                archivo_anterior.delete()
            
            # Crear nuevo registro de archivo
            with open(ruta_completa, 'rb') as f:
                from django.core.files.base import ContentFile
                contenido = f.read()
                archivo_final = ContentFile(contenido, name=f"nombres_ingles_{cliente.id}.xlsx")
                
                NombreInglesArchivo.objects.create(
                    cliente=cliente,
                    archivo=archivo_final
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
        from .utils.activity_logger import registrar_actividad_tarjeta
        from datetime import date
        
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='nombres_ingles',
            accion='process_excel',
            descripcion=f'Procesado archivo: {len(nombres_creados)} nombres en inglés creados',
            usuario=None,  # Tarea automática
            detalles={
                'total_creados': len(nombres_creados),
                'total_errores': len(errores),
                'nombres_eliminados_anteriores': nombres_eliminados,
                'errores': errores[:10] if errores else []  # Solo primeros 10 errores
            },
            resultado='exito',
            ip_address=None
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
        from .utils.activity_logger import registrar_actividad_tarjeta
        from datetime import date
        
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='nombres_ingles',
            accion='process_excel',
            descripcion=f'Error al procesar archivo de nombres en inglés: {str(e)}',
            usuario=None,  # Tarea automática
            detalles={
                'error': str(e),
                'archivo': ruta_relativa
            },
            resultado='error',
            ip_address=None
        )
        
        return error_msg