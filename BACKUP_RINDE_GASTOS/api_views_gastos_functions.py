from contabilidad.tasks import procesar_captura_masiva_gastos_task

def get_redis_client_db1():
    """
    Obtiene cliente Redis para db1 usando la configuración de Django
    Con soporte UTF-8 completo
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=True,
            encoding='utf-8',
            encoding_errors='strict'
        )

def get_redis_client_db1_binary():
    """
    Obtiene cliente Redis para db1 para datos binarios (sin decode_responses)
    Con soporte UTF-8 para metadatos
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    if redis_password:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            password=redis_password, 
            decode_responses=False,
            encoding='utf-8'
        )
    else:
        return redis.Redis(
            host='redis', 
            port=6379, 
            db=1, 
            decode_responses=False,
            encoding='utf-8'
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def captura_masiva_gastos(request):
    """
    Endpoint para procesar archivos Excel de captura masiva de gastos
    """
    try:
        # Validar que se haya enviado un archivo
        if 'archivo' not in request.FILES:
            return Response({
                'error': 'No se encontró archivo en la petición'
            }, status=400)
        
        archivo = request.FILES['archivo']
        
        # Validar extensión del archivo
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'El archivo debe ser un Excel (.xlsx o .xls)'
            }, status=400)
        
        # Validar tamaño del archivo (máximo 10MB)
        if archivo.size > 10 * 1024 * 1024:
            return Response({
                'error': 'El archivo no puede ser mayor a 10MB'
            }, status=400)
        
        # Obtener mapeo de centros de costos si se proporciona
        mapeo_cc = {}
        if 'mapeo_cc' in request.POST:
            try:
                mapeo_cc = json.loads(request.POST['mapeo_cc'])
            except json.JSONDecodeError:
                return Response({
                    'error': 'El mapeo de centros de costos no tiene formato JSON válido'
                }, status=400)
        
        # Leer contenido del archivo
        archivo_content = archivo.read()
        
        # Disparar tarea de Celery
        task = procesar_captura_masiva_gastos_task.delay(
            archivo_content,
            archivo.name,
            request.user.id,
            mapeo_cc  # Pasar el mapeo de centros de costos
        )
        
        return Response({
            'task_id': task.id,
            'mensaje': 'Archivo enviado para procesamiento',
            'archivo_nombre': archivo.name,
            'estado': 'procesando'
        }, status=202)
        
    except Exception as e:
        return Response({
            'error': f'Error procesando archivo: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_captura_gastos(request, task_id):
    """
    Consultar el estado de una tarea de captura masiva de gastos
    """
    try:
        redis_client = get_redis_client_db1()
        
        # Obtener metadatos de la tarea - incluir usuario_id en la clave
        metadata_raw = redis_client.get(f"captura_gastos_meta:{request.user.id}:{task_id}")
        if not metadata_raw:
            return Response({
                'error': 'No se encontró información de la tarea'
            }, status=404)
        
        metadata = json.loads(metadata_raw)
        
        return Response(metadata)
        
    except Exception as e:
        return Response({
            'error': f'Error consultando estado: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def descargar_resultado_gastos(request, task_id):
    """
    Descargar el archivo Excel procesado
    """
    try:
        redis_client = get_redis_client_db1()
        
        # Verificar que la tarea esté completada - incluir usuario_id en la clave
        metadata_raw = redis_client.get(f"captura_gastos_meta:{request.user.id}:{task_id}")
        if not metadata_raw:
            return Response({
                'error': 'No se encontró información de la tarea'
            }, status=404)
        
        metadata = json.loads(metadata_raw)
        
        if metadata.get('estado') != 'completado':
            return Response({
