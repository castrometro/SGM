from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    LibroMayorUpload,
    LibroMayorArchivo,  # ✅ Nuevo modelo
    MovimientoContable,
    TipoDocumento,
    NombreIngles,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
    ClasificacionCuentaArchivo,
    Incidencia,
    CierreContabilidad,
)
from ..serializers import LibroMayorUploadSerializer, LibroMayorArchivoSerializer
from ..tasks import procesar_libro_mayor
from ..utils.clientes import obtener_periodo_cierre_activo, get_client_ip
from ..utils.mixins import UploadLogMixin, ActivityLoggerMixin
from ..utils.uploads import guardar_temporal


class LibroMayorUploadViewSet(UploadLogMixin, ActivityLoggerMixin, viewsets.ModelViewSet):
    queryset = LibroMayorUpload.objects.all()
    serializer_class = LibroMayorUploadSerializer
    permission_classes = [IsAuthenticated]
    tipo_upload = "libro_mayor"

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        cierre = self.request.query_params.get("cierre")
        
        if cliente:
            qs = qs.filter(cierre__cliente_id=cliente)
        elif cierre:
            qs = qs.filter(cierre_id=cierre)
            
        return qs

    @action(detail=True, methods=["post"])
    def reprocesar(self, request, pk=None):
        upload = self.get_object()
        # Aquí solo registramos la actividad; la lógica real quedó en el archivo original
        self.log_activity(
            cliente_id=upload.cierre.cliente.id,
            periodo=upload.cierre.periodo,
            tarjeta="libro_mayor",
            accion="process_start",
            descripcion=f"Reprocesamiento iniciado para archivo: {upload.archivo.name}",
            usuario=request.user,
            detalles={"upload_id": upload.id},
            resultado="exito",
            ip_address=get_client_ip(request),
        )
        return Response({"mensaje": "Reprocesamiento iniciado"})


class LibroMayorArchivoViewSet(UploadLogMixin, ActivityLoggerMixin, viewsets.ModelViewSet):
    """ViewSet para LibroMayorArchivo - persiste entre cierres"""
    
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
        elif cierre:
            # Filtrar por cierre a través del upload_log
            qs = qs.filter(upload_log__cierre_id=cierre)
            
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
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    
    cierre = CierreContabilidad.objects.get(id=cierre_id)
    
    # ✅ NUEVO: Validar nombre de archivo y extraer período
    from ..models import UploadLog
    import re
    
    es_valido, msg_valid = UploadLog.validar_archivo_cliente_estatico(
        archivo.name, "libro_mayor", cierre.cliente
    )
    
    if not es_valido:
        return Response({"error": msg_valid}, status=400)
    
    # Extraer período del nombre del archivo (ej: 12345678_LibroMayor_042025.xlsx -> "042025")
    rut_limpio = cierre.cliente.rut.replace(".", "").replace("-", "") if cierre.cliente.rut else str(cierre.cliente.id)
    nombre_sin_ext = re.sub(r"\.(xlsx|xls)$", "", archivo.name, flags=re.IGNORECASE)
    patron_periodo = rf"^{rut_limpio}_(LibroMayor|Mayor)_(\d{{6}})$"
    match = re.match(patron_periodo, nombre_sin_ext)
    
    if not match:
        return Response({
            "error": "No se pudo extraer el período del nombre del archivo",
            "formato_requerido": f"{rut_limpio}_LibroMayor_MMAAAA.xlsx"
        }, status=400)
    
    periodo = match.group(2)
    
    # ✅ NUEVO: Crear o actualizar LibroMayorArchivo (persiste entre cierres)
    try:
        libro_archivo, created = LibroMayorArchivo.objects.get_or_create(
            cliente=cierre.cliente,
            defaults={
                "archivo": archivo,
                "periodo": periodo,
                "estado": "subido",
                "procesado": False,
            }
        )
        
        # Si ya existía, actualizar con el nuevo archivo
        if not created:
            # Eliminar archivo anterior si existe
            if libro_archivo.archivo:
                try:
                    libro_archivo.archivo.delete()
                except Exception:
                    pass
            
            libro_archivo.archivo = archivo
            libro_archivo.periodo = periodo
            libro_archivo.estado = "subido"
            libro_archivo.procesado = False
            libro_archivo.errores = ""
            libro_archivo.save()
        
    except Exception as e:
        return Response({"error": f"Error al guardar archivo: {str(e)}"}, status=400)
    
    # ✅ Crear UploadLog para tracking (como antes)
    mixin = UploadLogMixin()
    mixin.tipo_upload = "libro_mayor"
    upload_log = mixin.crear_upload_log(cierre.cliente, archivo)
    
    # Asignar el cierre y usuario al upload log
    upload_log.cierre = cierre
    upload_log.usuario = request.user
    upload_log.save()
    
    # ✅ Vincular LibroMayorArchivo con UploadLog
    libro_archivo.upload_log = upload_log
    libro_archivo.save()
    
    # Guardar archivo temporal para procesamiento
    ruta = guardar_temporal(f"libro_mayor_cliente_{cierre.cliente.id}_{upload_log.id}.xlsx", archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    
    # Lanzar procesamiento
    procesar_libro_mayor.delay(upload_log.id)
    
    return Response({
        "upload_log_id": upload_log.id,
        "libro_archivo_id": libro_archivo.id,
        "periodo": periodo,
        "mensaje": "Archivo subido correctamente"
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reprocesar_movimientos_incompletos(request):
    cierre_id = request.data.get("cierre_id")
    if not cierre_id:
        return Response({"error": "cierre_id requerido"}, status=400)
    cierre = CierreContabilidad.objects.get(id=cierre_id)
    movimientos = MovimientoContable.objects.filter(cierre=cierre, flag_incompleto=True).select_related("cuenta")
    movimientos_corregidos = []
    for mov in movimientos:
        if mov.tipo_documento_id is None and mov.tipo_doc_codigo:
            td = TipoDocumento.objects.filter(cliente=cierre.cliente, codigo=mov.tipo_doc_codigo).first()
            if td:
                mov.tipo_documento = td
        if not mov.cuenta.nombre_en:
            nombre = NombreIngles.objects.filter(cliente=cierre.cliente, cuenta_codigo=mov.cuenta.codigo).first()
            if nombre:
                mov.cuenta.nombre_en = nombre.nombre_ingles
                mov.cuenta.save()
        clas_arch = (
            ClasificacionCuentaArchivo.objects.filter(cliente=cierre.cliente, numero_cuenta=mov.cuenta.codigo)
            .order_by("-id")
            .first()
        )
        if clas_arch:
            for set_nombre, opcion_valor in clas_arch.clasificaciones.items():
                set_obj = ClasificacionSet.objects.filter(cliente=cierre.cliente, nombre=set_nombre).first()
                if not set_obj:
                    continue
                opcion_obj = ClasificacionOption.objects.filter(set_clas=set_obj, valor=opcion_valor).first()
                if not opcion_obj:
                    continue
                AccountClassification.objects.update_or_create(
                    cuenta=mov.cuenta,
                    set_clas=set_obj,
                    defaults={"opcion": opcion_obj, "asignado_por": request.user},
                )
        mov.flag_incompleto = False
        mov.save(update_fields=["tipo_documento", "flag_incompleto"])
        Incidencia.objects.filter(
            cierre=cierre,
            descripcion__icontains=f"cuenta {mov.cuenta.codigo}"
        ).update(resuelta=True)
        movimientos_corregidos.append(mov.id)
    return Response({"reprocesados": len(movimientos_corregidos), "aun_incompletos": movimientos.count() - len(movimientos_corregidos), "total_movimientos": movimientos.count()})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movimientos_incompletos(request, cierre_id):
    cierre = CierreContabilidad.objects.get(id=cierre_id)
    movimientos = (
        MovimientoContable.objects.filter(cierre=cierre, flag_incompleto=True).select_related("cuenta")
    )
    data = []
    for mov in movimientos:
        incidencias = list(
            Incidencia.objects.filter(cierre=cierre, descripcion__icontains=f"cuenta {mov.cuenta.codigo}").values_list("descripcion", flat=True)
        )
        data.append({
            "id": mov.id,
            "cuenta_codigo": mov.cuenta.codigo,
            "cuenta_nombre": mov.cuenta.nombre,
            "descripcion": mov.descripcion,
            "incidencias": incidencias,
        })
    return Response(data)
