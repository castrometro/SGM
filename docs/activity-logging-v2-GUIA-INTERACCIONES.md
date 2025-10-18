# 🎯 Activity Logging V2 - Guía de Interacciones

**Sistema de Seguimiento Automático de Actividad de Usuario**

---

## 📋 ¿QUÉ INTERACCIONES CAPTURA?

El sistema Activity Logging V2 registra **automáticamente** las siguientes interacciones cuando un usuario trabaja con las tarjetas de nómina:

---

### 🟢 **1. SESSION_STARTED**

**Cuándo se captura:** Al abrir/visualizar una tarjeta de archivo  
**Dónde ocurre:** useEffect al montar el componente  
**Componentes:** IngresosCard, FiniquitosCard, AusentismosCard, MovimientosMesCard

```javascript
// Se ejecuta automáticamente al abrir la tarjeta
useEffect(() => {
  if (cierreId && clienteId && !activityLogger.current) {
    activityLogger.current = createActivityLogger(clienteId, cierreId);
    activityLogger.current.logSessionStart(); // ← AQUÍ
  }
}, [cierreId, clienteId]);
```

**Evento registrado:**
```json
{
  "action": "session_started",
  "resource_type": "cierre",
  "resource_id": "123",
  "details": {}
}
```

**Ejemplo de uso:** "Usuario Juan abrió la tarjeta de Ingresos a las 10:30"

---

### 🔵 **2. MODAL_OPENED**

**Cuándo se captura:** Al hacer clic en "Subir Archivo" (abre modal)  
**Dónde ocurre:** Función `handleModalOpen()`  
**Componentes:** Todas las tarjetas con modal de subida

```javascript
const handleModalOpen = () => {
  setShowModal(true);
  if (activityLogger.current) {
    activityLogger.current.logModalOpen('ingresos'); // ← AQUÍ
  }
};
```

**Evento registrado:**
```json
{
  "action": "modal_opened",
  "resource_type": "ingresos",
  "details": {}
}
```

**Ejemplo de uso:** "Usuario María abrió el modal de subida de archivo de Finiquitos"

---

### 🟡 **3. FILE_SELECTED**

**Cuándo se captura:** Al seleccionar un archivo desde el explorador  
**Dónde ocurre:** onChange del `<input type="file">`  
**Componentes:** Todas las tarjetas con subida de archivos

```javascript
const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (file) {
    setSelectedFile(file);
    if (activityLogger.current) {
      activityLogger.current.logFileSelect('ingresos', file.name, file.size); // ← AQUÍ
    }
  }
};
```

**Evento registrado:**
```json
{
  "action": "file_selected",
  "resource_type": "ingresos",
  "details": {
    "filename": "ingresos_enero_2025.xlsx",
    "filesize": 45632
  }
}
```

**Ejemplo de uso:** "Usuario Pedro seleccionó el archivo 'ingresos_enero_2025.xlsx' (44 KB)"

---

### 🟠 **4. FILE_UPLOAD**

**Cuándo se captura:** Al presionar "Subir" y enviar el archivo al servidor  
**Dónde ocurre:** Después de `onSubirArchivo()` exitoso  
**Componentes:** Todas las tarjetas con subida de archivos

```javascript
const handleSubir = async () => {
  try {
    await onSubirArchivo(selectedFile);
    
    if (activityLogger.current) {
      activityLogger.current.logFileUpload('ingresos', selectedFile.name); // ← AQUÍ
    }
    
    setShowModal(false);
    setSelectedFile(null);
  } catch (error) {
    // ...
  }
};
```

**Evento registrado:**
```json
{
  "action": "file_upload",
  "resource_type": "ingresos",
  "details": {
    "filename": "ingresos_enero_2025.xlsx"
  }
}
```

**Ejemplo de uso:** "Usuario Ana subió exitosamente el archivo 'ingresos_enero_2025.xlsx'"

---

### 🟣 **5. POLLING_STARTED**

**Cuándo se captura:** Al iniciar el monitoreo automático del estado del archivo  
**Dónde ocurre:** useEffect que inicia el polling  
**Componentes:** Tarjetas con procesamiento asíncrono

```javascript
useEffect(() => {
  if (estado === "en_proceso" && !deberiaDetenerPolling) {
    if (activityLogger.current) {
      activityLogger.current.logPollingStart(3); // ← AQUÍ (cada 3 segundos)
    }
    
    pollingRef.current = setInterval(() => {
      onActualizarEstado();
    }, 3000);
  }
}, [estado]);
```

**Evento registrado:**
```json
{
  "action": "polling_started",
  "resource_type": "cierre",
  "details": {
    "interval_seconds": 3
  }
}
```

**Ejemplo de uso:** "Sistema inició monitoreo automático cada 3 segundos para usuario Luis"

---

### ⚪ **6. POLLING_STOPPED**

**Cuándo se captura:** Al detener el monitoreo (archivo procesado o error)  
**Dónde ocurre:** useEffect cleanup o cambio de estado  
**Componentes:** Tarjetas con procesamiento asíncrono

```javascript
useEffect(() => {
  return () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      if (activityLogger.current) {
        activityLogger.current.logPollingStop('component_unmount'); // ← AQUÍ
      }
    }
  };
}, []);
```

**Evento registrado:**
```json
{
  "action": "polling_stopped",
  "resource_type": "cierre",
  "details": {
    "reason": "file_processed" // o "error" o "component_unmount"
  }
}
```

**Ejemplo de uso:** "Monitoreo detenido: archivo procesado exitosamente"

---

### 🔵 **7. MODAL_CLOSED**

**Cuándo se captura:** Al cerrar el modal (con X o después de subir)  
**Dónde ocurre:** Función `handleModalClose()`  
**Componentes:** Todas las tarjetas con modal de subida

```javascript
const handleModalClose = () => {
  setShowModal(false);
  setSelectedFile(null);
  
  if (activityLogger.current) {
    activityLogger.current.logModalClose('ingresos'); // ← AQUÍ
  }
};
```

**Evento registrado:**
```json
{
  "action": "modal_closed",
  "resource_type": "ingresos",
  "details": {}
}
```

**Ejemplo de uso:** "Usuario Carlos cerró el modal de subida de Ausentismos"

---

## 🔍 FLUJO COMPLETO DE UNA SESIÓN TÍPICA

Así se vería una sesión real de un usuario subiendo un archivo:

```
1. 🟢 SESSION_STARTED         (10:30:00) - Abre tarjeta de Ingresos
2. 🔵 MODAL_OPENED            (10:30:15) - Click en "Subir Archivo"
3. 🟡 FILE_SELECTED           (10:30:22) - Selecciona "ingresos_enero.xlsx"
4. 🟠 FILE_UPLOAD             (10:30:28) - Presiona "Subir"
5. 🟣 POLLING_STARTED         (10:30:29) - Inicia monitoreo automático
   ... (sistema espera procesamiento cada 3 segundos)
6. ⚪ POLLING_STOPPED         (10:31:15) - Archivo procesado OK
7. 🔵 MODAL_CLOSED            (10:31:16) - Cierra modal automáticamente
```

**Total:** 7 eventos capturados en ~1 minuto de trabajo

---

## 📊 ¿CÓMO SE VEN LOS EVENTOS EN LA BASE DE DATOS?

```sql
SELECT 
  timestamp,
  action,
  resource_type,
  details
FROM nomina_activityevent
WHERE user_id = 5 AND cliente_id = 1
ORDER BY timestamp DESC;
```

**Resultado:**
```
| timestamp           | action           | resource_type | details                          |
|---------------------|------------------|---------------|----------------------------------|
| 2025-10-16 10:31:16 | modal_closed     | ingresos      | {}                               |
| 2025-10-16 10:31:15 | polling_stopped  | cierre        | {"reason": "file_processed"}     |
| 2025-10-16 10:30:29 | polling_started  | cierre        | {"interval_seconds": 3}          |
| 2025-10-16 10:30:28 | file_upload      | ingresos      | {"filename": "ingresos_..."}     |
| 2025-10-16 10:30:22 | file_selected    | ingresos      | {"filename": "...", "size": ...} |
| 2025-10-16 10:30:15 | modal_opened     | ingresos      | {}                               |
| 2025-10-16 10:30:00 | session_started  | cierre        | {}                               |
```

---

## 🎯 CASOS DE USO DEL LOGGING

### 1. **Análisis de UX**
- ¿Cuánto tiempo tardan los usuarios en subir archivos?
- ¿Cuántos intentos fallidos hay?
- ¿Qué tarjetas son más usadas?

### 2. **Auditoría**
- ¿Quién subió el archivo de Ingresos el 15 de enero?
- ¿Qué usuario hizo cambios en el cierre #123?

### 3. **Debugging**
- Si un usuario reporta un error, ver exactamente qué estaba haciendo
- Reproducir secuencia de acciones que causó un problema

### 4. **Optimización**
- Identificar cuellos de botella en el flujo de trabajo
- Detectar tareas que toman mucho tiempo

---

## 🧪 CÓMO PROBAR QUE FUNCIONA

### Paso 1: Abrir un cierre de nómina
```
1. Login en el sistema
2. Ir a: Menu → Nómina → Clientes
3. Seleccionar un cliente
4. Click en un cierre existente
```

### Paso 2: Interactuar con una tarjeta
```
1. En la sección "Archivos del Analista"
2. Click en tarjeta "Ingresos"
3. Click en "Subir Archivo"
4. Seleccionar un archivo Excel
5. Click en "Subir"
```

### Paso 3: Verificar eventos en BD
```bash
docker compose exec django python manage.py shell -c "
from nomina.models import ActivityEvent
eventos = ActivityEvent.objects.filter(user_id=YOUR_USER_ID).order_by('-timestamp')[:10]
for e in eventos:
    print(f'{e.timestamp} | {e.action:20} | {e.resource_type}')
"
```

**Deberías ver algo como:**
```
2025-10-16 10:30:28 | file_upload          | ingresos
2025-10-16 10:30:22 | file_selected        | ingresos
2025-10-16 10:30:15 | modal_opened         | ingresos
2025-10-16 10:30:00 | session_started      | cierre
```

---

## ❗ IMPORTANTE: ¿Por qué no funciona?

Si los eventos NO se están registrando, verifica:

### ✅ Checklist de Troubleshooting:

1. **Frontend compila sin errores**
   ```bash
   # Ver consola de Vite
   npm run dev
   ```

2. **Usuario tiene clienteId disponible**
   ```javascript
   // En consola del navegador
   console.log(cliente); // Debe mostrar objeto con .id
   ```

3. **API responde correctamente**
   ```bash
   # Ver logs de Django
   docker compose logs django --tail=50 | grep "activity"
   ```

4. **Logger está habilitado**
   ```javascript
   // En src/utils/activityLogger_v2.js
   const CONFIG = {
     enabled: true,  // ← DEBE SER TRUE
     debug: true,    // ← Muestra logs en consola
   };
   ```

5. **Componente recibe clienteId**
   ```javascript
   // En IngresosCard.jsx, agregar console.log:
   console.log('clienteId recibido:', clienteId);
   console.log('cierreId recibido:', cierreId);
   ```

---

## 🐛 ERROR COMÚN RESUELTO

**Error:** `'Usuario' object has no attribute 'clientes'`

**Causa:** El view estaba buscando `user.clientes.all()` pero el modelo usa `user.asignaciones`

**Solución:** ✅ Ya corregido en `views_activity_v2.py` líneas 38 y 118

---

## 📞 ¿Necesitas ayuda?

Si sigues sin ver eventos:
1. Abre la consola del navegador (F12)
2. Busca mensajes con `[ActivityV2]`
3. Copia los mensajes y compártelos

**Ejemplo de log exitoso:**
```
📤 [ActivityV2] {cliente_id: 1, action: "session_started", ...}
✅ [ActivityV2] OK
```

**Ejemplo de log con error:**
```
❌ [ActivityV2] Request failed with status code 500
```

---

**Fecha:** 16 de octubre de 2025  
**Sistema:** Activity Logging V2  
**Estado:** 🟢 Activo (después de fix de clientes)
