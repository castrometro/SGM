# 📊 Estado del Logging por Sección/Tarjeta - Sistema SGM Nómina

## 🎯 Resumen Ejecutivo

El sistema tiene **5 secciones principales** con diferentes estados de logging:

| # | Sección | Backend Logging | Frontend Logging | UI Integration | Estado |
|---|---------|-----------------|------------------|----------------|--------|
| 1 | **Libro de Remuneraciones** | ✅ COMPLETO | ✅ ACTIVO | ⏳ Pendiente | � 85% |
| 2 | **Movimientos del Mes** | ❌ FALTA | ✅ ACTIVO | ⏳ Pendiente | 🟡 40% |
| 3 | **Archivos del Analista** | ❌ FALTA | ✅ ACTIVO (parcial) | ⏳ Pendiente | 🟡 30% |
| 4 | **Discrepancias** | ❌ FALTA | ❌ Sin logging | ❌ Sin UI | 🔴 0% |
| 5 | **Incidencias** | ❌ FALTA | ❌ Sin logging | ❌ Sin UI | 🔴 0% |

**Última actualización:** 2025-01-10 - ✅ **Opción A completada**

---

## 📋 Detalle por Sección

### 1. 📚 Libro de Remuneraciones

**Backend** (`views_libro_remuneraciones.py`):
- ✅ `upload_iniciado`
- ✅ `archivo_validado` / `validacion_fallida`
- ✅ `upload_completado`
- ✅ `procesamiento_iniciado` / `procesamiento_error_inicio`
- ✅ `archivo_eliminado`
- ✅ `analisis_headers_iniciado/exitoso/error` (Celery)
- ✅ `clasificacion_headers_iniciada/exitosa/error` (Celery)

**Frontend** (`LibroRemuneracionesCard.jsx`):
- ✅ **ACTIVADO** - Migrado a V2 completamente
- ✅ 10 eventos frontend implementados:
  - `file_selected` - Usuario selecciona archivo
  - `upload_started` - Inicia subida
  - `upload_completed` - Upload exitoso
  - `upload_error` - Error en upload
  - `delete_started` - Inicia eliminación
  - `delete_completed` - Eliminación exitosa
  - `delete_error` - Error en eliminación
  - `procesamiento_final_iniciado` - Click en "Procesar"
  - `procesamiento_final_aceptado` - API acepta procesamiento
  - `procesamiento_final_error` - Error en procesamiento

**Props Integration:**
- ✅ `ArchivosTalanaSection.jsx` - Props agregados
- ✅ `ArchivosTalanaSection_v2.jsx` - Props agregados

**Estado**: � **85% Completo** - Backend + Frontend OK, falta UI integration (botón timeline)

---

### 2. 📦 Movimientos del Mes (4 sub-tarjetas)

**Backend** (`views_movimientos_mes.py`):
- ❌ NO tiene logging con ActivityEvent
- ⚠️ Solo usa el sistema stub antiguo

**Frontend**:
- ✅ `MovimientosMesCard.jsx` - Usa `activityLogger_v2`
  - `modal_opened`
  - `file_validated`
  - `upload_started`
- ✅ `IngresosCard.jsx` - Usa `activityLogger_v2`
- ✅ `FiniquitosCard.jsx` - Usa `activityLogger_v2`
- ✅ `AusentismosCard.jsx` - Usa `activityLogger_v2`

**Sub-componentes**:
1. **MovimientosMesCard** (archivo principal) - ✅ Logging activo
2. **IngresosCard** - ✅ Logging activo
3. **FiniquitosCard** - ✅ Logging activo
4. **AusentismosCard** - ✅ Logging activo

**Estado**: 🟡 **40% Completo** - Frontend OK, falta backend

---

### 3. 👤 Archivos del Analista (3 sub-tarjetas)

**Backend** (`views_archivos_analista.py`):
- ❌ NO tiene logging con ActivityEvent en upload
- ✅ Tiene logging SOLO en eliminación (`perform_destroy`)
- ⚠️ Usa sistema stub antiguo para el resto

**Frontend**:
Los 3 tipos de archivos del analista usan las mismas tarjetas que Movimientos:
- ✅ `IngresosCard.jsx` - Logging activo
- ✅ `FiniquitosCard.jsx` - Logging activo  
- ✅ `AusentismosCard.jsx` - Logging activo (para Incidencias)

**Tarjeta Novedades**:
- ❌ `NovedadesCard.jsx` - NO tiene logging activo

**Estado**: 🟡 **30% Completo** - Parcial en frontend, falta backend

---

### 4. ⚠️ Discrepancias

**Backend** (`views_discrepancias.py` / `utils/GenerarDiscrepancias.py`):
- ❌ NO tiene logging de ningún tipo
- ⚠️ Solo genera las discrepancias, no registra actividad

**Frontend** (`DiscrepanciasViewer.jsx`):
- ❌ NO tiene logging de ningún tipo
- ⚠️ Solo muestra las discrepancias

**Eventos que deberían capturarse**:
- Generación de discrepancias (automática)
- Visualización de discrepancias
- Filtrado de discrepancias
- Resolución/cierre de discrepancias

**Estado**: 🔴 **0% Completo** - Sin implementar

---

### 5. 🔔 Incidencias

**Backend** (`views_incidencias.py` / `models.py`):
- ❌ NO tiene logging con ActivityEvent
- ⚠️ Solo maneja el CRUD de incidencias

**Frontend** (`IncidenciasEncontradas/` components):
- ❌ NO tiene logging de ningún tipo
- ⚠️ `ModalResolucionIncidencia.jsx` - sin logging

**Eventos que deberían capturarse**:
- Creación de incidencia (manual o automática)
- Apertura de modal de resolución
- Envío de respuesta (analista/supervisor)
- Subida de adjuntos
- Cambio de estado (turno_analista ↔ turno_supervisor)
- Resolución final

**Estado**: 🔴 **0% Completo** - Sin implementar

---

## 🔧 Plan de Implementación Completo

### Fase 1: Completar Libro de Remuneraciones (2 horas)

**Ya hecho en esta sesión** ✅

---

### Fase 2: Implementar Movimientos del Mes (3 horas)

**Backend** - Agregar a `views_movimientos_mes.py`:

```python
from .models import ActivityEvent

class MovimientosMesUploadViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        # ✅ Logging: upload_iniciado, archivo_validado, upload_completado
        ActivityEvent.log(
            cierre_id=cierre.id,
            modulo='nomina',
            seccion='movimientos_mes',
            evento='upload_iniciado',
            usuario_id=request.user.id,
            datos={'archivo': archivo.name}
        )
        # ... resto del código
    
    def perform_destroy(self, instance):
        # ✅ Logging: archivo_eliminado
        ActivityEvent.log(
            cierre_id=instance.cierre.id,
            seccion='movimientos_mes',
            evento='archivo_eliminado',
            usuario_id=self.request.user.id
        )
```

**Tasks** - Agregar a `tasks.py`:
```python
@shared_task
def procesar_movimientos_mes(movimientos_id):
    # ✅ Logging: procesamiento_iniciado/exitoso/error
    ActivityEvent.log(...)
```

---

### Fase 3: Implementar Archivos del Analista (3 horas)

**Backend** - Agregar a `views_archivos_analista.py`:

```python
from .models import ActivityEvent

class ArchivoAnalistaUploadViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['post'])
    def subir(self, request, cierre_id=None, tipo_archivo=None):
        # ✅ Logging: upload_iniciado
        ActivityEvent.log(
            cierre_id=cierre_id,
            modulo='nomina',
            seccion='archivos_analista',
            evento=f'upload_{tipo_archivo}_iniciado',
            usuario_id=request.user.id,
            datos={'tipo_archivo': tipo_archivo}
        )
        
        # ... procesar archivo ...
        
        # ✅ Logging: upload_completado
        ActivityEvent.log(
            cierre_id=cierre_id,
            seccion='archivos_analista',
            evento=f'upload_{tipo_archivo}_completado',
            usuario_id=request.user.id
        )
```

**Tasks** - Agregar a `tasks.py`:
```python
@shared_task
def procesar_archivo_analista(archivo_id):
    # ✅ Logging: procesamiento_iniciado/exitoso/error
    ActivityEvent.log(...)
```

**Frontend** - Agregar a `NovedadesCard.jsx`:
```jsx
import { createActivityLogger } from "../../utils/activityLogger_v2";

// Agregar logging igual que las otras tarjetas
```

---

### Fase 4: Implementar Discrepancias (2 horas)

**Backend** - Agregar a `utils/GenerarDiscrepancias.py`:

```python
from nomina.models import ActivityEvent

def generar_todas_discrepancias(cierre):
    # ✅ Logging: generacion_discrepancias_iniciada
    ActivityEvent.log(
        cierre_id=cierre.id,
        modulo='nomina',
        seccion='discrepancias',
        evento='generacion_iniciada',
        datos={'trigger': 'automatic'}
    )
    
    # ... generar discrepancias ...
    
    # ✅ Logging: generacion_discrepancias_completada
    ActivityEvent.log(
        cierre_id=cierre.id,
        seccion='discrepancias',
        evento='generacion_completada',
        resultado='ok',
        datos={
            'total_discrepancias': total,
            'libro_vs_novedades': count1,
            'movimientos_vs_analista': count2
        }
    )
```

**Frontend** - Agregar a `DiscrepanciasViewer.jsx`:

```jsx
import { createActivityLogger } from "../../utils/activityLogger_v2";

useEffect(() => {
  const logger = createActivityLogger(clienteId, cierreId);
  
  // Log cuando abre la vista
  logger.log({
    action: 'vista_discrepancias_abierta',
    resourceType: 'discrepancias',
    details: { total: discrepancias.length }
  });
}, [cierreId]);

// Log cuando filtra
const handleFiltrar = (filtro) => {
  logger.log({
    action: 'filtro_aplicado',
    resourceType: 'discrepancias',
    details: { filtro }
  });
};
```

---

### Fase 5: Implementar Incidencias (4 horas)

**Backend** - Agregar a `views_incidencias.py`:

```python
from .models import ActivityEvent

class IncidenciaCierreViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        # ✅ Logging: incidencia_creada
        incidencia = serializer.save()
        ActivityEvent.log(
            cierre_id=incidencia.cierre.id,
            modulo='nomina',
            seccion='incidencias',
            evento='incidencia_creada',
            usuario_id=self.request.user.id,
            datos={
                'incidencia_id': incidencia.id,
                'tipo': incidencia.tipo,
                'estado': incidencia.estado
            }
        )

class ResolucionIncidenciaViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        # ✅ Logging: resolucion_enviada
        resolucion = serializer.save()
        ActivityEvent.log(
            cierre_id=resolucion.incidencia.cierre.id,
            seccion='incidencias',
            evento='resolucion_enviada',
            usuario_id=self.request.user.id,
            datos={
                'incidencia_id': resolucion.incidencia.id,
                'rol': 'analista' if resolucion.es_analista else 'supervisor',
                'tiene_adjunto': bool(resolucion.adjunto)
            }
        )
```

**Frontend** - Agregar a `ModalResolucionIncidencia.jsx`:

```jsx
import { createActivityLogger } from "../../../utils/activityLogger_v2";

const ModalResolucionIncidencia = ({ incidencia, cierreId, clienteId }) => {
  const logger = useRef(createActivityLogger(clienteId, cierreId));
  
  useEffect(() => {
    // Log al abrir modal
    logger.current.log({
      action: 'modal_resolucion_abierto',
      resourceType: 'incidencias',
      resourceId: String(incidencia.id),
      details: {
        incidencia_id: incidencia.id,
        estado: incidencia.estado
      }
    });
  }, [incidencia]);
  
  const handleEnviarRespuesta = async () => {
    // Log al enviar respuesta
    logger.current.log({
      action: 'respuesta_enviada',
      resourceType: 'incidencias',
      resourceId: String(incidencia.id),
      details: {
        texto_length: texto.length,
        tiene_adjunto: !!adjunto
      }
    });
    
    // ... enviar respuesta ...
  };
};
```

---

## 📊 Resumen de Prioridades

### 🔥 Críticas (Hacer Ahora)

1. **Fase 2: Movimientos del Mes** - Backend logging
   - Es una tarjeta principal del flujo
   - Frontend ya está listo
   - 3 horas de trabajo

2. **Fase 3: Archivos del Analista** - Backend logging
   - Flujo crítico del sistema
   - Frontend casi listo (falta NovedadesCard)
   - 3 horas de trabajo

### 🟡 Importantes (Hacer Pronto)

3. **Fase 4: Discrepancias** - Logging completo
   - Feature avanzada pero importante
   - 2 horas de trabajo

4. **Fase 5: Incidencias** - Logging completo
   - Feature colaborativa crítica
   - 4 horas de trabajo

### ✅ Completadas

- **Fase 1: Libro de Remuneraciones** ✅
  - Backend 100% completo
  - Falta solo activar frontend

---

## 🎯 Roadmap Sugerido

### Sprint 1 (Esta semana) - 6 horas
- ✅ Libro de Remuneraciones (backend) - HECHO
- ⏳ Movimientos del Mes (backend) - 3 horas
- ⏳ Archivos del Analista (backend) - 3 horas

### Sprint 2 (Próxima semana) - 6 horas
- ⏳ Discrepancias (backend + frontend) - 2 horas
- ⏳ Incidencias (backend + frontend) - 4 horas

### Sprint 3 (Opcional) - 2 horas
- Activar frontend del Libro de Remuneraciones
- Agregar logging a NovedadesCard
- Testing completo del sistema

---

## 💡 Consideraciones Técnicas

### Convenciones de Nomenclatura

**Backend (seccion)**:
- `libro_remuneraciones`
- `movimientos_mes`
- `archivos_analista`
- `discrepancias`
- `incidencias`

**Frontend (resourceType)**:
- `libro_remuneraciones`
- `movimientos_ingresos`, `movimientos_finiquitos`, `movimientos_ausentismos`
- `archivos_ingresos`, `archivos_finiquitos`, `archivos_incidencias`
- `discrepancias`
- `incidencias`

### Eventos Estándar

Todos los componentes deberían loggear:
- `modal_opened` / `modal_closed`
- `file_selected` / `file_validated`
- `upload_iniciado` / `upload_completado`
- `procesamiento_iniciado` / `procesamiento_exitoso` / `procesamiento_error`
- `archivo_eliminado`

---

## ✅ Checklist de Implementación

### Libro de Remuneraciones
- [x] Backend: Upload logging
- [x] Backend: Procesamiento Celery logging
- [x] Backend: Eliminación logging
- [x] Backend: Endpoints timeline
- [ ] Frontend: Activar activityLogger_v2
- [x] Frontend: Componente CierreTimeline

### Movimientos del Mes
- [ ] Backend: Upload logging
- [ ] Backend: Procesamiento Celery logging
- [ ] Backend: Eliminación logging
- [x] Frontend: Modal y file events (4 cards)

### Archivos del Analista
- [ ] Backend: Upload logging (3 tipos)
- [ ] Backend: Procesamiento Celery logging
- [x] Backend: Eliminación logging
- [x] Frontend: Logging (Ingresos, Finiquitos, Ausentismos)
- [ ] Frontend: Logging NovedadesCard

### Discrepancias
- [ ] Backend: Generación logging
- [ ] Backend: Resolución logging
- [ ] Frontend: Vista y filtros logging

### Incidencias
- [ ] Backend: Creación logging
- [ ] Backend: Resolución logging
- [ ] Backend: Cambio de estado logging
- [ ] Frontend: Modal logging
- [ ] Frontend: Respuestas logging
- [ ] Frontend: Adjuntos logging

---

## 🚀 ¿Qué Implementamos Ahora?

Opciones disponibles:

**A) Completar el flujo del Libro** (1 hora)
   - Activar frontend logging en LibroRemuneracionesCard
   - Integrar CierreTimeline en la página del cierre

**B) Implementar Movimientos del Mes** (3 horas)
   - Agregar logging backend completo
   - Ya tiene frontend activo

**C) Implementar Archivos del Analista** (3 horas)
   - Agregar logging backend completo
   - Activar logging en NovedadesCard

**D) Implementar Discrepancias** (2 horas)
   - Backend + Frontend desde cero

**E) Implementar Incidencias** (4 horas)
   - Backend + Frontend desde cero

¿Cuál prefieres? 🎯
