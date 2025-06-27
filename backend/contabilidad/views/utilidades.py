# backend/contabilidad/views/utilidades.py
import os
import glob
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.conf import settings

from ..models import UploadLog
from ..tasks import tarea_de_prueba


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test_celery(request):
    """
    Función de prueba para verificar que Celery está funcionando
    """
    try:
        # Ejecutar tarea de prueba
        result = tarea_de_prueba.delay("Test message from API")
        
        return Response({
            "mensaje": "Tarea de prueba enviada a Celery",
            "task_id": result.id,
            "status": "sent"
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error al enviar tarea a Celery: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def limpiar_archivos_temporales(request):
    """
    Limpia archivos temporales del directorio media/temp
    """
    try:
        archivos_eliminados = []
        directorios_limpiados = []
        
        # Directorio temporal principal
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
        
        if os.path.exists(temp_dir):
            # Buscar archivos temporales
            temp_files = glob.glob(os.path.join(temp_dir, "*"))
            
            for file_path in temp_files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        archivos_eliminados.append(os.path.basename(file_path))
                    elif os.path.isdir(file_path):
                        # Limpiar subdirectorios vacíos
                        if not os.listdir(file_path):
                            os.rmdir(file_path)
                            directorios_limpiados.append(os.path.basename(file_path))
                except OSError as e:
                    continue
        
        # También limpiar archivos huérfanos en otros directorios
        media_subdirs = ["clasificacion", "clasificaciones", "libros", "nombres_ingles", "remuneraciones", "tipo_documento"]
        
        for subdir in media_subdirs:
            subdir_path = os.path.join(settings.MEDIA_ROOT, subdir)
            if os.path.exists(subdir_path):
                # Buscar archivos muy antiguos (más de 7 días) que podrían ser huérfanos
                import time
                current_time = time.time()
                week_ago = current_time - (7 * 24 * 60 * 60)  # 7 días en segundos
                
                for root, dirs, files in os.walk(subdir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            # Verificar si el archivo es muy antiguo
                            file_time = os.path.getctime(file_path)
                            if file_time < week_ago:
                                # Verificar si el archivo está referenciado en la BD
                                relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                                if not UploadLog.objects.filter(ruta_archivo__icontains=relative_path).exists():
                                    os.remove(file_path)
                                    archivos_eliminados.append(relative_path)
                        except OSError:
                            continue
        
        return Response({
            "mensaje": "Limpieza de archivos temporales completada",
            "archivos_eliminados": len(archivos_eliminados),
            "directorios_limpiados": len(directorios_limpiados),
            "detalles": {
                "archivos": archivos_eliminados[:20],  # Mostrar solo los primeros 20
                "directorios": directorios_limpiados,
            }
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error al limpiar archivos temporales: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_upload_log(request, upload_log_id):
    """
    Obtiene el estado detallado de un upload log específico
    """
    try:
        upload_log = UploadLog.objects.select_related('cliente', 'usuario').get(id=upload_log_id)
        
        # Construir datos de forma segura, manejando campos que podrían no existir
        data = {
            "id": upload_log.id,
            "tipo": upload_log.tipo_upload,
            "cliente_id": upload_log.cliente.id if upload_log.cliente else None,
            "cliente_nombre": upload_log.cliente.nombre if upload_log.cliente else None,
            "estado": upload_log.estado,
            "nombre_archivo": upload_log.nombre_archivo_original,
            "fecha_creacion": upload_log.fecha_subida,
            "tiempo_procesamiento": (
                str(upload_log.tiempo_procesamiento)
                if hasattr(upload_log, 'tiempo_procesamiento') and upload_log.tiempo_procesamiento
                else None
            ),
            "errores": upload_log.errores if hasattr(upload_log, 'errores') else None,
            "resumen": upload_log.resumen if hasattr(upload_log, 'resumen') else None,
        }
        
        # Agregar campos opcionales si existen
        if hasattr(upload_log, 'fecha_procesamiento'):
            data["fecha_procesamiento"] = upload_log.fecha_procesamiento
        if hasattr(upload_log, 'registros_totales'):
            data["registros_totales"] = upload_log.registros_totales
        if hasattr(upload_log, 'registros_procesados'):
            data["registros_procesados"] = upload_log.registros_procesados
        if hasattr(upload_log, 'registros_errores'):
            data["registros_errores"] = upload_log.registros_errores
        if hasattr(upload_log, 'ruta_archivo'):
            data["ruta_archivo"] = upload_log.ruta_archivo
        if hasattr(upload_log, 'hash_archivo'):
            data["hash_archivo"] = upload_log.hash_archivo
        if hasattr(upload_log, 'tamaño_archivo'):
            data["tamaño_archivo"] = upload_log.tamaño_archivo
        if hasattr(upload_log, 'usuario') and upload_log.usuario:
            data["usuario"] = getattr(upload_log.usuario, 'correo_bdo', str(upload_log.usuario))
            
        return Response(data)
        
    except UploadLog.DoesNotExist:
        return Response(
            {"error": "UploadLog no encontrado"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error al consultar UploadLog: %s", e)
        return Response(
            {"error": "Error interno del servidor"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
