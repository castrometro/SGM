# Documentación: Tarjeta Tipo de Documento

## Resumen General

La tarjeta "Tipo de Documento" es la primera tarjeta del flujo de procesamiento contable. Permite a los usuarios subir un archivo Excel con los tipos de documento del cliente, implementando un sistema robusto de validación, tracking y auditabilidad.

## Características Principales

- ✅ **Validación estricta de nombre de archivo** por cliente
- ✅ **Tracking completo de uploads** con sistema UploadLog
- ✅ **Procesamiento asíncrono** con Celery
- ✅ **Monitoreo en tiempo real** del estado de procesamiento
- ✅ **Prevención de datos duplicados**
- ✅ **Mensajes de error específicos y claros**
- ✅ **Control de dependencias** para habilitar tarjetas siguientes

---

## 🏗️ Arquitectura del Sistema

### Backend (Django)

#### Modelos Involucrados

1. **`UploadLog`** (`backend/contabilidad/models.py`)
   - **Propósito**: Tracking unificado de todos los uploads
   - **Campos principales**:
     - `tipo_upload`: 'tipo_documento'
     - `cliente`: Referencia al cliente
     - `usuario`: Usuario que subió el archivo
     - `nombre_archivo_original`: Nombre exacto del archivo
     - `ruta_archivo`: Ruta del archivo en storage
     - `estado`: 'subido' → 'procesando' → 'completado'/'error'
     - `errores`: Detalles de errores si los hay
     - `resumen`: JSON con resultados del procesamiento

2. **`TipoDocumento`** (`backend/contabilidad/models.py`)
   - **Propósito**: Almacena los tipos de documento procesados
   - **Campos**: `codigo`, `descripcion`, `cliente`

3. **`TipoDocumentoArchivo`** (`backend/contabilidad/models.py`)
   - **Propósito**: Referencia al archivo actual del cliente
   - **Relación**: Vinculado con `UploadLog` para auditabilidad

#### Validación de Archivos

**Validación de Nombre** (`UploadLog.validar_nombre_archivo()`)
```python
# Formato requerido: {rut_sin_puntos_ni_guion}_TipoDocumento.xlsx
# Ejemplo: 967078700_TipoDocumento.xlsx

def validar_nombre_archivo(nombre_archivo, tipo_upload, cliente_rut):
    rut_limpio = cliente_rut.replace('.', '').replace('-', '')
    patron_esperado = f"{rut_limpio}_TipoDocumento"
    # Validación contra diferentes variantes aceptadas
```

**Estados de Validación**:
- ✅ **Válido**: Coincide exactamente con el formato
- ❌ **Inválido**: Retorna mensaje específico con formato esperado vs recibido

#### Vistas (APIs)

1. **`cargar_tipo_documento`** (`POST /api/contabilidad/tipo-documento/subir-archivo/`)
   - Valida nombre de archivo
   - Verifica que no existan datos previos
   - Crea registro UploadLog
   - Guarda archivo temporal
   - Dispara tarea Celery

2. **`estado_upload_log`** (`GET /api/contabilidad/upload-log/{id}/estado/`)
   - Consulta estado en tiempo real del procesamiento

3. **`eliminar_tipos_documento`** (`POST /api/contabilidad/tipo-documento/{cliente_id}/eliminar-todos/`)
   - Elimina tipos de documento existentes
   - Limpia UploadLogs relacionados
   - Elimina archivos físicos

#### Tarea Celery

**`procesar_tipo_documento_con_upload_log`** (`backend/contabilidad/tasks.py`)

**Flujo de Procesamiento**:
```
1. Validar nombre de archivo ✅
2. Verificar no existencia de datos previos ✅  
3. Buscar archivo temporal ✅
4. Calcular hash del archivo ✅
5. Procesar con parser existente ✅
6. Contar registros creados ✅
7. Actualizar TipoDocumentoArchivo ✅
8. Marcar como completado ✅
9. Limpiar archivo temporal ✅
```

### Frontend (React)

#### Componente Principal
**`TipoDocumentoCard`** (`src/components/TarjetasCierreContabilidad/TipoDocumentoCard.jsx`)

**Props**:
- `clienteId`: ID del cliente
- `cliente`: Objeto cliente completo (para mostrar RUT específico)
- `onCompletado`: Callback para notificar finalización
- `disabled`: Si la tarjeta está deshabilitada
- `numeroPaso`: Número de paso en el flujo

**Estados Internos**:
```jsx
const [estado, setEstado] = useState("pendiente"); // "pendiente" | "subido"
const [subiendo, setSubiendo] = useState(false);
const [uploadLogId, setUploadLogId] = useState(null);
const [uploadEstado, setUploadEstado] = useState(null);
const [uploadProgreso, setUploadProgreso] = useState("");
```

---

## 🔄 Flujo Completo de Operación

### 1. Carga Inicial
```jsx
useEffect(() => {
  // Verificar si ya hay tipos de documento subidos
  const data = await obtenerEstadoTipoDocumento(clienteId);
  setEstado(data === "subido" ? "subido" : "pendiente");
  onCompletado(data === "subido");
}, [clienteId]);
```

### 2. Subida de Archivo

#### Frontend - Selección y Validación
```jsx
const handleSeleccionArchivo = async (e) => {
  const archivo = e.target.files[0];
  
  // 1. Subir archivo
  const formData = new FormData();
  formData.append("cliente_id", clienteId);
  formData.append("archivo", archivo);
  
  const response = await subirTipoDocumento(formData);
  
  // 2. Iniciar monitoreo
  if (response.upload_log_id) {
    setUploadLogId(response.upload_log_id);
    // El useEffect iniciará el monitoreo automático
  }
};
```

#### Backend - Validación y Guardado
```python
def cargar_tipo_documento(request):
    # 1. Validar nombre de archivo
    es_valido, mensaje = UploadLog.validar_nombre_archivo(
        archivo.name, 'TipoDocumento', cliente.rut
    )
    
    # 2. Crear UploadLog
    upload_log = UploadLog.objects.create(
        tipo_upload='tipo_documento',
        cliente=cliente,
        usuario=request.user,
        nombre_archivo_original=archivo.name,
        estado='subido'
    )
    
    # 3. Guardar archivo temporal
    nombre_archivo = f"temp/tipo_doc_cliente_{cliente_id}_{upload_log.id}.xlsx"
    ruta_guardada = default_storage.save(nombre_archivo, archivo)
    
    # 4. Disparar tarea Celery
    procesar_tipo_documento_con_upload_log.delay(upload_log.id)
```

### 3. Monitoreo en Tiempo Real

#### Frontend - Polling del Estado
```jsx
useEffect(() => {
  if (!uploadLogId || !subiendo) return;

  const monitorearUpload = async () => {
    const logData = await obtenerEstadoUploadLog(uploadLogId);
    
    if (logData.estado === 'completado') {
      setEstado("subido");
      onCompletado(true); // Habilita tarjeta siguiente
      mostrarNotificacion("success", "Archivo procesado exitosamente");
    } else if (logData.estado === 'error') {
      setError(logData.errores);
      mostrarNotificacion("error", "Error en procesamiento");
    }
  };

  const intervalo = setInterval(monitorearUpload, 2000);
  return () => clearInterval(intervalo);
}, [uploadLogId, subiendo]);
```

#### Backend - Procesamiento Celery
```python
@shared_task
def procesar_tipo_documento_con_upload_log(upload_log_id):
    upload_log = UploadLog.objects.get(id=upload_log_id)
    upload_log.estado = 'procesando'
    upload_log.save()
    
    try:
        # Validar archivo nuevamente
        # Procesar con parser existente
        # Actualizar registros
        
        upload_log.estado = 'completado'
        upload_log.resumen = {
            'tipos_documento_creados': count,
            'procesamiento_exitoso': True
        }
        upload_log.save()
        
    except Exception as e:
        upload_log.estado = 'error'
        upload_log.errores = str(e)
        upload_log.save()
```

---

## 🎨 Interfaz de Usuario

### Estados Visuales

#### Estado Pendiente
```jsx
- Badge: "pendiente" (gris)
- Botón: "Elegir archivo .xlsx" (habilitado)
- Información: Muestra formato requerido específico del cliente
- Botón "Ver tipos": Deshabilitado
```

#### Estado Subiendo/Procesando
```jsx
- Badge: "pendiente" (gris con spinner)
- Botón: "Subiendo..." / "Procesando archivo..." (deshabilitado)
- Progreso: Indicador detallado del procesamiento
- Información adicional: Registros procesados, tiempo, etc.
```

#### Estado Completado
```jsx
- Badge: "subido" (verde)
- Botón: "Elegir archivo .xlsx" (habilitado para reemplazar)
- Botón "Ver tipos": Habilitado
- Información: "✔ Archivo cargado correctamente (X tipos de documento)"
```

### Validación y Errores

#### Error de Nombre de Archivo
```jsx
// Mensaje específico con formato esperado
❌ Nombre de archivo incorrecto

📋 Formato requerido: 967078700_TipoDocumento.xlsx
📁 Archivo enviado: archivo_incorrecto.xlsx

💡 Asegúrese de que el archivo siga exactamente el formato indicado.
```

#### Error de Datos Existentes
```jsx
// Error 409 del backend
⚠️ Ya existen 25 tipos de documento. 
Debe eliminar todos los registros antes de subir un nuevo archivo.

💡 Tip: Use el botón "Eliminar todos" primero.
```

---

## 🔧 Configuración y Mantenimiento

### Variables de Configuración

#### Formatos de Archivo Aceptados
```python
# En UploadLog.validar_nombre_archivo()
tipos_validos = {
    'TipoDocumento': ['TipoDocumento', 'TiposDocumento'],
    # Futuras variantes pueden agregarse aquí
}
```

#### Rutas de Archivos
```python
# Temporal: temp/tipo_doc_cliente_{cliente_id}_{upload_log_id}.xlsx
# Permanente: tipo_documento/cliente_{cliente_id}_{timestamp}.xlsx
```

### Logging y Auditabilidad

#### Logs de Sistema
```python
logger.info(f"Validando nombre de archivo: {archivo.name}")
logger.info(f"✅ Procesamiento completado: {count} tipos creados")
logger.error(f"Error en procesamiento: {error}")
```

#### Tracking de Usuario
```python
# TarjetaActivityLog registra:
- Subidas exitosas/fallidas
- Visualizaciones de datos
- Eliminaciones masivas
- Errores específicos
```

---

## 🚀 Integración con Otras Tarjetas

### Control de Dependencias

```jsx
// En CierreProgreso.jsx
const handleTipoDocumentoCompletado = (ready) => setTipoDocumentoReady(ready);

<ClasificacionBulkCard
  disabled={!tipoDocumentoReady}  // Solo se habilita cuando tipo doc está listo
  onCompletado={handleClasificacionCompletado}
/>
```

### Flujo de Habilitación
```
1. TipoDocumentoCard: disabled=false (siempre habilitada)
2. ClasificacionBulkCard: disabled=true → false (cuando tipo doc se completa)
3. NombresEnInglesCard: disabled=true → false (cuando clasificación se completa)
4. LibroMayorCard: disabled=true → false (cuando pasos previos se completan)
```

---

## 🧪 Testing y Validación

### Casos de Prueba

#### Nombres de Archivo Válidos
```
✅ 967078700_TipoDocumento.xlsx
✅ 123456789_TiposDocumento.xlsx (variante plural)
```

#### Nombres de Archivo Inválidos
```
❌ archivo.xlsx (sin formato)
❌ 967078700_TipoDoc.xlsx (abreviación incorrecta)
❌ 967078700_TipoDocumento.xls (extensión incorrecta)
❌ 12345_TipoDocumento.xlsx (RUT incompleto)
```

#### Flujos de Error
```
- Subir archivo con datos existentes → Error 409
- Subir archivo con nombre incorrecto → Error 400 con formato específico
- Error en procesamiento → Estado 'error' en UploadLog
- Archivo temporal perdido → Error específico de archivo no encontrado
```

---

## 📋 Checklist de Implementación

### Backend ✅
- [x] Modelo UploadLog implementado
- [x] Validación de nombres de archivo
- [x] Vista de subida con validación
- [x] Tarea Celery robusta
- [x] APIs de consulta de estado
- [x] Manejo de errores específicos

### Frontend ✅
- [x] Componente TipoDocumentoCard
- [x] Monitoreo en tiempo real
- [x] Indicadores visuales de progreso
- [x] Manejo de errores específicos
- [x] Integración con flujo de tarjetas

### Funcionalidades ✅
- [x] Validación estricta de archivos
- [x] Tracking completo de uploads
- [x] Procesamiento asíncrono
- [x] Control de dependencias
- [x] Auditabilidad completa
- [x] Experiencia de usuario fluida

---

## 🔄 Próximas Mejoras

### Funcionalidades Futuras
1. **Validación de contenido**: Verificar estructura interna del Excel
2. **Preview de datos**: Mostrar vista previa antes de procesar
3. **Notificaciones push**: WebSockets para actualizaciones en tiempo real
4. **Métricas avanzadas**: Dashboard de estadísticas de procesamiento
5. **Rollback**: Capacidad de deshacer procesamiento y volver a estado anterior

### Extensión a Otras Tarjetas
```
- Aplicar mismo patrón UploadLog a:
  ✅ ClasificacionBulkCard
  ✅ NombresEnInglesCard  
  ✅ LibroMayorCard
```

---

*Documentación actualizada: 17 de junio de 2025*
*Sistema en producción: UploadLog + TipoDocumento integrado*
