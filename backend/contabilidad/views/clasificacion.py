from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date
import glob
import logging
import os
from django.core.files.storage import default_storage
from django.db.models import Q

from api.models import Cliente
from ..models import (
    # ClasificacionCuentaArchivo,  # OBSOLETO - ELIMINADO EN REDISEÑO
    CuentaContable,
    CierreContabilidad,
    ClasificacionSet,
    AccountClassification,
    ClasificacionOption,
    UploadLog,
)
from ..serializers import (
    # ClasificacionCuentaArchivoSerializer,  # OBSOLETO - ELIMINADO
    ClasificacionSetSerializer,
    ClasificacionOptionSerializer,
    AccountClassificationSerializer,
)
from ..tasks_cuentas_bulk import iniciar_procesamiento_clasificacion_chain
from ..utils.activity_logger import registrar_actividad_tarjeta

# ============================================================
# VIEWSET OBSOLETO - ELIMINADO EN REDISEÑO DE CLASIFICACIONES
# ============================================================
# 
# class ClasificacionCuentaArchivoViewSet(viewsets.ModelViewSet):
#     """
#     OBSOLETO: Este ViewSet manejaba el modelo intermedio ClasificacionCuentaArchivo
#     que fue eliminado en el rediseño. Ahora se usa directamente AccountClassification.
#     """
#     serializer_class = ClasificacionCuentaArchivoSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         """
#         Filtra las clasificaciones RAW activas por cliente.
#         Solo muestra los registros activos (no obsoletos).
#         """
#         queryset = ClasificacionCuentaArchivo.objects.filter(activo=True)
#         
#         # Filtrar por cliente si se proporciona
#         cliente_id = self.request.query_params.get('cliente', None)
#         if cliente_id:
#             queryset = queryset.filter(cliente_id=cliente_id)
#         
#         # Mantener compatibilidad con filtro por upload_log si es necesario
#         upload_log_id = self.request.query_params.get('upload_log', None)
#         if upload_log_id:
#             queryset = queryset.filter(upload_log_id=upload_log_id)
#             
#         return queryset.select_related('cliente', 'upload_log').order_by('-fecha_creacion')


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def cargar_clasificacion_bulk(request):
    """
    Vista refactorizada para usar Celery Chains - Solo crea UploadLog y dispara chain
    """
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
    cierre_id = request.data.get("cierre_id")

    if not cliente_id or not archivo:
        return Response({"error": "cliente_id y archivo son requeridos"}, status=400)

    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    try:
        # BUSCAR EL CIERRE ASOCIADO
        cierre_relacionado = None
        
        if cierre_id:
            try:
                cierre_relacionado = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                logger.info(f"✅ Cierre encontrado usando cierre_id del frontend: {cierre_relacionado.id} - {cierre_relacionado.periodo}")
            except CierreContabilidad.DoesNotExist:
                logger.warning(f"❌ Cierre con id {cierre_id} no encontrado, buscando automáticamente")
                pass
        else:
            logger.info("🔎 No se envió cierre_id desde frontend, buscando automáticamente")
        
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

        # Crear UploadLog
        upload_log = UploadLog.objects.create(
            tipo_upload="clasificacion",
            cliente=cliente,
            cierre=cierre_relacionado,
            usuario=request.user,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
            estado="subido",
            ip_usuario=get_client_ip(request),
        )

        # Limpiar archivos temporales anteriores
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

        # Guardar archivo temporal
        nombre_archivo = f"temp/clasificacion_cliente_{cliente_id}_{upload_log.id}.xlsx"
        ruta_guardada = default_storage.save(nombre_archivo, archivo)

        upload_log.ruta_archivo = ruta_guardada
        upload_log.save()

        # Registrar actividad de subida
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

        # Disparar chain de procesamiento (delegando toda la lógica a las tasks)
        logger.info(f"🚀 Iniciando chain de clasificación para upload_log {upload_log.id}")
        iniciar_procesamiento_clasificacion_chain.delay(upload_log.id)

        return Response(
            {
                "mensaje": "Archivo recibido y procesamiento iniciado",
                "upload_log_id": upload_log.id,
                "estado": upload_log.estado,
            }
        )

    except Exception as e:
        logger.exception("Error al crear UploadLog para clasificacion: %s", e)
        
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


def verificar_y_marcar_completo(cuenta_id):
    """
    Helper function para verificar si todas las cuentas están clasificadas
    y marcar el cierre como completo
    """
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
        import logging

        logger = logging.getLogger(__name__)
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

    @action(detail=False, methods=["post"], url_path="clasificar-masivo")
    def clasificar_masivo(self, request):
        """
        Clasifica múltiples cuentas con la misma clasificación de una vez.
        
        Payload esperado:
        {
            "cuentas_ids": [1, 2, 3, 4],
            "set_clas_id": 5,
            "opcion_id": 10
        }
        """
        cuentas_ids = request.data.get("cuentas_ids", [])
        set_clas_id = request.data.get("set_clas_id")
        opcion_id = request.data.get("opcion_id")
        usuario = request.user
        
        # Validaciones
        if not cuentas_ids:
            return Response({"error": "Debe seleccionar al menos una cuenta"}, status=400)
            
        if not isinstance(cuentas_ids, list):
            return Response({"error": "cuentas_ids debe ser una lista"}, status=400)
            
        if not (set_clas_id and opcion_id):
            return Response({"error": "Debe especificar set_clas_id y opcion_id"}, status=400)
        
        # Verificar que el set y la opción existen
        try:
            set_clas = ClasificacionSet.objects.get(id=set_clas_id)
            opcion = ClasificacionOption.objects.get(id=opcion_id, set_clas_id=set_clas_id)
        except (ClasificacionSet.DoesNotExist, ClasificacionOption.DoesNotExist):
            return Response({"error": "Set o opción de clasificación no válidos"}, status=400)
        
        # Verificar que las cuentas existen y pertenecen al cliente autorizado
        cuentas = CuentaContable.objects.filter(id__in=cuentas_ids)
        
        if cuentas.count() != len(cuentas_ids):
            return Response({"error": "Algunas cuentas no fueron encontradas"}, status=400)
        
        # Verificar permisos: todas las cuentas deben pertenecer al mismo cliente
        cliente_ids = cuentas.values_list('cliente_id', flat=True).distinct()
        if len(cliente_ids) > 1:
            return Response({"error": "Las cuentas seleccionadas pertenecen a diferentes clientes"}, status=400)
        
        # Realizar clasificación masiva
        clasificaciones_creadas = 0
        clasificaciones_actualizadas = 0
        errores = []
        
        for cuenta in cuentas:
            try:
                obj, creado = AccountClassification.objects.update_or_create(
                    cuenta_id=cuenta.id,
                    set_clas_id=set_clas_id,
                    defaults={
                        "opcion_id": opcion_id,
                        "asignado_por": usuario,
                    },
                )
                
                if creado:
                    clasificaciones_creadas += 1
                else:
                    clasificaciones_actualizadas += 1
                    
                # Verificar y marcar cuenta como completa si es necesario
                verificar_y_marcar_completo(cuenta.id)
                
            except Exception as e:
                errores.append(f"Error en cuenta {cuenta.codigo}: {str(e)}")
        
        # Registrar actividad
        try:
            registrar_actividad_tarjeta(
                cliente_id=cliente_ids[0],
                periodo=date.today().strftime("%Y-%m"),
                tarjeta="clasificacion",
                accion="clasificar_masivo",
                descripcion=f"Clasificación masiva: {clasificaciones_creadas + clasificaciones_actualizadas} cuentas en set '{set_clas.nombre}' con opción '{opcion.valor}'",
                usuario=usuario,
                detalles={
                    "cuentas_procesadas": len(cuentas_ids),
                    "clasificaciones_creadas": clasificaciones_creadas,
                    "clasificaciones_actualizadas": clasificaciones_actualizadas,
                    "errores_count": len(errores),
                    "set_nombre": set_clas.nombre,
                    "opcion_valor": opcion.valor,
                },
                resultado="exito" if not errores else "parcial",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            # No fallar la operación principal por error de logging
            logging.getLogger(__name__).warning(f"Error registrando actividad de clasificación masiva: {e}")
        
        # Respuesta
        response_data = {
            "ok": True,
            "clasificaciones_creadas": clasificaciones_creadas,
            "clasificaciones_actualizadas": clasificaciones_actualizadas,
            "total_procesadas": clasificaciones_creadas + clasificaciones_actualizadas,
            "cuentas_solicitadas": len(cuentas_ids),
        }
        
        if errores:
            response_data["errores"] = errores
            response_data["errores_count"] = len(errores)
        
        return Response(response_data)


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

    def create(self, request, *args, **kwargs):
        """
        Crear una nueva opción con logging detallado para debugging bilingüe.
        UPDATED: Forzar recarga del viewset
        """
        print(f"🚀 ClasificacionOptionViewSet.create() - REQUEST DATA:")
        print(f"   📤 request.data: {request.data}")
        print(f"   🔍 Campos bilingües en request:")
        print(f"      valor: '{request.data.get('valor', 'NO_PRESENTE')}'")
        print(f"      valor_en: '{request.data.get('valor_en', 'NO_PRESENTE')}'")
        print(f"      descripcion: '{request.data.get('descripcion', 'NO_PRESENTE')}'")
        print(f"      descripcion_en: '{request.data.get('descripcion_en', 'NO_PRESENTE')}'")
        print(f"      set_clas: '{request.data.get('set_clas', 'NO_PRESENTE')}'")
        
        # Llamar al método create del padre
        response = super().create(request, *args, **kwargs)
        
        print(f"   ✅ RESPONSE DATA:")
        print(f"      status: {response.status_code}")
        print(f"      data: {response.data}")
        
        # Verificar qué se guardó realmente en la base de datos
        if response.status_code == 201 and 'id' in response.data:
            try:
                created_instance = ClasificacionOption.objects.get(id=response.data['id'])
                print(f"   🔍 VERIFICACIÓN EN DB - Instancia ID {created_instance.id}:")
                print(f"      valor (ES): '{created_instance.valor}'")
                print(f"      valor_en (EN): '{created_instance.valor_en}'")
                print(f"      descripcion (ES): '{created_instance.descripcion}'")
                print(f"      descripcion_en (EN): '{created_instance.descripcion_en}'")
                
                # Verificar si los campos bilingües se guardaron correctamente
                valor_en_guardado = created_instance.valor_en is not None and created_instance.valor_en.strip()
                if request.data.get('valor_en') and not valor_en_guardado:
                    print(f"   ❌ PROBLEMA: Se envió valor_en pero no se guardó!")
                    print(f"      Enviado: '{request.data.get('valor_en')}'")
                    print(f"      Guardado: '{created_instance.valor_en}'")
                elif request.data.get('valor_en') and valor_en_guardado:
                    print(f"   ✅ valor_en se guardó correctamente")
                    
            except Exception as e:
                print(f"   ❌ Error verificando instancia creada: {e}")
        
        return response

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
                "opcion_valor_en": instance.valor_en,  # Agregar campo en inglés
                "set_id": instance.set_clas.id,
                "set_nombre": instance.set_clas.nombre,
                "accion_origen": "manual_sets_tab",
                "es_bilingue": bool(instance.valor_en and instance.valor_en.strip()),
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
        # Asignar el usuario actual y asegurar que se establezca el cliente
        instance = serializer.save(
            asignado_por=self.request.user.usuario,
            cliente=serializer.validated_data.get('cuenta').cliente if serializer.validated_data.get('cuenta') else None
        )

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

        super().perform_destroy(instance)

        # Registrar eliminación
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=date.today().strftime("%Y-%m"),
            tarjeta="clasificacion",
            accion="individual_delete",
            descripcion=f"Eliminada clasificación: {clasificacion_info['cuenta_codigo']} → {clasificacion_info['set_nombre']}: {clasificacion_info['opcion_valor']}",
            usuario=self.request.user,
            detalles=clasificacion_info,
            resultado="exito",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )


# ==================== VISTAS PARA CLASIFICACIONES PERSISTENTES ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_clasificaciones_persistentes_detalladas(request, cliente_id):
    """
    Obtiene las clasificaciones persistentes con detalles completos para el modal de gestión.
    Incluye tanto clasificaciones con FK a cuenta como clasificaciones temporales.
    MEJORADO: También incluye cuentas sin clasificaciones.
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Obtener TODAS las clasificaciones del cliente (con FK y temporales)
    clasificaciones = AccountClassification.objects.filter(
        cliente=cliente
    ).select_related(
        'cuenta', 'set_clas', 'opcion'
    ).order_by('cuenta_codigo')  # Ordenar por código de cuenta
    
    # Crear diccionario para agrupar clasificaciones por cuenta
    clasificaciones_por_cuenta = {}
    
    # Procesar clasificaciones existentes
    for clasificacion in clasificaciones:
        # Manejar tanto clasificaciones con FK como temporales
        if clasificacion.cuenta:
            # Clasificación con FK a cuenta existente
            codigo_cuenta = clasificacion.cuenta.codigo
            
            if codigo_cuenta not in clasificaciones_por_cuenta:
                clasificaciones_por_cuenta[codigo_cuenta] = {
                    'cuenta_id': clasificacion.cuenta.id,
                    'cuenta_codigo': clasificacion.cuenta.codigo,
                    'cuenta_nombre': clasificacion.cuenta.nombre,
                    'cuenta_nombre_en': clasificacion.cuenta.nombre_en,
                    'es_temporal': False,
                    'clasificaciones': []
                }
            
            clasificaciones_por_cuenta[codigo_cuenta]['clasificaciones'].append({
                'id': clasificacion.id,
                'set_clas_id': clasificacion.set_clas.id,
                'set_nombre': clasificacion.set_clas.nombre,
                'opcion_id': clasificacion.opcion.id,
                'opcion_valor': clasificacion.opcion.valor,
                'opcion_valor_en': clasificacion.opcion.valor_en,
                'fecha_creacion': clasificacion.fecha_creacion,
                'fecha_actualizacion': clasificacion.fecha_actualizacion,
                'origen': clasificacion.origen,
            })
        else:
            # Clasificación temporal (sin FK a cuenta)
            codigo_cuenta = clasificacion.cuenta_codigo
            
            if codigo_cuenta not in clasificaciones_por_cuenta:
                clasificaciones_por_cuenta[codigo_cuenta] = {
                    'cuenta_id': None,
                    'cuenta_codigo': clasificacion.cuenta_codigo,
                    'cuenta_nombre': f"[TEMPORAL] Cuenta {clasificacion.cuenta_codigo}",
                    'cuenta_nombre_en': None,
                    'es_temporal': True,
                    'clasificaciones': []
                }
            
            clasificaciones_por_cuenta[codigo_cuenta]['clasificaciones'].append({
                'id': clasificacion.id,
                'set_clas_id': clasificacion.set_clas.id,
                'set_nombre': clasificacion.set_clas.nombre,
                'opcion_id': clasificacion.opcion.id,
                'opcion_valor': clasificacion.opcion.valor,
                'opcion_valor_en': clasificacion.opcion.valor_en,
                'fecha_creacion': clasificacion.fecha_creacion,
                'fecha_actualizacion': clasificacion.fecha_actualizacion,
                'origen': clasificacion.origen,
            })

    # NUEVO: Agregar cuentas sin clasificaciones
    from contabilidad.models import CuentaContable
    cuentas_sin_clasificacion = CuentaContable.objects.filter(
        cliente=cliente
    ).exclude(
        codigo__in=clasificaciones_por_cuenta.keys()
    )
    
    for cuenta in cuentas_sin_clasificacion:
        clasificaciones_por_cuenta[cuenta.codigo] = {
            'cuenta_id': cuenta.id,
            'cuenta_codigo': cuenta.codigo,
            'cuenta_nombre': cuenta.nombre,
            'cuenta_nombre_en': cuenta.nombre_en,
            'es_temporal': False,
            'clasificaciones': []  # Sin clasificaciones
        }

    # Convertir a formato que espera el frontend
    data = []
    for codigo_cuenta, info_cuenta in clasificaciones_por_cuenta.items():
        if info_cuenta['clasificaciones']:
            # Cuenta con clasificaciones - crear una entrada por clasificación
            for clasificacion in info_cuenta['clasificaciones']:
                data.append({
                    'id': clasificacion['id'],
                    'cuenta_id': info_cuenta['cuenta_id'],
                    'cuenta_codigo': info_cuenta['cuenta_codigo'],
                    'cuenta_nombre': info_cuenta['cuenta_nombre'],
                    'cuenta_nombre_en': info_cuenta['cuenta_nombre_en'],
                    'set_clas_id': clasificacion['set_clas_id'],
                    'set_nombre': clasificacion['set_nombre'],
                    'opcion_id': clasificacion['opcion_id'],
                    'opcion_valor': clasificacion['opcion_valor'],
                    'opcion_valor_en': clasificacion['opcion_valor_en'],
                    'fecha_creacion': clasificacion['fecha_creacion'],
                    'fecha_actualizacion': clasificacion['fecha_actualizacion'],
                    'es_temporal': info_cuenta['es_temporal'],
                    'origen': clasificacion['origen'],
                })
        else:
            # Cuenta sin clasificaciones - crear entrada placeholder
            data.append({
                'id': f"placeholder_{info_cuenta['cuenta_id']}",
                'cuenta_id': info_cuenta['cuenta_id'],
                'cuenta_codigo': info_cuenta['cuenta_codigo'],
                'cuenta_nombre': info_cuenta['cuenta_nombre'],
                'cuenta_nombre_en': info_cuenta['cuenta_nombre_en'],
                'set_clas_id': None,
                'set_nombre': None,
                'opcion_id': None,
                'opcion_valor': None,
                'opcion_valor_en': None,
                'fecha_creacion': None,
                'fecha_actualizacion': None,
                'es_temporal': info_cuenta['es_temporal'],
                'origen': 'sin_clasificacion',
            })
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_vista_clasificaciones_persistentes(request, cliente_id):
    """
    Registra que el usuario abrió el modal de clasificaciones persistentes
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    cierre_id = request.query_params.get('cierre_id')
    cierre = None
    
    if cierre_id:
        try:
            cierre = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
        except CierreContabilidad.DoesNotExist:
            pass

    periodo = cierre.periodo if cierre else date.today().strftime("%Y-%m")

    registrar_actividad_tarjeta(
        cliente_id=cliente_id,
        periodo=periodo,
        tarjeta="clasificacion",
        accion="view_persistent_modal",
        descripcion="Abrió modal de clasificaciones persistentes",
        usuario=request.user,
        detalles={
            "cierre_id": cierre_id,
            "modal_type": "persistent_classifications"
        },
        resultado="exito",
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response({"mensaje": "Vista registrada correctamente"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clasificacion_masiva_persistente(request):
    """
    Realiza clasificación masiva de cuentas en la base de datos persistente
    """
    cuenta_ids = request.data.get('cuenta_ids', [])
    set_clas_id = request.data.get('set_clas_id')
    opcion_id = request.data.get('opcion_id')
    
    if not cuenta_ids or not set_clas_id or not opcion_id:
        return Response({
            "error": "cuenta_ids, set_clas_id y opcion_id son requeridos"
        }, status=400)
    
    try:
        set_clas = ClasificacionSet.objects.get(id=set_clas_id)
        opcion = ClasificacionOption.objects.get(id=opcion_id, set_clas=set_clas)
        cuentas = CuentaContable.objects.filter(id__in=cuenta_ids)
        
        if len(cuentas) != len(cuenta_ids):
            return Response({
                "error": "Algunas cuentas no fueron encontradas"
            }, status=400)
        
        # Verificar que todas las cuentas pertenecen al mismo cliente
        cliente = cuentas.first().cliente
        if not all(cuenta.cliente == cliente for cuenta in cuentas):
            return Response({
                "error": "Todas las cuentas deben pertenecer al mismo cliente"
            }, status=400)
        
        created_count = 0
        updated_count = 0
        
        for cuenta in cuentas:
            clasificacion, created = AccountClassification.objects.update_or_create(
                cuenta=cuenta,
                set_clas=set_clas,
                defaults={'opcion': opcion}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Registrar actividad
        cierre = CierreContabilidad.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
        ).order_by('-fecha_creacion').first()
        
        periodo = cierre.periodo if cierre else date.today().strftime("%Y-%m")
        
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=periodo,
            tarjeta="clasificacion",
            accion="bulk_classify_persistent",
            descripcion=f"Clasificación masiva persistente: {len(cuenta_ids)} cuentas",
            usuario=request.user,
            detalles={
                "cuenta_ids": cuenta_ids,
                "set_nombre": set_clas.nombre,
                "opcion_valor": opcion.valor,
                "created_count": created_count,
                "updated_count": updated_count,
                "total_cuentas": len(cuenta_ids)
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        
        return Response({
            "mensaje": f"Clasificación masiva completada",
            "created": created_count,
            "updated": updated_count,
            "total": len(cuenta_ids)
        })
        
    except ClasificacionSet.DoesNotExist:
        return Response({"error": "Set de clasificación no encontrado"}, status=404)
    except ClasificacionOption.DoesNotExist:
        return Response({"error": "Opción de clasificación no encontrada"}, status=404)
    except Exception as e:
        return Response({
            "error": f"Error en clasificación masiva: {str(e)}"
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_estadisticas_clasificaciones_persistentes(request, cliente_id):
    """
    Obtiene estadísticas de las clasificaciones persistentes para el cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=404)

    # Contar clasificaciones
    total_clasificaciones = AccountClassification.objects.filter(
        cuenta__cliente=cliente
    ).count()
    
    # Contar cuentas totales
    total_cuentas = CuentaContable.objects.filter(cliente=cliente).count()
    
    # Contar cuentas clasificadas (que tienen al menos una clasificación)
    cuentas_clasificadas = CuentaContable.objects.filter(
        cliente=cliente,
        accountclassification__isnull=False
    ).distinct().count()
    
    # Cuentas sin clasificar
    cuentas_sin_clasificar = total_cuentas - cuentas_clasificadas
    
    # Contar sets disponibles
    total_sets = ClasificacionSet.objects.filter(cliente=cliente).count()
    
    return Response({
        "total_clasificaciones": total_clasificaciones,
        "total_cuentas": total_cuentas,
        "cuentas_clasificadas": cuentas_clasificadas,
        "cuentas_sin_clasificar": cuentas_sin_clasificar,
        "total_sets": total_sets,
        "porcentaje_clasificado": round((cuentas_clasificadas / total_cuentas * 100) if total_cuentas > 0 else 0, 2)
    })


# ==================== FIN VISTAS CLASIFICACIONES PERSISTENTES ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_registro_clasificacion_completo(request):
    """
    Crea un registro completo con múltiples clasificaciones.
    Maneja tanto cuentas existentes (con FK) como temporales (solo código).
    
    Payload esperado:
    {
        "cliente": 2,
        "numero_cuenta": "1234",
        "cuenta_nombre": "Nombre de cuenta",
        "clasificaciones": {
            "AGRUPACION INFORME": "ACTIVOS",
            "Estado Situacion Financiera": "ACTIVOS CORRIENTES"
        }
    }
    """
    try:
        cliente_id = request.data.get('cliente')
        numero_cuenta = request.data.get('numero_cuenta')
        cuenta_nombre = request.data.get('cuenta_nombre', numero_cuenta)
        clasificaciones = request.data.get('clasificaciones', {})
        
        if not cliente_id or not numero_cuenta:
            return Response({
                "error": "cliente y numero_cuenta son requeridos"
            }, status=400)
        
        # Verificar que el cliente existe
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)
        
        # Verificar si existe una cuenta con ese código
        cuenta_existente = CuentaContable.objects.filter(
            cliente=cliente, 
            codigo=numero_cuenta
        ).first()
        
        clasificaciones_creadas = []
        errores = []
        
        # Procesar cada clasificación
        for set_nombre, opcion_valor in clasificaciones.items():
            try:
                # Buscar el set por nombre
                set_clas = ClasificacionSet.objects.filter(
                    cliente=cliente,
                    nombre=set_nombre
                ).first()
                
                if not set_clas:
                    errores.append(f"Set '{set_nombre}' no encontrado")
                    continue
                
                # Buscar la opción por valor en el set
                opcion = ClasificacionOption.objects.filter(
                    set_clas=set_clas,
                    valor=opcion_valor
                ).first()
                
                if not opcion:
                    errores.append(f"Opción '{opcion_valor}' no encontrada en set '{set_nombre}'")
                    continue
                
                # Crear la clasificación
                if cuenta_existente:
                    # Clasificación con FK a cuenta existente
                    clasificacion, created = AccountClassification.objects.update_or_create(
                        cuenta=cuenta_existente,
                        set_clas=set_clas,
                        defaults={
                            'opcion': opcion,
                            'origen': 'modal_manual',
                            'cliente': cliente,
                            'cuenta_codigo': numero_cuenta  # Mantener código para compatibilidad con modal
                        }
                    )
                else:
                    # Clasificación temporal (sin FK a cuenta)
                    clasificacion, created = AccountClassification.objects.update_or_create(
                        cuenta_codigo=numero_cuenta,
                        set_clas=set_clas,
                        cliente=cliente,
                        defaults={
                            'opcion': opcion,
                            'origen': 'modal_manual'
                        }
                    )
                
                clasificaciones_creadas.append({
                    'id': clasificacion.id,
                    'set_nombre': set_nombre,
                    'opcion_valor': opcion_valor,
                    'created': created
                })
                
            except Exception as e:
                errores.append(f"Error en clasificación {set_nombre}: {str(e)}")
        
        # Registrar actividad
        try:
            cierre = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
            
            periodo = cierre.periodo if cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo,
                tarjeta="clasificacion",
                accion="create_complete_record",
                descripcion=f"Creó registro completo desde modal: {numero_cuenta} con {len(clasificaciones_creadas)} clasificaciones",
                usuario=request.user,
                detalles={
                    "numero_cuenta": numero_cuenta,
                    "cuenta_nombre": cuenta_nombre,
                    "cuenta_existe": bool(cuenta_existente),
                    "clasificaciones_creadas": len(clasificaciones_creadas),
                    "errores_count": len(errores),
                    "clasificaciones": clasificaciones,
                    "tipo": "temporal" if not cuenta_existente else "con_fk"
                },
                resultado="exito" if not errores else "parcial",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            # No fallar la operación principal por error de logging
            pass
        
        # Respuesta
        response_data = {
            "mensaje": "Registro creado exitosamente",
            "numero_cuenta": numero_cuenta,
            "cuenta_existe": bool(cuenta_existente),
            "clasificaciones_creadas": len(clasificaciones_creadas),
            "clasificaciones_solicitadas": len(clasificaciones),
            "detalles": clasificaciones_creadas
        }
        
        if errores:
            response_data["errores"] = errores
            response_data["errores_count"] = len(errores)
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            "error": f"Error creando registro completo: {str(e)}"
        }, status=500)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def actualizar_registro_clasificacion_completo(request, cuenta_codigo):
    """
    Actualiza un registro completo de clasificaciones para una cuenta específica.
    Permite modificar el código de cuenta y todas las clasificaciones asociadas.
    
    Payload esperado:
    {
        "nuevo_numero_cuenta": "1234", (opcional, para cambiar código de cuenta)
        "cuenta_nombre": "Nuevo nombre",
        "clasificaciones": {
            "AGRUPACION INFORME": "ACTIVOS",
            "Estado Situacion Financiera": "ACTIVOS CORRIENTES"
        }
    }
    """
    try:
        # Obtener cliente del query parameter o del contexto
        cliente_id = request.query_params.get('cliente')
        if not cliente_id:
            return Response({
                "error": "Parámetro 'cliente' es requerido"
            }, status=400)
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)
        
        nuevo_numero_cuenta = request.data.get('nuevo_numero_cuenta', cuenta_codigo)
        cuenta_nombre = request.data.get('cuenta_nombre', cuenta_codigo)
        clasificaciones = request.data.get('clasificaciones', {})
        
        # Buscar clasificaciones existentes para esta cuenta
        # Buscar tanto por FK como por código temporal
        clasificaciones_existentes = AccountClassification.objects.filter(
            cliente=cliente
        ).filter(
            # Buscar por FK a cuenta O por código temporal
            Q(cuenta__codigo=cuenta_codigo) | 
            Q(cuenta_codigo=cuenta_codigo, cuenta__isnull=True)
        )
        
        if not clasificaciones_existentes.exists():
            return Response({
                "error": f"No se encontraron clasificaciones para la cuenta {cuenta_codigo}"
            }, status=404)
        
        # Eliminar clasificaciones existentes
        clasificaciones_eliminadas = clasificaciones_existentes.count()
        sets_eliminados = list(set(clasificaciones_existentes.values_list('set_clas__nombre', flat=True)))
        clasificaciones_existentes.delete()
        
        # Verificar si la cuenta existe en la BD
        cuenta_existente = None
        if nuevo_numero_cuenta != cuenta_codigo:
            # Si cambió el código, buscar la nueva cuenta
            cuenta_existente = CuentaContable.objects.filter(
                cliente=cliente, 
                codigo=nuevo_numero_cuenta
            ).first()
        else:
            # Buscar la cuenta original
            cuenta_existente = CuentaContable.objects.filter(
                cliente=cliente, 
                codigo=cuenta_codigo
            ).first()
        
        # Crear las nuevas clasificaciones
        clasificaciones_creadas = []
        errores = []
        
        for set_nombre, opcion_valor in clasificaciones.items():
            try:
                # Buscar el set por nombre
                set_clas = ClasificacionSet.objects.filter(
                    cliente=cliente,
                    nombre=set_nombre
                ).first()
                
                if not set_clas:
                    errores.append(f"Set '{set_nombre}' no encontrado")
                    continue
                
                # Buscar la opción por valor en el set
                opcion = ClasificacionOption.objects.filter(
                    set_clas=set_clas,
                    valor=opcion_valor
                ).first()
                
                if not opcion:
                    errores.append(f"Opción '{opcion_valor}' no encontrada en set '{set_nombre}'")
                    continue
                
                # Crear la nueva clasificación
                if cuenta_existente:
                    # Clasificación con FK a cuenta existente
                    clasificacion = AccountClassification.objects.create(
                        cuenta=cuenta_existente,
                        set_clas=set_clas,
                        opcion=opcion,
                        origen='modal_edit',
                        cliente=cliente,
                        cuenta_codigo=nuevo_numero_cuenta  # Mantener código para compatibilidad con modal
                    )
                else:
                    # Clasificación temporal (sin FK a cuenta)
                    clasificacion = AccountClassification.objects.create(
                        cuenta_codigo=nuevo_numero_cuenta,
                        set_clas=set_clas,
                        opcion=opcion,
                        origen='modal_edit',
                        cliente=cliente
                    )
                
                clasificaciones_creadas.append({
                    'id': clasificacion.id,
                    'set_nombre': set_nombre,
                    'opcion_valor': opcion_valor
                })
                
            except Exception as e:
                errores.append(f"Error en clasificación {set_nombre}: {str(e)}")
        
        # Registrar actividad
        try:
            cierre = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
            
            periodo = cierre.periodo if cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo,
                tarjeta="clasificacion",
                accion="edit_complete_record",
                descripcion=f"Editó registro completo desde modal: {cuenta_codigo} → {nuevo_numero_cuenta}",
                usuario=request.user,
                detalles={
                    "cuenta_codigo_anterior": cuenta_codigo,
                    "cuenta_codigo_nuevo": nuevo_numero_cuenta,
                    "cuenta_nombre": cuenta_nombre,
                    "cuenta_existe": bool(cuenta_existente),
                    "clasificaciones_eliminadas": clasificaciones_eliminadas,
                    "sets_eliminados": sets_eliminados,
                    "clasificaciones_creadas": len(clasificaciones_creadas),
                    "errores_count": len(errores),
                    "clasificaciones_nuevas": clasificaciones,
                    "tipo": "temporal" if not cuenta_existente else "con_fk"
                },
                resultado="exito" if not errores else "parcial",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            # No fallar la operación principal por error de logging
            pass
        
        # Respuesta
        response_data = {
            "mensaje": "Registro actualizado exitosamente",
            "cuenta_codigo_anterior": cuenta_codigo,
            "cuenta_codigo_nuevo": nuevo_numero_cuenta,
            "cuenta_existe": bool(cuenta_existente),
            "clasificaciones_eliminadas": clasificaciones_eliminadas,
            "clasificaciones_creadas": len(clasificaciones_creadas),
            "clasificaciones_solicitadas": len(clasificaciones),
            "detalles": clasificaciones_creadas
        }
        
        if errores:
            response_data["errores"] = errores
            response_data["errores_count"] = len(errores)
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            "error": f"Error actualizando registro completo: {str(e)}"
        }, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_registro_clasificacion_completo(request, cuenta_codigo):
    """
    Elimina todas las clasificaciones de una cuenta específica.
    """
    try:
        # Obtener cliente del query parameter
        cliente_id = request.query_params.get('cliente')
        if not cliente_id:
            return Response({
                "error": "Parámetro 'cliente' es requerido"
            }, status=400)
        
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)
        
        # Buscar clasificaciones existentes para esta cuenta
        # Buscar tanto por FK como por código temporal
        clasificaciones_existentes = AccountClassification.objects.filter(
            cliente=cliente
        ).filter(
            # Buscar por FK a cuenta O por código temporal
            Q(cuenta__codigo=cuenta_codigo) | 
            Q(cuenta_codigo=cuenta_codigo, cuenta__isnull=True)
        )
        
        if not clasificaciones_existentes.exists():
            return Response({
                "error": f"No se encontraron clasificaciones para la cuenta {cuenta_codigo}"
            }, status=404)
        
        # Recopilar información antes de eliminar
        clasificaciones_info = []
        for clasificacion in clasificaciones_existentes:
            clasificaciones_info.append({
                'id': clasificacion.id,
                'set_nombre': clasificacion.set_clas.nombre,
                'opcion_valor': clasificacion.opcion.valor,
                'es_temporal': not bool(clasificacion.cuenta)
            })
        
        clasificaciones_eliminadas = clasificaciones_existentes.count()
        sets_afectados = list(set(clasificaciones_existentes.values_list('set_clas__nombre', flat=True)))
        
        # Eliminar todas las clasificaciones
        clasificaciones_existentes.delete()
        
        # Registrar actividad
        try:
            cierre = CierreContabilidad.objects.filter(
                cliente=cliente,
                estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
            ).order_by('-fecha_creacion').first()
            
            periodo = cierre.periodo if cierre else date.today().strftime("%Y-%m")
            
            registrar_actividad_tarjeta(
                cliente_id=cliente_id,
                periodo=periodo,
                tarjeta="clasificacion",
                accion="delete_complete_record",
                descripcion=f"Eliminó registro completo desde modal: {cuenta_codigo} ({clasificaciones_eliminadas} clasificaciones)",
                usuario=request.user,
                detalles={
                    "cuenta_codigo": cuenta_codigo,
                    "clasificaciones_eliminadas": clasificaciones_eliminadas,
                    "sets_afectados": sets_afectados,
                    "clasificaciones_info": clasificaciones_info
                },
                resultado="exito",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception as e:
            # No fallar la operación principal por error de logging
            pass
        
        return Response({
            "mensaje": "Registro eliminado exitosamente",
            "cuenta_codigo": cuenta_codigo,
            "clasificaciones_eliminadas": clasificaciones_eliminadas,
            "sets_afectados": sets_afectados,
            "detalles": clasificaciones_info
        })
        
    except Exception as e:
        return Response({
            "error": f"Error eliminando registro completo: {str(e)}"
        }, status=500)
