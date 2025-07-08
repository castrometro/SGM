# IMPACTO DE AGREGAR CAMPO `iteracion` A UploadLog

## Análisis de Uso Actual

### 1. **Queries Existentes que NO se afectan**
```python
# La mayoría son por ID específico o por cliente/tipo - NO IMPACTO
UploadLog.objects.get(pk=upload_log_id)  # ✅ Sin impacto
UploadLog.objects.filter(cliente=cliente)  # ✅ Sin impacto  
UploadLog.objects.filter(tipo_upload="libro_mayor")  # ✅ Sin impacto
```

### 2. **Queries que PODRÍAN necesitar ajuste**
```python
# En views/cliente.py línea 562
ultimo_upload = UploadLog.objects.filter(
    cliente=cliente, tipo_upload="nombres_ingles"
).order_by("-fecha_subida").first()

# En utils/procesamiento_incidencias.py línea 181  
libro_mayor_logs = UploadLog.objects.filter(
    cierre=upload_log_tarjeta.cierre,
    tipo_upload='libro_mayor',
    estado='completado'
).order_by('-fecha_subida')  # ⚠️ Podría cambiar comportamiento
```

## IMPACTOS ESPECÍFICOS:

### 1. **PROBLEMA POTENCIAL**: Múltiples UploadLog para mismo cierre
```python
# ANTES: Un cierre = Un UploadLog de libro_mayor
cierre_95 -> UploadLog(id=123, libro_mayor)

# DESPUÉS: Un cierre = Múltiples UploadLog de libro_mayor (por iteraciones)  
cierre_95 -> UploadLog(id=123, libro_mayor, iteracion=1)
cierre_95 -> UploadLog(id=124, libro_mayor, iteracion=2) 
cierre_95 -> UploadLog(id=125, libro_mayor, iteracion=3)
```

### 2. **Frontend LibroMayorCard**: Actualmente espera UN upload log
```javascript
// En LibroMayorCard.jsx - línea 49
const data = await obtenerLibrosMayor(cierreId);
const ultimo = data && data.length > 0 ? data[data.length - 1] : null;
```

### 3. **API obtenerLibrosMayor**: Puede devolver múltiples registros ahora
```python
# Probablemente en views/libro_mayor.py
def obtener_libros_mayor(cierre_id):
    return LibroMayorArchivo.objects.filter(cierre_id=cierre_id)
    # ¿Devuelve múltiples si hay varias iteraciones?
```

## SOLUCIONES PROPUESTAS:

### **Opción A: Conservativa (RECOMENDADA)**
Crear nuevo campo sin afectar flujo actual:

```python
class UploadLog(models.Model):
    # ... campos existentes ...
    
    iteracion = models.PositiveIntegerField(
        default=1,
        help_text="Número de iteración para reprocesamiento"
    )
    es_iteracion_principal = models.BooleanField(
        default=True,
        help_text="Marca si es la iteración principal visible al usuario"
    )
    
    class Meta:
        # ... meta existente ...
        indexes = [
            # ... existentes ...
            models.Index(fields=['cierre', 'tipo_upload', 'iteracion']),
            models.Index(fields=['cierre', 'tipo_upload', 'es_iteracion_principal']),
        ]
```

### **Opción B: Queries actualizados**
```python
# Actualizar queries problemáticos para usar última iteración
def obtener_ultimo_upload_log_libro_mayor(cierre_id):
    return UploadLog.objects.filter(
        cierre_id=cierre_id,
        tipo_upload='libro_mayor',
        estado='completado'
    ).order_by('-iteracion').first()  # ⚠️ CAMBIO

# Mantener compatibilidad en frontend
def obtener_libros_mayor(cierre_id):
    # Devolver solo la iteración principal o la última
    ultimo = obtener_ultimo_upload_log_libro_mayor(cierre_id)
    return [ultimo] if ultimo else []
```

### **Opción C: Modelo separado (Menos invasivo)**
```python
class HistorialProcesamientoLibroMayor(models.Model):
    upload_log_principal = models.ForeignKey(UploadLog, on_delete=models.CASCADE)
    iteracion = models.PositiveIntegerField()
    snapshot_incidencias = models.JSONField()
    # ... otros campos del historial
    
    class Meta:
        unique_together = ('upload_log_principal', 'iteracion')
```

## RECOMENDACIÓN FINAL:

### **IMPLEMENTACIÓN GRADUAL Y SEGURA:**

1. **Fase 1: Agregar campos sin romper nada**
   - Agregar `iteracion` con default=1
   - Agregar `es_iteracion_principal` con default=True
   - **TODOS los UploadLog existentes mantienen funcionalidad**

2. **Fase 2: Implementar lógica de iteraciones**
   - Solo para nuevos procesamientos de libro mayor
   - Frontend y APIs existentes siguen funcionando igual

3. **Fase 3: Optimizar queries gradualmente**
   - Actualizar solo las queries que necesiten acceso a iteraciones
   - Mantener compatibilidad hacia atrás

### **¿Dónde hay que hacer cambios mínimos?**

1. **views/cliente.py línea 562**: Cambiar a orden por iteración para libro_mayor
2. **utils/procesamiento_incidencias.py**: Usar última iteración 
3. **Frontend**: Podría mostrar número de iteración como info adicional

### **¿Qué NO se afecta?**
- Todas las demás tarjetas (tipo_documento, clasificacion, nombres_ingles)
- Queries por ID específico
- Queries por cliente/tipo que no sean libro_mayor
- El 95% del código existente

¿Te parece bien esta aproximación conservativa? Empezaría por agregar los campos sin cambiar ninguna lógica existente.
