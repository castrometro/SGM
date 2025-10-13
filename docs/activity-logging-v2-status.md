# SGM Activity Logging V2 - Estado del Proyecto

**Fecha:** 13 de octubre de 2025  
**Sistema:** SGM Contabilidad & Nómina  
**Módulo:** Activity Logging V2 (Sistema unificado de registros de actividad)

## 📋 Resumen Ejecutivo

Este documento registra el progreso de la migración del sistema de logging de actividades de **V1 (fragmentado)** a **V2 (unificado)** en el módulo de nómina del sistema SGM.

### 🎯 Objetivo del Proyecto
Reemplazar el sistema complejo y fragmentado de logging V1 por un sistema unificado V2 que:
- **Centralice** todos los logs en un solo modelo
- **Automatice** la captura via middleware
- **Simplifique** la API frontend/backend
- **Mejore** el rendimiento y mantenibilidad

---

## ✅ COMPLETADO

### 1. **Análisis y Limpieza del Sistema V1** ✅

#### **Frontend V1 limpiado:**
- ✅ Identificados imports de `activityLogger` en componentes de nómina
- ✅ Comentados imports en archivos:
  - `AusentismosCard.jsx`
  - `FiniquitosCard.jsx` 
  - `IngresosCard.jsx`
  - `MovimientosMesCard.jsx`
- ✅ Creado **stub temporal** en `src/utils/activityLogger.js`
- ✅ Frontend compila sin errores (puerto 5174)

#### **Backend V1 limpiado:**
- ✅ **Script automatizado** ejecutado (`cleanup_v1_backend.py`)
- ✅ Imports redirigidos a stubs temporales:
  - `models_logging.py` → `models_logging_stub.py`
  - `api_logging.py` → `api_logging_stub.py`
  - `views_logging.py` → `views_logging_stub.py`
  - `utils/mixins.py` → `utils/mixins_stub.py`
- ✅ URLs ajustadas para usar funciones stub (no clases)
- ✅ **Archivos de backup** creados automáticamente (`.backup`)
- ✅ Django pasa `manage.py check` sin errores

### 2. **Sistema V2 - Infraestructura Base** ✅

#### **Base de datos:**
- ✅ Modelo `ActivityEvent` creado en `nomina/models.py`
- ✅ Admin configurado en `nomina/admin.py` 
- ✅ **Migración 0248** creada y aplicada exitosamente
- ✅ Modelo probado: 2 eventos de prueba registrados

#### **Características del modelo V2:**
```python
class ActivityEvent(models.Model):
    # Identificación básica
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_index=True)
    
    # Contexto de la actividad
    event_type = models.CharField(max_length=50, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)  
    resource_id = models.CharField(max_length=100, blank=True)
    
    # Detalles del evento
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    
    # Metadatos de sesión
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
```

#### **Funcionalidades incluidas:**
- ✅ Método estático `ActivityEvent.log()` para registro simple
- ✅ Limpieza automática de eventos antiguos (`cleanup_old_events()`)
- ✅ Eventos relacionados por ventana de tiempo (`get_related_events()`)
- ✅ Índices optimizados para consultas frecuentes
- ✅ Admin de solo lectura (eventos inmutables)

---

## ❌ PENDIENTE

### 3. **Middleware V2 - Captura Automática** 🚧
**Estado:** NO INSTALADO

#### **Tareas pendientes:**
- [ ] Instalar `nomina.middleware.activity_middleware.ActivityCaptureMiddleware` en `settings.py`
- [ ] Configurar patrones URL para captura automática
- [ ] Probar captura automática de eventos en endpoints de nómina

#### **Archivos ya creados:**
- ✅ `backend/nomina/middleware/activity_middleware.py` (creado previamente)

### 4. **API V2 - Endpoints Reales** 🚧  
**Estado:** USANDO STUBS (no funcional)

#### **Tareas pendientes:**
- [ ] Crear vistas V2 reales en `nomina/views_activity_v2.py`
- [ ] Reemplazar stubs en URLs:
  ```python
  # ACTUAL (stubs):
  path('activity-log/modal/', ModalActivityView, ...)  # Stub
  
  # OBJETIVO (V2):
  path('activity-log/events/', ActivityEventListView.as_view(), ...)
  ```
- [ ] Implementar endpoints:
  - `GET /activity-log/events/` - Listar eventos
  - `POST /activity-log/events/` - Crear evento manual
  - `GET /activity-log/events/{id}/` - Detalle de evento

### 5. **Frontend V2 - Logger Unificado** 🚧
**Estado:** USANDO STUB (no registra nada)

#### **Tareas pendientes:**
- [ ] Integrar `activityLogger_v2.js` (ya creado)
- [ ] Reemplazar imports stub en componentes:
  ```jsx
  // ACTUAL:
  // import { createActivityLogger } from "../../utils/activityLogger";
  
  // OBJETIVO:
  import { useActivityLogger } from "../../utils/activityLogger_v2";
  ```
- [ ] Probar logging en componentes de nómina
- [ ] Verificar que eventos aparecen en admin Django

---

## 🧪 VERIFICACIÓN ACTUAL

### **Estado del Sistema (13/10/2025):**
```bash
# Frontend
✅ Compilación: Sin errores (puerto 5174)
❌ Logging: Stub activo (no registra)

# Backend  
✅ Django check: Sin errores
✅ Base de datos: ActivityEvent tabla existe
❌ Middleware: No instalado
❌ APIs: Usando stubs

# Datos
📊 Eventos V2 registrados: 2 (solo pruebas manuales)
🕒 Último evento: test.migration_test @ 15:27:16
```

### **Comandos de verificación:**
```bash
# Verificar modelo V2
docker compose exec django python manage.py shell -c "
from nomina.models import ActivityEvent; 
print(f'Eventos: {ActivityEvent.objects.count()}')"

# Verificar middleware
docker compose exec django python manage.py shell -c "
from django.conf import settings;
print([m for m in settings.MIDDLEWARE if 'activity' in m.lower()])"

# Verificar frontend
curl -s http://172.17.11.18:5174 | grep -o "ready in"
```

---

## 🚀 PRÓXIMOS PASOS

### **Orden de implementación recomendado:**

1. **📡 Instalar Middleware V2** (30 min)
   - Agregar a `MIDDLEWARE` en settings
   - Probar captura automática de requests

2. **🔌 Implementar APIs V2** (45 min)
   - Crear vistas reales en `views_activity_v2.py`
   - Actualizar URLs para usar vistas V2
   - Probar endpoints con Postman

3. **🖥️ Migrar Frontend V2** (60 min)
   - Reemplazar imports de stub por V2
   - Actualizar componentes uno por uno
   - Verificar logs en admin Django

4. **🧪 Testing Final** (30 min)
   - Flujo completo: Frontend → API → Base de datos
   - Verificar performance y cleanup automático
   - Documentar uso para desarrolladores

### **Tiempo estimado total restante:** ~3 horas

---

## 📁 ARCHIVOS IMPORTANTES

### **Archivos V2 (nuevos):**
```
backend/nomina/
├── models.py (+ ActivityEvent)
├── admin.py (+ ActivityEventAdmin)  
├── models_activity_v2.py ✅
├── middleware/activity_middleware.py ✅
└── migrations/0248_add_activity_event_v2.py ✅

src/utils/
└── activityLogger_v2.js ✅
```

### **Archivos stub (temporales):**
```
backend/nomina/
├── models_logging_stub.py
├── api_logging_stub.py
├── views_logging_stub.py
└── utils/mixins_stub.py

src/utils/
└── activityLogger.js (stub version)
```

### **Archivos de backup:**
```
backend/nomina/
├── views.py.backup
├── tasks.py.backup
├── views_archivos_analista.py.backup
└── contabilidad/tasks_de_tipo_doc.py.backup
```

---

## 🔧 COMANDOS ÚTILES

### **Para desarrolladores:**

```bash
# Crear evento manual
docker compose exec django python manage.py shell -c "
from nomina.models import ActivityEvent
from django.contrib.auth import get_user_model
from api.models import Cliente
ActivityEvent.log(
    user=User.objects.first(),
    cliente=Cliente.objects.first(), 
    event_type='manual',
    action='test'
)"

# Ver logs recientes
docker compose exec django python manage.py shell -c "
from nomina.models import ActivityEvent
for e in ActivityEvent.objects.all()[:5]:
    print(f'{e.timestamp}: {e}')"

# Limpiar eventos antiguos
docker compose exec django python manage.py shell -c "
from nomina.models import ActivityEvent
deleted = ActivityEvent.cleanup_old_events(days=30)
print(f'Eliminados: {deleted} eventos')"
```

---

**Creado por:** GitHub Copilot  
**Revisión siguiente:** Al completar middleware V2  
**Contacto:** Continuar en el chat para siguientes pasos