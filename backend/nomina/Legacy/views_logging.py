# backend/nomina/views_logging.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.db.models import Q

from .models_logging import UploadLogNomina, TarjetaActivityLogNomina, registrar_actividad_tarjeta_nomina
from api.models import Cliente


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_upload_log_nomina(request, upload_log_id):
    """
    Obtiene el estado detallado de un upload log específico para nómina
    """
    try:
        upload_log = UploadLogNomina.objects.select_related('cliente', 'usuario').get(id=upload_log_id)
        
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
                if upload_log.tiempo_procesamiento else None
            ),
            "errores": upload_log.errores,
            "resumen": upload_log.resumen,
            "fecha_procesamiento": upload_log.fecha_procesamiento,
            "registros_totales": upload_log.registros_totales,
            "registros_procesados": upload_log.registros_procesados,
            "registros_errores": upload_log.registros_errores,
            "ruta_archivo": upload_log.ruta_archivo,
            "hash_archivo": upload_log.hash_archivo,
            "usuario": upload_log.usuario.correo_bdo if upload_log.usuario else None,
            "ip_usuario": upload_log.ip_usuario,
        }
        
        return Response(data)
        
    except UploadLogNomina.DoesNotExist:
        return Response(
            {"error": "Log de upload no encontrado"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Error al obtener estado del upload: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_uploads_nomina(request, cliente_id):
    """
    Obtiene el historial de uploads para un cliente específico
    """
    try:
        # Validar que el cliente existe
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener parámetros de filtro
        tipo_upload = request.GET.get('tipo', None)
        limit = int(request.GET.get('limit', 20))
        page = int(request.GET.get('page', 1))
        
        # Construir query
        queryset = UploadLogNomina.objects.filter(cliente=cliente)
        
        if tipo_upload:
            queryset = queryset.filter(tipo_upload=tipo_upload)
        
        # Ordenar por fecha más reciente
        queryset = queryset.order_by('-fecha_subida')
        
        # Paginar
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serializar resultados
        results = []
        for upload in page_obj.object_list:
            results.append({
                "id": upload.id,
                "tipo": upload.tipo_upload,
                "estado": upload.estado,
                "nombre_archivo": upload.nombre_archivo_original,
                "fecha_subida": upload.fecha_subida,
                "fecha_procesamiento": upload.fecha_procesamiento,
                "registros_totales": upload.registros_totales,
                "registros_procesados": upload.registros_procesados,
                "registros_errores": upload.registros_errores,
                "usuario": upload.usuario.correo_bdo if upload.usuario else None,
                "errores": upload.errores,
                "resumen": upload.resumen,
            })
        
        return Response({
            "results": results,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        })
        
    except Cliente.DoesNotExist:
        return Response(
            {"error": "Cliente no encontrado"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Error al obtener historial: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activity_log_nomina(request, tarjeta_id):
    """
    Obtiene el log de actividad para una tarjeta específica
    """
    try:
        # Obtener parámetros de filtro
        tarjeta_tipo = request.GET.get('tarjeta_tipo', None)
        limit = int(request.GET.get('limit', 20))
        page = int(request.GET.get('page', 1))
        
        # Construir query
        queryset = TarjetaActivityLogNomina.objects.filter(tarjeta_id=tarjeta_id)
        
        if tarjeta_tipo:
            queryset = queryset.filter(tarjeta_tipo=tarjeta_tipo)
        
        # Ordenar por fecha más reciente
        queryset = queryset.order_by('-fecha_creacion')
        
        # Paginar
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serializar resultados
        results = []
        for activity in page_obj.object_list:
            results.append({
                "id": activity.id,
                "tarjeta_tipo": activity.tarjeta_tipo,
                "tarjeta_id": activity.tarjeta_id,
                "accion": activity.accion,
                "descripcion": activity.descripcion,
                "usuario": activity.usuario.correo_bdo if activity.usuario else None,
                "fecha_creacion": activity.fecha_creacion,
                "datos_adicionales": activity.datos_adicionales,
            })
        
        return Response({
            "results": results,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
        })
        
    except Exception as e:
        return Response(
            {"error": f"Error al obtener log de actividad: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_actividad_nomina(request):
    """
    Registra una nueva actividad en el log
    """
    try:
        data = request.data
        
        # Validar campos requeridos
        required_fields = ['tarjeta_tipo', 'tarjeta_id', 'accion', 'descripcion']
        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Campo requerido: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Crear actividad
        activity = TarjetaActivityLogNomina.objects.create(
            tarjeta_tipo=data['tarjeta_tipo'],
            tarjeta_id=data['tarjeta_id'],
            accion=data['accion'],
            descripcion=data['descripcion'],
            usuario=request.user,
            datos_adicionales=data.get('datos_adicionales', {}),
        )
        
        return Response({
            "id": activity.id,
            "mensaje": "Actividad registrada correctamente",
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {"error": f"Error al registrar actividad: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
