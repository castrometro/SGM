# 📊 **ACTIVITY LOGGER - DOCUMENTACIÓN TÉCNICA**

## 🚫 **ESTADO ACTUAL: DESHABILITADO**

El `ActivityLogger` está actualmente **deshabilitado** para evitar errores 404 ya que los endpoints del backend no están implementados.

## 🔧 **CONFIGURACIÓN ACTUAL**

```javascript
// src/utils/activityLogger.js
const ACTIVITY_LOGGING_ENABLED = false; // ← DESHABILITADO
```

### **Comportamiento Actual:**
- ✅ Todos los métodos del ActivityLogger funcionan sin errores
- ✅ Logging visible en **consola del navegador** para debugging
- ❌ **No se envían datos al backend** (intencionalmente)
- ✅ **No hay errores 404** ni problemas de red

---

## 📈 **FUNCIONALIDAD DEL ACTIVITY LOGGER**

### **Métodos Disponibles:**

#### **1. Gestión de Sesiones:**
```javascript
await activityLogger.logSessionStart();        // Inicio de sesión de trabajo
await activityLogger.logSessionEnd();          // Fin de sesión de trabajo
```

#### **2. Polling Monitoring:**
```javascript
await activityLogger.logPollingStart(5);       // Inicio de polling (intervalo 5s)
await activityLogger.logPollingStop('razón');  // Detención de polling
```

#### **3. Interacciones con Archivos:**
```javascript
await activityLogger.logFileSelect(nombre, tamaño);     // Selección de archivo
await activityLogger.logFileUploadStart(nombre);        // Inicio de subida
await activityLogger.logFileUploadComplete(nombre);     // Subida completada
await activityLogger.logFileUploadError(error);         // Error en subida
```

#### **4. Interacciones con Modales:**
```javascript
await activityLogger.logModalOpen('tipo', data);        // Apertura de modal
await activityLogger.logModalClose('tipo', data);       // Cierre de modal
```

#### **5. Descargas:**
```javascript
await activityLogger.logDownloadTemplate('tipo');       // Descarga de template
```

#### **6. Cambios de Estado:**
```javascript
await activityLogger.logStateChange(oldState, newState, trigger);
```

---

## 🏗️ **IMPLEMENTACIÓN DEL BACKEND (Cuando sea necesario)**

### **1. Endpoints Requeridos:**

#### **Sesiones:**
```python
# POST /api/nomina/activity-log/session/
{
    "cierre_id": 123,
    "tarjeta": "libro_remuneraciones",
    "action": "start|end",
    "duration_seconds": 45  # Solo para 'end'
}
```

#### **Polling:**
```python
# POST /api/nomina/activity-log/polling/
{
    "cierre_id": 123,
    "tarjeta": "movimientos_mes",
    "action": "start|stop",
    "interval_seconds": 5,  # Solo para 'start'
    "reason": "razón"       # Solo para 'stop'
}
```

#### **Archivos:**
```python
# POST /api/nomina/activity-log/file/
{
    "cierre_id": 123,
    "tarjeta": "libro_remuneraciones",
    "action": "select|upload_start|upload_complete|upload_error",
    "filename": "archivo.xlsx",
    "file_size": 1024,
    "error_message": "..."  # Solo para errores
}
```

#### **Modales:**
```python
# POST /api/nomina/activity-log/modal/
{
    "cierre_id": 123,
    "tarjeta": "libro_remuneraciones",
    "action": "open|close",
    "modal_type": "classification|file_selector",
    "data": {...}  # Datos adicionales del modal
}
```

#### **Descargas:**
```python
# POST /api/nomina/activity-log/download/
{
    "cierre_id": 123,
    "tarjeta": "movimientos_mes",
    "template_type": "movimientos_mes|libro_remuneraciones"
}
```

### **2. Modelo Django Sugerido:**

```python
# models.py
class ActivityLog(models.Model):
    TARJETA_CHOICES = [
        ('libro_remuneraciones', 'Libro de Remuneraciones'),
        ('movimientos_mes', 'Movimientos del Mes'),
        ('finiquitos', 'Finiquitos'),
        ('incidencias', 'Incidencias'),
        ('ingresos', 'Ingresos'),
        ('novedades', 'Novedades'),
    ]
    
    ACTION_CHOICES = [
        ('session_start', 'Inicio de Sesión'),
        ('session_end', 'Fin de Sesión'),
        ('polling_start', 'Inicio de Polling'),
        ('polling_stop', 'Fin de Polling'),
        ('file_select', 'Selección de Archivo'),
        ('file_upload_start', 'Inicio Subida'),
        ('file_upload_complete', 'Subida Completa'),
        ('file_upload_error', 'Error Subida'),
        ('modal_open', 'Apertura Modal'),
        ('modal_close', 'Cierre Modal'),
        ('download_template', 'Descarga Template'),
        ('state_change', 'Cambio de Estado'),
    ]
    
    cierre = models.ForeignKey(CierreNomina, on_delete=models.CASCADE)
    tarjeta = models.CharField(max_length=50, choices=TARJETA_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Campos opcionales para datos específicos
    filename = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    interval_seconds = models.IntegerField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    modal_type = models.CharField(max_length=50, blank=True, null=True)
    old_state = models.CharField(max_length=50, blank=True, null=True)
    new_state = models.CharField(max_length=50, blank=True, null=True)
    trigger = models.CharField(max_length=100, blank=True, null=True)
    additional_data = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['cierre', 'tarjeta']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
        ]
```

### **3. ViewSet Django Sugerido:**

```python
# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class ActivityLogViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'], url_path='session')
    def session(self, request):
        # Manejar logging de sesiones
        pass
    
    @action(detail=False, methods=['post'], url_path='polling')
    def polling(self, request):
        # Manejar logging de polling
        pass
    
    @action(detail=False, methods=['post'], url_path='file')
    def file(self, request):
        # Manejar logging de archivos
        pass
    
    @action(detail=False, methods=['post'], url_path='modal')
    def modal(self, request):
        # Manejar logging de modales
        pass
    
    @action(detail=False, methods=['post'], url_path='download')
    def download(self, request):
        # Manejar logging de descargas
        pass
```

---

## 🚀 **CÓMO REACTIVAR EL LOGGING**

### **Paso 1: Implementar Backend**
1. Crear modelo `ActivityLog`
2. Crear ViewSet con endpoints requeridos
3. Añadir URLs al routing
4. Ejecutar migraciones

### **Paso 2: Habilitar Frontend**
```javascript
// src/utils/activityLogger.js
const ACTIVITY_LOGGING_ENABLED = true; // ← CAMBIAR A TRUE
```

### **Paso 3: Verificar Funcionamiento**
1. Abrir consola del navegador
2. Interactuar con las tarjetas
3. Verificar que no hay errores 404
4. Confirmar que los logs se guardan en la base de datos

---

## 📊 **BENEFICIOS DEL ACTIVITY LOGGING**

### **Para Product Management:**
- 📈 **Métricas de uso** de cada tarjeta
- ⏱️ **Tiempo promedio** de sesiones de trabajo
- 📁 **Patrones de subida** de archivos
- 🔄 **Frecuencia de polling** y performance
- 🎯 **Puntos de fricción** en el flujo de trabajo

### **Para Desarrollo:**
- 🐛 **Debugging** de problemas de usuarios
- 🔍 **Monitoreo de errores** en tiempo real
- ⚡ **Optimización de performance** basada en datos
- 📊 **Analytics de comportamiento** de usuarios

### **Para Soporte:**
- 🆘 **Diagnostico** rápido de problemas
- 📝 **Historial de actividad** por sesión
- 🔄 **Reproducción** de problemas reportados

---

## ⚠️ **CONSIDERACIONES DE PRIVACY**

- ✅ **No se loggean datos sensibles** (contenido de archivos, RUTs, etc.)
- ✅ **Solo metadata** de interacciones (nombres, tamaños, timestamps)
- ✅ **Cumple con políticas** de privacidad corporativas
- ✅ **Datos anonimizables** para analytics

---

## 🎯 **CONCLUSIÓN**

El `ActivityLogger` está **preparado y funcional** en el frontend, solo esperando la implementación del backend para comenzar a recopilar métricas valiosas del uso del sistema.

**Estado Actual: ✅ Estable y sin errores**  
**Próximo Paso: 🏗️ Implementar backend cuando sea prioritario**
