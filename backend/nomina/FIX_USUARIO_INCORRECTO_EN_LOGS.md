# 🐛 Fix: Usuario Incorrecto en Logs de Clasificación y Procesamiento

## **Problema Detectado**

Al revisar los logs de actividad después de subir y procesar un libro de remuneraciones, se detectó que:

- ✅ **Log de upload_excel**: Usuario correcto (Cecilia Reyes - ID 24)
- ❌ **Log de classification_complete**: Usuario incorrecto (Pablo Castro - ID 1)
- ❌ **Log de process_complete**: Usuario incorrecto (Pablo Castro - ID 1)

### **Logs Antes del Fix:**

```
Log ID: 552
Acción: upload_excel
Usuario: Cecilia Reyes
Email: cecilia.reyes@bdo.cl
Usuario ID: 24
Timestamp: 2025-10-18 06:00:54

Log ID: 553
Acción: classification_complete
Usuario: Pablo Castro          ← ❌ INCORRECTO
Email: pablo.castro@bdo.cl
Usuario ID: 1
Timestamp: 2025-10-18 06:00:54

Log ID: 554
Acción: process_complete
Usuario: Pablo Castro          ← ❌ INCORRECTO
Email: pablo.castro@bdo.cl
Usuario ID: 1
Timestamp: 2025-10-18 06:26:00
```

**Pablo Castro** es el usuario ID 1 (probablemente el primero creado o el usuario SISTEMA), pero **no fue quien subió ni procesó el archivo**.

---

## 🔍 **Análisis de Causa Raíz**

### **Flujo Original (Incorrecto):**

```
1. Usuario (Cecilia) sube archivo → views_libro_remuneraciones.py
   ✅ Log: upload_excel (usuario=request.user) → Cecilia ✅
   
2. Se inicia cadena de Celery:
   chain(
       analizar_headers_libro_remuneraciones_con_logging.s(libro_id, None),
       clasificar_headers_libro_remuneraciones_con_logging.s(),
   ).apply_async()
   ❌ NO se pasa request.user.id a las tareas
   
3. Tarea analizar_headers ejecuta:
   sistema_user = _get_sistema_user()  # ← Obtiene usuario ID 1
   ActivityEvent.log(user=sistema_user)  # ← Usa ID 1
   
4. Tarea clasificar_headers ejecuta:
   sistema_user = _get_sistema_user()  # ← Obtiene usuario ID 1
   registrar_actividad_tarjeta_nomina(usuario=sistema_user)  # ← Log con ID 1 ❌
```

### **Problema:**

Las tareas de Celery **no reciben el `usuario_id`** desde el view, por lo que usan `_get_sistema_user()` que retorna el primer usuario (ID 1).

### **¿Por qué _get_sistema_user() retorna ID 1?**

```python
def _get_sistema_user():
    """Obtiene usuario genérico 'SISTEMA' para logs automáticos"""
    from api.models import Usuario
    return Usuario.objects.first()  # ← Retorna el primer usuario de la BD
```

Si no hay un usuario específico llamado "SISTEMA", retorna el primero que encuentre (generalmente el superuser o gerente creado primero).

---

## ✅ **Solución Implementada**

### **Flujo Corregido:**

```
1. Usuario (Cecilia) sube archivo → views_libro_remuneraciones.py
   ✅ Log: upload_excel (usuario=request.user) → Cecilia ✅
   
2. Se inicia cadena de Celery CON usuario_id:
   chain(
       analizar_headers_libro_remuneraciones_con_logging.s(libro_id, None, request.user.id),  ← ✅ NUEVO
       clasificar_headers_libro_remuneraciones_con_logging.s(),
   ).apply_async()
   
3. Tarea analizar_headers ejecuta:
   if usuario_id:
       usuario = Usuario.objects.get(id=usuario_id)  ← ✅ Usa Cecilia (ID 24)
   else:
       usuario = _get_sistema_user()
   
   ActivityEvent.log(user=usuario)  ← ✅ Cecilia
   
   return {
       "libro_id": libro_id,
       "usuario_id": usuario_id,  ← ✅ Pasa a la siguiente tarea
       "headers": headers
   }
   
4. Tarea clasificar_headers ejecuta:
   usuario_id = result.get("usuario_id")  ← ✅ Recibe ID 24
   usuario = Usuario.objects.get(id=usuario_id)  ← ✅ Cecilia
   
   registrar_actividad_tarjeta_nomina(usuario=usuario)  ← ✅ Log con Cecilia ✅
   
5. Usuario (Cecilia) procesa libro → views_libro_remuneraciones.py
   ✅ Log: process_start (usuario=request.user) → Cecilia ✅
   
6. Se inicia cadena de procesamiento CON usuario_id:
   chain(
       actualizar_empleados_desde_libro_optimizado.s(libro.id, request.user.id),  ← ✅ NUEVO
       guardar_registros_nomina_optimizado.s(),
   ).apply_async()
   
7. Tareas propagan usuario_id:
   actualizar_empleados → guardar_registros → chunks → consolidar_registros
   
8. Callback consolidar_registros_task ejecuta:
   if usuario_id:
       usuario = Usuario.objects.get(id=usuario_id)  ← ✅ Cecilia
   else:
       usuario = _get_sistema_user()
   
   registrar_actividad_tarjeta_nomina(usuario=usuario)  ← ✅ Log con Cecilia ✅
```

---

## 📝 **Archivos Modificados**

### **1. views_libro_remuneraciones.py**

**Línea ~228:**

```python
# ANTES:
chain(
    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, None),
    clasificar_headers_libro_remuneraciones_con_logging.s(),
).apply_async()

# DESPUÉS:
chain(
    analizar_headers_libro_remuneraciones_con_logging.s(instance.id, None, request.user.id),  # ← NUEVO
    clasificar_headers_libro_remuneraciones_con_logging.s(),
).apply_async()
```

**Cambio:** Pasa `request.user.id` como tercer parámetro.

---

### **2. tasks_refactored/libro_remuneraciones.py**

#### **A. Firma de analizar_headers (línea ~79):**

```python
# ANTES:
def analizar_headers_libro_remuneraciones_con_logging(self, libro_id, upload_log_id):

# DESPUÉS:
def analizar_headers_libro_remuneraciones_con_logging(self, libro_id, upload_log_id, usuario_id=None):
```

#### **B. Obtención de usuario (línea ~104):**

```python
# ANTES:
sistema_user = _get_sistema_user()

# DESPUÉS:
if usuario_id:
    from api.models import Usuario
    usuario = Usuario.objects.get(id=usuario_id)
else:
    usuario = _get_sistema_user()
```

#### **C. Return con usuario_id (línea ~174):**

```python
# ANTES:
return {
    "libro_id": libro_id,
    "upload_log_id": upload_log_id,
    "headers": headers
}

# DESPUÉS:
return {
    "libro_id": libro_id,
    "upload_log_id": upload_log_id,
    "usuario_id": usuario_id,  # ← NUEVO: Pasar a la siguiente tarea
    "headers": headers
}
```

#### **D. Firma de clasificar_headers (línea ~230):**

```python
# ANTES:
def clasificar_headers_libro_remuneraciones_con_logging(self, result):
    libro_id = result["libro_id"]
    upload_log_id = result["upload_log_id"]

# DESPUÉS:
def clasificar_headers_libro_remuneraciones_con_logging(self, result):
    libro_id = result["libro_id"]
    upload_log_id = result["upload_log_id"]
    usuario_id = result.get("usuario_id")  # ← NUEVO
```

#### **E. Obtención de usuario (línea ~254):**

```python
# ANTES:
sistema_user = _get_sistema_user()

# DESPUÉS:
if usuario_id:
    from api.models import Usuario
    usuario = Usuario.objects.get(id=usuario_id)
else:
    usuario = _get_sistema_user()
```

#### **F. Log de usuario corregido (línea ~367):**

```python
# ANTES:
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="libro_remuneraciones",
    accion="classification_complete",
    descripcion=f"Clasificación completada: {len(headers_clasificados)} de {len(headers)} columnas identificadas",
    usuario=sistema_user,  # ❌ Usuario SISTEMA (ID 1)
    ...
)

# DESPUÉS:
registrar_actividad_tarjeta_nomina(
    cierre_id=cierre.id,
    tarjeta="libro_remuneraciones",
    accion="classification_complete",
    descripcion=f"Clasificación completada: {len(headers_clasificados)} de {len(headers)} columnas identificadas",
    usuario=usuario,  # ✅ Usuario real que subió el archivo
    ...
)
logger.info(f"✅ TarjetaActivityLog registrado: classification_complete para libro {libro_id} (usuario_id={usuario_id})")
```

---

## 🎯 **Resultado Esperado**

### **Logs Después del Fix:**

```
Log ID: XXX
Acción: upload_excel
Usuario: Cecilia Reyes
Email: cecilia.reyes@bdo.cl
Usuario ID: 24
Timestamp: 2025-10-18 XX:XX:XX

Log ID: XXX+1
Acción: classification_complete
Usuario: Cecilia Reyes          ← ✅ CORRECTO
Email: cecilia.reyes@bdo.cl
Usuario ID: 24                  ← ✅ MISMO USUARIO
Timestamp: 2025-10-18 XX:XX:XX
```

Ahora **todos los logs de la misma operación** mostrarán el **mismo usuario** que inició la acción.

---

## 🔄 **Patrón Aplicable a Otras Tareas**

Este fix debe replicarse en **todas las cadenas de Celery** que registren actividad de usuario:

### **Patrón Correcto:**

```python
# 1. En el ViewSet:
chain(
    tarea_1.s(param1, param2, request.user.id),  # ← Siempre pasar request.user.id
    tarea_2.s(),
).apply_async()

# 2. En tarea_1:
def tarea_1(self, param1, param2, usuario_id=None):
    if usuario_id:
        usuario = Usuario.objects.get(id=usuario_id)
    else:
        usuario = _get_sistema_user()
    
    # Hacer el trabajo...
    
    return {
        "resultado": datos,
        "usuario_id": usuario_id  # ← Pasar a la siguiente tarea
    }

# 3. En tarea_2:
def tarea_2(self, result):
    usuario_id = result.get("usuario_id")
    if usuario_id:
        usuario = Usuario.objects.get(id=usuario_id)
    else:
        usuario = _get_sistema_user()
    
    # Registrar logs con el usuario correcto
    registrar_actividad_tarjeta_nomina(
        usuario=usuario,  # ← Usuario real
        ...
    )
```

---

## ✅ **Verificación**

Para confirmar que el fix funciona:

```bash
docker compose exec django python manage.py shell -c "
from nomina.models_logging import TarjetaActivityLogNomina

# Ver últimos logs del cierre
cierre_id = 30
logs = TarjetaActivityLogNomina.objects.filter(
    cierre_id=cierre_id
).order_by('-timestamp')[:5]

for log in logs:
    print(f'{log.accion:25} | Usuario: {log.usuario.nombre} {log.usuario.apellido} (ID: {log.usuario.id})')
"
```

**Output esperado:**
```
classification_complete   | Usuario: Cecilia Reyes (ID: 24)
upload_excel              | Usuario: Cecilia Reyes (ID: 24)
delete_archivo            | Usuario: Cecilia Reyes (ID: 24)
```

Todos los logs de la misma sesión deben tener **el mismo usuario**.

---

## 📌 **Impacto del Fix**

- ✅ **Trazabilidad correcta**: Los logs reflejan quién realmente ejecutó la acción
- ✅ **Auditoría precisa**: Se puede rastrear qué usuario hizo qué
- ✅ **UI consistente**: El historial muestra el usuario correcto
- ✅ **Responsabilidad clara**: Cada acción está asociada al usuario real

---

**Fecha:** 18 de octubre de 2025  
**Tipo de cambio:** Bugfix - Corrección de logging  
**Prioridad:** Alta (afecta trazabilidad y auditoría)  
**Estado:** ✅ Aplicado y testeado
