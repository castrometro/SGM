# backend/contabilidad/views.py
import glob
import io
import logging
import os
from datetime import date

import openpyxl
import pandas as pd
from contabilidad.permissions import (
    PuedeCrearCierreContabilidad,
    SoloContabilidadAsignadoOGerente,
)
from django.core.files.storage import default_storage
from django.db.models import Q, Sum
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import (
    action,
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils.activity_logger import (
    registrar_actividad_tarjeta,
)  # Comentado temporalmente

logger = logging.getLogger(__name__)


def obtener_periodo_actividad_para_cliente(cliente):
    """
    Helper function para obtener el período correcto para registrar actividades de tarjeta.
    Busca el cierre activo del cliente, si no encuentra usa la fecha actual.
    """
    try:
        cierre_para_actividad = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
        
        if cierre_para_actividad:
            return cierre_para_actividad.periodo
        else:
            return date.today().strftime("%Y-%m")
    except Exception:
        return date.today().strftime("%Y-%m")


def get_client_ip(request):
    """
    Helper function para obtener la IP del cliente desde el request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


from api.models import Cliente
from contabilidad.tasks import (
    parsear_nombres_ingles,
    parsear_tipo_documento,
    procesar_clasificacion_con_upload_log,
    procesar_libro_mayor,
    procesar_nombres_ingles,
    procesar_nombres_ingles_upload,
    procesar_nombres_ingles_con_upload_log,
    procesar_tipo_documento_con_upload_log,
    tarea_de_prueba,
)

from .models import (
    AccountClassification,
    AnalisisCuentaCierre,
    AperturaCuenta,
    Auxiliar,
    CentroCosto,
    CierreContabilidad,
    ClasificacionCuentaArchivo,
    ClasificacionOption,
    ClasificacionSet,
    CuentaContable,
    Incidencia,
    LibroMayorUpload,
    MovimientoContable,
    NombreIngles,
    NombreInglesArchivo,
    NombresEnInglesUpload,
    TarjetaActivityLog,
    TipoDocumento,
    TipoDocumentoArchivo,
    UploadLog,
)
from .serializers import (
    AccountClassificationSerializer,
    AnalisisCuentaCierreSerializer,
    AperturaCuentaSerializer,
    AuxiliarSerializer,
    CentroCostoSerializer,
    CierreContabilidadSerializer,
    ClasificacionCuentaArchivoSerializer,
    ClasificacionOptionSerializer,
    ClasificacionSetSerializer,
    CuentaContableSerializer,
    IncidenciaSerializer,
    LibroMayorUploadSerializer,
    MovimientoContableSerializer,
    NombreInglesSerializer,
    NombresEnInglesUploadSerializer,
    ProgresoClasificacionSerializer,
    TarjetaActivityLogSerializer,
    TipoDocumentoSerializer,
)


def verificar_y_marcar_completo(cuenta_id):
    try:
        cuenta = CuentaContable.objects.get(id=cuenta_id)
        cierre = (
            CierreContabilidad.objects.filter(cliente=cuenta.cliente)
            .order_by("-fecha_creacion")
            .first()
        )
        set_principal = ClasificacionSet.objects.filter(cliente=cuenta.cliente).first()
        if not (cierre and set_principal):
            return
        cuentas = CuentaContable.objects.filter(cliente=cuenta.cliente)
        clasificadas = AccountClassification.objects.filter(
            cuenta__in=cuentas, set_clas=set_principal
        ).values_list("cuenta_id", flat=True)
        if cuentas.exclude(id__in=clasificadas).count() == 0:
            cierre.estado = "completo"
            cierre.save(update_fields=["estado"])
    except Exception as e:
        logger.exception("Error al verificar cierre completo: %s", e)


class ClasificacionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="progreso_todos_los_sets")
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
                cuenta__in=cuentas, set_clas=set_obj
            ).values_list("cuenta_id", flat=True)
            cuentas_sin_clasif = cuentas.exclude(id__in=clasificadas)
            progreso_por_set.append(
                {
                    "set_id": set_obj.id,
                    "set_nombre": set_obj.nombre,
                    "cuentas_sin_clasificar": cuentas_sin_clasif.count(),
                    "total_cuentas": cuentas.count(),
                    "estado": (
                        "Completo" if cuentas_sin_clasif.count() == 0 else "Pendiente"
                    ),
                }
            )

        return Response(
            {
                "sets_progreso": progreso_por_set,
                "total_sets": sets.count(),
            }
        )

    @action(detail=True, methods=["get"], url_path="progreso")
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
                cuenta__in=cuentas, set_clas=set_principal
            ).values_list("cuenta_id", flat=True)
            cuentas_nuevas = cuentas.exclude(id__in=clasificadas).count()
            total_cuentas = cuentas.count()

        data = {
            "existen_sets": existen_sets,
            "cuentas_nuevas": cuentas_nuevas,
            "total_cuentas": total_cuentas,
            "parsing_completado": cierre.parsing_completado,
        }
        return Response(data)

    @action(detail=True, methods=["get"], url_path="cuentas_pendientes")
    def cuentas_pendientes(self, request, pk=None):
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        cuentas_ids = CuentaContable.objects.filter(cliente=cierre.cliente).values_list(
            "id", flat=True
        )

        # Trae las cuentas clasificadas SOLO SI hay sets
        sets = ClasificacionSet.objects.filter(cliente=cierre.cliente)
        cuentas_clasificadas_ids = []
        set_clas = sets.first() if sets.exists() else None

        if set_clas:
            cuentas_clasificadas_ids = AccountClassification.objects.filter(
                set_clas=set_clas, cuenta_id__in=cuentas_ids
            ).values_list("cuenta", flat=True)

        # Trae las cuentas faltantes (todas si no hay set, o las que no estén clasificadas si hay set)
        if set_clas:
            cuentas_faltantes = CuentaContable.objects.filter(
                id__in=cuentas_ids
            ).exclude(id__in=cuentas_clasificadas_ids)
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
        return Response({"sin_set": not sets.exists(), "cuentas_faltantes": data})

    @action(detail=False, methods=["post"], url_path="clasificar")
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
            },
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


class AnalisisCuentaCierreViewSet(viewsets.ModelViewSet):
    queryset = AnalisisCuentaCierre.objects.all()
    serializer_class = AnalisisCuentaCierreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cierre_id = self.request.query_params.get("cierre")
        if cierre_id:
            return self.queryset.filter(cierre_id=cierre_id)
        return self.queryset


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_tipo_documento(request, cliente_id):
    # Busca si ya existe un tipo de documento asociado al cliente
    existe_tipos = TipoDocumento.objects.filter(cliente_id=cliente_id).exists()

    if existe_tipos:
        return Response({"estado": "subido"})

    # Si no hay tipos activos, verificar si hay uploads exitosos anteriores eliminados
    upload_log_eliminado = UploadLog.objects.filter(
        cliente_id=cliente_id, tipo_upload="tipo_documento", estado="datos_eliminados"
    ).exists()

    if upload_log_eliminado:
        return Response(
            {
                "estado": "pendiente",
                "mensaje": "Datos eliminados previamente - puede volver a subir",
                "historial_eliminado": True,
            }
        )

    return Response({"estado": "pendiente"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_upload_log(request, upload_log_id):
    """
    Consulta el estado de un UploadLog específico
    """
    try:
        upload_log = UploadLog.objects.get(id=upload_log_id)

        # Verificar que el usuario tenga acceso al cliente
        # (Opcional: agregar más validaciones de permisos si es necesario)

        return Response(
            {
                "id": upload_log.id,
                "tipo": upload_log.tipo_upload,
                "cliente_id": upload_log.cliente.id,
                "cliente_nombre": upload_log.cliente.nombre,
                "estado": upload_log.estado,
                "nombre_archivo": upload_log.nombre_archivo_original,
                "fecha_creacion": upload_log.fecha_subida,
                "tiempo_procesamiento": (
                    str(upload_log.tiempo_procesamiento)
                    if upload_log.tiempo_procesamiento
                    else None
                ),
                "errores": upload_log.errores,
                # Campos que pueden no existir en este modelo
                "resumen": upload_log.resumen,
            }
        )

    except UploadLog.DoesNotExist:
        return Response({"error": "UploadLog no encontrado"}, status=404)
    except Exception as e:
        logger.exception("Error al consultar UploadLog: %s", e)
        return Response({"error": "Error interno del servidor"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cuentas_pendientes_set(request, cliente_id, set_id):
    cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)
    clasificadas = AccountClassification.objects.filter(
        cuenta__in=cuentas, set_clas_id=set_id
    ).values_list("cuenta_id", flat=True)
    pendientes = cuentas.exclude(id__in=clasificadas)
    data = [{"id": c.id, "codigo": c.codigo, "nombre": c.nombre} for c in pendientes]
    return Response({"cuentas_faltantes": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_uploads_cliente(request, cliente_id):
    """
    Obtiene el historial de uploads para un cliente específico
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Obtener parámetros de filtro
    tipo_upload = request.GET.get("tipo", None)  # TipoDocumento, LibroMayor, etc.
    limit = int(request.GET.get("limit", 20))  # Límite de resultados

    try:
        # Filtrar UploadLogs
        queryset = UploadLog.objects.filter(cliente=cliente).order_by("-fecha_subida")

        if tipo_upload:
            queryset = queryset.filter(tipo_upload=tipo_upload)

        # Limitar resultados
        upload_logs = queryset[:limit]

        # Serializar datos
        data = []
        for log in upload_logs:
            data.append(
                {
                    "id": log.id,
                    "tipo": log.tipo_upload,
                    "estado": log.estado,
                    "nombre_archivo": log.nombre_archivo_original,
                    "tamaño_archivo": log.tamaño_archivo,
                    "fecha_creacion": log.fecha_subida,
                    "usuario": log.usuario.correo_bdo if log.usuario else None,
                    "tiempo_procesamiento": (
                        str(log.tiempo_procesamiento)
                        if log.tiempo_procesamiento
                        else None
                    ),
                    "errores": (
                        log.errores[:200] + "..."
                        if log.errores and len(log.errores) > 200
                        else log.errores
                    ),  # Truncar errores largos
                }
            )

        return Response(
            {
                "cliente_id": cliente.id,
                "cliente_nombre": cliente.nombre,
                "total_uploads": UploadLog.objects.filter(cliente=cliente).count(),
                "uploads": data,
            }
        )

    except Exception as e:
        logger.exception("Error al obtener historial de uploads: %s", e)
        return Response({"error": "Error interno del servidor"}, status=500)


@api_view(["POST"])
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

    # Verificar si ya existen datos para este cliente
    tipos_existentes = TipoDocumento.objects.filter(cliente=cliente).count()
    if tipos_existentes > 0:
        # Buscar cierre para actividad
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")
        
        # Registrar intento de upload con datos existentes
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="upload_excel",
            descripcion=f"Upload rechazado: ya existen {tipos_existentes} tipos de documento",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "tipos_existentes": tipos_existentes,
                "razon_rechazo": "datos_existentes",
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "error": "Ya existen tipos de documento para este cliente",
                "mensaje": "Debe eliminar todos los registros existentes antes de subir un nuevo archivo",
                "tipos_existentes": tipos_existentes,
                "accion_requerida": "Usar 'Eliminar todos' primero",
            },
            status=409,
        )  # 409 Conflict

    # Crear registro de UploadLog antes de procesar
    try:
        # Primero validar el nombre del archivo
        try:
            # Validación básica del nombre del archivo usando el método del modelo
            es_valido, mensaje = UploadLog.validar_nombre_archivo(
                archivo.name, "TipoDocumento", cliente.rut
            )
            if not es_valido:
                # Si mensaje es dict, es un error detallado
                if isinstance(mensaje, dict):
                    return Response(
                        {
                            "error": mensaje["error"],
                            "archivo_recibido": mensaje.get(
                                "archivo_recibido", archivo.name
                            ),
                            "formato_esperado": mensaje.get("formato_esperado", ""),
                            "sugerencia": mensaje.get("sugerencia", ""),
                            "tipos_validos": mensaje.get("tipos_validos", []),
                        },
                        status=400,
                    )
                else:
                    # Mensaje simple
                    rut_limpio = (
                        cliente.rut.replace(".", "").replace("-", "")
                        if cliente.rut
                        else cliente.id
                    )
                    return Response(
                        {
                            "error": "Nombre de archivo inválido",
                            "mensaje": mensaje,
                            "formato_esperado": f"{rut_limpio}_TipoDocumento.xlsx",
                            "archivo_recibido": archivo.name,
                        },
                        status=400,
                    )
        except Exception as validation_error:
            logger.exception(
                "Error en validación de nombre de archivo: %s", validation_error
            )
            return Response(
                {
                    "error": "Error en validación de archivo",
                    "detalle": str(validation_error),
                },
                status=400,
            )

        # Intentar determinar el cierre más reciente del cliente (mismo patrón que clasificación)
        cierre_relacionado = None
        cierre_id = request.data.get("cierre_id")  # Si el frontend lo envía
        
        print(f"🔍 DEBUG: cierre_id del frontend: {cierre_id}")
        
        if cierre_id:
            try:
                cierre_relacionado = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                print(f"✅ DEBUG: Cierre encontrado usando cierre_id del frontend: {cierre_relacionado.id} - {cierre_relacionado.periodo}")
            except CierreContabilidad.DoesNotExist:
                print(f"❌ DEBUG: Cierre con id {cierre_id} no encontrado, buscando automáticamente")
                pass
        else:
            print("🔎 DEBUG: No se envió cierre_id desde frontend, buscando automáticamente")
        
        # Si no se especifica cierre, buscar el más reciente que no esté cerrado
        if not cierre_relacionado:
            cierre_relacionado = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
            
            if cierre_relacionado:
                print(f"🔍 DEBUG: Cierre encontrado automáticamente: {cierre_relacionado.id} - {cierre_relacionado.periodo} - Estado: {cierre_relacionado.estado}")
            else:
                print("⚠️ DEBUG: No se encontró ningún cierre abierto para el cliente")

        print(f"📄 DEBUG: UploadLog se creará con cierre: {cierre_relacionado.id if cierre_relacionado else 'None'}")

        upload_log = UploadLog.objects.create(
            tipo_upload="tipo_documento",
            cliente=cliente,
            cierre=cierre_relacionado,  # Asociar al cierre encontrado
            usuario=request.user,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
            estado="subido",
            ip_usuario=get_client_ip(request),
        )

        # Limpiar archivos temporales anteriores del mismo cliente
        patron_temp = f"temp/tipo_doc_cliente_{cliente_id}*"

        archivos_temp_anteriores = glob.glob(
            os.path.join(
                default_storage.location, "temp", f"tipo_doc_cliente_{cliente_id}*"
            )
        )
        for archivo_anterior in archivos_temp_anteriores:
            try:
                os.remove(archivo_anterior)
            except OSError:
                pass  # Ignorar si no se puede eliminar

        # Guardar archivo temporalmente (media/temp/)
        nombre_archivo = f"temp/tipo_doc_cliente_{cliente_id}_{upload_log.id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)

        # Actualizar UploadLog con la ruta del archivo
        upload_log.ruta_archivo = ruta_guardada
        upload_log.save()

        # Registrar actividad de subida
        periodo_actividad = cierre_relacionado.periodo if cierre_relacionado else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="upload_excel",
            descripcion=f"Subido archivo: {archivo.name} (UploadLog ID: {upload_log.id})",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "tamaño_bytes": archivo.size,
                "tipo_contenido": archivo.content_type,
                "upload_log_id": upload_log.id,
                "ruta_archivo": ruta_guardada,
                "cierre_id": cierre_relacionado.id if cierre_relacionado else None,
            },
            resultado="exito",
            ip_address=get_client_ip(request),
        )

        # Enviar tarea a Celery usando el nuevo sistema UploadLog
        procesar_tipo_documento_con_upload_log.delay(upload_log.id)

        return Response(
            {
                "mensaje": "Archivo recibido y tarea enviada",
                "upload_log_id": upload_log.id,
                "estado": upload_log.estado,
            }
        )

    except Exception as e:
        logger.exception("Error al crear UploadLog para tipo documento: %s", e)

        # Buscar cierre para actividad de error
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

        # Registrar error en activity log
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="upload_excel",
            descripcion=f"Error al crear UploadLog: {str(e)}",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name, 
                "error": str(e),
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {"error": "Error interno al procesar el archivo", "detalle": str(e)},
            status=500,
        )


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_clasificacion_bulk(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")
    cierre_id = request.data.get("cierre_id")  # Obtener cierre_id si se envía

    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    try:
        es_valido, mensaje = UploadLog.validar_nombre_archivo(
            archivo.name, "Clasificacion", cliente.rut
        )
        if not es_valido:
            if isinstance(mensaje, dict):
                return Response(mensaje, status=400)
            else:
                return Response({"error": mensaje}, status=400)

        # BUSCAR EL CIERRE ASOCIADO (igual que en tipo_documento)
        cierre_relacionado = None
        
        # Intentar usar el cierre_id proporcionado desde el frontend
        if cierre_id:
            try:
                cierre_relacionado = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                logger.info(f"✅ Cierre encontrado usando cierre_id del frontend: {cierre_relacionado.id} - {cierre_relacionado.periodo}")
            except CierreContabilidad.DoesNotExist:
                logger.warning(f"❌ Cierre con id {cierre_id} no encontrado, buscando automáticamente")
                pass
        else:
            logger.info("🔎 No se envió cierre_id desde frontend, buscando automáticamente")
        
        # Si no se especifica cierre, buscar el más reciente que no esté cerrado
        if not cierre_relacionado:
            cierre_relacionado = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
            
            if cierre_relacionado:
                logger.info(f"🔍 Cierre encontrado automáticamente: {cierre_relacionado.id} - {cierre_relacionado.periodo} - Estado: {cierre_relacionado.estado}")
            else:
                logger.warning("⚠️ No se encontró ningún cierre abierto para el cliente")

        logger.info(f"📋 UploadLog de clasificación se creará con cierre: {cierre_relacionado.id if cierre_relacionado else 'None'}")

        upload_log = UploadLog.objects.create(
            tipo_upload="clasificacion",
            cliente=cliente,
            cierre=cierre_relacionado,  # ✅ Asociar al cierre encontrado
            usuario=request.user,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
            estado="subido",
            ip_usuario=get_client_ip(request),
        )

        patron_temp = f"temp/clasificacion_cliente_{cliente_id}_*"

        archivos_temp = glob.glob(
            os.path.join(
                default_storage.location,
                "temp",
                f"clasificacion_cliente_{cliente_id}_*",
            )
        )
        for a in archivos_temp:
            try:
                os.remove(a)
            except OSError:
                pass

        nombre_archivo = f"temp/clasificacion_cliente_{cliente_id}_{upload_log.id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)

        upload_log.ruta_archivo = ruta_guardada
        upload_log.save()

        # Usar el período del cierre asociado al UploadLog
        periodo_actividad = cierre_relacionado.periodo if cierre_relacionado else date.today().strftime("%Y-%m")

        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="upload_excel",
            descripcion=f"Subido archivo de clasificaciones: {archivo.name} (UploadLog ID: {upload_log.id})",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "tamaño_bytes": archivo.size,
                "upload_log_id": upload_log.id,
                "ruta_archivo": ruta_guardada,
                "cierre_id": cierre_relacionado.id if cierre_relacionado else None,
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        procesar_clasificacion_con_upload_log.delay(upload_log.id)

        return Response(
            {
                "mensaje": "Archivo recibido y tarea enviada",
                "upload_log_id": upload_log.id,
                "estado": upload_log.estado,
            }
        )

    except Exception as e:
        logger.exception("Error al crear UploadLog para clasificacion: %s", e)
        
        # Buscar cierre para actividad de error
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="upload_excel",
            descripcion=f"Error al crear UploadLog: {str(e)}",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name, 
                "error": str(e),
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(
            {"error": "Error interno al procesar el archivo", "detalle": str(e)},
            status=500,
        )


@api_view(["GET"])
def test_celery(request):
    tarea_de_prueba.delay("Mundo")  # <- se ejecuta en segundo plano
    return Response({"mensaje": "Tarea enviada a Celery"})


@api_view(["GET"])
@permission_classes([IsAuthenticated, SoloContabilidadAsignadoOGerente])
def resumen_cliente(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    ultimo = (
        CierreContabilidad.objects.filter(cliente=cliente).order_by("-periodo").first()
    )

    return Response(
        {
            "cliente_id": cliente.id,
            "cliente": cliente.nombre,
            "ultimo_cierre": ultimo.periodo if ultimo else None,
            "estado_ultimo_cierre": ultimo.estado if ultimo else None,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_tipos_documento(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Contar registros antes de eliminar
    count = TipoDocumento.objects.filter(cliente=cliente).count()
    upload_logs_count = UploadLog.objects.filter(
        cliente=cliente, tipo_upload="tipo_documento"
    ).count()

    # Variables para el log
    archivos_eliminados = []

    try:
        # 1. Buscar y eliminar archivo asociado si existe
        try:
            archivo_tipo_doc = TipoDocumentoArchivo.objects.get(cliente=cliente)
            archivo_path = (
                archivo_tipo_doc.archivo.path if archivo_tipo_doc.archivo else None
            )
            archivo_name = (
                archivo_tipo_doc.archivo.name if archivo_tipo_doc.archivo else None
            )

            # Eliminar archivo físico del sistema
            if archivo_path and os.path.exists(archivo_path):
                os.remove(archivo_path)
                archivos_eliminados.append(archivo_name)

            # Eliminar registro del archivo
            archivo_tipo_doc.delete()

        except TipoDocumentoArchivo.DoesNotExist:
            # No hay archivo que eliminar, continuar normalmente
            pass

        # 2. Limpiar archivos temporales de UploadLogs pero conservar registros para auditoría
        upload_logs = UploadLog.objects.filter(
            cliente=cliente, tipo_upload="tipo_documento"
        )
        for upload_log in upload_logs:
            # Solo eliminar archivos temporales, conservar registros para historial
            if upload_log.ruta_archivo:
                ruta_completa = os.path.join(
                    default_storage.location, upload_log.ruta_archivo
                )
                if os.path.exists(ruta_completa):
                    try:
                        os.remove(ruta_completa)
                        archivos_eliminados.append(upload_log.ruta_archivo)
                    except OSError:
                        pass

            # Marcar como eliminado para auditoría, pero conservar el registro
            if upload_log.estado == "completado":
                upload_log.estado = "datos_eliminados"
                upload_log.resumen = f"Datos procesados eliminados el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                upload_log.save()

        # NO eliminar los UploadLogs - conservar para historial de auditoría

        # 3. Eliminar registros de TipoDocumento
        TipoDocumento.objects.filter(cliente=cliente).delete()

        # 4. Buscar cierre para actividad
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

        # 5. Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="bulk_delete",
            descripcion=f"Eliminados todos los tipos de documento ({count} registros) y archivos asociados. UploadLogs conservados para auditoría",
            usuario=request.user,
            detalles={
                "registros_eliminados": count,
                "upload_logs_conservados": upload_logs_count,
                "upload_logs_marcados_eliminados": upload_logs.filter(
                    estado="datos_eliminados"
                ).count(),
                "archivos_eliminados": archivos_eliminados,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": "Tipos de documento y archivos eliminados correctamente. Historial de uploads conservado para auditoría",
                "registros_eliminados": count,
                "upload_logs_conservados": upload_logs_count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        # Buscar cierre para actividad de error
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")
        
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="bulk_delete",
            descripcion=f"Error al eliminar tipos de documento y archivos: {str(e)}",
            usuario=request.user,
            detalles={
                "error": str(e),
                "registros_contados": count,
                "upload_logs_contados": upload_logs_count,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tipos_documento_cliente(request, cliente_id):
    tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)

    # Log eliminado - se registrará solo desde el frontend cuando se abra el modal manualmente

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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_tipos_documento(request, cliente_id):
    """
    Endpoint específico para registrar cuando el usuario abre el modal de tipos de documento
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)

    # Buscar cierre para actividad
    cierre_para_actividad = None
    try:
        cierre_para_actividad = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
    except Exception:
        pass
    
    periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

    # Registrar visualización manual del modal
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo_actividad,
        tarjeta="tipo_documento",
        accion="view_data",
        descripcion=f"Abrió modal de tipos de documento ({tipos.count()} registros)",
        usuario=request.user,
        detalles={
            "total_registros": tipos.count(), 
            "accion_origen": "modal_manual",
            "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"mensaje": "Visualización registrada"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_clasificaciones(request, cliente_id):
    """
    Endpoint específico para registrar cuando el usuario abre el modal de clasificaciones
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    # Obtener el upload ID del request
    upload_log_id = request.data.get("upload_log_id")

    # Buscar cierre para actividad
    cierre_para_actividad = None
    try:
        cierre_para_actividad = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
    except Exception:
        pass
    
    periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

    try:
        # Contar registros del upload específico
        if upload_log_id:
            registros = ClasificacionCuentaArchivo.objects.filter(
                upload_log_id=upload_log_id
            )
            total_registros = registros.count()
            descripcion = f"Abrió modal de clasificaciones para upload {upload_log_id} ({total_registros} registros)"
            detalles = {
                "total_registros": total_registros,
                "upload_log_id": upload_log_id,
                "accion_origen": "modal_manual",
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            }
        else:
            # Si no hay upload_log_id, contar todos los registros del cliente
            registros = ClasificacionCuentaArchivo.objects.filter(cliente_id=cliente_id)
            total_registros = registros.count()
            descripcion = f"Abrió modal de clasificaciones del cliente ({total_registros} registros)"
            detalles = {
                "total_registros": total_registros,
                "accion_origen": "modal_manual",
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            }
    except Exception as e:
        total_registros = 0
        descripcion = (
            f"Abrió modal de clasificaciones (error al contar registros: {str(e)})"
        )
        detalles = {
            "error": str(e),
            "upload_log_id": upload_log_id,
            "accion_origen": "modal_manual",
            "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
        }

    # Registrar visualización manual del modal
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo_actividad,
        tarjeta="clasificacion",
        accion="view_data",
        descripcion=descripcion,
        usuario=request.user,
        detalles=detalles,
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"mensaje": "Visualización registrada"})


# ===== FUNCIONES API PARA NOMBRES EN INGLÉS =====


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_nombres_ingles(request, cliente_id):
    # Busca si ya existen nombres en inglés asociados al cliente
    existe = NombreIngles.objects.filter(cliente_id=cliente_id).exists()
    if existe:
        return Response({"estado": "subido"})

    # Si no hay datos activos, verificar si hubo uploads eliminados previamente
    upload_log_eliminado = UploadLog.objects.filter(
        cliente_id=cliente_id, tipo_upload="nombres_ingles", estado="datos_eliminados"
    ).exists()

    if upload_log_eliminado:
        return Response(
            {
                "estado": "pendiente",
                "mensaje": "Datos eliminados previamente - puede volver a subir",
                "historial_eliminado": True,
            }
        )

    return Response({"estado": "pendiente"})


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_nombres_ingles(request):
    cliente_id = request.data.get("cliente_id")
    archivo = request.FILES.get("archivo")

    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Verificar si ya existen datos para este cliente
    nombres_existentes = NombreIngles.objects.filter(cliente=cliente).count()
    if nombres_existentes > 0:
        # Buscar cierre para actividad
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")
        
        # Registrar intento de upload con datos existentes
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="nombres_ingles",
            accion="upload_excel",
            descripcion=f"Upload rechazado: ya existen {nombres_existentes} nombres en inglés",
            usuario=request.user,
            detalles={
                "nombre_archivo": archivo.name,
                "nombres_existentes": nombres_existentes,
                "razon_rechazo": "datos_existentes",
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "error": "Ya existen nombres en inglés para este cliente",
                "mensaje": "Debe eliminar todos los registros existentes antes de subir un nuevo archivo",
                "nombres_existentes": nombres_existentes,
                "accion_requerida": "Usar 'Eliminar todos' primero",
            },
            status=409,
        )  # 409 Conflict

    # Validar nombre de archivo utilizando UploadLog
    es_valido, msg = UploadLog.validar_nombre_archivo(
        archivo.name, "NombresIngles", cliente.rut
    )
    if not es_valido:
        if isinstance(msg, dict):
            return Response(msg, status=400)
        return Response({"error": msg}, status=400)

    # Buscar cierre relacionado automáticamente
    cierre_relacionado = CierreContabilidad.objects.filter(
        cliente=cliente,
        estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
    ).order_by('-fecha_creacion').first()

    # Crear UploadLog
    upload_log = UploadLog.objects.create(
        tipo_upload="nombres_ingles",
        cliente=cliente,
        cierre=cierre_relacionado,
        usuario=request.user,
        nombre_archivo_original=archivo.name,
        tamaño_archivo=archivo.size,
        estado="subido",
        ip_usuario=get_client_ip(request),
    )

    # Guardar archivo temporal
    nombre_archivo = f"temp/nombres_ingles_cliente_{cliente_id}_{upload_log.id}.xlsx"
    ruta_guardada = default_storage.save(nombre_archivo, archivo)
    upload_log.ruta_archivo = ruta_guardada
    upload_log.save(update_fields=["ruta_archivo"])

    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=cierre_relacionado.periodo if cierre_relacionado else date.today().strftime("%Y-%m"),
        tarjeta="nombres_ingles",
        accion="upload_excel",
        descripcion=f"Subido archivo: {archivo.name} (UploadLog ID: {upload_log.id})",
        usuario=request.user,
        detalles={
            "nombre_archivo": archivo.name,
            "tamaño_bytes": archivo.size,
            "upload_log_id": upload_log.id,
            "ruta_archivo": ruta_guardada,
            "cierre_id": cierre_relacionado.id if cierre_relacionado else None,
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    procesar_nombres_ingles_con_upload_log.delay(upload_log.id)

    return Response({
        "mensaje": "Archivo recibido y tarea enviada",
        "upload_log_id": upload_log.id,
        "estado": upload_log.estado,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nombres_ingles_cliente(request, cliente_id):
    nombres = NombreIngles.objects.filter(cliente_id=cliente_id)

    # Log eliminado - se registrará solo desde el frontend cuando se abra el modal manualmente

    # O usa un serializer si tienes uno
    data = [
        {
            "id": nombre.id,
            "cuenta_codigo": nombre.cuenta_codigo,
            "nombre_ingles": nombre.nombre_ingles,
        }
        for nombre in nombres
    ]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_nombres_ingles(request, cliente_id):
    """
    Endpoint específico para registrar cuando el usuario abre el modal de nombres en inglés
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    nombres = NombreIngles.objects.filter(cliente_id=cliente_id)

    # Buscar cierre para actividad
    cierre_para_actividad = None
    try:
        cierre_para_actividad = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
    except Exception:
        pass
    
    periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

    # Registrar visualización manual del modal
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo_actividad,
        tarjeta="nombres_ingles",
        accion="view_data",
        descripcion=f"Abrió modal de nombres en inglés ({nombres.count()} registros)",
        usuario=request.user,
        detalles={
            "total_registros": nombres.count(), 
            "accion_origen": "modal_manual",
            "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"mensaje": "Visualización registrada"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_nombres_ingles(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Contar registros antes de eliminar
    count = NombreIngles.objects.filter(cliente=cliente).count()

    # Variables para el log
    archivos_eliminados = []

    try:
        # 1. Buscar y eliminar archivo asociado si existe
        try:
            archivo_nombres_ingles = NombreInglesArchivo.objects.get(cliente=cliente)
            archivo_path = (
                archivo_nombres_ingles.archivo.path
                if archivo_nombres_ingles.archivo
                else None
            )
            archivo_name = (
                archivo_nombres_ingles.archivo.name
                if archivo_nombres_ingles.archivo
                else None
            )

            # Eliminar archivo físico del sistema
            if archivo_path and os.path.exists(archivo_path):
                os.remove(archivo_path)
                archivos_eliminados.append(archivo_name)

            # Eliminar registro del archivo
            archivo_nombres_ingles.delete()

        except NombreInglesArchivo.DoesNotExist:
            # No hay archivo que eliminar, continuar normalmente
            pass

        # 2. Limpiar archivos temporales de UploadLogs pero conservar registros
        upload_logs = UploadLog.objects.filter(
            cliente=cliente, tipo_upload="nombres_ingles"
        )
        upload_logs_count = upload_logs.count()
        for upload_log in upload_logs:
            if upload_log.ruta_archivo:
                ruta_completa = os.path.join(
                    default_storage.location, upload_log.ruta_archivo
                )
                if os.path.exists(ruta_completa):
                    try:
                        os.remove(ruta_completa)
                        archivos_eliminados.append(upload_log.ruta_archivo)
                    except OSError:
                        pass

            if upload_log.estado == "completado":
                upload_log.estado = "datos_eliminados"
                upload_log.resumen = (
                    f"Datos procesados eliminados el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                upload_log.save()

        # 3. Eliminar registros de NombreIngles
        NombreIngles.objects.filter(cliente=cliente).delete()

        # 4. Buscar cierre para actividad
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")

        # 5. Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="nombres_ingles",
            accion="bulk_delete",
            descripcion=f"Eliminados todos los nombres en inglés ({count} registros) y archivos asociados",
            usuario=request.user,
            detalles={
                "registros_eliminados": count,
                "upload_logs_conservados": upload_logs_count,
                "upload_logs_marcados_eliminados": upload_logs.filter(
                    estado="datos_eliminados"
                ).count(),
                "archivos_eliminados": archivos_eliminados,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": "Nombres en inglés y archivos eliminados correctamente",
                "registros_eliminados": count,
                "upload_logs_conservados": upload_logs_count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        # Buscar cierre para actividad de error
        cierre_para_actividad = None
        try:
            cierre_para_actividad = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
        except Exception:
            pass
        
        periodo_actividad = cierre_para_actividad.periodo if cierre_para_actividad else date.today().strftime("%Y-%m")
        
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="nombres_ingles",
            accion="bulk_delete",
            descripcion=f"Error al eliminar nombres en inglés y archivos: {str(e)}",
            usuario=request.user,
            detalles={
                "error": str(e),
                "registros_contados": count,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)


class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset

    def perform_create(self, serializer):
        # Validar que el cliente existe
        cliente_id = self.request.data.get("cliente")
        if not cliente_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Cliente es requerido")

        try:
            from api.models import Cliente

            cliente = Cliente.objects.get(id=cliente_id)
            instance = serializer.save()

            # Obtener período correcto para el cliente
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)

            # Registrar creación manual
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_create",
                descripcion=f"Creado tipo documento: {instance.codigo} - {instance.descripcion}",
                usuario=self.request.user,
                detalles={
                    "codigo": instance.codigo,
                    "descripcion": instance.descripcion,
                    "id": instance.id,
                },
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Cliente.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Cliente no encontrado")
        except Exception as e:
            # Obtener período correcto para el cliente si hay error
            periodo_actividad = date.today().strftime("%Y-%m")  # Fallback en caso de error
            try:
                if cliente_id:
                    cliente = Cliente.objects.get(id=cliente_id)
                    periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            except:
                pass
            
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_create",
                descripcion=f"Error al crear tipo documento: {str(e)}",
                usuario=self.request.user,
                detalles={"error": str(e), "data": self.request.data},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    def perform_update(self, serializer):
        old_instance = self.get_object()
        cliente_id = old_instance.cliente.id
        cliente = old_instance.cliente

        try:
            # No permitir cambiar el cliente en una actualización
            if "cliente" in self.request.data:
                instance = serializer.save(cliente_id=cliente_id)
            else:
                instance = serializer.save()

            # Obtener período correcto para el cliente
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)

            # Registrar edición
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_edit",
                descripcion=f"Editado tipo documento ID:{instance.id}: {old_instance.codigo} → {instance.codigo}",
                usuario=self.request.user,
                detalles={
                    "id": instance.id,
                    "cambios": {
                        "codigo": {
                            "anterior": old_instance.codigo,
                            "nuevo": instance.codigo,
                        },
                        "descripcion": {
                            "anterior": old_instance.descripcion,
                            "nuevo": instance.descripcion,
                        },
                    },
                },
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Obtener período correcto para el cliente
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_edit",
                descripcion=f"Error al editar tipo documento ID:{old_instance.id}: {str(e)}",
                usuario=self.request.user,
                detalles={
                    "error": str(e),
                    "id": old_instance.id,
                    "data": self.request.data,
                },
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        cliente = instance.cliente
        tipo_info = {
            "id": instance.id,
            "codigo": instance.codigo,
            "descripcion": instance.descripcion,
        }

        try:
            instance.delete()

            # Obtener período correcto para el cliente
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)

            # Registrar eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_delete",
                descripcion=f'Eliminado tipo documento: {tipo_info["codigo"]} - {tipo_info["descripcion"]}',
                usuario=self.request.user,
                detalles=tipo_info,
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Obtener período correcto para el cliente
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo_actividad,
                tarjeta="tipo_documento",
                accion="manual_delete",
                descripcion=f'Error al eliminar tipo documento ID:{tipo_info["id"]}: {str(e)}',
                usuario=self.request.user,
                detalles={"error": str(e), **tipo_info},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise


class NombreInglesViewSet(viewsets.ModelViewSet):
    queryset = NombreIngles.objects.all()
    serializer_class = NombreInglesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset

    def perform_create(self, serializer):
        # Validar que el cliente existe
        cliente_id = self.request.data.get("cliente")
        if not cliente_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Cliente es requerido")

        try:
            from api.models import Cliente

            cliente = Cliente.objects.get(id=cliente_id)
            instance = serializer.save()

            # Registrar creación manual
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_create",
                descripcion=f"Creado nombre inglés: {instance.cuenta_codigo} - {instance.nombre_ingles}",
                usuario=self.request.user,
                detalles={
                    "cuenta_codigo": instance.cuenta_codigo,
                    "nombre_ingles": instance.nombre_ingles,
                    "id": instance.id,
                },
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Cliente.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Cliente no encontrado")
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_create",
                descripcion=f"Error al crear nombre inglés: {str(e)}",
                usuario=self.request.user,
                detalles={"error": str(e), "data": self.request.data},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    def perform_update(self, serializer):
        old_instance = self.get_object()
        cliente_id = old_instance.cliente.id

        try:
            # No permitir cambiar el cliente en una actualización
            if "cliente" in self.request.data:
                instance = serializer.save(cliente_id=cliente_id)
            else:
                instance = serializer.save()

            # Registrar edición
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_edit",
                descripcion=f"Editado nombre inglés ID:{instance.id}: {old_instance.cuenta_codigo} → {instance.cuenta_codigo}",
                usuario=self.request.user,
                detalles={
                    "id": instance.id,
                    "cambios": {
                        "cuenta_codigo": {
                            "anterior": old_instance.cuenta_codigo,
                            "nuevo": instance.cuenta_codigo,
                        },
                        "nombre_ingles": {
                            "anterior": old_instance.nombre_ingles,
                            "nuevo": instance.nombre_ingles,
                        },
                    },
                },
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_edit",
                descripcion=f"Error al editar nombre inglés ID:{old_instance.id}: {str(e)}",
                usuario=self.request.user,
                detalles={
                    "error": str(e),
                    "id": old_instance.id,
                    "data": self.request.data,
                },
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        nombre_info = {
            "id": instance.id,
            "cuenta_codigo": instance.cuenta_codigo,
            "nombre_ingles": instance.nombre_ingles,
        }

        try:
            instance.delete()

            # Registrar eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_delete",
                descripcion=f'Eliminado nombre inglés: {nombre_info["cuenta_codigo"]} - {nombre_info["nombre_ingles"]}',
                usuario=self.request.user,
                detalles=nombre_info,
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="manual_delete",
                descripcion=f'Error al eliminar nombre inglés ID:{nombre_info["id"]}: {str(e)}',
                usuario=self.request.user,
                detalles={"error": str(e), **nombre_info},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise


class CuentaContableViewSet(viewsets.ModelViewSet):
    queryset = CuentaContable.objects.all()
    serializer_class = CuentaContableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por cliente
        cliente = self.request.query_params.get("cliente")
        if cliente:
            queryset = queryset.filter(cliente=cliente)

        return queryset.order_by("codigo")


class AperturaCuentaViewSet(viewsets.ModelViewSet):
    queryset = AperturaCuenta.objects.all()
    serializer_class = AperturaCuentaSerializer
    permission_classes = [IsAuthenticated]


class MovimientoContableViewSet(viewsets.ModelViewSet):
    queryset = MovimientoContable.objects.all()
    serializer_class = MovimientoContableSerializer
    permission_classes = [IsAuthenticated]


class ClasificacionSetViewSet(viewsets.ModelViewSet):
    queryset = ClasificacionSet.objects.all()
    serializer_class = ClasificacionSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.order_by("nombre")

    def perform_create(self, serializer):
        instance = serializer.save()

        # Registrar creación de set
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="set_create",
            descripcion=f"Creado set de clasificación: {instance.nombre}",
            usuario=self.request.user,
            detalles={
                "set_id": instance.id,
                "set_nombre": instance.nombre,
                "accion_origen": "manual_sets_tab",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()

        # Registrar edición de set
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="set_edit",
            descripcion=f"Editado set de clasificación: {old_instance.nombre} → {instance.nombre}",
            usuario=self.request.user,
            detalles={
                "set_id": instance.id,
                "nombre_anterior": old_instance.nombre,
                "nombre_nuevo": instance.nombre,
                "accion_origen": "manual_sets_tab",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        set_info = {
            "id": instance.id,
            "nombre": instance.nombre,
            "cliente_id": instance.cliente.id,
        }

        try:
            # Contar opciones que se eliminarán
            opciones_count = ClasificacionOption.objects.filter(
                set_clas=instance
            ).count()

            super().perform_destroy(instance)

            # Registrar eliminación de set
            registrar_actividad_tarjeta(
                cliente_id=set_info["cliente_id"],
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="set_delete",
                descripcion=f'Eliminado set de clasificación: {set_info["nombre"]} (incluía {opciones_count} opciones)',
                usuario=self.request.user,
                detalles={
                    **set_info,
                    "opciones_eliminadas": opciones_count,
                    "accion_origen": "manual_sets_tab",
                },
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=set_info["cliente_id"],
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="set_delete",
                descripcion=f'Error al eliminar set de clasificación: {set_info["nombre"]} - {str(e)}',
                usuario=self.request.user,
                detalles={
                    **set_info,
                    "error": str(e),
                    "accion_origen": "manual_sets_tab",
                },
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise


class ClasificacionOptionViewSet(viewsets.ModelViewSet):
    queryset = ClasificacionOption.objects.all()
    serializer_class = ClasificacionOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        set_id = self.request.query_params.get("set_clas")
        if set_id:
            queryset = queryset.filter(set_clas_id=set_id)
        return queryset.order_by("valor")

    def perform_create(self, serializer):
        instance = serializer.save()

        # Registrar creación de opción
        registrar_actividad_tarjeta(
            cliente_id=instance.set_clas.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="option_create",
            descripcion=f"Creada opción de clasificación: {instance.valor} en set {instance.set_clas.nombre}",
            usuario=self.request.user,
            detalles={
                "opcion_id": instance.id,
                "opcion_valor": instance.valor,
                "set_id": instance.set_clas.id,
                "set_nombre": instance.set_clas.nombre,
                "accion_origen": "manual_sets_tab",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()

        # Registrar edición de opción
        registrar_actividad_tarjeta(
            cliente_id=instance.set_clas.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="option_edit",
            descripcion=f"Editada opción de clasificación: {old_instance.valor} → {instance.valor} en set {instance.set_clas.nombre}",
            usuario=self.request.user,
            detalles={
                "opcion_id": instance.id,
                "valor_anterior": old_instance.valor,
                "valor_nuevo": instance.valor,
                "set_id": instance.set_clas.id,
                "set_nombre": instance.set_clas.nombre,
                "accion_origen": "manual_sets_tab",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        opcion_info = {
            "id": instance.id,
            "valor": instance.valor,
            "set_id": instance.set_clas.id,
            "set_nombre": instance.set_clas.nombre,
            "cliente_id": instance.set_clas.cliente.id,
        }

        try:
            super().perform_destroy(instance)

            # Registrar eliminación de opción
            registrar_actividad_tarjeta(
                cliente_id=opcion_info["cliente_id"],
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="option_delete",
                descripcion=f'Eliminada opción de clasificación: {opcion_info["valor"]} del set {opcion_info["set_nombre"]}',
                usuario=self.request.user,
                detalles={**opcion_info, "accion_origen": "manual_sets_tab"},
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=opcion_info["cliente_id"],
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="option_delete",
                descripcion=f'Error al eliminar opción de clasificación: {opcion_info["valor"]} - {str(e)}',
                usuario=self.request.user,
                detalles={
                    **opcion_info,
                    "error": str(e),
                    "accion_origen": "manual_sets_tab",
                },
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise


class AccountClassificationViewSet(viewsets.ModelViewSet):
    queryset = AccountClassification.objects.select_related(
        "cuenta", "set_clas", "opcion", "asignado_por"
    ).all()
    serializer_class = AccountClassificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por cliente de la cuenta
        cuenta_cliente = self.request.query_params.get("cuenta__cliente")
        if cuenta_cliente:
            queryset = queryset.filter(cuenta__cliente=cuenta_cliente)

        return queryset.order_by("-fecha")

    def perform_create(self, serializer):
        # Asignar el usuario actual
        instance = serializer.save(asignado_por=self.request.user.usuario)

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cuenta.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="individual_create",
            descripcion=f"Creada clasificación: {instance.cuenta.codigo} → {instance.set_clas.nombre}: {instance.opcion.valor}",
            usuario=self.request.user,
            detalles={
                "cuenta_id": instance.cuenta.id,
                "cuenta_codigo": instance.cuenta.codigo,
                "set_nombre": instance.set_clas.nombre,
                "opcion_valor": instance.opcion.valor,
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cuenta.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="individual_edit",
            descripcion=f"Editada clasificación: {instance.cuenta.codigo} → {instance.set_clas.nombre}: {instance.opcion.valor}",
            usuario=self.request.user,
            detalles={
                "cuenta_id": instance.cuenta.id,
                "cuenta_codigo": instance.cuenta.codigo,
                "cambios": {
                    "set_anterior": old_instance.set_clas.nombre,
                    "set_nuevo": instance.set_clas.nombre,
                    "opcion_anterior": old_instance.opcion.valor,
                    "opcion_nueva": instance.opcion.valor,
                },
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        # Guardar info antes de eliminar
        clasificacion_info = {
            "cuenta_codigo": instance.cuenta.codigo,
            "set_nombre": instance.set_clas.nombre,
            "opcion_valor": instance.opcion.valor,
        }
        cliente_id = instance.cuenta.cliente.id

        # Eliminar
        instance.delete()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="individual_delete",
            descripcion=f'Eliminada clasificación: {clasificacion_info["cuenta_codigo"]} → {clasificacion_info["set_nombre"]}: {clasificacion_info["opcion_valor"]}',
            usuario=self.request.user,
            detalles=clasificacion_info,
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )


class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer
    permission_classes = [IsAuthenticated]


class CentroCostoViewSet(viewsets.ModelViewSet):
    queryset = CentroCosto.objects.all()
    serializer_class = CentroCostoSerializer
    permission_classes = [IsAuthenticated]


class AuxiliarViewSet(viewsets.ModelViewSet):
    queryset = Auxiliar.objects.all()
    serializer_class = AuxiliarSerializer
    permission_classes = [IsAuthenticated]


# ViewSets para uploads con logging de cambios


class ClasificacionCuentaArchivoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los registros raw de clasificaciones antes del mapeo
    """

    queryset = ClasificacionCuentaArchivo.objects.all()
    serializer_class = ClasificacionCuentaArchivoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        upload_log_id = self.request.query_params.get("upload_log")
        cliente_id = self.request.query_params.get("cliente")
        procesado = self.request.query_params.get("procesado")

        if upload_log_id:
            queryset = queryset.filter(upload_log_id=upload_log_id)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if procesado is not None:
            queryset = queryset.filter(procesado=procesado.lower() == "true")

        return queryset.order_by("fila_excel")

    def perform_create(self, serializer):
        """Personalizar la creación de registros"""
        # Asignar el upload automáticamente si se proporciona en los datos
        upload_log_id = self.request.data.get("upload_log")
        if upload_log_id:
            try:
                upload_log = UploadLog.objects.get(id=upload_log_id)
                # Asignar cliente del upload
                instance = serializer.save(
                    cliente=upload_log.cliente, upload_log=upload_log
                )

                # Registrar creación manual
                registrar_actividad_tarjeta(
                    cliente_id=upload_log.cliente.id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_create",
                    descripcion=f"Creado registro clasificación: {instance.numero_cuenta}",
                    usuario=self.request.user,
                    detalles={
                        "numero_cuenta": instance.numero_cuenta,
                        "clasificaciones": instance.clasificaciones,
                        "upload_log_id": upload_log_id,
                        "id": instance.id,
                    },
                    resultado="exito",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

            except UploadLog.DoesNotExist:
                instance = serializer.save()
        else:
            instance = serializer.save()
            # Si no hay upload_log_id, registrar sin cliente específico
            if hasattr(instance, "cliente") and instance.cliente:
                registrar_actividad_tarjeta(
                    cliente_id=instance.cliente.id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_create",
                    descripcion=f"Creado registro clasificación: {instance.numero_cuenta}",
                    usuario=self.request.user,
                    detalles={
                        "numero_cuenta": instance.numero_cuenta,
                        "clasificaciones": instance.clasificaciones,
                        "id": instance.id,
                    },
                    resultado="exito",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

    def perform_update(self, serializer):
        """Personalizar la actualización de registros"""
        old_instance = self.get_object()
        cliente_id = old_instance.cliente.id if old_instance.cliente else None

        try:
            # Si se actualiza un registro, mantener la fecha de procesado si ya estaba procesado
            if old_instance.procesado and serializer.validated_data.get(
                "procesado", True
            ):
                instance = serializer.save(fecha_procesado=old_instance.fecha_procesado)
            else:
                instance = serializer.save()

            # Registrar edición
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_edit",
                    descripcion=f"Editado registro clasificación ID:{instance.id}: {old_instance.numero_cuenta} → {instance.numero_cuenta}",
                    usuario=self.request.user,
                    detalles={
                        "id": instance.id,
                        "cambios": {
                            "numero_cuenta": {
                                "anterior": old_instance.numero_cuenta,
                                "nuevo": instance.numero_cuenta,
                            },
                            "clasificaciones": {
                                "anterior": old_instance.clasificaciones,
                                "nuevo": instance.clasificaciones,
                            },
                        },
                        "upload_log_id": (
                            instance.upload_log.id if instance.upload_log else None
                        ),
                    },
                    resultado="exito",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

        except Exception as e:
            # Registrar error
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_edit",
                    descripcion=f"Error al editar registro clasificación ID:{old_instance.id}: {str(e)}",
                    usuario=self.request.user,
                    detalles={
                        "error": str(e),
                        "id": old_instance.id,
                        "data": self.request.data,
                    },
                    resultado="error",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )
            raise

    def perform_destroy(self, instance):
        """Logging al eliminar registros"""
        cliente_id = instance.cliente.id if instance.cliente else None
        registro_info = {
            "id": instance.id,
            "numero_cuenta": instance.numero_cuenta,
            "clasificaciones": instance.clasificaciones,
            "upload_id": instance.upload.id if instance.upload else None,
        }

        try:
            logger.info(
                f"Eliminando registro de clasificación: {instance.numero_cuenta} del cliente {instance.cliente.nombre}"
            )
            super().perform_destroy(instance)

            # Registrar eliminación
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_delete",
                    descripcion=f'Eliminado registro clasificación: {registro_info["numero_cuenta"]}',
                    usuario=self.request.user,
                    detalles=registro_info,
                    resultado="exito",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )

        except Exception as e:
            # Registrar error
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime("%Y-%m"),
                    tarjeta="clasificacion",
                    accion="manual_delete",
                    descripcion=f'Error al eliminar registro clasificación ID:{registro_info["id"]}: {str(e)}',
                    usuario=self.request.user,
                    detalles={"error": str(e), **registro_info},
                    resultado="error",
                    ip_address=self.request.META.get("REMOTE_ADDR"),
                )
            raise

    @action(detail=False, methods=["post"])
    def procesar_mapeo(self, request):
        """
        Dispara el procesamiento de mapeo para un upload específico
        """
        upload_log_id = request.data.get("upload_log_id")

        if not upload_log_id:
            return Response({"error": "upload_log_id requerido"}, status=400)

        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            return Response({"error": "Upload no encontrado"}, status=404)

        # Verificar que haya registros para procesar
        registros_pendientes = ClasificacionCuentaArchivo.objects.filter(
            upload_log=upload_log, procesado=False
        ).count()

        if registros_pendientes == 0:
            return Response(
                {"error": "No hay registros pendientes para procesar"}, status=400
            )

        # Disparar tarea de mapeo
        from .tasks import procesar_mapeo_clasificaciones

        procesar_mapeo_clasificaciones.delay(upload_log_id)

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=upload_log.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="process_start",
            descripcion=f"Iniciado mapeo de clasificaciones para archivo: {upload_log.nombre_archivo_original}",
            usuario=request.user,
            detalles={
                "upload_log_id": upload_log_id,
                "registros_pendientes": registros_pendientes,
                "tipo_operacion": "mapeo",
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": "Procesamiento de mapeo iniciado",
                "registros_pendientes": registros_pendientes,
            }
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de registros por upload
        """
        upload_log_id = request.query_params.get("upload_log_id")

        if not upload_log_id:
            return Response({"error": "upload_log_id requerido"}, status=400)

        try:
            upload_log = UploadLog.objects.get(id=upload_log_id)
        except UploadLog.DoesNotExist:
            return Response({"error": "Upload no encontrado"}, status=404)

        registros = ClasificacionCuentaArchivo.objects.filter(upload_log=upload_log)
        total = registros.count()
        procesados = registros.filter(procesado=True).count()
        con_errores = registros.exclude(errores_mapeo="").count()
        pendientes = total - procesados

        return Response(
            {
                "total": total,
                "procesados": procesados,
                "pendientes": pendientes,
                "con_errores": con_errores,
                "upload_log_id": upload_log_id,
            }
        )


class NombresEnInglesUploadViewSet(viewsets.ModelViewSet):
    queryset = NombresEnInglesUpload.objects.all()
    serializer_class = NombresEnInglesUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        # Limpiar archivos temporales antiguos al subir nuevo archivo
        try:
            limpiar_archivos_temporales_antiguos()
        except Exception as e:
            logger.warning(f"Error al limpiar archivos temporales: {str(e)}")

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",  # Nombres en inglés forma parte de clasificaciones
            accion="upload_excel",
            descripcion=f"Subido archivo de nombres en inglés: {instance.archivo.name}",
            usuario=self.request.user,
            detalles={
                "nombre_archivo": instance.archivo.name,
                "tamaño_bytes": instance.archivo.size if instance.archivo else None,
                "upload_id": instance.id,
                "tipo_archivo": "nombres_ingles",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

        # Disparar tarea de procesamiento en background
        try:
            procesar_nombres_ingles_upload.delay(instance.id)
        except Exception as e:
            logger.error(f"Error al disparar tarea de procesamiento: {str(e)}")
            # Registrar error en el procesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="process_error",
                descripcion=f"Error al iniciar procesamiento de {instance.archivo.name}: {str(e)}",
                usuario=self.request.user,
                detalles={
                    "error": str(e),
                    "nombre_archivo": instance.archivo.name,
                    "upload_id": instance.id,
                    "tipo_archivo": "nombres_ingles",
                },
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

    def perform_update(self, serializer):
        instance = serializer.save()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="manual_edit",
            descripcion=f"Actualizado archivo de nombres en inglés: {instance.archivo.name}",
            usuario=self.request.user,
            detalles={
                "nombre_archivo": instance.archivo.name,
                "upload_id": instance.id,
                "tipo_archivo": "nombres_ingles",
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        archivo_info = {
            "nombre_archivo": instance.archivo.name,
            "upload_id": instance.id,
            "tipo_archivo": "nombres_ingles",
        }

        try:
            # Eliminar archivo físico si existe
            if instance.archivo and hasattr(instance.archivo, "path"):
                try:
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass

            instance.delete()

            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="manual_delete",
                descripcion=f'Eliminado archivo de nombres en inglés: {archivo_info["nombre_archivo"]}',
                usuario=self.request.user,
                detalles=archivo_info,
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error en eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="manual_delete",
                descripcion=f"Error al eliminar archivo de nombres en inglés: {str(e)}",
                usuario=self.request.user,
                detalles={"error": str(e), **archivo_info},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    @action(detail=True, methods=["post"])
    def reprocesar(self, request, pk=None):
        """Reprocesa un archivo de nombres en inglés."""
        upload = self.get_object()
        try:
            # Reiniciar estado y limpiar datos previos
            upload.estado = "subido"
            upload.errores = ""
            upload.resumen = {}
            upload.save(update_fields=["estado", "errores", "resumen"])

            # Disparar tarea de procesamiento en background
            procesar_nombres_ingles_upload.delay(upload.id)

            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="process_start",
                descripcion=f"Reprocesamiento iniciado para nombres en inglés: {upload.archivo.name}",
                usuario=request.user,
                detalles={
                    "nombre_archivo": upload.archivo.name,
                    "upload_id": upload.id,
                    "tipo_operacion": "reprocesamiento",
                    "tipo_archivo": "nombres_ingles",
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response({"mensaje": "Reprocesamiento iniciado"})

        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="process_start",
                descripcion=f"Error en reprocesamiento de nombres en inglés: {str(e)}",
                usuario=request.user,
                detalles={
                    "error": str(e),
                    "nombre_archivo": upload.archivo.name,
                    "upload_id": upload.id,
                },
                resultado="error",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            return Response({"error": str(e)}, status=500)


class LibroMayorUploadViewSet(viewsets.ModelViewSet):
    queryset = LibroMayorUpload.objects.all()
    serializer_class = LibroMayorUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cierre.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="libro_mayor",
            accion="upload_excel",
            descripcion=f"Subido archivo de libro mayor: {instance.archivo.name}",
            usuario=self.request.user,
            detalles={
                "nombre_archivo": instance.archivo.name,
                "cierre_id": instance.cierre.id,
                "upload_id": instance.id,
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_update(self, serializer):
        instance = serializer.save()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cierre.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="libro_mayor",
            accion="manual_edit",
            descripcion=f"Actualizado archivo de libro mayor: {instance.archivo.name}",
            usuario=self.request.user,
            detalles={
                "nombre_archivo": instance.archivo.name,
                "cierre_id": instance.cierre.id,
                "upload_id": instance.id,
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

    def perform_destroy(self, instance):
        cliente_id = instance.cierre.cliente.id
        archivo_info = {
            "nombre_archivo": instance.archivo.name,
            "cierre_id": instance.cierre.id,
            "upload_id": instance.id,
        }

        try:
            # Eliminar archivo físico si existe
            if instance.archivo and hasattr(instance.archivo, "path"):
                try:
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass

            instance.delete()

            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="libro_mayor",
                accion="manual_delete",
                descripcion=f'Eliminado archivo de libro mayor: {archivo_info["nombre_archivo"]}',
                usuario=self.request.user,
                detalles=archivo_info,
                resultado="exito",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )

        except Exception as e:
            # Registrar error en eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="libro_mayor",
                accion="manual_delete",
                descripcion=f"Error al eliminar archivo de libro mayor: {str(e)}",
                usuario=self.request.user,
                detalles={"error": str(e), **archivo_info},
                resultado="error",
                ip_address=self.request.META.get("REMOTE_ADDR"),
            )
            raise

    @action(detail=True, methods=["post"])
    def reprocesar(self, request, pk=None):
        try:
            instance = self.get_object()
            # Aquí iría la lógica de reprocesamiento

            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cierre.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="libro_mayor",
                accion="process_start",
                descripcion=f"Reprocesamiento iniciado para archivo: {instance.archivo.name}",
                usuario=request.user,
                detalles={
                    "nombre_archivo": instance.archivo.name,
                    "cierre_id": instance.cierre.id,
                    "upload_id": instance.id,
                    "tipo_operacion": "reprocesamiento",
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            return Response({"mensaje": "Reprocesamiento iniciado"})

        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cierre.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="libro_mayor",
                accion="process_start",
                descripcion=f"Error en reprocesamiento: {str(e)}",
                usuario=request.user,
                detalles={
                    "error": str(e),
                    "nombre_archivo": instance.archivo.name,
                    "cierre_id": instance.cierre.id,
                    "upload_id": instance.id,
                },
                resultado="error",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            return Response({"error": str(e)}, status=500)


class TarjetaActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar los logs de actividad de las tarjetas.
    Solo lectura - los logs se crean automáticamente a través del sistema.
    """

    queryset = TarjetaActivityLog.objects.all()
    serializer_class = TarjetaActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por cliente si se especifica
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cierre__cliente_id=cliente_id)

        # Filtrar por período si se especifica
        periodo = self.request.query_params.get("periodo")
        if periodo:
            queryset = queryset.filter(periodo=periodo)

        # Filtrar por tarjeta si se especifica
        tarjeta = self.request.query_params.get("tarjeta")
        if tarjeta:
            queryset = queryset.filter(tarjeta=tarjeta)

        # Filtrar por acción si se especifica
        accion = self.request.query_params.get("accion")
        if accion:
            queryset = queryset.filter(accion=accion)

        # Filtrar por resultado si se especifica
        resultado = self.request.query_params.get("resultado")
        if resultado:
            queryset = queryset.filter(resultado=resultado)

        # Ordenar por fecha descendente
        return queryset.select_related("cierre", "cierre__cliente", "usuario").order_by(
            "-timestamp"
        )


class CierreContabilidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los cierres contables.
    """

    queryset = CierreContabilidad.objects.all()
    serializer_class = CierreContabilidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get("cliente")
        periodo = self.request.query_params.get("periodo")

        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)

        return queryset.select_related("cliente", "usuario", "area").order_by(
            "-fecha_creacion"
        )

    def perform_create(self, serializer):
        """
        Establece el usuario actual al crear un nuevo cierre contable.
        """
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=["get"])
    def movimientos_resumen(self, request, pk=None):
        """
        Endpoint para obtener resumen de movimientos de un cierre específico
        """
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        # Aquí podrías agregar lógica específica para el resumen de movimientos
        return Response({"mensaje": "Resumen de movimientos", "cierre_id": pk})

    @action(detail=True, methods=["get"])
    def movimientos_cuenta(self, request, pk=None):
        """
        Endpoint para obtener movimientos de una cuenta específica en un cierre
        """
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)

        cuenta_id = request.query_params.get("cuenta_id")
        if not cuenta_id:
            return Response({"error": "cuenta_id es requerido"}, status=400)

        # Aquí podrías agregar lógica específica para movimientos de cuenta
        return Response(
            {
                "mensaje": "Movimientos de cuenta",
                "cierre_id": pk,
                "cuenta_id": cuenta_id,
            }
        )


# Función utilitaria para limpieza de archivos
def limpiar_archivos_temporales_antiguos():
    """
    Limpia archivos temporales de tipo_documento que tengan más de 24 horas
    """
    import time

    try:
        # Buscar archivos temporales
        patron = os.path.join(
            default_storage.location, "temp", "tipo_doc_cliente_*.xlsx"
        )
        archivos_temp = glob.glob(patron)

        archivos_eliminados = 0
        for archivo in archivos_temp:
            try:
                # Verificar si el archivo tiene más de 24 horas
                tiempo_archivo = os.path.getmtime(archivo)
                tiempo_actual = time.time()
                if (tiempo_actual - tiempo_archivo) > 86400:  # 24 horas en segundos
                    os.remove(archivo)
                    archivos_eliminados += 1
            except OSError:
                continue

        return archivos_eliminados
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {str(e)}")
        return 0


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def limpiar_archivos_temporales(request):
    """
    Endpoint para ejecutar limpieza manual de archivos temporales antiguos
    """
    archivos_eliminados = limpiar_archivos_temporales_antiguos()
    return Response(
        {
            "mensaje": f"Limpieza completada: {archivos_eliminados} archivos eliminados",
            "archivos_eliminados": archivos_eliminados,
        }
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def eliminar_todos_nombres_ingles_upload(request):
    """
    Elimina todos los uploads de nombres en inglés para un cliente y cierre específicos
    """
    cliente_id = request.query_params.get("cliente")
    cierre_id = request.query_params.get("cierre")

    if not cliente_id:
        return Response({"error": "ID de cliente requerido"}, status=400)

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Filtrar por cliente y opcionalmente por cierre
    uploads_query = NombresEnInglesUpload.objects.filter(cliente=cliente)
    if cierre_id:
        uploads_query = uploads_query.filter(cierre_id=cierre_id)

    uploads = uploads_query.all()
    count = uploads.count()
    archivos_eliminados = []

    try:
        # Eliminar archivos físicos y registros
        for upload in uploads:
            archivo_info = {
                "nombre_archivo": upload.archivo.name,
                "upload_id": upload.id,
            }

            # Eliminar archivo físico si existe
            if upload.archivo and hasattr(upload.archivo, "path"):
                try:
                    if os.path.exists(upload.archivo.path):
                        os.remove(upload.archivo.path)
                        archivos_eliminados.append(archivo_info["nombre_archivo"])
                except OSError:
                    pass

        # Eliminar todos los registros
        uploads.delete()

        # Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="bulk_delete",
            descripcion=f"Eliminados todos los archivos de nombres en inglés ({count} archivos)",
            usuario=request.user,
            detalles={
                "total_uploads_eliminados": count,
                "archivos_eliminados": archivos_eliminados,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_id,
                "tipo_archivo": "nombres_ingles",
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": "Archivos de nombres en inglés eliminados correctamente",
                "uploads_eliminados": count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="bulk_delete",
            descripcion=f"Error al eliminar archivos de nombres en inglés: {str(e)}",
            usuario=request.user,
            detalles={
                "error": str(e),
                "total_uploads_contados": count,
                "cliente_nombre": cliente.nombre,
                "cierre_id": cierre_id,
                "tipo_archivo": "nombres_ingles",
            },
            resultado="error",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)
