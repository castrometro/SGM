# backend/contabilidad/views/cliente.py
import os
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from api.models import Cliente
from ..models import (
    CierreContabilidad,
    TipoDocumento, 
    TipoDocumentoArchivo, 
    UploadLog,
    NombreIngles,
    NombreInglesArchivo,
    NombresEnInglesUpload,
    ClasificacionCuentaArchivo,
    ClasificacionArchivo,
)
from ..utils.activity_logger import registrar_actividad_tarjeta
from .helpers import obtener_periodo_actividad_para_cliente, get_client_ip


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen_cliente(request, cliente_id):
    """
    Obtiene un resumen básico del cliente con información del último cierre
    
    Returns:
        - cliente_id: ID del cliente
        - cliente: Nombre del cliente
        - ultimo_cierre: Período del último cierre (ej: "2024-12")
        - estado_ultimo_cierre: Estado del último cierre
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Obtener el último cierre del cliente
    ultimo_cierre = (
        CierreContabilidad.objects.filter(cliente=cliente)
        .order_by("-periodo")
        .first()
    )

    return Response(
        {
            "cliente_id": cliente.id,
            "cliente": cliente.nombre,
            "ultimo_cierre": ultimo_cierre.periodo if ultimo_cierre else None,
            "estado_ultimo_cierre": ultimo_cierre.estado if ultimo_cierre else None,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_cliente(request, cliente_id):
    """
    Obtiene información detallada del cliente incluyendo estadísticas de cierres
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    
    # Estadísticas de cierres
    cierres = CierreContabilidad.objects.filter(cliente=cliente)
    total_cierres = cierres.count()
    
    # Distribución por estado
    estados = {}
    for estado_code, estado_name in CierreContabilidad.ESTADOS:
        count = cierres.filter(estado=estado_code).count()
        if count > 0:
            estados[estado_code] = {
                'nombre': estado_name,
                'cantidad': count
            }
    
    # Cierres recientes
    cierres_recientes = list(
        cierres.order_by('-periodo')[:5].values(
            'id', 'periodo', 'estado', 'fecha_cierre', 'fecha_creacion'
        )
    )
    
    return Response({
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "rut": cliente.rut,
            "email": cliente.email,
            "activo": cliente.activo,
            "bilingue": cliente.bilingue,
        },
        "estadisticas": {
            "total_cierres": total_cierres,
            "estados_cierres": estados,
        },
        "cierres_recientes": cierres_recientes,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_uploads_cliente(request, cliente_id):
    """
    Obtiene el historial de uploads para un cliente específico
    
    Query params:
    - tipo: tipo de upload (clasificacion, libro_mayor, tipo_documento, nombres_ingles)
    - limit: límite de resultados (default 20)
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Obtener parámetros de filtro
    tipo_upload = request.GET.get("tipo", None)
    limit = int(request.GET.get("limit", 20))

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
            data.append({
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
                ),
            })

        return Response({
            "cliente_id": cliente.id,
            "cliente_nombre": cliente.nombre,
            "total_uploads": UploadLog.objects.filter(cliente=cliente).count(),
            "uploads": data,
        })

    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_tipo_documento(request, cliente_id):
    """
    Verifica el estado de los tipos de documento para un cliente específico
    
    Returns:
    - estado: "subido" | "pendiente"
    - mensaje: información adicional (opcional)
    - historial_eliminado: boolean (opcional)
    """
    try:
        # Busca si ya existe un tipo de documento asociado al cliente
        existe_tipos = TipoDocumento.objects.filter(cliente_id=cliente_id).exists()

        if existe_tipos:
            return Response({"estado": "subido"})

        # Si no hay tipos activos, verificar si hay uploads exitosos anteriores eliminados
        upload_log_eliminado = UploadLog.objects.filter(
            cliente_id=cliente_id, 
            tipo_upload="tipo_documento", 
            estado="datos_eliminados"
        ).exists()

        if upload_log_eliminado:
            return Response({
                "estado": "pendiente",
                "mensaje": "Datos eliminados previamente - puede volver a subir",
                "historial_eliminado": True,
            })

        return Response({"estado": "pendiente"})
        
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tipos_documento_cliente(request, cliente_id):
    """
    Obtiene la lista de tipos de documento para un cliente específico
    """
    try:
        tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)

        # Serializar datos
        data = [
            {
                "id": tipo.id,
                "codigo": tipo.codigo,
                "descripcion": tipo.descripcion,
            }
            for tipo in tipos
        ]
        return Response(data)
        
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_tipos_documento(request, cliente_id):
    """
    Registra cuando el usuario abre el modal de tipos de documento para tracking de actividad
    """
    try:
        from datetime import date
        
        cliente = Cliente.objects.get(id=cliente_id)
        tipos = TipoDocumento.objects.filter(cliente_id=cliente_id)

        # Obtener cierre_id del query parameter si se proporciona
        cierre_id = request.GET.get('cierre_id')
        
        if cierre_id:
            # Si se proporciona cierre_id específico, usarlo
            try:
                cierre_para_actividad = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                periodo_actividad = cierre_para_actividad.periodo
            except CierreContabilidad.DoesNotExist:
                # Si el cierre específico no existe, usar método genérico
                cierre_para_actividad = None
                periodo_actividad = date.today().strftime("%Y-%m")
        else:
            # Buscar cierre activo para actividad (método original)
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
                "cierre_especifico": bool(cierre_id),
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response({"mensaje": "Visualización registrada"})
        
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_tipos_documento(request, cliente_id):
    """
    Elimina todos los tipos de documento de un cliente específico
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

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

        # 3. Eliminar registros de TipoDocumento
        TipoDocumento.objects.filter(cliente=cliente).delete()

        # 4. Buscar cierre para actividad
        periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)

        # 5. Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=periodo_actividad,
            tarjeta="tipo_documento",
            accion="delete_all",
            descripcion=f"Eliminó todos los tipos de documento ({count} registros)",
            usuario=request.user,
            detalles={
                "registros_eliminados": count,
                "upload_logs_afectados": upload_logs_count,
                "archivos_eliminados": archivos_eliminados,
                "accion_origen": "eliminacion_manual",
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": f"Se eliminaron {count} tipos de documento exitosamente",
                "registros_eliminados": count,
                "upload_logs_afectados": upload_logs_count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Error al eliminar tipos de documento: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_nombres_ingles(request, cliente_id):
    """
    Elimina todos los nombres en inglés de un cliente específico
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Contar registros antes de eliminar
    count = NombreIngles.objects.filter(cliente=cliente).count()
    upload_logs_count = UploadLog.objects.filter(
        cliente=cliente, tipo_upload="nombres_ingles"
    ).count()

    # Variables para el log
    archivos_eliminados = []

    try:
        # 1. Buscar y eliminar archivo asociado si existe
        try:
            archivo_nombres = NombreInglesArchivo.objects.get(cliente=cliente)
            archivo_path = (
                archivo_nombres.archivo.path if archivo_nombres.archivo else None
            )
            archivo_name = (
                archivo_nombres.archivo.name if archivo_nombres.archivo else None
            )

            # Eliminar archivo físico del sistema
            if archivo_path and os.path.exists(archivo_path):
                os.remove(archivo_path)
                archivos_eliminados.append(archivo_name)

            # Eliminar registro del archivo
            archivo_nombres.delete()

        except NombreInglesArchivo.DoesNotExist:
            # No hay archivo que eliminar, continuar normalmente
            pass

        # 2. Limpiar archivos temporales de UploadLogs pero conservar registros para auditoría
        upload_logs = UploadLog.objects.filter(
            cliente=cliente, tipo_upload="nombres_ingles"
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

        # 3. Eliminar registros de NombreIngles
        NombreIngles.objects.filter(cliente=cliente).delete()

        # 4. Buscar cierre para actividad
        periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)

        # 5. Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=periodo_actividad,
            tarjeta="nombres_ingles",
            accion="delete_all",
            descripcion=f"Eliminó todos los nombres en inglés ({count} registros)",
            usuario=request.user,
            detalles={
                "registros_eliminados": count,
                "upload_logs_afectados": upload_logs_count,
                "archivos_eliminados": archivos_eliminados,
                "accion_origen": "eliminacion_manual",
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "mensaje": f"Se eliminaron {count} nombres en inglés exitosamente",
                "registros_eliminados": count,
                "upload_logs_afectados": upload_logs_count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Error al eliminar nombres en inglés: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def eliminar_todos_nombres_ingles_upload(request):
    """
    Elimina todos los uploads de nombres en inglés (función global)
    """
    try:
        # Contar registros antes de eliminar
        count = NombresEnInglesUpload.objects.count()
        archivos_eliminados = []

        # Eliminar archivos físicos
        uploads = NombresEnInglesUpload.objects.all()
        for upload in uploads:
            if upload.archivo:
                archivo_path = upload.archivo.path if upload.archivo else None
                if archivo_path and os.path.exists(archivo_path):
                    try:
                        os.remove(archivo_path)
                        archivos_eliminados.append(upload.archivo.name)
                    except OSError:
                        pass

        # Eliminar registros
        NombresEnInglesUpload.objects.all().delete()

        return Response(
            {
                "mensaje": f"Se eliminaron {count} uploads de nombres en inglés exitosamente",
                "registros_eliminados": count,
                "archivos_eliminados": len(archivos_eliminados),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Error al eliminar uploads de nombres en inglés: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_nombres_ingles(request, cliente_id):
    """
    Obtiene el estado de los nombres en inglés para un cliente
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Contar nombres en inglés
        nombres_count = NombreIngles.objects.filter(cliente=cliente).count()
        
        # Intentar obtener archivo de nombres, pero de forma segura
        archivo = None
        archivo_nombre = None
        try:
            archivo = NombreInglesArchivo.objects.filter(cliente=cliente).first()
            archivo_nombre = archivo.archivo.name if archivo and hasattr(archivo, 'archivo') and archivo.archivo else None
        except Exception:
            # Si el modelo NombreInglesArchivo no existe o hay error, continuar sin él
            pass
        
        # Obtener último upload log
        ultimo_upload = UploadLog.objects.filter(
            cliente=cliente, tipo_upload="nombres_ingles"
        ).order_by("-fecha_subida").first()

        # Determinar estado basado en datos disponibles
        if nombres_count > 0:
            estado = "subido"
        elif ultimo_upload and ultimo_upload.estado == "datos_eliminados":
            estado = "pendiente"
        else:
            estado = "pendiente"

        return Response(
            {
                "cliente_id": cliente.id,
                "cliente": cliente.nombre,
                "estado": estado,
                "total_nombres": nombres_count,
                "archivo_activo": bool(archivo),
                "archivo_nombre": archivo_nombre,
                "ultimo_upload": {
                    "id": ultimo_upload.id if ultimo_upload else None,
                    "fecha": ultimo_upload.fecha_subida if ultimo_upload else None,
                    "estado": ultimo_upload.estado if ultimo_upload else None,
                    "registros_procesados": getattr(ultimo_upload, 'registros_procesados', 0) if ultimo_upload else 0,
                } if ultimo_upload else None,
            }
        )

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error al obtener estado de nombres en inglés: %s", e)
        return Response(
            {"error": f"Error al obtener estado: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def nombres_ingles_cliente(request, cliente_id):
    """
    Lista los nombres en inglés de un cliente específico
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    nombres = NombreIngles.objects.filter(cliente=cliente).order_by("cuenta_codigo")
    
    data = []
    for nombre in nombres:
        data.append({
            "id": nombre.id,
            "cuenta_codigo": nombre.cuenta_codigo,
            "nombre_ingles": nombre.nombre_ingles,
            "fecha_creacion": nombre.fecha_creacion,
        })

    # Solo registrar actividad si es una consulta manual (con parámetro)
    # Las consultas automáticas para conteo no deberían registrar actividad
    registro_manual = request.GET.get('registrar_actividad', 'false').lower() == 'true'
    
    if registro_manual:
        # Registrar actividad solo cuando es una consulta manual del usuario
        periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
        registrar_actividad_tarjeta(
            cliente_id=cliente.id,
            periodo=periodo_actividad,
            tarjeta="nombres_ingles",
            accion="view_list",
            descripcion=f"Consultó lista de nombres en inglés ({len(data)} registros)",
            usuario=request.user,
            detalles={
                "total_registros": len(data),
                "accion_origen": "consulta_manual",
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

    return Response({
        "cliente": cliente.nombre,
        "total": len(data),
        "nombres": data,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_nombres_ingles(request, cliente_id):
    """
    Registra la visualización del modal de nombres en inglés
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        nombres = NombreIngles.objects.filter(cliente=cliente)
        
        # Obtener cierre_id del query parameter si se proporciona
        cierre_id = request.GET.get('cierre_id')
        
        if cierre_id:
            # Si se proporciona cierre_id específico, usarlo
            try:
                cierre_para_actividad = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                periodo_actividad = cierre_para_actividad.periodo
            except CierreContabilidad.DoesNotExist:
                # Si el cierre específico no existe, usar método genérico
                periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
                cierre_para_actividad = None
        else:
            # Usar método genérico
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            # Buscar cierre activo
            try:
                cierre_para_actividad = CierreContabilidad.objects.filter(
                    cliente=cliente,
                    estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
                ).order_by('-fecha_creacion').first()
            except Exception:
                cierre_para_actividad = None

        # Registrar actividad
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
                "cierre_especifico": bool(cierre_id),
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response({"mensaje": "Visualización registrada"})
        
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_vista_clasificaciones(request, cliente_id):
    """
    Registra la visualización del modal de clasificaciones
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Obtener conteo de clasificaciones (archivo activo)
        archivo_clasificacion = ClasificacionCuentaArchivo.objects.filter(cliente=cliente).first()
        total_registros = 0
        if archivo_clasificacion:
            # Aquí podrías contar las líneas del archivo o usar otro método
            total_registros = "archivo_activo"
        
        # Obtener cierre_id del query parameter si se proporciona
        cierre_id = request.GET.get('cierre_id')
        
        if cierre_id:
            # Si se proporciona cierre_id específico, usarlo
            try:
                cierre_para_actividad = CierreContabilidad.objects.get(id=cierre_id, cliente=cliente)
                periodo_actividad = cierre_para_actividad.periodo
            except CierreContabilidad.DoesNotExist:
                # Si el cierre específico no existe, usar método genérico
                periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
                cierre_para_actividad = None
        else:
            # Usar método genérico
            periodo_actividad = obtener_periodo_actividad_para_cliente(cliente)
            # Buscar cierre activo
            try:
                cierre_para_actividad = CierreContabilidad.objects.filter(
                    cliente=cliente,
                    estado__in=['pendiente', 'procesando', 'clasificacion', 'incidencias', 'en_revision']
                ).order_by('-fecha_creacion').first()
            except Exception:
                cierre_para_actividad = None

        # Registrar actividad
        registrar_actividad_tarjeta(
            cliente_id=cliente_id,
            periodo=periodo_actividad,
            tarjeta="clasificacion",
            accion="view_data", 
            descripcion=f"Abrió modal de clasificaciones",
            usuario=request.user,
            detalles={
                "total_registros": total_registros,
                "accion_origen": "modal_manual",
                "tiene_archivo": bool(archivo_clasificacion),
                "cierre_id": cierre_para_actividad.id if cierre_para_actividad else None,
                "cierre_especifico": bool(cierre_id),
            },
            resultado="exito",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response({"mensaje": "Visualización registrada"})
        
    except Cliente.DoesNotExist:
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cuentas_pendientes_set(request, cliente_id, set_id):
    """
    Obtiene las cuentas pendientes de clasificar para un set específico
    """
    from ..models import CuentaContable, AccountClassification
    
    cuentas = CuentaContable.objects.filter(cliente_id=cliente_id)
    clasificadas = AccountClassification.objects.filter(
        cuenta__in=cuentas, set_clas_id=set_id
    ).values_list("cuenta_id", flat=True)
    pendientes = cuentas.exclude(id__in=clasificadas)
    data = [{"id": c.id, "codigo": c.codigo, "nombre": c.nombre} for c in pendientes]
    return Response({"cuentas_faltantes": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_clasificaciones(request, cliente_id):
    """
    Verifica el estado de las clasificaciones para un cliente específico
    
    Returns:
    - estado: "subido" | "pendiente"
    - total_registros: cantidad de registros en el diccionario maestro
    - archivo_nombre: nombre del archivo subido (opcional)
    """
    try:
        # Buscar si existe archivo de clasificación (persiste entre cierres)
        archivo_clasificacion = ClasificacionArchivo.objects.filter(cliente_id=cliente_id).first()

        if archivo_clasificacion:
            # Contar registros en el diccionario maestro
            total_registros = ClasificacionCuentaArchivo.objects.filter(cliente_id=cliente_id).count()
            
            return Response({
                "estado": "subido",
                "total_registros": total_registros,
                "archivo_nombre": archivo_clasificacion.archivo.name.split('/')[-1] if archivo_clasificacion.archivo else None,
                "fecha_subida": archivo_clasificacion.fecha_subida,
            })

        # Si no hay archivo, verificar si hay uploads exitosos anteriores eliminados
        upload_log_eliminado = UploadLog.objects.filter(
            cliente_id=cliente_id, 
            tipo_upload="clasificacion", 
            estado="datos_eliminados"
        ).exists()

        if upload_log_eliminado:
            return Response({
                "estado": "pendiente",
                "mensaje": "Datos eliminados previamente - puede volver a subir",
                "historial_eliminado": True,
            })

        return Response({"estado": "pendiente"})
        
    except Exception as e:
        return Response({"error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper function que podría usarse en otras vistas
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
            # Si no hay cierre activo, usar fecha actual en formato YYYY-MM
            from datetime import date
            return date.today().strftime('%Y-%m')
    except Exception:
        # Fallback a fecha actual
        from datetime import date
        return date.today().strftime('%Y-%m')
