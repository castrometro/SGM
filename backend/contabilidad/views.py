#backend/contabilidad/views.py
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, parser_classes, action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import HttpResponse
import openpyxl
from django.core.files.storage import default_storage
from datetime import date
import os
from django.db.models import Q
from contabilidad.permissions import PuedeCrearCierreContabilidad, SoloContabilidadAsignadoOGerente
import logging

logger = logging.getLogger(__name__)


from .models import (
    TipoDocumento,
    CuentaContable,
    CierreContabilidad,
    LibroMayorUpload,
    AperturaCuenta,
    MovimientoContable,
    ClasificacionSet,
    ClasificacionOption,
    AccountClassification,
    Incidencia,
    CentroCosto,
    Auxiliar,
    AnalisisCuentaCierre,
)
from .serializers import (
    TipoDocumentoSerializer,
    CuentaContableSerializer,
    CierreContabilidadSerializer,
    LibroMayorUploadSerializer,
    AperturaCuentaSerializer,
    MovimientoContableSerializer,
    ClasificacionSetSerializer,
    ClasificacionOptionSerializer,
    AccountClassificationSerializer,
    IncidenciaSerializer,
    CentroCostoSerializer,
    AuxiliarSerializer,
    ProgresoClasificacionSerializer,
    AnalisisCuentaCierreSerializer,


)

from api.models import (
    Cliente,
)

from contabilidad.tasks import (
    tarea_de_prueba,
    parsear_tipo_documento,
    procesar_libro_mayor,
    procesar_nombres_ingles,
    )


def verificar_y_marcar_completo(cuenta_id):
    try:
        cuenta = CuentaContable.objects.get(id=cuenta_id)
        cierre = CierreContabilidad.objects.filter(cliente=cuenta.cliente).order_by('-fecha_creacion').first()
        set_principal = ClasificacionSet.objects.filter(cliente=cuenta.cliente).first()
        if not (cierre and set_principal):
            return
        cuentas = CuentaContable.objects.filter(cliente=cuenta.cliente)
        clasificadas = AccountClassification.objects.filter(
            cuenta__in=cuentas,
            set_clas=set_principal
        ).values_list("cuenta_id", flat=True)
        if cuentas.exclude(id__in=clasificadas).count() == 0:
            cierre.estado = "completo"
            cierre.save(update_fields=["estado"])
    except Exception as e:
        logger.exception("Error al verificar cierre completo: %s", e)

class ClasificacionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


    @action(detail=True, methods=['get'], url_path='progreso_todos_los_sets')
    def progreso_todos_los_sets(self, request, pk=None):
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        sets = ClasificacionSet.objects.filter(cliente=cierre.cliente)
        cuentas = CuentaContable.objects.filter(cliente=cierre.cliente)
        progreso_por_set = []

        for set_obj in sets:
            clasificadas = AccountClassification.objects.filter(
                cuenta__in=cuentas,
                set_clas=set_obj
            ).values_list("cuenta_id", flat=True)
            cuentas_sin_clasif = cuentas.exclude(id__in=clasificadas)
            progreso_por_set.append({
                "set_id": set_obj.id,
                "set_nombre": set_obj.nombre,
                "cuentas_sin_clasificar": cuentas_sin_clasif.count(),
                "total_cuentas": cuentas.count(),
                "estado": "Completo" if cuentas_sin_clasif.count() == 0 else "Pendiente"
            })

        return Response({
            "sets_progreso": progreso_por_set,
            "total_sets": sets.count(),
        })

    @action(detail=True, methods=['get'], url_path='progreso')
    def progreso(self, request, pk=None):
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        set_qs = ClasificacionSet.objects.filter(cliente=cierre.cliente)
        existen_sets = set_qs.exists()
        resumen = cierre.resumen_parsing or {}
        total_cuentas = resumen.get("total_cuentas", 0)
        cuentas_nuevas = cierre.cuentas_nuevas  # fallback

        if existen_sets:
            set_principal = set_qs.first()
            cuentas = CuentaContable.objects.filter(cliente=cierre.cliente)
            clasificadas = AccountClassification.objects.filter(
                cuenta__in=cuentas,
                set_clas=set_principal
            ).values_list("cuenta_id", flat=True)
            cuentas_nuevas = cuentas.exclude(id__in=clasificadas).count()
            total_cuentas = cuentas.count()

        data = {
            "existen_sets": existen_sets,
            "cuentas_nuevas": cuentas_nuevas,
            "total_cuentas": total_cuentas,
            "parsing_completado": cierre.parsing_completado
        }
        return Response(data)


    @action(detail=True, methods=['get'], url_path='cuentas_pendientes')
    def cuentas_pendientes(self, request, pk=None):
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        cuentas_ids = CuentaContable.objects.filter(
            cliente=cierre.cliente
        ).values_list('id', flat=True)

        # Trae las cuentas clasificadas SOLO SI hay sets
        sets = ClasificacionSet.objects.filter(cliente=cierre.cliente)
        cuentas_clasificadas_ids = []
        set_clas = sets.first() if sets.exists() else None

        if set_clas:
            cuentas_clasificadas_ids = AccountClassification.objects.filter(
                set_clas=set_clas,
                cuenta_id__in=cuentas_ids
            ).values_list('cuenta', flat=True)

        # Trae las cuentas faltantes (todas si no hay set, o las que no estén clasificadas si hay set)
        if set_clas:
            cuentas_faltantes = CuentaContable.objects.filter(
                id__in=cuentas_ids
            ).exclude(
                id__in=cuentas_clasificadas_ids
            )
        else:
            # No hay sets aún, todas son "pendientes"
            cuentas_faltantes = CuentaContable.objects.filter(id__in=cuentas_ids)

        data = [
            {
                "id": c.id,
                "codigo": c.codigo,
                "nombre": c.nombre,
            }
            for c in cuentas_faltantes
        ]
        return Response({
            "sin_set": not sets.exists(),
            "cuentas_faltantes": data
        })




    @action(detail=False, methods=['post'], url_path='clasificar')
    def clasificar(self, request):
        cuenta_id = request.data.get("cuenta_id")
        set_clas_id = request.data.get("set_clas_id")
        opcion_id = request.data.get("opcion_id")
        usuario = request.user
        if not (cuenta_id and set_clas_id and opcion_id):
            return Response({"error": "Datos incompletos"}, status=400)
        obj, creado = AccountClassification.objects.update_or_create(
            cuenta_id=cuenta_id,
            set_clas_id=set_clas_id,
            defaults={
                "opcion_id": opcion_id,
                "asignado_por": usuario,
            }
        )

        verificar_y_marcar_completo(cuenta_id)
        return Response({"ok": True, "id": obj.id, "creado": creado})


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
            cuentas_ids = MovimientoContable.objects.filter(
                cierre_id=cierre_id
            ).values_list("cuenta_id", flat=True).distinct()
            cuentas = CuentaContable.objects.filter(id__in=cuentas_ids)
        else:
            cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)
        
        if request.query_params.get("estado") == "1":
            faltantes = cuentas.filter(Q(nombre_en__isnull=True) | Q(nombre_en=""))
            data_faltantes = [
                {"codigo": c.codigo, "nombre": c.nombre}
                for c in faltantes
            ]
            estado = "subido" if not faltantes.exists() else "pendiente"
            # ---- Agrega esto ----
            total_cuentas = cuentas.count()
            return Response({
                "estado": estado,
                "faltantes": data_faltantes,
                "total": total_cuentas      # <--- NUEVO!
            })

        if request.query_params.get("list") == "1":
            datos = [
                {
                    "codigo": c.codigo,
                    "nombre": c.nombre,
                    "nombre_en": c.nombre_en or ""
                }
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
            response["Content-Disposition"] = f'attachment; filename="plantilla_nombres_ingles.xlsx"'
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
            return Response({"error": "cliente_id y archivo son requeridos"}, status=400)
        
        # Guarda el archivo en media/temp/
        nombre_archivo = f"temp/nombres_ingles_cliente_{cliente_id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)

        # Dispara task Celery
        procesar_nombres_ingles.delay(cliente_id, ruta_guardada)

        return Response({"mensaje": "Archivo recibido y tarea enviada a Celery", "ok": True})

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



class AnalisisCuentaCierreViewSet(viewsets.ModelViewSet):
    queryset = AnalisisCuentaCierre.objects.all()
    serializer_class = AnalisisCuentaCierreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            return self.queryset.filter(cierre_id=cierre_id)
        return self.queryset

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_tipo_documento(request, cliente_id):
    # Busca si ya existe un tipo de documento asociado al cliente
    existe = TipoDocumento.objects.filter(cliente_id=cliente_id).exists()
    return Response({"estado": "subido" if existe else "pendiente"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cuentas_pendientes_set(request, cliente_id, set_id):
    cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)
    clasificadas = AccountClassification.objects.filter(
        cuenta__in=cuentas, set_clas_id=set_id
    ).values_list("cuenta_id", flat=True)
    pendientes = cuentas.exclude(id__in=clasificadas)
    data = [
        {"id": c.id, "codigo": c.codigo, "nombre": c.nombre}
        for c in pendientes
    ]
    return Response({"cuentas_faltantes": data})


@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_tipo_documento(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")

    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Guardar archivo temporalmente (media/temp/)
    nombre_archivo = f"temp/tipo_doc_cliente_{cliente_id}.xlsx"
    ruta_guardada = default_storage.save(nombre_archivo, archivo)

    # Enviar tarea a Celery (con ruta relativa)
    parsear_tipo_documento.delay(cliente_id, ruta_guardada)

    return Response({"mensaje": "Archivo recibido y tarea enviada"})

@api_view(['GET'])
def test_celery(request):
    tarea_de_prueba.delay("Mundo")  # <- se ejecuta en segundo plano
    return Response({"mensaje": "Tarea enviada a Celery"})

@api_view(['GET'])
@permission_classes([IsAuthenticated, SoloContabilidadAsignadoOGerente])
def resumen_cliente(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    ultimo = (
        CierreContabilidad.objects
        .filter(cliente=cliente)
        .order_by("-periodo")
        .first()
    )

    return Response({
        "cliente_id": cliente.id,
        "cliente": cliente.nombre,
        "ultimo_cierre": ultimo.periodo if ultimo else None,
        "estado_ultimo_cierre": ultimo.estado if ultimo else None
    })



@api_view(['POST'])
def eliminar_tipos_documento(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    TipoDocumento.objects.filter(cliente=cliente).delete()
    return Response({"mensaje": "Tipos de documento eliminados"})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tipos_documento_cliente(request, cliente_id):
    tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)
    # O usa un serializer si tienes uno
    data = [
        {
            "id": tipo.id,
            "codigo": tipo.codigo,
            "descripcion": tipo.descripcion,
        }
        for tipo in tipos
    ]
    return Response(data)

# backend/contabilidad/views.py
class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset


class CuentaContableViewSet(viewsets.ModelViewSet):
    queryset = CuentaContable.objects.all()
    serializer_class = CuentaContableSerializer

class CierreContabilidadViewSet(viewsets.ModelViewSet):
    queryset = CierreContabilidad.objects.all()
    serializer_class = CierreContabilidadSerializer
    permission_classes = [IsAuthenticated, SoloContabilidadAsignadoOGerente]  # o la que prefieras

    def get_queryset(self):
        """
        Permite filtrar por cliente y periodo:
        /api/contabilidad/cierres/?cliente=1&periodo=2024-04
        """
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        periodo = self.request.query_params.get('periodo')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        return queryset

    def perform_create(self, serializer):
        """
        Asigna el usuario actual al crear el cierre.
        """
        serializer.save(usuario=self.request.user)



class LibroMayorUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroMayorUpload.objects.all()
    serializer_class = LibroMayorUploadSerializer
    permission_classes = [IsAuthenticated]  # o la que prefieras

    def get_queryset(self):
        """
        Permite filtrar por cierre (usado por el frontend)
        /api/contabilidad/libromayor/?cierre=ID
        """
        queryset = super().get_queryset()
        cierre_id = self.request.query_params.get('cierre')
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        return queryset

    def perform_create(self, serializer):
        """
        Guarda el LibroMayorUpload y puedes aquí disparar el proceso async (Celery) si quieres.
        """
        instance = serializer.save()
        # Aquí podrías llamar un task Celery para procesar el archivo:
        
        procesar_libro_mayor.delay(instance.id)
        return instance

class AperturaCuentaViewSet(viewsets.ModelViewSet):
    queryset = AperturaCuenta.objects.all()
    serializer_class = AperturaCuentaSerializer

class MovimientoContableViewSet(viewsets.ModelViewSet):
    queryset = MovimientoContable.objects.all()
    serializer_class = MovimientoContableSerializer

class ClasificacionSetViewSet(viewsets.ModelViewSet):
    queryset = ClasificacionSet.objects.all()
    serializer_class = ClasificacionSetSerializer

class ClasificacionOptionViewSet(viewsets.ModelViewSet):
    queryset = ClasificacionOption.objects.all()
    serializer_class = ClasificacionOptionSerializer
    filterset_fields = ['set_clas']  # asegúrate que esto está así

    def get_queryset(self):
        queryset = super().get_queryset()
        set_clas_id = self.request.query_params.get('set_clas')
        if set_clas_id:
            queryset = queryset.filter(set_clas_id=set_clas_id)
        return queryset

class AccountClassificationViewSet(viewsets.ModelViewSet):
    queryset = AccountClassification.objects.all()
    serializer_class = AccountClassificationSerializer

class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer

class CentroCostoViewSet(viewsets.ModelViewSet):
    queryset = CentroCosto.objects.all()
    serializer_class = CentroCostoSerializer

class AuxiliarViewSet(viewsets.ModelViewSet):
    queryset = Auxiliar.objects.all()
    serializer_class = AuxiliarSerializer
