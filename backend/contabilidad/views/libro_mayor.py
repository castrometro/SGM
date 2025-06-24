from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    LibroMayorUpload,
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
from ..serializers import LibroMayorUploadSerializer
from ..tasks import procesar_libro_mayor_con_upload_log
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
        if cliente:
            qs = qs.filter(cierre__cliente_id=cliente)
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cargar_libro_mayor(request):
    cierre_id = request.data.get("cierre_id")
    archivo = request.FILES.get("archivo")
    if not cierre_id or not archivo:
        return Response({"error": "cierre_id y archivo son requeridos"}, status=400)
    cierre = CierreContabilidad.objects.get(id=cierre_id)
    upload_log = UploadLogMixin().crear_upload_log(cierre.cliente, archivo)
    ruta = guardar_temporal(f"libro_mayor_{upload_log.id}.xlsx", archivo)
    upload_log.ruta_archivo = ruta
    upload_log.save()
    procesar_libro_mayor_con_upload_log.delay(upload_log.id)
    return Response({"upload_log_id": upload_log.id})


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
