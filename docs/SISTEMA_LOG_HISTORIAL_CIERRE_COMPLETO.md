# 📋 Sistema de Log Historial del Cierre - Implementación Completa

## 🎯 Resumen Ejecutivo

Se implementó un sistema completo de logging para rastrear TODA la actividad que ocurre en un cierre de nómina:

- ✅ **Upload de archivos** (Libro de Remuneraciones + 4 tarjetas)
- ✅ **Eliminación de archivos**
- ✅ **Procesamiento Celery** (análisis, clasificación)
- ✅ **Validaciones** (éxito y errores)
- ✅ **Timeline visual en el frontend**
- ✅ **Exportación a TXT**

---

## 🏗️ Arquitectura de la Solución

### Backend (Django)

#### 1. Modelo de Datos (`ActivityEvent`)

**Ubicación:** `backend/nomina/models_activity_v2.py`

```python
class ActivityEvent(models.Model):
    cierre_id = models.PositiveIntegerField(db_index=True)  # ✅ CLAVE: ID del cierre
    modulo = models.CharField(max_length=20)                 # 'nomina' o 'contabilidad'
    seccion = models.CharField(max_length=50)                # 'libro_remuneraciones', 'ingresos', etc.
    evento = models.CharField(max_length=50)                 # 'upload_iniciado', 'archivo_eliminado', etc.
    usuario_id = models.PositiveIntegerField()               # Quién hizo la acción
    timestamp = models.DateTimeField(auto_now_add=True)      # Cuándo ocurrió
    datos = models.JSONField(default=dict)                   # Información adicional
    resultado = models.CharField(choices=[...])              # 'ok', 'error', 'timeout'
```

**Método estático para logging:**

```python
ActivityEvent.log(
    cierre_id=123,
    modulo='nomina',
    seccion='libro_remuneraciones',
    evento='upload_iniciado',
    usuario_id=request.user.id,
    datos={
        'archivo': 'libro.xlsx',
        'tamano_bytes': 2048000
    }
)
```

---

#### 2. Eventos Capturados

##### A. Upload del Libro de Remuneraciones

**Archivo:** `backend/nomina/views_libro_remuneraciones.py`

```python
class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        # ✅ 1. Inicio de upload
        ActivityEvent.log(
            cierre_id=cierre.id,
            evento='upload_iniciado',
            datos={'archivo': archivo.name, 'tamano_bytes': archivo.size}
        )
        
        # ✅ 2. Archivo validado
        ActivityEvent.log(
            cierre_id=cierre.id,
            evento='archivo_validado',
            resultado='ok'
        )
        
        # ✅ 3. Upload completado
        ActivityEvent.log(
            cierre_id=cierre.id,
            evento='upload_completado',
            datos={'libro_id': instance.id, 'es_reemplazo': True/False}
        )
        
        # ✅ 4. Procesamiento iniciado (Celery)
        ActivityEvent.log(
            cierre_id=cierre.id,
            evento='procesamiento_iniciado'
        )
```

##### B. Eliminación de Archivo

```python
def perform_destroy(self, instance):
    # ✅ Registro de eliminación
    ActivityEvent.log(
        cierre_id=instance.cierre.id,
        evento='archivo_eliminado',
        datos={
            'libro_id': instance.id,
            'archivo': instance.nombre_original,
            'motivo': request.data.get('motivo', 'No especificado')
        }
    )
```

##### C. Procesamiento Celery

**Archivo:** `backend/nomina/tasks.py`

```python
@shared_task
def analizar_headers_libro_remuneraciones_con_logging(libro_id, upload_log_id):
    # ✅ 1. Inicio
    ActivityEvent.log(
        cierre_id=cierre_id,
        evento='analisis_headers_iniciado',
        datos={'libro_id': libro_id}
    )
    
    try:
        # ... procesamiento ...
        
        # ✅ 2. Éxito
        ActivityEvent.log(
            cierre_id=cierre_id,
            evento='analisis_headers_exitoso',
            resultado='ok',
            datos={'headers_detectados': len(headers)}
        )
    except Exception as e:
        # ✅ 3. Error
        ActivityEvent.log(
            cierre_id=cierre_id,
            evento='analisis_headers_error',
            resultado='error',
            datos={'error': str(e)}
        )
```

**También captura:**
- `clasificacion_headers_iniciada`
- `clasificacion_headers_exitosa`
- `clasificacion_headers_error`

---

#### 3. Endpoints REST API

**Archivo:** `backend/nomina/views_activity_v2.py`

##### Endpoint 1: Timeline Completo

```http
GET /api/nomina/cierre/{cierre_id}/timeline/
```

**Response:**
```json
{
  "cierre_id": 30,
  "periodo": "2025-10",
  "cliente": "Cliente ABC",
  "total_eventos": 47,
  "timeline": [
    {
      "timestamp": "2025-10-17T10:30:00Z",
      "seccion": "libro_remuneraciones",
      "evento": "upload_iniciado",
      "usuario": "Juan Pérez",
      "usuario_email": "juan@example.com",
      "resultado": "ok",
      "datos": {
        "archivo": "libro.xlsx",
        "tamano_bytes": 2048000
      }
    },
    ...
  ],
  "resumen": {
    "total_eventos": 47,
    "uploads_exitosos": 5,
    "uploads_fallidos": 1,
    "eliminaciones": 2,
    "procesamiento_exitoso": 4,
    "errores": 1,
    "primera_actividad": "2025-10-17T10:00:00Z",
    "ultima_actividad": "2025-10-17T14:20:00Z"
  },
  "por_seccion": {
    "libro_remuneraciones": 15,
    "ingresos": 10,
    "finiquitos": 8
  }
}
```

##### Endpoint 2: Exportar como TXT

```http
GET /api/nomina/cierre/{cierre_id}/log/export/txt/
```

**Descarga un archivo de texto:**
```
================================================================================
LOG DE ACTIVIDAD - CIERRE #30
Cliente: Cliente ABC
Período: 2025-10
Generado: 17/10/2025 15:30:45
================================================================================

17/10/2025 10:30:00 - Juan Pérez
  ✅ libro_remuneraciones: upload_iniciado
  Datos: {'archivo': 'libro.xlsx', 'tamano_bytes': 2048000}

17/10/2025 10:30:15 - Sistema
  ⚙️ libro_remuneraciones: analisis_headers_iniciado
  Datos: {'libro_id': 123}

...
```

---

### Frontend (React)

#### Componente `<CierreTimeline />`

**Ubicación:** `src/components/CierreTimeline.jsx`

**Uso:**

```jsx
import CierreTimeline from './components/CierreTimeline';

function MiComponente() {
  const [mostrarTimeline, setMostrarTimeline] = useState(false);
  const cierreId = 30;

  return (
    <>
      <button onClick={() => setMostrarTimeline(true)}>
        📋 Ver Historial del Cierre
      </button>

      {mostrarTimeline && (
        <CierreTimeline 
          cierreId={cierreId}
          onClose={() => setMostrarTimeline(false)}
        />
      )}
    </>
  );
}
```

**Características:**

- ✅ Modal fullscreen con overlay
- ✅ Timeline visual con iconos
- ✅ Resumen estadístico en tarjetas
- ✅ Detalles expandibles por evento
- ✅ Botón de exportar a TXT
- ✅ Scroll infinito para muchos eventos
- ✅ Colores diferenciados para errores

---

## 📊 Ejemplo de Timeline Real

```
CIERRE #30 - Octubre 2025 - Cliente ABC
════════════════════════════════════════════════════

📊 Total: 47 eventos | ✅ 40 exitosos | ❌ 3 errores | 🗑️ 2 eliminados

────────────────────────────────────────────────────

📅 17/10/2025 10:30:00 - Juan Pérez
   📤 Subió libro_remuneraciones.xlsx (2.3 MB)
   ✅ Estado: Exitoso

📅 17/10/2025 10:30:02 - Sistema
   🔍 Validando archivo...
   ✅ Validación exitosa

📅 17/10/2025 10:30:15 - Sistema Celery
   ⚙️ Analizando headers...
   
📅 17/10/2025 10:32:40 - Sistema Celery
   ✅ Análisis completado
   📊 71 headers detectados

📅 17/10/2025 10:32:41 - Sistema Celery
   🏷️ Clasificando headers...

📅 17/10/2025 10:35:20 - Sistema Celery
   ✅ Clasificación completada
   📊 71 clasificados, 0 sin clasificar

📅 17/10/2025 11:45:00 - María González
   📤 Subió ingresos.xlsx
   ✅ 5 ingresos procesados

📅 17/10/2025 14:20:00 - Juan Pérez
   🗑️ Eliminó ingresos.xlsx
   💬 Motivo: "Archivo con datos incorrectos"

📅 17/10/2025 14:25:00 - Juan Pérez
   📤 Subió ingresos_corregido.xlsx
   ✅ 5 ingresos procesados
```

---

## 🔍 Consultas Útiles

### 1. Ver todo lo que pasó en un cierre

```python
# Django ORM
from nomina.models_activity_v2 import ActivityEvent

eventos = ActivityEvent.objects.filter(
    cierre_id=30
).order_by('timestamp')

for e in eventos:
    print(f"{e.timestamp} - {e.usuario.get_full_name()}: {e.evento}")
```

### 2. Ver solo errores

```python
errores = ActivityEvent.objects.filter(
    cierre_id=30,
    resultado='error'
).order_by('timestamp')
```

### 3. Ver actividad de un usuario específico

```python
actividad_usuario = ActivityEvent.objects.filter(
    cierre_id=30,
    usuario_id=5
).order_by('timestamp')
```

### 4. Contar eventos por tipo

```python
from django.db.models import Count

resumen = ActivityEvent.objects.filter(
    cierre_id=30
).values('evento').annotate(
    total=Count('id')
).order_by('-total')
```

---

## 🚀 Cómo Probar la Implementación

### Paso 1: Reiniciar Django y Celery

```bash
# En Docker
docker compose restart django celery

# O en local
cd backend
python manage.py runserver
./celery_worker.sh
```

### Paso 2: Subir un archivo

1. Ve a la página de un cierre
2. Sube el libro de remuneraciones
3. El sistema registrará automáticamente:
   - `upload_iniciado`
   - `archivo_validado`
   - `upload_completado`
   - `procesamiento_iniciado`

### Paso 3: Esperar procesamiento Celery

El worker registrará:
- `analisis_headers_iniciado`
- `analisis_headers_exitoso`
- `clasificacion_headers_iniciada`
- `clasificacion_headers_exitosa`

### Paso 4: Ver el timeline

```jsx
// En el componente del cierre
<button onClick={() => setMostrarTimeline(true)}>
  📋 Ver Historial
</button>

{mostrarTimeline && (
  <CierreTimeline cierreId={cierreId} onClose={() => setMostrarTimeline(false)} />
)}
```

### Paso 5: Eliminar el archivo

1. Elimina el libro subido
2. El sistema registrará:
   - `archivo_eliminado`

### Paso 6: Volver a subir

1. Sube nuevamente
2. El evento tendrá `es_reemplazo: true` en los datos

---

## 📈 Beneficios del Sistema

### Para el Usuario

- ✅ **Trazabilidad completa**: Saber qué pasó y cuándo
- ✅ **Auditoría**: Ver quién hizo cada acción
- ✅ **Debugging**: Identificar errores fácilmente
- ✅ **Historial**: Recuperar información de uploads anteriores
- ✅ **Exportable**: Guardar el log como archivo de texto

### Para el Desarrollador

- ✅ **Debugging productivo**: Ver qué falló sin logs de servidor
- ✅ **Analytics**: Analizar patrones de uso
- ✅ **Performance**: Identificar cuellos de botella en procesamiento
- ✅ **Extensible**: Fácil agregar nuevos eventos

---

## 🔧 Extender el Sistema

### Agregar un nuevo evento

```python
# En cualquier view/task
from .models_activity_v2 import ActivityEvent

ActivityEvent.log(
    cierre_id=cierre.id,
    modulo='nomina',
    seccion='nueva_seccion',
    evento='nuevo_evento',
    usuario_id=user.id,
    resultado='ok',  # o 'error', 'timeout'
    datos={
        'campo_custom': 'valor',
        'otro_dato': 123
    }
)
```

### Agregar exportación a PDF

```python
# En views_activity_v2.py
from reportlab.pdfgen import canvas

@api_view(['GET'])
def exportar_cierre_log_pdf(request, cierre_id):
    # Similar a exportar_cierre_log_txt pero generando PDF
    ...
```

---

## ✅ Checklist de Implementación

- [x] Modelo `ActivityEvent` con campo `cierre_id`
- [x] Logging en upload del Libro de Remuneraciones
- [x] Logging en eliminación de archivos
- [x] Logging en tareas Celery (análisis + clasificación)
- [x] Endpoint `/cierre/{id}/timeline/`
- [x] Endpoint `/cierre/{id}/log/export/txt/`
- [x] Componente React `<CierreTimeline />`
- [x] Estilos CSS completos
- [x] Rutas registradas en `urls.py`
- [x] Documentación completa

---

## 📝 Notas Técnicas

### Rendimiento

- Se usa `select_related('usuario')` para evitar N+1 queries
- Índices en: `cierre_id`, `timestamp`, `resultado`
- Límite de 200 eventos en el endpoint (ajustable)

### Seguridad

- Verificación de acceso por cliente asignado
- Solo usuarios autenticados pueden ver el timeline
- Los datos sensibles se sanitizan antes de guardar

### Escalabilidad

- Si un cierre tiene +1000 eventos, considera paginación
- Los eventos antiguos pueden archivarse después de N meses
- El JSON `datos` tiene límite implícito de ~65KB

---

## 🎉 Resultado Final

**Ahora tienes un sistema completo** que responde a la pregunta:

> "¿Qué pasó en este cierre? ¿Quién subió qué? ¿Cuándo se procesó? ¿Hubo errores?"

Con un timeline visual, exportable, y completamente auditable. 🚀
