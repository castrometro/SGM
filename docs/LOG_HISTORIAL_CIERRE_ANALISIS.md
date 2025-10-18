# 📋 Log Historial del Cierre - Análisis y Solución

## 🎯 Requerimiento del Usuario

> "Necesito un log de la actividad del cierre. Saber qué ocurrió: si subió archivo, si eliminó, si volvió a subir, etc. Y al final poder guardarlo."

## ✅ Lo que YA TIENES (Implementado)

Con el `ActivityEvent` + `cierreId`, **ya puedes rastrear**:

```python
# Consultar TODO lo que pasó en un cierre
ActivityEvent.objects.filter(
    resource_type='cierre',
    resource_id='30'
).order_by('created_at')
```

### Eventos que SE ESTÁN Capturando Ahora:

| Componente | Eventos Capturados |
|------------|-------------------|
| **IngresosCard** | ✅ Modal abierto, archivo validado, upload iniciado |
| **FiniquitosCard** | ✅ Modal abierto, archivo validado, upload iniciado |
| **AusentismosCard** | ✅ Modal abierto, archivo validado, upload iniciado |
| **MovimientosMesCard** | ✅ Modal abierto, archivo validado, upload iniciado |

**PERO...**

---

## ❌ Lo que NO TIENES (Falta Implementar)

### 1. **Eventos Críticos del Libro de Remuneraciones**

El **archivo más importante** (Libro de Remuneraciones) **NO está loggeando** en ActivityEvent:

```python
# backend/nomina/views_libro_remuneraciones.py

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        # ❌ ESTE CÓDIGO NO USA ActivityEvent
        # Solo usa el stub viejo (models_logging_stub.py)
        
        upload_log_stub = log_mixin.crear_upload_log(cliente, archivo)
        # ☝️ Esto NO se guarda en ActivityEvent
```

### 2. **Eliminaciones (DELETE)**

No hay logging cuando:
- Eliminan un archivo subido
- Eliminan registros de nómina
- Eliminan el libro completo

### 3. **Re-subidas (REPLACE)**

No se registra cuando:
- Suben el mismo archivo dos veces
- Reemplazan un archivo existente

### 4. **Resultado Final de Procesamiento**

Falta capturar:
- ¿El procesamiento Celery terminó bien?
- ¿Cuántos registros se procesaron?
- ¿Hubo errores?

### 5. **Exportación del Log**

No hay endpoint para:
- Descargar el historial del cierre como PDF/Excel
- Ver timeline visual en el frontend

---

## 🔧 SOLUCIÓN COMPLETA - Plan de Implementación

### Fase 1: Integrar Libro de Remuneraciones (URGENTE)

```python
# backend/nomina/views_libro_remuneraciones.py

from .models_activity_v2 import ActivityEvent  # ✅ Importar el modelo correcto

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        # ... código existente ...
        
        # ✅ AGREGAR LOGGING
        ActivityEvent.log(
            cierre_id=cierre.id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='upload_iniciado',
            usuario_id=request.user.id,
            datos={
                'archivo': archivo.name,
                'tamano_bytes': archivo.size,
                'cliente_id': cliente.id,
            }
        )
        
        # Guardar el libro
        libro = serializer.save(
            cierre=cierre,
            archivo=temp_path,
            nombre_original=archivo.name,
            upload_log=None  # ✅ Ya tenemos ActivityEvent
        )
        
        # ✅ LOGGING DE ÉXITO
        ActivityEvent.log(
            cierre_id=cierre.id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='upload_completado',
            usuario_id=request.user.id,
            datos={
                'libro_id': libro.id,
                'archivo': archivo.name,
            }
        )
```

### Fase 2: Capturar Eliminaciones

```python
# backend/nomina/views_libro_remuneraciones.py

class LibroRemuneracionesUploadViewSet(viewsets.ModelViewSet):
    
    def perform_destroy(self, instance):
        """Logging al eliminar libro"""
        
        ActivityEvent.log(
            cierre_id=instance.cierre.id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='archivo_eliminado',
            usuario_id=self.request.user.id,
            datos={
                'libro_id': instance.id,
                'archivo': instance.nombre_original,
                'motivo': self.request.data.get('motivo', 'No especificado'),
            }
        )
        
        instance.delete()
```

### Fase 3: Logging en Tareas Celery

```python
# backend/nomina/tasks.py

@shared_task(bind=True)
def procesar_libro_remuneraciones_completo(self, libro_id, cierre_id):
    """Procesar libro con logging completo"""
    
    try:
        # ✅ LOG: Inicio
        ActivityEvent.log(
            cierre_id=cierre_id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='procesamiento_iniciado',
            datos={'libro_id': libro_id, 'task_id': self.request.id}
        )
        
        # Procesar...
        resultado = procesar_headers_y_filas(libro_id)
        
        # ✅ LOG: Éxito
        ActivityEvent.log(
            cierre_id=cierre_id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='procesamiento_exitoso',
            resultado='ok',
            datos={
                'libro_id': libro_id,
                'registros_procesados': resultado['total'],
                'empleados_creados': resultado['nuevos_empleados'],
                'duracion_segundos': resultado['tiempo'],
            }
        )
        
        return resultado
        
    except Exception as e:
        # ✅ LOG: Error
        ActivityEvent.log(
            cierre_id=cierre_id,
            modulo='nomina',
            seccion='libro_remuneraciones',
            evento='procesamiento_fallido',
            resultado='error',
            datos={
                'libro_id': libro_id,
                'error': str(e),
                'task_id': self.request.id,
            }
        )
        raise
```

### Fase 4: Endpoint para Historial del Cierre

```python
# backend/nomina/views_activity_v2.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models_activity_v2 import ActivityEvent
from django.db.models import Count, Q

@api_view(['GET'])
def get_cierre_timeline(request, cierre_id):
    """
    Obtener timeline completo de un cierre
    
    GET /api/nomina/cierre/{cierre_id}/timeline/
    
    Retorna:
    {
        "cierre_id": 30,
        "total_eventos": 47,
        "timeline": [
            {
                "timestamp": "2025-10-17T10:30:00Z",
                "seccion": "libro_remuneraciones",
                "evento": "upload_iniciado",
                "usuario": "Juan Pérez",
                "datos": {...}
            },
            ...
        ],
        "resumen": {
            "uploads_exitosos": 5,
            "uploads_fallidos": 1,
            "eliminaciones": 2,
            "ultima_actividad": "2025-10-17T14:20:00Z"
        }
    }
    """
    
    eventos = ActivityEvent.objects.filter(
        cierre_id=cierre_id
    ).select_related('usuario').order_by('timestamp')
    
    # Resumen agregado
    resumen = eventos.aggregate(
        uploads_exitosos=Count('id', filter=Q(evento__contains='upload', resultado='ok')),
        uploads_fallidos=Count('id', filter=Q(evento__contains='upload', resultado='error')),
        eliminaciones=Count('id', filter=Q(evento__contains='eliminado')),
    )
    
    return Response({
        'cierre_id': cierre_id,
        'total_eventos': eventos.count(),
        'timeline': [
            {
                'timestamp': e.timestamp,
                'seccion': e.seccion,
                'evento': e.evento,
                'usuario': e.usuario.get_full_name() if e.usuario_id else 'Sistema',
                'resultado': e.resultado,
                'datos': e.datos,
            }
            for e in eventos
        ],
        'resumen': resumen,
    })
```

### Fase 5: Exportación a PDF

```python
# backend/nomina/views_activity_v2.py

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
import io

@api_view(['GET'])
def exportar_cierre_log_pdf(request, cierre_id):
    """
    Exportar historial del cierre como PDF
    
    GET /api/nomina/cierre/{cierre_id}/log/export/pdf/
    """
    
    # Crear buffer
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Obtener eventos
    eventos = ActivityEvent.objects.filter(cierre_id=cierre_id).order_by('timestamp')
    cierre = CierreNomina.objects.get(id=cierre_id)
    
    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"Log de Actividad - Cierre {cierre.periodo}")
    p.setFont("Helvetica", 10)
    p.drawString(50, 730, f"Cliente: {cierre.cliente.razon_social}")
    p.drawString(50, 715, f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Timeline
    y = 680
    for evento in eventos:
        p.drawString(50, y, f"{evento.timestamp.strftime('%d/%m %H:%M')} - {evento.seccion}: {evento.evento}")
        y -= 15
        
        if y < 50:
            p.showPage()
            y = 750
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cierre_{cierre_id}_log.pdf"'
    return response
```

---

## 📊 Resultado Final: Timeline Completo del Cierre

Con todas las fases implementadas, podrás ver:

```
CIERRE #30 - Octubre 2025
════════════════════════════════════════

📅 17/10/2025 10:30:00 - Juan Pérez
   📤 Subió libro_remuneraciones.xlsx (2.3 MB)
   ✅ Archivo validado correctamente

📅 17/10/2025 10:30:15 - Sistema Celery
   ⚙️ Procesamiento iniciado (Task: abc123)
   
📅 17/10/2025 10:32:40 - Sistema Celery
   ✅ Procesamiento exitoso
   📊 1,234 registros procesados
   👥 15 empleados nuevos creados
   ⏱️ Duración: 145 segundos

📅 17/10/2025 11:45:00 - María González
   📤 Subió ingresos.xlsx
   ✅ 5 ingresos procesados

📅 17/10/2025 14:20:00 - Juan Pérez
   🗑️ Eliminó ingresos.xlsx
   💬 Motivo: "Archivo con datos incorrectos"

📅 17/10/2025 14:25:00 - Juan Pérez
   📤 Subió ingresos_corregido.xlsx
   ✅ 5 ingresos procesados

════════════════════════════════════════
RESUMEN:
- 5 archivos subidos (100% exitosos)
- 1 archivo eliminado
- 0 errores de procesamiento
- Última actividad: 17/10/2025 14:25:00
```

---

## 🚀 Plan de Implementación Recomendado

| Fase | Prioridad | Esfuerzo | Impacto |
|------|-----------|----------|---------|
| **Fase 1**: Integrar Libro Remuneraciones | 🔥 CRÍTICA | 1 hora | ⭐⭐⭐⭐⭐ |
| **Fase 2**: Capturar Eliminaciones | Alta | 30 min | ⭐⭐⭐⭐ |
| **Fase 3**: Logging en Celery | Alta | 1 hora | ⭐⭐⭐⭐⭐ |
| **Fase 4**: Endpoint Timeline | Media | 1 hora | ⭐⭐⭐ |
| **Fase 5**: Exportación PDF | Baja | 2 horas | ⭐⭐ |

---

## ✅ Checklist de Implementación

### Inmediato (Hoy)
- [ ] Agregar `ActivityEvent.log()` en `perform_create` de LibroRemuneracionesUpload
- [ ] Agregar `ActivityEvent.log()` en `perform_destroy`
- [ ] Probar con una subida real

### Esta Semana
- [ ] Logging en todas las tareas Celery del libro
- [ ] Endpoint `/cierre/{id}/timeline/`
- [ ] Componente React `<CierreTimeline />`

### Próxima Iteración
- [ ] Exportación a PDF
- [ ] Exportación a Excel
- [ ] Dashboard de analytics del cierre

