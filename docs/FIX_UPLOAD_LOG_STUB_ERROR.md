# Fix: Error de Upload en Libro de Remuneraciones

## 🐛 Problema
Al intentar subir un archivo de Libro de Remuneraciones, el sistema arrojaba error 500:

```
AttributeError: 'function' object has no attribute 'create'
Exception Location: /app/nomina/utils/mixins.py, line 33
```

## 🔍 Causa Raíz

El error ocurría porque el **stub de transición** (`models_logging_stub.py`) estaba mal diseñado:

### ❌ Diseño incorrecto (antes)
```python
class UploadLogNomina:
    @classmethod
    def objects(cls):  # ← objects era un MÉTODO
        class StubManager:
            def create(cls, **kwargs):
                return None
        return StubManager()
```

En este diseño, `objects` era un **método** que debía ser llamado con paréntesis: `UploadLogNomina.objects()`. Sin embargo, el código en `mixins.py` lo usaba como un **atributo** (como en Django):

```python
upload_log = UploadLogNomina.objects.create(...)  # ❌ objects es función, no Manager
```

### ✅ Diseño correcto (después)
```python
class StubManager:
    """Manager stub que simula Django ORM"""
    def create(self, **kwargs):
        return StubInstance(**kwargs)
    
    def get(self, **kwargs):
        return None
    
    def filter(self, **kwargs):
        return []

class UploadLogNomina:
    objects = StubManager()  # ← objects es ATRIBUTO de clase
```

Ahora `objects` es un **atributo de clase** que contiene una instancia de `StubManager`, exactamente igual que en Django.

## 🔧 Solución Aplicada

**Archivo modificado:** `/root/SGM/backend/nomina/models_logging_stub.py`

### Cambios principales:

1. **StubManager como clase separada**: Manager reutilizable que simula Django ORM
2. **StubInstance**: Objeto que simula una instancia de modelo con atributos dinámicos
3. **objects como atributo**: `objects = StubManager()` en lugar de método `@classmethod`

### Código nuevo:
```python
class StubInstance:
    """Instancia stub que simula un objeto de modelo"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = None  # Simular que no tiene ID
    
    def save(self):
        logger.debug("STUB: save() no-op")
        pass

class StubManager:
    """Manager stub que simula Django ORM"""
    def create(self, **kwargs):
        logger.debug(f"STUB: UploadLogNomina.create(**kwargs)")
        return StubInstance(**kwargs)

class UploadLogNomina:
    objects = StubManager()  # ✅ Atributo, no método
```

## 🎯 Resultado

- ✅ `UploadLogNomina.objects.create()` ahora funciona correctamente
- ✅ El stub retorna una instancia simulada con los campos asignados
- ✅ No se genera ningún registro en base de datos (comportamiento stub)
- ✅ Los logs indican claramente que es un STUB

## 🔄 Próximos Pasos

Este stub es **temporal**. La migración completa incluye:

1. ✅ **Fase 1**: Activity Logging V2 implementado y funcionando
2. ✅ **Fase 2**: Stub funcionando correctamente (evita errores durante transición)
3. ⏳ **Fase 3**: Migrar `mixins.py` para usar Activity Logging V2 directamente
4. ⏳ **Fase 4**: Eliminar `models_logging_stub.py` y el código V1 obsoleto

## 📝 Nota Técnica

**¿Por qué no migrar directamente?**

El sistema V1 está profundamente integrado en múltiples ViewSets. El stub permite:
- Evitar errores 500 durante la transición
- Mantener el sistema funcionando mientras se migra gradualmente
- No bloquear operaciones críticas de usuarios

**Estrategia de migración gradual:**
1. Nuevo código → usa Activity V2 directamente
2. Código existente → usa stub (no-op) hasta migración
3. Una vez todo migrado → eliminar V1 completamente

## ✅ Verificación

```python
# Test en Django shell
from nomina.models_logging_stub import UploadLogNomina

# Debería funcionar sin error
log = UploadLogNomina.objects.create(
    cliente=cliente,
    tipo_upload='test',
    nombre_archivo_original='test.xlsx'
)
print(log)  # <StubInstance object>
print(log.tipo_upload)  # 'test'
```

## 🔧 Cambios Adicionales en views_libro_remuneraciones.py

Para evitar que el stub intente asignarse a ForeignKeys reales, se deshabilitaron las siguientes líneas:

1. **Línea ~106 y ~115**: `upload_log = None` en lugar de asignar el stub
2. **Líneas ~121-122**: Comentado el update de `ruta_archivo` del stub
3. **Líneas ~125-140**: Comentado `registrar_actividad_tarjeta_nomina()` (función stub V1)
4. **Líneas ~143-149**: Comentado el guardado de `resumen` del stub
5. **Línea ~154**: Pasando `None` en lugar de `upload_log.id` a Celery
6. **Línea ~160**: Comentado `marcar_como_error()` del stub

### Logs de debug agregados:
```python
logger.debug(f"[STUB] Upload log NO persistido. Ruta: {instance.archivo.path}")
logger.debug(f"[STUB] Actividad NO registrada. Archivo: {archivo.name}")
logger.debug(f"[STUB] Resumen NO guardado. Libro ID: {instance.id}")
```

Estos logs permiten rastrear qué operaciones están siendo omitidas durante la transición.

---

**Estado:** ✅ RESUELTO  
**Fecha:** 16 octubre 2025  
**Django restart:** Aplicado exitosamente (2 reinicios)
**Archivos modificados:**
- `/root/SGM/backend/nomina/models_logging_stub.py` (fix de `objects` como atributo)
- `/root/SGM/backend/nomina/views_libro_remuneraciones.py` (deshabilitar persistencia de stub)
