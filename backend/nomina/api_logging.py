# nomina/api_logging.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from .models_logging import registrar_actividad_tarjeta_nomina
from .utils.clientes import get_client_ip

logger = logging.getLogger(__name__)


class BaseActivityLogView(View):
    """Clase base para vistas de logging de actividad"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_request_data(self, request):
        """Extrae y valida datos de la request"""
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            return data, None
        except json.JSONDecodeError as e:
            return None, f"Error en formato JSON: {e}"
        except Exception as e:
            return None, f"Error procesando request: {e}"
    
    def validate_required_fields(self, data, required_fields):
        """Valida campos requeridos"""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return f"Campos requeridos faltantes: {', '.join(missing_fields)}"
        return None
    
    def log_activity_safe(self, **kwargs):
        """Registra actividad con manejo de errores"""
        try:
            activity_log = registrar_actividad_tarjeta_nomina(**kwargs)
            return activity_log, None
        except Exception as e:
            logger.error(f"Error registrando actividad: {e}")
            return None, str(e)


@method_decorator(csrf_exempt, name='dispatch')
class ModalActivityView(BaseActivityLogView):
    """Vista para logging de actividades de modal"""
    
    @require_http_methods(["POST"])
    def post(self, request):
        data, error = self.get_request_data(request)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Validar campos requeridos
        required_fields = ['cierre_id', 'tarjeta', 'action', 'modal_type']
        error = self.validate_required_fields(data, required_fields)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Mapear acción a nuestro sistema
        action_map = {
            'open': 'modal_open',
            'close': 'modal_close'
        }
        
        accion = action_map.get(data['action'])
        if not accion:
            return JsonResponse({
                'error': f"Acción no válida: {data['action']}. Valores permitidos: {list(action_map.keys())}"
            }, status=400)
        
        # Preparar descripción y detalles
        modal_type = data['modal_type']
        if accion == 'modal_open':
            descripcion = f"Modal abierto: {modal_type}"
        else:
            descripcion = f"Modal cerrado: {modal_type}"
        
        detalles = {
            'modal_type': modal_type,
            'context': data.get('context', {}),
            'action_taken': data.get('action_taken') if accion == 'modal_close' else None
        }
        
        # Registrar actividad
        activity_log, error = self.log_activity_safe(
            cierre_id=data['cierre_id'],
            tarjeta=data['tarjeta'],
            accion=accion,
            descripcion=descripcion,
            usuario=request.user if request.user.is_authenticated else None,
            detalles=detalles,
            resultado='exito',
            ip_address=get_client_ip(request)
        )
        
        if error:
            return JsonResponse({'error': error}, status=500)
        
        return JsonResponse({
            'success': True,
            'activity_id': activity_log.id if activity_log else None,
            'message': f"Actividad '{accion}' registrada correctamente"
        })


@method_decorator(csrf_exempt, name='dispatch')
class FileActivityView(BaseActivityLogView):
    """Vista para logging de actividades de archivo"""
    
    @require_http_methods(["POST"])
    def post(self, request):
        data, error = self.get_request_data(request)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Validar campos requeridos
        required_fields = ['cierre_id', 'tarjeta', 'action']
        error = self.validate_required_fields(data, required_fields)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Mapear acción a nuestro sistema
        action_map = {
            'select': 'file_select',
            'validate': 'file_validate',
            'download_template': 'download_template'
        }
        
        accion = action_map.get(data['action'])
        if not accion:
            return JsonResponse({
                'error': f"Acción no válida: {data['action']}. Valores permitidos: {list(action_map.keys())}"
            }, status=400)
        
        # Preparar descripción y detalles basado en la acción
        if accion == 'file_select':
            archivo_nombre = data.get('archivo_nombre', 'archivo desconocido')
            descripcion = f"Archivo seleccionado: {archivo_nombre}"
            detalles = {
                'archivo_nombre': archivo_nombre,
                'archivo_size': data.get('archivo_size')
            }
        elif accion == 'file_validate':
            archivo_nombre = data.get('archivo_nombre', 'archivo desconocido')
            errores = data.get('errores', [])
            descripcion = f"Validación de archivo: {'exitosa' if not errores else 'fallida'}"
            detalles = {
                'archivo_nombre': archivo_nombre,
                'validacion_exitosa': not errores,
                'errores': errores
            }
        elif accion == 'download_template':
            template_type = data.get('template_type', 'plantilla')
            descripcion = f"Plantilla descargada: {template_type}"
            detalles = {
                'template_type': template_type
            }
        
        resultado = 'exito'
        if accion == 'file_validate' and data.get('errores'):
            resultado = 'error'
        
        # Registrar actividad
        activity_log, error = self.log_activity_safe(
            cierre_id=data['cierre_id'],
            tarjeta=data['tarjeta'],
            accion=accion,
            descripcion=descripcion,
            usuario=request.user if request.user.is_authenticated else None,
            detalles=detalles,
            resultado=resultado,
            ip_address=get_client_ip(request)
        )
        
        if error:
            return JsonResponse({'error': error}, status=500)
        
        return JsonResponse({
            'success': True,
            'activity_id': activity_log.id if activity_log else None,
            'message': f"Actividad '{accion}' registrada correctamente"
        })


@method_decorator(csrf_exempt, name='dispatch')
class ClassificationActivityView(BaseActivityLogView):
    """Vista para logging de actividades de clasificación"""
    
    @require_http_methods(["POST"])
    def post(self, request):
        data, error = self.get_request_data(request)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Validar campos requeridos
        required_fields = ['cierre_id', 'tarjeta', 'action']
        error = self.validate_required_fields(data, required_fields)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Mapear acción a nuestro sistema
        action_map = {
            'view': 'view_classification',
            'map_concept': 'concept_map',
            'unmap_concept': 'concept_unmap',
            'save': 'save_classification'
        }
        
        accion = action_map.get(data['action'])
        if not accion:
            return JsonResponse({
                'error': f"Acción no válida: {data['action']}. Valores permitidos: {list(action_map.keys())}"
            }, status=400)
        
        # Preparar descripción y detalles basado en la acción
        if accion == 'view_classification':
            headers_count = data.get('headers_count')
            classified_count = data.get('classified_count')
            descripcion = "Visualización de clasificación de headers"
            detalles = {
                'headers_count': headers_count,
                'classified_count': classified_count,
                'unclassified_count': (headers_count - classified_count) if headers_count and classified_count else None
            }
        elif accion == 'concept_map':
            header_name = data.get('header_name', 'header desconocido')
            concepto_nombre = data.get('concepto_nombre', 'concepto desconocido')
            descripcion = f"Header '{header_name}' mapeado a concepto '{concepto_nombre}'"
            detalles = {
                'header_name': header_name,
                'concepto_id': data.get('concepto_id'),
                'concepto_nombre': concepto_nombre
            }
        elif accion == 'concept_unmap':
            header_name = data.get('header_name', 'header desconocido')
            descripcion = f"Header '{header_name}' desmapeado"
            detalles = {
                'header_name': header_name
            }
        elif accion == 'save_classification':
            saved_count = data.get('saved_count', 0)
            total_count = data.get('total_count', 0)
            descripcion = f"Clasificación guardada: {saved_count} de {total_count} headers"
            detalles = {
                'saved_count': saved_count,
                'total_count': total_count,
                'completion_percentage': (saved_count / total_count * 100) if total_count > 0 else 0
            }
        
        # Registrar actividad
        activity_log, error = self.log_activity_safe(
            cierre_id=data['cierre_id'],
            tarjeta=data['tarjeta'],
            accion=accion,
            descripcion=descripcion,
            usuario=request.user if request.user.is_authenticated else None,
            detalles=detalles,
            resultado='exito',
            ip_address=get_client_ip(request)
        )
        
        if error:
            return JsonResponse({'error': error}, status=500)
        
        return JsonResponse({
            'success': True,
            'activity_id': activity_log.id if activity_log else None,
            'message': f"Actividad '{accion}' registrada correctamente"
        })


@method_decorator(csrf_exempt, name='dispatch')
class SessionActivityView(BaseActivityLogView):
    """Vista para logging de actividades de sesión"""
    
    @require_http_methods(["POST"])
    def post(self, request):
        data, error = self.get_request_data(request)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Validar campos requeridos
        required_fields = ['cierre_id', 'tarjeta', 'action']
        error = self.validate_required_fields(data, required_fields)
        if error:
            return JsonResponse({'error': error}, status=400)
        
        # Mapear acción a nuestro sistema
        action_map = {
            'start': 'session_start',
            'end': 'session_end',
            'state_change': 'state_change',
            'polling_start': 'polling_start',
            'polling_stop': 'polling_stop',
            'progress_update': 'progress_update'
        }
        
        accion = action_map.get(data['action'])
        if not accion:
            return JsonResponse({
                'error': f"Acción no válida: {data['action']}. Valores permitidos: {list(action_map.keys())}"
            }, status=400)
        
        # Preparar descripción y detalles basado en la acción
        tarjeta = data['tarjeta']
        
        if accion == 'session_start':
            descripcion = f"Sesión de trabajo iniciada en tarjeta {tarjeta}"
            detalles = {'tarjeta': tarjeta}
        elif accion == 'session_end':
            duration_seconds = data.get('duration_seconds')
            descripcion = f"Sesión de trabajo finalizada en tarjeta {tarjeta}"
            detalles = {
                'tarjeta': tarjeta,
                'duration_seconds': duration_seconds
            }
        elif accion == 'state_change':
            old_state = data.get('old_state', 'estado desconocido')
            new_state = data.get('new_state', 'estado desconocido')
            descripcion = f"Estado cambió de '{old_state}' a '{new_state}'"
            detalles = {
                'old_state': old_state,
                'new_state': new_state,
                'trigger': data.get('trigger')
            }
        elif accion == 'polling_start':
            interval_seconds = data.get('interval_seconds', 30)
            descripcion = f"Polling iniciado con intervalo de {interval_seconds} segundos"
            detalles = {'interval_seconds': interval_seconds}
        elif accion == 'polling_stop':
            reason = data.get('reason')
            descripcion = f"Polling detenido{': ' + reason if reason else ''}"
            detalles = {'reason': reason}
        elif accion == 'progress_update':
            progress_percentage = data.get('progress_percentage', 0)
            step_description = data.get('step_description', 'paso desconocido')
            descripcion = f"Progreso actualizado: {progress_percentage}% - {step_description}"
            detalles = {
                'progress_percentage': progress_percentage,
                'step_description': step_description
            }
        
        # Registrar actividad
        activity_log, error = self.log_activity_safe(
            cierre_id=data['cierre_id'],
            tarjeta=data['tarjeta'],
            accion=accion,
            descripcion=descripcion,
            usuario=request.user if request.user.is_authenticated else None,
            detalles=detalles,
            resultado='exito',
            ip_address=get_client_ip(request)
        )
        
        if error:
            return JsonResponse({'error': error}, status=500)
        
        return JsonResponse({
            'success': True,
            'activity_id': activity_log.id if activity_log else None,
            'message': f"Actividad '{accion}' registrada correctamente"
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_log(request, cierre_id, tarjeta):
    """
    Obtiene el log de actividades para un cierre y tarjeta específicos
    """
    try:
        from .models_logging import TarjetaActivityLogNomina
        
        logs = TarjetaActivityLogNomina.objects.filter(
            cierre_id=cierre_id,
            tarjeta=tarjeta
        ).order_by('-timestamp')
        
        # Limitar resultados
        limit = request.GET.get('limit', 100)
        try:
            limit = int(limit)
            if limit > 1000:
                limit = 1000
        except ValueError:
            limit = 100
        
        logs = logs[:limit]
        
        # Serializar logs
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'accion': log.accion,
                'descripcion': log.descripcion,
                'usuario': log.usuario.correo_bdo if log.usuario else None,
                'resultado': log.resultado,
                'detalles': log.detalles,
                'ip_address': log.ip_address,
                'upload_log_id': log.upload_log.id if log.upload_log else None
            })
        
        return Response({
            'success': True,
            'count': len(logs_data),
            'logs': logs_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs de actividad: {e}")
        return Response({
            'error': f"Error obteniendo logs: {str(e)}"
        }, status=500)
