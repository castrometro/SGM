from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
import openpyxl
from django.http import HttpResponse
from django.core.files.storage import default_storage

from ..models import NombreIngles, CuentaContable, MovimientoContable
from ..serializers import NombreInglesSerializer
from ..utils.activity_logger import registrar_actividad_tarjeta
from ..utils.clientes import obtener_periodo_cierre_activo, get_client_ip
from ..tasks import procesar_nombres_ingles


class NombreInglesViewSet(viewsets.ModelViewSet):
    queryset = NombreIngles.objects.all()
    serializer_class = NombreInglesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        cliente = self.request.query_params.get("cliente")
        if cliente:
            qs = qs.filter(cliente_id=cliente)
        return qs


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_nombres_ingles(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")
    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo requeridos"}, status=400)
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=obtener_periodo_cierre_activo(request.user.cliente_set.first()),
        tarjeta="nombres_ingles",
        accion="upload_excel",
        descripcion=f"Subido archivo nombres inglés: {archivo.name}",
        usuario=request.user,
        detalles={},
        resultado="exito",
        ip_address=get_client_ip(request),
    )
    return Response({"ok": True})


class NombresEnInglesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def get(self, request):
        """
        ?estado=1 → estado (faltantes)
        ?list=1 → listado
        ?plantilla=1 → descarga Excel
        """
        cliente_id = request.query_params.get("cliente_id")
        cierre_id = request.query_params.get("cierre_id")
        if not cliente_id:
            return Response({"error": "cliente_id es requerido"}, status=400)

        if cierre_id:
            cuentas_ids = (
                MovimientoContable.objects.filter(cierre_id=cierre_id)
                .values_list("cuenta_id", flat=True)
                .distinct()
            )
            cuentas = CuentaContable.objects.filter(id__in=cuentas_ids)
        else:
            cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)

        if request.query_params.get("estado") == "1":
            faltantes = cuentas.filter(Q(nombre_en__isnull=True) | Q(nombre_en=""))
            data_faltantes = [
                {"codigo": c.codigo, "nombre": c.nombre} for c in faltantes
            ]

            total_cuentas = cuentas.count()

            # Lógica corregida: si no hay cuentas en absoluto, el estado es pendiente
            if total_cuentas == 0:
                estado = "pendiente"  # No hay cuentas = aún no hay nada que traducir
            else:
                estado = "subido" if not faltantes.exists() else "pendiente"

            return Response(
                {"estado": estado, "faltantes": data_faltantes, "total": total_cuentas}
            )

        if request.query_params.get("list") == "1":
            datos = [
                {"codigo": c.codigo, "nombre": c.nombre, "nombre_en": c.nombre_en or ""}
                for c in cuentas
            ]
            return Response({"nombres": datos})

        if request.query_params.get("plantilla") == "1":
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["codigo", "nombre", "nombre_en"])
            for c in cuentas:
                ws.append([c.codigo, c.nombre, c.nombre_en or ""])
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="plantilla_nombres_ingles.xlsx"'
            )
            wb.save(response)
            return response

        return Response({"error": "Parámetro de acción no especificado"}, status=400)

    def post(self, request):
        """
        Recibe Excel y dispara el procesamiento en Celery.
        """
        cliente_id = request.data.get("cliente_id")
        archivo = request.FILES.get("archivo")
        if not cliente_id or not archivo:
            return Response(
                {"error": "cliente_id y archivo son requeridos"}, status=400
            )

        # Guarda el archivo en media/temp/
        nombre_archivo = f"temp/nombres_ingles_cliente_{cliente_id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)

        # Dispara task Celery
        procesar_nombres_ingles.delay(cliente_id, ruta_guardada)

        return Response(
            {"mensaje": "Archivo recibido y tarea enviada a Celery", "ok": True}
        )

    def delete(self, request):
        """
        Elimina todas las traducciones para el cliente.
        """
        cliente_id = request.query_params.get("cliente_id")
        if not cliente_id:
            return Response({"error": "cliente_id es requerido"}, status=400)
        cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)
        cuentas.update(nombre_en=None)
        return Response({"ok": True, "msg": "Traducciones eliminadas"})
