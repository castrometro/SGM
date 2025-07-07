# backend/nomina/views_upload_con_logging.py

from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from celery import chain

from api.models import Cliente
from .models import CierreNomina, LibroRemuneracionesUpload
from .utils.mixins import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
from .utils.clientes import get_client_ip
from .utils.uploads import guardar_temporal
from .tasks import (
    analizar_headers_libro_remuneraciones,
    analizar_headers_libro_remuneraciones_con_validacion,
    clasificar_headers_libro_remuneraciones_task,
    actualizar_empleados_desde_libro,
    guardar_registros_nomina,
    validar_nombre_archivo_libro_remuneraciones_task,
    verificar_archivo_libro_remuneraciones_task,
    validar_contenido_libro_remuneraciones_task,
)
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_libro_remuneraciones_con_logging(request):
    """
    Carga un libro de remuneraciones con logging integrado
    """
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    
    # 1. VALIDACIONES BÁSICAS SÍNCRONAS
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    
    # 2. VERIFICAR CIERRE EXISTE
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    
    # 3. VALIDAR ARCHIVO
    try:
        validador = ValidacionArchivoCRUDMixin()
        validador.validar_archivo(archivo)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    
    # 4. CREAR UPLOAD_LOG BÁSICO Y GUARDAR ARCHIVO
    mixin = UploadLogNominaMixin()
    mixin.tipo_upload = "libro_remuneraciones"
    mixin.usuario = request.user
    mixin.ip_usuario = get_client_ip(request)
    
    upload_log = mixin.crear_upload_log(cliente, archivo)
    logger.info(f"Upload log creado con ID: {upload_log.id}")
    
    # Guardar archivo temporal inmediatamente
    nombre_temporal = f"libro_remuneraciones_cierre_{cierre_id}_{upload_log.id}.xlsx"
    ruta = guardar_temporal(nombre_temporal, archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    logger.info(f"Upload log guardado con ruta: {ruta}")
    
    # 5. CREAR/ACTUALIZAR REGISTRO DE LIBRO REMUNERACIONES
    # Primero verificar si ya existe un libro para este cierre
    libro_existente = LibroRemuneracionesUpload.objects.filter(cierre=cierre).first()
    
    if libro_existente:
        # Actualizar existente
        libro_existente.archivo = archivo
        libro_existente.estado = "analizando_hdrs"
        libro_existente.upload_log = upload_log
        libro_existente.save()
        libro_id = libro_existente.id
    else:
        # Crear nuevo
        libro = LibroRemuneracionesUpload.objects.create(
            cierre=cierre,
            archivo=archivo,
            estado="analizando_hdrs",
            upload_log=upload_log
        )
        libro_id = libro.id
    
    # 6. REGISTRAR ACTIVIDAD Y GUARDAR LIBRO_ID EN RESUMEN
    mixin.registrar_actividad(
        tarjeta_tipo="libro_remuneraciones",
        tarjeta_id=libro_id,
        accion="archivo_subido",
        descripcion=f"Archivo {archivo.name} subido para procesamiento",
        datos_adicionales={
            "nombre_archivo": archivo.name,
            "tamaño_archivo": archivo.size,
            "upload_log_id": upload_log.id
        }
    )
    
    # Guardar libro_id en el resumen del upload_log para el chain
    if upload_log.resumen:
        upload_log.resumen['libro_id'] = libro_id
    else:
        upload_log.resumen = {'libro_id': libro_id}
    upload_log.save(update_fields=['resumen'])
    
    # Forzar commit de la transacción antes del chain
    from django.db import transaction
    transaction.commit()
    
    logger.info(f"Upload log {upload_log.id} completamente guardado, iniciando chain...")
    
    # 7. 🔗 INICIAR CELERY CHAIN CON VALIDACIONES
    try:
        logger.info(f"Iniciando chain de validación para upload_log_id: {upload_log.id}")
        result = chain(
            # Validaciones iniciales
            validar_nombre_archivo_libro_remuneraciones_task.s(upload_log.id),
            verificar_archivo_libro_remuneraciones_task.s(),
            validar_contenido_libro_remuneraciones_task.s(),
            # Procesamiento con validación integrada
            analizar_headers_libro_remuneraciones_con_validacion.s(),
            clasificar_headers_libro_remuneraciones_task.s(),
        )()
        
        logger.info(f"Procesamiento de libro iniciado para cierre {cierre_id}, upload_log {upload_log.id}")
        
    except Exception as e:
        logger.error(f"Error al iniciar chain de procesamiento: {str(e)}")
        # Marcar como error
        mixin.marcar_como_error(upload_log.id, f"Error al iniciar procesamiento: {str(e)}")
        
        return Response({
            "error": "Error al iniciar procesamiento",
            "detalle": str(e)
        }, status=500)
    
    return Response({
        "mensaje": "Archivo recibido y procesamiento iniciado",
        "upload_log_id": upload_log.id,
        "libro_id": libro_id,
        "estado": "procesando",
        "info": "El procesamiento se realizará de manera asíncrona"
    })


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_movimientos_mes_con_logging(request):
    """
    Carga movimientos del mes con logging integrado
    """
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    
    # 1. VALIDACIONES BÁSICAS SÍNCRONAS
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    
    # 2. VERIFICAR CIERRE EXISTE
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    
    # 3. VALIDAR ARCHIVO
    try:
        validador = ValidacionArchivoCRUDMixin()
        validador.validar_archivo(archivo)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    
    # 4. CREAR UPLOAD_LOG BÁSICO Y GUARDAR ARCHIVO
    mixin = UploadLogNominaMixin()
    mixin.tipo_upload = "movimientos_mes"
    mixin.usuario = request.user
    mixin.ip_usuario = get_client_ip(request)
    
    upload_log = mixin.crear_upload_log(cliente, archivo)
    
    # Guardar archivo temporal inmediatamente
    nombre_temporal = f"movimientos_mes_cierre_{cierre_id}_{upload_log.id}.xlsx"
    ruta = guardar_temporal(nombre_temporal, archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    
    # 5. CREAR/ACTUALIZAR REGISTRO DE MOVIMIENTOS
    from .models import MovimientosMesUpload
    
    movimiento_existente = MovimientosMesUpload.objects.filter(cierre=cierre).first()
    
    if movimiento_existente:
        # Actualizar existente
        movimiento_existente.archivo = archivo
        movimiento_existente.estado = "procesando"
        movimiento_existente.upload_log = upload_log
        movimiento_existente.save()
        movimiento_id = movimiento_existente.id
    else:
        # Crear nuevo
        movimiento = MovimientosMesUpload.objects.create(
            cierre=cierre,
            archivo=archivo,
            estado="procesando",
            upload_log=upload_log
        )
        movimiento_id = movimiento.id
    
    # 6. REGISTRAR ACTIVIDAD
    mixin.registrar_actividad(
        tarjeta_tipo="movimientos_mes",
        tarjeta_id=movimiento_id,
        accion="archivo_subido",
        descripcion=f"Archivo {archivo.name} subido para procesamiento",
        datos_adicionales={
            "nombre_archivo": archivo.name,
            "tamaño_archivo": archivo.size,
            "upload_log_id": upload_log.id
        }
    )
    
    # 7. 🔗 INICIAR PROCESAMIENTO
    try:
        from .tasks import procesar_movimientos_mes
        
        result = procesar_movimientos_mes.delay(movimiento_id, upload_log.id)
        
        logger.info(f"Procesamiento de movimientos iniciado para cierre {cierre_id}, upload_log {upload_log.id}")
        
    except Exception as e:
        logger.error(f"Error al iniciar procesamiento de movimientos: {str(e)}")
        # Marcar como error
        mixin.marcar_como_error(upload_log.id, f"Error al iniciar procesamiento: {str(e)}")
        
        return Response({
            "error": "Error al iniciar procesamiento",
            "detalle": str(e)
        }, status=500)
    
    return Response({
        "mensaje": "Archivo recibido y procesamiento iniciado",
        "upload_log_id": upload_log.id,
        "movimiento_id": movimiento_id,
        "estado": "procesando",
        "info": "El procesamiento se realizará de manera asíncrona"
    })


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_archivo_analista_con_logging(request):
    """
    Carga un archivo del analista con logging integrado
    """
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    tipo_archivo = request.data.get("tipo_archivo")  # 'finiquitos', 'incidencias', 'ingresos'
    
    # 1. VALIDACIONES BÁSICAS SÍNCRONAS
    if not cierre_id or not archivo or not tipo_archivo:
        return Response({"error": "cierre_id, archivo y tipo_archivo son requeridos"}, status=400)
    
    # 2. VERIFICAR CIERRE EXISTE
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    
    # 3. VALIDAR ARCHIVO
    try:
        validador = ValidacionArchivoCRUDMixin()
        validador.validar_archivo(archivo)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    
    # 4. CREAR UPLOAD_LOG BÁSICO Y GUARDAR ARCHIVO
    mixin = UploadLogNominaMixin()
    mixin.tipo_upload = f"archivo_analista_{tipo_archivo}"
    mixin.usuario = request.user
    mixin.ip_usuario = get_client_ip(request)
    
    upload_log = mixin.crear_upload_log(cliente, archivo)
    
    # Guardar archivo temporal inmediatamente
    nombre_temporal = f"archivo_analista_{tipo_archivo}_cierre_{cierre_id}_{upload_log.id}.xlsx"
    ruta = guardar_temporal(nombre_temporal, archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    
    # 5. CREAR/ACTUALIZAR REGISTRO DE ARCHIVO ANALISTA
    from .models import ArchivoAnalistaUpload
    
    archivo_existente = ArchivoAnalistaUpload.objects.filter(
        cierre=cierre, 
        tipo_archivo=tipo_archivo
    ).first()
    
    if archivo_existente:
        # Actualizar existente
        archivo_existente.archivo = archivo
        archivo_existente.estado = "procesando"
        archivo_existente.upload_log = upload_log
        archivo_existente.save()
        archivo_id = archivo_existente.id
    else:
        # Crear nuevo
        archivo_obj = ArchivoAnalistaUpload.objects.create(
            cierre=cierre,
            tipo_archivo=tipo_archivo,
            archivo=archivo,
            estado="procesando",
            upload_log=upload_log
        )
        archivo_id = archivo_obj.id
    
    # 6. REGISTRAR ACTIVIDAD
    mixin.registrar_actividad(
        tarjeta_tipo="archivo_analista",
        tarjeta_id=archivo_id,
        accion="archivo_subido",
        descripcion=f"Archivo {tipo_archivo} {archivo.name} subido para procesamiento",
        datos_adicionales={
            "nombre_archivo": archivo.name,
            "tamaño_archivo": archivo.size,
            "tipo_archivo": tipo_archivo,
            "upload_log_id": upload_log.id
        }
    )
    
    # 7. 🔗 INICIAR PROCESAMIENTO
    try:
        from .tasks import procesar_archivo_analista
        
        result = procesar_archivo_analista.delay(archivo_id, upload_log.id)
        
        logger.info(f"Procesamiento de archivo analista iniciado para cierre {cierre_id}, upload_log {upload_log.id}")
        
    except Exception as e:
        logger.error(f"Error al iniciar procesamiento de archivo analista: {str(e)}")
        # Marcar como error
        mixin.marcar_como_error(upload_log.id, f"Error al iniciar procesamiento: {str(e)}")
        
        return Response({
            "error": "Error al iniciar procesamiento",
            "detalle": str(e)
        }, status=500)
    
    return Response({
        "mensaje": "Archivo recibido y procesamiento iniciado",
        "upload_log_id": upload_log.id,
        "archivo_id": archivo_id,
        "tipo_archivo": tipo_archivo,
        "estado": "procesando",
        "info": "El procesamiento se realizará de manera asíncrona"
    })


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_archivo_novedades_con_logging(request):
    """
    Carga un archivo de novedades con logging integrado
    """
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    
    # 1. VALIDACIONES BÁSICAS SÍNCRONAS
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    
    # 2. VERIFICAR CIERRE EXISTE
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
        cliente = cierre.cliente
    except CierreNomina.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    
    # 3. VALIDAR ARCHIVO
    try:
        validador = ValidacionArchivoCRUDMixin()
        validador.validar_archivo(archivo)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    
    # 4. CREAR UPLOAD_LOG BÁSICO Y GUARDAR ARCHIVO
    mixin = UploadLogNominaMixin()
    mixin.tipo_upload = "archivo_novedades"
    mixin.usuario = request.user
    mixin.ip_usuario = get_client_ip(request)
    
    upload_log = mixin.crear_upload_log(cliente, archivo)
    
    # Guardar archivo temporal inmediatamente
    nombre_temporal = f"archivo_novedades_cierre_{cierre_id}_{upload_log.id}.xlsx"
    ruta = guardar_temporal(nombre_temporal, archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    
    # 5. CREAR/ACTUALIZAR REGISTRO DE ARCHIVO NOVEDADES
    from .models import ArchivoNovedadesUpload
    
    archivo_existente = ArchivoNovedadesUpload.objects.filter(cierre=cierre).first()
    
    if archivo_existente:
        # Actualizar existente
        archivo_existente.archivo = archivo
        archivo_existente.estado = "procesando"
        archivo_existente.upload_log = upload_log
        archivo_existente.save()
        archivo_id = archivo_existente.id
    else:
        # Crear nuevo
        archivo_obj = ArchivoNovedadesUpload.objects.create(
            cierre=cierre,
            archivo=archivo,
            estado="procesando",
            upload_log=upload_log
        )
        archivo_id = archivo_obj.id
    
    # 6. REGISTRAR ACTIVIDAD
    mixin.registrar_actividad(
        tarjeta_tipo="archivo_novedades",
        tarjeta_id=archivo_id,
        accion="archivo_subido",
        descripcion=f"Archivo de novedades {archivo.name} subido para procesamiento",
        datos_adicionales={
            "nombre_archivo": archivo.name,
            "tamaño_archivo": archivo.size,
            "upload_log_id": upload_log.id
        }
    )
    
    # 7. 🔗 INICIAR PROCESAMIENTO
    try:
        from .tasks import procesar_archivo_novedades
        
        result = procesar_archivo_novedades.delay(archivo_id, upload_log.id)
        
        logger.info(f"Procesamiento de archivo novedades iniciado para cierre {cierre_id}, upload_log {upload_log.id}")
        
    except Exception as e:
        logger.error(f"Error al iniciar procesamiento de archivo novedades: {str(e)}")
        # Marcar como error
        mixin.marcar_como_error(upload_log.id, f"Error al iniciar procesamiento: {str(e)}")
        
        return Response({
            "error": "Error al iniciar procesamiento",
            "detalle": str(e)
        }, status=500)
    
    return Response({
        "mensaje": "Archivo recibido y procesamiento iniciado",
        "upload_log_id": upload_log.id,
        "archivo_id": archivo_id,
        "estado": "procesando",
        "info": "El procesamiento se realizará de manera asíncrona"
    })
