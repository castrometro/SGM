from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import datetime
import os

from ..models import ArchivoSubido
from ..serializers import ArchivoSubidoSerializer, ArchivoUploadSerializer
from ..config.archivo_config import ArchivoConfig


class ArchivoSubidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los archivos subidos.
    Incluye funcionalidades de upload y procesamiento.
    """
    queryset = ArchivoSubido.objects.all()
    serializer_class = ArchivoSubidoSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por cierre si se proporciona
        cierre_id = self.request.query_params.get('cierre', None)
        if cierre_id:
            queryset = queryset.filter(cierre_id=cierre_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Endpoint universal para subir archivos de payroll.
        
        Funcionalidades:
        1. Reemplaza archivo existente del mismo tipo (elimina BD + storage)
        2. Valida archivo según configuración del tipo
        3. Genera nomenclatura específica por tipo
        4. Guarda con estructura organizada
        """
        # Validaciones manuales básicas
        cierre_id = request.data.get('cierre')
        tipo_archivo = request.data.get('tipo_archivo')
        archivo = request.FILES.get('archivo')
        
        if not all([cierre_id, tipo_archivo, archivo]):
            return Response({
                'success': False,
                'error': 'Faltan parámetros requeridos',
                'codigo_error': 'MISSING_PARAMS',
                'detalles': {
                    'requeridos': ['cierre', 'tipo_archivo', 'archivo'],
                    'recibidos': {
                        'cierre': bool(cierre_id),
                        'tipo_archivo': bool(tipo_archivo),
                        'archivo': bool(archivo)
                    }
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener el cierre
            from ..models import CierrePayroll
            cierre = CierrePayroll.objects.get(id=cierre_id)
        except CierrePayroll.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Cierre no encontrado',
                'codigo_error': 'CIERRE_NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar estado del cierre
        if cierre.estado in ['cerrado', 'error']:
            return Response({
                'success': False,
                'error': f'No se pueden subir archivos. El cierre está en estado: {cierre.get_estado_display()}',
                'codigo_error': 'INVALID_CIERRE_STATE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar extensión del archivo
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = archivo.name.lower().split('.')[-1]
        if f".{file_extension}" not in allowed_extensions:
            return Response({
                'success': False,
                'error': f'Extensión de archivo no permitida. Extensiones permitidas: {allowed_extensions}',
                'codigo_error': 'INVALID_EXTENSION'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar tamaño del archivo
        max_size = 50 * 1024 * 1024  # 50MB
        if archivo.size > max_size:
            return Response({
                'success': False,
                'error': 'El archivo es demasiado grande. Tamaño máximo permitido: 50MB',
                'codigo_error': 'FILE_TOO_LARGE'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Validar archivo según configuración (incluyendo formato de nombre)
            is_valid, validation_errors = ArchivoConfig.validate_file(archivo, tipo_archivo, cierre)
            if not is_valid:
                return Response({
                    'success': False,
                    'error': 'Archivo no válido',
                    'codigo_error': 'INVALID_FILE',
                    'detalles': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. REEMPLAZAR archivo existente del mismo tipo si existe
            archivo_existente = ArchivoSubido.objects.filter(
                cierre=cierre, 
                tipo_archivo=tipo_archivo
            ).first()
            
            # 3. Generar nomenclatura específica y ruta
            file_ext = os.path.splitext(archivo.name)[1].lower()
            upload_path = ArchivoConfig.get_upload_path(cierre, tipo_archivo, file_ext)
            
            if archivo_existente:
                # ACTUALIZAR archivo existente en lugar de eliminar y crear
                print(f"🔄 Actualizando archivo existente: {archivo_existente.nombre_original}")
                
                # Eliminar archivo físico anterior
                if archivo_existente.archivo:
                    try:
                        if archivo_existente.archivo.storage.exists(archivo_existente.archivo.name):
                            archivo_existente.archivo.storage.delete(archivo_existente.archivo.name)
                            print(f"�️ Archivo físico anterior eliminado: {archivo_existente.archivo.name}")
                    except Exception as e:
                        print(f"❌ Error eliminando archivo físico anterior: {e}")
                
                # Actualizar campos del archivo existente
                archivo_existente.nombre_original = archivo.name
                archivo_existente.tamaño = archivo.size
                archivo_existente.estado = 'subido'
                archivo_existente.fecha_subida = timezone.now()
                archivo_existente.registros_procesados = 0
                archivo_existente.errores_detectados = 0
                archivo_existente.log_errores = []
                archivo_existente.metadatos = {}
                archivo_existente.hash_md5 = ''  # Se calculará en save()
                
                # Asignar nuevo archivo
                archivo_existente.archivo.save(
                    os.path.basename(upload_path),
                    archivo,
                    save=False
                )
                
                # Guardar cambios (esto calculará el hash)
                archivo_existente.save()
                nuevo_archivo = archivo_existente
                archivo_reemplazado = True
                
            else:
                # 4. Crear nuevo archivo si no existe uno previo
                nuevo_archivo = ArchivoSubido(
                    cierre=cierre,
                    tipo_archivo=tipo_archivo,
                    nombre_original=archivo.name,
                    tamaño=archivo.size,
                    estado='subido'
                )
                
                # Asignar archivo con la ruta personalizada
                nuevo_archivo.archivo.save(
                    os.path.basename(upload_path),  # Solo el nombre del archivo
                    archivo,
                    save=False  # No guardar aún, lo haremos después de calcular hash
                )
                
                # 5. Calcular hash y guardar
                nuevo_archivo.save()  # Esto ejecutará el método save() que calcula el hash
                archivo_reemplazado = False
            
            # 6. Actualizar estado del cierre si es necesario
            if cierre.estado == 'pendiente':
                cierre.estado = 'archivos_subidos'
                cierre.save()
            
            # 7. Respuesta exitosa (el procesamiento se dispara automáticamente via signal)
            respuesta_data = {
                'success': True,
                'archivo': {
                    'id': nuevo_archivo.id,
                    'tipo_archivo': nuevo_archivo.tipo_archivo,
                    'nombre_original': nuevo_archivo.nombre_original,
                    'estado': nuevo_archivo.estado,
                    'fecha_subida': nuevo_archivo.fecha_subida,
                    'tamaño': nuevo_archivo.tamaño,
                    'url': nuevo_archivo.archivo.url if nuevo_archivo.archivo else None
                },
                'mensaje': f'Archivo {tipo_archivo} {"reemplazado" if archivo_reemplazado else "subido"} exitosamente',
                'archivo_reemplazado': archivo_reemplazado
            }
            
            # Indicar que el procesamiento se iniciará automáticamente para libro_remuneraciones
            if tipo_archivo == 'libro_remuneraciones':
                respuesta_data['procesamiento'] = {
                    'iniciado': True,
                    'automatico': True,
                    'mensaje': 'Procesamiento se iniciará automáticamente'
                }
            
            return Response(respuesta_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Manejo de errores inesperados
            return Response({
                'success': False,
                'error': 'Error interno del servidor',
                'codigo_error': 'INTERNAL_ERROR',
                'detalles': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def verificar_existencia(self, request):
        """
        Verifica si existe un archivo específico para un cierre y tipo.
        
        Parámetros GET requeridos:
        - cierre_id: ID del cierre
        - tipo_archivo: Tipo de archivo a verificar
        
        Respuesta:
        - exists: bool - Si el archivo existe
        - archivo: dict - Información del archivo si existe
        """
        cierre_id = request.query_params.get('cierre_id')
        tipo_archivo = request.query_params.get('tipo_archivo')
        
        # Validar parámetros requeridos
        if not cierre_id:
            return Response({
                'success': False,
                'error': 'Parámetro cierre_id requerido',
                'codigo_error': 'MISSING_CIERRE_ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not tipo_archivo:
            return Response({
                'success': False,
                'error': 'Parámetro tipo_archivo requerido',
                'codigo_error': 'MISSING_TIPO_ARCHIVO'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el tipo de archivo es válido
        tipos_validos = [choice[0] for choice in ArchivoSubido.TIPOS_ARCHIVO]
        if tipo_archivo not in tipos_validos:
            return Response({
                'success': False,
                'error': f'Tipo de archivo inválido: {tipo_archivo}',
                'codigo_error': 'INVALID_TIPO_ARCHIVO',
                'tipos_validos': tipos_validos
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Buscar el archivo
            archivo = ArchivoSubido.objects.filter(
                cierre_id=cierre_id,
                tipo_archivo=tipo_archivo
            ).first()
            
            if archivo:
                # El archivo existe
                return Response({
                    'success': True,
                    'exists': True,
                    'archivo': {
                        'id': archivo.id,
                        'tipo_archivo': archivo.tipo_archivo,
                        'nombre_original': archivo.nombre_original,
                        'estado': archivo.estado,
                        'fecha_subida': archivo.fecha_subida,
                        'tamaño': archivo.tamaño,
                        'url': archivo.archivo.url if archivo.archivo else None,
                        'hash_md5': archivo.hash_md5,
                        'registros_procesados': archivo.registros_procesados,
                        'errores_detectados': archivo.errores_detectados
                    }
                })
            else:
                # El archivo no existe
                return Response({
                    'success': True,
                    'exists': False,
                    'archivo': None,
                    'mensaje': f'No existe archivo de tipo {tipo_archivo} para el cierre {cierre_id}'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Error al verificar existencia del archivo',
                'codigo_error': 'VERIFICATION_ERROR',
                'detalles': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """Inicia el procesamiento de un archivo"""
        archivo = self.get_object()
        
        if archivo.estado != 'subido':
            return Response(
                {'error': 'El archivo no está en estado para ser procesado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo.estado = 'procesando'
        archivo.fecha_procesamiento = datetime.now()
        archivo.save()
        
        # Aquí se llamaría a la tarea de Celery para procesar el archivo
        # from ..tasks import procesar_archivo_task
        # procesar_archivo_task.delay(archivo.id)
        
        return Response(ArchivoSubidoSerializer(archivo).data)
    
    @action(detail=True, methods=['get'])
    def verificar_integridad(self, request, pk=None):
        """Verifica la integridad del archivo mediante hash"""
        archivo = self.get_object()
        
        # Recalcular hash
        hash_actual = archivo.calcular_hash()
        
        es_integro = hash_actual == archivo.hash_md5
        
        return Response({
            'archivo_id': archivo.id,
            'hash_original': archivo.hash_md5,
            'hash_actual': hash_actual,
            'es_integro': es_integro
        })


@api_view(['GET'])
def verificar_existencia_archivo(request):
    """
    Vista independiente para verificar si existe un archivo específico.
    
    Parámetros GET requeridos:
    - cierre_id: ID del cierre
    - tipo_archivo: Tipo de archivo a verificar
    """
    cierre_id = request.query_params.get('cierre_id')
    tipo_archivo = request.query_params.get('tipo_archivo')
    
    # Validar parámetros requeridos
    if not cierre_id:
        return Response({
            'success': False,
            'error': 'Parámetro cierre_id requerido',
            'codigo_error': 'MISSING_CIERRE_ID'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not tipo_archivo:
        return Response({
            'success': False,
            'error': 'Parámetro tipo_archivo requerido',
            'codigo_error': 'MISSING_TIPO_ARCHIVO'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que el tipo de archivo es válido
    tipos_validos = [choice[0] for choice in ArchivoSubido.TIPOS_ARCHIVO]
    if tipo_archivo not in tipos_validos:
        return Response({
            'success': False,
            'error': f'Tipo de archivo inválido: {tipo_archivo}',
            'codigo_error': 'INVALID_TIPO_ARCHIVO',
            'tipos_validos': tipos_validos
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Buscar el archivo
        archivo = ArchivoSubido.objects.filter(
            cierre_id=cierre_id,
            tipo_archivo=tipo_archivo
        ).first()
        
        if archivo:
            # El archivo existe
            return Response({
                'success': True,
                'exists': True,
                'archivo': {
                    'id': archivo.id,
                    'tipo_archivo': archivo.tipo_archivo,
                    'nombre_original': archivo.nombre_original,
                    'estado': archivo.estado,
                    'estado_procesamiento': archivo.estado_procesamiento,
                    'fecha_subida': archivo.fecha_subida,
                    'tamaño': archivo.tamaño,
                    'url': archivo.archivo.url if archivo.archivo else None,
                    'hash_md5': archivo.hash_md5,
                    'registros_procesados': archivo.registros_procesados,
                    'errores_detectados': archivo.errores_detectados
                }
            })
        else:
            # El archivo no existe
            return Response({
                'success': True,
                'exists': False,
                'archivo': None,
                'mensaje': f'No existe archivo de tipo {tipo_archivo} para el cierre {cierre_id}'
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error al verificar existencia del archivo',
            'codigo_error': 'VERIFICATION_ERROR',
            'detalles': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def estado_procesamiento(self, request, pk=None):
        """
        Consulta el estado de procesamiento de un archivo específico.
        
        Para archivos del tipo libro_remuneraciones, incluye información 
        detallada sobre el progreso de las tareas CHAIN.
        """
        try:
            archivo = self.get_object()
            
            respuesta = {
                'success': True,
                'archivo': {
                    'id': archivo.id,
                    'tipo_archivo': archivo.tipo_archivo,
                    'estado': archivo.estado,
                    'estado_procesamiento': archivo.estado_procesamiento,
                    'registros_procesados': archivo.registros_procesados,
                    'errores_detectados': archivo.errores_detectados,
                    'fecha_subida': archivo.fecha_subida
                }
            }
            
            # Si es libro de remuneraciones, consultar estado de las tareas staging
            if archivo.tipo_archivo == 'libro_remuneraciones':
                try:
                    from ..models import ListaEmpleados_stg, ItemsRemuneraciones_stg, ValorItemEmpleado_stg
                    
                    # Contar registros en cada tabla staging
                    empleados_count = ListaEmpleados_stg.objects.filter(archivo_subido=archivo).count()
                    items_count = ItemsRemuneraciones_stg.objects.filter(archivo_subido=archivo).count()
                    valores_count = ValorItemEmpleado_stg.objects.filter(archivo_subido=archivo).count()
                    
                    respuesta['procesamiento'] = {
                        'empleados_extraidos': empleados_count,
                        'items_extraidos': items_count,
                        'valores_extraidos': valores_count,
                        'fase_completada': self._determinar_fase_completada(archivo, empleados_count, items_count, valores_count)
                    }
                    
                    # Información adicional según el estado
                    if archivo.estado == 'procesando':
                        respuesta['procesamiento']['mensaje'] = 'Procesamiento en curso...'
                    elif archivo.estado == 'procesado':
                        respuesta['procesamiento']['mensaje'] = 'Procesamiento completado exitosamente'
                    elif archivo.estado == 'error':
                        respuesta['procesamiento']['mensaje'] = 'Error durante el procesamiento'
                        if archivo.log_errores:
                            respuesta['procesamiento']['errores'] = archivo.log_errores
                    
                except Exception as e:
                    print(f"❌ Error consultando estado de staging: {e}")
                    respuesta['procesamiento'] = {
                        'error': 'No se pudo consultar el estado del procesamiento',
                        'detalle': str(e)
                    }
            
            return Response(respuesta)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Error al consultar estado de procesamiento',
                'codigo_error': 'PROCESSING_STATUS_ERROR',
                'detalles': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _determinar_fase_completada(self, archivo, empleados_count, items_count, valores_count):
        """
        Determina qué fase del procesamiento CHAIN se ha completado basándose en los datos staging.
        """
        if valores_count > 0:
            return 'valores_extraidos'  # Fase 3 completada (todo el CHAIN)
        elif empleados_count > 0:
            return 'empleados_extraidos'  # Fase 2 completada  
        elif items_count > 0:
            return 'headers_extraidos'   # Fase 1 completada
        else:
            return 'iniciando'  # No hay datos aún
