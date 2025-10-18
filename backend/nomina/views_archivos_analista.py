# backend/nomina/views_archivos_analista.py

import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import ArchivoAnalistaUpload, CierreNomina
from .serializers import ArchivoAnalistaUploadSerializer
# USANDO STUBS DE TRANSICIÓN - MIGRAR A ACTIVITY V2
from .utils.mixins_stub import UploadLogNominaMixin, ValidacionArchivoCRUDMixin
from .utils.clientes import get_client_ip
from .utils.uploads import guardar_temporal
from .models_logging import registrar_actividad_tarjeta_nomina  # ✅ Usando función real, no stub
# Importar tarea refactorizada desde tasks_refactored/
from .tasks_refactored.archivos_analista import procesar_archivo_analista_con_logging

logger = logging.getLogger(__name__)


class ArchivoAnalistaUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar archivos del analista (finiquitos, incidencias, ingresos)
    """
    queryset = ArchivoAnalistaUpload.objects.all()
    serializer_class = ArchivoAnalistaUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        tipo_archivo = self.request.query_params.get('tipo_archivo')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        if tipo_archivo:
            queryset = queryset.filter(tipo_archivo=tipo_archivo)
        return queryset
    
    @action(detail=False, methods=['post'], url_path='subir/(?P<cierre_id>[^/.]+)/(?P<tipo_archivo>[^/.]+)')
    def subir(self, request, cierre_id=None, tipo_archivo=None):
        """Sube un archivo del analista para un cierre específico"""
        try:
            cierre = CierreNomina.objects.get(id=cierre_id)
        except CierreNomina.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        # Validar tipo de archivo
        tipos_validos = ['finiquitos', 'incidencias', 'ingresos']
        if tipo_archivo not in tipos_validos:
            return Response({"error": f"Tipo de archivo inválido. Debe ser uno de: {', '.join(tipos_validos)}"}, status=400)
        
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"error": "No se proporcionó archivo"}, status=400)
        
        # Validar que sea un archivo Excel
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response({"error": "El archivo debe ser de tipo Excel (.xlsx o .xls)"}, status=400)

        # Validar nombre de archivo
        from .utils.validaciones import validar_nombre_archivo_analista
        try:
            resultado_validacion = validar_nombre_archivo_analista(
                archivo.name, 
                tipo_archivo=tipo_archivo,
                rut_cliente=cierre.cliente.rut,
                periodo_cierre=cierre.periodo
            )
            
            if not resultado_validacion['es_valido']:
                errores = resultado_validacion.get('errores', [])
                mensaje_error = '\n'.join(errores) if errores else "Nombre de archivo inválido"
                return Response(
                    {"error": mensaje_error}, 
                    status=400
                )
                
            # Log de advertencias si las hay
            advertencias = resultado_validacion.get('advertencias', [])
            if advertencias:
                logger.warning(f"Advertencias en validación de archivo {archivo.name}: {advertencias}")
                
        except Exception as e:
            logger.error(f"Error validando nombre de archivo {archivo.name}: {e}")
            return Response(
                {"error": "Error interno validando el nombre del archivo"}, 
                status=500
            )
        
        # Crear el registro del archivo
        archivo_analista = ArchivoAnalistaUpload.objects.create(
            cierre=cierre,
            tipo_archivo=tipo_archivo,
            archivo=archivo,
            analista=request.user,
            estado='pendiente'
        )
        
        # ✅ Disparar tarea refactorizada con usuario_id
        procesar_archivo_analista_con_logging.delay(archivo_analista.id, request.user.id)
        
        return Response({
            "id": archivo_analista.id,
            "tipo_archivo": archivo_analista.tipo_archivo,
            "estado": archivo_analista.estado,
            "archivo_nombre": archivo.name,
            "fecha_subida": archivo_analista.fecha_subida,
            "mensaje": "Archivo subido correctamente y enviado a procesamiento"
        }, status=201)
    
    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        """Reprocesa un archivo del analista"""
        archivo = self.get_object()
        
        # Reiniciar estado
        archivo.estado = 'pendiente'
        archivo.save()
        
        # ✅ Disparar tarea refactorizada con usuario_id
        procesar_archivo_analista_con_logging.delay(archivo.id, request.user.id)
        
        return Response({
            "mensaje": "Archivo enviado a reprocesamiento",
            "estado": archivo.estado
        })

    def perform_destroy(self, instance):
        """
        Eliminar archivo del analista y todos sus datos relacionados
        """
        logger = logging.getLogger(__name__)
        cierre = instance.cierre
        tipo = instance.tipo_archivo
        
        # ✅ Registrar actividad con tarjeta específica (abreviado para DB limit de 25 chars)
        tarjeta_especifica = f"analista_{tipo}" if tipo else "archivos_analista"
        
        # Registrar actividad antes de eliminar
        registrar_actividad_tarjeta_nomina(
            cierre_id=cierre.id,
            tarjeta=tarjeta_especifica,  # ✅ 'analista_finiquitos' / 'analista_incidencias' / 'analista_ingresos'
            accion="delete_archivo",
            descripcion=f"Archivo del analista ({tipo}) eliminado para resubida",
            usuario=self.request.user,
            detalles={
                "archivo_id": instance.id,
                "tipo_archivo": tipo,
                "archivo_nombre": instance.archivo.name if instance.archivo else "N/A",
                "estado_anterior": instance.estado
            },
            ip_address=get_client_ip(self.request)
        )
        
        with transaction.atomic():
            # Contar registros antes de eliminar para logging
            if tipo == 'finiquitos':
                count = instance.analistafiniquito_set.count()
                logger.info(f"Eliminando {count} registros de finiquitos")
            elif tipo == 'incidencias':
                count = instance.analistaincidencia_set.count()
                logger.info(f"Eliminando {count} registros de incidencias")
            elif tipo == 'ingresos':
                count = instance.analistaingreso_set.count()
                logger.info(f"Eliminando {count} registros de ingresos")
            
            # El CASCADE automáticamente eliminará los registros relacionados
            # pero lo hacemos explícito para claridad
            instance.delete()
            logger.info(f"Archivo del analista {instance.id} ({tipo}) eliminado completamente")


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
        # ✅ Usar tarea refactorizada (solo 2 parámetros, sin upload_log obsoleto)
        result = procesar_archivo_analista_con_logging.delay(archivo_id, request.user.id)
        
        logger.info(f"Procesamiento de archivo analista iniciado para cierre {cierre_id}, usuario {request.user.correo_bdo}")
        
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
