# PROPUESTA: SISTEMA DE INCIDENCIAS PRE-CALCULADAS CON CACHÉ Y LOGGING

## Resumen Ejecutivo

Implementar un sistema que:
1. **Pre-calcula incidencias** durante el procesamiento del libro mayor (no overhead adicional)
2. **Cachea resultados** en Redis con invalidación inteligente
3. **Mantiene historial completo** de reprocesamiento y evolución de incidencias
4. **Optimiza performance** eliminando cálculos on-the-fly

## Arquitectura Propuesta

### 1. Flujo de Procesamiento Optimizado

```python
# En tasks_libro_mayor.py - durante el procesamiento
def procesar_libro_mayor_chain():
    # Procesamiento normal mov por mov
    for movimiento in movimientos:
        procesar_movimiento(movimiento)
        
        # NUEVO: Detectar incidencias en tiempo real
        incidencias_detectadas = detectar_incidencias_movimiento(movimiento)
        acumular_incidencias(incidencias_detectadas)
    
    # NUEVO: Al final del procesamiento
    incidencias_consolidadas = consolidar_incidencias_detectadas()
    
    # Guardar en BD + Caché Redis
    guardar_incidencias_consolidadas(cierre_id, incidencias_consolidadas)
    cachear_incidencias_redis(cierre_id, incidencias_consolidadas)
    
    # Crear registro de historial
    crear_registro_procesamiento(cierre_id, incidencias_consolidadas)
```

### 2. Nuevo Modelo de Historial

```python
# models_incidencias.py
class HistorialProcesamientoLibroMayor(models.Model):
    cierre = models.ForeignKey('CierreContabilidad', on_delete=models.CASCADE)
    iteracion = models.PositiveIntegerField()  # 1, 2, 3...
    
    # Trigger del reprocesamiento
    TRIGGER_INICIAL = 'inicial'
    TRIGGER_TIPO_DOC = 'tipo_doc_actualizado'
    TRIGGER_CLASIFICACION = 'clasificacion_actualizada'
    TRIGGER_NOMBRES_INGLES = 'nombres_ingles_actualizado'
    TRIGGER_MANUAL = 'reproceso_manual'
    
    TRIGGER_CHOICES = [
        (TRIGGER_INICIAL, 'Procesamiento inicial'),
        (TRIGGER_TIPO_DOC, 'Tipos de documento actualizados'),
        (TRIGGER_CLASIFICACION, 'Clasificación actualizada'),
        (TRIGGER_NOMBRES_INGLES, 'Nombres en inglés actualizados'),
        (TRIGGER_MANUAL, 'Reprocesamiento manual'),
    ]
    
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Timing
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True)
    tiempo_procesamiento = models.DurationField(null=True)
    
    # Métricas del procesamiento
    movimientos_procesados = models.PositiveIntegerField()
    movimientos_con_cambios = models.PositiveIntegerField(default=0)
    
    # Incidencias
    incidencias_detectadas = models.JSONField(default=list)  # Snapshot completo
    incidencias_resueltas = models.JSONField(default=list)   # Qué se resolvió vs iteración anterior
    incidencias_nuevas = models.JSONField(default=list)      # Qué apareció nuevo
    
    # Estado del caché
    cache_key = models.CharField(max_length=100)
    cache_expires_at = models.DateTimeField()
    
    # Logs adicionales
    logs_procesamiento = models.JSONField(default=dict)
    notas = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-iteracion']
        indexes = [
            models.Index(fields=['cierre', 'iteracion']),
            models.Index(fields=['trigger']),
        ]

class SnapshotIncidenciasConsolidadas(models.Model):
    """Tabla de caché/snapshot de incidencias consolidadas"""
    cierre = models.OneToOneField('CierreContabilidad', on_delete=models.CASCADE)
    iteracion_actual = models.PositiveIntegerField()
    
    # Datos consolidados (lo que antes se calculaba on-the-fly)
    incidencias_consolidadas = models.JSONField()
    estadisticas = models.JSONField()
    total_elementos_afectados = models.PositiveIntegerField()
    
    # Metadatos
    fecha_calculo = models.DateTimeField(auto_now=True)
    tiempo_calculo = models.DurationField()  # Cuánto tardó en calcular
    hash_contenido = models.CharField(max_length=64)  # Para validar integridad
    
    # Cache info
    cache_key = models.CharField(max_length=100)
    cache_ttl = models.PositiveIntegerField(default=3600)  # 1 hora default
```

### 3. Sistema de Caché Redis Inteligente

```python
# services/cache_incidencias.py
import redis
import json
import hashlib
from django.conf import settings

class CacheIncidenciasService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_INCIDENCIAS_DB
        )
    
    def get_cache_key(self, cierre_id, iteracion=None):
        if iteracion:
            return f"incidencias:cierre:{cierre_id}:iter:{iteracion}"
        return f"incidencias:cierre:{cierre_id}:current"
    
    def cachear_incidencias(self, cierre_id, incidencias_data, ttl=3600):
        """Cachea incidencias con TTL inteligente"""
        cache_key = self.get_cache_key(cierre_id)
        
        # Serializar y comprimir si es necesario
        data_json = json.dumps(incidencias_data, default=str)
        content_hash = hashlib.sha256(data_json.encode()).hexdigest()
        
        cache_payload = {
            'data': incidencias_data,
            'hash': content_hash,
            'timestamp': timezone.now().isoformat(),
            'ttl': ttl
        }
        
        # Guardar en Redis
        self.redis_client.setex(
            cache_key, 
            ttl, 
            json.dumps(cache_payload, default=str)
        )
        
        return cache_key, content_hash
    
    def obtener_incidencias_cache(self, cierre_id):
        """Obtiene incidencias desde caché"""
        cache_key = self.get_cache_key(cierre_id)
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            try:
                payload = json.loads(cached_data)
                return payload['data'], payload['hash']
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None, None
    
    def invalidar_cache(self, cierre_id, patron_relacionado=None):
        """Invalida caché específico y relacionado"""
        # Invalidar caché principal
        cache_key = self.get_cache_key(cierre_id)
        self.redis_client.delete(cache_key)
        
        # Invalidar patrones relacionados
        if patron_relacionado:
            keys = self.redis_client.keys(f"incidencias:*{patron_relacionado}*")
            if keys:
                self.redis_client.delete(*keys)
    
    def get_cache_stats(self, cierre_id):
        """Estadísticas del caché"""
        cache_key = self.get_cache_key(cierre_id)
        ttl = self.redis_client.ttl(cache_key)
        exists = self.redis_client.exists(cache_key)
        
        return {
            'exists': bool(exists),
            'ttl': ttl if ttl > 0 else None,
            'key': cache_key
        }
```

### 4. Detector de Incidencias Optimizado

```python
# services/detector_incidencias.py
class DetectorIncidenciasOptimizado:
    def __init__(self, cierre_id):
        self.cierre_id = cierre_id
        self.incidencias_acumuladas = defaultdict(list)
        self.stats = {
            'movimientos_procesados': 0,
            'incidencias_detectadas': 0,
            'tiempo_deteccion': 0
        }
    
    def detectar_incidencias_movimiento(self, movimiento_data):
        """Detecta incidencias para un movimiento específico"""
        start_time = time.time()
        incidencias = []
        
        # Detección inline durante procesamiento
        if not movimiento_data.get('cuenta_clasificada'):
            incidencias.append({
                'tipo': Incidencia.CUENTA_NO_CLASIFICADA,
                'cuenta_codigo': movimiento_data.get('codigo_cuenta'),
                'descripcion': f"Cuenta {movimiento_data.get('codigo_cuenta')} sin clasificación"
            })
        
        if not movimiento_data.get('cuenta_nombre_ingles'):
            incidencias.append({
                'tipo': Incidencia.CUENTA_SIN_INGLES,
                'cuenta_codigo': movimiento_data.get('codigo_cuenta'),
                'descripcion': f"Cuenta {movimiento_data.get('codigo_cuenta')} sin traducción"
            })
        
        if not movimiento_data.get('tipo_documento_valido'):
            incidencias.append({
                'tipo': Incidencia.DOC_NO_RECONOCIDO,
                'tipo_doc_codigo': movimiento_data.get('tipo_doc'),
                'descripcion': f"Tipo documento {movimiento_data.get('tipo_doc')} no reconocido"
            })
        
        # Acumular para consolidación posterior
        for inc in incidencias:
            self.incidencias_acumuladas[inc['tipo']].append(inc)
        
        self.stats['movimientos_procesados'] += 1
        self.stats['incidencias_detectadas'] += len(incidencias)
        self.stats['tiempo_deteccion'] += time.time() - start_time
        
        return incidencias
    
    def consolidar_incidencias(self):
        """Consolida todas las incidencias detectadas"""
        incidencias_consolidadas = []
        
        for tipo, incidencias_list in self.incidencias_acumuladas.items():
            # Agrupar y consolidar como antes, pero con datos ya procesados
            consolidada = self._consolidar_tipo(tipo, incidencias_list)
            incidencias_consolidadas.append(consolidada)
        
        return {
            'incidencias': incidencias_consolidadas,
            'estadisticas': self._generar_estadisticas(),
            'total_elementos_afectados': sum(
                len(incs) for incs in self.incidencias_acumuladas.values()
            ),
            'stats_procesamiento': self.stats
        }
```

### 5. Endpoint Optimizado con Caché

```python
# views/incidencias.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_incidencias_consolidadas_optimizado(request, cierre_id):
    """
    Endpoint optimizado que usa caché Redis
    """
    cache_service = CacheIncidenciasService()
    
    # 1. Intentar obtener desde caché
    cached_data, content_hash = cache_service.obtener_incidencias_cache(cierre_id)
    
    if cached_data:
        # Cache hit - devolver datos cached
        cached_data['_cache_info'] = {
            'hit': True,
            'hash': content_hash,
            'source': 'redis'
        }
        return Response(cached_data)
    
    # 2. Cache miss - obtener desde snapshot en BD
    try:
        snapshot = SnapshotIncidenciasConsolidadas.objects.get(cierre=cierre_id)
        
        response_data = {
            'incidencias': snapshot.incidencias_consolidadas,
            'estadisticas': snapshot.estadisticas,
            'total_elementos_afectados': snapshot.total_elementos_afectados,
            'cierre_info': {
                'id': cierre_id,
                'iteracion': snapshot.iteracion_actual,
            },
            '_cache_info': {
                'hit': False,
                'source': 'database_snapshot',
                'calculado_en': snapshot.fecha_calculo
            }
        }
        
        # Volver a cachear en Redis
        cache_service.cachear_incidencias(cierre_id, response_data, ttl=1800)
        
        return Response(response_data)
        
    except SnapshotIncidenciasConsolidadas.DoesNotExist:
        # 3. Fallback - calcular on-the-fly (método anterior)
        return obtener_incidencias_consolidadas_libro_mayor(request, cierre_id)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reprocesar_libro_mayor_con_historial(request, cierre_id):
    """
    Endpoint para reprocesar con tracking completo
    """
    trigger = request.data.get('trigger', 'manual')
    notas = request.data.get('notas', '')
    
    # Crear registro de historial
    historial = HistorialProcesamientoLibroMayor.objects.create(
        cierre_id=cierre_id,
        iteracion=HistorialProcesamientoLibroMayor.objects.filter(
            cierre_id=cierre_id
        ).count() + 1,
        trigger=trigger,
        usuario=request.user,
        fecha_inicio=timezone.now(),
        notas=notas
    )
    
    # Invalidar caché antes del reprocesamiento
    cache_service = CacheIncidenciasService()
    cache_service.invalidar_cache(cierre_id)
    
    # Lanzar tarea de reprocesamiento
    from .tasks_libro_mayor import reprocesar_libro_mayor_con_tracking
    task = reprocesar_libro_mayor_con_tracking.delay(
        cierre_id, 
        historial.id,
        trigger
    )
    
    return Response({
        'mensaje': 'Reprocesamiento iniciado',
        'historial_id': historial.id,
        'task_id': task.id,
        'iteracion': historial.iteracion
    })
```

### 6. Tarea Celery Actualizada

```python
# tasks_libro_mayor.py
@shared_task
def reprocesar_libro_mayor_con_tracking(cierre_id, historial_id, trigger):
    """
    Tarea que reprocesa y mantiene historial completo
    """
    historial = HistorialProcesamientoLibroMayor.objects.get(id=historial_id)
    
    try:
        # Detector de incidencias
        detector = DetectorIncidenciasOptimizado(cierre_id)
        
        # Procesar movimientos
        movimientos = obtener_movimientos_cierre(cierre_id)
        
        for movimiento in movimientos:
            # Procesar movimiento + detectar incidencias inline
            procesar_movimiento_optimizado(movimiento, detector)
        
        # Consolidar incidencias
        resultado_consolidacion = detector.consolidar_incidencias()
        
        # Comparar con iteración anterior para detectar cambios
        iteracion_anterior = HistorialProcesamientoLibroMayor.objects.filter(
            cierre_id=cierre_id,
            iteracion__lt=historial.iteracion
        ).order_by('-iteracion').first()
        
        cambios = calcular_cambios_incidencias(
            resultado_consolidacion,
            iteracion_anterior.incidencias_detectadas if iteracion_anterior else []
        )
        
        # Actualizar historial
        historial.fecha_fin = timezone.now()
        historial.tiempo_procesamiento = historial.fecha_fin - historial.fecha_inicio
        historial.movimientos_procesados = detector.stats['movimientos_procesados']
        historial.incidencias_detectadas = resultado_consolidacion['incidencias']
        historial.incidencias_resueltas = cambios['resueltas']
        historial.incidencias_nuevas = cambios['nuevas']
        historial.logs_procesamiento = detector.stats
        historial.save()
        
        # Crear/actualizar snapshot
        snapshot, created = SnapshotIncidenciasConsolidadas.objects.get_or_create(
            cierre_id=cierre_id,
            defaults={
                'iteracion_actual': historial.iteracion,
                'incidencias_consolidadas': resultado_consolidacion['incidencias'],
                'estadisticas': resultado_consolidacion['estadisticas'],
                'total_elementos_afectados': resultado_consolidacion['total_elementos_afectados'],
                'tiempo_calculo': historial.tiempo_procesamiento,
                'hash_contenido': hashlib.sha256(
                    json.dumps(resultado_consolidacion, default=str).encode()
                ).hexdigest()
            }
        )
        
        if not created:
            # Actualizar snapshot existente
            snapshot.iteracion_actual = historial.iteracion
            snapshot.incidencias_consolidadas = resultado_consolidacion['incidencias']
            snapshot.estadisticas = resultado_consolidacion['estadisticas']
            snapshot.total_elementos_afectados = resultado_consolidacion['total_elementos_afectados']
            snapshot.tiempo_calculo = historial.tiempo_procesamiento
            snapshot.save()
        
        # Cachear en Redis
        cache_service = CacheIncidenciasService()
        cache_key, content_hash = cache_service.cachear_incidencias(
            cierre_id, 
            resultado_consolidacion,
            ttl=determine_cache_ttl(trigger)  # TTL dinámico según trigger
        )
        
        snapshot.cache_key = cache_key
        snapshot.save()
        
        return {
            'status': 'success',
            'historial_id': historial.id,
            'incidencias_detectadas': len(resultado_consolidacion['incidencias']),
            'cambios': cambios,
            'cache_key': cache_key
        }
        
    except Exception as e:
        historial.fecha_fin = timezone.now()
        historial.logs_procesamiento = {'error': str(e)}
        historial.save()
        raise
```

## Beneficios de la Propuesta

### Performance
- **0 overhead** en detección (se hace durante procesamiento normal)
- **Respuesta instantánea** desde caché Redis (< 10ms)
- **Fallback robusto** con snapshot en BD

### Visibilidad
- **Historial completo** de cada reprocesamiento
- **Tracking de cambios** entre iteraciones
- **Métricas detalladas** de performance

### Escalabilidad
- **Caché inteligente** con TTL dinámico
- **Invalidación selectiva** por triggers
- **Compresión automática** para datasets grandes

### Auditabilidad
- **Log completo** de quién hizo qué y cuándo
- **Comparación** entre iteraciones
- **Rastreabilidad** de mejoras por analista

## Implementación Gradual

### Fase 1 (1-2 semanas)
1. Crear modelos de historial y snapshot
2. Implementar detector inline básico
3. Sistema de caché Redis simple

### Fase 2 (1 semana)
1. Endpoint optimizado con caché
2. Tarea Celery con tracking
3. Interface de reprocesamiento

### Fase 3 (1 semana)
1. Dashboard de historial
2. Métricas y analytics
3. Optimizaciones avanzadas

¿Te gusta esta propuesta? ¿Quieres que empiece implementando alguna parte específica?
