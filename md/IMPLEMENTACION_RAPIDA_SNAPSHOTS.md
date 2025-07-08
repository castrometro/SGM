# IMPLEMENTACIÓN RÁPIDA: SNAPSHOTS DE INCIDENCIAS POR INTENTOS

## Lo que YA tenemos disponible:

### 1. **UploadLog** (modelo existente)
- Ya tiene `cierre` (FK)
- Ya tiene `resumen` (JSONField) 
- Ya tiene `tiempo_procesamiento`
- Ya tiene `estado` y tracking completo

### 2. **IncidenciaResumen** (modelo existente)
- Ya tiene `upload_log` (FK)
- Ya tiene `elementos_afectados` (JSONField)
- Ya tiene `estadisticas` (JSONField)
- Ya tiene `cantidad_afectada`

## PROPUESTA MINIMALISTA (30 minutos implementación):

### Paso 1: Agregar campo `iteracion` a UploadLog
```python
# En models.py - agregar campo a UploadLog existente
class UploadLog(models.Model):
    # ... campos existentes ...
    
    # NUEVO CAMPO
    iteracion = models.PositiveIntegerField(
        default=1, 
        help_text="Número de iteración de procesamiento para este cierre"
    )
    
    # ... resto igual ...
    
    class Meta:
        # ... meta existente ...
        indexes = [
            # ... indexes existentes ...
            models.Index(fields=['cierre', 'tipo_upload', 'iteracion']),  # NUEVO
        ]
```

### Paso 2: Modificar tasks_libro_mayor.py para auto-incrementar iteración
```python
# En tasks_libro_mayor.py
def procesar_libro_mayor_chain(upload_log_id):
    upload_log = UploadLog.objects.get(id=upload_log_id)
    
    # NUEVO: Calcular iteración automáticamente
    if upload_log.cierre:
        iteracion_anterior = UploadLog.objects.filter(
            cierre=upload_log.cierre,
            tipo_upload='libro_mayor',
            estado='completado'
        ).count()
        
        upload_log.iteracion = iteracion_anterior + 1
        upload_log.save()
    
    # ... resto del procesamiento normal ...
    
    # Al final, ANTES de guardar las incidencias:
    incidencias_snapshot = {
        'iteracion': upload_log.iteracion,
        'timestamp': timezone.now().isoformat(),
        'incidencias_detectadas': resultado_incidencias,
        'comparacion_anterior': comparar_con_iteracion_anterior(upload_log)
    }
    
    # Guardar en el campo resumen existente
    upload_log.resumen['incidencias_snapshot'] = incidencias_snapshot
    upload_log.save()
```

### Paso 3: Endpoint optimizado usando UploadLog existente
```python
# En views/incidencias.py
@api_view(['GET'])
def obtener_incidencias_consolidadas_snapshot(request, cierre_id):
    try:
        # Obtener último UploadLog de libro mayor para este cierre
        ultimo_upload = UploadLog.objects.filter(
            cierre_id=cierre_id,
            tipo_upload='libro_mayor',
            estado='completado'
        ).order_by('-iteracion').first()
        
        if not ultimo_upload or not ultimo_upload.resumen:
            # Fallback al método actual
            return obtener_incidencias_consolidadas_libro_mayor(request, cierre_id)
        
        # Usar snapshot si existe
        snapshot = ultimo_upload.resumen.get('incidencias_snapshot')
        if snapshot:
            return Response({
                'incidencias': snapshot['incidencias_detectadas'],
                'estadisticas': snapshot.get('estadisticas', {}),
                'iteracion_info': {
                    'numero': ultimo_upload.iteracion,
                    'fecha': snapshot['timestamp'],
                    'upload_log_id': ultimo_upload.id
                },
                '_source': 'snapshot'
            })
        
        # Fallback
        return obtener_incidencias_consolidadas_libro_mayor(request, cierre_id)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def obtener_historial_incidencias(request, cierre_id):
    """NUEVO: Historial de todas las iteraciones"""
    uploads = UploadLog.objects.filter(
        cierre_id=cierre_id,
        tipo_upload='libro_mayor',
        estado='completado'
    ).order_by('-iteracion')
    
    historial = []
    for upload in uploads:
        snapshot = upload.resumen.get('incidencias_snapshot', {}) if upload.resumen else {}
        
        historial.append({
            'iteracion': upload.iteracion,
            'fecha': upload.fecha_subida,
            'tiempo_procesamiento': upload.tiempo_procesamiento.total_seconds() if upload.tiempo_procesamiento else None,
            'usuario': upload.usuario.nombre if upload.usuario else None,
            'total_incidencias': len(snapshot.get('incidencias_detectadas', [])),
            'archivo': upload.nombre_archivo_original,
            'comparacion': snapshot.get('comparacion_anterior', {}),
            'upload_log_id': upload.id
        })
    
    return Response({
        'historial': historial,
        'total_iteraciones': len(historial)
    })
```

### Paso 4: Función comparar iteraciones
```python
# Función helper
def comparar_con_iteracion_anterior(upload_log_actual):
    if upload_log_actual.iteracion <= 1:
        return {'es_primera_iteracion': True}
    
    upload_anterior = UploadLog.objects.filter(
        cierre=upload_log_actual.cierre,
        tipo_upload='libro_mayor',
        iteracion=upload_log_actual.iteracion - 1,
        estado='completado'
    ).first()
    
    if not upload_anterior or not upload_anterior.resumen:
        return {'anterior_no_encontrada': True}
    
    incidencias_anteriores = upload_anterior.resumen.get('incidencias_snapshot', {}).get('incidencias_detectadas', [])
    incidencias_actuales = # ... las que acabamos de calcular
    
    # Comparación simple por tipo
    tipos_anteriores = {inc['tipo_codigo']: inc['cantidad_afectada'] for inc in incidencias_anteriores}
    tipos_actuales = {inc['tipo_codigo']: inc['cantidad_afectada'] for inc in incidencias_actuales}
    
    cambios = {
        'resueltas': [],
        'nuevas': [],
        'empeoradas': [],
        'mejoradas': []
    }
    
    for tipo, cantidad_actual in tipos_actuales.items():
        cantidad_anterior = tipos_anteriores.get(tipo, 0)
        
        if cantidad_anterior > cantidad_actual:
            cambios['mejoradas'].append({
                'tipo': tipo,
                'anterior': cantidad_anterior,
                'actual': cantidad_actual,
                'diferencia': cantidad_anterior - cantidad_actual
            })
        elif cantidad_anterior < cantidad_actual:
            cambios['empeoradas'].append({
                'tipo': tipo,
                'anterior': cantidad_anterior,
                'actual': cantidad_actual,
                'diferencia': cantidad_actual - cantidad_anterior
            })
    
    # Tipos que desaparecieron completamente
    for tipo, cantidad_anterior in tipos_anteriores.items():
        if tipo not in tipos_actuales:
            cambios['resueltas'].append({
                'tipo': tipo,
                'cantidad_resuelta': cantidad_anterior
            })
    
    return cambios
```

### Paso 5: URLs
```python
# En urls.py - agregar
path("libro-mayor/<int:cierre_id>/incidencias-snapshot/", 
     obtener_incidencias_consolidadas_snapshot, 
     name="incidencias_snapshot"),
path("libro-mayor/<int:cierre_id>/historial-incidencias/", 
     obtener_historial_incidencias, 
     name="historial_incidencias"),
```

## RESULTADO:

Con esta implementación MINIMALISTA tendrías:

1. **Snapshots automáticos** en cada procesamiento (guardados en `UploadLog.resumen`)
2. **Historial completo** de iteraciones por cierre
3. **Comparación automática** entre iteraciones
4. **Reutilización total** de modelos existentes
5. **Fallback robusto** al método actual

**Tiempo estimado: 30-45 minutos de implementación**

¿Te parece esta aproximación minimalista? ¿Empiezo por el campo `iteracion` en UploadLog?
