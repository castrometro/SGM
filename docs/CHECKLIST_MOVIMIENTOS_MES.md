# ✅ Checklist de Validación - Movimientos Mes

## Pre-Despliegue ✅

- [x] Archivo `movimientos_mes.py` creado (309 líneas)
- [x] Import actualizado en `views_movimientos_mes.py`
- [x] Export agregado en `tasks_refactored/__init__.py`
- [x] Celery worker reiniciado
- [x] Sin errores de compilación (solo warnings de linter)
- [x] Documentación completa generada

---

## Testing Manual Requerido

### 1. Upload de Archivo ⏳

**Pasos:**
1. Ir a Nómina → Cierre → Movimientos del Mes
2. Seleccionar un cierre en estado adecuado
3. Subir archivo Excel válido de movimientos

**Verificación:**
- [ ] Upload exitoso (status 201)
- [ ] Task ID de Celery retornado
- [ ] Archivo visible en interfaz

### 2. Procesamiento ⏳

**Verificación:**
- [ ] Estado cambia: `pendiente` → `en_proceso` → `procesado`
- [ ] Sin errores en logs de Celery
- [ ] Resultados guardados en `resultados_procesamiento`

### 3. Logging Correcto ⏳

**Django Shell:**
```python
from nomina.models_logging import TarjetaActivityLogNomina
from django.contrib.auth import get_user_model

User = get_user_model()

# Obtener usuario de prueba (NO Pablo Castro ID 1)
usuario_test = User.objects.get(correo_bdo='cecilia.reyes@sgm.cl')  # Ajustar según tu caso

# Ver logs recientes
logs = TarjetaActivityLogNomina.objects.filter(
    tarjeta='movimientos_mes'
).order_by('-timestamp')[:10]

print("\n=== LOGS MOVIMIENTOS MES ===")
for log in logs:
    print(f"\n{log.accion}:")
    print(f"  Usuario: {log.usuario.correo_bdo} (ID: {log.usuario.id})")
    print(f"  Descripción: {log.descripcion}")
    print(f"  Resultado: {log.resultado}")
```

**Verificación:**
- [ ] Logs muestran usuario correcto (quien subió el archivo)
- [ ] NO muestra Pablo Castro (ID 1) ni sistema_user
- [ ] Eventos registrados: `process_start`, `process_complete`

### 4. ActivityEvent (Audit Trail) ⏳

```python
from nomina.models import ActivityEvent

# Ver eventos técnicos
events = ActivityEvent.objects.filter(
    resource_type='movimientos_mes'
).order_by('-timestamp')[:10]

print("\n=== ACTIVITY EVENTS ===")
for evt in events:
    print(f"\n{evt.action}:")
    print(f"  Usuario: {evt.user.correo_bdo} (ID: {evt.user.id})")
    print(f"  Detalles: {evt.details}")
```

**Verificación:**
- [ ] Eventos registrados: `procesamiento_celery_iniciado`, `procesamiento_completado`
- [ ] Usuario correcto en todos los eventos
- [ ] `celery_task_id` presente en detalles

### 5. Frontend ⏳

**Verificación:**
- [ ] Tarjeta muestra estado "procesado" con check verde
- [ ] Botón "Procesar" deshabilitado después de completar
- [ ] Resultados visibles (contadores por tipo de movimiento)
- [ ] Historial muestra usuario correcto

### 6. Registros Creados ⏳

**Django Shell:**
```python
from nomina.models import (
    MovimientoAltaBaja, 
    MovimientoAusentismo,
    MovimientoVacaciones,
    MovimientoVariacionSueldo,
    MovimientoVariacionContrato,
    CierreNomina
)

# ID del cierre de prueba
cierre = CierreNomina.objects.get(id=CIERRE_ID)

print(f"\n=== MOVIMIENTOS CREADOS ===")
print(f"Altas/Bajas: {MovimientoAltaBaja.objects.filter(cierre=cierre).count()}")
print(f"Ausentismos: {MovimientoAusentismo.objects.filter(cierre=cierre).count()}")
print(f"Vacaciones: {MovimientoVacaciones.objects.filter(cierre=cierre).count()}")
print(f"Variaciones Sueldo: {MovimientoVariacionSueldo.objects.filter(cierre=cierre).count()}")
print(f"Variaciones Contrato: {MovimientoVariacionContrato.objects.filter(cierre=cierre).count()}")
```

**Verificación:**
- [ ] Registros creados según contenido del Excel
- [ ] Contadores coinciden con `resultados_procesamiento`

---

## Escenarios de Error

### 7. Archivo Inválido ⏳

**Pasos:**
1. Subir archivo con formato incorrecto
2. Verificar manejo de error

**Verificación:**
- [ ] Estado: `con_error`
- [ ] Error registrado en `resultados_procesamiento.errores`
- [ ] Log con `resultado='error'`
- [ ] Frontend muestra error

### 8. Usuario No Encontrado ⏳

**Simulación:**
```python
# Llamar tarea con usuario_id inexistente
from nomina.tasks_refactored.movimientos_mes import procesar_movimientos_mes_con_logging

# DEBE usar fallback a sistema_user sin fallar
task = procesar_movimientos_mes_con_logging.delay(movimiento_id=123, usuario_id=9999)
```

**Verificación:**
- [ ] NO falla la tarea
- [ ] Warning en logs: "Usuario 9999 no encontrado, usando sistema_user"
- [ ] Procesamiento continúa con sistema_user como fallback

---

## Regresión

### 9. Libro de Remuneraciones ⏳

**Verificación:**
- [ ] Libro sigue funcionando correctamente
- [ ] No hay conflictos de imports
- [ ] Logging dual funciona en ambos módulos

---

## Performance

### 10. Tiempo de Procesamiento ⏳

**Benchmark:**
```python
import time
from django.utils import timezone

# Antes de procesar
inicio = timezone.now()

# ... subir y procesar archivo ...

# Después de completar
fin = timezone.now()
duracion = (fin - inicio).total_seconds()

print(f"Tiempo de procesamiento: {duracion} segundos")
```

**Verificación:**
- [ ] Tiempo similar a versión original
- [ ] Sin degradación de performance

---

## Checklist Final

### Funcionalidad Core
- [ ] Upload funciona
- [ ] Procesamiento funciona
- [ ] Delete funciona
- [ ] Resubida funciona

### Logging
- [ ] Usuario correcto en TarjetaActivityLogNomina
- [ ] Usuario correcto en ActivityEvent
- [ ] Eventos completos (start, complete, error)
- [ ] Detalles JSON correctos

### Estados
- [ ] `pendiente` → `en_proceso` → `procesado`
- [ ] `con_errores_parciales` cuando aplica
- [ ] `con_error` en fallos totales
- [ ] Frontend reconoce estado "procesado"

### Integración
- [ ] Sin conflictos con Libro de Remuneraciones
- [ ] Celery worker procesa correctamente
- [ ] Queue `nomina_queue` correcta
- [ ] Sin memory leaks

---

## Aprobación

**Testing realizado por:** ___________________  
**Fecha:** ___________________  
**Observaciones:** ___________________

**Estado Final:**
- [ ] ✅ APROBADO - Listo para producción
- [ ] ⚠️ APROBADO CON OBSERVACIONES
- [ ] ❌ RECHAZADO - Requiere correcciones

---

## Rollback Plan

Si se encuentra un bug crítico:

```bash
# 1. Restaurar import original
# En views_movimientos_mes.py línea 34:
from .tasks import procesar_movimientos_mes

# 2. Restaurar llamada original
# En views_movimientos_mes.py línea 271:
task = procesar_movimientos_mes.delay(instance.id, None, request.user.id)

# 3. Reiniciar Celery
docker compose restart celery_worker

# 4. Verificar funcionamiento
```

---

**Documento de validación v1.0**  
*Generado: 18 de octubre de 2025*
