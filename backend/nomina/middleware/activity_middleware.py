# backend/nomina/middleware/activity_middleware.py
"""
Middleware para captura automática de actividades
Intercepta requests específicos y registra automáticamente
"""

import json
import time
from django.utils.deprecation import MiddlewareMixin
from nomina.models import ActivityEvent


class ActivityCaptureMiddleware(MiddlewareMixin):
    """
    Middleware que captura automáticamente actividades relevantes
    Se enfoca en endpoints específicos de nómina/contabilidad
    """
    
    # Mapeo de URLs a eventos
    URL_EVENT_MAP = {
        # Nómina - Uploads
        '/api/nomina/cierres/': {
            'POST': ('nomina', 'cierre_general', 'create_cierre'),
        },
        '/api/nomina/libro/': {
            'POST': ('nomina', 'libro_remuneraciones', 'file_upload'),
        },
        '/api/nomina/movimientos/': {
            'POST': ('nomina', 'movimientos_mes', 'file_upload'),
        },
        '/api/nomina/ingresos/': {
            'POST': ('nomina', 'archivos_analista', 'ingresos_upload'),
        },
        '/api/nomina/finiquitos/': {
            'POST': ('nomina', 'archivos_analista', 'finiquitos_upload'),
        },
        '/api/nomina/ausentismos/': {
            'POST': ('nomina', 'archivos_analista', 'ausentismos_upload'),
        },
        
        # Nómina - Estado
        '/api/nomina/cierres/{id}/actualizar-estado/': {
            'POST': ('nomina', 'cierre_general', 'update_state'),
        },
        '/api/nomina/cierres/{id}/consolidar-datos/': {
            'POST': ('nomina', 'cierre_general', 'consolidate_data'),
        },
        
        # Contabilidad (futuro)
        '/api/contabilidad/libro-mayor/': {
            'POST': ('contabilidad', 'libro_mayor', 'file_upload'),
        },
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Marcar tiempo de inicio
        request._activity_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Procesa la respuesta para determinar si loggear actividad"""
        
        # Solo procesar si el logging está habilitado
        if not getattr(self, 'enabled', True):
            return response
            
        # Solo requests autenticados
        if not request.user or not request.user.is_authenticated:
            return response
            
        # Buscar si esta URL debe ser loggeada
        event_config = self._match_url_to_event(request.path, request.method)
        if not event_config:
            return response
            
        # Extraer cierre_id del request
        cierre_id = self._extract_cierre_id(request)
        if not cierre_id:
            return response
            
        # Determinar resultado basado en status code
        if response.status_code < 400:
            resultado = 'ok'
        elif response.status_code >= 500:
            resultado = 'error'
        else:
            resultado = 'error'
            
        # Construir datos del evento
        modulo, seccion, evento = event_config
        datos = {
            'status_code': response.status_code,
            'method': request.method,
            'path': request.path,
        }
        
        # Agregar datos específicos según el tipo de evento
        if 'upload' in evento:
            datos.update(self._extract_file_info(request))
        elif 'state' in evento:
            datos.update(self._extract_state_info(request, response))
            
        # Agregar tiempo de procesamiento
        if hasattr(request, '_activity_start_time'):
            datos['duration_ms'] = int((time.time() - request._activity_start_time) * 1000)
        
        # Registrar la actividad usando ActivityEvent V2
        try:
            ActivityEvent.log(
                user=request.user,
                cliente=getattr(request, 'cliente', None) or self._extract_cliente_from_request(request),
                event_type=modulo,
                action=evento,
                resource_type=seccion,
                resource_id=str(cierre_id) if cierre_id else '',
                details=datos,
                request=request
            )
        except Exception as e:
            # No queremos que falle el request si el logging falla
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error logging activity: {e}")
        
        return response
    
    def _match_url_to_event(self, path, method):
        """Busca si la URL coincide con algún patrón a loggear"""
        for url_pattern, methods in self.URL_EVENT_MAP.items():
            if method in methods:
                # Matching simple por ahora - se puede mejorar con regex
                if '{id}' in url_pattern:
                    # Pattern con ID - hacer matching más flexible
                    pattern_parts = url_pattern.split('/')
                    path_parts = path.split('/')
                    if len(pattern_parts) == len(path_parts):
                        match = True
                        for i, part in enumerate(pattern_parts):
                            if part != '{id}' and part != path_parts[i]:
                                match = False
                                break
                        if match:
                            return methods[method]
                else:
                    # Matching exacto
                    if path.startswith(url_pattern.rstrip('/')):
                        return methods[method]
        return None
    
    def _extract_cierre_id(self, request):
        """Extrae cierre_id del request (URL params, POST data, etc.)"""
        # Intentar desde URL path
        path_parts = request.path.split('/')
        try:
            # Buscar patrón /cierres/{id}/
            if 'cierres' in path_parts:
                cierre_idx = path_parts.index('cierres')
                if len(path_parts) > cierre_idx + 1:
                    return int(path_parts[cierre_idx + 1])
        except (ValueError, IndexError):
            pass
            
        # Intentar desde POST data
        if request.method == 'POST':
            try:
                # Solo usar request.data (parseado por DRF)
                # NO acceder a request.body porque el stream ya fue leído
                if hasattr(request, 'data') and 'cierre_id' in request.data:
                    return int(request.data['cierre_id'])
            except (ValueError, KeyError, AttributeError):
                pass
                
        # Intentar desde query params
        return request.GET.get('cierre_id')
    
    def _extract_file_info(self, request):
        """Extrae información de archivos subidos"""
        file_info = {}
        if request.FILES:
            for field_name, file_obj in request.FILES.items():
                file_info.update({
                    'file_field': field_name,
                    'filename': file_obj.name,
                    'file_size': file_obj.size,
                    'content_type': file_obj.content_type,
                })
                break  # Solo el primer archivo por simplicidad
        return file_info
    
    def _extract_state_info(self, request, response):
        """Extrae información de cambios de estado"""
        state_info = {}
        try:
            if response.content:
                data = json.loads(response.content)
                if 'estado_anterior' in data and 'estado_nuevo' in data:
                    state_info.update({
                        'old_state': data['estado_anterior'],
                        'new_state': data['estado_nuevo'],
                        'state_changed': data.get('cambio_estado', False),
                    })
        except (json.JSONDecodeError, KeyError):
            pass
        return state_info
    
    def _extract_cliente_from_request(self, request):
        """Intenta extraer el cliente del request"""
        from api.models import Cliente
        
        # Intentar obtener cliente_id de diferentes lugares
        cliente_id = None
        
        # 1. Query params
        cliente_id = request.GET.get('cliente_id')
        
        # 2. POST data
        if not cliente_id and request.method == 'POST':
            try:
                if hasattr(request, 'data'):
                    cliente_id = request.data.get('cliente_id')
                elif request.POST:
                    cliente_id = request.POST.get('cliente_id')
            except:
                pass
        
        # 3. Si hay cierre_id, sacar cliente de ahí
        if not cliente_id:
            cierre_id = self._extract_cierre_id(request)
            if cierre_id:
                try:
                    from nomina.models import CierreNomina
                    cierre = CierreNomina.objects.select_related('cliente').get(id=cierre_id)
                    return cierre.cliente
                except:
                    pass
        
        # Intentar obtener el cliente
        if cliente_id:
            try:
                return Cliente.objects.get(id=cliente_id)
            except:
                pass
        
        # Fallback: primer cliente del usuario (para testing)
        try:
            return request.user.clientes.first()
        except:
            return None


class ActivityToggleMixin:
    """Mixin para habilitar/deshabilitar logging fácilmente"""
    
    @classmethod
    def enable_activity_logging(cls):
        """Habilita el logging de actividad"""
        ActivityCaptureMiddleware.enabled = True
        
    @classmethod  
    def disable_activity_logging(cls):
        """Deshabilita el logging de actividad"""
        ActivityCaptureMiddleware.enabled = False