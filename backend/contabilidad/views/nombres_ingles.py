from rest_framework import viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes, action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status
from datetime import date
import openpyxl
import logging
import os
from django.core.files.storage import default_storage

from ..models import NombreIngles, CuentaContable, MovimientoContable, NombresEnInglesUpload, UploadLog, CierreContabilidad
from ..serializers import NombreInglesSerializer, NombresEnInglesUploadSerializer
from ..utils.activity_logger import registrar_actividad_tarjeta
from api.models import Cliente


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
    """
    Vista refactorizada para cargar nombres en inglés usando Celery Chains.
    
    Flujo simplificado:
    1. Validar entrada básica
    2. Crear UploadLog
    3. Guardar archivo temporal
    4. Disparar chain de procesamiento
    5. Retornar respuesta inmediata
    """
    import logging
    from django.core.files.storage import default_storage
    from api.models import Cliente
    from ..models import UploadLog, CierreContabilidad, NombreIngles
    from ..tasks_nombres_ingles import crear_chain_nombres_ingles
    from ..utils.activity_logger import registrar_actividad_tarjeta
    from datetime import date
    
    logger = logging.getLogger(__name__)
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
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
        )

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

    # Registrar actividad de upload exitoso
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
            "procesamiento": "chain_celery"
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    # Disparar chain de procesamiento
    try:
        chain_nombres_ingles = crear_chain_nombres_ingles(upload_log.id)
        chain_nombres_ingles.apply_async()
        logger.info(f"Chain de nombres en inglés iniciado para upload_log_id: {upload_log.id}")
        
        return Response({
            "mensaje": "Archivo recibido y procesamiento iniciado",
            "upload_log_id": upload_log.id,
            "estado": upload_log.estado,
            "tipo_procesamiento": "chain_celery"
        })
        
    except Exception as e:
        # Si falla el chain, marcar como error
        upload_log.estado = "error"
        upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
        upload_log.save()
        
        logger.error(f"Error iniciando chain de nombres en inglés: {str(e)}")
        return Response({
            "error": "Error iniciando procesamiento",
            "detalle": str(e),
            "upload_log_id": upload_log.id
        }, status=500)


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
        Recibe Excel y dispara el procesamiento usando Celery Chains.
        """
        from django.core.files.storage import default_storage
        from ..tasks_nombres_ingles import crear_chain_nombres_ingles
        from ..models import UploadLog, CierreContabilidad
        from datetime import date
        
        cliente_id = request.data.get("cliente_id")
        archivo = request.FILES.get("archivo")
        if not cliente_id or not archivo:
            return Response(
                {"error": "cliente_id y archivo son requeridos"}, status=400
            )

        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)

        # Buscar cierre relacionado
        cierre_relacionado = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()

        # Crear UploadLog para el nuevo flujo
        upload_log = UploadLog.objects.create(
            tipo_upload="nombres_ingles",
            cliente=cliente,
            cierre=cierre_relacionado,
            usuario=request.user,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
            estado="subido",
            ip_usuario=request.META.get("REMOTE_ADDR"),
        )

        # Guardar archivo temporal
        nombre_archivo = f"temp/nombres_ingles_cliente_{cliente_id}_{upload_log.id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)
        upload_log.ruta_archivo = ruta_guardada
        upload_log.save(update_fields=["ruta_archivo"])

        # Disparar chain de procesamiento
        try:
            chain_nombres_ingles = crear_chain_nombres_ingles(upload_log.id)
            chain_nombres_ingles.apply_async()
            
            return Response({
                "mensaje": "Archivo recibido y procesamiento iniciado con Celery Chains",
                "ok": True,
                "upload_log_id": upload_log.id,
                "tipo_procesamiento": "chain_celery"
            })
            
        except Exception as e:
            upload_log.estado = "error"
            upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
            upload_log.save()
            
            return Response({
                "error": "Error iniciando procesamiento",
                "detalle": str(e),
                "upload_log_id": upload_log.id
            }, status=500)

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
        """
        Crea una nueva instancia y dispara el procesamiento usando Celery Chains.
        """
        from ..tasks_nombres_ingles import crear_chain_nombres_ingles
        from ..models import UploadLog, CierreContabilidad
        from datetime import date
        
        instance = serializer.save()

        # Crear UploadLog para el nuevo flujo
        cierre_relacionado = CierreContabilidad.objects.filter(
            cliente=instance.cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()

        upload_log = UploadLog.objects.create(
            tipo_upload="nombres_ingles",
            cliente=instance.cliente,
            cierre=cierre_relacionado,
            usuario=self.request.user,
            nombre_archivo_original=instance.archivo.name,
            tamaño_archivo=instance.archivo.size,
            estado="subido",
            ip_usuario=self.request.META.get("REMOTE_ADDR"),
            ruta_archivo=instance.archivo.name,  # Usar el archivo guardado
        )

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=cierre_relacionado.periodo if cierre_relacionado else date.today().strftime("%Y-%m"),
            tarjeta="nombres_ingles",
            accion="upload_excel",
            descripcion=f"Subido archivo de nombres en inglés: {instance.archivo.name}",
            usuario=self.request.user,
            detalles={
                "nombre_archivo": instance.archivo.name,
                "tamaño_bytes": instance.archivo.size if instance.archivo else None,
                "upload_id": instance.id,
                "upload_log_id": upload_log.id,
                "tipo_archivo": "nombres_ingles",
                "procesamiento": "chain_celery"
            },
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )

        # Disparar tarea de procesamiento en background usando chains
        try:
            chain_nombres_ingles = crear_chain_nombres_ingles(upload_log.id)
            chain_nombres_ingles.apply_async()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al disparar chain de procesamiento: {str(e)}")
            
            # Marcar el upload_log como error
            upload_log.estado = "error"
            upload_log.errores = f"Error iniciando procesamiento: {str(e)}"
            upload_log.save()

    def perform_update(self, serializer):
        instance = serializer.save()

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=instance.cliente.id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="nombres_ingles",
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
                    import os
                    if os.path.exists(instance.archivo.path):
                        os.remove(instance.archivo.path)
                except OSError:
                    pass

            super().perform_destroy(instance)

            # Registrar eliminación exitosa
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
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
                tarjeta="nombres_ingles",
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
        """
        Reprocesa un archivo usando el nuevo sistema de Celery Chains.
        """
        from ..tasks_nombres_ingles import crear_chain_nombres_ingles
        from ..models import UploadLog, CierreContabilidad
        from datetime import date
        
        try:
            upload = self.get_object()

            # Crear un nuevo UploadLog para el reprocesamiento
            cierre_relacionado = CierreContabilidad.objects.filter(
                cliente=upload.cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()

            upload_log = UploadLog.objects.create(
                tipo_upload="nombres_ingles",
                cliente=upload.cliente,
                cierre=cierre_relacionado,
                usuario=request.user,
                nombre_archivo_original=upload.archivo.name,
                tamaño_archivo=upload.archivo.size,
                estado="subido",
                ip_usuario=request.META.get("REMOTE_ADDR"),
                ruta_archivo=upload.archivo.name,  # Usar el archivo ya existente
            )

            # Registrar reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=cierre_relacionado.periodo if cierre_relacionado else date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
                accion="process_start",
                descripcion=f"Reprocesamiento iniciado para nombres en inglés: {upload.archivo.name}",
                usuario=request.user,
                detalles={
                    "nombre_archivo": upload.archivo.name,
                    "upload_id": upload.id,
                    "upload_log_id": upload_log.id,
                    "tipo_operacion": "reprocesamiento",
                    "tipo_archivo": "nombres_ingles",
                    "procesamiento": "chain_celery"
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )

            # Disparar chain de procesamiento
            chain_nombres_ingles = crear_chain_nombres_ingles(upload_log.id)
            chain_nombres_ingles.apply_async()

            return Response({
                "message": "Archivo reprocesado exitosamente con Celery Chains",
                "upload_log_id": upload_log.id,
                "tipo_procesamiento": "chain_celery"
            })

        except Exception as e:
            # Registrar error en reprocesamiento
            registrar_actividad_tarjeta(
                cliente_id=upload.cliente.id,
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="nombres_ingles",
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
