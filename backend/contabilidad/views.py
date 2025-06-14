#backend/contabilidadfrom .utils.activity_logger import registrar_actividad_tarjetadad/views.py
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, parser_classes, action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import HttpResponse, FileResponse
import openpyxl
import io
import pandas as pd
from django.core.files.storage import default_storage
from datetime import date
import os
from django.db.models import Q, Sum
from contabilidad.permissions import PuedeCrearCierreContabilidad, SoloContabilidadAsignadoOGerente
from .utils.activity_logger import registrar_actividad_tarjeta  # Comentado temporalmente
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
    BulkClasificacionUpload,
    ClasificacionCuentaArchivo,
    NombresEnInglesUpload,
    TarjetaActivityLog,
    TipoDocumentoArchivo,
)
from .serializers import (
    TipoDocumentoSerializer,
    BulkClasificacionUploadSerializer,
    ClasificacionCuentaArchivoSerializer,
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
    NombresEnInglesUploadSerializer,
    TarjetaActivityLogSerializer,
)

from api.models import (
    Cliente,
)

from contabilidad.tasks import (
    tarea_de_prueba,
    parsear_tipo_documento,
    procesar_libro_mayor,
    procesar_nombres_ingles,
    procesar_bulk_clasificacion,
    procesar_nombres_ingles_upload,
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
            
            total_cuentas = cuentas.count()
            
            # Lógica corregida: si no hay cuentas en absoluto, el estado es pendiente
            if total_cuentas == 0:
                estado = "pendiente"  # No hay cuentas = aún no hay nada que traducir
            else:
                estado = "subido" if not faltantes.exists() else "pendiente"
            
            return Response({
                "estado": estado,
                "faltantes": data_faltantes,
                "total": total_cuentas
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

    # Verificar si ya existen datos para este cliente
    tipos_existentes = TipoDocumento.objects.filter(cliente=cliente).count()
    if tipos_existentes > 0:
        # Registrar intento de upload con datos existentes
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='tipo_documento',
            accion='upload_excel',
            descripcion=f'Upload rechazado: ya existen {tipos_existentes} tipos de documento',
            usuario=request.user,
            detalles={
                'nombre_archivo': archivo.name,
                'tipos_existentes': tipos_existentes,
                'razon_rechazo': 'datos_existentes'
            },
            resultado='error',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            "error": "Ya existen tipos de documento para este cliente",
            "mensaje": "Debe eliminar todos los registros existentes antes de subir un nuevo archivo",
            "tipos_existentes": tipos_existentes,
            "accion_requerida": "Usar 'Eliminar todos' primero"
        }, status=409)  # 409 Conflict

    # Limpiar archivos temporales anteriores del mismo cliente
    patron_temp = f"temp/tipo_doc_cliente_{cliente_id}*"
    import glob
    archivos_temp_anteriores = glob.glob(os.path.join(default_storage.location, "temp", f"tipo_doc_cliente_{cliente_id}*"))
    for archivo_anterior in archivos_temp_anteriores:
        try:
            os.remove(archivo_anterior)
        except OSError:
            pass  # Ignorar si no se puede eliminar

    # Guardar archivo temporalmente (media/temp/)
    nombre_archivo = f"temp/tipo_doc_cliente_{cliente_id}.xlsx"
    ruta_guardada = default_storage.save(nombre_archivo, archivo)

    # Registrar actividad de subida
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=date.today().strftime('%Y-%m'),  # Periodo actual por defecto
        tarjeta='tipo_documento',
        accion='upload_excel',
        descripcion=f'Subido archivo: {archivo.name}',
        usuario=request.user,
        detalles={
            'nombre_archivo': archivo.name,
            'tamaño_bytes': archivo.size,
            'tipo_contenido': archivo.content_type
        },
        resultado='exito',
        ip_address=request.META.get('REMOTE_ADDR')
    )

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
@permission_classes([IsAuthenticated])
def eliminar_tipos_documento(request, cliente_id):
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    # Contar registros antes de eliminar
    count = TipoDocumento.objects.filter(cliente=cliente).count()
    
    # Variables para el log
    archivos_eliminados = []
    
    try:
        # 1. Buscar y eliminar archivo asociado si existe
        try:
            archivo_tipo_doc = TipoDocumentoArchivo.objects.get(cliente=cliente)
            archivo_path = archivo_tipo_doc.archivo.path if archivo_tipo_doc.archivo else None
            archivo_name = archivo_tipo_doc.archivo.name if archivo_tipo_doc.archivo else None
            
            # Eliminar archivo físico del sistema
            if archivo_path and os.path.exists(archivo_path):
                os.remove(archivo_path)
                archivos_eliminados.append(archivo_name)
            
            # Eliminar registro del archivo
            archivo_tipo_doc.delete()
            
        except TipoDocumentoArchivo.DoesNotExist:
            # No hay archivo que eliminar, continuar normalmente
            pass
        
        # 2. Eliminar registros de TipoDocumento
        TipoDocumento.objects.filter(cliente=cliente).delete()
        
        # 3. Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='tipo_documento',
            accion='bulk_delete',
            descripcion=f'Eliminados todos los tipos de documento ({count} registros) y archivos asociados',
            usuario=request.user,
            detalles={
                'registros_eliminados': count,
                'archivos_eliminados': archivos_eliminados,
                'cliente_nombre': cliente.nombre
            },
            resultado='exito',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            "mensaje": "Tipos de documento y archivos eliminados correctamente",
            "registros_eliminados": count,
            "archivos_eliminados": len(archivos_eliminados)
        })
        
    except Exception as e:
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='tipo_documento',
            accion='bulk_delete',
            descripcion=f'Error al eliminar tipos de documento y archivos: {str(e)}',
            usuario=request.user,
            detalles={
                'error': str(e),
                'registros_contados': count,
                'cliente_nombre': cliente.nombre
            },
            resultado='error',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)


@api_view(['GET'])
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_vista_tipos_documento(request, cliente_id):
    """
    Endpoint específico para registrar cuando el usuario abre el modal de tipos de documento
    """
    tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)
    
    # Registrar visualización manual del modal
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=date.today().strftime('%Y-%m'),
        tarjeta='tipo_documento',
        accion='view_data',
        descripcion=f'Abrió modal de tipos de documento ({tipos.count()} registros)',
        usuario=request.user,
        detalles={
            'total_registros': tipos.count(),
            'accion_origen': 'modal_manual'
        },
        resultado='exito',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return Response({"mensaje": "Visualización registrada"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_vista_clasificaciones(request, cliente_id):
    """
    Endpoint específico para registrar cuando el usuario abre el modal de clasificaciones
    """
    # Obtener el upload ID del request
    upload_id = request.data.get('upload_id')
    
    try:
        # Contar registros del upload específico
        if upload_id:
            registros = ClasificacionCuentaArchivo.objects.filter(upload_id=upload_id)
            total_registros = registros.count()
            descripcion = f'Abrió modal de clasificaciones para upload {upload_id} ({total_registros} registros)'
            detalles = {
                'total_registros': total_registros,
                'upload_id': upload_id,
                'accion_origen': 'modal_manual'
            }
        else:
            # Si no hay upload_id, contar todos los registros del cliente
            registros = ClasificacionCuentaArchivo.objects.filter(cliente_id=cliente_id)
            total_registros = registros.count()
            descripcion = f'Abrió modal de clasificaciones del cliente ({total_registros} registros)'
            detalles = {
                'total_registros': total_registros,
                'accion_origen': 'modal_manual'
            }
    except Exception as e:
        total_registros = 0
        descripcion = f'Abrió modal de clasificaciones (error al contar registros: {str(e)})'
        detalles = {
            'error': str(e),
            'upload_id': upload_id,
            'accion_origen': 'modal_manual'
        }
    
    # Registrar visualización manual del modal
    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=date.today().strftime('%Y-%m'),
        tarjeta='clasificacion',
        accion='view_data',
        descripcion=descripcion,
        usuario=request.user,
        detalles=detalles,
        resultado='exito',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return Response({"mensaje": "Visualización registrada"})


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
        cliente_id = self.request.data.get('cliente')
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
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_create',
                descripcion=f'Creado tipo documento: {instance.codigo} - {instance.descripcion}',
                usuario=self.request.user,
                detalles={
                    'codigo': instance.codigo,
                    'descripcion': instance.descripcion,
                    'id': instance.id
                },
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Cliente.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cliente no encontrado")
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_create',
                descripcion=f'Error al crear tipo documento: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    'data': self.request.data
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

    def perform_update(self, serializer):
        old_instance = self.get_object()
        cliente_id = old_instance.cliente.id
        
        try:
            # No permitir cambiar el cliente en una actualización
            if 'cliente' in self.request.data:
                instance = serializer.save(cliente_id=cliente_id)
            else:
                instance = serializer.save()
            
            # Registrar edición
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_edit',
                descripcion=f'Editado tipo documento ID:{instance.id}: {old_instance.codigo} → {instance.codigo}',
                usuario=self.request.user,
                detalles={
                    'id': instance.id,
                    'cambios': {
                        'codigo': {'anterior': old_instance.codigo, 'nuevo': instance.codigo},
                        'descripcion': {'anterior': old_instance.descripcion, 'nuevo': instance.descripcion}
                    }
                },
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_edit',
                descripcion=f'Error al editar tipo documento ID:{old_instance.id}: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    'id': old_instance.id,
                    'data': self.request.data
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        tipo_info = {'id': instance.id, 'codigo': instance.codigo, 'descripcion': instance.descripcion}
        
        try:
            instance.delete()
            
            # Registrar eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_delete',
                descripcion=f'Eliminado tipo documento: {tipo_info["codigo"]} - {tipo_info["descripcion"]}',
                usuario=self.request.user,
                detalles=tipo_info,
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='tipo_documento',
                accion='manual_delete',
                descripcion=f'Error al eliminar tipo documento ID:{tipo_info["id"]}: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    **tipo_info
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise


class CuentaContableViewSet(viewsets.ModelViewSet):
    queryset = CuentaContable.objects.all()
    serializer_class = CuentaContableSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cliente
        cliente = self.request.query_params.get('cliente')
        if cliente:
            queryset = queryset.filter(cliente=cliente)
            
        return queryset.order_by('codigo')

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
        return queryset.order_by('nombre')
    
    def perform_create(self, serializer):
        instance = serializer.save()
        
        # Registrar creación de set
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='set_create',
            descripcion=f'Creado set de clasificación: {instance.nombre}',
            usuario=self.request.user,
            detalles={
                'set_id': instance.id,
                'set_nombre': instance.nombre,
                'accion_origen': 'manual_sets_tab'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()
        
        # Registrar edición de set
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='set_edit',
            descripcion=f'Editado set de clasificación: {old_instance.nombre} → {instance.nombre}',
            usuario=self.request.user,
            detalles={
                'set_id': instance.id,
                'nombre_anterior': old_instance.nombre,
                'nombre_nuevo': instance.nombre,
                'accion_origen': 'manual_sets_tab'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_destroy(self, instance):
        set_info = {'id': instance.id, 'nombre': instance.nombre, 'cliente_id': instance.cliente.id}
        
        try:
            # Contar opciones que se eliminarán
            opciones_count = ClasificacionOption.objects.filter(set_clas=instance).count()
            
            super().perform_destroy(instance)
            
            # Registrar eliminación de set
            registrar_actividad_tarjeta(
                cliente_id=set_info['cliente_id'],
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='set_delete',
                descripcion=f'Eliminado set de clasificación: {set_info["nombre"]} (incluía {opciones_count} opciones)',
                usuario=self.request.user,
                detalles={
                    **set_info,
                    'opciones_eliminadas': opciones_count,
                    'accion_origen': 'manual_sets_tab'
                },
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=set_info['cliente_id'],
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='set_delete',
                descripcion=f'Error al eliminar set de clasificación: {set_info["nombre"]} - {str(e)}',
                usuario=self.request.user,
                detalles={
                    **set_info,
                    'error': str(e),
                    'accion_origen': 'manual_sets_tab'
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
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
        return queryset.order_by('valor')
    
    def perform_create(self, serializer):
        instance = serializer.save()
        
        # Registrar creación de opción
        registrar_actividad_tarjeta(
            cliente_id=instance.set_clas.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='option_create',
            descripcion=f'Creada opción de clasificación: {instance.valor} en set {instance.set_clas.nombre}',
            usuario=self.request.user,
            detalles={
                'opcion_id': instance.id,
                'opcion_valor': instance.valor,
                'set_id': instance.set_clas.id,
                'set_nombre': instance.set_clas.nombre,
                'accion_origen': 'manual_sets_tab'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()
        
        # Registrar edición de opción
        registrar_actividad_tarjeta(
            cliente_id=instance.set_clas.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='option_edit',
            descripcion=f'Editada opción de clasificación: {old_instance.valor} → {instance.valor} en set {instance.set_clas.nombre}',
            usuario=self.request.user,
            detalles={
                'opcion_id': instance.id,
                'valor_anterior': old_instance.valor,
                'valor_nuevo': instance.valor,
                'set_id': instance.set_clas.id,
                'set_nombre': instance.set_clas.nombre,
                'accion_origen': 'manual_sets_tab'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_destroy(self, instance):
        opcion_info = {
            'id': instance.id, 
            'valor': instance.valor,
            'set_id': instance.set_clas.id,
            'set_nombre': instance.set_clas.nombre,
            'cliente_id': instance.set_clas.cliente.id
        }
        
        try:
            super().perform_destroy(instance)
            
            # Registrar eliminación de opción
            registrar_actividad_tarjeta(
                cliente_id=opcion_info['cliente_id'],
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='option_delete',
                descripcion=f'Eliminada opción de clasificación: {opcion_info["valor"]} del set {opcion_info["set_nombre"]}',
                usuario=self.request.user,
                detalles={
                    **opcion_info,
                    'accion_origen': 'manual_sets_tab'
                },
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error
            registrar_actividad_tarjeta(
                cliente_id=opcion_info['cliente_id'],
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='option_delete',
                descripcion=f'Error al eliminar opción de clasificación: {opcion_info["valor"]} - {str(e)}',
                usuario=self.request.user,
                detalles={
                    **opcion_info,
                    'error': str(e),
                    'accion_origen': 'manual_sets_tab'
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

class AccountClassificationViewSet(viewsets.ModelViewSet):
    queryset = AccountClassification.objects.select_related(
        'cuenta', 'set_clas', 'opcion', 'asignado_por'
    ).all()
    serializer_class = AccountClassificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cliente de la cuenta
        cuenta_cliente = self.request.query_params.get('cuenta__cliente')
        if cuenta_cliente:
            queryset = queryset.filter(cuenta__cliente=cuenta_cliente)
            
        return queryset.order_by('-fecha')
    
    def perform_create(self, serializer):
        # Asignar el usuario actual
        instance = serializer.save(asignado_por=self.request.user.usuario)
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cuenta.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='individual_create',
            descripcion=f'Creada clasificación: {instance.cuenta.codigo} → {instance.set_clas.nombre}: {instance.opcion.valor}',
            usuario=self.request.user,
            detalles={
                'cuenta_id': instance.cuenta.id,
                'cuenta_codigo': instance.cuenta.codigo,
                'set_nombre': instance.set_clas.nombre,
                'opcion_valor': instance.opcion.valor
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        instance = serializer.save()
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cuenta.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='individual_edit',
            descripcion=f'Editada clasificación: {instance.cuenta.codigo} → {instance.set_clas.nombre}: {instance.opcion.valor}',
            usuario=self.request.user,
            detalles={
                'cuenta_id': instance.cuenta.id,
                'cuenta_codigo': instance.cuenta.codigo,
                'cambios': {
                    'set_anterior': old_instance.set_clas.nombre,
                    'set_nuevo': instance.set_clas.nombre,
                    'opcion_anterior': old_instance.opcion.valor,
                    'opcion_nueva': instance.opcion.valor
                }
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_destroy(self, instance):
        # Guardar info antes de eliminar
        clasificacion_info = {
            'cuenta_codigo': instance.cuenta.codigo,
            'set_nombre': instance.set_clas.nombre,
            'opcion_valor': instance.opcion.valor
        }
        cliente_id = instance.cuenta.cliente.id
        
        # Eliminar
        instance.delete()
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='individual_delete',
            descripcion=f'Eliminada clasificación: {clasificacion_info["cuenta_codigo"]} → {clasificacion_info["set_nombre"]}: {clasificacion_info["opcion_valor"]}',
            usuario=self.request.user,
            detalles=clasificacion_info,
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
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
class BulkClasificacionUploadViewSet(viewsets.ModelViewSet):
    queryset = BulkClasificacionUpload.objects.all()
    serializer_class = BulkClasificacionUploadSerializer
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
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='upload_excel',
            descripcion=f'Subido archivo de clasificaciones: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'tamaño_bytes': instance.archivo.size if instance.archivo else None,
                'upload_id': instance.id
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        # Disparar tarea de procesamiento en background
        try:
            procesar_bulk_clasificacion.delay(instance.id)
        except Exception as e:
            logger.error(f"Error al disparar tarea de procesamiento: {str(e)}")
            # Registrar error en el procesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_error',
                descripcion=f'Error al iniciar procesamiento de {instance.archivo.name}: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    'nombre_archivo': instance.archivo.name,
                    'upload_id': instance.id
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )

    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='manual_edit',
            descripcion=f'Actualizado archivo de clasificaciones: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'upload_id': instance.id
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        archivo_info = {
            'nombre_archivo': instance.archivo.name,
            'upload_id': instance.id
        }
        
        try:
            # Eliminar archivo físico si existe
            if instance.archivo and hasattr(instance.archivo, 'path'):
                try:
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass
            
            instance.delete()
            
            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='manual_delete',
                descripcion=f'Eliminado archivo de clasificaciones: {archivo_info["nombre_archivo"]}',
                usuario=self.request.user,
                detalles=archivo_info,
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error en eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='manual_delete',
                descripcion=f'Error al eliminar archivo de clasificaciones: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    **archivo_info
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        try:
            upload = self.get_object()
            
            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_start',
                descripcion=f'Reprocesamiento iniciado para archivo: {upload.archivo.name}',
                usuario=request.user,
                detalles={
                    'nombre_archivo': upload.archivo.name,
                    'upload_id': upload.id,
                    'tipo_operacion': 'reprocesamiento'
                },
                resultado='exito',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({"message": "Archivo reprocesado exitosamente"})
            
        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_start',
                descripcion=f'Error en reprocesamiento: {str(e)}',
                usuario=request.user,
                detalles={
                    'error': str(e),
                    'nombre_archivo': upload.archivo.name,
                    'upload_id': upload.id
                },
                resultado='error',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({"error": str(e)}, status=500)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class ClasificacionCuentaArchivoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los registros raw de clasificaciones antes del mapeo
    """
    queryset = ClasificacionCuentaArchivo.objects.all()
    serializer_class = ClasificacionCuentaArchivoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        upload_id = self.request.query_params.get("upload")
        cliente_id = self.request.query_params.get("cliente")
        procesado = self.request.query_params.get("procesado")
        
        if upload_id:
            queryset = queryset.filter(upload_id=upload_id)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if procesado is not None:
            queryset = queryset.filter(procesado=procesado.lower() == 'true')
            
        return queryset.order_by('fila_excel')

    def perform_create(self, serializer):
        """Personalizar la creación de registros"""
        # Asignar el upload automáticamente si se proporciona en los datos
        upload_id = self.request.data.get('upload')
        if upload_id:
            try:
                upload = BulkClasificacionUpload.objects.get(id=upload_id)
                # Asignar cliente del upload
                instance = serializer.save(cliente=upload.cliente, upload=upload)
                
                # Registrar creación manual
                registrar_actividad_tarjeta(
                    cliente_id=upload.cliente.id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_create',
                    descripcion=f'Creado registro clasificación: {instance.numero_cuenta}',
                    usuario=self.request.user,
                    detalles={
                        'numero_cuenta': instance.numero_cuenta,
                        'clasificaciones': instance.clasificaciones,
                        'upload_id': upload_id,
                        'id': instance.id
                    },
                    resultado='exito',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
                
            except BulkClasificacionUpload.DoesNotExist:
                instance = serializer.save()
        else:
            instance = serializer.save()
            # Si no hay upload_id, registrar sin cliente específico
            if hasattr(instance, 'cliente') and instance.cliente:
                registrar_actividad_tarjeta(
                    cliente_id=instance.cliente.id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_create',
                    descripcion=f'Creado registro clasificación: {instance.numero_cuenta}',
                    usuario=self.request.user,
                    detalles={
                        'numero_cuenta': instance.numero_cuenta,
                        'clasificaciones': instance.clasificaciones,
                        'id': instance.id
                    },
                    resultado='exito',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )

    def perform_update(self, serializer):
        """Personalizar la actualización de registros"""
        old_instance = self.get_object()
        cliente_id = old_instance.cliente.id if old_instance.cliente else None
        
        try:
            # Si se actualiza un registro, mantener la fecha de procesado si ya estaba procesado
            if old_instance.procesado and serializer.validated_data.get('procesado', True):
                instance = serializer.save(fecha_procesado=old_instance.fecha_procesado)
            else:
                instance = serializer.save()
            
            # Registrar edición
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_edit',
                    descripcion=f'Editado registro clasificación ID:{instance.id}: {old_instance.numero_cuenta} → {instance.numero_cuenta}',
                    usuario=self.request.user,
                    detalles={
                        'id': instance.id,
                        'cambios': {
                            'numero_cuenta': {'anterior': old_instance.numero_cuenta, 'nuevo': instance.numero_cuenta},
                            'clasificaciones': {'anterior': old_instance.clasificaciones, 'nuevo': instance.clasificaciones}
                        },
                        'upload_id': instance.upload.id if instance.upload else None
                    },
                    resultado='exito',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
                
        except Exception as e:
            # Registrar error
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_edit',
                    descripcion=f'Error al editar registro clasificación ID:{old_instance.id}: {str(e)}',
                    usuario=self.request.user,
                    detalles={
                        'error': str(e),
                        'id': old_instance.id,
                        'data': self.request.data
                    },
                    resultado='error',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
            raise

    def perform_destroy(self, instance):
        """Logging al eliminar registros"""
        cliente_id = instance.cliente.id if instance.cliente else None
        registro_info = {
            'id': instance.id, 
            'numero_cuenta': instance.numero_cuenta, 
            'clasificaciones': instance.clasificaciones,
            'upload_id': instance.upload.id if instance.upload else None
        }
        
        try:
            logger.info(f"Eliminando registro de clasificación: {instance.numero_cuenta} del cliente {instance.cliente.nombre}")
            super().perform_destroy(instance)
            
            # Registrar eliminación
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_delete',
                    descripcion=f'Eliminado registro clasificación: {registro_info["numero_cuenta"]}',
                    usuario=self.request.user,
                    detalles=registro_info,
                    resultado='exito',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
                
        except Exception as e:
            # Registrar error
            if cliente_id:
                registrar_actividad_tarjeta(
                    cliente_id=cliente_id,
                    periodo=date.today().strftime('%Y-%m'),
                    tarjeta='clasificacion',
                    accion='manual_delete',
                    descripcion=f'Error al eliminar registro clasificación ID:{registro_info["id"]}: {str(e)}',
                    usuario=self.request.user,
                    detalles={
                        'error': str(e),
                        **registro_info
                    },
                    resultado='error',
                    ip_address=self.request.META.get('REMOTE_ADDR')
                )
            raise

    @action(detail=False, methods=['post'])
    def procesar_mapeo(self, request):
        """
        Dispara el procesamiento de mapeo para un upload específico
        """
        upload_id = request.data.get('upload_id')
        
        if not upload_id:
            return Response({"error": "upload_id requerido"}, status=400)
        
        try:
            upload = BulkClasificacionUpload.objects.get(id=upload_id)
        except BulkClasificacionUpload.DoesNotExist:
            return Response({"error": "Upload no encontrado"}, status=404)
        
        # Verificar que haya registros para procesar
        registros_pendientes = ClasificacionCuentaArchivo.objects.filter(
            upload=upload, 
            procesado=False
        ).count()
        
        if registros_pendientes == 0:
            return Response({"error": "No hay registros pendientes para procesar"}, status=400)
        
        # Disparar tarea de mapeo
        from .tasks import procesar_mapeo_clasificaciones
        procesar_mapeo_clasificaciones.delay(upload_id)
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=upload.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='process_start',
            descripcion=f'Iniciado mapeo de clasificaciones para archivo: {upload.archivo.name}',
            usuario=request.user,
            detalles={
                'upload_id': upload_id,
                'registros_pendientes': registros_pendientes,
                'tipo_operacion': 'mapeo'
            },
            resultado='exito',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            "mensaje": "Procesamiento de mapeo iniciado",
            "registros_pendientes": registros_pendientes
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de registros por upload
        """
        upload_id = request.query_params.get('upload_id')
        
        if not upload_id:
            return Response({"error": "upload_id requerido"}, status=400)
        
        try:
            upload = BulkClasificacionUpload.objects.get(id=upload_id)
        except BulkClasificacionUpload.DoesNotExist:
            return Response({"error": "Upload no encontrado"}, status=404)
        
        registros = ClasificacionCuentaArchivo.objects.filter(upload=upload)
        total = registros.count()
        procesados = registros.filter(procesado=True).count()
        con_errores = registros.exclude(errores_mapeo='').count()
        pendientes = total - procesados
        
        return Response({
            "total": total,
            "procesados": procesados,
            "pendientes": pendientes,
            "con_errores": con_errores,
            "upload_id": upload_id
        })


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
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',  # Nombres en inglés forma parte de clasificaciones
            accion='upload_excel',
            descripcion=f'Subido archivo de nombres en inglés: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'tamaño_bytes': instance.archivo.size if instance.archivo else None,
                'upload_id': instance.id,
                'tipo_archivo': 'nombres_ingles'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        # Disparar tarea de procesamiento en background
        try:
            procesar_nombres_ingles_upload.delay(instance.id)
        except Exception as e:
            logger.error(f"Error al disparar tarea de procesamiento: {str(e)}")
            # Registrar error en el procesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_error',
                descripcion=f'Error al iniciar procesamiento de {instance.archivo.name}: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    'nombre_archivo': instance.archivo.name,
                    'upload_id': instance.id,
                    'tipo_archivo': 'nombres_ingles'
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )

    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='manual_edit',
            descripcion=f'Actualizado archivo de nombres en inglés: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'upload_id': instance.id,
                'tipo_archivo': 'nombres_ingles'
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_destroy(self, instance):
        cliente_id = instance.cliente.id
        archivo_info = {
            'nombre_archivo': instance.archivo.name,
            'upload_id': instance.id,
            'tipo_archivo': 'nombres_ingles'
        }
        
        try:
            # Eliminar archivo físico si existe
            if instance.archivo and hasattr(instance.archivo, 'path'):
                try:
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass
            
            instance.delete()
            
            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='manual_delete',
                descripcion=f'Eliminado archivo de nombres en inglés: {archivo_info["nombre_archivo"]}',
                usuario=self.request.user,
                detalles=archivo_info,
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error en eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='manual_delete',
                descripcion=f'Error al eliminar archivo de nombres en inglés: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    **archivo_info
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        try:
            upload = self.get_object()
            
            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_start',
                descripcion=f'Reprocesamiento iniciado para nombres en inglés: {upload.archivo.name}',
                usuario=request.user,
                detalles={
                    'nombre_archivo': upload.archivo.name,
                    'upload_id': upload.id,
                    'tipo_operacion': 'reprocesamiento',
                    'tipo_archivo': 'nombres_ingles'
                },
                resultado='exito',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({"message": "Archivo reprocesado exitosamente"})
            
        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='clasificacion',
                accion='process_start',
                descripcion=f'Error en reprocesamiento de nombres en inglés: {str(e)}',
                usuario=request.user,
                detalles={
                    'error': str(e),
                    'nombre_archivo': upload.archivo.name,
                    'upload_id': upload.id
                },
                resultado='error',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        upload = self.get_object()
        try:
            # Aquí iría la lógica de reprocesamiento
            # Por ahora solo registramos el log
            UploadChangeLog.objects.create(
                tipo_upload="nombres_ingles",
                upload_id=upload.id,
                accion="reprocess",
                usuario=request.user,
                cliente=upload.cliente,
                descripcion="Archivo reprocesado"
            )
            return Response({"message": "Archivo reprocesado exitosamente"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


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
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='libro_mayor',
            accion='upload_excel',
            descripcion=f'Subido archivo de libro mayor: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'cierre_id': instance.cierre.id,
                'upload_id': instance.id
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cierre.cliente.id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='libro_mayor',
            accion='manual_edit',
            descripcion=f'Actualizado archivo de libro mayor: {instance.archivo.name}',
            usuario=self.request.user,
            detalles={
                'nombre_archivo': instance.archivo.name,
                'cierre_id': instance.cierre.id,
                'upload_id': instance.id
            },
            resultado='exito',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_destroy(self, instance):
        cliente_id = instance.cierre.cliente.id
        archivo_info = {
            'nombre_archivo': instance.archivo.name,
            'cierre_id': instance.cierre.id,
            'upload_id': instance.id
        }
        
        try:
            # Eliminar archivo físico si existe
            if instance.archivo and hasattr(instance.archivo, 'path'):
                try:
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass
            
            instance.delete()
            
            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='libro_mayor',
                accion='manual_delete',
                descripcion=f'Eliminado archivo de libro mayor: {archivo_info["nombre_archivo"]}',
                usuario=self.request.user,
                detalles=archivo_info,
                resultado='exito',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            
        except Exception as e:
            # Registrar error en eliminación
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='libro_mayor',
                accion='manual_delete',
                descripcion=f'Error al eliminar archivo de libro mayor: {str(e)}',
                usuario=self.request.user,
                detalles={
                    'error': str(e),
                    **archivo_info
                },
                resultado='error',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            raise

    @action(detail=True, methods=['post'])
    def reprocesar(self, request, pk=None):
        try:
            instance = self.get_object()
            # Aquí iría la lógica de reprocesamiento
            
            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cierre.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='libro_mayor',
                accion='process_start',
                descripcion=f'Reprocesamiento iniciado para archivo: {instance.archivo.name}',
                usuario=request.user,
                detalles={
                    'nombre_archivo': instance.archivo.name,
                    'cierre_id': instance.cierre.id,
                    'upload_id': instance.id,
                    'tipo_operacion': 'reprocesamiento'
                },
                resultado='exito',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({"mensaje": "Reprocesamiento iniciado"})
            
        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=instance.cierre.cliente.id,
                periodo=date.today().strftime('%Y-%m'),
                tarjeta='libro_mayor',
                accion='process_start',
                descripcion=f'Error en reprocesamiento: {str(e)}',
                usuario=request.user,
                detalles={
                    'error': str(e),
                    'nombre_archivo': instance.archivo.name,
                    'cierre_id': instance.cierre.id,
                    'upload_id': instance.id
                },
                resultado='error',
                ip_address=request.META.get('REMOTE_ADDR')
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
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cierre__cliente_id=cliente_id)
        
        # Filtrar por período si se especifica
        periodo = self.request.query_params.get('periodo')
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        
        # Filtrar por tarjeta si se especifica
        tarjeta = self.request.query_params.get('tarjeta')
        if tarjeta:
            queryset = queryset.filter(tarjeta=tarjeta)
        
        # Filtrar por acción si se especifica
        accion = self.request.query_params.get('accion')
        if accion:
            queryset = queryset.filter(accion=accion)
        
        # Filtrar por resultado si se especifica
        resultado = self.request.query_params.get('resultado')
        if resultado:
            queryset = queryset.filter(resultado=resultado)
        
        # Ordenar por fecha descendente
        return queryset.select_related('cierre', 'cierre__cliente', 'usuario').order_by('-timestamp')


class CierreContabilidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los cierres contables.
    """
    queryset = CierreContabilidad.objects.all()
    serializer_class = CierreContabilidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.select_related('cliente', 'usuario', 'area').order_by('-fecha_creacion')

    @action(detail=True, methods=['get'])
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

    @action(detail=True, methods=['get'])
    def movimientos_cuenta(self, request, pk=None):
        """
        Endpoint para obtener movimientos de una cuenta específica en un cierre
        """
        try:
            cierre = CierreContabilidad.objects.get(id=pk)
        except CierreContabilidad.DoesNotExist:
            return Response({"error": "Cierre no encontrado"}, status=404)
        
        cuenta_id = request.query_params.get('cuenta_id')
        if not cuenta_id:
            return Response({"error": "cuenta_id es requerido"}, status=400)
        
        # Aquí podrías agregar lógica específica para movimientos de cuenta
        return Response({
            "mensaje": "Movimientos de cuenta", 
            "cierre_id": pk, 
            "cuenta_id": cuenta_id
        })


# Función utilitaria para limpieza de archivos
def limpiar_archivos_temporales_antiguos():
    """
    Limpia archivos temporales de tipo_documento que tengan más de 24 horas
    """
    import glob
    import time
    
    try:
        # Buscar archivos temporales
        patron = os.path.join(default_storage.location, "temp", "tipo_doc_cliente_*.xlsx")
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def limpiar_archivos_temporales(request):
    """
    Endpoint para ejecutar limpieza manual de archivos temporales antiguos
    """
    archivos_eliminados = limpiar_archivos_temporales_antiguos()
    return Response({
        "mensaje": f"Limpieza completada: {archivos_eliminados} archivos eliminados",
        "archivos_eliminados": archivos_eliminados
    })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_todos_bulk_clasificacion(request):
    """
    Elimina todos los uploads de clasificación bulk para un cliente
    """
    cliente_id = request.query_params.get('cliente')
    if not cliente_id:
        return Response({"error": "ID de cliente requerido"}, status=400)
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)
    
    # Obtener todos los uploads del cliente
    uploads = BulkClasificacionUpload.objects.filter(cliente=cliente)
    count = uploads.count()
    archivos_eliminados = []
    
    try:
        # Eliminar archivos físicos y registros
        for upload in uploads:
            archivo_info = {
                'nombre_archivo': upload.archivo.name,
                'upload_id': upload.id
            }
            
            # Eliminar archivo físico si existe
            if upload.archivo and hasattr(upload.archivo, 'path'):
                try:
                    if os.path.exists(upload.archivo.path):
                        os.remove(upload.archivo.path)
                        archivos_eliminados.append(archivo_info['nombre_archivo'])
                except OSError:
                    pass
        
        # Eliminar todos los registros
        uploads.delete()
        
        # Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='bulk_delete',
            descripcion=f'Eliminados todos los archivos de clasificación bulk ({count} archivos)',
            usuario=request.user,
            detalles={
                'total_uploads_eliminados': count,
                'archivos_eliminados': archivos_eliminados,
                'cliente_nombre': cliente.nombre
            },
            resultado='exito',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            "mensaje": "Archivos de clasificación eliminados correctamente",
            "uploads_eliminados": count,
            "archivos_eliminados": len(archivos_eliminados)
        })
        
    except Exception as e:
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='bulk_delete',
            descripcion=f'Error al eliminar archivos de clasificación bulk: {str(e)}',
            usuario=request.user,
            detalles={
                'error': str(e),
                'total_uploads_contados': count,
                'cliente_nombre': cliente.nombre
            },
            resultado='error',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_todos_nombres_ingles_upload(request):
    """
    Elimina todos los uploads de nombres en inglés para un cliente y cierre específicos
    """
    cliente_id = request.query_params.get('cliente')
    cierre_id = request.query_params.get('cierre')
    
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
                'nombre_archivo': upload.archivo.name,
                'upload_id': upload.id
            }
            
            # Eliminar archivo físico si existe
            if upload.archivo and hasattr(upload.archivo, 'path'):
                try:
                    if os.path.exists(upload.archivo.path):
                        os.remove(upload.archivo.path)
                        archivos_eliminados.append(archivo_info['nombre_archivo'])
                except OSError:
                    pass
        
        # Eliminar todos los registros
        uploads.delete()
        
        # Registrar actividad exitosa
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='bulk_delete',
            descripcion=f'Eliminados todos los archivos de nombres en inglés ({count} archivos)',
            usuario=request.user,
            detalles={
                'total_uploads_eliminados': count,
                'archivos_eliminados': archivos_eliminados,
                'cliente_nombre': cliente.nombre,
                'cierre_id': cierre_id,
                'tipo_archivo': 'nombres_ingles'
            },
            resultado='exito',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            "mensaje": "Archivos de nombres en inglés eliminados correctamente",
            "uploads_eliminados": count,
            "archivos_eliminados": len(archivos_eliminados)
        })
        
    except Exception as e:
        # Registrar error
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime('%Y-%m'),
            tarjeta='clasificacion',
            accion='bulk_delete',
            descripcion=f'Error al eliminar archivos de nombres en inglés: {str(e)}',
            usuario=request.user,
            detalles={
                'error': str(e),
                'total_uploads_contados': count,
                'cliente_nombre': cliente.nombre,
                'cierre_id': cierre_id,
                'tipo_archivo': 'nombres_ingles'
            },
            resultado='error',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return Response({"error": f"Error al eliminar: {str(e)}"}, status=500)
