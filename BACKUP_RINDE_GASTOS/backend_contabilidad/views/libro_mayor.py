from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    LibroMayorArchivo,
    CierreContabilidad,
    UploadLog,
)
from ..serializers import LibroMayorArchivoSerializer
from ..utils.clientes import get_client_ip
from ..utils.mixins import UploadLogMixin, ActivityLoggerMixin
from ..utils.uploads import guardar_temporal



class LibroMayorArchivoViewSet(UploadLogMixin, ActivityLoggerMixin, viewsets.ModelViewSet):
    """ViewSet para LibroMayorArchivo - uno por cierre para mantener historicidad"""
    
    queryset = LibroMayorArchivo.objects.all()
    serializer_class = LibroMayorArchivoSerializer
    permission_classes = [IsAuthenticated]
    tipo_upload = "libro_mayor"

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        cierre = self.request.query_params.get("cierre")
        
        if cliente:
            qs = qs.filter(cliente_id=cliente)
        if cierre:
            qs = qs.filter(cierre_id=cierre)
            
        return qs

    @action(detail=True, methods=["get"])
    def estado(self, request, pk=None):
        """Obtiene el estado actual del archivo de libro mayor"""
        libro_archivo = self.get_object()
        
        return Response({
            "id": libro_archivo.id,
            "cliente_id": libro_archivo.cliente.id,
            "cliente_nombre": libro_archivo.cliente.nombre,
            "periodo": libro_archivo.periodo,
            "archivo_nombre": libro_archivo.archivo.name if libro_archivo.archivo else None,
            "fecha_subida": libro_archivo.fecha_subida,
            "estado": libro_archivo.estado,
            "procesado": libro_archivo.procesado,
            "errores": libro_archivo.errores,
            "upload_log_id": libro_archivo.upload_log.id if libro_archivo.upload_log else None,
        })

    @action(detail=True, methods=["post"])
    def reprocesar(self, request, pk=None):
        """Reprocesa el archivo de libro mayor"""
        libro_archivo = self.get_object()
        
        # Verificar que hay un archivo subido
        if not libro_archivo.archivo:
            return Response({"error": "No hay archivo para reprocesar"}, status=400)
        
        # Registrar actividad
        self.log_activity(
            cliente_id=libro_archivo.cliente.id,
            periodo=libro_archivo.periodo,
            tarjeta="libro_mayor",
            accion="process_start",
            descripcion=f"Reprocesamiento iniciado para archivo: {libro_archivo.archivo.name}",
            usuario=request.user,
            detalles={"libro_archivo_id": libro_archivo.id},
            resultado="exito",
            ip_address=get_client_ip(request),
        )
        
        # Aquí se podría implementar la lógica de reprocesamiento si fuera necesario
        # Por ahora solo actualizamos el estado
        libro_archivo.estado = "procesando"
        libro_archivo.save()
        
        return Response({"mensaje": "Reprocesamiento iniciado"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cargar_libro_mayor(request):
    """
    Vista refactorizada para cargar Libro Mayor usando Celery Chains.
    
    Flujo simplificado:
    1. Validar entrada básica
    2. Crear UploadLog
    3. Guardar archivo temporal
    4. Disparar chain de procesamiento
    5. Retornar respuesta inmediata
    """
    import logging
    from django.core.files.storage import default_storage
    from ..tasks_libro_mayor import crear_chain_libro_mayor
    from ..utils.activity_logger import registrar_actividad_tarjeta
    from datetime import date
    
    logger = logging.getLogger(__name__)
    
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    
    try:
        cierre = CierreContabilidad.objects.get(id=cierre_id)
    except CierreContabilidad.DoesNotExist:
        return Response({"error": "Cierre no encontrado"}, status=404)
    
    # Validar nombre de archivo básico (se validará más a fondo en el chain)
    if not archivo.name.lower().endswith(('.xlsx', '.xls')):
        return Response({"error": "Solo se aceptan archivos Excel (.xlsx, .xls)"}, status=400)
    
    # Crear UploadLog
    mixin = UploadLogMixin()
    mixin.tipo_upload = "libro_mayor"
    upload_log = mixin.crear_upload_log(cierre.cliente, archivo)
    
    # Asignar el cierre y usuario al upload log
    upload_log.cierre = cierre
    upload_log.usuario = request.user
    upload_log.save()
    
    # Guardar archivo temporal para procesamiento
    ruta = guardar_temporal(f"libro_mayor_cliente_{cierre.cliente.id}_{upload_log.id}.xlsx", archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save(update_fields=["ruta_archivo"])
    
    # Registrar actividad de upload exitoso
    registrar_actividad_tarjeta(
        cliente_id=cierre.cliente.id,
        periodo=cierre.periodo,
        tarjeta="libro_mayor",
        accion="upload_excel",
        descripcion=f"Subido archivo: {archivo.name} (UploadLog ID: {upload_log.id})",
        usuario=request.user,
        detalles={
            "nombre_archivo": archivo.name,
            "tamaño_bytes": archivo.size,
            "upload_log_id": upload_log.id,
            "cierre_id": cierre.id,
            "ruta_archivo": ruta,
            "procesamiento": "chain_celery"
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )
    
    # Disparar chain de procesamiento
    try:
        chain_libro_mayor = crear_chain_libro_mayor(upload_log.id, request.user.correo_bdo)
        chain_libro_mayor.apply_async()
        logger.info(f"Chain de Libro Mayor iniciado para upload_log_id: {upload_log.id}")
        
        return Response({
            "mensaje": "Archivo recibido y procesamiento iniciado",
            "upload_log_id": upload_log.id,
            "estado": upload_log.estado,
            "cierre_id": cierre.id,
            "tipo_procesamiento": "chain_celery"
        })
        
    except Exception as e:
        # Si falla el chain, marcar como error
        upload_log.estado = "error"
        upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
        upload_log.save()
        
        logger.error(f"Error iniciando chain de Libro Mayor: {str(e)}")
        return Response({
            "error": "Error iniciando procesamiento",
            "detalle": str(e),
            "upload_log_id": upload_log.id
        }, status=500)


















