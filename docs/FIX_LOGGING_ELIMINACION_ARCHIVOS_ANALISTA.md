# Fix: Logging de Eliminación de Archivos Analista

**Fecha:** 18 de octubre de 2025  
**Módulo:** `backend/nomina/views_archivos_analista.py`  
**Issue:** Los logs de eliminación no aparecían en TarjetaActivityLogNomina

## 🐛 Problema Detectado

Cuando un usuario eliminaba un archivo analista (finiquitos, incidencias o ingresos), el log de la eliminación **NO aparecía** en `TarjetaActivityLogNomina`, a pesar de que el código llamaba a `registrar_actividad_tarjeta_nomina()`.

### Síntomas
- ✅ La eliminación funcionaba correctamente
- ✅ Los datos relacionados se borraban
- ❌ No aparecía ningún registro en el activity log
- ❌ El usuario no veía evidencia de la eliminación

## 🔍 Análisis de Causa Raíz

El problema estaba en la **importación incorrecta** en `views_archivos_analista.py`:

```python
# ❌ INCORRECTO - Importaba un STUB que no hace nada
from .models_logging_stub import registrar_actividad_tarjeta_nomina
```

La función `registrar_actividad_tarjeta_nomina` en `models_logging_stub.py` es solo un **placeholder vacío**:

```python
def registrar_actividad_tarjeta_nomina(*args, **kwargs):
    """STUB: Función de registro de actividad"""
    logger.debug("STUB: registrar_actividad_tarjeta_nomina()")
    return None  # ⚠️ NO GUARDA NADA EN LA BASE DE DATOS
```

### Por qué existía el stub
Los stubs fueron creados durante la transición al sistema de logging v2, pero algunos módulos siguieron usando los stubs en lugar de migrar a las funciones reales.

## ✅ Solución Implementada

### Cambio en `views_archivos_analista.py` línea 16:

```python
# ✅ CORRECTO - Importa la función real que guarda en BD
from .models_logging import registrar_actividad_tarjeta_nomina  # ✅ Usando función real, no stub
```

La función real en `models_logging.py` **sí guarda** el registro:

```python
def registrar_actividad_tarjeta_nomina(
    cierre_id,
    tarjeta,
    accion,
    descripcion,
    usuario=None,
    detalles=None,
    resultado="exito",
    ip_address=None,
    upload_log=None
):
    """
    Función helper para registrar actividades en tarjetas de nómina
    """
    return TarjetaActivityLogNomina.objects.create(  # ✅ GUARDA EN BD
        cierre_id=cierre_id,
        tarjeta=tarjeta,
        accion=accion,
        descripcion=descripcion,
        usuario=usuario,
        detalles=detalles or {},
        resultado=resultado,
        ip_address=ip_address,
        upload_log=upload_log,
    )
```

## 🧪 Validación

Para probar que el fix funciona:

```python
# 1. Eliminar un archivo analista desde el frontend
# 2. Verificar en la base de datos:

from nomina.models import TarjetaActivityLogNomina

# Debería aparecer un registro como este:
TarjetaActivityLogNomina.objects.filter(
    tarjeta__in=['analista_finiquitos', 'analista_incidencias', 'analista_ingresos'],
    accion='delete_archivo'
).latest('created_at')

# Detalles esperados:
{
    'cierre_id': <id_del_cierre>,
    'tarjeta': 'analista_finiquitos',  # o incidencias, o ingresos
    'accion': 'delete_archivo',
    'descripcion': 'Archivo del analista (finiquitos) eliminado para resubida',
    'usuario': <usuario_que_eliminó>,
    'detalles': {
        'archivo_id': <id>,
        'tipo_archivo': 'finiquitos',
        'archivo_nombre': 'nombre_del_archivo.xlsx',
        'estado_anterior': 'procesado'
    },
    'ip_address': '<ip_del_usuario>'
}
```

## 📊 Impacto

### Antes del fix
- ❌ Eliminaciones no auditadas
- ❌ No se podía rastrear quién eliminó qué archivo
- ❌ Pérdida de trazabilidad

### Después del fix
- ✅ Todas las eliminaciones registradas en TarjetaActivityLogNomina
- ✅ Auditoría completa con usuario, timestamp, IP
- ✅ Trazabilidad total del ciclo de vida del archivo
- ✅ Filtrado por tipo específico (`analista_finiquitos`, etc.)

## 🔗 Archivos Modificados

1. **`backend/nomina/views_archivos_analista.py`**
   - Línea 16: Cambio de importación de stub a función real
   - Método: `perform_destroy()` (línea 132-171)

## 📝 Notas Adicionales

### Otros módulos con potenciales stubs
Revisar si otros views también importan desde `models_logging_stub.py`:

```bash
grep -r "from .models_logging_stub import" backend/nomina/
```

Cualquier importación desde el stub debería migrarse a `models_logging.py` para garantizar que los logs se guarden correctamente.

### Tarjetas con nombres abreviados
Recordar que usamos nombres abreviados por el límite de 25 caracteres en la BD:
- `analista_finiquitos` (20 chars) ✅
- `analista_incidencias` (21 chars) ✅
- `analista_ingresos` (18 chars) ✅

## ⚠️ Problema Adicional Detectado: Choices del Modelo

### Síntoma
Al ver el log en el admin de Django, la tarjeta aparecía como "----" (null/undefined) en el formulario de detalle, aunque en la lista se veía correctamente.

### Causa
El modelo `TarjetaActivityLogNomina` tenía `TARJETA_CHOICES` definidas, pero NO incluía las nuevas tarjetas específicas:
- `analista_finiquitos`
- `analista_incidencias`
- `analista_ingresos`

Solo tenía `archivos_analista` genérico, por lo que Django no reconocía los valores específicos como válidos.

### Solución
Agregamos las 3 nuevas opciones al campo `TARJETA_CHOICES` en `models_logging.py`:

```python
TARJETA_CHOICES = [
    ("libro_remuneraciones", "Tarjeta: Libro de Remuneraciones"),
    ("movimientos_mes", "Tarjeta: Movimientos del Mes"),
    ("novedades", "Tarjeta: Novedades"),
    ("archivos_analista", "Tarjeta: Archivos del Analista"),
    # ✅ Tarjetas específicas por tipo de archivo analista
    ("analista_finiquitos", "Tarjeta: Finiquitos"),
    ("analista_incidencias", "Tarjeta: Incidencias/Ausentismos"),
    ("analista_ingresos", "Tarjeta: Nuevos Ingresos"),
    ("incidencias", "Tarjeta: Incidencias"),
    ("revision", "Tarjeta: Revisión"),
]
```

**Archivo modificado:** `backend/nomina/models_logging.py` (línea 275-284)

## ✅ Despliegue

```bash
# Reiniciar Django para aplicar cambios
docker compose restart django
```

**Nota:** No se requiere migración porque solo cambiamos las opciones del `choices`, no la estructura de la base de datos.

---

## 📋 Resumen de Fixes Aplicados

1. ✅ **Import Fix**: Cambiar de `models_logging_stub` a `models_logging` en views
2. ✅ **Choices Fix**: Agregar `analista_finiquitos`, `analista_incidencias`, `analista_ingresos` a TARJETA_CHOICES

**Status:** ✅ COMPLETAMENTE RESUELTO  
**Testing:** Listo para validación en producción  
**Prioridad:** Alta (afecta auditoría y compliance)
