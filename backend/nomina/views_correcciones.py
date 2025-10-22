import logging
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from django.db import transaction
from .models import CierreNomina, LibroRemuneracionesUpload
from .models_logging import registrar_actividad_tarjeta_nomina
from .utils.clientes import get_client_ip
from .utils.mixins import UploadLogNominaMixin
from .utils.mixins import ValidacionArchivoCRUDMixin
from .tasks_refactored.correcciones import (
    log_correccion_start,
    log_correccion_cleanup_complete,
)

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def corregir_libro_view(request, cierre_id: int):
    """
    Endpoint mínimo para probar flujo de corrección de libro.
    Recibe un archivo vía multipart/form-data con key 'archivo'.
    Por ahora, sólo loggea/print y retorna un OK con metadatos.
    """
    archivo = request.FILES.get('archivo')
    if not archivo:
        return Response({"detail": "Se requiere archivo (.xlsx) en campo 'archivo'"}, status=status.HTTP_400_BAD_REQUEST)

    # 1) Obtener cierre y cliente asociado
    try:
        cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
    except CierreNomina.DoesNotExist:
        return Response({"detail": "Cierre no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # 2) Validar tipo/estructura del archivo y nombre con patrón estándar
    try:
        validator = ValidacionArchivoCRUDMixin()
        # Validación básica de archivo (extensión, tamaño, etc.)
        validator.validar_archivo(archivo)

        periodo_formato = (cierre.periodo or "").replace("-", "")  # '2025-08' -> '202508'
        rut = getattr(cierre.cliente, 'rut', '') or ''
        rut_sin_sep = rut.replace("-", "").replace(".", "")
        patron_regex = rf"^{periodo_formato}_libro_remuneraciones_{rut_sin_sep}(_.*)?\.(xlsx|xls)$"

        logger.info(f"[CorreccionLibro] Validando nombre '{archivo.name}' contra patrón: {patron_regex}")
        validator.validar_nombre_archivo(archivo.name, patron_regex)
    except ValueError as e:
        # Convertir a ValidationError de DRF
        raise ValidationError({"detail": str(e)})

    # 3) Validación OK → Eliminar archivos de libro anteriores y actualizar versión
    eliminados = 0
    eliminados_archivo = 0
    with transaction.atomic():
        # 🔄 NUEVO: Incrementar version_datos para sistema de versiones de incidencias
        cierre = CierreNomina.objects.select_for_update().get(id=cierre_id)
        version_anterior = cierre.version_datos or 1
        cierre.version_datos = version_anterior + 1
        cierre.save(update_fields=['version_datos'])
        
        logger.info(f"[CorreccionLibro] Versión incrementada: v{version_anterior} → v{cierre.version_datos}")

        # 📋 DUAL LOGGING: Inicio de corrección
        try:
            log_correccion_start(
                cierre_id=cierre.id,
                usuario_id=getattr(request.user, 'id', None),
                archivo_nombre=archivo.name,
                version_anterior=version_anterior,
                version_nueva=cierre.version_datos,
                ip_address=get_client_ip(request),
            )
        except Exception:
            # No bloquear si el logging falla
            pass
        
        libros_previos = list(
            LibroRemuneracionesUpload.objects.filter(cierre=cierre).order_by('-fecha_subida')
        )
        for libro in libros_previos:
            try:
                # Eliminar archivo físico si existe, pero sin guardar el modelo
                if getattr(libro, 'archivo', None):
                    try:
                        libro.archivo.delete(save=False)
                        eliminados_archivo += 1
                    except Exception:
                        # No interrumpir si falla eliminación física
                        pass
                # Eliminar registro del upload (no usar perform_destroy del ViewSet para no tocar consolidados)
                libro.delete()
                eliminados += 1
            except Exception as e:
                logger.warning(
                    f"[CorreccionLibro] Error eliminando libro previo id={getattr(libro, 'id', None)}: {e}"
                )

        # 4) Registrar UploadLog de corrección (usamos tipo válido)
        log_mixin = UploadLogNominaMixin()
        log_mixin.tipo_upload = "libro_remuneraciones"
        log_mixin.usuario = request.user
        log_mixin.ip_usuario = get_client_ip(request)
        upload_log = log_mixin.crear_upload_log(cierre.cliente, archivo)
        # Asociar el cierre para trazabilidad
        upload_log.cierre = cierre
        upload_log.save(update_fields=["cierre"])
        # Guardar un pequeño resumen indicando acción
        upload_log.resumen = {
            "accion": "correccion_eliminacion_previos",
            "cierre_id": cierre.id,
            "version_datos": cierre.version_datos,  # 🆕 Versión para trazabilidad
            "version_anterior": version_anterior,
            "libros_previos_eliminados": eliminados,
            "archivos_fisicos_eliminados": eliminados_archivo,
            "archivo_correccion_nombre": archivo.name,
        }
        upload_log.save(update_fields=['resumen'])

        # 5) Registrar actividad (dual) de cleanup completado
        try:
            log_correccion_cleanup_complete(
                cierre_id=cierre.id,
                usuario_id=getattr(request.user, 'id', None),
                eliminados=eliminados,
                eliminados_archivo=eliminados_archivo,
                upload_log_id=getattr(upload_log, 'id', None),
                archivo_nombre=archivo.name,
                version_nueva=cierre.version_datos,
                ip_address=get_client_ip(request),
            )
        except Exception:
            # No bloquear si el logging falla
            pass

    logger.info(
        f"[CorreccionLibro] cierre_id={cierre_id} archivo={archivo.name} validado. Previos eliminados={eliminados} (archivos={eliminados_archivo}). Versión: v{version_anterior} → v{cierre.version_datos}"
    )
    print(
        f"[CorreccionLibro] OK cierre={cierre_id} archivo={archivo.name} previos_eliminados={eliminados} version={cierre.version_datos}"
    )

    return Response({
        "message": "Archivo de corrección validado. Uploads anteriores eliminados.",
        "cierre_id": cierre_id,
        "version_datos": cierre.version_datos,  # 🆕 Nueva versión
        "version_anterior": version_anterior,  # 🆕 Versión anterior para referencia
        "archivo_nombre": archivo.name,
        "archivo_size": getattr(archivo, 'size', None),
        "patron_validado": True,
        "eliminados": eliminados,
        "eliminados_archivo": eliminados_archivo,
        "upload_log_id": upload_log.id,
    }, status=status.HTTP_200_OK)
